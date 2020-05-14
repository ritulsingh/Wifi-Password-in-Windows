# -*- coding: utf-8 -*-
"""
Created on Wed May 13 16:12:21 2020

@author: Ritul Singh
"""
# import subprocess library as su
import subprocess as su

# Getting all saved Wifi name in our computer
a = su.check_output(['netsh','wlan','show' ,'profiles']).decode('utf-8').split('\n')

# We want to know about all the profiles that are stored on our computer and we are stored in the wifi_name list
wifi_name = [i.split(":")[1][1:-1] for i in a if "All User Profile" in i]

# toatl number of wifi network in our computer using len
count = len(wifi_name)
print("\n The total number of wifi networks in your computer",count)
print("================================================================")
print(" Wifi Name                     |  Password\n")

for i in wifi_name:
    # the following command to see the password of any WiFi network:
    results = su.check_output(['netsh', 'wlan', 'show' , 'profile', i, 'key=clear']).decode('utf-8').split('\n')
    
  # search the word key content in results and split the password and again stored in results
    results = [b.split(":")[1][1:-1] for b in results if "Key Content" in b]
        
    try:
        # those contain password than the print
        print(" {:<30}|  {:<}".format(i, results[0]))

    except IndexError:
        # those not contain password  
        print(" {:<30}|  This wifi contain no passward  {:<}".format(i, ""))

