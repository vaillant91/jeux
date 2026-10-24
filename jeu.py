import pygame

# Initialise Pygame pour pouvoir utiliser les fonctions graphiques et la gestion des événements.
pygame.init()

# Crée la fenêtre de jeu et donne un titre à la fenêtre.
fenetre = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Mon premier jeu")

# Position et taille du joueur (un carré bleu).
x = 100
y = 400
taille = 50

# Variables liées au saut.
vitesse_y = 0
gravite = 1
au_sol = False

# Contrôle la boucle principale du jeu.
jeu = True

while jeu:
    # On vérifie les événements du jeu, comme la fermeture de la fenêtre.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jeu = False

    # Récupère l'état des touches enfoncées pour gérer les déplacements.
    touches = pygame.key.get_pressed()

    # Déplacement horizontal du joueur.
    if touches[pygame.K_LEFT]:
        x -= 0.5

    if touches[pygame.K_RIGHT]:
        x += 0.5

    # Le joueur ne peut sauter que s'il est bien sur le sol.
    if touches[pygame.K_SPACE] and au_sol:
        vitesse_y = -25

    # Applique la gravité pour faire tomber le joueur.
    vitesse_y += gravite
    y += vitesse_y

    # Si le joueur touche le sol, on le remet à la bonne hauteur et on arrête sa chute.
    if y >= 500:
        y = 500
        vitesse_y = 0
        au_sol = True
    else:
        au_sol = False

    # Efface tout l'écran avant de redessiner la scène.
    fenetre.fill((30, 30, 40))

    # Dessine le joueur.
    pygame.draw.rect(
        fenetre,
        (0, 200, 255),
        (x, y-taille, taille, 2*taille)
    )

    # Dessine le sol.
    pygame.draw.rect(
        fenetre,
        (80, 200, 80),
        (0, 550, 800, 50)
    )

    # Met à jour l'affichage pour montrer ce qui a été dessiné.
    pygame.display.flip()

# Termine proprement Pygame quand la boucle se termine.
pygame.quit()
