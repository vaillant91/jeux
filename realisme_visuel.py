"""Procedural lighting and surface rendering shared by the platform and hide modes."""
from __future__ import annotations

import math
import random
import pygame

from variations_materiaux import material_variant, wear_profile

RGB = tuple[int, int, int]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def blend(a: float, b: float, amount: float) -> float:
    return a + (b - a) * clamp(amount, 0.0, 1.0)


def blend_rgb(a: RGB, b: RGB, amount: float) -> RGB:
    return tuple(int(clamp(blend(a[i], b[i], amount), 0, 255)) for i in range(3))


def scale_rgb(color: RGB, amount: float) -> RGB:
    return tuple(int(clamp(channel * amount, 0, 255)) for channel in color)


class DayNightLighting:
    """Slow, deterministic light cycle with smooth dawn and dusk transitions."""

    def __init__(self, seed: int = 0, seconds_per_day: float = 360.0) -> None:
        self.seed = seed
        self.seconds_per_day = max(60.0, seconds_per_day)
        self.phase = .31
        self.elapsed = 0.0
        self.speed = 1.0
        self.flash = 0.0
        self.weather = 0.0
        self._sun_glows: dict[int, pygame.Surface] = {}

    @property
    def hour(self) -> float:
        return self.phase * 24.0

    @property
    def phase_name(self) -> str:
        hour = self.hour
        if 5 <= hour < 8:
            return "AUBE"
        if 8 <= hour < 17:
            return "JOUR"
        if 17 <= hour < 20:
            return "CREPUSCULE"
        return "NUIT"

    def colors(self) -> tuple[RGB, RGB, RGB, RGB, float]:
        """Return sky top, horizon, floor, fog, and ambient intensity."""
        hour = self.hour
        anchors = (
            (0.0, (8, 13, 31), (34, 43, 65), (23, 29, 39), (39, 48, 68), .35),
            (5.0, (24, 30, 54), (131, 82, 74), (47, 41, 43), (102, 76, 78), .56),
            (8.0, (39, 73, 112), (122, 161, 186), (60, 66, 63), (118, 148, 170), .95),
            (16.0, (43, 85, 127), (127, 163, 183), (64, 68, 63), (121, 148, 165), .93),
            (19.0, (48, 39, 72), (206, 118, 79), (70, 51, 46), (152, 103, 87), .72),
            (22.0, (14, 19, 40), (53, 61, 79), (32, 38, 45), (52, 62, 80), .43),
            (24.0, (8, 13, 31), (34, 43, 65), (23, 29, 39), (39, 48, 68), .35),
        )
        for index in range(len(anchors) - 1):
            left, right = anchors[index], anchors[index + 1]
            if left[0] <= hour <= right[0]:
                t = (hour - left[0]) / max(.001, right[0] - left[0])
                t = t * t * (3 - 2 * t)
                sky = blend_rgb(left[1], right[1], t)
                horizon = blend_rgb(left[2], right[2], t)
                floor = blend_rgb(left[3], right[3], t)
                fog = blend_rgb(left[4], right[4], t)
                intensity = blend(left[5], right[5], t)
                return sky, horizon, floor, fog, intensity
        return anchors[0][1:]

    def update(self, dt: float, speed: float | None = None) -> None:
        dt = clamp(dt, 0.0, .1)
        self.elapsed += dt
        self.phase = (self.phase + dt * (self.speed if speed is None else speed) / self.seconds_per_day) % 1.0
        self.flash = max(0.0, self.flash - dt)
        self.weather = max(0.0, self.weather - dt * .012)

    def sun(self, size: tuple[int, int], horizon: int) -> tuple[int, int]:
        width, _ = size
        daylight = clamp((self.hour - 6) / 12, 0, 1)
        return int(width * daylight), int(horizon * (1 - .75 * math.sin(math.pi * daylight)))

    def moon(self, size: tuple[int, int], horizon: int) -> tuple[int, int]:
        width, _ = size
        sx, sy = self.sun(size, horizon)
        return width - sx, max(12, horizon - (horizon - sy) // 2)

    def draw_gradient(self, surface: pygame.Surface, horizon: int) -> None:
        sky, horizon_color, _, _, _ = self.colors()
        width, height = surface.get_size()
        horizon = max(1, min(height, horizon))
        for y in range(horizon):
            t = y / horizon
            color = blend_rgb(sky, horizon_color, t)
            pulse = int(math.sin(self.elapsed * .2 + y * .01) * 1.4)
            color = tuple(int(clamp(c + pulse, 0, 255)) for c in color)
            pygame.draw.line(surface, color, (0, y), (width, y))

    def draw_sky_objects(self, surface: pygame.Surface, horizon: int) -> None:
        _, _, _, _, _ = self.colors()
        width, _ = surface.get_size()
        day = clamp((math.sin((self.hour - 6) * math.pi / 12) + .15) / .82, 0, 1)
        if day > .04:
            x, y = self.sun(surface.get_size(), horizon)
            radius = int(9 + day * 13)
            glow = self._sun_glows.get(radius)
            if glow is None:
                glow = pygame.Surface((radius * 8, radius * 8), pygame.SRCALPHA)
                center = radius * 4
                for factor, alpha in ((3.2, 9), (2.2, 17), (1.4, 36)):
                    pygame.draw.circle(glow, (255, 212, 148, alpha),
                                       (center, center), int(radius * factor))
                self._sun_glows[radius] = glow
            center = radius * 4
            surface.blit(glow, (x - center, y - center))
            pygame.draw.circle(surface, (255, 240, 202), (x, y), radius)
        if day < .78:
            x, y = self.moon(surface.get_size(), horizon)
            pygame.draw.circle(surface, (207, 218, 231), (x, y), 12)
            pygame.draw.circle(surface, self.colors()[0], (x + 5, y - 3), 11)
            rng = random.Random(self.seed + 908)
            for i in range(74):
                sx, sy = rng.randrange(max(1, width)), rng.randrange(max(1, horizon))
                blink = .5 + .5 * math.sin(self.elapsed + i * 1.41)
                if blink > .74:
                    pygame.draw.circle(surface, (153, 183, 222), (sx, sy), 1 + int(i % 13 == 0))

    def draw_horizon(self, surface: pygame.Surface, horizon: int,
                     elapsed: float, environment: str = "hall") -> None:
        """Add distant architectural silhouettes and restrained practical lights."""
        if environment != "hall":
            return
        width, height = surface.get_size()
        horizon = max(0, min(height - 1, horizon))
        _, horizon_color, _, _, intensity = self.colors()
        silhouette = blend_rgb(horizon_color, (18, 23, 34), .72)
        pygame.draw.rect(surface, silhouette, (0, horizon - 2, width, 5))
        # Repeating arches make the distant corridor feel built, without hiding the
        # ray-cast walls that are drawn over this background afterwards.
        spacing = max(90, width // 6)
        drift = int((elapsed * 5) % spacing)
        for index, x in enumerate(range(-spacing - drift, width + spacing, spacing)):
            arch_width = int(spacing * .68)
            arch_height = int(10 + spacing * (.15 + (index % 3) * .035))
            arch = pygame.Rect(x, horizon - arch_height, arch_width, arch_height * 2)
            pygame.draw.arc(surface, blend_rgb(silhouette, (100, 109, 119), .22),
                            arch, 0.0, math.pi, 2)
            pygame.draw.line(surface, silhouette, (x, horizon), (x, horizon - arch_height // 2), 2)
            pygame.draw.line(surface, silhouette, (x + arch_width, horizon),
                             (x + arch_width, horizon - arch_height // 2), 2)
            if index % 2 == 0:
                lamp_x = x + arch_width // 2
                lamp_y = horizon - max(5, arch_height // 3)
                pulse = .78 + .12 * math.sin(elapsed * 2.1 + index)
                lamp_color = tuple(int(channel * intensity * pulse) for channel in (226, 183, 111))
                pygame.draw.circle(surface, lamp_color, (lamp_x, lamp_y), 3)
                pygame.draw.line(surface, scale_rgb(lamp_color, .55),
                                 (lamp_x, lamp_y + 3), (lamp_x, horizon - 2), 1)


class MaterialRenderer:
    """Cached procedural textures and shaded raycaster columns."""

    def __init__(self, seed: int = 0, cache_limit: int = 72) -> None:
        self.seed = seed
        self.cache_limit = cache_limit
        self.cache: dict[tuple[str, int, int, int], pygame.Surface] = {}
        self.keys: list[tuple[str, int, int, int]] = []
        self.scaled_cache: dict[tuple[str, tuple[int, int], int, int], pygame.Surface] = {}
        self.scaled_keys: list[tuple[str, tuple[int, int], int, int]] = []

    def reset(self, seed: int) -> None:
        self.seed = int(seed)
        self.cache.clear()
        self.keys.clear()
        self.scaled_cache.clear()
        self.scaled_keys.clear()

    def texture(self, family: str, width: int, height: int, variant: int = 0) -> pygame.Surface:
        width = max(8, min(256, int(width)))
        height = max(8, min(256, int(height)))
        key = (family, width, height, int(variant))
        if key in self.cache:
            return self.cache[key]
        surface = self._create_texture(*key)
        self.cache[key] = surface
        self.keys.append(key)
        while len(self.keys) > self.cache_limit:
            self.cache.pop(self.keys.pop(0), None)
        return surface

    def _create_texture(self, family: str, width: int, height: int, variant: int) -> pygame.Surface:
        material = material_variant(family, variant, width, self.seed)
        base, light, shadow = material[2], material[3], material[4]
        roughness, scale, wear, pattern = wear_profile(material)
        rng = random.Random((self.seed + 1) * 65537 + variant * 97 + width * 7 + height)
        result = pygame.Surface((width, height), pygame.SRCALPHA)
        result.fill((*base, 255))
        amount = max(12, int(width * height * roughness / 90))
        for _ in range(amount):
            x, y = rng.randrange(width), rng.randrange(height)
            radius = rng.choices((1, 2, 3), (55, 33, 12))[0]
            color = light if rng.random() < .34 else shadow
            pygame.draw.ellipse(result, (*color, rng.randint(9, 43)),
                                (x - radius, y - radius // 2, radius * 2, radius))
        if family in {"brick", "stone"}:
            self._draw_masonry(result, light, shadow, pattern, scale, rng)
        elif family == "wood":
            self._draw_grain(result, light, shadow, rng)
        elif family == "metal":
            self._draw_metal(result, light, shadow)
        elif family == "grass":
            self._draw_grass(result, light, shadow, rng)
        elif family == "cloth":
            self._draw_fabric(result, light, shadow)
        else:
            self._draw_concrete(result, light, shadow, wear, rng)
        return result

    def _draw_masonry(self, surface, light, shadow, pattern, scale, rng) -> None:
        width, height = surface.get_size()
        row = max(7, int(height / (4 + pattern % 3) * scale))
        block = max(10, int(width / (4 + pattern % 2) * scale))
        for line, y in enumerate(range(0, height, row)):
            pygame.draw.line(surface, (*shadow, 188), (0, y), (width, y), 1 + pattern % 2)
            offset = block // 2 if line % 2 else 0
            for x in range(offset, width, block):
                pygame.draw.line(surface, (*shadow, 155), (x, y), (x, min(height, y + row)), 1)
                pygame.draw.line(surface, (*light, 46), (x + 2, y + 3),
                                 (min(width, x + block - 3), y + 3), 1)
                if rng.random() < .2:
                    sx, sy = x + rng.randrange(max(1, block)), y + rng.randrange(max(1, row))
                    pygame.draw.line(surface, (*shadow, 105), (sx, sy), (sx + 3, sy + 4), 1)

    def _draw_grain(self, surface, light, shadow, rng) -> None:
        width, height = surface.get_size()
        for line in range(max(3, width // 7)):
            x = rng.randrange(width)
            points = []
            for y in range(-4, height + 8, max(7, height // 9)):
                bend = int(math.sin(y * .045 + x) * 2 + rng.uniform(-1.5, 1.5))
                points.append((max(0, min(width - 1, x + bend)), y))
            pygame.draw.lines(surface, (*(shadow if line % 3 == 0 else light), rng.randint(20, 68)),
                              False, points, 1)

    def _draw_metal(self, surface, light, shadow) -> None:
        width, height = surface.get_size()
        for y in range(0, height, max(2, height // 25)):
            pygame.draw.line(surface, (*light, 18), (0, y), (width, y), 1)
        pygame.draw.rect(surface, (*shadow, 128), (2, 2, width - 4, height - 4), 1)
        for x in (5, width - 6):
            for y in (5, height - 6):
                pygame.draw.circle(surface, (*light, 150), (x, y), 2)

    def _draw_grass(self, surface, light, shadow, rng) -> None:
        width, height = surface.get_size()
        for _ in range(max(15, width)):
            x, y = rng.randrange(width), rng.randrange(max(1, height // 2))
            length = rng.randint(2, max(3, height // 8))
            color = light if rng.random() < .65 else shadow
            pygame.draw.line(surface, (*color, rng.randint(45, 130)),
                             (x, y + length), (x + rng.randint(-2, 2), y), 1)

    def _draw_fabric(self, surface, light, shadow) -> None:
        width, height = surface.get_size()
        for x in range(0, width, 3):
            pygame.draw.line(surface, (*light, 18), (x, 0), (x, height), 1)
        for y in range(0, height, 3):
            pygame.draw.line(surface, (*shadow, 15), (0, y), (width, y), 1)

    def _draw_concrete(self, surface, light, shadow, wear, rng) -> None:
        width, height = surface.get_size()
        for _ in range(max(3, int(width * wear / 3))):
            x, y = rng.randrange(width), rng.randrange(height)
            end = (max(0, min(width - 1, x + rng.randint(-8, 8))),
                   max(0, min(height - 1, y + rng.randint(4, max(5, height // 4)))))
            color = shadow if rng.random() < .65 else light
            pygame.draw.line(surface, (*color, rng.randint(18, 62)), (x, y), end, 1)

    def draw_wall(
        self, surface: pygame.Surface, x: int, top: int, bottom: int, strip: int,
        distance: float, u: float, world_x: float, world_y: float,
        family: str, light: float, fog: RGB
    ) -> None:
        profile = material_variant(family, int(world_x), int(world_y), self.seed)
        base, lit, dark = profile[2], profile[3], profile[4]
        roughness, scale, wear, pattern = wear_profile(profile)
        height = max(1, bottom - top)
        segments = max(8, min(84, height // 4))
        for index in range(segments):
            v = index / max(1, segments - 1)
            grain = math.sin((world_x * 19 + world_y * 13 + v * 31 + pattern) * .63) * wear
            grain += math.sin((world_y * 41 - world_x * 7 + u * 23) * .29) * wear * .5
            joint = 0.0
            if family in {"brick", "stone"}:
                if abs((v * (4 + pattern % 3) + world_y * .31) % 1) < .055:
                    joint = -.24
                if abs((u * (4 + pattern % 2) + world_x * .27) % 1) < .04:
                    joint = -.2
            shade = max(.12, light * (1 - distance / 30.0) + grain + joint)
            color = tuple(int(clamp(c * shade, 0, 255)) for c in base)
            if v < .06:
                color = blend_rgb(color, lit, .14)
            elif v > .92:
                color = blend_rgb(color, dark, .24)
            color = blend_rgb(color, fog, clamp((distance - 4) / 18, 0, .68))
            y0 = top + int(index * height / segments)
            y1 = top + max(index + 1, int((index + 1) * height / segments))
            pygame.draw.rect(surface, color, (x, y0, strip, max(1, y1 - y0)))
        if strip > 2 and height > 18 and (u < .025 or u > .975):
            pygame.draw.line(surface, dark, (x, top), (x, bottom), 1)

    def draw_platform(self, surface: pygame.Surface, rect: pygame.Rect, family: str, seed: int = 0) -> None:
        profile = material_variant(family, rect.x // 48, rect.y // 48, seed)
        base, lit, dark = profile[2], profile[3], profile[4]
        pygame.draw.rect(surface, scale_rgb(dark, .55), rect.move(2, 5), border_radius=4)
        pygame.draw.rect(surface, base, rect, border_radius=4)
        texture_seed = seed + rect.x // 48
        cache_key = (family, rect.size, texture_seed, self.seed)
        texture = self.scaled_cache.get(cache_key)
        if texture is None:
            source = self.texture(family, min(192, max(24, rect.width)),
                                  min(96, max(16, rect.height)), texture_seed)
            texture = pygame.transform.smoothscale(source, rect.size)
            texture.set_alpha(115)
            self.scaled_cache[cache_key] = texture
            self.scaled_keys.append(cache_key)
            while len(self.scaled_keys) > self.cache_limit * 3:
                self.scaled_cache.pop(self.scaled_keys.pop(0), None)
        surface.blit(texture, rect.topleft)
        pygame.draw.line(surface, lit, rect.topleft, (rect.right - 2, rect.top), 3)
        pygame.draw.line(surface, dark, (rect.left, rect.bottom - 1), rect.bottomright, 2)
        if family == "grass":
            rng = random.Random(seed + rect.x * 31 + rect.y)
            for _ in range(max(2, rect.width // 20)):
                x = rect.left + rng.randrange(max(1, rect.width))
                h = rng.randint(3, 8)
                pygame.draw.line(surface, lit, (x, rect.top + 2), (x + rng.randint(-1, 1), rect.top - h), 1)


class GameAtmosphere:
    """Scene-level ambience shared by the platformer and raycast mode."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.time = 0.0
        self.clock = DayNightLighting(seed)
        self.materials = MaterialRenderer(seed)
        self.particles = []
        self.max_particles = 260
        self.rng = random.Random(seed)
        self.weather = "dust"
        self.weather_rate = 5.0
        self.weather_cycle = ("clear", "dust", "rain", "snow")
        self.wind = 0.0
        self._vignettes: dict[tuple[int, int], pygame.Surface] = {}

    def reset(self, seed: int) -> None:
        self.seed = int(seed)
        self.time = 0.0
        self.clock.phase = .31
        self.clock.elapsed = 0.0
        self.clock.seed = int(seed)
        self.clock.flash = 0.0
        self.clock.weather = 0.0
        self.materials.reset(seed)
        self.particles.clear()
        self.rng.seed(seed)
        self.weather = "dust"
        self._vignettes.clear()

    def update(self, dt: float) -> None:
        dt = clamp(dt, 0, .05)
        self.time += dt
        self.clock.update(dt)
        season = int(self.time // 52) % len(self.weather_cycle)
        self.weather = self.weather_cycle[season]
        self.weather_rate = {"clear": 0.0, "dust": 5.0, "rain": 20.0, "snow": 8.0}[self.weather]
        self.wind = math.sin(self.time * .19) * 7
        expected = self.weather_rate * dt
        count = int(expected) + int(self.rng.random() < expected % 1)
        width, height = 1000, 700
        for _ in range(min(count, self.max_particles - len(self.particles))):
            x = self.rng.uniform(0, width)
            y = self.rng.uniform(0, height) if self.weather == "dust" else self.rng.uniform(-8, 10)
            if self.weather == "rain":
                item = [x, y, self.wind + self.rng.uniform(-20, 20), self.rng.uniform(340, 560), 1.0, "rain"]
            elif self.weather == "snow":
                item = [x, y, self.wind * .3 + self.rng.uniform(-10, 10), self.rng.uniform(12, 55), self.rng.uniform(3, 6), "snow"]
            else:
                item = [x, y, self.wind * .2 + self.rng.uniform(-4, 4), self.rng.uniform(-6, 6), self.rng.uniform(2, 5), "dust"]
            self.particles.append(item)
        alive = []
        for item in self.particles:
            item[4] -= dt
            item[0] += item[2] * dt
            item[1] += item[3] * dt
            if item[5] == "dust":
                item[2] += math.sin(self.time + item[0] * .01) * dt
            if item[4] > 0 and -20 < item[0] < width + 20 and -20 < item[1] < height + 20:
                alive.append(item)
        self.particles = alive

    def burst(self, x: float, y: float, color: RGB, count: int = 10) -> None:
        for _ in range(min(count, self.max_particles - len(self.particles))):
            angle = self.rng.random() * math.tau
            speed = self.rng.uniform(25, 150)
            life = self.rng.uniform(.2, .65)
            self.particles.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                   life, "spark", color, life])

    def draw_particles(self, surface: pygame.Surface) -> None:
        for item in self.particles:
            x, y, vx, vy, life, kind = item[:6]
            if kind == "rain":
                pygame.draw.line(surface, (129, 164, 188), (int(x), int(y)),
                                 (int(x - vx * .012), int(y - 8)), 1)
            elif kind == "snow":
                pygame.draw.circle(surface, (222, 233, 240), (int(x), int(y)), 2)
            elif kind == "spark":
                color = item[6]
                pygame.draw.circle(surface, color, (int(x), int(y)), 2)
            else:
                pygame.draw.circle(surface, (142, 156, 171), (int(x), int(y)), 1)

    def draw_ray_background(
        self, surface: pygame.Surface, horizon: int, camera_x: float,
        camera_y: float, angle: float
    ) -> None:
        self.clock.draw_gradient(surface, horizon)
        self.clock.draw_sky_objects(surface, horizon)
        sky, far, floor, fog, intensity = self.clock.colors()
        self.clock.draw_horizon(surface, horizon, self.time, "hall")
        width, height = surface.get_size()
        pygame.draw.rect(surface, floor, (0, horizon, width, height - horizon))
        depth = max(1, height - horizon)
        for row in range(1, 16):
            fraction = row / 16
            y = horizon + int(depth * fraction * fraction)
            pygame.draw.line(surface, blend_rgb(floor, (151, 153, 145), fraction * .12),
                             (0, y), (width, y), 1)
        for column in range(-12, 13):
            offset = column * .7 - camera_x * .09
            x = int(width * (.5 + offset / (4 + column * column * .08)) + math.sin(angle) * 9)
            pygame.draw.line(surface, scale_rgb(floor, .76), (x, horizon), (x, height), 1)

    def draw_platform_backdrop(self, surface: pygame.Surface, camera_x: float = 0.0) -> None:
        width, height = surface.get_size()
        points = [(0, int(height * .82))]
        for x in range(0, width + 74, 74):
            peak = 19 + (stable_hash(int((x + camera_x * .13) // 74), self.seed) % 61)
            points.extend(((x, int(height * .82) - peak), (x + 37, int(height * .82) + 8)))
        points.extend(((width, height), (0, height)))
        pygame.draw.polygon(surface, (13, 21, 40), points)
        points = [(0, int(height * .91))]
        for x in range(0, width + 96, 96):
            peak = 13 + (stable_hash(int((x + camera_x * .22) // 96), self.seed + 3) % 43)
            points.extend(((x, int(height * .91) - peak), (x + 48, int(height * .91) + 6)))
        points.extend(((width, height), (0, height)))
        pygame.draw.polygon(surface, (8, 14, 29), points)
        self.draw_particles(surface)

    def draw_platform_sky(self, surface: pygame.Surface, horizon: int | None = None) -> None:
        """Paint a changing sky before the level geometry and atmospheric silhouettes."""
        if horizon is None:
            horizon = int(surface.get_height() * .82)
        self.clock.draw_gradient(surface, horizon)
        self.clock.draw_sky_objects(surface, horizon)
        _, horizon_color, floor, _, _ = self.clock.colors()
        width, height = surface.get_size()
        pygame.draw.rect(surface, floor, (0, horizon, width, height - horizon))
        depth = max(1, height - horizon)
        for step in range(1, 10):
            y = horizon + depth * step // 10
            pygame.draw.line(surface, blend_rgb(floor, horizon_color, step * .018),
                             (0, y), (width, y), 1)

    def draw_vignette(self, surface: pygame.Surface, strength: float = .6) -> None:
        size = surface.get_size()
        overlay = self._vignettes.get(size)
        if overlay is None:
            width, height = size
            overlay = pygame.Surface(size, pygame.SRCALPHA)
            center = (width // 2, height // 2)
            maximum = int(math.hypot(width, height) * .52)
            for step in range(22, 0, -1):
                factor = step / 22
                radius = int(maximum * factor)
                alpha = int((1 - factor) ** 2 * 115)
                pygame.draw.ellipse(overlay, (1, 4, 10, alpha),
                                    (center[0] - radius, center[1] - int(radius * height / width),
                                     radius * 2, int(radius * 2 * height / width)),
                                    max(1, int(max(width, height) * .024)))
            self._vignettes[size] = overlay
        if strength < 1:
            overlay = overlay.copy()
            overlay.set_alpha(int(255 * clamp(strength, 0, 1)))
        surface.blit(overlay, (0, 0))


def stable_hash(*values: int) -> int:
    result = 2166136261
    for value in values:
        result = ((result ^ (int(value) & 0xffffffff)) * 16777619) & 0xffffffff
    return result
