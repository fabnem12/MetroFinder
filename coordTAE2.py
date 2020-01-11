from bs4 import BeautifulSoup
import math

from fusion2 import fusion

def remplaceNameParNom(nomFichier):
    with open(nomFichier, "r") as f:
        lignes = f.readlines()

    with open(nomFichier, "w") as f:
        for ligne in lignes:
            while "name" in ligne: ligne = ligne.replace("name", "nom")
            f.write(ligne)

remplaceNameParNom("csv-data/TAE.kml")
with open("csv-data/TAE.kml", "r") as fichier:
    contenu = fichier.readlines()
contenu = "\n".join(contenu)

soup = BeautifulSoup(contenu, "html.parser")

couleurs = {"Air 350":"0288D1", "AirBaltic":"FFD600", "HOP!":"E65100", "JOON":"C2185B"}

aeroports = dict()
compagnies = dict()
for compagnie in soup.find_all("folder"):
    nomCompagnie = compagnie.nom.string

    compagnies[nomCompagnie] = []

    for lien in compagnie.find_all("placemark"):
        if "-" not in lien.nom.string: continue
        retour = False

        depart, arrivee = lien.nom.string.split("-")
        via = None
        if lien.description == None or "base officielle" in lien.description.string:
            try: coordDep, coordArr = lien.coordinates.string.split()
            except: print(lien.coordinates.string, lien); quit()
            coordDep, coordArr = coordDep[:-2], coordArr[:-2]

        elif "via" in lien.description.string:
            indexVia = lien.description.string.index("via ")
            via = lien.description.string[indexVia+4:]

            if "retour" in lien.description.string:
                retour = True

            listeCoord = lien.coordinates.string.split()
            try: coordDep, coordVia, coordArr = listeCoord[:3]
            except: print(lien.coordinates.string, lien); quit()
            coordDep, coordVia, coordArr = coordDep[:-2], coordVia[:-2], coordArr[:-2]

        if depart in aeroports and aeroports[depart] == coordArr or arrivee in aeroports and aeroports[arrivee] == coordDep:
            coordDep, coordArr = coordArr, coordDep

        if depart not in aeroports: aeroports[depart] = coordDep
        if arrivee not in aeroports: aeroports[arrivee] = coordArr
        if via != None and via not in aeroports: aeroports[via] = coordVia

        if via != None:
            compagnies[nomCompagnie].append((arrivee, via))
            compagnies[nomCompagnie].append((via, depart))

            if retour:
                compagnies[nomCompagnie].append((depart, arrivee))
            else:
                compagnies[nomCompagnie].append((depart, via))
                compagnies[nomCompagnie].append((via, arrivee))
        else:
            compagnies[nomCompagnie].append((depart, arrivee))
            compagnies[nomCompagnie].append((arrivee, depart))

with open("csv-data/TAE.csv", "w") as fichier:
    printF = lambda x: fichier.write(x+"\n")

    for aeroport in sorted(aeroports):
        coord = aeroports[aeroport].split(",")
        coord = ", ".join(coord)
        aeroports[aeroport] = coord

        printF(coord+";"+aeroport)

def distance(a, b):
    a = list(map(float, a.split(", ")))
    b = list(map(float, b.split(", ")))

    deg2rad = lambda x: math.pi*x/180

    lon1, lat1, lon2, lat2 = map(deg2rad, (a[1], a[0], b[1], b[0]))
    try:
        return str(6378.137 * math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)))
    except:
        print(lat1, lon1)
        return 0

for compagnie in compagnies:
    with open("lignesAlt/tae/"+compagnie+".xml", "w") as fichier:
        printF = lambda x: fichier.write(x+"\n")

        printF('<?xml version="1.0" encoding="UTF-8"?>')
        printF('<ligne terminus="" couleur="'+couleurs[compagnie]+'">')

        for aeroport in sorted(list(aeroports.keys())):
            liensAeroCompa = []
            for lien in compagnies[compagnie]:
                depart, arrivee = lien
                if depart == aeroport: liensAeroCompa.append(arrivee)

            if liensAeroCompa != []:
                printF('\t<gare nom="'+aeroport+'" coord="'+aeroports[aeroport]+'">')

                for arrivee in set(liensAeroCompa):
                    printF('\t\t<voisin nom="'+arrivee+'" distance="' + distance(aeroports[aeroport], aeroports[arrivee]) + '" />')

                printF('\t</gare>')

        printF('</ligne>')

fusion("tae")
