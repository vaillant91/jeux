"""Mode cache-cache en vue a la troisieme personne, rendu 3D par raycasting."""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import pygame

from camera_realiste import FootstepClock, InertialMotion, ThirdPersonCamera
from perception_ia import AcousticField, BotDecisionModel, SensoryAgent, VisionModel
from realisme_visuel import GameAtmosphere

LARGEUR, HAUTEUR = 1000, 700
TAILLE = 25


def creer_grande_carte() -> list[str]:
    """Carte interieure de plusieurs quartiers, salles et cachettes."""
    grille = [["." for _ in range(TAILLE)] for _ in range(TAILLE)]
    for i in range(TAILLE):
        grille[0][i] = grille[-1][i] = "#"
        grille[i][0] = grille[i][-1] = "#"
    # Cloisons decoupees avec des passages pour former des pieces connectees.
    for x in (5, 10, 15, 20):
        for y in range(1, TAILLE - 1):
            grille[y][x] = "#"
        for y in (3, 8, 13, 18, 22):
            grille[y][x] = "."
    for y in (5, 10, 15, 20):
        for x in range(1, TAILLE - 1):
            grille[y][x] = "#"
        for x in (3, 8, 13, 18, 22):
            grille[y][x] = "."
    for x, y in ((2, 2), (7, 2), (12, 2), (17, 2), (22, 2),
                 (2, 7), (7, 7), (12, 7), (17, 7), (22, 7),
                 (2, 12), (7, 12), (12, 12), (17, 12), (22, 12),
                 (2, 17), (7, 17), (12, 17), (17, 17), (22, 17),
                 (2, 22), (7, 22), (12, 22), (17, 22), (22, 22)):
        grille[y][x] = "H"
    grille[1][1] = "."
    return ["".join(ligne) for ligne in grille]


CARTE_BASE = creer_grande_carte()


def fichier_carte() -> Path:
    return Path.home() / "AppData" / "Local" / "DefiTonPote" / "cache-cache.json"


class CacheCache3D:
    def __init__(self, ecran: pygame.Surface) -> None:
        self.ecran = ecran
        self.appareil_tactile = self.detecter_tactile()
        self.touches_tactiles: dict[tuple[int, int], str] = {}
        self.derniere_position_tactile: dict[tuple[int, int], tuple[int, int]] = {}
        self.horloge = pygame.time.Clock()
        self.police = pygame.font.Font(None, 30)
        self.petite = pygame.font.Font(None, 22)
        self.titre = pygame.font.Font(None, 64)
        self.chemin = fichier_carte()
        self.carte = [list(ligne) for ligne in CARTE_BASE]
        self.spawn = (1.5, 1.5)
        self.joueurs = []
        self.cache = False
        self.temps = 75.0
        self.etat = "menu"
        self.resultat = ""
        self.outil = "#"
        self.boutons = [pygame.Rect(310, 195 + i * 82, 380, 58) for i in range(4)]
        self.grille = pygame.Rect(70, 125, 520, 520)
        self.boutons_outils = [
            (pygame.Rect(650, 200 + index * 60, 285, 48), outil, nom)
            for index, (outil, nom) in enumerate((("#", "MUR"), (".", "SOL"), ("H", "CACHETTE")))
        ]
        self.bouton_depart = pygame.Rect(650, 400, 285, 48)
        self.bouton_sauvegarder = pygame.Rect(650, 466, 285, 48)
        self.depart_tactile = False
        self.bouton_menu_tactile = pygame.Rect(922, 132, 62, 46)
        self.taille_case = 20
        self.role_joueur = "cacheur"
        self.cadence_tir = 0.0
        self.flash_tir = 0.0
        self.cibles_restantes = 0
        self.avertissement_chercheur = 0.0
        self.camera_angle = 0.0
        self.camera_distance = 1.55
        self.camera_x = self.spawn[0] - self.camera_distance
        self.camera_y = self.spawn[1]
        self.vitesse_joueur = [0.0, 0.0]
        self.atmosphere = GameAtmosphere()
        self.atmosphere.weather_cycle = ("clear", "dust", "rain", "dust")
        self.mouvement = InertialMotion()
        self.camera_physique = ThirdPersonCamera()
        self.cadence_pas = FootstepClock()
        self.sons = AcousticField()
        self.modele_bots = BotDecisionModel()
        self.vision_bots = VisionModel()
        self.agents_sensoriels: list[SensoryAgent] = []
        self.accroupi = False
        self.camera_bob = 0.0

    @staticmethod
    def detecter_tactile() -> bool:
        if sys.platform == "android":
            return True
        try:
            from pygame._sdl2 import touch
            return touch.get_num_devices() > 0
        except (ImportError, AttributeError, pygame.error):
            return False

    def position_tactile(self, event: pygame.event.Event) -> tuple[int, int]:
        largeur, hauteur = pygame.display.get_window_size()
        echelle = min(largeur / LARGEUR, hauteur / HAUTEUR)
        decalage_x = (largeur - LARGEUR * echelle) / 2
        decalage_y = (hauteur - HAUTEUR * echelle) / 2
        return (
            round((event.x * largeur - decalage_x) / echelle),
            round((event.y * hauteur - decalage_y) / echelle),
        )

    def boutons_tactiles(self) -> list[tuple[str, tuple[int, int], int, str]]:
        action = "TIR" if self.role_joueur == "chasseur" else "CACHE"
        return [
            ("avant", (114, 548), 31, "AV"),
            ("gauche", (62, 610), 31, "G"),
            ("droite", (166, 610), 31, "D"),
            ("arriere", (114, 666), 25, "AR"),
            ("action", (864, 586), 43, action),
            ("course", (924, 651), 29, "RUN"),
        ]

    def action_tactile(self, position: tuple[int, int]) -> str | None:
        boutons = self.boutons_tactiles()
        candidats = [
            (math.dist(position, centre), action)
            for action, centre, rayon, _ in boutons
            if math.dist(position, centre) <= rayon
        ]
        if candidats:
            return min(candidats)[1]
        if self.bouton_menu_tactile.collidepoint(position):
            return "menu"
        return "camera" if position[0] > LARGEUR // 2 else None

    def interaction_tactile(self) -> None:
        if self.role_joueur == "chasseur":
            self.tirer()
            return
        x, y, _ = self.joueur
        if self.cache:
            self.cache = False
            self.sons.emit((x, y), .2, "toucher", owner=-1)
        else:
            self.cache = any(
                self.carte[cy][cx] == "H"
                and math.dist((x, y), (cx + .5, cy + .5)) < .9
                for cy in range(TAILLE) for cx in range(TAILLE)
            )
            if self.cache:
                self.sons.emit((x, y), .07, "toucher", owner=-1)

    def dessiner_commandes_tactiles(self) -> None:
        if not self.appareil_tactile or self.etat != "jeu":
            return
        calque = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        actifs = set(self.touches_tactiles.values())
        pygame.draw.rect(calque, (8, 14, 27, 180), self.bouton_menu_tactile, border_radius=10)
        pygame.draw.rect(calque, (117, 234, 213, 210), self.bouton_menu_tactile, 2, border_radius=10)
        menu_label = self.petite.render("MENU", True, (244, 248, 255))
        calque.blit(menu_label, menu_label.get_rect(center=self.bouton_menu_tactile.center))
        for action, centre, rayon, etiquette in self.boutons_tactiles():
            couleur = (117, 234, 213)
            pygame.draw.circle(calque, (8, 14, 27, 118), centre, rayon + 4)
            pygame.draw.circle(calque, (*couleur, 82 if action not in actifs else 145), centre, rayon)
            pygame.draw.circle(calque, (*couleur, 180), centre, rayon, 2)
            label = self.petite.render(etiquette, True, (244, 248, 255))
            calque.blit(label, label.get_rect(center=centre))
        self.ecran.blit(calque, (0, 0))

    def texte(self, message: str, position: tuple[int, int], police=None, couleur=(235, 242, 255), centre=True) -> None:
        surface = (police or self.police).render(message, True, couleur)
        rect = surface.get_rect(center=position) if centre else surface.get_rect(topleft=position)
        self.ecran.blit(surface, rect)

    def charger_perso(self) -> bool:
        try:
            data = json.loads(self.chemin.read_text(encoding="utf-8"))
            grille = data["map"]
            if (not grille or len(grille) > TAILLE or any(len(row) > TAILLE for row in grille)
                    or any(ch not in "#.H" for row in grille for ch in row)):
                return False
            self.carte = [["#"] * TAILLE for _ in range(TAILLE)]
            for y, row in enumerate(grille):
                self.carte[y][:len(row)] = list(row)
            self.spawn = tuple(data.get("spawn", [1.5, 1.5]))
            return True
        except (OSError, ValueError, TypeError, KeyError):
            return False

    def sauver_perso(self) -> None:
        try:
            self.chemin.parent.mkdir(parents=True, exist_ok=True)
            data = {"map": ["".join(row) for row in self.carte], "spawn": self.spawn}
            self.chemin.write_text(json.dumps(data), encoding="utf-8")
            self.resultat = "Ta carte est sauvegardee."
        except OSError as erreur:
            self.resultat = f"Sauvegarde impossible : {erreur}"

    def demarrer(self, perso: bool) -> None:
        if perso and not self.charger_perso():
            self.resultat = "Cree et sauvegarde d'abord ta carte."
            self.etat = "menu"
            return
        if not perso:
            self.carte = [list(ligne) for ligne in CARTE_BASE]
            self.spawn = (1.5, 1.5)
        self.role_joueur = random.choice(("cacheur", "chasseur"))
        self.joueur = [float(self.spawn[0]), float(self.spawn[1]), 0.0]
        self.camera_angle = 0.0
        self.camera_distance = 1.55
        self.camera_x = self.joueur[0] - self.camera_distance
        self.camera_y = self.joueur[1]
        self.vitesse_joueur = [0.0, 0.0]
        graine = int(self.spawn[0] * 7919 + self.spawn[1] * 104729)
        self.atmosphere.reset(graine)
        self.mouvement.reset()
        self.camera_physique.reset(self.joueur[0], self.joueur[1], self.camera_angle)
        self.cadence_pas.reset()
        self.sons.clear()
        self.modele_bots.new_round(graine)
        sols = [(x + .5, y + .5) for y in range(1, TAILLE - 1)
                for x in range(1, TAILLE - 1)
                if self.carte[y][x] != "#" and math.dist((x + .5, y + .5), self.spawn) > 4]
        random.shuffle(sols)
        role_bots = "chasseur" if self.role_joueur == "cacheur" else "cacheur"
        self.chercheurs = [{"x": x, "y": y, "vx": 0.0, "vy": 0.0,
                            "cible": (x, y), "pause": random.random(),
                            "role": role_bots, "cache": False,
                            "cherche_cache": False, "repere": False,
                            "phase": random.random() * math.tau,
                            "orientation": random.random() * math.tau,
                            "suspicion": 0.0, "speed": 0.0,
                            "route": [], "route_timer": 0.0,
                            "route_goal": None, "cache_goal": None,
                            "cache_timer": 0.0, "etat": "patrouille"}
                           for x, y in sols[:4]]
        self.agents_sensoriels = [SensoryAgent() for _ in self.chercheurs]
        self.cibles_restantes = len(self.chercheurs)
        self.cadence_tir = 0.0
        self.flash_tir = 0.0
        self.avertissement_chercheur = 0.0
        self.temps = 120.0
        self.cache = False
        self.resultat = ""
        self.etat = "jeu"
        if not self.appareil_tactile:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)

    def mur(self, x: float, y: float) -> bool:
        ix, iy = int(x), int(y)
        return not (0 <= ix < TAILLE and 0 <= iy < TAILLE) or self.carte[iy][ix] == "#"

    def position_libre(self, x: float, y: float, rayon: float = .22) -> bool:
        """Verifie le volume autour d'un personnage, pas seulement son centre."""
        for index in range(8):
            angle = math.tau * index / 8
            if self.mur(x + math.cos(angle) * rayon, y + math.sin(angle) * rayon):
                return False
        return not self.mur(x, y)

    def ligne_vue(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        distance = math.dist((x1, y1), (x2, y2))
        for i in range(1, int(distance * 12)):
            t = i / max(1, int(distance * 12))
            if self.mur(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t):
                return False
        return True

    def percevoir(self, index: int, bot: dict, cible: tuple[float, float] | None,
                  dt: float, role: str, dissimulation: float = 0.0):
        """Mets a jour la memoire de l'agent avec sa vue et les sons proches."""
        position = (bot["x"], bot["y"])
        vision = None
        if cible is not None:
            distance_cible = math.dist(position, cible)
            portee_initiale = self.vision_bots.range_limit
            portee = self.vision_bots.range_for(
                bot.get("speed", 0.0), self.atmosphere.clock.colors()[-1], False
            )
            self.vision_bots.range_limit = portee
            vision = self.vision_bots.evaluate(
                position,
                bot.get("orientation", 0.0),
                cible,
                moving=1.0 if distance_cible < 6 else .0,
                concealed=dissimulation,
                illumination=self.atmosphere.clock.colors()[-1],
                line_clear=self.ligne_vue(*position, *cible),
            )
            self.vision_bots.range_limit = portee_initiale
        attenuation = .09 if self.atmosphere.weather == "rain" else (
            .04 if self.atmosphere.weather == "snow" else 0.0
        )
        son = self.sons.listen(
            position, self.mur, threshold=.09 + attenuation,
            maximum_range=13.0 - attenuation * 24,
        )
        memoire = self.agents_sensoriels[index].update(
            dt, self.sons.clock, position, vision, son,
            cible if vision is not None and vision.visible else None, role,
        )
        bot["suspicion"] = memoire.suspicion
        bot["etat"] = memoire.state
        return vision, memoire

    def mise_a_jour(self, dt: float, touches) -> None:
        dt = min(max(dt, 0.0), .05)
        self.atmosphere.update(dt)
        self.sons.update(dt)
        self.temps -= dt
        self.cadence_tir = max(0.0, self.cadence_tir - dt)
        self.flash_tir = max(0.0, self.flash_tir - dt)
        self.avertissement_chercheur = max(0.0, self.avertissement_chercheur - dt)
        if self.temps <= 0:
            self.fin("Manche terminee : les cacheurs ont tenu bon !" if self.role_joueur == "cacheur"
                     else "Manche terminee : il reste des cacheurs.")
            return
        x, y, angle = self.joueur
        gauche_camera = int(touches[pygame.K_d]) - int(touches[pygame.K_q])
        zoom_camera = int(touches[pygame.K_s]) - int(touches[pygame.K_z])
        self.camera_angle = (self.camera_angle + gauche_camera * 1.65 * dt) % (2 * math.pi)
        self.camera_distance = max(1.2, min(4.0, self.camera_distance + zoom_camera * 1.25 * dt))

        actions_tactiles = set(self.touches_tactiles.values())
        avant = (int(touches[pygame.K_UP]) - int(touches[pygame.K_DOWN])
                 + int("avant" in actions_tactiles) - int("arriere" in actions_tactiles))
        cote = (int(touches[pygame.K_RIGHT]) - int(touches[pygame.K_LEFT])
                + int("droite" in actions_tactiles) - int("gauche" in actions_tactiles))
        direction_x = math.cos(self.camera_angle) * avant - math.sin(self.camera_angle) * cote
        direction_y = math.sin(self.camera_angle) * avant + math.cos(self.camera_angle) * cote
        longueur_direction = math.hypot(direction_x, direction_y)
        if longueur_direction > 1:
            direction_x /= longueur_direction
            direction_y /= longueur_direction
        self.accroupi = bool(touches[pygame.K_LCTRL] or touches[pygame.K_RCTRL])
        sprinte = bool(touches[pygame.K_LSHIFT] or touches[pygame.K_RSHIFT] or "course" in actions_tactiles) and not self.accroupi
        vitesse_max = 2.2 if self.role_joueur == "cacheur" else 2.5
        self.mouvement.maximum_speed = vitesse_max * (.62 if self.accroupi else 1.0)
        self.vitesse_joueur[:] = self.mouvement.update_velocity(
            direction_x, direction_y, dt, sprinte
        )
        vitesse_actuelle = math.hypot(*self.vitesse_joueur)
        x, y = self.mouvement.move(x, y, dt, self.mur, .23)
        if self.cadence_pas.update(dt, vitesse_actuelle, longueur_direction > .1):
            intensite_pas = .12 if self.accroupi else .18 + min(.72, vitesse_actuelle * .22)
            self.sons.emit((x, y), intensite_pas,
                           "course" if sprinte else "pas", owner=-1)
        if longueur_direction > .1:
            angle_cible = math.atan2(direction_y, direction_x)
            ecart_angle = (angle_cible - angle + math.pi) % (2 * math.pi) - math.pi
            angle += ecart_angle * min(1.0, dt * 8)
        self.joueur = [x, y, angle]
        self.camera_physique.set_zoom(self.camera_distance)
        pose = self.camera_physique.follow(x, y, self.camera_angle, dt,
                                           vitesse_actuelle, self.mur)
        self.camera_x, self.camera_y = pose.x, pose.y
        self.camera_bob = pose.bob
        if self.cache and self.carte[int(y)][int(x)] != "H": self.cache = False

        cacheurs = [bot for bot in self.chercheurs
                    if bot["role"] == "cacheur" and not bot["repere"]]
        for bot_index, bot in enumerate(self.chercheurs):
            if bot["repere"]:
                continue
            position_bot = (bot["x"], bot["y"])
            voit = False
            menace_proche = None
            memoire = self.agents_sensoriels[bot_index].memory
            if bot["role"] == "chasseur":
                bot["cache"] = False
                bot["cherche_cache"] = False
                if self.role_joueur == "cacheur":
                    cibles = [(x, y)] if not self.cache else []
                else:
                    cibles = [(cible["x"], cible["y"]) for cible in cacheurs
                              if cible is not bot and not cible["cache"]]
                if cibles:
                    cible_proche = min(cibles, key=lambda cible: math.dist(
                        position_bot, cible))
                    dissimulation = .92 if self.cache and self.role_joueur == "cacheur" else (
                        .38 if self.accroupi and self.role_joueur == "cacheur" else 0.0
                    )
                    vision, memoire = self.percevoir(
                        bot_index, bot, cible_proche, dt, "chasseur", dissimulation
                    )
                    voit = bool(vision and vision.visible and memoire.suspicion >= .2)
                else:
                    _, memoire = self.percevoir(bot_index, bot, None, dt, "chasseur")
                cible = self.agents_sensoriels[bot_index].target(bot["cible"])
                if memoire.state in {"investigation", "recherche", "alerte", "poursuite"}:
                    bot["etat"] = memoire.state
                if self.role_joueur == "cacheur":
                    distance_joueur = math.dist((x, y), (bot["x"], bot["y"]))
                    if (distance_joueur < 5.5
                            and (distance_joueur < 2.0
                                 or (not self.cache and self.ligne_vue(x, y, bot["x"], bot["y"])))):
                        self.avertissement_chercheur = 1.6
            else:
                menaces = []
                if self.role_joueur == "chasseur":
                    menaces.append((x, y))
                menaces.extend((chasseur["x"], chasseur["y"])
                               for chasseur in self.chercheurs
                               if chasseur is not bot and chasseur["role"] == "chasseur"
                               and not chasseur["repere"])
                if menaces:
                    menace_proche = min(menaces, key=lambda menace: math.dist(
                        position_bot, menace))
                    distance_menace = math.dist(position_bot, menace_proche)
                    dissimulation = .4 if self.accroupi and self.role_joueur == "chasseur" else 0.0
                    vision, memoire = self.percevoir(
                        bot_index, bot, menace_proche, dt, "cacheur", dissimulation
                    )
                    voit = bool(vision and vision.visible and memoire.suspicion >= .18)
                else:
                    distance_menace = math.inf
                    _, memoire = self.percevoir(bot_index, bot, None, dt, "cacheur")
                if voit:
                    bot["cherche_cache"] = True
                cible = bot["cible"]
                if bot["cherche_cache"] and menace_proche is not None and voit:
                    bot["cache_timer"] -= dt
                    menace_case = (int(menace_proche[0]), int(menace_proche[1]))
                    if (bot["cache_goal"] is None or bot["cache_timer"] <= 0
                            or bot.get("menace_case") != menace_case):
                        bot["cache_goal"] = self.modele_bots.hide_target(
                            self.carte, position_bot, menace_proche
                        )
                        bot["menace_case"] = menace_case
                        bot["cache_timer"] = .8
                    cible = bot["cache_goal"]
                elif memoire.state in {"investigation", "recherche", "alerte", "poursuite"}:
                    menace_memorisee = memoire.last_heard or memoire.last_known
                    if menace_memorisee is not None:
                        bot["cherche_cache"] = True
                        bot["cache_timer"] -= dt
                        menace_case = (int(menace_memorisee[0]), int(menace_memorisee[1]))
                        if (bot["cache_goal"] is None or bot["cache_timer"] <= 0
                                or bot.get("menace_case") != menace_case):
                            bot["cache_goal"] = self.modele_bots.hide_target(
                                self.carte, position_bot, menace_memorisee
                            )
                            bot["menace_case"] = menace_case
                            bot["cache_timer"] = .8
                        cible = bot["cache_goal"]
                elif bot["cherche_cache"]:
                    refuges = [(cx + .5, cy + .5) for cy, ligne in enumerate(self.carte)
                               for cx, cellule in enumerate(ligne) if cellule == "H"]
                    if refuges:
                        cible = min(refuges, key=lambda p: math.dist(p, position_bot))
                    else:
                        bot["cherche_cache"] = False
                elif distance_menace > 10:
                    bot["cache"] = False
                    bot["cherche_cache"] = False
                    bot["cache_goal"] = None
            bot["pause"] -= dt
            if ((bot["pause"] <= 0 or math.dist((bot["x"], bot["y"]), cible) < .4)
                    and not bot["cache"] and not bot["cherche_cache"]):
                eviter = menace_proche if bot["role"] == "cacheur" else None
                cible = self.modele_bots.patrol_target(self.carte, position_bot, eviter)
                bot["pause"] = random.uniform(1, 3)
            bot["cible"] = cible
            destination_case = (int(cible[0]), int(cible[1]))
            bot["route_timer"] -= dt
            if bot["route_timer"] <= 0 or bot["route_goal"] != destination_case:
                chemin = self.modele_bots.route_to(position_bot, cible, self.carte)
                case_actuelle = (int(bot["x"]), int(bot["y"]))
                bot["route"] = chemin[1:] if chemin and chemin[0] == case_actuelle else chemin
                bot["route_goal"] = destination_case
                bot["route_timer"] = .32
            while bot["route"] and math.dist(
                    position_bot, (bot["route"][0][0] + .5, bot["route"][0][1] + .5)) < .22:
                bot["route"].pop(0)
            if bot["route"]:
                tx, ty = bot["route"][0][0] + .5, bot["route"][0][1] + .5
            else:
                tx, ty = cible
            vx, vy = tx - bot["x"], ty - bot["y"]
            longueur = math.hypot(vx, vy)
            bot["speed"] = 0.0
            if longueur > .1:
                vitesse_bot = (1.35 if voit and bot["role"] == "chasseur"
                               else 1.12 if bot["role"] == "cacheur" and bot["cherche_cache"]
                               else .82)
                pas = min(vitesse_bot * dt, longueur)
                nx, ny = bot["x"] + vx / longueur * pas, bot["y"] + vy / longueur * pas
                ancien_x, ancien_y = bot["x"], bot["y"]
                if self.position_libre(nx, bot["y"], .17): bot["x"] = nx
                if self.position_libre(bot["x"], ny, .17): bot["y"] = ny
                bot["speed"] = math.dist((ancien_x, ancien_y), (bot["x"], bot["y"])) / max(dt, .001)
                if bot["speed"] > .02:
                    angle_cible = math.atan2(bot["y"] - ancien_y, bot["x"] - ancien_x)
                    ecart = (angle_cible - bot["orientation"] + math.pi) % math.tau - math.pi
                    bot["orientation"] = (bot["orientation"] + ecart * min(1.0, dt * 5.5)) % math.tau
                bot["phase"] += dt * 8
            else:
                bot["orientation"] = (
                    bot["orientation"] + math.sin(self.sons.clock * .7 + bot["phase"]) * dt * .28
                ) % math.tau
            if (bot["role"] == "cacheur" and bot["cherche_cache"]
                    and self.carte[int(bot["y"])][int(bot["x"])] == "H"
                    and math.dist((bot["x"], bot["y"]), cible) < .4):
                bot["cache"] = True
                bot["cherche_cache"] = False

    def tirer(self) -> None:
        """Tir d'entrainement sans impact graphique; les cibles sont simplement marquees."""
        if self.role_joueur != "chasseur" or self.cadence_tir > 0:
            return
        self.cadence_tir = .45
        self.flash_tir = .09
        self.sons.emit(tuple(self.joueur[:2]), 1.15, "objet", owner=-1)
        self.camera_physique.kick(.16)
        angle = self.camera_angle
        meilleur = None
        for bot in self.chercheurs:
            if bot["repere"] or bot["role"] != "cacheur":
                continue
            dx, dy = bot["x"] - self.joueur[0], bot["y"] - self.joueur[1]
            distance = math.hypot(dx, dy)
            if bot["cache"] and distance > 2.5:
                continue
            delta = (math.atan2(dy, dx) - angle + math.pi) % (2 * math.pi) - math.pi
            if distance < 11 and abs(delta) < .075 and self.ligne_vue(*self.joueur[:2], bot["x"], bot["y"]):
                if meilleur is None or distance < meilleur[0]: meilleur = (distance, bot)
        if meilleur:
            bot = meilleur[1]
            bot["role"] = "chasseur"
            bot["cache"] = False
            bot["cherche_cache"] = False
            self.cibles_restantes -= 1
            if self.cibles_restantes == 0:
                self.fin("Victoire ! Tous les cacheurs ont rejoint les chasseurs.")

    def fin(self, message: str) -> None:
        self.resultat = message
        self.etat = "fin"
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def dessiner_personnage(self, centre_x: int, pieds_y: int, hauteur: int,
                           couleur: tuple[int, int, int], phase: float = 0.0,
                           chasseur: bool = False, sac: bool = False,
                           dos: bool = False) -> None:
        """Personnage billboard detaille avec ombre, vetements et animation de marche."""
        hauteur = max(18, hauteur)
        largeur = max(8, int(hauteur * .31))
        pas = math.sin(phase) * hauteur * .035
        tete_r = max(4, int(hauteur * .115))
        sol = pieds_y
        haut = sol - hauteur
        eclairci = tuple(min(255, int(c * 1.18 + 8)) for c in couleur)
        ombre = tuple(max(0, int(c * .56)) for c in couleur)
        peau = (211, 166, 133)
        peau_ombre = (163, 116, 91)
        pantalon = (48, 57, 73) if chasseur else (50, 68, 57)
        pantalon_lumiere = (75, 84, 98) if chasseur else (70, 91, 73)

        pygame.draw.ellipse(self.ecran, (16, 20, 27),
                            (centre_x - largeur, sol - max(3, hauteur // 18),
                             largeur * 2, max(5, hauteur // 9)))
        # Jambes pliees en alternance et chaussures.
        hanche_y = sol - int(hauteur * .32)
        decalage = int(pas)
        for cote in (-1, 1):
            lx = centre_x + cote * largeur // 4
            bas_x = lx + (decalage if cote < 0 else -decalage)
            jambe = [(lx - largeur // 5, hanche_y), (lx + largeur // 5, hanche_y),
                     (bas_x + largeur // 6, sol - hauteur // 12),
                     (bas_x - largeur // 6, sol - hauteur // 12)]
            pygame.draw.polygon(self.ecran, pantalon, jambe)
            pygame.draw.line(self.ecran, pantalon_lumiere,
                             (lx, hanche_y + hauteur // 12),
                             (bas_x, sol - hauteur // 10), max(1, largeur // 12))
            pygame.draw.ellipse(self.ecran, (30, 34, 40),
                                (bas_x - largeur // 4, sol - hauteur // 11,
                                 max(4, largeur // 2), max(3, hauteur // 15)))

        torse_haut = sol - int(hauteur * .72)
        torse_bas = hanche_y + hauteur // 16
        if sac:
            pygame.draw.rect(self.ecran, (89, 75, 54),
                             (centre_x - largeur // 2, torse_haut + hauteur // 10,
                              largeur, int(hauteur * .34)), border_radius=max(2, largeur // 5))
            pygame.draw.line(self.ecran, (162, 139, 97),
                             (centre_x - largeur // 3, torse_haut + hauteur // 7),
                             (centre_x + largeur // 3, torse_bas - hauteur // 12),
                             max(1, largeur // 12))
        torse = [(centre_x - int(largeur * .72), torse_haut + hauteur // 9),
                 (centre_x - largeur // 2, torse_haut),
                 (centre_x + largeur // 2, torse_haut),
                 (centre_x + int(largeur * .72), torse_haut + hauteur // 9),
                 (centre_x + largeur // 2, torse_bas),
                 (centre_x - largeur // 2, torse_bas)]
        pygame.draw.polygon(self.ecran, ombre, torse)
        pygame.draw.polygon(self.ecran, couleur,
                            [(centre_x - largeur // 2, torse_haut),
                             (centre_x + largeur // 2, torse_haut),
                             (centre_x + largeur // 3, torse_bas),
                             (centre_x - largeur // 3, torse_bas)])
        pygame.draw.line(self.ecran, eclairci,
                         (centre_x - largeur // 3, torse_haut + hauteur // 9),
                         (centre_x - largeur // 5, torse_bas - hauteur // 10),
                         max(1, largeur // 12))
        # Coutures, poche et col donnent du relief aux vetements.
        pygame.draw.line(self.ecran, ombre, (centre_x, torse_haut + hauteur // 12),
                         (centre_x, torse_bas - hauteur // 14), max(1, largeur // 18))
        pygame.draw.rect(self.ecran, eclairci,
                         (centre_x + largeur // 8, torse_haut + hauteur // 3,
                          max(2, largeur // 4), max(3, hauteur // 12)),
                         border_radius=max(1, largeur // 14))
        pygame.draw.polygon(self.ecran, (224, 218, 202),
                            [(centre_x - largeur // 5, torse_haut),
                             (centre_x, torse_haut + hauteur // 10),
                             (centre_x + largeur // 5, torse_haut)])

        # Bras, manches, mains et arme d'entrainement du chasseur.
        epaule_y = torse_haut + hauteur // 8
        main_y = torse_bas - hauteur // 18
        for cote in (-1, 1):
            epaule_x = centre_x + cote * largeur // 2
            coude_x = epaule_x + cote * largeur // 4 + int(pas * .35)
            main_x = epaule_x + cote * largeur // 3 + (int(largeur * .38) if chasseur and cote > 0 else 0)
            pygame.draw.line(self.ecran, couleur, (epaule_x, epaule_y),
                             (coude_x, (epaule_y + main_y) // 2), max(2, largeur // 3))
            pygame.draw.line(self.ecran, ombre, (coude_x, (epaule_y + main_y) // 2),
                             (main_x, main_y), max(2, largeur // 4))
            pygame.draw.circle(self.ecran, peau, (main_x, main_y), max(2, largeur // 9))
        if chasseur:
            main_x = centre_x + int(largeur * .9)
            arme_y = main_y - hauteur // 20
            pygame.draw.rect(self.ecran, (32, 38, 43),
                             (main_x - 1, arme_y, max(6, largeur // 2), max(2, hauteur // 22)),
                             border_radius=max(1, largeur // 16))
            pygame.draw.rect(self.ecran, (69, 76, 78),
                             (main_x + largeur // 5, arme_y - hauteur // 45,
                              max(4, largeur // 3), max(2, hauteur // 28)))

        # Cou et visage, avec cheveux, oreilles, nez et ombrage.
        cou_y = torse_haut - hauteur // 18
        pygame.draw.rect(self.ecran, peau_ombre,
                         (centre_x - tete_r // 2, cou_y, tete_r, max(3, hauteur // 12)))
        visage_y = haut + tete_r + hauteur // 18
        pygame.draw.ellipse(self.ecran, peau_ombre,
                            (centre_x - tete_r, visage_y - tete_r,
                             tete_r * 2, int(tete_r * 2.15)))
        pygame.draw.ellipse(self.ecran, peau,
                            (centre_x - int(tete_r * .82), visage_y - int(tete_r * .94),
                             int(tete_r * 1.64), int(tete_r * 1.85)))
        pygame.draw.ellipse(self.ecran, (55, 43, 37),
                            (centre_x - int(tete_r * .9), visage_y - int(tete_r * 1.1),
                             int(tete_r * 1.8), int(tete_r * .72)))
        if dos:
            pygame.draw.ellipse(self.ecran, (48, 39, 34),
                                (centre_x - int(tete_r * .86), visage_y - int(tete_r * .05),
                                 int(tete_r * 1.72), int(tete_r * 1.05)))
            pygame.draw.line(self.ecran, (97, 75, 58),
                             (centre_x - tete_r // 3, visage_y + tete_r // 3),
                             (centre_x + tete_r // 4, visage_y + tete_r // 2), max(1, tete_r // 8))
        else:
            pygame.draw.line(self.ecran, peau_ombre,
                             (centre_x + tete_r // 3, visage_y),
                             (centre_x + tete_r // 2, visage_y + tete_r // 4), max(1, tete_r // 7))
            pygame.draw.circle(self.ecran, (242, 222, 203),
                               (centre_x - tete_r // 4, visage_y - tete_r // 4), max(1, tete_r // 9))
            if chasseur:
                pygame.draw.arc(self.ecran, (37, 48, 57),
                                (centre_x - tete_r, visage_y - int(tete_r * 1.1),
                                 tete_r * 2, tete_r), math.pi, math.tau, max(1, tete_r // 5))

    def tracer_rayon(self, origine_x: float, origine_y: float, angle: float):
        """Traverse la grille mur par mur; le cout depend des cases, pas de pas fixes."""
        direction_x, direction_y = math.cos(angle), math.sin(angle)
        cellule_x, cellule_y = int(origine_x), int(origine_y)
        delta_x = abs(1.0 / direction_x) if abs(direction_x) > 1e-9 else math.inf
        delta_y = abs(1.0 / direction_y) if abs(direction_y) > 1e-9 else math.inf
        pas_x = 1 if direction_x >= 0 else -1
        pas_y = 1 if direction_y >= 0 else -1
        cote_x = ((cellule_x + 1 - origine_x) * delta_x if pas_x > 0
                  else (origine_x - cellule_x) * delta_x)
        cote_y = ((cellule_y + 1 - origine_y) * delta_y if pas_y > 0
                  else (origine_y - cellule_y) * delta_y)
        distance = 22.0
        cote = 0
        mur_x, mur_y = cellule_x, cellule_y
        for _ in range(TAILLE * 2):
            if cote_x < cote_y:
                distance = cote_x
                cote_x += delta_x
                cellule_x += pas_x
                cote = 0
            else:
                distance = cote_y
                cote_y += delta_y
                cellule_y += pas_y
                cote = 1
            mur_x, mur_y = cellule_x, cellule_y
            if self.mur(cellule_x + .5, cellule_y + .5):
                break
        distance = max(.05, min(22.0, distance))
        hit_x = origine_x + direction_x * distance
        hit_y = origine_y + direction_y * distance
        texture_u = (hit_y % 1.0) if cote == 0 else (hit_x % 1.0)
        if (cote == 0 and direction_x > 0) or (cote == 1 and direction_y < 0):
            texture_u = 1.0 - texture_u
        return distance, hit_x, hit_y, texture_u, cote, mur_x, mur_y

    def dessiner_jeu(self) -> None:
        w, h = self.ecran.get_size()
        deplacement_y, impact = self.camera_physique.screen_offset()
        horizon = max(170, min(h - 170, h // 2 + int(deplacement_y * 110 + impact * 8)))
        px, py, angle = self.joueur
        camera_x = self.camera_x
        camera_y = self.camera_y
        angle = self.camera_angle
        self.atmosphere.draw_ray_background(
            self.ecran, horizon, camera_x, camera_y, angle
        )
        rays = 240
        profondeur = [22.0] * rays
        _, _, _, fog, intensity = self.atmosphere.clock.colors()
        palette = ("stone", "brick", "concrete", "wood", "metal")
        for i in range(rays):
            ray_angle = angle - .62 + 1.24 * i / rays
            distance_reelle, hit_x, hit_y, local_u, cote, cell_x, cell_y = self.tracer_rayon(
                camera_x, camera_y, ray_angle
            )
            distance = max(.05, distance_reelle * math.cos(ray_angle - angle))
            profondeur[i] = distance
            hauteur = min(h, int(h * .82 / max(.12, distance)))
            ombrage_face = .78 if cote else 1.0
            x = i * w // rays
            largeur = w // rays + 1
            family = palette[(cell_x * 17 + cell_y * 31 + self.atmosphere.seed // 7) % len(palette)]
            top = max(0, horizon - hauteur // 2)
            bottom = min(h, horizon + hauteur // 2)
            light = intensity * ombrage_face * (.64 if local_u < .045 or local_u > .955 else .82)
            self.atmosphere.materials.draw_wall(
                self.ecran, x, top, bottom, largeur, distance, local_u,
                hit_x, hit_y, family, light, fog,
            )
        objets = []
        for index, bot in enumerate(self.chercheurs):
            if bot.get("repere") or bot.get("cache"):
                continue
            distance = math.dist((camera_x, camera_y), (bot["x"], bot["y"]))
            angle_bot = math.atan2(bot["y"] - camera_y, bot["x"] - camera_x) - angle
            angle_bot = (angle_bot + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_bot) < .7 and distance > .2:
                objets.append((distance, angle_bot, index))
        for distance, angle_bot, index in sorted(objets, reverse=True):
            sx = int(w * (.5 + angle_bot / 1.24))
            ray_index = max(0, min(rays - 1, int(sx * rays / w)))
            if profondeur[ray_index] < distance - .25:
                continue
            taille = max(18, min(230, int(h * .62 / distance)))
            pieds = horizon + taille // 2
            bot = self.chercheurs[index]
            bot_est_chasseur = bot["role"] == "chasseur"
            base = (65, 94, 129) if bot_est_chasseur else (81, 133, 102)
            intensite = self.atmosphere.clock.colors()[-1]
            couleur = tuple(max(0, min(255, int(channel * (.62 + intensite * .46))))
                            for channel in base)
            angle_vue = math.atan2(camera_y - bot["y"], camera_x - bot["x"])
            orientation_vers_camera = (bot["orientation"] - angle_vue + math.pi) % math.tau - math.pi
            self.dessiner_personnage(sx, pieds, taille, couleur,
                                    bot["phase"], chasseur=bot_est_chasseur,
                                    sac=not bot_est_chasseur,
                                    dos=abs(orientation_vers_camera) > math.pi * .5)
            if bot["suspicion"] > .12:
                barre = pygame.Rect(sx - max(8, taille // 7), pieds - taille - 10,
                                    max(16, taille // 3), 4)
                pygame.draw.rect(self.ecran, (28, 34, 39), barre, border_radius=2)
                remplissage = barre.copy()
                remplissage.width = int(barre.width * bot["suspicion"])
                pygame.draw.rect(self.ecran, (245, 174, 81), remplissage, border_radius=2)
        # Le joueur est visible au premier plan, anime selon sa vitesse.
        vitesse_animation = math.hypot(*self.vitesse_joueur)
        phase_joueur = pygame.time.get_ticks() / 85 if vitesse_animation > .15 else 0.0
        taille_joueur = int(142 * 1.55 / self.camera_distance)
        if self.accroupi:
            taille_joueur = int(taille_joueur * .78)
        couleur_joueur = (176, 119, 72) if self.role_joueur == "chasseur" else (61, 139, 113)
        self.dessiner_personnage(w // 2, h - 142 + int(deplacement_y * 110), taille_joueur,
                                couleur_joueur, phase_joueur,
                                chasseur=self.role_joueur == "chasseur",
                                sac=self.role_joueur == "cacheur", dos=True)
        self.atmosphere.draw_particles(self.ecran)
        self.atmosphere.draw_vignette(self.ecran, .34)
        cx, cy, _ = self.joueur
        cache_proche = any(math.dist((cx, cy), (x + .5, y + .5)) < .9
                           for y, row in enumerate(self.carte) for x, cell in enumerate(row) if cell == "H")
        self.texte("CHASSEUR" if self.role_joueur == "chasseur" else "CACHEUR",
                   (w // 2, 28), self.police, (255, 204, 118))
        self.texte(f"Temps : {max(0, int(self.temps))} s", (100, 32), self.police)
        meteo = {"clear": "SEC", "dust": "POUSSIERE",
                 "rain": "PLUIE", "snow": "NEIGE"}.get(self.atmosphere.weather, "SEC")
        self.texte(f"{self.atmosphere.clock.phase_name} · {meteo}",
                   (w - 122, 66), self.petite, (178, 202, 224))
        if self.role_joueur == "cacheur" and self.avertissement_chercheur > 0:
            alerte = pygame.Rect(w // 2 - 235, 58, 470, 44)
            pygame.draw.rect(self.ecran, (83, 29, 24), alerte)
            pygame.draw.rect(self.ecran, (238, 126, 75), alerte, 2)
            self.texte("ATTENTION : UN CHERCHEUR EST PROCHE !", (w // 2, 80), self.petite, (255, 211, 156))
        if self.role_joueur == "cacheur":
            bruit = self.sons.level_at((cx, cy), self.mur)
            if bruit > .015:
                jauge = pygame.Rect(w // 2 - 78, 112, 156, 7)
                pygame.draw.rect(self.ecran, (31, 39, 49), jauge, border_radius=4)
                signal = jauge.copy()
                signal.width = int(jauge.width * bruit)
                couleur_signal = (220, 104, 82) if bruit > .45 else (219, 179, 94)
                pygame.draw.rect(self.ecran, couleur_signal, signal, border_radius=4)
                self.texte("BRUIT", (w // 2, 132), self.petite, (206, 214, 222))
        if self.role_joueur == "chasseur":
            allies = sum(bot["role"] == "chasseur" for bot in self.chercheurs)
            self.texte(f"Cacheurs restants : {self.cibles_restantes} | Allies : {allies}",
                       (w - 210, 32), self.petite)
        self.texte("CACHE !" if self.cache else "", (w // 2, h - 35), self.police, (105, 238, 178))
        self.texte("E : se cacher" if self.role_joueur == "cacheur" and cache_proche and not self.cache
                   else "E : sortir" if self.role_joueur == "cacheur" and self.cache else "",
                   (w // 2, h - 66), self.petite, (234, 226, 160))
        aide = (("Joystick : bouger | glisse a droite : camera | TIR/CACHE : action"
                 if self.appareil_tactile else
                 "Fleches : bouger | Q/D : tourner | Z/S : zoom | Maj : courir | Ctrl : discret | clic/Espace : tirer")
                if self.role_joueur == "chasseur" else
                ("Joystick : bouger | glisse a droite : camera | CACHE : se cacher"
                 if self.appareil_tactile else
                 "Fleches : bouger | Q/D : tourner | Z/S : zoom | Maj : courir | Ctrl : discret | E : cachette"))
        self.texte(aide, (w // 2, h - 12), self.petite, (195, 207, 229))
        if self.role_joueur == "chasseur":
            if self.flash_tir > 0:
                pygame.draw.circle(self.ecran, (255, 211, 126), (w // 2 + 48, h - 204), 12)
            pygame.draw.circle(self.ecran, (255, 248, 226), (w // 2, h // 2), 3)
            pygame.draw.line(self.ecran, (255, 248, 226), (w // 2 - 8, h // 2), (w // 2 - 4, h // 2))
            pygame.draw.line(self.ecran, (255, 248, 226), (w // 2 + 4, h // 2), (w // 2 + 8, h // 2))

    def dessiner_editeur(self) -> None:
        self.ecran.fill((13, 20, 39))
        self.texte("CREER TA CARTE 3D", (LARGEUR // 2, 44), self.titre)
        self.texte("Carte 25 x 25 | outil : " + {"#": "mur", ".": "sol", "H": "cachette"}[self.outil]
                   + " | choisis un outil, dessine et regle le depart",
                   (LARGEUR // 2, 85), self.petite)
        for y, row in enumerate(self.carte):
            for x, cell in enumerate(row):
                rect = pygame.Rect(self.grille.x + x * self.taille_case,
                                   self.grille.y + y * self.taille_case,
                                   self.taille_case - 1, self.taille_case - 1)
                couleur = {"#": (74, 91, 130), ".": (28, 38, 62), "H": (46, 147, 119)}[cell]
                pygame.draw.rect(self.ecran, couleur, rect)
                if (int(self.spawn[0]), int(self.spawn[1])) == (x, y):
                    pygame.draw.circle(self.ecran, (255, 221, 111), rect.center, 10)
        for rect, outil, nom in self.boutons_outils:
            actif = self.outil == outil
            couleur = (59, 115, 113) if actif else (28, 39, 67)
            pygame.draw.rect(self.ecran, couleur, rect, border_radius=9)
            pygame.draw.rect(self.ecran, (117, 234, 213), rect,
                             2 if actif else 1, border_radius=9)
            self.texte(nom, rect.center, self.police, (235, 243, 255))
        couleur_depart = (99, 83, 38) if self.depart_tactile else (28, 39, 67)
        pygame.draw.rect(self.ecran, couleur_depart, self.bouton_depart, border_radius=9)
        pygame.draw.rect(self.ecran, (255, 221, 111), self.bouton_depart, 2, border_radius=9)
        self.texte("CHOISIR LE DEPART" if not self.depart_tactile else "TOUCHE UNE CASE LIBRE",
                   self.bouton_depart.center, self.petite)
        pygame.draw.rect(self.ecran, (34, 99, 79), self.bouton_sauvegarder, border_radius=9)
        pygame.draw.rect(self.ecran, (104, 232, 163), self.bouton_sauvegarder, 2, border_radius=9)
        self.texte("SAUVEGARDER ET JOUER", self.bouton_sauvegarder.center, self.petite)
        self.texte("Les chercheurs apparaissent loin du depart.", (792, 550), self.petite)
        self.texte(self.resultat, (LARGEUR // 2, 675), self.petite, (104, 232, 163))

    def executer(self) -> None:
        running = True
        while running:
            dt = min(self.horloge.tick(60) / 1000, .05)
            for event in pygame.event.get():
                if event.type in (
                        getattr(pygame, "FINGERDOWN", -1),
                        getattr(pygame, "FINGERMOTION", -1),
                        getattr(pygame, "FINGERUP", -1)):
                    key = (getattr(event, "touch_id", 0), event.finger_id)
                    position = self.position_tactile(event)
                    if event.type == getattr(pygame, "FINGERDOWN", -1):
                        if not self.appareil_tactile:
                            self.appareil_tactile = True
                            pygame.event.set_grab(False)
                            pygame.mouse.set_visible(True)
                        if self.etat == "jeu":
                            action = self.action_tactile(position)
                            self.touches_tactiles[key] = action or ""
                            if action == "camera":
                                self.derniere_position_tactile[key] = position
                            elif action == "action":
                                self.interaction_tactile()
                            elif action == "menu":
                                self.etat = "menu"
                                pygame.event.set_grab(False)
                                pygame.mouse.set_visible(True)
                            continue
                        self.touches_tactiles[key] = "interface"
                        event = pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN, {"pos": position, "button": 1}
                        )
                    elif event.type == getattr(pygame, "FINGERMOTION", -1):
                        action = self.touches_tactiles.get(key)
                        if action == "camera":
                            ancienne = self.derniere_position_tactile.get(key, position)
                            dx, dy = position[0] - ancienne[0], position[1] - ancienne[1]
                            self.camera_angle = (self.camera_angle + dx * .005) % math.tau
                            self.camera_distance = max(1.2, min(4.0, self.camera_distance + dy * .004))
                            self.derniere_position_tactile[key] = position
                        elif self.etat == "jeu":
                            nouvelle_action = self.action_tactile(position)
                            self.touches_tactiles[key] = nouvelle_action or ""
                            if nouvelle_action == "camera":
                                self.derniere_position_tactile[key] = position
                        elif self.etat == "editeur" and action == "interface":
                            gx = (position[0] - self.grille.x) // self.taille_case
                            gy = (position[1] - self.grille.y) // self.taille_case
                            if 0 <= gx < TAILLE and 0 <= gy < TAILLE:
                                if self.depart_tactile and self.carte[gy][gx] != "#":
                                    self.spawn = (gx + .5, gy + .5)
                                    self.depart_tactile = False
                                elif (gx, gy) != (int(self.spawn[0]), int(self.spawn[1])) or self.outil != "#":
                                    self.carte[gy][gx] = self.outil
                        continue
                    else:
                        self.touches_tactiles.pop(key, None)
                        self.derniere_position_tactile.pop(key, None)
                        continue
                if (event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)
                        and getattr(event, "touch", False)):
                    continue
                if event.type == pygame.QUIT:
                    running = False
                    pygame.event.post(event)
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.etat in ("jeu", "fin", "editeur"):
                            self.etat = "menu"
                            pygame.event.set_grab(False)
                            pygame.mouse.set_visible(True)
                        else:
                            running = False
                    elif self.etat == "menu":
                        if event.key == pygame.K_1: self.demarrer(False)
                        elif event.key == pygame.K_2: self.etat = "editeur"
                        elif event.key == pygame.K_3: self.demarrer(True)
                        elif event.key == pygame.K_4: running = False
                    elif self.etat == "jeu" and self.role_joueur == "chasseur" and event.key == pygame.K_SPACE:
                        self.tirer()
                    elif self.etat == "jeu" and event.key == pygame.K_e and self.role_joueur == "cacheur":
                        self.interaction_tactile()
                    elif self.etat == "editeur":
                        if event.key == pygame.K_1: self.outil = "#"
                        elif event.key == pygame.K_2: self.outil = "."
                        elif event.key == pygame.K_3: self.outil = "H"
                        elif event.key == pygame.K_s:
                            self.sauver_perso()
                            self.demarrer(True)
                elif event.type == pygame.MOUSEMOTION and self.etat == "jeu":
                    self.camera_angle = (self.camera_angle + event.rel[0] * .003) % (2 * math.pi)
                elif event.type == pygame.MOUSEBUTTONDOWN and self.etat == "jeu" and event.button == 1:
                    self.tirer()
                elif event.type == pygame.MOUSEBUTTONDOWN and self.etat == "editeur":
                    mx, my = event.pos
                    if event.button == 1 and self.bouton_depart.collidepoint(event.pos):
                        self.depart_tactile = not self.depart_tactile
                    elif event.button == 1 and self.bouton_sauvegarder.collidepoint(event.pos):
                        self.sauver_perso()
                        self.demarrer(True)
                    elif event.button == 1 and any(
                            rect.collidepoint(event.pos)
                            for rect, _, _ in self.boutons_outils):
                        for rect, outil, _ in self.boutons_outils:
                            if rect.collidepoint(event.pos):
                                self.outil = outil
                                break
                    else:
                        gx = (mx - self.grille.x) // self.taille_case
                        gy = (my - self.grille.y) // self.taille_case
                        if 0 <= gx < TAILLE and 0 <= gy < TAILLE:
                            if event.button == 1:
                                if self.depart_tactile and self.carte[gy][gx] != "#":
                                    self.spawn = (gx + .5, gy + .5)
                                    self.depart_tactile = False
                                elif (gx, gy) != (int(self.spawn[0]), int(self.spawn[1])) or self.outil != "#":
                                    self.carte[gy][gx] = self.outil
                            elif event.button == 3 and self.carte[gy][gx] != "#":
                                self.spawn = (gx + .5, gy + .5)
                elif event.type == pygame.MOUSEBUTTONDOWN and self.etat == "menu" and event.button == 1:
                    if self.boutons[0].collidepoint(event.pos): self.demarrer(False)
                    elif self.boutons[1].collidepoint(event.pos): self.etat = "editeur"
                    elif self.boutons[2].collidepoint(event.pos): self.demarrer(True)
                    elif self.boutons[3].collidepoint(event.pos): running = False
            if not running:
                break
            if self.etat == "menu":
                self.ecran.fill((10, 15, 34))
                self.texte("CACHE-CACHE 3D", (LARGEUR // 2, 140), self.titre, (117, 234, 213))
                noms = ("JOUER - CARTE DE BASE", "CREER MA CARTE", "JOUER MA CARTE", "RETOUR A L'ACCUEIL")
                for rect, nom in zip(self.boutons, noms):
                    pygame.draw.rect(self.ecran, (28, 39, 67), rect, border_radius=12)
                    pygame.draw.rect(self.ecran, (79, 201, 190), rect, 2, border_radius=12)
                    self.texte(nom, rect.center, self.police)
                self.texte(self.resultat, (LARGEUR // 2, 620), self.petite, (255, 187, 115))
                self.texte("Fleches : deplacement | ZQSD : camera | clic/Espace : tir du chasseur | E : cachette",
                           (LARGEUR // 2, 665), self.petite, (191, 206, 227))
            elif self.etat == "jeu":
                self.mise_a_jour(dt, pygame.key.get_pressed())
                self.dessiner_jeu()
                self.dessiner_commandes_tactiles()
            elif self.etat == "editeur":
                self.dessiner_editeur()
            elif self.etat == "fin":
                self.ecran.fill((11, 17, 35))
                self.texte(self.resultat, (LARGEUR // 2, 270), self.titre,
                           (111, 235, 188) if "gagne" in self.resultat.lower() else (250, 103, 125))
                self.texte("Entree ou Echap : revenir au menu du mode", (LARGEUR // 2, 360), self.police)
                self.texte("Les tirs marquent les joueurs sans sang ni blessure visible.", (LARGEUR // 2, 402), self.petite)
                if pygame.key.get_pressed()[pygame.K_RETURN]: self.etat = "menu"
            pygame.display.flip()
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
