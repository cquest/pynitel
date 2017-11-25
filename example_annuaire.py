import serial
import pynitel
from bs4 import BeautifulSoup
import requests
import sys
import time
import json

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



def typeit(text):
    for c in text:
        pynitel._print(c)
        time.sleep(0.2)

with serial.Serial('/dev/ttyUSB0', 4800, parity=serial.PARITY_EVEN, bytesize=7, timeout=2) as ser:
    pynitel.conn=ser
    pynitel.home()
    pynitel.xdraw('ecrans/E.ANNUAIRE.OPTIM.vtx')

    ser.flush()
    time.sleep(1)
    pynitel.pos(5,13)
    typeit(sys.argv[1].upper())
    pynitel.pos(10,13)
    typeit(sys.argv[2].upper())
    res = []


    if len(res)==0:
        res = annuaire118712(sys.argv[1], sys.argv[2])
        annu = "118712.fr"
    if len(res)==0:
        res = annuaire118218(sys.argv[1], sys.argv[2])
        annu = "118218.fr"
    if len(res)==0:
        res = annu118000(sys.argv[1], sys.argv[2])
        annu = "118000.fr"


    pynitel.home()
    pynitel._print(sys.argv[1].upper()+' à '+sys.argv[2]+'\x0d\x0a')
    pynitel.color(pynitel.bleu)
    pynitel.plot('̶', 40)
    for r in res[:5]:
        pynitel.color(pynitel.blanc)
        pynitel._print(r['nom'])
        pynitel.plot(' ', 40-len(r['nom']+r['tel']))
        pynitel._print(r['tel']+'\x0d')
        pynitel.color(pynitel.vert)
        pynitel._print(r['adresse']+'\x0d\x0a'+r['cp']+' '+r['ville']+'\x0d\x0a')
        pynitel.color(pynitel.bleu)
        pynitel.plot('̶', 40)

    pynitel.pos(24,1)
    pynitel.color(pynitel.magenta)
    pynitel._print("Source "+annu)

    if len(res)>5:
        pynitel.pos(24,33)
        pynitel._print('→ ')
        pynitel.inverse()
        pynitel._print('SUITE')
        pynitel.pos(1,38)
        pynitel._print('1/'+str(int((len(res)+4)/5)))

    ser.flush()
