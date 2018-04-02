#!/usr/bin/env python3
import asyncio
import websockets
from bs4 import BeautifulSoup
import requests
import pynitel
import sys
import json


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

        if (touche == m.envoi):
            if quoi == '':
                await m.message(0, 1, 3,
                                "Entrez au moins un nom ou une rubrique !")
            else:
                return (touche, quoi, ou)
        elif touche != m.repetition:
            await m.message(0, 1, 3, "Désolé, pas encore disponible")


def annuaire_recherche(quoi, ou):
    "Effectue une recherche sur plusieurs annuaires"
    res = []
    if len(res) == 0:
        annu = "118712.fr"
        res = annuaire118712(quoi, ou)
    if len(res) == 0:
        annu = "118218.fr"
        res = annuaire118218(quoi, ou)
    if len(res) == 0:
        annu = "118000.fr"
        res = annu118000(quoi, ou)
    print(quoi, ou, annu, res)
    return(res, annu)


def add_if_not_none(the_dict, key, item):
    if item is not None:
        the_dict[key] = item.string.strip()


def annuaire118712(qui, ou):
    # recherche sur l'annuaire d'Orange (mais problème de captcha)
    res = []
    req = requests.get('https://annuaire.118712.fr/', params={"s": qui+' '+ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all(itemtype="http://schema.org/Person"):
        nom = p.find(itemprop="name").a.string.strip()
        cp = p.find(itemprop="postalCode").string.strip()
        ville = p.find(itemprop="addressLocality").string.strip()
        tel = p.find(itemprop="telephone").string.strip()
        propart = p.find(class_="propart_text").string.strip()
        result = dict(nom=nom, cp=cp, ville=ville, tel=tel, propart=propart)
        adresse = p.find(itemprop="streetAddress")
        if adresse is not None:
            result['adresse'] = adresse.string.strip()
        else:
            result['adresse'] = ''
        lat = p.find(itemprop="latitude")
        if lat is not None:
            result['lat'] = lat.string.strip()
        lon = p.find(itemprop="longitude")
        if lon is not None:
            result['lon'] = lon.string.strip()
        categories = p.find(class_="categories")
        if categories is not None:
            result['categories'] = categories.string.strip()
        res.append(result)
    for p in h.find_all(itemtype="http://schema.org/LocalBusiness"):
        nom = p.find(itemprop="name").a.string.strip()
        result = dict(nom=nom)
        add_if_not_none(result, 'adresse', p.find(itemprop="streetAddress"))
        add_if_not_none(result, 'cp', p.find(itemprop="postalCode"))
        add_if_not_none(result, 'ville', p.find(itemprop="addressLocality"))
        add_if_not_none(result, 'tel', p.find(itemprop="telephone"))
        if 'tel' not in result:
            tel = p.find(class_="hidden-phone")
            if tel is not None:
                result['tel'] = tel['data-wording']
        add_if_not_none(result, 'categories', p.find(class_="categories"))
        res.append(result)
    return(res)


def annuaire118218(qui, ou):
    # recherche sur l'annuaire 118218 (pas de captcha ?)
    res = []
    # recherche particuliers
    req = requests.get('http://www.118218.fr/recherche',
                       params={"who": qui, "where": ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all("section", class_="searchResult"):
        if p.a is not None:
            adresse = p.address.span.string.replace(',', '')
            p.address.span.unwrap()
            cp = p.address.span.span.string.replace(',', '')
            p.address.span.unwrap()
            p.address.span.unwrap()
            ville = p.address.span.string.replace('\n', '').strip()
            res.append(dict(nom=p.a.string, adresse=adresse, cp=cp,
                            ville=ville, tel=p.p.string))
    # recherche pro
    req = requests.get('http://www.118218.fr/recherche',
                       params={"what": qui, "where": ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all("section", class_="searchResult"):
        if p.a is not None:
            adresse = p.address.span.string.replace(',', '')
            p.address.span.unwrap()
            cp = p.address.span.span.string.replace(',', '')
            p.address.span.unwrap()
            p.address.span.unwrap()
            ville = p.address.span.string.replace('\n', '').strip()
            res.append(dict(nom=p.a.string, adresse=adresse,
                            cp=cp, ville=ville, tel=p.p.string))
    return(res)


def annu118000(qui, ou):
    # recherche sur l'annuaire 118000 (pas de captcha ?)
    res = []
    # recherche particuliers
    req = requests.get('https://www.118000.fr/search',
                       params={"who": qui, "label": ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all(class_="card"):
        b = p.find(class_="iconheart")
        if b['data-info'] is not None:
            j = json.loads(b['data-info'])
            res.append(dict(nom=p.h2.a.string, adresse=j['address'],
                            cp=j['cp'], ville=j['city'], tel=j['tel']))
    return(res)


def strformat(left='', right='', fill=' ', width=40):
    " formattage de texte "
    total = width-len(left+right)
    if total > 0:
        out = left + fill * total + right
    else:
        out = left+right
    return(out)


async def affiche_resultat(m, quoi, ou, res, annu=''):
    "Affiche les résultats de la recherche"
    page = 1
    while True:
        if page > 0:  # affichage
            # entête sur 2 lignes + séparation
            await m.home()
            await m._print(quoi.upper())
            if ou.strip() != '':
                await m._print(' à '+ou.upper())
            await m.pos(2)
            await m.color(m.bleu)
            await m.plot('̶', 40)
            if annu != '':
                await m.pos(23, 1)
                await m.color(m.bleu)
                await m._print("(C)\x0d\x0a"+annu)

            # plusieurs pages ?
            if len(res) > 5:
                await m.pos(1, 37)
                await m._print(" " + str(int(abs(page))) +
                               '/' + str(int((len(res)+4)/5)))
                await m.pos(3)

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
            await m.pos(3)
            for a in range((page-1)*5, page*5):
                if a < len(res):
                    r = res[a]
                    if 'adresse' not in r or r['adresse'] == '':
                        r['adresse'] = '(adresse masquée)'
                    if 'tel' not in r or r['tel'] == '':
                        r['tel'] = ' (num. masqué)'
                    await m.color(m.blanc)
                    await m._print(strformat(right=str(int(a+1)), width=3))
                    await m._print(' '+strformat(left=r['nom'][:20],
                                                 right=r['tel'], width=36))
                    await m.color(m.vert)
                    await m._print('    '+r['adresse'][:35]+'\x0d\x0a    ' +
                                   r['cp']+' '+r['ville']+'\x0d\x0a')
                    await m.color(m.bleu)
                    if a < page*5:
                        await m.plot(' ', 4)
                        await m.plot('̶', 36)

            # ligne finale
            await m.pos(22)
            await m.color(m.bleu)
            await m.plot('̶', 40)

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
                    await m.pos(22, 15)
                else:
                    await m.pos(23, 15)
                await m.color(m.vert)
                await m._print('page précédente →')
                await m.underline()
                await m._print(' ')
                await m.inverse()
                await m.color(m.cyan)
                await m._print('_RETOUR ')
            if len(res) > page*5:
                await m.pos(23, 17)
                await m.color(m.vert)
                await m._print('page suivante →')
                await m.underline()
                await m._print(' ')
                await m.inverse()
                await m.color(m.cyan)
                await m._print('_SUITE  ')

            await m.pos(24, 15)
            await m.color(m.vert)
            await m._print("autre recherche → ")
            await m.inverse()
            await m.color(m.cyan)
            await m._print("SOMMAIRE")
        else:
            page = abs(page)

        # attente saisie
        (choix, touche) = await m.input(0, 1, 0, '')
        await m.cursor(False)
        if touche == m.suite:
            if page*5 < len(res):
                page = page + 1
            else:
                await m.bip()
                page = -page  # pas de ré-affichage
        elif touche == m.retour:
            if page > 1:
                page = page - 1
            else:
                await m.bip()
                page = -page  # pas de ré-affichage
        elif touche == m.sommaire:
            break
        elif touche == m.correction:  # retour saisie pour correction
            return(touche)
        elif touche != m.repetition:
            await m.bip()
            page = -page  # pas de ré-affichage

    return(touche)


async def annuaire(websocket, path):
    # Initialisation du serveur vidéotex
    m = pynitel.Pynitel(pynitel.PynitelWS(websocket))

    if len(sys.argv) > 2:
        (annu_quoi, annu_ou) = (sys.argv[1], sys.argv[2])
    else:
        (annu_quoi, annu_ou) = ('', '')

    while True:
        (touche, annu_quoi, annu_ou) = await annuaire_saisie(m, annu_quoi,
                                                             annu_ou)
        if touche == m.envoi:
            # on lance la recherche
            await m.cursor(False)
            await m.pos(0, 1)
            await m.flash()
            await m._print('Recherche... ')
            (resultat, annu) = annuaire_recherche(annu_quoi, annu_ou)
            if len(resultat) == 0:
                await m.message(0, 1, 3, "Aucune adresse trouvée")
            else:
                if await affiche_resultat(m, annu_quoi, annu_ou,
                                          resultat, annu) != m.correction:
                    (annu_quoi, annu_ou) = ('', '')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(annuaire, 'localhost', 3611))
    loop.run_forever()
