#!/bin/bash
cd /home/pi/pynitel

# get the latest version available
/usr/bin/git pull

# update requirements if needed
/usr/bin/pip3 install -r requirements.txt --upgrade

# start the main python script
/usr/bin/python3 example_annuaire.py
