# -*- coding: utf8 -*-
import csv, codecs, os
import constantes as ctes
import xml.etree.ElementTree as ET

from coordTAE2 import retrouveTAE

def donnees(ligneCherche, requete, ville): #cherche les données CSV
	gares = dict()
	for ligne in ctes.lignesOK(ville, creation=True): gares[ligne] = []

	if "paris" in ville:
		fichier = "csv-data/paris.csv"
	elif ville == "londres":
		gares = {ligneCherche:[]}
		if ligneCherche != "pedestre": gares["pedestre"] = []
		fichier = "csv-data/londres-stations.csv"
	else:
		fichier = "csv-data/"+ville+".csv"

	coordGPS = dict()

	with codecs.open(fichier, 'r', "utf-8") as csvfile: #ouvre le fichier csv de la ville traitée
		reader = csv.reader(csvfile, delimiter=";", quotechar=" ") #extrait les données

		for row in reader:
			if "paris" in ville:
				if row[-14] in gares: #on vérifie que la ligne fait partie des lignes supportées
					if requete == "gares": gares[row[-14]].append(row[7]); gares["pedestre"].append(row[7])
					if requete == "coord":
						coordGPS[row[7]] = list(map(float, row[0].split(", "))) #extrait les coordonnées GPS à partir du texte
						if "exact" in ville: coordGPS[row[7]] = coordGPS[row[7]][::-1]
			elif "toulouse" in ville:
				if requete == "gares": gares[row[3]].append(row[2]); gares["pedestre"].append(row[2])
				if requete == "coord": coordGPS[row[2]] = list(map(float, row[0].split(", ")))
			elif "londres" in ville:
				if requete == "gares" and ligneCherche == "pedestre": gares["pedestre"].append(row[3][1:-1])
				if requete == "coord": coordGPS[row[3][1:-1]] = list(map(float, row[1:3]))
			elif "rennes" in ville:
				if requete == "gares": gares[row[2]].append(row[4])
				if requete == "coord": coordGPS[row[4]] = list(map(float, row[0].split(", ")))
			elif "delhi" in ville:
				if requete == "gares": gares[row[1]].append(row[2]); gares["pedestre"].append(row[2])
				if requete == "coord": coordGPS[row[2]] = list(map(float, row[0].split(", ")))
			elif "tae" in ville and len(row) > 0:
				if requete == "gares": gares[ligneCherche].append(row[1])
				if requete == "coord": coordGPS[row[1]] = list(map(float, row[0].split(", ")))

	if "londres" in ville and requete == "gares" and ligneCherche != "pedestre":
		_, _, listeGares, _, _ = lectureXMLLigne(ligneCherche, "londres", alt="Alt")

		gares[ligneCherche] = listeGares[:]

	if requete == "gares": return sorted(gares[ligneCherche])
	if requete == "coord": return coordGPS

def lectureXMLLigne(numLigne, ville, alt="", coordGPS=False): #récupère les infos des lignes déjà enregistrées au format XML
	fichier = "lignes"+alt+"/"+ville+"/"+numLigne+".xml"

	listeGares = []
	gares = dict()
	coordImg = dict()
	terminus = []
	couleur = "ffffff"

	a = int
	if ville in ctes.GPSCompte: a = lambda x: float(x)

	try:
		arbre = ET.parse(fichier) #extrait les données du XML
	except ET.ParseError as dataErreur:
		print("ohe", numLigne, dataErreur)
		return gares, coordImg, listeGares, terminus, couleur
	ligne = arbre.getroot()

	terminus = ligne.attrib["terminus"].split(",")
	if alt != "":
		try:
			couleur = ligne.attrib["couleur"]
		except:
			couleur = ctes.couleursLignes(ville, numLigne)
	else: couleur = ""

	for gare in ligne:
		nomGare = gare.attrib["nom"]
		listeGares.append(nomGare)
		gares[nomGare] = {}
		coordImg[nomGare] = gare.attrib["coord"]

		if ville in ctes.GPSCompte and not coordGPS:
			coordImg[nomGare] = list(map(a, coordImg[nomGare].split(", ")))
			for i in range(2): coordImg[nomGare][i] = str(round(ctes.adapteCoord(coordImg[nomGare][i], i, ville)))
			coordImg[nomGare] = ", ".join(coordImg[nomGare])

		for voisin in gare:
			nomVoisin = voisin.attrib["nom"]
			distVoisin = float(voisin.attrib["distance"])
			ligneVoisin = numLigne

			gares[nomGare][nomVoisin] = (distVoisin, ligneVoisin)

	return gares, coordImg, listeGares, terminus, couleur

def lectureXMLVille(ville, alt=""):
	"""Génère les dictionnaires gares et coordImg exploitables par le prog principal."""
	a = int
	if ville in ctes.GPSCompte: a = lambda x: float(x)

	fichier = "reseau"+alt+"_"+ville+".xml"
	if ville == "tae":
		retrouveTAE()

	gares = dict()
	coordImg = dict()

	arbre = ET.parse(fichier)
	racine = arbre.getroot()

	for gare in racine:
		nomGare = gare.attrib["nom"].replace("&amp;","&")
		if "|" not in gare.attrib["coord"]:
			coordImg[nomGare] = list(map(a, gare.attrib["coord"].split(", ")))

			if ville in ctes.GPSCompte:
				coordGPSGare, coord = coordImg[nomGare].copy(), coordImg[nomGare].copy()
				for i in range(2):
					coord[i] = round(ctes.adapteCoord(coord[i], i, ville))
				coordImg[nomGare] = (coordGPSGare, coord)
		else:
			coord = gare.attrib["coord"].split("|")
			coordImg[nomGare] = [list(map(a, coord[0].split(", "))), list(map(a, coord[1].split(", ")))]
			if ville in ctes.GPSCompte:
				coord, coordGPSGare = coordImg[nomGare].copy(), coordImg[nomGare][0].copy()
				for i in range(2):
					for j in range(2):
						coord[i][j] = round(ctes.adapteCoord(coord[i][j], j, ville))
				coordImg[nomGare] = (coordGPSGare, coord)

		gares[nomGare] = {}

		for voisin in gare: #permet d'ajouter autant de voisins que nécessaire
			nomVoisin = voisin.attrib["nom"].replace("&amp;","&")
			distVoisin = float(voisin.attrib["distance"])
			lignesVoisin = voisin.attrib["lignes"].split(",")
			for ligne in lignesVoisin: ligne.replace("&amp;","&")

			gares[nomGare][nomVoisin] = (distVoisin, lignesVoisin)

	return gares, coordImg
