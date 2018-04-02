#!/usr/bin/env python3

# ré-écritude en python3 de Cristel/Dragster !
# (C) 1984-2017 Christian Quest / A-GPL

import time
import websockets


class Pynitel:
    "Classe de gestion des entrée/sortie vidéotex avec un Minitel"

    def __init__(self, conn):
        self.ecrans = {'last': None}
        self.conn = conn
        self.lastkey = 0
        self.lastscreen = ''
        self.laststar = False
        self.zones = []
        self.zonenumber = 0

        # constantes de couleurs
        self.noir = 0
        self.rouge = 1
        self.vert = 2
        self.jaune = 3
        self.bleu = 4
        self.magenta = 5
        self.cyan = 6
        self.blanc = 7

        # constantes des touches de fonction du Minitel
        # en mode Vidéotex ou Mixte
        self.envoi = 1
        self.retour = 2
        self.repetition = 3
        self.guide = 4
        self.annulation = 5
        self.sommaire = 6
        self.correction = 7
        self.suite = 8
        self.connexionfin = 9

        # constantes des séquences protocole
        self.PRO1 = '\x1b\x39'
        self.PRO2 = '\x1b\x3a'
        self.PRO3 = '\x1b\x3b'

    async def wait(self):
        "Attente d'une connexion"

        print('ATTENTE')

        # ESC reçu... on considère qu'on est connecté
        while self.conn.read(1) != b' ':
            time.sleep(1)

        print('CONNECTION')

    async def end(self):
        "Fin de connexion, raccrochage"
        self.conn.write(b'\x1b9g')

    async def _if(self):
        "Dernier caractère reçu"
        data = self.conn.read(1)
        if not data:
            return None
        else:
            return data

    def clear(self):
        "Efface le buffer de réception"
        self.conn.settimeout(0)  # timeout de 2 minutes pour les saisies...
        self.conn.recv(10000)

    async def home(self):
        "Efface écran et ligne 0"
        await self._del(0, 1)
        await self.sendchr(12)  # FF
        await self.cursor(False)  # Coff

    async def vtab(self, ligne):
        "Positionne le curseur sur un début de ligne"
        await self.pos(ligne, 1)

    async def pos(self, ligne, colonne=1):
        "Positionne le curseur sur une ligne / colonne"
        if ligne == 1 and colonne == 1:
            await self.sendchr(30)
        else:
            await self.sendchr(31)
            await self.sendchr(64+ligne)
            await self.sendchr(64+colonne)

    async def _del(self, ligne, colonne):
        "Effacement jusque fin de ligne"
        await self.pos(ligne, colonne)
        await self.sendchr(24)

    async def normal(self):
        "Passage en vidéo normale"
        await self.sendesc('I')

    async def backcolor(self, couleur):
        """Change la couleur de fond,
        à valider par un espace pour le texte (identique à HCOLOR)"""
        await self.sendesc(chr(80+couleur))

    async def canblock(self, debut, fin, colonne, inverse=False):
        """Efface un rectangle sur l'écran,
        compris entre deux lignes et après une colonne"""
        if inverse is False:
            await self.pos(debut, colonne)
            await self.sendchr(24)
            for ligne in range(debut, fin):
                await self.sendchr(10)
                await self.sendchr(24)
        else:
            await self.pos(fin, colonne)
            await self.sendchr(24)
            for ligne in range(debut, fin):
                await self.sendchr(11)
                await self.sendchr(24)

    async def caneol(self, ligne, colonne):
        "Efface la fin de ligne derrière la colonne spécifiée"
        await self.pos(ligne, colonne)
        await self.sendchr(24)  # CAN

    async def cls(self):
        "Efface l'écran du Minitel"
        await self.home()

    async def color(self, couleur):
        "Change la couleur du texte ou graphique"
        await self.sendesc(chr(64+couleur))

    # curpos - donne la position actuelle du curseur du Minitel
    async def cursor(self, visible):
        "Permet de rendre apparent ou invisible le curseur clignotant"
        if visible == 1 or visible is True:
            await self.sendchr(17)  # Con
        else:
            await self.sendchr(20)  # Coff

    # dial - appel un numéro de téléphone
    async def draw(self, num=0):
        "Envoi un écran préchargé dans un buffer vers le minitel"
        if num is None:
            num = self.ecrans['last']
        self.ecrans['last'] = num
        if num is not None:
            await self.conn.write(self.ecrans[num])

    async def drawscreen(self, fichier):
        "Envoi du contenu d'un fichier"
        with open(fichier, 'rb') as f:
            await self.conn.write(f.read())

    async def flash(self, clignote=True):
        "Passage en clignotant"
        if clignote is None or clignote is True or clignote == 1:
            await self.sendesc('\x48')
        else:
            await self.sendesc('\x49')

    async def forecolor(self, couleur):
        "Change la couleur des caractères"
        await self.color(couleur)

    async def get(self):
        "Rend le contenu du buffer de saisie actuel"
        return(await self.conn.read(self.conn.in_waiting))

    # getid - lecture ROM/RAM Minitel
    async def getid(self):
        print("getid: non implémenté...")
        return

    async def hcolor(self, couleur):
        "Change la couleur de fond, à valider par un espace pour le texte"
        await self.sendesc(chr(80+couleur))

    async def input(self, ligne, colonne, longueur, data='',
                    caractere='.', redraw=True):
        "Gestion de zone de saisie"
        # affichage initial
        if redraw:
            await self.sendchr(20)  # Coff
            await self.pos(ligne, colonne)
            await self._print(data)
            await self.plot(caractere, longueur-len(data))
        await self.pos(ligne, colonne+len(data))
        await self.sendchr(17)  # Con

        while True:
            c = await self.conn.read(1)
            if c == '':
                continue
            elif c == b'\x0d':  # CR -> ENVOI
                self.lastkey = self.envoi
                return(data, self.envoi)
            elif c == b'\x13':  # SEP donc touche Minitel...
                c = await self.conn.read(1)

                if c == b'\x45' and data != '':  # annulation
                    data = ''
                    await self.sendchr(20)  # Coff
                    await self.pos(ligne, colonne)
                    await self._print(data)
                    await self.plot(caractere, longueur-len(data))
                    await self.pos(ligne, colonne)
                    await self.sendchr(17)  # Con
                elif c == b'\x47' and data != '':  # correction
                    await self.send(chr(8)+caractere+chr(8))
                    data = data[:len(data)-1]
                else:
                    self.lastkey = ord(c)-64
                    self.laststar = (data != '' and data[:-1] == '*')
                    return(data, ord(c)-64)
            elif c == b'\x1b':  # filtrage des acquittements protocole...
                c = c + await self.conn.read(1)
                if c == self.PRO1:
                    await self.conn.read(1)
                elif c == self.PRO2:
                    await self.conn.read(2)
                elif c == self.PRO3:
                    await self.conn.read(3)
            elif c >= b' ' and len(data) >= longueur:
                await self.bip()
            elif c >= b' ':
                data = data + c.decode()
                await self.send(c.decode())  # écho

    async def inverse(self, inverse=1):
        "Passage en inverse"
        if inverse is None or inverse == 1 or inverse is True:
            await self.sendesc('\x5D')
        else:
            await self.sendesc('\x5C')

    async def locate(self, ligne, colonne):
        "Positionne le curseur"
        await self.pos(ligne, colonne)

    # lower - clavier en mode minuscule / majuscule (mode "Enseignement")
    async def lower(self, islower=True):
        if islower or islower == 1:
            await self.send(self.PRO2+'\x69\x45')  # passage clavier en minus.
        else:
            await self.send(self.PRO2+'\x6a\x45')  # retour clavier majuscule

    async def message(self, ligne, colonne, delai, message, bip=False):
        """Affiche un message à une position donnée pendant un temps donné,
        puis l'efface"""
        if bip:
            await self.bip()
        await self.pos(ligne, colonne)
        await self._print(message)
        await self.conn.flush()
        time.sleep(delai)
        await self.pos(ligne, colonne)
        await self.plot(' ', len(message))

    async def printscreen(self, fichier):
        await self.drawscreen(fichier)

    def resetzones(self):
        while len(self.zones) > 0:
            self.zones.pop()

    # scroll - Active ou désactive le mode "rouleau"

    def starflag(self):
        """Indique si la dernière saisie s'est terminée par une étoile
        + touche de fonction"""
        return(self.laststar)

    # status - Etat du modem

    # swmodem - Retournement du modem

    # sysparm - Paramètres du modem

    async def underline(self, souligne=True):
        "Passe en mode souligné ou normal"
        if souligne is None or souligne is True or souligne == 1:
            await self.sendesc(chr(90))
        else:
            await self.sendesc(chr(89))

    async def waitzones(self, zone):
        "Gestion de zones de saisie"
        if len(self.zones) == 0:
            return (0, 0)

        zone = -zone

        while True:
            # affichage initial
            if zone <= 0:
                await self.cursor(False)
                for z in self.zones:
                    await self.pos(z['ligne'], z['colonne'])
                    if z['couleur'] != self.blanc:
                        await self.forecolor(z['couleur'])
                    await self._print(z['texte'])
                if zone < 0:
                    zone = -zone

            # gestion de la zone de saisie courante
            (self.zones[zone-1]['texte'], touche) = await self.input(self.zones[zone-1]['ligne'],  # noqa
                self.zones[zone-1]['colonne'], self.zones[zone-1]['longueur'],
                data=self.zones[zone-1]['texte'], caractere='.', redraw=False)

            # gestion des SUITE / RETOUR
            if touche == self.suite:
                if zone < len(self.zones):
                    zone = zone+1
                else:
                    zone = 1
            elif touche == self.retour:
                if zone > 1:
                    zone = zone-1
                else:
                    zone = len(self.zones)
            else:
                self.zonenumber = zone
                await self.cursor(False)
                return(zone, touche)

    # waitconnect - attente de CONNECTION

    def zone(self, ligne, colonne, longueur, texte, couleur):
        "Déclaration d'une zone de saisie"
        self.zones.append({"ligne": ligne, "colonne": colonne,
                           "longueur": longueur, "texte": texte,
                           "couleur": couleur})

    def key(self):
        "Dernière touche de fonction utilisée sur le Minitel lors d'une saisie"
        return self.lastkey

    async def scale(self, taille):
        "Change la taille du texte"
        await self.sendesc(chr(76+taille))

    async def notrace(self):
        "Passe en texte souligné, à valider par un espace"
        await self.sendesc(chr(89))

    async def trace(self):
        "Fin de texte souligné, à valider par un espace"
        await self.sendesc(chr(90))

    async def plot(self, car, nombre):
        "Affichage répété d'un caractère"
        if nombre > 1:
            await self._print(car)
        if nombre == 2:
            await self._print(car)
        elif nombre > 2:
            while nombre > 63:
                await self.sendchr(18)
                await self.sendchr(64+63)
                nombre = nombre-63
            await self.sendchr(18)
            await self.sendchr(64+nombre-1)

    async def text(self):
        "Mode texte"
        await self.sendchr(15)

    async def gr(self):
        "Mode graphique"
        await self.sendchr(14)

    async def step(self, scroll):
        "Active ou désactive le mode scrolling"
        await self.sendesc(':')
        await self.sendchr(ord('j')-scroll)
        await self.send('C')

    async def xdraw(self, fichier):
        "Envoi du contenu d'un fichier"
        with open(fichier, 'rb') as f:
            await self.conn.write(f.read())

    def load(self, num, fichier):
        "Charge un fichier vidéotex dans un buffer"
        with open(fichier, 'rb') as f:
            data = f.read()
            self.ecrans[num] = data

    def read(self):
        "Lecture de la date et heure"
        print('read: non implémenté')

    async def _print(self, texte):
        await self.send(self.accents(texte))

    async def send(self, text):
        "Envoi de données vers le minitel"
        if self.conn is not None:
            await self.conn.write(text.encode())
        else:
            print('conn = None')

    async def sendchr(self, ascii):
        await self.send(chr(ascii))

    async def sendesc(self, text):
        await self.sendchr(27)
        await self.send(text)

    async def bip(self):
        await self.sendchr(7)

    def accents(self, text):
        "Conversion des caractères accentués (cf STUM p 103)"
        text = text.replace('à', '\x19\x41a')
        text = text.replace('â', '\x19\x43a')
        text = text.replace('ä', '\x19\x48a')
        text = text.replace('è', '\x19\x41e')
        text = text.replace('é', '\x19\x42e')
        text = text.replace('ê', '\x19\x43e')
        text = text.replace('ë', '\x19\x48e')
        text = text.replace('î', '\x19\x43i')
        text = text.replace('ï', '\x19\x48i')
        text = text.replace('ô', '\x19\x43o')
        text = text.replace('ö', '\x19\x48o')
        text = text.replace('ù', '\x19\x43u')
        text = text.replace('û', '\x19\x43u')
        text = text.replace('ü', '\x19\x48u')
        text = text.replace('ç', '\x19\x4Bc')
        text = text.replace('°', '\x19\x30')
        text = text.replace('£', '\x19\x23')
        text = text.replace('Œ', '\x19\x6A').replace('œ', '\x19\x7A')
        text = text.replace('ß', '\x19\x7B')

        # Caractères spéciaux
        text = text.replace('¼', '\x19\x3C')
        text = text.replace('½', '\x19\x3D')
        text = text.replace('¾', '\x19\x3E')
        text = text.replace('←', '\x19\x2C')
        text = text.replace('↑', '\x19\x2D')
        text = text.replace('→', '\x19\x2E')
        text = text.replace('↓', '\x19\x2F')
        text = text.replace('̶', '\x60')
        text = text.replace('|', '\x7C')

        # Caractères accentués inexistants sur Minitel
        text = text.replace('À', 'A').replace('Â', 'A').replace('Ä', 'A')
        text = text.replace('È', 'E').replace('É', 'E')
        text = text.replace('Ê', 'E').replace('Ë', 'E')
        text = text.replace('Ï', 'I').replace('Î', 'I')
        text = text.replace('Ô', 'O').replace('Ö', 'O')
        text = text.replace('Ù', 'U').replace('Û', 'U').replace('Ü', 'U')
        text = text.replace('Ç', 'C')

        return(text)


class PynitelWS:
    def __init__(self, websocket):
        self.ws = websocket
        self.buffer = ''

    async def write(self, data):
        await self.ws.send(data.decode())

    async def read(self, maxlen=1):
        if len(self.buffer) < maxlen:
            data = await self.ws.recv()
            self.buffer = self.buffer + data
        if len(self.buffer) >= maxlen:
            data = self.buffer[:maxlen]
            self.buffer = self.buffer[maxlen:]
        else:
            data = ''
        return data.encode()

    def in_waiting(self):
        return

    def settimeout(self, timeout):
        return

    async def flush(self):
        return
