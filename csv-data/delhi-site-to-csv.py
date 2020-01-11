from bs4 import BeautifulSoup
import requests

class Gare():
    def __init__(self, nom, coord):
        self.nom = nom
        self.lignes = []
        self.coord = ", ".join([str(x) for x in coord])

    def ajoutLigne(self, nom):
        self.lignes.append(nom)

def trouveCoord(nom):
    texte = requests.get("https://www.google.fr/maps/search/"+nom.replace(" ","+")+"+Metro+Station+Delhi").text

    try:
        try:
            ligneCoord = texte.split("\n")[119]
            coordBrutes = ligneCoord.split(",")[-2:]

            coord = [float(coordBrutes[1][:-1]),float(coordBrutes[0])]
        except:
            ligneCoord = texte.split("\n")[132]
            coordBrutes = ligneCoord.split(",")[-2:]

            coord = [float(coordBrutes[1][:-1]),float(coordBrutes[0])]
    except:
        print(nom+" Metro Station ?")
        lat = input("Latitude : ")
        long = input("Longitude : ")

        coord = [float(long),float(lat)]
    finally:
        return coord

html = requests.get("https://delhimetrorail.info/delhi-metro-stations").text
soup = BeautifulSoup(html, "html.parser")

gares = dict()
for section in soup.find_all("section"):
    nomLigne = section["id"]
    print(nomLigne)

    for row in section.find_all("tr"):
        if ">ID<" in str(row): continue
        nom = row.a.text

        if nom not in gares:
            coord = trouveCoord(nom)
            gares[nom] = Gare(nom, coord)
        gares[nom].ajoutLigne(nomLigne)

with open("delhi.csv", "w") as fichier:
    printF = lambda x: fichier.write(x+"\n")

    for gare in gares.values():
        nom, coord, lignes = gare.nom, gare.coord, gare.lignes

        for ligne in lignes:
            printF(coord+";"+ligne+";"+nom)
