# -*- coding: utf8 -*-
from math import acos, cos, sin, pi
import sys, os, codecs
import cherche

villeParDefaut = "paris2"

lignesExistantes = {
"paris": list(map(str, range(1,15)))+["3b","7b","pedestre", "RER A", "RER B", "RER E", "ORLYVAL", "T1", "T2", "T3A", "T3B","T4","T5","T6","T7","T8"],
"toulouse": ["A","B","C","BUS", "T1", "T2", "pedestre"],
"paris2": list(map(str, range(1,15)))+["3b","7b","pedestre", "RER A", "RER B", "RER C", "RER D","RER E", "ORLYVAL", "T1", "T2", "T3A", "T3B","T4","T5","T6","T7","T8"],
"londres": ["pedestre"],
"tae": ["Air 350","JOON","AirBaltic","HOP!"],
"rennes": ["a","b"],
"delhi": ["RedLine","PinkLine","YellowLine","VioletLine","BlueLine","MagentaLine","GreenLine","AirportExpress","Rapid","AquaLine","pedestre"],
"paris_exact": list(map(str, range(1,15)))+["3b","7b","pedestre", "RER A", "RER B", "RER C", "RER D","RER E", "ORLYVAL", "T1", "T2", "T3A", "T3B","T4","T5","T6","T7","T8", "T11", "LIGNE H", "LIGNE J", "LIGNE K", "LIGNE L", "LIGNE N", "LIGNE P", "LIGNE R", "LIGNE U"],
"paris_metro_exact": list(map(str, range(1,15))) + ["3b", "7b", "pedestre", "T3A", "T3B"]}

def couleursLignes(ville, ligne):
    if "paris" in ville:
        _, _, _, _, couleur = cherche.lectureXMLLigne(ligne, "paris", alt="Alt")
        with codecs.open("lignesAlt/paris/"+ligne+".xml", "r", "utf-8") as fichierLigne:
            contenu = fichierLigne.readlines()

            for i in range(len(contenu)):
                code = contenu[i]

                if "ligne" in code and "couleur" not in code and "/" not in code:
                    code = code[:-1]
                    code += " couleur=\""+couleur+"\">\n"

        with codecs.open("lignesAlt/"+ville+"/"+ligne+".xml", "r", "utf-8") as fichierLigne:
            contenu = fichierLigne.readlines()

            codeParLigne = []
            for ligne in contenu:
                if "ligne" in ligne and "couleur" not in ligne and "/" not in ligne: ligne = code
                codeParLigne.append(ligne)

        with codecs.open("lignesAlt/"+ville+"/"+ligne+".xml", "w", "utf-8") as fichierLigne:
            for code in codeParLigne: fichierLigne.write(code)

        return couleur
    return "000000"

def lignesOK(ville, creation=False):
    supplement = []
    if creation: supplement = lignesExistantes[ville]
    return list(set([x[:-4] for x in os.listdir("./lignesAlt/"+ville+"/")]+supplement))

def rayon(ville):
    if ville in GPSCompte: return 8
    else: return 12

def bordure(ville):
    if ville in GPSCompte: return 3
    else: return 4

accesCartes = "images/"
dimCarte = {"toulouse": [861,744], "paris":[2800,2824], "paris2":[3000,3000], "londres":[1600,1069], "tae":[2058,1036], "rennes":[1280,926], "delhi":[3646,2926], "paris_exact":[1541,953], "paris_metro_exact":[1309,493], "intercités":[1470, 973]}
dimCanvasCarte = dimCarte["toulouse"].copy()
ecartOblig = (400, 100)
largeurAffichageLat = 120
marge = 100
NOSE = { #en x puis en y, en degrés décimaux
    "tae":[[-180,90],[180,-90]],
    "paris_exact":[[0.999166666667,49.4163888889],[3.60111111111,48.3558333333]],
    "paris_metro_exact":[[1.87083333333,48.950],[2.8025,48.721944444444]],
    "intercités":[[-5.15111111111,51.0716666667],[9.56,41.3166666667]]
}

villesDispos = ["paris_metro_exact","paris_exact","paris2","toulouse","paris","londres","tae","rennes","delhi", "intercités"]
GPSCompte = ["tae", "paris_exact", "paris_metro_exact", "intercités"]
GTFS = ["intercités"]

#v0
penaliteStop = 0.015871629776914285 #15 secondes
penaliteCorres = penaliteStop * 4*5 #5 minutes

#v1
penaliteStopNew = 3 * 0.5377902478889645 / 7 #15 secondes
penaliteCorresNew = penaliteStopNew * 4*5 #5 minutes
penaliteAvion = 1500 #2h environ en avion

couleurDep = "#007900"
#couleurDep = "#00ff00"
couleurCorres = "#f4b342"
couleurArr = "#FF463D"

couleurCercle = "#c0c0c0"
bordureCercle = 4
rayonCercle = 12
dashCercle = (7, 8)
largeurTrait = 3

toleranceEcartPixel = 40
infini = 10**90
couleurCercleDefaut = "gray"
erreursReconnaissance = {\
"paris":"Vous n'avez pas sélectionné de station de Métro/Tram/Orlyval, je ne reconnais pas les RER C, D et E, ni Transiliens.",\
"toulouse":"Vous n'avez pas sélectionné de station du réseau",\
"paris2":"Vous n'avez pas sélectionné de station de Métro/Tram/Orlyval, je ne reconnais pas les RER C, D et E, ni Transiliens.",\
"londres":"Vous n'avez pas sélectionné de station du réseau que je connais. Je ne connais pas \"Woolwich Arsenal\", \"Langdon Park\" et \"Woodlane\", ni les stations de l'\"East London Line\" qui sont au sud de \"New Cross\" ou au nord de \"Shoreditch\"",\
"tae":"Vous n'avez pas sélectionné de ville desservie par le réseau TAE.",\
"rennes":"Vous n'avez pas sélectionné de station du réseau de métro.",\
"delhi":"Vous n'avez pas sélectionné de station du réseau de métro. Il y a des lignes que je ne connais pas encore..."}

hauteurBouton = 44

def distance(a,b, GPS=False):
    a, b = a[:], b[:]
    for element in (a,b):
        if type(element[0]) not in (int, float):
            coords = element[:]
            for i in range(2):
                element[i] = round((coords[0][i]+coords[1][i])/2)

    if GPS:
        deg2rad = lambda x: pi*x/180

        lat1, lon1, lat2, lon2 = map(deg2rad, (a[1], a[0], b[1], b[0]))
        resultat = 6378.137 * acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1))
    else:
        resultat = ((a[0]-b[0])**2+(a[1]-b[1])**2)**(1/2)
    return resultat

def identVille(ville): #fonction qui identifie la ville en cours de traitement
    ville = sys.argv[-1]
    ville = ville.lower()
    console = ville[-7:] == "_txt.py" or ville[-4:] == "_txt"
    if console: ville = ville[:-4]

    for villeDispo in villesDispos:
        if villeDispo in ville: ville = villeDispo; break
    if ville not in villesDispos: ville = villeParDefaut #ville par defaut

    return ville, console

def traitementNom(nomBrut):
    nom = ""
    for lettre in nomBrut:
        if lettre == "&": lettre = "&amp;"
        elif lettre == "\"": continue
        nom += lettre

    return nom

def adapteCoord(coord, idCoord, ville):
    eventailCoord = [NOSE[ville][1][0] - NOSE[ville][0][0], NOSE[ville][0][1] - NOSE[ville][1][1]]
    centre = [(NOSE[ville][1][0] - NOSE[ville][0][0]) / 2 + NOSE[ville][0][0], (NOSE[ville][0][1] - NOSE[ville][1][1]) / 2 + NOSE[ville][1][1]]

    coord -= centre[idCoord]

    newCoord = dimCarte[ville][idCoord] * coord / eventailCoord[idCoord] #on répartit les points sur l'axe de même largeur/hauteur que la carte, mais certaines coordonnées sont tjs négatives...
    newCoord += dimCarte[ville][idCoord]//2 #on centre les coords qui étaient à 0 auparavant

    if idCoord == 1: newCoord = dimCarte[ville][idCoord] - newCoord #les ordonnées augmentent en descendant, contrairement aux longitudes... On le compense

    return round(newCoord)

def contrasteur(couleurInit):
    r, g, b = int(couleurInit[:2],16), int(couleurInit[2:4],16), int(couleurInit[4:],16)
    if (r+g+b)/3 < 128: return "ffffff"
    else: return "000000"

txtHex = lambda x: str("0"+hex(x)[2:])[-2:]
def moyenneCouleur(couleurs):
    nbCouleurs = len(couleurs)

    total = [0,0,0]
    for couleur in couleurs:
        for i in range(3):
            total[i] += int(couleur[2*i:2*(i+1)], 16)

    moyR, moyG, moyB = total[0]//nbCouleurs, total[1]//nbCouleurs, total[2]//nbCouleurs

    return txtHex(moyR)+txtHex(moyG)+txtHex(moyB)

def couleurComp(couleur):
    r, g, b = int(couleur[:2],16), int(couleur[2:4],16), int(couleur[4:],16) #couleur de départ
    r, g, b = txtHex(255-r), txtHex(255-g), txtHex(255-b) #nouvelle couleur, complémentaire

    return r+g+b
