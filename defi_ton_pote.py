"""Defi arcade local a partager avec un code de graine."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import random
import secrets
import string
import sys
import zlib
from datetime import date
from pathlib import Path

import pygame

from cache_cache_3d import CacheCache3D
from realisme_visuel import GameAtmosphere, MaterialRenderer


LARGEUR = 1000
HAUTEUR = 700
DUREE_PARTIE = 45.0
NIVEAUX_CARTE_BASE = 12
TAILLE_CASE = 48
COLONNES_NIVEAU = 40
LIGNES_NIVEAU = 11
DEBUT_CARTE = pygame.Vector2(24, 112)


def creer_fenetre_jeu() -> pygame.Surface:
    flags = getattr(pygame, "RESIZABLE", 0)
    try:
        return pygame.display.set_mode(
            (LARGEUR, HAUTEUR), flags | getattr(pygame, "SCALED", 0)
        )
    except pygame.error:
        return pygame.display.set_mode((LARGEUR, HAUTEUR), flags)


def appareil_tactile() -> bool:
    if sys.platform == "android":
        return True
    try:
        from pygame._sdl2 import touch
        return touch.get_num_devices() > 0
    except (ImportError, AttributeError, pygame.error):
        return False
SOL = 1
PLATEFORME = 2
PIC = 3
POINT_CONTROLE = 4
RESSORT = 5
GEMME = 6
COEUR = 7
OUTIL_DEPART = 8
OUTIL_ARRIVEE = 9
OUTIL_MONSTRE = 10
OUTIL_MONSTRE_CRACHEUR = 11
OUTIL_MONSTRE_CHARGEUR = 12
OUTIL_MONSTRE_SAUTEUR = 13
OUTILS_MONSTRES = (
    OUTIL_MONSTRE, OUTIL_MONSTRE_CRACHEUR,
    OUTIL_MONSTRE_CHARGEUR, OUTIL_MONSTRE_SAUTEUR,
)
MONSTRE_TRAQUEUR = 0
MONSTRE_CRACHEUR = 1
MONSTRE_CHARGEUR = 2
MONSTRE_SAUTEUR = 3
LARGEUR_MONSTRE = 42
HAUTEUR_MONSTRE = 40
OUTILS_PAR_CATEGORIE = {
    "blocs": (0, SOL, PLATEFORME, PIC, RESSORT, GEMME, COEUR,
              OUTIL_DEPART, OUTIL_ARRIVEE),
    "monstres": OUTILS_MONSTRES,
    "checkpoint": (POINT_CONTROLE,),
}
CODE_ALPHABET = string.ascii_uppercase + string.digits
THEMES_PARCOURS = ("prairie", "volcan", "glace", "desert")
NOMS_THEMES = {"prairie": "PRAIRIE", "volcan": "VOLCAN",
               "glace": "GLACE", "desert": "DESERT"}
ACCENTS_THEMES = {"prairie": (100, 220, 151), "volcan": (255, 112, 51),
                  "glace": (117, 221, 255), "desert": (255, 190, 82)}
SURFACES_TEINTE_THEME: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}
FOND = (12, 17, 33)
PANNEAU = (23, 31, 55)
BLANC = (239, 244, 255)
GRIS = (153, 168, 193)
CYAN = (72, 229, 226)
ROUGE = (255, 91, 116)
JAUNE = (255, 210, 104)
VERT = (100, 232, 151)


def dessiner_arriere_plan_theme(surface: pygame.Surface, theme: str,
                                decalage: float = 0.0,
                                zone: pygame.Rect | None = None) -> None:
    """Peint un paysage colore pour chaque biome hors prairie."""
    if theme == "prairie":
        return
    ancien_clip = surface.get_clip()
    zone = (zone or surface.get_rect()).clip(surface.get_rect())
    if zone.width <= 0 or zone.height <= 0:
        return
    surface.set_clip(zone)
    palettes = {
        "volcan": ((17, 14, 30), (104, 37, 31)),
        "glace": ((28, 66, 125), (151, 218, 243)),
        "desert": ((64, 32, 58), (245, 145, 75)),
    }
    haut, bas = palettes[theme]
    for y in range(zone.top, zone.bottom):
        progression = (y - zone.top) / max(1, zone.height - 1)
        couleur = tuple(round(a + (b - a) * progression)
                        for a, b in zip(haut, bas))
        pygame.draw.line(surface, couleur, (zone.left, y), (zone.right, y))

    if theme == "volcan":
        # Brume rouge au-dessus de plusieurs lignes de lave et de cendres.
        centre = round(zone.left + zone.width * .72 - decalage * .18)
        sommet = zone.top + round(zone.height * .20)
        pied = zone.bottom + 45
        pygame.draw.ellipse(surface, (164, 55, 27),
                            (centre - 230, sommet + 110, 470, 210))
        pygame.draw.polygon(surface, (51, 39, 47), [
            (zone.left - 40, pied), (centre - 330, pied),
            (centre - 104, sommet + 108), (centre - 63, sommet + 68),
            (centre - 20, sommet + 84), (centre + 25, sommet + 76),
            (centre + 82, sommet + 112), (centre + 305, pied),
            (zone.right + 40, pied),
        ])
        pygame.draw.ellipse(surface, (28, 24, 34),
                            (centre - 65, sommet + 58, 104, 30))
        pygame.draw.arc(surface, (255, 104, 37),
                        (centre - 78, sommet + 55, 130, 44), .12, 3.0, 5)
        for index, decalage_lave in enumerate((-64, -5, 57)):
            points = [
                (centre + decalage_lave, sommet + 89),
                (centre + decalage_lave + (index - 1) * 13, sommet + 151),
                (centre + decalage_lave + (index - 1) * 23, sommet + 203),
                (centre + decalage_lave + (index - 1) * 34, pied - 5),
            ]
            pygame.draw.lines(surface, (219, 62, 29), False, points, 10)
            pygame.draw.lines(surface, (255, 152, 44), False, points, 4)
        for index in range(8):
            x = zone.left + (index * 173 + 48 - round(decalage * .34)) % (zone.width + 120) - 50
            y = zone.top + 35 + (index * 47 % max(70, zone.height // 2))
            pygame.draw.circle(surface, (255, 123, 53), (x, y), 2 + index % 3)
        pygame.draw.polygon(surface, (71, 39, 43), [
            (zone.left - 20, zone.bottom - 24),
            (zone.left + zone.width // 3, zone.bottom - 140),
            (zone.left + zone.width * 2 // 3, zone.bottom - 65),
            (zone.right + 20, zone.bottom - 185),
            (zone.right + 20, zone.bottom + 30), (zone.left - 20, zone.bottom + 30),
        ])
        pygame.draw.line(surface, (255, 104, 34),
                         (zone.left, zone.bottom - 23), (zone.right, zone.bottom - 23), 4)
    elif theme == "glace":
        pygame.draw.circle(surface, (225, 247, 255),
                           (zone.left + round(zone.width * .78),
                            zone.top + round(zone.height * .20)),
                           max(18, zone.width // 30))
        for index in range(-1, zone.width // 205 + 2):
            base_x = zone.left + index * 205 - round(decalage * .22)
            peak_x = base_x + 106
            peak_y = zone.top + 85 + (abs(index * 31) % 74)
            base_y = zone.bottom - 40
            pygame.draw.polygon(surface, (65, 123, 177), [
                (base_x - 20, base_y), (peak_x, peak_y),
                (base_x + 218, base_y),
            ])
            cap = 38 + abs(index * 17) % 23
            pygame.draw.polygon(surface, (225, 247, 255), [
                (peak_x - cap, peak_y + cap),
                (peak_x, peak_y),
                (peak_x + cap, peak_y + cap // 2),
                (peak_x + 13, peak_y + cap // 3),
                (peak_x, peak_y + cap // 2),
                (peak_x - 13, peak_y + cap // 3),
            ])
        pygame.draw.polygon(surface, (113, 175, 208), [
            (zone.left - 20, zone.bottom - 35),
            (zone.left + zone.width // 3, zone.bottom - 108),
            (zone.left + zone.width * 2 // 3, zone.bottom - 54),
            (zone.right + 20, zone.bottom - 130),
            (zone.right + 20, zone.bottom + 20), (zone.left - 20, zone.bottom + 20),
        ])
        for index in range(24):
            x = zone.left + (index * 97 + 31 - round(decalage * .1)) % zone.width
            y = zone.top + (index * 53 + 27) % max(1, zone.height)
            pygame.draw.circle(surface, (224, 248, 255), (x, y), 1 + index % 2)
    else:
        soleil = (zone.left + round(zone.width * .77),
                  zone.top + round(zone.height * .22))
        pygame.draw.circle(surface, (255, 218, 134), soleil, max(22, zone.width // 24))
        for index, amplitude in enumerate((45, 70, 90)):
            points = [(zone.left - 20, zone.bottom + 20)]
            for x in range(zone.left - 20, zone.right + 25, 18):
                y = round(zone.top + zone.height * (.61 + index * .075)
                          + math.sin((x + decalage * (.12 + index * .05)) * .004) * amplitude)
                points.append((x, y))
            points.extend(((zone.right + 20, zone.bottom + 20),
                           (zone.left - 20, zone.bottom + 20)))
            pygame.draw.polygon(surface, (
                (170, 91 + index * 15, 63 + index * 8) if index == 0
                else (205, 127 + index * 10, 67 + index * 8)
            ), points)
        for x_base in (zone.left + zone.width // 5, zone.left + zone.width * 4 // 5):
            x = round(x_base - decalage * .08)
            y = zone.bottom - 98
            pygame.draw.rect(surface, (48, 107, 67), (x, y, 13, 78), border_radius=5)
            pygame.draw.rect(surface, (48, 107, 67), (x - 13, y + 20, 13, 10), border_radius=4)
            pygame.draw.rect(surface, (48, 107, 67), (x - 13, y + 5, 8, 25), border_radius=4)
            pygame.draw.rect(surface, (48, 107, 67), (x + 11, y + 37, 13, 10), border_radius=4)
            pygame.draw.rect(surface, (48, 107, 67), (x + 16, y + 27, 8, 25), border_radius=4)
    if theme == "volcan":
        # Un panache de cendres adoucit le contour du cratere.
        for index in range(7):
            derive = round(math.sin(index * 1.63 + decalage * .003) * (8 + index * 4))
            x_fumee = centre + derive
            y_fumee = sommet + 67 - index * 17
            rayon_x = 42 + index * 5
            rayon_y = 23 + index * 3
            nuance = 39 + index * 2
            pygame.draw.ellipse(surface, (nuance + 4, nuance, nuance + 7),
                                (x_fumee - rayon_x, y_fumee - rayon_y,
                                 rayon_x * 2, rayon_y * 2))
        for index in range(31):
            x = zone.left + (index * 137 + 53 - round(decalage * .29)) % zone.width
            y = zone.top + 20 + (index * 61 + 17) % max(1, zone.height * 2 // 3)
            pygame.draw.circle(surface, (158, 107, 83), (x, y), 1 + index % 2)
    elif theme == "glace":
        # Les faces ombrees et les aretes rendent les cretes moins plates.
        for index in range(-1, zone.width // 205 + 2):
            base_x = zone.left + index * 205 - round(decalage * .22)
            peak_x = base_x + 106
            peak_y = zone.top + 85 + (abs(index * 31) % 74)
            base_y = zone.bottom - 40
            pygame.draw.polygon(surface, (50, 96, 145), [
                (peak_x, peak_y), (base_x + 218, base_y),
                (base_x + 112, base_y),
            ])
            pygame.draw.line(surface, (188, 229, 244),
                             (peak_x, peak_y + 22), (peak_x - 19, peak_y + 48), 2)
        for index in range(34):
            x = zone.left + (index * 83 + 19 - round(decalage * .12)) % zone.width
            y = zone.top + (index * 59 + 13) % max(1, zone.height)
            pygame.draw.line(surface, (222, 246, 255), (x, y), (x + 2, y + 8), 1)
    else:
        # Fines strates suivent les dunes et donnent une echelle au relief.
        for index, amplitude in enumerate((45, 70, 90)):
            points = []
            for x in range(zone.left - 10, zone.right + 15, 20):
                y = round(zone.top + zone.height * (.61 + index * .075)
                          + math.sin((x + decalage * (.12 + index * .05)) * .004) * amplitude
                          + 12 + index * 4)
                points.append((x, y))
            pygame.draw.lines(surface, (226, 158 + index * 8, 91 + index * 7),
                              False, points, 2)

    surface.set_clip(ancien_clip)


def surface_teinte_theme(theme: str, taille: tuple[int, int]) -> pygame.Surface:
    """Retourne un voile de couleur reutilisable pour teinter une texture."""
    cle = (theme, taille)
    surface = SURFACES_TEINTE_THEME.get(cle)
    if surface is None:
        surface = pygame.Surface(taille, pygame.SRCALPHA)
        couleur, alpha = {
            "volcan": ((184, 74, 43), 68),
            "glace": ((106, 184, 232), 76),
            "desert": ((237, 171, 91), 62),
        }[theme]
        surface.fill((*couleur, alpha))
        SURFACES_TEINTE_THEME[cle] = surface
    return surface


def dessiner_bloc_theme(surface: pygame.Surface, rect: pygame.Rect,
                        type_case: int, theme: str, variante: int = 0,
                        materiaux: MaterialRenderer | None = None) -> None:
    """Dessine les blocs du biome avec grain, relief et reflets coherents."""
    x, y, largeur, hauteur = rect
    if largeur <= 0 or hauteur <= 0:
        return
    if theme == "volcan":
        roche, dessus, lueur = (48, 42, 48), (112, 52, 40), (255, 113, 35)
        reflet = (255, 178, 61)
        famille = "stone"
    elif theme == "glace":
        roche, dessus, lueur = (58, 112, 151), (185, 232, 248), (93, 207, 239)
        reflet = (240, 254, 255)
        famille = "concrete"
    else:
        roche, dessus, lueur = (139, 86, 48), (222, 163, 82), (255, 207, 107)
        reflet = (255, 231, 162)
        famille = "soil"

    def dessiner_matiere(zone: pygame.Rect, id_matiere: int) -> None:
        if materiaux is None:
            pygame.draw.rect(surface, roche, zone, border_radius=2)
            return
        texture = materiaux.texture(famille, zone.width, zone.height, id_matiere)
        surface.blit(texture, zone.topleft)
        surface.blit(surface_teinte_theme(theme, zone.size), zone.topleft)

    if type_case == SOL:
        dessiner_matiere(rect, variante)
        bandeau = max(5, hauteur // 5)
        pygame.draw.polygon(surface, dessus, [
            (x + 1, y + 2), (x + largeur // 3, y + 1),
            (x + largeur * 2 // 3, y + 3), (x + largeur - 2, y + 1),
            (x + largeur - 2, y + bandeau),
            (x + 2, y + bandeau + 2),
        ])
        pygame.draw.line(surface, reflet, (x + 3, y + 2),
                         (x + largeur - 4, y + 2), 1)
        if theme == "volcan":
            phase = .78 + .22 * ((math.sin(pygame.time.get_ticks() * .004
                                            + variante * .83) + 1) * .5)
            lueur = (255, round(77 + 45 * phase), round(24 + 13 * phase))
            for index in range(3):
                fissure_x = x + 7 + ((index * 17 + variante * 5) % max(8, largeur - 14))
                points = [
                    (fissure_x, y + bandeau + 3),
                    (fissure_x - 4, y + bandeau + hauteur // 3),
                    (fissure_x + 3, y + bandeau + hauteur // 2),
                    (fissure_x - 2, y + hauteur - 3),
                ]
                pygame.draw.lines(surface, (41, 31, 34), False, points, 5)
                pygame.draw.lines(surface, lueur, False, points, 2)
                pygame.draw.circle(surface, reflet, points[1], 1)
        elif theme == "glace":
            pygame.draw.polygon(surface, (221, 245, 253), [
                (x + 2, y + 2), (x + largeur // 3, y + 3),
                (x + largeur // 2, y + bandeau), (x + largeur - 2, y + 2),
            ])
            pygame.draw.line(surface, (239, 252, 255),
                             (x + 6, y + bandeau + 7), (x + largeur // 2, y + hauteur - 5), 1)
            pygame.draw.line(surface, (125, 197, 224),
                             (x + largeur // 2, y + hauteur // 2),
                             (x + largeur - 7, y + hauteur - 8), 1)
        else:
            for index in range(3):
                strate_y = y + bandeau + 7 + index * max(5, hauteur // 5)
                if strate_y < y + hauteur - 3:
                    pygame.draw.line(surface, (91, 58, 42),
                                     (x + 4, strate_y), (x + largeur - 5, strate_y + (index % 2)),
                                     1)
                    pygame.draw.line(surface, reflet,
                                     (x + 7, strate_y + 2),
                                     (x + largeur // 2, strate_y + 2), 1)
    elif type_case == PLATEFORME:
        y_plateforme = y + hauteur // 4
        h_plateforme = max(7, hauteur // 3)
        zone_plateforme = pygame.Rect(x + 1, y_plateforme, largeur - 2, h_plateforme)
        dessiner_matiere(zone_plateforme, variante)
        pygame.draw.polygon(surface, dessus, [
            (x + 2, y_plateforme + 1), (x + largeur // 3, y_plateforme),
            (x + largeur * 2 // 3, y_plateforme + 1), (x + largeur - 2, y_plateforme),
            (x + largeur - 3, y_plateforme + max(3, h_plateforme // 3)),
            (x + 2, y_plateforme + max(3, h_plateforme // 3)),
        ])
        pygame.draw.line(surface, lueur, (x + 4, y_plateforme + h_plateforme - 2),
                         (x + largeur - 5, y_plateforme + h_plateforme - 2), 2)
        if theme == "volcan":
            pygame.draw.lines(surface, reflet, False, [
                (x + largeur // 3, y_plateforme + 2),
                (x + largeur // 2, y_plateforme + h_plateforme // 2),
                (x + largeur * 2 // 3, y_plateforme + 2),
            ], 2)
        elif theme == "glace":
            pygame.draw.line(surface, (244, 253, 255),
                             (x + 7, y_plateforme + 2),
                             (x + largeur // 2, y_plateforme + 2), 2)
        else:
            pygame.draw.line(surface, (104, 65, 39),
                             (x + 6, y_plateforme + h_plateforme // 2),
                             (x + largeur - 6, y_plateforme + h_plateforme // 2), 1)
    elif type_case == PIC:
        for centre_x in (x + largeur // 4, x + largeur // 2, x + largeur * 3 // 4):
            pointe_y = y + hauteur // 5
            demi_largeur = max(3, largeur // 5)
            pygame.draw.polygon(surface, roche, [
                (centre_x - demi_largeur, y + hauteur - 5),
                (centre_x, pointe_y),
                (centre_x + demi_largeur, y + hauteur - 5),
            ])
            pygame.draw.line(surface, reflet, (centre_x, pointe_y + 3),
                             (centre_x - 3, y + hauteur // 2), 2)
        pygame.draw.line(surface, lueur, (x + 3, y + hauteur - 3),
                         (x + largeur - 4, y + hauteur - 3), max(2, hauteur // 12))



def dessiner_coeur(surface: pygame.Surface, centre: tuple[int, int], taille: int = 20) -> None:
    """Dessine un coeur de soin a la taille demandee."""
    rayon = max(4, taille // 2)
    x, y = centre
    couleur = (255, 93, 137)
    pygame.draw.circle(surface, couleur, (x - rayon // 2, y - rayon // 4), rayon // 2)
    pygame.draw.circle(surface, couleur, (x + rayon // 2, y - rayon // 4), rayon // 2)
    pygame.draw.polygon(surface, couleur, [
        (x - rayon, y - rayon // 8), (x + rayon, y - rayon // 8),
        (x, y + rayon),
    ])


def dessiner_monstre(surface: pygame.Surface, rect: pygame.Rect,
                      type_monstre: int = MONSTRE_TRAQUEUR, temps: float = 0.0,
                      direction: float = 1.0, etat: str = "patrouille") -> None:
    """Dessine des creatures organiques detaillees et animees."""
    if rect.width <= 0 or rect.height <= 0:
        return
    w, h = rect.size
    sprite = pygame.Surface((w, h), pygame.SRCALPHA)
    phase = temps * 9.0
    pas = round(math.sin(phase) * 2)
    pygame.draw.ellipse(sprite, (5, 9, 17, 105),
                        (4, h - 8, max(8, w - 8), 7))

    if type_monstre == MONSTRE_CRACHEUR:
        peau, ombre, lumiere = (92, 151, 77), (43, 77, 50), (161, 201, 105)
        pygame.draw.polygon(sprite, ombre, [
            (13, 24), (5, 22), (0, 18 + pas), (2, 26), (12, 29),
        ])
        for index, px in enumerate((9, 18, 31)):
            swing = pas if index % 2 else -pas
            pygame.draw.line(sprite, ombre, (px, 24), (px - 2, 32 + swing), 5)
            pygame.draw.line(sprite, peau, (px, 26), (px - 2, 32 + swing), 2)
            pygame.draw.line(sprite, ombre, (px - 5, 33 + swing),
                             (px + 1, 33 + swing), 2)
        pygame.draw.ellipse(sprite, ombre, (7, 13, 29, 20))
        pygame.draw.ellipse(sprite, peau, (8, 11, 28, 19))
        pygame.draw.ellipse(sprite, lumiere, (12, 13, 16, 6))
        pygame.draw.ellipse(sprite, (64, 111, 68), (23, 12, 19, 14))
        pygame.draw.ellipse(sprite, peau, (27, 11, 15, 12))
        pygame.draw.ellipse(sprite, (48, 76, 53), (32, 19, 10, 5))
        pygame.draw.line(sprite, (34, 59, 43), (31, 23), (41, 23), 2)
        for px, py in ((13, 14), (19, 12), (25, 13), (16, 19), (23, 21)):
            pygame.draw.circle(sprite, (112, 164, 88), (px, py), 2)
        pygame.draw.polygon(sprite, (58, 99, 62), [(12, 12), (15, 5), (18, 13)])
        pygame.draw.polygon(sprite, (58, 99, 62), [(19, 12), (23, 4), (25, 13)])
        pygame.draw.ellipse(sprite, (54, 85, 56), (28, 9, 8, 7))
        pygame.draw.circle(sprite, (226, 234, 159), (32, 12), 3)
        pygame.draw.circle(sprite, (27, 43, 34), (33, 12), 1)
        pygame.draw.circle(sprite, (105, 202, 91), (17, 27), 4)
        pygame.draw.circle(sprite, (174, 242, 116), (16, 26), 2)
        pygame.draw.circle(sprite, (35, 77, 48), (38, 21), 1)
    elif type_monstre == MONSTRE_CHARGEUR:
        peau, ombre, lumiere = (170, 76, 59), (76, 39, 43), (231, 133, 89)
        for px, swing in ((9, pas), (17, -pas), (29, -pas), (36, pas)):
            pygame.draw.line(sprite, ombre, (px, 24), (px + 1, 33 + swing), 6)
            pygame.draw.line(sprite, peau, (px, 25), (px + 1, 32 + swing), 2)
            pygame.draw.line(sprite, (48, 35, 39), (px - 3, 34 + swing),
                             (px + 4, 34 + swing), 2)
        pygame.draw.ellipse(sprite, ombre, (3, 12, 37, 20))
        pygame.draw.ellipse(sprite, peau, (5, 10, 34, 19))
        pygame.draw.ellipse(sprite, (111, 53, 52), (7, 7, 30, 18))
        pygame.draw.ellipse(sprite, (194, 92, 65), (9, 8, 26, 14))
        for px in (14, 21, 28):
            pygame.draw.arc(sprite, (232, 145, 94), (px - 5, 9, 10, 12),
                            0.1, 2.9, 2)
        pygame.draw.polygon(sprite, (232, 174, 111),
                            [(29, 13), (40, 8), (37, 17), (31, 20)])
        pygame.draw.polygon(sprite, (249, 225, 167),
                            [(35, 16), (42, 18), (37, 24), (33, 21)])
        pygame.draw.polygon(sprite, (246, 215, 165),
                            [(35, 23), (41, 26), (36, 29)])
        pygame.draw.ellipse(sprite, (89, 43, 47), (29, 17, 12, 8))
        pygame.draw.circle(sprite, (255, 195, 102), (32, 16), 3)
        pygame.draw.circle(sprite, (35, 30, 36), (33, 16), 1)
        pygame.draw.line(sprite, lumiere, (10, 21), (25, 24), 2)
        pygame.draw.line(sprite, (72, 43, 43), (8, 26), (29, 29), 2)
        pygame.draw.circle(sprite, (255, 204, 139), (13, 12), 2)
    elif type_monstre == MONSTRE_SAUTEUR:
        peau, ombre, lumiere = (75, 139, 177), (35, 60, 92), (135, 207, 220)
        ailes = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(ailes, (135, 221, 235, 70), (8, 5, 18, 15))
        pygame.draw.ellipse(ailes, (135, 221, 235, 70), (20, 4, 17, 15))
        pygame.draw.line(ailes, (210, 249, 245, 150), (12, 17), (20, 7), 1)
        pygame.draw.line(ailes, (210, 249, 245, 150), (25, 17), (31, 7), 1)
        sprite.blit(ailes, (0, 0))
        for index, px in enumerate((11, 20, 29, 37)):
            end_y = 31 + (pas if index % 2 else -pas)
            pygame.draw.line(sprite, ombre, (px, 21), (px - 4, 27), 3)
            pygame.draw.line(sprite, peau, (px - 4, 27), (px - 2, end_y), 3)
            pygame.draw.circle(sprite, lumiere, (px - 2, end_y), 2)
            pygame.draw.line(sprite, (32, 49, 75), (px - 2, end_y),
                             (px + 2, end_y + 2), 1)
        pygame.draw.ellipse(sprite, ombre, (6, 13, 20, 16))
        pygame.draw.ellipse(sprite, peau, (7, 11, 19, 15))
        pygame.draw.ellipse(sprite, (46, 91, 129), (21, 14, 15, 13))
        pygame.draw.ellipse(sprite, lumiere, (23, 14, 10, 5))
        pygame.draw.ellipse(sprite, (42, 79, 110), (27, 10, 13, 12))
        pygame.draw.arc(sprite, lumiere, (26, 9, 13, 12), 0.2, 2.8, 2)
        for px, py in ((31, 13), (36, 14), (33, 18)):
            pygame.draw.circle(sprite, (241, 236, 176), (px, py), 2)
            pygame.draw.circle(sprite, (26, 39, 55), (px + 1, py), 1)
        pygame.draw.arc(sprite, (29, 51, 71), (29, 18, 10, 6), 3.2, 6.1, 1)
        pygame.draw.line(sprite, peau, (30, 10), (28, 3), 2)
        pygame.draw.line(sprite, peau, (35, 10), (39, 4), 2)
        pygame.draw.circle(sprite, lumiere, (28, 3), 2)
        pygame.draw.circle(sprite, lumiere, (39, 4), 2)
        pygame.draw.ellipse(sprite, (42, 86, 127), (8, 15, 8, 7))
        pygame.draw.line(sprite, (175, 223, 232), (10, 17), (14, 19), 1)
    else:
        peau, ombre, lumiere = (128, 78, 169), (54, 37, 75), (190, 130, 211)
        pygame.draw.polygon(sprite, ombre, [(8, 23), (1, 20), (0, 17 + pas),
                                            (8, 26), (14, 28)])
        for px, swing in ((10, pas), (18, -pas), (28, -pas), (36, pas)):
            pygame.draw.line(sprite, ombre, (px, 24), (px - 2, 32 + swing), 6)
            pygame.draw.line(sprite, (151, 102, 180), (px, 26),
                             (px - 2, 32 + swing), 2)
            pygame.draw.line(sprite, (44, 34, 59), (px - 5, 33 + swing),
                             (px + 2, 33 + swing), 2)
        pygame.draw.ellipse(sprite, ombre, (5, 12, 31, 20))
        pygame.draw.ellipse(sprite, peau, (6, 10, 30, 19))
        pygame.draw.ellipse(sprite, (89, 53, 129), (9, 14, 21, 12))
        pygame.draw.ellipse(sprite, (212, 165, 219), (11, 25, 19, 5))
        pygame.draw.polygon(sprite, (85, 57, 112), [(10, 14), (8, 6), (16, 13)])
        pygame.draw.polygon(sprite, (85, 57, 112), [(23, 12), (29, 4), (30, 15)])
        pygame.draw.ellipse(sprite, (100, 61, 143), (25, 12, 16, 16))
        pygame.draw.ellipse(sprite, peau, (27, 11, 14, 15))
        pygame.draw.ellipse(sprite, (66, 42, 89), (31, 20, 11, 6))
        pygame.draw.line(sprite, (43, 35, 58), (31, 24), (40, 24), 2)
        pygame.draw.polygon(sprite, (249, 226, 241),
                            [(34, 22), (36, 22), (35, 26)])
        pygame.draw.polygon(sprite, (249, 226, 241),
                            [(39, 22), (41, 22), (40, 25)])
        pygame.draw.ellipse(sprite, (246, 210, 115), (28, 14, 7, 6))
        pygame.draw.ellipse(sprite, (246, 210, 115), (36, 14, 5, 6))
        pygame.draw.circle(sprite, (27, 28, 42), (32, 17), 2)
        pygame.draw.circle(sprite, (27, 28, 42), (38, 17), 2)
        for px, py in ((12, 17), (18, 14), (20, 20), (25, 23)):
            pygame.draw.circle(sprite, lumiere, (px, py), 1)

    if etat == "windup":
        couleur_signal = ((226, 255, 131) if type_monstre == MONSTRE_CRACHEUR
                          else (255, 183, 97) if type_monstre == MONSTRE_CHARGEUR
                          else (255, 224, 126))
        pulsation = 3 + round((math.sin(temps * 16) + 1) * 1.5)
        pygame.draw.circle(sprite, (*couleur_signal, 100),
                           (w - 6, 13), pulsation + 4)
        pygame.draw.circle(sprite, couleur_signal, (w - 6, 13), pulsation, 1)
    if etat in ("lunge", "charge"):
        couleur_trace = (255, 204, 123, 110) if etat == "charge" else (210, 185, 240, 90)
        for index in range(3):
            yy = 12 + index * 7
            pygame.draw.line(sprite, couleur_trace, (2, yy), (11, yy - 2), 2)
    if direction < 0:
        sprite = pygame.transform.flip(sprite, True, False)
    surface.blit(sprite, rect.topleft)


def dessiner_projectile_monstre(surface: pygame.Surface, rect: pygame.Rect,
                                temps: float = 0.0) -> None:
    """Dessine une globule acide translucide avec une trainee lumineuse."""
    pulsation = 1 + round((math.sin(temps * 13) + 1) * 1.5)
    pygame.draw.ellipse(surface, (79, 171, 61, 45), rect.inflate(12, 8))
    pygame.draw.ellipse(surface, (100, 214, 74), rect)
    pygame.draw.ellipse(surface, (49, 126, 60),
                        (rect.x + 2, rect.y + rect.height // 2,
                         max(2, rect.width - 3), max(3, rect.height // 2)))
    pygame.draw.circle(surface, (218, 255, 153),
                       (rect.x + rect.width // 3, rect.y + rect.height // 3),
                       pulsation)
    pygame.draw.circle(surface, (239, 255, 197),
                       (rect.x + rect.width // 3, rect.y + rect.height // 3), 1)


def dessiner_icone_palette(surface: pygame.Surface, rect: pygame.Rect,
def dessiner_icone_palette(surface: pygame.Surface, rect: pygame.Rect,
                           type_case: int) -> None:
    """Dessine des icones larges et contrastes pour les outils de l'editeur."""
    cx, cy = rect.center
    gauche, haut = cx - 18, cy - 15

    if type_case == 0:
        pygame.draw.polygon(surface, (83, 43, 54), [
            (cx - 15, cy + 8), (cx - 4, cy - 10),
            (cx + 15, cy + 1), (cx + 4, cy + 11),
        ])
        pygame.draw.polygon(surface, (239, 135, 158), [
            (cx - 12, cy + 6), (cx - 3, cy - 8),
            (cx + 12, cy + 1), (cx + 3, cy + 9),
        ])
        pygame.draw.polygon(surface, (255, 207, 218), [
            (cx - 12, cy + 6), (cx - 3, cy - 8),
            (cx + 1, cy - 5), (cx - 8, cy + 9),
        ])
        pygame.draw.line(surface, (255, 241, 244),
                         (cx - 7, cy - 2), (cx + 7, cy + 5), 2)
    elif type_case == SOL:
        pygame.draw.rect(surface, (65, 48, 39), (gauche, haut + 7, 36, 24),
                         border_radius=3)
        pygame.draw.rect(surface, (139, 94, 58), (gauche + 1, haut + 7, 34, 22),
                         border_radius=2)
        pygame.draw.rect(surface, (73, 147, 82), (gauche, haut + 2, 36, 9),
                         border_radius=3)
        pygame.draw.line(surface, (177, 222, 123), (gauche + 2, haut + 8),
                         (gauche + 34, haut + 8), 3)
        for offset in (-12, 0, 12):
            pygame.draw.line(surface, (189, 224, 140),
                             (cx + offset, haut + 4), (cx + offset - 2, haut), 2)
        pygame.draw.line(surface, (104, 69, 48), (gauche + 3, cy + 4),
                         (gauche + 13, cy + 4), 2)
        pygame.draw.ellipse(surface, (202, 164, 109), (cx + 5, cy + 5, 5, 3))
        pygame.draw.ellipse(surface, (106, 73, 53), (cx - 11, cy + 10, 4, 3))
    elif type_case == PLATEFORME:
        pygame.draw.rect(surface, (72, 47, 32), (gauche, cy - 3, 36, 13),
                         border_radius=3)
        pygame.draw.rect(surface, (153, 98, 52), (gauche + 1, cy - 5, 34, 9),
                         border_radius=3)
        pygame.draw.line(surface, (231, 181, 104), (gauche + 3, cy - 3),
                         (gauche + 33, cy - 3), 2)
        pygame.draw.line(surface, (93, 57, 35), (gauche + 4, cy + 1),
                         (gauche + 32, cy + 1), 2)
        pygame.draw.rect(surface, (112, 71, 39), (gauche + 4, cy + 8, 5, 6))
        pygame.draw.rect(surface, (112, 71, 39), (gauche + 27, cy + 8, 5, 6))
        pygame.draw.circle(surface, (255, 218, 147), (gauche + 4, cy - 1), 2)
        pygame.draw.circle(surface, (255, 218, 147), (gauche + 32, cy - 1), 2)
    elif type_case == PIC:
        for centre_x in (cx - 12, cx, cx + 12):
            pygame.draw.polygon(surface, (45, 52, 64), [
                (centre_x - 8, cy + 13), (centre_x, cy - 14),
                (centre_x + 8, cy + 13),
            ])
            pygame.draw.polygon(surface, (177, 195, 205), [
                (centre_x - 5, cy + 11), (centre_x, cy - 11),
                (centre_x - 1, cy + 10),
            ])
            pygame.draw.line(surface, (239, 246, 246),
                             (centre_x, cy - 11), (centre_x - 1, cy + 5), 2)
        pygame.draw.line(surface, (113, 126, 137),
                         (cx - 18, cy + 14), (cx + 18, cy + 14), 2)
    elif type_case == POINT_CONTROLE:
        pygame.draw.ellipse(surface, (28, 42, 44), (cx - 16, cy + 11, 32, 6))
        pygame.draw.line(surface, (35, 47, 56), (cx - 10, cy + 13),
                         (cx - 10, cy - 16), 5)
        pygame.draw.line(surface, (219, 230, 227), (cx - 11, cy + 11),
                         (cx - 11, cy - 15), 2)
        pygame.draw.polygon(surface, (55, 161, 98), [
            (cx - 8, cy - 15), (cx + 14, cy - 10), (cx + 8, cy - 1),
            (cx - 8, cy - 4),
        ])
        pygame.draw.circle(surface, (225, 255, 230), (cx + 1, cy - 8), 3)
    elif type_case == RESSORT:
        pygame.draw.rect(surface, (45, 48, 58), (cx - 16, cy + 9, 32, 7),
                         border_radius=2)
        pygame.draw.rect(surface, (185, 79, 57), (cx - 13, cy + 6, 26, 5),
                         border_radius=2)
        pygame.draw.lines(surface, (207, 62, 49), False, [
            (cx - 11, cy + 6), (cx - 7, cy - 10), (cx - 2, cy + 5),
            (cx + 3, cy - 10), (cx + 8, cy + 5), (cx + 11, cy - 7),
        ], 4)
        pygame.draw.lines(surface, (255, 190, 116), False, [
            (cx - 12, cy + 5), (cx - 8, cy - 8), (cx - 3, cy + 3),
            (cx + 2, cy - 8), (cx + 7, cy + 3),
        ], 1)
    elif type_case == GEMME:
        pygame.draw.polygon(surface, (30, 92, 119), [
            (cx - 11, cy - 8), (cx - 5, cy - 16), (cx + 7, cy - 16),
            (cx + 14, cy - 7), (cx + 10, cy + 8), (cx, cy + 16),
            (cx - 11, cy + 7), (cx - 14, cy - 5),
        ])
        pygame.draw.polygon(surface, (42, 202, 222), [
            (cx - 9, cy - 7), (cx - 4, cy - 13), (cx + 6, cy - 13),
            (cx + 11, cy - 6), (cx + 8, cy + 6), (cx, cy + 13),
            (cx - 9, cy + 5), (cx - 12, cy - 5),
        ])
        pygame.draw.polygon(surface, (149, 250, 245), [
            (cx - 4, cy - 13), (cx + 6, cy - 13), (cx + 1, cy - 1),
        ])
        pygame.draw.polygon(surface, (93, 228, 237), [
            (cx - 9, cy - 7), (cx - 4, cy - 13), (cx + 1, cy - 1),
            (cx - 12, cy - 5),
        ])
        pygame.draw.line(surface, (232, 255, 250), (cx - 4, cy - 11),
                         (cx - 1, cy - 5), 2)
    elif type_case == COEUR:
        dessiner_coeur(surface, (cx, cy + 1), 29)
        pygame.draw.line(surface, (255, 194, 207), (cx - 8, cy - 6),
                         (cx - 4, cy - 10), 2)
    elif type_case in OUTILS_MONSTRES:
        pygame.draw.ellipse(surface, (38, 31, 45), (cx - 19, cy + 12, 38, 5))
        dessiner_monstre(
            surface, pygame.Rect(cx - 20, cy - 18, 40, 36),
            OUTILS_MONSTRES.index(type_case),
        )
    elif type_case == OUTIL_DEPART:
        pygame.draw.ellipse(surface, (42, 76, 54), (cx - 17, cy + 11, 34, 6))
        pygame.draw.line(surface, (44, 69, 72), (cx - 10, cy + 13),
                         (cx - 10, cy - 17), 5)
        pygame.draw.line(surface, (224, 236, 230), (cx - 11, cy + 12),
                         (cx - 11, cy - 15), 2)
        pygame.draw.polygon(surface, (44, 180, 101), [
            (cx - 8, cy - 16), (cx + 16, cy - 10),
            (cx + 3, cy - 2), (cx - 8, cy - 5),
        ])
        pygame.draw.circle(surface, (240, 255, 242), (cx + 1, cy - 9), 3)
    elif type_case == OUTIL_ARRIVEE:
        pygame.draw.ellipse(surface, (64, 51, 34), (cx - 17, cy + 11, 34, 6))
        pygame.draw.line(surface, (48, 53, 60), (cx - 10, cy + 13),
                         (cx - 10, cy - 17), 5)
        pygame.draw.line(surface, (233, 237, 228), (cx - 11, cy + 12),
                         (cx - 11, cy - 15), 2)
        pygame.draw.polygon(surface, (241, 179, 57), [
            (cx - 8, cy - 16), (cx + 16, cy - 10), (cx - 8, cy - 3),
        ])
        pygame.draw.rect(surface, (255, 240, 199), (cx - 4, cy - 13, 4, 4))
        pygame.draw.rect(surface, (255, 240, 199), (cx + 5, cy - 11, 4, 4))
        pygame.draw.circle(surface, (255, 234, 169), (cx - 10, cy - 17), 3)




def ligne_support_monstre(niveau: dict[str, object], colonne: int,
                           ligne: int) -> int | None:
    """Trouve la plateforme directement sous un monstre ou dans sa case."""
    cases = niveau["tiles"]
    if cases[ligne][colonne] in (SOL, PLATEFORME):
        return ligne
    dessous = ligne + 1
    if dessous < LIGNES_NIVEAU and cases[dessous][colonne] in (SOL, PLATEFORME):
        return dessous
    return None


def niveau_depart() -> dict[str, object]:
    """Construit un parcours de demonstration avec plusieurs defis et monstres."""
    cases = [[0 for _ in range(COLONNES_NIVEAU)] for _ in range(LIGNES_NIVEAU)]
    trous = {8, 9, 17, 18, 26, 27, 34}
    for colonne in range(COLONNES_NIVEAU):
        if colonne not in trous:
            cases[LIGNES_NIVEAU - 1][colonne] = SOL

    for colonne, ligne in (
        (3, 8), (4, 8), (5, 8), (8, 8), (11, 8), (12, 8),
        (14, 7), (15, 7), (17, 8), (20, 8), (21, 8), (22, 8),
        (24, 7), (25, 7), (27, 8), (29, 8), (30, 8), (31, 8),
        (32, 7), (33, 7), (34, 8), (36, 8), (37, 8),
    ):
        cases[ligne][colonne] = PLATEFORME

    for colonne in (5, 12, 15, 21, 25, 32):
        cases[9][colonne] = PIC

    for colonne, ligne in (
        (4, 7), (12, 7), (15, 6), (21, 7),
        (25, 6), (30, 7), (33, 6), (37, 7),
    ):
        cases[ligne][colonne] = GEMME
    for colonne in (2, 10, 20, 28, 35):
        cases[9][colonne] = GEMME
    for colonne in (3, 36):
        cases[9][colonne] = COEUR
    for colonne in (13, 29):
        cases[9][colonne] = POINT_CONTROLE
    cases[9][19] = RESSORT

    monstres = [[6, 9], [14, 9], [23, 9], [31, 9]]
    return {
        "tiles": cases,
        "start": [1, 9],
        "goal": [38, 9],
        "monstres": monstres,
        "theme": "prairie",
    }


def niveau_carte_base(numero: int) -> dict[str, object]:
    """Construit un niveau de campagne dont les obstacles augmentent avec le numero."""
    numero = max(1, min(NIVEAUX_CARTE_BASE, numero))
    cases = [[0 for _ in range(COLONNES_NIVEAU)] for _ in range(LIGNES_NIVEAU)]
    trous: set[int] = set()
    nombre_trous = 1 + (numero - 1) // 2
    for index in range(nombre_trous):
        depart = round(8 + index * 24 / max(1, nombre_trous - 1))
        largeur = 1 + int(numero >= 7 and index % 2 == 0)
        for colonne in range(depart, min(COLONNES_NIVEAU - 2, depart + largeur)):
            trous.add(colonne)
    for colonne in range(COLONNES_NIVEAU):
        if colonne not in trous:
            cases[LIGNES_NIVEAU - 1][colonne] = SOL

    nombre_pics = min(14, numero + 2)
    candidats = [colonne for colonne in range(4, 36) if colonne not in trous]
    pics: set[int] = set()
    for index in range(nombre_pics):
        cible = round(4 + index * 31 / max(1, nombre_pics - 1))
        disponibles = [colonne for colonne in candidats if colonne not in pics
                       and all(abs(colonne - autre) >= 2 for autre in pics)]
        if not disponibles:
            disponibles = [colonne for colonne in candidats if colonne not in pics]
        if not disponibles:
            break
        colonne = min(disponibles, key=lambda valeur: (abs(valeur - cible), valeur))
        pics.add(colonne)
        cases[LIGNES_NIVEAU - 2][colonne] = PIC

    nombre_monstres = 1 + numero // 2
    monstres: list[list[int]] = []
    cases_monstres = [colonne for colonne in range(5, 35)
                      if colonne not in trous and colonne not in pics]
    for index in range(nombre_monstres):
        cible = round(5 + index * 29 / max(1, nombre_monstres - 1))
        disponibles = [colonne for colonne in cases_monstres
                       if all(abs(colonne - autre[0]) >= 3 for autre in monstres)]
        if not disponibles:
            disponibles = [colonne for colonne in cases_monstres
                           if all(colonne != autre[0] for autre in monstres)]
        if not disponibles:
            break
        colonne = min(disponibles, key=lambda valeur: (abs(valeur - cible), valeur))
        monstres.append([colonne, LIGNES_NIVEAU - 2])
        cases_monstres.remove(colonne)

    # Les plateformes offrent des passages en hauteur quand le sol devient charge.
    nombre_plateformes = numero // 2
    for index in range(nombre_plateformes):
        cible = round(6 + index * 28 / max(1, nombre_plateformes - 1))
        disponibles = [colonne for colonne in range(4, 36)
                       if cases[8][colonne] == 0 and colonne not in trous]
        if disponibles:
            colonne = min(disponibles, key=lambda valeur: (abs(valeur - cible), valeur))
            cases[8][colonne] = PLATEFORME

    cases[9][2] = GEMME
    cases[9][37] = GEMME
    if numero >= 4:
        positions_sures = [colonne for colonne in range(8, 33)
                           if colonne not in trous and colonne not in pics
                           and [colonne, 9] not in monstres]
        nombre_controles = min(2, numero // 6)
        for index in range(nombre_controles):
            if not positions_sures:
                break
            cible = 13 if index == 0 else 27
            colonne = min(positions_sures, key=lambda valeur: (abs(valeur - cible), valeur))
            cases[9][colonne] = POINT_CONTROLE
            positions_sures.remove(colonne)
    if numero >= 5:
        cases[9][3] = COEUR
        cases[9][36] = COEUR

    return {
        "tiles": cases,
        "start": [1, 9],
        "goal": [38, 9],
        "monstres": monstres,
        "theme": "prairie",
    }


def encoder_niveau(niveau: dict[str, object]) -> str:
    """Encode la carte, son biome et ses monstres dans un code partageable."""
    valider_niveau(niveau)
    contenu = bytes(case for rangee in niveau["tiles"] for case in rangee)
    contenu += bytes((*niveau["start"], *niveau["goal"]))
    monstres = niveau.get("monstres", [])
    contenu += len(monstres).to_bytes(2, "big")
    contenu += bytes(coord for monstre in monstres for coord in monstre)
    contenu += bytes((THEMES_PARCOURS.index(niveau.get("theme", "prairie")),))
    code = base64.urlsafe_b64encode(zlib.compress(contenu, level=9)).decode("ascii")
    return "P4-" + code.rstrip("=")


def decoder_niveau(code: str) -> dict[str, object]:
    """Decode les anciens parcours et les nouveaux codes avec biome."""
    code_nettoye = code.strip()
    prefixe = code_nettoye[:3].upper()
    if prefixe not in ("P1-", "P2-", "P3-", "P4-") or len(code_nettoye) > 2000:
        raise ValueError("Ce code de parcours n'est pas reconnu.")
    contenu_code = code_nettoye[3:]
    if not contenu_code or any(caractere not in string.ascii_letters + string.digits + "-_"
                               for caractere in contenu_code):
        raise ValueError("Le code du parcours contient des caracteres invalides.")
    try:
        remplissage = "=" * (-len(contenu_code) % 4)
        compresse = base64.urlsafe_b64decode(contenu_code + remplissage)
        decompression = zlib.decompressobj()
        contenu = decompression.decompress(compresse, 5000)
        if decompression.unconsumed_tail or not decompression.eof:
            raise ValueError("Le code du parcours est trop volumineux ou incomplet.")
        if prefixe in ("P2-", "P3-", "P4-"):
            nombre_tuiles = LIGNES_NIVEAU * COLONNES_NIVEAU
            taille_base = nombre_tuiles + 4
            if prefixe == "P2-":
                if len(contenu) != taille_base:
                    raise ValueError("Le code du parcours est incomplet ou abime.")
                monstres = []
                theme = "prairie"
            else:
                taille_theme = 1 if prefixe == "P4-" else 0
                if len(contenu) < taille_base + 2 + taille_theme:
                    raise ValueError("Le code du parcours est incomplet ou abime.")
                nombre_monstres = int.from_bytes(contenu[taille_base:taille_base + 2], "big")
                fin_monstres = len(contenu) - taille_theme
                if fin_monstres != taille_base + 2 + nombre_monstres * 2:
                    raise ValueError("Le code du parcours est incomplet ou abime.")
                debut_monstres = taille_base + 2
                monstres = [list(contenu[i:i + 2])
                            for i in range(debut_monstres, fin_monstres, 2)]
                if prefixe == "P4-":
                    index_theme = contenu[-1]
                    if index_theme >= len(THEMES_PARCOURS):
                        raise ValueError("Le biome du parcours n'est pas reconnu.")
                    theme = THEMES_PARCOURS[index_theme]
                else:
                    theme = "prairie"
            tuiles = list(contenu[:nombre_tuiles])
            cases = [tuiles[i:i + COLONNES_NIVEAU]
                     for i in range(0, nombre_tuiles, COLONNES_NIVEAU)]
            niveau = {"tiles": cases, "start": list(contenu[nombre_tuiles:nombre_tuiles + 2]),
                      "goal": list(contenu[nombre_tuiles + 2:nombre_tuiles + 4]),
                      "monstres": monstres, "theme": theme}
        else:
            niveau = json.loads(contenu.decode("utf-8"))
    except (ValueError, zlib.error, json.JSONDecodeError, UnicodeDecodeError) as erreur:
        raise ValueError("Le code du parcours est incomplet ou abime.") from erreur
    if not isinstance(niveau, dict):
        raise ValueError("Le code ne contient pas une carte valide.")
    niveau.setdefault("monstres", [])
    niveau.setdefault("theme", "prairie")
    valider_niveau(niveau)
    return niveau

def valider_niveau(niveau: dict[str, object]) -> None:
    """Verifie la carte, ses points et le biome choisi."""
    theme = niveau.setdefault("theme", "prairie")
    if not isinstance(theme, str) or theme not in THEMES_PARCOURS:
        raise ValueError("Le theme du parcours n'est pas reconnu.")
    cases = niveau.get("tiles")
    if not isinstance(cases, list) or len(cases) != LIGNES_NIVEAU:
        raise ValueError("La carte doit avoir 11 rangees.")
    for ligne in cases:
        if not isinstance(ligne, list) or len(ligne) != COLONNES_NIVEAU:
            raise ValueError("La carte doit avoir 40 cases par rangee.")
        if any(type(case) is not int or case not in
               (0, SOL, PLATEFORME, PIC, POINT_CONTROLE, RESSORT, GEMME, COEUR) for case in ligne):
            raise ValueError("La carte contient un bloc invalide.")
    for nom in ("start", "goal"):
        point = niveau.get(nom)
        if (not isinstance(point, list) or len(point) != 2
                or any(type(coord) is not int for coord in point)
                or not (0 <= point[0] < COLONNES_NIVEAU)
                or not (0 <= point[1] < LIGNES_NIVEAU)):
            raise ValueError(f"Le point {nom} est absent ou hors de la carte.")
    depart = niveau["start"]
    if (depart[1] >= LIGNES_NIVEAU - 1
            or cases[depart[1]][depart[0]] != 0
            or cases[depart[1] + 1][depart[0]] not in (SOL, PLATEFORME)):
        raise ValueError("Le depart doit etre libre et pose sur une case sure.")
    if depart == niveau["goal"]:
        raise ValueError("Le depart et l'arrivee doivent etre differents.")
    arrivee = niveau["goal"]
    if cases[arrivee[1]][arrivee[0]] in (SOL, PLATEFORME, PIC, RESSORT, GEMME, COEUR):
        raise ValueError("L'arrivee doit etre placee sur une case libre.")
    monstres = niveau.get("monstres", [])
    if not isinstance(monstres, list) or len(monstres) > COLONNES_NIVEAU * LIGNES_NIVEAU:
        raise ValueError("La liste des monstres est invalide.")
    positions_monstres: set[tuple[int, int]] = set()
    for monstre in monstres:
        if (not isinstance(monstre, list) or len(monstre) != 2
                or any(type(coord) is not int for coord in monstre)
                or not (0 <= monstre[0] < COLONNES_NIVEAU)
                or not (0 <= monstre[1] < LIGNES_NIVEAU)):
            raise ValueError("Un monstre est place hors de la carte.")
        position = tuple(monstre)
        if position in positions_monstres or position in (tuple(depart), tuple(arrivee)):
            raise ValueError("Chaque monstre doit avoir une place libre et unique.")
        positions_monstres.add(position)


def normaliser_code(code: str) -> str:
    """Nettoie et valide un code de defi compose de six lettres/chiffres."""
    code_nettoye = "".join(caractere for caractere in code.upper() if caractere in CODE_ALPHABET)
    if len(code_nettoye) not in (4, 6):
        raise ValueError("Le code arcade doit contenir 4 caracteres (les anciens codes a 6 restent valides).")
    return code_nettoye


def code_vers_graine(code: str) -> int:
    """Convertit le code en graine stable pour reproduire le meme defi."""
    graine = 0
    for caractere in normaliser_code(code):
        graine = graine * len(CODE_ALPHABET) + CODE_ALPHABET.index(caractere)
    return graine


def nouveau_code() -> str:
    """Genere un code aleatoire facile a dicter ou a copier."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))


def code_defi_du_jour() -> str:
    """Construit le meme code arcade pour tous les joueurs ce jour-ci."""
    graine_jour = hashlib.sha256(date.today().isoformat().encode("ascii")).digest()
    return "".join(CODE_ALPHABET[valeur % len(CODE_ALPHABET)] for valeur in graine_jour[:4])


def chemin_scores() -> Path:
    """Retourne le chemin de sauvegarde local, hors du dossier du projet."""
    return Path.home() / "AppData" / "Local" / "DefiTonPote" / "scores.json"


def chemin_brouillon() -> Path:
    """Retourne l'emplacement local du dernier parcours edite."""
    return chemin_scores().with_name("brouillon.json")


def lire_record(code: str, fichier: Path) -> int:
    """Lit le meilleur score local de ce defi; un fichier absent vaut zero."""
    if not fichier.exists():
        return 0
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        raise OSError(f"Impossible de lire les records ({erreur}).") from erreur
    if not isinstance(donnees, dict):
        raise OSError("Le fichier des records n'a pas un format reconnu.")
    record = donnees.get(normaliser_code(code), 0)
    return record if isinstance(record, int) and not isinstance(record, bool) else 0


def enregistrer_record(code: str, score: int, fichier: Path) -> int:
    """Sauvegarde le meilleur score pour ce code et le renvoie."""
    records: dict[str, int] = {}
    if fichier.exists():
        try:
            donnees = json.loads(fichier.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as erreur:
            raise OSError(f"Impossible de lire les records ({erreur}).") from erreur
        if not isinstance(donnees, dict):
            raise OSError("Le fichier des records n'a pas un format reconnu.")
        records = {
            cle: valeur
            for cle, valeur in donnees.items()
            if isinstance(cle, str) and isinstance(valeur, int) and not isinstance(valeur, bool)
        }

    cle = normaliser_code(code)
    record = max(records.get(cle, 0), score)
    records[cle] = record
    try:
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps(records, indent=2), encoding="utf-8")
    except OSError as erreur:
        raise OSError(f"Impossible d'enregistrer le record ({erreur}).") from erreur
    return record


def cle_record_parcours(code: str) -> str:
    """Retourne une cle courte et stable pour une carte partagee."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def lire_record_parcours(code: str, fichier: Path) -> int:
    """Lit le meilleur temps en millisecondes enregistre pour ce parcours."""
    fichier_parcours = fichier.with_name("records-parcours.json")
    if not fichier_parcours.exists():
        return 0
    try:
        records = json.loads(fichier_parcours.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        raise OSError(f"Impossible de lire les records de parcours ({erreur}).") from erreur
    if not isinstance(records, dict):
        raise OSError("Le fichier des records de parcours n'a pas un format reconnu.")
    temps = records.get(cle_record_parcours(code), 0)
    return temps if isinstance(temps, int) and not isinstance(temps, bool) else 0


def enregistrer_record_parcours(code: str, temps_ms: int, fichier: Path) -> int:
    """Conserve le meilleur temps connu pour une carte partagee."""
    fichier_parcours = fichier.with_name("records-parcours.json")
    records: dict[str, int] = {}
    if fichier_parcours.exists():
        try:
            donnees = json.loads(fichier_parcours.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as erreur:
            raise OSError(f"Impossible de lire les records de parcours ({erreur}).") from erreur
        if not isinstance(donnees, dict):
            raise OSError("Le fichier des records de parcours n'a pas un format reconnu.")
        records = {
            cle: valeur
            for cle, valeur in donnees.items()
            if isinstance(cle, str) and isinstance(valeur, int) and not isinstance(valeur, bool)
        }
    cle = cle_record_parcours(code)
    record = min(records.get(cle, temps_ms), temps_ms)
    records[cle] = record
    try:
        fichier_parcours.parent.mkdir(parents=True, exist_ok=True)
        fichier_parcours.write_text(json.dumps(records, indent=2), encoding="utf-8")
    except OSError as erreur:
        raise OSError(f"Impossible d'enregistrer le record de parcours ({erreur}).") from erreur
    return record


def texte(surface: pygame.Surface, police: pygame.font.Font, contenu: str,
          position: tuple[int, int], couleur: tuple[int, int, int] = BLANC,
          centre: bool = False) -> pygame.Rect:
    image = police.render(contenu, True, couleur)
    rect = image.get_rect()
    if centre:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)
    return rect


def dessiner_bouton(surface: pygame.Surface, rect: pygame.Rect, etiquette: str,
                    police: pygame.font.Font, survole: bool = False,
                    accent: tuple[int, int, int] = CYAN) -> None:
    couleur = tuple(min(255, canal + (15 if survole else 0)) for canal in PANNEAU)
    pygame.draw.rect(surface, (7, 11, 22), rect.move(0, 4), border_radius=15)
    pygame.draw.rect(surface, couleur, rect, border_radius=15)
    pygame.draw.rect(surface, accent, rect, width=2, border_radius=15)
    pygame.draw.rect(surface, accent, (rect.x + 2, rect.y + 10, 4, rect.height - 20),
                     border_radius=2)
    pygame.draw.line(surface, tuple(min(255, canal + 70) for canal in accent),
                     (rect.x + 14, rect.y + 2), (rect.right - 14, rect.y + 2), 1)
    if survole:
        pygame.draw.rect(surface, accent, rect.inflate(5, 5), width=1, border_radius=18)
    texte(surface, police, etiquette, rect.center, BLANC, centre=True)


def dessiner_personnage_arcade(
    surface: pygame.Surface,
    centre: tuple[int, int],
    temps: float,
    direction: pygame.Vector2,
    esquive: bool,
) -> None:
    """Dessine Nova, une exploratrice animee vue du dessus."""
    x, y = centre
    direction = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
    cote = pygame.Vector2(-direction.y, direction.x)
    pas = math.sin(temps * 15) * 3.5

    pygame.draw.ellipse(surface, (4, 8, 19), (x - 15, y + 12, 30, 9))
    if esquive:
        pygame.draw.circle(surface, (58, 226, 236), centre, 27, 2)
        pygame.draw.circle(surface, (135, 255, 244), centre, 22, 1)

    echarpe = pygame.Vector2(x, y - 5) - direction * 12
    pointe = echarpe - direction * (13 + math.sin(temps * 12) * 3)
    pygame.draw.polygon(surface, (255, 111, 104), [
        (round(echarpe.x + cote.x * 5), round(echarpe.y + cote.y * 5)),
        (round(echarpe.x - cote.x * 5), round(echarpe.y - cote.y * 5)),
        (round(pointe.x), round(pointe.y)),
    ])

    for cote_pied in (-1, 1):
        pied_x = round(x + cote_pied * 6 + pas * (1 if cote_pied > 0 else -1))
        pygame.draw.ellipse(surface, (26, 43, 66), (pied_x - 5, y + 8, 10, 8))
        pygame.draw.ellipse(surface, (247, 185, 112), (pied_x - 4, y + 9, 8, 5))

    pygame.draw.ellipse(surface, (20, 64, 88), (x - 14, y - 13, 28, 30))
    pygame.draw.ellipse(surface, (53, 184, 190), (x - 11, y - 12, 22, 27))
    pygame.draw.ellipse(surface, (26, 94, 124), (x - 13 - round(direction.x * 4),
                                                  y - 5 - round(direction.y * 4), 8, 13))
    pygame.draw.circle(surface, (247, 199, 143), (x, y - 12), 9)
    pygame.draw.arc(surface, (77, 49, 55), (x - 9, y - 21, 18, 18), math.pi, math.tau, 4)
    visiere = (x + round(direction.x * 3), y - 13 + round(direction.y * 3))
    pygame.draw.ellipse(surface, (27, 54, 78), (visiere[0] - 6, visiere[1] - 4, 12, 8))
    pygame.draw.ellipse(surface, (137, 244, 238), (visiere[0] - 4, visiere[1] - 3, 8, 5))
    pygame.draw.circle(surface, BLANC, (visiere[0] - 1, visiere[1] - 2), 1)
    pygame.draw.circle(surface, (255, 221, 133), (x - 9, y + 1), 2)


def dessiner_personnage_plateforme(
    surface: pygame.Surface,
    rect: pygame.Rect,
    temps: float,
    vitesse_x: float,
) -> None:
    """Dessine Nova en profil avec foullee et echarpe animees."""
    x, y = rect.x, rect.y
    largeur, hauteur = rect.size
    centre_x = rect.centerx
    face = 1 if vitesse_x >= 0 else -1
    en_marche = abs(vitesse_x) > 35
    pas = math.sin(temps * 16) * (4 if en_marche else 1)
    respiration = math.sin(temps * 4) * 1.2

    pygame.draw.ellipse(surface, (5, 9, 18), (x - 5, y + hauteur - 2, largeur + 10, 8))
    cou = (centre_x - face * 10, y + 14)
    bout = (centre_x - face * (24 + round(math.sin(temps * 12) * 3)), y + 10)
    pygame.draw.polygon(surface, (255, 111, 104), [
        (cou[0], cou[1] - 4), (cou[0], cou[1] + 2), bout,
    ])

    for cote_pied in (-1, 1):
        jambe_x = centre_x + cote_pied * 5
        mouvement = round(pas * (1 if cote_pied > 0 else -1)) if en_marche else 0
        pygame.draw.line(surface, (35, 93, 125), (jambe_x, y + 27),
                         (jambe_x + mouvement, y + 34), 5)
        pygame.draw.ellipse(surface, (27, 43, 65),
                            (jambe_x + mouvement - 5, y + 31, 11, 7))
        pygame.draw.line(surface, (38, 91, 115), (centre_x - face * 7, y + 19),
                         (centre_x - face * 11, y + 27 - mouvement), 4)
        pygame.draw.circle(surface, (247, 199, 143),
                           (centre_x - face * 11, y + 27 - mouvement), 3)

    corps = pygame.Rect(x + 5, y + 14 + round(respiration), largeur - 10, 17)
    pygame.draw.rect(surface, (20, 64, 88), corps.inflate(3, 2), border_radius=7)
    pygame.draw.rect(surface, (53, 184, 190), corps, border_radius=6)
    pygame.draw.line(surface, (255, 221, 133), (centre_x - 3, corps.y + 4),
                     (centre_x + 3, corps.y + 4), 2)

    tete = pygame.Rect(centre_x - 8, y + 2 + round(respiration), 16, 16)
    pygame.draw.ellipse(surface, (247, 199, 143), tete)
    pygame.draw.polygon(surface, (91, 58, 58), [
        (tete.left - 1, tete.y + 7), (tete.left + 1, tete.y + 1),
        (centre_x + face * 7, tete.y), (tete.right + 1, tete.y + 7),
        (centre_x + face * 2, tete.y + 4),
    ])
    oeil = (centre_x + face * 4, tete.centery + 1)
    pygame.draw.circle(surface, (32, 49, 68), oeil, 2)
    pygame.draw.circle(surface, (250, 255, 247), (oeil[0] + face, oeil[1] - 1), 1)
    pygame.draw.line(surface, (255, 111, 104), (centre_x - 3, y + 16),
                     (centre_x + face * 7, y + 14), 3)


class JeuDefi:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Defi ton pote")
        self.ecran = creer_fenetre_jeu()
        self.appareil_tactile = appareil_tactile()
        self.touches_tactiles: dict[tuple[int, int], str] = {}
        self.clavier_tactile_actif = False
        self.bouton_pause_tactile = pygame.Rect(930, 18, 50, 50)
        self.horloge = pygame.time.Clock()
        self.police = pygame.font.Font(None, 28)
        self.police_petite = pygame.font.Font(None, 22)
        self.police_titre = pygame.font.Font(None, 82)
        self.police_moyenne = pygame.font.Font(None, 42)
        self.sauvegarde = chemin_scores()
        self.atmosphere = GameAtmosphere()
        self.fichier_brouillon = chemin_brouillon()
        self.dossier_parcours = self.fichier_brouillon.parent / "parcours"
        self.id_parcours = "principal"
        self.nom_parcours = "Mon parcours"
        self.saisie_nom_active = False
        self.champ_nom = pygame.Rect(260, 644, 480, 34)
        self.bouton_theme = pygame.Rect(20, 644, 220, 34)
        self.parcours_disponibles: list[Path] = []
        self.lignes_bibliotheque = [pygame.Rect(170, 190 + i * 57, 660, 48) for i in range(7)]
        self.bouton_nouveau = pygame.Rect(230, 610, 220, 54)
        self.bouton_retour_bibliotheque = pygame.Rect(550, 610, 220, 54)
        self.etat = "menu"
        self.code = nouveau_code()
        self.niveau = niveau_depart()
        self.saisie_code = ""
        self.erreur = ""
        self.message_sauvegarde = ""
        self.paused = False
        self.type_partie = "arcade"
        self.campagne_base = False
        self.numero_niveau_base = 0
        self.nouveau_record = False
        self.retour_resultat = "menu"
        self.case_selectionnee = SOL
        self.camera_editeur = 0
        self.partage_code = ""
        self.message_partage = ""
        self.boutons_menu = [pygame.Rect(80 + index * 280, 270, 240, 74)
                             for index in range(3)]
        self.boutons_creation = [pygame.Rect(210, 280, 260, 92),
                                 pygame.Rect(530, 280, 260, 92)]
        self.bouton_retour_creation = pygame.Rect(370, 440, 260, 58)
        self.boutons_parcours = [pygame.Rect(160, 280, 300, 92),
                                 pygame.Rect(500, 280, 300, 92)]
        self.bouton_retour_parcours = pygame.Rect(370, 440, 260, 58)
        self.categorie_palette = "blocs"
        self.categories_editeur = [
            ("blocs", "BLOCS", pygame.Rect(12, 13, 100, 42)),
            ("monstres", "MONSTRES", pygame.Rect(122, 13, 110, 42)),
            ("checkpoint", "CHECKPOINT", pygame.Rect(242, 13, 130, 42)),
        ]
        self.palette_editeur = [
            (pygame.Rect(12 + index * 49, 62, 46, 42), type_case)
            for index, type_case in enumerate(
                OUTILS_PAR_CATEGORIE[self.categorie_palette]
            )
        ]
        self.actions_editeur = [
            pygame.Rect(552, 16, 94, 36),
            pygame.Rect(651, 16, 94, 36),
            pygame.Rect(750, 16, 94, 36),
            pygame.Rect(849, 16, 94, 36),
        ]
        self.bouton_copier = pygame.Rect(350, 516, 300, 54)
        self.bouton_partage_test = pygame.Rect(250, 590, 220, 52)
        self.bouton_partage_editer = pygame.Rect(490, 590, 260, 52)
        self.historique_niveau: list[dict[str, object]] = []
        self.refaire_niveau: list[dict[str, object]] = []
        self.etoiles = [
            (random.randrange(LARGEUR), random.randrange(HAUTEUR), random.choice((1, 1, 2)))
            for _ in range(150)
        ]
        self.fond_degrade = pygame.Surface((LARGEUR, HAUTEUR))
        for y in range(HAUTEUR):
            progression = y / HAUTEUR
            couleur = (int(9 + 12 * progression), int(13 + 9 * progression),
                       int(31 + 27 * progression))
            pygame.draw.line(self.fond_degrade, couleur, (0, y), (LARGEUR, y))
        self.voile_couleur_parcours = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        for centre, largeur, hauteur, couleur in (
                ((170, 260), 640, 390, (38, 166, 239)),
                ((820, 270), 610, 370, (176, 87, 230)),
                ((500, 505), 850, 230, (255, 139, 79))):
            for couche in range(22, 0, -1):
                progression = couche / 22
                zone = pygame.Rect(
                    centre[0] - round(largeur * progression / 2),
                    centre[1] - round(hauteur * progression / 2),
                    round(largeur * progression),
                    round(hauteur * progression),
                )
                alpha = round(1 + 44 * (1 - progression) ** 2)
                pygame.draw.ellipse(self.voile_couleur_parcours,
                                    (*couleur, alpha), zone)
        bandes_arc_en_ciel = (
            (255, 76, 103, 76), (255, 145, 69, 78), (255, 217, 81, 80),
            (105, 220, 112, 78), (67, 213, 220, 76), (86, 132, 248, 74),
            (180, 112, 244, 72),
        )
        for index, couleur_arc in enumerate(bandes_arc_en_ciel):
            rayon_x = 440 - index * 9
            rayon_y = 370 - index * 7
            points_arc = []
            for etape in range(61):
                x_arc = round(LARGEUR // 2 - rayon_x + 2 * rayon_x * etape / 60)
                progression = (x_arc - LARGEUR / 2) / rayon_x
                y_arc = round(470 - rayon_y * math.sqrt(max(0, 1 - progression ** 2)))
                points_arc.append((x_arc, y_arc))
            pygame.draw.lines(self.voile_couleur_parcours, couleur_arc,
                              False, points_arc, 8)
        self.voile_parcours = pygame.Surface((LARGEUR - 48, HAUTEUR - 124), pygame.SRCALPHA)
        pygame.draw.rect(self.voile_parcours, (24, 43, 59, 78),
                         self.voile_parcours.get_rect(), border_radius=18)
        self.voile_nebuleuse = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        pygame.draw.circle(self.voile_nebuleuse, (93, 47, 160, 24), (790, 140), 230)
        pygame.draw.circle(self.voile_nebuleuse, (24, 143, 170, 22), (170, 510), 270)
        pygame.draw.circle(self.voile_nebuleuse, (105, 63, 173, 18), (480, 330), 310)
        for centre, largeur, hauteur, couleur in (
                ((690, 300), 300, 190, (98, 64, 188)),
                ((280, 330), 270, 210, (27, 117, 151)),
                ((850, 535), 220, 150, (81, 53, 151))):
            for couche in range(20, 0, -1):
                progression = couche / 20
                alpha = round(1 + 9 * (1 - progression) ** 2)
                zone = pygame.Rect(
                    centre[0] - round(largeur * progression / 2),
                    centre[1] - round(hauteur * progression / 2),
                    round(largeur * progression),
                    round(hauteur * progression),
                )
                pygame.draw.ellipse(self.voile_nebuleuse, (*couleur, alpha), zone)
        self.voile_arene = pygame.Surface(
            (LARGEUR - 48, HAUTEUR - 122), pygame.SRCALPHA
        )
        self.voile_arene.fill((5, 9, 24, 82))
        self.bouton_aleatoire = pygame.Rect(350, 390, 300, 58)
        self.champ_code = pygame.Rect(350, 470, 300, 54)
        self.bouton_saisie = pygame.Rect(350, 540, 145, 58)
        self.bouton_code = pygame.Rect(505, 540, 145, 58)
        self.saisie_active = False
        self.bouton_rejouer = pygame.Rect(300, 440, 190, 58)
        self.bouton_menu = pygame.Rect(510, 440, 190, 58)
        self.bouton_copier_code = pygame.Rect(350, 419, 300, 46)

    def actualiser_palette_editeur(self) -> None:
        self.palette_editeur = [
            (pygame.Rect(12 + index * 49, 62, 46, 42), type_case)
            for index, type_case in enumerate(
                OUTILS_PAR_CATEGORIE[self.categorie_palette]
            )
        ]

    def selectionner_categorie_editeur(self, categorie: str) -> None:
        self.categorie_palette = categorie
        outils = OUTILS_PAR_CATEGORIE[categorie]
        if self.case_selectionnee not in outils:
            self.case_selectionnee = SOL if categorie == "blocs" else outils[0]
        self.actualiser_palette_editeur()

    def selectionner_outil_editeur(self, type_case: int) -> None:
        self.case_selectionnee = type_case
        self.categorie_palette = next(
            categorie for categorie, outils in OUTILS_PAR_CATEGORIE.items()
            if type_case in outils
        )
        self.actualiser_palette_editeur()

    def copier_texte(self, contenu: str) -> bool:
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, contenu.encode("utf-8"))
        except pygame.error:
            return False
        return True

    def copier_code_arcade(self) -> None:
        self.message_partage = (
            "Code copie ! Envoie-le a tes amis."
            if self.copier_texte(self.code)
            else "Copie impossible : note le code affiche."
        )

    def lire_presse_papier(self) -> str:
        try:
            pygame.scrap.init()
            contenu = pygame.scrap.get(pygame.SCRAP_TEXT)
        except pygame.error:
            return ""
        if not contenu:
            return ""
        return contenu.decode("utf-8", errors="ignore").strip("\x00\r\n \t")

    def lancer_niveau_carte_base(self, numero: int = 1) -> None:
        numero = max(1, min(NIVEAUX_CARTE_BASE, numero))
        niveau = niveau_carte_base(numero)
        self.lancer_parcours(niveau, encoder_niveau(niveau), "parcours_menu",
                             campagne_base=True, numero_niveau_base=numero)

    def lancer_parcours(self, niveau: dict[str, object], code: str,
                        retour: str = "menu", campagne_base: bool = False,
                        numero_niveau_base: int = 1) -> None:
        valider_niveau(niveau)
        # La partie travaille sur une copie pour garder la carte source intacte.
        self.niveau = copy.deepcopy(niveau)
        self.code = code
        self.type_partie = "parcours"
        self.campagne_base = campagne_base
        self.numero_niveau_base = numero_niveau_base if campagne_base else 0
        graine_atmosphere = int(hashlib.sha256(code.encode("utf-8")).hexdigest()[:8], 16)
        self.atmosphere.reset(graine_atmosphere)
        self.retour_resultat = retour
        self.joueur = pygame.Vector2(0, 0)
        depart = niveau["start"]
        self.joueur.x = DEBUT_CARTE.x + depart[0] * TAILLE_CASE + 10
        self.joueur.y = depart[1] * TAILLE_CASE + 5
        self.rect_joueur = pygame.Rect(
            int(self.joueur.x), int(DEBUT_CARTE.y + self.joueur.y), 28, 38
        )
        self.vitesse_x = 0.0
        self.vitesse_y = 0.0
        self.sol = False
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.aleatoire = random.Random(
            int(hashlib.sha256(code.encode("utf-8")).hexdigest()[:16], 16)
        )
        self.particules: list[dict[str, object]] = []
        self.invulnerable = 0.8
        self.temps_parcours = 0.0
        self.vies = 3
        self.message_sauvegarde = ""
        self.nouveau_record = False
        try:
            self.record = lire_record_parcours(code, self.sauvegarde)
        except OSError as erreur:
            self.record = 0
            self.message_sauvegarde = str(erreur)
        self.score_parcours = 0
        self.gemmes_parcours = 0
        self.gemmes = {
            (colonne, ligne)
            for ligne, rangee in enumerate(self.niveau["tiles"])
            for colonne, type_case in enumerate(rangee)
            if type_case == GEMME
        }
        self.gemmes_collectees: set[tuple[int, int]] = set()
        self.coeurs_restants = {
            (colonne, ligne)
            for ligne, rangee in enumerate(self.niveau["tiles"])
            for colonne, type_case in enumerate(rangee)
            if type_case == COEUR
        }
        self.initialiser_monstres()
        self.total_gemmes = len(self.gemmes)
        depart = tuple(niveau["start"])
        self.depart_controle = depart
        self.dernier_controle = depart
        self.controles_actives: set[tuple[int, int]] = set()
        self.ressort_verrouille = False
        self.camera_parcours = 0.0
        self.paused = False
        self.etat = "parcours"

    def initialiser_monstres(self) -> None:
        """Place les monstres sur leur plateforme et definit leur trajet de patrouille."""
        cases = self.niveau["tiles"]
        plateformes = (SOL, PLATEFORME)
        self.monstres: list[dict[str, float]] = []
        for colonne, ligne in self.niveau.get("monstres", []):
            gauche = droite = colonne
            ligne_sol = ligne_support_monstre(self.niveau, colonne, ligne)
            en_patrouille = ligne_sol is not None and ligne_sol > 0
            ligne_trajet = ligne_sol - 1 if en_patrouille else ligne
            if en_patrouille:
                while (gauche > 0 and cases[ligne_sol][gauche - 1] in plateformes
                       and cases[ligne_trajet][gauche - 1] not in (SOL, PLATEFORME, PIC)):
                    gauche -= 1
                while (droite + 1 < COLONNES_NIVEAU
                       and cases[ligne_sol][droite + 1] in plateformes
                       and cases[ligne_trajet][droite + 1] not in (SOL, PLATEFORME, PIC)):
                    droite += 1
                minimum = int(DEBUT_CARTE.x) + gauche * TAILLE_CASE + 4
                maximum = int(DEBUT_CARTE.x) + (droite + 1) * TAILLE_CASE - 38
                y_monstre = int(DEBUT_CARTE.y) + ligne_sol * TAILLE_CASE - 34
            else:
                minimum = maximum = int(DEBUT_CARTE.x) + colonne * TAILLE_CASE + 7
                y_monstre = int(DEBUT_CARTE.y) + ligne * TAILLE_CASE + 8
            x_depart = int(DEBUT_CARTE.x) + colonne * TAILLE_CASE + 7
            x_depart = max(minimum, min(maximum, x_depart))
            self.monstres.append({
                "x": float(x_depart), "y": float(y_monstre),
                "min_x": float(minimum), "max_x": float(maximum),
                "direction": 1.0 if colonne % 2 == 0 else -1.0,
            })

    def editer_nouveau_niveau(self, identifiant: str | None = None) -> None:
        self.erreur = ""
        self.dossier_parcours.mkdir(parents=True, exist_ok=True)
        if identifiant is None:
            identifiant = "jeu-" + secrets.token_hex(3)
            self.niveau = niveau_depart()
        else:
            chemin = self.dossier_parcours / f"{identifiant}.json"
            try:
                self.niveau = decoder_niveau(chemin.read_text(encoding="utf-8"))
            except (OSError, ValueError) as erreur:
                self.erreur = f"Parcours impossible a charger : {erreur}"
                return
        self.id_parcours = identifiant
        fichier_nom = self.dossier_parcours / f"{identifiant}.name"
        if fichier_nom.exists():
            try:
                self.nom_parcours = fichier_nom.read_text(encoding="utf-8").strip() or "Mon parcours"
            except OSError:
                self.nom_parcours = "Mon parcours"
        else:
            self.nom_parcours = "Mon parcours" if identifiant.startswith("jeu-") else f"Parcours {identifiant}"
        self.saisie_nom_active = False
        self.camera_editeur = 0
        self.niveau.setdefault("monstres", [])
        self.case_selectionnee = SOL
        self.historique_niveau = []
        self.refaire_niveau = []
        self.sauvegarder_brouillon()
        self.etat = "editeur"

    def sauvegarder_brouillon(self) -> bool:
        try:
            code = encoder_niveau(self.niveau)
            self.dossier_parcours.mkdir(parents=True, exist_ok=True)
            (self.dossier_parcours / f"{self.id_parcours}.json").write_text(code, encoding="utf-8")
            (self.dossier_parcours / f"{self.id_parcours}.name").write_text(self.nom_parcours, encoding="utf-8")
            self.fichier_brouillon.parent.mkdir(parents=True, exist_ok=True)
            self.fichier_brouillon.write_text(code, encoding="utf-8")
        except (OSError, ValueError) as erreur:
            self.erreur = f"Impossible de sauvegarder le parcours : {erreur}"
            return False
        self.erreur = f"Sauvegarde automatique : {self.id_parcours}"
        return True

    def ouvrir_bibliotheque(self) -> None:
        try:
            self.dossier_parcours.mkdir(parents=True, exist_ok=True)
            ancien = self.dossier_parcours / "ancien-brouillon.json"
            if self.fichier_brouillon.exists() and not ancien.exists():
                ancien.write_text(self.fichier_brouillon.read_text(encoding="utf-8"), encoding="utf-8")
            self.parcours_disponibles = sorted(
                self.dossier_parcours.glob("*.json"),
                key=lambda chemin: chemin.stat().st_mtime, reverse=True,
            )[:7]
            self.erreur = ""
        except OSError as erreur:
            self.parcours_disponibles = []
            self.erreur = f"Bibliotheque inaccessible : {erreur}"
        self.etat = "bibliotheque"

    def memoriser_niveau(self) -> None:
        self.historique_niveau.append(copy.deepcopy(self.niveau))
        if len(self.historique_niveau) > 40:
            self.historique_niveau.pop(0)
        self.refaire_niveau.clear()

    def annuler_modification(self) -> None:
        if self.historique_niveau:
            self.refaire_niveau.append(copy.deepcopy(self.niveau))
            self.niveau = self.historique_niveau.pop()
            self.sauvegarder_brouillon()

    def refaire_modification(self) -> None:
        if self.refaire_niveau:
            self.historique_niveau.append(copy.deepcopy(self.niveau))
            self.niveau = self.refaire_niveau.pop()
            self.sauvegarder_brouillon()

    def changer_case(self, colonne: int, ligne: int, type_case: int,
                     memoriser: bool = False) -> None:
        if not (0 <= colonne < COLONNES_NIVEAU and 0 <= ligne < LIGNES_NIVEAU):
            return
        point = [colonne, ligne]
        monstres = self.niveau.setdefault("monstres", [])
        if type_case == OUTIL_MONSTRE:
            if point in (self.niveau["start"], self.niveau["goal"]) or point in monstres:
                return
            if memoriser:
                self.memoriser_niveau()
            monstres.append(point)
            self.sauvegarder_brouillon()
            return
        if type_case in (OUTIL_DEPART, OUTIL_ARRIVEE):
            nom = "start" if type_case == OUTIL_DEPART else "goal"
            if nom == "start" and ligne >= LIGNES_NIVEAU - 1:
                ligne = LIGNES_NIVEAU - 2
                point = [colonne, ligne]
            if (self.niveau[nom] == point
                    or self.niveau["start" if nom == "goal" else "goal"] == point
                    or point in monstres):
                return
            if memoriser:
                self.memoriser_niveau()
            self.niveau[nom] = point
            if type_case == OUTIL_DEPART:
                self.niveau["tiles"][ligne][colonne] = 0
                dessous = ligne + 1
                if (dessous < LIGNES_NIVEAU
                        and self.niveau["tiles"][dessous][colonne] not in (SOL, PLATEFORME)):
                    self.niveau["tiles"][dessous][colonne] = SOL
            else:
                self.niveau["tiles"][ligne][colonne] = 0
            self.sauvegarder_brouillon()
            return
        if point in (self.niveau["start"], self.niveau["goal"]):
            return
        if type_case == 0 and point in monstres:
            if memoriser:
                self.memoriser_niveau()
            monstres.remove(point)
            self.sauvegarder_brouillon()
            return
        monstre_present = point in monstres
        if self.niveau["tiles"][ligne][colonne] == type_case and not monstre_present:
            return
        if memoriser:
            self.memoriser_niveau()
        if monstre_present:
            monstres.remove(point)
        self.niveau["tiles"][ligne][colonne] = type_case
        self.sauvegarder_brouillon()

    def ouvrir_partage(self) -> None:
        try:
            self.partage_code = encoder_niveau(self.niveau)
        except ValueError as erreur:
            self.erreur = str(erreur)
            return
        self.sauvegarder_brouillon()
        self.message_partage = (
            "Code copie ! Envoie-le a ton ami."
            if self.copier_texte(self.partage_code)
            else "Selectionne le code ci-dessous pour le copier."
        )
        self.etat = "partage"

    def lancer(self, code: str) -> None:
        self.code = normaliser_code(code)
        self.type_partie = "arcade"
        self.message_partage = ""
        self.nouveau_record = False
        self.retour_resultat = "menu"
        self.graine = code_vers_graine(self.code)
        self.aleatoire = random.Random(self.graine)
        self.joueur = pygame.Vector2(LARGEUR / 2, HAUTEUR / 2 + 45)
        self.direction_personnage = pygame.Vector2(1, 0)
        self.direction_esquive = pygame.Vector2(1, 0)
        self.temps_animation = 0.0
        self.vitesse_joueur = 310.0
        self.temps = 0.0
        self.score = 0
        self.fragments = 0
        self.vies = 3
        self.invulnerable = 1.0
        self.duree_esquive = 0.0
        self.recharge_esquive = 0.0
        self.projectiles: list[dict[str, object]] = []
        self.fragments_actifs: list[pygame.Vector2] = []
        self.particules: list[dict[str, object]] = []
        self.prochain_projectile = 1.1
        self.prochain_fragment = 1.0
        self.combo = 0
        self.derniere_collecte = -10.0
        self.paused = False
        self.message_sauvegarde = ""
        try:
            self.record = lire_record(self.code, self.sauvegarde)
        except OSError as erreur:
            self.record = 0
            self.message_sauvegarde = str(erreur)
        self.etat = "jeu"

    def terminer(self, gagne: bool) -> None:
        self.gagne = gagne
        self.score += self.vies * 100
        try:
            self.record = enregistrer_record(self.code, self.score, self.sauvegarde)
        except OSError as erreur:
            self.message_sauvegarde = str(erreur)
        self.etat = "resultat"

    def ajouter_particules(self, position: pygame.Vector2, couleur: tuple[int, int, int],
                           quantite: int = 12) -> None:
        for _ in range(quantite):
            angle = self.aleatoire.random() * 6.283
            vitesse = self.aleatoire.uniform(45, 190)
            self.particules.append({
                "position": pygame.Vector2(position),
                "vitesse": pygame.Vector2(vitesse, 0).rotate_rad(angle),
                "vie": self.aleatoire.uniform(0.25, 0.55),
                "couleur": couleur,
            })

    def position_tactile(self, evenement: pygame.event.Event) -> tuple[int, int]:
        largeur, hauteur = pygame.display.get_window_size()
        echelle = min(largeur / LARGEUR, hauteur / HAUTEUR)
        decalage_x = (largeur - LARGEUR * echelle) / 2
        decalage_y = (hauteur - HAUTEUR * echelle) / 2
        x = (evenement.x * largeur - decalage_x) / echelle
        y = (evenement.y * hauteur - decalage_y) / echelle
        return round(x), round(y)

    def boutons_tactiles(self) -> list[tuple[str, tuple[int, int], int, str]]:
        if self.etat == "parcours":
            return [
                ("gauche", (88, 620), 35, "G"),
                ("droite", (180, 620), 35, "D"),
                ("saut", (850, 620), 35, "SAUT"),
                ("course", (940, 620), 35, "RUN"),
            ]
        if self.etat == "jeu":
            return [
                ("haut", (120, 550), 32, "H"),
                ("gauche", (65, 610), 32, "G"),
                ("droite", (175, 610), 32, "D"),
                ("bas", (120, 670), 25, "B"),
                ("esquive", (875, 615), 42, "ESQ"),
            ]
        return []

    def action_tactile(self, position: tuple[int, int]) -> str | None:
        if self.paused:
            return None
        boutons = self.boutons_tactiles()
        candidats = []
        for action, centre, rayon, _ in boutons:
            distance = math.dist(position, centre)
            if distance <= rayon:
                candidats.append((distance, action))
        return min(candidats)[1] if candidats else None

    def traiter_tactile(self, evenement: pygame.event.Event) -> bool:
        cle = (getattr(evenement, "touch_id", 0), evenement.finger_id)
        position = self.position_tactile(evenement)
        if evenement.type == getattr(pygame, "FINGERDOWN", -1):
            if not self.appareil_tactile:
                self.appareil_tactile = True
            if self.etat in ("jeu", "parcours"):
                if self.bouton_pause_tactile.collidepoint(position):
                    self.paused = not self.paused
                    self.touches_tactiles[cle] = "pause"
                    return True
                action = self.action_tactile(position)
                if action:
                    self.touches_tactiles[cle] = action
                    if action == "saut":
                        self.jump_buffer = 0.14
                    elif action == "esquive":
                        self.lancer_esquive()
                return True
            if self.etat == "menu" and not (
                    self.champ_code.collidepoint(position)
                    or self.bouton_saisie.collidepoint(position)):
                self.saisie_active = False
            if self.etat == "editeur" and not self.champ_nom.collidepoint(position):
                self.saisie_nom_active = False
            self.touches_tactiles[cle] = "interface"
            resultat = self.evenement(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": position, "button": 1}
            ))
            champ_actif = ((self.etat == "menu" and self.saisie_active)
                           or (self.etat == "editeur" and self.saisie_nom_active))
            self.clavier_tactile_actif = champ_actif
            fonction_clavier = getattr(
                pygame.key, "start_text_input" if champ_actif else "stop_text_input", None
            )
            if self.appareil_tactile and fonction_clavier:
                fonction_clavier()
            return resultat
        if evenement.type == getattr(pygame, "FINGERMOTION", -1):
            ancienne_action = self.touches_tactiles.get(cle)
            if ancienne_action in {"gauche", "droite", "haut", "bas", "saut", "course", "esquive"}:
                self.touches_tactiles[cle] = self.action_tactile(position) or ""
            elif self.etat == "editeur" and ancienne_action == "interface":
                self.editer_case_sous_souris(position, self.case_selectionnee)
            return True
        if evenement.type == getattr(pygame, "FINGERUP", -1):
            self.touches_tactiles.pop(cle, None)
            return True
        return True

    def dessiner_commandes_tactiles(self) -> None:
        if not self.appareil_tactile or self.etat not in ("jeu", "parcours"):
            return
        calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        actions_actives = set(self.touches_tactiles.values())
        couleur = CYAN if self.etat == "jeu" else ACCENTS_THEMES.get(
            self.niveau.get("theme", "prairie"), CYAN
        )
        for action, centre, rayon, etiquette in self.boutons_tactiles():
            actif = action in actions_actives
            remplissage = (*couleur, 88 if actif else 43)
            bordure = (*couleur, 230 if actif else 150)
            pygame.draw.circle(calque, (9, 15, 29, 120), centre, rayon + 4)
            pygame.draw.circle(calque, remplissage, centre, rayon)
            pygame.draw.circle(calque, bordure, centre, rayon, 2)
            label = self.police_petite.render(etiquette, True, BLANC)
            calque.blit(label, label.get_rect(center=centre))
        pygame.draw.rect(calque, (12, 20, 36, 190), self.bouton_pause_tactile, border_radius=12)
        pygame.draw.rect(calque, (*couleur, 210), self.bouton_pause_tactile, 2, border_radius=12)
        for x in (self.bouton_pause_tactile.x + 18, self.bouton_pause_tactile.x + 29):
            pygame.draw.rect(calque, BLANC, (x, self.bouton_pause_tactile.y + 14, 5, 22), border_radius=2)
        self.ecran.blit(calque, (0, 0))

    def mettre_a_jour(self, dt: float, touches: pygame.key.ScancodeWrapper) -> None:
        if self.etat != "jeu" or self.paused:
            return

        self.temps = min(DUREE_PARTIE, self.temps + dt)
        self.duree_esquive = max(0.0, self.duree_esquive - dt)
        self.recharge_esquive = max(0.0, self.recharge_esquive - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.temps_animation += dt

        actions_tactiles = set(self.touches_tactiles.values())
        direction = pygame.Vector2(
            int(touches[pygame.K_d] or touches[pygame.K_RIGHT] or "droite" in actions_tactiles)
            - int(touches[pygame.K_q] or touches[pygame.K_a] or touches[pygame.K_LEFT] or "gauche" in actions_tactiles),
            int(touches[pygame.K_s] or touches[pygame.K_DOWN] or "bas" in actions_tactiles)
            - int(touches[pygame.K_z] or touches[pygame.K_w] or touches[pygame.K_UP] or "haut" in actions_tactiles),
        )
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.direction_personnage = direction.copy()
        if self.duree_esquive > 0:
            direction = self.direction_esquive
            vitesse = self.vitesse_joueur * 2.45
        else:
            vitesse = self.vitesse_joueur
        self.joueur += direction * vitesse * dt
        self.joueur.x = max(40, min(LARGEUR - 40, self.joueur.x))
        self.joueur.y = max(127, min(HAUTEUR - 50, self.joueur.y))

        if self.temps >= self.prochain_projectile:
            self.creer_projectile()
            intervalle = max(0.52, 1.45 - self.temps * 0.018)
            self.prochain_projectile += self.aleatoire.uniform(intervalle * 0.75, intervalle * 1.2)
        if self.temps >= self.prochain_fragment and len(self.fragments_actifs) < 2:
            self.fragments_actifs.append(pygame.Vector2(
                self.aleatoire.randint(90, LARGEUR - 90),
                self.aleatoire.randint(155, HAUTEUR - 90),
            ))
            self.prochain_fragment = self.temps + self.aleatoire.uniform(2.2, 3.1)

        for projectile in self.projectiles[:]:
            if projectile["delai"] > 0:
                projectile["delai"] = max(0.0, projectile["delai"] - dt)
                continue
            projectile["age"] += dt
            if projectile["type"] == "spirale":
                projectile["vitesse"].rotate_ip(115 * dt)
            projectile["position"] += projectile["vitesse"] * dt
            if not pygame.Rect(-60, 80, LARGEUR + 120, HAUTEUR + 60).collidepoint(projectile["position"]):
                self.projectiles.remove(projectile)
                continue
            if self.joueur.distance_to(projectile["position"]) < projectile["rayon"] + 13:
                self.projectiles.remove(projectile)
                if self.invulnerable <= 0 and self.duree_esquive <= 0:
                    self.vies -= 1
                    self.combo = 0
                    self.invulnerable = 1.35
                    self.ajouter_particules(self.joueur, ROUGE, 18)
                    self.projectiles.clear()
                    if self.vies <= 0:
                        self.terminer(False)
                        return

        for fragment in self.fragments_actifs[:]:
            if self.joueur.distance_to(fragment) < 27:
                self.fragments_actifs.remove(fragment)
                self.fragments += 1
                self.combo = self.combo + 1 if self.temps - self.derniere_collecte < 4.0 else 1
                self.derniere_collecte = self.temps
                self.score += 150 + min(150, (self.combo - 1) * 30)
                self.ajouter_particules(fragment, CYAN, 14)

        for particule in self.particules[:]:
            particule["position"] += particule["vitesse"] * dt
            particule["vie"] -= dt
            if particule["vie"] <= 0:
                self.particules.remove(particule)

        self.score = max(self.score, int(self.temps * 12) + self.fragments * 150)
        if self.temps >= DUREE_PARTIE:
            self.terminer(True)

    def cases_solides(self, rect: pygame.Rect) -> list[tuple[int, int, int]]:
        cases = self.niveau["tiles"]
        gauche = max(0, int((rect.left - DEBUT_CARTE.x) // TAILLE_CASE))
        droite = min(COLONNES_NIVEAU - 1,
                     int((rect.right - DEBUT_CARTE.x) // TAILLE_CASE))
        haut = max(0, (rect.top - int(DEBUT_CARTE.y)) // TAILLE_CASE)
        bas = min(LIGNES_NIVEAU - 1,
                  (rect.bottom - int(DEBUT_CARTE.y)) // TAILLE_CASE)
        trouvees: list[tuple[int, int, int]] = []
        for ligne in range(haut, bas + 1):
            for colonne in range(gauche, droite + 1):
                type_case = cases[ligne][colonne]
                if type_case in (SOL, PLATEFORME, PIC, POINT_CONTROLE, RESSORT, GEMME, COEUR):
                    trouvees.append((colonne, ligne, type_case))
        return trouvees

    def reapparaitre(self) -> None:
        self.vies -= 1
        point = self.dernier_controle
        self.rect_joueur.topleft = (
            int(DEBUT_CARTE.x) + point[0] * TAILLE_CASE + 10,
            int(DEBUT_CARTE.y) + point[1] * TAILLE_CASE + 5,
        )
        self.vitesse_x = 0.0
        self.vitesse_y = 0.0
        self.jump_buffer = 0.0
        self.invulnerable = 1.0
        self.coyote = 0.0
        self.sol = False
        self.ressort_verrouille = False
        if self.vies <= 0:
            self.terminer_parcours(False)

    def terminer_parcours(self, gagne: bool) -> None:
        self.gagne = gagne
        if gagne:
            self.score_parcours += max(0, 10000 - round(self.temps_parcours * 50))
            temps_ms = round(self.temps_parcours * 1000)
            ancien_record = self.record
            try:
                self.record = enregistrer_record_parcours(
                    self.code, temps_ms, self.sauvegarde
                )
                self.nouveau_record = ancien_record == 0 or temps_ms < ancien_record
            except OSError as erreur:
                self.nouveau_record = False
                self.message_sauvegarde = str(erreur)
        self.etat = "resultat"

    def mettre_a_jour_parcours(self, dt: float,
                               touches: pygame.key.ScancodeWrapper) -> None:
        if self.paused:
            return
        self.atmosphere.update(dt)
        self.temps_parcours += dt
        for particule in self.particules[:]:
            particule["position"] += particule["vitesse"] * dt
            particule["vie"] -= dt
            if particule["vie"] <= 0:
                self.particules.remove(particule)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.jump_buffer = max(0.0, self.jump_buffer - dt)
        self.coyote = max(0.0, self.coyote - dt)
        for monstre in self.monstres:
            monstre["x"] += monstre["direction"] * 82 * dt
            if monstre["x"] <= monstre["min_x"]:
                monstre["x"] = monstre["min_x"]
                monstre["direction"] = 1.0
            elif monstre["x"] >= monstre["max_x"]:
                monstre["x"] = monstre["max_x"]
                monstre["direction"] = -1.0
        actions_tactiles = set(self.touches_tactiles.values())
        direction_x = (
            int(touches[pygame.K_d] or touches[pygame.K_RIGHT] or "droite" in actions_tactiles)
            - int(touches[pygame.K_q] or touches[pygame.K_a] or touches[pygame.K_LEFT] or "gauche" in actions_tactiles)
        )
        ancienne_gauche = self.rect_joueur.left
        ancienne_droite = self.rect_joueur.right
        ancienne_x = self.rect_joueur.x
        course = touches[pygame.K_LSHIFT] or touches[pygame.K_RSHIFT] or "course" in actions_tactiles
        vitesse_max = 360 if course else 270
        vitesse_cible = direction_x * vitesse_max
        if direction_x:
            acceleration = 2300 if self.sol else 1150
        else:
            acceleration = 2600 if self.sol else 260
        ecart_vitesse = vitesse_cible - self.vitesse_x
        self.vitesse_x += max(-acceleration * dt, min(acceleration * dt, ecart_vitesse))
        self.rect_joueur.x += round(self.vitesse_x * dt)
        self.rect_joueur.x = max(int(DEBUT_CARTE.x), min(
            int(DEBUT_CARTE.x) + COLONNES_NIVEAU * TAILLE_CASE - self.rect_joueur.width,
            self.rect_joueur.x,
        ))
        deplacement_x = self.rect_joueur.x - ancienne_x
        for colonne, ligne, type_case in self.cases_solides(self.rect_joueur):
            if type_case == PIC:
                continue
            bloc = pygame.Rect(int(DEBUT_CARTE.x) + colonne * TAILLE_CASE,
                               int(DEBUT_CARTE.y) + ligne * TAILLE_CASE,
                               TAILLE_CASE, TAILLE_CASE)
            if type_case == SOL and self.rect_joueur.colliderect(bloc):
                if deplacement_x > 0:
                    self.rect_joueur.right = bloc.left
                    self.vitesse_x = 0.0
                elif deplacement_x < 0:
                    self.rect_joueur.left = bloc.right
                    self.vitesse_x = 0.0
                elif ancienne_droite <= bloc.left:
                    self.rect_joueur.right = bloc.left
                elif ancienne_gauche >= bloc.right:
                    self.rect_joueur.left = bloc.right

        if self.jump_buffer > 0 and (self.sol or self.coyote > 0):
            self.vitesse_y = -510
            self.sol = False
            self.coyote = 0
            self.jump_buffer = 0

        # Relacher le saut reduit sa hauteur, comme dans les jeux de plateforme classiques.
        saut_maintenu = (touches[pygame.K_SPACE] or touches[pygame.K_UP] or touches[pygame.K_w] or touches[pygame.K_z] or "saut" in actions_tactiles)
        gravite = 900 if self.vitesse_y < 0 and saut_maintenu else 1450
        ancienne_bas = self.rect_joueur.bottom
        self.vitesse_y = min(780, self.vitesse_y + gravite * dt)
        self.rect_joueur.y += round(self.vitesse_y * dt)
        etait_sol = self.sol
        self.sol = False
        for colonne, ligne, type_case in self.cases_solides(self.rect_joueur):
            if type_case in (PIC, RESSORT, POINT_CONTROLE, GEMME, COEUR):
                continue
            bloc = pygame.Rect(int(DEBUT_CARTE.x) + colonne * TAILLE_CASE,
                               int(DEBUT_CARTE.y) + ligne * TAILLE_CASE,
                               TAILLE_CASE, TAILLE_CASE)
            chevauche_horizontal = (
                self.rect_joueur.right > bloc.left
                and self.rect_joueur.left < bloc.right
            )
            if (self.vitesse_y >= 0 and chevauche_horizontal
                    and ancienne_bas <= bloc.top and self.rect_joueur.bottom >= bloc.top):
                self.rect_joueur.bottom = bloc.top
                self.vitesse_y = 0
                self.sol = True
                if not etait_sol:
                    self.coyote = 0.1
                    self.ajouter_particules(
                        pygame.Vector2(self.rect_joueur.centerx, self.rect_joueur.bottom),
                        (190, 200, 210), 5,
                    )
            elif (type_case == SOL and self.vitesse_y < 0
                  and self.rect_joueur.colliderect(bloc)):
                self.rect_joueur.top = bloc.bottom
                self.vitesse_y = 0
        if self.sol and etait_sol:
            self.coyote = 0.1

        for ligne, rangee in enumerate(self.niveau["tiles"]):
            for colonne, type_case in enumerate(rangee):
                if type_case != POINT_CONTROLE:
                    continue
                tuile = pygame.Rect(
                    int(DEBUT_CARTE.x) + colonne * TAILLE_CASE,
                    int(DEBUT_CARTE.y) + ligne * TAILLE_CASE,
                    TAILLE_CASE, TAILLE_CASE,
                )
                point = (colonne, ligne)
                if self.rect_joueur.colliderect(tuile) and point not in self.controles_actives:
                    self.dernier_controle = point
                    self.controles_actives.add(point)
                    self.score_parcours += 250
                    self.ajouter_particules(
                        pygame.Vector2(tuile.centerx, tuile.centery), VERT, 18
                    )

        touches_ressort = False
        for colonne, ligne, type_case in self.cases_solides(self.rect_joueur):
            tuile = pygame.Rect(
                int(DEBUT_CARTE.x) + colonne * TAILLE_CASE,
                int(DEBUT_CARTE.y) + ligne * TAILLE_CASE,
                TAILLE_CASE, TAILLE_CASE,
            )
            if type_case == RESSORT and self.rect_joueur.colliderect(tuile):
                touches_ressort = True
                if not self.ressort_verrouille and self.vitesse_y >= 0:
                    self.rect_joueur.bottom = tuile.top + 8
                    self.vitesse_y = -690
                    self.sol = False
                    self.coyote = 0
                    self.ressort_verrouille = True
                    self.ajouter_particules(
                        pygame.Vector2(tuile.centerx, tuile.centery), JAUNE, 14
                    )
            if (type_case == GEMME and (colonne, ligne) in self.gemmes
                    and self.rect_joueur.colliderect(tuile)):
                self.gemmes.remove((colonne, ligne))
                self.gemmes_collectees.add((colonne, ligne))
                self.gemmes_parcours += 1
                self.score_parcours += 500
                self.ajouter_particules(
                    pygame.Vector2(tuile.centerx, tuile.centery), CYAN, 16
                )
            if (type_case == COEUR and (colonne, ligne) in self.coeurs_restants
                    and self.rect_joueur.colliderect(tuile)):
                self.coeurs_restants.remove((colonne, ligne))
                self.vies = min(5, self.vies + 1)
                self.score_parcours += 250
                self.ajouter_particules(
                    pygame.Vector2(tuile.centerx, tuile.centery), (255, 93, 137), 18
                )
        if not touches_ressort:
            self.ressort_verrouille = False

        for colonne, ligne, type_case in self.cases_solides(self.rect_joueur):
            if type_case == PIC:
                pic = pygame.Rect(int(DEBUT_CARTE.x) + colonne * TAILLE_CASE + 4,
                                  int(DEBUT_CARTE.y) + ligne * TAILLE_CASE + 12,
                                  TAILLE_CASE - 8, TAILLE_CASE - 12)
                if self.rect_joueur.colliderect(pic) and self.invulnerable <= 0:
                    self.reapparaitre()
                    return
        for monstre in self.monstres:
            rectangle_monstre = pygame.Rect(round(monstre["x"]), round(monstre["y"]), 34, 34)
            if self.rect_joueur.colliderect(rectangle_monstre) and self.invulnerable <= 0:
                self.reapparaitre()
                return
        arrivee = self.niveau["goal"]
        porte = pygame.Rect(int(DEBUT_CARTE.x) + arrivee[0] * TAILLE_CASE,
                            int(DEBUT_CARTE.y) + arrivee[1] * TAILLE_CASE - 22,
                            TAILLE_CASE, TAILLE_CASE + 22)
        if self.rect_joueur.colliderect(porte):
            self.terminer_parcours(True)
        elif self.rect_joueur.top > HAUTEUR + 50:
            self.reapparaitre()
        if self.etat != "parcours":
            return
        camera_max = int(DEBUT_CARTE.x) + COLONNES_NIVEAU * TAILLE_CASE - (LARGEUR - 24)
        anticipation = max(-42, min(42, self.vitesse_x * .12))
        camera_cible = max(0.0, min(
            camera_max, self.rect_joueur.centerx - LARGEUR * .42 + anticipation
        ))
        inertie_camera = 1 - math.exp(-8 * dt)
        self.camera_parcours += (camera_cible - self.camera_parcours) * inertie_camera

    def creer_projectile(self) -> None:
        bord = self.aleatoire.randrange(4)
        if bord == 0:
            position = pygame.Vector2(self.aleatoire.randint(20, LARGEUR - 20), 100)
        elif bord == 1:
            position = pygame.Vector2(LARGEUR - 20, self.aleatoire.randint(120, HAUTEUR - 20))
        elif bord == 2:
            position = pygame.Vector2(self.aleatoire.randint(20, LARGEUR - 20), HAUTEUR - 20)
        else:
            position = pygame.Vector2(20, self.aleatoire.randint(120, HAUTEUR - 20))
        direction = self.joueur - position
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()
        archetype = self.aleatoire.choices(
            ("traqueur", "eclat", "spirale"), weights=(5, 3, 2)
        )[0]
        if archetype == "traqueur":
            vitesse = 145 + min(145, self.temps * 2.3)
            rayon = self.aleatoire.randint(10, 13)
        elif archetype == "eclat":
            vitesse = 225 + min(100, self.temps * 1.8)
            rayon = self.aleatoire.randint(7, 9)
        else:
            vitesse = 105 + min(75, self.temps * 1.5)
            rayon = self.aleatoire.randint(12, 15)
        self.projectiles.append({
            "position": position,
            "vitesse": direction * vitesse,
            "rayon": rayon,
            "type": archetype,
            "age": 0.0,
            "delai": 0.34,
        })

    def lancer_esquive(self) -> None:
        if self.etat == "jeu" and not self.paused and self.recharge_esquive <= 0:
            self.duree_esquive = 0.19
            self.recharge_esquive = 1.05
            self.direction_esquive = self.direction_personnage.copy()
            self.invulnerable = max(self.invulnerable, 0.24)

    def action_principale_resultat(self) -> None:
        if self.type_partie == "parcours":
            if self.campagne_base and self.gagne:
                prochain = (1 if self.numero_niveau_base >= NIVEAUX_CARTE_BASE
                            else self.numero_niveau_base + 1)
                self.lancer_niveau_carte_base(prochain)
            else:
                self.lancer_parcours(
                    self.niveau, self.code, self.retour_resultat,
                    campagne_base=self.campagne_base,
                    numero_niveau_base=self.numero_niveau_base,
                )
        else:
            self.lancer(self.code)

    def evenement(self, evenement: pygame.event.Event) -> bool:
        if evenement.type == getattr(pygame, "TEXTINPUT", -1):
            if self.clavier_tactile_actif:
                for caractere in evenement.text:
                    if self.etat == "menu" and self.saisie_active:
                        caractere = caractere.upper()
                        if (caractere in CODE_ALPHABET or caractere in "-_") and len(self.saisie_code) < 2000:
                            self.saisie_code += caractere
                            self.erreur = ""
                    elif self.etat == "editeur" and self.saisie_nom_active:
                        if caractere.isprintable() and len(self.nom_parcours) < 28:
                            self.nom_parcours += caractere
                            self.sauvegarder_brouillon()
            return True
        if evenement.type in (
                getattr(pygame, "FINGERDOWN", -1),
                getattr(pygame, "FINGERMOTION", -1),
                getattr(pygame, "FINGERUP", -1)):
            return self.traiter_tactile(evenement)
        if (evenement.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)
                and getattr(evenement, "touch", False)):
            return True
        if evenement.type == pygame.QUIT:
            return False
        if evenement.type == pygame.KEYDOWN:
            if evenement.key == pygame.K_ESCAPE:
                if self.etat in ("jeu", "parcours"):
                    self.paused = not self.paused
                elif self.etat == "editeur":
                    self.sauvegarder_brouillon()
                    self.etat = "menu"
                elif self.etat == "parcours_menu":
                    self.etat = "creation"
                elif self.etat in ("bibliotheque", "creation"):
                    self.etat = "menu"
                elif self.etat == "partage":
                    self.etat = "editeur"
                else:
                    return False
            elif self.etat == "menu":
                if evenement.key == pygame.K_v and evenement.mod & pygame.KMOD_CTRL:
                    contenu = self.lire_presse_papier()
                    if contenu:
                        self.saisie_code = contenu[:2000]
                        self.erreur = ""
                elif evenement.key == pygame.K_BACKSPACE and self.saisie_active:
                    self.saisie_code = self.saisie_code[:-1]
                    self.erreur = ""
                elif evenement.key == pygame.K_RETURN and self.saisie_active:
                    self.jouer_code_saisi()
                elif self.saisie_active and not self.clavier_tactile_actif and evenement.unicode and evenement.unicode.upper() in CODE_ALPHABET:
                    if len(self.saisie_code) < 2000:
                        self.saisie_code += evenement.unicode
                        self.erreur = ""
                elif self.saisie_active and not self.clavier_tactile_actif and evenement.unicode in "-_":
                    if len(self.saisie_code) < 2000:
                        self.saisie_code += evenement.unicode
            elif self.etat == "jeu":
                if evenement.key == pygame.K_p:
                    self.paused = not self.paused
                elif evenement.key == pygame.K_SPACE:
                    self.lancer_esquive()
            elif self.etat == "parcours":
                if (not self.paused
                        and evenement.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_z)):
                    self.jump_buffer = 0.14
                elif evenement.key == pygame.K_p:
                    self.paused = not self.paused
            elif self.etat == "editeur":
                if self.saisie_nom_active and evenement.key == pygame.K_RETURN:
                    self.saisie_nom_active = False
                    self.sauvegarder_brouillon()
                elif self.saisie_nom_active and evenement.key == pygame.K_BACKSPACE:
                    self.nom_parcours = self.nom_parcours[:-1]
                    self.sauvegarder_brouillon()
                elif self.saisie_nom_active and not self.clavier_tactile_actif and evenement.unicode and evenement.unicode.isprintable():
                    if len(self.nom_parcours) < 28:
                        self.nom_parcours += evenement.unicode
                        self.sauvegarder_brouillon()
                elif evenement.mod & pygame.KMOD_CTRL and evenement.key == pygame.K_s:
                    self.sauvegarder_brouillon()
                elif evenement.key == pygame.K_n:
                    self.editer_nouveau_niveau()
                elif evenement.mod & pygame.KMOD_CTRL and evenement.key == pygame.K_z:
                    self.annuler_modification()
                elif evenement.mod & pygame.KMOD_CTRL and evenement.key == pygame.K_y:
                    self.refaire_modification()
                else:
                    outils_clavier = {
                        pygame.K_0: 0,
                        pygame.K_1: SOL,
                        pygame.K_2: PLATEFORME,
                        pygame.K_3: PIC,
                        pygame.K_4: POINT_CONTROLE,
                        pygame.K_5: RESSORT,
                        pygame.K_6: GEMME,
                        pygame.K_7: COEUR,
                        pygame.K_m: OUTIL_MONSTRE,
                        pygame.K_8: OUTIL_DEPART,
                        pygame.K_9: OUTIL_ARRIVEE,
                    }
                    if evenement.key in outils_clavier:
                        self.selectionner_outil_editeur(outils_clavier[evenement.key])
            elif self.etat == "partage":
                if evenement.key == pygame.K_c:
                    self.message_partage = (
                        "Code copie ! Envoie-le a ton ami."
                        if self.copier_texte(self.partage_code)
                        else "Copie impossible : selectionne le code manuellement."
                    )
            elif self.etat == "resultat":
                if evenement.key == pygame.K_RETURN:
                    self.action_principale_resultat()
                elif evenement.key == pygame.K_n:
                    self.code = nouveau_code()
                    self.lancer(self.code)
                elif evenement.key == pygame.K_m:
                    self.etat = self.retour_resultat
                elif evenement.key == pygame.K_c and self.type_partie == "arcade":
                    self.copier_code_arcade()
        if (self.appareil_tactile and evenement.type == pygame.MOUSEBUTTONDOWN
                and evenement.button == 1 and self.etat in ("jeu", "parcours")
                and self.bouton_pause_tactile.collidepoint(evenement.pos)):
            self.paused = not self.paused
            return True
        if evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
            if self.etat == "menu":
                if self.boutons_menu[0].collidepoint(evenement.pos):
                    self.etat = "creation"
                elif self.boutons_menu[1].collidepoint(evenement.pos):
                    self.lancer(code_defi_du_jour())
                elif self.boutons_menu[2].collidepoint(evenement.pos):
                    self.ouvrir_bibliotheque()
                elif self.champ_code.collidepoint(evenement.pos):
                    self.saisie_active = True
                elif self.bouton_saisie.collidepoint(evenement.pos):
                    self.saisie_active = True
                elif self.bouton_code.collidepoint(evenement.pos):
                    self.jouer_code_saisi()
            elif self.etat == "creation":
                if self.boutons_creation[0].collidepoint(evenement.pos):
                    CacheCache3D(self.ecran).executer()
                    self.ecran = creer_fenetre_jeu()
                elif self.boutons_creation[1].collidepoint(evenement.pos):
                    self.etat = "parcours_menu"
                elif self.bouton_retour_creation.collidepoint(evenement.pos):
                    self.etat = "menu"
            elif self.etat == "parcours_menu":
                if self.boutons_parcours[0].collidepoint(evenement.pos):
                    self.lancer_niveau_carte_base()
                elif self.boutons_parcours[1].collidepoint(evenement.pos):
                    self.editer_nouveau_niveau()
                elif self.bouton_retour_parcours.collidepoint(evenement.pos):
                    self.etat = "creation"
            elif self.etat == "bibliotheque":
                if self.bouton_nouveau.collidepoint(evenement.pos):
                    self.editer_nouveau_niveau()
                elif self.bouton_retour_bibliotheque.collidepoint(evenement.pos):
                    self.etat = "menu"
                else:
                    for chemin, rect in zip(self.parcours_disponibles, self.lignes_bibliotheque):
                        if rect.collidepoint(evenement.pos):
                            self.editer_nouveau_niveau(chemin.stem)
                            break
            elif self.etat == "editeur":
                if self.bouton_theme.collidepoint(evenement.pos):
                    self.memoriser_niveau()
                    index_theme = THEMES_PARCOURS.index(self.niveau.get("theme", "prairie"))
                    self.niveau["theme"] = THEMES_PARCOURS[
                        (index_theme + 1) % len(THEMES_PARCOURS)
                    ]
                    self.sauvegarder_brouillon()
                elif self.champ_nom.collidepoint(evenement.pos):
                    self.saisie_nom_active = True
                else:
                    categorie = next(
                        (categorie for categorie, _, rect in self.categories_editeur
                         if rect.collidepoint(evenement.pos)),
                        None,
                    )
                    if categorie is not None:
                        self.selectionner_categorie_editeur(categorie)
                    else:
                        for rect, type_case in self.palette_editeur:
                            if rect.collidepoint(evenement.pos):
                                self.case_selectionnee = type_case
                                break
                        else:
                            if self.actions_editeur[0].collidepoint(evenement.pos):
                                self.sauvegarder_brouillon()
                            elif self.actions_editeur[1].collidepoint(evenement.pos):
                                self.sauvegarder_brouillon()
                                self.ouvrir_partage()
                            elif self.actions_editeur[2].collidepoint(evenement.pos):
                                try:
                                    code = encoder_niveau(self.niveau)
                                    self.sauvegarder_brouillon()
                                    self.lancer_parcours(self.niveau, code, "editeur")
                                except ValueError as erreur:
                                    self.erreur = str(erreur)
                            elif self.actions_editeur[3].collidepoint(evenement.pos):
                                self.sauvegarder_brouillon()
                                self.etat = "menu"
                            else:
                                self.editer_case_sous_souris(
                                    evenement.pos, self.case_selectionnee
                                )
            elif self.etat == "partage":
                if self.bouton_copier.collidepoint(evenement.pos):
                    self.message_partage = (
                        "Code copie ! Envoie-le a ton ami."
                        if self.copier_texte(self.partage_code)
                        else "Copie impossible : selectionne le code manuellement."
                    )
                elif self.bouton_partage_test.collidepoint(evenement.pos):
                    self.lancer_parcours(self.niveau, self.partage_code, "editeur")
                elif self.bouton_partage_editer.collidepoint(evenement.pos):
                    self.etat = "editeur"
            elif self.etat == "resultat":
                if (self.type_partie == "arcade"
                        and self.bouton_copier_code.collidepoint(evenement.pos)):
                    self.copier_code_arcade()
                elif self.bouton_rejouer.collidepoint(evenement.pos):
                    self.action_principale_resultat()
                elif self.bouton_menu.collidepoint(evenement.pos):
                    self.etat = self.retour_resultat
        if self.etat == "editeur" and evenement.type == pygame.MOUSEBUTTONDOWN:
            if evenement.button == 3:
                self.editer_case_sous_souris(evenement.pos, 0)
            elif evenement.button == 4:
                self.camera_editeur = max(0, self.camera_editeur - 3 * TAILLE_CASE)
            elif evenement.button == 5:
                self.camera_editeur = min(
                    COLONNES_NIVEAU * TAILLE_CASE - (LARGEUR - 48),
                    self.camera_editeur + 3 * TAILLE_CASE,
                )
        if self.etat == "editeur" and evenement.type == pygame.MOUSEWHEEL:
            self.camera_editeur = max(0, min(
                COLONNES_NIVEAU * TAILLE_CASE - (LARGEUR - 48),
                self.camera_editeur - evenement.y * 3 * TAILLE_CASE,
            ))
        if self.etat == "editeur" and evenement.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0] and evenement.pos[1] >= int(DEBUT_CARTE.y):
                self.editer_case_sous_souris(evenement.pos, self.case_selectionnee)
            elif pygame.mouse.get_pressed()[2] and evenement.pos[1] >= int(DEBUT_CARTE.y):
                self.editer_case_sous_souris(evenement.pos, 0)
        if self.etat == "editeur" and evenement.type == pygame.KEYDOWN:
            if evenement.key == pygame.K_a:
                self.camera_editeur = max(0, self.camera_editeur - 100)
            elif evenement.key == pygame.K_d:
                self.camera_editeur = min(
                    COLONNES_NIVEAU * TAILLE_CASE - (LARGEUR - 48),
                    self.camera_editeur + 100,
                )
        return True

    def editer_case_sous_souris(self, position: tuple[int, int], type_case: int) -> None:
        x, y = position
        if not (24 <= x < LARGEUR - 24 and int(DEBUT_CARTE.y) <= y < 640):
            return
        colonne = (x - 24 + self.camera_editeur) // TAILLE_CASE
        ligne = (y - int(DEBUT_CARTE.y)) // TAILLE_CASE
        self.changer_case(colonne, ligne, type_case, memoriser=True)

    def jouer_code_saisi(self) -> None:
        code = self.saisie_code.strip()
        if code.upper().startswith(("P1-", "P2-", "P3-", "P4-")):
            try:
                niveau = decoder_niveau(code)
            except ValueError as erreur:
                self.erreur = str(erreur)
                return
            self.niveau = niveau
            self.lancer_parcours(niveau, encoder_niveau(niveau))
            return
        try:
            self.lancer(code)
        except ValueError as erreur:
            self.erreur = str(erreur)

    def dessiner_fond(self) -> None:
        self.ecran.blit(self.fond_degrade, (0, 0))
        self.ecran.blit(self.voile_nebuleuse, (0, 0))
        secondes = pygame.time.get_ticks() / 1000.0
        scintillement = pygame.time.get_ticks() // 500
        for index, (x, y, rayon) in enumerate(self.etoiles):
            pulsation = 0.62 + 0.38 * (
                0.5 + 0.5 * math.sin(index * 1.73 + secondes * (1.5 + index % 5 * 0.17))
            )
            couleur_base = (142, 174, 218) if (index + scintillement) % 11 == 0 else (67, 88, 132)
            if index % 13 == 0:
                couleur_base = (112, 142, 190)
            couleur = tuple(round(canal * pulsation) for canal in couleur_base)
            position = (
                round((x + math.sin(secondes * 0.17 + index) * 1.5) % LARGEUR),
                round((y - secondes * (0.7 + index % 4 * 0.32)) % HAUTEUR),
            )
            pygame.draw.circle(self.ecran, couleur, position, rayon)
            if rayon > 1 and pulsation > 0.95:
                pygame.draw.line(self.ecran, couleur,
                                 (position[0] - 4, position[1]),
                                 (position[0] + 4, position[1]), 1)
                pygame.draw.line(self.ecran, couleur,
                                 (position[0], position[1] - 4),
                                 (position[0], position[1] + 4), 1)
        # Grandes orbites fines pour renforcer la profondeur spatiale.
        pygame.draw.arc(self.ecran, (37, 58, 99), (334, 20, 566, 290), 0.15, 2.7, 1)
        pygame.draw.ellipse(self.ecran, (48, 70, 111), (748, 91, 174, 104), width=2)
        pygame.draw.ellipse(self.ecran, (34, 54, 91), (98, 449, 144, 122), width=1)

        # Planete bleue avec un degrade en cercles concentriques.
        for rayon in range(65, 0, -1):
            lumiere = 1 - rayon / 65
            couleur = (
                int(18 + 40 * lumiere),
                int(29 + 61 * lumiere),
                int(61 + 91 * lumiere),
            )
            pygame.draw.circle(self.ecran, couleur, (833, 141), rayon)
        pygame.draw.circle(self.ecran, (88, 127, 174), (814, 119), 15)
        pygame.draw.circle(self.ecran, (52, 77, 120), (851, 153), 9, width=2)
        pygame.draw.circle(self.ecran, (25, 43, 79), (833, 141), 65, width=2)
        pygame.draw.arc(self.ecran, (111, 143, 190), (748, 91, 174, 104), 3.25, 6.08, 2)
        angle_satellite = secondes * 0.42
        satellite = (
            round(833 + math.cos(angle_satellite) * 91),
            round(141 + math.sin(angle_satellite) * 36),
        )
        pygame.draw.circle(self.ecran, (62, 99, 145), satellite, 7)
        pygame.draw.circle(self.ecran, (175, 222, 246), satellite, 3)

        phase_meteore = (pygame.time.get_ticks() % 13000) / 1000.0
        if phase_meteore < 0.82:
            progression = phase_meteore / 0.82
            tete = (round(410 + progression * 340), round(290 - progression * 220))
            queue = (tete[0] - 82, tete[1] + 54)
            pygame.draw.line(self.ecran, (36, 87, 127), queue, tete, 5)
            pygame.draw.line(self.ecran, (145, 224, 255), queue, tete, 2)
            pygame.draw.circle(self.ecran, (229, 247, 255), tete, 3)

        # Petite lune au premier plan et reliefs lointains au bas de l'ecran.
        pygame.draw.circle(self.ecran, (30, 74, 98), (170, 510), 54)
        pygame.draw.circle(self.ecran, (49, 111, 128), (157, 495), 21)
        pygame.draw.circle(self.ecran, (22, 53, 79), (184, 523), 12)
        pygame.draw.circle(self.ecran, (85, 142, 157), (170, 510), 54, width=2)
        pygame.draw.polygon(self.ecran, (14, 23, 44), [
            (0, 626), (82, 601), (155, 635), (250, 586), (354, 642),
            (464, 604), (574, 647), (699, 590), (817, 641), (910, 604),
            (LARGEUR, 626), (LARGEUR, HAUTEUR), (0, HAUTEUR),
        ])
        pygame.draw.lines(self.ecran, (34, 51, 78), False, [
            (0, 626), (82, 601), (155, 635), (250, 586), (354, 642),
            (464, 604), (574, 647), (699, 590), (817, 641), (910, 604),
            (LARGEUR, 626),
        ], 1)
        pygame.draw.polygon(self.ecran, (9, 16, 34), [
            (0, 676), (116, 640), (230, 681), (352, 637), (485, 684),
            (619, 644), (744, 686), (870, 644), (LARGEUR, 670),
            (LARGEUR, HAUTEUR), (0, HAUTEUR),
        ])


        pygame.draw.circle(self.ecran, (210, 230, 255), (833, 141), 2)
        pygame.draw.circle(self.ecran, (177, 220, 231), (170, 510), 2)

    def dessiner_menu(self) -> None:
        self.dessiner_fond()
        pygame.draw.line(self.ecran, (66, 104, 145), (420, 53), (580, 53), 1)
        texte(self.ecran, self.police_petite, "LE DEFI COMMENCE ICI",
              (LARGEUR // 2, 52), CYAN, True)
        texte(self.ecran, self.police_titre, "DEFI TON POTE", (LARGEUR // 2, 115), BLANC, True)
        texte(self.ecran, self.police, "Un defi rapide chaque jour. Des parcours a partager entre amis.",
              (LARGEUR // 2, 175), GRIS, True)
        pygame.draw.line(self.ecran, (43, 66, 97), (184, 218), (816, 218), 1)
        pygame.draw.circle(self.ecran, CYAN, (LARGEUR // 2, 218), 3)
        panneau_amis = pygame.Rect(205, 389, 590, 232)
        pygame.draw.rect(self.ecran, (6, 10, 22), panneau_amis.move(0, 5),
                         border_radius=20)
        pygame.draw.rect(self.ecran, (14, 22, 42), panneau_amis, border_radius=20)
        pygame.draw.rect(self.ecran, (48, 78, 112), panneau_amis,
                         width=1, border_radius=20)
        souris = pygame.mouse.get_pos()
        etiquettes = ("CREER UN JEU", "DEFI DU JOUR", "MES PARCOURS")
        for index, (rect, etiquette) in enumerate(zip(self.boutons_menu, etiquettes)):
            dessiner_bouton(self.ecran, rect, etiquette, self.police_petite,
                            rect.collidepoint(souris), (JAUNE, ROUGE, VERT)[index])
            details = ("Cache-cache ou parcours", "Meme defi pour tous", "Jeux sauvegardes")
            texte(self.ecran, self.police_petite, details[index],
                  (rect.centerx, rect.bottom + 22), GRIS, True)
        texte(self.ecran, self.police_moyenne, "REJOINDRE UN AMI", (LARGEUR // 2, 415),
              BLANC, True)
        texte(self.ecran, self.police_petite,
              "Colle son code pour jouer au meme parcours.",
              (LARGEUR // 2, 445), GRIS, True)
        pygame.draw.rect(self.ecran, PANNEAU, self.champ_code, border_radius=13)
        pygame.draw.rect(self.ecran, (64, 86, 119), self.champ_code, width=1, border_radius=13)
        invite = self.saisie_code or ("" if self.saisie_active else "COLLE LE CODE ICI")
        couleur_invite = BLANC if self.saisie_code else GRIS
        image_invite = self.police.render(invite, True, couleur_invite)
        zone_invite = self.champ_code.inflate(-24, -10)
        if self.saisie_active:
            rect_invite = image_invite.get_rect(midleft=(zone_invite.left, zone_invite.centery))
            if image_invite.get_width() > zone_invite.width:
                rect_invite.right = zone_invite.right
        elif image_invite.get_width() <= zone_invite.width:
            rect_invite = image_invite.get_rect(center=zone_invite.center)
        else:
            rect_invite = image_invite.get_rect(midleft=(zone_invite.left, zone_invite.centery))
        ancien_clip = self.ecran.get_clip()
        self.ecran.set_clip(zone_invite)
        self.ecran.blit(image_invite, rect_invite)
        if self.saisie_active:
            curseur_x = min(zone_invite.right - 2, rect_invite.right + 3)
            pygame.draw.line(self.ecran, CYAN,
                             (curseur_x, zone_invite.top + 7),
                             (curseur_x, zone_invite.bottom - 7), 2)
        self.ecran.set_clip(ancien_clip)
        couleur_champ = CYAN if self.saisie_active else (64, 86, 119)
        pygame.draw.rect(self.ecran, couleur_champ, self.champ_code, width=2 if self.saisie_active else 1, border_radius=13)
        dessiner_bouton(self.ecran, self.bouton_saisie, "ECRIRE LE CODE",
                        self.police_petite, self.bouton_saisie.collidepoint(souris), CYAN)
        dessiner_bouton(self.ecran, self.bouton_code, "JOUER",
                        self.police, self.bouton_code.collidepoint(souris), JAUNE)
        texte(self.ecran, self.police_petite, "Clique sur ECRIRE, puis tape ou colle le code",
              (LARGEUR // 2, 606), GRIS, True)
        if self.erreur:
            texte(self.ecran, self.police_petite, self.erreur,
                  (LARGEUR // 2, 641), ROUGE, True)

    def dessiner_creation(self) -> None:
        self.dessiner_fond()
        texte(self.ecran, self.police_titre, "CREER UN JEU", (LARGEUR // 2, 150), BLANC, True)
        texte(self.ecran, self.police, "Choisis le mode de ta nouvelle partie.",
              (LARGEUR // 2, 205), GRIS, True)
        souris = pygame.mouse.get_pos()
        dessiner_bouton(self.ecran, self.boutons_creation[0], "CACHE-CACHE",
                        self.police_moyenne, self.boutons_creation[0].collidepoint(souris),
                        (101, 194, 191))
        dessiner_bouton(self.ecran, self.boutons_creation[1], "PARCOURS",
                        self.police_moyenne, self.boutons_creation[1].collidepoint(souris), CYAN)
        texte(self.ecran, self.police_petite, "Role attribue automatiquement",
              (self.boutons_creation[0].centerx, self.boutons_creation[0].bottom + 28), GRIS, True)
        texte(self.ecran, self.police_petite, "Creer un nouveau parcours",
              (self.boutons_creation[1].centerx, self.boutons_creation[1].bottom + 28), GRIS, True)
        dessiner_bouton(self.ecran, self.bouton_retour_creation, "RETOUR A L'ACCUEIL",
                        self.police_petite, self.bouton_retour_creation.collidepoint(souris), JAUNE)

    def dessiner_parcours_menu(self) -> None:
        self.dessiner_fond()
        texte(self.ecran, self.police_titre, "PARCOURS", (LARGEUR // 2, 150), BLANC, True)
        texte(self.ecran, self.police,
              "Joue les 12 niveaux de difficulte croissante ou construis le tien.",
              (LARGEUR // 2, 205), GRIS, True)
        souris = pygame.mouse.get_pos()
        dessiner_bouton(self.ecran, self.boutons_parcours[0], "JOUER LA CARTE DE BASE",
                        self.police_petite, self.boutons_parcours[0].collidepoint(souris), VERT)
        dessiner_bouton(self.ecran, self.boutons_parcours[1], "CREER UN PARCOURS",
                        self.police_petite, self.boutons_parcours[1].collidepoint(souris), CYAN)
        dessiner_bouton(self.ecran, self.bouton_retour_parcours, "RETOUR",
                        self.police_petite, self.bouton_retour_parcours.collidepoint(souris), JAUNE)

    def dessiner_bibliotheque(self) -> None:
        self.dessiner_fond()
        texte(self.ecran, self.police_titre, "MES PARCOURS", (LARGEUR // 2, 100), BLANC, True)
        texte(self.ecran, self.police_petite, "Choisis un parcours pour le reprendre. Les changements sont sauvegardes automatiquement.",
              (LARGEUR // 2, 148), GRIS, True)
        souris = pygame.mouse.get_pos()
        for chemin, rect in zip(self.parcours_disponibles, self.lignes_bibliotheque):
            try:
                nom = chemin.with_suffix(".name").read_text(encoding="utf-8").strip()
            except OSError:
                nom = ""
            dessiner_bouton(self.ecran, rect, nom or chemin.stem, self.police,
                            rect.collidepoint(souris), CYAN)
        if not self.parcours_disponibles:
            texte(self.ecran, self.police, "Aucun parcours sauvegarde pour l'instant.",
                  (LARGEUR // 2, 260), GRIS, True)
        dessiner_bouton(self.ecran, self.bouton_nouveau, "NOUVEAU PARCOURS", self.police_petite,
                        self.bouton_nouveau.collidepoint(souris), VERT)
        dessiner_bouton(self.ecran, self.bouton_retour_bibliotheque, "RETOUR AU MENU", self.police_petite,
                        self.bouton_retour_bibliotheque.collidepoint(souris), JAUNE)
        if self.erreur:
            texte(self.ecran, self.police_petite, self.erreur, (LARGEUR // 2, 680), ROUGE, True)

    def dessiner_editeur(self) -> None:
        self.dessiner_fond()
        theme = self.niveau.get("theme", "prairie")
        couleurs = {
            0: (95, 111, 140), SOL: (107, 180, 123),
            PLATEFORME: (101, 156, 222), PIC: ROUGE,
            POINT_CONTROLE: VERT, RESSORT: JAUNE, GEMME: CYAN,
            COEUR: (255, 93, 137), OUTIL_MONSTRE: (154, 91, 204),
            OUTIL_DEPART: VERT, OUTIL_ARRIVEE: JAUNE,
        }
        souris = pygame.mouse.get_pos()
        for categorie, etiquette, rect in self.categories_editeur:
            actif = categorie == self.categorie_palette
            accent = ACCENTS_THEMES[theme] if actif else GRIS
            dessiner_bouton(
                self.ecran, rect, etiquette, self.police_petite,
                rect.collidepoint(souris) or actif, accent,
            )
        for (rect, type_case) in self.palette_editeur:
            actif = self.case_selectionnee == type_case
            couleur = couleurs[type_case]
            if theme != "prairie" and type_case in (SOL, PLATEFORME):
                couleur = ACCENTS_THEMES[theme]
            pygame.draw.rect(self.ecran, PANNEAU, rect, border_radius=8)
            pygame.draw.rect(self.ecran, couleur, rect,
                             width=3 if actif else 1, border_radius=8)
            if theme != "prairie" and type_case in (SOL, PLATEFORME, PIC):
                dessiner_bloc_theme(self.ecran, rect.inflate(-7, -7), type_case, theme,
                                    materiaux=self.atmosphere.materials)
            else:
                dessiner_icone_palette(self.ecran, rect, type_case)
        etiquettes_actions = ("SAUVER", "CODE", "TEST", "ACCUEIL")
        for rect, etiquette, couleur in zip(
                self.actions_editeur, etiquettes_actions, (CYAN, JAUNE, ROUGE)):
            dessiner_bouton(self.ecran, rect, etiquette, self.police_petite,
                            rect.collidepoint(souris), couleur)

        dessiner_bouton(
            self.ecran, self.bouton_theme,
            f"THEME : {NOMS_THEMES[theme]}  >",
            self.police_petite, self.bouton_theme.collidepoint(souris),
            ACCENTS_THEMES[theme],
        )
        pygame.draw.rect(self.ecran, PANNEAU, self.champ_nom, border_radius=8)
        pygame.draw.rect(self.ecran, CYAN if self.saisie_nom_active else GRIS,
                         self.champ_nom, width=2 if self.saisie_nom_active else 1, border_radius=8)
        etiquette_nom = f"Nom : {self.nom_parcours}" + ("_" if self.saisie_nom_active else "")
        texte(self.ecran, self.police_petite, etiquette_nom, self.champ_nom.center, BLANC, True)
        zone_carte = pygame.Rect(24, 112, 952, 528)
        if theme == "prairie":
            pygame.draw.rect(self.ecran, (17, 24, 43), zone_carte, border_radius=8)
        else:
            dessiner_arriere_plan_theme(
                self.ecran, theme, self.camera_editeur * .16, zone_carte
            )
        cases = self.niveau["tiles"]
        debut_colonne = max(0, self.camera_editeur // TAILLE_CASE)
        fin_colonne = min(COLONNES_NIVEAU,
                          (self.camera_editeur + LARGEUR) // TAILLE_CASE + 2)
        for ligne in range(LIGNES_NIVEAU):
            for colonne in range(debut_colonne, fin_colonne):
                x = 24 + colonne * TAILLE_CASE - self.camera_editeur
                y = int(DEBUT_CARTE.y) + ligne * TAILLE_CASE
                rect = pygame.Rect(x, y, TAILLE_CASE, TAILLE_CASE)
                pygame.draw.rect(self.ecran, (34, 45, 67), rect, width=1)
                type_case = cases[ligne][colonne]
                if theme != "prairie" and type_case in (SOL, PLATEFORME, PIC):
                    dessiner_bloc_theme(self.ecran, rect.inflate(-2, -2), type_case,
                                        theme, colonne + ligne * 3, self.atmosphere.materials)
                elif type_case == SOL:
                    pygame.draw.rect(self.ecran, (82, 177, 122), rect.inflate(-3, -3),
                                     border_radius=5)
                    pygame.draw.rect(self.ecran, (117, 99, 81),
                                     (x + 3, y + 15, TAILLE_CASE - 6, TAILLE_CASE - 18),
                                     border_radius=4)
                    pygame.draw.line(self.ecran, (173, 145, 98),
                                     (x + 4, y + 15), (x + TAILLE_CASE - 4, y + 15), 3)
                    pygame.draw.line(self.ecran, (84, 68, 53),
                                     (x + 6, y + 31), (x + TAILLE_CASE - 6, y + 31), 1)
                    for detail in range(3):
                        pierre_x = x + 8 + ((detail * 13 + colonne * 5) % 28)
                        pierre_y = y + 24 + ((detail * 7 + ligne * 3) % 14)
                        pygame.draw.ellipse(self.ecran, (178, 142, 100),
                                            (pierre_x, pierre_y, 5, 3))
                    for detail in range(4):
                        brin_x = x + 6 + ((detail * 10 + colonne * 7) % 35)
                        pygame.draw.line(self.ecran, (174, 224, 134),
                                         (brin_x, y + 16), (brin_x - 2, y + 10), 2)
                elif type_case == PLATEFORME:
                    pygame.draw.rect(self.ecran, (75, 48, 32),
                                     (x + 2, y + 14, TAILLE_CASE - 4, 16),
                                     border_radius=4)
                    pygame.draw.rect(self.ecran, (150, 96, 51),
                                     (x + 3, y + 12, TAILLE_CASE - 6, 10),
                                     border_radius=4)
                    pygame.draw.line(self.ecran, (228, 180, 106),
                                     (x + 6, y + 14), (x + TAILLE_CASE - 6, y + 14), 2)
                    pygame.draw.line(self.ecran, (93, 56, 34),
                                     (x + 6, y + 23), (x + TAILLE_CASE - 6, y + 23), 2)
                    pygame.draw.rect(self.ecran, (110, 71, 42),
                                     (x + 7, y + 29, 6, 5), border_radius=2)
                    pygame.draw.rect(self.ecran, (110, 71, 42),
                                     (x + TAILLE_CASE - 13, y + 29, 6, 5), border_radius=2)
                    pygame.draw.circle(self.ecran, (248, 210, 147), (x + 8, y + 19), 2)
                    pygame.draw.circle(self.ecran, (248, 210, 147),
                                       (x + TAILLE_CASE - 8, y + 19), 2)
                elif type_case in (PIC, POINT_CONTROLE, RESSORT, GEMME):
                    dessiner_icone_palette(self.ecran, rect.inflate(-2, -2), type_case)
                elif type_case == COEUR:
                    dessiner_coeur(self.ecran, rect.center, 22)
        for colonne, ligne in self.niveau.get("monstres", []):
            x = 24 + colonne * TAILLE_CASE - self.camera_editeur + 7
            ligne_sol = ligne_support_monstre(self.niveau, colonne, ligne)
            y = (int(DEBUT_CARTE.y) + ligne_sol * TAILLE_CASE - 34
                 if ligne_sol is not None and ligne_sol > 0
                 else int(DEBUT_CARTE.y) + ligne * TAILLE_CASE + 8)
            dessiner_monstre(self.ecran, pygame.Rect(x, y, 34, 34))
        for nom, outil in (("start", OUTIL_DEPART), ("goal", OUTIL_ARRIVEE)):
            colonne, ligne = self.niveau[nom]
            x = 24 + colonne * TAILLE_CASE - self.camera_editeur + TAILLE_CASE // 2
            y = int(DEBUT_CARTE.y) + ligne * TAILLE_CASE + TAILLE_CASE // 2
            icone = pygame.Rect(round(x - 23), y - 21, 46, 42)
            dessiner_icone_palette(self.ecran, icone, outil)
        if self.erreur:
            texte(self.ecran, self.police_petite, self.erreur,
                  (LARGEUR // 2, 690),
                  ROUGE if self.erreur.startswith("Impossible") or
                  self.erreur.startswith("Brouillon impossible") else VERT, True)
        else:
            texte(
                self.ecran, self.police_petite,
                "Molette ou A/D : defiler | Outils 0-9, M | Ctrl+Z/Y",
                (LARGEUR // 2, 690), GRIS, True,
            )

    def dessiner_partage(self) -> None:
        self.dessiner_fond()
        texte(self.ecran, self.police_titre, "TON PARCOURS EST PRET !",
              (LARGEUR // 2, 112), CYAN, True)
        texte(self.ecran, self.police, "Le code contient toute ta carte : copie-le et envoie-le a tes amis.",
              (LARGEUR // 2, 180), GRIS, True)
        max_par_ligne = 75
        lignes = [self.partage_code[index:index + max_par_ligne]
                  for index in range(0, len(self.partage_code), max_par_ligne)]
        hauteur_depart = 240 - max(0, len(lignes) - 2) * 10
        for index, ligne in enumerate(lignes[:8]):
            texte(self.ecran, self.police_petite, ligne,
                  (LARGEUR // 2, hauteur_depart + index * 27), BLANC, True)
        souris = pygame.mouse.get_pos()
        dessiner_bouton(self.ecran, self.bouton_copier, "COPIER LE CODE",
                        self.police, self.bouton_copier.collidepoint(souris))
        dessiner_bouton(self.ecran, self.bouton_partage_test, "JOUER LE PARCOURS",
                        self.police_petite,
                        self.bouton_partage_test.collidepoint(souris), JAUNE)
        dessiner_bouton(self.ecran, self.bouton_partage_editer, "RETOURNER A L'EDITEUR",
                        self.police_petite,
                        self.bouton_partage_editer.collidepoint(souris), ROUGE)
        texte(self.ecran, self.police_petite, self.message_partage,
              (LARGEUR // 2, 490), VERT, True)
        if self.erreur.startswith("Impossible"):
            texte(self.ecran, self.police_petite, self.erreur,
                  (LARGEUR // 2, 473), ROUGE, True)

    def dessiner_jeu(self) -> None:
        self.dessiner_fond()
        self.ecran.blit(self.voile_arene, (24, 98))
        pygame.draw.rect(self.ecran, (68, 99, 139), (24, 98, LARGEUR - 48, HAUTEUR - 122),
                         width=1, border_radius=22)
        for index, x in enumerate(range(55, LARGEUR - 30, 40)):
            teinte = (34, 51, 80) if index % 4 else (43, 66, 101)
            pygame.draw.line(self.ecran, teinte, (x, 100), (x, HAUTEUR - 25))
        for index, y in enumerate(range(130, HAUTEUR - 20, 40)):
            teinte = (34, 51, 80) if index % 4 else (43, 66, 101)
            pygame.draw.line(self.ecran, teinte, (25, y), (LARGEUR - 25, y))
        pygame.draw.rect(self.ecran, (13, 21, 40), (32, 22, 936, 72), border_radius=16)
        pygame.draw.rect(self.ecran, (47, 69, 101), (32, 22, 936, 72),
                         width=1, border_radius=16)
        for x in (160, 414, 792):
            pygame.draw.line(self.ecran, (47, 65, 92), (x, 34), (x, 82), 1)

        temps_restant = max(0, int(DUREE_PARTIE - self.temps + 0.99))
        texte(self.ecran, self.police_moyenne, f"{temps_restant:02d}s",
              (65, 47), JAUNE, True)
        texte(self.ecran, self.police, f"SCORE  {self.score:05d}", (180, 38), BLANC)
        texte(self.ecran, self.police_petite, f"FRAGMENTS  {self.fragments}", (181, 69), CYAN)
        texte(self.ecran, self.police_petite, f"CODE  {self.code}", (LARGEUR // 2, 49), CYAN, True)
        texte(self.ecran, self.police_petite, "P / ECHAP : pause", (LARGEUR - 170, 52), GRIS)

        for index in range(3):
            couleur = ROUGE if index < self.vies else (62, 68, 86)
            pygame.draw.circle(self.ecran, couleur, (LARGEUR - 125 + index * 30, 92), 9)
        temps_effets = pygame.time.get_ticks() / 1000.0
        for index, fragment in enumerate(self.fragments_actifs):
            pulsation = 0.5 + 0.5 * math.sin(temps_effets * 5 + index * 2.1)
            rayon = round(18 + pulsation * 4)
            pygame.draw.circle(self.ecran, (18, 75, 94), fragment, rayon + 7)
            pygame.draw.circle(self.ecran, (44, 159, 172), fragment, rayon + 3, 1)
            pygame.draw.circle(self.ecran, (25, 100, 112), fragment, rayon)
            pygame.draw.circle(self.ecran, CYAN, fragment, 10)
            pygame.draw.circle(self.ecran, BLANC, fragment, 4)
        for projectile in self.projectiles:
            position = projectile["position"]
            rayon = projectile["rayon"]
            centre = (round(position.x), round(position.y))
            if projectile["delai"] > 0:
                progression = 1 - projectile["delai"] / 0.34
                pygame.draw.circle(self.ecran, (255, 185, 108), centre,
                                   round(9 + progression * 8), 2)
                pygame.draw.circle(self.ecran, (255, 229, 169), centre, 3)
                continue
            vitesse = projectile["vitesse"]
            if vitesse.length_squared():
                arriere = pygame.Vector2(centre) - vitesse.normalize() * (rayon + 7)
                pygame.draw.line(self.ecran, (109, 52, 85), centre,
                                 (round(arriere.x), round(arriere.y)), max(2, rayon // 2))
            if projectile["type"] == "eclat":
                pygame.draw.polygon(self.ecran, (90, 48, 126), [
                    (centre[0], centre[1] - rayon - 4),
                    (centre[0] + rayon, centre[1]),
                    (centre[0], centre[1] + rayon + 4),
                    (centre[0] - rayon, centre[1]),
                ])
                pygame.draw.polygon(self.ecran, (220, 151, 255), [
                    (centre[0], centre[1] - rayon),
                    (centre[0] + rayon // 2, centre[1]),
                    (centre[0], centre[1] + rayon),
                    (centre[0] - rayon // 2, centre[1]),
                ])
            elif projectile["type"] == "spirale":
                pygame.draw.circle(self.ecran, (112, 56, 33), centre, rayon + 5, 3)
                pygame.draw.circle(self.ecran, (255, 157, 75), centre, rayon)
                angle = projectile["age"] * 5
                eclat = pygame.Vector2(rayon, 0).rotate_rad(angle)
                pygame.draw.circle(self.ecran, (255, 239, 184),
                                   (round(centre[0] + eclat.x), round(centre[1] + eclat.y)), 3)
            else:
                pygame.draw.circle(self.ecran, (90, 34, 65), centre, rayon + 5)
                pygame.draw.circle(self.ecran, ROUGE, centre, rayon)
                pygame.draw.circle(self.ecran, (255, 207, 192), centre,
                                   max(3, rayon // 3))
        for particule in self.particules:
            position = particule["position"]
            pygame.draw.circle(self.ecran, particule["couleur"],
                               (round(position.x), round(position.y)), 3)

        visible = self.invulnerable <= 0 or int(self.temps * 12) % 2 == 0
        if visible:
            dessiner_personnage_arcade(
                self.ecran,
                (round(self.joueur.x), round(self.joueur.y)),
                self.temps_animation,
                self.direction_personnage,
                self.duree_esquive > 0,
            )
        texte(self.ecran, self.police_petite, "ESQUIVE [ESPACE]", (58, 648), GRIS)
        pygame.draw.rect(self.ecran, (37, 48, 70), (222, 649, 170, 10), border_radius=5)
        recharge = 1 - self.recharge_esquive / 1.05
        largeur_barre = round(166 * max(0, min(1, recharge)))
        couleur_barre = CYAN if self.recharge_esquive <= 0 else JAUNE
        if largeur_barre:
            pygame.draw.rect(self.ecran, couleur_barre,
                             (224, 651, largeur_barre, 6), border_radius=3)
        etiquette_esquive = "PRETE" if self.recharge_esquive <= 0 else f"{self.recharge_esquive:0.1f}s"
        texte(self.ecran, self.police_petite, etiquette_esquive, (405, 644), couleur_barre)
        if self.combo > 1:
            texte(self.ecran, self.police_petite, f"COMBO x{self.combo}",
                  (510, 73), JAUNE)
        if self.paused:
            voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            voile.fill((5, 9, 20, 205))
            self.ecran.blit(voile, (0, 0))
            texte(self.ecran, self.police_titre, "PAUSE", (LARGEUR // 2, 310), BLANC, True)
            texte(self.ecran, self.police, "P ou ECHAP pour reprendre",
                  (LARGEUR // 2, 380), GRIS, True)

    def dessiner_paysage_parcours(self) -> None:
        luminosite = self.atmosphere.clock.colors()[4]
        facteur = .72 + luminosite * .34

        def teinter(couleur: tuple[int, int, int]) -> tuple[int, int, int]:
            return tuple(max(0, min(255, round(canal * facteur))) for canal in couleur)

        couches = (
            (566, 184, .12, (69, 107, 178), 112),
            (600, 139, .25, (53, 148, 157), 67),
            (630, 108, .42, (66, 151, 105), 39),
        )
        for index_couche, (base_y, largeur, parallaxe, couleur_base, relief) in enumerate(couches):
            decalage = self.camera_parcours * parallaxe
            debut = math.floor(decalage / largeur) - 2
            nombre = LARGEUR // largeur + 6
            couleur = teinter(couleur_base)
            eclat = teinter(tuple(min(255, canal + 34) for canal in couleur_base))
            ombre = teinter(tuple(max(0, canal - 25) for canal in couleur_base))
            points = []
            facettes = []
            for montagne in range(debut, debut + nombre):
                gauche = round(montagne * largeur - decalage)
                pointe_x = gauche + largeur // 2
                droite = gauche + largeur
                hauteur = relief // 2 + (abs(montagne * 37 + index_couche * 19) % relief)
                pointe_y = base_y - hauteur
                points.extend(((gauche, base_y), (pointe_x, pointe_y), (droite, base_y)))
                facettes.append((gauche, pointe_x, droite, pointe_y))
            points.extend(((LARGEUR + 40, HAUTEUR), (-40, HAUTEUR)))
            pygame.draw.polygon(self.ecran, couleur, points)
            for gauche, pointe_x, droite, pointe_y in facettes:
                pygame.draw.polygon(self.ecran, eclat, [
                    (gauche, base_y), (pointe_x, pointe_y), (pointe_x, base_y),
                ])
                pygame.draw.polygon(self.ecran, ombre, [
                    (pointe_x, base_y), (pointe_x, pointe_y), (droite, base_y),
                ])
                if index_couche == 0 and pointe_y < 438:
                    pygame.draw.polygon(self.ecran, teinter((210, 227, 244)), [
                        (pointe_x - 10, pointe_y + 17),
                        (pointe_x, pointe_y),
                        (pointe_x + 12, pointe_y + 19),
                        (pointe_x + 3, pointe_y + 15),
                    ])

        fleurs = ((255, 112, 154), (255, 205, 91), (183, 143, 255),
                  (108, 230, 205), (255, 151, 96))
        for index in range(13):
            monde_x = index * 151 + 58
            x = round(monde_x - self.camera_parcours * .68)
            y = 579 + (index * 31 % 48)
            couleur = fleurs[index % len(fleurs)]
            pygame.draw.line(self.ecran, teinter((54, 139, 86)), (x, y + 8), (x, y), 2)
            pygame.draw.ellipse(self.ecran, teinter((84, 184, 98)), (x - 5, y + 2, 6, 3))
            pygame.draw.ellipse(self.ecran, teinter((84, 184, 98)), (x, y + 4, 6, 3))
            for petale in range(5):
                angle = petale * math.tau / 5
                px = x + round(math.cos(angle) * 4)
                py = y + round(math.sin(angle) * 4)
                pygame.draw.circle(self.ecran, teinter(couleur), (px, py), 2)
            pygame.draw.circle(self.ecran, teinter((255, 235, 153)), (x, y), 2)

    def dessiner_nuages_parcours(self) -> None:
        palette = (
            ((255, 208, 170), (255, 239, 215)),
            ((167, 220, 255), (224, 247, 255)),
            ((213, 187, 255), (243, 230, 255)),
            ((164, 235, 207), (226, 255, 238)),
            ((255, 185, 194), (255, 230, 230)),
        )
        luminosite = self.atmosphere.clock.colors()[4]
        facteur = .76 + luminosite * .3
        for index in range(7):
            x = round((index * 218 - self.camera_parcours * .14
                       + self.temps_parcours * 5) % (LARGEUR + 230) - 115)
            y = 146 + (index % 3) * 61
            base, lumiere = palette[index % len(palette)]
            base = tuple(min(255, round(canal * facteur)) for canal in base)
            lumiere = tuple(min(255, round(canal * facteur)) for canal in lumiere)
            pygame.draw.ellipse(self.ecran, (67, 75, 107), (x - 5, y + 7, 105, 23))
            pygame.draw.ellipse(self.ecran, base, (x, y, 62, 25))
            pygame.draw.ellipse(self.ecran, lumiere, (x + 20, y - 10, 39, 34))
            pygame.draw.ellipse(self.ecran, base, (x + 43, y - 3, 46, 28))
            pygame.draw.line(self.ecran, lumiere, (x + 12, y + 5),
                             (x + 34, y + 2), 2)

    def dessiner_parcours(self) -> None:
        theme = self.niveau.get("theme", "prairie")
        if theme == "prairie":
            self.atmosphere.draw_platform_sky(self.ecran, int(HAUTEUR * .82))
            self.ecran.blit(self.voile_parcours, (24, 100))
            self.ecran.blit(self.voile_couleur_parcours, (0, 0))
            couleur_cadre = (61, 79, 106)
            self.atmosphere.draw_platform_backdrop(self.ecran, self.camera_parcours)
            self.dessiner_paysage_parcours()
            self.dessiner_nuages_parcours()
        else:
            dessiner_arriere_plan_theme(
                self.ecran, theme, self.camera_parcours * .16
            )
            self.ecran.blit(self.voile_parcours, (24, 100))
            couleur_cadre = ACCENTS_THEMES[theme]
        pygame.draw.rect(self.ecran, couleur_cadre,
                         (24, 100, LARGEUR - 48, HAUTEUR - 124),
                         width=1, border_radius=18)
        for ligne in range(LIGNES_NIVEAU):
            for colonne, type_case in enumerate(self.niveau["tiles"][ligne]):
                if (type_case == 0
                        or (type_case == GEMME and (colonne, ligne) in self.gemmes_collectees)
                        or (type_case == COEUR and (colonne, ligne) not in self.coeurs_restants)):
                    continue
                x = round(24 + colonne * TAILLE_CASE - self.camera_parcours)
                y = int(DEBUT_CARTE.y) + ligne * TAILLE_CASE
                if x < -TAILLE_CASE or x > LARGEUR:
                    continue
                rect = pygame.Rect(x, y, TAILLE_CASE, TAILLE_CASE)
                if theme != "prairie" and type_case in (SOL, PLATEFORME, PIC):
                    if type_case == SOL:
                        bloc = rect.inflate(-2, -2)
                    elif type_case == PLATEFORME:
                        bloc = pygame.Rect(x + 2, y + 8, TAILLE_CASE - 4, 25)
                    else:
                        bloc = rect
                    dessiner_bloc_theme(self.ecran, bloc, type_case, theme,
                                        colonne + ligne * 3,
                                        self.atmosphere.materials)
                elif type_case == SOL:
                    self.atmosphere.materials.draw_platform(
                        self.ecran, rect.inflate(-2, -2), "grass", self.atmosphere.seed
                    )
                    pygame.draw.rect(self.ecran, (117, 99, 81),
                                     (x + 3, y + 19, TAILLE_CASE - 6, TAILLE_CASE - 21),
                                     border_radius=4)
                    pygame.draw.line(self.ecran, (172, 143, 99),
                                     (x + 4, y + 19), (x + TAILLE_CASE - 4, y + 19), 3)
                    pygame.draw.line(self.ecran, (83, 71, 66),
                                     (x + 6, y + 31), (x + TAILLE_CASE - 6, y + 31), 1)
                    for detail in range(5):
                        brin_x = x + 5 + ((detail * 9 + colonne * 7) % 37)
                        pygame.draw.line(self.ecran, (157, 205, 116),
                                         (brin_x, y + 18), (brin_x - 2, y + 12), 1)
                    for detail in range(4):
                        pierre_x = x + 7 + ((detail * 11 + colonne * 5) % 31)
                        pierre_y = y + 26 + ((detail * 7 + ligne * 3) % 14)
                        pygame.draw.ellipse(self.ecran, (146, 123, 99),
                                            (pierre_x, pierre_y, 4, 2))
                elif type_case == PLATEFORME:
                    self.atmosphere.materials.draw_platform(
                        self.ecran, pygame.Rect(x + 2, y + 13, TAILLE_CASE - 4, 12),
                        "wood", self.atmosphere.seed,
                    )
                    pygame.draw.line(self.ecran, (105, 69, 42),
                                     (x + 7, y + 19), (x + TAILLE_CASE - 7, y + 19), 1)
                    pygame.draw.line(self.ecran, (223, 177, 104),
                                     (x + 9, y + 15), (x + TAILLE_CASE - 9, y + 15), 1)
                    pygame.draw.circle(self.ecran, (226, 193, 135), (x + 8, y + 21), 2)
                    pygame.draw.circle(self.ecran, (226, 193, 135), (x + TAILLE_CASE - 8, y + 21), 2)
                elif type_case == PIC:
                    pygame.draw.polygon(self.ecran, ROUGE, [
                        (x + 4, y + TAILLE_CASE - 3),
                        (x + TAILLE_CASE // 2, y + 6),
                        (x + TAILLE_CASE - 4, y + TAILLE_CASE - 3),
                    ])
                elif type_case == POINT_CONTROLE:
                    point = (colonne, ligne)
                    couleur = VERT if point in self.controles_actives else (82, 117, 103)
                    pygame.draw.circle(self.ecran, couleur, (x + 24, y + 24), 15)
                    pygame.draw.circle(self.ecran, BLANC, (x + 24, y + 24), 7)
                    pygame.draw.line(self.ecran, couleur, (x + 24, y + 37),
                                     (x + 24, y + 47), 3)
                elif type_case == RESSORT:
                    pygame.draw.rect(self.ecran, (164, 107, 42),
                                     (x + 7, y + 30, TAILLE_CASE - 14, 12),
                                     border_radius=4)
                    pygame.draw.line(self.ecran, JAUNE, (x + 12, y + 28),
                                     (x + 22, y + 18), 4)
                    pygame.draw.line(self.ecran, JAUNE, (x + 22, y + 18),
                                     (x + 32, y + 28), 4)
                elif type_case == GEMME:
                    flottement = round(pygame.time.get_ticks() / 180) % 5
                    pygame.draw.polygon(self.ecran, CYAN, [
                        (x + 24, y + 7 + flottement), (x + 40, y + 24),
                        (x + 24, y + 41 - flottement), (x + 8, y + 24),
                    ])
                    pygame.draw.polygon(self.ecran, BLANC, [
                        (x + 24, y + 12 + flottement), (x + 34, y + 24),
                        (x + 24, y + 36 - flottement), (x + 14, y + 24),
                    ], 1)
                elif type_case == COEUR:
                    dessiner_coeur(self.ecran, (x + 24, y + 24), 22)
        for monstre in self.monstres:
            x = round(monstre["x"] - self.camera_parcours)
            y = round(monstre["y"])
            if -34 <= x <= LARGEUR:
                dessiner_monstre(self.ecran, pygame.Rect(x, y, 34, 34))
        depart = self.niveau["start"]
        arrivee = self.niveau["goal"]
        depart_x = round(24 + depart[0] * TAILLE_CASE - self.camera_parcours + TAILLE_CASE // 2)
        depart_y = int(DEBUT_CARTE.y) + depart[1] * TAILLE_CASE + TAILLE_CASE // 2
        pygame.draw.circle(self.ecran, VERT, (depart_x, depart_y), 13)
        texte(self.ecran, self.police_petite, "D", (depart_x, depart_y), FOND, True)
        arrivee_x = round(24 + arrivee[0] * TAILLE_CASE - self.camera_parcours + TAILLE_CASE // 2)
        arrivee_base = int(DEBUT_CARTE.y) + arrivee[1] * TAILLE_CASE + TAILLE_CASE - 2
        pygame.draw.ellipse(self.ecran, (16, 24, 35),
                            (arrivee_x - 13, arrivee_base - 1, 26, 7))
        pygame.draw.line(self.ecran, (218, 224, 221),
                         (arrivee_x, arrivee_base - 3), (arrivee_x, arrivee_base - 49), 4)
        pygame.draw.circle(self.ecran, JAUNE, (arrivee_x, arrivee_base - 50), 4)
        pygame.draw.polygon(self.ecran, (238, 174, 66), [
            (arrivee_x + 2, arrivee_base - 46),
            (arrivee_x + 26, arrivee_base - 39),
            (arrivee_x + 3, arrivee_base - 29),
        ])
        pygame.draw.line(self.ecran, (255, 225, 142),
                         (arrivee_x + 4, arrivee_base - 43),
                         (arrivee_x + 19, arrivee_base - 39), 2)
        self.atmosphere.draw_vignette(self.ecran, .24)
        titre = (f"CARTE DE BASE - NIVEAU {self.numero_niveau_base}/{NIVEAUX_CARTE_BASE}"
                 if self.campagne_base else f"PARCOURS - {NOMS_THEMES[theme]}")
        texte(self.ecran, self.police, titre, (38, 40), BLANC)
        texte(self.ecran, self.police_petite, f"Temps : {self.temps_parcours:0.1f}s",
              (38, 73), JAUNE)
        texte(self.ecran, self.police_petite,
              f"Gemmes {self.gemmes_parcours}/{self.total_gemmes}",
              (300, 50), CYAN)
        texte(self.ecran, self.police_petite, f"Score {self.score_parcours}",
              (300, 77), BLANC)
        if self.record:
            texte(self.ecran, self.police_petite,
                  f"Record {self.record / 1000:0.1f}s", (475, 50), JAUNE)
        etat_meteo = {"clear": "SEC", "dust": "POUSSIERE",
                      "rain": "PLUIE", "snow": "NEIGE"}.get(
                          self.atmosphere.weather, "SEC"
                      )
        texte(self.ecran, self.police_petite,
              f"{self.atmosphere.clock.phase_name} · {etat_meteo}",
              (690, 50), (171, 203, 224))
        for index in range(5):
            pygame.draw.circle(self.ecran, ROUGE if index < self.vies else (62, 68, 86),
                               (LARGEUR - 165 + index * 27, 85), 8)
        for particule in self.particules:
            position = particule["position"]
            pygame.draw.circle(self.ecran, particule["couleur"],
                               (round(position.x - self.camera_parcours),
                                round(position.y)), 3)
        if self.invulnerable <= 0 or int(self.temps_parcours * 12) % 2 == 0:
            joueur_ecran = self.rect_joueur.move(-round(self.camera_parcours), 0)
            dessiner_personnage_plateforme(
                self.ecran, joueur_ecran, self.temps_parcours, self.vitesse_x
            )
        if self.paused:
            voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            voile.fill((5, 9, 20, 205))
            self.ecran.blit(voile, (0, 0))
            texte(self.ecran, self.police_titre, "PAUSE", (LARGEUR // 2, 310), BLANC, True)
            texte(self.ecran, self.police, "P ou ECHAP pour reprendre",
                  (LARGEUR // 2, 380), GRIS, True)
        texte(self.ecran, self.police_petite,
              "ZQSD / fleches : bouger   |   Espace : sauter   |   Maj : courir   |   Echap : pause",
              (LARGEUR // 2, 674), GRIS, True)

    def dessiner_resultat(self) -> None:
        self.dessiner_fond()
        if self.type_partie == "parcours":
            if self.campagne_base:
                if self.gagne and self.numero_niveau_base == NIVEAUX_CARTE_BASE:
                    titre = "CAMPAGNE TERMINEE !"
                elif self.gagne:
                    titre = f"NIVEAU {self.numero_niveau_base} TERMINE !"
                else:
                    titre = f"REESSAIE LE NIVEAU {self.numero_niveau_base}"
            else:
                titre = "PARCOURS TERMINE !" if self.gagne else "REESSAIE LE PARCOURS"
            couleur = CYAN if self.gagne else ROUGE
            texte(self.ecran, self.police_titre, titre,
                  (LARGEUR // 2, 190), couleur, True)
            temps = f"Temps : {self.temps_parcours:0.1f} secondes"
            texte(self.ecran, self.police_moyenne, temps,
                  (LARGEUR // 2, 282), BLANC, True)
            if self.campagne_base:
                texte(self.ecran, self.police,
                      f"Niveau {self.numero_niveau_base}/{NIVEAUX_CARTE_BASE} - difficulte {self.numero_niveau_base}",
                      (LARGEUR // 2, 344), CYAN, True)
            else:
                texte(self.ecran, self.police, f"Code du parcours : {self.code[:30]}",
                      (LARGEUR // 2, 344), CYAN, True)
            if self.gagne:
                texte(self.ecran, self.police_moyenne,
                      f"Score {self.score_parcours}  |  Gemmes {self.gemmes_parcours}/{self.total_gemmes}",
                      (LARGEUR // 2, 397), JAUNE, True)
                record = self.record / 1000 if self.record else self.temps_parcours
                texte(self.ecran, self.police,
                      f"Meilleur temps local : {record:0.2f}s",
                      (LARGEUR // 2, 428), GRIS, True)
                if self.nouveau_record:
                    texte(self.ecran, self.police, "NOUVEAU RECORD !",
                          (LARGEUR // 2, 460), JAUNE, True)
            self.bouton_rejouer = pygame.Rect(300, 485, 190, 58)
            self.bouton_menu = pygame.Rect(510, 485, 190, 58)
            souris = pygame.mouse.get_pos()
            if self.campagne_base and self.gagne:
                action = ("NIVEAU SUIVANT" if self.numero_niveau_base < NIVEAUX_CARTE_BASE
                          else "RECOMMENCER")
            else:
                action = "REJOUER"
            dessiner_bouton(self.ecran, self.bouton_rejouer, action,
                            self.police_petite, self.bouton_rejouer.collidepoint(souris))
            etiquette_retour = "RETOUR EDITEUR" if self.retour_resultat == "editeur" else "MENU"
            dessiner_bouton(self.ecran, self.bouton_menu, etiquette_retour,
                            self.police_petite, self.bouton_menu.collidepoint(souris), JAUNE)
            aide = ("Entree : continuer   |   M : retour"
                    if self.campagne_base and self.gagne
                    else "Entree : rejouer   |   M : retour")
            texte(self.ecran, self.police_petite, aide,
                  (LARGEUR // 2, 545), GRIS, True)
            if self.message_sauvegarde:
                texte(self.ecran, self.police_petite, self.message_sauvegarde,
                      (LARGEUR // 2, 584), ROUGE, True)
            return
        titre = "DEFI REUSSI !" if self.gagne else "PLUS DE VIES !"
        couleur = CYAN if self.gagne else ROUGE
        texte(self.ecran, self.police_titre, titre, (LARGEUR // 2, 190), couleur, True)
        texte(self.ecran, self.police_moyenne, f"{self.score} points",
              (LARGEUR // 2, 282), BLANC, True)
        texte(self.ecran, self.police, f"Code a partager : {self.code}",
              (LARGEUR // 2, 344), CYAN, True)
        texte(self.ecran, self.police, f"Record local sur ce code : {self.record}",
              (LARGEUR // 2, 388), GRIS, True)
        self.bouton_rejouer = pygame.Rect(300, 485, 190, 58)
        self.bouton_menu = pygame.Rect(510, 485, 190, 58)
        souris = pygame.mouse.get_pos()
        dessiner_bouton(self.ecran, self.bouton_copier_code, "COPIER LE CODE POUR UN AMI",
                        self.police_petite, self.bouton_copier_code.collidepoint(souris), CYAN)
        dessiner_bouton(self.ecran, self.bouton_rejouer, "REJOUER LE CODE",
                        self.police_petite, self.bouton_rejouer.collidepoint(souris))
        dessiner_bouton(self.ecran, self.bouton_menu, "MENU / NOUVEAU",
                        self.police_petite, self.bouton_menu.collidepoint(souris), JAUNE)
        texte(self.ecran, self.police_petite, "Entree : rejouer  |  N : nouveau code  |  C : copier  |  M : menu",
              (LARGEUR // 2, 557), GRIS, True)
        if self.message_partage:
            texte(self.ecran, self.police_petite, self.message_partage,
                  (LARGEUR // 2, 592), CYAN, True)
        if self.message_sauvegarde:
            texte(self.ecran, self.police_petite, self.message_sauvegarde,
                  (LARGEUR // 2, 622), ROUGE, True)

    def executer(self) -> None:
        en_cours = True
        while en_cours:
            dt = min(self.horloge.tick(60) / 1000.0, 0.04)
            for evenement in pygame.event.get():
                en_cours = self.evenement(evenement) and en_cours
            if self.etat == "jeu":
                self.mettre_a_jour(dt, pygame.key.get_pressed())
                self.dessiner_jeu()
            elif self.etat == "parcours":
                self.mettre_a_jour_parcours(dt, pygame.key.get_pressed())
                self.dessiner_parcours()
            elif self.etat == "resultat":
                self.dessiner_resultat()
            elif self.etat == "editeur":
                self.dessiner_editeur()
            elif self.etat == "bibliotheque":
                self.dessiner_bibliotheque()
            elif self.etat == "creation":
                self.dessiner_creation()
            elif self.etat == "parcours_menu":
                self.dessiner_parcours_menu()
            elif self.etat == "partage":
                self.dessiner_partage()
            else:
                self.dessiner_menu()
            self.dessiner_commandes_tactiles()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    JeuDefi().executer() 