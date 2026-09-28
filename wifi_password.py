# -*- coding: utf-8 -*-
"""
Show the passwords of all Wi-Fi networks saved on a Windows computer
and save them to a text file.

Created on Wed May 13 16:12:21 2020
@author: Ritul Singh

Saving the output to a text file added on 27/10/2020
@abolfazl_samadi
"""
import argparse
import ctypes
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

DEFAULT_OUTPUT = "password_router.txt"
NO_PASSWORD = "(no saved password: open or enterprise network)"

# "    All User Profile     : name" -> the label is localized, so match the
# layout instead. The value is kept verbatim: profile names may have
# trailing spaces, colons or non-ASCII characters.
PROFILE_LINE = re.compile(r"^\s{4}\S[^:]*?\s+: (.*)$")
KEY_LINE = re.compile(r"^\s+Key Content\s+: (.*)$")


def decode(raw):
    """Decode netsh output: UTF-8 if possible, else the console's code page."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        codepage = ctypes.windll.kernel32.GetConsoleOutputCP() or ctypes.windll.kernel32.GetOEMCP()
        return raw.decode(f"cp{codepage}", errors="replace")


def netsh(*args):
    result = subprocess.run(
        ["netsh", "wlan", *args],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    output = decode(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(output.strip() or f"netsh exited with code {result.returncode}")
    return output.splitlines()


def get_profiles():
    return [m.group(1) for line in netsh("show", "profiles") if (m := PROFILE_LINE.match(line))]


def get_password(profile):
    try:
        lines = netsh("show", "profile", f"name={profile}", "key=clear")
    except RuntimeError:
        return None
    for line in lines:
        if m := KEY_LINE.match(line):
            return m.group(1)
    return None


def build_report(results):
    width = max([len("Wifi Name")] + [len(name) for name, _ in results])
    lines = [
        f"The total number of wifi networks in your computer = {len(results)}",
        "=" * (width + 30),
        f"{'Wifi Name':<{width}} | Password",
        "-" * (width + 30),
    ]
    lines += [f"{name:<{width}} | {password or NO_PASSWORD}" for name, password in results]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Show saved Wi-Fi passwords on Windows.")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help=f"text file to save the result in (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--no-file", action="store_true", help="only print, do not save a file")
    args = parser.parse_args()

    if sys.platform != "win32":
        sys.exit("This script only works on Windows.")

    try:
        profiles = get_profiles()
    except FileNotFoundError:
        sys.exit("Error: 'netsh' was not found.")
    except RuntimeError as e:
        sys.exit(f"Error: could not read Wi-Fi profiles (is the WLAN service running?)\n{e}")

    if not profiles:
        print("No saved Wi-Fi networks were found.")
        return

    # Query all profiles in parallel; each netsh call is slow on its own.
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(zip(profiles, pool.map(get_password, profiles)))

    report = build_report(results)

    # Print safely even on consoles that cannot display every character.
    sys.stdout.reconfigure(errors="replace")
    print(report)

    if not args.no_file:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(report)
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
