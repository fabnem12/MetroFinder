# -*- coding: utf8 -*-
from cherche import lectureXMLVille, lectureXMLLigne
from heapq import *
from tkinter import *
import sys, math

from coordTAE2 import retrouveTAE
import constantes as ctes

modeDev = False

#Identification de la ville
ville = "tae"

if ville is None: ville, console = ctes.identVille(sys.argv[-1])
if ville in ctes.GPSCompte: #charger le module pour simuler une sphère
    from geographiclib.geodesic import Geodesic
    geod = Geodesic.WGS84

#####################################################################################################################################
#CLASSES#############################################################################################################################
#####################################################################################################################################
class Gare():
    def __init__(self, nom, voisins, coord):
        self.nom, self.voisins, self.coord = nom, voisins, coord
        self.cercle = None, False
        self.coordGPS = []

        if ville in ctes.GPSCompte: self.setCoordGPS()

        if type(self.coord[0]) == int:
            self.coord = self.coord+self.coord
        else:
            coord = []
            for i in range(4):
                coord.append(self.coord[i//2][i%2])

            self.coord = coord

    def setCoordGPS(self): self.coordGPS, self.coord = self.coord
    def setVoisins(self, nouvVoisins): self.voisins = nouvVoisins

    def __str__(self): return self.nom

    def __getattr__(self, demande):
        infos = {"nom":self.nom, "coord":self.coord, "voisins":self.voisins, "cercle":self.cercle}

        try: return infos[demande]
        except: print("Erreur","Attribut non trouvé : "+demande); sys.exit()
#####################################################################################################################################
#FONCTIONS###########################################################################################################################
#####################################################################################################################################
def calculCheminsLongs(dicoGares, affi=True):
    global depart, arrivee

    listeGares = sorted(list(gares.keys()))
    longueursTrajets = []

    for indice1 in range(len(listeGares)):
        depart = dicoGares[listeGares[indice1]]
        if not affi: print(depart.nom)

        for indice2 in range(indice1+1, len(listeGares)):
            arrivee = dicoGares[listeGares[indice2]]

            try: longueursTrajets.append((calculIti(dicoGares, affi=False), depart.nom, arrivee.nom))
            except: pass
            if affi: print(depart.nom, arrivee.nom, longueursTrajets[-1][0])

        with open("data.txt", "w") as fichier:
            for trajet in sorted(longueursTrajets):
                fichier.write(str(trajet) + "\n")
    print(sorted(longueursTrajets)[-1])
    print(sum([x[0] for x in longueursTrajets]) / len(longueursTrajets))
    print(len([x for x in longueursTrajets if x[0] <= 4]), len([x for x in longueursTrajets if x[0] > 4]))

#Calcul du chemin
def calculIti(dicoGares, chercheTerminus=False, depTerminus=None, arrTerminus=None, affi=True):
    global depart, arrivee, chemin

    predecesseurs = dict()

    d = init(dicoGares, depart)
    dicoQ = dict()
    for nomGare in dicoGares: dicoQ[dicoGares[nomGare]] = 0

    while dicoQ != {}:
        s1 = trouveMin(dicoQ, d)
        if s1 == -1:
            break
        del dicoQ[s1]

        for voisin in s1.voisins:
            d, predecesseurs = majDistances(s1, voisin, d, predecesseurs)

    A = []
    s = arrivee
    while s != depart:
        nouvS, lignes = predecesseurs[s]
        A += [[s, lignes]]
        s = nouvS

    A += [[depart,[]]]
    A.reverse()

    for i in range(len(A)-1):
        A[i][1] = A[i+1][1].copy()

    A = trouveLignes(A.copy())

    if not chercheTerminus:
        if affi: trace(A.copy(), d[arrivee])
        else: return len(A)

        depart, arrivee = depArrInit
        affiDep.config(text=depart)
        affiArr.config(text=arrivee)

        if modeDev:
            for gare in d:
                coord = gare.coord
                moyX, moyY = (coord[0]+coord[2])//2, (coord[1]+coord[3])//2
                distance = round(d[gare],5)

                canvasCarte.create_text(moyX, moyY, text=str(distance))
    else:
        return A[:]

def trouveLignes(chemin):
    j = -1
    for i in range(len(chemin)-1):
        if i <= j: continue

        lignesCommunes = chemin[i][1]

        j = i
        while len(set(lignesCommunes) & set(chemin[j+1][1])) > 0 and j+1 < len(chemin)-1:
            lignesCommunes = list(set(lignesCommunes) & set(chemin[j+1][1]))
            j += 1

        for id in range(i, j+1):
            chemin[id][1] = sorted(lignesCommunes)

    return chemin

def init(dicoGares, depart):
    d = dict()
    for nomGare in dicoGares:
        gare = dicoGares[nomGare]
        d[gare] = ctes.infini
    d[depart] = 0

    return d

def majDistances(s1, voisin, d, predecesseurs):
    s2, dist, lignes = voisin

    try: lignesPrec = predecesseurs[s1][1]
    except: lignesPrec = []

    lignesCommunes = list(set(lignesPrec) & set(lignes))

    poids = dist + ctes.penaliteStopNew #on ajoute une pénalité de 15 secondes à chaque arrêt, ce qui permet de favoriser un itinéraire avec moins d'arrêt par rapport à un autre de même distance mais avec plus d'arrêt
    if lignesCommunes == []: #on doit faire une correspondance
        if "pedestre" not in lignesPrec+lignes:
            penalite = ctes.penaliteCorresNew #5 minutes

            nbCorresPossibles = len(set([ligne for x in s2.voisins for ligne in x[2]])) - 1
            penalite += nbCorresPossibles * ctes.penaliteCorresNew / 5 #on ajoute 1 minute de correspondance par ligne possible, donc par quai, moins la ligne en cours
            if "tae" in ville:
                penalite = 0 #la penalité est déjà incluse (11 lignes plus bas) à partir du moment où on change d'avion, elle est rajoutée dans la "distance"

            poids += penalite
    else:
        lignes = lignesCommunes

    for ligne in lignes:
        if "RER" in ligne or "LIGNE" in ligne:
            poids += 4*ctes.penaliteStopNew/3 #on ajoute 20 secondes supplémentaires à l'arrêt si on prend le RER/Transilien
            break

    if "tae" in ville: poids += ctes.penaliteAvion #on ajoute 1500km, environ 2h, pour chaque changement d'avion. Comme on change d'avion à chaque arrêt, on le fait pour chaque tronçon

    if d[s2] > d[s1] + poids:
        d[s2] = d[s1] + poids
        predecesseurs[s2] = [s1, lignes]

    return d, predecesseurs

def trouveMin(dicoQ, d):
    mini = ctes.infini
    sommet = -1
    for gare in dicoQ:
        if d[gare] < mini:
            mini = d[gare]
            sommet = gare

    return sommet
#Fin Calcul du chemin
#Trace et efface chemin
def trace(chemin, distanceArrivee):
    global couleursLignes, cerclesDepArr, autresTrucsVisuels

    for etape in chemin:
        particule = ""

        gare, lignes = etape
        if chemin.index(etape) not in (0, len(chemin)-1): #début ou fin de parcours sont ignorés au moment de créer les ovales, car les leurs sont déjà tracés
            if ville in ctes.GPSCompte: #on trace le chemin plutôt que tracer les cercles sur une carte
                traceChemin(garePrec, gare, couleur)

            pointilles = True
            if ville in ctes.GTFS: couleur = "#000000"
            elif len(lignes) == 1: #une seule ligne est possible, pas de suspense
                couleur = "#"+couleursLignes[lignes[0]]
            else: #si plusieurs lignes sont possibles, on fait une moyenne colorimétrique de leurs couleurs
                couleurs = []
                for ligne in lignes: couleurs.append(couleursLignes[ligne])

                couleur = "#"+ctes.moyenneCouleur(couleurs)

            if list(set(lignesPrec) & set(lignes)) == []: #il faut faire une correspondance, donc on fait un arc de cercle
                particule = " - ligne "+lignes[0]

                if ville not in ctes.GPSCompte:
                    coord = gare.coord
                    bordure = ctes.bordure(ville)
                    rayon = ctes.rayon(ville)
                    angleOuverture = 240 #240°, soit 2 tiers du cercle, pour faire un C
                    start = 60

                    cercle = canvasCarte.create_arc(coord[0]-rayon, coord[1]-rayon, coord[2]+rayon, coord[3]+rayon, start=start, extent=angleOuverture, outline=ctes.couleurCorres, width=bordure, style="arc")
                    autresTrucsVisuels.append(cercle)
                else:
                    if ville in ctes.GTFS:
                        couleur = "#000000"
                    else:
                        try:
                            couleur = "#"+couleursLignes[lignes[0]]
                        except:
                            print(gare.nom, lignes)
                            couleur = "#FF0000"

                    cercle = canvasCarte.create_oval(gare.coord[0]-ctes.rayon(ville), gare.coord[1]-ctes.rayon(ville), gare.coord[0]+ctes.rayon(ville), gare.coord[1]+ctes.rayon(ville), fill=couleur, outline="#"+ctes.contrasteur(couleur[1:]), width=ctes.bordure(ville))
                    autresTrucsVisuels.append(cercle)
            else:
                if ville not in ctes.GPSCompte:
                    traceCercle(gare, pointilles, "#"+ctes.couleurComp(couleur[1:]))
                elif "tae" in ville:
                    cercle = canvasCarte.create_oval(gare.coord[0]-ctes.rayon(ville), gare.coord[1]-ctes.rayon(ville), gare.coord[0]+ctes.rayon(ville), gare.coord[1]+ctes.rayon(ville), fill=couleur, outline="#"+ctes.contrasteur(couleur[1:]) , width=ctes.bordure(ville))
                    autresTrucsVisuels.append(cercle)

        else:
            if chemin.index(etape) == 0: #début
                couleurs = []
                for ligne in lignes: couleurs.append(couleursLignes[ligne])
                couleur = "#"+ctes.moyenneCouleur(couleurs)

                particule = " - ligne "+", ".join(lignes)
            else: #fin
                if ville in ctes.GPSCompte:
                    couleur = "#000000"
                    if ville not in ctes.GTFS:
                        couleurs = []
                        for ligne in lignes: couleurs.append(couleursLignes[ligne])
                        couleur = "#"+ctes.moyenneCouleur(couleurs)

                    traceChemin(garePrec, gare, couleur)

        garePrec = gare

        lstRecherche.insert(END, gare.nom+particule)
        lstRecherche.itemconfig(END, {"bg":couleur, "fg":"#"+ctes.contrasteur(couleur[1:])})

        lignesPrec = lignes
    #lstRecherche.insert(END, "Temps de trajet prévu : "+str(round(temps))+" minutes")

def effaceChemin(exceptions=[]):
    global autresTrucsVisuels, cerclesDepArr

    for cercle in autresTrucsVisuels+cerclesDepArr:
        if cercle not in exceptions and cercle != -1:
            canvasCarte.delete(cercle)
    lstRecherche.delete(0, END)

    autresTrucsVisuels = []
    """for i in range(2):
        if cerclesDepArr[i] not in exceptions: cerclesDepArr[i] = -1"""

#Fin Trace et efface chemin
#Autres fonctions
def creerObjetsGares(dictGares, coordImg):
    for nomGare in dictGares:
        voisins = []
        for voisin in list(dictGares[nomGare].keys()):
            infosVoisin = dictGares[nomGare][voisin]
            voisins.append((voisin, infosVoisin[0], infosVoisin[1]))
        coord = coordImg[nomGare]

        dictGares[nomGare] = Gare(nomGare, voisins, coord)

    return dictGares

def fermeture():
    fenetreLat.destroy()
    fenetreCarte.destroy()

def rechercheCoord(event, dicoGares):
    global dimCarte

    ecartX = int(defilX.get()[0]*dimCarte[0])
    ecartY = int(defilY.get()[0]*dimCarte[1])
    coord = (event.x+ecartX, event.y+ecartY)

    possibles = []
    for nomGare in dicoGares:
        coordGare = gares[nomGare].coord
        dist = ctes.distance(coord, coordGare)

        if dist < ctes.toleranceEcartPixel or ((coordGare[0],coordGare[1]) != (coordGare[2],coordGare[3]) and coordGare[0] < coord[0] < coordGare[2] and coordGare[1] < coord[1] < coordGare[3]):
            possibles.append((dist, nomGare))
    possibles.sort()

    if len(possibles) > 0:
        gareIdent = possibles[0][1]
        selGare(gareIdent)

def rechercheNom(dicoGares, rec=""):
    if rec == "": rec = txtRecherche.get() #recupere ce qui a ete saisi dans le champ saisie
    possiblesRec = []

    for nomGare in dicoGares:
        if rec.lower() in nomGare.lower(): possiblesRec.append(nomGare)

    possiblesRec.sort()

    lstRecherche.delete(0, END)
    for possible in possiblesRec: lstRecherche.insert(END, possible)

    return possiblesRec

def remplaceVoisins(dictGares):
    for nomGare in dictGares:
        gare = gares[nomGare]

        nouvVoisins = []
        for voisin in gare.voisins:
            nomVoisin, dist, lignes = voisin
            nouvVoisins += [(gares[nomVoisin], dist, lignes)]

        gare.setVoisins(nouvVoisins)

def selLstRecherche(event):
    selection = lstRecherche.curselection()

    if selection != []:
        gareIdent = lstRecherche.get(selection[0])
        selGare(gareIdent, parNom=True)

def selGare(nomGare, parNom=False):
    global gares, depart, arrivee, changeDep

    gare = gares[nomGare]
    if changeDep:
        garePerdStatut = depart
        depart = gare
        affiDep.config(text=gare.nom)
        couleur = ctes.couleurDep
        effaceChemin()
    else:
        garePerdStatut = arrivee
        arrivee = gare
        affiArr.config(text=gare.nom)
        couleur = ctes.couleurArr

    if parNom:
        operations = [canvasCarte.xview, canvasCarte.yview]
        for i in range(2):
            deplacement = (gare.coord[i] - dimFenCarte[i]//2) / dimCarte[i]
            operations[i]("moveto", deplacement)

    if garePerdStatut not in depArrInit:
        cercleSuppr = garePerdStatut.cercle
        if cercleSuppr != None: canvasCarte.delete(cercleSuppr)

    traceCercle(gare, False, couleur)

    exceptions = []
    if depart not in depArrInit or not changeDep: exceptions += [cerclesDepArr[0]]
    if arrivee not in depArrInit: exceptions += [cerclesDepArr[1]]
    effaceChemin(exceptions)

    toggleChangeDep()

def toggleChangeDep():
    global changeDep
    changeDep = not changeDep

    couleurs = ["yellow","white"]
    changements = [(textArr,affiArr),(textDep, affiDep)]
    if changeDep: changements = [changements[1],changements[0]]

    for i in range(2):
        for element in changements[i]: element.config(bg=couleurs[i])

    if depart != depArrInit[0] and arrivee != depArrInit[1]: btnCal.config(state=ACTIVE)

def touches(event):
    touche = event.keysym
    actionsDeplacement = {"Left":(-1,0), "Right":(1,0), "Up":(0,-1), "Down":((0,1))}
    if touche in actionsDeplacement:
        x, y = actionsDeplacement[touche]
        deplaceAscenseur(x,y)

def traceChemin(garePrec, gare, couleur):
    global autresTrucsVisuels

    adapteur = lambda val, xy: round(ctes.adapteCoord(val, xy, ville))

    coordPrec, coord = garePrec.coordGPS, gare.coordGPS
    courbe = geod.InverseLine(coordPrec[1], coordPrec[0], coord[1], coord[0])

    ds = ctes.distance(coordPrec, coord, GPS=True) * 1000 / 100 #longueur d'un trait en mètres, sachant que la fonction distance retourne une distance en km, que l'on convertit en m (*1000). On divise par 100 pour avoir 100 sections de traits
    n = int(math.ceil(courbe.s13 / ds))

    debutTrait = garePrec.coord
    if len(debutTrait) > 2: debutTrait = debutTrait[:2]
    for i in range(2, n+1):
        s = min(ds * i, courbe.s13)
        g = courbe.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        finTrait = (adapteur(g['lon2'],0), adapteur(g['lat2'], 1))

        autresTrucsVisuels.append(canvasCarte.create_line(debutTrait[0], debutTrait[1], finTrait[0], finTrait[1], width=ctes.largeurTrait, fill=couleur))

        debutTrait = finTrait

def traceCercle(gare, pointilles=True, couleur="gray"):
    global cerclesDepArr, autresTrucsVisuels

    coord = gare.coord
    rayon = ctes.rayon(ville)
    bordure = ctes.bordure(ville)

    dash = (1, 1)
    if pointilles: dash = ctes.dashCercle

    cercle = canvasCarte.create_oval(coord[0]-rayon, coord[1]-rayon, coord[2]+rayon, coord[3]+rayon, width=bordure, outline=couleur, dash=dash)
    if gare not in (depart, arrivee):
        autresTrucsVisuels.append(cercle)
    elif gare == depart:
        if len(cerclesDepArr) == 0: cerclesDepArr = [0,0]
        cerclesDepArr[0] = cercle
    else:
        if len(cerclesDepArr) == 0: cerclesDepArr = [0,0]
        cerclesDepArr[1] = cercle

#Gestion molette et flèches
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

#####################################################################################################################################
#PROGRAMME PRINCIPAL#################################################################################################################
#####################################################################################################################################
# Init ------------------------------------------------------------------------------------------------------------------------------
fichierCarte = ctes.accesCartes+ville+".png"
dimCarte = ctes.dimCarte[ville]

chemin = []
depArrInit = ("Selectionner une gare de depart", "Selectionner une gare d'arrivee")
cerclesDepArr, autresTrucsVisuels = [], []
depart, arrivee = depArrInit
changeDep = True #si on sélectionne une gare, elle va être enregistrée en tant que départ. Si False, elle va être enregistrée en tant qu'arrivée

gares, coordImg = lectureXMLVille(ville, alt="Alt") #recupere toutes les infos du graphe de la ville selectionnee

gares = creerObjetsGares(gares, coordImg)
remplaceVoisins(gares)

couleursLignes = dict()
if ville not in ctes.GTFS:
    for ligne in ctes.lignesOK(ville):
        _, _, _, _, couleur = lectureXMLLigne(ligne, ville, alt="Alt")
        couleursLignes[ligne] = couleur
# Fin Init --------------------------------------------------------------------------------------------------------------------------

# Affichage -------------------------------------------------------------------------------------------------------------------------
#Initialisation de l'affichage
fenetreCarte = Tk()
fenetreCarte.title("Métro de "+ville.capitalize())
tailleEcran = [fenetreCarte.winfo_screenwidth(), fenetreCarte.winfo_screenheight()-50]
dimFenCarte = [tailleEcran[0]-300,tailleEcran[1]]
fenetreCarte.geometry("x".join(list(map(str, dimFenCarte)))+"+0+0")

fenetreLat = Toplevel(fenetreCarte)
fenetreLat.title("Menu")
fenetreLat.geometry("300x"+str(tailleEcran[1])+"-0+0")

affiCarte = Frame(fenetreCarte, bd=0)
affiLat = PanedWindow(fenetreLat, bd=0, width=300, orient=HORIZONTAL)

w, h = min(dimCarte[0], tailleEcran[0])-300-15, min(dimCarte[1], tailleEcran[1])-15
if min(dimCarte[0], tailleEcran[0]) == dimCarte[0]: w += 315
if min(dimCarte[1], tailleEcran[1]) == dimCarte[1]: h += 15

canvasCarte = Canvas(affiCarte, height=h, width=w, scrollregion=(0, 0, dimCarte[0], dimCarte[1]))
canvasCarte.grid(row=0, column=0)

#-Scrollbars
defilY = Scrollbar(affiCarte, orient='vertical',
    command=canvasCarte.yview)
defilY.grid(row=0, column=1, sticky='ns')

defilX = Scrollbar(affiCarte, orient='horizontal',
    command=canvasCarte.xview)
defilX.grid(row=1, column=0, sticky='ew')

canvasCarte['xscrollcommand'] = defilX.set
canvasCarte['yscrollcommand'] = defilY.set
#-Fin Scrollbars
#Fin Initialisation de l'affichage

#Affichage de la carte
carte = PhotoImage(file="images/"+ville+".png")
canvasCarte.create_image(0, 0, anchor=NW, image=carte)
#Fin Affichage de la carte

#Affichage latéral
#-Recherche de gare
affiRec = LabelFrame(affiLat, text="Chercher une gare", bg="white")
varRec = StringVar()
txtRecherche = Entry(affiRec, textvariable=varRec, width=40, text="Rechercher")
btnRecherche = Button(affiRec, text="Chercher !", command=lambda: rechercheNom(gares))

lstRecherche = Listbox(affiRec, bd=0, selectmode="single")
#- Fin Recherche de gare

#-Itinéraire
affiIti = LabelFrame(affiLat, text="Itinéraire", bg="white")

couleur = "yellow" #le depart est selectionne au debut...
textDep = Label(affiIti, text="Départ", bg=couleur)
affiDep = Label(affiIti, text=depart, bg=couleur)

couleur = "white" #... et pas l'arrivee
textArr = Label(affiIti, text="Arrivée", bg=couleur)
affiArr = Label(affiIti, text=arrivee, bg=couleur)

btnCal = Button(affiIti, text="Calculer l'itinéraire !", command=lambda: calculIti(gares), state=DISABLED)
#-Fin Itinéraire
#Fin Affichage latéral

#Structure
affiCarte.pack()

affiLat.add(affiRec, pady=1)
affiLat.add(affiIti, pady=1)

frameRec = [affiRec, txtRecherche, btnRecherche]
for element in frameRec: element.pack(fill=X)
affiRec.pack(fill=BOTH, expand=1)
lstRecherche.pack(fill=BOTH, expand=1)

frameIti = [affiIti, textDep, affiDep, textArr, affiArr, btnCal]
for element in frameIti:
    element.pack(fill=X)

affiLat.pack(fill=Y, expand=1)
#Fin Structure

#Mainloop, protocols et bindings
fenetreLat.protocol("WM_DELETE_WINDOW", fermeture)
fenetreCarte.protocol("WM_DELETE_WINDOW", fermeture)

for element in frameIti[1:-1]: element.bind("<Button-1>", lambda x: toggleChangeDep())
lstRecherche.bind("<Double-Button-1>", selLstRecherche)

#Commandes basiques (molette et flèches)
commandes = {"<Button-4>":monteAscenseur, "<Button-5>":descendAscenseur, "<Shift-Button-4>":gaucheAscenseur, "<Shift-Button-5>":droiteAscenseur, "<MouseWheel>":ascenseurVertWindows, "<Shift-MouseWheel>":ascenseurHoriWindows}
for commande in commandes: canvasCarte.bind(commande, commandes[commande])
canvasCarte.bind_all("<Key>", touches)

affiRec.bind_all("<Return>", lambda x: rechercheNom(gares))

#Clic gauche sur la carte
canvasCarte.bind("<Button-1>", lambda x: rechercheCoord(x, gares))

#print(len(list(gares.keys())))
#calculCheminsLongs(gares, affi=False) #Fonction pour calculer tous les itinéraires possibles, et voir quels sont les plus longs

fenetreCarte.mainloop()
# Fin Affichage ---------------------------------------------------------------------------------------------------------------------
