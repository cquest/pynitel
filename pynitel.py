# ré-écritude en python3 de Cristel !
# (C) 1984-2017 Christian Quest / A-GPL

import serial
import time

ecrans = {'last': None}
conn = None
inbuf = b''

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

def input(ligne, colonne, longueur, caractere = '.', data=''):
  "Gestion de zone de saisie"
  texte = ''
  # affichage initial
  pos(ligne, colonne)
  _print(data)
  plot(caractere,longueur-len(data))
  pos(ligne, colonne+len(data))

  while True:
      c = conn.read(1).decode()
      if c == '':
          continue
      elif c>=' ' and len(data)>=longueur:
          bip()
      elif c>=' ' :
          data = data + c
      elif c == '\x13': #SEP donc touche Minitel...
        c = conn.read(1).decode()

        if c == '\x45': # annulation
            if data == '':
                bip()
            else:
                data = ''
                pos(ligne, colonne)
                _print(data)
                plot(caractere,longueur-len(data))
                pos(ligne, colonne)


        elif c == '\x47': # correction
            if data != '':
                send(chr(8)+caractere+chr(8))
                data = data[:len(data)-1]
            else:
                bip()
        else:
            return(data,ord(c)-64)

def _print(text):
  "Envoi de texte vers le minitel"
  send(accents(text))

def home():
  "Efface écran et ligne 0"
  _del(0,1)
  sendchr(12) # FF
  sendchr(20) # Coff

def vtab(ligne):
  "Positionne le curseur sur un début de ligne"
  pos(ligne,1)

def pos(ligne, colonne):
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
  sendesc('\\')

def flash():
  "Passage en clignotant"
  sendesc('H')

def hcolor(couleur):
  "Change la couleur de fond, à valider par un espace pour le texte"
  sendesc(chr(80+couleur))

def color(couleur):
  "Change la couleur du texte ou graphique"
  sendesc(chr(64+couleur))

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
  _print(car)
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

def draw(num):
  "Envoi un écran préchargé dans un buffer vers le minitel"
  if num is None:
    num = ecrans['last']
  ecrans['last']=num
  if num is not None:
    conn.write(ecrans[num])

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
