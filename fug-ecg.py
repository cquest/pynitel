#!/usr/bin/env python3

import serial
import pynitel
import time

m = None

# bascule en 4800bps
m = pynitel.Pynitel(serial.Serial('/dev/ttyUSB0', 1200,
                                    parity=serial.PARITY_EVEN, bytesize=7,
                                    timeout=2))
m._print(m.PRO2+"\x6b\x76")
time.sleep(0.1)


m = pynitel.Pynitel(serial.Serial('/dev/ttyUSB0', 4800,
                                    parity=serial.PARITY_EVEN, bytesize=7,
                                    timeout=2))

def ecg(m, couleur, phase):
    "Tracé des différentes phases du signal ECG"
    if phase>0:
        print(couleur, phase)

    if phase == 1:
        m.pos(12,1)
        m.color(couleur)
        m._print("___")

    if phase == 2:
        m.pos(12,4)
        m.color(couleur)
        if couleur == m.blanc:
            m._print(chr(7))
        m.scale(1)
        m._print("/\x0b\x0b"*3+"/\\")
        m._print("\x0a\x0a\\"*5)
        m._print("/\x0b\x0b"*2)
        m.scale(0)

    if phase == 3:
        m.pos(12,16)
        m.color(couleur)
        m._print("_____")

    if phase == 4:
        m.pos(12,21)
        m.color(couleur)
        m._print("/\x0b/\x0a")
        m.scale(1)
        m._print("\\")
        m.scale(0)

    if phase == 5:
        m.pos(12,24)
        m.color(couleur)
        m._print("________")

    if phase == 6:
        m.pos(12,32)
        m.color(couleur)
        m._print("/\\")

    if phase == 7:
        m.pos(12,34)
        m.color(couleur)
        m._print("_______")


# efface écran + affichage grille
m.home()
m.color(m.bleu)
for nb in range(5):
    m._print("   |"*10)
    m._print("   |"*10)
    m._print("   |"*10)
    m._print("̶̶̶+"*10)
m._print("   |"*10)
m._print("   |"*10)
m._print("   |"*10)

# boucle infinie...
while True:
    # on passe par chaque phase du signal
    for phase in range(10):
        # front de signal (blanc)
        ecg(m, m.blanc, phase)
        # rémanence signal
        ecg(m, m.cyan, phase-1)
        ecg(m, m.magenta, phase-2)
        ecg(m, m.bleu, phase-3)
