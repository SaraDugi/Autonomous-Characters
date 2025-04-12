import pygame
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flocking Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

MAX_SPEED = 5.0
MAX_FORCE = 0.03
NEIGHBOR_RADIUS = 50
DESIRED_SEPARATION = 25
target_pos = None

class Boid:
    def __init__(self, x, y, color):
        self.position = pygame.math.Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle))
        self.acceleration = pygame.math.Vector2(0, 0)
        self.max_speed = MAX_SPEED
        self.max_force = MAX_FORCE
        self.size = 5
        self.color = color

    def run(self, boids):
        self.flock(boids)
        if target_pos:
            steer_to_target = self.arrive(target_pos)
            self.applyForce(steer_to_target)
        self.update()
        self.borders()
        self.render()

    def applyForce(self, force):
        self.acceleration += force

    def flock(self, boids):
        sep = self.separate(boids)
        ali = self.align(boids)
        coh = self.cohesion(boids)
        sep *= 1.5
        ali *= 1.0
        coh *= 1.0
        self.applyForce(sep)
        self.applyForce(ali)
        self.applyForce(coh)

    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length_squared() > self.max_speed ** 2:
            self.velocity.scale_to_length(self.max_speed)
        self.position += self.velocity
        self.acceleration.update(0, 0)

    def borders(self):
        if self.position.x < 0 or self.position.x > WIDTH:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > HEIGHT:
            self.velocity.y *= -1
        self.position.x = max(0, min(WIDTH, self.position.x))
        self.position.y = max(0, min(HEIGHT, self.position.y))

    def render(self):
        angle = math.atan2(self.velocity.y, self.velocity.x) + math.pi / 2
        cosA, sinA = math.cos(angle), math.sin(angle)
        tip = pygame.math.Vector2(0, -2 * self.size)
        left = pygame.math.Vector2(-self.size, 2 * self.size)
        right = pygame.math.Vector2(self.size, 2 * self.size)
        def rotate(v): return (self.position.x + v.x * cosA - v.y * sinA,
                               self.position.y + v.x * sinA + v.y * cosA)
        points = [rotate(tip), rotate(left), rotate(right)]
        pygame.draw.polygon(screen, self.color, points)

    def separate(self, boids):
        steer = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            dist = self.position.distance_to(other.position)
            if 0 < dist < DESIRED_SEPARATION:
                steer += (self.position - other.position).normalize() / dist
                count += 1
        if count > 0:
            steer /= count
            steer.scale_to_length(self.max_speed)
            steer -= self.velocity
            if steer.length_squared() > self.max_force ** 2:
                steer.scale_to_length(self.max_force)
        return steer

    def align(self, boids):
        avg = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            if self.position.distance_to(other.position) < NEIGHBOR_RADIUS:
                avg += other.velocity
                count += 1
        if count > 0:
            avg /= count
            avg.scale_to_length(self.max_speed)
            steer = avg - self.velocity
            if steer.length_squared() > self.max_force ** 2:
                steer.scale_to_length(self.max_force)
            return steer
        return pygame.math.Vector2(0, 0)

    def cohesion(self, boids):
        center = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if other is self:
                continue
            if self.position.distance_to(other.position) < NEIGHBOR_RADIUS:
                center += other.position
                count += 1
        if count > 0:
            center /= count
            desired = center - self.position
            if desired.length_squared() > 0:
                desired.scale_to_length(self.max_speed)
                steer = desired - self.velocity
                if steer.length_squared() > self.max_force ** 2:
                    steer.scale_to_length(self.max_force)
                return steer
        return pygame.math.Vector2(0, 0)

    def arrive(self, target):
        desired = pygame.math.Vector2(target) - self.position
        dist = desired.length()
        if dist < 100:
            desired.scale_to_length(max((dist / 100) * self.max_speed, 0.01))
        else:
            desired.scale_to_length(self.max_speed)
        steer = desired - self.velocity
        if steer.length_squared() > self.max_force ** 2:
            steer.scale_to_length(self.max_force)
        return steer

class Flock:
    def __init__(self):
        self.boids = []

    def addBoid(self, boid):
        self.boids.append(boid)

    def run(self):
        for boid in self.boids:
            boid.run(self.boids)

def draw_button(rect, text, hover=False):
    color = (100, 100, 255) if hover else (70, 70, 200)
    pygame.draw.rect(screen, color, rect)
    label = font.render(text, True, (255, 255, 255))
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def mode_selection_menu():
    button_single = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 70, 240, 50)
    button_flock = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 20, 240, 50)
    while True:
        screen.fill((20, 20, 20))
        mx, my = pygame.mouse.get_pos()
        hover_single = button_single.collidepoint(mx, my)
        hover_flock = button_flock.collidepoint(mx, my)
        draw_button(button_single, "Single Boid Mode", hover_single)
        draw_button(button_flock, "Flock Mode", hover_flock)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hover_single:
                    return "single"
                elif hover_flock:
                    return "flock"
        pygame.display.flip()
        clock.tick(60)

mode = mode_selection_menu()

flock_red = Flock()
flock_blue = Flock()

if mode == "single":
    flock_red.addBoid(Boid(WIDTH / 2, HEIGHT / 2, (255, 255, 0)))
else:
    centerX, centerY = WIDTH / 2, HEIGHT / 2
    spawn_radius = 50
    num_boids = 40
    for i in range(num_boids):
        x = random.uniform(centerX - spawn_radius, centerX + spawn_radius)
        y = random.uniform(centerY - spawn_radius, centerY + spawn_radius)
        color = (255, 50, 50) if i % 2 == 0 else (50, 50, 255)
        boid = Boid(x, y, color)
        (flock_red if i % 2 == 0 else flock_blue).addBoid(boid)

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                target_pos = pygame.mouse.get_pos()
            elif event.button == 3:
                target_pos = None

    screen.fill((30, 30, 30))
    flock_red.run()
    flock_blue.run()
    if target_pos:
        pygame.draw.circle(screen, (255, 255, 0), target_pos, 5)
    pygame.display.flip()

pygame.quit()
