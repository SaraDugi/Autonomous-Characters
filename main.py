import pygame
import math
import random
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flock Simulation with Obstacles")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)

WHITE = (255, 255, 255)
BLUE  = (50, 150, 255)
RED   = (255, 0, 0)
GRAY  = (200, 200, 200)
BLACK = (0, 0, 0)

# Make neighbor radius moderately large so they sense each other,
# but keep separation radius smaller so they stay close.
NEIGHBOR_RADIUS = 80
SEPARATION_RADIUS = 10

# Field of view angle (in radians) can be overridden by user input
FOV_ANGLE = math.radians(270)

class Agent:
    def __init__(self, x, y, velocity=None, color=BLUE):
        self.position = pygame.math.Vector2(x, y)
        # Give each agent a small random velocity so alignment can take hold
        if velocity is not None:
            self.velocity = velocity
        else:
            vx = random.uniform(-0.3, 0.3)
            vy = random.uniform(-0.3, 0.3)
            self.velocity = pygame.math.Vector2(vx, vy)
            if self.velocity.length() == 0:
                self.velocity = pygame.math.Vector2(0.2, 0)

        # Start them with a small speed
        self.velocity.scale_to_length(1.0)

        self.max_speed = 3
        self.radius = 6
        self.wander_angle = 0
        self.color = color

    def in_fov(self, other):
        """Check if 'other' is in this agent's field of view."""
        global FOV_ANGLE
        direction = self.velocity.normalize()
        to_other = other.position - self.position
        if to_other.length_squared() == 0:
            return False
        to_other.normalize_ip()
        angle = math.acos(max(-1, min(1, direction.dot(to_other))))
        return angle <= FOV_ANGLE / 2

    def seek(self, target):
        """
        Move towards a user-clicked target.
        All flock members will collectively do this if in multi-mode.
        """
        desired = target - self.position
        if desired.length_squared() > 1:
            distance = desired.length()
            slowing_radius = 100
            if distance < slowing_radius:
                # Slow down near target
                desired.scale_to_length(self.max_speed * (distance / slowing_radius))
            else:
                desired.scale_to_length(self.max_speed)
            steer = desired - self.velocity
            self.velocity += steer * 0.1

    def wander(self, multiplier=0.0):
        """
        If multiplier=0 => effectively no wander, so they won't scatter.
        """
        if multiplier <= 0:
            return

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
        wander_force = (circle_center + displacement) * multiplier
        self.velocity += wander_force

    def separate(self, all_agents):
        """
        Light separation => they won't overlap but remain close.
        Lower multiplier => minimal repulsion.
        """
        steer = pygame.math.Vector2()
        count = 0
        for other in all_agents:
            if other != self and self.in_fov(other):
                dist = self.position.distance_to(other.position)
                if 0 < dist < SEPARATION_RADIUS:
                    diff = self.position - other.position
                    diff /= (dist if dist != 0 else 1)
                    steer += diff
                    count += 1

        if count > 0:
            steer /= count
            if steer.length() > 0:
                steer.scale_to_length(self.max_speed)
                steer -= self.velocity
                # Lower repulsion => 0.1
                self.velocity += steer * 0.1

    def align(self, same_flock):
        """
        Strong alignment => quickly adopt same velocity => move as one group.
        """
        avg_velocity = pygame.math.Vector2()
        count = 0
        for other in same_flock:
            if other != self and self.in_fov(other):
                dist = self.position.distance_to(other.position)
                if dist < NEIGHBOR_RADIUS:
                    avg_velocity += other.velocity
                    count += 1
        if count > 0:
            avg_velocity /= count
            if avg_velocity.length() > 0:
                avg_velocity.scale_to_length(self.max_speed)
            steer = avg_velocity - self.velocity
            # 0.5 => strong alignment
            self.velocity += steer * 0.5

    def cohesion(self, same_flock):
        """
        Strong cohesion => they cluster and move in a single mass.
        """
        center_mass = pygame.math.Vector2()
        count = 0
        for other in same_flock:
            if other != self and self.in_fov(other):
                dist = self.position.distance_to(other.position)
                if dist < NEIGHBOR_RADIUS:
                    center_mass += other.position
                    count += 1
        if count > 0:
            center_mass /= count
            desired = center_mass - self.position
            if desired.length() > 0:
                desired.scale_to_length(self.max_speed)
                steer = desired - self.velocity
                # 0.5 => strong cohesion
                self.velocity += steer * 0.5

    def avoid_obstacles(self, obstacles):
        """
        Avoid collisions with obstacles.
        """
        steer = pygame.math.Vector2()
        for obs in obstacles:
            dist = self.position.distance_to(obs.position)
            safe_dist = obs.radius + SEPARATION_RADIUS
            if dist < safe_dist:
                diff = self.position - obs.position
                diff /= (dist if dist != 0 else 1)
                steer += diff
        if steer.length() > 0:
            steer.scale_to_length(self.max_speed)
            steer -= self.velocity
            self.velocity += steer * 0.3

    def flee_from_center(self, other_center, radius=100):
        """
        Keep the flocks from merging by fleeing the other's center if too close.
        Lower radius => they can be somewhat near each other but remain distinct.
        """
        dist = self.position.distance_to(other_center)
        if dist < radius:
            desired = self.position - other_center
            desired.scale_to_length(self.max_speed)
            steer = desired - self.velocity
            self.velocity += steer * 0.3

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
        """
        Draw agent as a triangle pointing in direction of velocity.
        """
        angle = math.atan2(self.velocity.y, self.velocity.x)
        size = 12
        front = self.position + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * size
        right = self.position + pygame.math.Vector2(
            math.cos(angle + 2.5),
            math.sin(angle + 2.5)
        ) * size * 0.6
        left = self.position + pygame.math.Vector2(
            math.cos(angle - 2.5),
            math.sin(angle - 2.5)
        ) * size * 0.6

        pygame.draw.polygon(screen, self.color, [front, right, left])


class Obstacle:
    def __init__(self, x, y, radius=30):
        self.position = pygame.math.Vector2(x, y)
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, (120, 120, 120),
                           (int(self.position.x), int(self.position.y)),
                           self.radius)
        pygame.draw.circle(screen, BLACK,
                           (int(self.position.x), int(self.position.y)),
                           self.radius, 2)


def draw_button(rect, text):
    pygame.draw.rect(screen, GRAY, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    label = font.render(text, True, BLACK)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def get_input(prompt):
    """
    Only accepts digits; press Enter to confirm.
    """
    input_str = ""
    while True:
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

def select_mode():
    """
    Let user pick single or multiple agent flocks, and set FOV angle.
    Returns (flock1_count, flock2_count, FOV_ANGLE).
    """
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
                    # Single agent => 1 in flock1, 0 in flock2
                    angle_str = get_input("Field of View angle (degrees): ")
                    if angle_str == "":
                        angle_str = "270"
                    fov_deg = float(angle_str)
                    return (1, 0, math.radians(fov_deg))

                elif button_multi.collidepoint(event.pos):
                    number_str = get_input("Number of agents total: ")
                    if number_str == "":
                        number_str = "30"
                    total_agents = max(2, int(number_str))
                    half = total_agents // 2
                    flock1_size = half
                    flock2_size = total_agents - half

                    angle_str = get_input("Field of View angle (degrees): ")
                    if angle_str == "":
                        angle_str = "270"
                    fov_deg = float(angle_str)

                    return (flock1_size, flock2_size, math.radians(fov_deg))

def flock_center(agents):
    """
    Compute the center of mass of a flock.
    """
    if not agents:
        return pygame.math.Vector2(0, 0)
    center = pygame.math.Vector2()
    for a in agents:
        center += a.position
    center /= len(agents)
    return center

def main():
    global FOV_ANGLE

    AGENT_COUNT_1, AGENT_COUNT_2, FOV_ANGLE = select_mode()

    agents1 = []
    agents2 = []

    multiple_mode = (AGENT_COUNT_1 > 1 or AGENT_COUNT_2 > 0)

    # --- Create Flock 1 ---
    if AGENT_COUNT_1 > 0:
        if AGENT_COUNT_1 == 1 and AGENT_COUNT_2 == 0:
            # Single agent mode
            agents1 = [Agent(random.randint(50, WIDTH - 50),
                             random.randint(50, HEIGHT - 50),
                             color=BLUE)]
        else:
            # spawn around left-center
            center_left = pygame.math.Vector2(WIDTH//2 - 80, HEIGHT//2)
            for _ in range(AGENT_COUNT_1):
                x_off = random.uniform(-2, 2)
                y_off = random.uniform(-2, 2)
                agents1.append(Agent(center_left.x + x_off,
                                     center_left.y + y_off,
                                     color=BLUE))

    # --- Create Flock 2 ---
    if AGENT_COUNT_2 > 0:
        center_right = pygame.math.Vector2(WIDTH//2 + 80, HEIGHT//2)
        for _ in range(AGENT_COUNT_2):
            x_off = random.uniform(-2, 2)
            y_off = random.uniform(-2, 2)
            agents2.append(Agent(center_right.x + x_off,
                                 center_right.y + y_off,
                                 color=RED))

    # Obstacles
    obstacles = []
    for _ in range(3):
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 100)
        r = random.randint(20, 40)
        obstacles.append(Obstacle(x, y, r))

    target_pos = None
    running = True

    # Single list for cross-flock separation
    all_agents = agents1 + agents2

    while running:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                target_pos = pygame.math.Vector2(pygame.mouse.get_pos())

        for obs in obstacles:
            obs.draw(screen)

        # Flock centers (so each can flee the other if you want them separate)
        center_blue = flock_center(agents1)
        center_red = flock_center(agents2)

        # --- Update & Draw FLOCK 1 ---
        for agent in agents1:
            agent.separate(all_agents)  # minimal repulsion, enough to avoid overlap
            if len(agents1) > 1:
                agent.align(agents1)     # strong alignment
                agent.cohesion(agents1)  # strong cohesion => group motion

            if len(agents2) > 0:
                # If you want flocks separate, keep this; else remove
                agent.flee_from_center(center_red, radius=100)

            agent.avoid_obstacles(obstacles)

            # If user clicked => group seeks that point
            if target_pos:
                agent.seek(target_pos)
            else:
                # No wander => stable group movement
                if multiple_mode:
                    agent.wander(0.0)
                else:
                    agent.wander(0.005)

            agent.update()
            agent.draw(screen)

        # --- Update & Draw FLOCK 2 ---
        for agent in agents2:
            agent.separate(all_agents)
            if len(agents2) > 1:
                agent.align(agents2)
                agent.cohesion(agents2)

            if len(agents1) > 0:
                agent.flee_from_center(center_blue, radius=100)

            agent.avoid_obstacles(obstacles)

            if target_pos:
                agent.seek(target_pos)
            else:
                if multiple_mode:
                    agent.wander(0.0)
                else:
                    agent.wander(0.005)

            agent.update()
            agent.draw(screen)

        # Draw the user's mouse click target if any
        if target_pos:
            pygame.draw.circle(screen, RED, (int(target_pos.x), int(target_pos.y)), 6)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()