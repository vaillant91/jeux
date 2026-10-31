import math
import random
import pygame

# Course de nuages : petit jeu arcade en perspective, dessine sans image externe.
pygame.init()
LARGEUR, HAUTEUR = 1100, 700
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Nuage Express — la course licorne")
horloge = pygame.time.Clock()

BLANC = (255, 255, 255)
ROSE = (255, 130, 190)
VIOLET = (111, 91, 190)
font = pygame.font.SysFont("segoeui", 23, bold=True)
titre = pygame.font.SysFont("segoeui", 54, bold=True)
petit = pygame.font.SysFont("segoeui", 17)

# Ciel pre-calcule : le decor garde un bon framerate pendant la course.
FOND_CIEL = pygame.Surface((LARGEUR, HAUTEUR))
for _y in range(HAUTEUR):
    _k = _y / HAUTEUR
    _haut, _bas = (75, 158, 224), (205, 231, 255)
    _couleur = tuple(int(_haut[i]*(1-_k)+_bas[i]*_k) for i in range(3))
    pygame.draw.line(FOND_CIEL, _couleur, (0, _y), (LARGEUR, _y))
HALO_SOLEIL = pygame.Surface((260, 260), pygame.SRCALPHA)
for _r, _a in ((118, 9), (92, 13), (67, 22), (43, 45)):
    pygame.draw.circle(HALO_SOLEIL, (255, 244, 190, _a), (130, 130), _r)

# Le ruban de nuages se resserre vers l'horizon, comme une route en 3D.
HORIZON = 205
joueur_x = 0.0
vitesse = 0.0
distance = 0.0
accelerateurs = []
particules = []
bots = []
feu_z = 0.45
temps_penalite = 0.0
message_feu = 0.0
nitro = 100.0
compte_a_rebours = 3.0
boosts_pris = 0
etat = "titre"
temps = 0.0


def texte(surface, message, police, couleur, pos, centre=True):
    image = police.render(message, True, couleur)
    rect = image.get_rect(center=pos) if centre else image.get_rect(topleft=pos)
    surface.blit(image, rect)


def nuage(surface, x, y, echelle, couleur=(255, 255, 255), ombre=True):
    x, y, e = int(x), int(y), max(1, int(echelle))
    if ombre:
        c = (max(0, couleur[0]-30), max(0, couleur[1]-34), max(0, couleur[2]-23))
        pygame.draw.ellipse(surface, c, (x-e, y+e//3, e*2, max(3, e//2)))
    pygame.draw.circle(surface, couleur, (x-e//2, y), e//2)
    pygame.draw.circle(surface, couleur, (x, y-e//4), int(e*.65))
    pygame.draw.circle(surface, couleur, (x+e//2, y), e//2)
    pygame.draw.ellipse(surface, couleur, (x-e, y-e//5, e*2, e*4//5))


def ciel(surface, t):
    surface.blit(FOND_CIEL, (0, 0))
    surface.blit(HALO_SOLEIL, (790, 30))
    pygame.draw.circle(surface, (255, 249, 218), (920, 160), 31)
    pygame.draw.circle(surface, (255, 255, 240), (910, 151), 9)
    for i in range(9):
        x = (i*173 - int(t*17)) % (LARGEUR+220) - 100
        y = 110 + (i*47 % 95)
        nuage(surface, x, y, 54 + i % 3 * 13, (245, 250, 255), False)


def route(surface, t):
    # Base pastel sous la route.
    pygame.draw.rect(surface, (200, 229, 255), (0, HORIZON, LARGEUR, HAUTEUR-HORIZON))
    # Nuages de fond, très grands et défilant lentement.
    for i in range(13):
        x = (i*112 - int(t*36)) % (LARGEUR+250) - 100
        y = 260 + (i*71 % 370)
        nuage(surface, x, y, 72 + (i*19 % 50), (245, 250, 255), True)
    # Route trapézoïdale en plusieurs bandes pour matérialiser la profondeur.
    centre = LARGEUR//2 - int(joueur_x*175)
    proche_g, proche_d = centre-480, centre+480
    loin_g, loin_d = LARGEUR//2-36, LARGEUR//2+36
    # Ruban d'asphalte bleu-gris, avec accotements et bords eclaires.
    pygame.draw.polygon(surface, (68, 80, 103), [(loin_g-12,HORIZON),(loin_d+12,HORIZON),(proche_d,HAUTEUR),(proche_g,HAUTEUR)])
    pygame.draw.polygon(surface, (103, 117, 138), [(loin_g,HORIZON),(loin_d,HORIZON),(proche_d-38,HAUTEUR),(proche_g+38,HAUTEUR)])
    pygame.draw.polygon(surface, (113, 126, 144), [(loin_g+8,HORIZON),(loin_d-8,HORIZON),(proche_d-54,HAUTEUR),(proche_g+54,HAUTEUR)])
    pygame.draw.lines(surface, (226, 232, 239), False, [(loin_g,HORIZON),(proche_g+38,HAUTEUR)], 4)
    pygame.draw.lines(surface, (226, 232, 239), False, [(loin_d,HORIZON),(proche_d-38,HAUTEUR)], 4)
    phase = (t*0.62) % 1
    # Granulat et fines traces de roulement repartis selon la profondeur.
    for grain in range(84):
        z = ((grain / 84 + phase * .31) % 1)
        y = int(HORIZON + z*z*(HAUTEUR-HORIZON))
        demi = 36 + z*406
        lateral = ((grain * 37) % 97) / 97 * 1.62 - .81
        px = int(LARGEUR//2 - int(joueur_x*175) + lateral*demi)
        longueur = max(1, int(1 + z*5))
        teinte = (86, 99, 117) if grain % 3 else (151, 162, 176)
        pygame.draw.line(surface, teinte, (px, y), (px+longueur, y+1), max(1, int(1+z)))
    for i in range(13):
        z = (i/13 + phase) % 1
        y = int(HORIZON + z*z*(HAUTEUR-HORIZON))
        demi = int(36 + z*406)
        x = LARGEUR//2 - int(joueur_x*175)
        w = max(2, int(2+z*5))
        for voie in (-1, 1):
            px = int(x + voie*demi/3)
            pygame.draw.line(surface, (242, 239, 222), (px-w,y), (px+w,y), w)
        pygame.draw.line(surface, (255, 249, 229), (x-w,y), (x+w,y), w)
    # Glissieres et balises refractaires qui rapetissent vers l'horizon.
    for side in (-1, 1):
        points = []
        for index in range(17):
            z = index / 16
            y = int(HORIZON + z*z*(HAUTEUR-HORIZON))
            demi = 36 + z*406
            points.append((int(LARGEUR//2 - joueur_x*175 + side*demi), y - int(3+z*13)))
        pygame.draw.lines(surface, (70, 82, 102), False, points, 5)
        pygame.draw.lines(surface, (190, 202, 216), False, points, 2)
        for index in range(1, 17, 2):
            z = index / 16
            y = int(HORIZON + z*z*(HAUTEUR-HORIZON))
            demi = 36 + z*406
            px = int(LARGEUR//2 - joueur_x*175 + side*demi)
            haut = max(2, int(3+z*15))
            pygame.draw.line(surface, (72, 84, 102), (px, y), (px, y-haut), max(1, int(1+z*3)))

    # Petits nuages sur les côtés de la route.
    for side in (-1, 1):
        for i in range(7):
            z = ((i/7 + t*.12) % 1)
            y = int(HORIZON + z*z*(HAUTEUR-HORIZON))
            spread = int(90+z*500)
            x = LARGEUR//2 + side*spread - int(joueur_x*80)
            nuage(surface, x, y, int(12+z*45), (255,255,255), True)


def dessiner_voiture(surface, x, y, echelle, t, teinte=ROSE):
    """Draw the unicorn racer with layered paint, glass, rubber and mane details."""
    w, h = max(1, int(190*echelle)), max(1, int(105*echelle))
    ombre = pygame.Surface((w+70, h+45), pygame.SRCALPHA)
    pygame.draw.ellipse(ombre, (57, 67, 105, 76), (25, h//2, w, h//2))
    surface.blit(ombre, (int(x-w/2-35), int(y-h/2+10)))

    eclaircie = tuple(min(255, int(c + (255-c)*.55)) for c in teinte)
    peinture_sombre = tuple(int(c*.52) for c in teinte)
    peinture_reflet = tuple(min(255, int(c*.68 + 255*.32)) for c in teinte)

    # Pneus en caoutchouc, bandes de roulement et jantes a rayons.
    roues = []
    for roue_x in (x-w*.32, x+w*.32):
        centre_roue = (round(roue_x), round(y+h*.30))
        largeur_pneu, hauteur_pneu = max(8, int(w*.23)), max(6, int(h*.45))
        pneu = pygame.Rect(0, 0, largeur_pneu, hauteur_pneu)
        pneu.center = centre_roue
        roues.append(pneu)
        pygame.draw.ellipse(surface, (24, 26, 37), pneu)
        pygame.draw.ellipse(surface, (63, 70, 85),
                            pneu.inflate(-max(2, int(echelle*4)), -max(2, int(echelle*3))),
                            max(1, int(echelle*2)))
        jante = pneu.inflate(-max(4, int(echelle*9)), -max(4, int(echelle*8)))
        pygame.draw.ellipse(surface, (113, 131, 150), jante)
        pygame.draw.ellipse(surface, (45, 57, 75),
                            jante.inflate(-max(2, int(echelle*4)), -max(2, int(echelle*4))))
        pygame.draw.circle(surface, (218, 228, 235), centre_roue, max(1, int(4*echelle)))
        for branche in range(5):
            angle = t*.35 + branche*math.tau/5
            debut = (round(centre_roue[0]+math.cos(angle)*2*echelle),
                     round(centre_roue[1]+math.sin(angle)*2*echelle))
            fin = (round(centre_roue[0]+math.cos(angle)*5*echelle),
                   round(centre_roue[1]+math.sin(angle)*5*echelle))
            pygame.draw.line(surface, (207, 219, 230), debut, fin,
                             max(1, int(echelle*1.5)))
        for rainure in range(8):
            angle = rainure*math.tau/8 + t*.35
            debut = (round(centre_roue[0]+math.cos(angle)*largeur_pneu*.47),
                     round(centre_roue[1]+math.sin(angle)*hauteur_pneu*.47))
            fin = (round(centre_roue[0]+math.cos(angle)*largeur_pneu*.37),
                   round(centre_roue[1]+math.sin(angle)*hauteur_pneu*.37))
            pygame.draw.line(surface, (102, 108, 119), debut, fin, 1)

    # Carrosserie profilee, bas de caisse et courbes d'ailes.
    silhouette = [
        (round(x-w*.49), round(y+h*.18)), (round(x-w*.42), round(y+h*.02)),
        (round(x-w*.25), round(y-h*.03)), (round(x+w*.25), round(y-h*.03)),
        (round(x+w*.43), round(y+h*.03)), (round(x+w*.50), round(y+h*.20)),
        (round(x+w*.46), round(y+h*.43)), (round(x+w*.34), round(y+h*.52)),
        (round(x-w*.34), round(y+h*.52)), (round(x-w*.46), round(y+h*.43)),
    ]
    pygame.draw.polygon(surface, (54, 48, 74), [
        (px, py+max(1, int(echelle*4))) for px, py in silhouette
    ])
    pygame.draw.polygon(surface, peinture_sombre, silhouette)
    pygame.draw.ellipse(surface, teinte, (x-w*.48, y-h*.01, w*.96, h*.52))
    pygame.draw.ellipse(surface, peinture_reflet,
                        (x-w*.39, y-h*.10, w*.78, h*.32))
    pygame.draw.arc(surface, eclaircie,
                    (x-w*.43, y-h*.09, w*.83, h*.43), .18, 2.75,
                    max(1, int(2*echelle)))
    pygame.draw.arc(surface, peinture_sombre,
                    (x-w*.46, y+h*.02, w*.92, h*.48), 3.35, 6.0,
                    max(1, int(3*echelle)))

    # Ailes qui epousent les roues et soulignent le volume de la carrosserie.
    for pneu in roues:
        rect_aile = pneu.inflate(max(4, int(echelle*14)), max(3, int(echelle*8)))
        pygame.draw.arc(surface, peinture_sombre, rect_aile, math.pi, math.tau,
                        max(1, int(4*echelle)))
        pygame.draw.arc(surface, eclaircie, rect_aile.inflate(-2, -2),
                        math.pi, math.tau, max(1, int(2*echelle)))

    # Pare-brise teinte, joint sombre et reflet du ciel.
    vitre = pygame.Rect(round(x-w*.20), round(y-h*.13),
                        max(2, int(w*.40)), max(2, int(h*.25)))
    pygame.draw.rect(surface, (57, 99, 132), vitre, border_radius=max(2, int(8*echelle)))
    pygame.draw.rect(surface, (116, 180, 210), vitre.inflate(-max(2, int(echelle*5)),
                                                              -max(2, int(echelle*4))),
                     border_radius=max(2, int(7*echelle)))
    pygame.draw.line(surface, (232, 248, 255),
                     (round(x-w*.11), round(y-h*.09)),
                     (round(x-w*.025), round(y+h*.015)),
                     max(1, int(2*echelle)))
    pygame.draw.line(surface, (178, 224, 240),
                     (round(x+w*.045), round(y-h*.085)),
                     (round(x+w*.11), round(y-h*.015)),
                     max(1, int(echelle)))

    # Calandre, prises d'air et pare-chocs avant.
    grille = pygame.Rect(round(x-w*.105), round(y+h*.315),
                         max(3, int(w*.21)), max(2, int(h*.09)))
    pygame.draw.rect(surface, (48, 52, 72), grille, border_radius=max(1, int(3*echelle)))
    for barre in range(1, 4):
        px = grille.left + grille.width*barre//4
        pygame.draw.line(surface, (153, 164, 183), (px, grille.top+1),
                         (px, grille.bottom-1), 1)
    pygame.draw.arc(surface, (255, 214, 231),
                    (x-w*.43, y+h*.25, w*.86, h*.30), .08, math.pi-.08,
                    max(1, int(3*echelle)))

    # Phares avec verre chaud et monture sombre.
    for cote in (-1, 1):
        phare = pygame.Rect(round(x+cote*w*.31), round(y+h*.155),
                            max(3, int(w*.14)), max(3, int(h*.17)))
        pygame.draw.ellipse(surface, (112, 79, 108), phare)
        pygame.draw.ellipse(surface, (255, 216, 151),
                            phare.inflate(-max(1, int(echelle*3)),
                                          -max(1, int(echelle*3))))
        pygame.draw.ellipse(surface, (255, 250, 220),
                            phare.inflate(-max(3, int(echelle*7)),
                                          -max(3, int(echelle*6))))

    # Embleme etoile nacre sur le capot.
    etoile(surface, int(x), int(y+h*.20), max(3, int(7*echelle)), t*.2)

    # Cou et criniere en meches effilees animees par le vent.
    cx, cy = int(x), int(y-h*.27 + math.sin(t*4)*echelle)
    cou = [
        (round(cx-w*.16), round(cy+h*.04)), (round(cx+w*.11), round(cy+h*.03)),
        (round(cx+w*.20), round(y+h*.31)), (round(cx-w*.27), round(y+h*.31)),
    ]
    pygame.draw.polygon(surface, (142, 111, 137), [(px+2, py+3) for px, py in cou])
    pygame.draw.polygon(surface, (255, 246, 239), cou)
    pygame.draw.lines(surface, (255, 255, 250), False, cou[:3], max(1, int(echelle*2)))
    couleurs_criniere = ((133, 68, 126), (235, 93, 157), (255, 188, 83), (93, 181, 219))
    for index, couleur in enumerate(couleurs_criniere):
        decalage = math.sin(t*5+index*.8)*echelle*2
        base_x = cx-w*.25+index*w*.055
        meche = [
            (round(base_x+w*.13), round(cy-h*.24+decalage)),
            (round(base_x+w*.24), round(cy-h*.10+decalage)),
            (round(base_x+w*.12), round(cy+h*.18+decalage)),
            (round(base_x-w*.04), round(cy+h*.31+decalage)),
            (round(base_x+w*.015), round(cy+h*.02+decalage)),
        ]
        pygame.draw.polygon(surface, couleur, meche)
        pygame.draw.lines(surface, (255, 235, 243), False, meche[1:4], max(1, int(echelle)))

    # Oreilles avec contours et interieur rose.
    oreilles = (
        [(cx-w*.13,cy-h*.16),(cx-w*.20,cy-h*.43),(cx-w*.035,cy-h*.27)],
        [(cx+w*.07,cy-h*.17),(cx+w*.16,cy-h*.42),(cx+w*.19,cy-h*.14)],
    )
    for points in oreilles:
        pygame.draw.polygon(surface, (213, 180, 183),
                            [(round(px), round(py)) for px, py in points])
        interieur = [(cx+(px-cx)*.66, cy+(py-cy)*.66) for px, py in points]
        pygame.draw.polygon(surface, (255, 176, 201),
                            [(round(px), round(py)) for px, py in interieur])
        pygame.draw.aalines(surface, (255, 242, 237), True,
                            [(round(px), round(py)) for px, py in points])

    # Corne doree en spirale.
    corne = [(round(cx-w*.035), round(cy-h*.20)),
             (round(cx+w*.055), round(cy-h*.20)),
             (round(cx+w*.015), round(cy-h*.58))]
    pygame.draw.polygon(surface, (158, 105, 45), corne)
    pygame.draw.polygon(surface, (255, 218, 112),
                        [(corne[0][0]+1, corne[0][1]-1),
                         (corne[1][0]-1, corne[1][1]-1),
                         (corne[2][0], corne[2][1]+2)])
    pygame.draw.lines(surface, (255, 244, 184), False,
                      [corne[0], (round(cx+w*.005), round(cy-h*.34)), corne[2]],
                      max(1, int(echelle*1.5)))
    for bande in range(4):
        yy = round(cy-h*.235-bande*h*.073)
        decalage = max(1, int(h*.025))
        pygame.draw.line(surface, (185, 126, 55),
                         (round(cx-w*.02), yy),
                         (round(cx+w*.025), yy-decalage),
                         max(1, int(echelle)))

    # Tete equine de profil, avec volumes et ombres douces.
    tete = [
        (round(cx-w*.16), round(cy-h*.25)), (round(cx-w*.13), round(cy-h*.34)),
        (round(cx-w*.025), round(cy-h*.38)), (round(cx+w*.075), round(cy-h*.31)),
        (round(cx+w*.13), round(cy-h*.18)), (round(cx+w*.18), round(cy-h*.045)),
        (round(cx+w*.16), round(cy+h*.075)), (round(cx+w*.07), round(cy+h*.13)),
        (round(cx-w*.09), round(cy+h*.09)), (round(cx-w*.17), round(cy-.01*h)),
    ]
    pygame.draw.polygon(surface, (201, 174, 174), [(px+2, py+3) for px, py in tete])
    pygame.draw.polygon(surface, (255, 249, 241), tete)
    joue = pygame.Rect(round(cx-w*.12), round(cy-h*.03), max(2,int(w*.17)), max(2,int(h*.15)))
    pygame.draw.ellipse(surface, (255, 239, 231), joue)
    pygame.draw.lines(surface, (255, 255, 250), False, tete[1:6], max(1, int(echelle*2)))

    # Oeil en amande, iris profond, paupiere et sourcil.
    oeil_x, oeil_y = round(cx+w*.065), round(cy-h*.13)
    rayon_oeil = max(2, int(4.2*echelle))
    contour_oeil = [
        (oeil_x-rayon_oeil, oeil_y), (oeil_x-round(rayon_oeil*.25), oeil_y-round(rayon_oeil*.62)),
        (oeil_x+rayon_oeil, oeil_y-round(rayon_oeil*.12)),
        (oeil_x+round(rayon_oeil*.35), oeil_y+round(rayon_oeil*.48)),
    ]
    pygame.draw.polygon(surface, (112, 71, 85), contour_oeil)
    pygame.draw.ellipse(surface, (74, 49, 74),
                        (oeil_x-rayon_oeil//2, oeil_y-rayon_oeil//2,
                         max(2, rayon_oeil), max(2, rayon_oeil)))
    pygame.draw.circle(surface, (28, 31, 43),
                       (oeil_x+max(1, rayon_oeil//5), oeil_y), max(1, rayon_oeil//3))
    pygame.draw.circle(surface, (255, 255, 255),
                       (oeil_x-max(1, rayon_oeil//5), oeil_y-max(1, rayon_oeil//4)),
                       max(1, rayon_oeil//4))
    pygame.draw.arc(surface, (114, 79, 88),
                    (oeil_x-rayon_oeil, oeil_y-rayon_oeil,
                     rayon_oeil*2, max(2, rayon_oeil*2)), 3.25, 6.0,
                    max(1, int(echelle*1.4)))

    # Museau allonge, narine et bouche fine.
    museau = pygame.Rect(round(cx+w*.085), round(cy-h*.01),
                         max(3, int(w*.15)), max(2, int(h*.12)))
    pygame.draw.ellipse(surface, (224, 193, 190), museau.inflate(2, 2))
    pygame.draw.ellipse(surface, (255, 225, 218), museau)
    narine = pygame.Rect(museau.right-max(3,int(6*echelle)),
                         museau.centery-max(1,int(2*echelle)),
                         max(2,int(3*echelle)), max(2,int(2.5*echelle)))
    pygame.draw.ellipse(surface, (126, 80, 91), narine)
    pygame.draw.arc(surface, (139, 89, 101),
                    (museau.left, museau.centery, museau.width, max(2, int(h*.075))),
                    3.35, 5.85, max(1, int(echelle)))
    pygame.draw.ellipse(surface, (247, 174, 184),
                        (round(cx-w*.10), round(cy+h*.01), max(2,int(w*.075)), max(2,int(h*.07))))

    # Reflets fins sur les meches de la criniere.
    pygame.draw.lines(surface, (255, 231, 244), False,
                      [(round(cx-w*.19), round(cy-h*.18)),
                       (round(cx-w*.08), round(cy-h*.12)),
                       (round(cx-w*.18), round(cy-h*.02))],
                      max(1, int(echelle*1.5)))


def etoile(surface, x, y, r, t):
    points = []
    for i in range(10):
        angle = -math.pi/2 + i*math.pi/5 + t
        rayon = r if i % 2 == 0 else r*.43
        points.append((int(x+math.cos(angle)*rayon), int(y+math.sin(angle)*rayon)))
    pygame.draw.polygon(surface, (255,220,91), points)
    pygame.draw.polygon(surface, (255,255,220), points, 2)


def nouvelle_partie():
    global joueur_x, vitesse, distance, accelerateurs, particules, bots, feu_z, temps_penalite, message_feu, nitro, compte_a_rebours, boosts_pris, temps
    joueur_x, vitesse, distance, boosts_pris, temps = 0.0, 0.0, 0.0, 0, 0.0
    nitro, compte_a_rebours = 100.0, 3.0
    accelerateurs, particules, bots = [], [], []
    feu_z, temps_penalite, message_feu = 0.45, 0.0, 0.0
    for i in range(7):
        accelerateurs.append({
            "z": random.uniform(.12, .94),
            "x": random.choice((-.62, -.2, .2, .62)),
            "phase": random.random() * math.tau,
            "touche": False,
        })
    for nom, allure, voie, couleur in (("Pistache",49,-.60,(70,190,230)),("Comete",56,.60,(115,105,225)),("Paillette",44,.20,(255,180,65))):
        bots.append({"nom": nom, "vitesse": allure, "distance": random.uniform(0,90), "voie": voie, "couleur": couleur})


def dessiner_accelerateur(surface, x, y, echelle, t, phase):
    largeur = max(4, int(57 * echelle))
    profondeur = max(3, int(23 * echelle))
    forme = [
        (int(x-largeur), int(y-profondeur*.38)),
        (int(x+largeur), int(y-profondeur*.38)),
        (int(x+largeur*.78), int(y+profondeur*.55)),
        (int(x-largeur*.78), int(y+profondeur*.55)),
    ]
    pygame.draw.polygon(surface, (29, 48, 76), forme)
    interieur = [
        (int(x-largeur*.87), int(y-profondeur*.27)),
        (int(x+largeur*.87), int(y-profondeur*.27)),
        (int(x+largeur*.70), int(y+profondeur*.38)),
        (int(x-largeur*.70), int(y+profondeur*.38)),
    ]
    lueur = int(20 + 18 * (0.5 + 0.5 * math.sin(t*7 + phase)))
    pygame.draw.polygon(surface, (24, 112+lueur, 151+lueur), interieur)
    pygame.draw.lines(surface, (133, 244, 255), True, interieur, max(1, int(echelle*2)))
    for index in range(3):
        centre = x + (index-1)*largeur*.43
        demi = max(1, int(largeur*.12))
        fleche = [
            (int(centre-demi), int(y+profondeur*.27)),
            (int(centre), int(y-profondeur*.18)),
            (int(centre+demi), int(y+profondeur*.27)),
        ]
        pygame.draw.lines(surface, (235, 255, 255), False, fleche, max(1, int(echelle*3)))


def dessiner_feu(surface, x, y, echelle, rouge):
    taille = max(8, int(26*echelle))
    pygame.draw.line(surface, (100, 93, 125), (int(x),int(y)), (int(x),int(y-taille*3.8)), max(2,taille//5))
    pygame.draw.rect(surface, (62, 67, 100), (int(x-taille*.58),int(y-taille*4.2),int(taille*1.16),int(taille*2.2)), border_radius=max(2,taille//4))
    pygame.draw.circle(surface, (255, 61, 88) if rouge else (106, 104, 113), (int(x),int(y-taille*3.55)), max(2,int(taille*.31)))
    pygame.draw.circle(surface, (91, 255, 157) if not rouge else (105, 92, 100), (int(x),int(y-taille*2.7)), max(2,int(taille*.31)))


def boucle():
    global etat, joueur_x, vitesse, distance, boosts_pris, temps, feu_z, temps_penalite, message_feu, nitro, compte_a_rebours
    vivant = True
    nouvelle_partie()
    while vivant:
        dt = min(horloge.tick(60)/1000, .04)
        temps += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                vivant = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    vivant = False
                if ev.key == pygame.K_p:
                    if etat == "jeu": etat = "pause"
                    elif etat == "pause": etat = "jeu"
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE) and etat in ("titre","termine"):
                    nouvelle_partie(); etat = "depart"
                if ev.key == pygame.K_r and etat == "termine":
                    nouvelle_partie(); etat = "depart"
        touches = pygame.key.get_pressed()
        ciel(ecran, temps)
        route(ecran, temps if etat == "jeu" else temps*.25)
        if etat == "depart":
            compte_a_rebours -= dt
            if compte_a_rebours <= 0:
                etat = "jeu"
        if etat == "jeu":
            direction = int(touches[pygame.K_RIGHT] or touches[pygame.K_d]) - int(touches[pygame.K_LEFT] or touches[pygame.K_q] or touches[pygame.K_a])
            cible = max(-.88, min(.88, joueur_x + direction*dt*1.45))
            joueur_x += (cible-joueur_x)*min(1,dt*8)
            accelere = touches[pygame.K_UP] or touches[pygame.K_w] or touches[pygame.K_z]
            frein = touches[pygame.K_DOWN] or touches[pygame.K_s]
            boost = touches[pygame.K_SPACE] and nitro > 0
            if accelere:
                vitesse = min(1.0, vitesse + dt*.42)
            elif not boost:
                vitesse = max(0.0, vitesse - dt*.08)
            if frein:
                vitesse = max(0.0, vitesse-dt*.72)
            if boost:
                nitro = max(0.0, nitro-dt*30)
                vitesse = min(1.22, vitesse+dt*.28)
            else:
                nitro = min(100.0, nitro+dt*9)
            if temps_penalite > 0:
                temps_penalite = max(0, temps_penalite-dt)
                vitesse = min(vitesse, .25)
            distance += dt*vitesse*65.0
            if distance >= 2500.0:
                distance = 2500.0
                etat = "termine"
            # Les bots avancent sur leurs voies et ralentissent au feu rouge.
            rouge = (temps % 8.0) < 4.5
            for bot in bots:
                allure = bot["vitesse"] * (0.35 if rouge and (temps % 8.0) > 3.4 else 1.0)
                bot["distance"] += dt*allure
            # Plaques au sol : elles propulsent la licorne et rechargent la nitro.
            for accelerateur in accelerateurs:
                accelerateur["z"] += dt*(.20+vitesse*.27)
                if accelerateur["z"] >= 1.0:
                    accelerateur["z"] = random.uniform(-.12,.08)
                    accelerateur["x"] = random.choice((-.62,-.2,.2,.62))
                    accelerateur["phase"] = random.random()*math.tau
                    accelerateur["touche"] = False
                az = accelerateur["z"]
                if az >= 0:
                    ax = LARGEUR//2 + accelerateur["x"]*(38+az*440) - joueur_x*155*az
                    ay = HORIZON + az*az*(HAUTEUR-HORIZON)
                    dessiner_accelerateur(ecran, ax, ay, .12+az*.88, temps, accelerateur["phase"])
                if .88 < az < .97 and not accelerateur["touche"] and abs(accelerateur["x"]-joueur_x)<.19:
                    accelerateur["touche"] = True
                    boosts_pris += 1
                    vitesse = min(1.22, vitesse+.24)
                    nitro = min(100.0, nitro+18)
                    for _ in range(14):
                        particules.append([ax, ay, random.uniform(-110,110), random.uniform(-150,25), .48])
            # Les particules du turbo filent en petits traits lumineux.
            for p in particules[:]:
                p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[4]-=dt
                if p[4]<=0:
                    particules.remove(p)
                else:
                    fin = (int(p[0]-p[2]*.025), int(p[1]-p[3]*.025))
                    pygame.draw.line(ecran,(139,245,255),(int(p[0]),int(p[1])),fin,max(1,int(p[4]*4)))
            # Feu suspendu au-dessus de la route : s'arr?ter avec bas/S au rouge.
            feu_z += dt*(.20+vitesse*.27)
            if feu_z >= 1.0:
                feu_z = random.uniform(-.12,.05)
            fz = feu_z
            fx = LARGEUR//2 - int(joueur_x*130*fz)
            fy = HORIZON + fz*fz*(HAUTEUR-HORIZON)
            dessiner_feu(ecran,fx,fy-15,.15+fz*.85,(temps%8.0)<4.5)
            if .90 < fz < .96 and (temps%8.0)<4.5 and vitesse>.20 and temps_penalite<=0:
                vitesse = .08
                temps_penalite = 1.6
                message_feu = 1.6
            message_feu = max(0, message_feu-dt)
            avance_joueur = distance
            for bot in sorted(bots, key=lambda b: b["distance"]):
                ecart = bot["distance"]-avance_joueur
                if abs(ecart) < 1000:
                    bz = max(.08,min(.95,.55+ecart/1800))
                    bx = LARGEUR//2 + bot["voie"]*(38+bz*440) - joueur_x*155*bz
                    by = HORIZON + bz*bz*(HAUTEUR-HORIZON)
                    dessiner_voiture(ecran,bx,by-38*bz,.20+bz*.55,temps,bot["couleur"])
                    if bz > .25:
                        texte(ecran,bot["nom"],petit,(90,78,130),(bx,by-75*bz))
            dessiner_voiture(ecran,LARGEUR//2+joueur_x*280,HAUTEUR-135,1.0,temps)
            # Interface en verre dépoli.
            panneau=pygame.Surface((230,82),pygame.SRCALPHA); pygame.draw.rect(panneau,(255,255,255,185),(0,0,230,82),border_radius=18)
            texte(ecran,f"Turbo pris : {boosts_pris}",font,VIOLET,(46,36),False)
            texte(ecran,f"Distance  {int(distance)} / 2500 m",petit,(81,96,140),(48,67),False)
            texte(ecran,f"Vitesse : {int(vitesse*240)} km/h",petit,(81,96,140),(48,86),False)
            pygame.draw.rect(ecran,(204,211,232),(49,119,174,9),border_radius=5)
            pygame.draw.rect(ecran,(74,210,203),(49,119,int(174*nitro/100),9),border_radius=5)
            classement=1+sum(1 for b in bots if b["distance"]>distance)
            texte(ecran,f"Course : {classement}e / 4",font,VIOLET,(LARGEUR-145,48))
            texte(ecran,"Haut/Z : accelerer | Bas/S : freiner | Espace : nitro | P : pause",petit,(91,111,145),(LARGEUR//2,HAUTEUR-48))
            texte(ecran,"Gauche/droite ou Q/D | Echap : quitter",petit,(91,111,145),(LARGEUR//2,HAUTEUR-24))
            if message_feu>0:
                texte(ecran,"Attention ! Freine au feu rouge !",font,(207,62,98),(LARGEUR//2,100))
        elif etat == "depart":
            voile=pygame.Surface((LARGEUR,HAUTEUR),pygame.SRCALPHA); voile.fill((36,49,92,65)); ecran.blit(voile,(0,0))
            texte(ecran,"PRETS ?",titre,(255,255,255),(LARGEUR//2,230))
            texte(ecran,str(max(1,int(compte_a_rebours)+1)),titre,(255,238,170),(LARGEUR//2,315))
            texte(ecran,"Accelerateur : haut / W / Z  |  Nitro : espace",font,(255,255,255),(LARGEUR//2,390))
        elif etat == "titre":
            # Voiture en démonstration devant le panneau titre.
            dessiner_voiture(ecran,LARGEUR//2,HAUTEUR-145,1.08,temps)
            voile=pygame.Surface((LARGEUR,HAUTEUR),pygame.SRCALPHA); voile.fill((31,58,112,42)); ecran.blit(voile,(0,0))
            texte(ecran,"NUAGE EXPRESS",titre,(255,255,255),(LARGEUR//2,150))
            texte(ecran,"La grande course de la licorne",font,(255,239,250),(LARGEUR//2,205))
            pygame.draw.rect(ecran,(255,255,255,210),(LARGEUR//2-190,260,380,74),border_radius=24)
            texte(ecran,"Entree ou Espace pour demarrer",font,VIOLET,(LARGEUR//2,297))
            texte(ecran,"Roule sur les accelerateurs et bats les trois bots !",petit,(255,255,255),(LARGEUR//2,365))
            texte(ecran,"G/D ou fleches : diriger | Haut/Z : accelerer | Bas/S : freiner",petit,(255,255,255),(LARGEUR//2,395))
        elif etat == "pause":
            voile=pygame.Surface((LARGEUR,HAUTEUR),pygame.SRCALPHA); voile.fill((31,42,78,150)); ecran.blit(voile,(0,0))
            texte(ecran,"PAUSE",titre,(255,255,255),(LARGEUR//2,270))
            texte(ecran,"P pour reprendre  |  Echap pour quitter",font,(255,255,255),(LARGEUR//2,340))
        else:
            dessiner_voiture(ecran,LARGEUR//2,HAUTEUR-145,1.0,temps)
            voile=pygame.Surface((LARGEUR,HAUTEUR),pygame.SRCALPHA); voile.fill((41,51,94,105)); ecran.blit(voile,(0,0))
            place=1+sum(1 for b in bots if b["distance"]>distance)
            texte(ecran,"COURSE TERMINEE !",titre,(255,255,255),(LARGEUR//2,200))
            texte(ecran,f"Tu termines {place}e sur 4",font,(255,239,184),(LARGEUR//2,270))
            texte(ecran,f"Accelerateurs pris : {boosts_pris}",font,(255,255,255),(LARGEUR//2,315))
            texte(ecran,"Entree pour rejouer | Echap pour quitter",petit,(255,255,255),(LARGEUR//2,370))
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    boucle()
import math
import random
import pygame

pygame.init()
pygame.display.set_caption("Unicorn Turbo - La course arc-en-ciel")
W, H = 1100, 700
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
FPS = 60

# Palette
SKY_TOP = (93, 168, 255)
SKY_BOTTOM = (255, 198, 229)
WHITE = (255, 250, 255)
INK = (68, 50, 105)
PINK = (255, 104, 190)
PURPLE = (153, 100, 255)
CYAN = (92, 235, 255)
GOLD = (255, 211, 92)
ROAD = (69, 69, 112)
ROAD_EDGE = (255, 117, 205)
GRASS = (83, 205, 143)

font = pygame.font.SysFont("arial", 22, bold=True)
small = pygame.font.SysFont("arial", 16, bold=True)
big = pygame.font.SysFont("arial", 54, bold=True)

def draw_text(text, x, y, f=font, color=WHITE, center=False):
    img = f.render(text, True, INK)
    rect = img.get_rect()
    if center:
        rect.center = (x+2, y+3)
    else:
        rect.topleft = (x+2, y+3)
    screen.blit(img, rect)
    img2 = f.render(text, True, color)
    rect2 = img2.get_rect()
    if center:
        rect2.center = (x, y)
    else:
        rect2.topleft = (x, y)
    screen.blit(img2, rect2)

def gradient_sky():
    for y in range(H):
        t = y / H
        col = (int(SKY_TOP[0]*(1-t)+SKY_BOTTOM[0]*t),
               int(SKY_TOP[1]*(1-t)+SKY_BOTTOM[1]*t),
               int(SKY_TOP[2]*(1-t)+SKY_BOTTOM[2]*t))
        pygame.draw.line(screen, col, (0,y), (W,y))
    # Puffy clouds
    for cx, cy, s in clouds:
        for ox, oy, r in [(-35,4,25),(-10,-8,31),(20,0,27),(43,8,20)]:
            pygame.draw.circle(screen, (255,255,255), (cx+ox*s,cy+oy*s), int(r*s))
            pygame.draw.circle(screen, (255,235,250), (cx+ox*s,cy+oy*s), int(r*s), 2)
    # Rainbow
    rainbow = pygame.Surface((420, 220), pygame.SRCALPHA)
    colors = [(255,92,135,210),(255,177,82,210),(255,237,100,210),
              (100,231,151,210),(89,203,255,210),(164,126,255,210)]
    for i,c in enumerate(colors):
        pygame.draw.arc(rainbow, c, (i*8, i*8, 400-i*16, 400-i*16), math.pi, math.tau, 12)
    screen.blit(rainbow, (625, -110))
    # distant candy hills
    pygame.draw.ellipse(screen, (173, 222, 255), (-120, 230, 530, 230))
    pygame.draw.ellipse(screen, (255, 174, 220), (270, 250, 530, 190))
    pygame.draw.ellipse(screen, (176, 245, 202), (650, 225, 600, 240))

def draw_tree(x, y, scale=1):
    # candy tree
    pygame.draw.rect(screen, (151, 94, 116), (int(x-7*scale), int(y), int(14*scale), int(38*scale)), border_radius=5)
    for ox, oy, r, c in [(-15,-5,19,(255,135,207)),(3,-18,23,(255,183,225)),(20,-3,17,(218,132,255))]:
        pygame.draw.circle(screen, c, (int(x+ox*scale),int(y+oy*scale)), int(r*scale))
        pygame.draw.circle(screen, (255,220,245), (int(x+ox*scale),int(y+oy*scale)), int(r*scale), max(1,int(2*scale)))

def draw_road(offset):
    # Grass and sparkling roadside
    screen.fill(GRASS, (0, 350, W, H-350))
    # patterned grass
    for i in range(45):
        x = (i*97 + int(offset*0.4)) % W
        y = 380 + (i*47)%300
        pygame.draw.circle(screen, random.choice([(255,255,255),(255,231,112),(255,126,209)]), (x,y), 2)
    # road polygon, perspective-ish but arcade readable
    road_poly = [(330, H), (770, H), (690, 325), (410, 325)]
    pygame.draw.polygon(screen, ROAD_EDGE, [(310,H),(790,H),(708,315),(392,315)])
    pygame.draw.polygon(screen, ROAD, road_poly)
    # road edge dashed shine
    for y in range(350, H, 56):
        yy = (y + int(offset*1.4)) % (H-330) + 330
        # road lanes
        pygame.draw.rect(screen, (255,255,255), (548, yy, 7, 25), border_radius=3)
        # little edge glows
        pygame.draw.circle(screen, (255,220,249), (int(415+(yy-330)*0.12), yy), 3)
        pygame.draw.circle(screen, (255,220,249), (int(685-(yy-330)*0.12), yy), 3)
    # roadside candy trees / lollipop signs
    for i in range(7):
        yy = (i*125 + int(offset*1.0)) % 800 - 50
        scale = 0.55 + (yy+50)/900
        leftx = 250 - int((yy-300)*0.13)
        rightx = 850 + int((yy-300)*0.13)
        draw_tree(leftx, yy, scale)
        draw_tree(rightx, yy, scale)

def draw_unicorn_car(x, y, t, boost=False):
    # shadow
    pygame.draw.ellipse(screen, (43,47,95), (x-49,y+35,98,25))
    # boost trail
    if boost:
        for i in range(5):
            yy = y + 38 + i*10
            pygame.draw.polygon(screen, random.choice([(255,130,215),(104,224,255),(255,226,105)]),
                                [(x-15,yy),(x+15,yy),(x,yy+random.randint(12,24))])
    # wheels
    for wx in (x-38,x+38):
        pygame.draw.ellipse(screen,(40,36,65),(wx-11,y+12,22,35))
        pygame.draw.ellipse(screen,(175,190,220),(wx-5,y+19,10,20))
    # car body silhouette
    pygame.draw.ellipse(screen,(246,83,177),(x-49,y-17,98,72))
    pygame.draw.ellipse(screen,(255,165,222),(x-42,y-20,84,55))
    pygame.draw.polygon(screen,(255,123,199),[(x-39,y+18),(x-32,y-24),(x-13,y-39),(x+14,y-39),(x+34,y-21),(x+41,y+18)])
    # windshield
    pygame.draw.polygon(screen,(120,218,255),[(x-25,y-22),(x-11,y-34),(x+11,y-34),(x+25,y-22)])
    pygame.draw.line(screen,(225,255,255),(x-17,y-25),(x-8,y-32),3)
    # headlights
    pygame.draw.ellipse(screen,(255,250,167),(x-37,y+9,15,9))
    pygame.draw.ellipse(screen,(255,250,167),(x+22,y+9,15,9))
    # unicorn ears
    pygame.draw.polygon(screen,(255,207,231),[(x-24,y-36),(x-31,y-53),(x-12,y-42)])
    pygame.draw.polygon(screen,(255,207,231),[(x+24,y-36),(x+31,y-53),(x+12,y-42)])
    # horn
    pygame.draw.polygon(screen,(255,218,93),[(x-7,y-42),(x,y-72),(x+7,y-42)])
    pygame.draw.line(screen,(255,249,183),(x-2,y-50),(x+1,y-61),2)
    # mane
    for i,c in enumerate([(255,115,198),(177,116,255),(94,224,255),(255,226,115)]):
        pygame.draw.arc(screen,c,(x-27+i*4,y-47+i*2,54-i*8,28),math.pi,math.tau,5)
    # eyes / cheeks
    pygame.draw.circle(screen,(75,50,95),(x-16,y-13),3)
    pygame.draw.circle(screen,(75,50,95),(x+16,y-13),3)
    pygame.draw.circle(screen,(255,113,169),(x-25,y-5),5)
    pygame.draw.circle(screen,(255,113,169),(x+25,y-5),5)
    # sparkle emblem
    pygame.draw.circle(screen,(255,250,255),(x,y+8),9)
    pygame.draw.polygon(screen,GOLD,[(x,y-1),(x+3,y+6),(x+10,y+8),(x+3,y+10),(x,y+17),(x-3,y+10),(x-10,y+8),(x-3,y+6)])

def draw_item(item):
    x,y=item["x"],item["y"]
    kind=item["kind"]
    pulse=math.sin(item["phase"])*3
    if kind=="boost":
        # golden lightning capsule
        pygame.draw.ellipse(screen,(255,240,141),(x-24,y-23,48,46))
        pygame.draw.ellipse(screen,(255,255,224),(x-19,y-18,38,36),3)
        pygame.draw.polygon(screen,(255,166,46),[(x+2,y-17),(x-11,y+2),(x-1,y+2),(x-5,y+17),(x+12,y-5),(x+3,y-5)])
        pygame.draw.circle(screen,(255,255,255),(x-10,y-10),3)
    elif kind=="star":
        pygame.draw.circle(screen,(255,231,114),(x,y),24+int(pulse), width=0)
        pts=[]
        for j in range(10):
            a=-math.pi/2+j*math.pi/5
            r=17 if j%2==0 else 8
            pts.append((x+math.cos(a)*r,y+math.sin(a)*r))
        pygame.draw.polygon(screen,(255,255,255),pts)
        pygame.draw.polygon(screen,(255,193,67),pts,3)
    elif kind=="cone":
        pygame.draw.ellipse(screen,(255,255,255),(x-20,y+13,40,10))
        pygame.draw.polygon(screen,(255,125,78),[(x,y-23),(x-20,y+16),(x+20,y+16)])
        pygame.draw.polygon(screen,(255,236,214),[(x-11,y+1),(x+11,y+1),(x+15,y+9),(x-15,y+9)])
        pygame.draw.line(screen,(255,206,186),(x,y-16),(x-11,y+9),2)
    elif kind=="puddle":
        pygame.draw.ellipse(screen,(67,177,255),(x-31,y-12,62,24))
        pygame.draw.ellipse(screen,(188,245,255),(x-22,y-7,42,11),3)
        pygame.draw.circle(screen,(255,255,255),(x+12,y-5),3)
    elif kind=="cotton":
        for ox,oy,r in [(-14,3,14),(0,-5,17),(15,3,13),(0,8,15)]:
            pygame.draw.circle(screen,(255,255,255),(x+ox,y+oy),r)
            pygame.draw.circle(screen,(255,205,237),(x+ox,y+oy),r,2)
        pygame.draw.line(screen,(255,130,198),(x-12,y+12),(x+12,y-10),3)

def reset_game():
    return {"x":550.0,"y":555.0,"speed":300.0,"distance":0,"stars":0,"lives":3,
            "items":[],"particles":[],"spawn":0,"boost":0,"slow":0,"hit_flash":0,
            "over":False,"paused":False,"message":"Attrape les étoiles et fonce !","message_t":2.5}

clouds=[(100,105,1.0),(360,155,.72),(690,92,.85),(970,175,.7)]
game=reset_game()
road_offset=0
elapsed=0
running=True

while running:
    dt=min(clock.tick(FPS)/1000,0.035)
    elapsed+=dt
    keys=pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: running=False
            if event.key==pygame.K_p and not game["over"]: game["paused"]=not game["paused"]
            if event.key==pygame.K_RETURN and game["over"]: game=reset_game()

    if not game["over"] and not game["paused"]:
        # steer
        move=(int(keys[pygame.K_RIGHT] or keys[pygame.K_d])-int(keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]))
        game["x"]+=move*420*dt
        game["x"]=max(390,min(710,game["x"]))
        game["boost"]=max(0,game["boost"]-dt)
        game["slow"]=max(0,game["slow"]-dt)
        game["hit_flash"]=max(0,game["hit_flash"]-dt)
        game["message_t"]=max(0,game["message_t"]-dt)
        speed=game["speed"]*(1.8 if game["boost"]>0 else 0.65 if game["slow"]>0 else 1)
        road_offset+=speed*dt
        game["distance"]+=speed*dt/12

        # item spawner, density increases with distance
        game["spawn"]+=dt
        if game["spawn"]>.62:
            game["spawn"]=0
            lane=random.choice([430,490,550,610,670])
            kind=random.choices(["star","boost","cone","puddle","cotton"],[35,17,17,15,16])[0]
            game["items"].append({"x":lane+random.randint(-12,12),"y":310,"kind":kind,"phase":random.random()*6.28})

        for item in game["items"][:]:
            item["y"]+=speed*dt*0.8
            item["phase"]+=dt*5
            if item["y"]>H+50:
                game["items"].remove(item)
                continue
            if abs(item["x"]-game["x"])<42 and abs(item["y"]-game["y"])<48:
                if item["kind"]=="star":
                    game["stars"]+=1
                    game["message"]="Super ! Une etoile !"
                    game["message_t"]=1.1
                    for _ in range(12):
                        game["particles"].append({"x":game["x"],"y":game["y"],"vx":random.uniform(-120,120),"vy":random.uniform(-180,40),"life":.7,"color":GOLD})
                elif item["kind"]=="boost":
                    game["boost"]=2.6
                    game["message"]="TURBO ARC-EN-CIEL !"
                    game["message_t"]=1.5
                    for _ in range(18):
                        game["particles"].append({"x":game["x"],"y":game["y"]+30,"vx":random.uniform(-100,100),"vy":random.uniform(20,160),"life":.6,"color":random.choice([PINK,CYAN,GOLD,PURPLE])})
                elif item["kind"]=="cotton":
                    game["message"]="Nuage tout doux !"
                    game["message_t"]=1.2
                    game["stars"]+=2
                elif item["kind"] in ("cone","puddle") and game["hit_flash"]<=0:
                    game["lives"]-=1
                    game["hit_flash"]=1.1
                    game["slow"]=1.4
                    game["message"]="Oups ! Fais attention !"
                    game["message_t"]=1.5
                    for _ in range(14):
                        game["particles"].append({"x":game["x"],"y":game["y"],"vx":random.uniform(-130,130),"vy":random.uniform(-150,60),"life":.5,"color":PINK})
                    if game["lives"]<=0: game["over"]=True
                game["items"].remove(item)

        for p in game["particles"][:]:
            p["x"]+=p["vx"]*dt
            p["y"]+=p["vy"]*dt
            p["vy"]+=240*dt
            p["life"]-=dt
            if p["life"]<=0: game["particles"].remove(p)

    # background and road
    gradient_sky()
    draw_road(road_offset)
    # distant flowers and roadside signs
    for i in range(6):
        yy=(i*145+int(road_offset*.75))%800-60
        # signs
        sx=300-int((yy-300)*.12)
        pygame.draw.rect(screen,(255,255,255),(sx-3,yy,6,45),border_radius=3)
        pygame.draw.circle(screen,(255,125,202),(sx,yy),14)
        pygame.draw.circle(screen,(255,240,250),(sx,yy),14,3)
        pygame.draw.circle(screen,(255,218,92),(sx,yy),5)

    for item in game["items"]:
        draw_item(item)
    draw_unicorn_car(int(game["x"]),int(game["y"]),elapsed,game["boost"]>0)

    for p in game["particles"]:
        pygame.draw.circle(screen,p["color"],(int(p["x"]),int(p["y"])),max(1,int(5*p["life"]/.7)))

    # UI header
    panel=pygame.Surface((W,90),pygame.SRCALPHA)
    pygame.draw.rect(panel,(80,52,128,190),(0,0,W,90))
    pygame.draw.line(panel,(255,220,250,230),(0,88),(W,88),3)
    screen.blit(panel,(0,0))
    draw_text("UNICORN TURBO  *",22,13,font,(255,235,255))
    draw_text(f"Etoiles : {game['stars']}",25,50,small,(255,239,132))
    draw_text(f"Distance : {int(game['distance'])} m",220,20,small,WHITE)
    draw_text("Vies :",440,20,small,WHITE)
    for i in range(3):
        col=(255,92,156) if i<game["lives"] else (110,91,130)
        hx=500+i*28
        pygame.draw.circle(screen,col,(hx-5,32),8)
        pygame.draw.circle(screen,col,(hx+5,32),8)
        pygame.draw.polygon(screen,col,[(hx-13,34),(hx+13,34),(hx,48)])
    draw_text("← → ou A/D : tourner",700,12,small,WHITE)
    draw_text("P : pause   Échap : quitter",700,42,small,WHITE)

    if game["boost"]>0:
        pygame.draw.rect(screen,(255,255,255),(W//2-130,105,260,18),border_radius=9)
        pygame.draw.rect(screen,(255,184,69),(W//2-126,109,int(252*game["boost"]/2.6),10),border_radius=6)
        draw_text("TURBO !",W//2,145,small,(255,248,151),True)

    if game["message_t"]>0 and not game["over"]:
        draw_text(game["message"],W//2,200,font,(255,255,255),True)

    if game["paused"]:
        veil=pygame.Surface((W,H),pygame.SRCALPHA); veil.fill((44,26,82,170)); screen.blit(veil,(0,0))
        draw_text("PAUSE",W//2,H//2-20,big,WHITE,True)
        draw_text("Appuie sur P pour reprendre",W//2,H//2+40,font,(255,230,250),True)

    if game["over"]:
        veil=pygame.Surface((W,H),pygame.SRCALPHA); veil.fill((48,27,84,205)); screen.blit(veil,(0,0))
        draw_text("FIN DE LA COURSE",W//2,260,big,(255,231,250),True)
        draw_text(f"Tu as ramasse {game['stars']} etoiles !",W//2,335,font,(255,240,140),True)
        draw_text("Appuie sur ENTREE pour rejouer",W//2,400,font,WHITE,True)

    pygame.display.flip()

pygame.quit()
