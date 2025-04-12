import pygame
import math, random
from pygame.math import Vector2

class Boid:
    def __init__(self, x, y, color, width, height, max_speed=2.5, max_force=0.1, radius=5):
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

    def seek(self, target):
        desired = target - self.position
        if desired.length() == 0:
            return Vector2(0, 0)
        desired = desired.normalize() * self.max_speed
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
        desired_separation = 25
        steer = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
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
        neighbor_dist = 50
        avg_vel = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
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
        neighbor_dist = 50
        center_of_mass = Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
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
        sep = self.separate(boids) * 1.5
        ali = self.align(boids) * 0.8
        coh = self.cohesion(boids) * 1
        self.acceleration = Vector2(0, 0)
        self.acceleration += sep + ali + coh
        if avoid_others:
            avoid = self.separate(avoid_others) * 2
            self.acceleration += avoid

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

    def run(self, boids, target_pos=None, chase=False, evade_pos=None, avoid_others=None):
        self.flock(boids, avoid_others)
        if chase and target_pos is not None:
            self.acceleration += self.seek(Vector2(target_pos))
        if evade_pos is not None:
            distance = self.position.distance_to(evade_pos)
            if distance < 100:
                self.acceleration += self.flee(evade_pos) * (1 - distance / 100)
        self.update()
        self.borders()

    def draw(self, screen):
        angle = math.atan2(self.velocity.y, self.velocity.x)
        tip = self.position + Vector2(math.cos(angle), math.sin(angle)) * (self.radius * 2)
        left = self.position + Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * self.radius
        right = self.position + Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * self.radius
        pygame.draw.polygon(screen, self.color, [tip, left, right])

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
        for boid in self.boids:
            boid.run(self.boids, target_pos=target_pos, chase=(target_pos is not None if mode == 'flock' else boid is selected_boid), evade_pos=evade_pos, avoid_others=avoid_others)

def draw_menu(screen, font):
    screen.fill((30, 30, 30))
    title = font.render("Choose Mode", True, (255, 255, 255))
    single = font.render("1 - Single Boid Mode", True, (200, 200, 200))
    flock = font.render("2 - Flock Mode", True, (200, 200, 200))
    screen.blit(title, (300, 200))
    screen.blit(single, (300, 260))
    screen.blit(flock, (300, 300))
    pygame.display.flip()

def main():
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Boids Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    mode = None
    while mode not in ['single', 'flock']:
        draw_menu(screen, font)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    mode = 'single'
                elif event.key == pygame.K_2:
                    mode = 'flock'

    flock_red = Flock(width, height)
    flock_blue = Flock(width, height)

    if mode == 'flock':
        num_red, num_blue = 20, 20
        center_red = Vector2(width * 0.25, height * 0.5)
        center_blue = Vector2(width * 0.75, height * 0.5)
        spread = 50
        for _ in range(num_red):
            pos = center_red + Vector2(random.uniform(-spread, spread), random.uniform(-spread, spread))
            flock_red.add_boid(Boid(pos.x, pos.y, (255, 0, 0), width, height))
        for _ in range(num_blue):
            pos = center_blue + Vector2(random.uniform(-spread, spread), random.uniform(-spread, spread))
            flock_blue.add_boid(Boid(pos.x, pos.y, (0, 0, 255), width, height))
    else:  # single
        pos = Vector2(width / 2, height / 2)
        flock_red.add_boid(Boid(pos.x, pos.y, (0, 255, 0), width, height))

    target_pos = None
    selected_boid = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = event.pos
                if mode == 'single':
                    all_boids = flock_red.boids + flock_blue.boids
                    selected_boid = min(all_boids, key=lambda b: Vector2(event.pos).distance_to(b.position)) if all_boids else None
                else:
                    selected_boid = None

        red_center = flock_red.get_center()
        blue_center = flock_blue.get_center()

        flock_red.run(target_pos=target_pos, mode=mode, selected_boid=selected_boid, evade_pos=blue_center, avoid_others=flock_blue.boids)
        flock_blue.run(target_pos=target_pos, mode=mode, selected_boid=selected_boid, evade_pos=red_center, avoid_others=flock_red.boids)

        screen.fill((10, 10, 30))
        if target_pos:
            pygame.draw.circle(screen, (255, 255, 255), (int(target_pos[0]), int(target_pos[1])), 5, 1)
        for boid in flock_red.boids + flock_blue.boids:
            boid.draw(screen)
        mode_text = f"Mode: {mode.capitalize()} (click to move)"
        text_surface = font.render(mode_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()