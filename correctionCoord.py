# -*- coding: utf8 -*-
from tkinter import *
from tkinter.messagebox import *
from cherche import lectureXMLVille
from string import ascii_lowercase
from difflib import SequenceMatcher
import codecs, sys
import constantes as ctes

#Identification de la ville
ville, _ = ctes.identVille(sys.argv[-1])

lignes = ctes.lignesOK(ville)
dimCarte = ctes.dimCarte[ville]
fichierCarte = ctes.accesCartes+ville+".png"

_, coordImg = lectureXMLVille(ville) #récupère les coordonées sur la carte de chaque gare
gareIdent = "" #gareIdentfiée
gareRechercheeParNom = ""
enRecherche = False

#Fonctions -----------------------------------------------------------------------------------------------------------------------------------------
def sauvegarde(event=None):
    global coordImg

    for type in ["global", "ligne"]:
        if type == "global": #fichier données de la ville
            fichier = "reseau_"+ville
            aTraiter = [""]
            ajoutIdentation = ""
        else:
            fichier = "lignes/"+ville+"/"
            ajoutIndentation = "\t"
            aTraiter = lignes

        for numLigne in aTraiter: #pour chaque fichier ligne à traiter ou le fichier donnéees de la ville
            with codecs.open(fichier+numLigne+".xml", "r", "utf-8") as fichierEnCours: #lit les données du fichier
                contenu = fichierEnCours.readlines()

            with codecs.open(fichier+numLigne+".xml", "w", "utf-8") as fichierEnCours: #écrit sur le fichier
                for ligne in contenu:
                    if "<gare" in ligne: #met à jour les coordonnées sur le plan
                        infos = ligne.split("\"")
                        nomGare = infos[1]
                        coord = str(coordImg[nomGare])[1:-1]

                        ligne = ajoutIdentation + "\t<gare nom=\""+nomGare+"\" coord=\""+coord+"\">\n"

                    fichierEnCours.write(ligne)

    print("Sauvegarde effectuée avec succès")
    fenetre.destroy() #ferme la fenetre

def detCoord(event): #détermine les coordonnées sur la carte, en prenant en compte le scroll
    ecartX = int(defilX.get()[0]*dimCarte[0])
    ecartY = int(defilY.get()[0]*dimCarte[1])

    return (event.x+ecartX, event.y+ecartY)

#Identification des gares
def identGare(event, coord="", nomGare=""): #identifie la gare par coordonnees
    global coordImg, gareIdent

    if nomGare != "": coord = coordImg[nomGare]
    if coord == "" and nomGare == "": coord = detCoord(event)

    possibles = []

    for nomGare in coordImg:
        coordGare = coordImg[nomGare]
        try:
            dist = ctes.distance(coord, coordGare)
        except:
            print("coord",coord,"coordGare",coordGare)
            sys.exit()
        if dist < ctes.toleranceEcartPixel:
            possibles.append((dist, nomGare))

    if gareIdent != "": canvasCarte.itemconfig(cercles[gareIdent], outline=ctes.couleurCercle)
    if len(possibles) != 0:
        gareIdent = min(possibles)[1]
        canvasCarte.itemconfig(cercles[gareIdent], outline=ctes.couleurCorres)
    else:
        gareIdent = ""

    gareEnCours.config(text="Gare selectionnee : "+gareIdent)

def identGareParNom(nom): #identifie la gare par nom
    global coordImg

    possibles = []
    for nomGare in coordImg:
        if nom.lower() in nomGare.lower():
            possibles.append(nomGare)
    possibles.sort()

    return possibles


def clic(event): #déplacer le cercle sélectionné à l'endroit où l'on a cliqué
    global coordImg, gareIdent, coordImg

    if gareIdent != "":
        coord = detCoord(event)
        coordAv = coordImg[gareIdent]

        delta = (coord[0]-coordAv[0], coord[1]-coordAv[1])

        changeCoord(delta)

def changeCoord(delta): #déplace le cercle et change les données
    global gareIdent, coordImg, cercles

    if gareIdent != "":
        coordAv = coordImg[gareIdent]
        coord = [coordAv[0]+delta[0], coordAv[1]+delta[1]]

        canvasCarte.move(cercles[gareIdent], delta[0], delta[1])
        coordImg[gareIdent] = coord

def chercheGareParNom(event):
    global coordImg, enRecherche, gareRechercheeParNom, gareIdent

    if enRecherche:
        if gareRechercheeParNom != "" and event.keycode in (36,37): #touche ctrl gauche ou entree enfoncee
            possibles = identGareParNom(gareRechercheeParNom)
            if len(possibles) == 1 or gareRechercheeParNom.lower() in [nomGare.lower() for nomGare in possibles]:
                nomGare = possibles[0]
                identGare(0, nomGare=nomGare)

                #deplacer la vue de la carte pour la centrer autour de la gare selectionnee
                operations = [canvasCarte.xview, canvasCarte.yview]
                for i in range(2):
                    deplacement = (coordImg[nomGare][i] - dimCanvasCarte[i]//2) / dimCarte[i]
                    operations[i]("moveto", deplacement)

            elif len(possibles) == 0: showinfo("Attention","Je n'ai pas trouve de resultat...")
            else:
                showinfo("Attention","Trop de resultats correspondent a cette recherche, soyez plus precis en refaisant une nouvelle recherche. J'ai trouve :"+str(possibles))

            enRecherche = False
        else:
            if event.keycode == 22: #touche retour arriere enfoncee
                gareRechercheeParNom = gareRechercheeParNom[:-1]
            else:
                try: gareRechercheeParNom += event.char
                except: gareRechercheeParNom += " "

            gareEnCours.configure(text="Recherche de gare : "+gareRechercheeParNom)

    if not enRecherche and event.keycode in (36,37): #trouche ctrl gauche ou entree enfoncee
        enRecherche = True

        gareRechercheeParNom = ""
        gareEnCours.configure(text="Recherche de gare")

def fleches(event):
    global gareIdent

    touche = event.keysym

    actions = {"Left":(-1,0), "Right":(1,0), "Up":(0,-1), "Down":((0,1))}
    if touche in actions:
        if gareIdent != "": changeCoord(actions[touche])
        else:
            x, y = actions[touche]
            deplaceAscenseur(x,y)

#support de la molette sur linux et windows
def ascenseurVertWindows(event):
    if event.delta > 0: deplaceAscenseur(0,-1)
    else: deplaceAscenseur(0,1)
def ascenseurHoriWindows(event):
    if event.delta > 0: deplaceAscenseur(-1,0)
    else: deplaceAscenseur(1,0)
def monteAscenseur(event): deplaceAscenseur(0,-1)
def descendAscenseur(event): deplaceAscenseur(0,1)
def gaucheAscenseur(event): deplaceAscenseur(-1,0)
def droiteAscenseur(event): deplaceAscenseur(1,0)
def deplaceAscenseur(x, y):
    canvasCarte.xview("scroll", x, "units")
    canvasCarte.yview("scroll", y, "units")
#UI ------------------------------------------------------------------------------------------------------------------------------------------------
fenetre = Tk()
fenetre.title("Correction des coordImg"+ville)
tailleEcran = (fenetre.winfo_screenwidth(), fenetre.winfo_screenheight())
fenetre.geometry("x".join(map(str, tailleEcran)))

fonctionnel = PanedWindow(fenetre, orient=VERTICAL)
gareEnCours = Label(fonctionnel, text="Pas de gare selectionnee")

#Carte
fCarte = Frame(fenetre, bd=0)
carte = PhotoImage(file=fichierCarte)

#adapte la carte à l'écran
dimCanvasCarte = ctes.dimCanvasCarte
ecartOblig = ctes.ecartOblig
for i in range(2):
    dimCanvasCarte[i] = tailleEcran[i]
    if tailleEcran[i] < dimCanvasCarte[i] + ecartOblig[i]: dimCanvasCarte[i] -= ecartOblig[i]

w, h = dimCarte
canvasCarte = Canvas(fCarte,width=dimCanvasCarte[0], height=dimCanvasCarte[1], scrollregion=(0, 0, w, h))
canvasCarte.create_image(0, 0, anchor=NW, image=carte)

cercles = {}

for nomGare in coordImg: #affiche un cercle pour chaque gare
    coord = coordImg[nomGare]
    couleur = ctes.couleurCercle
    rayon, bordure, dash = ctes.rayonCercle, ctes.bordureCercle, ctes.dashCercle

    cercles[nomGare] = canvasCarte.create_oval(coord[0]-rayon, coord[1]-rayon, coord[0]+rayon, coord[1]+rayon, outline=couleur, width=bordure, dash=dash)

canvasCarte.grid(row=0, column=0)

#Scrollbars
defilY = Scrollbar(fCarte, orient='vertical',
    command=canvasCarte.yview)
defilY.grid(row=0, column=1, sticky='ns')

defilX = Scrollbar(fCarte, orient='horizontal',
    command=canvasCarte.xview)
defilX.grid(row=1, column=0, sticky='ew')

canvasCarte['xscrollcommand'] = defilX.set
canvasCarte['yscrollcommand'] = defilY.set

#Structure
fonctionnel.add(gareEnCours)
fonctionnel.add(fCarte)

fonctionnel.pack()

canvasCarte.bind("<Button-3>", identGare) #clic droit -> identifie une gare
canvasCarte.bind_all("<Key>", fleches) #fleches -> on déplace finement le cercle sélectionné
canvasCarte.bind_all("<Control_L>", chercheGareParNom) #debuter une recherche de gare par nom
for lettre in list(ascii_lowercase)+["<space>"]: canvasCarte.bind_all(lettre, chercheGareParNom) #capter les lettres de la recherche par nom
canvasCarte.bind_all("<BackSpace>", chercheGareParNom) #effacer la derniere lettre
canvasCarte.bind_all("<Return>", chercheGareParNom) #effectuer la recherche

#Gere la molette pour linux et windows + clic gauche, sur canvasCarte
commandes = {"<Button-1>":clic,"<Button-4>":monteAscenseur, "<Button-5>":descendAscenseur, "<Shift-Button-4>":gaucheAscenseur, "<Shift-Button-5>":droiteAscenseur, "<MouseWheel>":ascenseurVertWindows, "<Shift-MouseWheel>":ascenseurHoriWindows}

for commande in commandes: canvasCarte.bind(commande, commandes[commande])

fenetre.protocol("WM_DELETE_WINDOW", sauvegarde) #sauvegarde à la fermeture de la fenetre
fenetre.mainloop()
