#!/usr/bin/env python3

import serial
import pynitel
import sys
import json
import csv

m = None


def init():
    "Initialisation du serveur vidéotex"
    global m
    m = pynitel.Pynitel(serial.Serial('/dev/ttyUSB0', 1200,
                                      parity=serial.PARITY_EVEN, bytesize=7,
                                      timeout=2))

    if len(sys.argv) > 2:
        (quoi, ou) = (sys.argv[1], sys.argv[2])
    else:
        (quoi, ou) = ('', '')
    return(quoi, ou)


def annuaire_saisie(quoi, ou):
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
            m.home()
            m.xdraw('ecrans/E.ANNUAIRE.OPTIM.vtx')

        # gestion de la zone de saisie courante
        (zone, touche) = m.waitzones(zone)

        if touche == m.envoi:
            quoi = ("%s %s %s" % (m.zones[0]['texte'], m.zones[1]['texte'],
                                  m.zones[5]['texte'])).strip()
            ou = ("%s %s %s" % (m.zones[4]['texte'], m.zones[3]['texte'],
                                m.zones[2]['texte'])).strip()
            if quoi == '':
                m.message(0, 1, 3, "Indiquez un nom ou une rubrique")
                touche = 0
                zone = 1
            elif ou == '':
                m.message(0, 1, 3, "Indiquez localité ou département")
                touche = 0
                zone = 3
            elif len(quoi)<6 or len(ou)<5:
                m.message(0, 1, 3, "Veuillez préciser")
                touche = 0

        if touche != m.repetition and touche != 0:
            break

    return (touche, quoi, ou)


def annuaire_recherche(quoi, ou):
    "Effectue une recherche sur plusieurs annuaires"
    res = []
    if len(res) == 0:
        annu = ""
        res = annufake(quoi, ou)
    return(res, annu)


def add_if_not_none(the_dict, key, item):
    if item is not None:
        the_dict[key] = item.string.strip()


def annufake(qui, ou):
    # recherche sur faux annuaire stocké en CSV
    res = []

    qui = qui.upper().strip().replace('-',' ')
    ou = ou.upper().strip()

    with open('fug.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if ((qui in row['nom'].upper() or qui in row['prof'].upper())
                and ou in row['ville'].replace('ç','C').upper()):
                    res.append(dict(nom=row['nom'], adresse=row['prof'],
                                    cp=row['adresse'], ville=row['ville'], tel=row['tel'])) 

    return(res)


def strformat(left='', right='', fill=' ', width=40):
    " formattage de texte "
    total = width-len(left+right)
    if total > 0:
        out = left + fill * total + right
    else:
        out = left+right
    print("'"+out+"'", width, total, len(out))
    return(out)


def affiche_resultat(quoi, ou, res, annu=''):
    "Affiche les résultats de la recherche"
    global m
    page = 1
    while True:
        if page > 0:  # affichage
            # entête sur 2 lignes + séparation
            m.home()
            m._print(quoi.upper()+' à '+ou)
            m.pos(2)
            m.color(m.bleu)
            m.plot('̶', 40)
            if annu != '':
                m.pos(23, 1)
                m.color(m.bleu)
                m._print("(C)\x0d\x0a"+annu)

            # plusieurs pages ?
            if len(res) > 5:
                m.pos(1, 37)
                m._print(" "+str(int(abs(page)))+'/'+str(int((len(res)+4)/5)))
                m.pos(3)

            # if len(res)>5:
            #     if abs(page)>1:
            #         m.pos(2,33)
            #         m.inverse()
            #         m.color(m.cyan)
            #         m._print('↑RETOUR↑')
            #         m.inverse(False)
            #     else:
            #         m.pos(2,33)
            #         m.color(m.bleu)
            #         m.plot('̶', 8)

            # première ligne de résultat
            m.pos(3)
            for a in range((page-1)*5, page*5):
                if a < len(res):
                    r = res[a]
                    if 'adresse' not in r or r['adresse'] == '':
                        r['adresse'] = '(adresse masquée)'
                    if 'tel' not in r or r['tel'] == '':
                        r['tel'] = ' (num. masqué)'
                    m.color(m.blanc)
                    m._print(strformat(right=str(int(a+1)), width=3))
                    m._print(' '+strformat(left=r['nom'][:20],
                                           right=r['tel'], width=36))
                    m.color(m.vert)
                    m._print('    '+r['adresse'][:35]+'\x0d\x0a    ' +
                             r['cp']+' '+r['ville']+'\x0d\x0a')
                    m.color(m.bleu)
                    if a < page*5:
                        m.plot(' ', 4)
                        m.plot('̶', 36)

            # ligne finale
            m.pos(22)
            m.color(m.bleu)
            m.plot('̶', 40)

            # if len(res)>5:
            #     if len(res)>page*5:
            #         m.pos(22,34)
            #         m.inverse()
            #         m.color(m.cyan)
            #         m._print('↓SUITE↓')
            #     else:
            #         m.pos(22,33)
            #         m.color(m.bleu)
            #         m.plot('̶', 8)
            # if len(res)<5 or len(res)<=page*5:
            #     m.pos(22)
            #     m.color(m.bleu)
            #     m.plot('̶', 40)

            if page > 1:
                if len(res) > page*5:  # place pour le SUITE
                    m.pos(22, 15)
                else:
                    m.pos(23, 15)
                m.color(m.vert)
                m._print('page précédente →')
                m.underline()
                m._print(' ')
                m.inverse()
                m.color(m.cyan)
                m._print('_RETOUR ')
            if len(res) > page*5:
                m.pos(23, 17)
                m.color(m.vert)
                m._print('page suivante →')
                m.underline()
                m._print(' ')
                m.inverse()
                m.color(m.cyan)
                m._print('_SUITE  ')

            m.pos(24, 15)
            m.color(m.vert)
            m._print("autre recherche → ")
            m.inverse()
            m.color(m.cyan)
            m._print("SOMMAIRE")
        else:
            page = abs(page)

        # attente saisie
        (choix, touche) = m.input(0, 1, 0, '')
        m.cursor(False)
        if touche == m.suite:
            if page*5 < len(res):
                page = page + 1
            else:
                m.bip()
                page = -page  # pas de ré-affichage
        elif touche == m.retour:
            if page > 1:
                page = page - 1
            else:
                m.bip()
                page = -page  # pas de ré-affichage
        elif touche == m.sommaire:
            break
        elif touche == m.correction:  # retour saisie pour correction
            return(touche)
        elif touche != m.repetition:
            m.bip()
            page = -page  # pas de ré-affichage

    return(touche)


def annuaire():
    global m
    (annuaire_quoi, annuaire_ou) = init()

    while True:
        print(annuaire_quoi, annuaire_ou)
        (touche, annuaire_quoi, annuaire_ou) = annuaire_saisie(annuaire_quoi,
                                                               annuaire_ou)
        if touche == m.envoi:
            # on lance la recherche
            m.cursor(False)
            m.pos(0, 1)
            m.flash()
            m._print('Recherche... ')
            (resultat, annu) = annuaire_recherche(annuaire_quoi, annuaire_ou)
            print(resultat)
            if len(resultat) == 0:
                m.message(0, 1, 3, "Aucune adresse trouvée")
                annuaire_quoi = ''
                annuaire_ou = ''
            else:
                if affiche_resultat(annuaire_quoi, annuaire_ou,
                                    resultat, annu) != m.correction:
                    (annuaire_quoi, annuaire_ou) = ('', '')

if __name__ == '__main__':
    annuaire()
