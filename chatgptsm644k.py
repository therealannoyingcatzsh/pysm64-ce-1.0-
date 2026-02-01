import pygame
import math
import random

# Initialize Pygame
pygame.init()

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
FPS = 60

BG = (0, 0, 40)
FG = (220, 220, 255)
HL = (255, 255, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SUPER MARIO 64 - DEBUG COURSE SELECT")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier New", 18, bold=True)
title_font = pygame.font.SysFont("Courier New", 32, bold=True)

# ---------------- COURSE DATA ----------------
COURSES = [
    # (Name, Background Color, Icon Color, Theme Color)
    ("CASTLE GROUNDS", (50, 100, 150), (200, 180, 120), (100, 80, 60)),
    ("BOB-OMB BATTLEFIELD", (100, 150, 100), (255, 100, 100), (180, 100, 80)),
    ("WHOMP'S FORTRESS", (150, 120, 100), (200, 200, 200), (120, 100, 80)),
    ("JOLLY ROGER BAY", (60, 100, 180), (220, 220, 180), (180, 150, 120)),
    ("COOL, COOL MOUNTAIN", (200, 230, 255), (150, 200, 255), (100, 150, 200)),
    ("BIG BOO'S HAUNT", (30, 30, 50), (200, 180, 220), (80, 60, 100)),
    ("HAZY MAZE CAVE", (120, 80, 60), (180, 140, 100), (100, 60, 40)),
    ("LETHAL LAVA LAND", (180, 60, 40), (255, 200, 60), (220, 100, 60)),
    ("SHIFTING SAND LAND", (210, 180, 100), (255, 220, 150), (180, 140, 80)),
    ("DIRE, DIRE DOCKS", (40, 80, 160), (120, 180, 255), (80, 120, 200)),
    ("SNOWMAN'S LAND", (230, 240, 255), (200, 220, 240), (180, 200, 220)),
    ("WET-DRY WORLD", (100, 140, 180), (150, 200, 220), (120, 160, 200)),
    ("TALL, TALL MOUNTAIN", (120, 160, 120), (180, 220, 180), (140, 180, 140)),
    ("TINY-HUGE ISLAND", (180, 140, 100), (220, 180, 140), (160, 120, 80)),
    ("TICK TOCK CLOCK", (80, 80, 100), (200, 200, 180), (140, 140, 120)),
    ("RAINBOW RIDE", (180, 100, 180), (255, 220, 120), (220, 160, 200)),
]

STATE_DEBUG = 0
STATE_LEVEL = 1
STATE_CASTLE = 2

# ---------------- GAME STATE ----------------
cursor = 0
state = STATE_DEBUG
current_course = 0
level_timer = 0
particles = []
castle_rotation = 0

# ---------------- PARTICLE SYSTEM ----------------
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 6)
        self.speed_x = random.uniform(-2, 2)
        self.speed_y = random.uniform(-2, 2)
        self.life = random.randint(30, 60)
        
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size *= 0.98
        return self.life > 0
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

# ---------------- DRAWING FUNCTIONS ----------------
def draw_castle(surface, x, y, scale=1.0):
    """Draw a simple castle icon"""
    # Castle base
    base_rect = pygame.Rect(x - 40*scale, y - 30*scale, 80*scale, 60*scale)
    pygame.draw.rect(surface, (200, 200, 220), base_rect, border_radius=int(5*scale))
    
    # Towers
    for i in range(-1, 2):
        tower_x = x + i * 20 * scale
        tower_rect = pygame.Rect(tower_x - 10*scale, y - 60*scale, 20*scale, 30*scale)
        pygame.draw.rect(surface, (180, 180, 200), tower_rect, border_radius=int(3*scale))
        
        # Tower top
        top_rect = pygame.Rect(tower_x - 8*scale, y - 70*scale, 16*scale, 10*scale)
        pygame.draw.rect(surface, (220, 220, 240), top_rect, border_radius=int(2*scale))
        
    # Door
    door_rect = pygame.Rect(x - 15*scale, y - 10*scale, 30*scale, 30*scale)
    pygame.draw.rect(surface, (160, 140, 120), door_rect, border_radius=int(3*scale))

def draw_level_icon(surface, x, y, course_index, selected=False):
    """Draw an icon representing the level"""
    bg_color, icon_color, theme_color = COURSES[course_index][1:]
    
    # Background
    rect = pygame.Rect(x - 60, y - 40, 120, 80)
    pygame.draw.rect(surface, bg_color, rect, border_radius=10)
    if selected:
        pygame.draw.rect(surface, HL, rect, 3, border_radius=10)
    
    # Level-specific icon
    if course_index == 0:  # Castle Grounds
        draw_castle(surface, x, y, 0.5)
    elif course_index == 1:  # Bob-omb Battlefield
        pygame.draw.circle(surface, icon_color, (x, y), 20)
        pygame.draw.circle(surface, theme_color, (x, y), 15)
    elif course_index == 2:  # Whomp's Fortress
        points = [(x, y-25), (x-20, y+15), (x+20, y+15)]
        pygame.draw.polygon(surface, icon_color, points)
    elif course_index == 3:  # Jolly Roger Bay
        pygame.draw.ellipse(surface, icon_color, (x-25, y-15, 50, 30))
        pygame.draw.ellipse(surface, theme_color, (x-15, y-5, 30, 20))
    elif course_index == 4:  # Cool Cool Mountain
        points = [(x, y-25), (x-25, y+15), (x+25, y+15)]
        pygame.draw.polygon(surface, icon_color, points)
    elif course_index == 5:  # Big Boo's Haunt
        pygame.draw.circle(surface, icon_color, (x, y), 25)
        pygame.draw.circle(surface, theme_color, (x, y), 20)
        # Eyes
        pygame.draw.circle(surface, (255, 255, 255), (x-8, y-5), 6)
        pygame.draw.circle(surface, (255, 255, 255), (x+8, y-5), 6)
    elif course_index == 6:  # Hazy Maze Cave
        pygame.draw.rect(surface, icon_color, (x-20, y-20, 40, 40))
        pygame.draw.rect(surface, theme_color, (x-10, y-10, 20, 20))
    elif course_index == 7:  # Lethal Lava Land
        pygame.draw.circle(surface, icon_color, (x, y), 25)
        # Lava waves
        for i in range(3):
            y_offset = y + 5 + i * 8
            pygame.draw.arc(surface, (255, 100, 0), (x-20, y_offset-5, 40, 10), 
                           math.pi, 2*math.pi, 3)
    elif course_index == 8:  # Shifting Sand Land
        pygame.draw.ellipse(surface, icon_color, (x-30, y-15, 60, 30))
        # Dunes
        pygame.draw.arc(surface, theme_color, (x-25, y-5, 50, 20), 0, math.pi, 5)
    elif course_index == 9:  # Dire Dire Docks
        pygame.draw.rect(surface, icon_color, (x-25, y-10, 50, 20))
        # Water ripple
        for i in range(3):
            radius = 15 + i * 5
            pygame.draw.circle(surface, theme_color, (x, y), radius, 1)
    elif course_index == 10:  # Snowman's Land
        pygame.draw.circle(surface, icon_color, (x, y), 20)
        pygame.draw.circle(surface, (240, 240, 250), (x, y-15), 15)
    elif course_index == 11:  # Wet-Dry World
        pygame.draw.rect(surface, icon_color, (x-25, y-20, 50, 40))
        # Water level
        water_height = 20
        pygame.draw.rect(surface, theme_color, (x-25, y, 50, water_height))
    elif course_index == 12:  # Tall Tall Mountain
        for i in range(3):
            height = 25 - i * 5
            width = 40 - i * 10
            pygame.draw.polygon(surface, icon_color, 
                              [(x, y-height), (x-width//2, y), (x+width//2, y)])
    elif course_index == 13:  # Tiny-Huge Island
        size = 25 if course_index % 2 == 0 else 15
        pygame.draw.circle(surface, icon_color, (x, y), size)
        pygame.draw.circle(surface, theme_color, (x, y), size-5)
    elif course_index == 14:  # Tick Tock Clock
        pygame.draw.circle(surface, icon_color, (x, y), 25)
        # Clock hands
        angle = pygame.time.get_ticks() / 1000
        hand_length = 20
        end_x = x + hand_length * math.cos(angle)
        end_y = y + hand_length * math.sin(angle)
        pygame.draw.line(surface, theme_color, (x, y), (end_x, end_y), 3)
    elif course_index == 15:  # Rainbow Ride
        colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                 (0, 255, 0), (0, 0, 255), (75, 0, 130), (238, 130, 238)]
        for i, color in enumerate(colors):
            rect = pygame.Rect(x-30 + i*4, y-20, 8, 40)
            pygame.draw.rect(surface, color, rect)

def draw_star(surface, x, y, size, color):
    """Draw a star shape"""
    points = []
    for i in range(5):
        angle = math.pi/2 + i * 2*math.pi/5
        outer_x = x + size * math.cos(angle)
        outer_y = y + size * math.sin(angle)
        inner_x = x + size/2 * math.cos(angle + math.pi/5)
        inner_y = y + size/2 * math.sin(angle + math.pi/5)
        points.extend([(outer_x, outer_y), (inner_x, inner_y)])
    pygame.draw.polygon(surface, color, points)

def draw_debug_menu():
    """Draw the debug course selection menu"""
    # Background
    screen.fill(BG)
    
    # Title
    title = title_font.render("SUPER MARIO 64 - DEBUG COURSE SELECT", True, HL)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
    
    # Course grid (4x4)
    for i, (name, bg_color, icon_color, theme_color) in enumerate(COURSES):
        row = i // 4
        col = i % 4
        
        x = 100 + col * 200
        y = 100 + row * 120
        
        # Draw icon
        draw_level_icon(screen, x, y, i, i == cursor)
        
        # Draw course number and name
        num_text = font.render(f"{i:02d}", True, FG if i != cursor else HL)
        name_text = font.render(name, True, FG if i != cursor else HL)
        
        screen.blit(num_text, (x - num_text.get_width()//2, y + 50))
        screen.blit(name_text, (x - name_text.get_width()//2, y + 70))
        
        # Add particles for selected course
        if i == cursor:
            for _ in range(2):
                particles.append(Particle(
                    x + random.randint(-30, 30),
                    y + random.randint(-30, 30),
                    HL
                ))
    
    # Draw particles
    for particle in particles[:]:
        if particle.update():
            particle.draw(screen)
        else:
            particles.remove(particle)
    
    # Hints
    hint1 = font.render("UP/DOWN/LEFT/RIGHT: SELECT    ENTER: LOAD COURSE", True, FG)
    hint2 = font.render("ESC: RETURN TO CASTLE    F1: RELOAD TEXTURES", True, FG)
    screen.blit(hint1, (WIDTH//2 - hint1.get_width()//2, HEIGHT - 60))
    screen.blit(hint2, (WIDTH//2 - hint2.get_width()//2, HEIGHT - 35))

def draw_level_view():
    """Draw the selected level view"""
    bg_color, icon_color, theme_color = COURSES[current_course][1:]
    
    # Animated background gradient
    for y in range(0, HEIGHT, 2):
        progress = y / HEIGHT
        r = int(bg_color[0] * (1 - progress) + 0 * progress)
        g = int(bg_color[1] * (1 - progress) + 0 * progress)
        b = int(bg_color[2] * (1 - progress) + 20 * progress)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    
    # Draw floating stars
    for i in range(10):
        x = (pygame.time.get_ticks() / 100 + i * 50) % WIDTH
        y = 100 + 50 * math.sin(pygame.time.get_ticks() / 1000 + i)
        size = 5 + 3 * math.sin(pygame.time.get_ticks() / 500 + i)
        draw_star(screen, x, y, size, icon_color)
    
    # Level info panel
    panel_rect = pygame.Rect(50, 50, 300, 200)
    pygame.draw.rect(screen, (0, 0, 0, 128), panel_rect)
    pygame.draw.rect(screen, theme_color, panel_rect, 3)
    
    # Level info text
    course_num = font.render(f"COURSE {current_course:02d}", True, HL)
    course_name = font.render(COURSES[current_course][0], True, FG)
    
    screen.blit(course_num, (70, 70))
    screen.blit(course_name, (70, 100))
    
    # Timer
    minutes = level_timer // 3600
    seconds = (level_timer // 60) % 60
    timer_text = font.render(f"TIME: {minutes:02d}:{seconds:02d}", True, FG)
    screen.blit(timer_text, (70, 140))
    
    # Stars collected (placeholder)
    stars = font.render("STARS: 0/7", True, FG)
    screen.blit(stars, (70, 170))
    
    # Draw level icon
    draw_level_icon(screen, 500, 200, current_course, True)
    
    # Control hints
    hint1 = font.render("ARROWS: MOVE    SPACE: JUMP    Z: ACTION", True, FG)
    hint2 = font.render("ESC: RETURN TO DEBUG MENU", True, FG)
    screen.blit(hint1, (WIDTH//2 - hint1.get_width()//2, HEIGHT - 80))
    screen.blit(hint2, (WIDTH//2 - hint2.get_width()//2, HEIGHT - 40))

def draw_castle_view():
    """Draw Peach's Castle view"""
    # Sky gradient
    for y in range(0, HEIGHT):
        progress = y / HEIGHT
        r = int(100 * (1 - progress) + 0 * progress)
        g = int(150 * (1 - progress) + 50 * progress)
        b = int(255 * (1 - progress) + 100 * progress)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    
    # Ground
    pygame.draw.rect(screen, (100, 80, 60), (0, HEIGHT-100, WIDTH, 100))
    
    # Draw castle with rotation
    castle_center_x = WIDTH // 2
    castle_center_y = HEIGHT // 2
    
    # Castle base
    base_points = [
        (castle_center_x - 100, castle_center_y + 50),
        (castle_center_x - 60, castle_center_y - 50),
        (castle_center_x + 60, castle_center_y - 50),
        (castle_center_x + 100, castle_center_y + 50)
    ]
    pygame.draw.polygon(screen, (200, 200, 220), base_points)
    
    # Main tower
    tower_rect = pygame.Rect(castle_center_x - 30, castle_center_y - 150, 60, 100)
    pygame.draw.rect(screen, (180, 180, 200), tower_rect, border_radius=10)
    
    # Tower top
    tower_top = pygame.Rect(castle_center_x - 20, castle_center_y - 180, 40, 30)
    pygame.draw.rect(screen, (220, 220, 240), tower_top, border_radius=5)
    
    # Side towers
    for offset in [-80, 80]:
        side_tower = pygame.Rect(castle_center_x + offset - 20, castle_center_y - 100, 40, 50)
        pygame.draw.rect(screen, (190, 190, 210), side_tower, border_radius=8)
    
    # Moons
    for i in range(3):
        angle = pygame.time.get_ticks() / 2000 + i * 2 * math.pi / 3
        moon_x = castle_center_x + 200 * math.cos(angle)
        moon_y = castle_center_y - 100 + 50 * math.sin(angle)
        pygame.draw.circle(screen, (255, 255, 200), (int(moon_x), int(moon_y)), 15)
    
    # Title
    title = title_font.render("PEACH'S CASTLE", True, (255, 220, 180))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    # Hint
    hint = font.render("PRESS ENTER FOR DEBUG MENU", True, FG)
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 50))

# ---------------- MAIN LOOP ----------------
running = True
while running:
    dt = clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if state == STATE_CASTLE:
                if event.key == pygame.K_RETURN:
                    state = STATE_DEBUG
            
            elif state == STATE_DEBUG:
                if event.key == pygame.K_UP:
                    cursor = max(0, cursor - 4)
                if event.key == pygame.K_DOWN:
                    cursor = min(len(COURSES)-1, cursor + 4)
                if event.key == pygame.K_LEFT:
                    cursor = (cursor - 1) % len(COURSES)
                if event.key == pygame.K_RIGHT:
                    cursor = (cursor + 1) % len(COURSES)
                if event.key == pygame.K_RETURN:
                    current_course = cursor
                    level_timer = 0
                    state = STATE_LEVEL
                if event.key == pygame.K_ESCAPE:
                    state = STATE_CASTLE
                if event.key == pygame.K_F1:
                    # Reload/refresh effect
                    for _ in range(50):
                        particles.append(Particle(
                            random.randint(0, WIDTH),
                            random.randint(0, HEIGHT),
                            random.choice([(255, 255, 0), (255, 200, 0), (255, 150, 0)])
                        ))
            
            elif state == STATE_LEVEL:
                if event.key == pygame.K_ESCAPE:
                    state = STATE_DEBUG
                # Add gameplay controls here
                if event.key == pygame.K_SPACE:
                    # Jump effect
                    for _ in range(20):
                        particles.append(Particle(
                            WIDTH//2 + random.randint(-50, 50),
                            HEIGHT - 100,
                            (255, 255, 200)
                        ))

    # ---------------- UPDATE ----------------
    if state == STATE_LEVEL:
        level_timer += 1
    
    castle_rotation += 0.5
    
    # ---------------- DRAW ----------------
    if state == STATE_DEBUG:
        draw_debug_menu()
    elif state == STATE_LEVEL:
        draw_level_view()
    elif state == STATE_CASTLE:
        draw_castle_view()
    
    # ---------------- FPS COUNTER ----------------
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, FG)
    screen.blit(fps_text, (10, HEIGHT - 30))
    
    pygame.display.flip()

pygame.quit()
