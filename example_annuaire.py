import serial
import pynitel
from bs4 import BeautifulSoup
import requests
import sys
import json


def init():
    "Initialisation du serveur vidéotex"
    pynitel.conn = serial.Serial('/dev/ttyUSB0', 4800, parity=serial.PARITY_EVEN, bytesize=7, timeout=2)

    if len(sys.argv) > 2:
        (quoi,ou) = (sys.argv[1],sys.argv[2])
    else:
        (quoi,ou)=('','')
    return(quoi,ou)


def annuaire_saisie(quoi,ou):
    "Masque de saisie des critères de recherche"
    # définition des zones
    pynitel.resetzones()
    pynitel.zone(5, 13, 27, quoi, pynitel.vert)
    pynitel.zone(7, 13, 27, '', pynitel.vert)
    pynitel.zone(10, 13, 27, ou, pynitel.vert)
    pynitel.zone(13, 13, 27, '', pynitel.vert)
    pynitel.zone(14, 13, 27, '', pynitel.vert)
    pynitel.zone(15, 13, 27, '', pynitel.vert)
    touche = pynitel.repetition
    zone = 1

    while True:
        # affichage initial ou répétition
        if touche == pynitel.repetition:
            pynitel.home()
            pynitel.xdraw('ecrans/E.ANNUAIRE.OPTIM.vtx')

        # gestion de la zone de saisie courante
        (zone, touche) = pynitel.waitzones(zone)

        if touche != pynitel.repetition:
            break

    quoi = ("%s %s %s" % (pynitel.zones[0]['texte'],pynitel.zones[1]['texte'],pynitel.zones[5]['texte'])).strip()
    ou = ("%s %s %s" % (pynitel.zones[4]['texte'],pynitel.zones[3]['texte'],pynitel.zones[2]['texte'])).strip()
    return (touche, quoi, ou)


def annuaire_recherche(quoi, ou):
    "Effectue une recherche sur plusieurs annuaires"
    res = []
    if len(res)==0:
        annu = "118712.fr"
        res = annuaire118712(quoi, ou)
    if len(res)==0:
        annu = "118218.fr"
        res = annuaire118218(quoi, ou)
    if len(res)==0:
        annu = "118000.fr"
        res = annu118000(quoi, ou)
    return(res, annu)


def add_if_not_none(the_dict,key,item):
    if item is not None:
        the_dict[key] = item.string.strip()

def annuaire118712(qui, ou):
    # recherche sur l'annuaire d'Orange (mais problème de captcha)
    res = []
    req = requests.get('https://annuaire.118712.fr/',params={"s": qui+' '+ou})
    h = BeautifulSoup(req.text,'lxml')
    for p in h.find_all(itemtype="http://schema.org/Person"):
        nom = p.find(itemprop="name").a.string.strip()
        cp = p.find(itemprop="postalCode").string.strip()
        ville = p.find(itemprop="addressLocality").string.strip()
        tel = p.find(itemprop="telephone").string.strip()
        propart = p.find(class_="propart_text").string.strip()
        result = dict(nom=nom,cp=cp,ville=ville,tel=tel,propart=propart)
        adresse = p.find(itemprop="streetAddress")
        if adresse is not None:
            result['adresse'] = adresse.string.strip()
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
        add_if_not_none(result,'adresse',p.find(itemprop="streetAddress"))
        add_if_not_none(result,'cp',p.find(itemprop="postalCode"))
        add_if_not_none(result,'ville',p.find(itemprop="addressLocality"))
        add_if_not_none(result,'tel',p.find(itemprop="telephone"))
        if 'tel' not in result:
            tel = p.find(class_="hidden-phone")
            if tel is not None:
                result['tel'] = tel['data-wording']
        add_if_not_none(result,'categories', p.find(class_="categories"))
        res.append(result)
    return(res)


def annuaire118218(qui, ou):
    # recherche sur l'annuaire 118218 (pas de captcha ?)
    res = []
    # recherche particuliers
    req = requests.get('http://www.118218.fr/recherche',params={"who": qui, "where": ou})
    h = BeautifulSoup(req.text,'lxml')
    for p in h.find_all("section", class_="searchResult"):
        if p.a is not None:
            adresse=p.address.span.string.replace(',','')
            p.address.span.unwrap()
            cp=p.address.span.span.string.replace(',','')
            p.address.span.unwrap()
            p.address.span.unwrap()
            ville=p.address.span.string.replace('\n','').strip()
            res.append(dict(nom=p.a.string, adresse=adresse, cp=cp, ville=ville, tel=p.p.string))
    # recherche pro
    req = requests.get('http://www.118218.fr/recherche',params={"what": qui, "where": ou})
    h = BeautifulSoup(req.text,'lxml')
    for p in h.find_all("section", class_="searchResult"):
        if p.a is not None:
            adresse=p.address.span.string.replace(',','')
            p.address.span.unwrap()
            cp=p.address.span.span.string.replace(',','')
            p.address.span.unwrap()
            p.address.span.unwrap()
            ville=p.address.span.string.replace('\n','').strip()
            res.append(dict(nom=p.a.string, adresse=adresse, cp=cp, ville=ville, tel=p.p.string))
    return(res)


def annu118000(qui, ou):
    # recherche sur l'annuaire 118000 (pas de captcha ?)
    res = []
    # recherche particuliers
    req = requests.get('https://www.118000.fr/search',params={"who": qui, "label": ou})
    h = BeautifulSoup(req.text,'lxml')
    for p in h.find_all(class_="card"):
        b=p.find(class_="iconheart")
        if b['data-info'] is not None:
            j=json.loads(b['data-info'])
            res.append(dict(nom=p.h2.a.string, adresse=j['address'], cp=j['cp'], ville=j['city'], tel=j['tel']))
    return(res)


def affiche_resultat(quoi, ou, res, annu=''):
    "Affiche les résultats de la recherche"
    page = 1

    while True:
        if page > 0: # affichage
            pynitel.home()
            pynitel._print(quoi.upper()+' à '+ou)
            pynitel.pos(2)
            pynitel.color(pynitel.bleu)
            pynitel.plot('̶', 40)
            if annu != '':
                pynitel.pos(2,10)
                pynitel.color(pynitel.bleu)
                pynitel._print(" Source: "+annu+" ")

            # plusieurs pages ?
            if len(res)>5:
                pynitel.pos(1,37)
                pynitel._print(" "+str(int(abs(page)))+'/'+str(int((len(res)+4)/5)))
                pynitel.pos(3)

            if len(res)>5:
                if abs(page)>1:
                    pynitel.pos(2,33)
                    pynitel.inverse()
                    pynitel._print('↑RETOUR↑')
                    pynitel.inverse(False)
                else:
                    pynitel.pos(2,33)
                    pynitel.color(pynitel.bleu)
                    pynitel.plot('̶', 8)

            pynitel.pos(3)
            for r in res[(page-1)*5:page*5]:
                pynitel.color(pynitel.blanc)
                pynitel._print(r['nom'])
                pynitel.plot(' ', 40-len(r['nom']+r['tel']))
                pynitel._print(r['tel']+'\x0d')
                pynitel.color(pynitel.vert)
                pynitel._print(r['adresse']+'\x0d\x0a'+r['cp']+' '+r['ville']+'\x0d\x0a')
                pynitel.color(pynitel.bleu)
                pynitel.plot('̶', 40)

            if len(res)>5:
                if len(res)>page*5:
                    pynitel.pos(22,34)
                    pynitel.inverse()
                    pynitel._print('↓SUITE↓')
                else:
                    pynitel.pos(22,33)
                    pynitel.color(pynitel.bleu)
                    pynitel.plot('̶', 8)
            if len(res)<5 or len(res)<=page*5:
                pynitel.pos(22)
                pynitel.color(pynitel.bleu)
                pynitel.plot('̶', 40)

            pynitel.pos(24,15)
            pynitel.color(pynitel.vert)
            pynitel._print("Autre recherche → ")
            pynitel.inverse()
            pynitel.color(pynitel.blanc)
            pynitel._print("SOMMAIRE")
        else:
            page = abs(page)

        (choix,touche) = pynitel.input(0, 1, 0, data='')
        pynitel.cursor(False)
        if touche == pynitel.suite:
            if page*5 < len(res):
                page = page + 1
            else:
                pynitel.bip()
                page = -page # pas de ré-affichage
        elif touche == pynitel.retour:
            if page>1:
                page = page - 1
            else:
                pynitel.bip()
                page = -page # pas de ré-affichage
        elif touche == pynitel.sommaire:
            break
        elif touche != pynitel.repetition:
            pynitel.bip()
            page = -page # pas de ré-affichage

    return(touche)


def annuaire():
    (quoi, ou) = init()

    while True:
        (touche, quoi, ou) = annuaire_saisie(quoi, ou)
        if touche == pynitel.envoi:
            # on lance la recherche
            pynitel.pos(0,1)
            pynitel.flash()
            pynitel._print('Recherche... ')
            (resultat, annu) = annuaire_recherche(quoi, ou)
            print(resultat)
            if len(resultat) == 0:
                pynitel.message(0, 1, 3, "Aucune adresse trouvée")
            else:
                affiche_resultat(quoi, ou, resultat, annu)
            quoi = ''
            ou = ''

annuaire()
