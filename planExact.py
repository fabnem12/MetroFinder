# -*- coding: utf8 -*-
from cherche import donnees, lectureXMLLigne, lectureXMLVille
from cairosvg import svg2png
import constantes as ctes
import sys

largeurCarte = 4000 #la hauteur est définie en fonction de la largeur, puisque l'on veut qu'il y ait la même échelle sur l'axe nord-sud que ouest-est
infini = ctes.infini
marge = ctes.marge

#marge = 0

#Classes
class Gare():
    def __init__(self, nom, coord, voisinsBruts):
        self.nom, self.coord, self.voisins = nom, coord, voisinsBruts #voisinsBruts car on n'a que leurs noms, l'idée étant de remplacer à terme les noms par les objets
    def setVoisins(self, nouvVoisins):
        self.voisins = nouvVoisins
#Fin Classes

#Fonctions
def init(ville=""):
    if ville == "": ville, console = ctes.identVille(sys.argv[-1])
    if ville not in ctes.GPSCompte: print("Je ne fais pas de plan géographiquement exact pour les villes qui ne sont pas compatibles !"); quit()

    infosGares, dicoCoord = lectureXMLVille(ville, alt="Alt")
    for element in dicoCoord:
        if type(dicoCoord[element][0]) in (list, tuple): dicoCoord[element] = dicoCoord[element][1]

    couleursLignes = dict()
    for ligne in ctes.lignesOK(ville):
        _, _, _, _, couleur = lectureXMLLigne(ligne, ville, alt="Alt")
        couleursLignes[ligne] = couleur

    dicoGares = dict()
    for gare in dicoCoord:
        coord = dicoCoord[gare]
        if type(coord[0]) == list: #deux coordonnées sont indiquées, on fait donc la moyenne
            newCoord = []
            for i in range(2):
                moyenne = round((dicoCoord[gare][0][i] + dicoCoord[gare][1][i]) / 2)
                newCoord.append(moyenne)

            coord = newCoord.copy()

        voisinsBruts = [(nomVoisin, infosGares[gare][nomVoisin][1]) for nomVoisin in infosGares[gare]]

        dicoGares[gare] = Gare(gare, coord, voisinsBruts)

    return dicoGares, couleursLignes, ville

def traitementGare(gare, dicoGares, couleursLignes):
    nouvVoisins = []
    for nomVoisin, lignes in gare.voisins:
        if lignes == ["pedestre"]: continue

        couleursDesLignesDuVoisin = [couleursLignes[ligne] for ligne in lignes if ligne != "pedestre"]
        moyenneCol = ctes.moyenneCouleur(couleursDesLignesDuVoisin)

        voisin = dicoGares[nomVoisin]

        nouvVoisins.append((voisin, moyenneCol))

    gare.setVoisins(nouvVoisins)

def ecritSVG(dicoGares, dimCarte, ville):
    txt = "<?xml version=\"1.0\" standalone=\"no\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\""+str(dimCarte[0])+"\" height=\""+str(dimCarte[1])+"\">\n"
    txt += '\n<defs><style>.gare {stroke:#000; fill:#fff;}</style></defs>'

    for gare in dicoGares.values():
        nom, coord, voisins = gare.nom, gare.coord, gare.voisins
        if "(" in nom: nom = nom[:nom.index("(")]

        txt += "\n\t<circle id=\""+nom+"\" cx=\""+str(coord[0])+"\" cy=\""+str(coord[1])+"\" r=\"2\" class=\"gare\" />"
        for voisin, couleur in voisins:
            coordVoisin = voisin.coord
            txt += "\n\t<line x1=\""+str(coord[0])+"\" y1=\""+str(coord[1])+"\" x2=\""+str(coordVoisin[0])+"\" y2=\""+str(coordVoisin[1])+"\" style=\"fill:#"+couleur+";stroke:#"+couleur+";\" />"

    txt += "\n</svg>"

    """with open("images/"+ville+".svg","w") as fichierSVG:
        fichierSVG.write(txt)"""
    conversion(txt, ville)

def conversion(codeSVG, ville):
    svg2png(bytestring=codeSVG,write_to="images/"+ville+'.png')

    from PIL import Image
    fond = Image.open("images/carte-"+ville+".png")
    interessant = Image.open("images/"+ville+".png")

    fond.paste(interessant, (0,0), interessant)
    fond.save("images/"+ville+".png")

#Fin Fonctions

#Programme principal
dicoGares, couleursLignes, ville = init()
for gare in dicoGares.values(): traitementGare(gare, dicoGares, couleursLignes)
ecritSVG(dicoGares, ctes.dimCarte[ville], ville)
