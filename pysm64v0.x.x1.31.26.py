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
    # SM64 1:1 camera: 52° FOV, spherical orbit, pitch limits (N64-style)
    FOV_DEG = 52
    FOV_RAD = math.radians(FOV_DEG)
    CAM_DIST = 550
    PITCH_MIN = math.radians(-28)
    PITCH_MAX = math.radians(62)
    CAM_LAG = 0.08
    FOV = WIDTH / (2 * math.tan(FOV_RAD / 2))  # horizontal FOV scale

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
    # Course colors
    LAVA_RED      = (180, 40, 20)
    SAND_TAN      = (220, 180, 120)
    SNOW_WHITE    = (240, 248, 255)
    WATER_BLUE    = (50, 100, 200, 180)
    CAVE_GRAY     = (90, 90, 100)
    BOO_PURPLE    = (100, 60, 140)
    RAINBOW_PINK  = (255, 180, 200)
    WOOD_BROWN    = (139, 90, 43)

    # ---------------- GLOBALS (set in run(); no external files) ----------------
    screen = None
    clock = None
    font = None
    font_title = None
    font_menu = None
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
        """SM64 1:1 Lakitu camera: spherical orbit, 52° FOV, pitch limits."""
        def __init__(self):
            self.x, self.y, self.z = 0, 200, 0
            self.yaw = 0
            self.pitch = math.radians(15)
            self.target_yaw = 0
            self.target_pitch = math.radians(15)

        def update(self, target_x, target_y, target_z):
            # Lakitu: camera orbits target at CAM_DIST, smooth lag
            self.target_pitch = max(PITCH_MIN, min(PITCH_MAX, self.target_pitch))
            self.yaw += (self.target_yaw - self.yaw) * CAM_LAG
            self.pitch += (self.target_pitch - self.pitch) * CAM_LAG
            # Spherical position (SM64: camera behind and above Mario)
            dx = math.cos(self.pitch) * math.sin(self.yaw)
            dy = math.sin(self.pitch)
            dz = math.cos(self.pitch) * math.cos(self.yaw)
            desired_x = target_x - dx * CAM_DIST
            desired_y = target_y + dy * CAM_DIST
            desired_z = target_z - dz * CAM_DIST
            self.x += (desired_x - self.x) * CAM_LAG
            self.y += (desired_y - self.y) * CAM_LAG
            self.z += (desired_z - self.z) * CAM_LAG

        def project(self, x, y, z):
            """Project 3D to 2D with SM64 FOV; camera space uses yaw+pitch."""
            rx, ry, rz = x - self.x, y - self.y, z - self.z
            # Rotate by -yaw (Y axis)
            sy, cy = math.sin(-self.yaw), math.cos(-self.yaw)
            rx, rz = rx * cy - rz * sy, rx * sy + rz * cy
            # Rotate by -pitch (X axis, so look up/down)
            sp, cp = math.sin(-self.pitch), math.cos(-self.pitch)
            ry, rz = ry * cp - rz * sp, ry * sp + rz * cp
            if rz <= 1:
                return None
            scale = FOV / rz
            sx = WIDTH // 2 + rx * scale
            sy = HEIGHT // 2 + ry * scale
            return (sx, sy, scale)

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

    def build_bobomb_battlefield():
        polys = []
        polys.append(Polygon3D([(-800, 0, -800), (800, 0, -800), (800, 0, 800), (-800, 0, 800)], GRASS_GREEN))
        polys.append(Polygon3D([(-200, 0, -200), (200, 0, -200), (200, 0, 200), (-200, 0, 200)], PATH_TAN))
        polys.append(Polygon3D([(-80, 0, 100), (80, 0, 100), (80, 80, 100), (-80, 80, 100)], CASTLE_WHITE))
        polys.append(Polygon3D([(-80, 80, 100), (80, 80, 100), (0, 120, 100)], ROOF_RED))
        return polys

    def build_whomps_fortress():
        polys = []
        polys.append(Polygon3D([(-600, 0, -600), (600, 0, -600), (600, 0, 600), (-600, 0, 600)], GRASS_GREEN))
        polys.append(Polygon3D([(-250, 0, -250), (250, 0, -250), (250, 0, 250), (-250, 0, 250)], WOOD_BROWN))
        polys.append(Polygon3D([(-200, 0, 0), (200, 0, 0), (200, 200, 0), (-200, 200, 0)], CASTLE_WHITE))
        polys.append(Polygon3D([(-150, 200, -50), (150, 200, -50), (150, 200, 50), (-150, 200, 50)], PATH_TAN))
        return polys

    def build_jolly_roger_bay():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], (40, 80, 120)))
        polys.append(Polygon3D([(-300, 5, -300), (300, 5, -300), (300, 5, 300), (-300, 5, 300)], WATER_BLUE[:3]))
        polys.append(Polygon3D([(-150, 10, -100), (150, 10, -100), (150, 10, 100), (-150, 10, 100)], SAND_TAN))
        polys.append(Polygon3D([(-80, 10, 0), (80, 10, 0), (80, 60, 0), (-80, 60, 0)], CASTLE_WHITE))
        return polys

    def build_cool_cool_mountain():
        polys = []
        polys.append(Polygon3D([(-800, 0, -800), (800, 0, -800), (800, 0, 800), (-800, 0, 800)], SNOW_WHITE))
        polys.append(Polygon3D([(-200, 0, -200), (200, 0, -200), (200, 0, 200), (-200, 0, 200)], (200, 220, 240)))
        polys.append(Polygon3D([(-100, 0, 150), (100, 0, 150), (100, 150, 150), (-100, 150, 150)], CASTLE_WHITE))
        polys.append(Polygon3D([(-100, 150, 150), (100, 150, 150), (0, 200, 150)], ROOF_RED))
        return polys

    def build_big_boos_haunt():
        polys = []
        polys.append(Polygon3D([(-600, 0, -600), (600, 0, -600), (600, 0, 600), (-600, 0, 600)], CAVE_GRAY))
        polys.append(Polygon3D([(-200, 0, -200), (200, 0, -200), (200, 0, 200), (-200, 0, 200)], BOO_PURPLE))
        polys.append(Polygon3D([(-120, 0, 0), (120, 0, 0), (120, 120, 0), (-120, 120, 0)], (60, 40, 80)))
        polys.append(Polygon3D([(-80, 120, -40), (80, 120, -40), (80, 120, 40), (-80, 120, 40)], PATH_TAN))
        return polys

    def build_hazy_maze_cave():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], CAVE_GRAY))
        polys.append(Polygon3D([(-300, 0, -300), (300, 0, -300), (300, 0, 300), (-300, 0, 300)], (70, 75, 85)))
        polys.append(Polygon3D([(-150, 0, 100), (150, 0, 100), (150, 80, 100), (-150, 80, 100)], WOOD_BROWN))
        polys.append(Polygon3D([(-100, 80, 80), (100, 80, 80), (100, 80, 120), (-100, 80, 120)], PATH_TAN))
        return polys

    def build_lethal_lava_land():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], (50, 30, 30)))
        polys.append(Polygon3D([(-400, 15, -400), (400, 15, -400), (400, 15, 400), (-400, 15, 400)], LAVA_RED))
        polys.append(Polygon3D([(-180, 15, -180), (180, 15, -180), (180, 15, 180), (-180, 15, 180)], WOOD_BROWN))
        polys.append(Polygon3D([(-80, 15, 0), (80, 15, 0), (80, 95, 0), (-80, 95, 0)], CASTLE_WHITE))
        return polys

    def build_shifting_sand_land():
        polys = []
        polys.append(Polygon3D([(-800, 0, -800), (800, 0, -800), (800, 0, 800), (-800, 0, 800)], SAND_TAN))
        polys.append(Polygon3D([(-250, 0, -250), (250, 0, -250), (250, 0, 250), (-250, 0, 250)], (200, 160, 100)))
        polys.append(Polygon3D([(-100, 0, 120), (100, 0, 120), (100, 100, 120), (-100, 100, 120)], CASTLE_WHITE))
        polys.append(Polygon3D([(-60, 100, 100), (60, 100, 100), (60, 100, 140), (-60, 100, 140)], PATH_TAN))
        return polys

    def build_dire_dire_docks():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], (30, 60, 120)))
        polys.append(Polygon3D([(-350, 8, -350), (350, 8, -350), (350, 8, 350), (-350, 8, 350)], (50, 100, 200)))
        polys.append(Polygon3D([(-120, 8, -120), (120, 8, -120), (120, 8, 120), (-120, 8, 120)], PATH_TAN))
        polys.append(Polygon3D([(-60, 8, 0), (60, 8, 0), (60, 68, 0), (-60, 68, 0)], CASTLE_WHITE))
        return polys

    def build_snowmans_land():
        polys = []
        polys.append(Polygon3D([(-800, 0, -800), (800, 0, -800), (800, 0, 800), (-800, 0, 800)], SNOW_WHITE))
        polys.append(Polygon3D([(-220, 0, -220), (220, 0, -220), (220, 0, 220), (-220, 0, 220)], (220, 240, 255)))
        polys.append(Polygon3D([(-100, 0, 150), (100, 0, 150), (100, 100, 150), (-100, 100, 150)], CASTLE_WHITE))
        polys.append(Polygon3D([(-80, 100, 130), (80, 100, 130), (80, 100, 170), (-80, 100, 170)], PATH_TAN))
        return polys

    def build_wet_dry_world():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], (100, 120, 80)))
        polys.append(Polygon3D([(-300, 5, -300), (300, 5, -300), (300, 5, 300), (-300, 5, 300)], (60, 100, 180)))
        polys.append(Polygon3D([(-150, 5, -150), (150, 5, -150), (150, 5, 150), (-150, 5, 150)], SAND_TAN))
        polys.append(Polygon3D([(-70, 5, 0), (70, 5, 0), (70, 75, 0), (-70, 75, 0)], CASTLE_WHITE))
        return polys

    def build_tall_tall_mountain():
        polys = []
        polys.append(Polygon3D([(-800, 0, -800), (800, 0, -800), (800, 0, 800), (-800, 0, 800)], GRASS_GREEN))
        polys.append(Polygon3D([(-300, 0, -300), (300, 0, -300), (300, 0, 300), (-300, 0, 300)], (80, 140, 80)))
        polys.append(Polygon3D([(-120, 0, 200), (120, 0, 200), (120, 250, 200), (-120, 250, 200)], CASTLE_WHITE))
        polys.append(Polygon3D([(-100, 250, 180), (100, 250, 180), (100, 250, 220), (-100, 250, 220)], PATH_TAN))
        polys.append(Polygon3D([(-80, 250, 200), (80, 250, 200), (0, 300, 200)], ROOF_RED))
        return polys

    def build_tiny_huge_island():
        polys = []
        polys.append(Polygon3D([(-600, 0, -600), (600, 0, -600), (600, 0, 600), (-600, 0, 600)], GRASS_GREEN))
        polys.append(Polygon3D([(-200, 0, -200), (200, 0, -200), (200, 0, 200), (-200, 0, 200)], (60, 130, 60)))
        polys.append(Polygon3D([(-100, 0, 100), (100, 0, 100), (100, 120, 100), (-100, 120, 100)], CASTLE_WHITE))
        polys.append(Polygon3D([(-80, 120, 80), (80, 120, 80), (80, 120, 120), (-80, 120, 120)], PATH_TAN))
        return polys

    def build_tick_tock_clock():
        polys = []
        polys.append(Polygon3D([(-500, 0, -500), (500, 0, -500), (500, 0, 500), (-500, 0, 500)], CAVE_GRAY))
        polys.append(Polygon3D([(-200, 0, -200), (200, 0, -200), (200, 0, 200), (-200, 0, 200)], (100, 100, 110)))
        polys.append(Polygon3D([(-80, 0, 0), (80, 0, 0), (80, 100, 0), (-80, 100, 0)], WOOD_BROWN))
        polys.append(Polygon3D([(-60, 100, -20), (60, 100, -20), (60, 100, 20), (-60, 100, 20)], PATH_TAN))
        return polys

    def build_rainbow_ride():
        polys = []
        polys.append(Polygon3D([(-700, 0, -700), (700, 0, -700), (700, 0, 700), (-700, 0, 700)], SKY_BLUE))
        polys.append(Polygon3D([(-300, 50, -300), (300, 50, -300), (300, 50, 300), (-300, 50, 300)], RAINBOW_PINK))
        polys.append(Polygon3D([(-100, 50, 0), (100, 50, 0), (100, 150, 0), (-100, 150, 0)], (255, 200, 220)))
        polys.append(Polygon3D([(-80, 150, -30), (80, 150, -30), (80, 150, 30), (-80, 150, 30)], PATH_TAN))
        return polys

    # (name, builder, spawn_x, spawn_y, spawn_z, ground_y)
    LEVELS = [
        ("Castle Grounds", build_castle_grounds, 0, 0, 0, 0),
        ("Bob-omb Battlefield", build_bobomb_battlefield, 0, 0, 0, 0),
        ("Whomp's Fortress", build_whomps_fortress, 0, 0, 0, 0),
        ("Jolly Roger Bay", build_jolly_roger_bay, 0, 20, 0, 10),
        ("Cool Cool Mountain", build_cool_cool_mountain, 0, 0, 0, 0),
        ("Big Boo's Haunt", build_big_boos_haunt, 0, 0, 0, 0),
        ("Hazy Maze Cave", build_hazy_maze_cave, 0, 0, 0, 0),
        ("Lethal Lava Land", build_lethal_lava_land, 0, 25, 0, 15),
        ("Shifting Sand Land", build_shifting_sand_land, 0, 0, 0, 0),
        ("Dire Dire Docks", build_dire_dire_docks, 0, 18, 0, 8),
        ("Snowman's Land", build_snowmans_land, 0, 0, 0, 0),
        ("Wet-Dry World", build_wet_dry_world, 0, 15, 0, 5),
        ("Tall Tall Mountain", build_tall_tall_mountain, 0, 0, 0, 0),
        ("Tiny Huge Island", build_tiny_huge_island, 0, 0, 0, 0),
        ("Tick Tock Clock", build_tick_tock_clock, 0, 0, 0, 0),
        ("Rainbow Ride", build_rainbow_ride, 0, 60, 0, 50),
    ]

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

    def draw_course_select(sel):
        screen.fill(SKY_BOTTOM)
        t = font_title.render("Select Course", True, TITLE_GOLD)
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 30))
        for i, (name, _, _, _, _, _) in enumerate(LEVELS):
            y = 90 + i * 32
            r = pygame.Rect(80, y - 4, WIDTH - 160, 28)
            color = (120, 200, 100) if i == sel else GRASS_GREEN
            pygame.draw.rect(screen, color, r, border_radius=6)
            pygame.draw.rect(screen, BLACK, r, 2, border_radius=6)
            txt = font.render(f"{i+1}. {name}", True, WHITE)
            screen.blit(txt, (100, y))
        hint = font.render("1-9/0: Select  ENTER: Play  ESC: Back", True, (200, 200, 255))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 36))

    def get_course_click(pos):
        for i in range(len(LEVELS)):
            y = 90 + i * 32
            r = pygame.Rect(80, y - 4, WIDTH - 160, 28)
            if r.collidepoint(pos):
                return i
        return None

    # ---------------- MAIN LOOP (run entry point) ----------------
    def run():
        """Run Ultra Mario 3D Bros. No external files; all rendering in-code."""
        global screen, clock, font, font_title, font_menu, game_state
        global mario, cam, world_polys
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption("Ultra Mario 3D Bros - pysm64")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 18, bold=True)
        font_title = pygame.font.SysFont("Arial", 48, bold=True)
        font_menu = pygame.font.SysFont("Arial", 24, bold=True)
        game_state = "menu"
        course_sel = 0
        current_level_name = ""
        mario = Mario()
        cam = Camera()
        world_polys = build_castle_grounds()

        def load_level(idx):
            nonlocal world_polys, current_level_name
            name, builder, sx, sy, sz, ground_y = LEVELS[idx]
            world_polys = builder()
            mario.x, mario.y, mario.z = sx, sy, sz
            mario.ground_y = ground_y
            mario.vel_fwd = 0
            mario.vel_y = 0
            cam.x, cam.y, cam.z = mario.x, mario.y + 200, mario.z + 300
            cam.yaw = 0
            cam.pitch = math.radians(15)
            cam.target_yaw = 0
            cam.target_pitch = math.radians(15)
            current_level_name = name

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if game_state == "menu":
                        if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                            game_state = "course_select"
                        if event.key == pygame.K_ESCAPE:
                            running = False
                    elif game_state == "course_select":
                        if event.key == pygame.K_ESCAPE:
                            game_state = "menu"
                        elif event.key == pygame.K_RETURN:
                            load_level(course_sel)
                            game_state = "playing"
                        elif event.key == pygame.K_0 or event.key == pygame.K_KP0:
                            course_sel = min(9, len(LEVELS) - 1)
                        elif pygame.K_1 <= event.key <= pygame.K_9 or (pygame.K_KP1 <= event.key <= pygame.K_KP9):
                            k = (event.key - pygame.K_1) if event.key <= pygame.K_9 else (event.key - pygame.K_KP1)
                            course_sel = min(k, len(LEVELS) - 1)
                        elif event.key == pygame.K_UP:
                            course_sel = max(0, course_sel - 1)
                        elif event.key == pygame.K_DOWN:
                            course_sel = min(len(LEVELS) - 1, course_sel + 1)
                    elif game_state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            game_state = "course_select"
                        if event.key == pygame.K_q:
                            cam.target_yaw -= math.pi / 2
                        if event.key == pygame.K_e:
                            cam.target_yaw += math.pi / 2
                        if event.key == pygame.K_r:
                            cam.target_pitch = max(PITCH_MIN, cam.target_pitch + math.radians(12))
                        if event.key == pygame.K_f:
                            cam.target_pitch = min(PITCH_MAX, cam.target_pitch - math.radians(12))
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state == "course_select":
                    idx = get_course_click(event.pos)
                    if idx is not None:
                        course_sel = idx
                        load_level(course_sel)
                        game_state = "playing"

            if game_state == "menu":
                draw_main_menu()
                pygame.display.flip()
                clock.tick(FPS)
                continue
            if game_state == "course_select":
                draw_course_select(course_sel)
                pygame.display.flip()
                clock.tick(FPS)
                continue

            keys = pygame.key.get_pressed()
            mario.update(keys)
            cam.update(mario.x, mario.y, mario.z)

            screen.fill(SKY_BLUE)

            def get_poly_dist(poly):
                ax = sum(p[0] for p in poly.points) / len(poly.points)
                ay = sum(p[1] for p in poly.points) / len(poly.points)
                az = sum(p[2] for p in poly.points) / len(poly.points)
                return (ax - cam.x)**2 + (ay - cam.y)**2 + (az - cam.z)**2

            world_polys.sort(key=get_poly_dist, reverse=True)
            for poly in world_polys:
                poly.draw(screen, cam)
            mario.draw(screen, cam)

            ui_text = font.render(f"{current_level_name}  STAR: 0  x: {int(mario.x)} z: {int(mario.z)}", True, (255, 255, 255))
            screen.blit(ui_text, (20, 20))
            inst_text = font.render("ARROWS: Move | SPACE: Jump | Q/E: Yaw | R/F: Pitch", True, (255, 255, 0))
            screen.blit(inst_text, (20, HEIGHT - 40))

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()


    if __name__ == "__main__":
        run()
        sys.exit(0)
