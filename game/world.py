import pygame
import random

PLATFORM_COLOR = (100, 80, 50)
LAVA_COLOR = (220, 60, 20)

class Particle:
    def __init__(self, x, y, vx, vy, color, size, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.35
        self.life -= 1

    def draw(self, screen, cam_y):
        if self.life > 0:
            alpha_ratio = self.life / self.max_life
            s = int(max(1, self.size * alpha_ratio))
            pygame.draw.rect(screen, self.color, (int(self.x), int(self.y - cam_y), s, s))

def spawn_crumble_particles(platform):
    particles = []
    dust_colors = [(130, 110, 95), (150, 120, 105), (100, 85, 75), (180, 150, 130)]
    for _ in range(16):
        px = random.randint(platform.left, platform.right)
        py = random.randint(platform.top, platform.bottom)
        vx = random.uniform(-2.5, 2.5)
        vy = random.uniform(-3.5, 0.5)
        color = random.choice(dust_colors)
        size = random.randint(3, 6)
        life = random.randint(25, 45)
        particles.append(Particle(px, py, vx, vy, color, size, life))
    return particles

class Platform(pygame.Rect):
    def __init__(self, x, y, width, height, kind="normal"):
        super().__init__(x, y, width, height)
        self.kind = kind
        self.triggered = False
        self.crumble_timer = 60  # 1 second at 60 FPS
        self.is_broken = False
        self.shake_offset = 0
        self.spring_recoil = 0

    def on_player_land(self, player):
        if self.kind == "crumbling":
            if not self.triggered:
                self.triggered = True
        elif self.kind == "spring":
            player.vel_y = -22
            player.on_ground = False
            self.spring_recoil = 14

    def update(self):
        just_broke = False
        if self.kind == "crumbling" and self.triggered and not self.is_broken:
            self.crumble_timer -= 1
            if self.crumble_timer > 0:
                self.shake_offset = random.randint(-3, 3)
            else:
                self.is_broken = True
                self.shake_offset = 0
                just_broke = True
        if self.spring_recoil > 0:
            self.spring_recoil -= 1
        return just_broke

    def draw(self, screen, cam_y):
        dr = pygame.Rect(self.x + self.shake_offset, int(self.y - cam_y), self.width, self.height)

        if self.kind == "normal":
            pygame.draw.rect(screen, PLATFORM_COLOR, dr, border_radius=4)
            pygame.draw.line(screen, (135, 110, 75), (dr.left + 2, dr.top + 1), (dr.right - 2, dr.top + 1), 2)

        elif self.kind == "crumbling":
            # Weathered cracked stone aesthetic
            base_col = (120, 100, 90)
            if self.triggered:
                progress = 1.0 - (self.crumble_timer / 60.0)
                r = int(min(255, 120 + progress * 70))
                g = int(max(0, 100 - progress * 40))
                b = int(max(0, 90 - progress * 40))
                base_col = (r, g, b)
            pygame.draw.rect(screen, base_col, dr, border_radius=3)
            # Crack lines
            crack_color = (60, 45, 40)
            mid_x = dr.centerx
            pygame.draw.line(screen, crack_color, (mid_x - 12, dr.top + 2), (mid_x - 4, dr.top + 7), 1)
            pygame.draw.line(screen, crack_color, (mid_x - 4, dr.top + 7), (mid_x + 6, dr.bottom - 2), 1)
            if dr.width > 120:
                pygame.draw.line(screen, crack_color, (dr.left + 20, dr.top + 3), (dr.left + 30, dr.bottom - 4), 1)
                pygame.draw.line(screen, crack_color, (dr.right - 30, dr.top + 2), (dr.right - 20, dr.bottom - 3), 1)

        elif self.kind == "spring":
            # Distinct yellow spring platform with coil & recoil compression
            SPRING_YELLOW = (250, 210, 40)
            SPRING_BASE = (170, 140, 20)
            compression = int(min(6, self.spring_recoil * 0.7)) if self.spring_recoil > 0 else 0

            # Base plate
            base_rect = pygame.Rect(dr.x, dr.y + dr.height - 4, dr.width, 4)
            pygame.draw.rect(screen, SPRING_BASE, base_rect, border_radius=2)

            # Central metal spring coil
            cx = dr.centerx
            top_y = dr.y + compression + 4
            bot_y = dr.bottom - 4
            coil_pts = [
                (cx - 9, bot_y),
                (cx + 9, bot_y - 2),
                (cx - 9, top_y + 2),
                (cx + 9, top_y)
            ]
            pygame.draw.lines(screen, (220, 220, 230), False, coil_pts, 2)

            # Bouncy yellow top pad
            pad_h = max(5, dr.height - 4 - compression)
            top_rect = pygame.Rect(dr.x, dr.y + compression, dr.width, pad_h)
            pygame.draw.rect(screen, SPRING_YELLOW, top_rect, border_radius=4)
            pygame.draw.line(screen, (255, 245, 140), (top_rect.left + 3, top_rect.top + 1), (top_rect.right - 3, top_rect.top + 1), 2)

def generate_platforms(width, base_y, count=30):
    # Ground platform (always normal)
    plats = [Platform(0, base_y, width, 20, kind="normal")]
    y = base_y - 110

    # Distribute: ~23% crumbling (7), ~17% spring (5), remainder normal (17)
    # Platforms 1 through 29 are intermediate, platform 30 (top) is always normal
    kinds = ["crumbling"] * 7 + ["spring"] * 5 + ["normal"] * 17
    random.shuffle(kinds)

    # Avoid consecutive crumbling platforms to ensure fair pathing
    for idx in range(len(kinds) - 1):
        if kinds[idx] == "crumbling" and kinds[idx + 1] == "crumbling":
            for swap_idx in range(idx + 2, len(kinds)):
                if kinds[swap_idx] != "crumbling":
                    kinds[idx + 1], kinds[swap_idx] = kinds[swap_idx], kinds[idx + 1]
                    break

    for i in range(count):
        w = random.randint(80, 200)
        x = random.randint(0, width - w)
        # The final top platform (victory) is always normal
        p_kind = "normal" if i == count - 1 else kinds[i]
        plats.append(Platform(x, y, w, 16, kind=p_kind))
        y -= random.randint(80, 130)

    return plats

def draw_lava(screen, lava_y, cam_y, width, height, frame):
    import math
    ly = int(lava_y - cam_y)
    if ly < height:
        # lava surface wave
        pts = [(0, ly)]
        for x in range(0, width + 20, 20):
            pts.append((x, ly + int(math.sin(x * 0.08 + frame * 0.1) * 8)))
        pts.append((width, height))
        pts.append((0, height))
        pygame.draw.polygon(screen, LAVA_COLOR, pts)
        # glow
        s = pygame.Surface((width, 30), pygame.SRCALPHA)
        for i in range(15):
            pygame.draw.line(s, (255, 100, 0, max(0, 60 - i * 4)), (0, i), (width, i), 1)
        screen.blit(s, (0, ly - 15))
