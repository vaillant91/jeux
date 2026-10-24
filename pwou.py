import copy
import math
import random
from functools import lru_cache
from pathlib import Path

import pygame

import sauvegarde


# Vue en perspective a la troisieme personne, rendue sans ressources externes.
LARGEUR_FENETRE = 1000
HAUTEUR_FENETRE = 720
LARGEUR_CARTE = 160
HAUTEUR_CARTE = 120
LARGEUR_CASE = 56
HAUTEUR_CASE = 20
LARGEUR_MINI_CARTE = 205
HAUTEUR_MINI_CARTE = 150
FPS = 60
CYCLE_JOUR_MS = 360_000
NUANCES_SAISONS = {
    "Printemps": (7, 12, 2),
    "Ete": (5, 5, -4),
    "Automne": (14, -7, -17),
    "Hiver": (8, 10, 14),
}

VERT_HERBE = (65, 145, 73)
VERT_CLAIR = (78, 158, 81)
BLEU_EAU = (42, 125, 190)
NOIR = (20, 31, 35)
BLANC = (245, 245, 225)


def biome_region(x, y):
    """Retourne le biome d'une region, y compris dans les nouvelles terres."""
    if x < 80:
        return "prairie" if x < 20 else "foret" if x < 40 else "desert" if x < 60 else "neige"
    if y < 60:
        return "prairie" if x < 100 else "foret" if x < 120 else "desert" if x < 140 else "neige"
    if y < 90:
        return "foret" if x < 100 else "prairie" if x < 120 else "desert" if x < 140 else "neige"
    return "prairie" if x < 100 else "foret" if x < 120 else "neige"


# Villages et royaumes traverses d'ouest en est.
VILLAGES = [
    {"nom": "Clairval", "royaume": "Prairies", "x": 9.5, "y": 9.5, "couleur": (205, 170, 101)},
    {"nom": "Brumebois", "royaume": "Foret", "x": 28.5, "y": 22.5, "couleur": (116, 92, 63)},
    {"nom": "Soleil-d'Or", "royaume": "Desert", "x": 48.5, "y": 35.5, "couleur": (214, 165, 83)},
    {"nom": "Givrehaut", "royaume": "Montagnes", "x": 68.5, "y": 48.5, "couleur": (157, 173, 191)},
]

HABITANTS_VILLAGES = (
    (
        ("Aline", "Ancienne", (71, 116, 151), (190, 202, 161), (137, 92, 64), "canne"),
        ("Milo", "Fermier", (112, 139, 78), (203, 177, 112), (95, 58, 39), "faucille"),
        ("Jeanne", "Boulangere", (157, 86, 67), (221, 194, 149), (83, 54, 45), "panier"),
        ("Tomas", "Garde", (70, 91, 112), (170, 163, 135), (116, 75, 48), "lance"),
        ("Lina", "Apprentie", (129, 87, 135), (221, 183, 133), (64, 44, 37), "livre"),
    ),
    (
        ("Edrin", "Gardien", (76, 111, 78), (174, 190, 147), (101, 62, 43), "canne"),
        ("Nella", "Herboriste", (151, 101, 71), (203, 179, 133), (72, 48, 40), "panier"),
        ("Boris", "Bucheron", (114, 75, 53), (188, 143, 101), (77, 49, 35), "hache"),
        ("Maelle", "Tisseuse", (88, 113, 139), (210, 188, 145), (113, 75, 48), "livre"),
        ("Ren", "Eclaireur", (70, 101, 78), (175, 157, 121), (65, 47, 39), "lance"),
    ),
    (
        ("Sanaa", "Cheffe", (161, 104, 54), (225, 191, 130), (70, 46, 34), "canne"),
        ("Yasmin", "Marchande", (137, 77, 64), (212, 163, 105), (74, 49, 38), "panier"),
        ("Idris", "Forgeron", (72, 86, 98), (176, 132, 91), (65, 43, 32), "marteau"),
        ("Nour", "Guide", (162, 132, 72), (231, 192, 128), (86, 55, 38), "lance"),
        ("Kamil", "Musicien", (108, 76, 123), (199, 151, 101), (51, 39, 35), "luth"),
    ),
    (
        ("Thoren", "Ancien", (89, 111, 128), (193, 203, 202), (119, 90, 73), "canne"),
        ("Freya", "Chasseuse", (83, 118, 119), (211, 185, 152), (131, 83, 55), "arc"),
        ("Oskar", "Forgeron", (87, 92, 107), (181, 146, 117), (99, 68, 52), "marteau"),
        ("Eira", "Guetteuse", (103, 132, 153), (224, 203, 166), (177, 137, 94), "lance"),
        ("Sven", "Messager", (129, 90, 72), (191, 157, 117), (91, 65, 51), "panier"),
    ),
)

RELIQUE_X = 75.5
RELIQUE_Y = 53.5

ARMES = {
    "epee_fer": {"nom": "Epee en fer", "type": "corps", "degats": 4, "couleur": (205, 218, 226), "description": "Une lame fiable."},
    "epee_royale": {"nom": "Epee royale", "type": "corps", "degats": 7, "couleur": (245, 207, 103), "description": "Une lame finement forge."},
    "hache_guerre": {"nom": "Hache de guerre", "type": "corps", "degats": 5, "couleur": (188, 198, 205), "description": "Lourde et devastatrice."},
    "arc_chasseur": {"nom": "Arc de chasseur", "type": "arc", "degats": 4, "couleur": (163, 112, 64), "description": "Arc court, rapide a bander."},
    "arc_long": {"nom": "Arc long", "type": "arc", "degats": 6, "couleur": (115, 79, 50), "description": "Grande portee et bonne puissance."},
    "arc_ancien": {"nom": "Arc des anciens", "type": "arc", "degats": 8, "couleur": (103, 183, 161), "description": "Un arc rare charge de magie."},
    "dague_fer": {"nom": "Dague en fer", "type": "corps", "degats": 2, "portee": 1.55, "delai": 300, "niveau": 1, "forme": "dague", "couleur": (185, 195, 196), "description": "Courte lame legere et rapide."},
    "lance_chasse": {"nom": "Lance de chasse", "type": "corps", "degats": 3, "portee": 2.7, "delai": 650, "niveau": 1, "forme": "lance", "couleur": (164, 178, 177), "description": "Longue portee, frappe lente."},
    "masse_fer": {"nom": "Masse d'armes", "type": "corps", "degats": 4, "portee": 1.85, "delai": 680, "niveau": 2, "forme": "masse", "couleur": (149, 158, 164), "description": "Tete lourde, coups puissants."},
    "arbalete": {"nom": "Arbalete", "type": "arc", "degats": 4, "vitesse_projectile": 14.0, "delai_tir": 850, "niveau": 2, "forme": "arbalete", "couleur": (131, 97, 63), "description": "Tir puissant, rechargement lent."},
    "lance_fer": {"nom": "Lance en fer", "type": "corps", "degats": 4, "portee": 3.0, "delai": 620, "niveau": 3, "forme": "lance", "couleur": (188, 198, 204), "description": "Pointe solide et grande allonge."},
    "epee_longue": {"nom": "Epee longue", "type": "corps", "degats": 8, "portee": 2.25, "delai": 540, "niveau": 3, "forme": "epee", "couleur": (211, 220, 224), "description": "Lame d'acier a deux mains."},
    "arc_composite": {"nom": "Arc composite", "type": "arc", "degats": 7, "vitesse_projectile": 13.0, "delai_tir": 450, "niveau": 3, "forme": "arc", "couleur": (147, 105, 68), "description": "Puissant et rapide a bander."},
    "marteau_guerre": {"nom": "Marteau de guerre", "type": "corps", "degats": 7, "portee": 2.0, "delai": 900, "niveau": 4, "forme": "marteau", "couleur": (162, 171, 174), "description": "Tres lourd, inflige de lourds degats."},
}

NIVEAU_MIN_ARMES = {
    "epee_fer": 1,
    "arc_chasseur": 1,
    "dague_fer": 1,
    "lance_chasse": 1,
    "epee_royale": 2,
    "arc_long": 2,
    "masse_fer": 2,
    "arbalete": 2,
    "lance_fer": 3,
    "epee_longue": 3,
    "arc_composite": 3,
    "hache_guerre": 3,
    "arc_ancien": 4,
    "marteau_guerre": 4,
}

BOUCLIERS = {
    "bouclier_bois": {"nom": "Bouclier en bois", "defense": 1, "couleur": (139, 91, 53), "description": "Reduit les degats recus de 1."},
    "bouclier_fer": {"nom": "Pavois de fer", "defense": 2, "couleur": (139, 157, 170), "description": "Reduit les degats recus de 2."},
    "bouclier_tour": {"nom": "Bouclier-tour", "defense": 3, "couleur": (94, 119, 145), "description": "Une protection lourde et solide."},
    "bouclier_dragon": {"nom": "Egide du dragon", "defense": 4, "couleur": (183, 92, 72), "description": "Un bouclier legendaire."},
}

MONSTRES = {
    "gelatine": {"vies": 1, "degats": 1, "vitesse": 1.15, "couleur": (92, 210, 121), "nom": "Gelatine"},
    "araignee": {"vies": 2, "degats": 1, "vitesse": 2.2, "couleur": (188, 116, 76), "nom": "Araignee"},
    "gobelin": {"vies": 3, "degats": 1, "vitesse": 1.7, "couleur": (208, 94, 69), "nom": "Gobelin"},
    "pillard": {"vies": 4, "degats": 1, "vitesse": 1.8, "couleur": (174, 91, 62), "nom": "Pillard des camps"},
    "chauve_souris": {"vies": 2, "degats": 1, "vitesse": 2.5, "couleur": (112, 92, 139), "nom": "Chauve-souris"},
    "loup": {"vies": 3, "degats": 2, "vitesse": 2.6, "couleur": (132, 145, 155), "nom": "Loup des neiges"},
    "chevalier": {"vies": 6, "degats": 2, "vitesse": 1.35, "couleur": (122, 118, 195), "nom": "Chevalier noir"},
    "ogre": {"vies": 16, "degats": 3, "vitesse": 0.88, "couleur": (116, 139, 73), "nom": "Ogre des cavernes", "boss": True, "portee": 1.65, "collision": 0.7},
    "centaure": {"vies": 18, "degats": 2, "vitesse": 1.55, "couleur": (151, 91, 54), "nom": "Centaure des plaines", "boss": True, "portee": 1.25, "collision": 0.62},
    "cyclope": {"vies": 24, "degats": 3, "vitesse": 0.88, "couleur": (106, 133, 91), "nom": "Cyclope des rochers", "boss": True, "portee": 1.7, "collision": 0.72},
    "geant": {"vies": 30, "degats": 4, "vitesse": 0.72, "couleur": (139, 108, 84), "nom": "Geant des cendres", "boss": True, "portee": 1.9, "collision": 0.82},
    "dragon": {"vies": 42, "degats": 4, "vitesse": 0.82, "couleur": (184, 54, 49), "nom": "Dragon ancien a trois tetes", "boss": True, "portee": 2.0, "collision": 1.0},
}

ECHOS_MANGAS = (
    {
        "id": "equipage_des_mers",
        "manga": "One Piece",
        "nom": "Boussole des horizons",
        "indice": "Une vieille carte evoque un equipage et un tresor au bout des mers.",
        "x": 19.5,
        "y": 10.5,
        "couleur": (221, 166, 76),
        "symbole": "boussole",
    },
    {
        "id": "orbe_des_etoiles",
        "manga": "Dragon Ball",
        "nom": "Orbe des constellations",
        "indice": "Un orbe aux etoiles aurait ete vu pres des dunes du sud.",
        "x": 49.5,
        "y": 32.5,
        "couleur": (240, 157, 67),
        "symbole": "etoile",
    },
    {
        "id": "sceau_du_justicier",
        "manga": "One Punch Man",
        "nom": "Sceau du justicier",
        "indice": "Un heros legendaire aurait regle un duel d'un seul coup.",
        "x": 34.5,
        "y": 29.5,
        "couleur": (203, 76, 65),
        "symbole": "poing",
    },
    {
        "id": "insigne_des_mages",
        "manga": "Fairy Tail",
        "nom": "Insigne de la guilde",
        "indice": "Un insigne de guilde magique se cache dans les bois brumeux.",
        "x": 37.5,
        "y": 22.5,
        "couleur": (157, 106, 210),
        "symbole": "guilde",
    },
    {
        "id": "carnet_de_transmutation",
        "manga": "Fullmetal Alchemist",
        "nom": "Carnet de transmutation",
        "indice": "Un carnet alchimique porte un cercle grave dans la pierre.",
        "x": 61.5,
        "y": 48.5,
        "couleur": (183, 190, 190),
        "symbole": "cercle",
    },
    {
        "id": "fiole_de_reveil",
        "manga": "Dr. Stone",
        "nom": "Fiole de renaissance",
        "indice": "Une fiole scientifique attend pres des anciennes ruines.",
        "x": 91.5,
        "y": 40.5,
        "couleur": (97, 205, 174),
        "symbole": "fiole",
    },
)

ECHOS_MANGAS = tuple(
    {**echo, "univers": "manga", "oeuvre": echo["manga"]}
    for echo in ECHOS_MANGAS
) + (
    {
        "id": "journal_des_courants",
        "univers": "manga",
        "oeuvre": "One Piece",
        "manga": "One Piece",
        "nom": "Journal des courants",
        "indice": "Une route maritime impossible est tracee dans un vieux journal.",
        "x": 14.5,
        "y": 20.5,
        "couleur": (90, 172, 201),
        "symbole": "boussole",
    },
    {
        "id": "carte_du_grand_large",
        "univers": "manga",
        "oeuvre": "One Piece",
        "manga": "One Piece",
        "nom": "Carte du grand large",
        "indice": "Un fragment de carte attend pres des falaises de l'ouest.",
        "x": 26.5,
        "y": 15.5,
        "couleur": (221, 166, 76),
        "symbole": "etoile",
    },
    {
        "id": "orbe_des_six_etoiles",
        "univers": "manga",
        "oeuvre": "Dragon Ball",
        "manga": "Dragon Ball",
        "nom": "Orbe des six etoiles",
        "indice": "Un autre orbe scintille dans les plaines centrales.",
        "x": 43.5,
        "y": 28.5,
        "couleur": (240, 157, 67),
        "symbole": "etoile",
    },
    {
        "id": "orbe_du_voeu",
        "univers": "manga",
        "oeuvre": "Dragon Ball",
        "manga": "Dragon Ball",
        "nom": "Orbe du voeu",
        "indice": "Une lueur orange a ete apercue sur le chemin des montagnes.",
        "x": 70.5,
        "y": 44.5,
        "couleur": (250, 180, 83),
        "symbole": "boussole",
    },
    {
        "id": "cape_du_defenseur",
        "univers": "manga",
        "oeuvre": "One Punch Man",
        "manga": "One Punch Man",
        "nom": "Cape du defenseur",
        "indice": "Une cape de heros flotte au-dessus d'un ancien camp.",
        "x": 18.5,
        "y": 29.5,
        "couleur": (213, 76, 65),
        "symbole": "guilde",
    },
    {
        "id": "medaille_du_coup_unique",
        "univers": "manga",
        "oeuvre": "One Punch Man",
        "manga": "One Punch Man",
        "nom": "Medaille du coup unique",
        "indice": "Une medaille marque l'endroit d'un duel tres bref.",
        "x": 57.5,
        "y": 28.5,
        "couleur": (191, 66, 60),
        "symbole": "poing",
    },
    {
        "id": "flamme_de_guilde",
        "univers": "manga",
        "oeuvre": "Fairy Tail",
        "manga": "Fairy Tail",
        "nom": "Flamme de la guilde",
        "indice": "Une flamme violette brille pres du vieux sentier forestier.",
        "x": 29.5,
        "y": 32.5,
        "couleur": (157, 106, 210),
        "symbole": "guilde",
    },
    {
        "id": "grimoire_des_liens",
        "univers": "manga",
        "oeuvre": "Fairy Tail",
        "manga": "Fairy Tail",
        "nom": "Grimoire des liens",
        "indice": "Un grimoire parle de la force des compagnons.",
        "x": 53.5,
        "y": 48.5,
        "couleur": (170, 118, 220),
        "symbole": "cercle",
    },
    {
        "id": "gant_articule",
        "univers": "manga",
        "oeuvre": "Fullmetal Alchemist",
        "manga": "Fullmetal Alchemist",
        "nom": "Gant articule",
        "indice": "Un gant de metal repose pres des anciennes forges.",
        "x": 64.5,
        "y": 57.5,
        "couleur": (175, 184, 193),
        "symbole": "poing",
    },
    {
        "id": "sceau_de_lequilibre",
        "univers": "manga",
        "oeuvre": "Fullmetal Alchemist",
        "manga": "Fullmetal Alchemist",
        "nom": "Sceau de l'equilibre",
        "indice": "Un cercle aux symboles geometriques est grave dans les ruines.",
        "x": 76.5,
        "y": 43.5,
        "couleur": (196, 184, 157),
        "symbole": "cercle",
    },
    {
        "id": "tablette_scientifique",
        "univers": "manga",
        "oeuvre": "Dr. Stone",
        "manga": "Dr. Stone",
        "nom": "Tablette scientifique",
        "indice": "Une tablette de calcul attend dans une clairiere au sud.",
        "x": 84.5,
        "y": 32.5,
        "couleur": (108, 197, 174),
        "symbole": "cercle",
    },
    {
        "id": "fiole_de_reveil_pale",
        "univers": "manga",
        "oeuvre": "Dr. Stone",
        "manga": "Dr. Stone",
        "nom": "Fiole de reveil pale",
        "indice": "Une seconde fiole est cachee vers les terres lointaines.",
        "x": 110.5,
        "y": 53.5,
        "couleur": (95, 217, 179),
        "symbole": "fiole",
    },
)

ECHOS_ZELDA = (
    {
        "id": "relique_des_origines",
        "oeuvre": "The Legend of Zelda",
        "nom": "Carte des premieres terres",
        "indice": "Une carte ancienne montre un chemin perdu dans les prairies.",
        "x": 8.5,
        "y": 19.5,
        "couleur": (211, 183, 97),
        "symbole": "boussole",
    },
    {
        "id": "relique_du_royaume_du_nord",
        "oeuvre": "Zelda II: The Adventure of Link",
        "nom": "Ecu du royaume du nord",
        "indice": "Un ecu oublie serait cache pres d'un vieux fort.",
        "x": 15.5,
        "y": 38.5,
        "couleur": (183, 156, 105),
        "symbole": "guilde",
    },
    {
        "id": "relique_du_monde_ombre",
        "oeuvre": "A Link to the Past",
        "nom": "Fragment du monde-reflet",
        "indice": "Un miroir terni luit a la lisiere des bois.",
        "x": 24.5,
        "y": 42.5,
        "couleur": (151, 108, 185),
        "symbole": "cercle",
    },
    {
        "id": "relique_de_lile_revee",
        "oeuvre": "Link's Awakening",
        "nom": "Coquillage des songes",
        "indice": "Une coquille nacree a ete trouvee au bord d'un lac.",
        "x": 33.5,
        "y": 12.5,
        "couleur": (114, 191, 196),
        "symbole": "boussole",
    },
    {
        "id": "relique_du_temps",
        "oeuvre": "Ocarina of Time",
        "nom": "Flute des heures",
        "indice": "Une flute de pierre resonne pres des collines.",
        "x": 40.5,
        "y": 39.5,
        "couleur": (133, 173, 200),
        "symbole": "guilde",
    },
    {
        "id": "relique_des_masques",
        "oeuvre": "Majora's Mask",
        "nom": "Masque des trois lunes",
        "indice": "Un masque rituel veille dans une clairiere isolee.",
        "x": 47.5,
        "y": 20.5,
        "couleur": (187, 84, 119),
        "symbole": "etoile",
    },
    {
        "id": "relique_des_saisons",
        "oeuvre": "Oracle of Seasons",
        "nom": "Boussole des saisons",
        "indice": "Une boussole aux quatre couleurs se cache dans les plaines.",
        "x": 54.5,
        "y": 17.5,
        "couleur": (197, 155, 75),
        "symbole": "boussole",
    },
    {
        "id": "relique_des_ages",
        "oeuvre": "Oracle of Ages",
        "nom": "Sablier des ages",
        "indice": "Un sablier de cristal serait enfoui pres des dunes.",
        "x": 59.5,
        "y": 30.5,
        "couleur": (105, 165, 207),
        "symbole": "cercle",
    },
    {
        "id": "relique_des_quatre_lames",
        "oeuvre": "Four Swords",
        "nom": "Eclat des quatre lames",
        "indice": "Quatre eclats colores sont reunis au sud de la foret.",
        "x": 28.5,
        "y": 51.5,
        "couleur": (172, 107, 173),
        "symbole": "etoile",
    },
    {
        "id": "relique_du_minish",
        "oeuvre": "The Minish Cap",
        "nom": "Bonnet des minuscules",
        "indice": "Un minuscule bonnet repose au pied d'un arbre immense.",
        "x": 38.5,
        "y": 44.5,
        "couleur": (94, 174, 107),
        "symbole": "guilde",
    },
    {
        "id": "relique_du_loup_crepusculaire",
        "oeuvre": "Twilight Princess",
        "nom": "Gemme du crepuscule",
        "indice": "Une gemme sombre scintille au bord des montagnes.",
        "x": 73.5,
        "y": 34.5,
        "couleur": (110, 96, 164),
        "symbole": "cercle",
    },
    {
        "id": "relique_du_grand_large",
        "oeuvre": "The Wind Waker",
        "nom": "Voile du grand large",
        "indice": "Un morceau de voile flotte pres de la cote orientale.",
        "x": 83.5,
        "y": 18.5,
        "couleur": (82, 177, 204),
        "symbole": "boussole",
    },
    {
        "id": "relique_du_compas_des_mers",
        "oeuvre": "Phantom Hourglass",
        "nom": "Compas des mers",
        "indice": "Un compas marin indique un detour vers le sud-est.",
        "x": 100.5,
        "y": 29.5,
        "couleur": (121, 179, 200),
        "symbole": "etoile",
    },
    {
        "id": "relique_du_chemin_de_fer",
        "oeuvre": "Spirit Tracks",
        "nom": "Sifflet des rails perdus",
        "indice": "Un sifflet de locomotive dort pres des plaines lointaines.",
        "x": 113.5,
        "y": 34.5,
        "couleur": (184, 142, 84),
        "symbole": "fiole",
    },
    {
        "id": "relique_du_ciel",
        "oeuvre": "Skyward Sword",
        "nom": "Plume des iles celestes",
        "indice": "Une plume blanche est tombee des hauts plateaux.",
        "x": 79.5,
        "y": 65.5,
        "couleur": (216, 223, 211),
        "symbole": "etoile",
    },
    {
        "id": "relique_du_monde_inverse",
        "oeuvre": "A Link Between Worlds",
        "nom": "Cadre du monde-reflet",
        "indice": "Un cadre de pierre semble ouvrir sur un autre paysage.",
        "x": 94.5,
        "y": 68.5,
        "couleur": (166, 118, 190),
        "symbole": "cercle",
    },
    {
        "id": "relique_des_trois_maisons",
        "oeuvre": "Tri Force Heroes",
        "nom": "Insigne des trois compagnons",
        "indice": "Un insigne triangulaire attend pres des trois rochers.",
        "x": 121.5,
        "y": 48.5,
        "couleur": (209, 139, 171),
        "symbole": "guilde",
    },
    {
        "id": "relique_de_la_nature_sauvage",
        "oeuvre": "Breath of the Wild",
        "nom": "Ardoise des terres sauvages",
        "indice": "Une tablette ancienne luit au milieu des herbes hautes.",
        "x": 130.5,
        "y": 32.5,
        "couleur": (87, 192, 193),
        "symbole": "cercle",
    },
    {
        "id": "relique_des_profondeurs",
        "oeuvre": "Tears of the Kingdom",
        "nom": "Cristal des profondeurs",
        "indice": "Un cristal lumineux semble venir des profondeurs de la terre.",
        "x": 137.5,
        "y": 61.5,
        "couleur": (153, 98, 204),
        "symbole": "etoile",
    },
    {
        "id": "relique_des_sagesse",
        "oeuvre": "Echoes of Wisdom",
        "nom": "Clochette des echos",
        "indice": "Une clochette repond a chaque son dans les terres du sud.",
        "x": 145.5,
        "y": 85.5,
        "couleur": (216, 174, 102),
        "symbole": "guilde",
    },
)

ECHOS_ZELDA += (
    {
        "id": "relique_des_quatre_aventuriers",
        "oeuvre": "Four Swords Adventures",
        "nom": "Banniere des quatre aventuriers",
        "indice": "Une banniere a quatre couleurs flotte pres des marais du sud.",
        "x": 11.5,
        "y": 61.5,
        "couleur": (183, 92, 119),
        "symbole": "guilde",
    },
    {
        "id": "relique_des_battements",
        "oeuvre": "The Legend of Zelda: Game & Watch",
        "nom": "Medaille des gardes nocturnes",
        "indice": "Une medaille ancienne se cache au sud de la grande route.",
        "x": 20.5,
        "y": 73.5,
        "couleur": (192, 178, 105),
        "symbole": "etoile",
    },
    {
        "id": "relique_des_tablettes_anciennes",
        "oeuvre": "BS The Legend of Zelda: Ancient Stone Tablets",
        "nom": "Tablette des quatre fragments",
        "indice": "Une tablette brisee porte des signes au sud des forets.",
        "x": 31.5,
        "y": 67.5,
        "couleur": (150, 179, 128),
        "symbole": "cercle",
    },
    {
        "id": "relique_du_tir",
        "oeuvre": "Link's Crossbow Training",
        "nom": "Cible des archers",
        "indice": "Une cible percee de fleches attend dans les terres du sud.",
        "x": 46.5,
        "y": 70.5,
        "couleur": (203, 113, 79),
        "symbole": "etoile",
    },
    {
        "id": "relique_du_champ_de_bataille",
        "oeuvre": "Hyrule Warriors",
        "nom": "Etendard des armees",
        "indice": "Un vieil etendard de bataille repose pres des collines.",
        "x": 58.5,
        "y": 77.5,
        "couleur": (197, 132, 75),
        "symbole": "guilde",
    },
    {
        "id": "relique_du_sceau_calme",
        "oeuvre": "Hyrule Warriors: Age of Calamity",
        "nom": "Sceau du calme",
        "indice": "Un sceau ancien protege le passage vers l'est.",
        "x": 70.5,
        "y": 84.5,
        "couleur": (110, 167, 191),
        "symbole": "cercle",
    },
    {
        "id": "relique_du_rythme",
        "oeuvre": "Cadence of Hyrule",
        "nom": "Tambour des voyageurs",
        "indice": "Un tambour de marche resonne dans la vallee du sud.",
        "x": 88.5,
        "y": 80.5,
        "couleur": (189, 105, 126),
        "symbole": "guilde",
    },
    {
        "id": "relique_du_royaume_des_rupies",
        "oeuvre": "Freshly-Picked Tingle's Rosy Rupeeland",
        "nom": "Bourse des voyageurs",
        "indice": "Une bourse coloree est cachee pres des ruines du sud-est.",
        "x": 108.5,
        "y": 84.5,
        "couleur": (97, 181, 133),
        "symbole": "boussole",
    },
    {
        "id": "relique_du_bataillon",
        "oeuvre": "Hyrule Warriors: Age of Imprisonment",
        "nom": "Insigne des ages anciens",
        "indice": "Un insigne de bataille dort dans les terres orientales.",
        "x": 119.5,
        "y": 103.5,
        "couleur": (143, 119, 190),
        "symbole": "etoile",
    },
)

ECHOS_HOMMAGES = ECHOS_MANGAS + tuple(
    {**echo, "univers": "Zelda"}
    for echo in ECHOS_ZELDA
)

INDICES_ECHOS_VILLAGES = (
    "Temples, pirates et tresors se cachent dans les terres lointaines.",
    "Des reliques de guildes et des echos du monde-reflet sont en foret.",
    "Orbes etoiles, sabliers et souvenirs magiques attendent au desert.",
    "Le ciel, les rails perdus et les ruines gardent d'autres reliques.",
)

COFFRES_MONDE = (
    {"x": 16.5, "y": 14.5, "ouvert": False, "armes": ["arc_chasseur", "dague_fer"], "boucliers": ["bouclier_fer"], "fleches": 16, "gemmes": 2},
    {"x": 36.5, "y": 27.5, "ouvert": False, "armes": ["epee_royale", "arc_long", "lance_chasse"], "boucliers": ["bouclier_tour"], "fleches": 24, "gemmes": 4},
    {"x": 57.5, "y": 40.5, "ouvert": False, "armes": ["hache_guerre", "masse_fer"], "boucliers": [], "fleches": 30, "gemmes": 6},
    {"x": 72.5, "y": 50.5, "ouvert": False, "armes": ["arc_ancien", "epee_royale", "lance_fer"], "boucliers": ["bouclier_dragon"], "fleches": 36, "gemmes": 10},
    {"x": 12.5, "y": 29.5, "ouvert": False, "armes": [], "boucliers": [], "fleches": 10, "gemmes": 3},
    {"x": 31.5, "y": 42.5, "ouvert": False, "armes": ["arc_chasseur"], "boucliers": [], "fleches": 14, "gemmes": 4},
    {"x": 91.5, "y": 57.5, "ouvert": False, "armes": ["epee_royale"], "boucliers": [], "fleches": 18, "gemmes": 5},
    {"x": 126.5, "y": 88.5, "ouvert": False, "armes": ["hache_guerre"], "boucliers": [], "fleches": 22, "gemmes": 7},
    {"x": 20.5, "y": 37.5, "ouvert": False, "armes": ["lance_chasse"], "boucliers": [], "fleches": 8, "gemmes": 2},
    {"x": 44.5, "y": 58.5, "ouvert": False, "armes": ["masse_fer"], "boucliers": [], "fleches": 10, "gemmes": 3},
    {"x": 82.5, "y": 53.5, "ouvert": False, "armes": ["arbalete"], "boucliers": [], "fleches": 14, "gemmes": 4},
    {"x": 99.5, "y": 61.5, "ouvert": False, "armes": ["epee_longue"], "boucliers": [], "fleches": 16, "gemmes": 5},
    {"x": 118.5, "y": 72.5, "ouvert": False, "armes": ["arc_composite"], "boucliers": [], "fleches": 20, "gemmes": 6},
    {"x": 144.5, "y": 91.5, "ouvert": False, "armes": ["marteau_guerre"], "boucliers": [], "fleches": 24, "gemmes": 8},
)


def creer_carte():
    """Fabrique une grande carte avec des chemins, des mares, des arbres et des rochers."""
    hasard = random.Random(17)
    carte = [["herbe" for _ in range(LARGEUR_CARTE)] for _ in range(HAUTEUR_CARTE)]
    chemins = set()

    # L'ancienne route est conservee ; elle serpente ensuite vers les terres lointaines.
    for x in range(2, 78):
        y_centre = int(3 + (x - 2) * 0.65 + math.sin(x / 4) * 1.5)
        for y in range(max(1, y_centre - 1), min(HAUTEUR_CARTE - 1, y_centre + 2)):
            chemins.add((x, y))
            carte[y][x] = "chemin"

    for x in range(78, LARGEUR_CARTE - 2):
        y_centre = int(53 + (x - 78) * 0.17 + math.sin(x / 5) * 1.3)
        for y in range(max(1, y_centre - 1), min(HAUTEUR_CARTE - 1, y_centre + 2)):
            chemins.add((x, y))
            carte[y][x] = "chemin"

    # Un sentier secondaire descend vers les vallees du sud.
    for y in range(52, HAUTEUR_CARTE - 2):
        x_centre = int(78 + (y - 52) * 0.42 + math.sin(y / 7) * 2)
        for x in range(max(1, x_centre - 1), min(LARGEUR_CARTE - 1, x_centre + 2)):
            chemins.add((x, y))
            carte[y][x] = "chemin"

    # Plusieurs lacs et etangs sont places hors du chemin principal.
    lacs = (
        (14, 22, 5, 4), (29, 10, 4, 3), (42, 36, 5, 3),
        (50, 20, 3, 5), (63, 17, 5, 4), (71, 42, 4, 5),
        (94, 25, 7, 5), (116, 42, 6, 8), (143, 25, 7, 5),
        (91, 91, 8, 5), (126, 103, 7, 6), (148, 75, 5, 8),
    )
    for cx, cy, rayon_x, rayon_y in lacs:
        for y in range(1, HAUTEUR_CARTE - 1):
            for x in range(1, LARGEUR_CARTE - 1):
                distance = ((x - cx) / rayon_x) ** 2 + ((y - cy) / rayon_y) ** 2
                if distance < 1 and (x, y) not in chemins:
                    carte[y][x] = "eau"

    # Des cours d'eau sinueux donnent une forme plus naturelle aux nouveaux biomes.
    for y in range(3, 58):
        x_riviere = round(108 + math.sin(y / 6) * 3)
        for x in range(x_riviere, x_riviere + 2):
            if (x, y) not in chemins:
                carte[y][x] = "eau"
    for y in range(63, HAUTEUR_CARTE - 3):
        x_riviere = round(137 + math.sin(y / 7) * 4)
        for x in range(x_riviere, x_riviere + 2):
            if (x, y) not in chemins:
                carte[y][x] = "eau"

    # Chaque region a son propre type de terrain. Les chemins restent visibles.
    for y in range(HAUTEUR_CARTE):
        for x in range(LARGEUR_CARTE):
            if carte[y][x] in ("eau", "chemin"):
                continue
            carte[y][x] = biome_region(x, y)

    arbres = set()
    rochers = set()
    cases_degagees = {
        (px + dx, py + dy)
        for px, py in chemins
        for dx in range(-2, 3)
        for dy in range(-2, 3)
        if abs(dx) + abs(dy) < 3
    }
    for y in range(2, HAUTEUR_CARTE - 2):
        for x in range(2, LARGEUR_CARTE - 2):
            if carte[y][x] not in ("prairie", "foret", "desert", "neige") or abs(x - 3) + abs(y - 3) < 4:
                continue
            if (x, y) in cases_degagees:
                continue
            taux_arbres = 0.28 if carte[y][x] == "foret" else 0.09 if carte[y][x] == "neige" else 0.035
            if hasard.random() < taux_arbres:
                arbres.add((x, y))
            elif hasard.random() < (0.085 if carte[y][x] in ("desert", "neige") else 0.05):
                rochers.add((x, y))

    # Degage une place plus large autour des villages et de leurs maisons.
    for village in VILLAGES:
        vx, vy = int(village["x"]), int(village["y"])
        for y in range(vy - 5, vy + 6):
            for x in range(vx - 5, vx + 6):
                if 0 <= x < LARGEUR_CARTE and 0 <= y < HAUTEUR_CARTE:
                    if abs(x - vx) + abs(y - vy) <= 5 and carte[y][x] == "eau":
                        carte[y][x] = "chemin"
                    if (x - vx) ** 2 + (y - vy) ** 2 <= 23:
                        arbres.discard((x, y))
                        rochers.discard((x, y))

    return carte, arbres, rochers


def creer_decorations(carte, arbres, rochers, ruines):
    """Ajoute des details non bloquants propres a chaque biome."""
    hasard = random.Random(41)
    obstacles = arbres | rochers | ruines
    decorations = []
    fleurs = ((244, 205, 108), (228, 139, 157), (226, 226, 183))
    for y, ligne in enumerate(carte):
        for x, terrain in enumerate(ligne):
            if terrain not in ("prairie", "foret", "desert", "neige") or (x, y) in obstacles:
                continue
            probabilite = {
                "prairie": 0.12,
                "foret": 0.075,
                "desert": 0.055,
                "neige": 0.045,
            }[terrain]
            if hasard.random() >= probabilite:
                continue

            if terrain == "prairie":
                tirage = hasard.random()
                sorte = "herbe_haute" if tirage < 0.24 else "fleur" if tirage < 0.66 else "herbe"
                couleur = hasard.choice(fleurs)
            elif terrain == "foret":
                tirage = hasard.random()
                sorte = "herbe_haute" if tirage < 0.28 else "champignon" if tirage < 0.56 else "fougere"
                couleur = (196, 125, 97) if sorte == "champignon" else (104, 164, 82)
            elif terrain == "desert":
                sorte = "touffe"
                couleur = (169, 127, 69)
            else:
                sorte = "cristal"
                couleur = (203, 235, 239)
            decorations.append({
                "x": x + hasard.uniform(0.25, 0.75),
                "y": y + hasard.uniform(0.25, 0.75),
                "type": sorte,
                "couleur": couleur,
            })
    return decorations


def projeter(x, y, camera_x, camera_y):
    """Convertit une position de la carte en position a l'ecran."""
    ecran_x = LARGEUR_FENETRE // 2 + (x - y - camera_x + camera_y) * LARGEUR_CASE / 2
    ecran_y = HAUTEUR_FENETRE // 2 + (x + y - camera_x - camera_y) * HAUTEUR_CASE / 2
    return round(ecran_x), round(ecran_y)


@lru_cache(maxsize=65_536)
def _calculer_altitude(x, y):
    pics = (
        (65.5, 45.5, 4.4, 8.0), (74.0, 39.0, 3.2, 6.2), (73.0, 51.5, 2.6, 5.0),
        (88.0, 19.0, 2.5, 8.0), (116.0, 17.0, 2.0, 7.0),
        (130.0, 84.0, 3.0, 9.0), (149.0, 97.0, 4.2, 11.0),
        (42.0, 103.0, 2.8, 9.0),
    )
    return sum(
        hauteur * math.exp(-((x - px) ** 2 + (y - py) ** 2) / (rayon ** 2))
        for px, py, hauteur, rayon in pics
    )


class Aventure:
    """Contient le monde, les regles de jeu, les combats et le dessin."""

    def __init__(self):
        pygame.init()
        self.ecran = pygame.display.set_mode((LARGEUR_FENETRE, HAUTEUR_FENETRE))
        pygame.display.set_caption("Les ruines de Valombre")
        self.horloge = pygame.time.Clock()
        self.police = pygame.font.Font(None, 27)
        self.grande_police = pygame.font.Font(None, 64)
        self.police_details = pygame.font.Font(None, 21)
        self.lueur_soleil = pygame.Surface((220, 220), pygame.SRCALPHA)
        for rayon in range(106, 0, -2):
            pygame.draw.circle(
                self.lueur_soleil,
                (255, 222, 158, round(24 * (1 - rayon / 107) ** 2)),
                (110, 110),
                rayon,
            )
        self.brume_horizon = {}
        couleurs_brume = {
            "prairie": (169, 193, 197),
            "foret": (147, 176, 161),
            "desert": (211, 187, 150),
            "montagnes": (171, 196, 208),
        }
        for biome, couleur in couleurs_brume.items():
            brume = pygame.Surface((LARGEUR_FENETRE, 150), pygame.SRCALPHA)
            for y in range(brume.get_height()):
                progression = y / max(1, brume.get_height() - 1)
                alpha = round(48 * math.sin(math.pi * progression) ** 2)
                pygame.draw.line(brume, (*couleur, alpha), (0, y), (LARGEUR_FENETRE, y))
            self.brume_horizon[biome] = brume
        self._projection_cache = {}
        self.vignette = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        for bord in range(55):
            alpha = round(45 * (1 - bord / 55) ** 2)
            pygame.draw.rect(
                self.vignette,
                (15, 24, 31, alpha),
                (bord, bord, LARGEUR_FENETRE - bord * 2, HAUTEUR_FENETRE - bord * 2),
                1,
            )
        self.filtre_nuit = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        self.filtre_crepuscule = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        self.voile_orage = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        self.voile_orage.fill((18, 25, 42, 25))
        self.phase_journee = 0.5
        self.elevation_soleil = 1.0
        self.lumiere_jour = 1.0
        self.lumiere_crepuscule = 0.0
        self.temps_monde = 0.0
        self.saison = "Printemps"
        self.meteo = "clair"
        self._meteo_precedente = "clair"
        self.icones_equipement = {}

        self.carte, self.arbres, self.rochers = creer_carte()
        self.ruines = {(74, 52), (77, 52), (74, 55), (77, 55)}
        self.decorations = creer_decorations(self.carte, self.arbres, self.rochers, self.ruines)
        self.cases_triees = sorted(
            (x + y, x, y)
            for y in range(HAUTEUR_CARTE)
            for x in range(LARGEUR_CARTE)
        )
        self.mini_carte = self.creer_mini_carte()
        self.villages = []
        positions_habitants = ((1.2, 0.35), (-1.45, 0.45), (-0.45, -1.45), (1.55, 1.35), (-1.6, -1.5))
        positions_maisons = (
            (-3.0, -2.0), (0.0, -3.5), (3.0, -2.0),
            (-3.4, 1.7), (0.0, 3.5), (3.4, 1.7),
        )
        for village_index, definition in enumerate(VILLAGES):
            village = dict(definition)
            village["biome"] = biome_region(village["x"], village["y"])
            village["maisons"] = [
                {
                    "x": village["x"] + dx,
                    "y": village["y"] + dy,
                    "couleur": village["couleur"],
                    "variante": index,
                    "biome": village["biome"],
                }
                for index, (dx, dy) in enumerate(positions_maisons)
            ]
            village["habitants"] = [
                {
                    "nom": personne[0],
                    "metier": personne[1],
                    "tunique": personne[2],
                    "peau": personne[3],
                    "cheveux": personne[4],
                    "outil": personne[5],
                    "x": village["x"] + positions_habitants[index][0],
                    "y": village["y"] + positions_habitants[index][1],
                    "phase": village_index * 1.7 + index * 2.1,
                    "donneur_quete": index == 0,
                    "village_index": village_index,
                }
                for index, personne in enumerate(HABITANTS_VILLAGES[village_index])
            ]
            self.villages.append(village)
        self.dans_grotte = False
        self.grotte_active = None
        self.cinematique = None
        self.cinematique_index = 0
        self.cinematique_suivante = 0
        self.cinematique_page_debut = 0
        self.voile_cinematique = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        self.aura_cinematique = pygame.Surface((144, 240), pygame.SRCALPHA)
        pygame.draw.ellipse(self.aura_cinematique, (205, 170, 93, 12), (4, 4, 136, 232))
        pygame.draw.ellipse(self.aura_cinematique, (227, 195, 123, 12), (22, 22, 100, 196))
        self.monde_surface = None
        self.joueur_x = 3.5
        self.joueur_y = 3.5
        self.chemin_sauvegarde = Path(__file__).with_name("sauvegarde.json")
        self.vies = 5
        self.score = 0
        self.echos_decouverts = set()
        self.nourriture = 2
        self.faim = 100
        self.temps_faim = 0
        self.temps_degats_faim = 0
        self.message = "Explore les royaumes et parle aux habitants avec E."
        self.message_jusqua = 5000
        self.camera_yaw = math.atan2(0.65, 1.0)
        self.direction = (math.cos(self.camera_yaw), math.sin(self.camera_yaw))
        self.camera_drag = False
        self.accroupi = False
        self.temps_marche = 0.0
        self.en_marche = False
        self.grimpe = False
        self.endurance = 100.0
        self.invulnerable_jusqua = 0
        self.attaque_jusqua = 0
        self.attaque_prete = 0
        self.attaque_touche = False
        self.attaque_affichage_debut = 0
        self.attaque_affichage_jusqua = 0
        self.projectiles = []
        self.tir_pret = 0
        self.piege_prochain = 0
        self.esquive_jusqua = 0
        self.esquive_prete = 0
        self.special_jusqua = 0
        self.special_prete = 0
        self.special_debut = 0
        self.inventaire_ouvert = False
        self.inventaire_index = 0
        self.armes = ["epee_fer"]
        self.boucliers = ["bouclier_bois"]
        self.arme_equipee = "epee_fer"
        self.bouclier_equipe = "bouclier_bois"
        self.fleches = 12
        self.termine = False
        self.gagne = False
        self.game_over = False
        self.departs_quetes = {}
        self.quetes = [
            {"nom": "Les recoltes perdues", "detail": "Ramasse 3 rations.", "type": "nourriture", "besoin": 3, "progres": 0, "active": False, "faite": False, "recompense": 2},
            {"nom": "Les gardiens des camps", "detail": "Vaincs les boss de 2 camps.", "type": "repaire", "besoin": 2, "progres": 0, "active": False, "faite": False, "recompense": 6},
            {"nom": "Les profondeurs maudites", "detail": "Vaincs 3 monstres dans une grotte.", "type": "grotte", "besoin": 3, "progres": 0, "active": False, "faite": False, "recompense": 4},
            {"nom": "Le dragon des cimes", "detail": "Vaincs le dragon ancien a trois tetes.", "type": "dragon", "besoin": 1, "progres": 0, "active": False, "faite": False, "recompense": 8},
        ]
        self.monstres_grottes_vaincus = 0
        self.dragon_vaincu = False

        self.repaire_monstres = [
            {"nom": "Camp des pillards", "x": 17, "y": 18, "niveau": 1, "monstres": ("pillard", "araignee", "gobelin"), "chef": "centaure"},
            {"nom": "Nid des loups", "x": 35, "y": 18, "niveau": 2, "monstres": ("chauve_souris", "loup", "pillard"), "chef": "cyclope"},
            {"nom": "Fort des cendres", "x": 52, "y": 43, "niveau": 3, "monstres": ("araignee", "chauve_souris", "chevalier"), "chef": "geant"},
            {"nom": "Bastion des glaces", "x": 62, "y": 55, "niveau": 4, "monstres": ("chauve_souris", "loup", "pillard"), "chef": "cyclope"},
        ]
        for repaire in self.repaire_monstres:
            repaire["conquis"] = False
            repaire["boss_vaincu"] = False
            repaire["garnison_v2"] = True

        # Quelques rencontres jalonnent la route ; le dragon garde les ruines.
        emplacements = [
            (12, 12, "gelatine"), (27, 25, "gobelin"),
            (41, 32, "loup"), (55, 39, "chevalier"),
            (75, 53, "dragon"),
        ]
        self.ennemis = []
        for x, y, sorte in emplacements:
            if self.case_bloquee(x, y):
                continue
            points = MONSTRES[sorte]["vies"]
            self.ennemis.append({
                "x": x + 0.5,
                "y": y + 0.5,
                "type": sorte,
                "vies": points,
                "vies_max": points,
                "attaque": 0,
                "attaque_charge": 0,
                "boss": MONSTRES[sorte].get("boss", False),
                "rayon_collision": MONSTRES[sorte].get("collision", 0.42),
            })

        self.ajouter_garnisons()
        self.grottes = [
            {"nom": "Grotte des murmures", "x": 23.5, "y": 14.5, "niveau": 1, "etat": None},
            {"nom": "Mine engloutie", "x": 43.5, "y": 38.5, "niveau": 2, "etat": None},
            {"nom": "Sanctuaire du givre", "x": 69.5, "y": 51.5, "niveau": 3, "etat": None},
            {"nom": "Temple des runes", "x": 104.5, "y": 73.5, "niveau": 4, "etat": None},
        ]

        self.objets = [
            {"x": 12.5, "y": 12.5, "type": "coeur"},
            {"x": 48.5, "y": 35.5, "type": "coeur"},
            {"x": 30.5, "y": 8.5, "type": "gemme"},
            {"x": 66.5, "y": 46.5, "type": "gemme"},
            {"x": 8.5, "y": 8.5, "type": "nourriture"},
            {"x": 13.5, "y": 14.5, "type": "nourriture"},
            {"x": 19.5, "y": 17.5, "type": "nourriture"},
            {"x": 25.5, "y": 20.5, "type": "nourriture"},
            {"x": 31.5, "y": 24.5, "type": "nourriture"},
            {"x": 47.5, "y": 34.5, "type": "nourriture"},
            {"x": 56.5, "y": 39.5, "type": "nourriture"},
            {"x": 65.5, "y": 46.5, "type": "nourriture"},
            {"x": 69.5, "y": 48.5, "type": "nourriture"},
            {"x": 5.5, "y": 6.5, "type": "nourriture"},
            {"x": 10.5, "y": 16.5, "type": "nourriture"},
            {"x": 15.5, "y": 11.5, "type": "nourriture"},
            {"x": 18.5, "y": 23.5, "type": "nourriture"},
            {"x": 22.5, "y": 19.5, "type": "nourriture"},
            {"x": 28.5, "y": 28.5, "type": "nourriture"},
            {"x": 37.5, "y": 22.5, "type": "nourriture"},
            {"x": 39.5, "y": 34.5, "type": "nourriture"},
            {"x": 44.5, "y": 31.5, "type": "nourriture"},
            {"x": 51.5, "y": 32.5, "type": "nourriture"},
            {"x": 58.5, "y": 45.5, "type": "nourriture"},
            {"x": 63.5, "y": 39.5, "type": "nourriture"},
        ]
        self.objets.extend(
            {"x": echo["x"], "y": echo["y"], "type": "echo", **echo}
            for echo in ECHOS_HOMMAGES
        )
        # Les tresors ne doivent jamais apparaitre dans un lac ou sous un arbre.
        for objet in self.objets:
            x, y = int(objet["x"]), int(objet["y"])
            self.carte[y][x] = "chemin" if self.carte[y][x] == "eau" else self.carte[y][x]
            self.arbres.discard((x, y))
            self.rochers.discard((x, y))
        self.rations_depart = copy.deepcopy(
            [objet for objet in self.objets if objet["type"] == "nourriture"]
        )

        self.coffres = [copy.deepcopy(coffre) for coffre in COFFRES_MONDE]
        for coffre in self.coffres:
            x, y = int(coffre["x"]), int(coffre["y"])
            self.carte[y][x] = "chemin" if self.carte[y][x] == "eau" else self.carte[y][x]
            self.arbres.discard((x, y))
            self.rochers.discard((x, y))

        for grotte in self.grottes:
            x, y = int(grotte["x"]), int(grotte["y"])
            self.carte[y][x] = "chemin"
            self.arbres.discard((x, y))
            self.rochers.discard((x, y))
        self.ajouter_rencontres_carte()
        self.rencontres_carte_v2 = True
        self.rencontres_carte_v3 = True

    def altitude_at(self, x, y):
        """Hauteur douce des sommets enneiges, en unites de monde."""
        return _calculer_altitude(x, y)

    def creer_ennemi(self, x, y, sorte, niveau=1, base_id=None, chef=False):
        profil = MONSTRES[sorte]
        multiplicateur = 1 + max(0, niveau - 1) * 0.32
        direction_x = self.joueur_x - (x + 0.5)
        direction_y = self.joueur_y - (y + 0.5)
        longueur = math.hypot(direction_x, direction_y) or 1
        return {
            "x": x + 0.5,
            "y": y + 0.5,
            "type": sorte,
            "vies": max(1, round(profil["vies"] * multiplicateur)),
            "vies_max": max(1, round(profil["vies"] * multiplicateur)),
            "degats": profil["degats"] + max(0, niveau - 1) // 2,
            "vitesse": profil["vitesse"] * (1 + max(0, niveau - 1) * 0.06),
            "attaque": 0,
            "niveau": niveau,
            "base_id": base_id,
            "chef": chef,
            "boss": chef or profil.get("boss", False),
            "rayon_collision": profil.get("collision", 0.42),
            "attaque_charge": 0,
            "regard_x": direction_x / longueur,
            "regard_y": direction_y / longueur,
            "alerte_jusqua": 0,
        }

    def ajouter_garnisons(self):
        """Installe un feu de camp entoure de gardes et d'un chef."""
        for index, repaire in enumerate(self.repaire_monstres):
            cx, cy = repaire["x"], repaire["y"]
            repaire["feu"] = (cx + 0.5, cy + 0.5)
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if dx * dx + dy * dy <= 16 and 0 <= x < LARGEUR_CARTE and 0 <= y < HAUTEUR_CARTE:
                        self.carte[y][x] = "chemin" if self.carte[y][x] == "eau" else self.carte[y][x]
                        self.arbres.discard((x, y))
                        self.rochers.discard((x, y))
            positions = ((cx - 2, cy), (cx + 2, cy), (cx, cy - 2), (cx, cy + 2))
            rencontres = repaire["monstres"] + (repaire["chef"],)
            for (x, y), sorte in zip(positions, rencontres):
                ennemi = self.creer_ennemi(x, y, sorte, repaire["niveau"], index, sorte == repaire["chef"])
                direction_x = ennemi["x"] - repaire["feu"][0]
                direction_y = ennemi["y"] - repaire["feu"][1]
                longueur = math.hypot(direction_x, direction_y) or 1
                ennemi["regard_x"] = direction_x / longueur
                ennemi["regard_y"] = direction_y / longueur
                self.ennemis.append(ennemi)

    def ajouter_rencontres_carte(self):
        """Place un petit groupe de rencontres dans chaque grand secteur."""
        hasard = random.Random(20261014)
        choix_biome = {
            "prairie": ("gobelin", "pillard", "araignee", "chauve_souris"),
            "foret": ("araignee", "chauve_souris", "gobelin", "pillard"),
            "desert": ("pillard", "araignee", "chauve_souris", "gelatine"),
            "neige": ("loup", "chauve_souris", "araignee", "pillard"),
        }
        positions_camps = [(camp["x"], camp["y"]) for camp in self.repaire_monstres]
        positions_villages = [(village["x"], village["y"]) for village in VILLAGES]
        positions_grottes = [(grotte["x"], grotte["y"]) for grotte in self.grottes]
        positions_coffres = [(coffre["x"], coffre["y"]) for coffre in self.coffres]
        largeur = len(self.carte[0])
        hauteur = len(self.carte)

        for debut_y in range(4, hauteur, 30):
            for debut_x in range(4, largeur, 32):
                candidats = [
                    (x, y)
                    for y in range(debut_y, min(debut_y + 30, hauteur - 2))
                    for x in range(debut_x, min(debut_x + 32, largeur - 2))
                    if self.carte[y][x] not in ("eau", "grotte")
                    and (x, y) not in self.arbres
                    and (x, y) not in self.rochers
                    and (x, y) not in self.ruines
                ]
                hasard.shuffle(candidats)
                for x, y in candidats:
                    px, py = x + 0.5, y + 0.5
                    if math.hypot(px - self.joueur_x, py - self.joueur_y) < 8:
                        continue
                    if any(math.hypot(px - cx, py - cy) < 7 for cx, cy in positions_camps):
                        continue
                    if any(math.hypot(px - vx, py - vy) < 5.5 for vx, vy in positions_villages):
                        continue
                    if any(math.hypot(px - gx, py - gy) < 4 for gx, gy in positions_grottes):
                        continue
                    if any(math.hypot(px - cx, py - cy) < 2.5 for cx, cy in positions_coffres):
                        continue
                    if any(math.hypot(px - ennemi["x"], py - ennemi["y"]) < 5.5 for ennemi in self.ennemis):
                        continue

                    biome = biome_region(px, py)
                    sorte = hasard.choice(choix_biome[biome])
                    niveau = min(4, max(1, int(math.hypot(px - self.joueur_x, py - self.joueur_y) // 32) + 1))
                    ennemi = self.creer_ennemi(x, y, sorte, niveau)
                    angle = hasard.random() * math.tau
                    ennemi["regard_x"] = math.cos(angle)
                    ennemi["regard_y"] = math.sin(angle)
                    ennemi["rencontre_carte"] = True
                    self.ennemis.append(ennemi)
                    break

    def faire_tomber_arme(self, ennemi):
        """Donne une chance de butin, plus elevee et meilleur pour un ennemi fort."""
        niveau = max(1, ennemi.get("niveau", 1))
        boss = ennemi.get("boss", False)
        niveau_butin = min(4, niveau + int(boss))
        disponibles = [
            identifiant for identifiant, niveau_min in NIVEAU_MIN_ARMES.items()
            if niveau_min <= niveau_butin and identifiant not in self.armes
        ]
        if not disponibles:
            return
        if not boss and random.random() >= 0.22 + min(0.24, (niveau - 1) * 0.08):
            return
        meilleur_niveau = max(NIVEAU_MIN_ARMES[identifiant] for identifiant in disponibles)
        armes_du_palier = [
            identifiant for identifiant in disponibles
            if NIVEAU_MIN_ARMES[identifiant] == meilleur_niveau
        ]
        identifiant = random.choice(armes_du_palier)
        self.objets.append({
            "x": ennemi["x"],
            "y": ennemi["y"],
            "type": "arme",
            "arme": identifiant,
        })

    def entrer_grotte(self, grotte):
        if grotte["etat"] is None:
            largeur, hauteur = 16, 12
            temple = grotte["niveau"] == 4
            rochers = {
                (5, 3), (7, 3), (11, 3), (13, 4), (4, 7), (8, 8), (11, 8), (13, 7),
            }
            niveau_gardien = min(3, grotte["niveau"]) - 1
            ennemis = [] if temple else [
                self.creer_ennemi(6, 4, "araignee", grotte["niveau"]),
                self.creer_ennemi(10, 5, ("ogre", "cyclope", "geant")[niveau_gardien], grotte["niveau"], chef=True),
                self.creer_ennemi(12, 8, ("gobelin", "gelatine", "loup")[niveau_gardien], grotte["niveau"]),
            ]
            coffre = {
                "x": 13.5,
                "y": 9.5,
                "ouvert": False,
                "armes": [("arc_chasseur", "epee_royale", "arc_ancien")[niveau_gardien]],
                "boucliers": [("bouclier_fer", "bouclier_tour", "bouclier_dragon")[niveau_gardien]],
                "fleches": 12 + grotte["niveau"] * 6,
                "gemmes": 3 + grotte["niveau"] * 2,
            }
            if temple:
                rochers = {
                    (12, 6), (12, 7), (12, 8), (12, 9), (12, 10),
                    (13, 6), (14, 6), (13, 7), (13, 9), (13, 10), (14, 10),
                }
                ennemis = [
                    self.creer_ennemi(8, 5, "araignee", grotte["niveau"]),
                    self.creer_ennemi(14, 8, "chevalier", 2, chef=True),
                ]
                coffre.update({"x": 14.3, "y": 9.2, "armes": ["epee_royale"], "boucliers": ["bouclier_dragon"], "gemmes": 12})
                grotte["enigme"] = {
                    "ordre": ("lune", "soleil", "etoile"),
                    "progression": 0,
                    "resolue": False,
                    "dalles": (
                        {"x": 5.5, "y": 5.5, "symbole": "soleil"},
                        {"x": 8.5, "y": 7.5, "symbole": "lune"},
                        {"x": 10.5, "y": 5.5, "symbole": "etoile"},
                    ),
                }
                grotte["pieges"] = ((6, 7), (9, 6), (11, 8))
            grotte["etat"] = {
                "carte": [["grotte" for _ in range(largeur)] for _ in range(hauteur)],
                "arbres": set(),
                "rochers": rochers,
                "ruines": set(),
                "decorations": [],
                "ennemis": ennemis,
                "objets": [
                    {"x": 10.5, "y": 9.5, "type": "gemme"},
                    {"x": 4.5, "y": 9.5, "type": "nourriture"},
                ],
                "coffres": [coffre],
            }
        self.monde_surface = {
            nom: getattr(self, nom)
            for nom in ("carte", "arbres", "rochers", "ruines", "decorations", "ennemis", "objets", "coffres", "villages", "mini_carte")
        }
        self.position_surface = (self.joueur_x, self.joueur_y)
        self.grotte_active = grotte
        self.dans_grotte = True
        for nom in ("carte", "arbres", "rochers", "ruines", "decorations", "ennemis", "objets", "coffres"):
            setattr(self, nom, grotte["etat"][nom])
        self.villages = []
        self.joueur_x, self.joueur_y = 2.5, 2.5
        self.projectiles.clear()
        self.piege_prochain = 0
        self.mini_carte = self.creer_mini_carte()
        if grotte.get("enigme"):
            self.dire("Temple des runes : suis la fresque, LUNE, SOLEIL, ETOILE. E active une dalle.")
        else:
            self.dire(f"Tu entres dans {grotte['nom']}. E te fera ressortir.")

    def sortir_grotte(self):
        etat = self.grotte_active["etat"]
        for nom in ("carte", "arbres", "rochers", "ruines", "decorations", "ennemis", "objets", "coffres"):
            etat[nom] = getattr(self, nom)
        for nom, valeur in self.monde_surface.items():
            setattr(self, nom, valeur)
        self.joueur_x, self.joueur_y = self.position_surface
        self.monde_surface = None
        self.dans_grotte = False
        self.projectiles.clear()
        self.dire("Tu retrouves la lumiere du jour.")

    def case_bloquee(self, x, y):
        """Indique si une case est de l'eau, un arbre, un rocher ou hors de la carte."""
        ix, iy = int(x), int(y)
        largeur, hauteur = len(self.carte[0]), len(self.carte)
        if ix < 0 or iy < 0 or ix >= largeur or iy >= hauteur:
            return True
        if self.dans_grotte and (ix == 0 or iy == 0 or ix == largeur - 1 or iy == hauteur - 1):
            return True
        return (
            self.carte[iy][ix] == "eau"
            or (ix, iy) in self.arbres
            or (ix, iy) in self.rochers
            or (ix, iy) in self.ruines
        )

    def joueur_dissimule(self):
        """Une posture basse dans les hautes herbes masque le joueur."""
        return self.accroupi and any(
            decoration["type"] == "herbe_haute"
            and int(decoration["x"]) == int(self.joueur_x)
            and int(decoration["y"]) == int(self.joueur_y)
            for decoration in self.decorations
        )

    def ennemi_voit_joueur(self, ennemi, dissimule=None):
        """Teste le champ de vision, les obstacles du terrain et les herbes hautes."""
        if dissimule is None:
            dissimule = self.joueur_dissimule()
        if dissimule:
            return False

        dx = self.joueur_x - ennemi["x"]
        dy = self.joueur_y - ennemi["y"]
        distance = math.hypot(dx, dy)
        if distance < 0.01:
            return True
        profil = MONSTRES[ennemi["type"]]
        portee_vue = profil.get("vision", 9.0 if ennemi.get("boss") else 7.0)
        if self.accroupi:
            portee_vue *= 0.55
        if distance > portee_vue:
            return False

        regard_x = ennemi.get("regard_x", 1.0)
        regard_y = ennemi.get("regard_y", 0.0)
        angle_vue = 48 if self.accroupi else 65
        if (dx * regard_x + dy * regard_y) / distance < math.cos(math.radians(angle_vue)):
            return False

        pas = max(2, math.ceil(distance * 4))
        for index in range(1, pas):
            facteur = index / pas
            x = int(ennemi["x"] + dx * facteur)
            y = int(ennemi["y"] + dy * facteur)
            case = (x, y)
            if case in self.arbres or case in self.rochers or case in self.ruines:
                return False
        return True

    def creer_mini_carte(self):
        """Pre-dessine le terrain de la mini-carte, qui ne change pas en jeu."""
        largeur = len(self.carte[0])
        hauteur = len(self.carte)
        facteur = min(2.7, LARGEUR_MINI_CARTE / largeur, HAUTEUR_MINI_CARTE / hauteur)
        self.facteur_mini_carte = facteur
        surface = pygame.Surface((round(largeur * facteur), round(hauteur * facteur)))
        couleurs = {
            "eau": BLEU_EAU,
            "chemin": (151, 119, 76),
            "prairie": VERT_HERBE,
            "foret": (44, 111, 59),
            "desert": (211, 181, 112),
            "neige": (193, 211, 218),
            "grotte": (69, 69, 75),
        }
        for y, ligne in enumerate(self.carte):
            for x, terrain in enumerate(ligne):
                pygame.draw.rect(
                    surface,
                    couleurs[terrain],
                    (
                        round(x * facteur),
                        round(y * facteur),
                        max(1, round((x + 1) * facteur) - round(x * facteur)),
                        max(1, round((y + 1) * facteur) - round(y * facteur)),
                    ),
                )
        return surface

    def peut_bouger(self, x, y):
        """Verifie les quatre coins du personnage pour eviter de traverser les obstacles."""
        rayon = 0.22
        return not any(
            self.case_bloquee(x + dx, y + dy)
            for dx, dy in ((-rayon, -rayon), (rayon, -rayon), (-rayon, rayon), (rayon, rayon))
        )

    def peut_grimper(self, x, y):
        if self.dans_grotte:
            return True
        distance = math.hypot(x - self.joueur_x, y - self.joueur_y)
        return abs(self.altitude_at(x, y) - self.altitude_at(self.joueur_x, self.joueur_y)) <= max(0.08, distance * 0.95)

    def peut_escalader(self, x, y):
        if self.dans_grotte or self.endurance <= 0:
            return False
        distance = math.hypot(x - self.joueur_x, y - self.joueur_y)
        denivele = self.altitude_at(x, y) - self.altitude_at(self.joueur_x, self.joueur_y)
        return denivele > 0 and denivele <= max(0.08, distance * 3.5)

    def _etat_monde(self, monde):
        return {
            nom: monde[nom]
            for nom in (
                "carte", "arbres", "rochers", "ruines", "decorations",
                "ennemis", "objets", "coffres",
            )
        }

    def sauvegarder_partie(self):
        """Enregistre la progression et l'etat des mondes visites."""
        if self.dans_grotte:
            surface = self._etat_monde(self.monde_surface)
            surface["villages"] = self.monde_surface["villages"]
            grottes = copy.deepcopy(self.grottes)
            index_grotte = next(
                index for index, grotte in enumerate(self.grottes)
                if grotte is self.grotte_active
            )
            grottes[index_grotte]["etat"] = self._etat_monde({
                nom: getattr(self, nom)
                for nom in (
                    "carte", "arbres", "rochers", "ruines", "decorations",
                    "ennemis", "objets", "coffres",
                )
            })
        else:
            surface = self._etat_monde({
                nom: getattr(self, nom)
                for nom in (
                    "carte", "arbres", "rochers", "ruines", "decorations",
                    "ennemis", "objets", "coffres",
                )
            })
            surface["villages"] = self.villages
            grottes = copy.deepcopy(self.grottes)

        etat = {
            "joueur_x": self.joueur_x,
            "joueur_y": self.joueur_y,
            "direction": self.direction,
            "camera_yaw": self.camera_yaw,
            "vies": self.vies,
            "score": self.score,
            "nourriture": self.nourriture,
            "faim": self.faim,
            "armes": self.armes,
            "boucliers": self.boucliers,
            "arme_equipee": self.arme_equipee,
            "bouclier_equipe": self.bouclier_equipe,
            "fleches": self.fleches,
            "termine": self.termine,
            "gagne": self.gagne,
            "game_over": self.game_over,
            "quetes": self.quetes,
            "departs_quetes": self.departs_quetes,
            "monstres_grottes_vaincus": self.monstres_grottes_vaincus,
            "dragon_vaincu": self.dragon_vaincu,
            "echos_decouverts": sorted(self.echos_decouverts),
            "repaire_monstres": self.repaire_monstres,
            "grottes": grottes,
            "surface": surface,
            "rencontres_carte_v2": self.rencontres_carte_v2,
            "rencontres_carte_v3": self.rencontres_carte_v3,
            "dans_grotte": self.dans_grotte,
            "grotte_index": index_grotte if self.dans_grotte else None,
            "position_surface": self.position_surface if self.dans_grotte else None,
            "endurance": self.endurance,
        }
        try:
            sauvegarde.sauvegarder(etat, self.chemin_sauvegarde)
        except OSError as erreur:
            self.dire(f"Sauvegarde impossible : {erreur}")
            return
        self.dire("Partie sauvegardee (F5).")

    def charger_partie(self):
        """Recharge une partie valide, y compris si elle etait dans une grotte."""
        camps_configures = copy.deepcopy(self.repaire_monstres)
        grottes_configurees = copy.deepcopy(self.grottes)
        try:
            etat = sauvegarde.charger(self.chemin_sauvegarde)
            champs_requis = (
                "joueur_x", "joueur_y", "direction", "camera_yaw", "vies", "score",
                "nourriture", "faim", "armes", "boucliers", "arme_equipee",
                "bouclier_equipe", "fleches", "termine", "gagne", "game_over",
                "quetes", "departs_quetes", "monstres_grottes_vaincus", "dragon_vaincu",
                "repaire_monstres", "grottes", "surface", "dans_grotte",
                "grotte_index", "position_surface", "endurance",
            )
            if any(champ not in etat for champ in champs_requis):
                raise ValueError("sauvegarde incomplete")
            if not isinstance(etat["surface"], dict) or not isinstance(etat["grottes"], list):
                raise ValueError("donnees de monde invalides")
            echos_decouverts = etat.get("echos_decouverts", [])
            identifiants_echos = {echo["id"] for echo in ECHOS_HOMMAGES}
            if not isinstance(echos_decouverts, list) or any(
                identifiant not in identifiants_echos for identifiant in echos_decouverts
            ):
                raise ValueError("liste des echos decouverts invalide")
            champs_monde = (
                "carte", "arbres", "rochers", "ruines", "decorations",
                "ennemis", "objets", "coffres",
            )
            if any(champ not in etat["surface"] for champ in champs_monde + ("villages",)):
                raise ValueError("monde de surface incomplet")
            objets_surface = etat["surface"]["objets"]
            if not isinstance(objets_surface, list) or any(
                not isinstance(objet, dict) for objet in objets_surface
            ):
                raise ValueError("liste d'objets de surface invalide")
            objets_surface[:] = [
                objet for objet in objets_surface
                if objet.get("id") not in echos_decouverts
            ]
            echos_presents = {
                objet.get("id") for objet in objets_surface
                if objet.get("type") == "echo"
            }
            objets_surface.extend(
                {"x": echo["x"], "y": echo["y"], "type": "echo", **echo}
                for echo in ECHOS_HOMMAGES
                if echo["id"] not in echos_decouverts and echo["id"] not in echos_presents
            )
            for grotte in etat["grottes"]:
                if not isinstance(grotte, dict):
                    raise ValueError("donnees de grotte invalides")
                monde_grotte = grotte.get("etat")
                if monde_grotte is not None and (
                    not isinstance(monde_grotte, dict)
                    or any(champ not in monde_grotte for champ in champs_monde)
                ):
                    raise ValueError("etat de grotte incomplet")
            if not isinstance(etat["dans_grotte"], bool):
                raise ValueError("position sauvegardee invalide")
            if etat["dans_grotte"] and not (
                isinstance(etat["grotte_index"], int)
                and 0 <= etat["grotte_index"] < len(etat["grottes"])
                and etat["grottes"][etat["grotte_index"]].get("etat") is not None
                and isinstance(etat["position_surface"], tuple)
            ):
                raise ValueError("grotte sauvegardee invalide")
        except (OSError, ValueError, TypeError, KeyError) as erreur:
            self.dire(f"Chargement impossible : {erreur}")
            return

        for nom, valeur in etat["surface"].items():
            setattr(self, nom, valeur)
        if not any(decoration.get("type") == "herbe_haute" for decoration in self.decorations):
            nouvelles_herbes = (
                decoration
                for decoration in creer_decorations(self.carte, self.arbres, self.rochers, self.ruines)
                if decoration["type"] == "herbe_haute"
            )
            for decoration in nouvelles_herbes:
                if all(
                    math.hypot(decoration["x"] - existante["x"], decoration["y"] - existante["y"]) >= 0.4
                    for existante in self.decorations
                ):
                    self.decorations.append(decoration)
        coffres_presents = {
            (round(coffre["x"], 2), round(coffre["y"], 2))
            for coffre in self.coffres
        }
        for coffre in COFFRES_MONDE:
            position = round(coffre["x"], 2), round(coffre["y"], 2)
            if position in coffres_presents:
                continue
            self.coffres.append(copy.deepcopy(coffre))
            x, y = int(coffre["x"]), int(coffre["y"])
            self.carte[y][x] = "chemin" if self.carte[y][x] == "eau" else self.carte[y][x]
            self.arbres.discard((x, y))
            self.rochers.discard((x, y))
        grottes_sauvegardees = etat["grottes"]
        noms_grottes = {grotte.get("nom") for grotte in grottes_sauvegardees}
        grottes_sauvegardees.extend(
            grotte for grotte in grottes_configurees
            if grotte["nom"] not in noms_grottes
        )
        self.grottes = grottes_sauvegardees
        self.repaire_monstres = etat["repaire_monstres"]
        for index, repaire in enumerate(self.repaire_monstres):
            if repaire.get("garnison_v2"):
                continue
            modele = camps_configures[index]
            repaire["feu"] = modele["feu"]
            repaire["monstres"] = modele["monstres"]
            repaire["chef"] = modele["chef"]
            if not repaire.get("conquis"):
                for dy in range(-4, 5):
                    for dx in range(-4, 5):
                        x, y = repaire["x"] + dx, repaire["y"] + dy
                        if dx * dx + dy * dy <= 16 and 0 <= x < len(self.carte[0]) and 0 <= y < len(self.carte):
                            self.carte[y][x] = "chemin" if self.carte[y][x] == "eau" else self.carte[y][x]
                            self.arbres.discard((x, y))
                            self.rochers.discard((x, y))
                presents = [
                    ennemi for ennemi in self.ennemis
                    if ennemi.get("base_id") == index
                ]
                positions = ((repaire["x"] - 2, repaire["y"]), (repaire["x"] + 2, repaire["y"]), (repaire["x"], repaire["y"] - 2))
                for slot, sorte in enumerate(repaire["monstres"]):
                    if any(ennemi["type"] == sorte for ennemi in presents):
                        continue
                    x, y = positions[slot]
                    ennemi = self.creer_ennemi(x, y, sorte, repaire["niveau"], index)
                    self.ennemis.append(ennemi)
                    presents.append(ennemi)
                if not repaire.get("boss_vaincu") and not any(ennemi.get("chef") for ennemi in presents):
                    ennemi = self.creer_ennemi(repaire["x"], repaire["y"] + 2, repaire["chef"], repaire["niveau"], index, True)
                    self.ennemis.append(ennemi)
            repaire["garnison_v2"] = True
        if not etat.get("rencontres_carte_v2", False):
            self.ajouter_rencontres_carte()
            self.rencontres_carte_v2 = True
        else:
            self.rencontres_carte_v2 = True
        if not etat.get("rencontres_carte_v3", False):
            self.ennemis = [
                ennemi for ennemi in self.ennemis
                if not ennemi.get("rencontre_carte")
            ]
            self.ajouter_rencontres_carte()
        self.rencontres_carte_v3 = True
        for nom in (
            "joueur_x", "joueur_y", "direction", "camera_yaw", "vies", "score",
            "nourriture", "faim", "armes", "boucliers", "arme_equipee",
            "bouclier_equipe", "fleches", "termine", "gagne", "game_over",
            "quetes", "departs_quetes", "monstres_grottes_vaincus", "dragon_vaincu",
            "endurance",
        ):
            setattr(self, nom, etat[nom])
        self.echos_decouverts = set(etat.get("echos_decouverts", ()))

        self.dans_grotte = etat["dans_grotte"]
        if self.dans_grotte:
            self.position_surface = etat["position_surface"]
            self.monde_surface = {
                nom: getattr(self, nom)
                for nom in (
                    "carte", "arbres", "rochers", "ruines", "decorations",
                    "ennemis", "objets", "coffres", "villages", "mini_carte",
                )
            }
            self.grotte_active = self.grottes[etat["grotte_index"]]
            for nom, valeur in self.grotte_active["etat"].items():
                setattr(self, nom, valeur)
            self.villages = []
        else:
            self.monde_surface = None
            self.grotte_active = None
            self.position_surface = None
        self.mini_carte = self.creer_mini_carte()
        self.projectiles.clear()
        self.cinematique = None
        self.temps_faim = 0
        self.temps_degats_faim = 0
        self.grimpe = False
        self.inventaire_ouvert = False
        self.dire("Partie chargee (F9).")

    def frapper(self, maintenant):
        """Utilise l'arme equipee, au corps a corps ou a distance."""
        arme = ARMES[self.arme_equipee]
        if arme["type"] == "arc":
            self.tirer(maintenant)
            return
        if maintenant < self.attaque_prete:
            return
        self.attaque_prete = maintenant + arme.get(
            "delai",
            620 if self.arme_equipee == "hache_guerre" else 430,
        )
        self.attaque_jusqua = maintenant + 220
        self.attaque_affichage_debut = maintenant
        self.attaque_affichage_jusqua = maintenant + 420
        self.attaque_touche = False

    def esquiver(self, maintenant):
        """Effectue une esquive courte, avec un bref instant d'invulnerabilite."""
        if maintenant < self.esquive_prete or self.endurance < 24:
            return
        if math.hypot(*self.direction) < 0.01:
            self.direction = (math.cos(self.camera_yaw), math.sin(self.camera_yaw))
        self.endurance -= 24
        self.esquive_jusqua = maintenant + 180
        self.esquive_prete = maintenant + 850
        self.invulnerable_jusqua = max(self.invulnerable_jusqua, maintenant + 280)
        self.dire("Esquive !")

    def attaque_speciale(self, maintenant):
        """Lance une attaque puissante au corps a corps ou une fleche chargee."""
        cout = 30
        if maintenant < self.special_prete:
            return
        if ARMES[self.arme_equipee]["type"] == "arc" and self.fleches <= 0:
            self.dire("Tu n'as plus de fleches.")
            return
        if self.endurance < cout:
            self.dire("Pas assez d'endurance pour l'attaque speciale.")
            return
        self.endurance -= cout
        self.special_prete = maintenant + 1100
        profil_arme = ARMES[self.arme_equipee]
        if profil_arme["type"] == "arc":
            self.fleches -= 1
            dx, dy = self.direction
            self.projectiles.append({
                "x": self.joueur_x, "y": self.joueur_y,
                "dx": dx, "dy": dy,
                "vitesse": profil_arme.get("vitesse_projectile", 14.0),
                "degats": profil_arme["degats"] * 2,
                "distance": 0.0,
            })
            self.special_jusqua = maintenant + 220
            self.special_debut = maintenant
            self.tir_pret = max(
                self.tir_pret,
                maintenant + profil_arme.get("delai_tir", 450),
            )
            self.dire("Fleche chargee !")
            return
        self.special_jusqua = maintenant + 520
        self.special_debut = maintenant
        self.attaque_jusqua = self.special_jusqua
        self.attaque_affichage_debut = maintenant
        self.attaque_affichage_jusqua = maintenant + 520
        self.attaque_touche = False

    def actualiser_monde(self, dt):
        self.temps_monde += dt
        saisons = ("Printemps", "Ete", "Automne", "Hiver")
        self.saison = saisons[int(self.temps_monde // 90) % len(saisons)]
        meteo_cycle = ("clair", "vent", "pluie", "clair", "orage", "vent", "neige", "clair")
        meteo = meteo_cycle[int(self.temps_monde // 30) % len(meteo_cycle)]
        if meteo == "neige" and self.saison != "Hiver" and biome_region(self.joueur_x, self.joueur_y) != "neige":
            meteo = "pluie"
        self.meteo = meteo
        if meteo != self._meteo_precedente:
            self._meteo_precedente = meteo
            descriptions = {
                "vent": "Le vent se leve.",
                "pluie": "La pluie commence a tomber.",
                "orage": "Un orage eclate au-dessus de Valombre.",
                "neige": "La neige recouvre les sentiers.",
                "clair": "Le ciel s'eclaircit.",
            }
            if not self.dans_grotte:
                self.dire(descriptions[meteo])

    def tirer(self, maintenant):
        """Tire une fleche dans la derniere direction regardee."""
        if maintenant < self.tir_pret:
            return
        if self.fleches <= 0:
            self.dire("Tu n'as plus de fleches. Cherche un coffre.")
            return
        self.fleches -= 1
        profil_arme = ARMES[self.arme_equipee]
        self.tir_pret = maintenant + profil_arme.get("delai_tir", 520)
        dx, dy = self.direction
        self.projectiles.append({
            "x": self.joueur_x,
            "y": self.joueur_y,
            "dx": dx,
            "dy": dy,
            "vitesse": profil_arme.get("vitesse_projectile", 11.0),
            "degats": ARMES[self.arme_equipee]["degats"],
            "distance": 0.0,
        })
        self.attaque_jusqua = maintenant + 140

    def blesser_ennemi(self, ennemi, degats):
        ennemi["vies"] -= degats
        if ennemi["vies"] <= 0:
            self.ennemis.remove(ennemi)
            self.score += 1
            self.progresser_quetes("monstres")
            self.faire_tomber_arme(ennemi)
            if self.dans_grotte:
                self.monstres_grottes_vaincus += 1
                self.progresser_quetes("grotte")
            base_id = ennemi.get("base_id")
            if base_id is not None and ennemi.get("boss"):
                repaire = self.repaire_monstres[base_id]
                if not repaire.get("boss_vaincu", False):
                    repaire["boss_vaincu"] = True
                    self.progresser_quetes("repaire")
                    self.dire(f"Chef vaincu : {repaire['nom']} !")
            if base_id is not None and not any(monstre.get("base_id") == base_id for monstre in self.ennemis):
                repaire = self.repaire_monstres[base_id]
                if repaire["boss_vaincu"] and not repaire["conquis"]:
                    repaire["conquis"] = True
                    self.dire(f"Boss vaincu ! {repaire['nom']} est libere.")
            if ennemi["type"] == "dragon":
                self.dragon_vaincu = True
                self.progresser_quetes("dragon")
                self.dire("Le dragon a trois tetes s'effondre. Les cimes sont libres !")

    def ouvrir_coffre(self, coffre):
        if coffre["ouvert"]:
            self.dire("Ce coffre est deja vide.")
            return
        coffre["ouvert"] = True
        nouvelles_armes = [arme for arme in coffre["armes"] if arme not in self.armes]
        nouveaux_boucliers = [bouclier for bouclier in coffre["boucliers"] if bouclier not in self.boucliers]
        self.armes.extend(nouvelles_armes)
        self.boucliers.extend(nouveaux_boucliers)
        self.fleches += coffre["fleches"]
        self.score += coffre["gemmes"]
        tresors = [ARMES[item]["nom"] for item in nouvelles_armes]
        tresors.extend(BOUCLIERS[item]["nom"] for item in nouveaux_boucliers)
        tresors.extend((f"{coffre['fleches']} fleches", f"{coffre['gemmes']} gemmes"))
        self.dire("Coffre ouvert : " + ", ".join(tresors) + ".")

    def demarrer_cinematique(self, village, habitant, quete, maintenant):
        """Joue une courte scene de remerciement au retour de chaque quete."""
        recits = {
            "nourriture": (
                "Les greniers sont de nouveau pleins. Les familles de Clairval "
                "pourront passer l'hiver sans manquer de pain.",
                "Tu as rendu l'espoir a nos champs. Le village entier te remercie.",
            ),
            "repaire": (
                "Les sentiers sont libres et les bannieres des pillards sont tombees. "
                "Les voyageurs peuvent enfin reprendre la route.",
                "Les routes sont a nous de nouveau. Ta bravoure restera dans nos chansons.",
            ),
            "grotte": (
                "Les profondeurs se sont apaisees. Les mineurs peuvent rallumer leurs "
                "lanternes et rentrer chez eux.",
                "Meme les cavernes semblent moins sombres. Tu as sauve bien des vies.",
            ),
            "dragon": (
                "Le dragon ne menace plus les sommets. Au loin, les cloches des villages "
                "sonnent pour celebrer ta victoire.",
                "Valombre n'oubliera jamais le courage qui a libere nos montagnes.",
            ),
        }
        histoire, remerciement = recits[quete["type"]]
        self.cinematique = {
            "village": village["nom"],
            "habitant": habitant,
            "quete": quete["nom"],
            "recompense": quete["recompense"],
            "pages": (
                {"titre": "UNE QUETE ACCOMPLIE", "personnage": "Chronique de Valombre", "texte": histoire},
                {"titre": village["nom"], "personnage": f"{habitant['nom']} - {habitant['metier']}", "texte": remerciement},
                {
                    "titre": "LE SERMENT DU HEROS",
                    "personnage": "Un eclat d'acier dans la terre",
                    "texte": "Le heros brandit son epee, bondit et la plante dans le sol. Valombre se souviendra de son courage.",
                    "action": "epee_plantee",
                    "duree": 5200,
                },
                {
                    "titre": "UNE NOUVELLE LEGENDE",
                    "personnage": "Recompense",
                    "texte": f"{quete['recompense']} gemmes et une ration rejoignent ton sac. Le peuple de {village['nom']} te salue.",
                },
            ),
        }
        self.cinematique_index = 0
        self.cinematique_page_debut = maintenant
        self.cinematique_suivante = maintenant + self.cinematique["pages"][0].get("duree", 6200)

    def avancer_cinematique(self, maintenant):
        if self.cinematique is None:
            return
        if self.cinematique_index + 1 < len(self.cinematique["pages"]):
            self.cinematique_index += 1
            self.cinematique_page_debut = maintenant
            page = self.cinematique["pages"][self.cinematique_index]
            self.cinematique_suivante = maintenant + page.get("duree", 6200)
        else:
            village = self.cinematique["village"]
            self.cinematique = None
            self.dire(f"{village} te souhaite bonne route !")

    def interagir(self):
        """Ouvre un coffre, parle aux villageois ou recupere la relique."""
        if self.dans_grotte:
            enigme = self.grotte_active.get("enigme") if self.grotte_active else None
            if enigme and not enigme["resolue"]:
                dalle = next(
                    (
                        dalle for dalle in enigme["dalles"]
                        if math.hypot(self.joueur_x - dalle["x"], self.joueur_y - dalle["y"]) < 1.25
                    ),
                    None,
                )
                if dalle:
                    attendu = enigme["ordre"][enigme["progression"]]
                    if dalle["symbole"] != attendu:
                        enigme["progression"] = 0
                        self.dire("La rune s'eteint. Recommence : lune, soleil, etoile.")
                    else:
                        enigme["progression"] += 1
                        if enigme["progression"] == len(enigme["ordre"]):
                            enigme["resolue"] = True
                            self.rochers.discard((12, 8))
                            self.dire("Les runes s'illuminent ! Le sceau du chevalier est brise.")
                        else:
                            self.dire("La rune s'allume. La fresque indique : lune, soleil, etoile.")
                    return
            for coffre in self.coffres:
                if math.hypot(self.joueur_x - coffre["x"], self.joueur_y - coffre["y"]) < 1.7:
                    self.ouvrir_coffre(coffre)
                    return
            if math.hypot(self.joueur_x - 2.5, self.joueur_y - 2.5) < 1.5:
                self.sortir_grotte()
            else:
                self.dire("Explore la grotte et reviens a l'entree pour ressortir.")
            return

        for grotte in self.grottes:
            if math.hypot(self.joueur_x - grotte["x"], self.joueur_y - grotte["y"]) < 1.8:
                self.entrer_grotte(grotte)
                return

        for coffre in self.coffres:
            if math.hypot(self.joueur_x - coffre["x"], self.joueur_y - coffre["y"]) < 1.7:
                self.ouvrir_coffre(coffre)
                return

        for index, village in enumerate(self.villages):
            distance = math.hypot(self.joueur_x - village["x"], self.joueur_y - village["y"])
            if distance >= 2.0:
                continue
            quete = self.quetes[index]
            if quete["faite"]:
                self.dire(f"{village['nom']} te remercie encore !")
            elif not quete["active"]:
                if any(q["active"] for q in self.quetes):
                    self.dire("Termine d'abord ta quete en cours avant d'en accepter une autre.")
                else:
                    progres_historique = {
                        "repaire": sum(
                            repaire.get("boss_vaincu", False) or repaire.get("conquis", False)
                            for repaire in self.repaire_monstres
                        ),
                        "grotte": self.monstres_grottes_vaincus,
                        "dragon": int(self.dragon_vaincu),
                    }
                    quete["progres"] = min(quete["besoin"], progres_historique.get(quete["type"], 0))
                    quete["active"] = True
                    self.capturer_depart_quete(index)
                    self.dire(f"Indice : {INDICES_ECHOS_VILLAGES[index]}")
            elif quete["progres"] >= quete["besoin"]:
                quete["active"] = False
                quete["faite"] = True
                self.score += quete["recompense"]
                self.nourriture += 1
                self.demarrer_cinematique(village, village["habitants"][0], quete, pygame.time.get_ticks())
            else:
                self.dire(f"{quete['nom']} : {quete['progres']}/{quete['besoin']}")
            return

        if math.hypot(self.joueur_x - RELIQUE_X, self.joueur_y - RELIQUE_Y) < 1.5:
            self.termine = True
            self.gagne = True
            return
        self.dire("Rien a proximite. Approche-toi d'un village ou de la relique.")

    def dire(self, texte):
        """Affiche un message temporaire en bas de l'ecran."""
        self.message = texte
        self.message_jusqua = pygame.time.get_ticks() + 4500

    def elements_inventaire(self):
        return (
            [("arme", identifiant) for identifiant in self.armes]
            + [("bouclier", identifiant) for identifiant in self.boucliers]
        )

    def choisir_inventaire(self):
        elements = self.elements_inventaire()
        if not elements:
            return
        genre, identifiant = elements[self.inventaire_index]
        if genre == "arme":
            self.arme_equipee = identifiant
            nom = ARMES[identifiant]["nom"]
        else:
            self.bouclier_equipe = identifiant
            nom = BOUCLIERS[identifiant]["nom"]
        self.dire(f"{nom} equipe.")

    def manger(self, maintenant):
        """Consomme une ration pour calmer la faim et recuperer une vie."""
        if self.nourriture <= 0:
            self.dire("Tu n'as plus de nourriture ! Cherche des rations dans les royaumes.")
            return
        if self.faim >= 100 and self.vies >= 5:
            self.dire("Tu n'as pas besoin de manger pour le moment.")
            return
        self.nourriture -= 1
        self.faim = min(100, self.faim + 45)
        self.vies = min(5, self.vies + 1)
        self.invulnerable_jusqua = max(self.invulnerable_jusqua, maintenant + 300)
        self.dire("Miam ! Tu recuperes une vie et 45 points de faim.")

    def progresser_quetes(self, genre, nombre=1):
        """Fait avancer toutes les quetes actives correspondant a l'action."""
        for quete in self.quetes:
            if quete["active"] and quete["type"] == genre:
                quete["progres"] = min(quete["besoin"], quete["progres"] + nombre)

    def capturer_depart_quete(self, index):
        """Garde les elements necessaires pour recommencer la quete active."""
        quete = self.quetes[index]
        depart = {
            "index": index,
            "position": (self.villages[index]["x"], self.villages[index]["y"]),
            "direction": self.direction,
            "camera_yaw": self.camera_yaw,
            "type": quete["type"],
        }
        if quete["type"] == "nourriture":
            depart["rations"] = copy.deepcopy(self.rations_depart)
        elif quete["type"] == "grotte":
            depart["grottes"] = copy.deepcopy(self.grottes)
        elif quete["type"] == "repaire":
            depart["repaire_monstres"] = copy.deepcopy(self.repaire_monstres)
            depart["ennemis_repaire"] = copy.deepcopy(
                [ennemi for ennemi in self.ennemis if ennemi.get("base_id") is not None]
            )
        elif quete["type"] == "dragon":
            dragon = next(
                (ennemi for ennemi in self.ennemis if ennemi["type"] == "dragon"),
                None,
            )
            depart["dragon"] = copy.deepcopy(dragon) if dragon else self.creer_ennemi(75, 53, "dragon")
        self.departs_quetes[index] = depart

    def declencher_game_over(self):
        """Met la partie en pause sur l'ecran de defaite."""
        self.vies = 0
        self.termine = True
        self.gagne = False
        self.game_over = True
        self.inventaire_ouvert = False
        self.attaque_jusqua = 0
        self.attaque_touche = False
        self.attaque_affichage_jusqua = 0
        self.esquive_jusqua = 0
        self.projectiles.clear()
        self.dire("GAME OVER")

    def reprendre_apres_mort(self):
        """Rend ses forces au heros sans deplacer le joueur ni changer le monde."""
        self.vies = 5
        self.faim = 45
        self.temps_faim = 0
        self.temps_degats_faim = 0
        self.invulnerable_jusqua = pygame.time.get_ticks() + 1800
        self.termine = False
        self.gagne = False
        self.game_over = False
        self.dire("Tu reprends ton souffle et te releves au meme endroit.")

    def degats_apres_bouclier(self, degats):
        """Soustrait la defense equipee, jusqu'a bloquer entierement le coup."""
        defense = BOUCLIERS.get(self.bouclier_equipe, {}).get("defense", 0)
        return max(0, degats - defense)

    def recommencer_quete(self):
        """Recommence la quete active depuis son village et restaure ses objectifs."""
        index = next(
            (index for index, quete in enumerate(self.quetes) if quete["active"]),
            None,
        )
        depart = self.departs_quetes.get(index) if index is not None else None
        if self.dans_grotte:
            self.sortir_grotte()

        if depart:
            genre = depart["type"]
            if genre == "nourriture":
                self.objets = [
                    objet for objet in self.objets if objet["type"] != "nourriture"
                ] + copy.deepcopy(depart["rations"])
            elif genre == "grotte":
                self.grottes = copy.deepcopy(depart["grottes"])
                self.monstres_grottes_vaincus = 0
            elif genre == "repaire":
                self.repaire_monstres = copy.deepcopy(depart["repaire_monstres"])
                self.ennemis = [
                    ennemi for ennemi in self.ennemis if ennemi.get("base_id") is None
                ] + copy.deepcopy(depart["ennemis_repaire"])
            elif genre == "dragon":
                self.dragon_vaincu = False
                self.ennemis = [
                    ennemi for ennemi in self.ennemis if ennemi["type"] != "dragon"
                ]
                self.ennemis.append(copy.deepcopy(depart["dragon"]))

            quete = self.quetes[depart["index"]]
            quete["progres"] = 0
            quete["active"] = True
            self.joueur_x, self.joueur_y = depart["position"]
            self.direction = depart["direction"]
            self.camera_yaw = depart["camera_yaw"]
            texte = f"Quete recommencee : {quete['nom']}."
        else:
            self.joueur_x, self.joueur_y = 3.5, 3.5
            texte = "Tu reprends l'aventure au debut."

        self.vies = 5
        self.faim = 100
        self.temps_faim = 0
        self.temps_degats_faim = 0
        self.invulnerable_jusqua = pygame.time.get_ticks() + 1200
        self.attaque_jusqua = 0
        self.attaque_prete = 0
        self.attaque_touche = False
        self.attaque_affichage_jusqua = 0
        self.projectiles.clear()
        self.termine = False
        self.gagne = False
        self.game_over = False
        self.inventaire_ouvert = False
        self.dire(texte)

    def mettre_a_jour(self, dt, maintenant, touches):
        """Met a jour les commandes, la faim, les combats, les ennemis et les objets."""
        if self.cinematique is not None:
            self.en_marche = False
            if maintenant >= self.cinematique_suivante:
                self.avancer_cinematique(maintenant)
            return
        if self.termine or self.inventaire_ouvert:
            return

        self.accroupi = (
            not self.dans_grotte
            and (touches[pygame.K_LCTRL] or touches[pygame.K_RCTRL])
        )
        self.actualiser_monde(dt)
        avant = int(touches[pygame.K_UP] or touches[pygame.K_z] or touches[pygame.K_w]) - int(touches[pygame.K_DOWN] or touches[pygame.K_s])
        cote = int(touches[pygame.K_RIGHT] or touches[pygame.K_d]) - int(touches[pygame.K_LEFT] or touches[pygame.K_q] or touches[pygame.K_a])
        self.en_marche = bool(avant or cote)
        if avant or cote:
            longueur = math.hypot(avant, cote)
            avant, cote = avant / longueur, cote / longueur
            avant_x, avant_y = math.cos(self.camera_yaw), math.sin(self.camera_yaw)
            cote_x, cote_y = -avant_y, avant_x
            dx = avant_x * avant + cote_x * cote
            dy = avant_y * avant + cote_y * cote
            self.direction = (dx, dy)
        else:
            dx = dy = 0

        vitesse = (2.1 if touches[pygame.K_LSHIFT] or touches[pygame.K_RSHIFT] else 4.0) * dt
        if self.accroupi:
            vitesse *= 0.52
        if self.esquive_jusqua > maintenant:
            vitesse = 10.0 * dt
            if not (avant or cote):
                dx, dy = self.direction
            self.en_marche = True
        if dx or dy:
            self.temps_marche += dt
        escalade_demandee = touches[pygame.K_LSHIFT] or touches[pygame.K_RSHIFT]
        endurance_utilisee = False
        cible_x = self.joueur_x + dx * vitesse
        if dx and self.peut_bouger(cible_x, self.joueur_y):
            if escalade_demandee and self.peut_escalader(cible_x, self.joueur_y):
                self.joueur_x = cible_x
                endurance_utilisee = True
            elif self.peut_grimper(cible_x, self.joueur_y):
                self.joueur_x = cible_x
        cible_y = self.joueur_y + dy * vitesse
        if dy and self.peut_bouger(self.joueur_x, cible_y):
            if escalade_demandee and self.peut_escalader(self.joueur_x, cible_y):
                self.joueur_y = cible_y
                endurance_utilisee = True
            elif self.peut_grimper(self.joueur_x, cible_y):
                self.joueur_y = cible_y
        self.grimpe = endurance_utilisee
        if endurance_utilisee:
            self.endurance = max(0.0, self.endurance - 24 * dt)
        else:
            self.endurance = min(100.0, self.endurance + 16 * dt)

        # La faim baisse avec le temps ; une faim nulle fait perdre des vies.
        self.temps_faim += dt
        if self.temps_faim >= 2:
            baisse = int(self.temps_faim // 2)
            self.faim = max(0, self.faim - baisse)
            self.temps_faim %= 2
        if self.faim == 0:
            self.temps_degats_faim += dt
            if self.temps_degats_faim >= 8:
                self.temps_degats_faim = 0
                self.vies -= 1
                self.invulnerable_jusqua = maintenant + 800
                self.dire("Tu as faim ! Mange avec F ou trouve de la nourriture.")
                if self.vies <= 0:
                    self.declencher_game_over()
                    return
        else:
            self.temps_degats_faim = 0

        # Un coup ne touche qu'une fois et seulement les monstres situes devant le heros.
        if (
            ARMES[self.arme_equipee]["type"] == "corps"
            and maintenant < self.attaque_jusqua
            and not self.attaque_touche
        ):
            fx, fy = self.direction
            for ennemi in self.ennemis[:]:
                ex = ennemi["x"] - self.joueur_x
                ey = ennemi["y"] - self.joueur_y
                distance = math.hypot(ex, ey)
                devant = ex * fx + ey * fy
                portee = ARMES[self.arme_equipee].get("portee", 1.9) + ennemi.get("rayon_collision", 0.0)
                speciale = self.special_jusqua > maintenant
                portee *= 1.45 if speciale else 1.0
                if distance < portee and devant > (-0.35 if speciale else -0.1):
                    degats = ARMES[self.arme_equipee]["degats"] * (2 if speciale else 1)
                    self.blesser_ennemi(ennemi, degats)
                    self.attaque_touche = True
                    break

        for projectile in self.projectiles[:]:
            pas = min(projectile["vitesse"] * dt, 16 - projectile["distance"])
            projectile["x"] += projectile["dx"] * pas
            projectile["y"] += projectile["dy"] * pas
            projectile["distance"] += pas
            touche = next(
                (
                    ennemi for ennemi in self.ennemis
                    if math.hypot(ennemi["x"] - projectile["x"], ennemi["y"] - projectile["y"])
                    < ennemi.get("rayon_collision", 0.42) + 0.2
                ),
                None,
            )
            if touche:
                self.blesser_ennemi(touche, projectile["degats"])
                self.projectiles.remove(projectile)
            elif projectile["distance"] >= 16 or self.case_bloquee(projectile["x"], projectile["y"]):
                self.projectiles.remove(projectile)

        # Les villages restent des refuges : leurs habitants ne sont pas attaques.
        dans_un_village = not self.dans_grotte and any(
            math.hypot(self.joueur_x - village["x"], self.joueur_y - village["y"]) < 2.5
            for village in self.villages
        )
        dissimule = self.joueur_dissimule()

        # Les ennemis n'agissent que s'ils voient le joueur sans obstacle.
        for ennemi in self.ennemis:
            if dans_un_village:
                continue
            profil = MONSTRES[ennemi["type"]]
            vitesse_ennemi = ennemi.get("vitesse", profil["vitesse"])
            degats_ennemi = ennemi.get("degats", profil["degats"])
            ex = self.joueur_x - ennemi["x"]
            ey = self.joueur_y - ennemi["y"]
            distance = math.hypot(ex, ey)
            joueur_visible = self.ennemi_voit_joueur(ennemi, dissimule)
            if not joueur_visible:
                ennemi["voit_joueur"] = False
                ennemi["attaque_charge"] = 0
                continue
            if not ennemi.get("voit_joueur", False):
                ennemi["alerte_jusqua"] = maintenant + 1400
            ennemi["voit_joueur"] = True
            ennemi["regard_x"] = ex / distance if distance else ennemi.get("regard_x", 1.0)
            ennemi["regard_y"] = ey / distance if distance else ennemi.get("regard_y", 0.0)
            attaque_chargee = ennemi.get("attaque_charge", 0) > maintenant
            if 0.72 < distance < 8 and not attaque_chargee:
                pas = min(vitesse_ennemi * dt, distance)
                nx = ennemi["x"] + ex / distance * pas
                ny = ennemi["y"] + ey / distance * pas
                if self.peut_bouger(nx, ennemi["y"]):
                    ennemi["x"] = nx
                if self.peut_bouger(ennemi["x"], ny):
                    ennemi["y"] = ny
            if ennemi.get("boss"):
                if ennemi.get("attaque_charge", 0) and maintenant >= ennemi["attaque_charge"]:
                    cible_x, cible_y = ennemi.get("cible_charge", (self.joueur_x, self.joueur_y))
                    rayon_attaque = profil.get("portee", 1.5)
                    if math.hypot(self.joueur_x - cible_x, self.joueur_y - cible_y) < rayon_attaque:
                        if maintenant >= self.invulnerable_jusqua:
                            self.vies -= self.degats_apres_bouclier(degats_ennemi)
                            self.invulnerable_jusqua = maintenant + 1100
                            self.dire(f"{profil['nom']} frappe le sol !")
                            if self.vies <= 0:
                                self.declencher_game_over()
                                return
                    ennemi["attaque_charge"] = 0
                elif distance < profil.get("portee", 1.5) and maintenant >= ennemi["attaque"]:
                    ennemi["attaque"] = maintenant + 2100
                    ennemi["attaque_charge"] = maintenant + 650
                    ennemi["cible_charge"] = (self.joueur_x, self.joueur_y)
            elif ennemi["type"] == "loup":
                if ennemi.get("attaque_charge", 0) and maintenant >= ennemi["attaque_charge"]:
                    cible_x, cible_y = ennemi.get("cible_charge", (self.joueur_x, self.joueur_y))
                    if math.hypot(self.joueur_x - cible_x, self.joueur_y - cible_y) < 0.95:
                        if maintenant >= self.invulnerable_jusqua:
                            self.vies -= self.degats_apres_bouclier(degats_ennemi)
                            self.invulnerable_jusqua = maintenant + 1100
                            self.dire("Le loup bondit sur toi !")
                            if self.vies <= 0:
                                self.declencher_game_over()
                                return
                    ennemi["attaque_charge"] = 0
                elif distance < 3.0 and maintenant >= ennemi["attaque"]:
                    ennemi["attaque"] = maintenant + 1750
                    ennemi["attaque_charge"] = maintenant + 480
                    ennemi["cible_charge"] = (self.joueur_x, self.joueur_y)
            elif distance < 0.8 and maintenant >= ennemi["attaque"]:
                ennemi["attaque"] = maintenant + 950
                if maintenant >= self.invulnerable_jusqua:
                    self.vies -= self.degats_apres_bouclier(degats_ennemi)
                    self.invulnerable_jusqua = maintenant + 1100
                    if self.vies <= 0:
                        self.declencher_game_over()
                        return

        pieges = self.grotte_active.get("pieges", ()) if self.dans_grotte and self.grotte_active else ()
        if (
            pieges
            and (int(self.joueur_x), int(self.joueur_y)) in pieges
            and maintenant % 1800 < 900
            and maintenant >= self.piege_prochain
            and maintenant >= self.invulnerable_jusqua
        ):
            self.vies -= 1
            self.invulnerable_jusqua = maintenant + 700
            self.piege_prochain = maintenant + 900
            self.dire("Les pics du temple te blessent ! Attends leur retractation pour passer.")
            if self.vies <= 0:
                self.declencher_game_over()
                return

        # Les coeurs rendent une vie ; les gemmes augmentent le score.
        for objet in self.objets[:]:
            if math.hypot(objet["x"] - self.joueur_x, objet["y"] - self.joueur_y) < 0.65:
                self.objets.remove(objet)
                if objet["type"] == "coeur":
                    self.vies = min(5, self.vies + 1)
                elif objet["type"] == "nourriture":
                    self.nourriture += 1
                    self.progresser_quetes("nourriture")
                    self.dire("Tu as trouve une ration de nourriture.")
                elif objet["type"] == "arme":
                    identifiant = objet["arme"]
                    if identifiant not in self.armes:
                        self.armes.append(identifiant)
                        self.dire(f"Arme trouvee : {ARMES[identifiant]['nom']} !")
                elif objet["type"] == "echo":
                    self.echos_decouverts.add(objet["id"])
                    self.score += 3
                    nombre_echos = len(self.echos_decouverts)
                    if nombre_echos == len(ECHOS_HOMMAGES):
                        self.score += 12
                        self.dire(
                            f"Tous les {len(ECHOS_HOMMAGES)} echos sont reunis ! "
                            "Tu gagnes 12 points bonus."
                        )
                    else:
                        self.dire(
                            f"{objet['oeuvre']} : {objet['nom']} "
                            f"({nombre_echos}/{len(ECHOS_HOMMAGES)})."
                        )
                else:
                    self.score += 3

    def dessiner_case(self, x, y, camera_x, camera_y):
        """Dessine une case en losange et sa couleur selon le terrain."""
        centre_x, centre_y = projeter(x + 0.5, y + 0.5, camera_x, camera_y)
        if (
            centre_x < -LARGEUR_CASE
            or centre_x > LARGEUR_FENETRE + LARGEUR_CASE
            or centre_y < -HAUTEUR_CASE
            or centre_y > HAUTEUR_FENETRE + HAUTEUR_CASE
        ):
            return
        losange = [
            (centre_x, centre_y - HAUTEUR_CASE // 2),
            (centre_x + LARGEUR_CASE // 2, centre_y),
            (centre_x, centre_y + HAUTEUR_CASE // 2),
            (centre_x - LARGEUR_CASE // 2, centre_y),
        ]
        terrain = self.carte[y][x]
        couleurs = {
            "eau": BLEU_EAU,
            "chemin": (151, 119, 76),
            "prairie": VERT_CLAIR if (x * 7 + y * 3) % 5 == 0 else VERT_HERBE,
            "foret": (44, 111, 59) if (x + y) % 4 else (55, 128, 63),
            "desert": (211, 181, 112) if (x + y) % 4 else (224, 197, 131),
            "neige": (193, 211, 218) if (x + y) % 4 else (222, 232, 235),
        }
        couleur = couleurs[terrain]
        pygame.draw.polygon(self.ecran, couleur, losange)
        bord = (35, 92, 53) if terrain in ("prairie", "foret") else (123, 105, 77) if terrain == "chemin" else (90, 127, 150) if terrain == "eau" else (155, 135, 100)
        pygame.draw.polygon(self.ecran, bord, losange, 1)

        # Petites marques deterministes pour donner une texture sans clignotement.
        motif = (x * 37 + y * 19) % 11
        if terrain == "eau":
            if motif < 3:
                pygame.draw.line(self.ecran, (106, 190, 215), (centre_x - 8, centre_y), (centre_x + 5, centre_y - 2), 2)
        elif terrain == "desert" and motif < 4:
            pygame.draw.ellipse(self.ecran, (190, 157, 94), (centre_x - 12, centre_y + 1, 8, 3))
        elif terrain == "neige" and motif < 3:
            pygame.draw.circle(self.ecran, (246, 249, 242), (centre_x + 8, centre_y - 2), 2)
        elif terrain == "prairie" and motif == 0:
            pygame.draw.circle(self.ecran, (244, 215, 118), (centre_x + 7, centre_y - 1), 2)
        elif terrain == "chemin" and motif < 2:
            pygame.draw.ellipse(self.ecran, (181, 151, 108), (centre_x - 7, centre_y - 2, 7, 3))

    def dessiner_villageois(self, village, camera_x, camera_y):
        """Dessine une maison detaillee et un habitant avec visage et vetements."""
        sx, sy = projeter(village["x"], village["y"], camera_x, camera_y)
        couleur = village["couleur"]
        # Maison : ombre au sol, murs avec poutres, fenetre, porte et toit.
        pygame.draw.ellipse(self.ecran, (47, 71, 46), (sx - 32, sy + 4, 64, 18))
        pygame.draw.rect(self.ecran, (190, 157, 111), (sx - 23, sy - 35, 46, 39), border_radius=3)
        pygame.draw.polygon(self.ecran, (83, 60, 45), [(sx - 30, sy - 33), (sx, sy - 59), (sx + 30, sy - 33)])
        pygame.draw.polygon(self.ecran, couleur, [(sx - 25, sy - 34), (sx, sy - 55), (sx + 25, sy - 34)])
        pygame.draw.line(self.ecran, (235, 204, 151), (sx - 17, sy - 28), (sx - 17, sy - 3), 3)
        pygame.draw.line(self.ecran, (235, 204, 151), (sx + 17, sy - 28), (sx + 17, sy - 3), 3)
        pygame.draw.rect(self.ecran, (86, 61, 43), (sx - 6, sy - 19, 13, 23), border_radius=3)
        pygame.draw.circle(self.ecran, (225, 187, 97), (sx + 3, sy - 8), 1)
        pygame.draw.rect(self.ecran, (113, 177, 205), (sx - 20, sy - 27, 9, 9), border_radius=2)
        pygame.draw.line(self.ecran, (235, 225, 194), (sx - 16, sy - 27), (sx - 16, sy - 18), 1)
        pygame.draw.line(self.ecran, (235, 225, 194), (sx - 20, sy - 22), (sx - 11, sy - 22), 1)

        # Le villageois se tient a cote de la porte, plutot que devant la maison.
        nx, ny = projeter(village["x"] + 0.85, village["y"] + 0.25, camera_x, camera_y)
        pygame.draw.ellipse(self.ecran, (48, 66, 48), (nx - 10, ny - 2, 20, 8))
        pygame.draw.line(self.ecran, (67, 47, 39), (nx - 4, ny - 9), (nx - 5, ny - 2), 3)
        pygame.draw.line(self.ecran, (67, 47, 39), (nx + 4, ny - 9), (nx + 5, ny - 2), 3)
        pygame.draw.ellipse(self.ecran, (66, 111, 157), (nx - 8, ny - 25, 16, 18))
        pygame.draw.polygon(self.ecran, (233, 208, 167), [(nx, ny - 23), (nx - 6, ny - 9), (nx, ny - 6), (nx + 6, ny - 9)])
        pygame.draw.line(self.ecran, (205, 166, 125), (nx - 7, ny - 20), (nx - 12, ny - 13), 3)
        pygame.draw.line(self.ecran, (205, 166, 125), (nx + 7, ny - 20), (nx + 12, ny - 14), 3)
        pygame.draw.circle(self.ecran, (239, 199, 143), (nx, ny - 31), 7)
        pygame.draw.arc(self.ecran, (99, 61, 40), (nx - 7, ny - 38, 14, 12), 3.14, 6.28, 4)
        pygame.draw.circle(self.ecran, (72, 52, 43), (nx - 2, ny - 31), 1)
        pygame.draw.circle(self.ecran, (72, 52, 43), (nx + 2, ny - 31), 1)
        pygame.draw.arc(self.ecran, (145, 64, 57), (nx - 2, ny - 29, 5, 4), 0, 3.14, 1)
        index = self.villages.index(village)
        if not self.quetes[index]["faite"]:
            indication = self.police.render("!", True, (255, 226, 90))
            self.ecran.blit(indication, indication.get_rect(center=(nx + 13, ny - 47)))

    def dessiner_arbre(self, x, y, camera_x, camera_y):
        """Dessine une essence adaptee au royaume : arbre feuillu ou sapin."""
        sx, sy = projeter(x + 0.5, y + 0.5, camera_x, camera_y)
        pygame.draw.ellipse(self.ecran, (31, 76, 43), (sx - 21, sy - 4, 42, 17))
        biome = biome_region(x, y)
        if biome == "desert":
            pygame.draw.polygon(self.ecran, (40, 83, 56), [(sx - 7, sy - 3), (sx - 7, sy - 45), (sx, sy - 57), (sx + 7, sy - 45), (sx + 7, sy - 3)])
            pygame.draw.polygon(self.ecran, (65, 132, 79), [(sx - 5, sy - 8), (sx - 5, sy - 42), (sx, sy - 51), (sx + 4, sy - 41), (sx + 4, sy - 8)])
            pygame.draw.line(self.ecran, (190, 190, 142), (sx - 4, sy - 31), (sx + 4, sy - 31), 1)
            pygame.draw.line(self.ecran, (190, 190, 142), (sx - 4, sy - 21), (sx + 4, sy - 21), 1)
            pygame.draw.line(self.ecran, (190, 190, 142), (sx - 4, sy - 12), (sx + 4, sy - 12), 1)
            return
        pygame.draw.rect(self.ecran, (105, 67, 39), (sx - 5, sy - 36, 10, 38))
        biome = biome_region(x, y)
        if biome == "neige":
            pygame.draw.polygon(self.ecran, (44, 90, 81), [(sx, sy - 82), (sx - 24, sy - 31), (sx + 24, sy - 31)])
            pygame.draw.polygon(self.ecran, (58, 119, 100), [(sx, sy - 68), (sx - 19, sy - 25), (sx + 19, sy - 25)])
            pygame.draw.polygon(self.ecran, (225, 235, 230), [(sx, sy - 82), (sx - 7, sy - 66), (sx + 8, sy - 66)])
        else:
            couleur_base = (29, 95, 48) if biome in ("prairie", "foret") else (105, 127, 61)
            couleur_claire = (42, 125, 57) if biome in ("prairie", "foret") else (145, 153, 75)
            pygame.draw.circle(self.ecran, couleur_base, (sx, sy - 45), 23)
            pygame.draw.circle(self.ecran, couleur_claire, (sx - 12, sy - 48), 14)
            pygame.draw.circle(self.ecran, couleur_claire, (sx + 11, sy - 51), 15)

    def dessiner_decoration(self, decoration, camera_x, camera_y):
        sx, sy = projeter(decoration["x"], decoration["y"], camera_x, camera_y)
        couleur = decoration["couleur"]
        pygame.draw.ellipse(self.ecran, (44, 59, 42), (sx - 7, sy - 1, 14, 5))
        sorte = decoration["type"]
        if sorte in ("fleur", "champignon"):
            pygame.draw.line(self.ecran, (72, 123, 64), (sx, sy - 2), (sx, sy - 10), 2)
            if sorte == "fleur":
                pygame.draw.circle(self.ecran, couleur, (sx, sy - 11), 3)
                pygame.draw.circle(self.ecran, (245, 218, 128), (sx, sy - 11), 1)
            else:
                pygame.draw.ellipse(self.ecran, (239, 218, 179), (sx - 3, sy - 8, 6, 4))
                pygame.draw.arc(self.ecran, couleur, (sx - 4, sy - 13, 8, 7), 0, math.pi, 3)
        elif sorte in ("herbe", "fougere"):
            pygame.draw.line(self.ecran, couleur, (sx, sy - 2), (sx - 4, sy - 10), 2)
            pygame.draw.line(self.ecran, couleur, (sx, sy - 2), (sx + 1, sy - 12), 2)
            pygame.draw.line(self.ecran, couleur, (sx, sy - 2), (sx + 5, sy - 9), 2)
        elif sorte == "touffe":
            pygame.draw.line(self.ecran, (113, 79, 48), (sx - 4, sy - 3), (sx, sy - 10), 2)
            pygame.draw.line(self.ecran, couleur, (sx, sy - 3), (sx - 1, sy - 12), 2)
            pygame.draw.line(self.ecran, couleur, (sx + 3, sy - 3), (sx + 6, sy - 9), 2)
        else:
            pygame.draw.polygon(self.ecran, (115, 181, 197), [(sx, sy - 15), (sx - 4, sy - 5), (sx, sy - 3), (sx + 4, sy - 5)])
            pygame.draw.line(self.ecran, couleur, (sx, sy - 12), (sx, sy - 5), 1)

    def dessiner_ennemi(self, ennemi, camera_x, camera_y):
        """Dessine chaque monstre avec une silhouette reconnaissable."""
        sx, sy = projeter(ennemi["x"], ennemi["y"], camera_x, camera_y)
        profil = MONSTRES[ennemi["type"]]
        teinte = profil["couleur"]
        sorte = ennemi["type"]
        taille = 45 if sorte == "dragon" else 34 if sorte == "loup" else 29
        pygame.draw.ellipse(self.ecran, (36, 58, 43), (sx - taille // 2, sy - 2, taille, 12))

        if sorte == "gelatine":
            pygame.draw.ellipse(self.ecran, teinte, (sx - 13, sy - 22, 26, 22))
            pygame.draw.ellipse(self.ecran, (143, 235, 163), (sx - 7, sy - 19, 8, 5))
            pygame.draw.circle(self.ecran, BLANC, (sx - 5, sy - 12), 3)
            pygame.draw.circle(self.ecran, BLANC, (sx + 5, sy - 12), 3)
            pygame.draw.circle(self.ecran, NOIR, (sx - 4, sy - 12), 1)
            pygame.draw.circle(self.ecran, NOIR, (sx + 6, sy - 12), 1)
        elif sorte == "araignee":
            # Huit pattes articulees autour d'un abdomen distinct de la tete.
            for cote in (-1, 1):
                for niveau in range(4):
                    depart = (sx + cote * 8, sy - 10 + niveau * 3)
                    coude = (sx + cote * (17 + niveau), sy - 16 + niveau * 5)
                    pied = (sx + cote * (21 + niveau), sy - 9 + niveau * 5)
                    pygame.draw.line(self.ecran, (91, 61, 49), depart, coude, 2)
                    pygame.draw.line(self.ecran, (91, 61, 49), coude, pied, 2)
            pygame.draw.ellipse(self.ecran, teinte, (sx - 10, sy - 19, 20, 18))
            pygame.draw.circle(self.ecran, (78, 49, 42), (sx, sy - 20), 7)
            pygame.draw.circle(self.ecran, (239, 73, 62), (sx - 3, sy - 21), 2)
            pygame.draw.circle(self.ecran, (239, 73, 62), (sx + 3, sy - 21), 2)
        elif sorte == "loup":
            # Silhouette basse, museau avance et oreilles pointues.
            pygame.draw.ellipse(self.ecran, teinte, (sx - 17, sy - 22, 30, 17))
            pygame.draw.ellipse(self.ecran, (171, 177, 177), (sx + 5, sy - 19, 13, 10))
            pygame.draw.polygon(self.ecran, teinte, [(sx - 13, sy - 17), (sx - 12, sy - 32), (sx - 3, sy - 20)])
            pygame.draw.polygon(self.ecran, teinte, [(sx - 4, sy - 19), (sx + 1, sy - 31), (sx + 5, sy - 17)])
            pygame.draw.circle(self.ecran, (245, 192, 82), (sx + 9, sy - 15), 2)
            pygame.draw.line(self.ecran, teinte, (sx - 12, sy - 8), (sx - 17, sy - 3), 3)
            pygame.draw.line(self.ecran, teinte, (sx + 5, sy - 8), (sx + 8, sy - 3), 3)
        elif sorte == "chevalier":
            # Armure, casque a visiere, bouclier et jambieres metalliques.
            pygame.draw.line(self.ecran, (178, 190, 200), (sx - 8, sy - 8), (sx - 10, sy - 2), 4)
            pygame.draw.line(self.ecran, (178, 190, 200), (sx + 8, sy - 8), (sx + 10, sy - 2), 4)
            pygame.draw.polygon(self.ecran, (102, 113, 145), [(sx - 12, sy - 25), (sx + 12, sy - 25), (sx + 9, sy - 7), (sx - 9, sy - 7)])
            pygame.draw.polygon(self.ecran, (183, 195, 211), [(sx - 11, sy - 24), (sx - 6, sy - 23), (sx - 8, sy - 9), (sx - 11, sy - 9)])
            pygame.draw.ellipse(self.ecran, (147, 161, 180), (sx - 9, sy - 37, 18, 15))
            pygame.draw.polygon(self.ecran, (198, 203, 208), [(sx - 10, sy - 32), (sx, sy - 46), (sx + 10, sy - 32)])
            pygame.draw.line(self.ecran, (54, 58, 68), (sx - 5, sy - 30), (sx + 5, sy - 30), 2)
            pygame.draw.ellipse(self.ecran, (184, 52, 51), (sx + 10, sy - 22, 9, 14))
            pygame.draw.line(self.ecran, (218, 221, 222), (sx + 18, sy - 30), (sx + 18, sy - 9), 3)
        elif sorte == "dragon":
            # Grandes ailes nervurees et corps ecailleux.
            pygame.draw.polygon(self.ecran, (117, 41, 48), [(sx - 10, sy - 22), (sx - 35, sy - 43), (sx - 29, sy - 17), (sx - 17, sy - 12)])
            pygame.draw.polygon(self.ecran, (117, 41, 48), [(sx + 10, sy - 22), (sx + 35, sy - 43), (sx + 29, sy - 17), (sx + 17, sy - 12)])
            pygame.draw.line(self.ecran, (225, 120, 93), (sx - 12, sy - 21), (sx - 32, sy - 37), 2)
            pygame.draw.line(self.ecran, (225, 120, 93), (sx + 12, sy - 21), (sx + 32, sy - 37), 2)
            pygame.draw.ellipse(self.ecran, teinte, (sx - 17, sy - 27, 34, 25))
            pygame.draw.ellipse(self.ecran, (224, 115, 69), (sx + 8, sy - 25, 17, 12))
            pygame.draw.polygon(self.ecran, (230, 197, 123), [(sx - 9, sy - 39), (sx - 14, sy - 51), (sx - 2, sy - 39)])
            pygame.draw.polygon(self.ecran, (230, 197, 123), [(sx + 3, sy - 39), (sx + 10, sy - 51), (sx + 11, sy - 37)])
            pygame.draw.circle(self.ecran, (250, 218, 85), (sx + 16, sy - 22), 3)
            pygame.draw.circle(self.ecran, NOIR, (sx + 17, sy - 22), 1)
            pygame.draw.polygon(self.ecran, teinte, [(sx - 14, sy - 15), (sx - 25, sy - 8), (sx - 22, sy - 13)])

        if ennemi["vies"] > 1:
            pygame.draw.rect(self.ecran, (70, 35, 35), (sx - 16, sy - taille - 8, 32, 5), border_radius=2)
            largeur_vie = round(30 * ennemi["vies"] / ennemi["vies_max"])
            pygame.draw.rect(self.ecran, (225, 70, 70), (sx - 15, sy - taille - 7, largeur_vie, 3), border_radius=2)

    def dessiner_coffre(self, coffre, camera_x, camera_y):
        sx, sy = projeter(coffre["x"], coffre["y"], camera_x, camera_y)
        pygame.draw.ellipse(self.ecran, (42, 55, 39), (sx - 17, sy - 1, 34, 10))
        bois = (91, 68, 48) if coffre["ouvert"] else (137, 91, 48)
        pygame.draw.rect(self.ecran, bois, (sx - 13, sy - 19, 26, 17), border_radius=3)
        pygame.draw.arc(self.ecran, (171, 123, 71), (sx - 13, sy - 25, 26, 16), 3.14, 6.28, 5)
        pygame.draw.line(self.ecran, (199, 158, 91), (sx - 11, sy - 15), (sx + 11, sy - 15), 2)
        pygame.draw.rect(self.ecran, (219, 183, 93), (sx - 2, sy - 15, 5, 7), border_radius=1)
        if coffre["ouvert"]:
            pygame.draw.line(self.ecran, (65, 47, 35), (sx - 11, sy - 19), (sx + 10, sy - 25), 3)

    def creer_icone_equipement(self, genre, identifiant):
        cle = genre, identifiant
        if cle in self.icones_equipement:
            return self.icones_equipement[cle]

        profil = ARMES[identifiant] if genre == "arme" else BOUCLIERS[identifiant]
        icone = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(icone, (25, 32, 34), (2, 2, 60, 60), border_radius=13)
        pygame.draw.rect(icone, (95, 82, 60), (2, 2, 60, 60), 2, border_radius=13)
        pygame.draw.ellipse(icone, (10, 15, 17, 150), (10, 48, 44, 9))
        metal = profil["couleur"]

        if genre == "bouclier":
            forme = [(32, 9), (51, 15), (48, 39), (32, 54), (16, 39), (13, 15)]
            interieur = [(32, 14), (46, 18), (43, 37), (32, 48), (21, 37), (18, 18)]
            pygame.draw.polygon(icone, (24, 28, 30), forme)
            pygame.draw.polygon(icone, metal, interieur)
            pygame.draw.polygon(icone, tuple(min(255, c + 38) for c in metal), [(32, 15), (43, 19), (40, 35), (32, 42)])
            pygame.draw.line(icone, (232, 211, 157), (32, 15), (32, 44), 2)
            pygame.draw.line(icone, (59, 49, 37), (19, 24), (45, 24), 2)
            pygame.draw.circle(icone, (241, 209, 126), (32, 23), 3)
        elif profil.get("forme") == "arbalete":
            pygame.draw.line(icone, (105, 72, 43), (18, 35), (48, 35), 7)
            pygame.draw.line(icone, metal, (17, 24), (49, 24), 4)
            pygame.draw.line(icone, (232, 211, 157), (17, 24), (49, 24), 1)
            pygame.draw.line(icone, (48, 34, 26), (32, 20), (32, 48), 5)
            pygame.draw.polygon(icone, (232, 211, 157), [(53, 24), (46, 21), (46, 27)])
        elif profil["type"] == "arc":
            grand = identifiant != "arc_chasseur"
            hauteur = 40 if grand else 32
            x = 32
            arc = [(x - 5, 32 - hauteur // 2), (x + 7, 25), (x + 9, 32), (x + 7, 39), (x - 5, 32 + hauteur // 2)]
            pygame.draw.lines(icone, (48, 34, 26), False, [(px + 2, py + 1) for px, py in arc], 6)
            pygame.draw.lines(icone, metal, False, arc, 3)
            pygame.draw.line(icone, (231, 219, 185), arc[0], arc[-1], 1)
            pygame.draw.line(icone, (232, 211, 157), (x - 8, 32), (x + 21, 32), 2)
            pygame.draw.polygon(icone, (232, 211, 157), [(53, 32), (46, 29), (47, 35)])
            pygame.draw.line(icone, (109, 70, 41), (x - 2, 27), (x - 2, 37), 4)
        elif identifiant == "hache_guerre":
            pygame.draw.line(icone, (76, 51, 33), (20, 47), (43, 16), 7)
            pygame.draw.line(icone, (156, 112, 69), (20, 47), (43, 16), 3)
            pygame.draw.polygon(icone, (40, 44, 47), [(37, 25), (37, 14), (49, 10), (57, 16), (51, 28), (43, 31)])
            pygame.draw.polygon(icone, metal, [(40, 23), (41, 16), (49, 13), (53, 17), (49, 24)])
            pygame.draw.line(icone, (247, 231, 189), (49, 14), (54, 17), 2)
            pygame.draw.circle(icone, (219, 183, 93), (37, 27), 3)
        elif profil.get("forme") == "lance":
            pygame.draw.line(icone, (70, 48, 32), (20, 50), (44, 12), 7)
            pygame.draw.line(icone, (153, 108, 65), (20, 50), (44, 12), 3)
            pygame.draw.polygon(icone, (37, 43, 46), [(44, 10), (39, 21), (49, 18)])
            pygame.draw.polygon(icone, metal, [(44, 11), (42, 19), (47, 17)])
            pygame.draw.line(icone, (247, 237, 209), (44, 11), (47, 13), 1)
        elif profil.get("forme") in ("masse", "marteau"):
            pygame.draw.line(icone, (74, 49, 32), (21, 50), (43, 14), 8)
            pygame.draw.line(icone, (150, 105, 63), (21, 50), (43, 14), 3)
            largeur_tete = 16 if profil["forme"] == "marteau" else 12
            pygame.draw.rect(icone, (46, 51, 55), (38, 10, largeur_tete, 12), border_radius=2)
            pygame.draw.rect(icone, metal, (40, 11, largeur_tete - 4, 8), border_radius=2)
            pygame.draw.line(icone, (244, 237, 218), (41, 12), (48, 12), 1)
        elif profil.get("forme") == "dague":
            pygame.draw.line(icone, (65, 43, 29), (23, 47), (33, 34), 7)
            pygame.draw.line(icone, (150, 104, 62), (23, 47), (33, 34), 3)
            pygame.draw.line(icone, (222, 194, 112), (27, 38), (38, 43), 3)
            pygame.draw.polygon(icone, (44, 50, 54), [(33, 36), (46, 14), (40, 34)])
            pygame.draw.polygon(icone, metal, [(34, 34), (44, 16), (39, 35)])
        else:
            pygame.draw.line(icone, (52, 37, 27), (17, 48), (47, 15), 9)
            pygame.draw.line(icone, (135, 94, 54), (17, 48), (47, 15), 5)
            pygame.draw.polygon(icone, (32, 37, 41), [(41, 24), (45, 12), (51, 8), (55, 13), (49, 30)])
            pygame.draw.polygon(icone, metal, [(44, 21), (47, 13), (50, 11), (52, 14), (48, 24)])
            pygame.draw.line(icone, (246, 237, 208), (48, 13), (52, 13), 2)
            pygame.draw.line(icone, (219, 183, 93), (35, 26), (41, 31), 2)

        self.icones_equipement[cle] = icone
        return icone

    def dessiner_inventaire(self):
        voile = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
        voile.fill((8, 15, 17, 205))
        self.ecran.blit(voile, (0, 0))
        cadre = pygame.Rect(150, 75, 700, 570)
        pygame.draw.rect(self.ecran, (28, 36, 35), cadre, border_radius=14)
        pygame.draw.rect(self.ecran, (185, 151, 91), cadre, 3, border_radius=14)
        pygame.draw.rect(self.ecran, (49, 59, 51), (166, 87, 668, 73), border_radius=10)
        self.ecran.blit(self.grande_police.render("Arsenal", True, (246, 224, 169)), (188, 94))
        self.ecran.blit(self.police.render("Choisis ton equipement avant de repartir a l'aventure", True, (194, 198, 177)), (191, 133))
        elements = self.elements_inventaire()
        lignes_visibles = 5
        premiere_ligne = max(0, self.inventaire_index // 2 - lignes_visibles + 1)
        self.ecran.set_clip(pygame.Rect(166, 165, 668, 365))
        for index, (genre, identifiant) in enumerate(elements):
            colonne = index % 2
            ligne = index // 2
            x = 177 + colonne * 323
            y = 171 + (ligne - premiere_ligne) * 72
            selectionne = index == self.inventaire_index
            rect = pygame.Rect(x, y, 310, 64)
            profil = ARMES[identifiant] if genre == "arme" else BOUCLIERS[identifiant]
            equipee = identifiant == (self.arme_equipee if genre == "arme" else self.bouclier_equipe)
            fond = (66, 71, 54) if selectionne else (39, 47, 44)
            bord = (235, 200, 111) if equipee else (104, 107, 89)
            pygame.draw.rect(self.ecran, fond, rect, border_radius=9)
            pygame.draw.rect(self.ecran, bord, rect, 2 if selectionne or equipee else 1, border_radius=9)
            icone = self.creer_icone_equipement(genre, identifiant)
            self.ecran.blit(icone, (x + 6, y))
            if selectionne:
                etiquette = "ARME" if genre == "arme" else "BOUCLIER"
            else:
                etiquette = "ARME" if genre == "arme" else "BOUCLIER"
            couleur_nom = (255, 225, 151) if equipee else BLANC
            nom = profil["nom"]
            if len(nom) > 19:
                nom = nom[:18] + "."
            self.ecran.blit(self.police.render(nom, True, couleur_nom), (x + 70, y + 7))
            valeur = f"Degats {profil['degats']}" if genre == "arme" else f"Defense {profil['defense']}"
            self.ecran.blit(self.police_details.render(f"{etiquette}  |  {valeur}", True, (179, 196, 176)), (x + 71, y + 27))
            description = profil["description"]
            if len(description) > 25:
                description = description[:24] + "."
            self.ecran.blit(self.police_details.render(description, True, (158, 169, 151)), (x + 71, y + 46))
            if equipee:
                pygame.draw.circle(self.ecran, (243, 208, 119), (x + 294, y + 13), 4)
        self.ecran.set_clip(None)
        resume = self.police.render(f"Fleches : {self.fleches}     Gemmes : {self.score}", True, (145, 221, 219))
        self.ecran.blit(resume, (190, 544))
        self.ecran.blit(
            self.police_details.render(
                f"Ligne {self.inventaire_index // 2 + 1}/{max(1, (len(elements) + 1) // 2)}",
                True,
                (194, 198, 177),
            ),
            (680, 551),
        )
        self.ecran.blit(self.police.render("Haut/Bas : choisir   Entree : equiper   I : fermer", True, BLANC), (190, 585))

    def dessiner_arme_en_main(self, centre_x, centre_y, face_x, face_y, attaque):
        profil = ARMES[self.arme_equipee]
        depart = (centre_x + 8, centre_y - 19)
        if profil.get("forme") == "arbalete":
            ux, uy = face_x, face_y
            px, py = -uy, ux
            bout = (round(depart[0] + ux * 21), round(depart[1] + uy * 21))
            pygame.draw.line(self.ecran, (79, 52, 33), depart, bout, 7)
            pygame.draw.line(self.ecran, profil["couleur"], depart, bout, 3)
            pygame.draw.line(
                self.ecran,
                profil["couleur"],
                (round(bout[0] + px * 13), round(bout[1] + py * 13)),
                (round(bout[0] - px * 13), round(bout[1] - py * 13)),
                4,
            )
            pygame.draw.line(
                self.ecran,
                (228, 218, 192),
                (round(bout[0] + px * 13), round(bout[1] + py * 13)),
                (round(bout[0] - px * 13), round(bout[1] - py * 13)),
                1,
            )
            return
        if profil["type"] == "arc":
            courbe = [
                (depart[0] + 7, centre_y - 17),
                (depart[0] + 12, centre_y - 12),
                (depart[0] + 14, centre_y - 4),
                (depart[0] + 12, centre_y + 4),
                (depart[0] + 7, centre_y + 9),
            ]
            pygame.draw.lines(self.ecran, (53, 37, 26), False, courbe, 5)
            pygame.draw.lines(self.ecran, profil["couleur"], False, courbe, 3)
            pygame.draw.line(self.ecran, (225, 217, 190), courbe[0], courbe[-1], 1)
            if attaque:
                pygame.draw.line(self.ecran, (237, 224, 191), courbe[0], courbe[-1], 1)
                pygame.draw.line(self.ecran, (220, 201, 154), (depart[0] + 10, depart[1] - 2), (depart[0] + 38, depart[1] - 2), 2)
            return

        ux, uy = face_x, face_y
        px, py = -uy, ux
        longueur = 36 if attaque else 23
        if profil.get("forme") == "lance":
            longueur += 13
        elif profil.get("forme") == "dague":
            longueur = 22 if attaque else 14
        bout = (round(depart[0] + ux * longueur), round(depart[1] + uy * longueur))
        garde = (round(depart[0] + ux * 7), round(depart[1] + uy * 7))
        pygame.draw.line(self.ecran, (63, 42, 28), (depart[0] - round(ux * 5), depart[1] - round(uy * 5)), garde, 6)
        pygame.draw.line(self.ecran, (154, 105, 57), (depart[0] - round(ux * 5), depart[1] - round(uy * 5)), garde, 3)
        pygame.draw.line(
            self.ecran,
            (218, 183, 94),
            (round(garde[0] + px * 6), round(garde[1] + py * 6)),
            (round(garde[0] - px * 6), round(garde[1] - py * 6)),
            3,
        )
        if profil.get("forme") in ("masse", "marteau"):
            tete = (round(bout[0] - ux * 4), round(bout[1] - uy * 4))
            pygame.draw.line(self.ecran, (49, 53, 57), (round(tete[0] + px * 7), round(tete[1] + py * 7)), (round(tete[0] - px * 7), round(tete[1] - py * 7)), 8)
            pygame.draw.line(self.ecran, profil["couleur"], (round(tete[0] + px * 7), round(tete[1] + py * 7)), (round(tete[0] - px * 7), round(tete[1] - py * 7)), 5)
        elif self.arme_equipee == "hache_guerre":
            tete = (round(bout[0] - ux * 4), round(bout[1] - uy * 4))
            pygame.draw.polygon(
                self.ecran,
                (49, 53, 57),
                [
                    (round(tete[0] + px * 3), round(tete[1] + py * 3)),
                    (round(tete[0] + ux * 4 + px * 11), round(tete[1] + uy * 4 + py * 11)),
                    (round(tete[0] + ux * 10 + px * 10), round(tete[1] + uy * 10 + py * 10)),
                    (round(tete[0] + ux * 9 - px * 5), round(tete[1] + uy * 9 - py * 5)),
                ],
            )
            pygame.draw.line(self.ecran, profil["couleur"], (round(tete[0] + ux * 4 + px * 8), round(tete[1] + uy * 4 + py * 8)), (round(tete[0] + ux * 10 + px * 8), round(tete[1] + uy * 10 + py * 8)), 2)
        else:
            cote = 5 if attaque else 4
            pygame.draw.polygon(
                self.ecran,
                (38, 44, 48),
                [
                    (round(garde[0] + ux * 3 + px * 2), round(garde[1] + uy * 3 + py * 2)),
                    (round(bout[0] + px * cote), round(bout[1] + py * cote)),
                    bout,
                    (round(bout[0] - px * cote), round(bout[1] - py * cote)),
                    (round(garde[0] + ux * 3 - px * 2), round(garde[1] + uy * 3 - py * 2)),
                ],
            )
            pygame.draw.line(self.ecran, (249, 243, 220), (round(garde[0] + ux * 8 + px), round(garde[1] + uy * 8 + py)), (round(bout[0] - px), round(bout[1] - py)), 2)

    def dessiner_personnage(self, camera_x, camera_y, maintenant):
        """Dessine le heros avec des vetements detailles et une marche en volume."""
        sx, sy = projeter(self.joueur_x, self.joueur_y, camera_x, camera_y)
        clignote = maintenant < self.invulnerable_jusqua and maintenant // 100 % 2 == 0
        if clignote:
            return
        phase = self.temps_marche * 11 if self.en_marche else 0
        pas_gauche = math.sin(phase) * 4 if self.en_marche else 0
        pas_droit = -pas_gauche
        leve_gauche = max(0, math.cos(phase)) * 3 if self.en_marche else 0
        leve_droit = max(0, -math.cos(phase)) * 3 if self.en_marche else 0
        rebond = round(abs(math.sin(phase * 2)) * 2) if self.en_marche else 0
        corps_y = sy - rebond
        # Convertit le regard du monde en direction visible sur l'ecran.
        face_x = self.direction[0] - self.direction[1]
        face_y = self.direction[0] + self.direction[1]
        longueur = max(1, math.hypot(face_x, face_y))
        face_x, face_y = face_x / longueur, face_y / longueur
        regard_x = round(face_x * 3)
        regard_y = round(face_y * 2)

        # L'ombre s'aplatit et les jambes alternent hauteur et avance pendant le pas.
        largeur_ombre = 29 + rebond
        pygame.draw.ellipse(self.ecran, (31, 43, 34), (sx - largeur_ombre // 2, sy - 3, largeur_ombre, 8))
        pygame.draw.ellipse(self.ecran, (67, 74, 55), (sx - 10, sy - 3, 20, 4))
        for jambe_x, pas, leve in ((sx - 5, pas_gauche, leve_gauche), (sx + 5, pas_droit, leve_droit)):
            hanche = (jambe_x, corps_y - 13)
            genou = (round(jambe_x + pas * 0.45), round(corps_y - 7 - leve))
            pied = (round(jambe_x + pas), round(sy - 5 - leve))
            pygame.draw.line(self.ecran, (43, 38, 35), hanche, genou, 7)
            pygame.draw.line(self.ecran, (107, 76, 55), hanche, genou, 4)
            pygame.draw.circle(self.ecran, (139, 99, 68), genou, 3)
            pygame.draw.line(self.ecran, (71, 53, 42), genou, pied, 5)
            pygame.draw.line(self.ecran, (128, 95, 66), (genou[0] - 1, genou[1] + 1), (pied[0] - 1, pied[1] - 1), 2)
            pygame.draw.ellipse(self.ecran, (44, 36, 31), (pied[0] - 5, pied[1] - 2, 11, 6))
            pygame.draw.line(self.ecran, (151, 112, 75), (pied[0] - 2, pied[1] - 2), (pied[0] + 3, pied[1] - 2), 1)

        # Tunique, ceinture et bras dessines avant la tete pour creer des couches.
        pygame.draw.polygon(self.ecran, (28, 55, 87), [(sx - 9, corps_y - 34), (sx + 8, corps_y - 34), (sx + 13, corps_y - 12), (sx + 7, corps_y - 10), (sx - 12, corps_y - 12), (sx - 14, corps_y - 17)])
        pygame.draw.polygon(self.ecran, (39, 83, 149), [(sx - 8, corps_y - 33), (sx + 6, corps_y - 32), (sx + 9, corps_y - 14), (sx - 10, corps_y - 14)])
        pygame.draw.polygon(self.ecran, (70, 117, 168), [(sx - 7, corps_y - 30), (sx - 2, corps_y - 31), (sx - 5, corps_y - 15), (sx - 9, corps_y - 15)])
        pygame.draw.line(self.ecran, (121, 83, 54), (sx - 10, corps_y - 16), (sx + 10, corps_y - 16), 4)
        pygame.draw.rect(self.ecran, (219, 184, 87), (sx - 2, corps_y - 18, 5, 5), border_radius=1)
        pygame.draw.line(self.ecran, (178, 131, 70), (sx - 10, corps_y - 22), (sx + 8, corps_y - 22), 1)
        pygame.draw.rect(self.ecran, (119, 77, 46), (sx + 5, corps_y - 20, 6, 7), border_radius=2)
        pygame.draw.line(self.ecran, (187, 147, 94), (sx + 7, corps_y - 19), (sx + 7, corps_y - 15), 1)
        pygame.draw.polygon(self.ecran, (219, 211, 184), [(sx - 4, corps_y - 33), (sx, corps_y - 28), (sx + 4, corps_y - 33)])
        bras_gauche = (sx - 12, corps_y - 26 + round(pas_gauche * 0.25))
        bras_droit = (sx + 12, corps_y - 26 + round(pas_droit * 0.25))
        pygame.draw.line(self.ecran, (31, 64, 105), (sx - 8, corps_y - 29), bras_gauche, 7)
        pygame.draw.line(self.ecran, (57, 101, 155), (sx - 9, corps_y - 28), (bras_gauche[0], bras_gauche[1] - 2), 2)
        pygame.draw.line(self.ecran, (31, 64, 105), (sx + 8, corps_y - 29), bras_droit, 7)
        pygame.draw.line(self.ecran, (57, 101, 155), (sx + 9, corps_y - 28), (bras_droit[0], bras_droit[1] - 2), 2)
        pygame.draw.circle(self.ecran, (206, 155, 111), bras_gauche, 4)
        pygame.draw.circle(self.ecran, (228, 181, 134), bras_droit, 4)
        if self.bouclier_equipe:
            teinte_bouclier = BOUCLIERS[self.bouclier_equipe]["couleur"]
            pygame.draw.polygon(self.ecran, (43, 48, 48), [(sx - 18, corps_y - 30), (sx - 5, corps_y - 27), (sx - 7, corps_y - 11), (sx - 14, corps_y - 7), (sx - 21, corps_y - 12)])
            pygame.draw.polygon(self.ecran, teinte_bouclier, [(sx - 17, corps_y - 28), (sx - 7, corps_y - 26), (sx - 9, corps_y - 13), (sx - 14, corps_y - 10), (sx - 19, corps_y - 13)])
            pygame.draw.line(self.ecran, (217, 194, 132), (sx - 14, corps_y - 26), (sx - 14, corps_y - 13), 1)

        # Tete, oreilles, cheveux et visage avec un oeil dans la direction du regard.
        pygame.draw.rect(self.ecran, (178, 124, 91), (sx - 3, corps_y - 41, 7, 10), border_radius=2)
        pygame.draw.circle(self.ecran, (196, 143, 107), (sx + 1, corps_y - 40), 8)
        pygame.draw.circle(self.ecran, (236, 194, 151), (sx, corps_y - 45), 10)
        pygame.draw.circle(self.ecran, (216, 164, 124), (sx - 10, corps_y - 44), 3)
        pygame.draw.circle(self.ecran, (216, 164, 124), (sx + 10, corps_y - 44), 3)
        pygame.draw.arc(self.ecran, (91, 57, 41), (sx - 9, corps_y - 54, 18, 13), 3.14, 6.28, 4)
        pygame.draw.circle(self.ecran, (224, 181, 133), (sx - 3, corps_y - 48), 3)
        pygame.draw.circle(self.ecran, (255, 221, 183), (sx - 3, corps_y - 47), 1)
        pygame.draw.circle(self.ecran, NOIR, (sx + regard_x + 2, corps_y - 46 + regard_y), 2)
        pygame.draw.circle(self.ecran, (255, 231, 193), (sx + regard_x + 2, corps_y - 47 + regard_y), 1)
        pygame.draw.line(self.ecran, (117, 72, 53), (sx - 1, corps_y - 40), (sx + 4, corps_y - 39), 1)

        # Un bonnet de voyage avec coutures et bord en cuir.
        pygame.draw.ellipse(self.ecran, (38, 119, 63), (sx - 10, corps_y - 58, 20, 13))
        pygame.draw.polygon(self.ecran, (53, 147, 75), [(sx - 9, corps_y - 52), (sx + 5, corps_y - 60), (sx + 12, corps_y - 51)])
        pygame.draw.ellipse(self.ecran, (31, 101, 53), (sx - 12, corps_y - 51, 25, 5))
        pygame.draw.line(self.ecran, (95, 168, 103), (sx - 5, corps_y - 55), (sx + 3, corps_y - 59), 1)
        pygame.draw.circle(self.ecran, (238, 205, 104), (sx + 4, corps_y - 53), 2)

        attaque = maintenant < self.attaque_jusqua
        self.dessiner_arme_en_main(sx, corps_y, face_x, face_y, attaque)
        if attaque and ARMES[self.arme_equipee]["type"] == "corps":
            angle = math.atan2(face_y, face_x)
            trajectoire = [
                (
                    round(sx + math.cos(angle + ecart) * 34),
                    round(corps_y - 27 + math.sin(angle + ecart) * 19),
                )
                for ecart in (-0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75)
            ]
            pygame.draw.lines(self.ecran, (71, 57, 43), False, trajectoire, 5)
            pygame.draw.lines(self.ecran, (250, 238, 184), False, trajectoire, 2)

    def dessiner_interface(self):
        """Affiche la region, les quetes, la faim, les commandes et la mini-carte."""
        pygame.draw.rect(self.ecran, (23, 44, 38), (12, 12, 525, 230), border_radius=10)
        biome = biome_region(self.joueur_x, self.joueur_y)
        royaume = "Grotte" if self.dans_grotte else (
            "Prairies" if self.joueur_x < 20 else
            "Foret" if self.joueur_x < 40 else
            "Desert" if self.joueur_x < 60 else
            "Montagnes" if self.joueur_x < 80 else
            "Marches vertes" if biome == "prairie" else
            "Bois lointains" if biome == "foret" else
            "Dunes anciennes" if biome == "desert" else
            "Cimes du nord"
        )
        self.ecran.blit(self.police.render(f"{royaume}   Gemmes : {self.score}   Rations : {self.nourriture}", True, BLANC), (27, 19))
        meteo_noms = {"clair": "Clair", "vent": "Venteux", "pluie": "Pluie", "orage": "Orage", "neige": "Neige"}
        self.ecran.blit(self.police_details.render(f"{self.saison} | {meteo_noms[self.meteo]}", True, (190, 218, 230)), (380, 22))
        arme = ARMES[self.arme_equipee]["nom"]
        bouclier = BOUCLIERS[self.bouclier_equipe]["nom"] if self.bouclier_equipe else "Aucun bouclier"
        self.ecran.blit(self.police.render(f"Arme : {arme}   Bouclier : {bouclier}   Fleches : {self.fleches}", True, (222, 220, 192)), (27, 42))
        self.ecran.blit(self.police.render("Vies", True, BLANC), (27, 64))
        for index in range(5):
            coeur_x = 81 + index * 23
            coeur_y = 68
            couleur = (226, 61, 70) if index < self.vies else (91, 58, 60)
            points = (
                (coeur_x, coeur_y + 5),
                (coeur_x + 1, coeur_y + 2),
                (coeur_x + 4, coeur_y),
                (coeur_x + 7, coeur_y + 1),
                (coeur_x + 9, coeur_y + 4),
                (coeur_x + 11, coeur_y + 1),
                (coeur_x + 14, coeur_y),
                (coeur_x + 17, coeur_y + 2),
                (coeur_x + 18, coeur_y + 5),
                (coeur_x + 17, coeur_y + 8),
                (coeur_x + 9, coeur_y + 16),
                (coeur_x + 1, coeur_y + 8),
            )
            pygame.draw.polygon(self.ecran, (35, 39, 36), [(x + 1, y + 2) for x, y in points])
            pygame.draw.polygon(self.ecran, couleur, points)
            if index < self.vies:
                pygame.draw.line(
                    self.ecran,
                    (255, 157, 153),
                    (coeur_x + 3, coeur_y + 4),
                    (coeur_x + 6, coeur_y + 3),
                    1,
                )

        self.ecran.blit(self.police.render("Endurance", True, BLANC), (232, 64))
        pygame.draw.rect(self.ecran, (37, 48, 45), (350, 68, 165, 15), border_radius=7)
        if self.endurance > 0:
            pygame.draw.rect(
                self.ecran,
                (94, 202, 141),
                (350, 68, round(161 * max(0.0, min(100.0, self.endurance)) / 100), 15),
                border_radius=7,
            )
        pygame.draw.rect(self.ecran, (176, 222, 187), (350, 68, 165, 15), 1, border_radius=7)

        self.ecran.blit(self.police.render("Faim", True, BLANC), (27, 89))
        pygame.draw.rect(self.ecran, (67, 59, 43), (82, 94, 168, 12), border_radius=5)
        pygame.draw.rect(
            self.ecran,
            (226, 171, 70),
            (82, 94, round(168 * max(0, min(100, self.faim)) / 100), 12),
            border_radius=5,
        )
        self.ecran.blit(self.police_details.render(f"{self.faim}/100", True, (241, 219, 175)), (258, 91))
        quete = next((q for q in self.quetes if q["active"]), None)
        if quete:
            libelle = f"Quete : {quete['nom']} ({quete['progres']}/{quete['besoin']})"
            detail = quete["detail"]
        else:
            quete = next((q for q in self.quetes if not q["faite"]), None)
            libelle = f"Quete : parle a l'habitant. Prochaine : {quete['nom']}" if quete else "Toutes les quetes sont terminees !"
            detail = quete["detail"] if quete else "Explore jusqu'aux ruines et trouve la relique."
        self.ecran.blit(self.police.render(libelle[:55], True, (255, 226, 133)), (27, 115))
        self.ecran.blit(self.police.render(f"Objectif : {detail}", True, BLANC), (27, 138))
        self.ecran.blit(self.police_details.render("ZQSD bouger | Maj grimper | Ctrl discret | E agir", True, BLANC), (27, 163))
        self.ecran.blit(self.police_details.render("Espace attaquer | X esquive | C attaque speciale", True, (224, 220, 197)), (27, 184))
        self.ecran.blit(
            self.police_details.render(
                f"Echos secrets : {len(self.echos_decouverts)}/{len(ECHOS_HOMMAGES)}",
                True,
                (230, 190, 240),
            ),
            (27, 207),
        )
        if self.accroupi:
            dissimule = self.joueur_dissimule()
            texte_furtivite = "CAMOUFLE - les hautes herbes te cachent" if dissimule else "ACCROUPI - pas lents, detection reduite"
            couleur_furtivite = (155, 235, 164) if dissimule else (226, 214, 166)
            self.ecran.blit(self.police_details.render(texte_furtivite, True, couleur_furtivite), (27, 230))
        elif pygame.time.get_ticks() < self.message_jusqua:
            self.ecran.blit(self.police.render(self.message[:67], True, (165, 235, 241)), (27, 230))

        largeur_mini, hauteur_mini = self.mini_carte.get_size()
        mini_x, mini_y = LARGEUR_FENETRE - largeur_mini - 23, 18
        pygame.draw.rect(
            self.ecran,
            (23, 44, 38),
            (mini_x - 7, mini_y - 7, largeur_mini + 14, hauteur_mini + 14),
            border_radius=8,
        )
        facteur = self.facteur_mini_carte
        self.ecran.blit(self.mini_carte, (mini_x, mini_y))
        for ennemi in self.ennemis:
            pygame.draw.circle(self.ecran, (235, 75, 65), (round(mini_x + ennemi["x"] * facteur), round(mini_y + ennemi["y"] * facteur)), 2)
        for coffre in self.coffres:
            couleur_coffre = (100, 83, 61) if coffre["ouvert"] else (244, 190, 83)
            pygame.draw.circle(self.ecran, couleur_coffre, (round(mini_x + coffre["x"] * facteur), round(mini_y + coffre["y"] * facteur)), 2)
        for echo in (objet for objet in self.objets if objet["type"] == "echo"):
            pygame.draw.circle(
                self.ecran,
                echo["couleur"],
                (round(mini_x + echo["x"] * facteur), round(mini_y + echo["y"] * facteur)),
                3,
            )
        for objet in (objet for objet in self.objets if objet["type"] == "arme"):
            pygame.draw.circle(
                self.ecran,
                ARMES[objet["arme"]]["couleur"],
                (round(mini_x + objet["x"] * facteur), round(mini_y + objet["y"] * facteur)),
                3,
            )
        pygame.draw.circle(self.ecran, (255, 224, 85), (round(mini_x + RELIQUE_X * facteur), round(mini_y + RELIQUE_Y * facteur)), 3)
        pygame.draw.circle(self.ecran, (255, 255, 255), (round(mini_x + self.joueur_x * facteur), round(mini_y + self.joueur_y * facteur)), 3)
        for village in self.villages:
            pygame.draw.circle(self.ecran, (250, 207, 115), (round(mini_x + village["x"] * facteur), round(mini_y + village["y"] * facteur)), 2)
        for grotte in self.grottes if not self.dans_grotte else ():
            pygame.draw.circle(self.ecran, (40, 35, 38), (round(mini_x + grotte["x"] * facteur), round(mini_y + grotte["y"] * facteur)), 3)
        for repaire in self.repaire_monstres if not self.dans_grotte else ():
            couleur = (104, 192, 116) if repaire["conquis"] else (227, 78, 66)
            pygame.draw.circle(self.ecran, couleur, (round(mini_x + (repaire["x"] + 0.5) * facteur), round(mini_y + (repaire["y"] + 0.5) * facteur)), 3)

    def projeter_camera(self, x, y, hauteur=0.0):
        """Projette une position du monde en perspective depuis la camera."""
        cle = (x, y, hauteur)
        if cle in self._projection_cache:
            return self._projection_cache[cle]
        if not self.dans_grotte and hauteur == 0.0:
            hauteur = self.altitude_at(x, y)
        avant_x, avant_y = math.cos(self.camera_yaw), math.sin(self.camera_yaw)
        cote_x, cote_y = -avant_y, avant_x
        camera_x = self.joueur_x - avant_x * 3.0
        camera_y = self.joueur_y - avant_y * 3.0
        relatif_x, relatif_y = x - camera_x, y - camera_y
        profondeur = relatif_x * avant_x + relatif_y * avant_y
        if profondeur <= 0.55:
            self._projection_cache[cle] = None
            return None
        lateral = relatif_x * cote_x + relatif_y * cote_y
        focale = 430.0
        horizon = 174.0
        echelle = focale / profondeur
        relief_visuel = 0.38
        projection = (
            round(LARGEUR_FENETRE / 2 + lateral * echelle),
            round(horizon + (2.65 + ((0 if self.dans_grotte else self.altitude_at(self.joueur_x, self.joueur_y)) - hauteur) * relief_visuel) * echelle),
            profondeur,
        )
        self._projection_cache[cle] = projection
        return projection

    def dessiner_brume_horizon(self):
        """Adoucit les silhouettes lointaines avec une brume propre au biome."""
        if self.dans_grotte:
            return
        biome = biome_region(self.joueur_x, self.joueur_y)
        ambiance = "montagnes" if biome == "neige" else biome
        self.ecran.blit(self.brume_horizon[ambiance], (0, 205))

    def actualiser_ambiance(self):
        self.phase_journee = (pygame.time.get_ticks() % CYCLE_JOUR_MS / CYCLE_JOUR_MS + 0.5) % 1.0
        angle = self.phase_journee * math.tau - math.pi / 2
        self.elevation_soleil = math.sin(angle)
        self.lumiere_jour = max(0.0, min(1.0, (self.elevation_soleil + 0.12) / 0.42))
        self.lumiere_crepuscule = max(0.0, 1.0 - abs(self.elevation_soleil) / 0.35)

    def dessiner_ciel(self):
        if self.dans_grotte:
            self.ecran.fill((31, 31, 38))
            pygame.draw.polygon(self.ecran, (51, 48, 53), [(0, 0), (1000, 0), (1000, 200), (850, 178), (700, 205), (520, 172), (350, 201), (180, 175), (0, 207)])
            for x, hauteur in ((90, 37), (225, 23), (410, 42), (625, 28), (870, 45)):
                pygame.draw.polygon(self.ecran, (76, 70, 69), [(x - 12, 0), (x + 11, 0), (x + 5, hauteur), (x, hauteur + 11), (x - 5, hauteur)])
            pygame.draw.circle(self.ecran, (233, 184, 108), (790, 192), 22)
            pygame.draw.circle(self.ecran, (252, 215, 147), (790, 192), 12)
            return

        def melanger(couleur_a, couleur_b, facteur):
            return tuple(round(a + (b - a) * facteur) for a, b in zip(couleur_a, couleur_b))

        bandes = 120
        nuit = ((9, 18, 38), (23, 38, 65), (76, 76, 91))
        jour = ((48, 105, 151), (111, 169, 197), (207, 211, 181))
        crepuscule = ((75, 93, 133), (204, 126, 103), (245, 177, 118))
        couleurs = tuple(
            melanger(melanger(couleur_nuit, couleur_jour, self.lumiere_jour), couleur_crepuscule, self.lumiere_crepuscule * 0.85)
            for couleur_nuit, couleur_jour, couleur_crepuscule in zip(nuit, jour, crepuscule)
        )
        for index in range(bandes):
            progression = index / (bandes - 1)
            if progression < 0.7:
                debut, fin = couleurs[0], couleurs[1]
                melange = progression / 0.7
            else:
                debut, fin = couleurs[1], couleurs[2]
                melange = (progression - 0.7) / 0.3
            couleur = tuple(round(a + (b - a) * melange) for a, b in zip(debut, fin))
            y = index * 300 // bandes
            hauteur_bande = (index + 1) * 300 // bandes - y
            pygame.draw.rect(self.ecran, couleur, (0, y, LARGEUR_FENETRE, hauteur_bande))
        temps = pygame.time.get_ticks() / 1000
        angle = self.phase_journee * math.tau - math.pi / 2
        soleil_x = round(LARGEUR_FENETRE / 2 + math.cos(angle) * 430)
        soleil_y = round(238 - max(0.0, self.elevation_soleil) * 170)
        visibilite_soleil = max(0.0, min(1.0, (self.elevation_soleil + 0.08) / 0.18))
        if visibilite_soleil:
            couleur_soleil = melanger((255, 183, 123), (255, 246, 218), self.lumiere_jour)
            self.lueur_soleil.set_alpha(round(220 * visibilite_soleil))
            self.ecran.blit(self.lueur_soleil, (soleil_x - 110, soleil_y - 110))
            pygame.draw.circle(self.ecran, couleur_soleil, (soleil_x, soleil_y), 39)
            pygame.draw.circle(self.ecran, (255, 246, 218), (soleil_x - 4, soleil_y - 4), 25)

        if self.elevation_soleil < 0:
            lune_x = LARGEUR_FENETRE - soleil_x
            lune_y = round(238 + self.elevation_soleil * 130)
            if 0 < lune_y < 250:
                pygame.draw.circle(self.ecran, (222, 229, 220), (lune_x, lune_y), 21)
                pygame.draw.circle(self.ecran, couleurs[0], (lune_x + 9, lune_y - 5), 18)

        visibilite_etoiles = max(0.0, min(1.0, (-self.elevation_soleil - 0.04) / 0.5))
        if visibilite_etoiles:
            for index in range(48):
                x = (index * 197 + 31) % LARGEUR_FENETRE
                y = (index * 73 + 19) % 185
                scintillement = 0.65 + 0.35 * math.sin(temps * 1.7 + index * 2.3)
                intensite = visibilite_etoiles * scintillement
                couleur = (round(98 * intensite), round(139 * intensite), round(190 * intensite))
                rayon = 2 if index % 11 == 0 and intensite > 0.55 else 1
                pygame.draw.circle(self.ecran, couleur, (x, y), rayon)
                if rayon == 2:
                    pygame.draw.line(self.ecran, couleur, (x - 3, y), (x + 3, y), 1)
                    pygame.draw.line(self.ecran, couleur, (x, y - 3), (x, y + 3), 1)

        pygame.draw.rect(self.ecran, (78, 132, 80), (0, 300, LARGEUR_FENETRE, HAUTEUR_FENETRE - 300))
        for index, (couleur, base, amplitude, pas) in enumerate((
            ((156, 183, 184), 222, 37, 59),
            ((129, 162, 166), 238, 44, 43),
        )):
            sommets = [(-20, 320)]
            for x in range(-20, LARGEUR_FENETRE + 40, pas):
                vague = (
                    math.sin((x + index * 89) / 137 + temps * 0.018) * 0.62
                    + math.sin((x - index * 53) / 72) * 0.25
                )
                pic = base - vague * amplitude
                sommets.append((x, round(pic)))
                sommets.append((x + pas // 2, round(pic - amplitude * 0.11)))
            sommets.extend(((LARGEUR_FENETRE + 20, 340), (-20, 340)))
            pygame.draw.polygon(self.ecran, couleur, sommets)
        for index, (couleur, base, amplitude, pas) in enumerate((
            ((113, 151, 157), 231, 57, 45),
            ((80, 123, 132), 252, 75, 34),
            ((56, 94, 99), 283, 93, 25),
        )):
            sommets = [(-20, 320)]
            for x in range(-20, LARGEUR_FENETRE + 40, pas):
                vague = (
                    math.sin((x + index * 118) / 151 + temps * 0.018) * 0.48
                    + math.sin((x - index * 71) / 67) * 0.22
                    + math.sin(x / 33 + index) * 0.08
                )
                pic = base - vague * amplitude
                sommets.append((x, round(pic)))
                sommets.append((x + pas // 2, round(pic - amplitude * 0.16)))
            sommets.extend(((LARGEUR_FENETRE + 20, 340), (-20, 340)))
            pygame.draw.polygon(self.ecran, couleur, sommets)
        for index in range(4):
            x = (index * 293 + round(temps * (5 + index))) % (LARGEUR_FENETRE + 180) - 90
            y = 72 + (index * 47) % 94
            couleur_nuage = melanger((79, 93, 116), (229, 237, 231), self.lumiere_jour)
            couleur_nuage = melanger(couleur_nuage, (244, 171, 134), self.lumiere_crepuscule * 0.65)
            ombre_nuage = melanger((42, 53, 74), (177, 201, 207), self.lumiere_jour)
            pygame.draw.ellipse(self.ecran, ombre_nuage, (x + 4, y + 4, 92, 15))
            pygame.draw.ellipse(self.ecran, couleur_nuage, (x, y, 85, 13))
            pygame.draw.ellipse(self.ecran, couleur_nuage, (x + 14, y - 7, 35, 20))
            pygame.draw.ellipse(self.ecran, couleur_nuage, (x + 43, y - 3, 34, 16))
        self.dessiner_oiseaux(temps)

    def dessiner_oiseaux(self, temps):
        """Anime de petits vols d'oiseaux en silhouette au-dessus des montagnes."""
        vols = ((-65, 96, 12, 4, 0.82), (218, 139, 9, 3, 0.58), (603, 178, 7, 2, 0.43))
        for vol_index, (depart_x, hauteur, ecart, nombre, echelle) in enumerate(vols):
            x_vol = (depart_x + temps * (13 + vol_index * 3)) % (LARGEUR_FENETRE + 180) - 90
            for oiseau in range(nombre):
                phase = temps * 8.5 + oiseau * 1.35 + vol_index * 2.2
                battement = math.sin(phase)
                x = round(x_vol + oiseau * ecart)
                y = round(hauteur + math.sin(phase * 0.38) * 3 + oiseau * 2)
                envergure = max(3, round(8 * echelle))
                couleur = (67, 88, 91) if vol_index == 0 else (78, 98, 99)
                ombre = (45, 65, 69)
                corps = pygame.Rect(
                    x - max(1, round(2 * echelle)),
                    y - max(1, round(echelle)),
                    max(3, round(5 * echelle)),
                    max(2, round(2 * echelle)),
                )
                pygame.draw.ellipse(self.ecran, ombre, corps.move(0, 1))
                pygame.draw.ellipse(self.ecran, couleur, corps)
                for cote in (-1, 1):
                    bout_x = x + cote * envergure
                    bout_y = round(y - battement * 4 * echelle + abs(cote) * echelle)
                    milieu_x = x + round(cote * envergure * 0.48)
                    milieu_y = round(y - battement * 1.8 * echelle - 1)
                    aile = [
                        (x, y),
                        (milieu_x, milieu_y),
                        (bout_x, bout_y),
                        (x + round(cote * envergure * 0.62), y + round(2 * echelle)),
                    ]
                    pygame.draw.polygon(self.ecran, couleur, aile)
                bec = (x + round(4 * echelle), y)
                pygame.draw.line(
                    self.ecran,
                    couleur,
                    (x + round(2 * echelle), y),
                    bec,
                    1,
                )

    def dessiner_meteo(self, maintenant):
        if self.dans_grotte or self.meteo == "clair":
            return
        secondes = maintenant / 1000
        if self.meteo in ("pluie", "orage"):
            nombre = 110 if self.meteo == "orage" else 72
            couleur = (139, 171, 190) if self.meteo == "orage" else (154, 186, 198)
            for index in range(nombre):
                x = (index * 173 - round(secondes * 250)) % LARGEUR_FENETRE
                y = (index * 97 + round(secondes * 520)) % HAUTEUR_FENETRE
                longueur = 13 if self.meteo == "orage" else 9
                pygame.draw.line(self.ecran, couleur, (x, y), (x - 3, y + longueur), 1)
            if self.meteo == "orage":
                self.ecran.blit(self.voile_orage, (0, 0))
        elif self.meteo == "neige":
            for index in range(65):
                x = (index * 137 + round(math.sin(secondes + index) * 18)) % LARGEUR_FENETRE
                y = (index * 83 + round(secondes * 65)) % HAUTEUR_FENETRE
                rayon = 1 if index % 4 else 2
                pygame.draw.circle(self.ecran, (223, 236, 241), (x, y), rayon)
        elif self.meteo == "vent":
            for index in range(18):
                x = (index * 89 + round(secondes * 125)) % LARGEUR_FENETRE
                y = (index * 47 + round(math.sin(secondes * 1.6 + index) * 11)) % HAUTEUR_FENETRE
                pygame.draw.ellipse(self.ecran, (183, 173, 121), (x, y, 5, 2))

    def dessiner_terrain_perspective(self):
        couleurs = {
            "prairie": (92, 151, 79),
            "foret": (54, 111, 65),
            "desert": (194, 160, 101),
            "neige": (178, 205, 211),
            "chemin": (143, 113, 76),
            "eau": (48, 117, 153),
            "grotte": (78, 73, 73),
        }
        hauteur_carte, largeur_carte = len(self.carte), len(self.carte[0])
        x_debut, x_fin = max(0, int(self.joueur_x) - 22), min(largeur_carte, int(self.joueur_x) + 23)
        y_debut, y_fin = max(0, int(self.joueur_y) - 22), min(hauteur_carte, int(self.joueur_y) + 23)
        if self.dans_grotte:
            atmosphere = (110, 105, 112)
        else:
            biome = biome_region(self.joueur_x, self.joueur_y)
            atmosphere = {
                "prairie": (151, 179, 181),
                "foret": (128, 164, 150),
                "desert": (190, 172, 139),
                "neige": (156, 183, 194),
            }[biome]
        cases = []
        for y in range(y_debut, y_fin):
            for x in range(x_debut, x_fin):
                centre = self.projeter_camera(x + 0.5, y + 0.5)
                if centre and 0.5 < centre[2] < 28 and -180 < centre[0] < LARGEUR_FENETRE + 180:
                    cases.append((centre[2], x, y))

        for profondeur, x, y in sorted(cases, reverse=True):
            coins = (
                self.projeter_camera(x, y),
                self.projeter_camera(x + 1, y),
                self.projeter_camera(x + 1, y + 1),
                self.projeter_camera(x, y + 1),
            )
            if any(coin is None for coin in coins):
                continue
            points = [(coin[0], coin[1]) for coin in coins]
            if max(point[1] for point in points) < 255 or min(point[1] for point in points) > HAUTEUR_FENETRE + 70:
                continue
            terrain = self.carte[y][x]
            brume = min(0.34, max(0.0, (profondeur - 6) / 55))
            coins_altitude = (
                self.altitude_at(x, y),
                self.altitude_at(x + 1, y),
                self.altitude_at(x + 1, y + 1),
                self.altitude_at(x, y + 1),
            ) if not self.dans_grotte else (0, 0, 0, 0)
            pente_x = pente_y = 0.0
            if not self.dans_grotte and terrain not in ("eau", "grotte"):
                centre_x, centre_y = x + 0.5, y + 0.5
                pente_x = self.altitude_at(centre_x + 0.35, centre_y) - self.altitude_at(centre_x - 0.35, centre_y)
                pente_y = self.altitude_at(centre_x, centre_y + 0.35) - self.altitude_at(centre_x, centre_y - 0.35)
            eclairage_terrain = round(max(-10, min(10, (-pente_x * 0.55 - pente_y * 0.7) * 7)))
            subdivisions = 2 if profondeur < 7 or max(coins_altitude) > 0.3 and profondeur < 8 else 1
            for sy_index in range(subdivisions):
                for sx_index in range(subdivisions):
                    gauche, droite = x + sx_index / subdivisions, x + (sx_index + 1) / subdivisions
                    haut, bas = y + sy_index / subdivisions, y + (sy_index + 1) / subdivisions
                    sous_centre = self.altitude_at((gauche + droite) / 2, (haut + bas) / 2) if not self.dans_grotte else 0
                    sous_coins = (
                        self.projeter_camera(gauche, haut),
                        self.projeter_camera(droite, haut),
                        self.projeter_camera(droite, bas),
                        self.projeter_camera(gauche, bas),
                    )
                    if any(coin is None for coin in sous_coins):
                        continue
                    base = couleurs[terrain]
                    if terrain not in ("eau", "grotte"):
                        nuance = NUANCES_SAISONS[self.saison]
                        base = tuple(max(0, min(255, canal + nuance[index])) for index, canal in enumerate(base))
                    graine = (x * 73856093 + y * 19349663 + sx_index * 83492791 + sy_index * 2971215073) & 0xFFFFFFFF
                    variation = (graine % 9) - 4
                    if sous_centre > 0.45:
                        roche = (125, 128, 124)
                        neige_sommet = (222, 231, 229)
                        melange_roche = min(1.0, (sous_centre - 0.45) / 1.8)
                        base = tuple(round(a + (b - a) * melange_roche) for a, b in zip(base, roche))
                        melange_neige = min(0.9, max(0.0, (sous_centre - 2.1) / 2.3))
                        base = tuple(round(a + (b - a) * melange_neige) for a, b in zip(base, neige_sommet))
                        variation += round(sous_centre * 1.2)
                    variation += eclairage_terrain
                    couleur = tuple(
                        max(0, min(255, round(composante + variation + (atmosphere - composante) * brume)))
                        for composante, atmosphere in zip(base, atmosphere)
                    )
                    points_sous_case = [(coin[0], coin[1]) for coin in sous_coins]
                    pygame.draw.polygon(self.ecran, couleur, points_sous_case)
                    if terrain not in ("eau", "grotte") and (graine >> 3) % 2:
                        eclaircie = tuple(min(255, canal + 5) for canal in couleur)
                        pygame.draw.polygon(
                            self.ecran,
                            eclaircie,
                            [points_sous_case[index] for index in (0, 1, 2)],
                        )
            if profondeur < 9 and terrain != "grotte":
                echelle = 430 / max(1, profondeur)
                for graine in range(3):
                    graine_valeur = (x * 73856093 + y * 19349663 + graine * 83492791) & 0xFFFFFFFF
                    u = 0.12 + ((graine_valeur & 0xFFFF) / 65535) * 0.76
                    v = 0.12 + (((graine_valeur >> 16) & 0xFFFF) / 65535) * 0.76
                    px = x + u
                    py = y + v
                    point = self.projeter_camera(px, py)
                    if point is None:
                        continue
                    sx, sy, _ = point
                    longueur = max(1, round(min(5, echelle * 0.045)))
                    if terrain in ("prairie", "foret"):
                        teinte = ((59, 105, 54), (143, 171, 91), (105, 143, 68))[graine]
                        pygame.draw.line(self.ecran, teinte, (sx, sy), (sx - longueur, sy - max(1, longueur * 2)), max(1, round(echelle * 0.008)))
                        if graine == 1 and longueur > 1:
                            pygame.draw.line(self.ecran, (168, 185, 112), (sx, sy), (sx + longueur, sy - max(1, longueur)), 1)
                    elif terrain == "desert":
                        teinte = (160, 126, 80) if graine % 2 == 0 else (213, 184, 132)
                        pygame.draw.ellipse(self.ecran, teinte, (sx, sy, longueur * 2, max(1, longueur // 2)))
                        if graine == 0:
                            pygame.draw.line(self.ecran, (226, 197, 142), (sx - longueur, sy - 1), (sx + longueur, sy - 2), 1)
                    elif terrain == "neige":
                        pygame.draw.line(self.ecran, (230, 240, 239), (sx - longueur, sy), (sx + longueur, sy - max(1, longueur // 2)), 1)
                    else:
                        pygame.draw.circle(self.ecran, (107, 105, 101), (sx, sy), max(1, round(echelle * 0.01)))
            if terrain == "eau":
                centre_x = sum(point[0] for point in points) // 4
                centre_y = sum(point[1] for point in points) // 4
                phase = math.sin(pygame.time.get_ticks() / 450 + x * 1.7 + y) * 4
                if (x * 3 + y) % 3 == 0:
                    pygame.draw.line(self.ecran, (142, 199, 208), (centre_x - 7, centre_y), (centre_x + 7, round(centre_y - 2 + phase)), 2)
                if (x * 5 + y) % 7 == 0:
                    pygame.draw.line(self.ecran, (194, 222, 216), (centre_x - 3, centre_y + 4), (centre_x + 5, centre_y + 3), 1)

    def dessiner_feu_camp(self, sx, sy, echelle, maintenant):
        facteur = max(0.35, echelle)
        taille = lambda valeur: max(1, round(valeur * facteur))
        phase = maintenant / 125
        pygame.draw.ellipse(self.ecran, (57, 42, 34), (sx - taille(18), sy - taille(3), taille(36), taille(10)))
        for index in range(8):
            angle = math.tau * index / 8
            pierre_x = sx + round(math.cos(angle) * taille(13))
            pierre_y = sy + round(math.sin(angle) * taille(4))
            pygame.draw.ellipse(
                self.ecran,
                (108, 106, 94) if index % 2 else (151, 144, 122),
                (pierre_x - taille(3), pierre_y - taille(2), taille(6), taille(4)),
            )
        pygame.draw.line(self.ecran, (89, 55, 34), (sx - taille(8), sy - taille(3)), (sx + taille(7), sy - taille(7)), taille(3))
        pygame.draw.line(self.ecran, (123, 79, 44), (sx - taille(7), sy - taille(7)), (sx + taille(8), sy - taille(3)), taille(3))
        vacillement = round(math.sin(phase) * taille(2))
        pygame.draw.polygon(
            self.ecran,
            (224, 75, 34),
            [(sx - taille(7), sy - taille(4)), (sx - taille(4) + vacillement, sy - taille(16)), (sx, sy - taille(7)), (sx + taille(4), sy - taille(18) + vacillement), (sx + taille(8), sy - taille(4))],
        )
        pygame.draw.polygon(
            self.ecran,
            (255, 178, 54),
            [(sx - taille(4), sy - taille(4)), (sx - taille(2), sy - taille(12) + vacillement), (sx + taille(1), sy - taille(6)), (sx + taille(4), sy - taille(13)), (sx + taille(5), sy - taille(4))],
        )
        pygame.draw.ellipse(self.ecran, (255, 229, 130), (sx - taille(2), sy - taille(7), taille(4), taille(3)))
        for index in range(3):
            etincelle_x = sx + round(math.sin(phase + index * 2.1) * taille(9))
            etincelle_y = sy - taille(17 + (index * 7 + maintenant // 180) % 11)
            pygame.draw.circle(self.ecran, (255, 205, 93), (etincelle_x, etincelle_y), max(1, taille(1)))

    def dessiner_monstre_perspective(self, sx, sy, echelle, ennemi, maintenant):
        taille = max(3, round(14 * echelle))
        profil = MONSTRES[ennemi["type"]]
        teinte = profil["couleur"]
        ombre = tuple(max(0, canal - 45) for canal in teinte)
        facteur = max(0.35, echelle)
        p = lambda x, y: (sx + round(x * facteur), sy + round(y * facteur))

        if ennemi["type"] == "araignee":
            balancement = round(math.sin(maintenant / 150 + ennemi["x"]) * 2 * facteur)
            for cote in (-1, 1):
                for index in range(4):
                    depart = p(cote * 5, -9 + index * 3)
                    coude = p(cote * (11 + index * 2), -15 + index * 5 + balancement)
                    pied = p(cote * (16 + index * 2), -7 + index * 4)
                    pygame.draw.line(self.ecran, ombre, depart, coude, max(1, round(2 * facteur)))
                    pygame.draw.line(self.ecran, teinte, coude, pied, max(1, round(2 * facteur)))
            pygame.draw.ellipse(self.ecran, ombre, (sx - taille, sy - round(20 * facteur), taille * 2, round(17 * facteur)))
            pygame.draw.ellipse(self.ecran, teinte, (sx - round(taille * 0.7), sy - round(18 * facteur), round(taille * 1.4), round(13 * facteur)))
            for cote in (-1, 1):
                pygame.draw.circle(self.ecran, (245, 82, 61), p(cote * 3, -14), max(1, round(2 * facteur)))
        elif ennemi["type"] == "chauve_souris":
            battement = math.sin(maintenant / 95 + ennemi["x"]) * 8 * facteur
            pygame.draw.polygon(self.ecran, ombre, [p(-2, -15), p(-18, -23 - battement), p(-14, -11), p(-8, -7), p(0, -9)])
            pygame.draw.polygon(self.ecran, ombre, [p(2, -15), p(18, -23 - battement), p(14, -11), p(8, -7), p(0, -9)])
            pygame.draw.line(self.ecran, (174, 147, 179), p(-3, -13), p(-15, -21 - battement), max(1, round(facteur)))
            pygame.draw.line(self.ecran, (174, 147, 179), p(3, -13), p(15, -21 - battement), max(1, round(facteur)))
            pygame.draw.ellipse(self.ecran, ombre, (sx - round(5 * facteur), sy - round(20 * facteur), round(10 * facteur), round(14 * facteur)))
            pygame.draw.polygon(self.ecran, teinte, [p(-4, -17), p(-5, -25), p(-1, -20)])
            pygame.draw.polygon(self.ecran, teinte, [p(4, -17), p(5, -25), p(1, -20)])
            pygame.draw.circle(self.ecran, (255, 94, 66), p(-2, -16), max(1, round(facteur)))
            pygame.draw.circle(self.ecran, (255, 94, 66), p(2, -16), max(1, round(facteur)))
        elif ennemi["type"] in ("pillard", "gobelin"):
            balancement = round(math.sin(maintenant / 170 + ennemi["x"]) * 2 * facteur)
            pygame.draw.ellipse(self.ecran, (47, 42, 37), (sx - round(10 * facteur), sy - round(3 * facteur), round(8 * facteur), round(4 * facteur)))
            pygame.draw.ellipse(self.ecran, (47, 42, 37), (sx + round(2 * facteur), sy - round(3 * facteur), round(8 * facteur), round(4 * facteur)))
            pygame.draw.line(self.ecran, ombre, p(-5, -8), p(-6 + balancement, -1), max(1, round(4 * facteur)))
            pygame.draw.line(self.ecran, ombre, p(5, -8), p(6 - balancement, -1), max(1, round(4 * facteur)))
            pygame.draw.ellipse(self.ecran, ombre, (sx - round(10 * facteur), sy - round(23 * facteur), round(20 * facteur), round(18 * facteur)))
            pygame.draw.ellipse(self.ecran, teinte, (sx - round(8 * facteur), sy - round(22 * facteur), round(16 * facteur), round(15 * facteur)))
            pygame.draw.polygon(self.ecran, teinte, [p(-7, -19), p(-13, -27), p(-4, -24)])
            pygame.draw.polygon(self.ecran, teinte, [p(7, -19), p(13, -27), p(4, -24)])
            pygame.draw.ellipse(self.ecran, teinte, (sx - round(9 * facteur), sy - round(34 * facteur), round(18 * facteur), round(16 * facteur)))
            pygame.draw.ellipse(self.ecran, tuple(min(255, canal + 27) for canal in teinte), (sx - round(7 * facteur), sy - round(32 * facteur), round(14 * facteur), round(10 * facteur)))
            pygame.draw.ellipse(self.ecran, (118, 70, 52), (sx - round(5 * facteur), sy - round(25 * facteur), round(10 * facteur), round(6 * facteur)))
            pygame.draw.circle(self.ecran, (255, 224, 111), p(-4, -29), max(1, round(2 * facteur)))
            pygame.draw.circle(self.ecran, (255, 224, 111), p(4, -29), max(1, round(2 * facteur)))
            pygame.draw.circle(self.ecran, (35, 30, 29), p(-4, -29), max(1, round(facteur)))
            pygame.draw.circle(self.ecran, (35, 30, 29), p(4, -29), max(1, round(facteur)))
            pygame.draw.polygon(self.ecran, (238, 226, 190), [p(-5, -24), p(-4, -20), p(-2, -24)])
            pygame.draw.polygon(self.ecran, (238, 226, 190), [p(5, -24), p(4, -20), p(2, -24)])
            pygame.draw.line(self.ecran, (94, 59, 44), p(-8, -15), p(8, -12), max(1, round(2 * facteur)))
            if ennemi["type"] == "pillard":
                pygame.draw.rect(self.ecran, (87, 64, 47), (sx - round(8 * facteur), sy - round(19 * facteur), round(16 * facteur), max(1, round(3 * facteur))))
                pygame.draw.line(self.ecran, (128, 83, 47), p(11, -20), p(15, -2), max(1, round(2 * facteur)))
                pygame.draw.polygon(self.ecran, (178, 180, 157), [p(12, -20), p(17, -24), p(16, -17)])
                pygame.draw.line(self.ecran, (198, 103, 67), p(-5, -12), p(6, -10), max(1, round(3 * facteur)))
        elif ennemi["type"] == "loup":
            pygame.draw.ellipse(self.ecran, teinte, (sx - round(15 * facteur), sy - round(21 * facteur), round(29 * facteur), round(16 * facteur)))
            pygame.draw.ellipse(self.ecran, tuple(min(255, canal + 28) for canal in teinte), (sx + round(4 * facteur), sy - round(19 * facteur), round(12 * facteur), round(9 * facteur)))
            pygame.draw.polygon(self.ecran, teinte, [p(-11, -17), p(-10, -30), p(-2, -19)])
            pygame.draw.polygon(self.ecran, teinte, [p(-3, -18), p(2, -29), p(5, -17)])
            pygame.draw.circle(self.ecran, (255, 208, 91), p(10, -15), max(1, round(2 * facteur)))
            pygame.draw.line(self.ecran, ombre, p(-9, -8), p(-12, -2), max(1, round(3 * facteur)))
            pygame.draw.line(self.ecran, ombre, p(7, -8), p(9, -2), max(1, round(3 * facteur)))
        else:
            pygame.draw.ellipse(self.ecran, (36, 46, 40), (sx - taille, sy - round(4 * facteur), taille * 2, max(2, round(5 * facteur))))
            pygame.draw.ellipse(self.ecran, teinte, (sx - taille, sy - taille * 2, taille * 2, taille * 2))
            pygame.draw.circle(self.ecran, (255, 221, 102), p(4, -18), max(1, round(2 * facteur)))
            pygame.draw.circle(self.ecran, (38, 32, 28), p(4, -18), max(1, round(facteur)))

        if ennemi["vies_max"] > 1:
            largeur = max(3, round(24 * facteur))
            hauteur = max(2, round(3 * facteur))
            barre_x = sx - largeur // 2
            barre_y = sy - round(39 * facteur)
            pygame.draw.rect(self.ecran, (57, 34, 35), (barre_x, barre_y, largeur, hauteur))
            pygame.draw.rect(self.ecran, (219, 65, 61), (barre_x, barre_y, max(1, round(largeur * ennemi["vies"] / ennemi["vies_max"])), hauteur))

    def dessiner_alerte_ennemi(self, sx, sy, echelle, ennemi, maintenant):
        charge_du_loup = ennemi["type"] == "loup" and ennemi.get("attaque_charge", 0) > maintenant
        if ennemi.get("alerte_jusqua", 0) > maintenant or charge_du_loup:
            centre = (sx, sy - round(65 * echelle))
            fond = (123, 44, 35) if charge_du_loup else (43, 37, 34)
            couleur = (255, 114, 75) if charge_du_loup else (249, 208, 75)
            texte = (255, 245, 226) if charge_du_loup else (111, 44, 31)
            pygame.draw.circle(self.ecran, fond, centre, max(5, round(8 * echelle)))
            pygame.draw.circle(self.ecran, couleur, centre, max(4, round(7 * echelle)))
            alerte = self.police.render("!", True, texte)
            self.ecran.blit(alerte, alerte.get_rect(center=centre))

    def dessiner_echo_perspective(self, sx, sy, echelle, echo, maintenant):
        """Dessine un petit autel et un symbole original pour chaque echo."""
        largeur = max(5, round(22 * echelle))
        hauteur = max(3, round(8 * echelle))
        pygame.draw.ellipse(
            self.ecran,
            (48, 45, 54),
            (sx - largeur // 2, sy - hauteur // 2, largeur, hauteur),
        )
        pygame.draw.polygon(
            self.ecran,
            (112, 100, 87),
            [(sx - largeur // 2, sy), (sx, sy - hauteur), (sx + largeur // 2, sy), (sx, sy + hauteur)],
        )
        hauteur_echo = round((14 + math.sin(maintenant / 260 + sx) * 2) * echelle)
        centre = (sx, sy - hauteur_echo)
        taille = max(2, round(5 * echelle))
        couleur = echo["couleur"]
        clair = tuple(min(255, canal + 50) for canal in couleur)
        pygame.draw.circle(self.ecran, couleur, centre, taille + max(1, round(echelle)))
        pygame.draw.circle(self.ecran, (247, 237, 209), centre, taille, max(1, round(echelle)))
        symbole = echo["symbole"]
        if symbole in ("boussole", "etoile"):
            pointe = taille - max(1, round(echelle))
            pygame.draw.polygon(
                self.ecran,
                clair,
                [
                    (centre[0], centre[1] - pointe),
                    (centre[0] + max(1, pointe // 3), centre[1]),
                    (centre[0], centre[1] + pointe),
                    (centre[0] - max(1, pointe // 3), centre[1]),
                ],
            )
            pygame.draw.polygon(
                self.ecran,
                couleur,
                [
                    (centre[0] - pointe, centre[1]),
                    (centre[0], centre[1] - max(1, pointe // 3)),
                    (centre[0] + pointe, centre[1]),
                    (centre[0], centre[1] + max(1, pointe // 3)),
                ],
            )
        elif symbole == "poing":
            pygame.draw.rect(
                self.ecran,
                clair,
                (centre[0] - taille // 2, centre[1] - taille // 3, taille, max(2, taille // 2)),
                border_radius=max(1, taille // 4),
            )
            for doigt in range(3):
                x = centre[0] - taille // 2 + doigt * max(1, taille // 3)
                pygame.draw.line(self.ecran, clair, (x, centre[1] - taille // 3), (x, centre[1] - taille), max(1, round(echelle)))
        elif symbole == "guilde":
            pygame.draw.circle(self.ecran, clair, centre, taille - max(1, round(echelle)), max(1, round(echelle)))
            for offset_x, offset_y in ((-1, -1), (1, -1), (0, 1)):
                pygame.draw.circle(
                    self.ecran,
                    couleur,
                    (centre[0] + offset_x * max(1, taille // 2), centre[1] + offset_y * max(1, taille // 2)),
                    max(1, round(echelle)),
                )
        elif symbole == "cercle":
            pygame.draw.circle(self.ecran, clair, centre, taille - max(1, round(echelle)), max(1, round(echelle)))
            pygame.draw.polygon(
                self.ecran,
                couleur,
                [(centre[0], centre[1] - taille // 2), (centre[0] + taille // 2, centre[1] + taille // 2), (centre[0] - taille // 2, centre[1] + taille // 2)],
                max(1, round(echelle)),
            )
        else:
            pygame.draw.line(self.ecran, clair, (centre[0] - taille // 3, centre[1] - taille), (centre[0] + taille // 3, centre[1] - taille), max(1, round(echelle)))
            pygame.draw.line(self.ecran, clair, (centre[0] - taille // 3, centre[1] - taille), (centre[0] - taille // 2, centre[1] + taille // 2), max(1, round(echelle)))
            pygame.draw.line(self.ecran, clair, (centre[0] + taille // 3, centre[1] - taille), (centre[0] + taille // 2, centre[1] + taille // 2), max(1, round(echelle)))
            pygame.draw.line(self.ecran, couleur, (centre[0] - taille // 2, centre[1] + taille // 2), (centre[0] + taille // 2, centre[1] + taille // 2), max(1, round(echelle)))

    def dessiner_arme_au_sol(self, sx, sy, echelle, identifiant, maintenant):
        profil = ARMES[identifiant]
        couleur = profil["couleur"]
        forme = profil.get("forme", "epee")
        oscillation = round(math.sin(maintenant / 210 + sx) * 2 * echelle)
        depart = (sx - round(5 * echelle), sy - round((11 + oscillation) * echelle))
        if forme == "lance":
            pointe = (sx + round(7 * echelle), sy - round(34 * echelle))
            pygame.draw.line(self.ecran, (117, 83, 53), depart, pointe, max(1, round(2 * echelle)))
            pygame.draw.polygon(self.ecran, couleur, [
                pointe,
                (pointe[0] - round(4 * echelle), pointe[1] + round(7 * echelle)),
                (pointe[0] + round(4 * echelle), pointe[1] + round(7 * echelle)),
            ])
        elif forme in ("masse", "marteau"):
            manche = (sx + round(3 * echelle), sy - round(31 * echelle))
            pygame.draw.line(self.ecran, (117, 83, 53), depart, manche, max(1, round(3 * echelle)))
            pygame.draw.rect(
                self.ecran,
                couleur,
                (manche[0] - round(7 * echelle), manche[1] - round(4 * echelle), max(3, round(14 * echelle)), max(3, round(8 * echelle))),
                border_radius=max(1, round(2 * echelle)),
            )
        elif forme == "arbalete":
            pygame.draw.line(self.ecran, (117, 83, 53), (sx - round(10 * echelle), sy - round(23 * echelle)), (sx + round(10 * echelle), sy - round(23 * echelle)), max(1, round(3 * echelle)))
            pygame.draw.line(self.ecran, couleur, (sx, sy - round(28 * echelle)), (sx, sy - round(10 * echelle)), max(1, round(3 * echelle)))
            pygame.draw.line(self.ecran, (229, 218, 187), (sx - round(10 * echelle), sy - round(23 * echelle)), (sx + round(10 * echelle), sy - round(23 * echelle)), 1)
        else:
            longueur = 15 if forme == "dague" else 25
            pointe = (sx + round(6 * echelle), sy - round((longueur + oscillation) * echelle))
            garde = (sx, sy - round(8 * echelle))
            pygame.draw.line(self.ecran, (105, 72, 45), depart, garde, max(1, round(3 * echelle)))
            pygame.draw.line(self.ecran, (218, 190, 124), (sx - round(5 * echelle), garde[1]), (sx + round(5 * echelle), garde[1]), max(1, round(2 * echelle)))
            pygame.draw.polygon(self.ecran, couleur, [
                (sx - round(2 * echelle), garde[1]),
                (sx + round(2 * echelle), garde[1]),
                (pointe[0] + round(1 * echelle), pointe[1]),
                pointe,
            ])

    def dessiner_decor_perspective(self, sorte, x, y, profondeur, donnees=None):
        projection = self.projeter_camera(x, y)
        if projection is None:
            return
        sx, sy, profondeur = projection
        echelle = min(1.8, 4.2 / profondeur)
        if sy < 230 or sy > HAUTEUR_FENETRE + 50 or sx < -100 or sx > LARGEUR_FENETRE + 100:
            return
        largeur = max(2, round(18 * echelle))
        pygame.draw.ellipse(self.ecran, (38, 52, 40), (sx - largeur, sy - 2, largeur * 2, max(2, round(7 * echelle))))
        if sorte == "arbre":
            biome = biome_region(x, y)
            if biome == "neige":
                pygame.draw.rect(self.ecran, (82, 71, 61), (sx - max(1, round(4 * echelle)), sy - round(30 * echelle), max(2, round(8 * echelle)), round(31 * echelle)))
                pygame.draw.line(self.ecran, (149, 132, 110), (sx - round(2 * echelle), sy - round(28 * echelle)), (sx - round(2 * echelle), sy - round(4 * echelle)), max(1, round(echelle)))
                for niveau in range(3):
                    offset = round((niveau - 1) * 9 * echelle)
                    sommet = sy - round((70 - niveau * 17) * echelle)
                    largeur_pointe = round((13 + niveau * 3) * echelle)
                    base_y = sy - round((34 - niveau * 13) * echelle)
                    silhouette = [
                        (sx + offset, sommet),
                        (sx + offset - largeur_pointe, base_y),
                        (sx + offset + largeur_pointe, base_y),
                    ]
                    pygame.draw.polygon(self.ecran, (29, 66, 64), [(px + round(2 * echelle), py + round(2 * echelle)) for px, py in silhouette])
                    pygame.draw.polygon(self.ecran, (44 + niveau * 6, 96 + niveau * 5, 87 + niveau * 3), silhouette)
                    pygame.draw.polygon(
                        self.ecran,
                        (73 + niveau * 5, 126 + niveau * 4, 111 + niveau * 3),
                        [
                            (sx + offset, sommet + round(5 * echelle)),
                            (sx + offset - round(largeur_pointe * 0.48), base_y),
                            (sx + offset - round(largeur_pointe * 0.12), base_y),
                        ],
                    )
                    pygame.draw.line(self.ecran, (221, 235, 225), (sx + offset, sommet + round(4 * echelle)), (sx + offset - round(largeur_pointe * 0.48), base_y - round(2 * echelle)), max(1, round(echelle * 1.5)))
            elif biome == "desert":
                cactus = (sx, sy - round(62 * echelle))
                pygame.draw.line(self.ecran, (45, 86, 57), (sx - round(10 * echelle), sy - round(8 * echelle)), (sx - round(10 * echelle), sy - round(30 * echelle)), max(2, round(8 * echelle)))
                pygame.draw.line(self.ecran, (45, 86, 57), (sx - round(10 * echelle), sy - round(30 * echelle)), (sx - round(4 * echelle), sy - round(30 * echelle)), max(2, round(7 * echelle)))
                pygame.draw.line(self.ecran, (45, 86, 57), (sx + round(10 * echelle), sy - round(8 * echelle)), (sx + round(10 * echelle), sy - round(24 * echelle)), max(2, round(8 * echelle)))
                pygame.draw.line(self.ecran, (45, 86, 57), (sx + round(10 * echelle), sy - round(24 * echelle)), (sx + round(4 * echelle), sy - round(24 * echelle)), max(2, round(7 * echelle)))
                pygame.draw.polygon(self.ecran, (73, 119, 75), [(sx, cactus[1]), (sx - round(12 * echelle), sy - round(30 * echelle)), (sx - round(7 * echelle), sy - round(6 * echelle)), (sx + round(8 * echelle), sy - round(6 * echelle)), (sx + round(13 * echelle), sy - round(31 * echelle))])
                pygame.draw.line(self.ecran, (196, 190, 145), (sx, sy - round(47 * echelle)), (sx, sy - round(11 * echelle)), max(1, round(echelle)))
                for spine in range(4):
                    spine_y = sy - round((18 + spine * 8) * echelle)
                    pygame.draw.line(self.ecran, (215, 214, 177), (sx - round(4 * echelle), spine_y), (sx - round(7 * echelle), spine_y - round(2 * echelle)), max(1, round(echelle)))
                    pygame.draw.line(self.ecran, (215, 214, 177), (sx + round(4 * echelle), spine_y), (sx + round(7 * echelle), spine_y - round(2 * echelle)), max(1, round(echelle)))
            else:
                pygame.draw.rect(self.ecran, (91, 61, 42), (sx - max(1, round(5 * echelle)), sy - round(39 * echelle), max(2, round(10 * echelle)), round(40 * echelle)))
                pygame.draw.line(self.ecran, (154, 112, 72), (sx - round(2 * echelle), sy - round(36 * echelle)), (sx - round(2 * echelle), sy - round(4 * echelle)), max(1, round(echelle)))
                feuillage = (42, 101, 55) if biome in ("prairie", "foret") else (138, 146, 77)
                if self.saison == "Automne":
                    feuillage = (min(255, feuillage[0] + 62), max(0, feuillage[1] - 19), max(0, feuillage[2] - 18))
                elif self.saison == "Hiver":
                    feuillage = tuple(round(canal * 0.68 + 62) for canal in feuillage)
                ombre_feuillage = tuple(max(0, c - 22) for c in feuillage)
                lumiere_feuillage = tuple(min(255, c + 23) for c in feuillage)
                vent = math.sin(pygame.time.get_ticks() / 720 + x * 0.63 + y * 0.41) * 2.1 * echelle
                couronne = sy - round(49 * echelle)
                centre_feuillage = sx + round(vent)
                graine_arbre = (int(x * 73856093) ^ int(y * 19349663)) & 0xFFFFFFFF
                rayon = max(2, round((18 + graine_arbre % 5) * echelle))
                pygame.draw.line(self.ecran, (67, 46, 35), (sx, sy - round(29 * echelle)), (centre_feuillage - round(10 * echelle), couronne + round(5 * echelle)), max(1, round(5 * echelle)))
                pygame.draw.line(self.ecran, (67, 46, 35), (sx, sy - round(29 * echelle)), (centre_feuillage + round(11 * echelle), couronne + round(5 * echelle)), max(1, round(5 * echelle)))
                pygame.draw.ellipse(self.ecran, (24, 57, 38), (centre_feuillage - rayon - round(3 * echelle), couronne - round(12 * echelle), (rayon + round(3 * echelle)) * 2, (rayon + round(4 * echelle)) * 2))
                pygame.draw.ellipse(self.ecran, ombre_feuillage, (centre_feuillage - rayon, couronne - rayon // 2, rayon * 2, round(rayon * 1.65)))
                amas = (
                    (-0.62, -0.05, 0.67, 0.72, ombre_feuillage),
                    (0.48, -0.16, 0.61, 0.68, feuillage),
                    (-0.08, -0.62, 0.68, 0.70, feuillage),
                    (-0.48, -0.53, 0.43, 0.47, lumiere_feuillage),
                    (0.32, -0.57, 0.47, 0.49, lumiere_feuillage),
                    (0.02, 0.18, 0.52, 0.43, ombre_feuillage),
                )
                for offset_x, offset_y, largeur_couronne, hauteur_couronne, teinte in amas:
                    rect = pygame.Rect(
                        centre_feuillage + round(offset_x * rayon) - round(largeur_couronne * rayon / 2),
                        couronne + round(offset_y * rayon) - round(hauteur_couronne * rayon / 2),
                        max(2, round(largeur_couronne * rayon)),
                        max(2, round(hauteur_couronne * rayon)),
                    )
                    pygame.draw.ellipse(self.ecran, teinte, rect)
                if echelle > 0.35:
                    for index in range(7):
                        angle = index * 2.4 + graine_arbre % 17
                        feuille_x = centre_feuillage + round(math.cos(angle) * rayon * 0.58)
                        feuille_y = couronne + round(math.sin(angle) * rayon * 0.43)
                        pygame.draw.ellipse(self.ecran, lumiere_feuillage, (feuille_x, feuille_y, max(2, round(5 * echelle)), max(2, round(3 * echelle))))
        elif sorte == "rocher":
            forme = [
                (sx - largeur, sy - round(4 * echelle)),
                (sx - round(16 * echelle), sy - round(17 * echelle)),
                (sx - round(5 * echelle), sy - round(25 * echelle)),
                (sx + round(10 * echelle), sy - round(23 * echelle)),
                (sx + largeur, sy - round(8 * echelle)),
                (sx + round(12 * echelle), sy),
            ]
            pygame.draw.polygon(self.ecran, (69, 75, 75), forme)
            pygame.draw.polygon(self.ecran, (125, 133, 129), [forme[1], forme[2], forme[3], (sx + round(4 * echelle), sy - round(6 * echelle)), (sx - round(9 * echelle), sy - round(9 * echelle))])
            pygame.draw.line(self.ecran, (171, 177, 166), forme[2], forme[3], max(1, round(echelle)))
            pygame.draw.line(self.ecran, (53, 57, 59), (sx - round(7 * echelle), sy - round(8 * echelle)), (sx, sy - round(17 * echelle)), max(1, round(echelle)))
            pygame.draw.line(self.ecran, (91, 96, 90), (sx, sy - round(17 * echelle)), (sx - round(2 * echelle), sy - round(10 * echelle)), max(1, round(echelle)))
            if biome_region(x, y) in ("prairie", "foret") and echelle > 0.24:
                mousse = pygame.Rect(
                    sx - round(9 * echelle),
                    sy - round(7 * echelle),
                    max(2, round(8 * echelle)),
                    max(2, round(3 * echelle)),
                )
                pygame.draw.ellipse(self.ecran, (75, 112, 66), mousse)
                pygame.draw.ellipse(self.ecran, (122, 151, 83), mousse.inflate(-round(3 * echelle), -round(echelle)))
        elif sorte == "decoration":
            decoration = donnees or {}
            if decoration.get("type") == "herbe_haute":
                phase = math.sin(pygame.time.get_ticks() / 500 + x * 2 + y) * 2 * echelle
                for index in range(5):
                    depart_x = sx + round((index - 2) * 3 * echelle)
                    hauteur = (10 + (index % 3) * 2) * echelle
                    couleur = (44, 102, 49) if index % 2 else (93, 143, 66)
                    pygame.draw.line(
                        self.ecran,
                        couleur,
                        (depart_x, sy),
                        (depart_x + round(phase + (index - 2) * 2 * echelle), sy - round(hauteur)),
                        max(1, round(2 * echelle)),
                    )
                    pygame.draw.ellipse(
                        self.ecran,
                        (132, 169, 87),
                        (depart_x + round(phase + (index - 2) * 2 * echelle) - max(1, round(echelle)), sy - round(hauteur), max(2, round(3 * echelle)), max(1, round(echelle))),
                    )
            else:
                pygame.draw.line(self.ecran, (124, 155, 96), (sx, sy), (sx - round(3 * echelle), sy - round(8 * echelle)), max(1, round(2 * echelle)))
                pygame.draw.circle(self.ecran, (224, 191, 116), (sx, sy - round(8 * echelle)), max(1, round(2 * echelle)))
        elif sorte == "ruine":
            pygame.draw.rect(self.ecran, (103, 103, 91), (sx - round(8 * echelle), sy - round(50 * echelle), max(2, round(16 * echelle)), round(50 * echelle)))
            pygame.draw.rect(self.ecran, (160, 154, 127), (sx - round(11 * echelle), sy - round(52 * echelle), max(2, round(22 * echelle)), max(2, round(6 * echelle))))
        elif sorte == "rune":
            dalle = donnees or {}
            symbole = dalle["symbole"]
            couleur = {"lune": (120, 198, 235), "soleil": (247, 184, 76), "etoile": (194, 161, 246)}[symbole]
            rayon = max(3, round(11 * echelle))
            pygame.draw.ellipse(self.ecran, (34, 35, 42), (sx - rayon - 2, sy - round(4 * echelle), rayon * 2 + 4, max(3, round(8 * echelle))))
            pygame.draw.ellipse(self.ecran, (91, 91, 101), (sx - rayon, sy - round(5 * echelle), rayon * 2, max(3, round(7 * echelle))))
            pygame.draw.ellipse(self.ecran, couleur, (sx - rayon + 2, sy - round(4 * echelle), max(2, rayon * 2 - 4), max(2, round(4 * echelle))))
            centre = (sx, sy - round(4 * echelle))
            if symbole == "lune":
                pygame.draw.circle(self.ecran, (231, 239, 229), centre, max(2, round(4 * echelle)))
                pygame.draw.circle(self.ecran, (91, 91, 101), (sx + round(2 * echelle), sy - round(6 * echelle)), max(2, round(4 * echelle)))
            elif symbole == "soleil":
                pygame.draw.circle(self.ecran, (255, 232, 151), centre, max(2, round(3 * echelle)))
                pygame.draw.circle(self.ecran, couleur, centre, max(4, round(6 * echelle)), max(1, round(echelle)))
            else:
                pygame.draw.polygon(self.ecran, (244, 225, 255), [
                    (sx, sy - round(9 * echelle)), (sx + round(2 * echelle), sy - round(5 * echelle)),
                    (sx + round(6 * echelle), sy - round(4 * echelle)), (sx + round(2 * echelle), sy - round(2 * echelle)),
                    (sx, sy + round(2 * echelle)), (sx - round(2 * echelle), sy - round(2 * echelle)),
                    (sx - round(6 * echelle), sy - round(4 * echelle)), (sx - round(2 * echelle), sy - round(5 * echelle)),
                ])
        elif sorte == "piege":
            actif = pygame.time.get_ticks() % 1800 < 900
            for index in range(3):
                pointe_x = sx + round((index - 1) * 6 * echelle)
                pointe_y = sy - round((10 if actif else 4) * echelle)
                base_y = sy - round(1 * echelle)
                pygame.draw.polygon(self.ecran, (83, 74, 69), [
                    (pointe_x, pointe_y), (pointe_x - round(2 * echelle), base_y),
                    (pointe_x + round(2 * echelle), base_y),
                ])
                if actif:
                    pygame.draw.line(self.ecran, (177, 169, 156), (pointe_x, pointe_y), (pointe_x, base_y), max(1, round(echelle)))
        elif sorte == "coffre":
            coffre = donnees or {}
            largeur_coffre = max(4, round(20 * echelle))
            hauteur_coffre = max(3, round(12 * echelle))
            gauche = sx - largeur_coffre // 2
            bas = sy - max(1, round(2 * echelle))
            pygame.draw.ellipse(self.ecran, (46, 51, 38), (gauche - 2, bas - 1, largeur_coffre + 4, max(2, round(5 * echelle))))
            pygame.draw.rect(self.ecran, (99, 66, 39), (gauche, bas - hauteur_coffre, largeur_coffre, hauteur_coffre), border_radius=max(1, round(2 * echelle)))
            pygame.draw.rect(self.ecran, (153, 101, 52), (gauche + 1, bas - hauteur_coffre + 1, max(2, largeur_coffre - 2), max(2, hauteur_coffre - 3)), border_radius=max(1, round(2 * echelle)))
            for bande_x in (gauche + round(4 * echelle), gauche + largeur_coffre - round(5 * echelle)):
                pygame.draw.line(self.ecran, (211, 171, 99), (bande_x, bas - hauteur_coffre), (bande_x, bas), max(1, round(2 * echelle)))
            if coffre.get("ouvert"):
                pygame.draw.polygon(
                    self.ecran,
                    (104, 70, 43),
                    [(gauche, bas - hauteur_coffre), (gauche + round(2 * echelle), bas - round(22 * echelle)), (gauche + largeur_coffre, bas - round(18 * echelle)), (gauche + largeur_coffre, bas - hauteur_coffre + round(2 * echelle))],
                )
                pygame.draw.line(self.ecran, (245, 209, 112), (sx - round(3 * echelle), bas - hauteur_coffre + round(3 * echelle)), (sx + round(3 * echelle), bas - hauteur_coffre + round(3 * echelle)), max(1, round(echelle)))
            else:
                pygame.draw.arc(self.ecran, (204, 156, 83), (gauche, bas - hauteur_coffre - max(1, round(6 * echelle)), largeur_coffre, max(3, round(12 * echelle))), math.pi, math.tau, max(1, round(2 * echelle)))
                pygame.draw.rect(self.ecran, (239, 207, 111), (sx - max(1, round(2 * echelle)), bas - round(8 * echelle), max(2, round(4 * echelle)), max(2, round(5 * echelle))))
        elif sorte == "entree_grotte":
            pygame.draw.polygon(self.ecran, (66, 64, 67), [(sx - round(22 * echelle), sy), (sx - round(17 * echelle), sy - round(28 * echelle)), (sx, sy - round(42 * echelle)), (sx + round(19 * echelle), sy - round(25 * echelle)), (sx + round(23 * echelle), sy)])
            pygame.draw.ellipse(self.ecran, (19, 20, 25), (sx - round(13 * echelle), sy - round(26 * echelle), round(26 * echelle), round(27 * echelle)))
            pygame.draw.ellipse(self.ecran, (226, 188, 104), (sx - round(16 * echelle), sy - round(4 * echelle), round(32 * echelle), round(8 * echelle)), max(1, round(echelle)))
        elif sorte == "repaire":
            repaire = donnees
            rayon = round(27 * echelle)
            pygame.draw.ellipse(self.ecran, (101, 71, 51), (sx - rayon, sy - max(2, round(7 * echelle)), rayon * 2, max(3, round(13 * echelle))))
            pygame.draw.polygon(self.ecran, (118, 71, 50), [(sx - round(14 * echelle), sy), (sx - round(12 * echelle), sy - round(22 * echelle)), (sx, sy - round(32 * echelle)), (sx + round(13 * echelle), sy - round(20 * echelle)), (sx + round(16 * echelle), sy)])
            pygame.draw.polygon(self.ecran, (160, 113, 68), [(sx - round(10 * echelle), sy - round(2 * echelle)), (sx - round(8 * echelle), sy - round(20 * echelle)), (sx, sy - round(28 * echelle)), (sx + round(9 * echelle), sy - round(19 * echelle)), (sx + round(11 * echelle), sy - round(2 * echelle))])
            pygame.draw.line(self.ecran, (209, 187, 127), (sx, sy - round(27 * echelle)), (sx, sy - round(2 * echelle)), max(1, round(2 * echelle)))
            couleur_banniere = (101, 181, 112) if repaire["conquis"] else (185, 55, 48)
            pygame.draw.line(self.ecran, (77, 54, 39), (sx + round(16 * echelle), sy - round(4 * echelle)), (sx + round(16 * echelle), sy - round(47 * echelle)), max(1, round(2 * echelle)))
            pygame.draw.polygon(self.ecran, couleur_banniere, [(sx + round(17 * echelle), sy - round(46 * echelle)), (sx + round(31 * echelle), sy - round(41 * echelle)), (sx + round(17 * echelle), sy - round(35 * echelle))])
            pygame.draw.rect(self.ecran, (111, 74, 43), (sx - round(29 * echelle), sy - round(13 * echelle), max(3, round(10 * echelle)), max(3, round(10 * echelle))))
            pygame.draw.line(self.ecran, (186, 143, 88), (sx - round(29 * echelle), sy - round(13 * echelle)), (sx - round(19 * echelle), sy - round(3 * echelle)), max(1, round(echelle)))
            pygame.draw.ellipse(self.ecran, (117, 79, 55), (sx + round(21 * echelle), sy - round(8 * echelle), max(3, round(12 * echelle)), max(3, round(7 * echelle))))
            pygame.draw.line(self.ecran, (173, 132, 86), (sx + round(21 * echelle), sy - round(5 * echelle)), (sx + round(32 * echelle), sy - round(5 * echelle)), max(1, round(echelle)))
        elif sorte == "feu_camp":
            self.dessiner_feu_camp(sx, sy, echelle, pygame.time.get_ticks())
        elif sorte == "objet":
            if donnees["type"] == "echo":
                self.dessiner_echo_perspective(sx, sy, echelle, donnees, pygame.time.get_ticks())
                return
            if donnees["type"] == "arme":
                self.dessiner_arme_au_sol(sx, sy, echelle, donnees["arme"], pygame.time.get_ticks())
                return
            couleurs = {"coeur": (231, 74, 90), "gemme": (89, 224, 233), "nourriture": (239, 165, 62)}
            couleur = couleurs[donnees["type"]]
            hauteur_objet = round((13 + math.sin(pygame.time.get_ticks() / 220 + x) * 2) * echelle)
            pygame.draw.circle(self.ecran, couleur, (sx, sy - hauteur_objet), max(2, round(5 * echelle)))
            pygame.draw.circle(self.ecran, (255, 249, 213), (sx - max(1, round(2 * echelle)), sy - hauteur_objet - max(1, round(2 * echelle))), max(1, round(echelle)))
        elif sorte == "ennemi":
            ennemi = donnees
            profil = MONSTRES[ennemi["type"]]
            if profil.get("boss"):
                self.dessiner_boss_perspective(sx, sy, echelle, ennemi, profondeur)
                self.dessiner_alerte_ennemi(sx, sy, echelle, ennemi, pygame.time.get_ticks())
                return
            maintenant = pygame.time.get_ticks()
            self.dessiner_monstre_perspective(sx, sy, echelle, ennemi, maintenant)
            self.dessiner_alerte_ennemi(sx, sy, echelle, ennemi, maintenant)
        elif sorte == "village":
            self.dessiner_place_village(sx, sy, echelle, donnees)
        elif sorte == "village_maison":
            self.dessiner_maison_perspective(sx, sy, echelle, donnees)
        elif sorte == "villageois":
            self.dessiner_villageois_perspective(sx, sy, echelle, donnees, pygame.time.get_ticks())

    def dessiner_boss_perspective(self, sx, sy, echelle, boss, profondeur):
        profil = MONSTRES[boss["type"]]
        sorte = boss["type"]
        teinte = profil["couleur"]
        clair = tuple(min(255, canal + 45) for canal in teinte)
        sombre = tuple(max(0, canal - 45) for canal in teinte)
        facteur = max(0.14, echelle)
        p = lambda x, y: (sx + round(x * facteur), sy + round(y * facteur))
        taille = lambda valeur: max(1, round(valeur * facteur))
        temps = pygame.time.get_ticks() / 260
        balancement = math.sin(temps + boss["x"]) * taille(2)

        pygame.draw.ellipse(self.ecran, (31, 39, 34), (sx - taille(36), sy - taille(4), taille(72), taille(12)))
        if boss.get("attaque_charge", 0) > pygame.time.get_ticks():
            pygame.draw.ellipse(
                self.ecran,
                (220, 92, 69),
                (sx - taille(30), sy - taille(7), taille(60), taille(14)),
                max(1, taille(2)),
            )

        if sorte == "centaure":
            pygame.draw.ellipse(self.ecran, sombre, (sx - taille(34), sy - taille(36), taille(54), taille(25)))
            pygame.draw.ellipse(self.ecran, teinte, (sx - taille(30), sy - taille(39), taille(48), taille(24)))
            pygame.draw.ellipse(self.ecran, clair, (sx - taille(25), sy - taille(37), taille(26), taille(9)))
            pygame.draw.polygon(self.ecran, teinte, [p(-28, -24), p(-38, -15), p(-36, -8), p(-25, -19)])
            pygame.draw.polygon(self.ecran, clair, [p(5, -23), p(18, -34), p(28, -31), p(25, -18), p(11, -13)])
            pygame.draw.polygon(self.ecran, sombre, [p(23, -30), p(30, -38), p(31, -27)])
            pygame.draw.polygon(self.ecran, (225, 188, 125), [p(5, -34), p(3, -47), p(12, -37)])
            pygame.draw.polygon(self.ecran, (225, 188, 125), [p(20, -33), p(25, -45), p(26, -32)])
            pygame.draw.polygon(self.ecran, (95, 69, 49), [p(8, -20), p(25, -21), p(23, -3), p(6, -3)])
            for cote in (-1, 1):
                depart_x = sx + cote * taille(22)
                pied_x = depart_x + round(balancement * cote)
                pygame.draw.line(self.ecran, sombre, (depart_x, sy - taille(18)), (pied_x, sy - taille(2)), taille(6))
                pygame.draw.line(self.ecran, (70, 53, 42), (pied_x, sy - taille(6)), (pied_x + cote * taille(5), sy - taille(2)), taille(4))
            pygame.draw.line(self.ecran, (118, 79, 48), p(9, -35), p(12, -64), taille(3))
            pygame.draw.line(self.ecran, (204, 187, 142), p(12, -64), p(16, -52), taille(2))
            pygame.draw.polygon(self.ecran, (154, 58, 49), [p(12, -62), p(29, -57), p(13, -52)])
            pygame.draw.ellipse(self.ecran, (205, 177, 111), (sx + taille(18), sy - taille(29), taille(3), taille(3)))
        elif sorte in ("geant", "ogre"):
            hauteur = 76 if sorte == "geant" else 59
            largeur = 27 if sorte == "geant" else 22
            pygame.draw.line(self.ecran, sombre, p(-13, -25), p(-18, -3), taille(10))
            pygame.draw.line(self.ecran, sombre, p(13, -25), p(18, -3), taille(10))
            pygame.draw.ellipse(self.ecran, (58, 49, 42), (sx - taille(25), sy - taille(8), taille(18), taille(7)))
            pygame.draw.ellipse(self.ecran, (58, 49, 42), (sx + taille(8), sy - taille(8), taille(18), taille(7)))
            pygame.draw.polygon(self.ecran, sombre, [p(-largeur, -hauteur + 19), p(-17, -hauteur), p(16, -hauteur + 2), p(largeur, -hauteur + 20), p(23, -21), p(-22, -21)])
            pygame.draw.polygon(self.ecran, teinte, [p(-20, -hauteur + 20), p(-13, -hauteur + 8), p(13, -hauteur + 9), p(21, -hauteur + 21), p(16, -20), p(-17, -20)])
            pygame.draw.polygon(self.ecran, clair, [p(-14, -hauteur + 15), p(-7, -hauteur + 11), p(-5, -26), p(-15, -25)])
            pygame.draw.polygon(self.ecran, (89, 75, 58), [p(-19, -39), p(-9, -45), p(-4, -36), p(-12, -26)])
            pygame.draw.polygon(self.ecran, (91, 73, 54), [p(19, -38), p(9, -45), p(4, -35), p(12, -25)])
            pygame.draw.ellipse(self.ecran, teinte, (sx - taille(18), sy - taille(hauteur + 8), taille(36), taille(27)))
            pygame.draw.arc(self.ecran, clair, (sx - taille(20), sy - taille(hauteur + 13), taille(40), taille(21)), math.pi, math.tau, taille(3))
            pygame.draw.circle(self.ecran, (61, 46, 37), p(-6, -hauteur - 1), taille(2))
            pygame.draw.circle(self.ecran, (61, 46, 37), p(7, -hauteur - 1), taille(2))
            pygame.draw.line(self.ecran, (59, 43, 34), p(-6, -hauteur + 9), p(7, -hauteur + 9), taille(2))
            if sorte == "geant":
                pygame.draw.line(self.ecran, (93, 61, 39), p(25, -47), p(31, -4), taille(8))
                pygame.draw.polygon(self.ecran, (133, 93, 57), [p(20, -48), p(29, -58), p(38, -49), p(33, -40)])
                for index in range(3):
                    pygame.draw.line(self.ecran, (184, 145, 103), p(27 + index * 2, -48), p(32 + index * 2, -46), taille(1))
            else:
                pygame.draw.ellipse(self.ecran, (89, 112, 76), (sx + taille(7), sy - taille(hauteur - 2), taille(9), taille(8)))
                pygame.draw.arc(self.ecran, (199, 178, 124), (sx + taille(6), sy - taille(hauteur + 7), taille(11), taille(17)), math.pi, math.tau, taille(2))
        elif sorte == "cyclope":
            pygame.draw.line(self.ecran, sombre, p(-11, -25), p(-16, -2), taille(9))
            pygame.draw.line(self.ecran, sombre, p(11, -25), p(16, -2), taille(9))
            pygame.draw.ellipse(self.ecran, (58, 49, 42), (sx - taille(25), sy - taille(8), taille(18), taille(7)))
            pygame.draw.ellipse(self.ecran, (58, 49, 42), (sx + taille(8), sy - taille(8), taille(18), taille(7)))
            pygame.draw.polygon(self.ecran, sombre, [p(-23, -20), p(-20, -55), p(-12, -68), p(13, -68), p(22, -54), p(24, -19)])
            pygame.draw.polygon(self.ecran, teinte, [p(-18, -22), p(-16, -53), p(-9, -63), p(10, -63), p(17, -51), p(18, -22)])
            pygame.draw.polygon(self.ecran, (104, 78, 55), [p(-16, -35), p(-10, -45), p(11, -45), p(17, -34), p(10, -27), p(-10, -27)])
            pygame.draw.ellipse(self.ecran, (240, 221, 178), (sx - taille(8), sy - taille(59), taille(16), taille(11)))
            pygame.draw.ellipse(self.ecran, (84, 112, 63), (sx - taille(4), sy - taille(58), taille(8), taille(9)))
            pygame.draw.ellipse(self.ecran, (24, 27, 23), (sx - taille(1.5), sy - taille(57), taille(3), taille(7)))
            pygame.draw.polygon(self.ecran, (170, 146, 109), [p(-19, -53), p(-29, -62), p(-25, -43)])
            pygame.draw.polygon(self.ecran, (170, 146, 109), [p(19, -53), p(29, -62), p(25, -43)])
            pygame.draw.polygon(self.ecran, (116, 88, 61), [p(-15, -27), p(15, -27), p(19, -19), p(13, -8), p(-13, -8), p(-19, -19)])
            pygame.draw.line(self.ecran, (99, 69, 43), p(21, -39), p(29, -3), taille(7))
            pygame.draw.polygon(self.ecran, (131, 92, 55), [p(22, -43), p(30, -50), p(37, -43), p(32, -35)])
            pygame.draw.line(self.ecran, (213, 180, 115), p(-10, -23), p(10, -23), taille(2))
        elif sorte == "dragon":
            aile_g = [p(-10, -31), p(-49, -69), p(-44, -34), p(-30, -17), p(-18, -12)]
            aile_d = [p(10, -31), p(49, -69), p(44, -34), p(30, -17), p(18, -12)]
            pygame.draw.polygon(self.ecran, sombre, aile_g)
            pygame.draw.polygon(self.ecran, sombre, aile_d)
            pygame.draw.polygon(self.ecran, (129, 44, 49), [p(-8, -29), p(-39, -61), p(-35, -35), p(-17, -17)])
            pygame.draw.polygon(self.ecran, (129, 44, 49), [p(8, -29), p(39, -61), p(35, -35), p(17, -17)])
            for cote in (-1, 1):
                pygame.draw.line(self.ecran, clair, p(cote * 11, -28), p(cote * 42, -57), taille(2))
                pygame.draw.line(self.ecran, clair, p(cote * 14, -24), p(cote * 37, -34), taille(1))
            pygame.draw.ellipse(self.ecran, sombre, (sx - taille(22), sy - taille(37), taille(45), taille(32)))
            pygame.draw.ellipse(self.ecran, teinte, (sx - taille(19), sy - taille(39), taille(39), taille(29)))
            pygame.draw.ellipse(self.ecran, (180, 103, 74), (sx - taille(7), sy - taille(27), taille(15), taille(18)))
            for ecaille in range(3):
                pygame.draw.line(self.ecran, (224, 160, 108), p(-4, -24 + ecaille * 4), p(4, -24 + ecaille * 4), taille(1))
            pygame.draw.line(self.ecran, sombre, p(0, -32), p(0, -70), taille(10))
            pygame.draw.line(self.ecran, teinte, p(0, -32), p(0, -68), taille(7))
            pygame.draw.line(self.ecran, sombre, p(-12, -32), p(-39, -57), taille(9))
            pygame.draw.line(self.ecran, teinte, p(-12, -32), p(-38, -55), taille(7))
            pygame.draw.line(self.ecran, sombre, p(12, -32), p(39, -57), taille(9))
            pygame.draw.line(self.ecran, teinte, p(12, -32), p(38, -55), taille(7))
            for tete_x, tete_y in ((-44, -60), (0, -76), (44, -60)):
                pygame.draw.ellipse(self.ecran, sombre, (sx + taille(tete_x - 13), sy + taille(tete_y - 9), taille(27), taille(19)))
                pygame.draw.ellipse(self.ecran, teinte, (sx + taille(tete_x - 12), sy + taille(tete_y - 11), taille(24), taille(17)))
                pygame.draw.polygon(self.ecran, (225, 167, 103), [p(tete_x - 5, tete_y - 9), p(tete_x - 1, tete_y - 19), p(tete_x + 3, tete_y - 9)])
                pygame.draw.polygon(self.ecran, (225, 167, 103), [p(tete_x + 3, tete_y - 9), p(tete_x + 8, tete_y - 17), p(tete_x + 9, tete_y - 8)])
                pygame.draw.polygon(self.ecran, clair, [p(tete_x + 5, tete_y - 1), p(tete_x + 16, tete_y + 2), p(tete_x + 5, tete_y + 5)])
                pygame.draw.circle(self.ecran, (248, 215, 89), p(tete_x + 5, tete_y - 4), taille(2.5))
                pygame.draw.circle(self.ecran, (26, 29, 25), p(tete_x + 6, tete_y - 4), taille(0.8))
            pygame.draw.polygon(self.ecran, teinte, [p(-17, -17), p(-31, -8), p(-27, -15)])

        if boss.get("vies_max", 1) > 1:
            largeur = taille(64)
            hauteur = max(3, taille(5))
            barre_x = sx - largeur // 2
            barre_y = sy - taille(88 if sorte == "dragon" else 83 if sorte == "cyclope" else 77 if sorte == "geant" else 70)
            pygame.draw.rect(self.ecran, (37, 28, 28), (barre_x - 1, barre_y - taille(1), largeur + 2, hauteur + taille(2)), border_radius=max(1, taille(2)))
            pygame.draw.rect(self.ecran, (126, 37, 39), (barre_x, barre_y, largeur, hauteur), border_radius=max(1, taille(2)))
            reste = max(1, round(largeur * boss["vies"] / boss["vies_max"]))
            pygame.draw.rect(self.ecran, (226, 74, 57), (barre_x, barre_y, reste, hauteur), border_radius=max(1, taille(2)))
            if profondeur < 9 and echelle > 0.48:
                nom = self.police_details.render(profil["nom"], True, (255, 228, 177))
                self.ecran.blit(nom, nom.get_rect(center=(sx, barre_y - taille(10))))

    def dessiner_place_village(self, sx, sy, echelle, village):
        """Dessine un lieu de rassemblement adapte au climat et aux ressources locales."""
        facteur = echelle * 1.35
        taille = lambda valeur: max(1, round(valeur * facteur))
        biome = village.get("biome", biome_region(village["x"], village["y"]))

        pygame.draw.ellipse(
            self.ecran,
            (48, 54, 43),
            (sx - taille(34), sy - taille(5), taille(68), taille(17)),
        )
        pave = (145, 133, 111) if biome == "neige" else (150, 134, 107) if biome == "desert" else (111, 119, 104)
        pygame.draw.ellipse(
            self.ecran,
            pave,
            (sx - taille(30), sy - taille(7), taille(60), taille(13)),
        )
        for index in range(9):
            angle = index * math.tau / 9
            pierre_x = sx + round(math.cos(angle) * taille(23))
            pierre_y = sy - taille(2) + round(math.sin(angle) * taille(5))
            pygame.draw.ellipse(
                self.ecran,
                (190, 177, 148) if index % 2 else (91, 101, 91),
                (pierre_x - taille(3), pierre_y - taille(1), taille(6), taille(2)),
            )

        if biome == "foret":
            pygame.draw.ellipse(self.ecran, (46, 85, 51), (sx - taille(13), sy - taille(24), taille(26), taille(27)))
            pygame.draw.rect(self.ecran, (93, 64, 42), (sx - taille(5), sy - taille(30), taille(10), taille(27)))
            pygame.draw.line(self.ecran, (155, 115, 69), (sx - taille(2), sy - taille(27)), (sx - taille(2), sy - taille(8)), taille(2))
            for cote in (-1, 1):
                pygame.draw.line(self.ecran, (108, 76, 46), (sx, sy - taille(23)), (sx + cote * taille(15), sy - taille(34)), taille(3))
            for feuille_x, feuille_y, rayon in ((-12, -34, 10), (0, -40, 12), (13, -33, 10)):
                pygame.draw.circle(self.ecran, (31, 74, 46), (sx + taille(feuille_x), sy + taille(feuille_y)), taille(rayon))
                pygame.draw.circle(self.ecran, (69, 121, 67), (sx + taille(feuille_x - 2), sy + taille(feuille_y - 2)), taille(rayon * 0.55))
            pygame.draw.ellipse(self.ecran, (67, 139, 108), (sx - taille(7), sy - taille(7), taille(14), taille(5)))
        elif biome == "desert":
            pygame.draw.ellipse(self.ecran, (125, 83, 45), (sx - taille(16), sy - taille(14), taille(32), taille(12)))
            pygame.draw.ellipse(self.ecran, (190, 151, 92), (sx - taille(12), sy - taille(16), taille(24), taille(10)))
            pygame.draw.ellipse(self.ecran, (46, 104, 119), (sx - taille(8), sy - taille(15), taille(16), taille(6)))
            pygame.draw.line(self.ecran, (105, 67, 43), (sx - taille(18), sy - taille(8)), (sx - taille(18), sy - taille(35)), taille(3))
            pygame.draw.line(self.ecran, (105, 67, 43), (sx + taille(18), sy - taille(8)), (sx + taille(18), sy - taille(35)), taille(3))
            pygame.draw.line(self.ecran, (143, 87, 47), (sx - taille(20), sy - taille(35)), (sx + taille(20), sy - taille(35)), taille(3))
            pygame.draw.polygon(self.ecran, (178, 103, 56), [(sx - taille(23), sy - taille(34)), (sx, sy - taille(43)), (sx + taille(23), sy - taille(34))])
            pygame.draw.polygon(self.ecran, (221, 161, 91), [(sx - taille(17), sy - taille(34)), (sx, sy - taille(40)), (sx + taille(17), sy - taille(34))])
            pygame.draw.circle(self.ecran, (239, 198, 117), (sx, sy - taille(34)), taille(2))
        elif biome == "neige":
            pygame.draw.ellipse(self.ecran, (75, 84, 91), (sx - taille(13), sy - taille(11), taille(26), taille(10)))
            pygame.draw.ellipse(self.ecran, (194, 207, 208), (sx - taille(10), sy - taille(13), taille(20), taille(8)))
            pygame.draw.ellipse(self.ecran, (52, 91, 103), (sx - taille(6), sy - taille(12), taille(12), taille(5)))
            pygame.draw.line(self.ecran, (93, 76, 57), (sx - taille(18), sy - taille(6)), (sx - taille(18), sy - taille(36)), taille(3))
            pygame.draw.line(self.ecran, (93, 76, 57), (sx + taille(18), sy - taille(6)), (sx + taille(18), sy - taille(36)), taille(3))
            pygame.draw.line(self.ecran, (128, 94, 58), (sx - taille(19), sy - taille(36)), (sx + taille(19), sy - taille(36)), taille(3))
            pygame.draw.polygon(self.ecran, (75, 104, 119), [(sx - taille(24), sy - taille(35)), (sx, sy - taille(50)), (sx + taille(24), sy - taille(35))])
            pygame.draw.polygon(self.ecran, (225, 235, 230), [(sx - taille(19), sy - taille(37)), (sx, sy - taille(50)), (sx + taille(19), sy - taille(37))])
            pygame.draw.line(self.ecran, (169, 196, 199), (sx - taille(17), sy - taille(36)), (sx, sy - taille(47)), taille(2))
        else:
            pygame.draw.ellipse(self.ecran, (105, 73, 47), (sx - taille(15), sy - taille(13), taille(30), taille(12)))
            pygame.draw.ellipse(self.ecran, (198, 165, 118), (sx - taille(11), sy - taille(15), taille(22), taille(9)))
            pygame.draw.ellipse(self.ecran, (47, 105, 119), (sx - taille(7), sy - taille(14), taille(14), taille(5)))
            pygame.draw.line(self.ecran, (104, 70, 44), (sx - taille(17), sy - taille(7)), (sx - taille(17), sy - taille(36)), taille(3))
            pygame.draw.line(self.ecran, (104, 70, 44), (sx + taille(17), sy - taille(7)), (sx + taille(17), sy - taille(36)), taille(3))
            pygame.draw.line(self.ecran, (142, 97, 55), (sx - taille(19), sy - taille(36)), (sx + taille(19), sy - taille(36)), taille(3))
            pygame.draw.polygon(self.ecran, (129, 81, 47), [(sx - taille(23), sy - taille(35)), (sx, sy - taille(49)), (sx + taille(23), sy - taille(35))])
            pygame.draw.line(self.ecran, (184, 135, 80), (sx - taille(18), sy - taille(35)), (sx, sy - taille(46)), taille(2))
            pygame.draw.line(self.ecran, (184, 135, 80), (sx, sy - taille(46)), (sx + taille(18), sy - taille(35)), taille(2))

    def dessiner_maison_perspective(self, sx, sy, echelle, maison):
        """Dessine une maison dont les materiaux suivent ceux du biome."""
        facteur = echelle * 1.3
        taille = lambda valeur: max(1, round(valeur * facteur))
        biome = maison.get("biome", biome_region(maison["x"], maison["y"]))
        materiaux = {
            "prairie": ((211, 187, 143), (191, 156, 108), (153, 88, 52), (187, 109, 61)),
            "foret": ((145, 119, 86), (114, 91, 67), (61, 82, 55), (86, 112, 67)),
            "desert": ((221, 184, 126), (193, 147, 91), (139, 78, 47), (180, 103, 59)),
            "neige": ((174, 185, 183), (134, 148, 151), (61, 82, 101), (85, 115, 132)),
        }
        mur_clair, mur_sombre, toit_sombre, toit_clair_base = materiaux[biome]
        mur = mur_clair if maison["variante"] % 2 == 0 else mur_sombre
        ombre_mur = tuple(max(0, canal - 45) for canal in mur)
        toit = toit_sombre
        toit_clair = toit_clair_base

        pygame.draw.ellipse(self.ecran, (44, 52, 41), (sx - taille(38), sy - taille(4), taille(76), taille(15)))
        pygame.draw.polygon(self.ecran, (110, 102, 83), [(sx - taille(27), sy - taille(3)), (sx - taille(20), sy - taille(10)), (sx + taille(17), sy - taille(10)), (sx + taille(27), sy - taille(3))])
        for index in range(5):
            pierre_x = sx - taille(19) + round(index * taille(9))
            pygame.draw.line(self.ecran, (156, 146, 123), (pierre_x, sy - taille(8)), (pierre_x + taille(4), sy - taille(4)), max(1, taille(1)))
        pygame.draw.polygon(self.ecran, ombre_mur, [(sx - taille(25), sy - taille(17)), (sx, sy - taille(31)), (sx + taille(25), sy - taille(17)), (sx + taille(25), sy), (sx - taille(25), sy)])
        pygame.draw.rect(self.ecran, mur, (sx - taille(22), sy - taille(28), taille(39), taille(28)))
        pygame.draw.polygon(self.ecran, toit, [(sx - taille(29), sy - taille(27)), (sx - taille(2), sy - taille(53)), (sx + taille(29), sy - taille(27)), (sx + taille(24), sy - taille(22)), (sx - taille(24), sy - taille(22))])
        pygame.draw.polygon(self.ecran, toit_clair, [(sx - taille(26), sy - taille(29)), (sx - taille(2), sy - taille(50)), (sx + taille(5), sy - taille(44)), (sx - taille(17), sy - taille(26))])
        for ligne in range(1, 5):
            decalage = taille(ligne * 5)
            pygame.draw.line(
                self.ecran,
                tuple(max(0, canal - 34) for canal in toit_clair),
                (sx - taille(25) + decalage, sy - taille(29) + round(decalage * 0.43)),
                (sx - taille(3) + decalage, sy - taille(49) + round(decalage * 0.43)),
                max(1, taille(0.8)),
            )
        pygame.draw.line(self.ecran, (93, 59, 39), (sx - taille(29), sy - taille(27)), (sx + taille(24), sy - taille(27)), taille(3))
        pygame.draw.line(self.ecran, (112, 76, 48), (sx - taille(23), sy - taille(26)), (sx - taille(23), sy - taille(2)), taille(3))
        pygame.draw.line(self.ecran, (112, 76, 48), (sx + taille(13), sy - taille(26)), (sx + taille(13), sy - taille(2)), taille(3))
        pygame.draw.line(self.ecran, (136, 96, 58), (sx - taille(4), sy - taille(27)), (sx - taille(4), sy - taille(2)), taille(2))
        pygame.draw.line(self.ecran, (229, 205, 161), (sx - taille(18), sy - taille(10)), (sx + taille(8), sy - taille(10)), taille(2))
        porte_x = sx - taille(3)
        pygame.draw.rect(self.ecran, (92, 62, 44), (porte_x, sy - taille(21), taille(12), taille(21)), border_radius=taille(2))
        pygame.draw.rect(self.ecran, (134, 91, 56), (porte_x + taille(2), sy - taille(19), taille(8), taille(18)), border_radius=taille(1))
        pygame.draw.arc(self.ecran, (75, 53, 40), (porte_x, sy - taille(25), taille(12), taille(10)), math.pi, math.tau, max(1, taille(1)))
        pygame.draw.circle(self.ecran, (240, 196, 91), (sx + taille(6), sy - taille(10)), taille(1.5))
        for fenetre_x in (sx - taille(16), sx + taille(16)):
            fenetre = pygame.Rect(fenetre_x - taille(4), sy - taille(22), taille(8), taille(10))
            pygame.draw.rect(self.ecran, (78, 106, 108), fenetre, border_radius=taille(2))
            pygame.draw.rect(self.ecran, (62, 48, 37), fenetre.inflate(taille(4), taille(3)), max(1, taille(2)), border_radius=taille(2))
            pygame.draw.rect(self.ecran, (226, 207, 163), fenetre, max(1, taille(1)), border_radius=taille(2))
            pygame.draw.line(self.ecran, (226, 207, 163), fenetre.midtop, fenetre.midbottom, max(1, taille(1)))
            pygame.draw.line(self.ecran, (226, 207, 163), fenetre.midleft, fenetre.midright, max(1, taille(1)))
            for volet in (-1, 1):
                volet_x = fenetre_x + volet * taille(6)
                pygame.draw.rect(self.ecran, (111, 75, 48), (volet_x - taille(2), sy - taille(22), taille(3), taille(10)))
                pygame.draw.line(self.ecran, (177, 137, 84), (volet_x - taille(2), sy - taille(17)), (volet_x, sy - taille(17)), max(1, taille(1)))
        pygame.draw.rect(self.ecran, (100, 69, 47), (sx + taille(12), sy - taille(47), taille(8), taille(15)))
        pygame.draw.rect(self.ecran, (171, 138, 94), (sx + taille(11), sy - taille(49), taille(10), taille(3)))
        if biome == "prairie":
            for poutre_x in (-18, -3, 13):
                pygame.draw.line(self.ecran, (105, 70, 43), (sx + taille(poutre_x), sy - taille(25)), (sx + taille(poutre_x), sy - taille(2)), taille(2))
            pygame.draw.line(self.ecran, (105, 70, 43), (sx - taille(21), sy - taille(16)), (sx + taille(16), sy - taille(16)), taille(2))
            pygame.draw.polygon(self.ecran, (233, 207, 153), [(sx - taille(27), sy - taille(28)), (sx - taille(2), sy - taille(53)), (sx + taille(27), sy - taille(28))])
            for index in range(5):
                depart_x = sx - taille(21) + index * taille(10)
                pygame.draw.line(self.ecran, (205, 176, 120), (depart_x, sy - taille(34)), (depart_x + taille(9), sy - taille(28)), max(1, taille(1)))
        elif biome == "foret":
            for niveau in range(3):
                poutre_y = sy - taille(7 + niveau * 9)
                pygame.draw.line(self.ecran, (80, 54, 37), (sx - taille(21), poutre_y), (sx + taille(16), poutre_y), taille(3))
                pygame.draw.line(self.ecran, (183, 139, 86), (sx - taille(19), poutre_y - taille(1)), (sx + taille(14), poutre_y - taille(1)), max(1, taille(1)))
            pygame.draw.line(self.ecran, (72, 53, 38), (sx - taille(20), sy - taille(26)), (sx + taille(15), sy - taille(3)), taille(2))
            pygame.draw.line(self.ecran, (72, 53, 38), (sx + taille(15), sy - taille(26)), (sx - taille(20), sy - taille(3)), taille(2))
            pygame.draw.ellipse(self.ecran, (112, 142, 76), (sx - taille(27), sy - taille(31), taille(19), taille(6)))
        elif biome == "desert":
            pygame.draw.rect(self.ecran, mur_sombre, (sx - taille(24), sy - taille(30), taille(43), taille(5)))
            pygame.draw.rect(self.ecran, mur_clair, (sx - taille(22), sy - taille(34), taille(39), taille(5)))
            pygame.draw.rect(self.ecran, (171, 119, 74), (sx - taille(21), sy - taille(7), taille(36), taille(5)))
            pygame.draw.line(self.ecran, (148, 88, 53), (sx - taille(18), sy - taille(24)), (sx + taille(10), sy - taille(24)), max(1, taille(1)))
            pygame.draw.line(self.ecran, (148, 88, 53), (sx - taille(18), sy - taille(19)), (sx + taille(10), sy - taille(19)), max(1, taille(1)))
        else:
            pygame.draw.polygon(self.ecran, (219, 231, 230), [(sx - taille(29), sy - taille(28)), (sx - taille(2), sy - taille(53)), (sx + taille(24), sy - taille(28)), (sx + taille(17), sy - taille(31)), (sx - taille(2), sy - taille(47)), (sx - taille(22), sy - taille(29))])
            pygame.draw.line(self.ecran, (114, 130, 136), (sx - taille(21), sy - taille(25)), (sx + taille(14), sy - taille(25)), taille(2))
            for poutre_x in (-17, 13):
                pygame.draw.line(self.ecran, (96, 81, 66), (sx + taille(poutre_x), sy - taille(26)), (sx + taille(poutre_x), sy - taille(2)), taille(2))
            pygame.draw.ellipse(self.ecran, (199, 215, 221), (sx - taille(22), sy - taille(7), taille(10), taille(3)))

        couleur_auvent = {
            "prairie": (83, 132, 77),
            "foret": (65, 111, 70),
            "desert": (190, 117, 66),
            "neige": (89, 129, 145),
        }[biome]
        pygame.draw.polygon(
            self.ecran,
            couleur_auvent,
            [
                (sx - taille(24), sy - taille(11)),
                (sx - taille(15), sy - taille(15)),
                (sx + taille(2), sy - taille(11)),
                (sx - taille(1), sy - taille(8)),
            ],
        )
        pygame.draw.line(self.ecran, (92, 68, 45), (sx - taille(20), sy - taille(11)), (sx - taille(21), sy - taille(2)), max(1, taille(1)))
        pygame.draw.line(self.ecran, (92, 68, 45), (sx - taille(2), sy - taille(9)), (sx - taille(2), sy - taille(2)), max(1, taille(1)))
        if facteur > 0.58:
            phase = pygame.time.get_ticks() / 520 + maison["variante"]
            fumee_x = sx + taille(16)
            progression = (pygame.time.get_ticks() / 850 + maison["variante"] * 1.7) % 1
            fumee_y = sy - taille(53 + progression * 20)
            rayon_fumee = max(1, taille(1.5 + progression * 1.5))
            pygame.draw.circle(self.ecran, (104, 111, 105), (fumee_x + round(math.sin(phase) * taille(2)), fumee_y), rayon_fumee + 1)
            pygame.draw.circle(self.ecran, (208, 213, 199), (fumee_x + round(math.sin(phase) * taille(2)), fumee_y), rayon_fumee)

    def dessiner_villageois_perspective(self, sx, sy, echelle, habitant, maintenant):
        """Dessine un habitant anime avec des vetements et un outil distinctif."""
        facteur = echelle * 1.28 if echelle <= 1.8 else echelle
        taille = lambda valeur: max(1, round(valeur * facteur))
        phase = maintenant / 430 + habitant["phase"]
        balancement = math.sin(phase) * taille(2)
        rebond = abs(math.sin(phase * 0.7)) * taille(1.2)
        pied_y = sy - round(rebond)
        peau = habitant["peau"]
        cheveux = habitant["cheveux"]
        tunique = habitant["tunique"]
        tunique_claire = tuple(min(255, canal + 27) for canal in tunique)
        tunique_sombre = tuple(max(0, canal - 31) for canal in tunique)
        peau_claire = tuple(min(255, canal + 20) for canal in peau)
        pygame.draw.ellipse(self.ecran, (35, 49, 38), (sx - taille(13), pied_y - taille(2), taille(26), taille(7)))

        jambe_g = sx - taille(4) + round(balancement)
        jambe_d = sx + taille(4) - round(balancement)
        pygame.draw.line(self.ecran, (64, 54, 47), (sx - taille(4), pied_y - taille(13)), (jambe_g, pied_y - taille(3)), taille(4))
        pygame.draw.line(self.ecran, (78, 64, 51), (sx + taille(4), pied_y - taille(13)), (jambe_d, pied_y - taille(3)), taille(4))
        pygame.draw.ellipse(self.ecran, (53, 43, 37), (jambe_g - taille(5), pied_y - taille(5), taille(9), taille(5)))
        pygame.draw.ellipse(self.ecran, (53, 43, 37), (jambe_d - taille(4), pied_y - taille(5), taille(9), taille(5)))

        epaule_y = pied_y - taille(17)
        pygame.draw.ellipse(self.ecran, tunique_sombre, (sx - taille(10), epaule_y - taille(2), taille(20), taille(20)))
        pygame.draw.polygon(self.ecran, tunique, [(sx - taille(8), epaule_y), (sx, epaule_y - taille(3)), (sx + taille(8), epaule_y), (sx + taille(9), pied_y - taille(11)), (sx, pied_y - taille(9)), (sx - taille(9), pied_y - taille(11))])
        pygame.draw.polygon(self.ecran, tunique_claire, [(sx - taille(6), epaule_y), (sx, epaule_y - taille(2)), (sx - taille(2), pied_y - taille(12)), (sx - taille(6), pied_y - taille(12))])
        pygame.draw.polygon(self.ecran, tunique_sombre, [(sx + taille(4), epaule_y + taille(1)), (sx + taille(8), epaule_y + taille(2)), (sx + taille(9), pied_y - taille(11)), (sx + taille(4), pied_y - taille(10))])
        pygame.draw.polygon(self.ecran, (235, 218, 180), [(sx - taille(4), epaule_y), (sx, epaule_y + taille(6)), (sx + taille(4), epaule_y), (sx + taille(2), epaule_y + taille(9)), (sx, epaule_y + taille(7)), (sx - taille(2), epaule_y + taille(9))])
        pygame.draw.line(self.ecran, (100, 73, 49), (sx - taille(8), pied_y - taille(12)), (sx + taille(8), pied_y - taille(12)), taille(2))
        pygame.draw.circle(self.ecran, (222, 187, 104), (sx, pied_y - taille(12)), taille(1.4))
        for bouton in range(3):
            bouton_y = epaule_y + taille(6 + bouton * 4)
            pygame.draw.circle(self.ecran, (231, 201, 135), (sx, bouton_y), taille(0.8))
        if habitant["metier"] in ("Fermier", "Boulangere", "Forgeron", "Marchande", "Tisseuse"):
            tablier = (126, 91, 61) if habitant["metier"] == "Forgeron" else (218, 194, 151)
            pygame.draw.polygon(self.ecran, tablier, [(sx - taille(5), pied_y - taille(10)), (sx + taille(5), pied_y - taille(10)), (sx + taille(6), pied_y - taille(2)), (sx - taille(6), pied_y - taille(2))])
            pygame.draw.line(self.ecran, (132, 100, 66), (sx - taille(4), pied_y - taille(4)), (sx + taille(4), pied_y - taille(4)), max(1, taille(0.8)))

        bras_g = (sx - taille(8), epaule_y + taille(2))
        main_g = (sx - taille(12) + round(balancement), pied_y - taille(9))
        pygame.draw.line(self.ecran, tunique_sombre, bras_g, (sx - taille(12), epaule_y + taille(10)), taille(5))
        pygame.draw.line(self.ecran, peau_claire, (sx - taille(12), epaule_y + taille(9)), main_g, taille(3))
        bras_d = (sx + taille(8), epaule_y + taille(2))
        main_d = (sx + taille(12) - round(balancement), pied_y - taille(10))
        pygame.draw.line(self.ecran, tunique_claire, bras_d, (sx + taille(12), epaule_y + taille(9)), taille(5))
        pygame.draw.line(self.ecran, peau, (sx + taille(12), epaule_y + taille(8)), main_d, taille(3))

        cou_y = epaule_y - taille(3)
        pygame.draw.rect(self.ecran, peau, (sx - taille(3), cou_y, taille(6), taille(6)))
        tete_y = cou_y - taille(7)
        pygame.draw.ellipse(self.ecran, peau, (sx - taille(7), tete_y - taille(7), taille(14), taille(15)))
        pygame.draw.ellipse(self.ecran, cheveux, (sx - taille(7), tete_y - taille(8), taille(14), taille(7)))
        pygame.draw.arc(self.ecran, peau_claire, (sx - taille(6), tete_y - taille(5), taille(12), taille(12)), math.pi, math.tau, max(1, taille(1)))
        pygame.draw.circle(self.ecran, (66, 50, 42), (sx - taille(2), tete_y), taille(0.8))
        pygame.draw.circle(self.ecran, (66, 50, 42), (sx + taille(3), tete_y), taille(0.8))
        pygame.draw.circle(self.ecran, (250, 235, 208), (sx - taille(2), tete_y - taille(0.5)), max(1, taille(0.35)))
        pygame.draw.circle(self.ecran, (250, 235, 208), (sx + taille(3), tete_y - taille(0.5)), max(1, taille(0.35)))
        pygame.draw.line(self.ecran, cheveux, (sx - taille(5), tete_y - taille(2)), (sx - taille(1), tete_y - taille(3)), max(1, taille(0.8)))
        pygame.draw.line(self.ecran, cheveux, (sx + taille(1), tete_y - taille(3)), (sx + taille(5), tete_y - taille(2)), max(1, taille(0.8)))
        pygame.draw.line(self.ecran, (132, 83, 65), (sx, tete_y + taille(2)), (sx + taille(1), tete_y + taille(4)), max(1, taille(1)))
        pygame.draw.arc(self.ecran, (121, 69, 59), (sx - taille(2), tete_y + taille(4), taille(5), taille(3)), 0, math.pi, max(1, taille(1)))
        if habitant["metier"] in ("Ancienne", "Ancien", "Gardien", "Cheffe"):
            pygame.draw.arc(self.ecran, (221, 190, 123), (sx - taille(8), tete_y - taille(9), taille(16), taille(10)), math.pi, math.tau, max(1, taille(2)))
        elif habitant["metier"] in ("Chasseuse", "Eclaireur", "Guetteuse"):
            pygame.draw.polygon(self.ecran, tunique_sombre, [(sx - taille(8), tete_y - taille(5)), (sx, tete_y - taille(11)), (sx + taille(8), tete_y - taille(5))])

        outil = habitant["outil"]
        outil_x = sx + taille(14)
        if outil in ("canne", "lance", "arc"):
            sommet = sy - taille(43 if outil == "lance" else 34)
            pygame.draw.line(self.ecran, (122, 81, 48), (outil_x, pied_y - taille(8)), (outil_x, sommet), taille(2))
            pygame.draw.circle(self.ecran, (206, 173, 103), (outil_x, sommet), taille(2))
            if outil == "arc":
                pygame.draw.arc(self.ecran, (169, 118, 67), (outil_x - taille(6), sommet, taille(12), taille(22)), -1.5, 1.5, max(1, taille(2)))
        elif outil in ("hache", "marteau"):
            pygame.draw.line(self.ecran, (113, 76, 47), (outil_x, pied_y - taille(8)), (outil_x, epaule_y), taille(2))
            pygame.draw.polygon(self.ecran, (166, 174, 173), [(outil_x, epaule_y - taille(2)), (outil_x + taille(8), epaule_y - taille(5)), (outil_x + taille(9), epaule_y + taille(1)), (outil_x + taille(1), epaule_y + taille(2))])
        elif outil in ("panier", "livre", "luth", "faucille"):
            accessoire_y = pied_y - taille(13)
            pygame.draw.ellipse(self.ecran, (148, 104, 60), (sx - taille(16), accessoire_y, taille(9), taille(8)))
            pygame.draw.arc(self.ecran, (215, 184, 125), (sx - taille(16), accessoire_y - taille(4), taille(9), taille(8)), math.pi, math.tau, max(1, taille(1)))
            if outil == "livre":
                pygame.draw.line(self.ecran, (223, 198, 137), (sx - taille(12), accessoire_y + taille(1)), (sx - taille(12), accessoire_y + taille(6)), max(1, taille(1)))

        if habitant["donneur_quete"]:
            quete = self.quetes[habitant["village_index"]]
            if not quete["faite"]:
                symbole = "?" if quete["active"] and quete["progres"] >= quete["besoin"] else "!"
                couleur = (119, 236, 172) if symbole == "?" else (255, 222, 104)
                pygame.draw.circle(self.ecran, (36, 47, 40), (sx, tete_y - taille(17)), taille(8))
                icone = self.police.render(symbole, True, couleur)
                self.ecran.blit(icone, icone.get_rect(center=(sx, tete_y - taille(17))))

        if echelle > 0.58 and habitant.get("afficher_nom", True):
            nom = self.police_details.render(habitant["nom"], True, (255, 244, 214))
            etiquette = self.police_details.render(habitant["metier"], True, (209, 213, 193))
            y_texte = tete_y - taille(28)
            fond = pygame.Rect(0, 0, max(nom.get_width(), etiquette.get_width()) + 12, nom.get_height() + etiquette.get_height() + 8)
            fond.midbottom = (sx, y_texte - taille(3))
            pygame.draw.rect(self.ecran, (27, 44, 39), fond, border_radius=max(2, taille(4)))
            self.ecran.blit(nom, nom.get_rect(center=(fond.centerx, fond.top + nom.get_height() // 2 + 3)))
            self.ecran.blit(etiquette, etiquette.get_rect(center=(fond.centerx, fond.bottom - etiquette.get_height() // 2 - 3)))

    def dessiner_cinematique(self, maintenant):
        if self.cinematique is None:
            return
        age = max(0, maintenant - self.cinematique_page_debut)
        fondu = min(1.0, age / 420)
        self.voile_cinematique.fill((8, 17, 21, round(210 * fondu)))
        self.ecran.blit(self.voile_cinematique, (0, 0))
        pygame.draw.rect(self.ecran, (8, 15, 17), (0, 0, LARGEUR_FENETRE, 46))
        pygame.draw.rect(self.ecran, (8, 15, 17), (0, HAUTEUR_FENETRE - 47, LARGEUR_FENETRE, 47))
        pygame.draw.line(self.ecran, (190, 148, 76), (70, 47), (930, 47), 1)
        pygame.draw.line(self.ecran, (190, 148, 76), (70, HAUTEUR_FENETRE - 48), (930, HAUTEUR_FENETRE - 48), 1)

        page = self.cinematique["pages"][self.cinematique_index]
        titre = self.grande_police.render(page["titre"], True, (255, 231, 168))
        titre.set_alpha(round(255 * fondu))
        self.ecran.blit(titre, titre.get_rect(center=(LARGEUR_FENETRE // 2, 105)))
        sous_titre = self.police.render(f"{self.cinematique['village']}  -  {self.cinematique['quete']}", True, (212, 224, 212))
        sous_titre.set_alpha(round(255 * fondu))
        self.ecran.blit(sous_titre, sous_titre.get_rect(center=(LARGEUR_FENETRE // 2, 145)))

        maintenant_s = maintenant / 1000
        for index in range(19):
            x = 95 + (index * 137 + round(math.sin(maintenant_s * 0.38 + index) * 18)) % 810
            y = 193 + (index * 59 + round(math.sin(maintenant_s * 0.7 + index * 1.3) * 16)) % 310
            rayon = 1 + index % 3
            pygame.draw.circle(self.ecran, (210, 177, 102), (x, y), rayon)
            pygame.draw.circle(self.ecran, (246, 226, 175), (x, y), max(1, rayon - 1))

        self.ecran.blit(self.aura_cinematique, (326, 226))
        self.ecran.blit(self.aura_cinematique, (525, 226))
        pygame.draw.ellipse(self.ecran, (42, 58, 48), (339, 463, 327, 27))
        habitant = dict(self.cinematique["habitant"])
        habitant["donneur_quete"] = False
        habitant["afficher_nom"] = False
        self.dessiner_villageois_perspective(400, 480, 2.75, habitant, maintenant)

        age = max(0, maintenant - self.cinematique_page_debut)
        if page.get("action") == "epee_plantee":
            self.dessiner_serment_epee(600, 468, age)
        else:
            self.dessiner_heros_cinematique(600, 468 + round(abs(math.sin(maintenant_s * 2.1)) * 2))

        panneau = pygame.Rect(70, 525, 860, 136)
        pygame.draw.rect(self.ecran, (13, 30, 29), panneau, border_radius=14)
        pygame.draw.rect(self.ecran, (191, 151, 83), panneau, 2, border_radius=14)
        nom = self.police.render(page["personnage"], True, (255, 222, 135))
        self.ecran.blit(nom, (panneau.x + 25, panneau.y + 17))
        mots = page["texte"].split()
        lignes = []
        ligne = ""
        for mot in mots:
            proposition = f"{ligne} {mot}".strip()
            if self.police.size(proposition)[0] > panneau.width - 54 and ligne:
                lignes.append(ligne)
                ligne = mot
            else:
                ligne = proposition
        if ligne:
            lignes.append(ligne)
        for index, texte in enumerate(lignes[:2]):
            rendu = self.police.render(texte, True, (245, 245, 229))
            self.ecran.blit(rendu, (panneau.x + 25, panneau.y + 50 + index * 28))

        nombre_pages = len(self.cinematique["pages"])
        for index in range(nombre_pages):
            couleur = (255, 221, 139) if index == self.cinematique_index else (105, 119, 108)
            pygame.draw.circle(self.ecran, couleur, (LARGEUR_FENETRE // 2 - (nombre_pages - 1) * 11 + index * 22, 489), 4)
        aide = self.police_details.render("E / ESPACE : continuer     ECHAP : passer la scene", True, (219, 220, 201))
        self.ecran.blit(aide, aide.get_rect(center=(LARGEUR_FENETRE // 2, 686)))

    def dessiner_heros_cinematique(self, hx, sol_y):
        pygame.draw.ellipse(self.ecran, (48, 39, 32), (hx - 32, sol_y - 46, 20, 46))
        pygame.draw.ellipse(self.ecran, (69, 49, 34), (hx + 5, sol_y - 46, 21, 46))
        pygame.draw.polygon(self.ecran, (67, 53, 42), [(hx - 31, sol_y - 13), (hx + 30, sol_y - 13), (hx + 40, sol_y), (hx - 41, sol_y)])
        pygame.draw.polygon(self.ecran, (45, 81, 47), [(hx - 35, sol_y - 104), (hx + 32, sol_y - 100), (hx + 43, sol_y - 19), (hx, sol_y - 30), (hx - 46, sol_y - 18)])
        pygame.draw.polygon(self.ecran, (56, 126, 64), [(hx - 23, sol_y - 108), (hx + 24, sol_y - 108), (hx + 31, sol_y - 45), (hx, sol_y - 37), (hx - 31, sol_y - 45)])
        pygame.draw.line(self.ecran, (192, 151, 90), (hx - 18, sol_y - 105), (hx - 3, sol_y - 51), 4)
        pygame.draw.line(self.ecran, (192, 151, 90), (hx + 18, sol_y - 105), (hx + 3, sol_y - 51), 4)
        pygame.draw.ellipse(self.ecran, (145, 92, 57), (hx - 48, sol_y - 93, 22, 51))
        pygame.draw.ellipse(self.ecran, (196, 149, 75), (hx - 43, sol_y - 87, 12, 37), 2)
        pygame.draw.rect(self.ecran, (135, 93, 58), (hx - 23, sol_y - 152, 46, 40), border_radius=10)
        pygame.draw.ellipse(self.ecran, (221, 177, 111), (hx - 22, sol_y - 166, 44, 43))
        pygame.draw.polygon(self.ecran, (48, 107, 61), [(hx - 30, sol_y - 155), (hx - 23, sol_y - 179), (hx + 19, sol_y - 178), (hx + 31, sol_y - 153), (hx + 18, sol_y - 146), (hx - 16, sol_y - 147)])
        pygame.draw.line(self.ecran, (92, 174, 99), (hx - 18, sol_y - 171), (hx + 14, sol_y - 171), 3)
        pygame.draw.polygon(self.ecran, (225, 187, 128), [(hx - 20, sol_y - 148), (hx - 31, sol_y - 151), (hx - 22, sol_y - 138)])
        pygame.draw.polygon(self.ecran, (225, 187, 128), [(hx + 20, sol_y - 148), (hx + 31, sol_y - 151), (hx + 22, sol_y - 138)])

    def dessiner_serment_epee(self, hx, sol_y, age):
        """Anime le heros qui saisit son epee, bondit et la plante au sol."""
        duree = 5200
        t = min(1.0, max(0.0, age / duree))
        saute = math.sin(min(1.0, max(0.0, (t - 0.27) / 0.42)) * math.pi) * 67
        y = sol_y - round(saute)
        impact = max(0.0, min(1.0, (t - 0.67) / 0.09))
        atterrit = max(0.0, min(1.0, (t - 0.76) / 0.14))
        ombre_largeur = round(30 + saute * 0.28)
        pygame.draw.ellipse(self.ecran, (44, 50, 39), (hx - ombre_largeur, sol_y - 5, ombre_largeur * 2, 13))

        if t < 0.76:
            self.dessiner_heros_cinematique(hx, y)
            main_x, main_y = hx + 26, y - 111
            pygame.draw.line(self.ecran, (48, 104, 57), (hx + 20, y - 110), (main_x, main_y), 9)
            pygame.draw.circle(self.ecran, (215, 169, 120), (main_x, main_y), 7)
            # Epee levee, puis abattue vers la terre pendant le saut.
            levee = min(1.0, max(0.0, (t - 0.08) / 0.25))
            plongee = min(1.0, max(0.0, (t - 0.53) / 0.23))
            pommeau = (
                round(hx + 17 + 35 * levee - 53 * plongee),
                round(y - 106 - 48 * levee + 93 * plongee),
            )
            pointe = (
                round(pommeau[0] + 18 - 21 * plongee),
                round(pommeau[1] - 83 + 153 * plongee),
            )
            self.dessiner_epee_cinematique(pointe, pommeau)
        else:
            self.dessiner_heros_cinematique(hx, sol_y)
            lame_x = hx - 24
            pointe = (lame_x + round(6 * (1 - atterrit)), sol_y + 5)
            pommeau = (lame_x + round(6 * (1 - atterrit)), sol_y - 91)
            self.dessiner_epee_cinematique(pointe, pommeau)
            if impact > 0:
                rayon = round(10 + impact * 45)
                pygame.draw.ellipse(self.ecran, (220, 188, 104), (lame_x - rayon, sol_y - 7, rayon * 2, 14), max(1, round(3 * (1 - impact) + 1)))
                for index in range(8):
                    angle = index * math.tau / 8 + age / 320
                    debut = (lame_x + round(math.cos(angle) * 14), sol_y - 5 + round(math.sin(angle) * 5))
                    fin = (lame_x + round(math.cos(angle) * 25), sol_y - 5 + round(math.sin(angle) * 10))
                    pygame.draw.line(self.ecran, (255, 220, 133), debut, fin, 2)

    def dessiner_epee_cinematique(self, pointe, pommeau):
        dx, dy = pointe[0] - pommeau[0], pointe[1] - pommeau[1]
        longueur = max(1.0, math.hypot(dx, dy))
        perpendiculaire = (-dy / longueur, dx / longueur)
        demi_largeur = 5
        lame = [
            (round(pointe[0] + perpendiculaire[0] * 1), round(pointe[1] + perpendiculaire[1] * 1)),
            (round(pommeau[0] + perpendiculaire[0] * demi_largeur), round(pommeau[1] + perpendiculaire[1] * demi_largeur)),
            (round(pommeau[0] - perpendiculaire[0] * demi_largeur), round(pommeau[1] - perpendiculaire[1] * demi_largeur)),
            (round(pointe[0] - perpendiculaire[0] * 1), round(pointe[1] - perpendiculaire[1] * 1)),
        ]
        pygame.draw.polygon(self.ecran, (71, 76, 74), lame)
        pygame.draw.polygon(self.ecran, (222, 232, 226), [lame[0], lame[1], (round((lame[0][0] + lame[1][0]) / 2), round((lame[0][1] + lame[1][1]) / 2))])
        pygame.draw.line(self.ecran, (255, 250, 220), pointe, pommeau, 1)
        garde_g = (round(pommeau[0] + perpendiculaire[0] * 14), round(pommeau[1] + perpendiculaire[1] * 14))
        garde_d = (round(pommeau[0] - perpendiculaire[0] * 14), round(pommeau[1] - perpendiculaire[1] * 14))
        pygame.draw.line(self.ecran, (184, 135, 61), garde_g, garde_d, 5)
        pygame.draw.line(self.ecran, (89, 56, 36), pommeau, (round(pommeau[0] - dx / longueur * 19), round(pommeau[1] - dy / longueur * 19)), 7)
        pygame.draw.circle(self.ecran, (240, 205, 112), pommeau, 4)

    def dessiner_joueur_perspective(self, maintenant):
        projection = self.projeter_camera(self.joueur_x, self.joueur_y)
        if projection is None:
            return
        sx, sy, profondeur = projection
        echelle = min(1.65, 4.6 / profondeur)
        if maintenant < self.invulnerable_jusqua and maintenant // 100 % 2 == 0:
            return

        phase = self.temps_marche * 10 if self.en_marche else 0
        sprite = pygame.Surface((112, 156), pygame.SRCALPHA)
        facteur = 2

        def posture_y(y):
            if self.accroupi:
                return 74 + (y - 74) * 0.68
            return y

        def posture_x(x, y):
            if self.accroupi:
                inclinaison = max(0.0, min(1.0, (52 - y) / 52))
                return x + 2.6 * inclinaison
            return x

        def point(x, y):
            return round(posture_x(x, y) * facteur), round(posture_y(y) * facteur)

        def ellipse(color, rect, width=0):
            x, y, largeur, hauteur = rect
            centre_x = posture_x(x + largeur / 2, y + hauteur / 2)
            haut = posture_y(y)
            bas = posture_y(y + hauteur)
            pygame.draw.ellipse(
                sprite,
                color,
                pygame.Rect(
                    round((centre_x - largeur / 2) * facteur),
                    round(haut * facteur),
                    round(largeur * facteur),
                    round((bas - haut) * facteur),
                ),
                round(width * facteur),
            )

        def polygon(color, points):
            pygame.draw.polygon(sprite, color, [point(x, y) for x, y in points])

        def line(color, start, end, width=1):
            pygame.draw.line(sprite, color, point(*start), point(*end), max(1, round(width * facteur)))

        def circle(color, center, radius, width=0):
            pygame.draw.circle(sprite, color, point(*center), max(1, round(radius * facteur)), round(width * facteur))

        pas = math.sin(phase) * 4 if self.en_marche else 0
        leve_gauche = max(0, math.cos(phase)) * 2 if self.en_marche else 0
        leve_droit = max(0, -math.cos(phase)) * 2 if self.en_marche else 0
        rebond = abs(math.sin(phase * 2)) * 1.2 if self.en_marche else 0
        souffle = math.sin(maintenant / 650) * 0.55 if not self.en_marche else 0
        rebond += souffle
        cape_souffle = math.sin(maintenant / 210 + phase) * 2.1 + pas * 0.34

        ellipse((30, 35, 32, 100), (12, 67, 31, 7))

        # Boots and articulated trousers.
        polygon((49, 44, 36), [(17, 49), (26, 49), (26, 61), (22, 68 - leve_gauche), (15 + pas, 68 - leve_gauche), (16, 62)])
        polygon((68, 55, 43), [(17, 51), (23, 51), (22, 61), (18 + pas, 66 - leve_gauche), (15 + pas, 66 - leve_gauche), (16, 60)])
        polygon((39, 35, 31), [(27, 49), (36, 49), (37, 60), (41 - pas, 67 - leve_droit), (34 - pas, 68 - leve_droit), (29, 61)])
        polygon((60, 48, 39), [(29, 51), (35, 51), (35, 60), (39 - pas, 65 - leve_droit), (35 - pas, 66 - leve_droit), (30, 60)])
        line((97, 72, 49), (19, 57), (22, 61), 1)
        line((100, 75, 51), (32, 57), (35, 61), 1)
        polygon((48, 39, 31), [(14 + pas, 65 - leve_gauche), (22 + pas, 65 - leve_gauche), (25 + pas, 70 - leve_gauche), (24 + pas, 73 - leve_gauche), (11 + pas, 73 - leve_gauche), (10 + pas, 71 - leve_gauche)])
        polygon((56, 45, 35), [(31 - pas, 65 - leve_droit), (39 - pas, 65 - leve_droit), (44 - pas, 70 - leve_droit), (43 - pas, 73 - leve_droit), (30 - pas, 73 - leve_droit), (28 - pas, 71 - leve_droit)])
        line((137, 99, 66), (13 + pas, 71 - leve_gauche), (21 + pas, 71 - leve_gauche), 1)
        line((139, 101, 68), (33 - pas, 71 - leve_droit), (41 - pas, 71 - leve_droit), 1)

        # Travel pack, bedroll and shoulder straps sit behind the tunic.
        ellipse((47, 37, 29), (8, 28, 15, 27))
        ellipse((115, 78, 44), (9, 30, 12, 22))
        ellipse((145, 111, 65), (10, 32, 8, 4))
        line((66, 45, 31), (10, 36), (18, 38), 1)
        line((173, 139, 83), (12, 43), (18, 43), 1)
        line((74, 51, 34), (10, 49), (18, 49), 1)
        line((184, 149, 92), (11, 34), (11, 51), 1)
        polygon((27, 78, 51), [(35, 25), (41, 28), (45, 39 + cape_souffle * 0.25), (49 + cape_souffle, 54), (43, 61), (37, 54), (34, 39)])
        polygon((43, 111, 71), [(37, 29), (41, 31), (43, 43 + cape_souffle * 0.25), (45 + cape_souffle * 0.55, 53), (41, 55), (38, 46)])
        line((130, 171, 111), (39, 34), (43, 49 + cape_souffle * 0.25), 0.9)
        line((177, 151, 95), (16, 31), (22, 39), 1.2)
        line((177, 151, 95), (37, 31), (31, 39), 1.2)

        # Coat silhouette, inset panels and fabric folds.
        polygon((19, 49, 34), [(18, 23), (25, 21), (31, 23), (38, 21), (43, 25), (47, 50), (42, 57), (14, 57), (9, 50), (13, 28)])
        polygon((48, 105, 57), [(19, 25), (26, 23), (30, 26), (28, 54), (15, 53), (13, 49)])
        polygon((35, 83, 46), [(31, 25), (38, 24), (42, 27), (45, 49), (40, 54), (30, 54)])
        polygon((31, 75, 43), [(18, 27), (25, 24), (28, 27), (24, 34), (18, 32)])
        polygon((58, 119, 63), [(38, 26), (42, 29), (44, 43), (40, 48), (35, 34)])
        polygon((24, 64, 41), [(15, 50), (28, 53), (27, 59), (20, 62), (13, 56)])
        polygon((24, 64, 41), [(31, 53), (43, 49), (46, 56), (39, 61), (29, 59)])
        line((152, 182, 112), (17, 29), (14, 49), 1)
        line((100, 153, 88), (42, 30), (44, 47), 1)
        line((17, 54, 35), (17, 51), (41, 53), 1)
        for seam_y in (32, 39, 46):
            line((112, 155, 91), (18, seam_y), (21, seam_y + 1), 0.7)
        for button_y in (34, 40, 46):
            circle((207, 177, 112), (29, button_y), 0.75)
            circle((75, 67, 51), (29, button_y), 0.3)
        line((19, 57, 40), (19, 35), (17, 44), 1)
        line((132, 161, 93), (23, 37), (22, 42), 0.8)
        line((19, 57, 40), (40, 34), (42, 43), 1)
        line((132, 161, 93), (37, 36), (38, 41), 0.8)

        # A fitted collar, leather belt, engraved buckle and field pouches.
        polygon((28, 70, 43), [(19, 24), (25, 22), (29, 28), (33, 22), (40, 25), (34, 32), (27, 34)])
        polygon((195, 153, 99), [(24, 31), (29, 35), (34, 31), (31, 39), (27, 39)])
        polygon((222, 190, 125), [(35, 25), (39, 25), (40, 28), (36, 29)])
        circle((244, 220, 151), (38, 27), 0.9)
        line((74, 48, 32), (15, 48), (42, 47), 3)
        line((174, 127, 73), (16, 47), (41, 46), 0.8)
        polygon((43, 36, 29), [(34, 44), (40, 43), (42, 51), (35, 52)])
        polygon((122, 85, 45), [(35, 44), (40, 44), (40, 50), (35, 50)])
        pygame.draw.rect(sprite, (222, 190, 112), pygame.Rect(*point(27, 44), round(4 * facteur), round(5 * facteur)), border_radius=2)
        pygame.draw.rect(sprite, (83, 60, 39), pygame.Rect(*point(28, 45), round(2 * facteur), round(3 * facteur)), border_radius=1)
        line((185, 145, 87), (14, 48), (14, 53), 1)
        line((83, 57, 38), (17, 51), (21, 51), 1)

        # Neck, ears, layered hair and the back of a shaped travel hood.
        polygon((120, 78, 53), [(23, 18), (32, 18), (33, 26), (24, 27)])
        ellipse((69, 43, 31), (20, 7 + rebond, 17, 22))
        ellipse((96, 56, 35), (21, 8 + rebond, 15, 18))
        ellipse((139, 88, 48), (23, 9 + rebond, 11, 13))
        ellipse((77, 43, 29), (21, 16 + rebond, 7, 9))
        ellipse((112, 67, 36), (31, 15 + rebond, 6, 9))
        ellipse((91, 54, 34), (18, 15 + rebond, 8, 14))
        ellipse((105, 62, 39), (33, 15 + rebond, 7, 13))
        polygon((226, 185, 126), [(20, 16 + rebond), (13, 13 + rebond), (19, 20 + rebond), (22, 21 + rebond)])
        polygon((226, 185, 126), [(37, 16 + rebond), (45, 13 + rebond), (39, 20 + rebond), (36, 21 + rebond)])
        for index in range(4):
            line((181, 124, 68), (22 + index * 2, 20 + rebond), (22 + index * 2.2, 25 + rebond), 0.7)
        ellipse((25, 78, 47), (16, 5 + rebond, 24, 15))
        ellipse((37, 111, 64), (18, 5 + rebond, 20, 11))
        polygon((45, 133, 74), [(17, 12 + rebond), (19, 7 + rebond), (24, 4 + rebond), (31, 3 + rebond), (37, 7 + rebond), (40, 13 + rebond), (36, 16 + rebond), (33, 12 + rebond), (27, 10 + rebond), (22, 13 + rebond)])
        polygon((66, 157, 91), [(20, 8 + rebond), (25, 5 + rebond), (31, 5 + rebond), (36, 9 + rebond), (30, 8 + rebond), (25, 11 + rebond)])
        line((22, 70, 44), (19, 13 + rebond), (37, 14 + rebond), 1.4)
        line((129, 192, 111), (23, 7 + rebond), (29, 5 + rebond), 0.8)
        circle((211, 180, 105), (37, 12 + rebond), 1.1)
        circle((241, 219, 152), (37, 12 + rebond), 0.5)
        ellipse((245, 223, 180), (35, 17 + rebond, 1.5, 1.2))
        circle((63, 48, 38), (36, 17 + rebond), 0.45)
        line((108, 63, 41), (38, 20 + rebond), (40, 22 + rebond), 0.65)
        line((139, 75, 60), (36, 25 + rebond), (39, 25 + rebond), 0.55)
        line((77, 43, 35), (23, 17 + rebond), (26, 16 + rebond), 0.7)
        line((77, 43, 35), (31, 16 + rebond), (34, 17 + rebond), 0.7)
        line((151, 91, 65), (29, 18 + rebond), (29.5, 20 + rebond), 0.65)
        line((119, 65, 53), (28, 23 + rebond), (31, 23 + rebond), 0.6)
        line((142, 75, 61), (18, 16 + rebond), (20, 18 + rebond), 0.7)
        line((142, 75, 61), (40, 16 + rebond), (38, 18 + rebond), 0.7)

        # Original pointed forest cap, layered over the hair.
        polygon((24, 66, 43), [(16, 13 + rebond), (20, 7 + rebond), (28, 5 + rebond), (35, 2 + rebond), (37, 0 + rebond), (38, 6 + rebond), (46, 10 + rebond), (41, 14 + rebond), (38, 17 + rebond), (22, 17 + rebond)])
        polygon((47, 119, 69), [(19, 12 + rebond), (22, 8 + rebond), (30, 6 + rebond), (36, 3 + rebond), (36, 8 + rebond), (42, 11 + rebond), (38, 13 + rebond), (24, 15 + rebond)])
        polygon((31, 88, 52), [(35, 3 + rebond), (37, 1 + rebond), (37, 7 + rebond), (42, 10 + rebond), (37, 9 + rebond)])
        line((151, 190, 113), (22, 11 + rebond), (34, 8 + rebond), 0.9)
        line((32, 83, 51), (20, 14 + rebond), (39, 15 + rebond), 1.1)
        circle((225, 196, 128), (35, 10 + rebond), 1.0)
        line((26, 67, 44), (19, 17 + rebond), (39, 17 + rebond), 0.7)
        line((28, 73, 48), (24, 12 + rebond), (27, 10 + rebond), 0.65)

        # Sleeves, articulated elbows and leather gloves.
        ellipse((25, 71, 42), (10, 25, 11, 16))
        ellipse((63, 126, 70), (11, 26, 8, 13))
        line((35, 91, 50), (13, 35), (10, 45 + pas * 0.35), 4.5)
        line((134, 178, 116), (13, 35), (11, 44 + pas * 0.35), 1)
        ellipse((23, 62, 39), (38, 25, 10, 16))
        ellipse((54, 110, 61), (39, 27, 8, 12))
        line((31, 82, 45), (43, 35), (47, 45 - pas * 0.35), 4.5)
        line((125, 170, 108), (42, 34), (46, 43 - pas * 0.35), 1)
        ellipse((86, 58, 39), (8, 42 + pas * 0.35, 5, 5))
        ellipse((190, 139, 93), (45, 42 - pas * 0.35, 5, 5))
        line((102, 70, 43), (9, 44 + pas * 0.35), (12, 46 + pas * 0.35), 1)
        line((225, 178, 122), (46, 44 - pas * 0.35), (48, 46 - pas * 0.35), 1)
        line((170, 125, 77), (9, 39 + pas * 0.35), (14, 41 + pas * 0.35), 0.7)
        line((170, 125, 77), (42, 40 - pas * 0.35), (47, 38 - pas * 0.35), 0.7)
        line((33, 63, 42), (11, 31), (18, 34), 1)
        line((33, 63, 42), (39, 32), (44, 30), 1)

        # Shield with a metal rim and painted heraldic stripe.
        if self.bouclier_equipe:
            teinte = BOUCLIERS[self.bouclier_equipe]["couleur"]
            ombre_bouclier = tuple(max(0, valeur - 48) for valeur in teinte)
            lumiere_bouclier = tuple(min(255, valeur + 42) for valeur in teinte)
            polygon((34, 36, 31), [(5, 32), (15, 29), (20, 33), (18, 48), (12, 55), (6, 50)])
            polygon(ombre_bouclier, [(6, 33), (15, 31), (18, 34), (16, 47), (12, 52), (8, 48)])
            polygon(teinte, [(8, 34), (14, 33), (16, 35), (15, 46), (12, 49), (9, 47)])
            line(lumiere_bouclier, (11, 34), (11, 48), 1.1)
            line((224, 194, 127), (7, 34), (14, 33), 0.9)
            line(ombre_bouclier, (8, 47), (15, 46), 1)
            circle((226, 199, 128), (12, 41), 1.2)

        # The carried weapon changes shape with the selected equipment.
        arme = ARMES[self.arme_equipee]
        if arme["type"] == "arc":
            line((63, 43, 30), (38, 16), (44, 27), 2.5)
            pygame.draw.aalines(sprite, (129, 83, 48), False, [point(38, 16), point(44, 22), point(43, 30), point(39, 38), point(36, 41)])
            pygame.draw.aalines(sprite, (213, 200, 166), False, [point(38, 16), point(36, 29), point(36, 41)])
            line((183, 173, 147), (36, 29), (43, 28), 0.7)
            for index in range(3):
                line((210, 199, 166), (34 + index * 1.6, 17), (33 + index * 1.6, 10), 0.7)
        else:
            line((66, 45, 31), (34, 48), (43, 27), 4)
            line((162, 119, 72), (35, 46), (42, 28), 1.8)
            if self.arme_equipee == "hache_guerre":
                polygon((49, 53, 54), [(40, 31), (42, 24), (46, 21), (50, 23), (48, 29), (44, 33)])
                polygon((196, 205, 206), [(44, 25), (47, 23), (48, 25), (46, 29), (43, 29)])
                line((236, 234, 218), (46, 24), (48, 23), 0.7)
            else:
                polygon((64, 68, 69), [(41, 31), (43, 24), (47, 14), (48, 16), (45, 28)])
                polygon((201, 207, 203), [(44, 24), (47, 14), (48, 16), (45, 27)])
                line((238, 231, 199), (46, 18), (48, 15), 0.7)
            line((205, 169, 94), (39, 29), (45, 32), 1.5)
            line((70, 49, 34), (38, 47), (42, 50), 2)
        ellipse((79, 54, 34), (34, 16, 7, 12))
        line((171, 131, 78), (35, 18), (39, 19), 0.7)
        for index in range(3):
            line((198, 184, 145), (35 + index * 1.6, 17), (34 + index * 1.6, 11), 0.7)
            polygon((93, 80, 61), [(33 + index * 1.6, 11), (34 + index * 1.6, 9), (35 + index * 1.6, 11)])

        decorrel = self.direction[0] * -math.sin(self.camera_yaw) + self.direction[1] * math.cos(self.camera_yaw)
        angle = max(-16, min(16, decorrel * 15))
        largeur = max(1, round(50 * echelle))
        hauteur = max(1, round(74 * echelle))
        dissimule = self.joueur_dissimule()
        sprite = pygame.transform.smoothscale(sprite, (largeur, hauteur))
        if dissimule:
            sprite.set_alpha(205)
        if abs(angle) > 1:
            sprite = pygame.transform.rotate(sprite, angle)
        pygame.draw.ellipse(
            self.ecran,
            (30, 38, 33),
            (sx - round(17 * echelle), sy - round(3 * echelle), round(34 * echelle), round(8 * echelle)),
        )
        if self.esquive_jusqua > maintenant:
            for train in range(3):
                debut = (sx - round((18 + train * 7) * echelle), sy - round((11 + train * 3) * echelle))
                fin = (sx - round(5 * echelle), sy - round((10 + train * 3) * echelle))
                pygame.draw.line(self.ecran, (194, 213, 191), debut, fin, max(1, round(echelle)))
        if self.special_jusqua > maintenant:
            progression_speciale = max(0.0, min(1.0, (maintenant - self.special_debut) / 520))
            rayon_special = max(5, round((20 + progression_speciale * 18) * echelle))
            cercle_special = pygame.Rect(
                sx - rayon_special,
                sy - round(35 * echelle) - rayon_special,
                rayon_special * 2,
                rayon_special * 2,
            )
            pygame.draw.arc(
                self.ecran,
                (255, 216, 126),
                cercle_special,
                progression_speciale * math.tau,
                progression_speciale * math.tau + math.pi * 1.55,
                max(1, round(3 * echelle)),
            )
        self.ecran.blit(sprite, sprite.get_rect(midbottom=(sx, sy - round(rebond * echelle))))
        if maintenant < self.attaque_affichage_jusqua:
            self.dessiner_arme_attaque_perspective(sx, sy, echelle, maintenant)

    def dessiner_arme_attaque_perspective(self, sx, sy, echelle, maintenant):
        """Dessine l'arme equipee dans la main pendant le coup porte."""
        progression = max(
            0.0,
            min(1.0, (maintenant - self.attaque_affichage_debut) / 420),
        )
        depart = (round(sx + 9 * echelle), round(sy - 31 * echelle))
        coude = (round(sx + 5 * echelle), round(sy - 38 * echelle))
        pygame.draw.line(
            self.ecran,
            (31, 73, 48),
            coude,
            depart,
            max(2, round(5 * echelle)),
        )
        pygame.draw.line(
            self.ecran,
            (192, 142, 91),
            (coude[0] + 1, coude[1]),
            (depart[0] + 1, depart[1]),
            max(1, round(2 * echelle)),
        )

        angle = -2.15 + progression * 2.25
        longueur = 37 * echelle
        ux, uy = math.cos(angle), math.sin(angle)
        px, py = -uy, ux
        pommeau = (
            round(depart[0] - ux * 7 * echelle),
            round(depart[1] - uy * 7 * echelle),
        )
        garde = (
            round(depart[0] + ux * 2 * echelle),
            round(depart[1] + uy * 2 * echelle),
        )
        pointe = (
            round(depart[0] + ux * longueur),
            round(depart[1] + uy * longueur),
        )
        pygame.draw.line(
            self.ecran,
            (76, 48, 32),
            pommeau,
            garde,
            max(2, round(5 * echelle)),
        )
        pygame.draw.line(
            self.ecran,
            (224, 186, 91),
            (round(garde[0] + px * 6 * echelle), round(garde[1] + py * 6 * echelle)),
            (round(garde[0] - px * 6 * echelle), round(garde[1] - py * 6 * echelle)),
            max(2, round(3 * echelle)),
        )
        if self.arme_equipee == "hache_guerre":
            tete = (
                round(pointe[0] - ux * 5 * echelle),
                round(pointe[1] - uy * 5 * echelle),
            )
            bord = (
                round(tete[0] + px * 8 * echelle),
                round(tete[1] + py * 8 * echelle),
            )
            pygame.draw.line(
                self.ecran,
                (69, 75, 79),
                (round(tete[0] - px * 8 * echelle), round(tete[1] - py * 8 * echelle)),
                bord,
                max(3, round(8 * echelle)),
            )
            pygame.draw.line(
                self.ecran,
                (213, 221, 218),
                (round(bord[0] - ux * 3 * echelle), round(bord[1] - uy * 3 * echelle)),
                bord,
                max(1, round(2 * echelle)),
            )
            return

        largeur = 4 * echelle
        lame = [
            (round(garde[0] + px * largeur), round(garde[1] + py * largeur)),
            (round(pointe[0] + px * largeur * 0.35), round(pointe[1] + py * largeur * 0.35)),
            pointe,
            (round(pointe[0] - px * largeur * 0.35), round(pointe[1] - py * largeur * 0.35)),
            (round(garde[0] - px * largeur), round(garde[1] - py * largeur)),
        ]
        pygame.draw.polygon(self.ecran, (53, 61, 64), lame)
        pygame.draw.line(
            self.ecran,
            (235, 239, 226),
            (round(garde[0] + px * 1.4 * echelle), round(garde[1] + py * 1.4 * echelle)),
            (round(pointe[0] + px * 0.2 * echelle), round(pointe[1] + py * 0.2 * echelle)),
            max(1, round(1.5 * echelle)),
        )
        pygame.draw.circle(
            self.ecran,
            (241, 205, 112),
            pommeau,
            max(1, round(2 * echelle)),
        )

    def dessiner(self, maintenant):
        """Dessine le monde avec une camera perspective suiveuse."""
        self._projection_cache.clear()
        self.actualiser_ambiance()
        self.dessiner_ciel()
        self.dessiner_terrain_perspective()
        self.dessiner_brume_horizon()

        avant_x, avant_y = math.cos(self.camera_yaw), math.sin(self.camera_yaw)
        cote_x, cote_y = -avant_y, avant_x
        elements = []
        for x, y in self.arbres | self.rochers | self.ruines:
            elements.append((x + 0.5, y + 0.5, "arbre" if (x, y) in self.arbres else "rocher" if (x, y) in self.rochers else "ruine"))
        elements.extend((item["x"], item["y"], "decoration", item) for item in self.decorations)
        if not self.dans_grotte:
            for village in self.villages:
                elements.append((village["x"], village["y"], "village", village))
                elements.extend((maison["x"], maison["y"], "village_maison", maison) for maison in village["maisons"])
                habitant_proche = min(
                    village["habitants"],
                    key=lambda personne: math.hypot(personne["x"] - self.joueur_x, personne["y"] - self.joueur_y),
                )
                proche = math.hypot(habitant_proche["x"] - self.joueur_x, habitant_proche["y"] - self.joueur_y) < 3.5
                for habitant in village["habitants"]:
                    phase = pygame.time.get_ticks() / 2200 + habitant["phase"]
                    position = dict(habitant)
                    position["x"] += math.sin(phase) * 0.08
                    position["y"] += math.cos(phase * 0.8) * 0.06
                    position["afficher_nom"] = habitant is habitant_proche and proche and self.cinematique is None
                    elements.append((position["x"], position["y"], "villageois", position))
            elements.extend((grotte["x"], grotte["y"], "entree_grotte", grotte) for grotte in self.grottes)
            for repaire in self.repaire_monstres:
                elements.append((repaire["x"] - 1.0, repaire["y"] + 0.3, "repaire", repaire))
                feu_x, feu_y = repaire.get("feu", (repaire["x"] + 0.5, repaire["y"] + 0.5))
                elements.append((feu_x, feu_y, "feu_camp", repaire))
        elements.extend((coffre["x"], coffre["y"], "coffre", coffre) for coffre in self.coffres)
        if self.dans_grotte and self.grotte_active:
            enigme = self.grotte_active.get("enigme")
            if enigme and not enigme["resolue"]:
                elements.extend((dalle["x"], dalle["y"], "rune", dalle) for dalle in enigme["dalles"])
            elements.extend((x + 0.5, y + 0.5, "piege") for x, y in self.grotte_active.get("pieges", ()))
        elements.extend((ennemi["x"], ennemi["y"], "ennemi", ennemi) for ennemi in self.ennemis)
        elements.extend((objet["x"], objet["y"], "objet", objet) for objet in self.objets)
        elements.extend((fleche["x"], fleche["y"], "fleche", fleche) for fleche in self.projectiles)
        elements.append((self.joueur_x, self.joueur_y, "joueur"))

        visibles = []
        for element in elements:
            if math.hypot(element[0] - self.joueur_x, element[1] - self.joueur_y) > 33:
                continue
            projection = self.projeter_camera(element[0], element[1])
            if projection and projection[2] < 30:
                visibles.append((projection[2], element))
        for profondeur, element in sorted(visibles, reverse=True, key=lambda item: item[0]):
            x, y, sorte = element[:3]
            if sorte == "joueur":
                self.dessiner_joueur_perspective(maintenant)
            elif sorte in ("arbre", "rocher", "ruine", "decoration"):
                self.dessiner_decor_perspective(
                    sorte,
                    x,
                    y,
                    profondeur,
                    element[3] if sorte == "decoration" and len(element) > 3 else None,
                )
            elif sorte == "fleche":
                projection = self.projeter_camera(x, y, 0.5)
                if projection:
                    sx, sy, echelle = projection
                    direction_x = element[3]["dx"] * cote_x + element[3]["dy"] * cote_y
                    longueur = max(0.01, math.hypot(direction_x, 0.25))
                    fin = (round(sx + direction_x / longueur * 12 / echelle), round(sy - 10 / echelle))
                    pygame.draw.line(self.ecran, (222, 210, 173), (sx, sy), fin, max(1, round(2 / echelle)))
            else:
                self.dessiner_decor_perspective(sorte, x, y, profondeur, element[3] if len(element) > 3 else None)

        rx, ry, profondeur = self.projeter_camera(RELIQUE_X, RELIQUE_Y, 0.0) or (0, 0, 0)
        if profondeur:
            echelle = min(1.5, 4.2 / profondeur)
            pygame.draw.circle(self.ecran, (255, 220, 111), (rx, ry - round(21 * echelle)), max(3, round(13 * echelle)), max(1, round(3 * echelle)))
            pygame.draw.polygon(self.ecran, (255, 239, 157), [(rx, ry - round(34 * echelle)), (rx + round(8 * echelle), ry - round(20 * echelle)), (rx, ry - round(5 * echelle)), (rx - round(8 * echelle), ry - round(20 * echelle))])

        if not self.dans_grotte:
            alpha_nuit = round(105 * (1 - self.lumiere_jour))
            if alpha_nuit:
                self.filtre_nuit.fill((12, 19, 45, alpha_nuit))
                self.ecran.blit(self.filtre_nuit, (0, 0))
            alpha_crepuscule = round(18 * self.lumiere_crepuscule)
            if alpha_crepuscule:
                self.filtre_crepuscule.fill((255, 156, 100, alpha_crepuscule))
                self.ecran.blit(self.filtre_crepuscule, (0, 0))
            self.dessiner_meteo(maintenant)

        self.ecran.blit(self.vignette, (0, 0))
        if self.cinematique is None:
            self.dessiner_interface()
            if self.dans_grotte and self.grotte_active and self.grotte_active.get("enigme"):
                enigme = self.grotte_active["enigme"]
                progression = len(enigme["ordre"]) if enigme["resolue"] else enigme["progression"]
                texte_runes = self.police.render(f"Temple des runes   {progression}/3", True, (205, 198, 248))
                fond_runes = pygame.Surface((texte_runes.get_width() + 24, 34), pygame.SRCALPHA)
                fond_runes.fill((25, 25, 36, 205))
                self.ecran.blit(fond_runes, (LARGEUR_FENETRE // 2 - fond_runes.get_width() // 2, 16))
                self.ecran.blit(texte_runes, texte_runes.get_rect(center=(LARGEUR_FENETRE // 2, 33)))
        if self.inventaire_ouvert:
            self.dessiner_inventaire()
        if self.termine:
            voile = pygame.Surface((LARGEUR_FENETRE, HAUTEUR_FENETRE), pygame.SRCALPHA)
            voile.fill((10, 20, 22, 185))
            self.ecran.blit(voile, (0, 0))
            message = "Tu as trouve la relique !" if self.gagne else "GAME OVER"
            texte = self.grande_police.render(message, True, BLANC)
            aide_texte = (
                "Entree : reprendre ou tu en etais     Echap : quitter"
                if self.game_over
                else "Appuie sur Echap pour quitter"
            )
            aide = self.police.render(aide_texte, True, BLANC)
            self.ecran.blit(texte, texte.get_rect(center=(LARGEUR_FENETRE // 2, HAUTEUR_FENETRE // 2 - 20)))
            self.ecran.blit(aide, aide.get_rect(center=(LARGEUR_FENETRE // 2, HAUTEUR_FENETRE // 2 + 35)))
        elif self.cinematique is not None:
            self.dessiner_cinematique(maintenant)

        pygame.display.flip()

    def lancer(self):
        """Lance la boucle de jeu jusqu'a la fermeture de la fenetre."""
        en_cours = True
        while en_cours:
            dt = min(self.horloge.tick(FPS) / 1000, 0.04)
            maintenant = pygame.time.get_ticks()
            for evenement in pygame.event.get():
                if evenement.type == pygame.QUIT:
                    en_cours = False
                elif evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1 and self.cinematique is not None:
                    self.avancer_cinematique(maintenant)
                elif evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 3:
                    self.camera_drag = True
                elif evenement.type == pygame.MOUSEBUTTONUP and evenement.button == 3:
                    self.camera_drag = False
                elif evenement.type == pygame.MOUSEMOTION and self.camera_drag and not self.inventaire_ouvert and self.cinematique is None:
                    self.camera_yaw -= evenement.rel[0] * 0.006
                elif evenement.type == pygame.KEYDOWN:
                    if evenement.key == pygame.K_F5:
                        self.sauvegarder_partie()
                    elif evenement.key == pygame.K_F9:
                        self.charger_partie()
                    elif self.cinematique is not None:
                        if evenement.key == pygame.K_ESCAPE:
                            self.cinematique = None
                            self.dire("La scene est passee.")
                        elif evenement.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.avancer_cinematique(maintenant)
                    elif self.game_over and evenement.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.reprendre_apres_mort()
                    elif evenement.key == pygame.K_ESCAPE:
                        en_cours = False
                    elif evenement.key == pygame.K_i and not self.termine:
                        self.inventaire_ouvert = not self.inventaire_ouvert
                    elif self.inventaire_ouvert:
   
                        elements = self.elements_inventaire()
                        if evenement.key == pygame.K_UP:
                            self.inventaire_index = (self.inventaire_index - 1) % len(elements)
                        elif evenement.key == pygame.K_DOWN:
                            self.inventaire_index = (self.inventaire_index + 1) % len(elements)
                        elif evenement.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.choisir_inventaire()
                    elif evenement.key == pygame.K_SPACE and not self.termine:
                        self.frapper(maintenant)
                    elif evenement.key == pygame.K_x and not self.termine:
                        self.esquiver(maintenant)
                    elif evenement.key == pygame.K_c and not self.termine:
                        self.attaque_speciale(maintenant)
                    elif evenement.key == pygame.K_e and not self.termine:
                        self.interagir()
                    elif evenement.key == pygame.K_f and not self.termine:
                        self.manger(maintenant)

            self.mettre_a_jour(dt, maintenant, pygame.key.get_pressed())
            self.dessiner(maintenant)

        pygame.quit()


if __name__ == "__main__":
    Aventure().lancer()
