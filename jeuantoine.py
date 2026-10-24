import pygame


# Dimensions de la fenêtre et du niveau, plus la hauteur du sol.
LARGEUR = 900
HAUTEUR = 600
MONDE_LARGEUR = 2600
SOL_Y = 540

# Couleurs utilisées pour dessiner les différents éléments du jeu.
CIEL = (135, 206, 235)
BLEU_FONCE = (35, 55, 90)
VERT = (65, 170, 105)
TERRE = (135, 85, 55)
JAUNE = (255, 220, 65)


def creer_niveau():
    """Construit les plateformes, les cristaux et les créatures du niveau."""
    # Chaque rectangle est décrit par sa position (x, y) et sa taille (largeur, hauteur).
    plateformes = [
        pygame.Rect(0, SOL_Y, 570, 100),
        pygame.Rect(690, SOL_Y, 450, 100),
        pygame.Rect(1270, SOL_Y, 520, 100),
        pygame.Rect(1920, SOL_Y, 680, 100),
        pygame.Rect(190, 440, 150, 22),
        pygame.Rect(420, 365, 150, 22),
        pygame.Rect(760, 440, 155, 22),
        pygame.Rect(990, 355, 150, 22),
        pygame.Rect(1300, 440, 150, 22),
        pygame.Rect(1515, 360, 155, 22),
        pygame.Rect(1840, 440, 150, 22),
        pygame.Rect(2070, 350, 155, 22),
        pygame.Rect(2330, 430, 155, 22),
    ]
    # Crée un petit rectangle pour chaque cristal à ramasser.
    cristaux = [
        pygame.Rect(x, y, 20, 20)
        for x, y in [
            (245, 405), (465, 330), (800, 405), (1035, 320),
            (1350, 405), (1565, 325), (1885, 405), (2120, 315),
            (2380, 395),
        ]
    ]
    # Les créatures se déplacent entre leurs limites min et max.
    creatures = [
        {"rect": pygame.Rect(x, SOL_Y - 30, 34, 30), "min": x - 70, "max": x + 70, "speed": 2}
        for x in (480, 870, 1450, 2005, 2220)
    ]
    return plateformes, cristaux, creatures


def dessiner_personnage(surface, rect, camera_x):
    """Dessine le personnage, en tenant compte du défilement de la caméra."""
    # La position à l'écran est décalée par la caméra, mais pas dans le monde.
    x = rect.x - camera_x
    # Corps bleu : rectangle arrondi placé sous la tête.
    pygame.draw.rect(surface, (39, 111, 190), (x + 5, rect.y + 12, rect.width - 10, rect.height - 12), border_radius=8)
    # Tête couleur peau : cercle au-dessus du corps.
    pygame.draw.circle(surface, (255, 211, 161), (x + rect.width // 2, rect.y + 13), 13)
    # Dessus rouge de la casquette : ellipse posée sur la tête.
    pygame.draw.ellipse(surface, (205, 65, 75), (x + 7, rect.y - 2, 23, 15))
    # Visière rouge foncé : ellipse aplatie devant le dessus de la casquette.
    pygame.draw.ellipse(surface, (155, 42, 58), (x + 4, rect.y + 7, 28, 7))
    # Oeil foncé : petit cercle sur le côté droit de la tête.
    pygame.draw.circle(surface, (30, 40, 55), (x + rect.width // 2 + 5, rect.y + 12), 2)
    # Pied gauche blanc : petit rectangle arrondi au bas du corps.
    pygame.draw.rect(surface, (248, 250, 255), (x + 7, rect.bottom - 8, 11, 8), border_radius=3)
    # Pied droit blanc : petit rectangle arrondi au bas du corps.
    pygame.draw.rect(surface, (248, 250, 255), (x + rect.width - 18, rect.bottom - 8, 11, 8), border_radius=3)


def dessiner_niveau(surface, plateformes, cristaux, creatures, camera_x):
    """Dessine le décor et tous les objets visibles du niveau."""
    surface.fill(CIEL)

    # Les nuages avancent moins vite que le décor : cela donne une impression de profondeur.
    for x, y in ((70, 95), (390, 150), (760, 75), (1120, 130), (1540, 80), (1980, 145), (2380, 90)):
        nuage_x = int((x - camera_x * 0.35) % (MONDE_LARGEUR + 180)) - 100
        pygame.draw.circle(surface, (248, 252, 255), (nuage_x, y), 22)
        pygame.draw.circle(surface, (248, 252, 255), (nuage_x + 25, y - 9), 28)
        pygame.draw.circle(surface, (248, 252, 255), (nuage_x + 53, y), 20)

    # Dessine les plateformes, leurs surfaces en herbe et les détails de la terre.
    for plateforme in plateformes:
        visible = plateforme.move(-camera_x, 0)
        pygame.draw.rect(surface, TERRE, visible)
        pygame.draw.rect(surface, VERT, (visible.x, visible.y, visible.width, 10), border_radius=4)
        for bloc_x in range(visible.x + 12, visible.right, 42):
            pygame.draw.line(surface, (115, 68, 48), (bloc_x, visible.y + 15), (bloc_x, visible.bottom), 2)

    # Transforme chaque cristal en losange jaune.
    for cristal in cristaux:
        centre = (cristal.centerx - camera_x, cristal.centery)
        points = [(centre[0], centre[1] - 12), (centre[0] + 10, centre[1]), (centre[0], centre[1] + 12), (centre[0] - 10, centre[1])]
        pygame.draw.polygon(surface, JAUNE, points)
        pygame.draw.polygon(surface, (255, 250, 190), points, 2)

    # Chaque créature est dessinée comme un petit monstre avec des yeux.
    for creature in creatures:
        rect = creature["rect"].move(-camera_x, 0)
        pygame.draw.ellipse(surface, (157, 70, 95), rect)
        pygame.draw.circle(surface, (255, 255, 255), (rect.x + 11, rect.y + 10), 5)
        pygame.draw.circle(surface, (255, 255, 255), (rect.x + 24, rect.y + 10), 5)
        pygame.draw.circle(surface, BLEU_FONCE, (rect.x + 12, rect.y + 10), 2)
        pygame.draw.circle(surface, BLEU_FONCE, (rect.x + 25, rect.y + 10), 2)

    # Le drapeau marque l'arrivée du niveau.
    sortie_x = MONDE_LARGEUR - 120 - camera_x
    pygame.draw.rect(surface, (245, 245, 235), (sortie_x, SOL_Y - 110, 8, 110))
    pygame.draw.polygon(surface, (235, 105, 75), [(sortie_x + 8, SOL_Y - 108), (sortie_x + 63, SOL_Y - 91), (sortie_x + 8, SOL_Y - 73)])


def nouvelle_partie():
    """Réinitialise le niveau et renvoie les variables de départ."""
    plateformes, cristaux, creatures = creer_niveau()
    joueur = pygame.Rect(60, SOL_Y - 48, 34, 48)
    # Au départ, le joueur est posé au sol, a trois vies et le jeu n'est pas terminé.
    return plateformes, cristaux, creatures, joueur, 0, 0, 3, True, False


def main():
    """Initialise Pygame et exécute la boucle principale du jeu."""
    pygame.init()
    fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("L'aventure des îles flottantes")
    horloge = pygame.time.Clock()
    police = pygame.font.Font(None, 30)
    grande_police = pygame.font.Font(None, 64)

    # Charge le niveau et prépare les variables qui évoluent pendant la partie.
    plateformes, cristaux, creatures, joueur, vitesse_y, score, vies, au_sol, termine = nouvelle_partie()
    lance = True

    while lance:
        # Limite le jeu à 60 images par seconde et adapte les déplacements au temps écoulé.
        dt = min(horloge.tick(60) / 16.6667, 1.5)

        # Réagit à la fermeture de la fenêtre et aux touches pressées une seule fois.
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                lance = False
            elif evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_ESCAPE:
                    lance = False
                elif evenement.key == pygame.K_r and termine:
                    plateformes, cristaux, creatures, joueur, vitesse_y, score, vies, au_sol, termine = nouvelle_partie()

        # Lit l'état des touches et met à jour le personnage tant que la partie est en cours.
        touches = pygame.key.get_pressed()
        if not termine:
            vitesse_x = 0
            # Les flèches ou A/D déplacent le joueur ; Espace, Haut ou W déclenchent le saut.
            if touches[pygame.K_LEFT] or touches[pygame.K_a]:
                vitesse_x = -5
            if touches[pygame.K_RIGHT] or touches[pygame.K_d]:
                vitesse_x = 5
            if (touches[pygame.K_SPACE] or touches[pygame.K_UP] or touches[pygame.K_w]) and au_sol:
                vitesse_y = -13
                au_sol = False

            # Déplace le joueur horizontalement et l'empêche de sortir du niveau.
            joueur.x += round(vitesse_x * dt)
            joueur.x = max(0, min(joueur.x, MONDE_LARGEUR - joueur.width))
            # Si le joueur heurte le côté d'une plateforme, il s'arrête contre elle.
            for plateforme in plateformes:
                if joueur.colliderect(plateforme):
                    if vitesse_x > 0:
                        joueur.right = plateforme.left
                    elif vitesse_x < 0:
                        joueur.left = plateforme.right

            # Applique la gravité, puis pose le joueur sur les plateformes qu'il traverse en tombant.
            ancienne_bas = joueur.bottom
            vitesse_y = min(vitesse_y + 0.65 * dt, 14)
            joueur.y += round(vitesse_y * dt)
            au_sol = False
            for plateforme in plateformes:
                if joueur.colliderect(plateforme):
                    if vitesse_y > 0 and ancienne_bas <= plateforme.top + 8:
                        joueur.bottom = plateforme.top
                        vitesse_y = 0
                        au_sol = True
                    elif vitesse_y < 0:
                        joueur.top = plateforme.bottom
                        vitesse_y = 0

            # La copie de la liste permet de retirer un cristal sans interrompre la boucle.
            for cristal in cristaux[:]:
                if joueur.colliderect(cristal):
                    cristaux.remove(cristal)
                    score += 1

            # Les créatures patrouillent ; sauter dessus les élimine, les toucher autrement coûte une vie.
            for creature in creatures[:]:
                creature["rect"].x += creature["speed"] * dt
                if creature["rect"].x < creature["min"] or creature["rect"].x > creature["max"]:
                    creature["speed"] *= -1
                if joueur.colliderect(creature["rect"]):
                    if vitesse_y > 0 and ancienne_bas <= creature["rect"].top + 12:
                        creatures.remove(creature)
                        vitesse_y = -8
                        score += 2
                    else:
                        vies -= 1
                        joueur.x, joueur.y = 60, SOL_Y - joueur.height
                        vitesse_y = 0
                        au_sol = True
                        if vies <= 0:
                            termine = True
                        break

            # Une chute hors de l'écran fait perdre une vie et replace le joueur au départ.
            if joueur.top > HAUTEUR + 100:
                vies -= 1
                joueur.x, joueur.y = 60, SOL_Y - joueur.height
                vitesse_y = 0
                au_sol = True
                if vies <= 0:
                    termine = True

            # Atteindre le drapeau termine la partie et marque une victoire.
            if joueur.x >= MONDE_LARGEUR - 145:
                termine = True
                gagne = True
            else:
                gagne = False
        else:
            gagne = joueur.x >= MONDE_LARGEUR - 145

        # Suit le joueur sans laisser la caméra dépasser les bords du niveau.
        camera_x = max(0, min(joueur.centerx - LARGEUR // 2, MONDE_LARGEUR - LARGEUR))
        dessiner_niveau(fenetre, plateformes, cristaux, creatures, camera_x)
        dessiner_personnage(fenetre, joueur, camera_x)

        # Affiche le score et les commandes en haut de la fenêtre.
        hud = police.render(f"Cristaux : {score}     Vies : {vies}     Deplacement : A/D ou fleches     Saut : Espace", True, BLEU_FONCE)
        fenetre.blit(hud, (18, 16))

        # Recouvre l'écran et affiche un message quand la partie est gagnée ou perdue.
        if termine:
            voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            voile.fill((15, 25, 45, 175))
            fenetre.blit(voile, (0, 0))
            message = "Bravo, aventure terminee !" if gagne else "Partie terminee"
            texte = grande_police.render(message, True, (255, 255, 255))
            conseil = police.render("Appuie sur R pour recommencer ou Echap pour quitter", True, (255, 255, 255))
            fenetre.blit(texte, texte.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 25)))
            fenetre.blit(conseil, conseil.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 + 28)))

        # Présente à l'écran la nouvelle image dessinée.
        pygame.display.flip()

    # Ferme proprement Pygame lorsque le joueur quitte.
    pygame.quit()


# Cette condition lance le jeu uniquement si ce fichier est exécuté directement.
if __name__ == "__main__":
    main()