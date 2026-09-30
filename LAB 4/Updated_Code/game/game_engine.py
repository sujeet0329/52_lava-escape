import pygame
from game.player import Player
from game.world import generate_platforms, draw_lava, PLATFORM_COLOR, spawn_crumble_particles

WIDTH, HEIGHT = 500, 640
FPS = 60
BG = (20, 15, 30)
GROUND_Y = HEIGHT + 200

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Lava Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 42, bold=True)
        self.hud_font = pygame.font.SysFont("monospace", 14, bold=True)
        self.warning_font = pygame.font.SysFont(["segoeuiemoji", "segoeuisymbol", "arial", "monospace"], 24, bold=True)
        self.reset()

    def reset(self):
        self.platforms = generate_platforms(WIDTH, GROUND_Y)
        self.player = Player(WIDTH // 2 - 16, GROUND_Y - 50)
        self.cam_y = 0
        self.lava_y = GROUND_Y + 60
        self.lava_rise = 0.4
        self.score = 0
        self.game_over = False
        self.won = False
        self.top_y = self.platforms[-1].y
        self.frame = 0
        self.particles = []
        self.surge_timer = 0
        self.is_surging = False
        self.surge_duration = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
        return True

    def update(self):
        if self.game_over or self.won:
            return
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.platforms, WIDTH)

        # Camera vertical tracking
        target = self.player.rect.centery - HEIGHT // 2
        if target < self.cam_y:
            self.cam_y = target

        # Platform lifecycle (crumbling countdown, removal, dust particles)
        surviving = []
        for p in self.platforms:
            if hasattr(p, "update"):
                just_broke = p.update()
                if just_broke:
                    self.particles.extend(spawn_crumble_particles(p))
                if not getattr(p, "is_broken", False):
                    surviving.append(p)
            else:
                surviving.append(p)
        self.platforms = surviving

        # Particles update
        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles if pt.life > 0]

        # Task 4: Lava surge cycle (every 15s for 3s, lava speed accelerated ~2.8x)
        SURGE_INTERVAL = 15 * FPS
        SURGE_DURATION = 3 * FPS
        if not self.is_surging:
            self.surge_timer += 1
            if self.surge_timer >= SURGE_INTERVAL:
                self.is_surging = True
                self.surge_duration = SURGE_DURATION
                self.surge_timer = 0
        else:
            self.surge_duration -= 1
            if self.surge_duration <= 0:
                self.is_surging = False

        surge_mult = 2.8 if self.is_surging else 1.0
        current_rise = self.lava_rise * surge_mult
        self.lava_y -= current_rise
        self.lava_rise = min(1.2, self.lava_rise + 0.0003)

        self.score = max(0, (GROUND_Y - self.player.rect.y) // 10)
        self.frame += 1

        if self.player.rect.bottom >= self.lava_y:
            self.game_over = True
        if self.player.rect.top <= self.top_y - 20:
            self.won = True

    def _draw_danger_meter(self):
        mx, my, mw, mh = 310, 14, 175, 18
        surge_mult = 2.8 if self.is_surging else 1.0
        current_rise = self.lava_rise * surge_mult
        ratio = min(1.0, max(0.08, current_rise / 3.36))

        # Speed / Danger label
        lbl = self.hud_font.render(f"LAVA SPEED: {current_rise:.2f}x", True, (240, 215, 195))
        self.screen.blit(lbl, (mx, my - 16))

        # Meter background and frame
        pygame.draw.rect(self.screen, (35, 25, 42), (mx, my, mw, mh), border_radius=4)
        pygame.draw.rect(self.screen, (100, 75, 95), (mx, my, mw, mh), width=1, border_radius=4)

        # Danger meter fill
        if self.is_surging:
            fill_col = (255, 60, 30) if (self.frame // 6) % 2 == 0 else (255, 190, 30)
        elif ratio < 0.25:
            fill_col = (230, 185, 40)
        elif ratio < 0.5:
            fill_col = (245, 130, 30)
        else:
            fill_col = (235, 50, 25)

        fill_w = int((mw - 4) * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(mx + 2, my + 2, fill_w, mh - 4)
            pygame.draw.rect(self.screen, fill_col, fill_rect, border_radius=3)

    def _draw_surge_warning(self):
        text = "⚠️ LAVA SURGE! ⚠️"
        surf = self.warning_font.render(text, True, (255, 235, 50))
        pad_x, pad_y = 16, 8
        banner_w = surf.get_width() + pad_x * 2
        banner_h = surf.get_height() + pad_y * 2
        bx = WIDTH // 2 - banner_w // 2
        by = 68

        bg_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        bg_surf.fill((190, 25, 15, 215))
        self.screen.blit(bg_surf, (bx, by))
        pygame.draw.rect(self.screen, (255, 215, 40), (bx, by, banner_w, banner_h), width=2, border_radius=6)
        self.screen.blit(surf, (bx + pad_x, by + pad_y))

    def draw(self):
        self.screen.fill(BG)

        # Draw platforms
        for p in self.platforms:
            if hasattr(p, "draw"):
                p.draw(self.screen, self.cam_y)
            else:
                dr = p.move(0, -int(self.cam_y))
                pygame.draw.rect(self.screen, PLATFORM_COLOR, dr, border_radius=4)

        # Draw particles
        for pt in self.particles:
            pt.draw(self.screen, self.cam_y)

        # Draw player
        self.player.draw(self.screen, self.cam_y)

        # Draw lava
        draw_lava(self.screen, self.lava_y, self.cam_y, WIDTH, HEIGHT, self.frame)

        # HUD: Height Score and restart hint
        sc = self.font.render(f"Height: {self.score}m", True, (220, 200, 180))
        self.screen.blit(sc, (10, 8))
        rst_hint = self.hud_font.render("R = Restart", True, (160, 150, 160))
        self.screen.blit(rst_hint, (10, 34))

        # Lava Danger/Speed HUD meter
        self._draw_danger_meter()

        # Flashing Lava Surge Warning
        if self.is_surging and (self.surge_duration // 10) % 2 == 0:
            self._draw_surge_warning()

        if self.game_over:
            self._msg("LAVA GOT YOU!", (220, 80, 40))
        if self.won:
            self._msg("ESCAPED!", (80, 220, 100))
        pygame.display.flip()

    def _msg(self, text, color):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))
        m = self.big_font.render(text, True, color)
        s = self.font.render("Press R to Play Again", True, (200, 200, 200))
        self.screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 20))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
