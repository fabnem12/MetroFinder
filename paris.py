# -*- coding: utf8 -*-
from cherche import lectureXMLVille, lectureXMLLigne
from heapq import *
from random import choice
import sys, smtplib
import constantes as ctes

#-----------------------------------------------------------------------------------------------------------------------------------#
# Initialisation -------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------------------------------#
#Identification de la ville
ville, console = ctes.identVille(sys.argv[-1])
#ville = "paris2"

fichierCarte = ctes.accesCartes+ville+".png"
dimCarte = ctes.dimCarte[ville]

gares, coordImg = lectureXMLVille(ville) #recupere toutes les infos du graphe de la ville selectionnee

#Init globale
if not console:
    from tkinter import *
    from tkinter.messagebox import *

depArrInit = ("Selectionner une gare de depart", "Selectionner une gare d'arrivee")
depart, arrivee = depArrInit
departModifie = False #permet de jongler entre modifier le depart et l'arrivee, si false, on modifie le depart, si true on modifie l'arrivee
chemin = []
cercles = []
rondDep = rondArr = 0

#-----------------------------------------------------------------------------------------------------------------------------------#
# Fonctions ------------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------------------------------#
def chercheGare(etape): #console uniquement
    possibles = []; idPossible = 10**9

    while len(possibles) == 0:
        requete = input(etape.capitalize()+" :")
        possibles = recherche(None, requete)
    while idPossible >= len(possibles):
        idPossible = input("Numero de la gare souhaitee : ")
        if idPossible != "": idPossible = int(idPossible)-1
        else: idPossible = 10**9

    return possibles[idPossible]

def calculIti():
    """parcours en profondeur pour Dijkstra"""
    global depart, arrivee, chemin, gares, changements

    if depart != arrivee:
        chemin = []

        #calcul du chemin en lui-meme
        infos = itineraireDijkstra(gares, depart, arrivee)
        cheminement(infos, depart, arrivee) #genere un chemin

        afficheChemin()

        #remettre les affichages de depart et arrivee en fond blanc
        if not console:
            for i in range(1, len(changements)): changements[i].config(bg="white")

def itineraireDijkstra(gares, depart, arrivee): #algorithme de Dijkstra
    tas = []; heapify(tas) #cree une liste de gares a traiter, et la transforme en tas
    traites = [depart] #pour se rappeler quelles gares ont deja ete traitees, initialise au sommet de depart
    infos = {} #toutes les infos necessaires pour etablir le chemin le plus court suite au itineraire Dijkstra
    for nomGare in gares: infos[nomGare] = []

    #donnees initiales
    distCumSommet, lignesPrec = 0, [""]
    nomSommet = depart

    tasPrec = []
    while len(gares) != len(traites): #on regarde si toutes les gares ont ete traitees ou pas
        for nomVoisin in gares[nomSommet]:
            dist, lignesTroncon = gares[nomSommet][nomVoisin] #longueur et lignes du troncon etudie

            if nomVoisin not in traites:
                lignesCommunes = list(set(lignesPrec) & set(lignesTroncon)) #(intersection d'ensembles)
                if len(lignesCommunes) != 0:
                    lignes = lignesCommunes
                else:
                    dist += ctes.penaliteCorres
                    lignes = lignesTroncon
                heappush(tas, (distCumSommet+dist, nomVoisin, nomSommet, lignes))

        if len(tas) == 0 and "pedestre" in lignes:
            return infos
        else:
            distCumSommet, nomSommet, depuis, lignesPrec = heappop(tas) #on recupere le troncon en haut du tas
            if nomSommet not in traites: traites.append(nomSommet)
            dist, _ = gares[depuis][nomSommet]
            infos[nomSommet].append((distCumSommet+dist, depuis, lignesPrec))

    return infos

def cheminement(infos, depart, arrivee):
    """determine le chemin le plus court a partir des infos preparees par la fonction precedente, en remontant a rebours, de l'arrivee au depart. Algorithme recursif."""
    global chemin, gares

    if depart != arrivee: #Tant que l'on doit remonter a rebours
        #determine le voisin le plus proche du point de depart
        distMini = ctes.infini
        nomMini = ""
        lignesMini = ""
        for voisin in infos[arrivee]:
            distVoisin, _, _ = voisin

            if distVoisin <= distMini:
                distMini, nomMini, lignesMini = voisin

        #le voisin le plus proche est donc sur notre chemin, on l'ajoute et on recommence le meme algo, sauf que l'arrivee devient ce voisin, pour arriver de proche en proche au point de depart
        if len(chemin) == 0: #on vient de commencer le cheminement
            chemin.append((arrivee, lignesMini))

        chemin.append((nomMini, lignesMini))
        cheminement(infos, depart, nomMini)

    else:
        chemin = chemin[::-1] #on renverse l'ordre des stations du chemin, puisqu'on les a ajoutees a rebours

def trouveTerminus(ligne, depart, arrivee): #calcul d'itineraire vers chaque terminus, pour voir quelle direction prendre
    global chemin
    garesLigne, _, _, terminus, _ = lectureXMLLigne(ligne, ville)

    if arrivee in terminus: return arrivee
    chemins = []

    for nomTerminus in terminus:
        chemin = []
        infos = itineraireDijkstra(garesLigne, depart, nomTerminus)
        cheminement(infos, depart, nomTerminus)
        chemin.append((nomTerminus, ligne))

        parcours = []
        for etape in chemin: parcours.append(etape[0])
        chemins.append(parcours)

    for parcours in chemins:
        if arrivee in parcours: return parcours[-1] #si le parcours vers le terminus contient la station que l'on cherche, alors il faut prendre la ligne dans la direction de ce terminus
    return arrivee

def afficheChemin(): #affiche tout ce qu'il faut sur le chemin, les stations par lesquelles on passe en les entourant par des cercles, et en les affichant sur l'affichage lateral, les instructions qui sont affichees sur la console de l'interpreteur python
    global chemin, cercles

    itineraire = chemin[:] #copie du tableau chemin cree precedemment
    correspondances = []
    idCorrespondances = [] #enregistre les emplacements des Correspondances dans le tableau itineraire
    rayon, bordure, dash = ctes.rayonCercle, ctes.bordureCercle, ctes.dashCercle

    _, lignesEnCours = itineraire[0]
    for etape in itineraire[1:-1]: #pour chaque etape du itineraire sauf le depart et l'arrivee -> cercles
        nomEtape, lignesEtape = etape

        couleur = ctes.couleurCercle
        if len(set(lignesEnCours) & set(lignesEtape)) == 0 and etape != itineraire[-1]: #si on doit necessairement changer de ligne
            correspondances.append(etape)
            idCorrespondances.append(itineraire.index(etape))
            lignesEnCours = lignesEtape
            couleur = ctes.couleurCorres

        if not console:
            coordEtape = coordImg[nomEtape] #pour savoir ou centrer le cercle

            if type(coordEtape[0]) != int:
                x1, y1 = coordEtape[0]
                x2, y2 = coordEtape[1]
            else:
                x1, y1 = coordEtape
                x2, y2 = x1, y1

            cercles.append(canvasCarte.create_oval(x1-rayon, y1-rayon, x2+rayon, y2+rayon, outline=couleur, width=bordure, dash=dash)) #on cree un cercle, et on le met dans une liste, ce qui permet ensuite de supprimer tous les cercles dans une autre fonction plus bas
    correspondances.append(itineraire[-1])

    #permet de determiner dans les morceaux sans changement de ligne quelle ligne on doit prendre
    lignesEmpruntees = []
    debut = 0
    for idChange in idCorrespondances + [len(itineraire)-1]:
        fin = idChange
        _, lignes = itineraire[debut]
        ensembleCommun = set(lignes)

        for etape in chemin[debut:fin]:
            _, lignes = etape
            ensembleCommun = ensembleCommun & set(lignes)

        lignesEmpruntees.append(choice(list(ensembleCommun)))
        debut = fin

    #Affichage des instructions
    if not console:
        #-Preparation affichage lateral
        btnPos.config(text="Chemin")
        listePos.delete(0, "end")

    #-Depart
    indexLignesEmpruntees = 0
    ligne = lignesEmpruntees[indexLignesEmpruntees]
    nomGare, _ = itineraire[0]
    if ligne == "</ligne>": print("c'est le cas"); quit()
    terminus = trouveTerminus(ligne, nomGare, correspondances[0][0])
    couleur = ctes.couleurDep

    affichageConsole = nomGare+" -> "+itineraire[-1][0]+"\n"
    affichageConsole += "\nPartir de "+nomGare+" prendre ligne "+ligne+" direction "+terminus

    if not console:
        listePos.insert("end", nomGare+" ligne "+ligne)
        listePos.itemconfig("end", {"fg":couleur})

    #-Entre depart et arrivee
    for etape in itineraire[1:-1]:
        nomGare, _ = etape

        if etape in correspondances: #-Chaque changement
            indexLignesEmpruntees += 1
            ligne = lignesEmpruntees[indexLignesEmpruntees]
            indexCorres = correspondances.index(etape)
            corresSuivante = correspondances[indexCorres+1]
            terminus = trouveTerminus(ligne, nomGare, corresSuivante[0])

            couleur = ctes.couleurCorres

            affichageConsole += "\n- Changer a "+nomGare+" prendre ligne "+ligne+" direction "+terminus

            if not console:
                listePos.insert("end", nomGare+" ligne "+ligne)
                listePos.itemconfig("end", {"fg":couleur})
        elif not console:
            listePos.insert("end", nomGare)

    #-Arrivee
    nomGare, _ = itineraire[-1]
    couleur = ctes.couleurArr

    affichageConsole += "\nVous arriverez a "+nomGare+" avec cette ligne.\n"

    if not console:
        listePos.insert("end", nomGare)
        listePos.itemconfig("end", {"fg":couleur})

    print(affichageConsole)

# Fonctions graphiques -------------------------------------------------------------------------------------------------------------#
def effaceChemin(): #enleve toutes les traces d'un calcul d'itineraire pour en faire un autre
    global cercles

    for cercle in cercles:
        canvasCarte.delete(cercle)
    cercles = []

    btnPos.config(text="Chercher !")
    listePos.delete(0, "end")

def majDepArr(statutInit, nomGare): #met a jour le depart ou l'arrivee
    global departModifie, depart, arrivee, changements

    if statutInit == "depart":
        changements = [gareDepart, texteDep, gareDepart, texteArr, gareArrivee]
        depart = nomGare
    else:
        changements = [gareArrivee, texteArr, gareArrivee, texteDep, gareDepart]
        arrivee = nomGare

    departModifie = not departModifie
    changements[0].config(text=nomGare)

    if depart not in depArrInit and arrivee not in depArrInit and depart != arrivee:
        btnCal.config(state=ACTIVE) #permet le calcul d'itineraire
        for i in range(1, len(changements)):
            changements[i].config(bg="green")
    else:
        btnCal.config(state=DISABLED)

        for i in range(1,len(changements)): #change les couleurs pour savoir si l'on modifie le depart ou l'arrivee
            if i <= 2: couleur = "white" #non sélectionné
            else: couleur = "yellow" #sélectionné

            changements[i].config(bg=couleur)

def clic(event): #quand on clique sur la carte
    global departModifie

    gareIdentifiee = identGare(event)

    if gareIdentifiee != None: #si on a bien identifie une gare
        if not departModifie: statut = "depart"
        else: statut = "arrivee"
        majDepArr(statut, gareIdentifiee)

        effaceChemin()

        cerclesDepArr(gareIdentifiee, statut)

def changementForce(event):
    global departModifie, depart, arrivee

    if not departModifie: majDepArr("depart", depart)
    else: majDepArr("arrivee", arrivee)

def identGare(event):
    ecartX = int(defilX.get()[0]*dimCarte[0])
    ecartY = int(defilY.get()[0]*dimCarte[1])

    xCoord = event.x+ecartX
    yCoord = event.y+ecartY
    tableauCoord = (xCoord, yCoord)

    possibles = []

    for nomGare in coordImg: #on regarde pour chacune des gares si elle est assez proche pour considerer que l'utilisateur a pu la choisir
        coordGare = coordImg[nomGare]
        dist = ctes.distance(tableauCoord, coordGare)
        if dist < ctes.toleranceEcartPixel:
            possibles.append((dist, nomGare))

    if len(possibles) != 0: return min(possibles)[1] #la gare identifiee est la plus proche parmi les candidats raisonnables
    else:
        showinfo("Attention", ctes.erreursReconnaissance[ville])
        return None

def recherche(event=None,rec=""): #champ de saisie lateral, pour trouver une gare par son nom
    global possiblesRec

    if rec == "": rec = rechercher.get() #recupere ce qui a ete saisi dans le champ saisie
    possiblesRec = []

    if not console: effaceChemin()

    for nomGare in coordImg:
        if rec.lower() in nomGare.lower():
            possiblesRec.append(nomGare)

    possiblesRec.sort()

    i = 1
    for possible in possiblesRec:
        if console: print(i, possible); i += 1
        else: listePos.insert("end", possible)

    return possiblesRec

def selPossible(event): #si on clique parmi les gares proposees suite a une recherche textuelle...
    global departModifie, possiblesRec, cercles

    selec = listePos.curselection()
    if selec != () and len(cercles) == 0:
        gareSelec = possiblesRec[selec[0]] #associe un element selectionne a la gare correspondante

        #deplacer la vue de la carte pour la centrer autour de la gare selectionnee
        operations = [canvasCarte.xview, canvasCarte.yview]
        for i in range(2):
            coord = coordImg[gareSelec] #pour savoir ou centrer le cercle
            if type(coord[0]) != int: coord = [round((coord[0][0]+coord[0][1])/2),round((coord[1][0]+coord[1][1])/2)]

            deplacement = (coord[i] - dimCanvasCarte[i]//2) / dimCarte[i]
            operations[i]("moveto", deplacement)

        if not departModifie: statut = "depart"
        else: statut = "arrivee"

        cerclesDepArr(gareSelec, statut)

        majDepArr(statut, gareSelec)

def cerclesDepArr(nomGare, statut):
    global coordImg, rondDep, rondArr

    rayon = ctes.rayonCercle
    bordure = ctes.bordureCercle
    coord = coordImg[nomGare] #pour savoir ou centrer le cercle
    if type(coord[0]) != int:
        x1, y1 = coord[0]
        x2, y2 = coord[1]
    else:
        x1, y1 = coord
        x2, y2 = x1, y1

    if statut == "depart":
        canvasCarte.delete(rondDep)
        rondDep = canvasCarte.create_oval((x1-rayon),(y1-rayon),(x2+rayon),(y2+rayon),width=bordure,outline=ctes.couleurDep)
    else:
        canvasCarte.delete(rondArr)
        rondArr = canvasCarte.create_oval((x1-rayon),(y1-rayon),(x2+rayon),(y2+rayon),width=bordure,outline=ctes.couleurArr)

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

if not console:
    #-----------------------------------------------------------------------------------------------------------------------------------#
    # UI -------------------------------------------------------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------------------------------------------------------#
    # Initialisation---------------------------------------------------------------------------------------------------#
    fenetre = Tk()
    fenetre.title ("Metro de "+ville.capitalize())
    tailleEcran = (fenetre.winfo_screenwidth(), fenetre.winfo_screenheight())
    fenetre.geometry("x".join(map(str, tailleEcran)))

    p = PanedWindow(fenetre, orient=HORIZONTAL) #separe la carte du menu lateral
    # Carte ------------------------------------------------------------------------------------------------------------#
    fCarte = Frame(p, bd=0)
    carte = PhotoImage(file=fichierCarte)

    #redimensionne la carte si l'ecran n'a pas une resolution suffisante
    dimCanvasCarte, ecartOblig = ctes.dimCanvasCarte, ctes.ecartOblig

    for i in range(2):
        dimCanvasCarte[i] = tailleEcran[i]
        if tailleEcran[i] < dimCanvasCarte[i] + ecartOblig[i]:
            dimCanvasCarte[i] -= ecartOblig[i]

    w, h = dimCarte
    canvasCarte = Canvas(fCarte,width=dimCanvasCarte[0], height=dimCanvasCarte[1], scrollregion=(0, 0, w, h))
    canvasCarte.create_image(0, 0, anchor=NW, image=carte)
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

    # Affichage lateral ------------------------------------------------------------------------------------------------#
    affichageLat = PanedWindow(p, orient=VERTICAL)

    #Menu en bas a droite
    iti = LabelFrame(affichageLat, text="Itineraire", bg="white")

    couleur = "yellow" #le depart est selectionne au debut...
    texteDep = Label(iti, text="Depart", bg=couleur)
    gareDepart = Label(iti, text=depart, bg=couleur)

    couleur = "white" #... et pas l'arrivee
    texteArr = Label(iti, text="Arrivee", bg=couleur)
    gareArrivee = Label(iti, text=arrivee, bg=couleur)

    btnCal = Button(iti, text="Calculer l'itineraire !", command=calculIti, state=DISABLED)

    #Recherche gare
    rec = LabelFrame(affichageLat, text="Chercher une gare", bg="white")
    varRec = StringVar()
    rechercher = Entry(rec, textvariable=varRec, width=40, text="Rechercher")
    btnPos = Button(rec, text="Chercher !", command=recherche)

    listePos = Listbox(rec, bd=0)

    # Structure --------------------------------------------------------------------------------------------------------#
    p.add(fCarte, minsize=dimCanvasCarte[0])

    p.add(affichageLat, minsize=0)

    frameIti = [texteDep, gareDepart, texteArr, gareArrivee, btnCal]
    for element in frameIti:
        element.pack(fill=X)

    frameRec = [rechercher, btnPos]
    for element in frameRec:
        element.pack(fill=X)
    listePos.pack(fill=BOTH, expand=1)

    largeurMin = ctes.largeurAffichageLat
    affichageLat.add(rec, minsize=dimCanvasCarte[1]-largeurMin, pady=1)
    affichageLat.add(iti, pady=1)

    p.pack()

    # Mainloop ---------------------------------------------------------------------------------------------------------#
    #Gere la molette pour linux et windows + clic gauche, sur canvasCarte
    commandes = {"<Button-1>":clic,"<Button-4>":monteAscenseur, "<Button-5>":descendAscenseur, "<Shift-Button-4>":gaucheAscenseur, "<Shift-Button-5>":droiteAscenseur, "<MouseWheel>":ascenseurVertWindows, "<Shift-MouseWheel>":ascenseurHoriWindows}

    for commande in commandes: canvasCarte.bind(commande, commandes[commande])
    for element in frameIti[0:-1]: element.bind("<Button-1>", changementForce) #changer entre depart et arrivee
    canvasCarte.bind_all("<Key>", fleches)
    rechercher.bind("<Return>", recherche) #lancer la recherche de gare par nom
    listePos.bind("<<ListboxSelect>>", selPossible) #identifer une gare parmi celles proposees

    fenetre.mainloop()
else:
    print("Metro de "+ville.capitalize()+"\n")
    while True:
        #recherche depart et arrivee
        depart = chercheGare("depart")
        print("Vous souhaitez partir de "+depart+"\n")

        arrivee = chercheGare("arrivee")
        print("Vous souhaitez partir de "+arrivee+"\n")

        #calcul itineraire
        calculIti()

        if "oui" not in input("Souhaitez-vous continuer ? ").lower(): break
