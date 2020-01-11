# -*- coding: utf8 -*-
import csv, codecs, cherche
import constantes as ctes

#CLASSES########################################################################
class Ligne():
    def __init__(self, id, nom, couleur):
        self.id, self.nom, self.couleur = id, nom, couleur
        self.terminus = []
        self.gares = []

    def ajoutGare(self, gare):
        self.gares.append(gare)

    def setTerminus(self, data):
        self.terminus = data

    def get(self, demande):
        infos = {"id":self.id, "nom":self.nom, "gares":self.gares, "terminus":self.terminus, "couleur":self.couleur}

        return infos[demande]

class Gare():
    def __init__(self, id, lat, long, nom, coordImg, nVoisins=[]):
        self.id, self.nom = id, nom

        self.coordGPS = (float(lat), float(long))
        self.coordImg = coordImg
        self.voisins = nVoisins

    def ajoutVoisin(self, nVoisin, dist, ligne):
        self.voisins.append((dist, nVoisin, ligne))

    def setVoisins(self, data): self.voisins = data

    def get(self, demande):
        infos = {"nom":self.nom, "id":self.id, "coordGPS":self.coordGPS, "coordImg":self.coordImg, "voisins":self.voisins}

        return infos[demande]
#FIN CLASSES####################################################################

#FONCTIONS######################################################################
def recupGares():
    gares = dict()
    _, coordImg = cherche.lectureXMLVille("londres", alt="Alt")

    with codecs.open("csv-data/londres-stations.csv", "r", "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar=None) #extrait les données

        for row in reader:
            id, lat, long, nom = row[:4]
            nom = ctes.traitementNom(nom)

            coord = (0,0)
            if nom in coordImg: coord = coordImg[nom]; print(nom)

            gare = Gare(id, lat, long, nom, coord)
            gares[id] = gare

    return gares

def recupLignes():
    lignes = dict()
    with codecs.open("csv-data/londres-lignes.csv", "r", "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar=None) #extrait les donnees

        for row in reader:
            id, nom, couleur = row[:3]
            nom, couleur = nom[1:-1], ctes.traitementNom(couleur)

            ligne = Ligne(id, nom, couleur)
            lignes[id] = ligne

    return lignes

def relierGares(gares, lignes):
    with codecs.open("csv-data/londres-liens.csv", "r", "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar=None)

        for row in reader:
            idStation1, idStation2, idLigne = row

            station1, station2, ligne = gares[idStation1], gares[idStation2], lignes[idLigne]
            coordGPS1, coordGPS2 = station1.get("coordGPS"), station2.get("coordGPS")

            dist = ctes.distance(coordGPS1, coordGPS2) + ctes.penaliteStopNew

            station1.setVoisins(station1.get("voisins")+[(dist, station2, ligne)])
            station2.setVoisins(station2.get("voisins")+[(dist, station1, ligne)])

            for x in (station1, station2):
                if x not in ligne.get("gares"):
                    ligne.ajoutGare(x)

def trouveTerminus(ligne):
    gares = ligne.get("gares")

    terminus = []
    for gare in gares:
        voisins = gare.get("voisins")

        if len([x for x in voisins if x[2] == ligne]) == 1:
            terminus.append(gare)

    return terminus

def ecritXMLLigne(ligne):
    terminus = ligne.get("terminus")
    gares = ligne.get("gares")

    with codecs.open("lignesAlt/londres/"+ligne.get("nom")+".xml", "w", "utf-8") as fichierLigne:
        printF = lambda x: fichierLigne.write(x+"\n")

        printF("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        printF("<ligne terminus=\"" + ",".join([x.get("nom") for x in terminus]) + "\" couleur=\""+ligne.get("couleur")+"\">")

        for gare in gares:
            nomGare = gare.get("nom")
            coordImg = gare.get("coordImg")
            if type(coordImg[0]) == tuple:
                coordImg = str(coordImg[0])[1:-1]
            else:
                coordImg = str(coordImg)[1:-1]

            printF("\t<gare nom=\""+nomGare+"\" coord=\""+coordImg+"\">")

            for infosVoisin in gare.get("voisins"):
                dist, voisin, ligneVoisin = infosVoisin

                if ligneVoisin == ligne:
                    printF("\t\t<voisin nom=\""+voisin.get("nom")+"\" distance=\""+str(dist)+"\" />")

            printF("\t</gare>")

        printF("</ligne>")
#FIN FONCTIONS##################################################################

#PROGRAMME PRINCIPAL############################################################
#Initialisation
#-Création des gares
print("Récupération des informations sur chaque gare...")
gares = recupGares()

#-Création des lignes
print("Récupération des noms de chaque ligne...")
lignes = recupLignes()

#-Mise en place des liens entre gares
print("Création des liens de voisinage entre stations...")
relierGares(gares, lignes)

#-Trouve les terminus de chaque ligne
for idLigne in lignes:
    ligne = lignes[idLigne]
    terminus = trouveTerminus(ligne)

    ligne.setTerminus(terminus)
#Fin Initialisation

#Création des XML
#-Création d'un XML par ligne
print("Écriture du XML correspondant à chaque ligne...")
for idLigne in lignes:
    ligne = lignes[idLigne]
    ecritXMLLigne(ligne)
    print(ligne.get("nom"),"OK")
print("Terminé !\n")

print("Les données ont été correctement initialisées. Il ne reste plus qu'à mettre les gares sur le plan avec XMLCreator2.py")
#Fin Création des XML
#FIN PROGRAMME PRINCIPAL########################################################
