#!/usr/bin/env python3
import asyncio
import websockets
import pynitel
import sys
import os

async def annuaire_saisie(m, quoi, ou):
    "Masque de saisie des critères de recherche"
    # définition des zones
    m.resetzones()
    m.zone(5, 13, 27, quoi, m.blanc)
    m.zone(7, 13, 27, '', m.blanc)
    m.zone(10, 13, 27, ou, m.blanc)
    m.zone(13, 13, 27, '', m.blanc)
    m.zone(14, 13, 27, '', m.blanc)
    m.zone(15, 13, 27, '', m.blanc)
    touche = m.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await m.xdraw('ecrans/E.ANNUAIRE.OPTIM.vtx')

        # gestion de la zone de saisie courante
        (zone, touche) = await m.waitzones(zone)
        # on récupère les quoi et le ou...
        quoi = ("%s %s %s" % (m.zones[0]['texte'], m.zones[1]['texte'],
                              m.zones[5]['texte'])).strip().replace('  ', ' ')
        ou = ("%s %s %s" % (m.zones[4]['texte'], m.zones[3]['texte'],
                            m.zones[2]['texte'])).strip().replace('  ', ' ')

        if (touche == m.sommaire):
            return(touche, '', '')
        if (touche == m.envoi):
            if quoi == '':
                await m.message(0, 1, 3,
                                "Entrez au moins un nom ou une rubrique !")
            else:
                return (touche, quoi, ou)
        elif touche != m.repetition:
            await m.message(0, 1, 3, "Désolé, pas encore disponible")


def strformat(left='', right='', fill=' ', width=40):
    " formattage de texte "
    total = width-len(left+right)
    if total > 0:
        out = left + fill * total + right
    else:
        out = left+right
    return(out)


async def titre(m, titre):
    await m.caneol(0, 1)
    await m.forecolor(m.bleu)
    await m._print(titre+'\x0d')


async def arbo_teletel(m, service):
    """Gestion d'un service arborescent
        Les noms de fichiers définissent l'arborescence: NNNs_[#cle,cle_]nom
        - 'NNN' sont les choix successifs dans les menus
        - 's' (en minuscule) les séquences de pages en SUITE/RETOUR
        - '#cle#cle#' les mots-clé pour accès direct à la page

        Exemple:
        - 0a_accueil.vtx
        - 0b_sommaire.vtx
        - 0b1_choix1.vtx
        - 0b2_choix2.vtx
        - 0b2a_#BUR#_2eme_page_choix2.vtx
        - 0b3b_3eme_page_choix2.vtx
        etc
    """
    # page de démarrage du service
    path = 'services/'+service+'/'
    page = '0'
    pages = os.listdir(path)
    pages.sort()

    touche = 0
    "Masque de saisie des critères de recherche"
    touche = m.repetition

    cur = None
    for p in pages:
        if p[:len(page)] == page:
            cur = p
            break
    # dossier contenant des écrans en vrac...
    if not cur:
        page = ''
        cur = pages[0]

    while True:
        print(page, cur)
        # on cherche la page correspondante
        # affichage initial ou répétition
        if touche == m.repetition:
            await m.home()
            await titre(m, cur)
            await m.xdraw(path+cur)

        # gestion de la zone de saisie courante
        (choix, touche) = await m.input(0, 1, 10, data='', caractere=' ',
                                        redraw=True)
        await m.cursor(False)

        # navigation dans l'arbre...
        if (touche == m.suite):
            next_ = None
            for p in pages:
                if p[:len(page)] == page and p > cur:
                    next_ = p
                    break
            if next_:
                cur = next_
                await titre(m, cur)
                await m.xdraw(path+cur)
            else:
                await m.message(0, 1, 3, "Pas de page suivante !", bip=True)
        elif (touche == m.retour):
            prev = None
            for p in pages:
                if p[:len(page)] == page:
                    if p == cur:
                        break
                    else:
                        prev = p
            if prev:
                cur = prev
                await titre(m, cur)
                await m.xdraw(path+cur)
            else:
                await m.message(0, 1, 3, "Pas de page précédente !", bip=True)
        elif (touche == m.envoi):
            if choix == '':
                await m.message(0, 1, 3,
                                "Entrez un choix ou un mot-clé !", bip=True)
            else:
                # on cherche un choix dans un menu
                for p in pages:
                    if p[:len(page+choix)] == page+choix:
                        cur = p
                        page = page + choix
                        await titre(m, cur)
                        await m.xdraw(path+cur)
                        break
                # on cherche un mot-clé
                for p in pages:
                    if p.find('#'+choix+'#') > 0:
                        cur = p
                        page = p[:p.find('_')]
                        await titre(m, cur)
                        await m.xdraw(path+cur)
                        break
        elif touche != m.repetition:
            await m.message(0, 1, 3, "Désolé, pas encore disponible")


async def arbo(websocket, path):
    # Initialisation du serveur vidéotex
    m = pynitel.Pynitel(pynitel.PynitelWS(websocket))

    if len(sys.argv) > 1:
        service = sys.argv[1]
    else:
        service = ''

    await arbo_teletel(m, service)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(arbo, 'localhost', 3615))
    loop.run_forever()
