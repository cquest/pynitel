#!/bin/bash
cd /home/pi/pynitel

# wait IP connection (ping to github)
for i in {1..50}; do ping -c1 www.github.com &> /dev/null && break; done

# get the latest version available
/usr/bin/git pull

# update requirements if needed
/usr/bin/pip3 install -r requirements.txt --upgrade

# start the main python script
/usr/bin/python3 example_annuaire.py
