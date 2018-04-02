#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import websockets
import pynitel
import sys
from mastodon import Mastodon
import os
import re


async def connexion(m, login='', passe=''):
    "Ecran d'accueil et d'identification"
    m.resetzones()
    m.zone(16, 2, 30, login, m.blanc)
    touche = m.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA')

        # gestion de la zone de saisie courante
        (zone, touche) = await m.waitzones(zone)

        if touche != m.repetition:
            break

    if touche == m.envoi:
        login = m.zones[0]['texte'].strip()
        if login:
            if login[0] == '@':
                login = login[1:]

            if passe == '':
                await m.pos(0, 1)
                await m._print("Passe:")
                (passe, touche) = await m.input(0, 7, 30, data='')

    return (login, passe, touche)


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


async def print_acct(m, acct):
    "affiche un login mastodon en couleur"
    print(acct)
    await m.forecolor(m.blanc)
    if '@' in acct:
        await m._print(acct.split('@')[0])
        await m.forecolor(m.bleu)
        await m._print('@')
        await m.forecolor(m.vert)
        await m._print(acct.split('@')[1])
    else:
        await m._print(acct)


async def ulla_sommaire(m, login, mastodon):
    "Sommaire général"
    touche = m.repetition
    zone = 1

    while True:
        m.resetzones()
        choix = ''
        m.zone(24, 31, 2, choix, m.blanc)
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA.SOM')

            home = mastodon.timeline_home(limit=9999)
            await m.pos(21)

            if len(home) > 0:
                if '_pagination_next' in home[-1]:
                    await m._print("plus de ")
                await m._print(str(len(home)))
                await m.forecolor(m.vert)
                if len(home) > 1:
                    await m._print(" messages reçus")
                else:
                    await m._print(" message reçu")
                await m.forecolor(m.vert)
                await m._print(", dernier de :")
                await m.pos(22)
                await print_acct(m, home[1]['account']['acct'])
            else:
                await m._print("aucun message reçu")

        # gestion de la zone de saisie courante
        (zone, touche) = await m.waitzones(zone)
        choix = m.zones[0]['texte'].strip()

        if touche == m.envoi:
            if choix < '1' or choix > '7':
                await m.message(0, 1, 2, "Choix entre 1 et 7", bip=True)
            elif choix == '4':
                await m.message(0, 1, 2, "Horoscope indisponible", bip=True)
            elif choix == '5':
                await m.message(0, 1, 2, "SMS indisponible", bip=True)
            elif choix == '6':
                await m.message(0, 1, 2, "emails bientôt disponibles !",
                                bip=True)
        elif touche != m.repetition:
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


async def ulla_dialogue_liste(m, login, mastodon):
    "Dialogue"
    touche = m.repetition
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
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA.LISTE')
            await m.caneol(3, 21)
            await m.canblock(4, 19, 1)
            page = -abs(page)
        else:
            await m.cursor(False)
            await m.canblock(4, 19, 1)

        if page < 0:
            page = abs(page)
            pages = round((len(follow)+lignes-1)/lignes)
            await m.pos(3, 21)
            await m._print(strformat(left="%s/%s" % (page, pages), width=10))
            for ligne in range(1, lignes+1):
                await m.pos(3+ligne)
                await m.forecolor(m.cyan)
                debut = (page-1)*lignes
                await m._print(strformat(right=str(debut+ligne), width=3))
                await m.forecolor(m.bleu)
                await m._print("←" if 'follower' in follow[debut+ligne-1] else '̶')  # noqa
                await m._print("→" if 'following' in follow[debut+ligne-1] else '̶')  # noqa
                print_acct(m, follow[debut+ligne-1]['acct'])
                if debut+ligne == len(follow):
                    break

        # gestion de la zone de saisie courante
        choix = ''
        (choix, touche) = await m.input(23, 2, 3)

        if choix == 'R' and touche == m.envoi:
            await m.message(0, 1, 2, "Liste régionale indisponible", bip=True)
        elif choix == 'G' and touche == m.envoi:
            await m.message(0, 1, 2, "Guide bientôt disponible", bip=True)
        elif choix == 'P' and touche == m.envoi:  # changer de pseudo
            return('RAZ', '')
        elif choix != '' and int(choix) >= 1 and int(choix) <= len(follow):
            if touche == m.suite:
                await ulla_message_affiche(m, login, mastodon,
                                           follow[int(choix)-1]['acct'])
                touche = m.repetition
            if touche == m.envoi:
                return('MSG', follow[int(choix)-1]['acct'])
            if touche == m.guide:
                # return('INF',follow[int(choix)-1]['acct'])
                await ulla_portrait(m, login, mastodon,
                                    follow[int(choix)-1]['acct'])
                touche = m.repetition
        elif touche == m.suite:
            page = -(page+1)
        elif touche == m.retour:
            if page > 1:
                page = -(page-1)
            else:
                await m.bip()
        elif touche != m.repetition:
            break

    return('', '')


async def ulla_portrait(m, login, mastodon, qui):
    "Affiche un portrait"
    touche = m.repetition

    while True:
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA.ANNONCE')
            await m.pos(3)
            if '@' in qui:
                await m._print(qui.split('@')[0])
                await m.forecolor(m.vert)
                await m._print("@"+(qui.split('@')[1]))
            else:
                await m._print(qui)

        portrait = mastodon.account_search(qui)[0]
        print(portrait)
        await m.pos(5)
        item = "%s → %s #msg=%s → %s" % (portrait['followers_count'],
                                         portrait['display_name'],
                                         portrait['statuses_count'],
                                         portrait['following_count'])
        note = re.sub('<.*?>', '', re.sub('<(p|br)>', '\x0d\x0a',
                                          portrait['note']))
        await m._print(item + '\x0d\x0a' + note)
        await m.pos(20, 31)
        await m._print(str(portrait['created_at'])[:10])

        (choix, touche) = await m.input(24, 1, 0)

        if touche == m.envoi:
            ulla_message_envoi(m, login, mastodon, qui)
            return('', '')
        if touche == m.retour:
            return('', '')
        if touche != m.repetition:
            break

    return('', '')  # retour sommaire général


async def ulla_message_envoi(m, login, mastodon, qui):
    "Envoi d'un message"
    touche = m.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA.NEWMSG')
            await m.pos(2)
            if '@' in qui:
                await m._print(qui.split('@')[0])
                await m.forecolor(m.vert)
                await m._print("@"+(qui.split('@')[1]))
            else:
                await m._print(qui)

        m.resetzones()
        msg = ''
        m.zone(4, 1, 240, msg, m.blanc)

        # gestion de la zone de saisie courante
        (zone, touche) = await m.waitzones(zone)
        msg = m.zones[0]['texte'].strip()

        if touche == m.envoi:
            toot = mastodon.status_post("@"+qui + " " + msg,
                                        visibility='direct')
            if toot is not None:
                await m.message(0, 1, 2, "Message envoyé")
                return('')

        if touche != m.repetition:
            break

    return('')  # retour sommaire général


async def ulla_message_affiche(m, login, mastodon, qui):
    "Affiche un message"
    touche = m.repetition

    if qui != '':
        statuses = mastodon.account_statuses(mastodon.account_search(qui)[0]['id'])  # noqa
    else:
        statuses = mastodon.timeline_home(limit=9999)

    courant = 0

    while True:
        status = statuses[courant]
        qui = status['account']['acct']
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.drawscreen('ecrans/ulla/E.ULLA.REPONSE')
            await m.pos(2)
            if '@' in qui:
                await m._print(qui.split('@')[0])
                await m.forecolor(m.vert)
                await m._print("@"+(qui.split('@')[1]))
            else:
                await m._print(qui)

            await m.pos(4)
            await m._print(re.sub('<.*?>', '',
                                  re.sub('<(p|br)>', ' ',
                                         status['content'])).strip()[:240])

            if ('in_reply_to_id' in status and
                status['in_reply_to_id'] is not None):
                    reply_to = mastodon.status(status['in_reply_to_id'])
                    await m.pos(18)
                    await m._print(re.sub('<.*?>', '',
                                          re.sub('<(p|br)>', ' ',
                                                 reply_to['content'])).strip()[:240])  # noqa
            else:
                reply_to = None

        (msg, touche) = await m.input(11, 1, 240, data='',
                                      caractere='.', redraw=True)

        if msg != '' and touche == m.envoi:
            toot = mastodon.status_post("@"+qui + " " + msg,
                                        in_reply_to_id=status['id'],
                                        visibility='direct')
            print(toot)
            if toot is not None:
                await m.message(0, 1, 2, "Message envoyé")
            return('', '')

        elif touche == m.suite:
            if courant < len(statuses)-1:
                courant = courant+1
                touche = m.repetition
            else:
                await m.message(0, 1, 2, "Fin des messages", bip=True)
        elif touche == m.retour:
            if courant > 0:
                courant = courant-1
                touche = m.repetition
            else:
                await m.message(0, 1, 2, "Début des messages", bip=True)
        elif touche != m.repetition:
            break

    return('', '')  # retour sommaire général


async def ulla_teletel(m):
    await m._print(m.PRO2+'\x69\x45')  # passage clavier en minuscules
    (login, passe, touche) = await connexion(m)
    if touche == m.envoi:
        mastodon = mastodon_login(login, passe)

        # affiche la version de l'instance mastodon distante
        await m.caneol(0, 1)
        await m._print("Mastodon v"+mastodon.retrieve_mastodon_version())

        rubrique = ''
        qui = ''

    while touche not in [m.sommaire, m.connexionfin]:
        if rubrique == 'DIA':
            (rubrique, qui) = await ulla_dialogue_liste(m,
                                                        login, mastodon)

        if rubrique == 'ANN':
            (rubrique, qui) = await ulla_message_affiche(m, login,
                                                         mastodon, '')

        elif rubrique == 'RAZ':  # changer de pseudo > reconnexion mastodon
            (login, passe) = await connexion(m, '', '')
            rubrique = ''

        elif rubrique == 'MSG':  # changer de pseudo > reconnexion mastodon
            rubrique = await ulla_message_envoi(m, login, mastodon, qui)

        else:
            if rubrique != '':
                await m.message(0, 1, 2,
                                "Désolé, pas encore implémenté", bip=True)
                print(rubrique, "pas implémenté")

            choix = await ulla_sommaire(m, login, mastodon)
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


async def ulla(websocket, path):
    m = pynitel.Pynitel(pynitel.PynitelWS(websocket))
    await ulla_teletel(m)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(ulla, 'localhost', 3611))
    loop.run_forever()
