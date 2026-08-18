import pygame
import random
import sys
import json
import os
import math

from jinja2.utils import htmlsafe_json_dumps

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)

from settings import *

# 🔥 SCALE ENV BACKGROUNDS (WIDTH, HEIGHT) 🔥
galaxy_bg = pygame.transform.scale(pygame.image.load("game_assets/galaxy.jpg"), (WIDTH, HEIGHT))
stars_bg = pygame.transform.scale(pygame.image.load("game_assets/stars.jpg"), (WIDTH, HEIGHT))
nebula_bg = pygame.transform.scale(pygame.image.load("game_assets/nebula.jpg"), (WIDTH, HEIGHT))
blackhole_bg = pygame.transform.scale(pygame.image.load("game_assets/blackhole.png"), (WIDTH, HEIGHT))

# Load a lock icon (Image button pe locked overlay lagane ke liye)
lock_icon = pygame.image.load("game_assets/lock.png") # PNG use karna transparency ke liye
lock_icon = pygame.transform.scale(lock_icon, (90, 90)) # adjust size as needed

# 👇 PEHLE SCREEN BANA
# Tumhara purana WIDTH aur HEIGHT wahi rehne do (shayed 800 aur 600 hai)
WIDTH = 800
HEIGHT = 600

# ==========================================
# 1. LOGO FIX (Mendhak hatane ke liye)
# ==========================================
try:
    # Tumhari 'icon.ico' file ko load kar rahe hain
    game_icon = pygame.image.load('icon.ico')
    pygame.display.set_icon(game_icon)
except:
    print("Warning: icon.ico file nahi mili!")

# ==========================================
# 2. FULL SCREEN & AUTO-SCALE FIX
# ==========================================
# pygame.SCALED jaadu ki tarah kaam karega, sab kuch auto-fit ho jayega!
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

# Game ka naam (Window Title)
pygame.display.set_caption("Crazyy Simulation")
from assets import *

# --- Variables ---
kill_count = 0
state = -1
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
music_vol = 0.5
sfx_vol = 0.7
is_dragging_music = False
is_dragging_sfx = False
mission_scroll_y = 0
is_dragging_missions = False
last_mouse_y = 0
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

load_progress = 0
load_pause_timer = 0
# Loading speed slow kar di hai taaki 9-10 seconds lage
load_speed = random.uniform(1.2, 1.4)
stutter_points = [60, 150, 220, 280]  # Loading rukne ke points

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
asteroid_img = pygame.image.load("game_assets/asteroid.png").convert_alpha()

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
STATE_LOADING = -1
STATE_MAIN_MENU = 0
STATE_ENV_SELECT = 20
STATE_LEVEL_SELECT = 1
state = STATE_LOADING

# --- Colors Definition ---
BRAND_RED = (200, 20, 20)
BRAND_GOLD = (230, 190, 80)
BRAND_GLOW = (255, 100, 100, 100)

# --- BRANDING ANIMATION VARIABLES ---
state = -2
anim_time = pygame.time.get_ticks()
anim_duration = 2000
anim_played = False
anim_flash_alpha = 0
anim_logo_scale = 1.0
anim_text_alpha = 0
anim_text_y = HEIGHT + 50
anim_shine_x = -300
last_frame_ticks = pygame.time.get_ticks()

brand_logo_placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
pygame.draw.circle(brand_logo_placeholder, BRAND_RED, (100, 100), 80)
pygame.draw.polygon(brand_logo_placeholder, WHITE, [(50,150), (100,50), (150,150)])

brand_text_placeholder = pygame.font.SysFont("Impact", 80).render("TEXT", True, WHITE)
brand_text_y_target = 480

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
        "control_type": control_type,
        "music_vol": music_vol,
        "sfx_vol": sfx_vol
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)


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
    if 1 <= level <= 10:
        prices = [100, 200, 400, 800, 1000]
        # Agar revives_done list ke andar hai, toh wo price do, warna 1000 ke baad fix ya aur badhana hai
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
        # 500 se start, aur har baar double (500, 1000, 2000, 4000...)
        return 500 * (2 ** revives_done)

    return 100  # Fallback safety ke liye

def load_game():
    global music_vol, sfx_vol, tap_snd
    global total_coins, unlocked_hp, hp_step, unlocked_speed, speed_step
    global unlocked_bullets, bullet_step, max_galaxy_level, max_nebula_level, max_blackhole_level, control_type
    global env2_unlocked, env3_unlocked

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
                max_galaxy_level = 40
                max_nebula_level = 40
                max_blackhole_level = 40
                
                env2_unlocked = True
                env3_unlocked = True
                
                control_type = data.get("control_type", 'PC')
                if not control_type:
                    control_type = 'PC'
                music_vol = data.get("music_vol", 0.5)
                sfx_vol = data.get("sfx_vol", 0.7)
                pygame.mixer.music.set_volume(music_vol)
                shoot_snd.set_volume(sfx_vol)
                game_won_snd.set_volume(sfx_vol)
                game_loose_snd.set_volume(sfx_vol)
                tap_snd = pygame.mixer.Sound("game_assets/tap.mp3")
                tap_snd.set_volume(sfx_vol)
                boss_expl_snd.set_volume(sfx_vol)
                expl_snd.set_volume(sfx_vol)
                hit_snd.set_volume(sfx_vol)
        except Exception as e:
            print("Save file load error:", e)


def reset_level_logic(level):
    global player_health, fighters, elites, heavies, bullets, enemy_bullets, achievements, particles, level_coins
    global boss_active, boss_arriving, boss_warning_timer, boss_defeated_timer
    global boss_hp, boss_max_hp, boss_death_timer, current_level, boss_rect, kill_count
    global current_boss_img
    global win_snd_played, loose_snd_played
    global blackhole_alert_active
    win_snd_played = False
    loose_snd_played = False
    blackhole_alert_active = (current_selected_env == 3)
    global galaxy_bg_y
    galaxy_bg_y = 0.0
    global revives_done_this_level
    revives_done_this_level = 0

    current_level = level
    kill_count = 0
    player_health = unlocked_hp
    player_rect.center = (WIDTH // 2, HEIGHT - 60)
    fighters, elites, heavies, bullets, enemy_bullets, achievements, particles = [], [], [], [], [], [], []
    level_coins = 0

    reset_match()

    boss_active = False
    boss_arriving = False
    boss_warning_timer = 0
    boss_defeated_timer = 0
    boss_death_timer = 0

    boss_max_hp = 250 + (current_level * 100)
    boss_hp = boss_max_hp

    # ==========================================
    # 🔥 BOSS SCALING & IMAGE LOGIC FIXED 🔥
    # ==========================================
    # 1. Calculate tier (1-8) based on current_level (1-40)
    # Lvl 1-5 -> Tier 1, Lvl 6-10 -> Tier 2, ..., Lvl 36-40 -> Tier 8
    boss_tier = ((current_level - 1) // 5) + 1
    boss_tier = min(boss_tier, 8)  # Cap at tier 8

    # 2. Get pre-scaled boss image based on calculated tier
    current_boss_img = boss_surfs.get(boss_tier, boss_surfs[1])

    # 3. Create Hitbox (Rect) exactly matching the current pre-scaled image size
    boss_rect = current_boss_img.get_rect(center=(WIDTH // 2, -150))

    for s in skills: skills[s]['active'] = False

def update_coins(amount):
    global total_coins, level_coins
    total_coins += amount
    level_coins += amount
    save_game()

# --- SAVE/LOAD SYSTEM ke niche ---
def reset_match():
    global asteroids_spawned, asteroids_spawned_in_match
    asteroids_spawned = 0
    asteroids_spawned_in_match = 0
    asteroid_group.empty() # Saare purane asteroids saaf ho jayenge

# --- Anti-Overlap Logic ---
def check_enemy_spawn(new_rect, all_enemies):
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
        pygame.mixer.music.play(0)  # 0 ka matlab sirf ek baar play hoga
        current_bgm = "loading"
    elif target_bgm == "fast" and current_bgm != "fast":
        pygame.mixer.music.load(game_bgm_fast)
        pygame.mixer.music.play(-1) # -1 ka matlab loop mein play hoga
        current_bgm = "fast"
    elif target_bgm == "main" and current_bgm != "main":
        pygame.mixer.music.load(game_bgm_main)
        pygame.mixer.music.play(-1) # -1 ka matlab loop mein play hoga
        current_bgm = "main"
    # ==========================================

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: m_c = True
            if event.button == 4: level_scroll_y = min(0, level_scroll_y + 30)
            if event.button == 5: level_scroll_y = max(-850, level_scroll_y - 30)

    # ==========================================
    # 🔥 3. BRANDING ANIMATION (STATE -2) BEST QUALITY 🔥
    # ==========================================
    if state == -2:
        # Start sound only once
        if not anim_played:
            # Sound "game_assets/tap.mp3" reuse kar raha hoon, baad mein load_snd kar lena Professional startup sound
            tap_snd.play()
            anim_played = True

        # Calculate animation timeline
        anim_progress = pygame.time.get_ticks() - anim_time

        # --- PHASE 1: FLASH & LOGO ENTRY (0s - 0.5s) ---
        if 0 < anim_progress < 500:
            # FLASH EFFECT (Fades out over 0.5s)
            flash_alpha = int(255 - (anim_progress / 500 * 255))
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill(BRAND_RED)
            flash_surf.set_alpha(max(0, flash_alpha))
            screen.blit(flash_surf, (0, 0))

            # LOGO ENTRY (Scale down and Fade In)
            entry_logo_surf = pygame.transform.scale(brand_logo_placeholder,
                                                         (int(200 * max(0.2, anim_logo_scale)),
                                                          int(200 * max(0.2, anim_logo_scale))))
            entry_logo_rect = entry_logo_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(entry_logo_surf, entry_logo_rect)

            # Smoothly change variables using Delta Time (dt)
            anim_logo_scale = max(0.1, anim_logo_scale - 0.03 * dt)

            # --- PHASE 2: LOGO HOLD & TEXT ENTRY (0.5s - 1.2s) ---
        elif 500 <= anim_progress < 1200:
            # LOGO HOLD (Normal size)
            final_logo_rect = brand_logo_placeholder.get_rect(center=(WIDTH // 2, 280))  # Upper position
            screen.blit(brand_logo_placeholder, final_logo_rect)

            # TEXT ENTRY (Fades In and moves Up)
            current_brand_text = pygame.font.SysFont("Impact", 80).render("BIKRAM", True, BRAND_GOLD)
            current_brand_text.set_alpha(min(255, anim_text_alpha))
            text_rect = current_brand_text.get_rect(center=(WIDTH // 2, int(anim_text_y)))
            screen.blit(current_brand_text, text_rect)

            # Smooth movement logic using dt
            anim_text_alpha = min(255, anim_text_alpha + 15 * dt)
            anim_text_y = max(brand_text_y_target, anim_text_y - 8 * dt)

        # --- PHASE 3: TEXT GLOW & SWEEP & FADE OUT (1.2s - 2.0s) ---
        elif 1200 <= anim_progress < anim_duration:
            # LOGO HOLD (Upper position)
            final_logo_rect = brand_logo_placeholder.get_rect(center=(WIDTH // 2, 280))
            screen.blit(brand_logo_placeholder, final_logo_rect)

            # TEXT HOLD (Glowing Gold color)
            current_brand_text = pygame.font.SysFont("Impact", 80).render("BIKRAM", True, BRAND_GOLD)
            text_rect = current_brand_text.get_rect(center=(WIDTH // 2, brand_text_y_target))
            screen.blit(current_brand_text, text_rect)

            # --- SHINE SWEEP EFFECT ---
            # Shiny reddish/white sweep passing over text
            shine_surf = pygame.Surface((300, 100), pygame.SRCALPHA)
            pygame.draw.rect(shine_surf, (255, 255, 255, 150), (0, 0, 150, 100))  # Simple shininess structure
            shine_surf.set_alpha(100)  # transparency

            screen.set_clip(text_rect)  # Only draw shine within text boundaries
            screen.blit(shine_surf, (anim_shine_x, brand_text_y_target - 50))
            screen.set_clip(None)  # Remove clipping

            # Move shine sweep using dt
            anim_shine_x += 18 * dt

            # --- TRANSITION TO LOADING SCREEN ---
        if anim_progress >= anim_duration:
            state = -1  # Go to loading state
            load_progress = 0  # reset loading tracker

    # ==========================
    # LOADING SCREEN (STATE -1)
    # ==========================

    if state == -1:
        draw_text("CRAZYY SIMULATION", FONT_TITLE, CYAN, 400, 250)
        pygame.draw.rect(screen, LIGHT_GRAY, (250, 350, 300, 20), border_radius=10)

        is_stuttering = False
        for sp in stutter_points:
            if int(load_progress) == sp and load_pause_timer < 80:
                load_pause_timer += 1
                is_stuttering = True
                break
        if not is_stuttering:
            load_progress += load_speed
            load_pause_timer = 0

        final_w = min(300, int(load_progress))
        pygame.draw.rect(screen, GREEN, (250, 350, final_w, 20), border_radius=min(10, final_w // 2))
        draw_text("Loading...", FONT_SMALL, WHITE, 400, 390)
        if load_progress >= 300:
            state = 0

    # ==========================
    # MAIN MENU (STATE 0)
    # ==========================
    elif state == 0:
        screen.blit(menu_bg, (0, 0))
        
        # Add a subtle dark overlay for better text readability
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        draw_text("CRAZYY SIMULATION", FONT_TITLE, CYAN, 400, 80)
        
        # Modern Coin display in a sleek pill shape
        coin_bg = pygame.Rect(320, 140, 160, 40)
        pygame.draw.rect(screen, (20, 20, 30, 180), coin_bg, border_radius=20)
        pygame.draw.rect(screen, YELLOW, coin_bg, width=2, border_radius=20)
        screen.blit(coin_icon, (330, 140))
        draw_text(f"{total_coins}", FONT_UI, YELLOW, x = 410, y = 158)

        menu_btns = [
            ("MISSIONS", BLUE, 220, STATE_ENV_SELECT),
            ("STORE", MAGENTA, 310, 6),
            ("SETTINGS", ORANGE, 400, 9),
            ("QUIT", RED, 490, 0)
        ]

        mx, my = pygame.mouse.get_pos()

        for txt, col, y, target in menu_btns:
            btn_rect = pygame.Rect(270, y, 260, 70)
            is_hover = btn_rect.collidepoint(mx, my)

            # Use the new draw_button function
            draw_button(screen, txt, FONT_UI, WHITE, btn_rect, col, is_hover, outline_color=CYAN)

            # --- Click Logic ---
            if m_c and is_hover:
                if txt == "QUIT":
                    running = False
                elif (txt == "MISSIONS" or txt == "STORE") and control_type is None:
                    tap_snd.play()
                    win_snd_played = False
                    loose_snd_played = False
                    show_settings_warning = True
                else:
                    tap_snd.play()
                    state = target

        # WARNING POPUP DRAWING
        if show_settings_warning:
            overlay_w = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay_w.fill((0, 0, 0, 210))
            screen.blit(overlay_w, (0, 0))

            warn_rect = pygame.Rect(130, 180, 540, 240)
            draw_panel(screen, warn_rect, alpha=245, bg_color=(20, 25, 35), border_color=CYAN, border_width=3, border_radius=20)

            draw_text("CONTROL CONFIGURATION", FONT_MSG, CYAN, 400, 225)
            draw_text("Select your preferred device (PC / Mobile) in Settings.", FONT_SMALL, WHITE, 400, 275)
            draw_text("Defaulting to PC (WASD + Space auto-fire).", FONT_SMALL, YELLOW, 400, 305)

            btn_set = pygame.Rect(170, 345, 210, 50)
            btn_ok = pygame.Rect(420, 345, 210, 50)

            is_h_set = btn_set.collidepoint(mx, my)
            is_h_ok = btn_ok.collidepoint(mx, my)

            draw_button(screen, "SETTINGS", FONT_UI, WHITE, btn_set, ORANGE, is_h_set)
            draw_button(screen, "CONTINUE (PC)", FONT_UI, WHITE, btn_ok, GREEN, is_h_ok)

            if m_c:
                if is_h_set:
                    tap_snd.play()
                    show_settings_warning = False
                    state = 9
                elif is_h_ok:
                    tap_snd.play()
                    control_type = 'PC'
                    show_settings_warning = False


    # ==========================
    # 🔥 1. SELECT ENVIRONMENT (NEW STATE 20) 🔥
    # ==========================
    elif state == STATE_ENV_SELECT:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))  # Darker for emphasis
        screen.blit(overlay, (0, 0))

        draw_text("SELECT ENVIRONMENT", FONT_TITLE, CYAN, 400, 80)

        mx, my = pygame.mouse.get_pos()

        btn_env1 = pygame.Rect(100, 180, 280, 160)
        btn_env2 = pygame.Rect(420, 180, 280, 160)
        btn_env3 = pygame.Rect(260, 360, 280, 160)

        is_h_e1 = btn_env1.collidepoint(mx, my)
        is_h_e2 = btn_env2.collidepoint(mx, my) and env2_unlocked
        is_h_e3 = btn_env3.collidepoint(mx, my) and env3_unlocked

        env_col_1 = (0, 80, 200)
        env_col_2 = (150, 40, 200) if env2_unlocked else (50, 50, 50)
        env_col_3 = (200, 40, 40) if env3_unlocked else (50, 50, 50)

        # Draw Base Panels
        draw_button(screen, "", FONT_UI, WHITE, btn_env1, env_col_1, is_h_e1, outline_color=GREEN if current_selected_env == 1 else CYAN)
        draw_button(screen, "", FONT_UI, WHITE, btn_env2, env_col_2, is_h_e2, outline_color=GREEN if current_selected_env == 2 else CYAN)
        draw_button(screen, "", FONT_UI, WHITE, btn_env3, env_col_3, is_h_e3, outline_color=GREEN if current_selected_env == 3 else CYAN)

        # Texts
        draw_text("GALAXY", FONT_UI, WHITE, btn_env1.centerx, btn_env1.centery - 20)
        draw_text("40 Levels", FONT_SMALL, CYAN, btn_env1.centerx, btn_env1.centery + 20)

        t_col2 = WHITE if env2_unlocked else LIGHT_GRAY
        draw_text("NEBULA", FONT_UI, t_col2, btn_env2.centerx, btn_env2.centery - 20)
        draw_text("Unlocked" if env2_unlocked else "🔒 Locked", FONT_SMALL, CYAN if env2_unlocked else RED, btn_env2.centerx, btn_env2.centery + 20)

        t_col3 = WHITE if env3_unlocked else LIGHT_GRAY
        draw_text("BLACKHOLE", FONT_UI, t_col3, btn_env3.centerx, btn_env3.centery - 20)
        draw_text("Unlocked" if env3_unlocked else "🔒 Locked", FONT_SMALL, CYAN if env3_unlocked else RED, btn_env3.centerx, btn_env3.centery + 20)

        if not env2_unlocked: screen.blit(lock_icon, (btn_env2.centerx - 45, btn_env2.centery - 45))
        if not env3_unlocked: screen.blit(lock_icon, (btn_env3.centerx - 45, btn_env3.centery - 45))

        # --- BACK BUTTON ---
        btn_back = pygame.Rect(270, 540, 260, 50)
        is_h_back = btn_back.collidepoint(mx, my)
        draw_button(screen, "BACK TO MENU", FONT_UI, WHITE, btn_back, RED, is_h_back)

        if m_c:
            if is_h_e1:
                tap_snd.play()
                current_selected_env = 1
                state = STATE_LEVEL_SELECT
            elif is_h_e2:
                tap_snd.play()
                current_selected_env = 2
                state = STATE_LEVEL_SELECT
            elif is_h_e3:
                tap_snd.play()
                current_selected_env = 3
                state = STATE_LEVEL_SELECT
            elif is_h_back:
                tap_snd.play()
                state = 0

    # ==========================
    # SETTINGS MENU (STATE 9, 11, 12)
    # ==========================
    elif state == 9:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        draw_text("GAME SETTINGS", FONT_TITLE, CYAN, 400, 60)

        # Device Selection Cards
        btn_mob = pygame.Rect(150, 140, 200, 100)
        btn_pc = pygame.Rect(450, 140, 200, 100)
        
        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]
        
        is_h_mob = btn_mob.collidepoint(mx, my)
        is_h_pc = btn_pc.collidepoint(mx, my)

        draw_button(screen, "", FONT_UI, WHITE, btn_mob, (30, 80, 150) if control_type != 'MOBILE' else (0, 200, 255), is_h_mob)
        draw_text("MOBILE", FONT_UI, WHITE, 250, 175)
        draw_text("CONTROL", FONT_SMALL, CYAN if control_type == 'MOBILE' else LIGHT_GRAY, 250, 205)

        draw_button(screen, "", FONT_UI, WHITE, btn_pc, (150, 30, 80) if control_type != 'PC' else (0, 200, 255), is_h_pc)
        draw_text("PC", FONT_UI, WHITE, 550, 175)
        draw_text("CONTROL", FONT_SMALL, CYAN if control_type == 'PC' else LIGHT_GRAY, 550, 205)

        # --- SLIDERS LOGIC ---
        slider_y_pos = [320, 420]
        slider_labels = ["MUSIC VOLUME", "SOUND EFFECTS"]
        current_vols = [music_vol, sfx_vol]

        for i in range(2):
            draw_text(slider_labels[i], FONT_SMALL, WHITE, 400, slider_y_pos[i] - 30)
            s_rect = pygame.Rect(200, slider_y_pos[i], 400, 20)  # Thinner, sleeker bar
            pygame.draw.rect(screen, (30, 30, 40), s_rect, border_radius=10)

            # Gradient/Neon Fill bar
            fill_w = int(current_vols[i] * 400)
            if fill_w > 0:
                pygame.draw.rect(screen, CYAN, (200, slider_y_pos[i], fill_w, 20), border_radius=10)

            # Percentage text
            draw_text(f"{int(current_vols[i] * 100)}%", FONT_SMALL, WHITE if fill_w < 200 else BLACK, 400, slider_y_pos[i] + 10)

            # Modern Slider Handle
            handle_x = 200 + fill_w
            pygame.draw.circle(screen, WHITE, (handle_x, slider_y_pos[i] + 10), 12)
            pygame.draw.circle(screen, CYAN, (handle_x, slider_y_pos[i] + 10), 6)

            # Interaction
            if m_down and s_rect.inflate(20, 40).collidepoint(mx, my):
                new_val = max(0, min(1, (mx - 200) / 400))
                if i == 0:
                    music_vol = new_val
                    pygame.mixer.music.set_volume(music_vol)
                else:
                    sfx_vol = new_val
                    shoot_snd.set_volume(sfx_vol)
                    game_won_snd.set_volume(sfx_vol)
                    game_loose_snd.set_volume(sfx_vol)
                    tap_snd.set_volume(sfx_vol)
                    boss_expl_snd.set_volume(sfx_vol)
                    expl_snd.set_volume(sfx_vol)
                    hit_snd.set_volume(sfx_vol)

        btn_back = pygame.Rect(325, 520, 150, 50)
        is_h_back = btn_back.collidepoint(mx, my)
        draw_button(screen, "BACK", FONT_UI, WHITE, btn_back, RED, is_h_back)

        if m_c:
            if is_h_mob:
                tap_snd.play()
                control_type = 'MOBILE'
                state = 12
                save_game()
            elif is_h_pc:
                tap_snd.play()
                control_type = 'PC'
                state = 11
                save_game()
            elif is_h_back:
                tap_snd.play()
                if settings_from_pause:
                    state = 10
                    settings_from_pause = False
                else:
                    state = 0
                save_game()

    # ==========================
    # PC CONTROLS INFO (STATE 11)
    # ==========================
    elif state == 11:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        info_box = pygame.Rect(100, 80, 600, 440)
        draw_panel(screen, info_box, alpha=245, border_color=MAGENTA, border_width=3, border_radius=20)

        draw_text("PC FLIGHT COMMANDS", FONT_MSG, CYAN, 400, 125)

        instructions = [
            ("• Flight Navigation:", "Use [W, A, S, D] or [Arrow Keys] for 2D maneuvering & dodging."),
            ("• Weapons Barrage:", "Hold [SPACEBAR] or [Left Mouse Button] for rapid auto-fire."),
            ("• Tactical Powerups:", "Collect [S] for Energy Shield & [2X] for Dual Laser Spread."),
            ("• Singularity Hazard:", "In Black Hole environments, resist gravitational pull with thrusters!")
        ]

        for idx, (head, body) in enumerate(instructions):
            draw_text(head, FONT_SMALL, YELLOW, 400, 180 + idx * 60)
            draw_text(body, FONT_SMALL, WHITE, 400, 205 + idx * 60)

        mx, my = pygame.mouse.get_pos()
        btn_ok = pygame.Rect(300, 435, 200, 50)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_button(screen, "GOT IT", FONT_UI, WHITE, btn_ok, GREEN, is_h_ok)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9

    # ==========================
    # MOBILE CONTROLS INFO (STATE 12)
    # ==========================
    elif state == 12:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        info_box = pygame.Rect(100, 80, 600, 440)
        draw_panel(screen, info_box, alpha=245, border_color=BLUE, border_width=3, border_radius=20)

        draw_text("MOBILE TOUCH COMMANDS", FONT_MSG, CYAN, 400, 125)

        m_instructions = [
            ("• Touch Navigation:", "Slide your finger anywhere on screen to steer your starship."),
            ("• Auto-Firing:", "Rapid pulse cannons automatically fire while touching screen."),
            ("• Tactical Powerups:", "Touch [S] Shield and [2X] Double Shot floating energy orbs."),
            ("• Singularity Hazard:", "Steer away from the black hole center to avoid collapse!")
        ]

        for idx, (head, body) in enumerate(m_instructions):
            draw_text(head, FONT_SMALL, YELLOW, 400, 180 + idx * 60)
            draw_text(body, FONT_SMALL, WHITE, 400, 205 + idx * 60)

        mx, my = pygame.mouse.get_pos()
        btn_ok = pygame.Rect(300, 435, 200, 50)
        is_h_ok = btn_ok.collidepoint(mx, my)
        draw_button(screen, "GOT IT", FONT_UI, WHITE, btn_ok, GREEN, is_h_ok)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9

    # ==========================
    # MISSIONS / LEVEL SELECT (STATE 1)
    # ==========================
    elif state == STATE_LEVEL_SELECT:  # Yaani state == 1
        if current_selected_env == 1:
            screen.blit(galaxy_bg, (0, 0))
        elif current_selected_env == 2:
            screen.blit(nebula_bg, (0, 0))
        elif current_selected_env == 3:
            screen.blit(blackhole_bg, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        draw_text("MISSIONS", FONT_TITLE, CYAN, 400, 60)

        box_rect = pygame.Rect(120, 120, 560, 360)
        draw_panel(screen, box_rect, alpha=200, border_color=MAGENTA)

        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        if m_down and box_rect.collidepoint(mx, my):
            if not is_dragging_missions:
                is_dragging_missions = True
                last_mouse_y = my
            else:
                dy = my - last_mouse_y
                level_scroll_y += dy
                last_mouse_y = my
        else:
            is_dragging_missions = False

        level_scroll_y = max(-850, min(0, level_scroll_y))
        screen.set_clip(box_rect.inflate(-10, -10))

        env_max = 40  # Temporarily fully unlocked for all envs
        
        for i in range(1, 41):
            lx = 150 + ((i - 1) % 5) * 100
            ly = 140 + ((i - 1) // 5) * 100 + level_scroll_y

            lvl_rect = pygame.Rect(lx, ly, 80, 80)
            is_u = i <= env_max
            is_h = False
            
            if 100 < ly < 480:
                is_h = lvl_rect.collidepoint(mx, my) and is_u and box_rect.collidepoint(mx, my)

                # Modern Node button
                draw_button(screen, str(i), FONT_TITLE, WHITE if is_u else LIGHT_GRAY, lvl_rect, BLUE if is_u else (30, 30, 30), is_h, border_radius=20, outline_color=CYAN)

                if m_c and is_h:
                    tap_snd.play()
                    selected_level = i
                    state = 2
        screen.set_clip(None)

        # --- BACK BUTTON ---
        btn_back = pygame.Rect(270, 500, 260, 60)
        is_h_b = btn_back.collidepoint(mx, my)
        draw_button(screen, "BACK", FONT_UI, WHITE, btn_back, RED, is_h_b)

        if m_c and is_h_b:
            tap_snd.play()
            state = STATE_ENV_SELECT

    # ==========================
    # STORE (STATE 6, 7, 8)
    # ==========================
    elif state == 6:
        screen.blit(menu_bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        draw_text("SPACE STORE", FONT_TITLE, CYAN, 400, 70)
        
        coin_bg = pygame.Rect(320, 120, 160, 40)
        pygame.draw.rect(screen, (20, 20, 30, 180), coin_bg, border_radius=20)
        pygame.draw.rect(screen, YELLOW, coin_bg, width=2, border_radius=20)
        screen.blit(coin_icon, (330, 120))
        draw_text(f"{total_coins}", FONT_UI, YELLOW, x=410, y=138)
        
        items = [("Max HP", GREEN, 100, 'hp', unlocked_hp), ("Speed", ORANGE, 310, 'sp', unlocked_speed), ("Bullets", RED, 520, 'pb', unlocked_bullets)]
        mx, my = pygame.mouse.get_pos()
        
        for name, col, x, key, curr_val in items:
            btn = pygame.Rect(x, 200, 180, 140)
            is_h = btn.collidepoint(mx, my)
            draw_button(screen, "", FONT_UI, WHITE, btn, (40, 40, 50), is_h, outline_color=col)
            draw_text(name, FONT_UI, col, x + 90, 240)
            draw_text(f"Lvl {curr_val}", FONT_SMALL, WHITE, x + 90, 290)
            
            if m_c and is_h:
                tap_snd.play()
                store_selection = key

        if store_selection:
            # Blur overlay for popup
            pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pop_overlay.fill((0, 0, 0, 200))
            screen.blit(pop_overlay, (0, 0))
            
            box_info = pygame.Rect(150, 180, 500, 260)
            draw_panel(screen, box_info, alpha=240, border_color=CYAN)

            desc = {"hp": "Increase Total HP Capacity", "sp": "Boost Ship Navigation Speed", "pb": "Unlock Multi-Bullet Fire"}[store_selection]
            if store_selection == 'hp':
                cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
            elif store_selection == 'sp':
                cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
            else:
                cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"

            draw_text("ITEM DETAILS", FONT_UI, YELLOW, 400, 220)
            draw_text(desc, FONT_SMALL, WHITE, 400, 270)
            draw_text(f"COST: {cost} COINS", FONT_UI, GREEN if cost != "MAX" and total_coins >= (cost if cost != "MAX" else 0) else RED, 400, 330)

            btn_st_bk = pygame.Rect(180, 370, 150, 50)
            btn_buy = pygame.Rect(470, 370, 150, 50)
            
            is_h_bk = btn_st_bk.collidepoint(mx, my)
            is_h_buy = btn_buy.collidepoint(mx, my)
            
            draw_button(screen, "BACK", FONT_SMALL, WHITE, btn_st_bk, RED, is_h_bk)
            if cost != "MAX":
                draw_button(screen, "BUY NOW", FONT_SMALL, WHITE, btn_buy, GREEN, is_h_buy)

            if m_c:
                if is_h_bk:
                    tap_snd.play()
                    store_selection = None
                elif is_h_buy and cost != "MAX":
                    if total_coins >= cost:
                        state = 7
                    else:
                        tap_snd.play()
                        state = 8

        if not store_selection:
            btn_b_m = pygame.Rect(270, 450, 260, 60)
            is_h_bm = btn_b_m.collidepoint(mx, my)
            draw_button(screen, "BACK", FONT_UI, WHITE, btn_b_m, RED, is_h_bm)
            if m_c and is_h_bm:
                tap_snd.play()
                state = 0

    elif state == 7:
        pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_overlay.fill((0, 0, 0, 200))
        screen.blit(pop_overlay, (0, 0))
        
        box = pygame.Rect(200, 200, 400, 200)
        draw_panel(screen, box, alpha=240, border_color=YELLOW)
        
        draw_text("Confirm Purchase?", FONT_UI, WHITE, 400, 260)
        b_n, b_y = pygame.Rect(230, 320, 120, 50), pygame.Rect(450, 320, 120, 50)
        
        mx, my = pygame.mouse.get_pos()
        is_h_n = b_n.collidepoint(mx, my)
        is_h_y = b_y.collidepoint(mx, my)
        
        draw_button(screen, "No", FONT_UI, WHITE, b_n, RED, is_h_n)
        draw_button(screen, "Yes", FONT_UI, WHITE, b_y, GREEN, is_h_y)
        
        if m_c:
            if is_h_n:
                tap_snd.play()
                state = 6
            if is_h_y:
                cost = hp_costs[hp_step] if store_selection == 'hp' else speed_costs[speed_step] if store_selection == 'sp' else bullet_costs[bullet_step]
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

    elif state == 8:
        pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_overlay.fill((0, 0, 0, 200))
        screen.blit(pop_overlay, (0, 0))
        
        box = pygame.Rect(200, 200, 400, 220)
        draw_panel(screen, box, alpha=240, border_color=RED)
        
        draw_text("Not Enough Coins!", FONT_UI, RED, 400, 250)
        b_b = pygame.Rect(230, 330, 120, 50)
        b_t = pygame.Rect(450, 330, 120, 50)
        
        mx, my = pygame.mouse.get_pos()
        is_h_b = b_b.collidepoint(mx, my)
        is_h_t = b_t.collidepoint(mx, my)
        
        draw_button(screen, "BACK", FONT_SMALL, WHITE, b_b, RED, is_h_b)
        draw_button(screen, "TOP UP", FONT_SMALL, BLACK, b_t, YELLOW, is_h_t)
        
        if m_c and is_h_b:
            tap_snd.play()
            state = 6

    # ==========================
    # MISSION INFO (STATE 2)
    # ==========================
    elif state == 2:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(160, 150, 480, 300)
        draw_panel(screen, box_rect, alpha=240, border_color=CYAN)

        env_names = {1: "GALAXY SECTOR", 2: "NEBULA ZONE", 3: "BLACKHOLE HORIZON"}
        curr_env_title = env_names.get(current_selected_env, "GALAXY SECTOR")

        draw_text(curr_env_title, FONT_UI, CYAN, 400, 195)
        draw_text(f"MISSION {selected_level}", FONT_MSG, YELLOW, 400, 240)

        boss_kill_reqs = {1: 15, 2: 20, 3: 25, 4: 35, 5: 45, 6: 60, 7: 75, 8: 90, 9: 105, 10: 120}
        req_k = min(200, 120 + (selected_level - 10) * 4) if selected_level >= 11 else boss_kill_reqs.get(selected_level, 25)
        draw_text(f"Eliminate {req_k} Enemies to summon Sector Boss", FONT_SMALL, WHITE, 400, 295)

        b_r = pygame.Rect(190, 360, 190, 55)
        b_a = pygame.Rect(420, 360, 190, 55)

        mx, my = pygame.mouse.get_pos()
        is_h_r = b_r.collidepoint(mx, my)
        is_h_a = b_a.collidepoint(mx, my)

        draw_button(screen, "LAUNCH", FONT_UI, WHITE, b_r, GREEN, is_h_r)
        draw_button(screen, "BACK", FONT_UI, WHITE, b_a, RED, is_h_a)

        if m_c:
            if is_h_r:
                tap_snd.play()
                reset_level_logic(selected_level)
                state = 3
            elif is_h_a:
                tap_snd.play()
                state = 1

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
        # ⚠ BLACKHOLE STARTING WARNING POPUP (FIXED SIZING) ⚠
        # ----------------------------------------------------
        if blackhole_alert_active:
            screen.blit(blackhole_bg, (0, 0))

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            screen.blit(overlay, (0, 0))

            alert_box = pygame.Rect(70, 75, 660, 450)
            draw_panel(screen, alert_box, alpha=245, bg_color=(25, 12, 30), border_color=(255, 60, 120), border_width=3, border_radius=22)

            draw_text("⚠ GRAVITATIONAL HAZARD ⚠", FONT_MSG, (255, 60, 80), 400, 125)
            draw_text("BLACK HOLE SINGULARITY DETECTED", FONT_UI, CYAN, 400, 175)

            warnings = [
                ("• Extreme Gravity:", "All ships & asteroids are continuously dragged toward the center!"),
                ("• Relativistic Time Dilation:", "All ship navigation, bullets, and combat speeds are slowed down."),
                ("• Singularity Hazard:", "Getting sucked to the center will shrink & crush your ship into oblivion!"),
                ("• Active Thrusters:", "Use [W, A, S, D] / [Arrows] with quick reflexes to resist the collapse!")
            ]

            for idx, (head, body) in enumerate(warnings):
                draw_text(head, FONT_SMALL, (255, 220, 100) if idx == 2 else YELLOW, 400, 225 + idx * 52)
                draw_text(body, FONT_SMALL, WHITE, 400, 247 + idx * 52)

            btn_engage = pygame.Rect(260, 445, 280, 50)
            is_h_eng = btn_engage.collidepoint(mx, my)
            draw_button(screen, "ENGAGE THRUSTERS", FONT_UI, WHITE, btn_engage, (190, 30, 90), is_h_eng, outline_color=CYAN)

            if m_c and is_h_eng:
                tap_snd.play()
                blackhole_alert_active = False

            pygame.display.flip()
            clock.tick(60)
            continue

        # ----------------------------------------------------
        # RELATIVISTIC ENVIRONMENT MULTIPLIER & SETTINGS
        # ----------------------------------------------------
        is_blackhole = (current_selected_env == 3)
        env_speed_mult = 0.68 if is_blackhole else 1.0
        eff_player_speed = max(3.0, unlocked_speed * env_speed_mult)

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
                if player_rect.centerx < mx - 5 and player_rect.right < WIDTH:
                    player_rect.x += eff_player_speed
                elif player_rect.centerx > mx + 5 and player_rect.left > 0:
                    player_rect.x -= eff_player_speed

                if player_rect.centery < my - 5 and player_rect.bottom < HEIGHT - 10:
                    player_rect.y += eff_player_speed
                elif player_rect.centery > my + 5 and player_rect.top > 80:
                    player_rect.y -= eff_player_speed

                if fire_cooldown <= 0:
                    is_firing = True
                    fire_cooldown = 9 if is_blackhole else (8 if current_level <= 15 else 6)

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
        if m_c and is_h_pause:
            tap_snd.play()
            state = 10

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

        # Boss Logic
        if boss_active:
            if boss_death_timer > 0:
                boss_death_timer -= 1
                if boss_death_timer % 4 == 0:
                    for _ in range(30):
                        p_color = random.choice(BLAST_COLORS)
                        particles.append([boss_rect.centerx + random.randint(-40, 40), boss_rect.centery + random.randint(-30, 30), random.uniform(-8, 8), random.uniform(-8, 8), random.randint(5, 14), p_color])
                if boss_death_timer == 1:
                    boss_active = False
                    boss_defeated_timer = 120
                    boss_expl_snd.play()
                    if current_selected_env == 1 and current_level == max_galaxy_level and max_galaxy_level < 40:
                        max_galaxy_level += 1
                        env2_unlocked = True
                    elif current_selected_env == 2 and current_level == max_nebula_level and max_nebula_level < 40:
                        max_nebula_level += 1
                        env3_unlocked = True
                    elif current_selected_env == 3 and current_level == max_blackhole_level and max_blackhole_level < 40:
                        max_blackhole_level += 1
                    save_game()
            else:
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
                        boss_death_timer = 150
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
                                # Beginner-friendly generous coin drops
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
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(180, 140, 440, 360)
        draw_panel(screen, box, alpha=240, border_color=CYAN)
        draw_text("GAME PAUSED", FONT_TITLE, CYAN, 400, 190)

        btn_resume = pygame.Rect(220, 250, 160, 55)
        btn_restart = pygame.Rect(420, 250, 160, 55)
        btn_settings = pygame.Rect(220, 330, 160, 55)
        btn_menu = pygame.Rect(420, 330, 160, 55)

        mx, my = pygame.mouse.get_pos()
        is_h_p = btn_resume.collidepoint(mx, my)
        is_h_r = btn_restart.collidepoint(mx, my)
        is_h_s = btn_settings.collidepoint(mx, my)
        is_h_m = btn_menu.collidepoint(mx, my)

        draw_button(screen, "RESUME", FONT_UI, WHITE, btn_resume, GREEN, is_h_p)
        draw_button(screen, "RESTART", FONT_UI, WHITE, btn_restart, ORANGE, is_h_r)
        draw_button(screen, "SETTINGS", FONT_UI, WHITE, btn_settings, BLUE, is_h_s)
        draw_button(screen, "MENU", FONT_UI, WHITE, btn_menu, RED, is_h_m)

        if m_c:
            if is_h_p:
                tap_snd.play()
                state = 3
            elif is_h_s:
                tap_snd.play()
                settings_from_pause = True
                state = 9
            elif is_h_m:
                tap_snd.play()
                warning_target = "MENU"
                state = 15
            elif is_h_r:
                tap_snd.play()
                warning_target = "RESTART"
                state = 15

    # ==========================
    # WARNING SCREEN (STATE 15)
    # ==========================
    elif state == 15:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        w_box = pygame.Rect(120, 180, 560, 270)
        draw_panel(screen, w_box, alpha=240, border_color=RED)

        draw_text("⚠ WARNING ⚠", FONT_MSG, RED, 400, 225)
        draw_text("If you leave or restart now,", FONT_UI, WHITE, 400, 275)
        draw_text("all coins earned in this level will be lost!", FONT_SMALL, YELLOW, 400, 310)

        btn_w_back = pygame.Rect(180, 360, 180, 50)
        btn_ok = pygame.Rect(440, 360, 180, 50)

        mx, my = pygame.mouse.get_pos()
        is_h_back = btn_w_back.collidepoint(mx, my)
        is_h_ok = btn_ok.collidepoint(mx, my)

        draw_button(screen, "GO BACK", FONT_UI, WHITE, btn_w_back, GREEN, is_h_back)
        draw_button(screen, "CONFIRM", FONT_UI, WHITE, btn_ok, RED, is_h_ok)

        if m_c:
            if is_h_back:
                tap_snd.play()
                state = 10
            elif is_h_ok:
                tap_snd.play()
                total_coins -= level_coins
                level_coins = 0

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
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        # State 5: Confirmation Modal for Revive (Clean Dedicated View - No Ghosting)
        if state == 5 and show_revive_confirm:
            p_box = pygame.Rect(140, 150, 520, 300)
            draw_panel(screen, p_box, alpha=250, bg_color=(25, 20, 30), border_color=YELLOW, border_width=3, border_radius=20)

            draw_text("CONFIRM REVIVE?", FONT_MSG, YELLOW, 400, 195)
            c_price = get_revive_price(current_level, revives_done_this_level)
            draw_text("Restore 100% HP & clear active hazards", FONT_SMALL, WHITE, 400, 250)
            
            can_afford = total_coins >= c_price
            cost_color = GREEN if can_afford else RED
            draw_text(f"Price: {c_price} Coins  |  Your Coins: {total_coins}", FONT_SMALL, cost_color, 400, 285)

            b_back = pygame.Rect(180, 360, 190, 50)
            b_buy = pygame.Rect(430, 360, 190, 50)

            is_h_rbk = b_back.collidepoint(mx, my)
            is_h_rbuy = b_buy.collidepoint(mx, my)

            draw_button(screen, "CANCEL", FONT_UI, WHITE, b_back, RED, is_h_rbk)
            draw_button(screen, f"{c_price} COINS", FONT_UI, BLACK if can_afford else WHITE, b_buy, GREEN if can_afford else DARK_GRAY, is_h_rbuy)

            if m_c:
                if is_h_rbk:
                    tap_snd.play()
                    show_revive_confirm = False
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

        # Regular Victory / Defeat Modal
        else:
            box = pygame.Rect(140, 120, 520, 400)
            draw_panel(screen, box, alpha=240, border_color=GREEN if state == 4 else RED)

            if state == 4:
                draw_text("VICTORY!", FONT_TITLE, GREEN, 400, 175)
                draw_text(f"+{level_coins} Coins Earned", FONT_UI, YELLOW, 400, 220)
            else:
                draw_text("MISSION FAILED", FONT_TITLE, RED, 400, 175)
                draw_text("Ship Destroyed in Combat", FONT_UI, LIGHT_GRAY, 400, 220)

            # Star Rating on Victory
            if state == 4:
                earned_stars = 3 if kill_count >= 20 else (2 if kill_count >= 10 else 1)
                star_icon = pygame.transform.scale(star_for_rating, (46, 46))
                start_x = 400 - ((earned_stars * 52) // 2) + 5
                for i in range(earned_stars):
                    screen.blit(star_icon, (start_x + (i * 52), 255))

            b_m = pygame.Rect(180, 330, 180, 55)
            b_n = pygame.Rect(440, 330, 180, 55)

            is_h_m = b_m.collidepoint(mx, my)
            is_h_n = b_n.collidepoint(mx, my)

            draw_button(screen, "MAIN MENU", FONT_UI, WHITE, b_m, BLUE, is_h_m)
            draw_button(screen, "NEXT LEVEL" if state == 4 else "RETRY", FONT_UI, WHITE, b_n, GREEN if state == 4 else ORANGE, is_h_n)

            # Revive button on Game Over
            if state == 5:
                rev_b = pygame.Rect(280, 415, 240, 55)
                is_h_rev = rev_b.collidepoint(mx, my)
                draw_button(screen, "⚡ REVIVE SHIP ⚡", FONT_UI, BLACK, rev_b, YELLOW, is_h_rev, outline_color=WHITE)

                if m_c and is_h_rev:
                    tap_snd.play()
                    show_revive_confirm = True

            if m_c:
                if is_h_m:
                    tap_snd.play()
                    level_coins = 0
                    save_game()
                    state = 0
                elif is_h_n:
                    if state == 4 and current_level < 40:
                        level_coins = 0
                        selected_level = current_level + 1
                        reset_level_logic(selected_level)
                        tap_snd.play()
                        state = 3
                    elif state == 5:
                        level_coins = 0
                        reset_level_logic(selected_level)
                        tap_snd.play()
                        state = 3

    pygame.display.flip()
    clock.tick(60)