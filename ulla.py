#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import pynitel
import sys
import json
from mastodon import Mastodon
import os
import time

def init():
    "Initialisation du serveur vidéotex"
    minitel = pynitel.Pynitel(serial.Serial('/dev/ttyUSB0', 4800, parity=serial.PARITY_EVEN, bytesize=7, timeout=2))
    return(minitel)

def connexion(minitel, login='', passe=''):
    "Ecran d'accueil et d'identification"
    minitel.resetzones()
    minitel.zone(16, 2, 30, login, minitel.blanc)
    touche = minitel.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA')

        # gestion de la zone de saisie courante
        (zone, touche) = minitel.waitzones(zone)

        if touche != minitel.repetition:
            break

    login = minitel.zones[0]['texte'].strip()
    if login[0] == '@':
        login = login[1:]

    if login != '' and touche == minitel.envoi and passe == '':
        minitel.pos(0,1)
        minitel._print("Passe:")
        (passe,touche) = minitel.input(0, 7, 30, data='')

    return (login, passe)


def mastodon_login(login, passe):
    "Connexion à l'instance mastodon, retourne un objet api mastodon"
    instance = login.split('@')[1]

    # Create application if it does not exist
    if not os.path.isfile(instance+'.secret'):
        if Mastodon.create_app(
            'minitel',
            api_base_url='https://'+instance,
            to_file = instance+'.secret'
        ):
            print('minitel app created on instance '+instance)
        else:
            print('failed to create app on instance '+instance)
            sys.exit(1)

    try:
        mastodon = Mastodon(
          client_id=instance+'.secret',
          api_base_url='https://'+instance
        )
        mastodon.log_in(
            username=login,
            password=passe,
            scopes=['read', 'write'],
            to_file=login+".secret"
        )
    except:
        print("ERROR: First Login Failed!", login, passe)
        sys.exit(1)

    return(mastodon)


def strformat(left='',right='',fill=' ',width=40):
    " formattage de texte "
    total = width-len(left+right)
    if total > 0 :
        out = left + fill * total + right
    else:
        out = left+center+right
    return(out)


def print_acct(minitel, acct):
    "affiche un login mastodon en couleur"
    minitel.forecolor(minitel.blanc)
    if '@' in acct:
        minitel._print(acct.split('@')[0])
        minitel.forecolor(minitel.bleu)
        minitel._print('@')
        minitel.forecolor(minitel.vert)
        minitel._print(acct.split('@')[1])
    else:
        minitel._print(acct)


def ulla_sommaire(minitel, login, mastodon):
    "Sommaire général"
    touche = minitel.repetition
    zone = 1

    while True:
        minitel.resetzones()
        choix = ''
        minitel.zone(24, 31, 2, choix, minitel.blanc)
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.SOM')

            home = mastodon.timeline_home()
            minitel.pos(21)

            if len(home)>0:
                minitel._print(str(len(home)))
                minitel.forecolor(minitel.vert)
                if len(home)>1:
                    minitel._print(" messages reçus")
                else:
                    minitel._print(" message reçu")
                print(home[1])
                minitel.forecolor(minitel.vert)
                minitel._print(", dernier de :")
                minitel.pos(22)
                print_acct(minitel, home[1]['account']['acct'])
            else:
                minitel._print("aucun message reçu")

        # gestion de la zone de saisie courante
        (zone, touche) = minitel.waitzones(zone)
        choix = minitel.zones[0]['texte'].strip()

        if choix < '1' or choix > '7':
            minitel.message(0, 1, 2, "Choix entre 1 et 7", bip=True)
        elif choix == '4':
            minitel.message(0, 1, 2, "Horoscope indisponible", bip=True)
        elif choix == '5':
            minitel.message(0, 1, 2, "SMS indisponible", bip=True)
        elif choix == '6':
            minitel.message(0, 1, 2, "emails bientôt disponibles !", bip=True)
        elif touche != minitel.repetition:
            break

    return (choix)


def ulla_dialogue_liste(minitel, login, mastodon):
    "Dialogue"
    touche = minitel.repetition
    zone = 1
    page = 1

    while True:
        me = mastodon.account_search(login)
        follow = mastodon.account_following(me[0]['id'])

        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.LISTE')

        minitel.resetzones()
        choix = ''
        minitel.zone(23, 2, 3, choix, minitel.blanc)
        # affichage initial ou répétition


        for f in range(1,len(follow)):
            minitel.pos(3+f)
            minitel._print(strformat(right=str(f),width=3)+" ")
            print_acct(minitel, follow[f-1]['acct'])
            if f>15:
                break

        # gestion de la zone de saisie courante
        (zone, touche) = minitel.waitzones(zone)
        choix = minitel.zones[0]['texte'].strip()

        if choix == 'R' and touche == minitel.envoi:
            minitel.message(0, 1, 2, "Liste régionale indisponible", bip=True)
        elif choix == 'G' and touche == minitel.envoi:
            minitel.message(0, 1, 2, "Guide bientôt disponible", bip=True)
        elif choix == 'P' and touche == minitel.envoi: # changer de pseudo
            return('RAZ','')
        elif choix !='' and int(choix) >= 1 and int(choix)<=len(follow):
            if touche == minitel.envoi:
                return('MSG',follow[int(choix)-1]['acct'])
            if touche == minitel.guide:
                return('INF',follow[int(choix)-1]['acct'])
        elif touche != minitel.repetition:
            break

    return('','')


def ulla_message_envoi(minitel, login, mastodon, qui):
    "Envoi d'un message"
    touche = minitel.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.NEWMSG')
            minitel.pos(2)
            if '@' in qui:
                minitel._print(qui.split('@')[0])
                minitel.forecolor(minitel.vert)
                minitel._print("@"+(qui.split('@')[1]))
            else:
                minitel._print(qui)

        minitel.resetzones()
        msg = ''
        minitel.zone(4, 1, 240, msg, minitel.blanc)

        # gestion de la zone de saisie courante
        (zone, touche) = minitel.waitzones(zone)
        msg = minitel.zones[0]['texte'].strip()

        if touche == minitel.envoi:
            toot = mastodon.status_post(qui + " " + msg, visibility='direct')
            print(toot)
            if toot is not None:
                minitel.message(0, 1, 2, "Message envoyé")
                return('')

        if touche != minitel.repetition:
            break

    return('') # retour sommaire général


def ulla():
    minitel = init()
    minitel._print(minitel.PRO2+'\x69\x45') # passage clavier en minuscules

    login = sys.argv[1] if (len(sys.argv)>1) else ''
    passe = sys.argv[2] if (len(sys.argv)>2) else ''

    if login == '' or passe == '':
        (login,passe) = connexion(minitel, login, passe)
    mastodon = mastodon_login(login, passe)

    # affiche la version de l'instance mastodon distante
    minitel.caneol(0,1)
    minitel._print("Mastodon v"+mastodon.retrieve_mastodon_version())

    rubrique = ''
    qui = ''
    while True:
        if rubrique == 'DIA':
            (rubrique,qui) = ulla_dialogue_liste(minitel, login, mastodon)

        elif rubrique == 'RAZ': # changer de pseudo > reconnexion mastodon
            (login,passe) = connexion(minitel, '', '')
            rubrique = ''

        elif rubrique == 'MSG': # changer de pseudo > reconnexion mastodon
            rubrique = ulla_message_envoi(minitel, login, mastodon, qui)

        else:
            if rubrique != '':
                minitel.message(0, 1, 2, "Désolé, pas encore implémenté", bip=True)
                print(rubrique,"pas implémenté")

            choix = ulla_sommaire(minitel, login, mastodon)
            if choix == '1':
                rubrique = 'DIA'
            elif choix == '2':
                rubrique = 'ANN'
            elif choix == '3':
                rubrique = 'BAL'
            elif choix == '3':
                rubrique = 'BAL'
            elif choix == '7':
                rubrique = 'MSG'
                qui = 'cquest@amicale.net'


if __name__ == '__main__':
    ulla()
