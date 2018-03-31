#!/usr/bin/env python3
import asyncio
import websockets
import pynitel
import sys

m = None


async def annuaire_saisie(quoi, ou):
    "Masque de saisie des critères de recherche"
    # définition des zones
    global m
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
            await m.xdraw('ecrans/E.ANNUAIRE.vtx')

        # gestion de la zone de saisie courante
        (zone, touche) = await m.waitzones(zone)

        if touche != m.repetition:
            break

    quoi = ("%s %s %s" % (m.zones[0]['texte'], m.zones[1]['texte'],
                          m.zones[5]['texte'])).strip()
    ou = ("%s %s %s" % (m.zones[4]['texte'], m.zones[3]['texte'],
                        m.zones[2]['texte'])).strip()
    return (touche, quoi, ou)


async def annuaire(websocket, path):
    global m
    # Initialisation du serveur vidéotex
    m = pynitel.Pynitel(pynitel.PynitelWS(websocket))

    if len(sys.argv) > 2:
        (annuaire_quoi, annuaire_ou) = (sys.argv[1], sys.argv[2])
    else:
        (annuaire_quoi, annuaire_ou) = ('', '')

    while True:
        print(annuaire_quoi, annuaire_ou)
        (touche, annuaire_quoi, annuaire_ou) = await annuaire_saisie(annuaire_quoi, annuaire_ou)  # noqa

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(annuaire, 'localhost', 3611))
    asyncio.get_event_loop().run_forever()
