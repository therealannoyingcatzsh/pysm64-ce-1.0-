"""
pysm64 - Ultra Mario 3D Bros (pygame-ce, no external files).
Port to pygame-ce: use pygame_ce if available, else pygame.
Import and run:  import pysm64; pysm64.run()
"""
import sys
import math
try:
    import pygame_ce as pygame
except ImportError:
    import pygame

# ============================================================
# pysm64 - Custom Super Mario 64 Pseudo-3D Engine
# By realflameselite - Upgraded with Mode 7 Projection
# ============================================================

# ---------------- CONFIGURATION ----------------
WIDTH, HEIGHT = 800, 600
FPS = 60
FOV = 400
CAM_DIST = 500
CAM_HEIGHT = 300

# PHYSICS CONSTANTS (Tuned for SM64 feel)
MAX_SPEED = 12
ACCEL = 0.5
FRICTION = 0.85
TURN_SPEED = 0.15
GRAVITY = 0.8
JUMP_FORCE = 16
TRIPLE_JUMP_MULTIPLIER = 1.2

# COLORS
SKY_BLUE      = (100, 150, 255)
SKY_TOP       = (135, 195, 255)   # SM64 menu gradient top
SKY_BOTTOM    = (50, 100, 200)   # SM64 menu gradient bottom
GRASS_GREEN   = (50, 160, 50)
PATH_TAN      = (210, 180, 140)
MOAT_BLUE     = (60, 120, 200, 200) # RGBA
CASTLE_WHITE  = (220, 220, 220)
ROOF_RED      = (200, 50, 50)
MARIO_RED     = (255, 0, 0)
MARIO_BLUE    = (0, 0, 255)
SHADOW        = (0, 0, 0, 100)
TITLE_GOLD    = (255, 220, 0)
TITLE_RED     = (200, 0, 0)
TITLE_OUTLINE = (80, 0, 0)

# ---------------- INIT ----------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
pygame.display.set_caption("Ultra Mario 3D Bros - pysm64")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)
font_title = pygame.font.SysFont("Arial", 48, bold=True)
font_menu = pygame.font.SysFont("Arial", 24, bold=True)

# Game state: "menu" | "playing"
game_state = "menu"

# ---------------- MATH UTILS ----------------
def rotate_point(x, z, cx, cz, angle):
    """Rotates a point (x,z) around center (cx,cz) by angle (radians)"""
    s, c = math.sin(angle), math.cos(angle)
    x -= cx
    z -= cz
    xnew = x * c - z * s
    znew = x * s + z * c
    return xnew + cx, znew + cz

class Camera:
    def __init__(self):
        self.x = 0
        self.y = CAM_HEIGHT
        self.z = 0
        self.yaw = 0
        self.target_yaw = 0

    def update(self, target_x, target_z):
        # Lakitu style: Follow target but lag slightly behind
        desired_x = target_x - math.sin(self.yaw) * CAM_DIST
        desired_z = target_z - math.cos(self.yaw) * CAM_DIST
        
        self.x += (desired_x - self.x) * 0.1
        self.z += (desired_z - self.z) * 0.1
        self.yaw += (self.target_yaw - self.yaw) * 0.1

    def project(self, x, y, z):
        """Projects 3D world coordinates to 2D screen coordinates"""
        # Relative to camera
        rx = x - self.x
        ry = y - self.y
        rz = z - self.z
        
        # Rotate around Y axis (Yaw)
        s, c = math.sin(-self.yaw), math.cos(-self.yaw)
        rot_x = rx * c - rz * s
        rot_z = rx * s + rz * c
        
        # Clip behind camera
        if rot_z <= 1:
            return None
            
        # Perspective projection
        scale = FOV / rot_z
        screen_x = WIDTH // 2 + rot_x * scale
        screen_y = HEIGHT // 2 + ry * scale # Y is up/down
        
        return (screen_x, screen_y, scale)

# ---------------- ENTITIES ----------------
class Mario:
    def __init__(self):
        self.x, self.y, self.z = 0, 0, 0 # Y is Up in 3D
        self.vel_fwd = 0
        self.vel_y = 0
        self.face_angle = 0
        self.state = "IDLE" # IDLE, RUN, JUMP
        self.ground_y = 0

    def update(self, keys):
        # Input Handling
        input_mag = 0
        target_angle = self.face_angle

        # Stick inputs (Arrow keys)
        dx, dz = 0, 0
        if keys[pygame.K_LEFT]:  dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]:    dz = 1
        if keys[pygame.K_DOWN]:  dz = -1

        if dx != 0 or dz != 0:
            input_mag = 1
            # Calculate angle relative to camera
            cam_angle = cam.yaw
            input_angle = math.atan2(dx, dz)
            target_angle = cam_angle + input_angle

        # Movement Physics (Momentum)
        if input_mag > 0:
            # Turn towards input
            angle_diff = (target_angle - self.face_angle + math.pi) % (2 * math.pi) - math.pi
            self.face_angle += angle_diff * TURN_SPEED
            
            # Accelerate
            if self.vel_fwd < MAX_SPEED:
                self.vel_fwd += ACCEL
        else:
            # Friction
            self.vel_fwd *= FRICTION
            if abs(self.vel_fwd) < 0.1: self.vel_fwd = 0

        # Apply velocity
        self.x += math.sin(self.face_angle) * self.vel_fwd
        self.z += math.cos(self.face_angle) * self.vel_fwd

        # Jumping & Gravity
        if keys[pygame.K_SPACE] and self.y == self.ground_y:
            self.vel_y = -JUMP_FORCE
            self.state = "JUMP"
        
        self.vel_y += GRAVITY
        self.y += self.vel_y

        # Ground Collision
        if self.y > self.ground_y:
            self.y = self.ground_y
            self.vel_y = 0
            self.state = "RUN" if self.vel_fwd > 1 else "IDLE"

    def draw(self, screen, cam):
        # 3D Projection for Mario
        proj = cam.project(self.x, self.y - 40, self.z) # -40 to center sprite vertically
        if not proj: return
        sx, sy, scale = proj
        
        # Shadow projection
        shadow_proj = cam.project(self.x, self.ground_y - 2, self.z)
        if shadow_proj:
            sh_x, sh_y, sh_scale = shadow_proj
            # Draw shadow ellipse
            sw, sh = 40 * sh_scale, 20 * sh_scale
            s_surf = pygame.Surface((int(sw*2), int(sh*2)), pygame.SRCALPHA)
            pygame.draw.ellipse(s_surf, SHADOW, (0, 0, sw, sh))
            screen.blit(s_surf, (sh_x - sw//2, sh_y - sh//2))

        # Simple Mario Shapes (Body + Hat)
        size = 60 * scale
        
        # Cap
        pygame.draw.circle(screen, MARIO_RED, (sx, sy - size*0.4), size/2)
        # Brim
        brim_off_x = math.sin(self.face_angle - cam.yaw) * (size/3)
        pygame.draw.circle(screen, MARIO_RED, (sx + brim_off_x, sy - size*0.3), size/2.5)
        # Body
        body_rect = pygame.Rect(sx - size/3, sy, size/1.5, size/1.5)
        pygame.draw.rect(screen, MARIO_BLUE, body_rect, border_radius=4)
        # Buttons
        pygame.draw.circle(screen, (255,255,0), (sx - size/6, sy + size/4), size/10)
        pygame.draw.circle(screen, (255,255,0), (sx + size/6, sy + size/4), size/10)

# ---------------- WORLD GEOMETRY ----------------
class Polygon3D:
    def __init__(self, points, color):
        self.points = points # List of (x, y, z)
        self.color = color

    def draw(self, screen, cam):
        projected_points = []
        for p in self.points:
            proj = cam.project(p[0], p[1], p[2])
            if not proj: return # Simple culling if any point is behind
            projected_points.append((proj[0], proj[1]))
        
        pygame.draw.polygon(screen, self.color, projected_points)

def build_castle_grounds():
    polys = []
    
    # 1. Main Grass Field (Large base)
    polys.append(Polygon3D([(-1000, 0, -1000), (1000, 0, -1000), (1000, 0, 1000), (-1000, 0, 1000)], GRASS_GREEN))
    
    # 2. Path to Castle
    polys.append(Polygon3D([(-150, -1, -600), (150, -1, -600), (150, -1, 400), (-150, -1, 400)], PATH_TAN))

    # 3. Moat (Blue surface slightly below grass)
    polys.append(Polygon3D([(-400, 10, -500), (400, 10, -500), (400, 10, -300), (-400, 10, -300)], MOAT_BLUE))
    
    # 4. Bridge
    polys.append(Polygon3D([(-100, -2, -500), (100, -2, -500), (100, -2, -300), (-100, -2, -300)], (139, 69, 19)))

    # 5. Castle Front Wall
    cw, ch, cd = 300, 300, -600
    polys.append(Polygon3D([(-cw, 0, cd), (cw, 0, cd), (cw, -ch, cd), (-cw, -ch, cd)], CASTLE_WHITE))
    
    # 6. Castle Tower (Central)
    tw, th = 100, 450
    polys.append(Polygon3D([(-tw, -ch, cd), (tw, -ch, cd), (tw, -th, cd), (-tw, -th, cd)], CASTLE_WHITE))
    
    # 7. Roof
    polys.append(Polygon3D([(-tw-20, -th, cd), (tw+20, -th, cd), (0, -th-100, cd)], ROOF_RED))

    return polys

# ---------------- SM64-STYLE MAIN MENU ----------------
def draw_main_menu():
    """SM64-style main menu: blue sky gradient, title, star, press start, copyright."""
    # Blue sky gradient (SM64: light top, darker bottom)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Gold star (SM64 logo star above title)
    star_cx, star_cy = WIDTH // 2, HEIGHT // 2 - 100
    star_outer = 50
    star_points = []
    for i in range(5):
        angle = math.pi / 2 + i * 2 * math.pi / 5
        star_points.append((
            star_cx + math.cos(angle) * star_outer,
            star_cy - math.sin(angle) * star_outer
        ))
    pygame.draw.polygon(screen, TITLE_GOLD, star_points)
    pygame.draw.polygon(screen, (200, 180, 0), star_points, 2)

    # Title: "Ultra Mario 3D Bros" — SM64 style (red outline, gold fill)
    title_text = "Ultra Mario 3D Bros"
    # Outline (multiple offsets for thick outline)
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            if dx == 0 and dy == 0:
                continue
            surf = font_title.render(title_text, True, TITLE_OUTLINE)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2 + dx, HEIGHT // 2 - 40 + dy))
    surf = font_title.render(title_text, True, TITLE_RED)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2 - 2, HEIGHT // 2 - 42))
    surf = font_title.render(title_text, True, TITLE_GOLD)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, HEIGHT // 2 - 40))

    # "Press SPACE to Start" (blinking like SM64)
    blink = (pygame.time.get_ticks() // 500) % 2
    if blink:
        start_text = font_menu.render("Press SPACE to Start", True, (255, 255, 255))
        screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 + 40))

    # Copyright line (SM64-style at bottom)
    copy_text = font.render("(C) Cat's 1999-2026  (C) Nintendo", True, (200, 200, 255))
    screen.blit(copy_text, (WIDTH // 2 - copy_text.get_width() // 2, HEIGHT - 50))

# ---------------- MAIN LOOP ----------------
mario = Mario()
cam = Camera()
world_polys = build_castle_grounds()

running = True
while running:
    # 1. Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    game_state = "playing"
                if event.key == pygame.K_ESCAPE:
                    running = False
            else:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Camera C-Buttons (Q/E)
                if event.key == pygame.K_q: cam.target_yaw -= math.pi / 2
                if event.key == pygame.K_e: cam.target_yaw += math.pi / 2

    if game_state == "menu":
        draw_main_menu()
        pygame.display.flip()
        clock.tick(FPS)
        continue

    # 2. Updates (playing)
    keys = pygame.key.get_pressed()
    mario.update(keys)
    cam.update(mario.x, mario.z)

    # 3. Render
    screen.fill(SKY_BLUE)
    
    # Sort polygons by depth (Painter's Algorithm)
    def get_poly_dist(poly):
        avg_x = sum(p[0] for p in poly.points) / len(poly.points)
        avg_z = sum(p[2] for p in poly.points) / len(poly.points)
        return (avg_x - cam.x)**2 + (avg_z - cam.z)**2
    
    world_polys.sort(key=get_poly_dist, reverse=True)

    # Draw World
    for poly in world_polys:
        poly.draw(screen, cam)

    # Draw Mario
    mario.draw(screen, cam)

    # UI / HUD
    ui_text = font.render(f"STAR: 0  x: {int(mario.x)} z: {int(mario.z)}", True, (255, 255, 255))
    screen.blit(ui_text, (20, 20))
    
    inst_text = font.render("ARROWS: Move | SPACE: Jump | Q/E: Rotate Camera", True, (255, 255, 0))
    screen.blit(inst_text, (20, HEIGHT - 40))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
