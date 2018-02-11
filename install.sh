# update raspbian
sudo apt update && sudo apt dist-upgrade

# installation git python3 et pip3
sudo apt install git python3 python3-pip

# instalation de pynitel
cd ~ && git clone https://github.com/cquest/pynitel.git
cd pynitel

# installation des dépendances
pip3 install -r requirements.txt

# installation service systemd
sudo cp ae.service /etc/systemd/system

sudo reboot
