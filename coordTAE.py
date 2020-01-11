# -*- coding: utf8 -*-
import requests, csv, os
from math import pi, acos, asin, cos, sin
from cherche import donnees

class Aeroport():
    def __init__(self, nom, coord):
        self.nom, self.coord = nom, coord
        self.liaisons = []

    def setLiaisons(self, newLiaisons):
        self.liaisons = newLiaisons

        for ville, reseau in self.liaisons:
            liaisonsVille = ville.liaisons

            if (self, reseau) not in liaisonsVille:
                ville.setLiaisons(liaisonsVille+[(self, reseau)])

    def estDansReseau(self, reseauCherche):
        for _, reseau in self.liaisons:
            if reseau == reseauCherche: return True

        return False

"""class Liaison():
    def __init__(self, ville1, ville2, reseau):
        self.villes, self.reseau = [ville1, ville2], reseau

        for ville in self.villes:
            liaisonsVille = ville.liaisons

            ville.setLiaisons(liaisonsVille+[self])"""

def distance(A,B):
	latA, latB = pi*A[0]/180, pi*B[0]/180
	dlon = pi*(B[1] - A[1])/180
	rayonT = 6378.137

	return rayonT*acos(sin(latA)*sin(latB)+cos(latA)*cos(latB)*cos(dlon))

def trouveCoordVille(ville, reseau):
    if os.path.isfile("lignesAlt/tae/"+reseau+".xml"):
        coordGPS = donnees(reseau, "coord", "tae")
        if ville in coordGPS:
            coordVille = list(map(float, str(coordGPS[ville])[1:-1].split(", ")))
            print(ville, coordVille, "OK")
            return coordVille

    if "Margrethe" not in ville and "Kansai" not in ville:
        texte = requests.get("https://www.google.fr/maps/search/"+ville).text

        try:
            ligneCoord = texte.split("\n")[119]
            coordBrutes = ligneCoord.split(",")[-2:]

            coordVille = [float(coordBrutes[1][:-1]),float(coordBrutes[0])]
            print(ville, coordVille, "OK via Maps")
        except:
            print(ville+" ?")
            lat = input("Latitude : ")
            long = input("Longitude : ")

            coordVille = [float(long),float(lat)]
        finally:
            return coordVille
    else:
       if "Margrethe" in ville: coordVille = [-38,67]
       else: coordVille = [134.841, 34.8976]

       print(ville, coordVille, "OK")
       return coordVille

def traitementVille(ville):
    for trucRetire in ("Ext.", "Int.", "Est", "Ouest", "O", "E", "Eu", "A"):
        lenTrucRetire = len(trucRetire)

        if trucRetire in ville[-1*lenTrucRetire:]:
            ville = ville[:-1*lenTrucRetire-1]

    return ville

bases = {"JOON":[],"Air 350":[], "AirBaltic":[], "HOP!":[], "Small":[]}
aeroports = dict()

lignesOK = list(bases.keys())
for ligne in lignesOK:
    with open("csv-data/TAE - "+ligne+".csv", "r") as fichier: colonnes = fichier.readlines()[0]

    colonnes = colonnes.split(";")[1:]
    bases = []
    for index in range(len(colonnes)):
        if "\n" in colonnes[index]: nomBase = colonnes[index].replace("\n","")
        else: nomBase = traitementVille(colonnes[index])

        if "Hors-base" not in nomBase and nomBase not in ("", " ") and nomBase not in bases: bases.append(nomBase)

    for base in bases:
        if base not in aeroports:
            nom, coord = base, trouveCoordVille(base, ligne)
            aeroports[nom] = Aeroport(nom, coord)

    with open("csv-data/TAE - "+ligne+".csv", newline="") as fichier:
        reader = csv.DictReader(fichier, delimiter=";")

        for row in reader:
            ville = row["Destinations"]

            for baseBrute in row:
                base = traitementVille(baseBrute)

                if row[baseBrute] != "" and base not in ("Destinations","Hors-base CRJ","Hors-base ATR"):
                    if ville not in aeroports:
                        coord = trouveCoordVille(ville, ligne)
                        aeroports[ville] = Aeroport(ville, coord)

                    liaisonsBase = aeroports[base].liaisons
                    aeroports[base].setLiaisons(liaisonsBase + [(aeroports[ville], ligne)])

    with open("lignesAlt/tae/"+ligne+".xml", "w") as fichier:
        printF = lambda x: fichier.write(x+"\n")

        printF('<?xml version="1.0" encoding="UTF-8" ?>')
        printF('<ligne terminus="" couleur="000000">')

        for aeroport in aeroports.values():
            if not aeroport.estDansReseau(ligne): continue

            nom, coord = aeroport.nom, str(aeroport.coord)[1:-1]
            printF('\t<gare nom="'+nom+'" coord="'+coord+'">')

            voisins = [x for x, y in aeroport.liaisons if y == ligne]
            for voisin in voisins:
                nomVoisin = voisin.nom
                dist = str(distance(aeroport.coord, voisin.coord))

                printF('\t\t<voisin nom="'+nomVoisin+'" distance="'+dist+'" />')
            printF('\t</gare>')

        printF('</ligne>')
    with open("csv-data/TAE.csv", "a") as fichier:
        printF = lambda x: fichier.write(x+"\n")

        for aeroport in sorted(aeroports.values(), key=lambda x:x.nom):
            nom, coordGPS = aeroport.nom, aeroport.coord
            printF(str(coordGPS)[1:-1]+";"+nom)
