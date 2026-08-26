"""Shared Crazyy Simulation game loop. Launch via main_pc.py or main_mobile.py."""
import webbrowser
import ctypes
try:
    myappid = 'iambkram.crazyysimulation.game.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

import pygame
import random
import sys
import json
import os
import math

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in (_ROOT_DIR, _SRC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cloud_sync
from platform_config import get_platform, is_mobile, is_pc
from pc import windowing as pc_windowing
from pc import controls as pc_controls
from mobile import scaling as mobile_scaling
from mobile import lifecycle as mobile_lifecycle
from mobile import touch_hud

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = _ROOT_DIR

try:
    os.chdir(app_dir)
except Exception:
    pass

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)

from settings import *
from ui.auth_ui import AuthUI
from ui.level_select_ui import render_env_select, render_level_select
from ui.store_ui import render_store, render_store_confirm, render_store_error
from ui.settings_ui import render_settings
auth_ui = AuthUI()

# ==========================================
# SCREEN SETUP (must happen before any image loading)
# ==========================================
WIDTH = 800
HEIGHT = 600
_plat = get_platform()

try:
    icon_path = os.path.join(app_dir, 'icon.ico')
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
    game_icon = pygame.image.load(icon_path)
    pygame.display.set_icon(game_icon)
except Exception:
    pass

if is_mobile():
    screen = mobile_scaling.create_window()
    is_fullscreen = True
else:
    screen = pc_windowing.create_window(
        fullscreen=False,
        use_scaled=_plat["use_scaled"],
        resizable=_plat["resizable"],
    )
    is_fullscreen = False

pygame.display.set_caption("Crazyy Simulation")

def apply_display_mode(fullscreen):
    """Safely apply Fullscreen or Windowed display mode with hardware scaling preserved."""
    global screen, is_fullscreen
    if is_mobile():
        is_fullscreen = True
        return screen
    screen, is_fullscreen = pc_windowing.apply_display_mode(screen, fullscreen)
    return screen

# Import only fonts and helper functions from assets (no heavy images yet)
from assets import *
from branding import CinematicBranding
from menu_battle import MenuBattleSimulation
from vfx import (VisualEffectsEngine, draw_neon_auth_bg,
                 draw_nebula_overlay, draw_blackhole_overlay, draw_neon_vignette)
from ai.enemy_ai import run_enemy_ai, SpawnDirector, WaveComposer

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

# Plasma bullet visuals are drawn procedurally via assets.draw_plasma_bullet()
# No static bullet_img needed — bullets are rendered in the gameplay loop

# SpawnDirector instance (initialized per-level in reset_level_logic)
spawn_director = None

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
unlocked_firerate, firerate_step = 1.0, 0
max_galaxy_level = 1
max_nebula_level = 1
max_blackhole_level = 1
level_scroll_y = 0
mouse_y_prev = 0
max_scroll_y = 850
control_type = get_platform()["default_control_type"]
show_settings_warning = False
fire_cooldown = 0
player_fire_anim = 0
player_dmg_anim = 0
click_cooldown = 0
ui_pulse_t = 0.0       # Global animation ticker for button glow effects
music_vol = 0.5
sfx_vol = 0.7
is_dragging_music = False
is_dragging_sfx = False
mission_scroll_y = 0
is_dragging_missions = False
level_drag_dist = 0
last_mouse_y = 0
touch_start_y = 0
touch_start_x = 0
total_drag_dist = 0
m_u = False
mouse_pressed = False
ignore_mouse_until_released = False
PLAYER_MIN_Y_NORMAL = 200
PLAYER_BOSS_MIN_Y = 380
PLAYER_MIN_Y = PLAYER_MIN_Y_NORMAL
PLAYER_MAX_Y = HEIGHT - 10
PLAYER_MIN_X = 10
PLAYER_MAX_X = WIDTH - 10
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

# Boss AI Brain State Machine
boss_ai_state    = 'patrol'    # patrol | chase | sweep | rage | dive | spiral | corner_hunt
boss_ai_timer    = 0           # Frame counter for current state
boss_ai_phase    = 1           # Phase 1 (full HP), 2 (50%), 3 (25% - enraged)
boss_angle       = 0.0         # Visual rotation angle for boss ship
boss_sweep_dir   = 1           # Sweep direction: +1 right, -1 left
boss_spiral_t    = 0.0         # Spiral bullet angle accumulator
boss_dive_target = (400, 400)  # Dive-bomb target coordinates

asteroid_group = pygame.sprite.Group()

# Spawning logic variables
asteroids_spawned = 0
spawn_timer = 0
next_spawn_time = random.randint(3000, 7000)
last_spawn_tick = pygame.time.get_ticks()

fighters, elites, heavies, bullets, enemy_bullets, achievements, particles, damage_numbers = [], [], [], [], [], [], [], []
phantoms, berserkers, commanders = [], [], []   # New enemy types (Levels 31-40)
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
STATE_ENV_SELECT = 20
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
is_fullscreen = is_mobile()
show_fps = False         # FPS counter overlay toggle
visual_quality = 'high'  # 'low', 'medium', 'high'
screen_shake_enabled = True  # Screen shake effects toggle
auto_fire_enabled = False    # Auto-fire functionality
show_damage_enabled = True   # Floating damage numbers

global_shake_intensity = 0.0 # Current shake magnitude (decays over time)

# --- Start at branding animation (assets are already loaded) ---
login_error_msg = ""
state = -2
branding_anim = CinematicBranding()
last_frame_ticks = pygame.time.get_ticks()

SAVE_FILE = os.path.join(app_dir, "save.json")

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
        "firerate": unlocked_firerate,
        "firerate_step": firerate_step,
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
        "auto_fire": auto_fire_enabled,
        "show_damage": show_damage_enabled,
        "display_mode": "fullscreen" if is_fullscreen else "windowed"
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
        cloud_sync.queue_sync(data)
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
        if visual_quality == 'high':
            self.rot_speed = random.uniform(-4.0, 4.0)
        elif visual_quality == 'medium':
            self.rot_speed = random.uniform(-2.0, 2.0)
        else:
            self.rot_speed = random.uniform(-0.5, 0.5)

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
    global unlocked_bullets, bullet_step, unlocked_firerate, firerate_step, max_galaxy_level, max_nebula_level, max_blackhole_level, control_type
    global env1_unlocked, env2_unlocked, env3_unlocked
    global show_fps, visual_quality, screen_shake_enabled, is_fullscreen
    global auto_fire_enabled, show_damage_enabled

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
                unlocked_firerate = data.get("firerate", 1.0)
                firerate_step = data.get("firerate_step", 0)
                max_galaxy_level = max(1, min(40, data.get("max_galaxy_level", 1)))
                max_nebula_level = max(1, min(40, data.get("max_nebula_level", 1)))
                max_blackhole_level = max(1, min(40, data.get("max_blackhole_level", 1)))
                control_type = data.get("control_type", 'PC')
                music_vol = data.get("music_vol", 0.5)
                sfx_vol = data.get("sfx_vol", 0.7)
                show_fps = data.get("show_fps", False)
                visual_quality = data.get("visual_quality", "high")
                screen_shake_enabled = data.get("screen_shake", True)
                auto_fire_enabled = data.get("auto_fire", False)
                show_damage_enabled = data.get("show_damage", True)
                is_fullscreen_str = data.get("display_mode", "fullscreen")
                is_fullscreen = (is_fullscreen_str == "fullscreen")
                
                # Unlock criteria: 30 levels of preceding environment must be completed
                env1_unlocked = True
                env2_unlocked = data.get("env2_unlocked", False) or (max_galaxy_level > 30)
                env3_unlocked = data.get("env3_unlocked", False) or (max_nebula_level > 30)

                if music_vol is None: music_vol = 0.5
                if sfx_vol is None: sfx_vol = 0.7

                pygame.mixer.music.set_volume(music_vol)
                shoot_snd.set_volume(sfx_vol)
                tap_snd.set_volume(sfx_vol)
                expl_snd.set_volume(sfx_vol)
                hit_snd.set_volume(sfx_vol)
                boss_expl_snd.set_volume(sfx_vol)
                game_won_snd.set_volume(sfx_vol)
                game_loose_snd.set_volume(sfx_vol)
        except Exception as e:
            print("Error loading game:", e)

    if get_platform()["force_control_type"]:
        control_type = get_platform()["default_control_type"]
    if is_mobile():
        is_fullscreen = True
    global current_level, player_health, player_rect, bullets, enemy_bullets
    global fighters, elites, heavies, phantoms, berserkers, commanders
    global achievements, particles
    global boss_hp, boss_max_hp, boss_death_timer, current_level, boss_rect, kill_count
    global boss_active, boss_arriving, boss_target_x, current_boss_img
    global boss_warning_timer, boss_defeated_timer
    global blackhole_alert_active, revive_protection_timer
    global galaxy_bg_y, spawn_director

    galaxy_bg_y = 0.0

    if level is None:
        level = current_level if current_level is not None else 1
    current_level = int(level)
    player_health = unlocked_hp
    player_rect.center = (WIDTH // 2, HEIGHT - 70)

    bullets.clear()
    enemy_bullets.clear()
    fighters.clear()
    elites.clear()
    heavies.clear()
    phantoms.clear()
    berserkers.clear()
    commanders.clear()
    achievements.clear()
    particles.clear()
    damage_numbers.clear()
    vfx_engine.reset_boss_effects()
    vfx_engine.clear_all()

    # (Re)initialize the adaptive SpawnDirector for this level
    spawn_director = SpawnDirector(current_level, env=current_selected_env)

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

    # Reset Boss AI brain
    global boss_ai_state, boss_ai_timer, boss_ai_phase, boss_angle, boss_sweep_dir, boss_spiral_t, boss_dive_target
    boss_ai_state    = 'patrol'
    boss_ai_timer    = 0
    boss_ai_phase    = 1
    boss_angle       = 0.0
    boss_sweep_dir   = 1
    boss_spiral_t    = 0.0
    boss_dive_target = (WIDTH // 2, HEIGHT // 2)

    # Boss HP scaling — now uses environment-aware difficulty
    # Nebula starts harder than Galaxy; Blackhole starts harder than Nebula
    env_mult = {1: 1.0, 2: 1.35, 3: 1.75}.get(current_selected_env, 1.0)
    if current_level <= 10:
        boss_max_hp = int((200 + (current_level - 1) * 65) * env_mult)
    elif current_level <= 25:
        boss_max_hp = int((850 + (current_level - 10) * 175) * env_mult)
    else:
        boss_max_hp = int((3600 + (current_level - 25) * 290) * env_mult)
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

# Cloud sync setup
cloud_sync.set_app_dir(app_dir)
cloud_sync.load_local_session()
cloud_sync.start_sync_thread(SAVE_FILE)

if is_pc():
    apply_display_mode(is_fullscreen)

# --- Main Loop ---
clock = pygame.time.Clock()
running = True

current_bgm = None
pygame.mixer.music.set_volume(music_vol)

while running:
    m_wheel = 0
    current_frame_ticks = pygame.time.get_ticks()
    dt = (current_frame_ticks - last_frame_ticks)/(1000/60)
    last_frame_ticks = current_frame_ticks

    screen.fill(BLACK)
    prev_state = state
    now = pygame.time.get_ticks()
    m_p = pygame.mouse.get_pos()
    m_c = False
    mx, my = pygame.mouse.get_pos()
    m_down = pygame.mouse.get_pressed()[0]
    mouse_pressed = m_down
    
    if cloud_sync.save_updated_from_cloud:
        cloud_sync.save_updated_from_cloud = False
        load_game()

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
    key_backspace = False
    key_unicode = ""

    ui_pulse_t += 0.05   # Drives hover glow pulsation across all UI

    if click_cooldown > 0:
        click_cooldown -= 1
        if mouse_pressed:
            ignore_mouse_until_released = True

    mouse_dx, mouse_dy = 0, 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if is_mobile() and mobile_lifecycle.is_app_minimized(event):
            mobile_lifecycle.on_minimize()
            if state == 3:
                state = 10
            continue
        if is_mobile() and mobile_lifecycle.is_app_restored(event):
            mobile_lifecycle.on_restore()
            continue
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pressed = True
                if click_cooldown <= 0:
                    m_c = True
                    ignore_mouse_until_released = False
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
                if not ignore_mouse_until_released and click_cooldown <= 0:
                    m_u = True
                ignore_mouse_until_released = False
        if event.type == pygame.MOUSEWHEEL:
            m_wheel = event.y
        if event.type == pygame.MOUSEMOTION:
            mouse_dx, mouse_dy = event.rel
        if event.type == pygame.FINGERDOWN:
            mx, my = mobile_scaling.logical_from_finger(event)
            pygame.mouse.set_pos(mx, my)
            mouse_pressed = True
            if click_cooldown <= 0:
                m_c = True
                ignore_mouse_until_released = False
        if event.type == pygame.FINGERUP:
            mouse_pressed = False
            if not ignore_mouse_until_released and click_cooldown <= 0:
                m_u = True
            ignore_mouse_until_released = False
        if event.type == pygame.FINGERMOTION:
            nx, ny = mobile_scaling.logical_from_finger(event)
            mouse_dx, mouse_dy = nx - mx, ny - my
            mx, my = nx, ny
            pygame.mouse.set_pos(mx, my)
        if event.type == pygame.KEYDOWN:
            _uni = getattr(event, "unicode", "") or ""
            if _uni.isprintable() and len(_uni) > 0:
                key_unicode = _uni
            if is_mobile() and mobile_lifecycle.is_android_back(event):
                key_escape = True
            if event.key == pygame.K_RETURN: key_enter = True
            elif event.key == pygame.K_BACKSPACE: key_backspace = True
            elif event.key == pygame.K_ESCAPE: key_escape = True
            elif event.key == pygame.K_UP or event.key == pygame.K_w: key_up = True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s: key_down = True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a: key_left = True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d: key_right = True
            elif event.key == pygame.K_TAB: key_tab = True
            elif event.key == pygame.K_F11 and is_pc():
                apply_display_mode(not is_fullscreen)
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
            if cloud_sync.current_session_id is not None:
                state = 0  # Transition smoothly into Main Menu
            else:
                state = -3 # Transition to Login Screen
            click_cooldown = 12
            m_c = False

    # ==========================
    # AUTHENTICATION UI (STATES -3, -4, -4.1, -4.2, -5)
    # ==========================
    elif state == -3:
        state = auth_ui.render_method_select(screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now)
        if state != -3:
            click_cooldown = 12
            m_c = False
    elif state == -4:
        state = auth_ui.render_google_action(screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now)
        if state != -4:
            click_cooldown = 12
            m_c = False
    elif state == -4.1:
        auth_ui.handle_input(key_unicode, key_backspace, key_tab)
        state = auth_ui.render_auth_form(screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now, is_signup=True)
    elif state == -4.2:
        auth_ui.handle_input(key_unicode, key_backspace, key_tab)
        state = auth_ui.render_auth_form(screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now, is_signup=False)
    elif state == -5:
        auth_ui.handle_input(key_unicode, key_backspace, key_tab)
        state = auth_ui.render_auth_form(screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now, is_signup=True, is_bind=True)
        if state == 11: # Cancelled bind, back to settings
            click_cooldown = 12
            m_c = False
    # ==========================
    # SYNCING PROFILE (STATE -6)
    # ==========================
    elif state == -6:
        draw_neon_auth_bg(screen, now)
        
        draw_text_shadow("SYNCING PROFILE...", FONT_TITLE, NEON_CYAN, 400, 280, shadow_color=(0,80,120), offset=4)
        
        # Wait until sync finishes, then load save and go to main menu
        if not cloud_sync.sync_in_progress:
            # Add a slight delay to ensure file writes are flushed
            load_game()
            state = 0

    # ==========================
    # MAIN MENU (STATE 0)
    # ==========================
    elif state == 0:
        settings_from_pause = False
        # Live autonomous combat simulation in selected environment (freezes when navigating away)
        menu_battle_sim.update(dt=dt, current_env=current_selected_env)
        menu_battle_sim.draw(screen, current_env=current_selected_env)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        # ---- Subtle neon edge vignette over the battle bg ----
        draw_neon_vignette(screen, color=(0, 10, 30), alpha_edge=90, steps=5)

        # ---- TITLE BLOCK ----
        # Primary glowing title
        title_glow_a = int(80 + 40 * math.sin(ui_pulse_t * 1.8))
        for goff, ga in [(5, title_glow_a // 4), (3, title_glow_a // 2), (1, title_glow_a)]:
            ts = FONT_TITLE.render("CRAZYY SIMULATION", True, NEON_CYAN)
            ts.set_alpha(ga)
            screen.blit(ts, ts.get_rect(center=(400 + goff, 70)))
        draw_text_shadow("CRAZYY SIMULATION", FONT_TITLE, NEON_CYAN, 400, 70, shadow_color=(0, 60, 100), offset=3)

        # COSMIC CIVIL WAR subtitle — glitch flicker effect
        ccw_alpha = int(180 + 60 * math.sin(ui_pulse_t * 3.1))
        ccw_col = (min(255, ccw_alpha), min(255, int(210 * ccw_alpha / 240)), 50)
        ccw_surf = FONT_MODAL_SUB.render("[ COSMIC CIVIL WAR ]", True, ccw_col)
        # Occasional glitch offset
        glitch_ox = int(random.choice([0, 0, 0, 2, -2]) if random.random() < 0.08 else 0)
        screen.blit(ccw_surf, ccw_surf.get_rect(center=(400 + glitch_ox, 108)))

        # Thin horizontal neon divider beneath title
        div_surf = pygame.Surface((300, 1), pygame.SRCALPHA)
        div_surf.fill((*NEON_CYAN, 80))
        screen.blit(div_surf, (250, 128))

        # ---- COIN BADGE (top center) ----
        coin_panel = pygame.Rect(320, 124, 160, 32)
        pygame.draw.rect(screen, (14, 16, 28), coin_panel, border_radius=16)
        pygame.draw.rect(screen, NEON_GOLD, coin_panel, width=1, border_radius=16)
        screen.blit(coin_icon, (328, 117))
        draw_text(str(total_coins), FONT_UI, NEON_GOLD, 395, 140)

        # ---- TOP RIGHT PROFILE BADGE ----
        profile_name = cloud_sync.current_username or "Guest"
        if len(profile_name) > 12:
            profile_name = profile_name[:10] + ".."
        prof_rect = pygame.Rect(645, 12, 140, 26)
        pygame.draw.rect(screen, (14, 18, 30), prof_rect, border_radius=13)
        pygame.draw.rect(screen, (40, 60, 90), prof_rect, width=1, border_radius=13)
        draw_text(f" {profile_name}", FONT_TINY, NEON_CYAN, prof_rect.centerx, prof_rect.centery)

        # ---- MENU BUTTONS ----
        menu_btns = [
            (">  CAMPAIGN",    NEON_BLUE,      172, 20),
            (">  MULTIPLAYER", MID_GRAY,       234, "locked"),
            (">  STORE",       (140, 40, 200), 296, 6),
            (">   SETTINGS",   NEON_ORANGE,    358, 9),
            ("X  QUIT",        NEON_PINK,      420, 0),
        ]

        # Keyboard navigation for menu
        if key_down or key_tab:
            focused_btn = (focused_btn + 1) % len(menu_btns)
        if key_up:
            focused_btn = (focused_btn - 1) % len(menu_btns)
        if key_escape:
            running = False

        for idx, (txt, col, y, target) in enumerate(menu_btns):
            btn_rect = pygame.Rect(250, y, 300, 50)
            is_hover = btn_rect.collidepoint(mx, my)
            is_focused = (idx == focused_btn)
            if is_hover and target != "locked":
                focused_btn = idx  # Mouse overrides keyboard focus
            
            draw_glowing_button(screen, txt, FONT_UI, WHITE if target != "locked" else LIGHT_GRAY, btn_rect, col, (is_hover or is_focused) and target != "locked",
                                border_radius=14, accent=NEON_CYAN, pulse_t=ui_pulse_t)
            
            if target == "locked":
                # Draw COMING SOON badge
                badge_rect = pygame.Rect(btn_rect.right - 92, btn_rect.y - 8, 96, 22)
                pygame.draw.rect(screen, RED, badge_rect, border_radius=11)
                draw_text("COMING v2.0", FONT_TINY, WHITE, badge_rect.centerx, badge_rect.centery)

            # Keyboard focus indicator
            if is_focused and not is_hover and target != "locked":
                focus_surf = pygame.Surface((btn_rect.width + 8, btn_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(focus_surf, (*NEON_CYAN, 90), focus_surf.get_rect(), border_radius=16, width=2)
                screen.blit(focus_surf, (btn_rect.x - 4, btn_rect.y - 4))

            activated = (m_c and is_hover) or (key_enter and is_focused)
            if activated and target != "locked":
                if txt.endswith("QUIT"):
                    running = False
                elif ("CAMPAIGN" in txt or "STORE" in txt) :
                    tap_snd.play()
                    win_snd_played = False
                    loose_snd_played = False
                    show_settings_warning = True
                    click_cooldown = 12
                    m_c = False
                else:
                    tap_snd.play()
                    if target == 9:
                        settings_from_pause = False
                    state = target
                    click_cooldown = 12
                    m_c = False

        # ---- BOTTOM LEFT: LOGOUT BUTTON (Clean & Small) ----
        btn_quick_logout = pygame.Rect(18, 554, 115, 30)
        is_h_q_logout = btn_quick_logout.collidepoint(mx, my)
        draw_glowing_button(screen, "ESC LOGOUT", FONT_TINY, WHITE, btn_quick_logout, RED, is_h_q_logout, border_radius=10, pulse_t=0)
        
        if m_c and is_h_q_logout:
            tap_snd.play()
            cloud_sync.clear_local_session()
            total_coins = 0
            max_galaxy_level = 1
            max_nebula_level = 1
            max_blackhole_level = 1
            unlocked_hp = 200
            unlocked_speed = 7
            unlocked_bullets = 1
            bullet_step = 0
            current_selected_env = 1
            state = -3
            click_cooldown = 12
            m_c = False

        # ---- BOTTOM RIGHT: REPORT ISSUES BUTTON (Direct to GitHub) ----
        btn_report_issues = pygame.Rect(642, 554, 140, 30)
        is_h_report = btn_report_issues.collidepoint(mx, my)
        draw_glowing_button(screen, "🐛 REPORT ISSUES", FONT_TINY, WHITE, btn_report_issues, NEON_CYAN, is_h_report, border_radius=10, pulse_t=ui_pulse_t)

        if m_c and is_h_report:
            tap_snd.play()
            try:
                webbrowser.open("https://github.com/iambkram/Crazyy-Simulation/issues")
            except Exception as e:
                print("Error opening issues page:", e)
            click_cooldown = 12
            m_c = False

        # ---- BOTTOM CENTER: VERSION TAG ----
        draw_text("v1.0.0  |  @iambkram", FONT_TINY, (60, 90, 130), 400, 569)

                elif is_h_ok:
                    tap_snd.play()
                    control_type = 'PC'
                    show_settings_warning = False
                    click_cooldown = 12
                    m_c = False
    elif state == 6:
        res = render_store(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t, menu_bg,
            coin_icon, total_coins, hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs, store_selection,
            unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate
        )
        state, store_selection, click_cooldown, m_c, key_escape, key_enter = res

    elif state == 7:
        res = render_store_confirm(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, tap_snd, ui_pulse_t, total_coins,
            store_selection, hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs
        )
        state, action_dict, click_cooldown, m_c, key_escape, key_enter = res
        
        if action_dict and action_dict.get('type') == 'buy':
            item = action_dict.get('item', store_selection)
            is_max = False
            if item in (0, 'hp') and hp_step >= len(hp_costs):
                is_max = True
            elif item in (1, 'sp') and speed_step >= len(speed_costs):
                is_max = True
            elif item in (2, 'pb', 'bullets') and bullet_step >= len(bullet_costs):
                is_max = True
            elif item in (3, 'fr', 'firerate', 'overclock') and firerate_step >= len(firerate_costs):
                is_max = True
                
            cost = action_dict.get('cost', 0)
            if not is_max and cost > 0 and total_coins >= cost:
                total_coins -= cost
                tap_snd.play()
                if item in (0, 'hp'):
                    hp_step += 1
                    unlocked_hp += 50
                elif item in (1, 'sp'):
                    speed_step += 1
                    unlocked_speed += 1
                elif item in (2, 'pb', 'bullets'):
                    bullet_step += 1
                    unlocked_bullets += 1
                elif item in (3, 'fr', 'firerate', 'overclock'):
                    firerate_step += 1
                    unlocked_firerate = round(1.0 + firerate_step * 0.15, 2)
                save_game()

    elif state == 8:
        res = render_store_error(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t)
        state, click_cooldown, m_c, key_escape, key_enter = res


    # ==========================
    # SELECT ENVIRONMENT (STATE 20)
    # ==========================
    elif state == 20:
        res = render_env_select(
            screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, tap_snd, ui_pulse_t, menu_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            env2_unlocked, env3_unlocked, current_selected_env, focused_btn
        )
        state, current_selected_env, click_cooldown, m_c, focused_btn = res

    elif state == 9:
        res = render_settings(
            screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
            control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
            screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, 0
        )
        state, control_type, visual_quality, show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, m_c = res
        shoot_snd.set_volume(sfx_vol)
        tap_snd.set_volume(sfx_vol)
        expl_snd.set_volume(sfx_vol)
        hit_snd.set_volume(sfx_vol)
        boss_expl_snd.set_volume(sfx_vol)
        game_won_snd.set_volume(sfx_vol)
        game_loose_snd.set_volume(sfx_vol)
        pygame.mixer.music.set_volume(music_vol)
        vfx_engine.set_quality(visual_quality)
        vfx_engine.set_quality(visual_quality)

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
            ("+  Flight Navigation",  "Use [W A S D] or Arrow Keys for 2D maneuvering & dodging."),
            ("-  Weapons Barrage",    "Hold [SPACEBAR] or Left Mouse Button for rapid auto-fire."),
            ("+  Tactical Powerups",  "Collect glowing [S] Shield & [2X] Dual Laser orbs mid-flight."),
            ("O  Singularity Hazard", "In Black Hole mode, resist gravity with fast thruster bursts!"),
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
        m_down = pygame.mouse.get_pressed()[0]
        btn_ok = pygame.Rect(270, 450, 260, 54)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_glowing_button(screen, "OK  GOT IT!", FONT_UI, WHITE, btn_ok, NEON_GREEN, is_h_ok,
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
            ("^  Touch Navigation",    "Slide your finger anywhere to smoothly glide your starship."),
            ("-  Auto-Firing",         "Cannons fire automatically while your finger is on the screen."),
            ("+  Tactical Powerups",   "Tap glowing [S] Shield & [2X] Double Shot orbs to collect them."),
            ("O  Singularity Hazard",  "Always keep sliding — Black Hole pulls you continuously inward!"),
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
        m_down = pygame.mouse.get_pressed()[0]
        btn_ok = pygame.Rect(270, 450, 260, 54)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_glowing_button(screen, "OK  GOT IT!", FONT_UI, WHITE, btn_ok, NEON_GREEN, is_h_ok,
                            border_radius=16, accent=GREEN, pulse_t=ui_pulse_t)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9
            click_cooldown = 12
            m_c = False

    # ==========================
    # MISSIONS / LEVEL SELECT (STATE 1)
    # ==========================
    elif state == 1:
        state, selected_level, level_scroll_y, is_dragging_missions, mouse_y_prev, m_c, level_drag_dist = render_level_select(
            screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
            current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            level_scroll_y, is_dragging_missions, max_scroll_y, mouse_y_prev, m_wheel, level_drag_dist
        )

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

        box_rect = pygame.Rect(120, 68, 560, 464)
        draw_holographic_panel(screen, box_rect, accent=env_acc2, alpha=250, border_radius=22,
                               bg=PANEL_BG, show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

        draw_text_shadow(f"MISSION  {selected_level}", FONT_MODAL_TITLE, NEON_GOLD, 400, 116, shadow_color=(80, 50, 0), offset=2)
        draw_badge(screen, curr_env_title, FONT_TINY, 400, 150, bg_color=PANEL_MID, text_color=env_acc2, border_color=env_acc2)
        draw_divider(screen, 155, 172, 645, env_acc2, alpha=50)

        boss_kill_reqs = {1: 15, 2: 20, 3: 25, 4: 35, 5: 45, 6: 60, 7: 75, 8: 90, 9: 105, 10: 120}
        req_k = min(200, 120 + (selected_level - 10) * 4) if selected_level >= 11 else boss_kill_reqs.get(selected_level, 25)

        # Objective card
        obj_rect = pygame.Rect(150, 188, 500, 72)
        pygame.draw.rect(screen, PANEL_MID, obj_rect, border_radius=12)
        pygame.draw.rect(screen, env_acc2, obj_rect, width=1, border_radius=12)
        pygame.draw.rect(screen, env_acc2, pygame.Rect(150, 198, 3, 52), border_radius=2)
        draw_text("VS  TACTICAL OBJECTIVE", FONT_SMALL, NEON_GOLD, 400, 210)
        draw_text(f"Eliminate {req_k} hostiles to draw out the Sector Boss", FONT_SMALL, WHITE, 400, 238)

        # Tier / difficulty badge
        tier = (selected_level - 1) // 5 + 1
        diff_labels = {1:"NOVICE", 2:"RECRUIT", 3:"VETERAN", 4:"ELITE", 5:"COMMANDER", 6:"OVERLORD", 7:"LEGEND", 8:"MYTHIC"}
        diff_txt = diff_labels.get(tier, "MYTHIC")
        diff_col = [NEON_GREEN, NEON_BLUE, NEON_CYAN, NEON_ORANGE, NEON_PINK, RED, NEON_PURPLE, NEON_GOLD][min(tier-1, 7)]
        draw_badge(screen, f"THREAT LEVEL: {diff_txt}", FONT_TINY, 400, 292, bg_color=PANEL_MID, text_color=diff_col, border_color=diff_col)

        # Dynamic enemy type roster preview
        preview_y = 338
        draw_text("INTEL: DETECTED ENEMY ROSTER", FONT_TINY, LIGHT_GRAY, 400, preview_y - 14)
        enemy_info = [
            (fighter_img, "Fighter",  NEON_CYAN),
            (elite_img,   "Elite",    NEON_PURPLE),
            (heavy_img,   "Heavy",    NEON_ORANGE),
        ]
        if selected_level >= 31:
            enemy_info.append((fighter_img, "Phantom", NEON_VIOLET))
        if selected_level >= 35:
            enemy_info.append((heavy_img, "Berserker", NEON_SCARLET))
        if selected_level >= 38:
            enemy_info.append((heavy_img, "Commander", NEON_GOLD))

        num_roster = len(enemy_info)
        spacing_r = min(80, 480 // max(1, num_roster))
        start_rx = 400 - ((num_roster - 1) * spacing_r) // 2
        for r_idx, (eimg, ename, ecol) in enumerate(enemy_info):
            rx = start_rx + r_idx * spacing_r
            esc = pygame.transform.scale(eimg, (32, 32))
            screen.blit(esc, (rx - 16, preview_y))
            draw_text(ename, FONT_TINY, ecol, rx, preview_y + 44)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]
        b_r = pygame.Rect(145, 442, 230, 56)
        b_a = pygame.Rect(425, 442, 230, 56)
        is_h_r = b_r.collidepoint(mx, my)
        is_h_a = b_a.collidepoint(mx, my)

        # Launch & Back buttons with plasma styling
        draw_plasma_button(screen, ">>>  LAUNCH", FONT_UI, WHITE, b_r, (0, 150, 60), is_h_r,
                           border_radius=16, accent=NEON_GREEN, pulse_t=ui_pulse_t)
        draw_plasma_button(screen, "< BACK", FONT_UI, WHITE, b_a, (140, 20, 50), is_h_a,
                           border_radius=16, accent=NEON_PINK, pulse_t=ui_pulse_t)

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
        m_down = pygame.mouse.get_pressed()[0]
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        pause_btn_rect = pygame.Rect(WIDTH - 55, 15, 40, 40)
        fire_btn_rect = touch_hud.fire_rect() if control_type == 'MOBILE' else pygame.Rect(0, 0, 0, 0)
        is_h_pause = pause_btn_rect.collidepoint(mx, my)
        is_h_fire = fire_btn_rect.collidepoint(mx, my) if control_type == 'MOBILE' else False

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

            draw_text_shadow("! GRAVITATIONAL HAZARD", FONT_MODAL_TITLE, NEON_PINK, 400, 115, shadow_color=(80,0,0), offset=2)
            draw_text("BLACK HOLE SINGULARITY DETECTED", FONT_TINY, NEON_CYAN, 400, 150)
            draw_divider(screen, 130, 168, 670, NEON_PINK, alpha=50)

            warnings = [
                ("O Massive Singularity", "Extreme gravity pulls all ships and matter to the center!"),
                ("⏳ Relativistic Time",    "All ship navigation, lasers, and combat speeds are slowed down."),
                ("💥 Event Horizon",        "Falling into the center will crush your starship!"),
                (">>> Active Defense",       "Use continuous sliding / WASD reflexes to resist gravity.")
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
            draw_glowing_button(screen, ">>> ENGAGE THRUSTERS", FONT_UI, WHITE, btn_engage, NEON_PINK, is_h_eng, accent=RED, pulse_t=ui_pulse_t)

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
        is_nebula    = (current_selected_env == 2)
        is_galaxy    = (current_selected_env == 1)
        env_speed_mult = 0.68 if is_blackhole else 1.0
        eff_player_speed = max(3.0, unlocked_speed * env_speed_mult)

        # Calculate mouse delta for mobile relative control
        if 'prev_mx' not in globals():
            global prev_mx, prev_my
            prev_mx, prev_my = mx, my
        mouse_dx = mx - prev_mx
        mouse_dy = my - prev_my
        prev_mx, prev_my = mx, my

        # Determine dynamic flight boundary (unrestricted during waves, restricted during boss encounter)
        current_player_min_y = PLAYER_BOSS_MIN_Y if (boss_active or boss_arriving) else PLAYER_MIN_Y_NORMAL

        # --- SMART CONTROLS LOGIC ---
        if fire_cooldown > 0:
            fire_cooldown -= 1

        is_firing = False

        if control_type == 'PC':
            if pc_controls.is_move_left(keys) and player_rect.left > PLAYER_MIN_X:
                player_rect.x -= eff_player_speed
            if pc_controls.is_move_right(keys) and player_rect.right < PLAYER_MAX_X:
                player_rect.x += eff_player_speed
            if pc_controls.is_move_up(keys) and player_rect.top > current_player_min_y:
                player_rect.y -= eff_player_speed
            if pc_controls.is_move_down(keys) and player_rect.bottom < PLAYER_MAX_Y:
                player_rect.y += eff_player_speed

            # Base cooldown governed purely by Store Overclock upgrade (no free level 15 boost)
            player_base_cd = max(6, 11 - firerate_step + (1 if is_blackhole else 0))
            if pc_controls.is_firing(keys, mouse_pressed, auto_fire_enabled, is_h_pause) and fire_cooldown <= 0:
                is_firing = True
                fire_cooldown = player_base_cd

        elif control_type == 'MOBILE':
            dragging_playfield = mouse_pressed and not is_h_pause and not is_h_fire
            if dragging_playfield and not m_c:
                # True 1:1 finger drag (logical pixels), not speed-clamped steering.
                player_rect.x += int(mouse_dx)
                player_rect.y += int(mouse_dy)

            player_base_cd = max(5, 10 - firerate_step + (1 if is_blackhole else 0))
            if ((is_h_fire and mouse_pressed) or dragging_playfield or auto_fire_enabled) and fire_cooldown <= 0:
                is_firing = True
                fire_cooldown = player_base_cd

        # Keep player ship strictly within active flight zone
        player_rect.left = max(PLAYER_MIN_X, player_rect.left)
        player_rect.right = min(PLAYER_MAX_X, player_rect.right)
        player_rect.top = max(current_player_min_y, player_rect.top)
        player_rect.bottom = min(PLAYER_MAX_Y, player_rect.bottom)

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
            player_fire_anim = 5

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

        # ----------------------------------------------------
        # IMMERSIVE ENVIRONMENT OVERLAYS (drawn after bg + stars)
        # ----------------------------------------------------
        if visual_quality != 'low':
            if is_nebula:
                draw_nebula_overlay(screen, ui_pulse_t)
            elif is_blackhole:
                draw_blackhole_overlay(screen, ui_pulse_t, bh_cx=BH_X, bh_cy=BH_Y)

        # Draw Player Flight Zone Defense Boundary Line (Only active when boss is arriving or in combat)
        if boss_arriving or boss_active:
            boundary_alpha = int(100 + 40 * math.sin(ui_pulse_t * 3.0))
            is_boss_fight = boss_active and boss_death_timer == 0
            barrier_color = NEON_CYAN if is_boss_fight else RED
            draw_divider(screen, 20, PLAYER_BOSS_MIN_Y, WIDTH - 20, barrier_color, alpha=boundary_alpha)
            
            # Subtle barrier shield glow strip
            barrier_surf = pygame.Surface((WIDTH - 40, 4), pygame.SRCALPHA)
            barrier_surf.fill((*barrier_color, min(140, boundary_alpha)))
            screen.blit(barrier_surf, (20, PLAYER_BOSS_MIN_Y - 2))

        # Asteroids Update & Collision
        asteroid_group.update()
        asteroid_group.draw(screen)

        for ast in list(asteroid_group):
            if ast.rect.colliderect(player_rect):
                if not skills['immortal']['active'] and revive_protection_timer <= 0:
                    player_health -= 30
                    player_dmg_anim = 15
                    global_shake_intensity = 8.0
                    hit_snd.play()
                ast.kill()
                for _ in range(12):
                    particles.append([ast.rect.centerx, ast.rect.centery, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 7), (120, 120, 130)])

        current_tick = pygame.time.get_ticks()
        max_asteroids_in_match = 12 if current_level <= 30 else 7
        if not boss_active and not boss_arriving and boss_defeated_timer == 0 and asteroids_spawned < max_asteroids_in_match:
            if current_tick - last_spawn_tick > next_spawn_time:
                new_asteroid = Asteroid(asteroid_img, env=current_selected_env)
                asteroid_group.add(new_asteroid)
                asteroids_spawned += 1
                last_spawn_tick = current_tick
                next_spawn_time = random.randint(7000, 14000)

        all_enemies_objs = fighters + elites + heavies + phantoms + berserkers + commanders

        # --- UNIFIED DIFFICULTY SCALING via settings.get_difficulty() ---
        # Accounts for environment-aware progression: Nebula L1 > Galaxy L10, Blackhole L1 > Nebula L10
        _sc, _fc, _sm_override, _boss_agr = get_difficulty(current_level)
        _env_mult_bonus = {1: 1.0, 2: 1.5, 3: 2.2}.get(current_selected_env, 1.0)
        spawn_chance = max(8, int(_sc / _env_mult_bonus))
        fire_chance  = max(18, int(_fc / _env_mult_bonus))

        _max_f, _max_e, _max_h, enable_phantom, enable_berserker, enable_commander = get_enemy_caps(current_level)
        # Scale caps by environment too
        _env_cap_bonus = {1: 1, 2: 2, 3: 3}.get(current_selected_env, 0)
        max_fighters = _max_f + _env_cap_bonus
        max_elites   = _max_e + _env_cap_bonus
        max_heavies  = _max_h + _env_cap_bonus
        max_phantoms   = (2 + current_level // 10) if enable_phantom else 0
        max_berserkers = (1 + (current_level - 35) // 3) if enable_berserker else 0
        max_commanders = (1 if enable_commander else 0)

        # --- SPAWN EXECUTION ---
        if not boss_active and not boss_arriving and boss_defeated_timer == 0:
            if len(fighters) < max_fighters and random.randint(1, spawn_chance) == 1:
                nr = fighter_img.get_rect(center=(random.randint(50, WIDTH - 50), -50))
                if check_enemy_spawn(nr, all_enemies_objs):
                    fighters.append({'rect': nr, 'hp': 1, 'max_hp': 1, 'start_x': float(nr.x),
                                     'time': random.randint(0, 50), 'type': 'fighter',
                                     'dive_speed': random.uniform(2.5, 4.5),
                                     'ai_state': 'descend', 'ai_timer': 0,
                                     'target_x': float(nr.x), 'dodge_dir': random.choice([-1, 1])})

            if current_level >= 2 and len(elites) < max_elites and random.randint(1, int(spawn_chance * 1.3)) == 1:
                nr = elite_img.get_rect(center=(random.randint(50, WIDTH - 50), -50))
                if check_enemy_spawn(nr, all_enemies_objs):
                    e_hp = max(2, min(current_level // 3 + 1, 6))
                    elites.append({'rect': nr, 'hp': e_hp, 'max_hp': e_hp, 'start_x': float(nr.x),
                                   'time': random.randint(0, 50), 'type': 'elite',
                                   'ai_state': 'strafe', 'ai_timer': 0,
                                   'target_x': float(nr.x), 'dodge_dir': random.choice([-1, 1])})

            if current_level >= 5 and len(heavies) < max_heavies and random.randint(1, int(spawn_chance * 2.2)) == 1:
                nr = heavy_img.get_rect(center=(random.randint(60, WIDTH - 60), -60))
                if check_enemy_spawn(nr, all_enemies_objs):
                    h_hp = max(5, min(current_level // 2, 16))
                    heavies.append({'rect': nr, 'hp': h_hp, 'max_hp': h_hp, 'start_x': float(nr.x),
                                    'time': 0, 'type': 'heavy', 'ai_state': 'advance',
                                    'ai_timer': 0, 'target_x': float(nr.x), 'dodge_dir': 1,
                                    'sub_timer': 0})

            # Phantom spawning (Level 31+)
            if enable_phantom and len(phantoms) < max_phantoms and random.randint(1, int(spawn_chance * 1.8)) == 1:
                nr = fighter_img.get_rect(center=(random.randint(50, WIDTH - 50), -50))
                if check_enemy_spawn(nr, all_enemies_objs):
                    p_hp = max(3, min(current_level // 4, 8))
                    phantoms.append({'rect': nr, 'hp': p_hp, 'max_hp': p_hp, 'start_x': float(nr.x),
                                     'time': 0, 'type': 'phantom', 'ai_state': 'descend',
                                     'ai_timer': 0, 'target_x': float(nr.x), 'dodge_dir': 1,
                                     'is_cloaked': False, 'cloak_timer': 0})

            # Berserker spawning (Level 35+)
            if enable_berserker and len(berserkers) < max_berserkers and random.randint(1, int(spawn_chance * 3)) == 1:
                nr = heavy_img.get_rect(center=(random.randint(60, WIDTH - 60), -70))
                if check_enemy_spawn(nr, all_enemies_objs):
                    b_hp = max(10, min(current_level // 2 + 5, 22))
                    berserkers.append({'rect': nr, 'hp': b_hp, 'max_hp': b_hp, 'start_x': float(nr.x),
                                       'time': 0, 'type': 'berserker', 'ai_state': 'charge',
                                       'ai_timer': 0, 'target_x': float(nr.x), 'dodge_dir': 1})

            # Commander spawning (Level 38+)
            if enable_commander and len(commanders) < max_commanders and random.randint(1, int(spawn_chance * 5)) == 1:
                nr = heavy_img.get_rect(center=(random.randint(100, WIDTH - 100), -80))
                if check_enemy_spawn(nr, all_enemies_objs):
                    c_hp = max(15, min(current_level // 2 + 10, 30))
                    commanders.append({'rect': nr, 'hp': c_hp, 'max_hp': c_hp, 'start_x': float(nr.x),
                                       'time': 0, 'type': 'commander', 'ai_state': 'orbit',
                                       'ai_timer': 0, 'target_x': float(nr.x), 'dodge_dir': 1,
                                       'bodyguard_spawned': False})

        # --- ENEMY AI: All types use run_enemy_ai() from ai.enemy_ai ---
        ai_aggression = min(1.0, current_level / 16.0)
        ai_accuracy   = min(1.0, current_level / 24.0)

        _coin_vals = {'fighter': 2, 'elite': 4, 'heavy': 8,
                      'phantom': 10, 'berserker': 15, 'commander': 20}

        all_active_lists = [
            (fighters,   fighter_img,  'fighter',   1),
            (elites,     elite_img,    'elite',     2),
            (heavies,    heavy_img,    'heavy',     5),
            (phantoms,   fighter_img,  'phantom',   4),
            (berserkers, heavy_img,    'berserker', 8),
            (commanders, heavy_img,    'commander', 10),
        ]

        for e_list, e_img, e_type, coin_val in all_active_lists:
            for e in e_list[:]:
                # Run AI (returns new bullets to spawn)
                new_bullets = run_enemy_ai(e, bullets, player_rect, current_level,
                                          env_speed_mult, ai_aggression, ai_accuracy,
                                          BH_X, BH_Y, is_blackhole)
                for nb in new_bullets:
                    enemy_bullets.append(nb)

                # Legacy fire logic for basic enemies (fighter/elite/heavy)
                # using fire_chance — ensures compatibility with existing tuning
                if e_type in ('fighter', 'elite', 'heavy') and random.randint(1, int(fire_chance)) == 1:
                    dmg = max(1, min(current_level // 4 + 1, 5))
                    if e_type == 'fighter':
                        bx = (player_rect.centerx - 3 if ai_accuracy > 0.5 and random.random() < ai_accuracy
                              else e['rect'].centerx - 3)
                        enemy_bullets.append({'rect': pygame.Rect(bx, e['rect'].bottom, 6, 14),
                                              'damage': dmg, 'color': RED, 'vx': 0, 'vy': 1.0, 'btype': 'fighter'})
                    elif e_type == 'elite':
                        for ex_off in [-5, 5]:
                            enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx + ex_off, e['rect'].bottom, 6, 14),
                                                  'damage': dmg, 'color': MAGENTA, 'vx': ex_off * 0.06, 'vy': 1.0, 'btype': 'elite'})
                    elif e_type == 'heavy':
                        for angle_d in [-20, 0, 20]:
                            rad = math.radians(angle_d + 90)
                            enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].bottom, 10, 16),
                                                  'damage': dmg + 4, 'color': ORANGE,
                                                  'vx': math.cos(rad) * 3.5,
                                                  'vy': math.sin(rad) * 3.5, 'btype': 'heavy'})

                # Emit thrusters
                vfx_engine.emit_enemy_thruster(e['rect'].centerx, e['rect'].top, e_type, e['rect'].width)

                # Enemy collision with player
                if e['rect'].colliderect(player_rect):
                    player_rect.y = min(PLAYER_MAX_Y, player_rect.y + 10)
                    if e in e_list:
                        e_list.remove(e)
                    if not skills['immortal']['active'] and revive_protection_timer <= 0:
                        dmg_contact = {'fighter': 15, 'elite': 25, 'heavy': 40,
                                       'phantom': 20, 'berserker': 50, 'commander': 30}.get(e_type, 15)
                        player_health -= dmg_contact
                        player_dmg_anim = 15
                        global_shake_intensity = 8.0
                        hit_snd.play()
                    # 5-stage explosion on contact
                    vfx_engine.spawn_explosion(e['rect'].centerx, e['rect'].centery, size='medium', enemy_type=e_type)
                    for _ in range(12):
                        particles.append([e['rect'].centerx, e['rect'].centery,
                                         random.uniform(-4, 4), random.uniform(-4, 4),
                                         random.randint(3, 6), random.choice(BLAST_COLORS)])
                elif e['rect'].top > HEIGHT:
                    if e in e_list:
                        e_list.remove(e)

        # Update and draw all explosion particles + ripples
        vfx_engine.update_and_draw_explosions(screen)
        vfx_engine.update_and_draw_ripples(screen)
        vfx_engine.update_and_draw_arcs(screen)

        # Ambient environment particles
        if visual_quality == 'high':
            vfx_engine.update_and_draw_ambient(screen, env=current_selected_env)

        # Emit player ship engine thrusters
        vfx_engine.emit_player_thruster(player_rect.centerx, player_rect.bottom)

        # Enemy-Enemy Anti-Merge Collision
        all_e = fighters + elites + heavies + phantoms + berserkers + commanders
        for i, e1 in enumerate(all_e):
            for j, e2 in enumerate(all_e):
                if i < j and e1['rect'].colliderect(e2['rect']):
                    dx = e1['rect'].centerx - e2['rect'].centerx
                    dy = e1['rect'].centery - e2['rect'].centery
                    if dx == 0 and dy == 0:
                        dx = 1
                    if abs(dx) > abs(dy):
                        shift = 2 if dx > 0 else -2
                        e1['rect'].x += shift
                        e2['rect'].x -= shift
                    else:
                        shift = 2 if dy > 0 else -2
                        e1['rect'].y += shift
                        e2['rect'].y -= shift

        # =========================================================
        # BOSS AI BRAIN — Scripted State Machine (GTA-style)
        # =========================================================
        # The boss has a BRAIN that reads the battlefield and picks
        # attack strategies. No static safe zone exists.
        # Phases trigger automatically based on remaining HP %.
        # =========================================================
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
                boss_ai_timer += 1

                # ── PHASE TRANSITIONS based on HP ───────────────────────────
                hp_pct = boss_hp / boss_max_hp
                new_phase = 1 if hp_pct > 0.5 else (2 if hp_pct > 0.25 else 3)
                if new_phase > boss_ai_phase:
                    boss_ai_phase = new_phase
                    boss_ai_state = 'rage'    # Always enter rage state on phase change
                    boss_ai_timer = 0

                # ── TIERED SPEED & ABILITY UNLOCKS BY LEVEL ─────────────────
                if current_level <= 10:
                    # Levels 1-10: Easy tier, gentle movement, basic animations
                    b_spd = 1.4 * env_speed_mult
                elif current_level <= 30:
                    # Levels 11-30: Moderate-hard tier, active sweeps and corner attacks
                    b_spd = (2.0 + (boss_ai_phase - 1) * 0.8) * env_speed_mult
                else:
                    # Levels 31-40: Hard tier, high speed, full bullet-hell abilities
                    b_spd = (2.8 + (boss_ai_phase - 1) * 1.2) * env_speed_mult

                # ── ENTRY: slide boss into cruising altitude ─────────────────
                if boss_rect.top < 65:
                    boss_rect.y += 2

                # ── CORNER HUNT: Check if player is hugging an edge (Lvl 11+)
                player_at_edge = (player_rect.left < 60 or player_rect.right > WIDTH - 60)
                if current_level >= 11 and player_at_edge and boss_ai_state == 'patrol' and boss_ai_timer % 120 == 0:
                    boss_ai_state = 'corner_hunt'
                    boss_ai_timer = 0

                # ─────────────────────────────────────────────────────────────
                # STATE: patrol — Smooth horizontal drift tracking player
                # ─────────────────────────────────────────────────────────────
                if boss_ai_state == 'patrol':
                    dx = player_rect.centerx - boss_rect.centerx
                    boss_rect.x += int(dx * 0.02 * b_spd)
                    
                    # Altitude stabilization at cruising height
                    if boss_rect.top < 65: boss_rect.y += 1
                    elif boss_rect.top > 80: boss_rect.y -= 1
                    
                    # Idle animation based on level
                    if current_level <= 10:
                        boss_angle = math.sin(boss_ai_timer * 0.04) * 3
                    elif current_level <= 30:
                        boss_angle = math.sin(boss_ai_timer * 0.08) * 8
                    else:
                        boss_angle = math.sin(boss_ai_timer * 0.12) * 14

                    if boss_ai_timer > 200:
                        # State rotation strictly tiered by level progression
                        if current_level <= 10:
                            # Only Patrol & Chase for Levels 1-10
                            boss_ai_state = 'chase'
                        elif current_level <= 30:
                            # Add Sweep and Corner Hunt for Levels 11-30
                            roll = random.random()
                            if roll < 0.45:    boss_ai_state = 'sweep'
                            elif roll < 0.75:  boss_ai_state = 'chase'
                            else:              boss_ai_state = 'corner_hunt'
                        else:
                            # All states unlocked for Levels 31-40 (Dive, Spiral, Rage)
                            roll = random.random()
                            if roll < 0.25:    boss_ai_state = 'sweep'
                            elif roll < 0.45:  boss_ai_state = 'chase'
                            elif roll < 0.65:  boss_ai_state = 'dive'
                            elif roll < 0.85:  boss_ai_state = 'spiral'
                            else:              boss_ai_state = 'corner_hunt'

                        boss_ai_timer = 0
                        boss_sweep_dir = random.choice([-1, 1])

                # ─────────────────────────────────────────────────────────────
                # STATE: chase — Horizontal pursuit in the upper sector
                # (Strictly capped in Y so it never descends near the player)
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'chase':
                    dx = player_rect.centerx - boss_rect.centerx
                    boss_rect.x += int(dx * 0.04 * b_spd)
                    
                    # Small altitude oscillation in the upper sector (65 to 110)
                    target_chase_y = 75 + int(math.sin(boss_ai_timer * 0.06) * 15)
                    if boss_rect.y < target_chase_y: boss_rect.y += 1
                    elif boss_rect.y > target_chase_y: boss_rect.y -= 1
                    boss_angle += 2.0 * boss_sweep_dir

                    if boss_ai_timer > 150:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0

                # ─────────────────────────────────────────────────────────────
                # STATE: sweep — Full-width screen sweep, fires a curtain of bullets
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'sweep':
                    boss_rect.x += int(b_spd * 1.8 * boss_sweep_dir)
                    boss_angle += 3.0 * boss_sweep_dir   # Visual tilt during sweep
                    
                    # Maintain upper altitude
                    if boss_rect.top < 65: boss_rect.y += 1
                    elif boss_rect.top > 80: boss_rect.y -= 1

                    # Reverse at edges — full screen coverage
                    if boss_rect.right >= WIDTH:
                        boss_rect.right = WIDTH
                        boss_sweep_dir = -1
                    if boss_rect.left <= 0:
                        boss_rect.left = 0
                        boss_sweep_dir = 1

                    # Bank into the turn
                    boss_angle = -15.0 * boss_sweep_dir

                    # Fire curtain every 14 frames during sweep
                    if boss_ai_timer % 14 == 0:
                        boss_eff_damage = min(current_level, 4)
                        dmg = 5 * boss_eff_damage
                        for bx_off in [-30, -10, 10, 30]:
                            bx = boss_rect.centerx + bx_off
                            enemy_bullets.append({'rect': pygame.Rect(bx - 4, boss_rect.bottom, 8, 16),
                                                  'damage': dmg, 'color': RED, 'vx': bx_off * 0.06, 'vy': 1.0})

                    if boss_ai_timer > 240:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: corner_hunt — Boss tracks player horizontally at range
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'corner_hunt':
                    target_x = player_rect.centerx
                    dx = target_x - boss_rect.centerx
                    boss_rect.x += int(dx * 0.06 * b_spd)
                    boss_angle = math.sin(boss_ai_timer * 0.15) * 12
                    
                    if boss_rect.top < 65: boss_rect.y += 1
                    elif boss_rect.top > 80: boss_rect.y -= 1

                    # Fire angled volley aimed at the player's position
                    if boss_ai_timer % 20 == 0:
                        boss_eff_damage = min(current_level, 4)
                        dmg = 6 * boss_eff_damage
                        bx = boss_rect.centerx
                        by = boss_rect.bottom
                        aim_dx = player_rect.centerx - bx
                        aim_dy = player_rect.centery - by
                        aim_dist = max(1, math.hypot(aim_dx, aim_dy))
                        norm_x = aim_dx / aim_dist
                        norm_y = aim_dy / aim_dist
                        enemy_bullets.append({
                            'rect': pygame.Rect(bx - 5, by, 10, 20),
                            'damage': dmg, 'color': (255, 80, 0),
                            'vx': norm_x * 4.5, 'vy': norm_y * 4.5
                        })

                    if boss_ai_timer > 200:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: dive — Controlled dive that stays far above player zone
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'dive':
                    # Strictly cap the dive point in Y so boss_rect.bottom never exceeds 260
                    max_dive_y = max(60, 260 - boss_rect.height)
                    if boss_ai_timer == 1:
                        boss_dive_target = (player_rect.centerx, max_dive_y)

                    tdx = boss_dive_target[0] - boss_rect.centerx
                    tdy = boss_dive_target[1] - boss_rect.centery
                    tdist = max(1, math.hypot(tdx, tdy))
                    dive_spd = b_spd * 2.0
                    boss_rect.x += int((tdx / tdist) * dive_spd)
                    boss_rect.y += int((tdy / tdist) * dive_spd)
                    boss_angle = math.sin(boss_ai_timer * 0.2) * 16

                    if boss_ai_timer > 80:
                        # Fire burst on reaching target area
                        boss_eff_damage = min(current_level, 4)
                        dmg = 7 * boss_eff_damage
                        for angle_deg in range(0, 360, 45):
                            rad = math.radians(angle_deg)
                            enemy_bullets.append({
                                'rect': pygame.Rect(boss_rect.centerx - 5, boss_rect.centery, 10, 10),
                                'damage': dmg, 'color': (255, 50, 200),
                                'vx': math.cos(rad) * 3.8, 'vy': math.sin(rad) * 3.8
                            })
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: spiral — Boss fires spiral bullet pattern from upper sector
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'spiral':
                    dx = (WIDTH // 2) - boss_rect.centerx
                    boss_rect.x += int(dx * 0.04)
                    boss_angle = math.sin(boss_ai_timer * 0.1) * 12
                    
                    if boss_rect.top < 65: boss_rect.y += 1
                    elif boss_rect.top > 80: boss_rect.y -= 1

                    if boss_ai_timer % 7 == 0:
                        boss_spiral_t += 0.45
                        boss_eff_damage = min(current_level, 4)
                        dmg = 4 * boss_eff_damage
                        for arm in range(3):    # 3-arm spiral
                            arm_angle = boss_spiral_t + (arm * 2.094)
                            sx = math.cos(arm_angle) * 4.5
                            sy = math.sin(arm_angle) * 4.5
                            enemy_bullets.append({
                                'rect': pygame.Rect(boss_rect.centerx - 4, boss_rect.centery, 8, 8),
                                'damage': dmg, 'color': (100, 200, 255),
                                'vx': sx, 'vy': abs(sy) + 1.0
                            })

                    if boss_ai_timer > 200:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: rage — Short burst state on phase transition
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'rage':
                    boss_rect.x += int(math.sin(boss_ai_timer * 0.5) * b_spd * 3)
                    boss_angle = math.sin(boss_ai_timer * 0.8) * 16
                    
                    if boss_rect.top < 65: boss_rect.y += 1
                    elif boss_rect.top > 80: boss_rect.y -= 1

                    # Fire a dense burst during rage
                    if boss_ai_timer % 12 == 0:
                        boss_eff_damage = min(current_level, 4)
                        dmg = 5 * boss_eff_damage
                        for bx_off in range(-40, 50, 20):
                            enemy_bullets.append({'rect': pygame.Rect(boss_rect.centerx + bx_off - 4, boss_rect.bottom, 8, 16),
                                                  'damage': dmg, 'color': (255, 100, 0), 'vx': 0, 'vy': 1.0})

                    if boss_ai_timer > 100:
                        boss_ai_state = 'sweep'
                        boss_ai_timer = 0

                # ── GLOBAL BOSS BOUNDARY LIMIT (Strict Y-Distance from Player) ──
                # Guarantees boss_rect.bottom NEVER crosses y=270, leaving 110+ px before player boundary (y=380)
                BOSS_MAX_BOTTOM_Y = 270
                max_boss_top = max(50, BOSS_MAX_BOTTOM_Y - boss_rect.height)
                boss_rect.y = max(50, min(max_boss_top, boss_rect.y))
                boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))

                # ── STANDARD SHOOT for patrol/chase (non-sweep states) ───────
                if boss_ai_state in ('patrol', 'chase', 'corner_hunt'):
                    # Shoot frequency & bullet count scaled smoothly by level tier
                    if current_level <= 10:
                        shoot_interval = 50
                        shots = 1
                        dmg = 8
                    elif current_level <= 20:
                        shoot_interval = 40
                        shots = 2 if boss_ai_phase > 1 else 1
                        dmg = 10
                    elif current_level <= 30:
                        shoot_interval = 32
                        shots = 2
                        dmg = 14
                    else:
                        shoot_interval = 24
                        shots = min(3 + (boss_ai_phase - 1), 4)
                        dmg = 18

                    if boss_ai_timer % shoot_interval == 0:
                        for s_i in range(shots):
                            ox = (s_i - (shots - 1) / 2.0) * 26
                            enemy_bullets.append({
                                'rect': pygame.Rect(int(boss_rect.centerx - 5 + ox), boss_rect.bottom, 10, 18),
                                'damage': dmg, 'color': RED, 'vx': 0, 'vy': 1.0
                            })


        # --- DRAWING & COLLISIONS ---
        # Boss vs Player Solid Boundary: player cannot enter or merge into the boss ship
        if boss_active and boss_death_timer == 0:
            if player_rect.colliderect(boss_rect):
                dx = player_rect.centerx - boss_rect.centerx
                dy = player_rect.centery - boss_rect.centery
                if abs(dx) > abs(dy):
                    if dx > 0: player_rect.left = boss_rect.right + 4
                    else: player_rect.right = boss_rect.left - 4
                else:
                    if dy > 0: player_rect.top = boss_rect.bottom + 4
                    else: player_rect.bottom = boss_rect.top - 4
                
                player_rect.top = max(PLAYER_BOSS_MIN_Y, player_rect.top)
                player_rect.bottom = min(PLAYER_MAX_Y, player_rect.bottom)
                player_rect.left = max(PLAYER_MIN_X, player_rect.left)
                player_rect.right = min(PLAYER_MAX_X, player_rect.right)

                if not skills['immortal']['active'] and revive_protection_timer <= 0 and player_dmg_anim <= 0:
                    player_health -= 15
                    player_dmg_anim = 30  # Give half a second of collision invulnerability
                    global_shake_intensity = 10.0
                    hit_snd.play()

                for _ in range(12):
                    particles.append([
                        player_rect.centerx + random.uniform(-15, 15),
                        player_rect.top,
                        random.uniform(-4, 4),
                        random.uniform(-3, 3),
                        random.randint(3, 6),
                        random.choice([(255, 180, 0), (255, 80, 20), (0, 255, 255)])
                    ])

        # Render all ship thrusters beneath hull sprites
        vfx_engine.update_and_draw_thrusters(screen)

        # Enemy Bullets — support both simple (y-only) and vectorized (vx,vy) bullets
        eb_speed = max(4, int(6 * env_speed_mult))
        for eb in enemy_bullets[:]:
            vx = eb.get('vx', 0)
            vy = eb.get('vy', 1.0)
            # Vectorized bullets use their own velocity; simple ones use eb_speed
            if vx != 0 or vy != 1.0:
                eb['rect'].x += int(vx * eb_speed * 0.7)
                eb['rect'].y += int(vy * eb_speed * 0.7)
            else:
                eb['rect'].y += eb_speed
            b_col = eb.get('color', RED)
            b_type = eb.get('btype', 'fighter')

            # Emit trail particles for enemy bullets (high quality only)
            if visual_quality == 'high':
                vfx_engine.emit_bullet_trail(eb['rect'].centerx, eb['rect'].centery,
                                             color=b_col, is_enemy=True)

            # Stylized bullet rendering
            if b_type == 'boss' or eb['rect'].width >= 10:
                draw_boss_bullet(screen, eb['rect'], color=b_col, pulse_t=ui_pulse_t)
            else:
                angle_deg = math.degrees(math.atan2(-vy, vx)) - 90
                draw_enemy_bullet(screen, eb['rect'], color=b_col, bullet_type=b_type, pulse_t=ui_pulse_t, angle=angle_deg)

            if eb['rect'].colliderect(player_rect):
                if not skills['immortal']['active'] and revive_protection_timer <= 0:
                    player_health -= eb['damage']
                    player_dmg_anim = 15
                    global_shake_intensity = 8.0  # Screen shake when player is hit
                    hit_snd.play()
                if eb in enemy_bullets:
                    enemy_bullets.remove(eb)
            elif (eb['rect'].top > HEIGHT or eb['rect'].bottom < 0 or
                  eb['rect'].left > WIDTH or eb['rect'].right < 0):
                if eb in enemy_bullets:
                    enemy_bullets.remove(eb)

        # Player Bullets
        pb_speed = int(14 * env_speed_mult)
        for b in bullets[:]:
            b['rect'].y -= max(8, pb_speed)
            hit = False

            if b in bullets:
                for eb in enemy_bullets[:]:
                    if b['rect'].colliderect(eb['rect']):
                        if b in bullets:
                            bullets.remove(b)
                        if eb in enemy_bullets:
                            enemy_bullets.remove(eb)
                        if visual_quality == 'high':
                            for _ in range(5):
                                particles.append([b['rect'].centerx, b['rect'].centery, random.uniform(-3, 3), random.uniform(-3, 3), random.randint(3, 6), ORANGE])
                        break

            if boss_active and boss_death_timer == 0 and b in bullets:
                if b['rect'].colliderect(boss_rect):
                    boss_hp -= 5
                    if show_damage_enabled:
                        damage_numbers.append({'x': b['rect'].centerx, 'y': b['rect'].top, 'val': 5, 'life': 30, 'col': NEON_GREEN})
                    hit_snd.play()
                    if b in bullets:
                        bullets.remove(b)
                    if boss_hp <= 0:
                        boss_death_timer = 180
                        global_shake_intensity = 15.0  # Massive screen shake for boss defeat
                        vfx_engine.reset_boss_effects()
                        update_coins(100 + current_level * 50)
                    hit = True

            if not hit:
                for e_list, c_val, e_type in [
                    (fighters, 1, 'fighter'),
                    (elites, 2, 'elite'),
                    (heavies, 5, 'heavy'),
                    (phantoms, 4, 'phantom'),
                    (berserkers, 8, 'berserker'),
                    (commanders, 10, 'commander'),
                ]:
                    for e in e_list[:]:
                        # Phantoms are invulnerable while cloaked (ambush predator mechanic)
                        if e_type == 'phantom' and e.get('is_cloaked', False):
                            continue

                        if b['rect'].colliderect(e['rect']):
                            e['hp'] -= 1
                            if show_damage_enabled:
                                damage_numbers.append({'x': b['rect'].centerx, 'y': b['rect'].top, 'val': 1, 'life': 20, 'col': WHITE})
                            if b in bullets:
                                bullets.remove(b)

                            if e['hp'] <= 0:
                                if e in e_list:
                                    e_list.remove(e)
                                update_coins(2 if c_val == 1 else 4 if c_val == 2 else 8 if c_val == 5 else 12)
                                kill_count += 1
                                if spawn_director:
                                    spawn_director.record_kill()
                                expl_snd.play()
                                if c_val >= 5:
                                    global_shake_intensity = 4.0 if c_val == 5 else 7.0

                                # 5-Stage Particle VFX Explosion
                                vfx_sz = 'large' if c_val >= 8 else ('medium' if c_val >= 4 else 'small')
                                vfx_engine.spawn_explosion(e['rect'].centerx, e['rect'].centery, size=vfx_sz, enemy_type=e_type)

                                for _ in range(14 if c_val < 5 else 24):
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
            draw_powerup_orb(screen, a['rect'].center, a['type'], now, ui_pulse_t)

            if a['rect'].colliderect(player_rect):
                skills[a['type']]['active'] = True
                skills[a['type']]['timer'] = now + skills[a['type']]['duration']
                tap_snd.play()
                if a in achievements:
                    achievements.remove(a)
            elif a['rect'].top > HEIGHT or a['rect'].bottom < 0 or a['rect'].right < 0 or a['rect'].left > WIDTH:
                if a in achievements:
                    achievements.remove(a)

        # Drawing Player Bullets — plasma capsules with glowing trails
        for b in bullets:
            # Emit plasma trail
            if visual_quality == 'high':
                vfx_engine.emit_bullet_trail(b['rect'].centerx, b['rect'].top, color=NEON_TEAL)
            draw_plasma_bullet(screen, b['rect'], color=NEON_TEAL, pulse_t=ui_pulse_t)

        # Render bullet trails
        vfx_engine.update_and_draw_trails(screen)

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
                    if visual_quality == 'high':
                        import random
                        pygame.draw.circle(screen, (0, 255, 255), (f['rect'].centerx, f['rect'].top), random.randint(2, 4))
            else:
                screen.blit(fighter_img, f['rect'])
                if visual_quality == 'high':
                    import random
                    pygame.draw.circle(screen, (0, 255, 255), (f['rect'].centerx, f['rect'].top), random.randint(2, 4))
            if f['hp'] < f['max_hp']:
                hp_w = int((f['rect'].width - 8) * (f['hp'] / f['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (f['rect'].left + 4, f['rect'].top - 8, f['rect'].width - 8, 4), border_radius=2)
                pygame.draw.rect(screen, (255, 50, 50), (f['rect'].left + 4, f['rect'].top - 8, hp_w, 4), border_radius=2)

        for e in elites:
            if is_blackhole:
                e_dist = math.hypot(BH_X - e['rect'].centerx, BH_Y - e['rect'].centery)
                if e_dist < 150:
                    e_scale = max(0.2, e_dist / 150.0)
                    scaled_e = pygame.transform.scale(elite_img, (max(10, int(60 * e_scale)), max(10, int(60 * e_scale))))
                    screen.blit(scaled_e, scaled_e.get_rect(center=e['rect'].center))
                else:
                    screen.blit(elite_img, e['rect'])
                    if visual_quality == 'high':
                        import random
                        pygame.draw.circle(screen, (255, 100, 255), (e['rect'].centerx - 10, e['rect'].top), random.randint(2, 5))
                        pygame.draw.circle(screen, (255, 100, 255), (e['rect'].centerx + 10, e['rect'].top), random.randint(2, 5))
            else:
                screen.blit(elite_img, e['rect'])
                if visual_quality == 'high':
                    import random
                    pygame.draw.circle(screen, (255, 100, 255), (e['rect'].centerx - 10, e['rect'].top), random.randint(2, 5))
                    pygame.draw.circle(screen, (255, 100, 255), (e['rect'].centerx + 10, e['rect'].top), random.randint(2, 5))

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
                    if visual_quality == 'high':
                        import random
                        pygame.draw.circle(screen, (255, 50, 50), (h['rect'].centerx - 15, h['rect'].top), random.randint(3, 6))
                        pygame.draw.circle(screen, (255, 50, 50), (h['rect'].centerx + 15, h['rect'].top), random.randint(3, 6))
            else:
                screen.blit(heavy_img, h['rect'])
                if visual_quality == 'high':
                    import random
                    pygame.draw.circle(screen, (255, 50, 50), (h['rect'].centerx - 15, h['rect'].top), random.randint(3, 6))
                    pygame.draw.circle(screen, (255, 50, 50), (h['rect'].centerx + 15, h['rect'].top), random.randint(3, 6))

            if h['hp'] < h['max_hp']:
                hp_w = int((h['rect'].width - 10) * (h['hp'] / h['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (h['rect'].left + 5, h['rect'].top - 10, h['rect'].width - 10, 5), border_radius=2)
                pygame.draw.rect(screen, ORANGE, (h['rect'].left + 5, h['rect'].top - 10, hp_w, 5), border_radius=2)

        # Drawing Phantoms (Cloaking stealth predator)
        for p in phantoms:
            is_cloaked = p.get('is_cloaked', False)
            if is_cloaked:
                ghost_surf = fighter_img.copy()
                ghost_surf.set_alpha(45)
                screen.blit(ghost_surf, p['rect'])
                if visual_quality == 'high':
                    pygame.draw.rect(screen, (*NEON_VIOLET, 80), p['rect'].inflate(4, 4), width=1, border_radius=8)
            else:
                screen.blit(fighter_img, p['rect'])
                if visual_quality == 'high':
                    pygame.draw.circle(screen, NEON_VIOLET, (p['rect'].centerx, p['rect'].top), 4)

            if p['hp'] < p['max_hp']:
                hp_w = int((p['rect'].width - 8) * (p['hp'] / p['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (p['rect'].left + 4, p['rect'].top - 8, p['rect'].width - 8, 4), border_radius=2)
                pygame.draw.rect(screen, NEON_VIOLET, (p['rect'].left + 4, p['rect'].top - 8, hp_w, 4), border_radius=2)

        # Drawing Berserkers (Hyper-aggressive scarlet tank)
        for bz in berserkers:
            screen.blit(heavy_img, bz['rect'])
            if visual_quality == 'high':
                # Pulsing rage aura
                r_alpha = int(80 + 60 * math.sin(ui_pulse_t * 6))
                r_surf = pygame.Surface((bz['rect'].width + 12, bz['rect'].height + 12), pygame.SRCALPHA)
                pygame.draw.rect(r_surf, (*NEON_SCARLET, r_alpha), r_surf.get_rect(), border_radius=12, width=2)
                screen.blit(r_surf, (bz['rect'].x - 6, bz['rect'].y - 6))

            if bz['hp'] < bz['hp']:
                pass
            if bz['hp'] < bz['max_hp']:
                hp_w = int((bz['rect'].width - 10) * (bz['hp'] / bz['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (bz['rect'].left + 5, bz['rect'].top - 10, bz['rect'].width - 10, 5), border_radius=2)
                pygame.draw.rect(screen, NEON_SCARLET, (bz['rect'].left + 5, bz['rect'].top - 10, hp_w, 5), border_radius=2)

        # Drawing Commanders (Golden squad leader with tactical beacon)
        for cmd in commanders:
            screen.blit(heavy_img, cmd['rect'])
            # Tactical command beacon aura
            cmd_surf = pygame.Surface((cmd['rect'].width + 16, cmd['rect'].height + 16), pygame.SRCALPHA)
            pygame.draw.rect(cmd_surf, (*NEON_GOLD, 90), cmd_surf.get_rect(), border_radius=14, width=2)
            screen.blit(cmd_surf, (cmd['rect'].x - 8, cmd['rect'].y - 8))
            draw_text("*", FONT_TINY, NEON_GOLD, cmd['rect'].centerx, cmd['rect'].top - 12)

            if cmd['hp'] < cmd['max_hp']:
                hp_w = int((cmd['rect'].width - 10) * (cmd['hp'] / cmd['max_hp']))
                pygame.draw.rect(screen, (40, 40, 40), (cmd['rect'].left + 5, cmd['rect'].top - 10, cmd['rect'].width - 10, 5), border_radius=2)
                pygame.draw.rect(screen, NEON_GOLD, (cmd['rect'].left + 5, cmd['rect'].top - 10, hp_w, 5), border_radius=2)

        if boss_active and boss_death_timer == 0:
            if boss_angle != 0.0:
                rotated_boss = pygame.transform.rotate(current_boss_img, boss_angle)
                new_rect = rotated_boss.get_rect(center=boss_rect.center)
                screen.blit(rotated_boss, new_rect.topleft)
            else:
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

        # Damage Numbers Update & Draw
        if show_damage_enabled:
            for dn in damage_numbers[:]:
                dn['y'] -= 1
                dn['life'] -= 1
                if dn['life'] > 0:
                    draw_text(str(dn['val']), FONT_TINY, dn['col'], int(dn['x']), int(dn['y']))
                else:
                    damage_numbers.remove(dn)

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
            if player_dmg_anim > 0 and (player_dmg_anim // 2) % 2 == 0 and visual_quality == 'high':
                pass # blink
            else:
                screen.blit(p_draw_surf, p_draw_rect)
        else:
            if player_dmg_anim > 0 and (player_dmg_anim // 2) % 2 == 0 and visual_quality == 'high':
                pass
            else:
                draw_rect = player_rect.copy()
                if player_fire_anim > 0 and visual_quality == 'high':
                    draw_rect.y += 2
                screen.blit(player_img, draw_rect)
                if player_fire_anim > 0 and visual_quality == 'high':
                    vfx_engine.draw_muzzle_flash(screen, draw_rect.centerx, draw_rect.top)
        if player_dmg_anim > 0: player_dmg_anim -= 1
        if player_fire_anim > 0: player_fire_anim -= 1

        # ==========================
        # PREMIUM HOLOGRAPHIC HUD
        # ==========================
        # HUD background panel (top bar)
        hud_bg = pygame.Surface((WIDTH, 68), pygame.SRCALPHA)
        pygame.draw.rect(hud_bg, (8, 12, 22, 235), hud_bg.get_rect(),
                         border_bottom_left_radius=22, border_bottom_right_radius=22)
        pygame.draw.rect(hud_bg, (0, 200, 255, 70), hud_bg.get_rect(), width=2,
                         border_bottom_left_radius=22, border_bottom_right_radius=22)
        screen.blit(hud_bg, (0, 0))

        # Scanline effect on HUD
        for _sy in range(0, 68, 4):
            sl = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            sl.fill((0, 0, 0, 14))
            screen.blit(sl, (0, _sy))

        # Corner brackets on HUD
        draw_corner_brackets(screen, pygame.Rect(2, 2, WIDTH - 4, 64), NEON_CYAN, size=10, width=1)

        # ── Coin Display (left) ──
        screen.blit(coin_icon, (14, 12))
        draw_neon_text(screen, str(total_coins), FONT_HUD, NEON_GOLD, 70, 34, glow_radius=3)

        # ── Environment + Level Badge (center) ──
        env_names_hud = {1: "GALAXY", 2: "NEBULA", 3: "BLACKHOLE"}
        env_label = env_names_hud.get(current_selected_env, "GALAXY")
        env_accent_hud = {1: NEON_BLUE, 2: NEON_PURPLE, 3: NEON_PINK}.get(current_selected_env, NEON_CYAN)

        # Environment + Level text
        hud_label = f"{env_label}  •  MISSION {current_level}"
        draw_neon_text(screen, hud_label, FONT_UI, env_accent_hud, WIDTH // 2 - 20, 34, glow_radius=2)

        # ── Pause Button ──
        draw_button(screen, "||", FONT_SMALL, WHITE, pause_btn_rect,
                    (40, 50, 70), is_h_pause, border_radius=10, outline_color=NEON_CYAN)

        if control_type == 'MOBILE':
            touch_hud.draw_fire_button(screen, is_h_fire and mouse_pressed, FONT_TINY)

        # ── Player Health Bar (right side) — chromatic ──
        hp_bar_rect = pygame.Rect(WIDTH - 212, 18, 188, 20)
        hp_frac = max(0.0, player_health / max(1, unlocked_hp))
        draw_chromatic_bar(screen, hp_bar_rect, hp_frac,
                           label=f"HP {int(max(0, player_health))}/{unlocked_hp}",
                           font=FONT_HP, border_radius=10, show_glow=True, pulse_t=ui_pulse_t)

        # ── Boss Health Bar ──
        if boss_active and boss_death_timer == 0:
            boss_hp_bg = pygame.Rect(WIDTH // 2 - 175, 76, 350, 18)
            boss_frac = max(0.0, boss_hp / max(1, boss_max_hp))

            # Phase markers on boss bar
            for ph_frac in [0.5, 0.25]:
                ph_x = boss_hp_bg.x + int(boss_hp_bg.width * ph_frac)
                ph_surf = pygame.Surface((2, boss_hp_bg.height + 4), pygame.SRCALPHA)
                ph_surf.fill((255, 255, 255, 180))
                screen.blit(ph_surf, (ph_x, boss_hp_bg.y - 2))

            draw_chromatic_bar(screen, boss_hp_bg, boss_frac,
                               label=f"BOSS  {int(max(0, boss_hp))}/{boss_max_hp}",
                               font=FONT_HP, border_radius=9, show_glow=True, pulse_t=ui_pulse_t,
                               color_full=NEON_PINK, color_mid=(200, 50, 180), color_low=NEON_SCARLET)

            # Phase indicators
            ph_str = f"PHASE {boss_ai_phase}/3"
            draw_text(ph_str, FONT_TINY, NEON_PINK, WIDTH // 2 + 185, 85)

        # Mobile hint
        if control_type == 'MOBILE':
            draw_text("SLIDE TO MOVE & FIRE", FONT_SMALL, (80, 100, 130), WIDTH // 2, HEIGHT - 18)

        # ── Kill Progress Ring ──
        boss_kill_reqs_hud = {1: 12, 2: 14, 3: 18, 4: 22, 5: 30,
                              6: 38, 7: 46, 8: 56, 9: 70, 10: 82}
        req_kills_hud = (min(222, 195 + (current_level - 30) * 3) if current_level >= 31
                         else (min(222, 140 + (current_level - 20) * 5) if current_level >= 21
                         else (min(140, 75 + (current_level - 10) * 6) if current_level >= 11
                         else boss_kill_reqs_hud.get(current_level, 25))))
        if not boss_active and not boss_arriving:
            kill_frac = min(1.0, kill_count / max(1, req_kills_hud))
            draw_kill_ring(screen, WIDTH // 2 - 20, 88, kill_frac, kill_count, req_kills_hud,
                           color=env_accent_hud, radius=22, pulse_t=ui_pulse_t)

        # ── Active Powerup Orbital Timers ──
        orb_x = 18
        for s_key, s_val in skills.items():
            if s_val['active']:
                rem_ms  = s_val['timer'] - now
                rem_frac = max(0.0, rem_ms / s_val['duration'])
                if rem_frac > 0:
                    draw_orbital_skill_timer(screen, orb_x + 24, 110,
                                            rem_frac, s_val['label'][:2],
                                            s_val['color'], ui_pulse_t)
                    orb_x += 56
                else:
                    s_val['active'] = False

        # Boss Spawning Condition (Beginner-friendly kill scaling)
        boss_kill_reqs = {1: 15, 2: 20, 3: 25, 4: 35, 5: 45, 6: 60, 7: 75, 8: 90, 9: 105, 10: 120}
        req_kills = min(200, 120 + (current_level - 10) * 4) if current_level >= 11 else boss_kill_reqs.get(current_level, 25)

        if kill_count >= req_kills and not boss_active and not boss_arriving and boss_defeated_timer == 0:
            boss_arriving = True
            boss_warning_timer = 180
            
            # 💥 MAP CLEAR: Clear all regular minions, bullets, and asteroids in a clean explosion
            for e_arr in (fighters, elites, heavies):
                for e in e_arr:
                    for _ in range(8):
                        particles.append([e['rect'].centerx, e['rect'].centery, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 6), random.choice(BLAST_COLORS)])
                e_arr.clear()
            for ast in list(asteroid_group):
                for _ in range(8):
                    particles.append([ast.rect.centerx, ast.rect.centery, random.uniform(-3, 3), random.uniform(-3, 3), random.randint(3, 6), (140, 140, 150)])
                ast.kill()
            enemy_bullets.clear()
            expl_snd.play()
            global_shake_intensity = 10.0

        if boss_arriving:
            boss_warning_timer -= 1
            
            # Smoothly glide player down to safety if they were high up on the map before the boundary solidifies
            if player_rect.top < PLAYER_BOSS_MIN_Y:
                player_rect.y += min(4, PLAYER_BOSS_MIN_Y - player_rect.top)

            # 🚨 Dramatic Screen Blink / Alarm Strobe
            if (boss_warning_timer // 15) % 2 == 0:
                blink_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                blink_surf.fill((255, 20, 20, 40))
                screen.blit(blink_surf, (0, 0))
                draw_text_shadow("! WARNING: BOSS APPROACHING !", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2 - 20, shadow_color=(80, 0, 0), offset=3)
                draw_text("SECTOR CLEARED // DEFENSE BARRIER ENGAGED", FONT_SMALL, NEON_GOLD, WIDTH // 2, HEIGHT // 2 + 25)
            else:
                draw_text_shadow("! WARNING: BOSS APPROACHING !", FONT_TITLE, YELLOW, WIDTH // 2, HEIGHT // 2 - 20, shadow_color=(80, 50, 0), offset=2)
                draw_text("SECTOR CLEARED // DEFENSE BARRIER ENGAGED", FONT_SMALL, WHITE, WIDTH // 2, HEIGHT // 2 + 25)

            if boss_warning_timer <= 0:
                boss_arriving = False
                boss_active = True
                boss_ai_state = 'patrol'
                boss_ai_timer = 0
                boss_ai_phase = 1
                boss_rect.centerx = WIDTH // 2
                boss_rect.bottom = 0  # Enter from top of screen
                player_rect.top = max(PLAYER_BOSS_MIN_Y, player_rect.top)

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

        box = pygame.Rect(160, 85, 480, 430)
        draw_neon_panel(screen, box, accent=NEON_CYAN, alpha=245, border_radius=20, bg=PANEL_BG)
        draw_text_shadow("GAME PAUSED", FONT_MODAL_TITLE, NEON_CYAN, 400, 125, shadow_color=(0, 60, 100), offset=2)
        draw_text("MISSION IN PROGRESS", FONT_TINY, LIGHT_GRAY, 400, 158)
        draw_divider(screen, 195, 175, 605, NEON_CYAN, alpha=50)

        btn_resume = pygame.Rect(200, 195, 400, 50)
        btn_restart = pygame.Rect(200, 255, 400, 50)
        btn_settings = pygame.Rect(200, 315, 400, 50)
        btn_menu = pygame.Rect(200, 375, 400, 50)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]
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

        draw_glowing_button(screen, ">  RESUME MISSION", FONT_UI, WHITE, btn_resume, NEON_GREEN, is_h_p, border_radius=14, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "@  RESTART LEVEL", FONT_UI, WHITE, btn_restart, NEON_ORANGE, is_h_r, border_radius=14, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, ">  SETTINGS", FONT_UI, WHITE, btn_settings, NEON_CYAN, is_h_s, border_radius=14, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "ESC  ABORT TO MENU", FONT_UI, WHITE, btn_menu, NEON_PINK, is_h_m, border_radius=14, pulse_t=ui_pulse_t)

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
            elif is_h_r and (m_c or key_enter):
                tap_snd.play()
                warning_target = "RESTART"
                state = 15
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

    # ==========================
    # WARNING SCREEN (STATE 15)
    # ==========================
    elif state == 15:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        w_box = pygame.Rect(140, 140, 520, 310)
        draw_neon_panel(screen, w_box, accent=RED, alpha=250, border_radius=20, bg=PANEL_BG)

        draw_text_shadow("ABORT MISSION?", FONT_MODAL_TITLE, RED, 400, 185, shadow_color=(80, 0, 0), offset=2)
        draw_divider(screen, 180, 215, 620, RED, alpha=50)
        draw_text("If you leave or restart now,", FONT_UI, WHITE, 400, 245)
        draw_text("all unbanked level coins will be lost!", FONT_SMALL, NEON_GOLD, 400, 280)

        btn_w_back = pygame.Rect(175, 340, 210, 54)
        btn_ok     = pygame.Rect(415, 340, 210, 54)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]
        is_h_back = btn_w_back.collidepoint(mx, my)
        is_h_ok   = btn_ok.collidepoint(mx, my)

        draw_glowing_button(screen, "RESUME", FONT_UI, WHITE, btn_w_back, NEON_GREEN, is_h_back, border_radius=14, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "CONFIRM LEAVE", FONT_UI, WHITE, btn_ok, RED, is_h_ok, border_radius=14, pulse_t=ui_pulse_t)

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
        m_down = pygame.mouse.get_pressed()[0]

        # State 5: Dedicated Confirmation Modal for Revive
        if state == 5 and show_revive_confirm:
            p_box = pygame.Rect(130, 100, 540, 400)
            draw_holographic_panel(screen, p_box, accent=NEON_GOLD, alpha=252, border_radius=22,
                                   bg=(25, 20, 30), show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

            draw_text_shadow("CONFIRM REVIVE", FONT_MODAL_TITLE, NEON_GOLD, 400, 145, shadow_color=(80, 50, 0), offset=2)
            draw_text("RESTORE FULL COMBAT POWER", FONT_TINY, NEON_CYAN, 400, 185)
            draw_divider(screen, 170, 202, 630, NEON_GOLD, alpha=50)

            feat_card = pygame.Rect(160, 220, 480, 64)
            pygame.draw.rect(screen, (35, 30, 45), feat_card, border_radius=12)
            pygame.draw.rect(screen, (80, 70, 100), feat_card, width=1, border_radius=12)
            draw_text("* Full Armor Hull + 3s Invulnerability Barrier", FONT_SMALL, WHITE, 400, 242)
            
            c_price = get_revive_price(current_level, revives_done_this_level)
            can_afford = total_coins >= c_price
            cost_color = NEON_GREEN if can_afford else RED
            draw_text(f"Price: $ {c_price} Coins  |  Bank: {total_coins} Coins", FONT_SMALL, cost_color, 400, 310)

            b_back = pygame.Rect(165, 380, 220, 54)
            b_buy = pygame.Rect(415, 380, 220, 54)

            is_h_rbk = b_back.collidepoint(mx, my)
            is_h_rbuy = b_buy.collidepoint(mx, my)

            draw_plasma_button(screen, "CANCEL", FONT_UI, WHITE, b_back, (140, 20, 50), is_h_rbk,
                               border_radius=14, accent=NEON_PINK, pulse_t=0)
            draw_plasma_button(screen, f"REVIVE ({c_price})", FONT_UI, WHITE, b_buy,
                               (0, 150, 60) if can_afford else (50, 50, 60), is_h_rbuy,
                               border_radius=14, accent=NEON_GREEN if can_afford else MID_GRAY, pulse_t=ui_pulse_t)

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
                    phantoms.clear()
                    berserkers.clear()
                    commanders.clear()
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
            box = pygame.Rect(130, 80, 540, 440)
            draw_holographic_panel(screen, box, accent=NEON_GREEN, alpha=252, border_radius=22,
                                   bg=(10, 24, 18), show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

            draw_text_shadow("VICTORY:  VICTORY!", FONT_MODAL_TITLE, NEON_GREEN, 400, 125, shadow_color=(0, 80, 40), offset=2)
            draw_text("SECTOR SECURED // THREAT NEUTRALIZED", FONT_TINY, NEON_CYAN, 400, 160)
            draw_divider(screen, 170, 178, 630, NEON_GREEN, alpha=50)

            # Star Rating on Victory
            earned_stars = 3 if kill_count >= 20 else (2 if kill_count >= 10 else 1)
            star_icon = pygame.transform.scale(star_for_rating, (48, 48))
            start_x = 400 - ((earned_stars * 54) // 2) + 3
            for i in range(earned_stars):
                screen.blit(star_icon, (start_x + (i * 54), 195))

            stats_box = pygame.Rect(170, 265, 460, 50)
            pygame.draw.rect(screen, PANEL_MID, stats_box, border_radius=12)
            pygame.draw.rect(screen, NEON_GREEN, stats_box, width=1, border_radius=12)
            draw_text(f"$ +{level_coins} Coins Earned  |  VS Hostiles Eliminated: {kill_count}", FONT_SMALL, NEON_GOLD, 400, 290)

            b_m = pygame.Rect(165, 350, 220, 56)
            b_n = pygame.Rect(415, 350, 220, 56)

            is_h_m = b_m.collidepoint(mx, my)
            is_h_n = b_n.collidepoint(mx, my)

            draw_plasma_button(screen, "< MAIN MENU", FONT_UI, WHITE, b_m, (0, 70, 160), is_h_m,
                               border_radius=16, accent=NEON_BLUE, pulse_t=ui_pulse_t)
            draw_plasma_button(screen, "NEXT LEVEL >", FONT_UI, WHITE, b_n, (0, 150, 60), is_h_n,
                               border_radius=16, accent=NEON_GREEN, pulse_t=ui_pulse_t)

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
            box = pygame.Rect(120, 70, 560, 465)
            draw_holographic_panel(screen, box, accent=NEON_PINK, alpha=252, border_radius=22,
                                   bg=(28, 10, 15), show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

            draw_text_shadow("FAILED:  MISSION FAILED", FONT_MODAL_TITLE, NEON_PINK, 400, 115, shadow_color=(80, 0, 0), offset=2)
            draw_text("STARSHIP DESTROYED IN COMBAT", FONT_TINY, LIGHT_GRAY, 400, 150)
            draw_divider(screen, 160, 168, 640, NEON_PINK, alpha=50)

            stats_box = pygame.Rect(160, 185, 480, 48)
            pygame.draw.rect(screen, PANEL_MID, stats_box, border_radius=12)
            pygame.draw.rect(screen, NEON_PINK, stats_box, width=1, border_radius=12)
            draw_text(f"$ Coins: +{level_coins}  |  VS Enemies Down: {kill_count}", FONT_SMALL, NEON_GOLD, 400, 209)

            rev_b = pygame.Rect(180, 255, 440, 58)
            b_n   = pygame.Rect(180, 325, 440, 50)
            b_m   = pygame.Rect(180, 385, 440, 50)

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

            draw_plasma_button(screen, "*  REVIVE STARSHIP", FONT_UI, WHITE, rev_b, (140, 100, 0), is_h_rev,
                               border_radius=16, accent=NEON_GOLD, pulse_t=ui_pulse_t)
            draw_plasma_button(screen, "@  RETRY MISSION", FONT_UI, WHITE, b_n, (140, 60, 0), is_h_n,
                               border_radius=14, accent=NEON_ORANGE, pulse_t=ui_pulse_t)
            draw_plasma_button(screen, "< MAIN MENU", FONT_UI, WHITE, b_m, (0, 70, 150), is_h_m,
                               border_radius=14, accent=NEON_BLUE, pulse_t=ui_pulse_t)

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

    # Apply Global Screen Shake
    if screen_shake_enabled and visual_quality == 'high' and global_shake_intensity > 0.5:
        shake_x = random.uniform(-global_shake_intensity, global_shake_intensity)
        shake_y = random.uniform(-global_shake_intensity, global_shake_intensity)
        shake_surf = screen.copy()
        screen.fill((10, 10, 15))  # Dark space background color for borders
        screen.blit(shake_surf, (int(shake_x), int(shake_y)))
    
    # Decay the shake intensity every frame
    if global_shake_intensity > 0:
        global_shake_intensity *= 0.85
        if global_shake_intensity < 0.1:
            global_shake_intensity = 0.0

    # FPS Counter Overlay
    if show_fps:
        fps_val = int(clock.get_fps())
        fps_color = NEON_GREEN if fps_val >= 50 else NEON_GOLD if fps_val >= 30 else RED
        fps_text = FONT_TINY.render(f"FPS: {fps_val}", True, fps_color)
        fps_bg = pygame.Rect(WIDTH - 78, 4, 74, 22)
        pygame.draw.rect(screen, (10, 12, 20, 200), fps_bg, border_radius=6)
        pygame.draw.rect(screen, fps_color, fps_bg, width=1, border_radius=6)
        screen.blit(fps_text, fps_text.get_rect(center=fps_bg.center))

    if state != prev_state:
        ignore_mouse_until_released = True
        
    pygame.display.flip()
    clock.tick(60)