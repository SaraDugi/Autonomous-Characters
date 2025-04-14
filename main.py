import pygame
import math
import random
from pygame.math import Vector2
from boid import Boid
from flock import Flock

def draw_menu(screen, font):
    screen.fill((30, 30, 30))
    title = font.render("Choose Mode", True, (255, 255, 255))
    single = font.render("1 - Single Boid Mode", True, (200, 200, 200))
    flock_mode = font.render("2 - Flow Fields Mode", True, (200, 200, 200))
    screen.blit(title, (300, 200))
    screen.blit(single, (300, 260))
    screen.blit(flock_mode, (300, 300))
    pygame.display.flip()

def draw_flow_field(screen, width, height, spacing=40):
    factor = 0.01
    for y in range(0, height, spacing):
        for x in range(0, width, spacing):
            pos = Vector2(x, y)
            angle = math.sin(x * factor) * math.cos(y * factor) * 2 * math.pi
            flow_vector = Vector2(math.cos(angle), math.sin(angle))
            arrow_length = spacing * 0.5
            end_point = pos + flow_vector * arrow_length
            pygame.draw.line(screen, (0, 255, 0), pos, end_point, 1)
            pygame.draw.circle(screen, (0, 255, 0), (int(end_point.x), int(end_point.y)), 2)

def generate_non_overlapping_boid(existing_boids, center, spread, color, width, height, min_distance=25):
    max_attempts = 100
    for _ in range(max_attempts):
        pos = center + Vector2(random.uniform(-spread, spread), random.uniform(-spread, spread))
        too_close = any(pos.distance_to(b.position) < min_distance for b in existing_boids)
        if not too_close:
            return Boid(pos.x, pos.y, color, width, height)
    return None

def main():
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Boids Simulation with Flow Fields, FOV, and Cross-Flock Evasion")
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
        spread = 120

        for _ in range(num_red):
            boid = generate_non_overlapping_boid(flock_red.boids, center_red, spread, (255, 0, 0), width, height)
            if boid:
                flock_red.add_boid(boid)

        for _ in range(num_blue):
            boid = generate_non_overlapping_boid(flock_blue.boids, center_blue, spread, (0, 0, 255), width, height)
            if boid:
                flock_blue.add_boid(boid)
    else:
        pos = Vector2(width / 2, height / 2)
        flock_red.add_boid(Boid(pos.x, pos.y, (0, 255, 0), width, height))

    target_pos = None
    selected_boid = None
    show_flow = False  

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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    show_flow = not show_flow

        red_center = flock_red.get_center()
        blue_center = flock_blue.get_center()

        flock_red.run(target_pos=target_pos, mode=mode, selected_boid=selected_boid,
                      evade_pos=blue_center, avoid_others=flock_blue.boids)
        flock_blue.run(target_pos=target_pos, mode=mode, selected_boid=selected_boid,
                       evade_pos=red_center, avoid_others=flock_red.boids)

        screen.fill((10, 10, 30))

        if show_flow and mode == 'flock':
            draw_flow_field(screen, width, height)

        if target_pos:
            pygame.draw.circle(screen, (255, 255, 255), (int(target_pos[0]), int(target_pos[1])), 5, 1)

        for boid in flock_red.boids + flock_blue.boids:
            boid.draw(screen)

        if mode == 'single':
            mode_text = "Mode: Single (click to move)"
        else:
            mode_text = "Mode: Flow Fields with FOV & Cross-Flock Evasion (press V to toggle flow field)"
        text_surface = font.render(mode_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()