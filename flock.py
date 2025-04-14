import pygame
from pygame.math import Vector2
from boid import Boid

class Flock:
    def __init__(self, width, height):
        self.boids = []
        self.width = width
        self.height = height

    def add_boid(self, boid):
        self.boids.append(boid)

    def get_center(self):
        if self.boids:
            return sum((b.position for b in self.boids), Vector2(0, 0)) / len(self.boids)
        else:
            return Vector2(self.width / 2, self.height / 2)

    def run(self, target_pos=None, mode='flock', selected_boid=None, evade_pos=None, avoid_others=None):
        min_flock_distance = 150
        for boid in self.boids:
            if mode == 'flock':
                boid.flock(self.boids, avoid_others)
                boid.acceleration += boid.follow_flow_field()
                if avoid_others:
                    for other in avoid_others:
                        d = boid.position.distance_to(other.position)
                        if d < min_flock_distance:
                            force = boid.flee(other.position) * (1 - d / min_flock_distance) * 1.5
                            boid.acceleration += force
                boid.update()
                boid.borders()
            else:
                boid.run(self.boids,
                         target_pos=target_pos,
                         chase=(target_pos is not None if mode == 'flock' else boid is selected_boid),
                         evade_pos=evade_pos,
                         avoid_others=avoid_others)
                if evade_pos is not None:
                    d = boid.position.distance_to(evade_pos)
                    if d < min_flock_distance:
                        force = boid.flee(evade_pos) * (1 - d / min_flock_distance) * 1.5
                        boid.acceleration += force