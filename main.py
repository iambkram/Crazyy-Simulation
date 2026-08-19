import pygame
import random
import sys
import json
import os
import math

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)

from settings import *

# ==========================================
# SCREEN SETUP (must happen before any image loading)
# ==========================================
WIDTH = 800
HEIGHT = 600

try:
    game_icon = pygame.image.load('icon.ico')
    pygame.display.set_icon(game_icon)
except:
    pass

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Crazyy Simulation")

# Import only fonts and helper functions from assets (no heavy images yet)
from assets import *
from branding import CinematicBranding
from menu_battle import MenuBattleSimulation
from vfx import VisualEffectsEngine

# ==========================================
# MINIMAL BOOTSTRAP ASSETS (tiny, needed before loading screen)
# ==========================================
_loading_bg_raw = pygame.image.load("game_assets/loading_bg.jpeg").convert()
loading_bg = pygame.transform.scale(_loading_bg_raw, (WIDTH, HEIGHT))

# ==========================================
# REAL PROGRESSIVE LOADING SYSTEM
# ==========================================
# Each task is (label_string, callable)
# We call each task during the loading screen, rendering progress between each one.

_load_results = {}   # will hold all loaded assets by name

def _make_load_tasks():
    """Returns an ordered list of (label, callable) for every real asset."""
    tasks = []
    ASSETS_DIR = "game_assets"

    def _img(name, size=None):
        path = os.path.join(ASSETS_DIR, name)
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size) if size else img

    def _snd(name):
        return pygame.mixer.Sound(os.path.join(ASSETS_DIR, name))

    # --- Backgrounds (heaviest files) ---
    tasks.append(("Loading Galaxy background...",      lambda: _img("galaxy.jpg", (WIDTH, HEIGHT))))
    tasks.append(("Loading Nebula background...",      lambda: _img("nebula.jpg", (WIDTH, HEIGHT))))
    tasks.append(("Loading Stars background...",       lambda: _img("stars.jpg", (WIDTH, HEIGHT))))
    tasks.append(("Loading Black Hole background...",  lambda: _img("blackhole.png", (WIDTH, HEIGHT))))
    tasks.append(("Loading Menu background...",        lambda: _img("menu_bg.jpeg", (WIDTH, HEIGHT))))

    # --- Ship sprites ---
    tasks.append(("Loading Player ship...",   lambda: _img("6B.png", (70, 70))))
    tasks.append(("Loading Fighter enemy...", lambda: _img("1.png", (50, 50))))
    tasks.append(("Loading Elite enemy...",   lambda: _img("3B.png", (60, 60))))
    tasks.append(("Loading Heavy enemy...",   lambda: _img("8B.png", (80, 80))))

    # --- Boss images ---
    boss_files = ["lvl_1_to_10.png", "lvl_11_to_20.png", "lvl_21_to_30.png", "lvl_31_to_40.png"]
    for i in range(1, 9):
        idx = min((i - 1) // 2, 3)
        fname = boss_files[idx]
        tier = i
        tasks.append((f"Loading Boss Tier {tier}...", lambda f=fname, t=tier: pygame.transform.scale(_img(f), (140 + t * 15, 100 + t * 10))))

    # --- UI icons ---
    tasks.append(("Loading Coin icon...",   lambda: pygame.transform.scale(_img("coin.png"), (40, 40))))
    tasks.append(("Loading Star icon...",   lambda: _img("star.png")))
    tasks.append(("Loading Lock icon...",   lambda: pygame.transform.scale(pygame.image.load("game_assets/lock.png"), (90, 90))))
    tasks.append(("Loading Asteroid...",    lambda: pygame.image.load("game_assets/asteroid.png").convert_alpha()))

    # --- Sound effects ---
    tasks.append(("Loading Shoot SFX...",   lambda: _snd("shoot.mp3")))
    tasks.append(("Loading Hit SFX...",     lambda: _snd("hit.mp3")))
    tasks.append(("Loading Explosion SFX...", lambda: _snd("expl.mp3")))
    tasks.append(("Loading Boss Explosion SFX...", lambda: _snd("boss_expl.mp3")))
    tasks.append(("Loading UI Tap SFX...",  lambda: _snd("tap.mp3")))
    tasks.append(("Loading Victory SFX...", lambda: _snd("game_won.mp3")))
    tasks.append(("Loading Defeat SFX...",  lambda: _snd("game_loose.mp3")))

    # --- BGM paths (just string paths, no actual load needed) ---
    tasks.append(("Preparing BGM tracks...", lambda: {
        "loading":  os.path.join(ASSETS_DIR, "loading.mp3"),
        "main":     os.path.join(ASSETS_DIR, "bgm_main.mp3"),
        "fast":     os.path.join(ASSETS_DIR, "bgm_fast.mp3"),
    }))

    return tasks


def run_loading_screen():
    """
    Runs the full loading screen with real progressive asset loading.
    Returns a dict of all loaded assets.
    """
    global loading_bg
    tasks = _make_load_tasks()
    total   = len(tasks)
    results = {}

    # Animated star particles for the loading background
    ldr_stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT),
                  random.uniform(0.3, 1.5), random.randint(60, 200)] for _ in range(120)]

    clock = pygame.time.Clock()

    # Start loading BGM immediately
    try:
        pygame.mixer.music.load("game_assets/loading.mp3")
        pygame.mixer.music.play(-1)
    except:
        pass

    label_text  = "Initializing..."
    done_count  = 0
    pulse_t     = 0       # for pulsing glow on bar
    particle_t  = 0       # for floating particles on bar

    for idx, (label, task_fn) in enumerate(tasks):
        label_text = label

        # ---- Do the real work ----
        results[idx] = task_fn()
        done_count   = idx + 1

        # ---- Render one frame of the loading screen ----
        pygame.event.pump()           # keep OS happy
        progress_frac = done_count / total
        pulse_t += 0.08

        # Background
        screen.blit(loading_bg, (0, 0))
        dark_ovr = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark_ovr.fill((0, 0, 20, 185))
        screen.blit(dark_ovr, (0, 0))

        # Animated stars
        for s in ldr_stars:
            s[1] += s[2]
            if s[1] > HEIGHT:
                s[0] = random.randint(0, WIDTH)
                s[1] = 0
            alpha = min(255, s[3])
            r = max(1, int(s[2] * 1.5))
            col = (int(120 + 135 * (s[3] / 255)), int(180 + 75 * (s[3] / 255)), 255)
            pygame.draw.circle(screen, col, (int(s[0]), int(s[1])), r)

        # Title
        draw_text("CRAZYY SIMULATION", FONT_TITLE, CYAN, WIDTH // 2, 190)

        # Subtle sub-title glow
        import math as _math
        glow_alpha = int(140 + 110 * _math.sin(pulse_t))
        subtitle_col = (glow_alpha, glow_alpha, 255)
        draw_text("INITIALIZING GAME SYSTEMS", FONT_MODAL_SUB, subtitle_col, WIDTH // 2, 235)

        # ---- Progress bar track ----
        bar_x, bar_y, bar_w, bar_h = 140, 310, 520, 22
        bar_radius = 11

        # Track shadow
        pygame.draw.rect(screen, (5, 5, 20), (bar_x + 3, bar_y + 3, bar_w, bar_h), border_radius=bar_radius)
        # Track background
        pygame.draw.rect(screen, (30, 35, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=bar_radius)
        # Track inner border
        pygame.draw.rect(screen, (60, 70, 100), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=bar_radius)

        # Filled portion
        fill_w = int(bar_w * progress_frac)
        if fill_w > 4:
            # Gradient: cyan → blue
            fill_surf = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            for px in range(fill_w):
                t = px / max(fill_w - 1, 1)
                r = int(0   + 0   * t)
                g = int(230 - 120 * t)
                b = int(255)
                pygame.draw.line(fill_surf, (r, g, b, 230), (px, 0), (px, bar_h))
            # Clip to rounded rect shape
            mask_surf = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            pygame.draw.rect(mask_surf, (255, 255, 255, 255), (0, 0, fill_w, bar_h), border_radius=bar_radius)
            fill_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(fill_surf, (bar_x, bar_y))

            # Pulse glow shimmer at tip
            shimmer_x = bar_x + fill_w - 12
            shimmer_alpha = int(100 + 100 * _math.sin(pulse_t * 3))
            if shimmer_alpha > 0 and fill_w > 20:
                sh_surf = pygame.Surface((28, bar_h), pygame.SRCALPHA)
                for px in range(28):
                    a = max(0, shimmer_alpha - abs(px - 14) * 12)
                    pygame.draw.line(sh_surf, (255, 255, 255, a), (px, 0), (px, bar_h))
                screen.blit(sh_surf, (shimmer_x, bar_y))

        # Percentage text
        pct_str = f"{int(progress_frac * 100)}%"
        draw_text(pct_str, FONT_UI, WHITE, WIDTH // 2, bar_y + bar_h + 26)

        # Status label
        draw_text(label_text, FONT_SMALL, (160, 200, 255), WIDTH // 2, bar_y + bar_h + 60)

        # Step counter  e.g. "12 / 28"
        draw_text(f"{done_count} / {total}", FONT_HP, (100, 130, 180), WIDTH // 2, bar_y + bar_h + 86)

        pygame.display.flip()
        clock.tick(60)

    # Final flash to white
    for alpha in range(0, 255, 18):
        screen.blit(loading_bg, (0, 0))
        flash = pygame.Surface((WIDTH, HEIGHT))
        flash.fill((255, 255, 255))
        flash.set_alpha(alpha)
        screen.blit(flash, (0, 0))
        pygame.display.flip()
        pygame.time.wait(12)

    return results


# ==========================================
# RUN LOADING — results stored in _load_results
# ==========================================
_load_results = run_loading_screen()

# ==========================================
# UNPACK LOADED ASSETS INTO GLOBAL NAMES
# ==========================================
_i = 0
galaxy_bg        = _load_results[_i]; _i += 1
nebula_bg        = _load_results[_i]; _i += 1
stars_bg         = _load_results[_i]; _i += 1
blackhole_bg     = _load_results[_i]; _i += 1
menu_bg          = _load_results[_i]; _i += 1

player_img       = _load_results[_i]; _i += 1
fighter_img      = _load_results[_i]; _i += 1
elite_img        = _load_results[_i]; _i += 1
heavy_img        = _load_results[_i]; _i += 1

boss_surfs = {}
for _tier in range(1, 9):
    boss_surfs[_tier] = _load_results[_i]; _i += 1

coin_icon        = _load_results[_i]; _i += 1
star_for_rating  = _load_results[_i]; _i += 1
lock_icon        = _load_results[_i]; _i += 1
asteroid_img     = _load_results[_i]; _i += 1

shoot_snd        = _load_results[_i]; _i += 1
hit_snd          = _load_results[_i]; _i += 1
expl_snd         = _load_results[_i]; _i += 1
boss_expl_snd    = _load_results[_i]; _i += 1
tap_snd          = _load_results[_i]; _i += 1
game_won_snd     = _load_results[_i]; _i += 1
game_loose_snd   = _load_results[_i]; _i += 1

_bgm_paths       = _load_results[_i]; _i += 1
loading_bgm      = _bgm_paths["loading"]
game_bgm_main    = _bgm_paths["main"]
game_bgm_fast    = _bgm_paths["fast"]

bullet_img = pygame.Surface((6, 15))
bullet_img.fill(BLUE)

del _load_results, _i, _bgm_paths, _tier

# ==========================================
# MAIN MENU AUTONOMOUS LIVE BATTLE BACKGROUND
# ==========================================
menu_battle_sim = MenuBattleSimulation({
    'player_img': player_img,
    'fighter_img': fighter_img,
    'elite_img': elite_img,
    'heavy_img': heavy_img,
    'galaxy_bg': galaxy_bg,
    'nebula_bg': nebula_bg,
    'blackhole_bg': blackhole_bg,
    'shoot_snd': shoot_snd,
    'expl_snd': expl_snd,
    'hit_snd': hit_snd
})

# ==========================================
# VISUAL EFFECTS ENGINE (Thrusters & Supernova Boss Cataclysm)
# ==========================================
vfx_engine = VisualEffectsEngine()

# --- Variables ---
kill_count = 0
total_coins = 0
unlocked_hp, hp_step = 200, 0
unlocked_speed, speed_step = 7, 0
unlocked_bullets, bullet_step = 1, 0
max_galaxy_level = 1
max_nebula_level = 1
max_blackhole_level = 1
level_scroll_y = 0
control_type = 'PC'
show_settings_warning = False
fire_cooldown = 0
click_cooldown = 0
ui_pulse_t = 0.0       # Global animation ticker for button glow effects
music_vol = 0.5
sfx_vol = 0.7
is_dragging_music = False
is_dragging_sfx = False
mission_scroll_y = 0
is_dragging_missions = False
last_mouse_y = 0
touch_start_y = 0
touch_start_x = 0
total_drag_dist = 0
m_u = False
settings_from_pause = False
level_coins = 0
warning_target = ""
revives_done_this_level = 0
show_revive_confirm = False
revive_protection_timer = 0
# Navigation & Unlocking Variables 🔥
current_selected_env = 1 # 1: Galaxy, 2: Nebula, 3: Blackhole
env1_unlocked = True     # Galaxy (default unlocked)
env2_unlocked = False    # 🔒 Nebula
env3_unlocked = False    # 🔒 Blackhole
loose_snd_played = False
win_snd_played = False
galaxy_bg_y = 0.0
galaxy_bg_speed = 0.05
bg_height = galaxy_bg.get_height()

store_selection = None
current_level, selected_level = 1, 1
player_health = 200
blackhole_alert_active = False

# Boss Timers and States
boss_active, boss_arriving = False, False
boss_warning_timer = 0
boss_defeated_timer = 0
boss_hp, boss_max_hp = 100, 100
boss_death_timer = 0

asteroid_group = pygame.sprite.Group()

# Spawning logic variables
asteroids_spawned = 0
spawn_timer = 0
next_spawn_time = random.randint(3000, 7000)
last_spawn_tick = pygame.time.get_ticks()

fighters, elites, heavies, bullets, enemy_bullets, achievements, particles = [], [], [], [], [], [], []
current_boss_img = None

skills = {
    'immortal': {'active': False, 'timer': 0, 'duration': 5000, 'color': MAGENTA, 'label': 'SHIELD'},
    'double': {'active': False, 'timer': 0, 'duration': 5000, 'color': CYAN, 'label': 'POWER SHOT'}
}

player_rect = player_img.get_rect(center=(WIDTH // 2, HEIGHT - 60))
boss_rect = pygame.Rect(0, 0, 0, 0)
boss_target_x = WIDTH // 2

# Stars Initialization
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(4.0, 10.0), random.randint(100, 255)] for _ in range(160)]

# --- Background Scrolling Variables ---
bg_y1 = 0
bg_y2 = -HEIGHT
bg_scroll_speed = 1.5

# States definition
STATE_MAIN_MENU   = 0
STATE_ENV_SELECT  = 20
STATE_LEVEL_SELECT = 1

# Keyboard Focus & Navigation System
focused_btn = 0          # Index of currently focused button on active screen
key_enter = False        # True on the frame Enter/Return was pressed
key_escape = False       # True on the frame Escape was pressed
key_up = False           # True on the frame Up/W was pressed (menu nav)
key_down = False         # True on the frame Down/S was pressed (menu nav)
key_left = False         # True on the frame Left/A was pressed (menu nav)
key_right = False        # True on the frame Right/A was pressed (menu nav)
key_tab = False          # True on the frame Tab was pressed
key_p = False            # True on the frame P was pressed (pause toggle)
key_r = False            # True on the frame R was pressed (retry shortcut)

# Display & Performance Settings
is_fullscreen = True     # Game starts in fullscreen mode
show_fps = False         # FPS counter overlay toggle
visual_quality = 'high'  # 'low', 'medium', 'high'
screen_shake_enabled = True  # Screen shake effects toggle

# --- Start at branding animation (assets are already loaded) ---
state = -2
branding_anim = CinematicBranding()
last_frame_ticks = pygame.time.get_ticks()

SAVE_FILE = "save.json"

# --- SAVE/LOAD SYSTEM ---
def save_game():
    data = {
        "coins": total_coins,
        "hp": unlocked_hp,
        "hp_step": hp_step,
        "speed": unlocked_speed,
        "speed_step": speed_step,
        "bullets": unlocked_bullets,
        "bullet_step": bullet_step,
        "max_galaxy_level": max_galaxy_level,
        "max_nebula_level": max_nebula_level,
        "max_blackhole_level": max_blackhole_level,
        "env2_unlocked": env2_unlocked or (max_galaxy_level > 30),
        "env3_unlocked": env3_unlocked or (max_nebula_level > 30),
        "control_type": control_type,
        "music_vol": music_vol,
        "sfx_vol": sfx_vol,
        "show_fps": show_fps,
        "visual_quality": visual_quality,
        "screen_shake": screen_shake_enabled,
        "display_mode": "fullscreen" if is_fullscreen else "windowed"
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Save error:", e)


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, asteroid_img, env=1):
        super().__init__()
        scale_factor = random.choice([1, 1.4, 1.8])
        base_size = 46
        new_size = int(base_size * scale_factor)

        self.original_image = pygame.transform.scale(asteroid_img, (new_size, new_size))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.env = env

        if env == 3:
            # Spawn along outer screen periphery in Black Hole environment
            side = random.choice(['top', 'left', 'right', 'bottom'])
            if side == 'top':
                self.pos_x = float(random.randint(0, WIDTH - self.rect.width))
                self.pos_y = float(-self.rect.height)
            elif side == 'left':
                self.pos_x = float(-self.rect.width)
                self.pos_y = float(random.randint(0, HEIGHT - self.rect.height))
            elif side == 'right':
                self.pos_x = float(WIDTH)
                self.pos_y = float(random.randint(0, HEIGHT - self.rect.height))
            else:
                self.pos_x = float(random.randint(0, WIDTH - self.rect.width))
                self.pos_y = float(HEIGHT)
            self.speed = random.uniform(1.0, 2.2)
        else:
            self.pos_x = float(random.randint(0, WIDTH - self.rect.width))
            self.pos_y = float(-self.rect.height)
            self.speed = random.uniform(3.0, 5.5)

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
        self.angle = 0
        self.rot_speed = random.uniform(-1.0, 1.0)

    def update(self):
        if self.env == 3:
            # Gravitational pull towards singularity at (400, 300)
            center_x = self.pos_x + self.original_image.get_width() / 2.0
            center_y = self.pos_y + self.original_image.get_height() / 2.0
            dx = 400 - center_x
            dy = 300 - center_y
            dist = math.hypot(dx, dy)
            if dist < 26:
                self.kill()
                return
            pull = self.speed + (90.0 / (dist + 50.0))
            self.pos_x += (dx / dist) * pull
            self.pos_y += (dy / dist) * pull
        else:
            self.pos_y += self.speed
            if self.pos_y > HEIGHT:
                self.kill()
                return

        self.angle += self.rot_speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=(int(self.pos_x + self.original_image.get_width() / 2), int(self.pos_y + self.original_image.get_height() / 2)))


def get_revive_price(level, revives_done):
    """Calculate revive cost based on sector tier and number of revives used."""
    if 1 <= level <= 10:
        prices = [100, 200, 400, 800, 1000]
        if revives_done < len(prices):
            return prices[revives_done]
        else:
            return 1000 + (revives_done - 4) * 200  # 1000, 1200, 1400...

    elif 11 <= level <= 30:
        prices = [100, 500, 1000]
        if revives_done < len(prices):
            return prices[revives_done]
        else:
            return 1000 + (revives_done - 2) * 500  # 1000, 1500, 2000...

    elif 31 <= level <= 40:
        # Exponential scaling for master tier sectors
        return 500 * (2 ** revives_done)

    return 100  # Safe fallback cost

def load_game():
    global music_vol, sfx_vol, tap_snd
    global total_coins, unlocked_hp, hp_step, unlocked_speed, speed_step
    global unlocked_bullets, bullet_step, max_galaxy_level, max_nebula_level, max_blackhole_level, control_type
    global env1_unlocked, env2_unlocked, env3_unlocked
    global show_fps, visual_quality, screen_shake_enabled, is_fullscreen

    # Safe Defaults for new players (Galaxy Lvl 1 only unlocked)
    max_galaxy_level = 1
    max_nebula_level = 1
    max_blackhole_level = 1
    env1_unlocked = True
    env2_unlocked = False
    env3_unlocked = False

    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                total_coins = data.get("coins", 0)
                unlocked_hp = data.get("hp", 200)
                hp_step = data.get("hp_step", 0)
                unlocked_speed = data.get("speed", 7)
                speed_step = data.get("speed_step", 0)
                unlocked_bullets = data.get("bullets", 1)
                bullet_step = data.get("bullet_step", 0)
                max_galaxy_level = max(1, min(40, data.get("max_galaxy_level", 1)))
                max_nebula_level = max(1, min(40, data.get("max_nebula_level", 1)))
                max_blackhole_level = max(1, min(40, data.get("max_blackhole_level", 1)))
                control_type = data.get("control_type", 'PC')
                music_vol = data.get("music_vol", 0.5)
                sfx_vol = data.get("sfx_vol", 0.7)
                show_fps = data.get("show_fps", False)
                visual_quality = data.get("visual_quality", "high")
                screen_shake_enabled = data.get("screen_shake", True)
                is_fullscreen_str = data.get("display_mode", "fullscreen")
                is_fullscreen = (is_fullscreen_str == "fullscreen")
                
                # Unlock criteria: 30 levels of preceding environment must be completed
                env1_unlocked = True
                env2_unlocked = data.get("env2_unlocked", False) or (max_galaxy_level > 30)
                env3_unlocked = data.get("env3_unlocked", False) or (max_nebula_level > 30)

                if music_vol is None: music_vol = 0.5
                if sfx_vol is None: sfx_vol = 0.7

                pygame.mixer.music.set_volume(music_vol)
                tap_snd.set_volume(sfx_vol)
                expl_snd.set_volume(sfx_vol)
                hit_snd.set_volume(sfx_vol)
                boss_expl_snd.set_volume(sfx_vol)
                game_won_snd.set_volume(sfx_vol)
                game_loose_snd.set_volume(sfx_vol)
        except Exception as e:
            print("Error loading game:", e)


def reset_level_logic(level):
    global current_level, player_health, player_rect, bullets, enemy_bullets
    global fighters, elites, heavies, achievements, particles
    global boss_hp, boss_max_hp, boss_death_timer, current_level, boss_rect, kill_count
    global boss_active, boss_arriving, boss_target_x, current_boss_img
    global boss_warning_timer, boss_defeated_timer
    global blackhole_alert_active, revive_protection_timer
    global galaxy_bg_y

    galaxy_bg_y = 0.0

    current_level = level
    player_health = unlocked_hp
    player_rect.center = (WIDTH // 2, HEIGHT - 70)

    bullets.clear()
    enemy_bullets.clear()
    fighters.clear()
    elites.clear()
    heavies.clear()
    achievements.clear()
    particles.clear()
    vfx_engine.reset_boss_effects()

    # Reset Black Hole alert popup for sector 3
    blackhole_alert_active = (current_selected_env == 3)
    revive_protection_timer = 0

    kill_count = 0
    boss_target_x = WIDTH // 2

    reset_match()

    boss_active = False
    boss_arriving = False
    boss_warning_timer = 0
    boss_defeated_timer = 0
    boss_death_timer = 0

    # Boss HP scaling
    boss_max_hp = 800 + (current_level * 150)
    boss_hp = boss_max_hp

    # Tier calculation based on level (1-40)
    boss_tier = min(((current_level - 1) // 5) + 1, 8)
    current_boss_img = boss_surfs.get(boss_tier, boss_surfs[1])
    boss_rect = current_boss_img.get_rect(center=(WIDTH // 2, -150))

    for s in skills: skills[s]['active'] = False

def update_coins(amount):
    global total_coins, level_coins
    total_coins += amount
    level_coins += amount
    save_game()

def reset_match():
    """Reset match entity counts and clear asteroid groups."""
    global asteroids_spawned, asteroids_spawned_in_match
    asteroids_spawned = 0
    asteroids_spawned_in_match = 0
    asteroid_group.empty()

def check_enemy_spawn(new_rect, all_enemies):
    """Check collision against existing enemies to prevent spawn overlap."""
    for e in all_enemies:
        if new_rect.colliderect(e['rect']):
            return False
    return True

load_game()

# --- Main Loop ---
clock = pygame.time.Clock()
running = True

current_bgm = None
pygame.mixer.music.set_volume(music_vol)

while running:
    current_frame_ticks = pygame.time.get_ticks()
    dt = (current_frame_ticks - last_frame_ticks)/(1000/60)
    last_frame_ticks = current_frame_ticks

    screen.fill(BLACK)
    now = pygame.time.get_ticks()
    m_p = pygame.mouse.get_pos()
    m_c = False

    # ==========================================
    # GLOBAL MUSIC CONTROLLER
    # ==========================================
    if state == -2:
        target_bgm = None
    elif state == -1:
        screen.blit(loading_bg, (0, 0))
        target_bgm = "loading"
    elif state == 3:
        target_bgm = "fast"
    else:
        target_bgm = "main"

    if target_bgm == "loading" and current_bgm != "loading":
        pygame.mixer.music.load(loading_bgm)
        pygame.mixer.music.play(0)  # Single playback
        current_bgm = "loading"
    elif target_bgm == "fast" and current_bgm != "fast":
        pygame.mixer.music.load(game_bgm_fast)
        pygame.mixer.music.play(-1) # Loop playback
        current_bgm = "fast"
    elif target_bgm == "main" and current_bgm != "main":
        pygame.mixer.music.load(game_bgm_main)
        pygame.mixer.music.play(-1) # Loop playback
        current_bgm = "main"
    # =============================================================

    m_c = False
    m_u = False

    # Reset single-frame keyboard flags
    key_enter = False
    key_escape = False
    key_up = False
    key_down = False
    key_left = False
    key_right = False
    key_tab = False
    key_p = False
    key_r = False

    ui_pulse_t += 0.05   # Drives hover glow pulsation across all UI

    if click_cooldown > 0:
        click_cooldown -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and click_cooldown <= 0:
                m_c = True
            if event.button == 4: level_scroll_y = min(0, level_scroll_y + 30)
            if event.button == 5: level_scroll_y = max(-850, level_scroll_y - 30)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                m_u = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                # Toggle fullscreen / windowed
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
            elif event.key == pygame.K_ESCAPE:
                key_escape = True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                key_enter = True
            elif event.key in (pygame.K_UP, pygame.K_w):
                if state != 3:  # Don't consume in gameplay (handled by get_pressed)
                    key_up = True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if state != 3:
                    key_down = True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if state != 3:
                    key_left = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if state != 3:
                    key_right = True
            elif event.key == pygame.K_TAB:
                key_tab = True
            elif event.key == pygame.K_f:
                if state != 3:  # F key toggles FPS outside gameplay
                    show_fps = not show_fps
            elif event.key == pygame.K_m:
                if state != 3:  # M key mutes/unmutes music
                    if music_vol > 0:
                        music_vol = 0.0
                    else:
                        music_vol = 0.5
                    pygame.mixer.music.set_volume(music_vol)
            elif event.key == pygame.K_p:
                key_p = True
            elif event.key == pygame.K_r:
                key_r = True

    # ==========================================
    # 🔥 3. CINEMATIC NEON BRANDING (STATE -2) 🔥
    # ==========================================
    if state == -2:
        branding_anim.update_and_draw(
            screen, dt, now,
            tap_snd=tap_snd,
            hit_snd=hit_snd,
            expl_snd=expl_snd
        )

        # Allow instant skip via mouse click or Space/Enter/Escape keys
        keys = pygame.key.get_pressed()
        if m_c or keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or keys[pygame.K_ESCAPE]:
            branding_anim.skip()

        if branding_anim.is_finished():
            state = 0  # Transition smoothly into Main Menu
            click_cooldown = 12
            m_c = False

    # ==========================
    # MAIN MENU (STATE 0)
    # ==========================
    elif state == 0:
        # Live autonomous combat simulation in selected environment (freezes when navigating away)
        menu_battle_sim.update(dt=dt, current_env=current_selected_env)
        menu_battle_sim.draw(screen, current_env=current_selected_env)

        mx, my = pygame.mouse.get_pos()

        # ---- TITLE ----
        title_glow = FONT_TITLE.render("CRAZYY SIMULATION", True, NEON_CYAN)
        glow_surf = pygame.Surface(title_glow.get_size(), pygame.SRCALPHA)
        glow_surf.blit(title_glow, (0, 0))
        glow_surf.set_alpha(int(60 + 30 * math.sin(ui_pulse_t * 2)))
        screen.blit(glow_surf, title_glow.get_rect(center=(401, 86)))
        draw_text_shadow("CRAZYY SIMULATION", FONT_TITLE, NEON_CYAN, 400, 84, shadow_color=(0, 80, 120), offset=3)
        draw_text("GALAXY WARFARE  ·  SURVIVAL EDITION", FONT_TINY, (80, 130, 180), 400, 120)

        # ---- COIN BADGE (top center) ----
        coin_panel = pygame.Rect(318, 138, 164, 36)
        pygame.draw.rect(screen, (14, 16, 28), coin_panel, border_radius=18)
        pygame.draw.rect(screen, NEON_GOLD, coin_panel, width=1, border_radius=18)
        screen.blit(coin_icon, (326, 130))
        draw_text(str(total_coins), FONT_UI, NEON_GOLD, 395, 156)

        # ---- MENU BUTTONS ----
        menu_btns = [
            ("🚀  MISSIONS",  NEON_BLUE,    210, STATE_ENV_SELECT),
            ("🛒  STORE",     (140, 40, 200), 282, 6),
            ("⚙   SETTINGS", NEON_ORANGE,   354, 9),
            ("✕  QUIT",      NEON_PINK,      426, 0),
        ]

        # Keyboard navigation for menu
        if key_down or key_tab:
            focused_btn = (focused_btn + 1) % len(menu_btns)
        if key_up:
            focused_btn = (focused_btn - 1) % len(menu_btns)
        if key_escape:
            running = False

        for idx, (txt, col, y, target) in enumerate(menu_btns):
            btn_rect = pygame.Rect(250, y, 300, 62)
            is_hover = btn_rect.collidepoint(mx, my)
            is_focused = (idx == focused_btn)
            if is_hover:
                focused_btn = idx  # Mouse overrides keyboard focus
            draw_glowing_button(screen, txt, FONT_UI, WHITE, btn_rect, col, is_hover or is_focused,
                                border_radius=16, accent=NEON_CYAN, pulse_t=ui_pulse_t)
            # Keyboard focus indicator
            if is_focused and not is_hover:
                focus_surf = pygame.Surface((btn_rect.width + 8, btn_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(focus_surf, (*NEON_CYAN, 90), focus_surf.get_rect(), border_radius=18, width=2)
                screen.blit(focus_surf, (btn_rect.x - 4, btn_rect.y - 4))

            activated = (m_c and is_hover) or (key_enter and is_focused)
            if activated:
                if txt.endswith("QUIT"):
                    running = False
                elif ("MISSIONS" in txt or "STORE" in txt) and control_type is None:
                    tap_snd.play()
                    win_snd_played = False
                    loose_snd_played = False
                    show_settings_warning = True
                    click_cooldown = 12
                    m_c = False
                else:
                    tap_snd.play()
                    state = target
                    click_cooldown = 12
                    m_c = False

        # ---- VERSION TAG ----
        draw_text("v1.0.0  |  @iambkram", FONT_TINY, (50, 70, 100), 400, 583)

        # ---- CONTROL CONFIGURATION WARNING POPUP ----
        if show_settings_warning:
            ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ovl.fill((0, 0, 0, 200))
            screen.blit(ovl, (0, 0))

            warn_rect = pygame.Rect(130, 160, 540, 280)
            draw_neon_panel(screen, warn_rect, accent=NEON_CYAN, alpha=248, border_radius=20)

            draw_text("⚙  CONTROL SETUP", FONT_MODAL_TITLE, NEON_CYAN, 400, 210)
            draw_divider(screen, 170, 235, 630, NEON_CYAN, alpha=50)
            draw_text("Choose your control scheme in Settings.", FONT_SMALL, WHITE, 400, 265)
            draw_text("Defaulting to PC: WASD + Space auto-fire", FONT_SMALL, NEON_GOLD, 400, 293)

            btn_set = pygame.Rect(165, 355, 210, 52)
            btn_ok  = pygame.Rect(425, 355, 210, 52)
            is_h_set = btn_set.collidepoint(mx, my)
            is_h_ok  = btn_ok.collidepoint(mx, my)

            draw_glowing_button(screen, "SETTINGS", FONT_UI, WHITE, btn_set, NEON_ORANGE, is_h_set, pulse_t=ui_pulse_t)
            draw_glowing_button(screen, "CONTINUE (PC)", FONT_UI, WHITE, btn_ok, NEON_GREEN, is_h_ok, pulse_t=ui_pulse_t)

            if m_c:
                if is_h_set:
                    tap_snd.play()
                    show_settings_warning = False
                    state = 9
                    click_cooldown = 12
                    m_c = False
                elif is_h_ok:
                    tap_snd.play()
                    control_type = 'PC'
                    show_settings_warning = False
                    click_cooldown = 12
                    m_c = False


    # ==========================
    # SELECT ENVIRONMENT (STATE 20)
    # ==========================
    elif state == STATE_ENV_SELECT:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 190))
        screen.blit(overlay, (0, 0))
        draw_menu_starfield(screen)

        mx, my = pygame.mouse.get_pos()

        draw_text_shadow("SELECT ENVIRONMENT", FONT_MSG, NEON_CYAN, 400, 52, shadow_color=(0,80,120), offset=2)
        draw_text("Choose your combat zone", FONT_TINY, (80, 130, 180), 400, 82)
        draw_divider(screen, 80, 98, 720, NEON_CYAN, alpha=40)

        # --- Environment Card Data & Progression Criteria ---
        env2_unlocked = (max_galaxy_level > 30) or env2_unlocked
        env3_unlocked = (max_nebula_level > 30) or env3_unlocked

        envs = [
            (1, "🌌  GALAXY SECTOR",   "Stellar battlefields",   NEON_BLUE,   True,          max_galaxy_level),
            (2, "🌫  NEBULA ZONE",      "Purple gas clouds",      NEON_PURPLE, env2_unlocked, max_nebula_level),
            (3, "⚫  BLACK HOLE",       "Singularity hazard",     NEON_PINK,   env3_unlocked, max_blackhole_level),
        ]

        card_y_positions = [118, 248, 378]

        for idx, (env_id, name, base_sub, accent, unlocked, max_lvl) in enumerate(envs):
            card = pygame.Rect(80, card_y_positions[idx], 640, 112)
            is_selected = (current_selected_env == env_id)
            is_hover    = card.collidepoint(mx, my) and unlocked

            if is_hover: focused_btn = idx
            is_focused = (focused_btn == idx)

            # Card background
            bg_col = PANEL_MID if unlocked else PANEL_DARK
            draw_neon_panel(screen, card, accent=accent if unlocked else (70, 30, 40),
                            alpha=230, border_radius=16, border_width=2 if not is_selected else 3, bg=bg_col)

            # Pulsing selected border
            if is_selected or (is_focused and unlocked):
                pulse_alpha = int(100 + 80 * math.sin(ui_pulse_t * 3))
                pulse_surf = pygame.Surface((card.width + 12, card.height + 12), pygame.SRCALPHA)
                pygame.draw.rect(pulse_surf, (*accent, pulse_alpha), pulse_surf.get_rect(), border_radius=20, width=2)
                screen.blit(pulse_surf, (card.x - 6, card.y - 6))

            # Environment name
            col = WHITE if unlocked else (160, 160, 170)
            draw_text(name, FONT_HUD, col, card.x + 100, card.centery - 20, center=False)

            # Subtitle / Unlock requirement text
            if unlocked:
                draw_text(f"{base_sub}  ·  Max Mission: {max_lvl}/40", FONT_TINY, accent, card.x + 102, card.centery + 14, center=False)
            else:
                if env_id == 2:
                    req_text = f"COMPLETE 30 GALAXY MISSIONS ({min(30, max_galaxy_level - 1)}/30 COMPLETED)"
                else:
                    req_text = f"COMPLETE 30 NEBULA MISSIONS ({min(30, max_nebula_level - 1)}/30 COMPLETED)"
                draw_text(req_text, FONT_TINY, (255, 100, 100), card.x + 102, card.centery + 14, center=False)

            # Status badge
            if not unlocked:
                draw_badge(screen, "🔒  LOCKED", FONT_TINY, card.right - 80, card.centery, bg_color=(50, 18, 22), text_color=(255, 100, 100), border_color=RED)
            elif is_selected:
                draw_badge(screen, "✔  SELECTED", FONT_TINY, card.right - 82, card.centery, bg_color=(20, 50, 30), text_color=NEON_GREEN, border_color=NEON_GREEN)
            else:
                draw_badge(screen, f"LVL {max_lvl}/40", FONT_TINY, card.right - 72, card.centery, bg_color=PANEL_BG, text_color=accent, border_color=accent)

            # Lock icon or Environment Swatch
            if not unlocked:
                lock_sm = pygame.transform.scale(lock_icon, (48, 48))
                screen.blit(lock_sm, (card.x + 24, card.centery - 24))
            else:
                swatch_rect = pygame.Rect(card.x + 22, card.centery - 26, 52, 52)
                pygame.draw.rect(screen, (10, 20, 40), swatch_rect, border_radius=12)
                pygame.draw.rect(screen, accent, swatch_rect, width=2, border_radius=12)
                draw_text(str(env_id), FONT_UI, accent, swatch_rect.centerx, swatch_rect.centery)

            # Click logic
            if (m_c and is_hover) or (key_enter and is_focused and unlocked):
                tap_snd.play()
                current_selected_env = env_id
                state = STATE_LEVEL_SELECT
                click_cooldown = 12
                m_c = False

        if key_down: focused_btn = (focused_btn + 1) % 4
        if key_up: focused_btn = (focused_btn - 1) % 4

        # Back button
        btn_back = pygame.Rect(260, 504, 280, 54)
        is_h_back = btn_back.collidepoint(mx, my)
        if is_h_back: focused_btn = 3
        is_focused_back = (focused_btn == 3) or is_h_back

        draw_glowing_button(screen, "← BACK TO MENU", FONT_UI, WHITE, btn_back, NEON_PINK, is_focused_back,
                            border_radius=16, accent=RED, pulse_t=ui_pulse_t)
        if (m_c and is_h_back) or (key_enter and focused_btn == 3) or key_escape:
            tap_snd.play()
            state = 0
            click_cooldown = 12
            m_c = False


    # ==========================
    # SETTINGS MENU (STATE 9, 11, 12)
    # ==========================
    elif state == 9:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 190))
        screen.blit(overlay, (0, 0))
        draw_menu_starfield(screen)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        draw_text_shadow("GAME SETTINGS", FONT_MSG, NEON_CYAN, 400, 50, shadow_color=(0,80,120), offset=2)
        draw_divider(screen, 80, 78, 720, NEON_CYAN, alpha=40)

        # --- Device Selection Cards ---
        mob_active = control_type == 'MOBILE'
        pc_active  = control_type == 'PC'

        btn_mob = pygame.Rect(80,  95, 280, 90)
        btn_pc  = pygame.Rect(440, 95, 280, 90)

        is_h_mob = btn_mob.collidepoint(mx, my)
        is_h_pc  = btn_pc.collidepoint(mx, my)

        mob_accent = NEON_CYAN if mob_active else MID_GRAY
        pc_accent  = NEON_CYAN if pc_active  else MID_GRAY

        draw_neon_panel(screen, btn_mob, accent=mob_accent, alpha=230, border_radius=16, border_width=3 if mob_active else 1, bg=PANEL_MID)
        draw_neon_panel(screen, btn_pc,  accent=pc_accent,  alpha=230, border_radius=16, border_width=3 if pc_active  else 1, bg=PANEL_MID)

        if mob_active:
            pulse_a = int(100 + 80 * math.sin(ui_pulse_t * 3))
            ps = pygame.Surface((btn_mob.width+12, btn_mob.height+12), pygame.SRCALPHA)
            pygame.draw.rect(ps, (*NEON_CYAN, pulse_a), ps.get_rect(), border_radius=20, width=2)
            screen.blit(ps, (btn_mob.x-6, btn_mob.y-6))
        if pc_active:
            pulse_a = int(100 + 80 * math.sin(ui_pulse_t * 3))
            ps = pygame.Surface((btn_pc.width+12, btn_pc.height+12), pygame.SRCALPHA)
            pygame.draw.rect(ps, (*NEON_CYAN, pulse_a), ps.get_rect(), border_radius=20, width=2)
            screen.blit(ps, (btn_pc.x-6, btn_pc.y-6))

        draw_text("📱  MOBILE", FONT_UI, WHITE if mob_active else LIGHT_GRAY, btn_mob.centerx, btn_mob.centery - 14)
        draw_text("Touch Controls", FONT_TINY, mob_accent, btn_mob.centerx, btn_mob.centery + 14)

        draw_text("🖥  PC / DESKTOP", FONT_UI, WHITE if pc_active else LIGHT_GRAY, btn_pc.centerx, btn_pc.centery - 14)
        draw_text("WASD + Space", FONT_TINY, pc_accent, btn_pc.centerx, btn_pc.centery + 14)

        # --- Volume Sliders ---
        slider_y_pos   = [260, 330]
        slider_labels  = ["🎵  MUSIC VOLUME", "🔊  SOUND EFFECTS"]
        slider_colors  = [NEON_CYAN, NEON_ORANGE]
        current_vols   = [music_vol, sfx_vol]

        for i in range(2):
            draw_text(slider_labels[i], FONT_SMALL, WHITE, 400, slider_y_pos[i] - 26)
            s_rect = pygame.Rect(160, slider_y_pos[i], 480, 24)
            draw_gradient_bar(screen, s_rect, current_vols[i],
                              color_low=(40, 40, 60), color_high=slider_colors[i],
                              bg_color=(20, 22, 35), border_radius=12, border_color=(50,55,80))

            pct_txt = f"{int(current_vols[i] * 100)}%"
            draw_text(pct_txt, FONT_TINY, WHITE, 400, slider_y_pos[i] + 12)

            # Handle
            handle_x = 160 + int(current_vols[i] * 480)
            pygame.draw.circle(screen, (230, 230, 255), (handle_x, slider_y_pos[i] + 12), 14)
            pygame.draw.circle(screen, slider_colors[i], (handle_x, slider_y_pos[i] + 12), 8)

            if m_down and s_rect.inflate(24, 48).collidepoint(mx, my):
                new_val = max(0.0, min(1.0, (mx - 160) / 480))
                if i == 0:
                    music_vol = new_val
                    pygame.mixer.music.set_volume(music_vol)
                else:
                    sfx_vol = new_val
                    for snd in [shoot_snd, game_won_snd, game_loose_snd, tap_snd, boss_expl_snd, expl_snd, hit_snd]:
                        snd.set_volume(sfx_vol)

        # --- Display Mode ---
        draw_text("DISPLAY MODE", FONT_SMALL, WHITE, 400, 375)
        btn_full = pygame.Rect(190, 395, 200, 36)
        btn_win = pygame.Rect(410, 395, 200, 36)
        is_h_full = btn_full.collidepoint(mx, my)
        is_h_win = btn_win.collidepoint(mx, my)

        draw_neon_panel(screen, btn_full, accent=NEON_GREEN if is_fullscreen else MID_GRAY, alpha=230, border_radius=8, border_width=2 if is_fullscreen else 1, bg=PANEL_MID)
        draw_neon_panel(screen, btn_win, accent=NEON_GREEN if not is_fullscreen else MID_GRAY, alpha=230, border_radius=8, border_width=2 if not is_fullscreen else 1, bg=PANEL_MID)
        
        draw_text("FULLSCREEN", FONT_TINY, WHITE if is_fullscreen else LIGHT_GRAY, btn_full.centerx, btn_full.centery)
        draw_text("WINDOWED", FONT_TINY, WHITE if not is_fullscreen else LIGHT_GRAY, btn_win.centerx, btn_win.centery)

        # --- Toggles ---
        # FPS Toggle
        btn_fps = pygame.Rect(190, 440, 200, 30)
        is_h_fps = btn_fps.collidepoint(mx, my)
        fps_color = NEON_GREEN if show_fps else MID_GRAY
        pygame.draw.rect(screen, fps_color, (btn_fps.x, btn_fps.y + 6, 18, 18), width=0 if show_fps else 2, border_radius=4)
        if show_fps:
            draw_text("✔", FONT_TINY, WHITE, btn_fps.x + 9, btn_fps.y + 15)
        draw_text("📊 SHOW FPS COUNTER", FONT_TINY, WHITE, btn_fps.x + 110, btn_fps.centery)
        
        # Screen Shake Toggle
        btn_shake = pygame.Rect(410, 440, 200, 30)
        is_h_shake = btn_shake.collidepoint(mx, my)
        shake_color = NEON_GREEN if screen_shake_enabled else MID_GRAY
        pygame.draw.rect(screen, shake_color, (btn_shake.x, btn_shake.y + 6, 18, 18), width=0 if screen_shake_enabled else 2, border_radius=4)
        if screen_shake_enabled:
            draw_text("✔", FONT_TINY, WHITE, btn_shake.x + 9, btn_shake.y + 15)
        draw_text("💫 SCREEN SHAKE EFFECTS", FONT_TINY, WHITE, btn_shake.x + 110, btn_shake.centery)

        # --- Visual Quality ---
        draw_text("VISUAL QUALITY", FONT_SMALL, WHITE, 400, 480)
        btn_q_low = pygame.Rect(150, 495, 150, 36)
        btn_q_med = pygame.Rect(325, 495, 150, 36)
        btn_q_high = pygame.Rect(500, 495, 150, 36)
        is_h_q_low = btn_q_low.collidepoint(mx, my)
        is_h_q_med = btn_q_med.collidepoint(mx, my)
        is_h_q_high = btn_q_high.collidepoint(mx, my)

        draw_neon_panel(screen, btn_q_low, accent=NEON_CYAN if visual_quality == 'low' else MID_GRAY, alpha=230, border_radius=8, border_width=2 if visual_quality == 'low' else 1, bg=PANEL_MID)
        draw_neon_panel(screen, btn_q_med, accent=NEON_CYAN if visual_quality == 'medium' else MID_GRAY, alpha=230, border_radius=8, border_width=2 if visual_quality == 'medium' else 1, bg=PANEL_MID)
        draw_neon_panel(screen, btn_q_high, accent=NEON_CYAN if visual_quality == 'high' else MID_GRAY, alpha=230, border_radius=8, border_width=2 if visual_quality == 'high' else 1, bg=PANEL_MID)

        draw_text("LOW", FONT_TINY, WHITE if visual_quality == 'low' else LIGHT_GRAY, btn_q_low.centerx, btn_q_low.centery)
        draw_text("MEDIUM", FONT_TINY, WHITE if visual_quality == 'medium' else LIGHT_GRAY, btn_q_med.centerx, btn_q_med.centery)
        draw_text("HIGH", FONT_TINY, WHITE if visual_quality == 'high' else LIGHT_GRAY, btn_q_high.centerx, btn_q_high.centery)

        # Save & Back
        btn_back = pygame.Rect(265, 540, 270, 46)
        is_h_back = btn_back.collidepoint(mx, my)
        draw_glowing_button(screen, "SAVE & BACK", FONT_UI, WHITE, btn_back, NEON_PINK, is_h_back,
                            border_radius=16, accent=RED, pulse_t=ui_pulse_t)

        if m_c:
            if is_h_mob:
                tap_snd.play()
                control_type = 'MOBILE'
                state = 12
                save_game()
                click_cooldown = 12
                m_c = False
            elif is_h_pc:
                tap_snd.play()
                control_type = 'PC'
                state = 11
                save_game()
                click_cooldown = 12
                m_c = False
            elif is_h_full:
                if not is_fullscreen:
                    tap_snd.play()
                    is_fullscreen = True
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    click_cooldown = 12
                    m_c = False
            elif is_h_win:
                if is_fullscreen:
                    tap_snd.play()
                    is_fullscreen = False
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                    click_cooldown = 12
                    m_c = False
            elif is_h_fps:
                tap_snd.play()
                show_fps = not show_fps
                click_cooldown = 12
                m_c = False
            elif is_h_shake:
                tap_snd.play()
                screen_shake_enabled = not screen_shake_enabled
                click_cooldown = 12
                m_c = False
            elif is_h_q_low:
                tap_snd.play()
                visual_quality = 'low'
                try:
                    vfx_engine.set_quality(visual_quality)
                except NameError:
                    pass
                click_cooldown = 12
                m_c = False
            elif is_h_q_med:
                tap_snd.play()
                visual_quality = 'medium'
                try:
                    vfx_engine.set_quality(visual_quality)
                except NameError:
                    pass
                click_cooldown = 12
                m_c = False
            elif is_h_q_high:
                tap_snd.play()
                visual_quality = 'high'
                try:
                    vfx_engine.set_quality(visual_quality)
                except NameError:
                    pass
                click_cooldown = 12
                m_c = False
            elif is_h_back:
                tap_snd.play()
                if settings_from_pause:
                    state = 10
                    settings_from_pause = False
                else:
                    state = 0
                save_game()
                click_cooldown = 12
                m_c = False

    # ==========================
    # PC CONTROLS INFO (STATE 11)
    # ==========================
    elif state == 11:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 190))
        screen.blit(overlay, (0, 0))
        draw_menu_starfield(screen)

        info_box = pygame.Rect(90, 65, 620, 470)
        draw_neon_panel(screen, info_box, accent=NEON_BLUE, alpha=248, border_radius=20)

        draw_text_shadow("PC FLIGHT COMMANDS", FONT_MSG, NEON_CYAN, 400, 112, shadow_color=(0,60,120), offset=2)
        draw_divider(screen, 120, 138, 680, NEON_CYAN, alpha=40)

        instructions = [
            ("🕹  Flight Navigation",  "Use [W A S D] or Arrow Keys for 2D maneuvering & dodging."),
            ("🔫  Weapons Barrage",    "Hold [SPACEBAR] or Left Mouse Button for rapid auto-fire."),
            ("⚡  Tactical Powerups",  "Collect glowing [S] Shield & [2X] Dual Laser orbs mid-flight."),
            ("⚫  Singularity Hazard", "In Black Hole mode, resist gravity with fast thruster bursts!"),
        ]

        for idx, (head, body) in enumerate(instructions):
            row_y = 165 + idx * 68
            row_rect = pygame.Rect(110, row_y, 580, 56)
            pygame.draw.rect(screen, PANEL_MID, row_rect, border_radius=10)
            pygame.draw.rect(screen, (40, 60, 100), row_rect, width=1, border_radius=10)
            # Left accent bar
            pygame.draw.rect(screen, NEON_BLUE, pygame.Rect(110, row_y + 8, 3, 40), border_radius=2)
            draw_text(head, FONT_SMALL, NEON_GOLD, 400, row_y + 18)
            draw_text(body, FONT_SMALL, LIGHT_GRAY, 400, row_y + 40)

        mx, my = pygame.mouse.get_pos()
        btn_ok = pygame.Rect(270, 450, 260, 54)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_glowing_button(screen, "✔  GOT IT!", FONT_UI, WHITE, btn_ok, NEON_GREEN, is_h_ok,
                            border_radius=16, accent=GREEN, pulse_t=ui_pulse_t)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9
            click_cooldown = 12
            m_c = False

    # ==========================
    # MOBILE CONTROLS INFO (STATE 12)
    # ==========================
    elif state == 12:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 190))
        screen.blit(overlay, (0, 0))
        draw_menu_starfield(screen)

        info_box = pygame.Rect(90, 65, 620, 470)
        draw_neon_panel(screen, info_box, accent=NEON_CYAN, alpha=248, border_radius=20)

        draw_text_shadow("MOBILE TOUCH COMMANDS", FONT_MSG, NEON_CYAN, 400, 112, shadow_color=(0,60,120), offset=2)
        draw_divider(screen, 120, 138, 680, NEON_CYAN, alpha=40)

        m_instructions = [
            ("👆  Touch Navigation",    "Slide your finger anywhere to smoothly glide your starship."),
            ("🔫  Auto-Firing",         "Cannons fire automatically while your finger is on the screen."),
            ("⚡  Tactical Powerups",   "Tap glowing [S] Shield & [2X] Double Shot orbs to collect them."),
            ("⚫  Singularity Hazard",  "Always keep sliding — Black Hole pulls you continuously inward!"),
        ]

        for idx, (head, body) in enumerate(m_instructions):
            row_y = 165 + idx * 68
            row_rect = pygame.Rect(110, row_y, 580, 56)
            pygame.draw.rect(screen, PANEL_MID, row_rect, border_radius=10)
            pygame.draw.rect(screen, (30, 70, 80), row_rect, width=1, border_radius=10)
            pygame.draw.rect(screen, NEON_CYAN, pygame.Rect(110, row_y + 8, 3, 40), border_radius=2)
            draw_text(head, FONT_SMALL, NEON_GOLD, 400, row_y + 18)
            draw_text(body, FONT_SMALL, LIGHT_GRAY, 400, row_y + 40)

        mx, my = pygame.mouse.get_pos()
        btn_ok = pygame.Rect(270, 450, 260, 54)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_glowing_button(screen, "✔  GOT IT!", FONT_UI, WHITE, btn_ok, NEON_GREEN, is_h_ok,
                            border_radius=16, accent=GREEN, pulse_t=ui_pulse_t)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9
            click_cooldown = 12
            m_c = False

    # ==========================
    # MISSIONS / LEVEL SELECT (STATE 1)
    # ==========================
    elif state == STATE_LEVEL_SELECT:
        # Draw environment background
        if current_selected_env == 1:
            screen.blit(galaxy_bg, (0, 0))
        elif current_selected_env == 2:
            screen.blit(nebula_bg, (0, 0))
        elif current_selected_env == 3:
            screen.blit(blackhole_bg, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        # Header
        env_label = {1: "🌌 GALAXY", 2: "🌫 NEBULA", 3: "⚫ BLACK HOLE"}[current_selected_env]
        env_acc   = {1: NEON_BLUE, 2: NEON_PURPLE, 3: NEON_PINK}[current_selected_env]
        draw_text_shadow("MISSIONS", FONT_MSG, NEON_CYAN, 400, 40, shadow_color=(0,60,120), offset=2)
        draw_badge(screen, env_label, FONT_TINY, 400, 72, bg_color=PANEL_MID, text_color=env_acc, border_color=env_acc)

        # Scrollable grid panel
        box_rect = pygame.Rect(110, 100, 580, 378)
        draw_neon_panel(screen, box_rect, accent=env_acc, alpha=210, border_radius=16, border_width=2, bg=PANEL_BG)

        # Drag / scroll
        if m_down and box_rect.collidepoint(mx, my):
            if not is_dragging_missions:
                is_dragging_missions = True
                last_mouse_y = my
                touch_start_y = my
                touch_start_x = mx
                total_drag_dist = 0
            else:
                dy = my - last_mouse_y
                level_scroll_y += dy
                total_drag_dist += abs(dy) + abs(my - touch_start_y)
                last_mouse_y = my
        else:
            if not m_down:
                is_dragging_missions = False

        if key_up:
            level_scroll_y += 50
        if key_down:
            level_scroll_y -= 50

        level_scroll_y = max(-850, min(0, level_scroll_y))
        screen.set_clip(box_rect.inflate(-8, -8))

        # Calculate current environment max unlocked level
        if current_selected_env == 1:
            env_max = max_galaxy_level
        elif current_selected_env == 2:
            env_max = max_nebula_level
        elif current_selected_env == 3:
            env_max = max_blackhole_level
        else:
            env_max = 1

        clicked_level = None

        for i in range(1, 41):
            col_i = (i - 1) % 5
            row_i = (i - 1) // 5
            lx = 138 + col_i * 104
            ly = 128 + row_i * 96 + level_scroll_y

            node_r = 36  # radius
            cx, cy = lx + node_r, ly + node_r
            lvl_rect = pygame.Rect(lx, ly, node_r*2, node_r*2)
            is_u = (i <= env_max)
            in_view = 100 < ly < 478
            is_h = False

            if in_view:
                is_h = lvl_rect.collidepoint(mx, my) and is_u and box_rect.collidepoint(mx, my)

                # Node fill
                if not is_u:
                    node_col = (15, 18, 26)
                    border_col = (50, 55, 70)
                elif i == selected_level:
                    node_col = (20, 50, 30)
                    border_col = NEON_GREEN
                elif is_h:
                    node_col = get_highlight(env_acc)
                    border_col = NEON_CYAN
                else:
                    node_col = PANEL_MID
                    border_col = env_acc

                pygame.draw.circle(screen, node_col, (cx, cy), node_r)
                bw = 3 if (is_h or i == selected_level) else 1
                pygame.draw.circle(screen, border_col, (cx, cy), node_r, bw)

                # Pulsing glow for selected
                if i == selected_level:
                    pa = int(80 + 60 * math.sin(ui_pulse_t * 3))
                    glow_s = pygame.Surface((node_r*2+16, node_r*2+16), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (*NEON_GREEN, pa), (node_r+8, node_r+8), node_r+6, 3)
                    screen.blit(glow_s, (cx - node_r - 8, cy - node_r - 8))

                # Level number or Lock symbol
                if is_u:
                    num_surf = FONT_HP.render(str(i), True, WHITE)
                    screen.blit(num_surf, num_surf.get_rect(center=(cx, cy)))
                else:
                    lock_mini = pygame.transform.scale(lock_icon, (24, 24))
                    screen.blit(lock_mini, lock_mini.get_rect(center=(cx, cy)))

                # Tap detection
                if m_u and is_h and total_drag_dist < 12 and click_cooldown <= 0:
                    clicked_level = i

        screen.set_clip(None)

        # Scroll position indicator (right thin strip)
        if level_scroll_y < 0:
            scroll_track = pygame.Rect(box_rect.right - 8, box_rect.y + 6, 4, box_rect.height - 12)
            pygame.draw.rect(screen, PANEL_MID, scroll_track, border_radius=2)
            scroll_frac  = abs(level_scroll_y) / 850
            thumb_h = max(30, int((box_rect.height - 12) * 0.4))
            thumb_y  = scroll_track.y + int(scroll_frac * (scroll_track.height - thumb_h))
            pygame.draw.rect(screen, env_acc, pygame.Rect(scroll_track.x, thumb_y, 4, thumb_h), border_radius=2)

        if clicked_level is not None:
            tap_snd.play()
            selected_level = clicked_level
            state = 2
            click_cooldown = 12
            m_c = False
            m_u = False
            total_drag_dist = 0

        # Back button
        btn_back = pygame.Rect(255, 494, 290, 56)
        is_h_b = btn_back.collidepoint(mx, my)
        draw_glowing_button(screen, "← BACK", FONT_UI, WHITE, btn_back, NEON_PINK, is_h_b,
                            border_radius=16, accent=RED, pulse_t=ui_pulse_t)

        if (m_c and is_h_b) or key_escape:
            tap_snd.play()
            state = STATE_ENV_SELECT
            click_cooldown = 12
            m_c = False


    # ==========================
    # STORE (STATE 6, 7, 8)
    # ==========================
    elif state == 6:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 185))
        screen.blit(overlay, (0, 0))
        draw_menu_starfield(screen)

        mx, my = pygame.mouse.get_pos()

        draw_text_shadow("SPACE STORE", FONT_MSG, NEON_CYAN, 400, 48, shadow_color=(0,80,120), offset=2)

        # Coin badge
        coin_panel = pygame.Rect(318, 78, 164, 36)
        pygame.draw.rect(screen, PANEL_BG, coin_panel, border_radius=18)
        pygame.draw.rect(screen, NEON_GOLD, coin_panel, width=1, border_radius=18)
        screen.blit(coin_icon, (326, 70))
        draw_text(str(total_coins), FONT_UI, NEON_GOLD, 395, 96)

        draw_divider(screen, 80, 124, 720, NEON_CYAN, alpha=40)

        # Store item cards
        store_items = [
            ("❤  MAX HP",   NEON_GREEN,   70,  'hp', unlocked_hp,      hp_step,    len(hp_costs),     hp_costs),
            ("⚡  SPEED",    NEON_ORANGE,  280, 'sp', unlocked_speed,   speed_step, len(speed_costs),  speed_costs),
            ("🔫  BULLETS",  NEON_PINK,    490, 'pb', unlocked_bullets, bullet_step,len(bullet_costs), bullet_costs),
        ]

        for name, col, x, key, curr_val, step, max_steps, costs in store_items:
            card = pygame.Rect(x, 148, 190, 220)
            is_h = card.collidepoint(mx, my)
            is_sel = store_selection == key

            draw_neon_panel(screen, card, accent=col if (is_h or is_sel) else MID_GRAY,
                            alpha=235, border_radius=16, border_width=2 if not is_sel else 3, bg=PANEL_MID)

            if is_sel:
                pa = int(100 + 80 * math.sin(ui_pulse_t * 3))
                gls = pygame.Surface((card.width+12, card.height+12), pygame.SRCALPHA)
                pygame.draw.rect(gls, (*col, pa), gls.get_rect(), border_radius=20, width=2)
                screen.blit(gls, (card.x-6, card.y-6))

            draw_text(name, FONT_SMALL, col, card.centerx, card.y + 34)
            draw_divider(screen, card.x + 12, card.y + 52, card.right - 12, col, alpha=60)

            # Current value
            draw_text(str(curr_val), FONT_HUD, WHITE, card.centerx, card.y + 90)

            # Upgrade progress bar
            prog_frac = min(1.0, step / max(1, max_steps))
            bar_rect = pygame.Rect(card.x + 14, card.y + 120, card.width - 28, 10)
            draw_gradient_bar(screen, bar_rect, prog_frac, color_low=(40,40,60), color_high=col,
                              bg_color=(20,22,35), border_radius=5, show_glow=False)
            draw_text(f"{step}/{max_steps}", FONT_TINY, LIGHT_GRAY, card.centerx, card.y + 144)

            # Cost
            next_cost = costs[step] if step < max_steps else "MAX"
            cost_col = NEON_GOLD if next_cost != "MAX" and total_coins >= (next_cost if next_cost != "MAX" else 0) else (RED if next_cost != "MAX" else MID_GRAY)
            cost_txt = f"🪙 {next_cost}" if next_cost != "MAX" else "✓ MAX"
            draw_text(cost_txt, FONT_SMALL, cost_col, card.centerx, card.y + 178)

            # Select on click
            if m_c and is_h:
                tap_snd.play()
                store_selection = key
                click_cooldown = 12
                m_c = False

        # Item detail popup
        if store_selection:
            pop_ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pop_ovl.fill((0, 0, 0, 200))
            screen.blit(pop_ovl, (0, 0))

            pop_box = pygame.Rect(145, 148, 510, 304)
            draw_neon_panel(screen, pop_box, accent=NEON_CYAN, alpha=248, border_radius=20)

            desc_map = {"hp": "Increase Maximum HP Capacity", "sp": "Boost Ship Navigation Speed", "pb": "Unlock Extra Bullet Streams"}
            desc = desc_map.get(store_selection, "")
            if store_selection == 'hp':
                cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
            elif store_selection == 'sp':
                cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
            else:
                cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"

            draw_text("UPGRADE DETAILS", FONT_MODAL_TITLE, NEON_GOLD, 400, 194)
            draw_divider(screen, 185, 218, 615, NEON_GOLD, alpha=50)
            draw_text(desc, FONT_SMALL, WHITE, 400, 252)

            can_afford = cost != "MAX" and total_coins >= cost
            cost_col2 = NEON_GREEN if can_afford else (RED if cost != "MAX" else MID_GRAY)
            cost_txt2 = f"🪙  {cost} COINS" if cost != "MAX" else "✓  ALREADY MAXED"
            draw_text(cost_txt2, FONT_UI, cost_col2, 400, 300)

            btn_st_bk = pygame.Rect(175, 368, 192, 54)
            btn_buy   = pygame.Rect(433, 368, 192, 54)
            is_h_bk   = btn_st_bk.collidepoint(mx, my)
            is_h_buy  = btn_buy.collidepoint(mx, my)

            draw_glowing_button(screen, "← BACK", FONT_UI, WHITE, btn_st_bk, NEON_PINK, is_h_bk, pulse_t=ui_pulse_t)
            if cost != "MAX":
                draw_glowing_button(screen, "🛒  BUY", FONT_UI, WHITE, btn_buy, NEON_GREEN if can_afford else MID_GRAY, is_h_buy, pulse_t=ui_pulse_t)

            if m_c or key_escape or key_enter:
                if is_h_bk or key_escape:
                    tap_snd.play()
                    store_selection = None
                    click_cooldown = 12
                    m_c = False
                    key_escape = False
                elif (is_h_buy or key_enter) and cost != "MAX":
                    if total_coins >= cost:
                        state = 7
                    else:
                        tap_snd.play()
                        state = 8
                    click_cooldown = 12
                    m_c = False
                    key_enter = False

        if not store_selection:
            btn_b_m = pygame.Rect(255, 430, 290, 56)
            is_h_bm = btn_b_m.collidepoint(mx, my)
            draw_glowing_button(screen, "← BACK TO MENU", FONT_UI, WHITE, btn_b_m, NEON_PINK, is_h_bm,
                                border_radius=16, accent=RED, pulse_t=ui_pulse_t)
            if (m_c and is_h_bm) or key_escape:
                tap_snd.play()
                state = 0
                click_cooldown = 12
                m_c = False

    elif state == 7:
        pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_overlay.fill((0, 0, 0, 210))
        screen.blit(pop_overlay, (0, 0))

        box = pygame.Rect(160, 170, 480, 260)
        draw_neon_panel(screen, box, accent=NEON_GOLD, alpha=250, border_radius=20)

        draw_text("⬆  CONFIRM UPGRADE?", FONT_MODAL_TITLE, NEON_GOLD, 400, 212)
        draw_divider(screen, 195, 238, 605, NEON_GOLD, alpha=50)
        cost = hp_costs[hp_step] if store_selection == 'hp' else speed_costs[speed_step] if store_selection == 'sp' else bullet_costs[bullet_step]
        draw_text(f"Spend  🪙 {cost} coins  to upgrade?", FONT_SMALL, WHITE, 400, 275)
        draw_text(f"You have: {total_coins} coins", FONT_TINY, LIGHT_GRAY, 400, 302)

        mx, my = pygame.mouse.get_pos()
        b_n = pygame.Rect(185, 340, 192, 54)
        b_y = pygame.Rect(423, 340, 192, 54)
        is_h_n = b_n.collidepoint(mx, my)
        is_h_y = b_y.collidepoint(mx, my)

        draw_glowing_button(screen, "CANCEL", FONT_UI, WHITE, b_n, NEON_PINK, is_h_n, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "✔  CONFIRM", FONT_UI, WHITE, b_y, NEON_GREEN, is_h_y, pulse_t=ui_pulse_t)

        if m_c or key_escape or key_enter:
            if is_h_n or key_escape:
                tap_snd.play()
                state = 6
                click_cooldown = 12
                m_c = False
            if is_h_y or key_enter:
                update_coins(-cost)
                if store_selection == 'hp':
                    unlocked_hp += 10
                    hp_step += 1
                elif store_selection == 'sp':
                    unlocked_speed += 2
                    speed_step += 1
                elif store_selection == 'pb':
                    unlocked_bullets += 1
                    bullet_step += 1
                save_game()
                tap_snd.play()
                state = 6
                store_selection = None
                click_cooldown = 12
                m_c = False

    elif state == 8:
        pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_overlay.fill((0, 0, 0, 210))
        screen.blit(pop_overlay, (0, 0))

        box = pygame.Rect(155, 170, 490, 260)
        draw_neon_panel(screen, box, accent=NEON_PINK, alpha=250, border_radius=20, bg=(28, 10, 15))

        draw_text("🪙  INSUFFICIENT COINS", FONT_MODAL_TITLE, NEON_PINK, 400, 212)
        draw_divider(screen, 190, 238, 610, NEON_PINK, alpha=50)
        draw_text("Not enough coins for this upgrade!", FONT_SMALL, WHITE, 400, 274)
        draw_text("Complete missions to earn more coins.", FONT_TINY, LIGHT_GRAY, 400, 302)

        mx, my = pygame.mouse.get_pos()
        b_b = pygame.Rect(185, 342, 192, 54)
        b_t = pygame.Rect(423, 342, 192, 54)
        is_h_b = b_b.collidepoint(mx, my)
        is_h_t = b_t.collidepoint(mx, my)

        draw_glowing_button(screen, "← STORE", FONT_UI, WHITE, b_b, NEON_PINK, is_h_b, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "🚀 MISSIONS", FONT_UI, WHITE, b_t, NEON_GREEN, is_h_t, pulse_t=ui_pulse_t)

        if m_c or key_escape or key_enter:
            if is_h_b or key_escape or key_enter:
                tap_snd.play()
                state = 6
                click_cooldown = 12
                m_c = False
            elif is_h_t:
                tap_snd.play()
                state = STATE_ENV_SELECT
                click_cooldown = 12
                m_c = False

    # ==========================
    # MISSION INFO (STATE 2)
    # ==========================
    elif state == 2:
        # Background — use active env bg
        if current_selected_env == 1:
            screen.blit(galaxy_bg, (0, 0))
        elif current_selected_env == 2:
            screen.blit(nebula_bg, (0, 0))
        else:
            screen.blit(blackhole_bg, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        env_acc2 = {1: NEON_BLUE, 2: NEON_PURPLE, 3: NEON_PINK}[current_selected_env]
        env_names = {1: "GALAXY SECTOR", 2: "NEBULA ZONE", 3: "BLACKHOLE HORIZON"}
        curr_env_title = env_names.get(current_selected_env, "GALAXY SECTOR")

        box_rect = pygame.Rect(130, 78, 540, 444)
        draw_neon_panel(screen, box_rect, accent=env_acc2, alpha=250, border_radius=20, bg=PANEL_BG)

        draw_text_shadow(f"MISSION  {selected_level}", FONT_MODAL_TITLE, NEON_GOLD, 400, 126, shadow_color=(80,50,0), offset=2)
        draw_badge(screen, curr_env_title, FONT_TINY, 400, 160, bg_color=PANEL_MID, text_color=env_acc2, border_color=env_acc2)
        draw_divider(screen, 165, 182, 635, env_acc2, alpha=50)

        boss_kill_reqs = {1: 15, 2: 20, 3: 25, 4: 35, 5: 45, 6: 60, 7: 75, 8: 90, 9: 105, 10: 120}
        req_k = min(200, 120 + (selected_level - 10) * 4) if selected_level >= 11 else boss_kill_reqs.get(selected_level, 25)

        # Objective card
        obj_rect = pygame.Rect(160, 200, 480, 72)
        pygame.draw.rect(screen, PANEL_MID, obj_rect, border_radius=12)
        pygame.draw.rect(screen, env_acc2, obj_rect, width=1, border_radius=12)
        pygame.draw.rect(screen, env_acc2, pygame.Rect(160, 210, 3, 52), border_radius=2)
        draw_text("⚔  OBJECTIVE", FONT_SMALL, NEON_GOLD, 400, 222)
        draw_text(f"Eliminate {req_k} enemies to summon the Sector Boss", FONT_SMALL, WHITE, 400, 250)

        # Tier / difficulty badge
        tier = (selected_level - 1) // 5 + 1
        diff_labels = {1:"NOVICE", 2:"RECRUIT", 3:"VETERAN", 4:"ELITE", 5:"COMMANDER", 6:"OVERLORD", 7:"LEGEND", 8:"MYTHIC"}
        diff_txt = diff_labels.get(tier, "MYTHIC")
        diff_col = [NEON_GREEN, NEON_BLUE, NEON_CYAN, NEON_ORANGE, NEON_PINK, RED, NEON_PURPLE, NEON_GOLD][min(tier-1, 7)]
        draw_badge(screen, f"DIFFICULTY: {diff_txt}", FONT_TINY, 400, 308, bg_color=PANEL_MID, text_color=diff_col, border_color=diff_col)

        # Enemy type preview
        preview_y = 352
        draw_text("ENEMY ROSTER", FONT_TINY, LIGHT_GRAY, 400, preview_y - 16)
        enemy_info = [
            (fighter_img, "Fighter",  NEON_CYAN),
            (elite_img,   "Elite",    NEON_PURPLE),
            (heavy_img,   "Heavy",    NEON_ORANGE),
        ]
        ex = 260
        for eimg, ename, ecol in enemy_info:
            esc = pygame.transform.scale(eimg, (36, 36))
            screen.blit(esc, (ex, preview_y))
            draw_text(ename, FONT_TINY, ecol, ex + 18, preview_y + 50)
            ex += 100

        mx, my = pygame.mouse.get_pos()
        b_r = pygame.Rect(155, 432, 220, 58)
        b_a = pygame.Rect(425, 432, 220, 58)
        is_h_r = b_r.collidepoint(mx, my)
        is_h_a = b_a.collidepoint(mx, my)

        # Launch button with animated border sweep
        draw_glowing_button(screen, "🚀  LAUNCH", FONT_UI, WHITE, b_r, NEON_GREEN, is_h_r,
                            border_radius=16, accent=GREEN, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "← BACK", FONT_UI, WHITE, b_a, NEON_PINK, is_h_a,
                            border_radius=16, accent=RED, pulse_t=ui_pulse_t)

        if m_c or key_enter or key_escape:
            if is_h_r or key_enter:
                tap_snd.play()
                reset_level_logic(selected_level)
                state = 3
                click_cooldown = 12
                m_c = False
                key_enter = False
            elif is_h_a or key_escape:
                tap_snd.play()
                state = 1
                click_cooldown = 12
                m_c = False
                key_escape = False


    # ==========================
    # GAMEPLAY (STATE 3)
    # ==========================
    elif state == 3:

        mx, my = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        pause_btn_rect = pygame.Rect(WIDTH - 55, 15, 40, 40)
        is_h_pause = pause_btn_rect.collidepoint(mx, my)

        # ----------------------------------------------------
        # BLACKHOLE STARTING WARNING POPUP (FIXED SIZING)
        # ----------------------------------------------------
        if blackhole_alert_active:
            screen.blit(blackhole_bg, (0, 0))

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 20, 210))
            screen.blit(overlay, (0, 0))

            alert_box = pygame.Rect(90, 80, 620, 480)
            draw_neon_panel(screen, alert_box, accent=NEON_PINK, alpha=250, border_radius=22, bg=(25,12,18))

            draw_text_shadow("⚠ GRAVITATIONAL HAZARD", FONT_MODAL_TITLE, NEON_PINK, 400, 115, shadow_color=(80,0,0), offset=2)
            draw_text("BLACK HOLE SINGULARITY DETECTED", FONT_TINY, NEON_CYAN, 400, 150)
            draw_divider(screen, 130, 168, 670, NEON_PINK, alpha=50)

            warnings = [
                ("⚫ Massive Singularity", "Extreme gravity pulls all ships and matter to the center!"),
                ("⏳ Relativistic Time",    "All ship navigation, lasers, and combat speeds are slowed down."),
                ("💥 Event Horizon",        "Falling into the center will crush your starship!"),
                ("🚀 Active Defense",       "Use continuous sliding / WASD reflexes to resist gravity.")
            ]

            for idx, (head, body) in enumerate(warnings):
                card_rect = pygame.Rect(115, 185 + idx * 64, 570, 56)
                pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=12)
                pygame.draw.rect(screen, NEON_PINK, card_rect, width=1, border_radius=12)
                pygame.draw.rect(screen, NEON_PINK, pygame.Rect(115, 195 + idx * 64, 3, 36), border_radius=2)
                draw_text(head, FONT_SMALL, NEON_GOLD, 400, card_rect.y + 18)
                draw_text(body, FONT_SMALL, LIGHT_GRAY, 400, card_rect.y + 40)

            btn_engage = pygame.Rect(250, 465, 300, 56)
            is_h_eng = btn_engage.collidepoint(mx, my)
            draw_glowing_button(screen, "🚀 ENGAGE THRUSTERS", FONT_UI, WHITE, btn_engage, NEON_PINK, is_h_eng, accent=RED, pulse_t=ui_pulse_t)

            if m_c and is_h_eng:
                tap_snd.play()
                blackhole_alert_active = False
                click_cooldown = 12
                m_c = False

            pygame.display.flip()
            clock.tick(60)
            continue

        # ----------------------------------------------------
        # RELATIVISTIC ENVIRONMENT MULTIPLIER & SETTINGS
        # ----------------------------------------------------
        is_blackhole = (current_selected_env == 3)
        env_speed_mult = 0.68 if is_blackhole else 1.0
        eff_player_speed = max(3.0, unlocked_speed * env_speed_mult)

        # Calculate mouse delta for mobile relative control
        if 'prev_mx' not in globals():
            global prev_mx, prev_my
            prev_mx, prev_my = mx, my
        mouse_dx = mx - prev_mx
        mouse_dy = my - prev_my
        prev_mx, prev_my = mx, my

        # --- SMART CONTROLS LOGIC ---
        if fire_cooldown > 0:
            fire_cooldown -= 1

        is_firing = False

        if control_type == 'PC':
            if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player_rect.left > 0:
                player_rect.x -= eff_player_speed
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player_rect.right < WIDTH:
                player_rect.x += eff_player_speed
            if (keys[pygame.K_w] or keys[pygame.K_UP]) and player_rect.top > 80:
                player_rect.y -= eff_player_speed
            if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and player_rect.bottom < HEIGHT - 10:
                player_rect.y += eff_player_speed

            if (keys[pygame.K_SPACE] or (mouse_pressed and not is_h_pause)) and fire_cooldown <= 0:
                is_firing = True
                fire_cooldown = 9 if is_blackhole else (8 if current_level <= 15 else 6)

        elif control_type == 'MOBILE':
            if mouse_pressed and not is_h_pause:
                if not m_c: # Ignore the very first frame to prevent teleporting
                    dist = math.hypot(mouse_dx, mouse_dy)
                    if dist > 0:
                        # Cap movement to eff_player_speed per frame so fast slides don't increase speed
                        step = min(dist, eff_player_speed)
                        player_rect.x += int((mouse_dx / dist) * step)
                        player_rect.y += int((mouse_dy / dist) * step)

                if fire_cooldown <= 0:
                    is_firing = True
                    fire_cooldown = 8 if is_blackhole else (7 if current_level <= 15 else 5)

        # Keep player ship within screen boundaries
        player_rect.left = max(0, player_rect.left)
        player_rect.right = min(WIDTH, player_rect.right)
        player_rect.top = max(80, player_rect.top)
        player_rect.bottom = min(HEIGHT - 10, player_rect.bottom)

        # ----------------------------------------------------
        # BLACKHOLE GRAVITATIONAL PULL ON PLAYER & SHRINK
        # ----------------------------------------------------
        BH_X, BH_Y = 400, 300
        p_dx = BH_X - player_rect.centerx
        p_dy = BH_Y - player_rect.centery
        p_dist = math.hypot(p_dx, p_dy)

        if is_blackhole and p_dist > 0:
            pull_mag = max(1.2, min(5.4, 750.0 / (p_dist + 50.0)))
            player_rect.x += int((p_dx / p_dist) * pull_mag)
            player_rect.y += int((p_dy / p_dist) * pull_mag)

            if p_dist < 26:
                player_health = 0
                for _ in range(80):
                    ang = random.uniform(0, 2 * math.pi)
                    spd = random.uniform(2, 8)
                    particles.append([BH_X, BH_Y, math.cos(ang) * spd, math.sin(ang) * spd, random.randint(5, 14), random.choice([(180, 20, 255), (255, 50, 100), (0, 255, 255), (255, 255, 255)])])
                boss_expl_snd.play()
                state = 5

        # Bullets Firing
        if is_firing and player_health > 0:
            b_cnt = unlocked_bullets + (1 if skills['double']['active'] else 0)
            for i in range(b_cnt):
                offset = (i - (b_cnt - 1) / 2.0) * 16
                bullets.append({'rect': pygame.Rect(player_rect.centerx + int(offset) - 3, player_rect.top - 8, 6, 16)})
            shoot_snd.play()

        # Pause button click
        if (m_c and is_h_pause) or key_p or key_escape:
            tap_snd.play()
            click_cooldown = 12
            m_c = False
            state = 10
            key_p = False
            key_escape = False

        # Background Drawing
        if not is_blackhole:
            galaxy_bg_y += 0.05
            if galaxy_bg_y >= bg_height:
                galaxy_bg_y = 0
            current_bg = galaxy_bg if current_selected_env == 1 else nebula_bg
            screen.blit(current_bg, (0, int(galaxy_bg_y)))
            screen.blit(current_bg, (0, int(galaxy_bg_y) - bg_height))
        else:
            screen.blit(blackhole_bg, (0, 0))

        # ----------------------------------------------------
        # STARS: SUCKED TOWARD BLACKHOLE AND VANISH AT CENTER
        # ----------------------------------------------------
        for s in stars:
            if is_blackhole:
                sdx = BH_X - s[0]
                sdy = BH_Y - s[1]
                sdist = math.hypot(sdx, sdy)

                s_spd = max(0.8, min(2.5, s[2] * 0.25 + 0.6))

                if sdist < 24:
                    angle = random.uniform(0, 2 * math.pi)
                    spawn_dist = random.uniform(380, 520)
                    s[0] = BH_X + math.cos(angle) * spawn_dist
                    s[1] = BH_Y + math.sin(angle) * spawn_dist
                    s[2] = random.uniform(1.0, 3.0)
                    s[3] = random.randint(100, 255)
                else:
                    s[0] += (sdx / sdist) * s_spd
                    s[1] += (sdy / sdist) * s_spd

                if sdist >= 26:
                    current_brightness = max(30, s[3] - random.randint(0, 60))
                    pygame.draw.rect(screen, (current_brightness, current_brightness, current_brightness), (int(s[0]), int(s[1]), 2, 2))
            else:
                current_brightness = max(30, s[3] - random.randint(0, 80))
                pygame.draw.rect(screen, (current_brightness, current_brightness, current_brightness), (s[0], int(s[1]), 2, 2))
                s[1] += s[2]
                if s[1] > HEIGHT:
                    s[1] = 0
                    s[0] = random.randint(0, WIDTH)

        # Asteroids Update & Collision
        asteroid_group.update()
        asteroid_group.draw(screen)

        for ast in list(asteroid_group):
            if ast.rect.colliderect(player_rect):
                if not skills['immortal']['active'] and revive_protection_timer <= 0:
                    player_health -= 30
                    hit_snd.play()
                ast.kill()
                for _ in range(12):
                    particles.append([ast.rect.centerx, ast.rect.centery, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 7), (120, 120, 130)])

        current_tick = pygame.time.get_ticks()
        max_asteroids_in_match = 12 if current_level <= 30 else 7
        if asteroids_spawned < max_asteroids_in_match:
            if current_tick - last_spawn_tick > next_spawn_time:
                new_asteroid = Asteroid(asteroid_img, env=current_selected_env)
                asteroid_group.add(new_asteroid)
                asteroids_spawned += 1
                last_spawn_tick = current_tick
                next_spawn_time = random.randint(7000, 14000)

        all_enemies_objs = fighters + elites + heavies

        # --- PROGRESSIVE BEGINNER-FRIENDLY DIFFICULTY TUNING ---
        eff_speed_lvl = min(current_level, 10)
        eff_dmg_lvl = min(current_level, 3)

        if current_level == 1:
            max_fighters = 3
            max_elites = 0
            max_heavies = 0
            spawn_chance = 75
            fire_chance = 180
        elif current_level == 2:
            max_fighters = 4
            max_elites = 1
            max_heavies = 0
            spawn_chance = 65
            fire_chance = 160
        elif current_level == 3:
            max_fighters = 5
            max_elites = 2
            max_heavies = 0  # No heavies on lvl 3!
            spawn_chance = 55
            fire_chance = 140
        elif current_level == 4:
            max_fighters = 5
            max_elites = 2
            max_heavies = 0  # No heavies on lvl 4!
            spawn_chance = 50
            fire_chance = 130
        elif current_level == 5:
            max_fighters = 6
            max_elites = 3
            max_heavies = 1  # 1 heavy gently introduced
            spawn_chance = 45
            fire_chance = 115
        elif current_level <= 10:
            max_fighters = int(5 + current_level * 0.3)
            max_elites = int(2 + current_level * 0.2)
            max_heavies = int(1 + current_level * 0.15)
            spawn_chance = max(25, int(50 - current_level * 1.5))
            fire_chance = max(50, int(130 - current_level * 3.5))
        else:
            max_fighters = min(10, int(7 + current_level * 0.2))
            max_elites = min(6, int(4 + current_level * 0.15))
            max_heavies = min(4, int(2 + current_level * 0.1))
            spawn_chance = max(15, int(40 - current_level * 0.6))
            fire_chance = max(30, int(95 - current_level * 1.5))

        # --- SPAWN EXECUTION ---
        if not boss_active and not boss_arriving and boss_defeated_timer == 0:
            if len(fighters) < max_fighters and random.randint(1, spawn_chance) == 1:
                nr = fighter_img.get_rect(center=(random.randint(50, WIDTH - 50), -50))
                if check_enemy_spawn(nr, all_enemies_objs):
                    fighters.append({'rect': nr, 'hp': 1, 'max_hp': 1, 'start_x': nr.x, 'time': random.randint(0, 50), 'type': 'fighter', 'dive_speed': random.uniform(2.5, 4.0)})

            if current_level >= 2 and len(elites) < max_elites and random.randint(1, int(spawn_chance * 1.4)) == 1:
                nr = elite_img.get_rect(center=(random.randint(50, WIDTH - 50), -50))
                if check_enemy_spawn(nr, all_enemies_objs):
                    e_hp = 2 if current_level <= 5 else 3
                    elites.append({'rect': nr, 'hp': e_hp, 'max_hp': e_hp, 'start_x': nr.x, 'time': random.randint(0, 50), 'type': 'elite'})

            if current_level >= 5 and len(heavies) < max_heavies and random.randint(1, int(spawn_chance * 2.2)) == 1:
                nr = heavy_img.get_rect(center=(random.randint(60, WIDTH - 60), -60))
                if check_enemy_spawn(nr, all_enemies_objs):
                    h_hp = 5 if current_level <= 9 else 8
                    heavies.append({'rect': nr, 'hp': h_hp, 'max_hp': h_hp, 'start_x': nr.x, 'time': 0, 'type': 'heavy'})

        # --- ENEMY MOVEMENT, COMBAT & BLACKHOLE GRAVITATIONAL PULL ---
        for e_list, val, e_type in [(fighters, 1, 'fighter'), (elites, 2, 'elite'), (heavies, 5, 'heavy')]:
            for e in e_list[:]:
                e['time'] = e.get('time', 0) + 1
                e['start_x'] = e.get('start_x', e['rect'].x)

                if e_type == 'fighter':
                    e['rect'].y += int((e.get('dive_speed', 3.0) + eff_speed_lvl * 0.2) * env_speed_mult)
                    strafe = math.sin(e['time'] * 0.08) * 3.5 * env_speed_mult
                    e['rect'].x += int(strafe)
                elif e_type == 'elite':
                    e['rect'].y += int((2.0 + eff_speed_lvl * 0.15) * env_speed_mult)
                    wave = math.sin(e['time'] * 0.05) * 6
                    e['rect'].x = int(e['start_x'] + wave)
                    if e['rect'].centerx < player_rect.centerx - 10:
                        e['start_x'] += 1
                    elif e['rect'].centerx > player_rect.centerx + 10:
                        e['start_x'] -= 1
                elif e_type == 'heavy':
                    e['rect'].y += int((1.4 + eff_speed_lvl * 0.1) * env_speed_mult)
                    if e['rect'].centerx < player_rect.centerx - 20:
                        e['rect'].x += 1
                    elif e['rect'].centerx > player_rect.centerx + 20:
                        e['rect'].x -= 1

                # Blackhole Attraction on Enemies
                if is_blackhole:
                    edx = BH_X - e['rect'].centerx
                    edy = BH_Y - e['rect'].centery
                    edist = math.hypot(edx, edy)
                    if edist > 0:
                        e_pull = max(0.9, min(4.5, 600.0 / (edist + 70.0)))
                        e['rect'].x += int((edx / edist) * e_pull)
                        e['rect'].y += int((edy / edist) * e_pull)

                    # Enemy sucked into singularity!
                    if edist < 28:
                        if e in e_list:
                            e_list.remove(e)
                        update_coins(1 if val == 1 else 2 if val == 2 else 5)
                        kill_count += 1
                        expl_snd.play()
                        for _ in range(16):
                            particles.append([BH_X, BH_Y, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 7), random.choice(BLAST_COLORS)])
                        continue

                # Separation logic to avoid clumping
                for other in all_enemies_objs:
                    if e != other and e['rect'].colliderect(other['rect']):
                        if e['rect'].x < other['rect'].x:
                            e['rect'].x -= 2
                        else:
                            e['rect'].x += 2

                e['rect'].x = max(0, min(WIDTH - e['rect'].width, e['rect'].x))

                # Enemy Shooting Archetypes
                if random.randint(1, int(fire_chance)) == 1:
                    dmg = eff_dmg_lvl * val
                    if e_type == 'fighter':
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 3, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': RED})
                    elif e_type == 'elite':
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].left + 4, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': MAGENTA})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].right - 10, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': MAGENTA})
                    elif e_type == 'heavy':
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].bottom, 10, 16), 'damage': dmg + 5, 'color': ORANGE})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].left + 5, e['rect'].bottom - 5, 8, 14), 'damage': dmg, 'color': YELLOW})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].right - 13, e['rect'].bottom - 5, 8, 14), 'damage': dmg, 'color': YELLOW})

                # Emit thrusters for active enemies
                vfx_engine.emit_enemy_thruster(e['rect'].centerx, e['rect'].top, e_type)

                # Collision with Player
                if e['rect'].colliderect(player_rect):
                    if e in e_list:
                        e_list.remove(e)
                    if not skills['immortal']['active'] and revive_protection_timer <= 0:
                        player_health -= (15 if e_type == 'fighter' else 25 if e_type == 'elite' else 40)
                        hit_snd.play()
                    for _ in range(15):
                        particles.append([e['rect'].centerx, e['rect'].centery, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 6), random.choice(BLAST_COLORS)])
                elif e['rect'].top > HEIGHT:
                    if e in e_list:
                        e_list.remove(e)

        # Emit player ship engine thrusters
        vfx_engine.emit_player_thruster(player_rect.centerx, player_rect.bottom)

        # Boss Logic & Thrusters
        if boss_active:
            if boss_death_timer > 0:
                boss_death_timer -= 1
                vfx_engine.update_and_draw_boss_death(screen, boss_rect, current_boss_img, boss_death_timer, expl_snd)
                if boss_death_timer == 1:
                    boss_active = False
                    boss_defeated_timer = 120
                    boss_expl_snd.play()
                    if current_selected_env == 1:
                        if current_level == max_galaxy_level and max_galaxy_level < 40:
                            max_galaxy_level += 1
                        if max_galaxy_level > 30:
                            env2_unlocked = True
                    elif current_selected_env == 2:
                        if current_level == max_nebula_level and max_nebula_level < 40:
                            max_nebula_level += 1
                        if max_nebula_level > 30:
                            env3_unlocked = True
                    elif current_selected_env == 3:
                        if current_level == max_blackhole_level and max_blackhole_level < 40:
                            max_blackhole_level += 1
                    save_game()
            else:
                vfx_engine.emit_boss_thrusters(boss_rect)

                if boss_rect.top < 70:
                    boss_rect.y += 2

                boss_eff_tier = min(((current_level - 1) // 5) + 1, 8)
                b_spd = max(1.5, (2 + (boss_eff_tier // 2)) * env_speed_mult)

                if boss_rect.centerx < boss_target_x:
                    dist_x = boss_target_x - boss_rect.centerx
                    boss_rect.x += min(dist_x, b_spd)
                elif boss_rect.centerx > boss_target_x:
                    dist_x = boss_rect.centerx - boss_target_x
                    boss_rect.x -= min(dist_x, b_spd)

                if abs(boss_rect.centerx - boss_target_x) < 4:
                    boss_target_x = random.randint(100, 700)

                shoot_chance = max(8, 28 - (current_level * 2))
                if random.randint(1, int(shoot_chance)) == 1:
                    bullet_x = boss_rect.centerx - 6
                    bullet_y = boss_rect.centery + 10
                    boss_eff_damage = min(current_level, 5)
                    enemy_bullets.append({'rect': pygame.Rect(bullet_x, bullet_y, 12, 22), 'damage': 10 * boss_eff_damage, 'color': RED})

        # --- DRAWING & COLLISIONS ---
        # Render all ship thrusters beneath hull sprites
        vfx_engine.update_and_draw_thrusters(screen)

        # Enemy Bullets
        eb_speed = int(6 * env_speed_mult)
        for eb in enemy_bullets[:]:
            eb['rect'].y += max(4, eb_speed)
            b_col = eb.get('color', RED)
            pygame.draw.rect(screen, b_col, eb['rect'], border_radius=3)
            pygame.draw.rect(screen, WHITE, eb['rect'].inflate(-2, -4), border_radius=2)

            if eb['rect'].colliderect(player_rect):
                if not skills['immortal']['active'] and revive_protection_timer <= 0:
                    player_health -= eb['damage']
                    hit_snd.play()
                if eb in enemy_bullets:
                    enemy_bullets.remove(eb)
            elif eb['rect'].top > HEIGHT:
                if eb in enemy_bullets:
                    enemy_bullets.remove(eb)

        # Player Bullets
        pb_speed = int(14 * env_speed_mult)
        for b in bullets[:]:
            b['rect'].y -= max(8, pb_speed)
            hit = False

            if boss_active and boss_death_timer == 0:
                if b['rect'].colliderect(boss_rect):
                    boss_hp -= 5
                    hit_snd.play()
                    if b in bullets:
                        bullets.remove(b)
                    if boss_hp <= 0:
                        boss_death_timer = 180
                        vfx_engine.reset_boss_effects()
                        update_coins(100 + current_level * 50)
                    hit = True

            if not hit:
                for e_list, c_val, _ in [(fighters, 1, 'fighter'), (elites, 2, 'elite'), (heavies, 5, 'heavy')]:
                    for e in e_list[:]:
                        if b['rect'].colliderect(e['rect']):
                            e['hp'] -= 1
                            if b in bullets:
                                bullets.remove(b)

                            if e['hp'] <= 0:
                                if e in e_list:
                                    e_list.remove(e)
                                update_coins(2 if c_val == 1 else 4 if c_val == 2 else 8)
                                kill_count += 1
                                expl_snd.play()

                                for _ in range(18):
                                    p_color = random.choice(BLAST_COLORS)
                                    particles.append([e['rect'].centerx, e['rect'].centery, random.uniform(-5, 5), random.uniform(-5, 5), random.randint(3, 7), p_color])
                            else:
                                hit_snd.play()
                                particles.append([b['rect'].centerx, b['rect'].top, random.uniform(-2, 2), random.uniform(-2, 2), 3, CYAN])
                            hit = True
                            break
                    if hit:
                        break

            # Remove off-screen player bullets (Prevents memory leak)
            if not hit and b['rect'].bottom < 0:
                if b in bullets:
                    bullets.remove(b)

        # Powerups Spawning
        if random.randint(1, 700) == 1:
            t = random.choice(['immortal', 'double'])
            achievements.append({'rect': pygame.Rect(random.randint(50, WIDTH - 50), -50, 32, 32), 'type': t})

        for a in achievements[:]:
            a['rect'].y += max(2, int(3 * env_speed_mult))
            p_color = skills[a['type']]['color']
            pygame.draw.circle(screen, p_color, a['rect'].center, 16)
            pygame.draw.circle(screen, WHITE, a['rect'].center, 8)
            draw_text("S" if a['type'] == 'immortal' else "2X", FONT_HP, BLACK, a['rect'].centerx, a['rect'].centery)

            if a['rect'].colliderect(player_rect):
                skills[a['type']]['active'] = True
                skills[a['type']]['timer'] = now + skills[a['type']]['duration']
                tap_snd.play()
                if a in achievements:
                    achievements.remove(a)
            elif a['rect'].top > HEIGHT or a['rect'].bottom < 0 or a['rect'].right < 0 or a['rect'].left > WIDTH:
                if a in achievements:
                    achievements.remove(a)

        # Drawing Bullets
        for b in bullets:
            pygame.draw.rect(screen, CYAN, b['rect'], border_radius=3)
            pygame.draw.rect(screen, WHITE, b['rect'].inflate(-2, -4), border_radius=2)

        # Drawing Ships (with Blackhole shrinkage if near center)
        for f in fighters:
            if is_blackhole:
                f_dist = math.hypot(BH_X - f['rect'].centerx, BH_Y - f['rect'].centery)
                if f_dist < 150:
                    f_scale = max(0.2, f_dist / 150.0)
                    scaled_f = pygame.transform.scale(fighter_img, (max(8, int(50 * f_scale)), max(8, int(50 * f_scale))))
                    screen.blit(scaled_f, scaled_f.get_rect(center=f['rect'].center))
                else:
                    screen.blit(fighter_img, f['rect'])
            else:
                screen.blit(fighter_img, f['rect'])

        for e in elites:
            if is_blackhole:
                e_dist = math.hypot(BH_X - e['rect'].centerx, BH_Y - e['rect'].centery)
                if e_dist < 150:
                    e_scale = max(0.2, e_dist / 150.0)
                    scaled_e = pygame.transform.scale(elite_img, (max(10, int(60 * e_scale)), max(10, int(60 * e_scale))))
                    screen.blit(scaled_e, scaled_e.get_rect(center=e['rect'].center))
                else:
                    screen.blit(elite_img, e['rect'])
            else:
                screen.blit(elite_img, e['rect'])

            if e['hp'] < e['max_hp']:
                hp_w = int((e['rect'].width - 8) * (e['hp'] / e['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (e['rect'].left + 4, e['rect'].top - 8, e['rect'].width - 8, 4), border_radius=2)
                pygame.draw.rect(screen, MAGENTA, (e['rect'].left + 4, e['rect'].top - 8, hp_w, 4), border_radius=2)

        for h in heavies:
            if is_blackhole:
                h_dist = math.hypot(BH_X - h['rect'].centerx, BH_Y - h['rect'].centery)
                if h_dist < 150:
                    h_scale = max(0.2, h_dist / 150.0)
                    scaled_h = pygame.transform.scale(heavy_img, (max(12, int(80 * h_scale)), max(12, int(80 * h_scale))))
                    screen.blit(scaled_h, scaled_h.get_rect(center=h['rect'].center))
                else:
                    screen.blit(heavy_img, h['rect'])
            else:
                screen.blit(heavy_img, h['rect'])

            if h['hp'] < h['max_hp']:
                hp_w = int((h['rect'].width - 10) * (h['hp'] / h['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (h['rect'].left + 5, h['rect'].top - 10, h['rect'].width - 10, 5), border_radius=2)
                pygame.draw.rect(screen, ORANGE, (h['rect'].left + 5, h['rect'].top - 10, hp_w, 5), border_radius=2)

        if boss_active and boss_death_timer == 0:
            screen.blit(current_boss_img, boss_rect)

        # Particles Update & Draw
        for particle in particles[:]:
            particle[0] += particle[2]
            particle[1] += particle[3]
            particle[4] -= 0.25
            if particle[4] > 0:
                pygame.draw.circle(screen, particle[5], (int(particle[0]), int(particle[1])), int(particle[4]))
            else:
                particles.remove(particle)

        # Player Shield / Revive Protection aura
        if skills['immortal']['active'] or revive_protection_timer > 0:
            shield_radius = max(player_rect.width, player_rect.height) // 2 + 10
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shield_color = (0, 255, 255, 120) if skills['immortal']['active'] else (255, 255, 100, 140)
            pygame.draw.circle(shield_surf, shield_color, (shield_radius, shield_radius), shield_radius, width=4)
            screen.blit(shield_surf, (player_rect.centerx - shield_radius, player_rect.centery - shield_radius))

        if revive_protection_timer > 0:
            revive_protection_timer -= 1

        # Draw Player (with spaghettification shrink in Blackhole)
        if is_blackhole and p_dist < 160:
            scale_ratio = max(0.15, min(1.0, p_dist / 160.0))
            cur_w = max(12, int(70 * scale_ratio))
            cur_h = max(12, int(70 * scale_ratio))
            p_draw_surf = pygame.transform.scale(player_img, (cur_w, cur_h))
            p_draw_rect = p_draw_surf.get_rect(center=player_rect.center)
            screen.blit(p_draw_surf, p_draw_rect)
        else:
            screen.blit(player_img, player_rect)

        # ==========================
        # MODERN UI & HUD
        # ==========================
        hud_bg = pygame.Surface((WIDTH, 65), pygame.SRCALPHA)
        pygame.draw.rect(hud_bg, (12, 18, 30, 230), hud_bg.get_rect(), border_bottom_left_radius=20, border_bottom_right_radius=20)
        pygame.draw.rect(hud_bg, (0, 200, 255, 80), hud_bg.get_rect(), width=2, border_bottom_left_radius=20, border_bottom_right_radius=20)
        screen.blit(hud_bg, (0, 0))

        # Coin Display
        screen.blit(coin_icon, (15, 12))
        draw_text(f"{total_coins}", FONT_HUD, YELLOW, 65, 16, center=False)

        # Current Level Display
        env_names = {1: "GALAXY", 2: "NEBULA", 3: "BLACKHOLE"}
        draw_text(f"{env_names.get(current_selected_env, 'GALAXY')} • LVL {current_level}", FONT_UI, CYAN, WIDTH // 2 - 20, 32)

        # Pause Button in HUD
        draw_button(screen, "||", FONT_SMALL, WHITE, pause_btn_rect, (40, 50, 70), is_h_pause, border_radius=10, outline_color=CYAN)

        # Player Health Bar (Right Side)
        health_bar_bg = pygame.Rect(WIDTH - 250, 20, 180, 22)
        pygame.draw.rect(screen, (35, 10, 15), health_bar_bg, border_radius=11)
        pygame.draw.rect(screen, (70, 70, 90), health_bar_bg, 2, border_radius=11)

        curr_hp_w = int(176 * (max(0, player_health) / unlocked_hp))
        if curr_hp_w > 0:
            hp_color = GREEN if player_health > unlocked_hp * 0.3 else RED
            pygame.draw.rect(screen, hp_color, (WIDTH - 248, 22, curr_hp_w, 18), border_radius=9)

        draw_text(f"HP {int(max(0, player_health))}/{unlocked_hp}", FONT_HP, WHITE, WIDTH - 160, 31)

        # Boss Health Bar
        if boss_active and boss_death_timer == 0:
            boss_hp_bg = pygame.Rect(WIDTH // 2 - 160, 75, 320, 20)
            pygame.draw.rect(screen, (40, 10, 10), boss_hp_bg, border_radius=10)
            pygame.draw.rect(screen, RED, boss_hp_bg, 2, border_radius=10)

            boss_hp_w = int(316 * (max(0, boss_hp) / boss_max_hp))
            if boss_hp_w > 0:
                pygame.draw.rect(screen, (255, 30, 80), (WIDTH // 2 - 158, 77, boss_hp_w, 16), border_radius=8)
            draw_text(f"BOSS HP: {int(max(0, boss_hp))}/{boss_max_hp}", FONT_HP, WHITE, WIDTH // 2, 85)

        # Mobile Slide Hint
        if control_type == 'MOBILE':
            draw_text("SLIDE FINGER TO MOVE & FIRE", FONT_SMALL, (100, 120, 150), WIDTH // 2, HEIGHT - 20)

        # Active Powerup Timers
        y_offset_sh = 80
        for s_key, s_val in skills.items():
            if s_val['active']:
                rem_time = (s_val['timer'] - now) // 1000
                if rem_time > 0:
                    pill_rect = pygame.Rect(15, y_offset_sh, 140, 28)
                    draw_panel(screen, pill_rect, alpha=200, bg_color=(20, 25, 35), border_color=s_val['color'], border_width=2, border_radius=8)
                    draw_text(f"{s_val['label']} {rem_time}s", FONT_SMALL, s_val['color'], pill_rect.centerx, pill_rect.centery)
                    y_offset_sh += 34
                else:
                    s_val['active'] = False

        # Boss Spawning Condition (Beginner-friendly kill scaling)
        boss_kill_reqs = {1: 15, 2: 20, 3: 25, 4: 35, 5: 45, 6: 60, 7: 75, 8: 90, 9: 105, 10: 120}
        req_kills = min(200, 120 + (current_level - 10) * 4) if current_level >= 11 else boss_kill_reqs.get(current_level, 25)

        if kill_count >= req_kills and not boss_active and not boss_arriving and boss_defeated_timer == 0:
            boss_arriving = True
            boss_warning_timer = 180

        if boss_arriving:
            boss_warning_timer -= 1
            if (boss_warning_timer // 15) % 2 == 0:
                draw_text("⚠ BOSS INCOMING ⚠", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2)
            if boss_warning_timer <= 0:
                boss_arriving = False
                boss_active = True

        if boss_defeated_timer > 0:
            boss_defeated_timer -= 1
            draw_text("VICTORY! BOSS DEFEATED", FONT_TITLE, CYAN, WIDTH // 2, HEIGHT // 2)
            if boss_defeated_timer <= 0:
                state = 4
                if not win_snd_played:
                    game_won_snd.play()
                    win_snd_played = True

        if player_health <= 0:
            state = 5
            if not loose_snd_played:
                game_loose_snd.play()
                loose_snd_played = True

    # ==========================
    # PAUSE SCREEN (STATE 10)
    # ==========================
    elif state == 10:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(160, 90, 480, 420)
        draw_panel(screen, box, alpha=245, bg_color=(18, 22, 32), border_color=CYAN, border_width=3, border_radius=20)
        draw_text("GAME PAUSED", FONT_MODAL_TITLE, CYAN, 400, 135)
        draw_text("MISSION IN PROGRESS", FONT_SMALL, LIGHT_GRAY, 400, 170)

        btn_resume = pygame.Rect(200, 205, 400, 52)
        btn_restart = pygame.Rect(200, 270, 400, 50)
        btn_settings = pygame.Rect(200, 330, 400, 50)
        btn_menu = pygame.Rect(200, 390, 400, 50)

        mx, my = pygame.mouse.get_pos()
        is_h_p = btn_resume.collidepoint(mx, my)
        is_h_r = btn_restart.collidepoint(mx, my)
        is_h_s = btn_settings.collidepoint(mx, my)
        is_h_m = btn_menu.collidepoint(mx, my)

        if is_h_p: focused_btn = 0
        if is_h_r: focused_btn = 1
        if is_h_s: focused_btn = 2
        if is_h_m: focused_btn = 3

        if key_down: focused_btn = (focused_btn + 1) % 4
        if key_up:   focused_btn = (focused_btn - 1) % 4

        is_h_p = is_h_p or focused_btn == 0
        is_h_r = is_h_r or focused_btn == 1
        is_h_s = is_h_s or focused_btn == 2
        is_h_m = is_h_m or focused_btn == 3

        draw_button(screen, "RESUME MISSION", FONT_UI, WHITE, btn_resume, GREEN, is_h_p)
        draw_button(screen, "RESTART LEVEL", FONT_UI, WHITE, btn_restart, ORANGE, is_h_r)
        draw_button(screen, "SETTINGS", FONT_UI, WHITE, btn_settings, BLUE, is_h_s)
        draw_button(screen, "ABORT TO MENU", FONT_UI, WHITE, btn_menu, RED, is_h_m)

        if m_c or key_enter or key_escape or key_p:
            if is_h_p or (key_escape or key_p):
                tap_snd.play()
                state = 3
                click_cooldown = 12
                m_c = False
                key_escape = False
                key_p = False
            elif is_h_s and (m_c or key_enter):
                tap_snd.play()
                settings_from_pause = True
                state = 9
                click_cooldown = 12
                m_c = False
                key_enter = False
            elif is_h_m and (m_c or key_enter):
                tap_snd.play()
                warning_target = "MENU"
                state = 15
                click_cooldown = 12
                m_c = False
                key_enter = False
            elif is_h_r and (m_c or key_enter):
                tap_snd.play()
                warning_target = "RESTART"
                state = 15
                click_cooldown = 12
                m_c = False
                key_enter = False

    # ==========================
    # WARNING SCREEN (STATE 15)
    # ==========================
    elif state == 15:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        w_box = pygame.Rect(140, 150, 520, 300)
        draw_panel(screen, w_box, alpha=250, bg_color=(25, 15, 20), border_color=RED, border_width=3, border_radius=20)

        draw_text("ABORT MISSION?", FONT_MODAL_TITLE, RED, 400, 195)
        draw_text("If you leave or restart now,", FONT_UI, WHITE, 400, 245)
        draw_text("all unbanked level coins will be lost!", FONT_SMALL, YELLOW, 400, 280)

        btn_w_back = pygame.Rect(180, 340, 200, 52)
        btn_ok = pygame.Rect(420, 340, 200, 52)

        mx, my = pygame.mouse.get_pos()
        is_h_back = btn_w_back.collidepoint(mx, my)
        is_h_ok = btn_ok.collidepoint(mx, my)

        draw_button(screen, "RESUME", FONT_UI, WHITE, btn_w_back, GREEN, is_h_back)
        draw_button(screen, "CONFIRM LEAVE", FONT_UI, WHITE, btn_ok, RED, is_h_ok)

        if m_c or key_escape or key_enter:
            if is_h_back or key_escape:
                tap_snd.play()
                state = 10
                click_cooldown = 12
                m_c = False
                key_escape = False
            elif is_h_ok or key_enter:
                tap_snd.play()
                total_coins -= level_coins
                level_coins = 0
                click_cooldown = 12
                m_c = False
                key_enter = False

                if warning_target == "MENU":
                    save_game()
                    state = 0
                elif warning_target == "RESTART":
                    reset_level_logic(selected_level)
                    state = 3

    # ==========================
    # WIN / LOSS (STATE 4 & 5)
    # ==========================
    elif state == 4 or state == 5:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 215))
        screen.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        # State 5: Dedicated Confirmation Modal for Revive
        if state == 5 and show_revive_confirm:
            p_box = pygame.Rect(140, 110, 520, 380)
            draw_panel(screen, p_box, alpha=250, bg_color=(25, 20, 30), border_color=YELLOW, border_width=3, border_radius=20)

            draw_text("CONFIRM REVIVE", FONT_MODAL_TITLE, YELLOW, 400, 160)
            draw_text("RESTORE FULL COMBAT POWER", FONT_MODAL_SUB, CYAN, 400, 200)

            feat_card = pygame.Rect(170, 235, 460, 60)
            pygame.draw.rect(screen, (35, 30, 45), feat_card, border_radius=12)
            pygame.draw.rect(screen, (80, 70, 100), feat_card, width=1, border_radius=12)
            draw_text("Full Health + 3s Invulnerability Shield", FONT_SMALL, WHITE, 400, 255)
            
            c_price = get_revive_price(current_level, revives_done_this_level)
            can_afford = total_coins >= c_price
            cost_color = GREEN if can_afford else RED
            draw_text(f"Price: {c_price} Coins  |  Your Coins: {total_coins}", FONT_SMALL, cost_color, 400, 278)

            b_back = pygame.Rect(180, 380, 200, 52)
            b_buy = pygame.Rect(420, 380, 200, 52)

            is_h_rbk = b_back.collidepoint(mx, my)
            is_h_rbuy = b_buy.collidepoint(mx, my)

            draw_button(screen, "CANCEL", FONT_UI, WHITE, b_back, RED, is_h_rbk)
            draw_button(screen, f"REVIVE ({c_price})", FONT_UI, BLACK if can_afford else WHITE, b_buy, GREEN if can_afford else DARK_GRAY, is_h_rbuy)

            if m_c:
                if is_h_rbk:
                    tap_snd.play()
                    show_revive_confirm = False
                    click_cooldown = 12
                    m_c = False
                elif is_h_rbuy and can_afford:
                    total_coins -= c_price
                    revives_done_this_level += 1
                    player_health = unlocked_hp
                    revive_protection_timer = 180
                    bullets.clear()
                    fighters.clear()
                    elites.clear()
                    heavies.clear()
                    enemy_bullets.clear()

                    for _ in range(60):
                        particles.append([player_rect.centerx, player_rect.centery, random.uniform(-10, 10), random.uniform(-10, 10), random.randint(6, 12), CYAN])

                    tap_snd.play()
                    state = 3
                    show_revive_confirm = False
                    click_cooldown = 12
                    m_c = False

        # Regular Victory Screen (State 4)
        elif state == 4:
            box = pygame.Rect(140, 90, 520, 420)
            draw_neon_panel(screen, box, accent=NEON_GREEN, alpha=250, border_radius=20, bg=(10,24,18))

            draw_text_shadow("🏆  VICTORY!", FONT_MODAL_TITLE, NEON_GREEN, 400, 135, shadow_color=(0,80,40), offset=2)
            draw_text("SECTOR SECURED", FONT_TINY, NEON_CYAN, 400, 170)
            draw_divider(screen, 180, 188, 620, NEON_GREEN, alpha=50)

            # Star Rating on Victory
            earned_stars = 3 if kill_count >= 20 else (2 if kill_count >= 10 else 1)
            star_icon = pygame.transform.scale(star_for_rating, (48, 48))
            start_x = 400 - ((earned_stars * 54) // 2) + 3
            for i in range(earned_stars):
                screen.blit(star_icon, (start_x + (i * 54), 205))

            stats_box = pygame.Rect(180, 275, 440, 50)
            pygame.draw.rect(screen, PANEL_MID, stats_box, border_radius=12)
            pygame.draw.rect(screen, NEON_GREEN, stats_box, width=1, border_radius=12)
            draw_text(f"🪙 +{level_coins} Coins Earned  |  ⚔ Kills: {kill_count}", FONT_SMALL, NEON_GOLD, 400, 300)

            b_m = pygame.Rect(175, 360, 210, 56)
            b_n = pygame.Rect(415, 360, 210, 56)

            is_h_m = b_m.collidepoint(mx, my)
            is_h_n = b_n.collidepoint(mx, my)

            draw_glowing_button(screen, "← MAIN MENU", FONT_UI, WHITE, b_m, NEON_BLUE, is_h_m, pulse_t=ui_pulse_t)
            draw_glowing_button(screen, "NEXT LEVEL ➔", FONT_UI, WHITE, b_n, NEON_GREEN, is_h_n, pulse_t=ui_pulse_t)

            if m_c or key_enter or key_escape or key_left:
                if is_h_m or key_escape or key_left:
                    tap_snd.play()
                    level_coins = 0
                    save_game()
                    state = 0
                    click_cooldown = 12
                    m_c = False
                    key_escape = False
                    key_left = False
                elif is_h_n or key_enter:
                    if current_level < 40:
                        level_coins = 0
                        selected_level = current_level + 1
                        reset_level_logic(selected_level)
                        tap_snd.play()
                        state = 3
                        click_cooldown = 12
                        m_c = False
                        key_enter = False

        # Regular Game Over Screen (State 5)
        elif state == 5:
            box = pygame.Rect(130, 80, 540, 450)
            draw_neon_panel(screen, box, accent=NEON_PINK, alpha=250, border_radius=20, bg=(28,10,15))

            draw_text_shadow("💀  MISSION FAILED", FONT_MODAL_TITLE, NEON_PINK, 400, 125, shadow_color=(80,0,0), offset=2)
            draw_text("SHIP DESTROYED IN COMBAT", FONT_TINY, LIGHT_GRAY, 400, 160)
            draw_divider(screen, 170, 178, 630, NEON_PINK, alpha=50)

            stats_box = pygame.Rect(170, 195, 460, 48)
            pygame.draw.rect(screen, PANEL_MID, stats_box, border_radius=12)
            pygame.draw.rect(screen, NEON_PINK, stats_box, width=1, border_radius=12)
            draw_text(f"🪙 Coins: +{level_coins}  |  ⚔ Enemies Down: {kill_count}", FONT_SMALL, NEON_GOLD, 400, 219)

            rev_b = pygame.Rect(190, 265, 420, 58)
            b_n   = pygame.Rect(190, 335, 420, 52)
            b_m   = pygame.Rect(190, 395, 420, 52)

            is_h_rev = rev_b.collidepoint(mx, my)
            is_h_n   = b_n.collidepoint(mx, my)
            is_h_m   = b_m.collidepoint(mx, my)

            if is_h_rev: focused_btn = 0
            if is_h_n: focused_btn = 1
            if is_h_m: focused_btn = 2
            
            if key_down: focused_btn = (focused_btn + 1) % 3
            if key_up: focused_btn = (focused_btn - 1) % 3
            
            is_h_rev = is_h_rev or focused_btn == 0
            is_h_n = is_h_n or focused_btn == 1
            is_h_m = is_h_m or focused_btn == 2

            draw_glowing_button(screen, "✨  REVIVE STARSHIP", FONT_UI, WHITE, rev_b, NEON_GOLD, is_h_rev, pulse_t=ui_pulse_t)
            draw_glowing_button(screen, "↻  RETRY MISSION", FONT_UI, WHITE, b_n, NEON_ORANGE, is_h_n, pulse_t=ui_pulse_t)
            draw_glowing_button(screen, "← MAIN MENU", FONT_UI, WHITE, b_m, NEON_BLUE, is_h_m, pulse_t=ui_pulse_t)

            if m_c or key_enter or key_escape or key_r:
                if is_h_rev and (m_c or (key_enter and focused_btn == 0)):
                    tap_snd.play()
                    show_revive_confirm = True
                    click_cooldown = 12
                    m_c = False
                    key_enter = False
                elif (is_h_n and (m_c or (key_enter and focused_btn == 1))) or key_r:
                    level_coins = 0
                    reset_level_logic(selected_level)
                    tap_snd.play()
                    state = 3
                    click_cooldown = 12
                    m_c = False
                    key_enter = False
                    key_r = False
                elif (is_h_m and (m_c or (key_enter and focused_btn == 2))) or key_escape:
                    tap_snd.play()
                    level_coins = 0
                    save_game()
                    state = 0
                    click_cooldown = 12
                    m_c = False
                    key_enter = False
                    key_escape = False

    # FPS Counter Overlay
    if show_fps:
        fps_val = int(clock.get_fps())
        fps_color = NEON_GREEN if fps_val >= 50 else NEON_GOLD if fps_val >= 30 else RED
        fps_text = FONT_TINY.render(f"FPS: {fps_val}", True, fps_color)
        fps_bg = pygame.Rect(WIDTH - 78, 4, 74, 22)
        pygame.draw.rect(screen, (10, 12, 20, 200), fps_bg, border_radius=6)
        pygame.draw.rect(screen, fps_color, fps_bg, width=1, border_radius=6)
        screen.blit(fps_text, fps_text.get_rect(center=fps_bg.center))

    pygame.display.flip()
    clock.tick(60)