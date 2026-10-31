import math
import random
import pygame

# ------------------------------------------------------------
# LE ROYAUME MAGIQUE - jeu 2D avec graphismes dessinés en Python
# Commande d'installation : py -3.13 -m pip install pygame
# Lancement : py -3.13 main.py
# ------------------------------------------------------------

pygame.init()
pygame.display.set_caption("Le Royaume Magique")

LARGEUR, HAUTEUR = 1000, 650
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
horloge = pygame.time.Clock()
FPS = 60

# Couleurs
BLANC = (245, 248, 255)
NOIR = (16, 20, 32)
OR = (255, 211, 94)
BLEU = (89, 190, 255)
VIOLET = (177, 103, 255)
VERT = (45, 130, 83)
ROUGE = (239, 75, 87)

police = pygame.font.SysFont("arial", 22, bold=True)
petite_police = pygame.font.SysFont("arial", 16, bold=True)
grande_police = pygame.font.SysFont("arial", 48, bold=True)

def texte(surface, contenu, x, y, font, couleur=BLANC, centre=False):
    image = font.render(contenu, True, couleur)
    rect = image.get_rect()
    if centre:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    # Ombre légère pour la lisibilité
    ombre = font.render(contenu, True, (20, 24, 40))
    surface.blit(ombre, rect.move(2, 3))
    surface.blit(image, rect)

def dessiner_fond():
    # Ciel dégradé
    for y in range(HAUTEUR):
        t = y / HAUTEUR
        couleur = (int(16 + 20*t), int(25 + 35*t), int(55 + 20*t))
        pygame.draw.line(ecran, couleur, (0, y), (LARGEUR, y))

    # Lune et halo
    halo = pygame.Surface((180, 180), pygame.SRCALPHA)
    for rayon, alpha in [(78, 12), (58, 18), (40, 28)]:
        pygame.draw.circle(halo, (126, 176, 255, alpha), (90, 90), rayon)
    ecran.blit(halo, (730, 35))
    pygame.draw.circle(ecran, (242, 245, 255), (820, 125), 29)
    pygame.draw.circle(ecran, (207, 221, 255), (830, 116), 26)

    # Étoiles scintillantes
    for sx, sy, taille in etoiles:
        pygame.draw.circle(ecran, (190, 218, 255), (sx, sy), taille)

    # Montagnes lointaines
    pygame.draw.polygon(ecran, (37, 53, 83), [
        (0, 380), (120, 220), (245, 370), (390, 205),
        (545, 375), (700, 240), (850, 365), (1000, 250), (1000, 480), (0, 480)
    ])
    pygame.draw.polygon(ecran, (47, 73, 91), [
        (0, 425), (160, 300), (300, 430), (470, 285),
        (620, 430), (810, 305), (1000, 430), (1000, 520), (0, 520)
    ])

    # Forêt en couches
    for x in range(-30, LARGEUR + 60, 95):
        hauteur = random.Random(x).randint(100, 190)
        y = 455 - hauteur
        pygame.draw.rect(ecran, (31, 61, 65), (x + 23, y + 65, 18, hauteur))
        pygame.draw.circle(ecran, (25, 77, 70), (x + 32, y + 35), 48)
        pygame.draw.circle(ecran, (32, 91, 76), (x + 5, y + 60), 34)
        pygame.draw.circle(ecran, (29, 83, 70), (x + 60, y + 62), 36)

    # Sol magique
    pygame.draw.rect(ecran, (24, 69, 61), (0, 480, LARGEUR, 170))
    pygame.draw.line(ecran, (67, 143, 98), (0, 480), (LARGEUR, 480), 4)
    for _ in range(65):
        x = random.Random(_ * 17).randint(0, LARGEUR)
        y = random.Random(_ * 23).randint(490, HAUTEUR)
        pygame.draw.circle(ecran, (48, 113, 79), (x, y), random.Random(_).randint(1, 3))

    # Petites fleurs lumineuses
    for fx, fy, fc in fleurs:
        pygame.draw.circle(ecran, fc, (fx, fy), 3)
        pygame.draw.circle(ecran, (180, 255, 200), (fx, fy), 7, 1)

def dessiner_heros(surface, x, y, temps, invincible=False):
    # Aura magique
    aura = pygame.Surface((100, 120), pygame.SRCALPHA)
    pulsation = 30 + int(4 * math.sin(temps * 5))
    pygame.draw.ellipse(aura, (72, 133, 255, 40), (50-pulsation, 54-pulsation//2, pulsation*2, pulsation))
    surface.blit(aura, (x-50, y-63))

    # Cape
    pygame.draw.polygon(surface, (100, 47, 177), [
        (x-16, y-19), (x+15, y-19), (x+23, y+26), (x-22, y+26)
    ])
    pygame.draw.polygon(surface, (153, 81, 222), [
        (x-10, y-16), (x+8, y-16), (x+14, y+20), (x-13, y+20)
    ])

    # Tête et cheveux
    pygame.draw.circle(surface, (247, 196, 150), (x, y-27), 15)
    pygame.draw.arc(surface, (65, 38, 49), (x-15, y-43, 30, 25), math.pi, math.tau, 6)
    pygame.draw.circle(surface, (35, 37, 54), (x+5, y-28), 2)

    # Chapeau pointu
    pygame.draw.polygon(surface, (72, 48, 160), [
        (x-19, y-38), (x+19, y-38), (x+1, y-73)
    ])
    pygame.draw.ellipse(surface, (115, 91, 218), (x-20, y-42, 40, 10))
    pygame.draw.circle(surface, OR, (x+1, y-51), 3)

    # Bottes
    pygame.draw.ellipse(surface, (42, 34, 54), (x-16, y+20, 14, 9))
    pygame.draw.ellipse(surface, (42, 34, 54), (x+3, y+20, 14, 9))

    # Bâton et orbe
    pygame.draw.line(surface, (111, 76, 48), (x+16, y+10), (x+30, y-24), 5)
    pygame.draw.circle(surface, (105, 221, 255), (x+31, y-27), 8)
    pygame.draw.circle(surface, (225, 251, 255), (x+29, y-29), 3)

    if invincible and int(temps * 12) % 2 == 0:
        pygame.draw.circle(surface, (255, 255, 255), (x, y-20), 34, 2)

def dessiner_monstre(surface, monstre, temps):
    x, y = int(monstre["x"]), int(monstre["y"])
    # Ombre
    pygame.draw.ellipse(surface, (13, 34, 36), (x-25, y+18, 50, 13))
    # Corps
    pygame.draw.ellipse(surface, (68, 190, 112), (x-22, y-20, 44, 42))
    pygame.draw.ellipse(surface, (98, 224, 133), (x-15, y-17, 25, 25))
    # Oreilles / cornes
    pygame.draw.polygon(surface, (48, 132, 84), [(x-15,y-14),(x-24,y-31),(x-4,y-20)])
    pygame.draw.polygon(surface, (48, 132, 84), [(x+15,y-14),(x+24,y-31),(x+4,y-20)])
    # Yeux
    pygame.draw.circle(surface, (255, 245, 215), (x-8, y-5), 6)
    pygame.draw.circle(surface, (255, 245, 215), (x+8, y-5), 6)
    pygame.draw.circle(surface, (34, 45, 40), (x-7, y-4), 3)
    pygame.draw.circle(surface, (34, 45, 40), (x+9, y-4), 3)
    # Bouche
    pygame.draw.arc(surface, (30, 80, 56), (x-8, y+1, 16, 10), 0, math.pi, 2)
    # Barre de vie
    pygame.draw.rect(surface, (35, 35, 45), (x-25, y-43, 50, 7), border_radius=3)
    ratio = max(0, monstre["vie"] / monstre["vie_max"])
    pygame.draw.rect(surface, (255, 93, 103), (x-24, y-42, int(48*ratio), 5), border_radius=3)

def creer_monstre():
    x = random.choice([-35, LARGEUR + 35])
    return {
        "x": float(x), "y": random.randint(500, 585),
        "vie": 3, "vie_max": 3,
        "vitesse": random.uniform(55, 90) + niveau * 5,
        "degats_touche": 0
    }

def nouveau_jeu():
    return {
        "x": 170.0, "y": 550.0, "vie": 5, "vie_max": 5,
        "xp": 0, "score": 0, "projectiles": [], "monstres": [],
        "particules": [], "invincible": 0, "recharge": 0,
        "temps_spawn": 0, "termine": False, "gagne": False
    }

# Décor fixe aléatoire, créé une seule fois
etoiles = [(random.randint(0, LARGEUR), random.randint(0, 300), random.choice([1, 1, 2])) for _ in range(90)]
fleurs = [(random.randint(0, LARGEUR), random.randint(495, 635),
           random.choice([(255, 214, 110), (147, 221, 255), (255, 153, 208)])) for _ in range(38)]

niveau = 1
jeu = nouveau_jeu()
temps_total = 0
message = ""
message_temps = 0

def particules(x, y, couleur, nombre=12):
    for _ in range(nombre):
        angle = random.random() * math.tau
        vitesse = random.uniform(40, 190)
        jeu["particules"].append({
            "x": x, "y": y,
            "vx": math.cos(angle)*vitesse, "vy": math.sin(angle)*vitesse,
            "vie": random.uniform(.25, .65), "max": .65,
            "couleur": couleur, "taille": random.randint(2, 5)
        })

def lancer_sort():
    if jeu["recharge"] <= 0 and not jeu["termine"]:
        direction = 1 if direction_sens[0] >= 0 else -1
        jeu["projectiles"].append({
            "x": jeu["x"] + direction*25, "y": jeu["y"]-26,
            "vx": direction*520, "vie": 1.3
        })
        jeu["recharge"] = .22
        particules(jeu["x"]+direction*30, jeu["y"]-27, (112, 224, 255), 4)

direction_sens = [1]
running = True

while running:
    dt = min(horloge.tick(FPS) / 1000, .035)
    temps_total += dt
    touches = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                lancer_sort()
            if event.key == pygame.K_RETURN and jeu["termine"]:
                niveau = 1
                jeu = nouveau_jeu()
            if event.key == pygame.K_r and jeu["termine"]:
                jeu = nouveau_jeu()
                niveau = 1

    if not jeu["termine"]:
        # Déplacement
        dx = int(touches[pygame.K_RIGHT] or touches[pygame.K_d]) - int(touches[pygame.K_LEFT] or touches[pygame.K_q] or touches[pygame.K_a])
        dy = int(touches[pygame.K_DOWN] or touches[pygame.K_s]) - int(touches[pygame.K_UP] or touches[pygame.K_z] or touches[pygame.K_w])
        if dx or dy:
            longueur = math.hypot(dx, dy)
            jeu["x"] += dx / longueur * 240 * dt
            jeu["y"] += dy / longueur * 180 * dt
            if dx:
                direction_sens[0] = 1 if dx > 0 else -1
        jeu["x"] = max(40, min(LARGEUR-40, jeu["x"]))
        jeu["y"] = max(500, min(HAUTEUR-45, jeu["y"]))

        jeu["recharge"] = max(0, jeu["recharge"] - dt)
        jeu["invincible"] = max(0, jeu["invincible"] - dt)

        # Les tirs suivent leur trajectoire
        for tir in jeu["projectiles"][:]:
            tir["x"] += tir["vx"] * dt
            tir["vie"] -= dt
            if tir["vie"] <= 0 or tir["x"] < -20 or tir["x"] > LARGEUR+20:
                jeu["projectiles"].remove(tir)
                continue
            touche_monstre = False
            for monstre in jeu["monstres"][:]:
                if abs(tir["x"]-monstre["x"]) < 28 and abs(tir["y"]-(monstre["y"]-4)) < 30:
                    monstre["vie"] -= 1
                    particules(tir["x"], tir["y"], (130, 226, 255), 8)
                    if tir in jeu["projectiles"]:
                        jeu["projectiles"].remove(tir)
                    touche_monstre = True
                    if monstre["vie"] <= 0:
                        particules(monstre["x"], monstre["y"], (105, 255, 153), 20)
                        jeu["monstres"].remove(monstre)
                        jeu["score"] += 10
                        jeu["xp"] += 1
                        if jeu["xp"] >= niveau * 5:
                            niveau += 1
                            jeu["xp"] = 0
                            jeu["vie"] = min(jeu["vie_max"], jeu["vie"]+1)
                            message = f"Niveau {niveau} ! +1 vie"
                            message_temps = 2.0
                    break

        # Apparition progressive des monstres
        jeu["temps_spawn"] += dt
        intervalle = max(.55, 1.8 - niveau*.12)
        if jeu["temps_spawn"] >= intervalle and len(jeu["monstres"]) < 7:
            jeu["monstres"].append(creer_monstre())
            jeu["temps_spawn"] = 0

        # Les monstres se rapprochent du héros
        for monstre in jeu["monstres"]:
            diff = jeu["x"] - monstre["x"]
            if abs(diff) > 25:
                monstre["x"] += (1 if diff > 0 else -1) * monstre["vitesse"] * dt
            if abs(monstre["x"]-jeu["x"]) < 36 and abs(monstre["y"]-jeu["y"]) < 34 and jeu["invincible"] <= 0:
                jeu["vie"] -= 1
                jeu["invincible"] = 1.0
                particules(jeu["x"], jeu["y"]-15, (255, 100, 120), 14)
                if jeu["vie"] <= 0:
                    jeu["termine"] = True
                    jeu["gagne"] = False

        # Particules magiques
        for p in jeu["particules"][:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 80 * dt
            p["vie"] -= dt
            if p["vie"] <= 0:
                jeu["particules"].remove(p)

    # Dessin de la scène
    dessiner_fond()

    # Pierres anciennes sur le sol
    for px in range(40, LARGEUR, 125):
        pygame.draw.ellipse(ecran, (38, 91, 78), (px, 600 + (px % 3)*5, 62, 16))
        pygame.draw.ellipse(ecran, (57, 119, 91), (px+4, 602 + (px % 3)*5, 53, 9))

    # Sorts
    for tir in jeu["projectiles"]:
        glow = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.circle(glow, (75, 194, 255, 45), (21, 21), 20)
        pygame.draw.circle(glow, (75, 194, 255, 100), (21, 21), 12)
        ecran.blit(glow, (int(tir["x"])-21, int(tir["y"])-21))
        pygame.draw.circle(ecran, (117, 231, 255), (int(tir["x"]), int(tir["y"])), 8)
        pygame.draw.circle(ecran, (255, 255, 255), (int(tir["x"])-2, int(tir["y"])-2), 3)

    for monstre in jeu["monstres"]:
        dessiner_monstre(ecran, monstre, temps_total)

    dessiner_heros(ecran, int(jeu["x"]), int(jeu["y"]), temps_total, jeu["invincible"] > 0)

    # Particules devant les personnages
    for p in jeu["particules"]:
        rayon = max(1, int(p["taille"] * p["vie"] / p["max"]))
        pygame.draw.circle(ecran, p["couleur"], (int(p["x"]), int(p["y"])), rayon)

    # Interface en haut
    panneau = pygame.Surface((LARGEUR, 86), pygame.SRCALPHA)
    pygame.draw.rect(panneau, (9, 15, 35, 205), (0, 0, LARGEUR, 86))
    pygame.draw.line(panneau, (92, 174, 255, 150), (0, 85), (LARGEUR, 85), 2)
    ecran.blit(panneau, (0, 0))
    texte(ecran, "LE ROYAUME MAGIQUE", 22, 13, police, (179, 222, 255))
    texte(ecran, f"Score : {jeu['score']}", 22, 47, petite_police, BLANC)
    texte(ecran, f"Niveau {niveau}", 220, 17, police, OR)
    texte(ecran, "XP", 220, 51, petite_police, BLANC)
    pygame.draw.rect(ecran, (45, 52, 78), (253, 53, 130, 12), border_radius=6)
    ratio_xp = jeu["xp"] / max(1, niveau*5)
    pygame.draw.rect(ecran, (99, 213, 255), (253, 53, int(126*ratio_xp), 8), border_radius=4)

    texte(ecran, "VIE", 430, 17, petite_police, BLANC)
    for i in range(jeu["vie_max"]):
        couleur = (255, 85, 116) if i < jeu["vie"] else (75, 57, 75)
        hx, hy = 480 + i*28, 30
        pygame.draw.circle(ecran, couleur, (hx-5, hy), 7)
        pygame.draw.circle(ecran, couleur, (hx+5, hy), 7)
        pygame.draw.polygon(ecran, couleur, [(hx-12,hy+2),(hx+12,hy+2),(hx,hy+15)])

    texte(ecran, "ZQSD / flèches : bouger", 650, 14, petite_police, (212, 225, 245))
    texte(ecran, "ESPACE : lancer un sort", 650, 43, petite_police, (143, 224, 255))

    if message_temps > 0:
        message_temps -= dt
        texte(ecran, message, LARGEUR//2, 125, police, OR, centre=True)

    if jeu["termine"]:
        voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        voile.fill((7, 10, 28, 190))
        ecran.blit(voile, (0, 0))
        titre = "PARTIE TERMINÉE"
        texte(ecran, titre, LARGEUR//2, 250, grande_police, (255, 125, 143), centre=True)
        texte(ecran, f"Score final : {jeu['score']}", LARGEUR//2, 320, police, BLANC, centre=True)
        texte(ecran, "Appuie sur ENTRÉE pour recommencer", LARGEUR//2, 375, police, OR, centre=True)
        texte(ecran, "ÉCHAP pour quitter", LARGEUR//2, 412, petite_police, BLANC, centre=True)

    pygame.display.flip()

pygame.quit()
