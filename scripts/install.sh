#
# Script d'installation pour un fonctionnement automatique
# de l'annuaire électronique sur une Raspberry Pi
#

# update raspbian
sudo apt update && sudo apt dist-upgrade -y

# installation git python3 et pip3
sudo apt install git python3 python3-pip python3-lxml -y

# instalation de pynitel
cd ~ && git clone https://github.com/cquest/pynitel.git
cd pynitel

# installation des dépendances
pip3 install -r requirements.txt

# installation service systemd
sudo cp scripts/ae.service /etc/systemd/system/
sudo systemctl enable ae.service
chmod u+x scripts/autostart.sh

sudo reboot
