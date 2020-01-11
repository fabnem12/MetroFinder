# -*- coding: utf8 -*-
from tkinter import *
from tkinter.messagebox import *
from random import choice
from cherche import donnees, lectureXMLLigne, lectureXMLVille
import codecs, sys, os
import constantes as ctes

#Initialisation###########################################################################################################
#-Identification de la ville
ville, _ = ctes.identVille(sys.argv[-1])
modeDev = False
sansEnregistrer = False

#if "tae" in ville: showinfo("Attention","Le réseau aérien ne se base pas sur le même système de coordonnées que le métro. Par conséquent, ce programme n'est pas accessible au réseau "+ville+" pour le moment. Une mise à jour à cet effet est prévue."); quit()

#-Constantes
class Ligne():
    def __init__(self, num):
        self.num = num
        self.gares = []
        self.couleur = ""
        self.pourrie = False

    def setGares(self, listeGares, coordGPS, coordImg, voisins, terminus, couleur):
        for nomGare in listeGares:
            nbVoisins = len(voisins[nomGare])

            statuts = {3:"fourche", 2:"normal", 0:""}
            if nomGare in terminus or "tae" in ville: statut = "terminus"
            elif nbVoisins in statuts: statut = statuts[nbVoisins]
            else: statut = "normal"

            try:
                gare = Gare(nomGare, coordGPS[nomGare], coordImg[nomGare], voisins[nomGare], statut)
            except:
                print("Erreur sur la ligne",self.num)
                print("nomGare :",nomGare)
                print("coordGPS",nomGare, nomGare in coordGPS)
                if nomGare in coordGPS: print(coordGPS[nomGare])
                print("coordImg",nomGare, nomGare in coordImg)
                if nomGare in coordImg: print(coordImg[nomGare])
                print("voisins", nomGare, nomGare in voisins)
                if nomGare in coordImg: print(voisins[nomGare])
                
                self.pourrie = True

            self.gares.append(gare)

        self.setVoisinsGares()
        self.couleur = couleur

    def setVoisinsGares(self):
        for gare in self.gares:
            voisinsInit = gare.get("voisins")

            voisins = [x for x in self.gares if x.get("nom") in voisinsInit]
            gare.setVoisins(voisins)

    def setCouleur(self, data):
        self.couleur = data

    def get(self, demande):
        infos = {"num":self.num, "gares":self.gares, "couleur":self.couleur}

        return infos[demande]

class Gare():
    def __init__(self, nom, coordGPS, coordImg, voisinsInit, statut):
        self.nom, self.coordGPS, self.coordImg, self.voisins, self.statut = nom, coordGPS, coordImg, voisinsInit, statut

        self.cercle = ""
        self.interventionHumaine = len(self.voisins) != 0

        if self.coordImg == (0,0) and self.statut == "normal": self.statut = ""
        if self.statut == "" and self.coordImg != (0,0): self.statut = "normal"

        if ville in ctes.GPSCompte:
            self.coordImg = [ctes.adapteCoord(self.coordGPS[0], 0, ville), ctes.adapteCoord(self.coordGPS[1], 1, ville)]
            if self.statut == "": self.statut = "normal"

    def get(self, demande):
        infos = {"nom":self.nom, "coordGPS":self.coordGPS, "coordImg":self.coordImg, "statut":self.statut, "voisins":self.voisins, "cercle":self.cercle, "interventionHumaine":self.interventionHumaine}

        infos["coord"] = self.coordImg
        if ville in ctes.GPSCompte: infos["coord"] = self.coordGPS

        return infos[demande]

    def setVoisins(self, data): self.voisins = data
    def ajoutVoisin(self, data): self.voisins += [data]
    def retireVoisin(self, data):
        if data in self.voisins: del self.voisins[self.voisins.index(data)]

    def setCoordImg(self, data): self.coordImg = data
    def setStatut(self, data): self.statut = data
    def setInterventionHumaine(self, data): self.interventionHumaine = data
    def setCercle(self, data):
        if type(data) == str: dessineCercle(self, self.coordImg, data)
        else: self.cercle = data

    def __gt__(self, compare): return self.nom > compare.nom

listeLignes = ctes.lignesOK(ville, creation=True)
dimCarte = ctes.dimCarte[ville]
fichierCarte = ctes.accesCartes+ville+".png"

lignes = dict()
for numero in listeLignes:
    lignes[numero] = Ligne(numero)
    if lignes[numero].pourrie: del lignes[numero]

#-Initialisation des données
lignesOK = ctes.lignesOK(ville, creation=False)
def init():
    for numero in lignes:
        #Init dicos et listes
        coordGPS = dict()
        coordImg = dict()
        voisins = dict()
        listeGaresCSV = []

        #Recup données csv
        listeGaresCSV = donnees(lignes[numero].get("num"), "gares", ville)
        coordGPS = donnees(lignes[numero].get("num"), "coord", ville)
        for nomGare in listeGaresCSV:
            coordImg[nomGare] = (0,0)
            voisins[nomGare] = []

        #Récup données XML par ligne
        couleur = ""
        if numero in lignesOK:
            gares, coordImgXML, listeGaresXML, terminus, couleur = lectureXMLLigne(lignes[numero].get("num"), ville, alt="Alt")

            for nomGare in listeGaresXML:
                voisins[nomGare] = gares[nomGare]

                if "|" in coordImgXML[nomGare]:
                    coordsBrutes = coordImgXML[nomGare]
                    coordsBrutes = coordsBrutes.split("|")

                    coords = []
                    coords = [int(x) for x in coordsBrutes[0].split(", ")]

                    coordImgXML[nomGare] = coords
                else:
                    if type(coordImgXML[nomGare]) == tuple: coordImgXML[nomGare] = str(coordImgXML[nomGare])[1:-1]
                    coordImgXML[nomGare] = tuple(map(int, coordImgXML[nomGare].split(", ")))

            if modeDev:
                _, coordImgVille = lectureXMLVille("paris2", alt="Alt")

                for gare in coordImgXML:
                    if gare in coordImgVille:
                        coords = []
                        for i in range(2):
                            if type(coordImgVille[gare][0]) != int:
                                coords.append(coordImgVille[gare][0][i] + ctes.rayon(ville))
                            else:
                                coords.append(coordImgVille[gare][i])

                        coordImgXML[gare] = coords
            for nomGare in coordImgXML: coordImg[nomGare] = coordImgXML[nomGare]
        elif os.path.exists("lignesAlt/"+ville+"/"+numero+".xml"):
            gares, coordImgXML, listeGaresXML, terminus, couleur = lectureXMLLigne(lignes[numero].get("num"), ville, alt="")

            for nomGare in listeGaresXML:
                voisins[nomGare] = gares[nomGare]
                coordImgXML[nomGare] = tuple(map(int, coordImgXML[nomGare].split(", ")))
            for nomGare in coordImgXML: coordImg[nomGare] = coordImgXML[nomGare]
        else:
            listeGaresXML = []
            terminus = []
            couleur = "000000"

        lignes[numero].setGares(list(set(listeGaresCSV+listeGaresXML)), coordGPS, coordImg, voisins, terminus, couleur)

init()

ligneEnCours = lignes[sorted(list(lignes.keys()))[0]]
gareEnCours = ""
traits = []
#Fin Initialisation########################################################################################################
#Fonctions sur les donnees#################################################################################################
def fermetureFenetre(event=None):
    global sansEnregistrer

    fenetre.destroy()

    if not sansEnregistrer:
        ecritXML(True)
        from fusion2 import listeGaresVille, ecritXMLVille
    else:
        print("Enregistrement automatique à la fermeture désactivé")

def ecritXML(toutesLesLignes=False):
    if not toutesLesLignes:
        global ligneEnCours
        listeLignes = [ligneEnCours]
    else:
        global lignes
        listeLignes = lignes.values()

    for ligne in listeLignes:
        terminus = [x for x in ligne.get("gares") if x.get("statut") == "terminus"]
        reste = [x for x in ligne.get("gares") if x not in terminus]

        numLigne = ligne.get("num")

        with codecs.open("lignesAlt/"+ville+"/"+numLigne+".xml", 'w', 'utf-8') as fichier:
            fichier.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fichier.write("<ligne terminus=\"" + ",".join([ctes.traitementNom(x.get("nom")) for x in terminus]) + "\" couleur=\""+ligne.get("couleur")+"\">\n")

            listeGaresLigne=terminus+reste

            for gare in sorted(listeGaresLigne, key=lambda x:x.get("nom")):
                nomGare = ctes.traitementNom(gare.get("nom"))

                if gare.get("coordImg") != (0,0):
                    fichier.write("\t<gare nom=\""+nomGare+"\" coord=\""+str(gare.get("coord"))[1:-1]+"\">\n")
                    for voisin in gare.get("voisins"):
                        dist = ctes.distance(gare.get("coordGPS"),voisin.get("coordGPS"), GPS=True)
                        if ligne.get("num") == "pedestre":
                            dist = str(ctes.penaliteCorresNew)

                        nomVoisin = ctes.traitementNom(voisin.get("nom"))

                        fichier.write("\t\t<voisin nom=\""+nomVoisin+"\" distance=\""+str(dist)+"\" />\n")
                    fichier.write("\t</gare>\n")

            fichier.write("</ligne>")

            if not toutesLesLignes: showinfo("Information", "J'ai fini le XML pour la ligne "+ligne.get("num"))

def trouveVoisins(gare):
    voisinsActuels = gare.get("voisins")
    nbVoisinsActuels = len(voisinsActuels)
    statut = gare.get("statut")
    coordGPSGare = gare.get("coordGPS")

    nbNouveauxVoisins = 2 - nbVoisinsActuels
    if statut == "terminus": nbNouveauxVoisins -= 1
    if statut == "fourche": nbNouveauxVoisins += 1

    if nbNouveauxVoisins < 1: return []

    nouveauxVoisins = identGare(coordGPSGare, voisins=voisinsActuels+[gare], nbReponses=-1)
    copie = nouveauxVoisins.copy()
    for i in range(len(copie)):
        voisinsDuVoisin = copie[i].get("voisins")
        nbVoisinsDuVoisin = len(voisinsDuVoisin)
        statutDuVoisin = copie[i].get("statut")

        voisinsEnPlus = 2 - nbVoisinsDuVoisin
        if statutDuVoisin == "terminus": voisinsEnPlus -= 1
        if statutDuVoisin == "fourche": voisinsEnPlus += 1

        nouveauVoisin = voisinsEnPlus > 0
        if not nouveauVoisin: del nouveauxVoisins[nouveauxVoisins.index(copie[i])]

    nouveauxVoisins = nouveauxVoisins[:nbNouveauxVoisins]

    voisinsFinaux = nouveauxVoisins + voisinsActuels
    gare.setVoisins(voisinsFinaux)

    for voisin in voisinsFinaux:
        if gare not in voisin.get("voisins"):
            voisin.ajoutVoisin(gare)

    return nouveauxVoisins

def trace():
    global ligneEnCours, traits

    gares = ligneEnCours.get("gares")
    if "tae" not in ville:
        terminus = [gare for gare in gares if gare.get("statut") == "terminus"]
        fourches = [gare for gare in gares if gare.get("statut") == "fourche"]

        aTraiter = terminus + fourches

        while len(aTraiter) > 0:
            gareEnCours = aTraiter[-1] #pile LIFO
            del aTraiter[-1]
            if gareEnCours.get("interventionHumaine"): continue

            nouveauxVoisins = trouveVoisins(gareEnCours)
            for voisin in nouveauxVoisins: aTraiter.append(voisin)

    for gare in gares:
        x1, y1 = gare.get("coordImg")

        gare.voisins = list(set(gare.get("voisins")))
        if gare in gare.get("voisins"): gare.setVoisins([x for x in gare.get("voisins") if x != gare])

        if gare.get("voisins") != []:
            for voisin in gare.get("voisins"):
                x2, y2 = voisin.get("coordImg")

                if (x1, y1) != (0,0) and (x2, y2) != (0, 0):
                    fleche = ""
                    if gare not in voisin.get("voisins"): #lien à sens unique de gare à voisin
                        fleche = "last"

                    traits += [canvasCarte.create_line(x1, y1, x2, y2, fill="red", width=ctes.largeurTrait, arrow=fleche)]

def selecGare(gare, index="", viaListbox=False):
    global ligneEnCours, gareEnCours

    deselecGare()

    if index != "":
        affiListeGares.selection_clear(0, END)
        affiListeGares.delete(0, index-1)
        affiListeGares.delete(1, END)
    else:
        affiListeGares.delete(0, END)
        affiListeGares.insert(0, gare.get("nom"))

    affiListeGares.itemconfig(0, {"bg":"black", "fg":"white"})
    if gare.get("cercle") != "":
        canvasCarte.itemconfig(gare.get("cercle"), outline=ctes.couleurCorres)

    if viaListbox and gare.get("coordImg") != (0,0):
        operations = [canvasCarte.xview, canvasCarte.yview]
        for i in range(2):
            deplacement = (gare.get("coordImg")[i] - dimCanvasCarte[i]//2) / dimCarte[i]
            operations[i]("moveto", deplacement)

    gareEnCours = gare

def deselecGare():
    global gareEnCours

    ancienneGare = gareEnCours
    gareEnCours = ""
    setLigne()

def identGare(pos, voisins=False, nbReponses=1):
    global ligneEnCours

    possibles = []

    for gare in ligneEnCours.get("gares"):
        if gare.get("statut") != "" and gare.get("coordImg") not in ((0,0),[0,0]):
            coordGare = gare.get("coordImg")
            if voisins != False: coordGare = gare.get("coordGPS")

            dist = ctes.distance(pos, coordGare)

            if (not voisins and dist < ctes.toleranceEcartPixel) or (voisins != False and 0 < dist and gare not in voisins and gare.get("statut") != ""):
                possibles.append((dist, gare))

    possibles = [possible[1] for possible in sorted(possibles)]
    if nbReponses > 0: possibles = possibles[:nbReponses]

    return possibles

def setCouleur():
    global ligneEnCours

    class popupWindow():
        def __init__(self):
            top=self.top=Toplevel(fenetre)
            self.l=Label(top,text="Code couleur de la ligne "+ligneEnCours.get('num')+" (sans #) : ")
            self.l.pack()
            self.e=Entry(top)
            self.e.pack()
            self.b=Button(top,text='Ok',command=self.cleanup)
            self.b.pack()
        def cleanup(self):
            nouvCouleur = self.e.get()
            if nouvCouleur != "":
                ligneEnCours.setCouleur(nouvCouleur)
                affiNumLigne.config(bg="#"+nouvCouleur, fg="#"+ctes.contrasteur(nouvCouleur))

            self.top.destroy()

    popUp = popupWindow()
#Fin Fonction sur les donnees#############################################################################################

#Fonctions graphiques#####################################################################################################
def setLigne(): #Changer la ligne traitee
    global lignes, ligneEnCours

    for gare in ligneEnCours.get("gares"):
        canvasCarte.itemconfig(gare.get("cercle"), state="hidden")
    for trait in traits:
        canvasCarte.itemconfig(trait, {"state":"hidden"})

    ligne = lignes[varNumLigne.get()]

    bg = ligne.get("couleur")
    if bg == "": bg = "ffffff"
    affiNumLigne.config(text="Ligne "+ligne.get("num"), bg="#"+bg, fg="#"+ctes.contrasteur(bg))

    affiListeGares.delete(0, END)
    for gare in sorted(ligne.get("gares")):
        affiListeGares.insert(END, gare.get("nom"))

        if gare.get("coordImg") == (0,0):
            coordPossibles = [x.get("coordImg") for x in ligne.get("gares") for ligne in lignes if x.get("nom") == gare.get("nom") and x.get("coordImg") != (0,0)]

            if len(coordPossibles) > 0: gare.setCoordImg(choice(coordPossibles))

        statut, cercle = gare.get("statut"), gare.get("cercle")
        if statut in ("","fourche","terminus","normal"):
            infos = {"normal":("gray","white"), "fourche":("red","yellow"), "terminus":("magenta","green"), "":("white","black")}
            bg, fg = infos[statut]
            couleurCercle = bg

            affiListeGares.itemconfig(END, {"bg":bg, "fg":fg})
            if statut != "":
                if cercle != "" and gare.get("coordImg") == (0,0):
                    canvasCarte.itemconfig(gare.get("cercle"), outline=couleurCercle, state="normal")
                elif gare.get("coordImg") != (0,0):
                    gare.setCercle(couleurCercle)

                if gare.get("coordImg") == (0,0) and statut in ("fourche", "terminus"):
                    affiListeGares.itemconfig(END, {"bg":"white", "fg":infos[statut][0]})

    ligneEnCours = ligne

def dessineCercle(gare, pos, couleur=ctes.couleurCorres):
    bordure = ctes.bordure(ville)
    rayon = ctes.rayon(ville)

    x, y = pos

    gare.setCercle(canvasCarte.create_oval(x-rayon, y-rayon, x+rayon, y+rayon, outline=couleur, width=bordure))

def bougeCercle(gare, delta):
    cercle = gare.get("cercle")
    coordAv = gare.get("coordImg")

    canvasCarte.move(cercle, delta[0], delta[1])

    newCoord = [coordAv[i]+delta[i] for i in range(2)]
    return tuple(newCoord)

#-Gestion molette et fleches
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
#-Fin Gestion molette et fleches

def clic(event, cote):
    global ligneEnCours, gareEnCours

    if event != "selecListBox":
        #pour recuperer l'ecart du au defilement de la carte
        ecartX = int(defilX.get()[0]*dimCarte[0])
        ecartY = int(defilY.get()[0]*dimCarte[1])

        pos = (event.x+ecartX, event.y+ecartY)

    if event == "selecListBox":
        try:
            index = affiListeGares.curselection()[0]
            gare = sorted(ligneEnCours.get("gares"))[index]

            selecGare(gare, index, viaListbox=True)
        except IndexError:
            pass

    if cote == "gauche":
        if event != "selecListBox" and gareEnCours != "":
            if gareEnCours.get("coordImg") == (0,0):
                dessineCercle(gareEnCours, pos)
                gareEnCours.setCoordImg(pos)

                if gareEnCours.get("statut") == "": gareEnCours.setStatut("normal")

            if gareEnCours.get("cercle") != "":
                xAncien, yAncien = gareEnCours.get("coordImg")
                delta = (pos[0]-xAncien, pos[1]-yAncien)

                gareEnCours.setCoordImg(bougeCercle(gareEnCours, delta))

    elif cote == "milieu":
        if gareEnCours != "":
            deselecGare()
    elif cote.lower() == "droite":
        if event != "selecListBox":
            gare = identGare(pos)[0]
            selecGare(gare)

        if type(gareEnCours) == str:
            showinfo("Attention", "Veuillez d'abord faire un clic gauche sur le nom de la station pour la sélectionner, avant de faire le double-clic-droit")

        if cote == "DROITE":
            listeGaresLigne = ligneEnCours.get("gares")
            listeVoisins = gareEnCours.get("voisins")
            dicoGares = dict()
            for gare in listeGaresLigne: dicoGares[gare.get("nom")] = gare

            def selection(liste, index):
                indObjet=0
                texte = ''
                if len(index) != 0:
                    indObjet = index[0]
                    texte=liste.get(indObjet)
                    if texte != '':
                        liste.delete(indObjet)
                        liste.insert(indObjet,'')
                    else:
                        indObjet=0

                    return texte,indObjet
            def deselection(liste, texte, index):
                if texte != '':
                    liste.delete(index)
                    liste.insert(index,texte)
            def sel_one(liste1, liste2, deselect=True):
                if len(liste1.curselection()) != 0:
                    texte, index = selection(liste1,liste1.curselection())
                    if deselect: deselection(liste2, texte, index)
                    else: return texte, index
            def deselect(): sel_one(affiVoisins, affiPasVoisins)
            def select(): sel_one(affiPasVoisins, affiVoisins)
            def changeNbSens():
                if len(affiVoisins.curselection()) != 0:
                    texte, index = sel_one(affiVoisins,[],deselect=False)
                    if texte[-1] == "1": texte = texte[:-1]+"2"
                    elif texte[-1] == "2": texte = texte[:-1]+"1"

                    deselection(affiVoisins, texte, index)

            def enregistreVoisins():
                liens = []
                for i in range(affiVoisins.size()):
                    if affiVoisins.get(i) != "": liens.append(affiVoisins.get(i))
                pasVoisins = []
                for i in range(affiPasVoisins.size()):
                    if affiPasVoisins.get(i) != "": pasVoisins.append(affiPasVoisins.get(i))

                voisins = []
                for infosVoisin in liens:
                    nomVoisin, nbSens = infosVoisin.split(", ")
                    voisin = dicoGares[nomVoisin]
                    voisins.append(voisin)

                    if nbSens == "2" and gareEnCours not in voisin.get("voisins"): voisin.ajoutVoisin(gareEnCours)
                    if nbSens == "1" and gareEnCours in voisin.get("voisins"): voisin.retireVoisin(gareEnCours)

                for infosPasVoisin in pasVoisins:
                    nomPasVoisin, nbSens = infosPasVoisin.split(", ")
                    pasVoisin = dicoGares[nomPasVoisin]
                    if nbSens == "2" and gareEnCours in pasVoisin.get("voisins"): pasVoisin.retireVoisin(gareEnCours)
                    if nbSens == "1" and gareEnCours not in pasVoisin.get("voisins"): pasVoisin.ajoutVoisin(gareEnCours) #c'est un voisin unidirectionnel, les trains vont de pasVoisin à gareEnCours, mais pas dans l'autre sens

                gareEnCours.setVoisins(voisins)

                gareEnCours.setInterventionHumaine(True)
                deselecGare()
                if ligneEnCours != lignes["pedestre"]: trace()
                fListeObjet.destroy()

            fListeObjet = Tk()
            fListeObjet.title(gareEnCours.get("nom")+" "+str(gareEnCours.get("coordImg")))

            menubar = Menu(fListeObjet)
            menubar.add_command(label="Enregistrer, fermer cette fenêtre",command=enregistreVoisins)

            fListeObjet.config(menu=menubar)

            flabel1=Frame(fListeObjet)
            label1=Label(flabel1, text="Voisins")
            label1.pack(side=TOP)
            affiVoisins = Listbox(flabel1,height=len(listeGaresLigne)-1,width=40)
            affiVoisins.pack(side=LEFT)

            bouton11 = Button(flabel1, text=">", command = deselect)
            bouton11.pack()
            bouton21 = Button(flabel1, text="<", command = select)
            bouton21.pack(side=BOTTOM)
            flabel1.pack(side=LEFT)

            flabel2=Frame(fListeObjet)
            label2=Label(flabel2, text="Pas voisins")
            label2.pack(side=TOP)
            affiPasVoisins = Listbox(flabel2,height=len(listeGaresLigne)-1,width=40)
            affiPasVoisins.pack(side=LEFT)
            flabel2.pack(side=LEFT)

            for item in sorted(listeGaresLigne):
                if item != gareEnCours:
                    nbSens = "2"
                    if gareEnCours not in item.get("voisins") and item in gareEnCours.get("voisins"): nbSens = "1"
                    if gareEnCours in item.get("voisins") and item not in gareEnCours.get("voisins"): nbSens = "1"

                    if item in listeVoisins:
                        affiVoisins.insert(END,item.get("nom")+", "+nbSens)
                        affiPasVoisins.insert(END,'')
                    else:
                        affiVoisins.insert(END,'')
                        affiPasVoisins.insert(END,item.get("nom")+", "+nbSens)


            affiVoisins.bind('<Double-1>', lambda x:deselect())
            affiVoisins.bind('<Shift-Button-1>', lambda x:changeNbSens())
            affiPasVoisins.bind('<Double-1>', lambda x:select())

            fListeObjet.mainloop()

def touches(event):
    global gareEnCours, sansEnregistrer

    touche = event.keysym
    actionsDeplacement = {"Left":(-1,0), "Right":(1,0), "Up":(0,-1), "Down":((0,1))}
    if touche in actionsDeplacement:
        x, y = actionsDeplacement[touche]
        if gareEnCours == "": deplaceAscenseur(x,y)
        else:
            gareEnCours.setCoordImg(bougeCercle(gareEnCours, (x, y)))
    else:
        if touche in ("t", "f") and gareEnCours != "":
            equivalences = {"t":"terminus", "f":"fourche"}

            if gareEnCours.get("statut") == "normal": gareEnCours.setStatut(equivalences[touche])
            elif gareEnCours.get("statut") in ("terminus", "fourche"): gareEnCours.setStatut("normal")
        if touche == "dollar": #danger : pas d'enregistrement
            sansEnregistrer = not sansEnregistrer
            dollar = ""
            if sansEnregistrer: dollar = "$"

            fenetre.title("Ajouter une ligne à "+ville.capitalize()+" "+dollar)
#Fin Fonctions graphiques#################################################################################################

#Initialisation graphique#################################################################################################
fenetre = Tk()
fenetre.title("Ajouter une ligne à "+ville.capitalize())
tailleEcran = (fenetre.winfo_screenwidth(), fenetre.winfo_screenheight())
fenetre.geometry("x".join(map(str, tailleEcran)))

affiCarteEtInfos = PanedWindow(fenetre, orient=HORIZONTAL)

#-Barre de menu
menubar = Menu(fenetre)
fenetre.config(menu=menubar)

#--Liste lignes
affiListeLignes = Menu(menubar, tearoff=0)
varNumLigne = StringVar()
varNumLigne.set(ligneEnCours.get("num"))

for numero in sorted(lignes.keys()):
    ligne = lignes[numero]
    bg = ligne.get("couleur")
    if bg == "": bg = "ffffff"

    if bg == None: print(numero)
    fg = ctes.contrasteur(bg)
    bg, fg = "#"+bg, "#"+fg

    affiListeLignes.add_radiobutton(label="Ligne "+numero, variable=varNumLigne, value=numero,
                                    background=bg, foreground=fg,
                                    command=setLigne)
#--Fin Liste lignes

menubar.add_cascade(label="Ligne", menu=affiListeLignes)
menubar.add_command(label="Tracer !", command=trace)
menubar.add_command(label="Couleur de la ligne", command=setCouleur)
menubar.add_command(label="Enregistrer le XML", command=ecritXML)
#-Fin Barre de menu

#-Carte
affiCarte = Frame(affiCarteEtInfos, bd=0)

imgCarte = PhotoImage(file=fichierCarte)
w, h = dimCarte
dimCanvasCarte = ctes.dimCanvasCarte

for i in range(2):
    dimCanvasCarte[i] = tailleEcran[i]
    if tailleEcran[i] < dimCanvasCarte[i] + ctes.ecartOblig[i]:
        dimCanvasCarte[i] -= ctes.ecartOblig[i]

canvasCarte = Canvas(affiCarte, width=dimCanvasCarte[0], height=dimCanvasCarte[1], scrollregion=(0, 0, w, h), bd=0)
canvasCarte.grid(row=0, column=0)

canvasCarte.create_image(0, 0, anchor=NW, image=imgCarte)

#--Scrollbars
defilY = Scrollbar(affiCarte, orient='vertical',
    command=canvasCarte.yview)
defilY.grid(row=0, column=1, sticky='ns')

defilX = Scrollbar(affiCarte, orient='horizontal',
    command=canvasCarte.xview)
defilX.grid(row=1, column=0, sticky='ew')

canvasCarte['xscrollcommand'] = defilX.set
canvasCarte['yscrollcommand'] = defilY.set
#--Fin Scrollbars

#-Fin Carte

#-Infos
affiInfos = PanedWindow(affiCarteEtInfos, orient=VERTICAL)

bg = ligneEnCours.get("couleur")
if bg == "": bg = "ffffff"
affiNumLigne = Label(affiInfos, text="Ligne "+ligneEnCours.get("num"), bg="#"+bg, fg="#"+ctes.contrasteur(bg), bd=0)

affiListeGares = Listbox(affiInfos, width=250, selectmode="single", bd=0)
setLigne()
#-Fin Infos

#-Positionnement
affiInfos.add(affiNumLigne)
affiInfos.add(affiListeGares)

affiCarteEtInfos.add(affiCarte)
affiCarteEtInfos.add(affiInfos)

affiCarteEtInfos.pack()
#-Fin Positionnement

#-Molette
commandes = {"<Button-1>":lambda x: clic(x, "gauche"),"<Button-2>": lambda x: clic(x, "milieu"),"<Button-3>":lambda x: clic(x, "droite"),"<Shift-Button-3>": lambda x: clic(x, "DROITE"),"<Button-4>":monteAscenseur, "<Button-5>":descendAscenseur, "<Shift-Button-4>":gaucheAscenseur, "<Shift-Button-5>":droiteAscenseur, "<MouseWheel>":ascenseurVertWindows, "<Shift-MouseWheel>":ascenseurHoriWindows}
for commande in commandes: canvasCarte.bind(commande, commandes[commande])
canvasCarte.bind_all("<Key>", touches)
#-Fin Molette

#-Listbox
affiListeGares.bind("<Double-1>", lambda x: clic("selecListBox", "gauche"))
affiListeGares.bind("<Double-3>", lambda x: clic("selecListBox", "DROITE"))
#-Fin Listbox
#Fin Initialisation graphique#############################################################################################

#Programme principal######################################################################################################
fenetre.protocol("WM_DELETE_WINDOW", fermetureFenetre)
fenetre.mainloop()
#Fin Programme principal##################################################################################################
