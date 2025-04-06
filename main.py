import pygame
import math
import random
import sys

# === SETUP ===
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flock Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

NEIGHBOR_RADIUS = 80
SEPARATION_RADIUS = 25

# === AGENT CLASS ===
class Agent:
    def __init__(self, x, y, velocity=None):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = velocity if velocity else pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.velocity.length() == 0:
            self.velocity = pygame.math.Vector2(1, 0)
        self.velocity.scale_to_length(2)
        self.max_speed = 3
        self.radius = 6
        self.wander_angle = 0

    def seek(self, target):
        desired = target - self.position
        if desired.length_squared() > 1:
            distance = desired.length()
            slowing_radius = 100
            if distance < slowing_radius:
                desired.scale_to_length(self.max_speed * (distance / slowing_radius))
            else:
                desired.scale_to_length(self.max_speed)
            steer = desired - self.velocity
            self.velocity += steer * 0.1

    def wander(self):
        wander_radius = 30
        wander_distance = 40
        angle_change = 0.2
        self.wander_angle += random.uniform(-angle_change, angle_change)
        if self.velocity.length() == 0:
            self.velocity = pygame.math.Vector2(1, 0)
        circle_center = self.velocity.normalize() * wander_distance
        displacement = pygame.math.Vector2(
            wander_radius * math.cos(self.wander_angle),
            wander_radius * math.sin(self.wander_angle)
        )
        wander_force = circle_center + displacement
        self.velocity += wander_force * 0.05

    def separate(self, agents):
        steer = pygame.math.Vector2()
        count = 0
        for other in agents:
            if other != self:
                distance = self.position.distance_to(other.position)
                if 0 < distance < SEPARATION_RADIUS:
                    diff = self.position - other.position
                    diff /= distance
                    steer += diff
                    count += 1
        if count > 0:
            steer /= count
            if steer.length() > 0:
                steer.scale_to_length(self.max_speed)
                steer -= self.velocity
                self.velocity += steer * 0.3

    def align(self, agents):
        avg_velocity = pygame.math.Vector2()
        count = 0
        for other in agents:
            if other != self and self.position.distance_to(other.position) < NEIGHBOR_RADIUS:
                avg_velocity += other.velocity
                count += 1
        if count > 0:
            avg_velocity /= count
            avg_velocity.scale_to_length(self.max_speed)
            steer = avg_velocity - self.velocity
            self.velocity += steer * 0.05

    def cohesion(self, agents):
        center_mass = pygame.math.Vector2()
        count = 0
        for other in agents:
            if other != self and self.position.distance_to(other.position) < NEIGHBOR_RADIUS:
                center_mass += other.position
                count += 1
        if count > 0:
            center_mass /= count
            desired = center_mass - self.position
            if desired.length() > 0:
                desired.scale_to_length(self.max_speed)
                steer = desired - self.velocity
                self.velocity += steer * 0.01

    def update(self):
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.position += self.velocity
        self.stay_in_bounds()

    def stay_in_bounds(self):
        margin = 20
        turn_factor = 1.5
        if self.position.x < margin:
            self.velocity.x += turn_factor
        elif self.position.x > WIDTH - margin:
            self.velocity.x -= turn_factor
        if self.position.y < margin:
            self.velocity.y += turn_factor
        elif self.position.y > HEIGHT - margin:
            self.velocity.y -= turn_factor

    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (int(self.position.x), int(self.position.y)), self.radius)

# === BUTTON + TEXT INPUT ===
def draw_button(rect, text):
    pygame.draw.rect(screen, GRAY, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    label = font.render(text, True, BLACK)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def get_input(prompt):
    input_str = ""
    input_active = True
    while input_active:
        screen.fill(WHITE)
        label = font.render(prompt + input_str, True, BLACK)
        screen.blit(label, (100, HEIGHT // 2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_str
                elif event.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif event.unicode.isdigit():
                    input_str += event.unicode

# === MODE SELECTION SCREEN ===
def select_mode():
    button_single = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 50)
    button_multi = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 20, 300, 50)

    while True:
        screen.fill(WHITE)
        draw_button(button_single, "Single Agent")
        draw_button(button_multi, "Multiple Agents")
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_single.collidepoint(event.pos):
                    return 1
                elif button_multi.collidepoint(event.pos):
                    number_str = get_input("Number of agents: ")
                    try:
                        count = int(number_str)
                        return max(2, count)
                    except ValueError:
                        return 30

# === START SIMULATION ===
AGENT_COUNT = select_mode()
agents = []

if AGENT_COUNT == 1:
    agents = [Agent(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))]
else:
    center = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
    direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
    for _ in range(AGENT_COUNT):
        pos_offset = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
        vel_offset = direction.rotate(random.uniform(-10, 10))
        agents.append(Agent(center.x + pos_offset.x, center.y + pos_offset.y, vel_offset))

target_pos = None

# === MAIN LOOP ===
running = True
while running:
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            target_pos = pygame.math.Vector2(pygame.mouse.get_pos())

    for agent in agents:
        if AGENT_COUNT > 1:
            agent.separate(agents)
            agent.align(agents)
            agent.cohesion(agents)
        if target_pos:
            agent.seek(target_pos)
        else:
            agent.wander()
        agent.update()
        agent.draw(screen)

    if target_pos:
        pygame.draw.circle(screen, RED, (int(target_pos.x), int(target_pos.y)), 6)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()