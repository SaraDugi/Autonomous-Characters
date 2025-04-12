from pygame.math import Vector2

class Flock:
    def __init__(self, width, height):
        self.boids = []
        self.width = width
        self.height = height

    def add_boid(self, boid):
        self.boids.append(boid)

    def get_center(self):
        return sum((b.position for b in self.boids), Vector2(0, 0)) / len(self.boids) if self.boids else Vector2(self.width / 2, self.height / 2)

    def run(self, target_pos=None, mode='flock', selected_boid=None, evade_pos=None, avoid_others=None):
        min_flock_distance = 150
        center = self.get_center()

        for boid in self.boids:
            boid.run(
                self.boids,
                target_pos=target_pos,
                chase=(target_pos is not None if mode == 'flock' else boid is selected_boid),
                evade_pos=evade_pos,
                avoid_others=avoid_others
            )
            if evade_pos is not None:
                distance = center.distance_to(evade_pos)
                if distance < min_flock_distance:
                    force = boid.flee(evade_pos) * (1 - distance / min_flock_distance) * 1.5
                    boid.acceleration += force