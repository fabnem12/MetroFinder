# -*- coding: utf8 -*-
import codecs, sys
import constantes as ctes
from cherche import lectureXMLLigne

#identification de la ville
ville, _ = ctes.identVille(sys.argv[-1])

lignes = ctes.lignesOK(ville)

gares = {}
coordImg = {}

for numLigne in lignes: #pour chaque ligne, on initialise les gares
    _, _, listeGares, _, _ = lectureXMLLigne(numLigne,ville, alt="Alt")

    for nomGare in listeGares: gares[nomGare] = []

def chercheInfos():
    for numLigne in lignes:
        with codecs.open("lignesAlt/"+ville+"/"+numLigne+".xml", "r", "utf-8") as fichierLigne:
            print("Recherche informations ligne",numLigne)

            contenu = fichierLigne.readlines() #lit le fichier de la ligne

            listeGares = []
            for nomGare in sorted(gares): listeGares.append(nomGare)

            for i in range(len(contenu)): #~ pour chaque ligne
                pos = i
                ligne = contenu[i]

                if "<gare" in ligne:
                    pos += 1 #si c'est une gare, elle a des voisins
                    nomGare = ligne.split("\"")[1].replace("&amp;","&")
                    coordImg[nomGare] = ligne.split("\"")[3]

                    while "<voisin" in contenu[pos]: #regarde chaque ligne qui suit la gare, tant que ce sont des voisins, puisque ce sont ses voisins
                        infosVoisin = contenu[pos].split("\"") #récupère des infos sur le voisin
                        nomVoisin, dist, ligneOrig = infosVoisin[1].replace("&amp;","&"), infosVoisin[3], numLigne.replace("&amp;","&")
                        gares[nomGare].append((nomVoisin, dist, ligneOrig))

                        pos += 1 #va a la ligne suivante

def ecritXMLVille():
    with codecs.open("reseau_"+ville+".xml", "w", "utf-8") as fichierDest: #écriture des données dans le fichier ville
        print("Démarrage de l'écriture des données...")

        fichierDest.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fichierDest.write("<data>\n")

        for nomGare in sorted(listeGares):
            coordGare = str(coordImg[nomGare])
            fichierDest.write("\t<gare nom=\""+nomGare.replace("&","&amp;")+"\" coord=\""+str(coordGare)+"\">\n")

            voisins = sorted(gares[nomGare])

            i = 0
            while i in range(len(voisins)):
                nomVoisin, dist, _ = voisins[i]

                lignes = []
                while i < len(voisins) and nomVoisin == voisins[i][0]:
                    lignes.append(voisins[i][2])
                    i += 1
                lignes = ",".join(lignes)

                fichierDest.write("\t\t<voisin nom=\""+nomVoisin.replace("&","&amp;")+"\" distance=\""+dist+"\" lignes=\""+str(lignes).replace("&","&amp;")+"\" />\n")

            fichierDest.write("\t</gare>\n")

            print("Gare", nomGare, "traitée")

        fichierDest.write("</data>")
##############################################################################################################################################
chercheInfos()
print("Recherche informations terminée...")
ecritXMLVille()
print("Écriture terminée!")
