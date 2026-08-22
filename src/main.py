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
import cloud_sync

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

try:
    icon_path = os.path.join(app_dir, 'icon.ico')
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
    game_icon = pygame.image.load(icon_path)
    pygame.display.set_icon(game_icon)
except:
    pass

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
pygame.display.set_caption("Crazyy Simulation")

is_fullscreen = False

def apply_display_mode(fullscreen):
    """Safely apply Fullscreen or Windowed display mode with hardware scaling preserved."""
    global screen, is_fullscreen
    target_fullscreen = bool(fullscreen)
    current_fullscreen = bool(screen.get_flags() & pygame.FULLSCREEN)
    
    if current_fullscreen != target_fullscreen:
        pygame.display.toggle_fullscreen()
        
    is_fullscreen = target_fullscreen
    return screen

# Import only fonts and helper functions from assets (no heavy images yet)
from assets import *
from branding import CinematicBranding
from menu_battle import MenuBattleSimulation
from vfx import VisualEffectsEngine, draw_neon_auth_bg

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
mouse_y_prev = 0
max_scroll_y = 850
control_type = 'PC'
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
is_fullscreen = True     # Game starts in fullscreen mode
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
    global unlocked_bullets, bullet_step, max_galaxy_level, max_nebula_level, max_blackhole_level, control_type
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


def reset_level_logic(level):
    global current_level, player_health, player_rect, bullets, enemy_bullets
    global fighters, elites, heavies, achievements, particles
    global boss_hp, boss_max_hp, boss_death_timer, current_level, boss_rect, kill_count
    global boss_active, boss_arriving, boss_target_x, current_boss_img
    global boss_warning_timer, boss_defeated_timer
    global blackhole_alert_active, revive_protection_timer
    global galaxy_bg_y

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
    achievements.clear()
    particles.clear()
    damage_numbers.clear()
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

    # Reset Boss AI brain
    global boss_ai_state, boss_ai_timer, boss_ai_phase, boss_angle, boss_sweep_dir, boss_spiral_t, boss_dive_target
    boss_ai_state    = 'patrol'
    boss_ai_timer    = 0
    boss_ai_phase    = 1
    boss_angle       = 0.0
    boss_sweep_dir   = 1
    boss_spiral_t    = 0.0
    boss_dive_target = (WIDTH // 2, HEIGHT // 2)

    # Boss HP scaling tiered by campaign difficulty
    if current_level <= 10:
        boss_max_hp = 120 + (current_level * 20)  # Lvl 1: 140 HP, Lvl 10: 320 HP
    elif current_level <= 30:
        boss_max_hp = 320 + ((current_level - 10) * 35)  # Lvl 11: 355 HP, Lvl 30: 1020 HP
    else:
        boss_max_hp = 1050 + ((current_level - 30) * 60)  # Lvl 31: 1110 HP, Lvl 40: 1650 HP
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
cloud_sync.load_local_session()
cloud_sync.start_sync_thread(SAVE_FILE)

if not is_fullscreen:
    apply_display_mode(False)

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
    now = pygame.time.get_ticks()
    m_p = pygame.mouse.get_pos()
    m_c = False
    mx, my = pygame.mouse.get_pos()
    m_down = pygame.mouse.get_pressed()[0]
    
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

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pressed = True
                if click_cooldown <= 0:
                    m_c = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
                m_u = True
        if event.type == pygame.MOUSEWHEEL:
            m_wheel = event.y
        if event.type == pygame.MOUSEMOTION:
            mouse_dx, mouse_dy = event.rel
        if event.type == pygame.KEYDOWN:
            if event.unicode.isprintable() and len(event.unicode) > 0:
                key_unicode = event.unicode
            if event.key == pygame.K_RETURN: key_enter = True
            elif event.key == pygame.K_BACKSPACE: key_backspace = True
            elif event.key == pygame.K_ESCAPE: key_escape = True
            elif event.key == pygame.K_UP or event.key == pygame.K_w: key_up = True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s: key_down = True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a: key_left = True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d: key_right = True
            elif event.key == pygame.K_TAB: key_tab = True
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

        # ---- PROFILE / LOGOUT (top right) ----
        profile_name = cloud_sync.current_username or "Guest"
        if len(profile_name) > 12:
            profile_name = profile_name[:10] + ".."
        draw_text(f"👤 {profile_name}", FONT_TINY, WHITE, 680, 25)
        
        btn_quick_logout = pygame.Rect(640, 45, 80, 24)
        is_h_q_logout = btn_quick_logout.collidepoint(mx, my)
        pygame.draw.rect(screen, RED if is_h_q_logout else (100, 30, 30), btn_quick_logout, border_radius=8)
        draw_text("LOGOUT", FONT_TINY, WHITE, btn_quick_logout.centerx, btn_quick_logout.centery)
        
        if m_c and is_h_q_logout:
            tap_snd.play()
            cloud_sync.clear_local_session()
            total_coins = 0
            max_galaxy_level = 1
            max_nebula_level = 1
            max_blackhole_level = 1
            unlocked_hp = 5
            unlocked_speed = 5
            unlocked_bullets = 1
            bullet_step = 0
            current_selected_env = 1
            total_coins = 0

            max_galaxy_level = 1
            max_nebula_level = 1
            max_blackhole_level = 1
            state = -3
            click_cooldown = 12
            m_c = False

        # ---- MENU BUTTONS ----
        menu_btns = [
            ("🎮  CAMPAIGN",    NEON_BLUE,      200, 20),
            ("🌐  MULTIPLAYER", MID_GRAY,       272, "locked"),
            ("🛒  STORE",       (140, 40, 200), 344, 6),
            ("⚙   SETTINGS",   NEON_ORANGE,    416, 9),
            ("✕  QUIT",        NEON_PINK,      488, 0),
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
            if is_hover and target != "locked":
                focused_btn = idx  # Mouse overrides keyboard focus
            
            draw_glowing_button(screen, txt, FONT_UI, WHITE if target != "locked" else LIGHT_GRAY, btn_rect, col, (is_hover or is_focused) and target != "locked",
                                border_radius=16, accent=NEON_CYAN, pulse_t=ui_pulse_t)
            
            if target == "locked":
                # Draw COMING SOON badge
                badge_rect = pygame.Rect(btn_rect.right - 95, btn_rect.y - 10, 100, 24)
                pygame.draw.rect(screen, RED, badge_rect, border_radius=12)
                draw_text("COMING v2.0", FONT_TINY, WHITE, badge_rect.centerx, badge_rect.centery)

            # Keyboard focus indicator
            if is_focused and not is_hover and target != "locked":
                focus_surf = pygame.Surface((btn_rect.width + 8, btn_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(focus_surf, (*NEON_CYAN, 90), focus_surf.get_rect(), border_radius=18, width=2)
                screen.blit(focus_surf, (btn_rect.x - 4, btn_rect.y - 4))

            activated = (m_c and is_hover) or (key_enter and is_focused)
            if activated and target != "locked":
                if txt.endswith("QUIT"):
                    running = False
                elif ("CAMPAIGN" in txt or "STORE" in txt) and control_type is None:
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
    elif state == 6:
        res = render_store(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t, menu_bg,
            coin_icon, total_coins, hp_step, speed_step, bullet_step,
            hp_costs, speed_costs, bullet_costs, store_selection,
            unlocked_hp, unlocked_speed, unlocked_bullets
        )
        state, store_selection, click_cooldown, m_c, key_escape, key_enter = res

    elif state == 7:
        res = render_store_confirm(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, tap_snd, ui_pulse_t, total_coins,
            store_selection, hp_step, speed_step, bullet_step,
            hp_costs, speed_costs, bullet_costs
        )
        state, action_dict, click_cooldown, m_c, key_escape, key_enter = res
        
        if action_dict and action_dict.get('type') == 'buy':
            cost = action_dict.get('cost', 0)
            if cost > 0 and total_coins >= cost:
                total_coins -= cost
                tap_snd.play()
                item = action_dict.get('item', store_selection)
                if item in (0, 'hp'):
                    hp_step = min(hp_step + 1, len(hp_costs) - 1)
                    unlocked_hp += 50
                elif item in (1, 'sp'):
                    speed_step = min(speed_step + 1, len(speed_costs) - 1)
                    unlocked_speed += 1
                elif item in (2, 'pb', 'bullets'):
                    bullet_step = min(bullet_step + 1, len(bullet_costs) - 1)
                    unlocked_bullets += 1
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
        m_down = pygame.mouse.get_pressed()[0]
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
        m_down = pygame.mouse.get_pressed()[0]
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
        m_down = pygame.mouse.get_pressed()[0]
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
        m_down = pygame.mouse.get_pressed()[0]
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

            if (keys[pygame.K_SPACE] or (mouse_pressed and not is_h_pause) or auto_fire_enabled) and fire_cooldown <= 0:
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

            if (mouse_pressed and not is_h_pause or auto_fire_enabled) and fire_cooldown <= 0:
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

        # Asteroids Update & Collision
        asteroid_group.update()
        asteroid_group.draw(screen)

        for ast in list(asteroid_group):
            if ast.rect.colliderect(player_rect):
                if not skills['immortal']['active'] and revive_protection_timer <= 0:
                    player_health -= 30
                    player_dmg_anim = 15
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

        # --- ENEMY AI: DIFFICULTY-SCALED MOVEMENT & COMBAT ---
        # AI aggression scales with level: 0.0 (easy) to 1.0 (max)
        ai_aggression = min(1.0, current_level / 20.0)
        ai_accuracy   = min(1.0, current_level / 30.0)  # How well enemies predict player position

        for e_list, val, e_type in [(fighters, 1, 'fighter'), (elites, 2, 'elite'), (heavies, 5, 'heavy')]:
            for e in e_list[:]:
                e['time'] = e.get('time', 0) + 1
                e['start_x'] = e.get('start_x', e['rect'].x)

                # Init per-enemy AI state fields
                if 'ai_state' not in e:
                    e['ai_state'] = 'descend'  # States: descend, strafe, dive, retreat
                    e['ai_timer'] = 0
                    e['target_x'] = e['rect'].x
                    e['dodge_dir'] = random.choice([-1, 1])

                e['ai_timer'] = e.get('ai_timer', 0) + 1

                # === FIGHTER AI: Fast dive-bombers that dodge bullets ===
                if e_type == 'fighter':
                    dive_spd = (e.get('dive_speed', 3.0) + eff_speed_lvl * 0.2) * env_speed_mult

                    # High-level fighters dodge incoming bullets
                    if ai_aggression > 0.4:
                        for b in bullets:
                            if abs(b['rect'].centerx - e['rect'].centerx) < 40 and b['rect'].top < e['rect'].bottom:
                                e['dodge_dir'] = 1 if e['rect'].centerx < 400 else -1
                                break

                    # Strafe: Sine wave + player tracking at higher levels
                    track_weight = ai_aggression * 0.5  # 0 to 0.5
                    target_x_drift = player_rect.centerx * track_weight + e['start_x'] * (1 - track_weight)
                    strafe = math.sin(e['time'] * 0.09) * (3.5 + ai_aggression * 2.5) * env_speed_mult
                    e['rect'].x += int(strafe) + int((target_x_drift - e['rect'].centerx) * 0.01 * ai_aggression)
                    e['rect'].y += int(dive_spd)

                # === ELITE AI: Flanking interceptors that predict player movement ===
                elif e_type == 'elite':
                    e_speed_y = (2.0 + eff_speed_lvl * 0.15) * env_speed_mult

                    # State machine: alternate between strafing and diving at player
                    if e['ai_timer'] % max(60, int(120 - ai_aggression * 80)) == 0:
                        # Re-pick strategy based on aggression
                        if random.random() < ai_aggression:
                            e['ai_state'] = 'dive'
                            # Predictive targeting: aim at where player WILL be
                            predicted_x = player_rect.centerx + (player_rect.centerx - e['rect'].centerx) * 0.2 * ai_accuracy
                            e['target_x'] = max(30, min(WIDTH - 30, int(predicted_x)))
                        else:
                            e['ai_state'] = 'strafe'
                            e['target_x'] = random.randint(60, WIDTH - 60)

                    if e['ai_state'] == 'dive':
                        dx_to_target = e['target_x'] - e['rect'].centerx
                        e['rect'].x += int(dx_to_target * 0.05 * (1 + ai_aggression))
                        e['rect'].y += int(e_speed_y * 1.3)
                    else:
                        wave = math.sin(e['time'] * 0.05) * 6
                        e['rect'].x = int(e['start_x'] + wave)
                        if e['rect'].centerx < player_rect.centerx - 10:
                            e['start_x'] += max(1, int(ai_aggression * 3))
                        elif e['rect'].centerx > player_rect.centerx + 10:
                            e['start_x'] -= max(1, int(ai_aggression * 3))
                        e['rect'].y += int(e_speed_y)

                # === HEAVY AI: Tanky bruisers that strafe and suppress player position ===
                elif e_type == 'heavy':
                    h_speed_y = (1.4 + eff_speed_lvl * 0.1) * env_speed_mult

                    # Heavy AI: alternates between strafing and positioning above player
                    if e['ai_timer'] % max(80, int(180 - ai_aggression * 100)) == 0:
                        if random.random() < ai_aggression * 0.7:
                            # Position directly above player for sustained fire
                            e['target_x'] = max(40, min(WIDTH - 40, player_rect.centerx + random.randint(-30, 30)))
                        else:
                            e['target_x'] = random.randint(80, WIDTH - 80)

                    dx_to_target = e['target_x'] - e['rect'].centerx
                    move_speed_x = min(abs(dx_to_target), max(1, int(2 + ai_aggression * 3)))
                    if dx_to_target > 0:
                        e['rect'].x += move_speed_x
                    elif dx_to_target < 0:
                        e['rect'].x -= move_speed_x
                    e['rect'].y += int(h_speed_y)

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

                # Enemy Shooting: Difficulty-scaled fire rate and bullet patterns
                if random.randint(1, int(fire_chance)) == 1:
                    dmg = eff_dmg_lvl * val
                    if e_type == 'fighter':
                        # At high levels, fighters aim at predicted player X
                        if ai_accuracy > 0.5 and random.random() < ai_accuracy:
                            bx = player_rect.centerx - 3
                        else:
                            bx = e['rect'].centerx - 3
                        enemy_bullets.append({'rect': pygame.Rect(bx, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': RED})
                    elif e_type == 'elite':
                        # Elites fire dual shots; at high level they angle inward
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].left + 4, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': MAGENTA})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].right - 10, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': MAGENTA})
                        if ai_aggression > 0.6 and random.random() < 0.4:
                            enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 3, e['rect'].bottom, 6, 14), 'damage': dmg, 'color': CYAN})
                    elif e_type == 'heavy':
                        # Heavies fire 3-way spread; at high level they add a 4th center shot
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].bottom, 10, 16), 'damage': dmg + 5, 'color': ORANGE})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].left + 5, e['rect'].bottom - 5, 8, 14), 'damage': dmg, 'color': YELLOW})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].right - 13, e['rect'].bottom - 5, 8, 14), 'damage': dmg, 'color': YELLOW})
                        if ai_aggression > 0.8:
                            enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - 3, e['rect'].bottom - 8, 6, 14), 'damage': dmg + 2, 'color': RED})

                # Emit thrusters for active enemies
                vfx_engine.emit_enemy_thruster(e['rect'].centerx, e['rect'].top, e_type)

                # Collision with Player
                if e['rect'].colliderect(player_rect):
                    if e in e_list:
                        e_list.remove(e)
                    if not skills['immortal']['active'] and revive_protection_timer <= 0:
                        player_health -= (15 if e_type == 'fighter' else 25 if e_type == 'elite' else 40)
                        player_dmg_anim = 15
                        hit_snd.play()
                    for _ in range(15):
                        particles.append([e['rect'].centerx, e['rect'].centery, random.uniform(-4, 4), random.uniform(-4, 4), random.randint(3, 6), random.choice(BLAST_COLORS)])
                elif e['rect'].top > HEIGHT:
                    if e in e_list:
                        e_list.remove(e)


        # Emit player ship engine thrusters
        vfx_engine.emit_player_thruster(player_rect.centerx, player_rect.bottom)

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

                # ── ENTRY: slide boss into view ──────────────────────────────
                if boss_rect.top < 70:
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
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    
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
                # STATE: chase — Aggressive direct pursuit of player
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'chase':
                    dx = player_rect.centerx - boss_rect.centerx
                    dy = (player_rect.centery - 120) - boss_rect.centery
                    boss_rect.x += int(dx * 0.04 * b_spd)
                    boss_rect.y += max(0, int(dy * 0.015))   # Only moves down, not off-screen
                    boss_rect.y = max(60, min(HEIGHT // 2, boss_rect.y))
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    boss_angle += 2.0 * boss_sweep_dir   # Wobble rotation during chase

                    if boss_ai_timer > 150:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0

                # ─────────────────────────────────────────────────────────────
                # STATE: sweep — Full-width screen sweep, fires a curtain of bullets
                # Edge-huggers cannot avoid a sweep
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'sweep':
                    boss_rect.x += int(b_spd * 1.8 * boss_sweep_dir)
                    boss_angle += 3.0 * boss_sweep_dir   # Visual tilt during sweep

                    # Reverse at edges — full screen coverage
                    if boss_rect.right >= WIDTH:
                        boss_rect.right = WIDTH
                        boss_sweep_dir = -1
                    if boss_rect.left <= 0:
                        boss_rect.left = 0
                        boss_sweep_dir = 1

                    # Bank into the turn
                    boss_angle = -15.0 * boss_sweep_dir

                    # Fire a dense curtain every 12 frames during sweep
                    if boss_ai_timer % 12 == 0:
                        boss_eff_damage = min(current_level, 5)
                        dmg = 6 * boss_eff_damage
                        # Spread bullets across the boss width + angled to sides
                        for bx_off in [-30, -10, 10, 30]:
                            bx = boss_rect.centerx + bx_off
                            enemy_bullets.append({'rect': pygame.Rect(bx - 4, boss_rect.bottom, 8, 16),
                                                  'damage': dmg, 'color': RED, 'vx': bx_off * 0.06, 'vy': 1.0})

                    if boss_ai_timer > 240:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: corner_hunt — Boss slides to player's edge and fires
                # Specifically counters edge camping
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'corner_hunt':
                    # Mirror boss X directly to the player's corner
                    target_x = player_rect.centerx
                    dx = target_x - boss_rect.centerx
                    boss_rect.x += int(dx * 0.06 * b_spd)
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    boss_angle = math.sin(boss_ai_timer * 0.15) * 12  # Aggressive wobble

                    # Fire angled volley aimed at the player's exact position
                    if boss_ai_timer % 18 == 0:
                        boss_eff_damage = min(current_level, 5)
                        dmg = 8 * boss_eff_damage
                        bx = boss_rect.centerx
                        by = boss_rect.bottom
                        # Direct aimed shot at player
                        aim_dx = player_rect.centerx - bx
                        aim_dy = player_rect.centery - by
                        aim_dist = max(1, math.hypot(aim_dx, aim_dy))
                        norm_x = aim_dx / aim_dist
                        norm_y = aim_dy / aim_dist
                        enemy_bullets.append({
                            'rect': pygame.Rect(bx - 5, by, 10, 20),
                            'damage': dmg, 'color': (255, 80, 0),
                            'vx': norm_x * 5.0, 'vy': norm_y * 5.0
                        })

                    if boss_ai_timer > 200:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: dive — Boss dive-bombs the player's current position
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'dive':
                    if boss_ai_timer == 1:
                        # Target player X, but limit Y so it doesn't crash into player completely
                        boss_dive_target = (player_rect.centerx, min(HEIGHT // 2 + 50, player_rect.centery - 150))

                    tdx = boss_dive_target[0] - boss_rect.centerx
                    tdy = boss_dive_target[1] - boss_rect.centery
                    tdist = max(1, math.hypot(tdx, tdy))
                    dive_spd = b_spd * 2.2
                    boss_rect.x += int((tdx / tdist) * dive_spd)
                    boss_rect.y += int((tdy / tdist) * dive_spd)
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    boss_rect.y = max(60, min(HEIGHT // 2 + 50, boss_rect.y)) # Never go below this
                    boss_angle = math.sin(boss_ai_timer * 0.2) * 20   # Fast shake during dive, no full spin

                    if boss_ai_timer > 80:
                        # Fire burst on reaching target area
                        boss_eff_damage = min(current_level, 5)
                        dmg = 9 * boss_eff_damage
                        for angle_deg in range(0, 360, 45):
                            rad = math.radians(angle_deg)
                            enemy_bullets.append({
                                'rect': pygame.Rect(boss_rect.centerx - 5, boss_rect.centery, 10, 10),
                                'damage': dmg, 'color': (255, 50, 200),
                                'vx': math.cos(rad) * 4.0, 'vy': math.sin(rad) * 4.0
                            })
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: spiral — Boss fires spiral bullet pattern
                # Covers entire screen; impossible to hide in corners
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'spiral':
                    # Hold position centered
                    dx = (WIDTH // 2) - boss_rect.centerx
                    boss_rect.x += int(dx * 0.04)
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    boss_angle = math.sin(boss_ai_timer * 0.1) * 15   # Gentle wobble instead of spin

                    if boss_ai_timer % 6 == 0:
                        boss_spiral_t += 0.45
                        boss_eff_damage = min(current_level, 5)
                        dmg = 5 * boss_eff_damage
                        for arm in range(3):    # 3-arm spiral
                            arm_angle = boss_spiral_t + (arm * 2.094)   # 120° apart
                            sx = math.cos(arm_angle) * 5.0
                            sy = math.sin(arm_angle) * 5.0
                            enemy_bullets.append({
                                'rect': pygame.Rect(boss_rect.centerx - 4, boss_rect.centery, 8, 8),
                                'damage': dmg, 'color': (100, 200, 255),
                                'vx': sx, 'vy': abs(sy) + 1.0   # Always downward component
                            })

                    if boss_ai_timer > 200:
                        boss_ai_state = 'patrol'
                        boss_ai_timer = 0
                        boss_angle = 0.0

                # ─────────────────────────────────────────────────────────────
                # STATE: rage — Short burst state on phase transition
                # ─────────────────────────────────────────────────────────────
                elif boss_ai_state == 'rage':
                    # Violent left-right shaking
                    boss_rect.x += int(math.sin(boss_ai_timer * 0.5) * b_spd * 3)
                    boss_rect.x = max(0, min(WIDTH - boss_rect.width, boss_rect.x))
                    boss_angle = math.sin(boss_ai_timer * 0.8) * 18  # Violent shake

                    # Fire a dense burst during rage
                    if boss_ai_timer % 10 == 0:
                        boss_eff_damage = min(current_level, 5)
                        dmg = 7 * boss_eff_damage
                        for bx_off in range(-40, 50, 20):
                            enemy_bullets.append({'rect': pygame.Rect(boss_rect.centerx + bx_off - 4, boss_rect.bottom, 8, 16),
                                                  'damage': dmg, 'color': (255, 100, 0), 'vx': 0, 'vy': 1.0})

                    if boss_ai_timer > 100:
                        boss_ai_state = 'sweep'
                        boss_ai_timer = 0

                # ── STANDARD SHOOT for patrol/chase (non-sweep states) ───────
                if boss_ai_state in ('patrol', 'chase', 'corner_hunt'):
                    # Shoot chance & bullet count scaled by level tier
                    if current_level <= 10:
                        shoot_interval = 50
                        shots = 1
                        dmg = 8
                    elif current_level <= 30:
                        shoot_interval = 35
                        shots = 2 if boss_ai_phase > 1 else 1
                        dmg = 14
                    else:
                        shoot_interval = 22
                        shots = min(3 + (boss_ai_phase - 1), 4)
                        dmg = 20

                    if boss_ai_timer % shoot_interval == 0:
                        for s_i in range(shots):
                            ox = (s_i - (shots - 1) / 2.0) * 26
                            enemy_bullets.append({
                                'rect': pygame.Rect(int(boss_rect.centerx - 5 + ox), boss_rect.bottom, 10, 18),
                                'damage': dmg, 'color': RED, 'vx': 0, 'vy': 1.0
                            })


        # --- DRAWING & COLLISIONS ---
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
            pygame.draw.rect(screen, b_col, eb['rect'], border_radius=3)
            if eb['rect'].width > 5:
                pygame.draw.rect(screen, WHITE, eb['rect'].inflate(-2, -4), border_radius=2)

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

            if boss_active and boss_death_timer == 0:
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
                for e_list, c_val, e_type in [(fighters, 1, 'fighter'), (elites, 2, 'elite'), (heavies, 5, 'heavy')]:
                    for e in e_list[:]:
                        if b['rect'].colliderect(e['rect']):
                            e['hp'] -= 1
                            if show_damage_enabled:
                                damage_numbers.append({'x': b['rect'].centerx, 'y': b['rect'].top, 'val': 1, 'life': 20, 'col': WHITE})
                            if b in bullets:
                                bullets.remove(b)

                            if e['hp'] <= 0:
                                if e in e_list:
                                    e_list.remove(e)
                                update_coins(2 if c_val == 1 else 4 if c_val == 2 else 8)
                                kill_count += 1
                                expl_snd.play()
                                if c_val == 5:
                                    global_shake_intensity = 4.0  # Small shake for heavy enemy destruction

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
                    draw_rect.y += 3
                screen.blit(player_img, draw_rect)
                if player_fire_anim > 0 and visual_quality == 'high':
                    import pygame
                    pygame.draw.circle(screen, (255, 255, 200), (draw_rect.centerx, draw_rect.top), 8 + player_fire_anim)
                    pygame.draw.circle(screen, (255, 150, 50), (draw_rect.centerx, draw_rect.top), 4 + player_fire_anim)
        if player_dmg_anim > 0: player_dmg_anim -= 1
        if player_fire_anim > 0: player_fire_anim -= 1

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
        m_down = pygame.mouse.get_pressed()[0]
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
        m_down = pygame.mouse.get_pressed()[0]

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

    # Apply Global Screen Shake
    if screen_shake_enabled and global_shake_intensity > 0.5:
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

    pygame.display.flip()
    clock.tick(60)