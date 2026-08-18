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
control_type = None
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

# Boss Timers and States
boss_active, boss_arriving = False, False
boss_warning_timer = 0
boss_defeated_timer = 0
boss_hp, boss_max_hp = 100, 100
boss_death_timer = 0

asteroid_group = pygame.sprite.Group()
asteroid_img = pygame.image.load("game_assets/asteroid.png").convert_alpha() # 2D model load karo

# Spawning logic variables
asteroids_spawned = 0
spawn_timer = 0
# Random interval (e.g., har 3 se 7 seconds mein ek spawn hoga)
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

# ✅ REPLACE KARO is line se (x, y, speed, max_brightness)
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(5.0, 12.0), random.randint(100, 255)] for _ in range(150)]

# --- Background Scrolling Variables ---
bg_y1 = 0
bg_y2 = -HEIGHT  # Dusri image screen ke thik upar rahegi
bg_scroll_speed = 1.5  # Isse speed kam-zyada kar sakte ho

# States definition
STATE_LOADING = -1
STATE_MAIN_MENU = 0
STATE_ENV_SELECT = 20 # 🔥 Naya state defined
STATE_LEVEL_SELECT = 1
# ... rest of states
state = STATE_LOADING # Start as loading

# --- Colors Definition ---
BRAND_RED = (200, 20, 20)
BRAND_GOLD = (230, 190, 80)
BRAND_GLOW = (255, 100, 100, 100) # Alpha included (Reddish Glow)

# --- BRANDING ANIMATION VARIABLES ---
# Naya state defined: state -2 branding ke liye hai
state = -2
# Animation Timeline (miliseconds mein)
anim_time = pygame.time.get_ticks()
# Branding control variables
anim_duration = 2000 # Total anim duration is strictly 2 seconds
anim_played = False
anim_flash_alpha = 0
anim_logo_scale = 1.0 # Logo scale from 1.0 down
anim_text_alpha = 0
anim_text_y = HEIGHT + 50 # Start below screen
anim_shine_x = -300 # Shine sweep starting position
last_frame_ticks = pygame.time.get_ticks() # For Delta Time

# --- PLACEHOLDER ASSETS (Ye main.py mein temporary hain taaki run ho) ---
# Tum inko baad mein replace kar lena
# temporary logo
brand_logo_placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
pygame.draw.circle(brand_logo_placeholder, BRAND_RED, (100, 100), 80)
pygame.draw.polygon(brand_logo_placeholder, WHITE, [(50,150), (100,50), (150,150)]) # simple shield shape

# temporary glowing text structure
brand_text_placeholder = pygame.font.SysFont("Impact", 80).render("TEXT", True, WHITE)
brand_text_y_target = 480 # Center target position for text

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
    def __init__(self, asteroid_img):
        super().__init__()

        # 1. ERROR FIX: random.choice mein SQUARE brackets [ ] lagane hote hain
        scale_factor = random.choice([1, 1.5, 2])
        base_size = 50
        new_size = int(base_size * scale_factor)

        # 2. ERROR FIX: scale function mein size ko ek saath () mein dena hota hai
        # Yahan hum original_image save kar rahe hain taaki ghumte waqt image fite nahi
        self.original_image = pygame.transform.scale(asteroid_img, (new_size, new_size))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()

        # 3. Position aur Speed
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.speed = random.randint(3, 6)

        # 4. ROTATION ke variables (Dheere ghumne ke liye)
        self.angle = 0
        self.rot_speed = random.uniform(-1.0, 1.0)  # Koi left ghumega koi right

    def update(self):
        # Niche aane ki speed
        self.rect.y += self.speed

        # ROTATION LOGIC:
        self.angle += self.rot_speed

        # Har baar original image ko rotate karo
        self.image = pygame.transform.rotate(self.original_image, self.angle)

        # Asteroid ko uski jagah par hi ghumane ke liye center set karna zaroori hai
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

        # Screen se bahar jaye to delete
        if self.rect.y > HEIGHT:
            self.kill()


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
                max_galaxy_level = data.get("max_galaxy_level", data.get("max_level", 1))
                max_nebula_level = data.get("max_nebula_level", 1)
                max_blackhole_level = data.get("max_blackhole_level", 1)
                
                env2_unlocked = max_galaxy_level > 20
                env3_unlocked = max_nebula_level > 20
                
                control_type = data.get("control_type", None) # Load control type
                music_vol = data.get("music_vol", 0.5)
                sfx_vol = data.get("sfx_vol", 0.7)
                pygame.mixer.music.set_volume(music_vol)
                shoot_snd.set_volume(sfx_vol)
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
    global current_boss_img  # 🔥 Naya variable global kiya
    global win_snd_played, loose_snd_played
    win_snd_played = False
    loose_snd_played = False
    global galaxy_bg_y
    galaxy_bg_y = 0.0
    global revives_done_this_level
    revives_done_this_level = 0

    current_level = level
    kill_count = 0
    player_health = unlocked_hp
    fighters, elites, heavies, bullets, enemy_bullets, achievements, particles = [], [], [], [], [], [], []
    level_coins = 0

    reset_match()

    boss_active = False
    boss_arriving = False
    boss_warning_timer = 0
    boss_defeated_timer = 0
    boss_death_timer = 0

    boss_max_hp = current_level * 100
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
    global asteroids_spawned_in_match
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
        draw_text("CRAZYY SIMULATION", FONT_TITLE, CYAN, 400, 80)
        screen.blit(coin_icon, (330,105))
        draw_text(f"{total_coins}", FONT_UI, YELLOW, x = 400, y = 110)

        # Buttons List: (Text, Color, Y-Position, Target State)
        # Note: Settings (9) hamesha khulna chahiye bina warning ke
        menu_btns = [
            ("MISSIONS", BLUE, 200, STATE_ENV_SELECT),
            ("STORE", MAGENTA, 290, 6),
            ("SETTINGS", ORANGE, 380, 9),
            ("QUIT", RED, 470, 0)
        ]

        mx, my = pygame.mouse.get_pos()

        for txt, col, y, target in menu_btns:
            btn_rect = pygame.Rect(270, y, 260, 70)
            is_hover = btn_rect.collidepoint(mx, my)

            # Button Draw logic
            draw_col = get_highlight(col) if is_hover else col
            pygame.draw.rect(screen, draw_col, btn_rect, border_radius=15)
            draw_text(txt, FONT_UI, WHITE, 400, y + 35)

            # --- Click Logic ---
            if m_c and is_hover:
                if txt == "QUIT":
                    running = False

                # Agar Control Type select nahi hai toh warning dikhao
                elif (txt == "MISSIONS" or txt == "STORE") and control_type is None:
                    tap_snd.play()
                    win_snd_played = False
                    loose_snd_played = False
                    show_settings_warning = True

                # Agar sab sahi hai toh target state par jao (Missions ke liye ab ye 20/STATE_ENV_SELECT hoga)
                else:
                    tap_snd.play()
                    state = target

            # --- WARNING POPUP DRAWING ---
            # Isko loop ke bahar rakha hai taaki ye buttons ke upar dikhe
            if show_settings_warning:
                # Dim background effect (Optional: screen thodi dark ho jayegi popup ke peeche)
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))

                warn_box = pygame.Rect(150, 200, 500, 220)
                pygame.draw.rect(screen, DARK_GRAY, warn_box, border_radius=20)
                pygame.draw.rect(screen, RED, warn_box, width=4, border_radius=20)

                draw_text("Please select your device", FONT_MSG, WHITE, 400, 260)
                draw_text("in the SETTINGS first!", FONT_UI, YELLOW, 400, 300)

                ok_btn = pygame.Rect(340, 340, 120, 50)
                is_h_ok = ok_btn.collidepoint(mx, my)
                pygame.draw.rect(screen, get_highlight(GREEN) if is_h_ok else GREEN, ok_btn, border_radius=10)
                draw_text("OK", FONT_UI, WHITE, 400, 365)

                if m_c and is_h_ok:
                    tap_snd.play()
                    show_settings_warning = False

        # WARNING POPUP DRAWING
        if show_settings_warning:
            warn_box = pygame.Rect(150, 200, 500, 200)
            pygame.draw.rect(screen, DARK_GRAY, warn_box, border_radius=20)
            pygame.draw.rect(screen, RED, warn_box, 3, border_radius=20)

            # Simple English text as requested
            draw_text("Please select your device", FONT_MSG, WHITE, 400, 250)
            draw_text("in the SETTINGS first!", FONT_UI, YELLOW, 400, 290)

            ok_btn = pygame.Rect(340, 330, 120, 50)
            pygame.draw.rect(screen, GREEN, ok_btn, border_radius=10)
            draw_text("OK", FONT_UI, WHITE, 400, 355)

            if m_c and ok_btn.collidepoint(m_p):
                tap_snd.play()
                show_settings_warning = False

    # ==========================
    # 🔥 1. SELECT ENVIRONMENT (NEW STATE 20) 🔥
    # ==========================
    elif state == STATE_ENV_SELECT:  # state == 20
        # Dark Overlay background previous state par blur effect dene ke liye (jaisa Pause screen mein hai)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Dark transparent
        screen.blit(overlay, (0, 0))

        draw_text("SELECT ENVIRONMENT", FONT_TITLE, GREEN, 400, 80)

        # Mouse check interaction ke liye
        mx, my = pygame.mouse.get_pos()

        # --- DEFINING BUTTON RECTS ---
        # 3 Big Grid Buttons (Yahan rectangle positions apne hisaab se tweak kar lena center aur symmetry ke liye)
        # Size example: 350x180
        btn_env1 = pygame.Rect(100, 180, 280, 160)  # Top Left (Galaxy)
        btn_env2 = pygame.Rect(420, 180, 280, 160)  # Top Right (Nebula)
        btn_env3 = pygame.Rect(260, 360, 280, 160)  # Bottom Center (Blackhole)

        # Hover logic setup
        is_h_e1 = btn_env1.collidepoint(mx, my)
        is_h_e2 = btn_env2.collidepoint(mx, my) and env2_unlocked  # Hover tabhi jab unlocked ho
        is_h_e3 = btn_env3.collidepoint(mx, my) and env3_unlocked

        # --- DRAWING ENVRIONMENT BUTTONS (SIMPLE COLORED RECTS FOR NOW) ---
        # Environment colors matching your JPG themes
        env_col_1 = DARK_GRAY if not env1_unlocked else (0, 100, 255)  # Deep Blue for Galaxy
        env_col_2 = DARK_GRAY if not env2_unlocked else (200, 50, 255)  # Purple/Magenta for Nebula
        env_col_3 = DARK_GRAY if not env3_unlocked else (150, 0, 0)  # Dark Red for Blackhole (Event Horizon feel)

        # Hover color update
        if is_h_e1: env_col_1 = get_highlight(env_col_1)
        if is_h_e2: env_col_2 = get_highlight(env_col_2)
        if is_h_e3: env_col_3 = get_highlight(env_col_3)

        # Drawing the base button rectangles
        pygame.draw.rect(screen, env_col_1, btn_env1, border_radius=15)
        pygame.draw.rect(screen, env_col_2, btn_env2, border_radius=15)
        pygame.draw.rect(screen, env_col_3, btn_env3, border_radius=15)

        # Locked Overlay Drawing (Draw a darker rectangle on top)
        if not env2_unlocked:
            pygame.draw.rect(screen, (30, 30, 30, 150), btn_env2, border_radius=15)  # Greyish locked overlay
        if not env3_unlocked:
            pygame.draw.rect(screen, (30, 30, 30, 150), btn_env3, border_radius=15)  # Greyish locked overlay

        # Border for Selected (Green border matching UI style)
        if current_selected_env == 1:
            pygame.draw.rect(screen, GREEN, btn_env1, width=4, border_radius=15)
        elif current_selected_env == 2 and env2_unlocked:
            pygame.draw.rect(screen, GREEN, btn_env2, width=4, border_radius=15)
        elif current_selected_env == 3 and env3_unlocked:
            pygame.draw.rect(screen, GREEN, btn_env3, width=4, border_radius=15)

        # --- Drawing Texts on Buttons ---
        draw_text("OUT OF THE GALAXY", FONT_UI, WHITE, btn_env1.centerx, btn_env1.centery - 10)
        draw_text("40 Levels", FONT_SMALL, WHITE, btn_env1.centerx, btn_env1.centery + 30)

        t_col2 = LIGHT_GRAY if not env2_unlocked else WHITE
        draw_text("NEBULA DUST", FONT_UI, t_col2, btn_env2.centerx, btn_env2.centery - 10)
        draw_text("🔒 20 Galaxy levels req.", FONT_SMALL, t_col2, btn_env2.centerx, btn_env2.centery + 30)

        t_col3 = LIGHT_GRAY if not env3_unlocked else WHITE
        draw_text("THE BLACKHOLE", FONT_UI, t_col3, btn_env3.centerx, btn_env3.centery - 10)
        draw_text("🔒 20 Nebula levels req.", FONT_SMALL, t_col3, btn_env3.centerx, btn_env3.centery + 30)

        # Draw lock icons over locked envs for better UX
        if not env2_unlocked:
            screen.blit(lock_icon, (btn_env2.centerx - 50, btn_env2.centery - 50))
        if not env3_unlocked:
            screen.blit(lock_icon, (btn_env3.centerx - 50, btn_env3.centery - 50))

        # --- BACK BUTTON ---
        btn_back = pygame.Rect(270, 520, 260, 60)
        is_h_back = btn_back.collidepoint(mx, my)
        pygame.draw.rect(screen, get_highlight(RED) if is_h_back else RED, btn_back, border_radius=10)
        draw_text("BACK", FONT_UI, WHITE, 400, 550)
        # ==========================================
        # 🔥 ENVIRONMENT SELECT CLICK LOGIC 🔥
        # ==========================================
        if m_c:
            # 1. Galaxy Selection (Hamesha Unlocked)
            if btn_env1.collidepoint(mx, my):
                tap_snd.play()
                current_selected_env = 1
                state = STATE_LEVEL_SELECT  # Level select par bhej do

            # 2. Nebula Selection (Locked/Unlocked Check)
            elif btn_env2.collidepoint(mx, my):
                if env2_unlocked:
                    tap_snd.play()
                    current_selected_env = 2
                    state = STATE_LEVEL_SELECT
                else:
                    pass  # Yahan locked wali error sound laga sakte ho

            # 3. Blackhole Selection (Locked/Unlocked Check)
            elif btn_env3.collidepoint(mx, my):
                if env3_unlocked:
                    tap_snd.play()
                    current_selected_env = 3
                    state = STATE_LEVEL_SELECT
                else:
                    pass  # Locked

            # 4. BACK Button
            elif btn_back.collidepoint(mx, my):
                tap_snd.play()
                state = 0  # Main Menu par wapas

    # ==========================
    # SETTINGS MENU (STATE 9, 11, 12)
    # ==========================
    elif state == 9:
        screen.blit(menu_bg, (0, 0))
        draw_text("GAME SETTINGS", FONT_TITLE, GREEN, 400, 60)

        # --- Chhote Buttons (Mobile / PC) ---
        # Mobile Button
        btn_mob = pygame.Rect(150, 140, 200, 100)
        pygame.draw.rect(screen, BLUE if control_type != 'MOBILE' else CYAN, btn_mob, border_radius=15)
        draw_text("MOBILE", FONT_UI, WHITE, 250, 180)
        draw_text("CONTROL", FONT_SMALL, WHITE, 250, 210)

        # PC Button
        btn_pc = pygame.Rect(450, 140, 200, 100)
        pygame.draw.rect(screen, MAGENTA if control_type != 'PC' else CYAN, btn_pc, border_radius=15)
        draw_text("PC", FONT_UI, WHITE, 550, 180)
        draw_text("CONTROL", FONT_SMALL, WHITE, 550, 210)

        # --- SLIDERS LOGIC ---
        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        # Slider Function (Code bachane ke liye hum logic yahi likh rahe hain)
        slider_y_pos = [320, 420]  # Music aur SFX ki height
        slider_labels = ["MUSIC VOLUME", "SOUND EFFECTS"]
        current_vols = [music_vol, sfx_vol]

        for i in range(2):
            draw_text(slider_labels[i], FONT_SMALL, WHITE, 400, slider_y_pos[i] - 40)
            s_rect = pygame.Rect(200, slider_y_pos[i], 400, 25)  # Background bar
            pygame.draw.rect(screen, (50, 50, 50), s_rect, border_radius=10)

            # Green Fill bar
            fill_w = int(current_vols[i] * 400)
            pygame.draw.rect(screen, GREEN, (200, slider_y_pos[i], fill_w, 25), border_radius=10)

            # Percentage text overlay
            draw_text(f"{int(current_vols[i] * 100)}%", FONT_SMALL, WHITE, 400, slider_y_pos[i] + 12)

            # Slider Handle (Dandi/Knob)
            handle_x = 200 + fill_w
            pygame.draw.rect(screen, WHITE, (handle_x - 5, slider_y_pos[i] - 10, 10, 45), border_radius=5)

            # Interaction Logic
            if m_down and s_rect.inflate(20, 40).collidepoint(mx, my):
                new_val = max(0, min(1, (mx - 200) / 400))
                if i == 0:

                    music_vol = new_val
                    pygame.mixer.music.set_volume(music_vol)
                else:

                    sfx_vol = new_val
                    shoot_snd.set_volume(sfx_vol)# Saare sounds yahan update honge
                    game_won_snd.set_volume(sfx_vol)
                    game_loose_snd.set_volume(sfx_vol)
                    tap_snd.set_volume(sfx_vol)
                    boss_expl_snd.set_volume(sfx_vol)
                    expl_snd.set_volume(sfx_vol)
                    hit_snd.set_volume(sfx_vol)

        # Back Button
        btn_back = pygame.Rect(325, 520, 150, 50)
        pygame.draw.rect(screen, RED, btn_back, border_radius=10)
        draw_text("BACK", FONT_UI, WHITE, 400, 545)

        # --- FIXED SETTINGS CLICK LOGIC ---
        if m_c:
            if btn_mob.collidepoint(m_p):
                tap_snd.play()
                control_type = 'MOBILE'
                state = 12  # Mobile info screen
                save_game()
            elif btn_pc.collidepoint(m_p):
                tap_snd.play()
                control_type = 'PC'
                state = 11  # PC info screen
                save_game()
            elif btn_back.collidepoint(m_p):
                tap_snd.play()
                if settings_from_pause:
                    state = 10  # Wapas Pause Menu
                    settings_from_pause = False
                else:
                    state = 0  # Wapas Main Menu
                save_game()
        # ⚠️ Yahan se wo akela 'state = 0' aur 'else: state = -1' bilkul hata dena

    # ==========================
    # PC CONTROLS INFO (STATE 11)
    # ==========================
    elif state == 11:
        screen.blit(menu_bg, (0, 0))  # Background draw karna zaroori hai

        # Ek sundar sa box instructions ke liye
        info_box = pygame.Rect(100, 120, 600, 330)
        pygame.draw.rect(screen, DARK_GRAY, info_box, border_radius=20)
        pygame.draw.rect(screen, MAGENTA, info_box, 3, border_radius=20)

        draw_text("PC CONTROL :", FONT_MSG, WHITE, 400, 180)
        draw_text("Use The Arrows Or 'A','D' Keys To Move.", FONT_UI, YELLOW, 400, 260)
        draw_text("Left Click On The Mouse To Fire Bullets.", FONT_UI, YELLOW, 400, 310)

        # Wapas jane ke liye button
        btn_ok = pygame.Rect(310, 360, 180, 55)
        is_h_ok = btn_ok.collidepoint(m_p)
        pygame.draw.rect(screen, GREEN if is_h_ok else (0, 180, 0), btn_ok, border_radius=10)
        draw_text("OK", FONT_UI, WHITE, 400, 387)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9  # Wapas settings mein jao

    # ==========================
    # MOBILE CONTROLS INFO (STATE 12)
    # ==========================
    elif state == 12:
        screen.blit(menu_bg, (0, 0))

        info_box = pygame.Rect(100, 120, 600, 330)
        pygame.draw.rect(screen, DARK_GRAY, info_box, border_radius=20)
        pygame.draw.rect(screen, BLUE, info_box, 3, border_radius=20)

        draw_text("MOBILE CONTROL : ", FONT_MSG, WHITE, 400, 180)
        draw_text("Slide Finger On The Screen To Move & Fire.", FONT_UI, YELLOW, 400, 280)

        btn_ok = pygame.Rect(310, 360, 180, 55)
        is_h_ok = btn_ok.collidepoint(m_p)
        pygame.draw.rect(screen, GREEN if is_h_ok else (0, 180, 0), btn_ok, border_radius=10)
        draw_text("OK", FONT_UI, WHITE, 400, 387)

        if m_c and is_h_ok:
            tap_snd.play()
            state = 9  # Wapas settings mein jao

    # ==========================
    # MISSIONS / LEVEL SELECT (STATE 1)
    # ==========================
    elif state == STATE_LEVEL_SELECT:  # Yaani state == 1
        # 🔥 1. DYNAMIC BACKGROUND 🔥
        if current_selected_env == 1:
            screen.blit(galaxy_bg, (0, 0))
        elif current_selected_env == 2:
            screen.blit(nebula_bg, (0, 0))
        elif current_selected_env == 3:
            screen.blit(blackhole_bg, (0, 0))

        # Background ke upar halka sa dark shadow taaki UI saaf dikhe
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))  # Thoda dark kiya hai
        screen.blit(overlay, (0, 0))

        # 🔥 2. MISSIONS UI (Yahan se menu_bg hata diya hai!) 🔥
        draw_text("MISSIONS", FONT_TITLE, GREEN, 400, 80)

        # Missions ka container box
        box_rect = pygame.Rect(150, 150, 500, 300)
        pygame.draw.rect(screen, DARK_GRAY, box_rect, border_radius=15)
        pygame.draw.rect(screen, CYAN, box_rect, 3, border_radius=15)

        # --- DRAG TO SCROLL LOGIC ---
        mx, my = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        if m_down and box_rect.collidepoint(mx, my):
            if not is_dragging_missions:
                is_dragging_missions = True
                last_mouse_y = my
            else:
                dy = my - last_mouse_y
                level_scroll_y += dy  # Missions ko move karo
                last_mouse_y = my
        else:
            is_dragging_missions = False

        level_scroll_y = max(-850, min(0, level_scroll_y))
        screen.set_clip(box_rect.inflate(-10, -10))

        # Get current environment's max level
        env_max = max_galaxy_level if current_selected_env == 1 else (max_nebula_level if current_selected_env == 2 else max_blackhole_level)
        
        for i in range(1, 41):
            lx = 180 + ((i - 1) % 4) * 115
            ly = 180 + ((i - 1) // 4) * 110 + level_scroll_y

            lvl_rect = pygame.Rect(lx, ly, 90, 90)
            is_u = False
            is_h = False
            if ly > 50 and ly < 500:
                is_u = i <= env_max
                is_h = lvl_rect.collidepoint(mx, my) and is_u and box_rect.collidepoint(mx, my)

            color = get_highlight(BLUE) if is_h else (BLUE if is_u else BLACK)
            pygame.draw.rect(screen, color, lvl_rect, border_radius=10)

            txt_color = WHITE if is_u else LIGHT_GRAY
            draw_text(str(i), FONT_TITLE, txt_color, lx + 45, ly + 45)

            if m_c and is_h:
                tap_snd.play()
                selected_level = i
                state = 2
        screen.set_clip(None)

        # --- BACK BUTTON ---
        btn_back = pygame.Rect(270, 480, 260, 60)
        is_h_b = btn_back.collidepoint(mx, my)
        pygame.draw.rect(screen, get_highlight(RED) if is_h_b else RED, btn_back, border_radius=10)
        draw_text("BACK", FONT_UI, WHITE, 400, 510)

        if m_c and is_h_b:
            tap_snd.play()
            state = STATE_ENV_SELECT  # Back karne par wapas Environment menu pe jaye!

    # ==========================
    # STORE (STATE 6, 7, 8)
    # ==========================
    elif state == 6:
        screen.blit(menu_bg, (0, 0))
        draw_text("SPACE STORE", FONT_TITLE, GREEN, 400, 80)
        screen.blit(coin_icon, (320, 115))
        draw_text(f"{total_coins}", FONT_UI, YELLOW, x=400, y=120)
        items = [("Health", GREEN, 100, 'hp'), ("Move Speed", ORANGE, 310, 'sp'), ("Power Bullets", RED, 520, 'pb')]
        for name, col, x, key in items:
            btn = pygame.Rect(x, 220, 180, 100)
            is_h = btn.collidepoint(m_p)
            pygame.draw.rect(screen, get_highlight(col) if is_h else col, btn, border_radius=15)
            draw_text(name, FONT_SMALL, WHITE, x + 90, 270)
            if m_c and is_h:
                tap_snd.play()
                store_selection = key

        if store_selection:
            pygame.draw.rect(screen, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT))
            box_info = pygame.Rect(150, 180, 500, 250)
            pygame.draw.rect(screen, DARK_GRAY, box_info, border_radius=20)
            pygame.draw.rect(screen, CYAN, box_info, 2, border_radius=20)

            desc = \
                {"hp": "Increase Total HP Capacity", "sp": "Boost Ship Navigation Speed",
                 "pb": "Unlock Multi-Bullet Fire"}[
                    store_selection]
            if store_selection == 'hp':
                cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
            elif store_selection == 'sp':
                cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
            else:
                cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"

            draw_text("ITEM DETAILS", FONT_UI, YELLOW, 400, 220)
            draw_text(desc, FONT_SMALL, WHITE, 400, 270)
            draw_text(f"COST: {cost} COINS", FONT_UI, GREEN, 400, 320)

            btn_st_bk = pygame.Rect(180, 360, 150, 50)
            pygame.draw.rect(screen, RED, btn_st_bk, border_radius=10)
            btn_buy = pygame.Rect(470, 360, 150, 50)
            pygame.draw.rect(screen, GREEN, btn_buy, border_radius=10)
            draw_text("BACK", FONT_SMALL, WHITE, 255, 385)
            draw_text("BUY NOW", FONT_SMALL, WHITE, 545, 385)

            if m_c:
                if btn_st_bk.collidepoint(m_p):
                    tap_snd.play()
                    store_selection = None
                elif btn_buy.collidepoint(m_p):
                    if cost != "MAX" and total_coins >= cost:
                        state = 7
                    else:
                        tap_snd.play()
                        state = 8

        if not store_selection:
            btn_b_m = pygame.Rect(20, 530, 120, 50)
            pygame.draw.rect(screen, RED, btn_b_m, border_radius=10)
            draw_text("BACK", FONT_UI, WHITE, 80, 555)
            if m_c and btn_b_m.collidepoint(m_p):
                tap_snd.play()
                state = 0

    elif state == 7:
        pygame.draw.rect(screen, DARK_GRAY, (200, 200, 400, 200), border_radius=20)
        draw_text("Confirm Purchase?", FONT_UI, WHITE, 400, 260)
        b_n, b_y = pygame.Rect(230, 320, 120, 50), pygame.Rect(450, 320, 120, 50)
        pygame.draw.rect(screen, RED, b_n, border_radius=10)
        pygame.draw.rect(screen, GREEN, b_y, border_radius=10)
        draw_text("No", FONT_UI, WHITE, 290, 345)
        draw_text("Yes", FONT_UI, WHITE, 510, 345)
        if m_c:
            if b_n.collidepoint(m_p):
                tap_snd.play()
                state = 6
            if b_y.collidepoint(m_p):
                cost = hp_costs[hp_step] if store_selection == 'hp' else speed_costs[
                    speed_step] if store_selection == 'sp' else bullet_costs[bullet_step]
                update_coins(-cost)
                if store_selection == 'hp':
                    unlocked_hp += 10;
                    hp_step += 1
                elif store_selection == 'sp':
                    unlocked_speed += 2;
                    speed_step += 1
                elif store_selection == 'pb':
                    unlocked_bullets += 1;
                    bullet_step += 1
                save_game()
                tap_snd.play()
                state = 6
                store_selection = None

    elif state == 8:
        pygame.draw.rect(screen, DARK_GRAY, (200, 200, 400, 220), border_radius=20)
        draw_text("Not Enough Coins!", FONT_UI, RED, 400, 250)
        b_b = pygame.Rect(230, 330, 120, 50)
        pygame.draw.rect(screen, RED, b_b, border_radius=10)
        b_t = pygame.Rect(450, 330, 120, 50)
        pygame.draw.rect(screen, YELLOW, b_t, border_radius=10)
        draw_text("BACK", FONT_SMALL, WHITE, 290, 355)
        draw_text("TOP UP", FONT_SMALL, BLACK, 510, 355)
        if m_c and b_b.collidepoint(m_p):
            tap_snd.play()
            state = 6

    # ==========================
    # MISSION INFO (STATE 2)
    # ==========================
    elif state == 2:
        pygame.draw.rect(screen, DARK_GRAY, (200, 200, 400, 250), border_radius=20)
        draw_text(f"Missions {selected_level}", FONT_MSG, YELLOW, 400, 260)
        b_r, b_a = pygame.Rect(230, 340, 140, 60), pygame.Rect(430, 340, 140, 60)
        pygame.draw.rect(screen, GREEN, b_r, border_radius=10)
        pygame.draw.rect(screen, RED, b_a, border_radius=10)
        draw_text("PLAY", FONT_UI, WHITE, 300, 370)
        draw_text("BACK", FONT_UI, WHITE, 500, 370)
        if m_c:
            if b_r.collidepoint(m_p):
                tap_snd.play()
                reset_level_logic(selected_level); state = 3

            if b_a.collidepoint(m_p):
                tap_snd.play()
                state = 1

    # ==========================
    # GAMEPLAY (STATE 3)
    # ==========================
    elif state == 3:

        pause_btn_rect = pygame.Rect(WIDTH - 50, 70, 40, 40)
        pygame.draw.rect(screen, WHITE, pause_btn_rect, border_radius=5)
        draw_text("||", FONT_SMALL, BLACK, WIDTH - 30, 90)
        if m_c and pause_btn_rect.collidepoint(m_p):
            tap_snd.play()
            state = 10

        # --- SMART CONTROLS LOGIC ---
        if fire_cooldown > 0:
            fire_cooldown -= 1

        is_firing = False

        if control_type == 'PC':
            keys = pygame.key.get_pressed()
            if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player_rect.left > 0: player_rect.x -= unlocked_speed
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player_rect.right < WIDTH: player_rect.x += unlocked_speed

            if m_c and not pause_btn_rect.collidepoint(m_p):
                is_firing = True

        elif control_type == 'MOBILE':
            mouse_pressed = pygame.mouse.get_pressed()[0]
            if mouse_pressed:
                mx, my = pygame.mouse.get_pos()

                # Slide to move logic

                if player_rect.centerx < mx and player_rect.right < WIDTH:
                        player_rect.x += unlocked_speed
                elif player_rect.centerx > mx and player_rect.left > 0:
                        player_rect.x -= unlocked_speed


                if fire_cooldown <= 0:
                    is_firing = True
                    if current_level <= 15: # Goli nikalne ke beech ka gap (tap and hold logic)
                        fire_cooldown = 9
                    else:
                        fire_cooldown = 7

        if is_firing:
            b_cnt = unlocked_bullets + (1 if skills['double']['active'] else 0)
            for i in range(b_cnt):
                offset = (i - b_cnt / 2) * 15 + 7
                bullets.append({'rect': pygame.Rect(player_rect.centerx + offset, player_rect.top, 6, 15)})
            shoot_snd.play()

        # --- SMART CONTROLS LOGIC END ---

        # ... (tumhara SMART CONTROLS LOGIC khatam hone ke baad) ...
        # shoot_snd.play() wali line ke baad yahan se replace karo:

        # Y-axis mein dheere dheere niche move karo
        galaxy_bg_y += 0.03

        # Agar image puri niche chali jaye, to usko wapas reset kar do
        if galaxy_bg_y >= bg_height:
            galaxy_bg_y = 0

        # Ek hi image ko 2 baar draw karna padega taaki upar koi khali (black) space na dikhe
        screen.blit(galaxy_bg, (0, int(galaxy_bg_y)))
        screen.blit(galaxy_bg, (0, int(galaxy_bg_y) - bg_height))

        # 🔥 2. STARS LOOP & TWINKLE EFFECT (Background ke Upar) 🔥
        for s in stars:
            # Twinkle effect (Glow aur dim karne ke liye brightness vary hogi)
            current_brightness = max(30, s[3] - random.randint(0, 80))
            star_color = (current_brightness, current_brightness, current_brightness)

            # Ekdam point ki tarah draw karega (1x1 ya 2x2 pixel)
            pygame.draw.rect(screen, star_color, (s[0], int(s[1]), 2, 2))

            # Stars ko niche move karo (+Y axis)
            s[1] += s[2]

            # Infinite Loop: Screen ke niche jaye to wapas upar bhej do
            if s[1] > HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, WIDTH)

        # 👇👇 NAYA CODE YAHAN PASTE KARO 👇👇
        # Asteroids ko move (update) aur screen par draw karo
        asteroid_group.update()
        asteroid_group.draw(screen)

        # Player aur Asteroid ka takrana (Collision Check)
        for ast in asteroid_group:
            if ast.rect.colliderect(player_rect):
                player_health -= 30  # 15 damage
                ast.kill()  # Takrane ke baad asteroid tut jayega
                hit_snd.play()  # Hit sound play hogi
        # 👆👆 NAYA CODE YAHAN KHATAM 👆👆

        current_tick = pygame.time.get_ticks()

        # Level ke hisaab se max limit set karna
        if current_level <= 30:
            max_asteroids_in_match = 12
        else:
            max_asteroids_in_match = 7  # Higher levels mein kam asteroids taaki lag na ho

        # --- SPAWN LOGIC START ---
        # 1. Check karo kya abhi limit bachi hai?
        if asteroids_spawned < max_asteroids_in_match:

            # 2. Check karo kya spawn karne ka waqt ho gaya hai?
            if current_tick - last_spawn_tick > next_spawn_time:
                # Naya asteroid banao aur group mein dalo
                new_asteroid = Asteroid(asteroid_img)
                asteroid_group.add(new_asteroid)

                # Counter badhao aur timer reset karo
                asteroids_spawned += 1
                last_spawn_tick = current_tick

                # Agla asteroid kab aayega (random 8 to 15 seconds)
                next_spawn_time = random.randint(8000, 15000)
        # --- SPAWN LOGIC END ---

    # ===============================================
    # Iske baad tumhara Enemies aur Boss ka code chalne do


        all_enemies_objs = fighters + elites + heavies

        # --- SMART DIFFICULTY ENGINE ---
        # 1. SPEED LOCK: Level 10 ke baad speed lock ho jayegi
        eff_speed_lvl = min(current_level, 10)

        # 🔥 DAMAGE LOCK: Level 5 ke baad enemies ka damage nahi badhega
        eff_dmg_lvl = min(current_level, 5)

        # SPAWN & FIRE RATE (Ye lagatar badhenge taaki mazza aaye)
        spawn_chance = max(10, int(50 - (current_level * 1.0)))
        fire_chance = max(30, int(120 - (current_level * 2.2)))

        max_fighters = int(8 + (current_level * 0.5))
        max_elites = int(5 + (current_level * 0.3))
        max_heavies = int(2 + (current_level * 0.2))

        # --- SPAWN EXECUTION ---
        if not boss_active and not boss_arriving and boss_defeated_timer == 0:
            if len(fighters) < max_fighters and random.randint(1, spawn_chance) == 1:
                nr = fighter_img.get_rect(center=(random.randint(50, 750), -50))
                if check_enemy_spawn(nr, all_enemies_objs): fighters.append({'rect': nr, 'hp': 1, 'start_x': nr.x, 'time': 0, 'type': 'fighter'})

            if current_level >= 2 and len(elites) < max_elites and random.randint(1, int(spawn_chance * 1.5)) == 1:
                nr = elite_img.get_rect(center=(random.randint(50, 750), -50))
                if check_enemy_spawn(nr, all_enemies_objs): elites.append({'rect': nr, 'hp': 2, 'start_x': nr.x, 'time': 0, 'type': 'elite'})

            if current_level >= 3 and len(heavies) < max_heavies and random.randint(1, int(spawn_chance * 2.5)) == 1:
                nr = heavy_img.get_rect(center=(random.randint(50, 750), -50))
                if check_enemy_spawn(nr, all_enemies_objs): heavies.append({'rect': nr, 'hp': 5, 'start_x': nr.x, 'time': 0, 'type': 'heavy'})

        for e_list, val in [(fighters, 1), (elites, 2), (heavies, 5)]:
            for e in e_list[:]:
                if 'time' not in e: e['time'] = 0
                if 'start_x' not in e: e['start_x'] = e['rect'].x
                e['time'] += 1

                speed_bonus = (eff_speed_lvl // 3) * 1
                move_speed_y = int(2 + (val // 2) + (eff_speed_lvl * 0.3) + speed_bonus)
                e['rect'].y += move_speed_y

                for other in all_enemies_objs:
                    if e != other and e['rect'].colliderect(other['rect']):
                        if e['rect'].x < other['rect'].x:
                            e['rect'].x -= 2
                        else:
                            e['rect'].x += 2

                # Tracking player and Movement patterns based on Environment
                track_speed_x = 1 + int(eff_speed_lvl * 0.25)
                
                if current_selected_env == 1: # Galaxy: Simple tracking
                    if e['rect'].x < player_rect.x:
                        e['rect'].x += track_speed_x
                    elif e['rect'].x > player_rect.x:
                        e['rect'].x -= track_speed_x
                elif current_selected_env == 2: # Nebula: Sine wave + tracking
                    wave_offset = math.sin(e['time'] * 0.05) * 5
                    e['rect'].x += int(wave_offset)
                    if e['rect'].x < player_rect.x - 20: e['rect'].x += track_speed_x
                    elif e['rect'].x > player_rect.x + 20: e['rect'].x -= track_speed_x
                elif current_selected_env == 3: # Blackhole: Aggressive zig-zag
                    wave_offset = math.cos(e['time'] * 0.1) * 8
                    e['rect'].x += int(wave_offset)
                    if e['rect'].x < player_rect.x: e['rect'].x += track_speed_x + 1
                    elif e['rect'].x > player_rect.x: e['rect'].x -= track_speed_x + 1
                    
                e['rect'].x = max(0, min(WIDTH - e['rect'].width, e['rect'].x))

                if random.randint(1, int(fire_chance)) == 1:
                    dmg = (eff_dmg_lvl * val)
                    size = (6, 12) if val < 5 else (12, 12)
                    
                    # Fire logic varies by environment
                    if current_selected_env >= 2 and val >= 2: # Elites and Heavies fire double/triple in higher envs
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].left + 5, e['rect'].bottom, size[0], size[1]), 'damage': dmg})
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].right - 5 - size[0], e['rect'].bottom, size[0], size[1]), 'damage': dmg})
                        if current_selected_env == 3 and val == 5: # Heavies in Blackhole fire triple spread
                             enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx - (size[0]//2), e['rect'].bottom, size[0], size[1]), 'damage': dmg})
                    else:
                        enemy_bullets.append({'rect': pygame.Rect(e['rect'].centerx, e['rect'].bottom, size[0], size[1]), 'damage': dmg})

                if e['rect'].colliderect(player_rect):
                    if e in e_list: e_list.remove(e)
                    if not skills['immortal']['active']:
                        player_health -= 20
                        hit_snd.set_volume(sfx_vol)
                        hit_snd.play()
                elif e['rect'].top > HEIGHT:
                    if e in e_list: e_list.remove(e)

        if boss_active:
            if boss_death_timer > 0:
                boss_death_timer -= 1
                if boss_death_timer % 5 == 0:
                    # BOSS DEATH BLAST LOGIC
                    # Boss ke marne par ek bada dhamaka

                    for _ in range(80):  # Boss marega toh 80 particles ek saath niklenge!
                        p_color = random.choice(BLAST_COLORS)

                        # Speed zyada rakhi hai taaki explosion door tak faile
                        p_speed_x = random.uniform(-9, 9)
                        p_speed_y = random.uniform(-9, 9)

                        # Radius bada rakha hai taaki aag ke gole bade dikhein
                        p_radius = random.randint(6, 15)

                        particles.append(
                            [boss_rect.centerx, boss_rect.centery, p_speed_x, p_speed_y, p_radius, p_color])
                if boss_death_timer == 1:
                    boss_active = False
                    boss_defeated_timer = 120
                    boss_expl_snd.play()
                    if current_selected_env == 1 and current_level == max_galaxy_level and max_galaxy_level < 40:
                        max_galaxy_level += 1
                        env2_unlocked = max_galaxy_level > 20
                    elif current_selected_env == 2 and current_level == max_nebula_level and max_nebula_level < 40:
                        max_nebula_level += 1
                        env3_unlocked = max_nebula_level > 20
                    elif current_selected_env == 3 and current_level == max_blackhole_level and max_blackhole_level < 40:
                        max_blackhole_level += 1
                        save_game()
            else:
                # (Move boss top into screen code remains same)
                if boss_rect.top < 60: boss_rect.y += 2

                # Determine speed based on tier (Cap at Tier 8)
                boss_eff_tier = min(((current_level - 1) // 5) + 1, 8)
                b_spd = 2 + (boss_eff_tier // 2)

                # 🔥 VIBRATION BUG FIX: Smart Movement Logic 🔥
                # Agar target X durbin se zyada dur hai, toh snap karo
                if boss_rect.centerx < boss_target_x:
                    dist_x = boss_target_x - boss_rect.centerx
                    if dist_x < b_spd:
                        boss_rect.centerx = boss_target_x  # Snap to exact target
                    else:
                        boss_rect.x += b_spd  # Move step
                elif boss_rect.centerx > boss_target_x:
                    dist_x = boss_rect.centerx - boss_target_x
                    if dist_x < b_spd:
                        boss_rect.centerx = boss_target_x  # Snap to exact target
                    else:
                        boss_rect.x -= b_spd  # Move step

                # Jab exact target tak pahunch jaye, tab naya target choose karo
                if abs(boss_rect.centerx - boss_target_x) < 2:
                    boss_target_x = random.randint(100, 700)

                # SHOOT CHANCE KO INT MEIN CONVERT KIYA HAI (TypeError fix karne ke liye)
                shoot_chance = max(10, 30 - (current_level * 2))
                if random.randint(1, int(shoot_chance)) == 1:
                    # GOLI AB BOSS KE CENTER SE THODA NICHE (NOSE) SE NIKLEGI
                    bullet_x = boss_rect.centerx - 6
                    bullet_y = boss_rect.centery - 10
                    boss_eff_damage = min(current_level, 5)
                    enemy_bullets.append({'rect': pygame.Rect(bullet_x, bullet_y, 12, 20),
                                          'damage': 10 * boss_eff_damage})

            # --- DRAWING & COLLISIONS ---
        for eb in enemy_bullets[:]:
            eb['rect'].y += 6
            pygame.draw.rect(screen, RED if eb['rect'].width < 10 else MAGENTA, eb['rect'])
            if eb['rect'].colliderect(player_rect):
                if not skills['immortal']['active']:
                    player_health -= eb['damage']

                    hit_snd.play()
                if eb in enemy_bullets: enemy_bullets.remove(eb)
            elif eb['rect'].top > HEIGHT:
                if eb in enemy_bullets: enemy_bullets.remove(eb)

        for b in bullets[:]:
            b['rect'].y -= 12
            hit = False

            if boss_active and boss_death_timer == 0:
                if b['rect'].colliderect(boss_rect):
                    boss_hp -= 5

                    hit_snd.play()
                    if b in bullets: bullets.remove(b)
                    if boss_hp <= 0:
                        boss_death_timer = 150
                        update_coins(current_level * 50)
                    hit = True

            if not hit:
                for e_list, c_val in [(fighters, 1), (elites, 2), (heavies, 5)]:
                    for e in e_list[:]:
                        if b['rect'].colliderect(e['rect']):
                            e['hp'] -= 1
                            if b in bullets: bullets.remove(b)

                            if e['hp'] <= 0:
                                # ✅ FIX 1: Enemy ko list se remove karo taaki wo gayab ho jaye
                                if e in e_list:
                                    e_list.remove(e)

                                update_coins(1 if c_val == 1 else 2 if c_val == 2 else 3)
                                kill_count += 1

                                expl_snd.play()

                                # ✅ FIX 2: Blast particles mein 'f' ki jagah 'e' use karo
                                for _ in range(15):
                                    p_color = random.choice(BLAST_COLORS)
                                    p_speed_x = random.uniform(-4, 4)
                                    p_speed_y = random.uniform(-4, 4)
                                    p_radius = random.randint(3, 6)

                                    # Yahan 'e' use hoga kyunki current enemy wahi hai
                                    particles.append(
                                        [e['rect'].centerx, e['rect'].centery, p_speed_x, p_speed_y, p_radius,
                                            p_color])
                            else:

                                hit_snd.play()
                            hit = True
                            break
                    if hit: break

            # Powerups logic
        if random.randint(1, 800) == 1:
            t = random.choice(['immortal', 'double'])
            achievements.append({'rect': pygame.Rect(random.randint(50, 750), -50, 30, 30), 'type': t})

        for a in achievements[:]:
            a['rect'].y += 3
            pygame.draw.circle(screen, skills[a['type']]['color'], a['rect'].center, 15)
            if a['rect'].colliderect(player_rect):
                skills[a['type']]['active'] = True
                skills[a['type']]['timer'] = now + skills[a['type']]['duration']
                if a in achievements: achievements.remove(a)

            # Drawing Layers
        for b in bullets: screen.blit(bullet_img, b['rect'])
        for f in fighters: screen.blit(fighter_img, f['rect'])
        for e in elites: screen.blit(elite_img, e['rect'])
        for h in heavies: screen.blit(heavy_img, h['rect'])

        if boss_active and boss_death_timer == 0:
            screen.blit(current_boss_img, boss_rect)

            # 🔥 3. PARTICLES DRAW (Ab Blast Effect sabse upar dikhega) 🔥
        # PARTICLE UPDATE AUR DRAW LOOP (Main loop ke andar)
        for particle in particles[:]:
            # Position update (X aur Y speed jod rahe hain)
            particle[0] += particle[2]
            particle[1] += particle[3]

            # RADIUS SHRINKING: Aag dheere dheere thandi ho rahi hai (is line se asli feel aayegi)
            particle[4] -= 0.2

            # Agar radius 0 se bada hai toh draw karo
            if particle[4] > 0:
                pygame.draw.circle(screen, particle[5], (int(particle[0]), int(particle[1])), int(particle[4]))
            else:
                # Pighal gaya toh list se hata do
                particles.remove(particle)

        # Player sabse upar rahega


        screen.blit(player_img, player_rect)

        # ==========================
        # MODERN UI & HUD
        # ==========================
        # Top gradient bar for a modern look
        hud_bg = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
        pygame.draw.rect(hud_bg, (10, 15, 30, 220), hud_bg.get_rect(), border_bottom_left_radius=20, border_bottom_right_radius=20)
        screen.blit(hud_bg, (0, 0))

        # Coin Display
        screen.blit(coin_icon, (20, 15))
        draw_text(f"{total_coins}", FONT_HUD, YELLOW, 70, 18, center=False)
        
        # Current Level Display
        env_names = {1: "GALAXY", 2: "NEBULA", 3: "BLACKHOLE"}
        draw_text(f"{env_names.get(current_selected_env, 'GALAXY')} LVL {current_level}", FONT_UI, CYAN, WIDTH // 2, 35)

        # Player Health Bar (Right Side)
        health_bar_bg = pygame.Rect(WIDTH - 230, 25, 210, 20)
        pygame.draw.rect(screen, (40, 0, 0), health_bar_bg, border_radius=10)
        pygame.draw.rect(screen, LIGHT_GRAY, health_bar_bg, 2, border_radius=10)
        
        curr_hp_w = int(206 * (max(0, player_health) / unlocked_hp))
        if curr_hp_w > 0:
            hp_color = GREEN if player_health > unlocked_hp * 0.3 else RED
            pygame.draw.rect(screen, hp_color, (WIDTH - 228, 27, curr_hp_w, 16), border_radius=8)
        
        draw_text(f"{int(max(0, player_health))}/{unlocked_hp}", FONT_HP, WHITE, WIDTH - 125, 35)

        # Boss Health Bar (Top Center, Below Level)
        if boss_active and boss_death_timer == 0:
            boss_hp_bg = pygame.Rect(WIDTH // 2 - 150, 75, 300, 15)
            pygame.draw.rect(screen, (50, 0, 0), boss_hp_bg, border_radius=7)
            pygame.draw.rect(screen, WHITE, boss_hp_bg, 2, border_radius=7)
            
            boss_hp_w = int(296 * (max(0, boss_hp) / boss_max_hp))
            if boss_hp_w > 0:
                pygame.draw.rect(screen, MAGENTA, (WIDTH // 2 - 148, 77, boss_hp_w, 11), border_radius=5)
            draw_text("BOSS", FONT_HP, WHITE, WIDTH // 2, 75)

        # --- ADD THIS FOR MOBILE UI DRAWING ---
        if control_type == 'MOBILE':

            # Slider Bar

            draw_text("SLIDE FINGER TO MOVE & FIRE", FONT_SMALL,(80,80,80), WIDTH // 2, HEIGHT - 30)

        y_offset_sh = 80
        for s_key, s_val in skills.items():
            if s_val['active']:
                rem_time = (s_val['timer'] - now) // 1000
                if rem_time > 0:
                    draw_text(f"{s_val['label']}: {rem_time}s", FONT_SMALL, s_val['color'], 20, y_offset_sh,
                              False)
                    y_offset_sh += 30
                else:
                    s_val['active'] = False

        if current_level >= 11:
            req_kills = 250
        else:
            boss_kill_reqs = {1: 50, 2: 100, 3: 100, 4: 150, 5: 150, 6: 200, 7: 200, 8: 200, 9: 200, 10: 200}
            req_kills = boss_kill_reqs.get(current_level, 550)

        if kill_count >= req_kills and not boss_active and not boss_arriving and boss_defeated_timer == 0:
            boss_arriving = True
            boss_warning_timer = 180

        if boss_arriving:
            boss_warning_timer -= 1
            if (boss_warning_timer // 15) % 2 == 0:
                draw_text("BOSS ARRIVING", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2)
            if boss_warning_timer <= 0:
                boss_arriving = False
                boss_active = True

        if boss_defeated_timer > 0:
            boss_defeated_timer -= 1
            draw_text("BOSS DEFEATED", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2)
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
        # Background Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Pause Box
        box = pygame.Rect(200, 150, 400, 350)
        pygame.draw.rect(screen, DARK_GRAY, box, border_radius=20)
        pygame.draw.rect(screen, CYAN, box, width=3, border_radius=20)
        draw_text("GAME PAUSED", FONT_MSG, YELLOW, 400, 210)

        # --- Button Rects (Size: 150x60) ---
        btn_menu = pygame.Rect(230, 280, 150, 60)
        btn_resume = pygame.Rect(420, 280, 150, 60)
        btn_settings = pygame.Rect(230, 370, 150, 60)
        btn_restart = pygame.Rect(420, 370, 150, 60)

        # Hover Check
        is_h_m = btn_menu.collidepoint(m_p)
        is_h_p = btn_resume.collidepoint(m_p)
        is_h_s = btn_settings.collidepoint(m_p)
        is_h_r = btn_restart.collidepoint(m_p)

        # Draw Buttons
        pygame.draw.rect(screen, RED if not is_h_m else get_highlight(RED), btn_menu, border_radius=10)
        pygame.draw.rect(screen, GREEN if not is_h_p else get_highlight(GREEN), btn_resume, border_radius=10)
        pygame.draw.rect(screen, ORANGE if not is_h_s else get_highlight(ORANGE), btn_settings, border_radius=10)
        pygame.draw.rect(screen, PURPLE if not is_h_r else get_highlight(PURPLE), btn_restart, border_radius=10)

        # Button Texts
        draw_text("MENU", FONT_UI, WHITE, 305, 310)
        draw_text("RESUME", FONT_UI, WHITE, 495, 310)
        draw_text("SETTINGS", FONT_UI, WHITE, 305, 400)
        draw_text("RESTART", FONT_UI, WHITE, 495, 400)

        # Click Logic FIXED
        if m_c:
            if is_h_p:
                state = 3  # FIX: 4 se 3 kiya (Resume Game)
            elif is_h_s:
                settings_from_pause = True
                state = 9  # FIX: 101 se 9 kiya (Settings)
            elif is_h_m:
                warning_target = "MENU"
                state = 15
            elif is_h_r:
                warning_target = "RESTART"
                state = 15

    # ==========================
    # WARNING SCREEN (STATE 15)
    # ==========================
    elif state == 15:
        # Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Warning Box (Bada aur chouda box)
        w_box = pygame.Rect(100, 200, 600, 260)
        pygame.draw.rect(screen, DARK_GRAY, w_box, border_radius=15)
        pygame.draw.rect(screen, RED, w_box, width=3, border_radius=15)

        # Warning Text (Text 2 line mein break kiya hai)
        draw_text("WARNING!", FONT_MSG, RED, 400, 240)
        draw_text("If you quit or restart, you will lose", FONT_UI, WHITE, 400, 290)
        draw_text("all coins earned in this level.", FONT_UI, WHITE, 400, 320)

        # Buttons - Left side Back, Right side OK
        btn_w_back = pygame.Rect(200, 380, 160, 50)
        btn_ok = pygame.Rect(440, 380, 160, 50)

        is_h_back = btn_w_back.collidepoint(m_p)
        is_h_ok = btn_ok.collidepoint(m_p)

        pygame.draw.rect(screen, GREEN if not is_h_back else get_highlight(GREEN), btn_w_back, border_radius=10)
        pygame.draw.rect(screen, RED if not is_h_ok else get_highlight(RED), btn_ok, border_radius=10)

        draw_text("BACK", FONT_UI, WHITE, 280, 405)
        draw_text("OK", FONT_UI, WHITE, 520, 405)

        # Click Logic FIXED
        if m_c:
            if is_h_back:
                state = 10  # Wapas pause screen pe
            elif is_h_ok:
                # Coins Loose Logic
                total_coins -= level_coins
                level_coins = 0  # Reset level progress

                if warning_target == "MENU":
                    save_game()
                    state = 0  # Main Menu
                elif warning_target == "RESTART":
                    reset_level_logic(selected_level)  # FIX: yaha crash ho raha tha kyunki bracket khali tha
                    state = 3  # FIX: 4 se 3 kiya taaki wapas game chal pade

    # ==========================
    # WIN / LOSS (STATE 4 & 5)
    # ==========================
    elif state == 4 or state == 5:

        box = pygame.Rect(150, 150, 500, 350)
        pygame.draw.rect(screen, DARK_GRAY, box, border_radius=20)
        draw_text("VICTORY" if state == 4 else "GAME OVER", FONT_MSG, GREEN if state == 4 else RED, 400, 200)
        # --- STAR RATING SYSTEM START ---
        # Logic: Agar kill_count 20 se jyada to 3 Star, 10 se jyada to 2 Star, warna 1 Star
        if kill_count >= 20:
            earned_stars = 3
        elif kill_count >= 10:
            earned_stars = 2
        else:
            earned_stars = 1

        # Star image ko resize kar lete hain taaki pop-up mein fit aaye
        star_icon = pygame.transform.scale(star_for_rating, (45, 45))

        # Stars ko center mein draw karne ka math
        # Agar 3 star hain, toh X start position piche khisakegi
        start_x = 400 - ((earned_stars * 50) // 2) + 5

        for i in range(earned_stars):
            # Y=250 rakha hai taaki Title aur Buttons ke beech mein aaye
            screen.blit(star_icon, (start_x + (i * 50), 245))
            # --- STAR RATING SYSTEM END ---
        b_m, b_n = pygame.Rect(180, 300, 180, 60), pygame.Rect(440, 300, 180, 60)

        is_h_m = b_m.collidepoint(m_p)
        is_h_n = b_n.collidepoint(m_p)
        pygame.draw.rect(screen, get_highlight(BLUE) if is_h_m else BLUE, b_m, border_radius=10)
        pygame.draw.rect(screen, get_highlight(MAGENTA) if is_h_n else MAGENTA, b_n, border_radius=10)

        draw_text("MENU", FONT_UI, WHITE, 270, 330)
        draw_text("NEXT LEVEL" if state == 4 else "RETRY", FONT_UI, WHITE, 530, 330)

        # --- REVIVE SYSTEM START ---
        if state == 5:  # Sirf Game Over hone par dikhao
            if not show_revive_confirm:
                # Naya REVIVE Button (Green) - Iski position adjust ki hai box ke hisaab se
                rev_b = pygame.Rect(310, 380, 180, 60)  # Beech mein thoda upar
                is_h_rev = rev_b.collidepoint(m_p)

                pygame.draw.rect(screen, get_highlight(GREEN) if is_h_rev else GREEN, rev_b, border_radius=10)
                draw_text("REVIVE", FONT_UI, BLACK, x=400, y=410)  # Text ko button ke center mein rakha hai

            elif show_revive_confirm:
                # --- CONFIRM REVIVING POPUP ---
                # Ye poore screen ke upar ek chhota box dikhayega
                p_box = pygame.Rect(200, 250, 400, 180)
                pygame.draw.rect(screen, (30, 30, 30), p_box, border_radius=15)
                pygame.draw.rect(screen, WHITE, p_box, 2, border_radius=15)  # Border

                draw_text("CONFIRM REVIVING?", FONT_MSG, WHITE, x=400, y=280)

                c_price = get_revive_price(current_level, revives_done_this_level)

                # Popup Buttons
                b_back = pygame.Rect(220, 370, 100, 40)
                b_buy = pygame.Rect(410, 370, 170, 40)

                # Back button draw
                pygame.draw.rect(screen, RED, b_back, border_radius=8)
                draw_text("BACK", FONT_UI, WHITE, x=270, y=390)

                # Buy button draw (Total coins check karke color change)
                btn_c = GREEN if total_coins >= c_price else (100, 100, 100)
                pygame.draw.rect(screen, btn_c, b_buy, border_radius=8)
                draw_text(f"{c_price} COINS", FONT_UI, BLACK, x=495, y=390)
        # --- REVIVE SYSTEM END ---

        if m_c:
            # 1. Agar Revive Confirm Popup khula hai, toh sirf uske buttons kaam karenge
            if state == 5 and show_revive_confirm:
                # BACK Button Click
                if b_back.collidepoint(m_p):
                    tap_snd.play()
                    show_revive_confirm = False

                # X COINS (Buy) Button Click
                elif b_buy.collidepoint(m_p):
                    price = get_revive_price(current_level, revives_done_this_level)
                    if total_coins >= price:
                       total_coins -= price
                       revives_done_this_level += 1

                       # 1. Player HP Full (Jitni max HP tumne set ki hai)
                       player_health = unlocked_hp

                       # 2. Saamne ke Enemies aur Bullets Clear karo
                       # Isse player ko "breathing space" milega
                       revive_protection_timer = 180
                       bullets.clear()
                       fighters.clear()
                       elites.clear()
                       heavies.clear()
                       # Agar dushman ki goliyaan (enemy_bullets) hain, toh unhe bhi clear kar do
                       # enemy_bullets.clear()

                       # 3. Ek bada blast effect (Optional but cool)
                       # Taaki dikhe ki revive hone par ek power wave nikli hai
                       for _ in range(50):
                         p_speed_x = random.uniform(-10, 10)
                         p_speed_y = random.uniform(-10, 10)
                         particles.append(
                            [player_rect.centerx, player_rect.centery, p_speed_x, p_speed_y, 8, (255, 255, 255)])

                    state = 3  # Wapas game mein
                    show_revive_confirm = False


            # 2. Agar Popup nahi khula, toh normal buttons kaam karenge
            else:
                # MENU Button
                if b_m.collidepoint(m_p):
                    tap_snd.play()
                    level_coins = 0
                    state = 0

                # NEXT LEVEL / RETRY Button
                elif b_n.collidepoint(m_p):
                    if state == 4 and current_level < 40:  # Victory Case
                        level_coins = 0
                        selected_level = current_level + 1
                        reset_level_logic(selected_level)
                        state = 3
                    elif state == 5:  # Game Over (Retry) Case
                        level_coins = 0
                        reset_level_logic(selected_level)
                        tap_snd.play()
                        state = 3

                # Naya REVIVE Button (Sirf Game Over state 5 mein)
                elif state == 5 and rev_b.collidepoint(m_p):
                    tap_snd.play()
                    show_revive_confirm = True

    pygame.display.flip()
    clock.tick(60)