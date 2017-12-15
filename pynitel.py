#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ré-écritude en python3 de Cristel !
# (C) 1984-2017 Christian Quest / A-GPL

import serial
import time

ecrans = {'last': None}
conn = None
inbuf = b''
lastkey = 0
lastscreen = ''
laststar = False
zones = []
zonenumber = 0

# constantes de couleurs
noir=0
rouge=1
vert=2
jaune=3
bleu=4
magenta=5
cyan=6
blanc=7

# constantes des touches de fonction du Minitel en mode Vidéotex ou Mixte
envoi=1
retour=2
repetition=3
guide=4
annulation=5
sommaire=6
correction=7
suite=8
connexionfin=9

def wait():
  "Attente d'une connexion"

  print('ATTENTE')

  while conn.read(1) != b' ' : # ESC reçu... on considère qu'on est connecté
    time.sleep(1)

  print('CONNECTION')

def end():
  "Fin de connexion, raccrochage"
  conn.write(b'\x1b9g')

def get():
  "Réception d'un caractère"
  return(conn.read(1))

def _if():
  "Dernier caractère reçu"
  data = conn.read()
  if not data:
  	return None
  else:
    return data

def clear():
  "Efface le buffer de réception"
  conn.settimeout(0) # timeout de 2 minutes pour les saisies...
  data = conn.recv(10000)

def _print(text):
  "Envoi de texte vers le minitel"
  send(accents(text))

def home():
  "Efface écran et ligne 0"
  _del(0,1)
  sendchr(12) # FF
  cursor(False) # Coff

def vtab(ligne):
  "Positionne le curseur sur un début de ligne"
  pos(ligne,1)

def pos(ligne, colonne=1):
  "Positionne le curseur sur une ligne / colonne"
  if ligne == 1 and colonne == 1:
    sendchr(30)
  else:
    sendchr(31)
    sendchr(64+ligne)
    sendchr(64+colonne)

def _del(ligne,colonne):
  "Effacement jusque fin de ligne"
  pos(ligne,colonne)
  sendchr(24)

def inverse():
  "Passage en vidéo inversée"
  sendesc(']')

def normal():
  "Passage en vidéo normale"
  sendesc('I')

def backcolor(couleur):
  "Change la couleur de fond, à valider par un espace pour le texte (identique à HCOLOR)"
  sendesc(chr(80+couleur))

def canblock(debut,fin,colonne,inverse=False):
    "Efface un rectangle sur l'écran, compris entre deux lignes et après une colonne"
    if inverse == False:
        pos(ligne,colonne)
        sendchr(24)
        for ligne in range(debut, fin):
            sendchr(10)
            sendchr(24)
    else:
        pos(fin,colonne)
        sendchr(24)
        for ligne in range(debut, fin):
            sendchr(11)
            sendchr(24)

def caneol(ligne, colonne):
    "Efface la fin de ligne derrière la colonne spécifiée"
    pos(ligne,colonne)
    sendchr(24) # CAN

def cls():
    "Efface l'écran du Minitel"
    home()

def color(couleur):
  "Change la couleur du texte ou graphique"
  sendesc(chr(64+couleur))

#curpos - donne la position actuelle du curseur du Minitel

def cursor(visible):
    "Permet de rendre apparent ou invisible le curseur clignotant"
    if visible == 1 or visible == True :
        sendchr(17) # Con
    else:
        sendchr(20) # Coff

#dial - appel un numéro de téléphone

def draw(num=0):
  "Envoi un écran préchargé dans un buffer vers le minitel"
  if num is None:
    num = ecrans['last']
  ecrans['last']=num
  if num is not None:
    conn.write(ecrans[num])

def drawscreen(fichier):
  "Envoi du contenu d'un fichier"
  with open(fichier,'rb') as f:
    conn.write(f.read())

def flash(clignote=True):
  "Passage en clignotant"
  if clignote is None or clignote == True or clignote == 1:
      sendesc('\x48')
  else:
      sendesc('\x49')

def forecolor(couleur):
    "Change la couleur des caractères"
    color(couleur)

def get():
    "Rend le contenu du buffer de saisie actuel"
    return(conn.read(conn.in_waiting).decode())

# getid - lecture ROM/RAM Minitel


def hcolor(couleur):
  "Change la couleur de fond, à valider par un espace pour le texte"
  sendesc(chr(80+couleur))

def input(ligne, colonne, longueur, data='', caractere = '.', redraw=True):
  "Gestion de zone de saisie"
  texte = ''
  # affichage initial
  if redraw:
      sendchr(20) # Coff
      pos(ligne, colonne)
      _print(data)
      plot(caractere,longueur-len(data))
  pos(ligne, colonne+len(data))
  sendchr(17) # Con

  while True:
      c = conn.read(1).decode()
      if c == '':
          continue
      elif c == '\x13': #SEP donc touche Minitel...
        c = conn.read(1).decode()

        if c == '\x45' and data != '': # annulation
            data = ''
            sendchr(20) # Coff
            pos(ligne, colonne)
            _print(data)
            plot(caractere,longueur-len(data))
            pos(ligne, colonne)
            sendchr(17) # Con
        elif c == '\x47' and data != '': # correction
            send(chr(8)+caractere+chr(8))
            data = data[:len(data)-1]
        else:
            lastkey = ord(c)-64
            laststar = (data != '' and data[:-1] == '*')
            return(data,ord(c)-64)
      elif c>=' ' and len(data)>=longueur:
          bip()
      elif c>=' ' :
          data = data + c

def inverse(inverse=1):
  "Passage en inverse"
  if inverse is None or inverse == 1 or inverse == True:
      sendesc('\x5D')
  else:
      sendesc('\x5C')

def locate(ligne,colonne):
    "Positionne le curseur"
    pos(ligne, colonne)

# lower - change le clavier en mode minuscule / majuscule (mode "Enseignement")

def message(ligne,colonne,delai,message,bip=False):
    "Affiche un message à une position donnée pendant un temps donné, puis l'efface"
    if bip:
        bip()
    pos(ligne, colonne)
    _print(message)
    conn.flush()
    time.sleep(delai)
    pos(ligne, colonne)
    plot(' ', len(message))

def printscreen(fichier):
    drawscreen(fichier)

def resetzones():
    while len(zones)>0:
        zones.pop()

# scroll - Active ou désactive le mode "rouleau"

def starflag():
    "Indique si la dernière saisie s'est terminée par une étoile + touche de fonction"
    return(laststar)

# status - Etat du modem

# swmodem - Retournement du modem

# sysparm - Paramètres du modem

def underline(souligne=True):
    "Passe en mode souligné ou normal"
    if souligne is None or souligne == True or souligne == 1:
        sendesc(chr(90))
    else:
        sendesc(chr(89))

def waitzones(zone):
    "Gestion de zones de saisie"
    if len(zones) == 0:
        return (0,0)

    zone = -zone

    while True:
        # affichage initial
        if zone <= 0:
            cursor(False)
            for z in range(1, len(zones)):
                pos(zones[z-1]['ligne'],zones[z-1]['colonne'])
                if zones[z-1]['couleur'] != blanc:
                    forecolor(zones[z-1]['couleur'])
                _print(zones[z-1]['texte'])
            if zone < 0:
                zone = -zone

        # gestion de la zone de saisie courante
        (zones[zone-1]['texte'],touche) = input(zones[zone-1]['ligne'],
            zones[zone-1]['colonne'], zones[zone-1]['longueur'],
            data=zones[zone-1]['texte'], caractere = '.', redraw=False)

        # gestion des SUITE / RETOUR
        if touche == suite:
            if zone<len(zones):
                zone = zone+1
            else:
                zone = 1
        elif touche == retour:
            if zone>1:
                zone = zone-1
            else:
                zone = len(zones)
        else:
            zonenumber = zone
            return(zone,touche)

# waitconnect - attente de CONNECTION

def zone(ligne, colonne, longueur, texte, couleur):
    "Déclaration d'une zone de saisie"
    zones.append({"ligne": ligne, "colonne": colonne,"longueur":longueur,"texte":texte,"couleur":couleur})

def key():
    "Dernière touche de fonction utilisée sur le Minitel lors d'une saisie"
    return lastkey

def scale(taille):
  "Change la taille du texte"
  sendesc(chr(76+taille))

def notrace():
  "Passe en texte souligné, à valider par un espace"
  sendesc(chr(89))

def trace():
  "Fin de texte souligné, à valider par un espace"
  sendesc(chr(90))

def plot(car,nombre):
  "Affichage répété d'un caractère"
  if nombre > 1:
      _print(car)
  if nombre == 2:
      _print(car)
  elif nombre > 2:
      sendchr(18)
      sendchr(63+nombre)

def text():
  "Mode texte"
  sendchr(15)

def gr():
  "Mode graphique"
  sendchr(14)

def step(scroll):
  "Active ou désactive le mode scrolling"
  sendesc(':')
  sendchr(ord('j')-scroll)
  send('C')

def xdraw(fichier):
  "Envoi du contenu d'un fichier"
  with open(fichier,'rb') as f:
    conn.write(f.read())

def load(num, fichier):
  "Charge un fichier vidéotex dans un buffer"
  with open(fichier,'rb') as f:
    data = f.read()
    ecrans[num] = data

def read():
  "Lecture de la date et heure"

def _print(texte):
    send(accents(texte))

def send(text):
  "Envoi de données vers le minitel"
  if conn is not None:
    conn.write(text.encode())
  else:
    print('conn = None')

def sendchr(ascii):
  send(chr(ascii))

def sendesc(text):
  sendchr(27)
  send(text)

def bip():
    sendchr(7)

def accents(text):
  "Conversion des caractères accentués (cf STUM p 103)"
  text = text.replace('à','\x19\x41a')
  text = text.replace('â','\x19\x43a')
  text = text.replace('ä','\x19\x48a')
  text = text.replace('è','\x19\x41e')
  text = text.replace('é','\x19\x42e')
  text = text.replace('ê','\x19\x43e')
  text = text.replace('ë','\x19\x48e')
  text = text.replace('î','\x19\x43i')
  text = text.replace('ï','\x19\x48i')
  text = text.replace('ô','\x19\x43o')
  text = text.replace('ö','\x19\x48o')
  text = text.replace('ù','\x19\x43u')
  text = text.replace('û','\x19\x43u')
  text = text.replace('ü','\x19\x48u')
  text = text.replace('ç','\x19\x4Bc')
  text = text.replace('°','\x19\x30')
  text = text.replace('£','\x19\x23')
  text = text.replace('Œ','\x19\x6A').replace('œ','\x19\x7A')
  text = text.replace('ß','\x19\x7B')

  # Caractères spéciaux
  text = text.replace('¼','\x19\x3C').replace('½','\x19\x3D').replace('¾','\x19\x3E')
  text = text.replace('←','\x19\x2C').replace('↑','\x19\x2D').replace('→','\x19\x2E').replace('↓','\x19\x2F')
  text = text.replace('̶','\x60')
  text = text.replace('|','\x7C')

  # Caractères accentués inexistants sur Minitel
  text = text.replace('À','A').replace('Â','A').replace('Ä','A')
  text = text.replace('È','E').replace('É','E').replace('Ê','E').replace('Ë','E')
  text = text.replace('Ï','I').replace('Î','I')
  text = text.replace('Ô','O').replace('Ö','O')
  text = text.replace('Ù','U').replace('Û','U').replace('Ü','U')
  text = text.replace('Ç','C')

  return(text)
