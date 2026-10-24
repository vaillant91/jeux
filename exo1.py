import pygame

pygame.init()

fenetre = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Mon premier exercice")

x = 100
y = 500

vitesse = 0.1

jeu = True

while jeu:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jeu = False

    touches = pygame.key.get_pressed()

    if touches[pygame.K_RIGHT]:
        x = x + vitesse

    if touches[pygame.K_LEFT]:
        x = x - vitesse

    if touches[pygame.K_UP]:
        y = y - vitesse

    fenetre.fill((30, 30, 30))

    pygame.draw.rect(fenetre, (0, 200, 255), (x, y, 50, 50))

    pygame.display.flip()

pygame.quit()