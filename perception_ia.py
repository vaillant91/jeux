"""Perception humaine simplifiée pour des bots crédibles dans le cache-cache."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random


Point = tuple[float, float]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def angle_delta(a: float, b: float) -> float:
    return (a - b + math.pi) % math.tau - math.pi


@dataclass
class SoundStimulus:
    """Un son garde sa position et perd de l'intensité avec le temps."""

    position: Point
    loudness: float
    category: str
    age: float = 0.0
    duration: float = 2.5
    owner: int | None = None
    tag: str = ""

    @property
    def remaining(self) -> float:
        return clamp(1.0 - self.age / max(.001, self.duration), 0.0, 1.0)

    def intensity_at(self, listener: Point) -> float:
        distance_factor = 1.0 / (1.0 + distance(self.position, listener) * .22)
        return self.loudness * self.remaining * distance_factor


class AcousticField:
    """Événements sonores bornés, filtrés par la distance et les murs."""

    def __init__(self, maximum_events: int = 48) -> None:
        self.maximum_events = maximum_events
        self.events: list[SoundStimulus] = []
        self.clock = 0.0

    def clear(self) -> None:
        self.events.clear()
        self.clock = 0.0

    def emit(
        self,
        position: Point,
        loudness: float,
        category: str,
        duration: float | None = None,
        owner: int | None = None,
        tag: str = "",
    ) -> SoundStimulus:
        durations = {
            "pas": .9,
            "course": 1.5,
            "atterrissage": 1.3,
            "objet": 1.0,
            "porte": 2.0,
            "sifflement": 2.5,
            "toucher": .6,
        }
        stimulus = SoundStimulus(
            (float(position[0]), float(position[1])),
            clamp(loudness, .0, 2.0),
            category,
            0.0,
            duration if duration is not None else durations.get(category, 1.0),
            owner,
            tag,
        )
        self.events.append(stimulus)
        if len(self.events) > self.maximum_events:
            del self.events[:len(self.events) - self.maximum_events]
        return stimulus

    def update(self, dt: float) -> None:
        dt = clamp(dt, 0.0, .1)
        self.clock += dt
        for event in self.events:
            event.age += dt
        self.events = [event for event in self.events if event.remaining > 0]

    def _occlusion(self, listener: Point, event: SoundStimulus, blocked) -> float:
        length = distance(listener, event.position)
        steps = max(1, min(160, int(length * 5)))
        obstruction = 0
        for index in range(1, steps):
            t = index / steps
            x = listener[0] + (event.position[0] - listener[0]) * t
            y = listener[1] + (event.position[1] - listener[1]) * t
            if blocked(x, y):
                obstruction += 1
        return math.exp(-obstruction * .16)

    def listen(
        self,
        listener: Point,
        blocked,
        threshold: float = .14,
        maximum_range: float = 12.0,
    ) -> SoundStimulus | None:
        """Retourne le son perceptible le plus clair, murs compris."""
        best: tuple[float, SoundStimulus] | None = None
        for event in self.events:
            if event.remaining <= 0:
                continue
            span = distance(listener, event.position)
            if span > maximum_range:
                continue
            signal = event.intensity_at(listener)
            if blocked is not None:
                signal *= self._occlusion(listener, event, blocked)
            if signal < threshold:
                continue
            if best is None or signal > best[0]:
                best = (signal, event)
        return best[1] if best else None

    def level_at(self, listener: Point, blocked=None) -> float:
        """Intensité combinée utile pour les jauges de danger."""
        total = 0.0
        for event in self.events:
            signal = event.intensity_at(listener)
            if blocked is not None:
                signal *= self._occlusion(listener, event, blocked)
            total += signal
        return clamp(total, 0.0, 1.0)


@dataclass
class VisionResult:
    visible: bool
    confidence: float
    distance: float
    angle_error: float


@dataclass
class SensoryMemory:
    """Mémoire courte d'un bot : dernière position et niveau d'alerte."""

    suspicion: float = 0.0
    last_known: Point | None = None
    last_seen_time: float = -999.0
    last_heard: Point | None = None
    last_heard_time: float = -999.0
    state: str = "patrouille"
    time_in_state: float = 0.0
    search_turns: int = 0
    confidence: float = 0.0


class VisionModel:
    """Champ de vision en cône avec distance, éclairage et camouflage."""

    def __init__(self, field_of_view: float = 1.8, range_limit: float = 9.0) -> None:
        self.field_of_view = field_of_view
        self.range_limit = range_limit
        self.minimum_confidence = .2

    def evaluate(
        self,
        observer: Point,
        facing: float,
        target: Point,
        target_heading: float | None = None,
        moving: float = 0.0,
        concealed: float = 0.0,
        illumination: float = 1.0,
        line_clear: bool = True,
    ) -> VisionResult:
        dx = target[0] - observer[0]
        dy = target[1] - observer[1]
        span = math.hypot(dx, dy)
        target_angle = math.atan2(dy, dx)
        error = abs(angle_delta(target_angle, facing))
        if span < .001:
            return VisionResult(True, 1.0, span, 0.0)
        if span > self.range_limit or error > self.field_of_view * .5 or not line_clear:
            return VisionResult(False, 0.0, span, error)
        range_signal = clamp(1.0 - span / self.range_limit, 0.0, 1.0)
        cone_signal = clamp(1.0 - error / max(.001, self.field_of_view * .5), 0.0, 1.0)
        motion_signal = clamp(.72 + moving * .34, .45, 1.2)
        light_signal = clamp(.42 + illumination * .62, .3, 1.0)
        disguise_signal = clamp(1.0 - concealed, .06, 1.0)
        facing_signal = 1.0
        if target_heading is not None:
            rear = abs(angle_delta(target_heading, target_angle + math.pi))
            facing_signal = .76 if rear < 1.1 else 1.0
        confidence = range_signal * .46 + cone_signal * .33
        confidence *= motion_signal * light_signal * disguise_signal * facing_signal
        confidence = clamp(confidence, 0.0, 1.0)
        return VisionResult(confidence >= self.minimum_confidence, confidence, span, error)

    def range_for(self, speed: float, light: float, crouching: bool = False) -> float:
        range_value = self.range_limit * clamp(.78 + light * .22, .55, 1.0)
        range_value += clamp(speed, 0, 2.0) * 1.1
        if crouching:
            range_value *= .63
        return range_value


class SensoryAgent:
    """Mise à jour de l'alerte et de la recherche à partir des sens."""

    def __init__(self, memory: SensoryMemory | None = None) -> None:
        self.memory = memory or SensoryMemory()
        self.decay_rate = .24
        self.notice_threshold = .24
        self.pursuit_threshold = .72
        self.forget_after = 6.5
        self.search_duration = 5.5

    def update(
        self,
        dt: float,
        now: float,
        observer: Point,
        vision: VisionResult | None,
        sound: SoundStimulus | None,
        target: Point | None,
        role: str,
    ) -> SensoryMemory:
        memory = self.memory
        dt = clamp(dt, 0.0, .12)
        memory.time_in_state += dt
        memory.suspicion = max(0.0, memory.suspicion - self.decay_rate * dt)
        memory.confidence = max(0.0, memory.confidence - .18 * dt)
        if vision is not None and vision.visible and target is not None:
            gain = vision.confidence * dt * (1.7 if role == "chasseur" else 1.35)
            memory.suspicion = clamp(memory.suspicion + gain, 0.0, 1.0)
            memory.confidence = max(memory.confidence, vision.confidence)
            memory.last_known = target
            memory.last_seen_time = now
            memory.state = "poursuite" if memory.suspicion >= self.pursuit_threshold else "alerte"
            memory.time_in_state = 0.0
        elif sound is not None:
            memory.last_heard = sound.position
            memory.last_heard_time = now
            memory.suspicion = clamp(memory.suspicion + sound.intensity_at(observer) * .45, 0.0, 1.0)
            if memory.state not in {"poursuite", "recherche"}:
                memory.state = "investigation"
                memory.time_in_state = 0.0
        elif memory.suspicion >= self.notice_threshold:
            if memory.state == "patrouille":
                memory.state = "alerte"
                memory.time_in_state = 0.0
        if memory.state == "poursuite" and now - memory.last_seen_time > 1.1:
            memory.state = "recherche"
            memory.time_in_state = 0.0
        if memory.state in {"recherche", "investigation"} and memory.time_in_state > self.search_duration:
            if now - max(memory.last_seen_time, memory.last_heard_time) > self.forget_after:
                memory.state = "patrouille"
                memory.suspicion *= .25
                memory.time_in_state = 0.0
        return memory

    def target(self, fallback: Point) -> Point:
        memory = self.memory
        if memory.state in {"poursuite", "recherche", "alerte"} and memory.last_known is not None:
            return memory.last_known
        if memory.state == "investigation" and memory.last_heard is not None:
            return memory.last_heard
        return fallback


class GridPathfinder:
    """Recherche de chemin A* avec coût de virage et pénalité de cachette."""

    def __init__(self, size: int = 25) -> None:
        self.size = size
        self.cache: dict[tuple[tuple[int, int], tuple[int, int], int], list[tuple[int, int]]] = {}
        self.cache_order: list[tuple[tuple[int, int], tuple[int, int], int]] = []
        self.cache_limit = 96

    def clear(self) -> None:
        self.cache.clear()
        self.cache_order.clear()

    def _key(self, start, goal, revision: int):
        return (start, goal, int(revision))

    def _neighbors(self, x: int, y: int, cells, hiding_penalty: float):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < self.size and 0 <= ny < self.size):
                continue
            if cells[ny][nx] == "#":
                continue
            cost = 1.0 + (hiding_penalty if cells[ny][nx] == "H" else 0.0)
            yield (nx, ny), cost

    def find_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        cells,
        revision: int = 0,
        hiding_penalty: float = 0.0,
    ) -> list[tuple[int, int]]:
        key = self._key(start, goal, revision)
        cached = self.cache.get(key)
        if cached is not None:
            return list(cached)
        if start == goal:
            return [start]
        frontier: list[tuple[float, int, tuple[int, int]]] = [(0.0, 0, start)]
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        cost_so_far: dict[tuple[int, int], float] = {start: 0.0}
        serial = 0
        while frontier:
            frontier.sort(key=lambda item: item[0], reverse=True)
            _, _, current = frontier.pop()
            if current == goal:
                break
            for neighbor, step in self._neighbors(*current, cells, hiding_penalty):
                new_cost = cost_so_far[current] + step
                if new_cost >= cost_so_far.get(neighbor, float("inf")):
                    continue
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heuristic = abs(goal[0] - neighbor[0]) + abs(goal[1] - neighbor[1])
                serial += 1
                frontier.append((new_cost + heuristic, serial, neighbor))
        if goal not in came_from:
            return []
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        self.cache[key] = path
        self.cache_order.append(key)
        while len(self.cache_order) > self.cache_limit:
            self.cache.pop(self.cache_order.pop(0), None)
        return list(path)

    def nearest_open(self, point: tuple[int, int], cells) -> tuple[int, int] | None:
        x, y = point
        if 0 <= x < self.size and 0 <= y < self.size and cells[y][x] != "#":
            return point
        for radius in range(1, self.size):
            for dx in range(-radius, radius + 1):
                for dy in (-radius, radius):
                    candidate = (x + dx, y + dy)
                    if 0 <= candidate[0] < self.size and 0 <= candidate[1] < self.size and cells[candidate[1]][candidate[0]] != "#":
                        return candidate
            for dy in range(-radius + 1, radius):
                for dx in (-radius, radius):
                    candidate = (x + dx, y + dy)
                    if 0 <= candidate[0] < self.size and 0 <= candidate[1] < self.size and cells[candidate[1]][candidate[0]] != "#":
                        return candidate
        return None


@dataclass
class AgentState:
    """État comportemental exposable à l'interface ou au debug."""

    mode: str = "patrouille"
    target: Point = (1.5, 1.5)
    orientation: float = 0.0
    movement_speed: float = 0.0
    suspicion: float = 0.0
    route: list[tuple[int, int]] = field(default_factory=list)
    reaction_delay: float = 0.0
    pause: float = 0.0


class BotDecisionModel:
    """Choix de destination lisible et déterministe pour un personnage."""

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.pathfinder = GridPathfinder()
        self.revision = 0

    def new_round(self, seed: int) -> None:
        self.rng.seed(seed)
        self.pathfinder.clear()
        self.revision += 1

    def patrol_target(self, cells, origin: Point, avoid: Point | None = None) -> Point:
        options = []
        oy, ox = int(origin[1]), int(origin[0])
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                if cell == "#":
                    continue
                distance = math.hypot(x + .5 - origin[0], y + .5 - origin[1])
                if distance < 2.0:
                    continue
                if avoid is not None and math.hypot(x + .5 - avoid[0], y + .5 - avoid[1]) < 2.0:
                    continue
                options.append((x, y))
        if not options:
            return origin
        chosen = self.rng.choice(options)
        return chosen[0] + .5, chosen[1] + .5

    def hide_target(self, cells, origin: Point, threat: Point) -> Point:
        choices = []
        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                if cell != "H":
                    continue
                candidate = (x + .5, y + .5)
                path = self.pathfinder.find_path(
                    (int(origin[0]), int(origin[1])),
                    (x, y),
                    cells,
                    self.revision,
                    hiding_penalty=0.0,
                )
                if not path:
                    continue
                threat_distance = math.hypot(candidate[0] - threat[0], candidate[1] - threat[1])
                travel = len(path)
                score = threat_distance - travel * .36 + self.rng.random() * .18
                choices.append((score, candidate))
        if choices:
            return max(choices, key=lambda value: value[0])[1]
        return self.patrol_target(cells, origin, threat)

    def route_to(self, start: Point, target: Point, cells) -> list[tuple[int, int]]:
        return self.pathfinder.find_path(
            (int(start[0]), int(start[1])),
            (int(target[0]), int(target[1])),
            cells,
            self.revision,
        )
