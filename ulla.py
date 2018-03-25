#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import pynitel
import sys
from mastodon import Mastodon
import os
import re


def init():
    "Initialisation du serveur vidéotex"
    minitel = pynitel.Pynitel(serial.Serial('/dev/ttyUSB0', 1200,
                                            parity=serial.PARITY_EVEN,
                                            bytesize=7, timeout=2))
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
        minitel.pos(0, 1)
        minitel._print("Passe:")
        (passe, touche) = minitel.input(0, 7, 30, data='')

    return (login, passe)


def mastodon_login(login, passe):
    "Connexion à l'instance mastodon, retourne un objet api mastodon"
    instance = login.split('@')[1]

    # Create application if it does not exist
    if not os.path.isfile(instance+'.secret'):
        if Mastodon.create_app(
            'minitel',
            api_base_url='https://'+instance,
            to_file=instance+'.secret'
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


def strformat(left='', center='', right='', fill=' ', width=40):
    " formattage de texte "
    total = width-len(left+center+right)
    if total > 0:
        out = left + fill * total + right
    else:
        out = left+center+right
    return(out[:width])


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

            home = mastodon.timeline_home(limit=9999)
            minitel.pos(21)

            if len(home) > 0:
                if '_pagination_next' in home[-1]:
                    minitel._print("plus de ")
                minitel._print(str(len(home)))
                minitel.forecolor(minitel.vert)
                if len(home) > 1:
                    minitel._print(" messages reçus")
                else:
                    minitel._print(" message reçu")
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


def mastodon_all_follow(mastodon, me, following=True):
    "Récupère la liste des comptes suivis ou qui nous suivent"
    if following:
        follow = mastodon.account_following(me[0]['id'], limit=9999)
    else:
        follow = mastodon.account_followers(me[0]['id'], limit=9999)
    while '_pagination_next' in follow[len(follow)-1]:
        more = mastodon.fetch_next(follow[len(follow)-1]['_pagination_next'])
        for f in more:
            follow.append(f)
    return(follow)


def ulla_dialogue_liste(minitel, login, mastodon):
    "Dialogue"
    touche = minitel.repetition
    page = 1
    lignes = 16

    me = mastodon.account_search(login)
    follow = mastodon_all_follow(mastodon, me)
    followers = mastodon_all_follow(mastodon, me, following=False)
    # on cherche les followers qu'on suit
    for f1 in follow:
        f1['following'] = True
        for f2 in followers:
            if f1['acct'] == f2['acct']:
                followers.remove(f2)
                f1['follower'] = True
                print(f1['acct'], len(followers))
                break
    # on ajoute les followers à la liste globale
    for f2 in followers:
        f2['follower'] = True
        follow.append(f2)

    while True:
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.LISTE')
            minitel.caneol(3, 21)
            minitel.canblock(4, 19, 1)
            page = -abs(page)
        else:
            minitel.cursor(False)
            minitel.canblock(4, 19, 1)

        if page < 0:
            page = abs(page)
            pages = round((len(follow)+lignes-1)/lignes)
            minitel.pos(3, 21)
            minitel._print(strformat(left="%s/%s" % (page, pages), width=10))
            for ligne in range(1, lignes+1):
                minitel.pos(3+ligne)
                minitel.forecolor(minitel.cyan)
                debut = (page-1)*lignes
                minitel._print(strformat(right=str(debut+ligne), width=3))
                minitel.forecolor(minitel.bleu)
                minitel._print("←" if 'follower' in follow[debut+ligne-1] else '̶')  # noqa
                minitel._print("→" if 'following' in follow[debut+ligne-1] else '̶')  # noqa
                print_acct(minitel, follow[debut+ligne-1]['acct'])
                if debut+ligne == len(follow):
                    break

        # gestion de la zone de saisie courante
        choix = ''
        (choix, touche) = minitel.input(23, 2, 3)

        if choix == 'R' and touche == minitel.envoi:
            minitel.message(0, 1, 2, "Liste régionale indisponible", bip=True)
        elif choix == 'G' and touche == minitel.envoi:
            minitel.message(0, 1, 2, "Guide bientôt disponible", bip=True)
        elif choix == 'P' and touche == minitel.envoi:  # changer de pseudo
            return('RAZ', '')
        elif choix !='' and int(choix) >= 1 and int(choix) <= len(follow):
            if touche == minitel.suite:
                ulla_message_affiche(minitel, login, mastodon,
                                     follow[int(choix)-1]['acct'])
                touche = minitel.repetition
            if touche == minitel.envoi:
                return('MSG', follow[int(choix)-1]['acct'])
            if touche == minitel.guide:
                # return('INF',follow[int(choix)-1]['acct'])
                ulla_portrait(minitel, login, mastodon,
                              follow[int(choix)-1]['acct'])
                touche = minitel.repetition
        elif touche == minitel.suite:
            page = -(page+1)
        elif touche == minitel.retour:
            if page > 1:
                page = -(page-1)
            else:
                minitel.bip()
        elif touche != minitel.repetition:
            break

    return('', '')


def ulla_portrait(minitel, login, mastodon, qui):
    "Affiche un portrait"
    touche = minitel.repetition

    while True:
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.ANNONCE')
            minitel.pos(3)
            if '@' in qui:
                minitel._print(qui.split('@')[0])
                minitel.forecolor(minitel.vert)
                minitel._print("@"+(qui.split('@')[1]))
            else:
                minitel._print(qui)

        portrait = mastodon.account_search(qui)[0]
        print(portrait)
        minitel.pos(5)
        minitel._print("%s → %s #msg=%s → %s" % (portrait['followers_count'],
                                                 portrait['display_name'],
                                                 portrait['statuses_count'],
                                                 portrait['following_count']) +
                       '\x0d\x0a')
        minitel._print(re.sub('<.*?>', '', re.sub('<(p|br)>', '\x0d\x0a',
                                                  portrait['note'])))
        minitel.pos(20, 31)
        minitel._print(str(portrait['created_at'])[:10])

        (choix, touche) = minitel.input(24, 1, 0)

        if touche == minitel.envoi:
            ulla_message_envoi(minitel, login, mastodon, qui)
            return('', '')
        if touche == minitel.retour:
            return('', '')
        if touche != minitel.repetition:
            break

    return('', '')  # retour sommaire général


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
            toot = mastodon.status_post("@"+qui + " " + msg,
                                        visibility='direct')
            if toot is not None:
                minitel.message(0, 1, 2, "Message envoyé")
                return('')

        if touche != minitel.repetition:
            break

    return('')  # retour sommaire général


def ulla_message_affiche(minitel, login, mastodon, qui):
    "Affiche un message"
    touche = minitel.repetition

    if qui != '':
        statuses = mastodon.account_statuses(mastodon.account_search(qui)[0]['id'])  # noqa
    else:
        statuses = mastodon.timeline_home(limit=9999)

    courant = 0

    while True:
        status = statuses[courant]
        qui = status['account']['acct']
        # affichage initial ou répétition
        if touche == minitel.repetition:
            minitel.home()
            minitel.drawscreen('ecrans/ulla/E.ULLA.REPONSE')
            minitel.pos(2)
            if '@' in qui:
                minitel._print(qui.split('@')[0])
                minitel.forecolor(minitel.vert)
                minitel._print("@"+(qui.split('@')[1]))
            else:
                minitel._print(qui)

            minitel.pos(4)
            minitel._print(re.sub('<.*?>', '',
                                  re.sub('<(p|br)>', ' ',
                                         status['content'])).strip()[:240])

            if ('in_reply_to_id' in status and
                status['in_reply_to_id'] is not None):
                    reply_to = mastodon.status(status['in_reply_to_id'])
                    minitel.pos(18)
                    minitel._print(re.sub('<.*?>', '',
                                          re.sub('<(p|br)>', ' ',
                                                 reply_to['content'])).strip()[:240])
            else:
                reply_to = None

        (msg, touche) = minitel.input(11, 1, 240, data='',
                                      caractere='.', redraw=True)

        if msg != '' and touche == minitel.envoi:
            toot = mastodon.status_post("@"+qui + " " + msg,
                                        in_reply_to_id=status['id'],
                                        visibility='direct')
            print(toot)
            if toot is not None:
                minitel.message(0, 1, 2, "Message envoyé")
            return('', '')

        elif touche == minitel.suite:
            if courant < len(statuses)-1:
                courant = courant+1
                touche = minitel.repetition
            else:
                minitel.message(0, 1, 2, "Fin des messages", bip=True)
        elif touche == minitel.retour:
            if courant > 0:
                courant = courant-1
                touche = minitel.repetition
            else:
                minitel.message(0, 1, 2, "Début des messages", bip=True)
        elif touche != minitel.repetition:
            break

    return('', '')  # retour sommaire général


def ulla():
    minitel = init()
    minitel._print(minitel.PRO2+'\x69\x45')  # passage clavier en minuscules

    login = sys.argv[1] if (len(sys.argv) > 1) else ''
    passe = sys.argv[2] if (len(sys.argv) > 2) else ''

    (login, passe) = connexion(minitel, login, passe)
    mastodon = mastodon_login(login, passe)

    # affiche la version de l'instance mastodon distante
    minitel.caneol(0, 1)
    minitel._print("Mastodon v"+mastodon.retrieve_mastodon_version())

    rubrique = ''
    qui = ''
    while True:
        if rubrique == 'DIA':
            (rubrique, qui) = ulla_dialogue_liste(minitel, login, mastodon)

        if rubrique == 'ANN':
            (rubrique, qui) = ulla_message_affiche(minitel, login,
                                                   mastodon, '')

        elif rubrique == 'RAZ':  # changer de pseudo > reconnexion mastodon
            (login, passe) = connexion(minitel, '', '')
            rubrique = ''

        elif rubrique == 'MSG':  # changer de pseudo > reconnexion mastodon
            rubrique = ulla_message_envoi(minitel, login, mastodon, qui)

        else:
            if rubrique != '':
                minitel.message(0, 1, 2, "Désolé, pas encore implémenté",
                                bip=True)
                print(rubrique, "pas implémenté")

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
