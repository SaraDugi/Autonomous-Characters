import pygame
import math
import random
from pygame.math import Vector2

class Boid:
    def __init__(self, x, y, color, width, height, max_speed=2.5, max_force=0.1, radius=5, fov=math.radians(270)):
        self.position = Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = Vector2(math.cos(angle), math.sin(angle))
        self.velocity.scale_to_length(random.uniform(0, max_speed))
        self.acceleration = Vector2(0, 0)
        self.max_speed = max_speed
        self.max_force = max_force
        self.color = color
        self.radius = radius
        self.width = width
        self.height = height
        self.wander_theta = random.uniform(0, 2 * math.pi)
        self.fov = fov

    def in_fov(self, other):
        direction = self.velocity.normalize() if self.velocity.length() != 0 else Vector2(1, 0)
        to_other = other.position - self.position
        if to_other.length() == 0:
            return True
        to_other_normalized = to_other.normalize()
        dot = direction.dot(to_other_normalized)

        dot = max(min(dot, 1), -1)
        angle = math.acos(dot)
        return angle < self.fov / 2

    def avoid_obstacles(self, obstacles):
        steer = Vector2(0, 0)
        for obs in obstacles:
            to_obstacle = obs.position - self.position
            distance = to_obstacle.length()
            if distance < obs.radius + 50:
                away = self.position - obs.position
                if away.length() > 0:
                    away = away.normalize() / distance
                steer += away
        if steer.length() > 0:
            steer = steer.normalize() * self.max_speed - self.velocity
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
        return steer

    def seek(self, target):
        desired = target - self.position
        dist = desired.length()
        if dist == 0:
            return Vector2(0, 0)
        desired = desired.normalize()
        if dist < 100:
            desired *= self.max_speed * (dist / 100)
        else:
            desired *= self.max_speed
        steer = desired - self.velocity
        if steer.length() > self.max_force:
            steer = steer.normalize() * self.max_force
        return steer

    def flee(self, threat):
        desired = self.position - threat
        if desired.length() == 0:
            return Vector2(0, 0)
        desired = desired.normalize() * self.max_speed
        steer = desired - self.velocity
        if steer.length() > self.max_force:
            steer = steer.normalize() * self.max_force
        return steer

    def separate(self, boids):
        desired_separation = 30
        steer = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            if not self.in_fov(other):
                continue
            d = self.position.distance_to(other.position)
            if 0 < d < desired_separation:
                diff = self.position - other.position
                if diff.length() != 0:
                    diff = diff.normalize()
                steer += diff / d
                count += 1
        if count > 0:
            steer /= count
        if steer.length() > 0:
            steer = steer.normalize() * self.max_speed - self.velocity
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
        return steer

    def align(self, boids):
        neighbor_dist = 75
        avg_vel = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            if not self.in_fov(other):
                continue
            d = self.position.distance_to(other.position)
            if 0 < d < neighbor_dist:
                avg_vel += other.velocity
                count += 1
        if count > 0:
            avg_vel /= count
            if avg_vel.length() > 0:
                avg_vel = avg_vel.normalize() * self.max_speed
            steer = avg_vel - self.velocity
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
            return steer
        return Vector2(0, 0)

    def cohesion(self, boids):
        neighbor_dist = 250
        center_of_mass = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            if not self.in_fov(other):
                continue
            d = self.position.distance_to(other.position)
            if 0 < d < neighbor_dist:
                center_of_mass += other.position
                count += 1
        if count > 0:
            center_of_mass /= count
            return self.seek(center_of_mass)
        return Vector2(0, 0)

    def flock(self, boids, avoid_others=None):
        sep = self.separate(boids) * 3
        ali = self.align(boids) * 1.2
        coh = self.cohesion(boids) * 1.8
        self.acceleration = Vector2(0, 0)
        self.acceleration += sep + ali + coh

        if avoid_others:
            avoid = self.separate(avoid_others) * 4
            self.acceleration += avoid

    def wander(self):
        wander_radius = 25
        wander_distance = 55
        change = 0.3
        self.wander_theta += random.uniform(-change, change)
        circle_center = self.velocity.normalize() * wander_distance
        displacement = Vector2(math.cos(self.wander_theta), math.sin(self.wander_theta)) * wander_radius
        wander_force = circle_center + displacement
        if wander_force.length() > self.max_force:
            wander_force = wander_force.normalize() * self.max_force
        return wander_force

    def follow_flow_field(self):
        factor = 0.01
        angle = math.sin(self.position.x * factor) * math.cos(self.position.y * factor) * 2 * math.pi
        desired = Vector2(math.cos(angle), math.sin(angle)) * self.max_speed
        steer = desired - self.velocity
        if steer.length() > self.max_force:
            steer = steer.normalize() * self.max_force
        return steer

    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        self.position += self.velocity
        self.acceleration = Vector2(0, 0)

    def borders(self):
        if self.position.x < 0 or self.position.x > self.width:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > self.height:
            self.velocity.y *= -1

    def run(self, boids, target_pos=None, chase=False, evade_pos=None, avoid_others=None, obstacles=None):
        self.flock(boids, avoid_others)
        if chase and target_pos is not None:
            self.acceleration += self.seek(Vector2(target_pos))
        elif target_pos is None:
            self.acceleration += self.wander()
        if evade_pos is not None:
            distance = self.position.distance_to(evade_pos)
            if distance < 100:
                self.acceleration += self.flee(evade_pos) * (1 - distance / 100)
        if obstacles:
            self.acceleration += self.avoid_obstacles(obstacles) * 2
        self.update()
        self.borders()

    def draw(self, screen):
        angle = math.atan2(self.velocity.y, self.velocity.x)
        tip = self.position + Vector2(math.cos(angle), math.sin(angle)) * (self.radius * 2)
        left = self.position + Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * self.radius
        right = self.position + Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * self.radius
        pygame.draw.polygon(screen, self.color, [tip, left, right])