import pygame
import sys
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boids - Single Agent ali Flock Mode (z nadgradnjami + ovire)")
clock = pygame.time.Clock()

# Colors
BELA = (255, 255, 255)
CRNA = (0, 0, 0)
MODRA = (0, 0, 255)
RDECA = (255, 0, 0)

NUM_AGENTS_BLUE = 12
NUM_AGENTS_RED = 12

# (center_x, center_y, radius)
obstacles = [
    (400, 300, 60),
    (200, 200, 40),
    (600, 400, 30),
]

class Agent:
    FOV_ANGLE = 120  # field of view in degrees

    def __init__(self, x, y, color=MODRA):
        self.pos = pygame.math.Vector2(x, y)
        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 2
        self.acc = pygame.math.Vector2(0, 0)
        self.max_speed = 4.0
        self.max_force = 0.1
        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.color = color

    def update(self):
        self.vel += self.acc
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self.pos += self.vel
        self.acc.update(0, 0)

    def apply_force(self, force):
        self.acc += force

    def in_view(self, other, angle_fov=FOV_ANGLE, neighbor_radius=50):
        """Returns True if 'other' agent is within this agent's FOV and neighbor distance."""
        diff = other.pos - self.pos
        dist = diff.length()
        if dist > neighbor_radius or dist == 0:
            return False

        direction = self.vel
        if direction.length() == 0:
            direction = pygame.math.Vector2(0, -1)
        angle = direction.angle_to(diff)
        return abs(angle) <= (angle_fov / 2)

    def seek(self, target):
        desired = target - self.pos
        if desired.length() > 0:
            desired = desired.normalize() * self.max_speed
        steer = desired - self.vel
        if steer.length() > self.max_force:
            steer = steer.normalize() * self.max_force
        return steer

    def arrive(self, target, slowing_radius=100):
        desired = target - self.pos
        dist = desired.length()
        if dist > 0:
            desired_normalized = desired.normalize()
            if dist < slowing_radius:
                # Slow down as we approach
                desired_normalized *= (self.max_speed * (dist / slowing_radius))
            else:
                desired_normalized *= self.max_speed

            steer = desired_normalized - self.vel
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
            return steer
        return pygame.math.Vector2(0, 0)

    def wander(self):
        circle_dist = 40.0  
        circle_radius = 30.0  

        # If velocity is zero, give it a small "forward" nudge
        if self.vel.length() == 0:
            self.vel.from_polar((1, 0))

        circle_center = self.vel.normalize() * circle_dist

        self.wander_angle += random.uniform(-0.3, 0.3)
        x = math.cos(self.wander_angle) * circle_radius
        y = math.sin(self.wander_angle) * circle_radius
        wander_force = circle_center + pygame.math.Vector2(x, y)

        desired = self.vel + wander_force
        if desired.length() > self.max_speed:
            desired.scale_to_length(self.max_speed)

        steer = desired - self.vel
        if steer.length() > self.max_force:
            steer = steer.normalize() * self.max_force
        return steer

    def avoid_obstacles(self, obstacles):
        """
        Steer away from obstacles. The closer we are, the stronger the push.
        """
        steer = pygame.math.Vector2(0, 0)
        for (ox, oy, r) in obstacles:
            obstacle_center = pygame.math.Vector2(ox, oy)
            diff = self.pos - obstacle_center
            dist = diff.length()

            safe_radius = r + 30  # how far we consider 'danger' from the obstacle
            if 0 < dist < safe_radius:
                # Overlap is how far into the "danger" zone we are
                overlap = (safe_radius - dist)
                # Increase repulsion based on overlap
                diff = diff.normalize() * overlap
                steer += diff

        if steer.length() > 0:
            steer = steer.normalize() * self.max_speed
            steer -= self.vel
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
        return steer

    def separation(self, agent_list, desired_separation=25, neighbor_radius=50):
        """
        Separation from all given agents (can include same color or other color).
        """
        steer = pygame.math.Vector2(0, 0)
        count = 0
        for other in agent_list:
            if other is self:
                continue
            if not self.in_view(other, self.FOV_ANGLE, neighbor_radius):
                continue
            diff = self.pos - other.pos
            dist = diff.length()
            if 0 < dist < desired_separation:
                diff = diff.normalize() / dist
                steer += diff
                count += 1

        if count > 0:
            steer /= count

        if steer.length() > 0:
            steer = steer.normalize() * self.max_speed - self.vel
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
        return steer

    def alignment(self, same_color_agents, neighbor_radius=50):
        """
        Alignment only with agents of the same color (same_color_agents).
        """
        avg_vel = pygame.math.Vector2(0, 0)
        count = 0
        for other in same_color_agents:
            if other is self:
                continue
            if not self.in_view(other, self.FOV_ANGLE, neighbor_radius):
                continue
            avg_vel += other.vel
            count += 1

        if count > 0:
            avg_vel /= count
            avg_vel = avg_vel.normalize() * self.max_speed
            steer = avg_vel - self.vel
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
            return steer
        return pygame.math.Vector2(0, 0)

    def cohesion(self, same_color_agents, neighbor_radius=50):
        """
        Cohesion only with agents of the same color (same_color_agents).
        """
        center_of_mass = pygame.math.Vector2(0, 0)
        count = 0
        for other in same_color_agents:
            if other is self:
                continue
            if not self.in_view(other, self.FOV_ANGLE, neighbor_radius):
                continue
            center_of_mass += other.pos
            count += 1

        if count > 0:
            center_of_mass /= count
            desired = center_of_mass - self.pos
            if desired.length() > 0:
                desired = desired.normalize() * self.max_speed
            steer = desired - self.vel
            if steer.length() > self.max_force:
                steer = steer.normalize() * self.max_force
            return steer
        return pygame.math.Vector2(0, 0)

    def boids_flock_multicolor(self, same_color_agents, all_agents):
        """
        1) Separate from *all* agents (own color + other color)
        2) Align with own color only
        3) Cohere with own color only
        """
        sep = self.separation(all_agents, desired_separation=25, neighbor_radius=50)
        ali = self.alignment(same_color_agents, neighbor_radius=50)
        coh = self.cohesion(same_color_agents, neighbor_radius=50)

        # Weight each force
        sep *= 1.5  
        ali *= 1.0
        coh *= 1.0

        return sep + ali + coh

    def bounce_inside(self, width, height):
        if self.pos.x < 0:
            self.pos.x = 0
            self.vel.x *= -1
        elif self.pos.x > width:
            self.pos.x = width
            self.vel.x *= -1

        if self.pos.y < 0:
            self.pos.y = 0
            self.vel.y *= -1
        elif self.pos.y > height:
            self.pos.y = height
            self.vel.y *= -1

    def draw(self, surface):
        # Rotate a small triangle in the direction of velocity
        angle_degrees = 0
        if self.vel.length() > 0:
            base_direction = pygame.math.Vector2(0, -1)
            angle_degrees = base_direction.angle_to(self.vel)

        size = 12
        half_base = 6

        points = [
            (0, -size),      # Tip
            (-half_base, 0), # Left
            (half_base, 0)   # Right
        ]

        rotated_points = []
        rad = math.radians(angle_degrees)
        cosA = math.cos(rad)
        sinA = math.sin(rad)

        for px, py in points:
            rx = px * cosA - py * sinA
            ry = px * sinA + py * cosA
            rx += self.pos.x
            ry += self.pos.y
            rotated_points.append((rx, ry))

        pygame.draw.polygon(surface, self.color, rotated_points)

def create_flock(num_agents, color=MODRA):
    flock = []
    for _ in range(num_agents):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        flock.append(Agent(x, y, color=color))
    return flock

def create_single_agent():
    x = WIDTH // 2
    y = HEIGHT // 2
    return [Agent(x, y, color=MODRA)]

def draw_obstacles(surface, obstacles):
    for (ox, oy, r) in obstacles:
        pygame.draw.circle(surface, (100, 200, 100), (int(ox), int(oy)), r)

mode = 'flock'
agents_blue = create_flock(NUM_AGENTS_BLUE, color=MODRA)
agents_red = create_flock(NUM_AGENTS_RED, color=RDECA)

target_pos = None
running = True

def update_and_draw_flock(own_flock, all_agents):
    # We collect the forces separately, then apply them to each agent
    forces = []
    for a in own_flock:
        # Boids flocking with same color but separating from *all* agents
        flock_force = a.boids_flock_multicolor(
            same_color_agents=own_flock,
            all_agents=all_agents
        )

        # If there's a target, arrive; otherwise wander
        if target_pos is not None:
            arrive_force = a.arrive(target_pos)
            combined_force = flock_force + arrive_force
        else:
            wander_force = a.wander()
            combined_force = flock_force + wander_force

        # Avoid obstacles
        avoid_force = a.avoid_obstacles(obstacles)

        # Combine everything
        total_force = combined_force + avoid_force

        # Optional clamp
        if total_force.length() > a.max_force * 2:
            total_force = total_force.normalize() * (a.max_force * 2)

        forces.append(total_force)

    # Apply and update each agent
    for i, a in enumerate(own_flock):
        a.apply_force(forces[i])
        a.update()
        a.bounce_inside(WIDTH, HEIGHT)
        a.draw(window)

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                mode = 'single'
                agents_blue = create_single_agent()
                agents_red = []
                target_pos = None
            elif event.key == pygame.K_2:
                mode = 'flock'
                agents_blue = create_flock(NUM_AGENTS_BLUE, MODRA)
                agents_red = create_flock(NUM_AGENTS_RED, RDECA)
                target_pos = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            target_pos = pygame.math.Vector2(mx, my)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            target_pos = None

    window.fill(BELA)
    draw_obstacles(window, obstacles)

    # Draw the target if it exists
    if target_pos is not None:
        pygame.draw.circle(window, CRNA, (int(target_pos.x), int(target_pos.y)), 6)

    # Combine both flocks for separation checking
    all_agents = agents_blue + agents_red

    # Update and draw: each flock uses the same all_agents for separation
    update_and_draw_flock(agents_blue, all_agents)
    update_and_draw_flock(agents_red, all_agents)

    pygame.display.flip()

pygame.quit()
sys.exit()