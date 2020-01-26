# -*- coding: utf8 -*-
import codecs, sys, os
import constantes as ctes
from cherche import lectureXMLLigne, donnees

#CLASSES########################################################################
class Ligne():
    def __init__(self, num):
        self.num = num
        self.gares = dict()
        self.terminus = []

    def setGares(self, listeGares, terminus, coordImg, infosVoisins):
        for nomGare in listeGares:
            statut = "normal"
            if nomGare in terminus: statut = "terminus"

            gare = Gare(nomGare, coordImg[nomGare], infosVoisins[nomGare], statut, self)
            if statut == "terminus": self.terminus.append(gare)

            self.gares[nomGare] = gare

        for gare in self.gares.values():
            infosVoisins = gare.get("voisins")
            voisins = []

            for infosVoisin in infosVoisins:
                dist, nomVoisin, _ = infosVoisin
                try: voisins.append((dist, self.gares[nomVoisin], self))
                except KeyError:
                    print("Vérfiez sur la ligne",self.num,"que vous avez bien placé sur le plan la gare",nomVoisin)
                    print("Vous pouvez le faire sur le programme XMLCreator2.py")
                    print("Cordialement,\nUn développeur qui a perdu beaucoup de temps un dimanche à cause de cette erreur")
                    quit()

            gare.setVoisins(voisins)

    def get(self, demande):
        infos = {"num":self.num, "gares":self.gares, "terminus":self.terminus}

        return infos[demande]

class Gare():
    def __init__(self, nom, coordImg, nomVoisins, statut, ligne):
        global ville

        self.nom, self.statut, self.voisins = nom, statut, nomVoisins
        self.lignes = ligne
        self.coordImg = coordImg

    def setCoordImg(self, data): self.coordImg = data
    def setLignes(self, data): self.lignes = data
    def setStatut(self, data): self.statut = data
    def setVoisins(self, data): self.voisins = data

    def __gt__(self, compare): self.get("nom") > compare.get("nom")
    def __eq__(self, compare): self.get("nom") == compare.get("nom")

    def get(self, demande):
        infos = {"nom": self.nom, "coordImg":self.coordImg, \
                "statut":self.statut, "voisins":self.voisins, "ligne":self.lignes}

        return infos[demande]
#FIN CLASSES####################################################################

#FONCTIONS######################################################################
def elimineDoublons(listeGares):
    i = 0
    while i < len(listeGares):
        if nbOccurences(listeGares[i].nom, listeGares) > 1:
            del listeGares[i]
        else: i += 1

    return listeGares[:]

def nbOccurences(nom, listeGares):
    occurences = [gare for gare in listeGares if gare.get("nom") == nom]

    return len(occurences)

def unifierGares(correspondances, listeGaresVille):
    traites = []
    for gare in correspondances:
        nomGare = gare.get("nom")

        if nomGare not in traites:
            occurences = [x for x in listeGaresVille if x.get("nom") == gare.get("nom")]
            voisins = [x for occurence in occurences for x in occurence.get("voisins")]

            #Unification des coordonnées
            listeCoordImg = []
            for occurence in occurences:
                coordImg = occurence.get("coordImg")
                listeCoordImg.append(coordImg)

            rayonCercle = ctes.rayonCercle
            coordMin = [min([x[0] for x in listeCoordImg]),min([x[1] for x in listeCoordImg])]
            coordMax = [max([x[0] for x in listeCoordImg]),max([x[1] for x in listeCoordImg])]

            #Modifs des infos
            for occurence in occurences:
                occurence.setStatut("corres")
                occurence.setCoordImg([coordMin,coordMax])
                occurence.setVoisins(voisins)

            traites.append(nomGare)

def traitementCoord(coord, statut):
    if statut == "corres":
        coord = [str(coord[0])[1:-1],str(coord[1])[1:-1]]
        coord = "|".join(coord)
    else:
        coord = str(coord)[1:-1]

    return coord

def ecritXMLVille(ville, listeGaresVille):
    with codecs.open("reseauAlt_"+ville+".xml", "w", "utf-8") as fichierDest:
        print("Démarrage de l'écriture des données...")

        printF=fichierDest.write
        printF('<?xml version="1.0" encoding="UTF-8"?>\n')
        printF("<data>\n")

        for gare in sorted(elimineDoublons(listeGaresVille), key=lambda x:x.nom):
            nomGare = ctes.traitementNom(gare.get("nom"))
            if len(gare.get("voisins")) == 0: continue

            coord = traitementCoord(gare.get("coordImg"), gare.get("statut"))
            printF("\t<gare nom=\""+nomGare+"\" coord=\""+coord+"\">\n")

            voisins = dict()
            for infosVoisin in sorted(gare.get("voisins"), key=lambda x:x[1]):
                dist, voisin, ligneVoisin = infosVoisin

                dist = str(dist)

                nomVoisin, numLigneVoisin = voisin.get("nom"), ctes.traitementNom(ligneVoisin.get("num"))
                if nomVoisin not in voisins:
                    voisins[nomVoisin] = [dist, [numLigneVoisin]]
                else:
                    voisins[nomVoisin][1] += [numLigneVoisin]
                    voisins[nomVoisin][0] = min(voisins[nomVoisin][0], dist)

            for nomVoisin in sorted(voisins):
                dist, numLigneVoisin = voisins[nomVoisin]
                printF("\t\t<voisin nom=\""+ctes.traitementNom(nomVoisin)+"\" distance=\""+dist+"\" lignes=\""+",".join(sorted(numLigneVoisin))+"\" />\n")
            printF("\t</gare>\n")

        printF("</data>")
        print("Écriture terminée !")

    if ville in ctes.GPSCompte and "exact" in ville.lower():
        print("Calcul du nouveau fond de carte...")

        from planExact import init, traitementGare, ecritSVG
        dicoGares, couleursLignes, _ = init(ville)
        for gare in dicoGares.values(): traitementGare(gare, dicoGares, couleursLignes)
        ecritSVG(dicoGares, ctes.dimCarte[ville], ville)

        print("Terminé !")

#FIN FONCTIONS##################################################################

#PROGRAMME PRINCIPAL############################################################
#-Initialisation
def fusion(ville = ""):
    print("Recherche d'informations...")

    ville, _ = ctes.identVille(ville if ville != "" else sys.argv[-1])
    #ville = "paris2"

    if ville in ctes.GPSCompte: typeVal = float
    else: typeVal = int

    lignes = dict()
    for numLigne in ctes.lignesOK(ville):
        lignes[numLigne] = Ligne(numLigne)

    listeGaresVille = []
    for numLigne in lignes:
        gares, coordImg, listeGares, terminus, _ = lectureXMLLigne(numLigne, ville, alt="Alt", coordGPS=True)
        coordGPS = donnees(numLigne, "coord", ville)

        voisins = dict()
        for nomGare in listeGares:
            listeVoisins = gares[nomGare]

            voisins[nomGare] = [(gares[nomGare][voisin][0], voisin, lignes[numLigne]) for voisin in listeVoisins]
            coordImg[nomGare] = tuple(map(typeVal, coordImg[nomGare].split(", ")))

        lignes[numLigne].setGares(listeGares, terminus, coordImg, voisins)

        for nomGare in lignes[numLigne].get("gares"):
            listeGaresVille += [lignes[numLigne].get("gares")[nomGare]]

    listeGaresVille = [x for x in listeGaresVille if x.get("coordImg") != (0,0)]
    correspondances = [x for x in listeGaresVille if nbOccurences(x.get("nom"), listeGaresVille) > 1]
    unifierGares(correspondances, listeGaresVille)

    print("Recherche d'informations... Terminée !")
    #-Fin Initialisation

    #-Ecriture des données dans un fichier pour la ville
    ecritXMLVille(ville, listeGaresVille)
    #-Fin Écriture des données dans un fichier pour la ville

if __name__ == "__main__":
    fusion()
#FIN PROGRAMME PRINCIPAL########################################################
