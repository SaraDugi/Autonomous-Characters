import pygame
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Išči in pristani")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (50, 150, 255)

class Agent:
    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.max_speed = 4
        self.radius = 10

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
            self.velocity += steer
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)

        self.position += self.velocity

    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (int(self.position.x), int(self.position.y)), self.radius)

agent = Agent(100, 100)
target_pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)

running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            target_pos = pygame.math.Vector2(pygame.mouse.get_pos())

    agent.seek(target_pos)
    agent.draw(screen)

    pygame.draw.circle(screen, RED, (int(target_pos.x), int(target_pos.y)), 8)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()