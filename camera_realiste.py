"""Camera third-person spring and inertial movement helpers."""
from __future__ import annotations

from dataclasses import dataclass
import math


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wrap_angle(angle: float) -> float:
    return (angle + math.pi) % math.tau - math.pi


def damp(current: float, target: float, response: float, dt: float) -> float:
    """Frame-rate independent exponential damping."""
    factor = 1.0 - math.exp(-max(0.0, response) * max(0.0, dt))
    return current + (target - current) * factor


@dataclass
class CameraPose:
    x: float = 0.0
    y: float = 0.0
    distance: float = 1.55
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    bob: float = 0.0


class ThirdPersonCamera:
    """Damped chase camera with obstacle avoidance, bob and impact response."""

    def __init__(self) -> None:
        self.pose = CameraPose()
        self.target = (0.0, 0.0)
        self.target_yaw = 0.0
        self.distance_target = 1.55
        self.pitch_target = 0.0
        self.roll_target = 0.0
        self.follow_response = 7.5
        self.rotation_response = 8.5
        self.zoom_response = 5.0
        self.impact = 0.0
        self.impact_velocity = 0.0
        self.speed = 0.0
        self.walk_phase = 0.0
        self.obstructed = False

    def reset(self, x: float, y: float, yaw: float = 0.0) -> None:
        self.target = (x, y)
        self.target_yaw = yaw
        self.pose = CameraPose(
            x - math.cos(yaw) * self.distance_target,
            y - math.sin(yaw) * self.distance_target,
            self.distance_target,
            yaw,
        )
        self.impact = 0.0
        self.impact_velocity = 0.0
        self.walk_phase = 0.0

    def set_zoom(self, distance: float) -> None:
        self.distance_target = clamp(distance, 1.15, 4.2)

    def kick(self, amount: float) -> None:
        self.impact_velocity += clamp(amount, 0.0, 2.0) * 3.8

    def follow(
        self,
        x: float,
        y: float,
        camera_yaw: float,
        dt: float,
        speed: float = 0.0,
        blocked=None,
    ) -> CameraPose:
        dt = clamp(dt, 0.0, .08)
        self.target = (x, y)
        self.target_yaw = camera_yaw
        self.speed = speed
        self.walk_phase += dt * (5.5 + speed * 1.3)
        bob_target = math.sin(self.walk_phase) * min(.045, speed * .018) if speed > .12 else 0.0
        bob_target += math.sin(self.walk_phase * .5) * min(.012, speed * .004)
        self.pose.bob = damp(self.pose.bob, bob_target, 11.0, dt)
        desired_x = x - math.cos(camera_yaw) * self.distance_target
        desired_y = y - math.sin(camera_yaw) * self.distance_target
        clear_distance = self.distance_target
        self.obstructed = False
        if blocked is not None:
            steps = max(2, int(self.distance_target * 16))
            for index in range(1, steps + 1):
                t = index / steps
                sample_x = x - math.cos(camera_yaw) * self.distance_target * t
                sample_y = y - math.sin(camera_yaw) * self.distance_target * t
                if blocked(sample_x, sample_y):
                    clear_distance = max(.72, self.distance_target * max(.22, t - .09))
                    self.obstructed = True
                    break
            desired_x = x - math.cos(camera_yaw) * clear_distance
            desired_y = y - math.sin(camera_yaw) * clear_distance
        self.pose.x = damp(self.pose.x, desired_x, self.follow_response, dt)
        self.pose.y = damp(self.pose.y, desired_y, self.follow_response, dt)
        self.pose.yaw = wrap_angle(self.pose.yaw + wrap_angle(camera_yaw - self.pose.yaw)
                                   * (1.0 - math.exp(-self.rotation_response * dt)))
        desired_roll = clamp(speed * .025, -.08, .08)
        self.pose.roll = damp(self.pose.roll, desired_roll, 5.5, dt)
        self.pose.pitch = damp(self.pose.pitch, self.pitch_target, 5.0, dt)
        self.pose.distance = damp(self.pose.distance, clear_distance, self.zoom_response, dt)
        self._update_impact(dt)
        return self.pose

    def _update_impact(self, dt: float) -> None:
        spring = 35.0
        damping = 10.0
        acceleration = -spring * self.impact - damping * self.impact_velocity
        self.impact_velocity += acceleration * dt
        self.impact += self.impact_velocity * dt
        if abs(self.impact) < .0005 and abs(self.impact_velocity) < .002:
            self.impact = 0.0
            self.impact_velocity = 0.0

    def screen_offset(self) -> tuple[float, float]:
        return self.pose.bob, self.impact

    def compass_heading(self) -> float:
        return self.pose.yaw % math.tau


class InertialMotion:
    """Acceleration, stopping friction and collision-safe substeps."""

    def __init__(
        self,
        acceleration: float = 8.8,
        deceleration: float = 10.5,
        maximum_speed: float = 2.4,
        radius: float = .23,
    ) -> None:
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.maximum_speed = maximum_speed
        self.radius = radius
        self.velocity = [0.0, 0.0]
        self.previous_speed = 0.0

    def reset(self) -> None:
        self.velocity[:] = (0.0, 0.0)
        self.previous_speed = 0.0

    def update_velocity(self, direction_x: float, direction_y: float, dt: float, sprint: bool = False) -> tuple[float, float]:
        dt = clamp(dt, 0.0, .08)
        length = math.hypot(direction_x, direction_y)
        if length > 1:
            direction_x /= length
            direction_y /= length
        speed = self.maximum_speed * (1.22 if sprint else 1.0)
        target_x = direction_x * speed
        target_y = direction_y * speed
        moving = length > .05
        response = self.acceleration if moving else self.deceleration
        alpha = 1.0 - math.exp(-response * dt)
        self.velocity[0] += (target_x - self.velocity[0]) * alpha
        self.velocity[1] += (target_y - self.velocity[1]) * alpha
        self.previous_speed = math.hypot(*self.velocity)
        return self.velocity[0], self.velocity[1]

    def move(
        self,
        x: float,
        y: float,
        dt: float,
        blocked,
        radius: float | None = None,
    ) -> tuple[float, float]:
        radius = self.radius if radius is None else radius
        dx = self.velocity[0] * dt
        dy = self.velocity[1] * dt
        steps = max(1, int(math.ceil(max(abs(dx), abs(dy)) / .055)))
        step_x = dx / steps
        step_y = dy / steps
        for _ in range(steps):
            if self._free(x + step_x, y, radius, blocked):
                x += step_x
            else:
                self.velocity[0] = 0.0
            if self._free(x, y + step_y, radius, blocked):
                y += step_y
            else:
                self.velocity[1] = 0.0
        return x, y

    def _free(self, x: float, y: float, radius: float, blocked) -> bool:
        if blocked(x, y):
            return False
        for index in range(12):
            angle = math.tau * index / 12
            if blocked(x + math.cos(angle) * radius, y + math.sin(angle) * radius):
                return False
        return True

    def stop(self, strength: float = 1.0) -> None:
        factor = clamp(strength, 0.0, 1.0)
        self.velocity[0] *= 1.0 - factor
        self.velocity[1] *= 1.0 - factor


@dataclass
class FootstepClock:
    """Cadence scheduler emitting grounded movement events."""

    interval_walk: float = .48
    interval_run: float = .32
    elapsed: float = 0.0
    side: int = 0

    def update(self, dt: float, speed: float, moving: bool) -> bool:
        if not moving or speed < .18:
            self.elapsed = min(self.elapsed, self.interval_walk)
            return False
        self.elapsed += max(0.0, dt)
        interval = self.interval_run if speed > 1.7 else self.interval_walk
        if self.elapsed < interval:
            return False
        self.elapsed -= interval
        self.side ^= 1
        return True

    def reset(self) -> None:
        self.elapsed = 0.0
        self.side = 0
