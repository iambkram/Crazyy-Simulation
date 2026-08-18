import pygame
import os
from settings import *

# Fonts Setup
pygame.font.init()
pygame.display.set_caption("Crazyy Simulation")
FONT_TITLE = pygame.font.SysFont("Impact", 80)
FONT_MSG = pygame.font.SysFont("Impact", 50)
FONT_MODAL_TITLE = pygame.font.SysFont("Impact", 42)
FONT_MODAL_SUB = pygame.font.SysFont("Impact", 26)
FONT_UI = pygame.font.SysFont("Impact", 30)
FONT_HUD = pygame.font.SysFont("Impact", 34)
FONT_SMALL = pygame.font.SysFont("Arial Black", 16)
FONT_HP = pygame.font.SysFont("Arial Black", 14)

# Assets Folder Path
ASSETS_DIR = "game_assets"

def load_img(name, size=None):
    path = os.path.join(ASSETS_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    if size:
        return pygame.transform.scale(img, size)
    return img

def load_snd(name):
    path = os.path.join(ASSETS_DIR, name)
    return pygame.mixer.Sound(path)

# Ships (Relative Paths)
player_img = load_img("6B.png", (70, 70))
fighter_img = load_img("1.png", (50, 50))
elite_img = load_img("3B.png", (60, 60))
heavy_img = load_img("8B.png", (80, 80))
menu_bg = load_img("menu_bg.jpeg",(800,600))
loading_bg = load_img("loading_bg.jpeg",(800,600))
coin_img = pygame.image.load("game_assets/coin.png").convert_alpha()
coin_icon = pygame.transform.scale(coin_img, (40,40))
star_for_rating = pygame.image.load("game_assets/star.png").convert_alpha()


# --- Boss Setup ---
# Saari boss images ki list (Make sure names folder se match karein)
boss_files = [
    "lvl_1_to_10.png",
    "lvl_11_to_20.png",
    "lvl_21_to_30.png",
    "lvl_31_to_40.png"
]

boss_surfs = {}

for i in range(1, 9):  # i refers to boss tier (Tier 1 = Lvl 5, Tier 2 = Lvl 10...)
    # Logic: Har 2 tiers (yaani 10 levels) ke liye image index change hoga
    # Tier 1,2 -> Index 0 | Tier 3,4 -> Index 1 | Tier 5,6 -> Index 2 ...
    img_index = (i - 1) // 2

    # Safety check: Agar boss tier list se bahar jaye toh last image hi uthayega
    actual_file = boss_files[min(img_index, len(boss_files) - 1)]

    # Image load karke scale karo (Size wahi rakhte hain jo pehle tha)
    temp_img = load_img(actual_file)
    boss_surfs[i] = pygame.transform.scale(temp_img, (140 + i * 15, 100 + i * 10))

bullet_img = pygame.Surface((6, 15))
bullet_img.fill(BLUE)

# Sounds
pygame.mixer.init()
shoot_snd = load_snd("shoot.mp3")
hit_snd = load_snd("hit.mp3")
expl_snd = load_snd("expl.mp3")
boss_expl_snd = load_snd("boss_expl.mp3")
tap_snd = load_snd("tap.mp3")
game_won_snd = load_snd("game_won.mp3")
game_loose_snd = load_snd("game_loose.mp3")


# BGM Paths (Bas naam rakho, game_assets ke andar se uthayega)
loading_bgm = os.path.join(ASSETS_DIR, "loading.mp3")
game_bgm_main = os.path.join(ASSETS_DIR, "bgm_main.mp3")
game_bgm_fast = os.path.join(ASSETS_DIR, "bgm_fast.mp3")


def draw_text(text, font, color, x, y, center=True):
    surf = font.render(str(text), True, color)
    target_screen = pygame.display.get_surface()
    if target_screen:
        rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
        target_screen.blit(surf, rect)

def get_highlight(color):
    return (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))

def draw_button(screen, text, font, font_color, rect, base_color, is_hover, border_radius=15, outline_color=WHITE, outline_width=2):
    # Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(screen, (10, 10, 15), shadow_rect, border_radius=border_radius)
    
    # Base or Hover Color
    draw_color = get_highlight(base_color) if is_hover else base_color
    pygame.draw.rect(screen, draw_color, rect, border_radius=border_radius)
    
    # Glowing Outline if Hover
    if is_hover:
        pygame.draw.rect(screen, outline_color, rect, width=outline_width, border_radius=border_radius)
        
    # Text
    if text:
        draw_text(text, font, font_color, rect.centerx, rect.centery)

def draw_panel(screen, rect, alpha=200, bg_color=(20, 25, 35), border_color=CYAN, border_width=3, border_radius=20):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*bg_color, alpha), panel.get_rect(), border_radius=border_radius)
    pygame.draw.rect(panel, border_color, panel.get_rect(), width=border_width, border_radius=border_radius)
    screen.blit(panel, rect.topleft)