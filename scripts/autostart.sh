#!/bin/bash
cd /home/pi/pynitel

# wait IP connection (ping to github)
for i in {1..50}; do ping -c1 www.118712.fr &> /dev/null && break; done

# start the main python script
/usr/bin/python3 example_annuaire.py
