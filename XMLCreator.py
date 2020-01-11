# -*- coding: utf8 -*-
from tkinter import *
from tkinter.messagebox import *
from cherche import donnees, lectureXMLLigne
import codecs, sys
import constantes as ctes

#Identification de la ville
ville, _ = ctes.identVille(sys.argv[-1])

#Variables ------------------------------------------------------------------------------------------------------------------------------------------------------------------
lignes = ctes.lignesOK(ville, creation=True)
dimCarte = ctes.dimCarte[ville]
numLigne = lignes[0] #ligne par défaut
fichierCarte = ctes.accesCartes+ville+".png"

def init(): #initialisation des données
    global gareSelectionnee, coordImg, garesDeso, coordGPS, garesOrdo, numLigne

    gareSelectionnee = None
    _, coordImg, garesOrdo, terminus = lectureXMLLigne(numLigne, ville) #récupère autant d'informations déjà sur XML que possible
    garesDeso = donnees(numLigne, "gares", ville) #récupère les données CSV
    for nomGare in garesOrdo:
        if nomGare in garesDeso: garesDeso.remove(nomGare) #retire les gares CSV qui ont déjà été enregistrées en XML
    coordGPS = donnees(numLigne, "coord", ville)

init()

#Création ligne -------------------------------------------------------------------------------------------------------------------------------------------------------------
def creationLigne(numLigne, gares, coordGPS, coordImg):
    with codecs.open("lignes/"+ville+"/"+numLigne+".xml", 'w', 'utf-8') as fichier:
        fichier.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        terminus = gares[0]+","+gares[-1]
        fichier.write("<ligne terminus=\"" + terminus + "\">\n")
        nbGares = len(gares)
        for idGare in range(nbGares):
            nomGare = gares[idGare]
            try:
                coordIm = str(coordImg[nomGare])[1:-1]
            except KeyError: #si on n'a pas renseigné les coordonnées sur le plan, valeur par défaut
                coordIm = "0, 0"
            fichier.write("\t<gare nom =\"" + nomGare + "\"" + " coord =" + "\"" + str(coordIm) + "\"" + ">\n")
            voisins = []
            if idGare != nbGares - 1:
                nomVoisin = gares[idGare + 1]
                coordGPSVoisin = coordGPS[nomVoisin]
                voisins.append((nomVoisin , coordGPSVoisin))
            if idGare != 0:
                nomVoisin = gares[idGare - 1]
                coordGPSVoisin = coordGPS[nomVoisin]
                voisins.append((nomVoisin , coordGPSVoisin))
            for tuple in voisins:
                nomVoisin = tuple[0]
                coordGPSVoisin = tuple[1]
                dist = ctes.distance(coordGPS[nomGare],coordGPSVoisin)
                fichier.write("\t\t<voisin nom =\"" + nomVoisin + "\"" + " distance =" + "\"" + str(dist) + "\"" + "/>\n")
            fichier.write("\t</gare>\n")
        fichier.write("</ligne>")

    showinfo("Information", "J'ai fini ton XML pour la ligne "+numLigne)

#Fonctions affichage --------------------------------------------------------------------------------------------------------------------------------------------------------
def ligneSel(event): #selection de la ligne à traiter
    global numLigne, garesDeso, garesOrdo

    selec = listeLignes.curselection()
    if selec != ():
        selec = selec[0]
        numLigne = lignes[selec]
        ligne.config(text="Ligne "+numLigne) #affiche le numéro de ligne à traiter

        #change les gares à traiter pour mettre celles de la ligne en question
        listeDesordonnee.delete(0, "end")
        listeOrdonnee.delete(0, "end")
        garesOrdo = []
        init()

        if len(garesOrdo) == 0: showinfo("Attention", "Fichier inexistant ou vide") #si pas de données XML

        for nomGare in garesDeso:
            listeDesordonnee.insert("end", nomGare)
        for nomGare in garesOrdo:
            listeOrdonnee.insert("end", nomGare)
            if nomGare in coordImg and str(coordImg[nomGare]) != "(0, 0)":
                listeOrdonnee.itemconfig("end", {"bg": ctes.couleurDep})

def gareSelDeso(event): #sélection parmi les désordonnés, qui n'ont pas de trace de leur présence sur le XML
    global gareSelectionnee

    selec = listeDesordonnee.curselection()
    if selec != ():
        selec = selec[0]
        gareSelectionnee = garesDeso[selec]
        garesDeso.remove(gareSelectionnee)
        listeDesordonnee.delete(selec)

        ordonnes(gareSelectionnee)

def gareSelOrdo(event): #sélection parmi les ordonnés, qui sont dans le bon ordre logique de la ligne
    global gareSelectionnee

    selec = listeOrdonnee.curselection()
    if selec != ():
        selec = selec[0]
        gareSelectionnee = garesOrdo[selec]

def clic(event): #détermine les coordonées sur la carte à appliquer à la gare sélectionnée
    global coordGare, gareSelectionnee

    if gareSelectionnee != None:
        ecartX = int(defilX.get()[0]*dimCarte[0]) #calcul de l'écart, cf fichier beta.py pour explications
        ecartY = int(defilY.get()[0]*dimCarte[1])

        coordImg[gareSelectionnee] = (event.x+ecartX, event.y+ecartY)

        indexNouv = garesOrdo.index(gareSelectionnee) + 1 #sélectionne la gare suivante dans la liste, après avoir attribué à la gare courante ses coordonnées
        listeOrdonnee.itemconfig(indexNouv - 1, {"bg": ctes.couleurDep})
        listeOrdonnee.selection_clear(indexNouv - 1) #déselectionne la gare traitée, car sinon plusieurs gares pourraient être sélectionnées en même temps

        if indexNouv < len(garesOrdo): #toutes les gares de la liste, sauf la dernière
            gareSelectionnee = garesOrdo[indexNouv] #change la gare sélectionnée dans la liste
            listeOrdonnee.selection_set(indexNouv)

def ordonnes(gareSelectionnee): #ajoute une gare à la liste des gares ordonéees
    global garesOrdo

    garesOrdo.append(gareSelectionnee)
    listeOrdonnee.insert("end", gareSelectionnee)

def bouge(sens, index): #déplacer une gare dans la liste des ordonnés, en cas d'erreur
    global gareSelectionnee, garesOrdo

    fond = listeOrdonnee.itemconfig(index, "background")
    police = listeOrdonnee.itemconfig(index, "fg")

    listeOrdonnee.delete(index)
    listeOrdonnee.insert(index + sens, gareSelectionnee)
    listeOrdonnee.itemconfig(index + sens, {"fg": police[4], "bg": fond[4]})
def monteOrdo(): #monter une gare
    global gareSelectionnee, garesOrdo

    index = garesOrdo.index(gareSelectionnee)
    if index != 0: #si on n'a pas sélectionné la première gare
        garesOrdo[index - 1], garesOrdo[index] = gareSelectionnee, garesOrdo[index - 1]

        bouge(-1, index)
def descendOrdo(): #descendre une gare
    global gareSelectionnee, garesOrdo

    index = garesOrdo.index(gareSelectionnee)
    if index != len(garesOrdo) - 1: #si on n'a pas sélectionné la dernière gare
        garesOrdo[index], garesOrdo[index + 1] = garesOrdo[index + 1], gareSelectionnee

        bouge(1, index)

def conversion(): #enregistrement des données au format XML
    global numLigne, garesOrdo, coordGPS, coordImg

    creationLigne(numLigne, garesOrdo, coordGPS, coordImg)

#support de la molette + fleches directionnelles sur linux et windows
def fleches(event):
    touche = event.keysym
    actions = {"Left":(-1,0), "Right":(1,0), "Up":(0,-1), "Down":((0,1))}
    if touche in actions:
        x, y = actions[touche]
        deplaceAscenseur(x,y)
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

#Tkinter --------------------------------------------------------------------------------------------------------------------------------------------------------------------
fenetre = Tk()
fenetre.title("Ajouter une ligne à "+ville.capitalize())
fLignes = Toplevel(fenetre)
fLignes.transient(fenetre)

#structure de l'interface
fonctionnel = PanedWindow(fenetre, orient=VERTICAL)
p = PanedWindow(fonctionnel, orient=HORIZONTAL)
listeDeso = PanedWindow(p, orient=VERTICAL)
listeOrdo = PanedWindow(p, orient=VERTICAL)

#Menu -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
menubar = Menu(fenetre)

menubar.add_command(label="Vers XML !", command=conversion) #bouton pour sauvegarder au format XML

#permet de choisir quelle ligne traiter
fLignes.title("Numéro des lignes")
fLignes.protocol("WM_DELETE_WINDOW", fLignes.iconify)
listeLignes = Listbox(fLignes)

for ligne in lignes: #affiche toutes les lignes pouvant être traitées
    listeLignes.insert("end", ligne)
listeLignes.pack()

ligne = Label(fonctionnel, text="Ligne "+numLigne) #affiche la ligne en cours de traitement

#Carte ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
fCarte = Frame(p, bd=0)

carte = PhotoImage(file=fichierCarte)
w, h = dimCarte
dimCanvasCarte = ctes.dimCanvasCarte

canvasCarte = Canvas(fCarte, width=dimCanvasCarte[0], height=dimCanvasCarte[1], scrollregion=(0, 0, w, h))
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

#Image
canvasCarte.create_image(0, 0, anchor=NW, image=carte)

#Liste désordonnée ----------------------------------------------------------------------------------------------------------------------------------------------------------
labelDeso = Label(listeDeso, text="Désordonnés")

listeDesordonnee = Listbox(listeDeso)

for i in range(len(garesDeso)):
    listeDesordonnee.insert(i, garesDeso[i])

#Liste ordonnée -------------------------------------------------------------------------------------------------------------------------------------------------------------
labelOrdo = Label(listeOrdo, text="Ordonnés")

listeOrdonnee = Listbox(listeOrdo, selectbackground="yellow", selectforeground=ctes.couleurArr, selectmode="single")
for nomGare in garesOrdo:
    listeOrdonnee.insert("end", nomGare)
    if nomGare in coordImg and str(coordImg[nomGare]) != "0, 0":
        listeOrdonnee.itemconfig("end", {"bg": ctes.couleurDep})

boutonsOrdo = PanedWindow(listeOrdo, orient=HORIZONTAL)
btHaut = Button(boutonsOrdo, text="Monter", command=monteOrdo) #bouton pour monter une gare
btBas = Button(boutonsOrdo, text="Descendre", command=descendOrdo) #bouton pour descendre une gare

boutonsOrdo.add(btHaut)
boutonsOrdo.add(btBas)

#Organisation ---------------------------------------------------------------------------------------------------------------------------------------------------------------
hauteurListes = dimCanvasCarte[1] - ctes.hauteurBouton

listeDeso.add(labelDeso)
listeDeso.add(listeDesordonnee, height=hauteurListes)

listeOrdo.add(labelOrdo)
listeOrdo.add(listeOrdonnee, height=hauteurListes)
listeOrdo.add(boutonsOrdo)

p.add(fCarte)
p.add(listeDeso)
p.add(listeOrdo)

fonctionnel.add(ligne)
fonctionnel.add(p)

fonctionnel.pack()

#Programme principal --------------------------------------------------------------------------------------------------------------------------------------------------------
fenetre.config(menu=menubar)

#Gere la molette pour linux et windows + clic gauche, sur canvasCarte
commandes = {"<Button-1>":clic,"<Button-4>":monteAscenseur, "<Button-5>":descendAscenseur, "<Shift-Button-4>":gaucheAscenseur, "<Shift-Button-5>":droiteAscenseur, "<MouseWheel>":ascenseurVertWindows, "<Shift-MouseWheel>":ascenseurHoriWindows}
for commande in commandes: canvasCarte.bind(commande, commandes[commande])
canvasCarte.bind_all("<Key>", fleches)

#sélection d'une gare ou d'une ligne
listeDesordonnee.bind("<<ListboxSelect>>", gareSelDeso)
listeOrdonnee.bind("<<ListboxSelect>>", gareSelOrdo)
listeLignes.bind("<<ListboxSelect>>", ligneSel)

if len(garesOrdo) == 0: showinfo("Attention", "Fichier inexistant ou vide")

fenetre.mainloop()
