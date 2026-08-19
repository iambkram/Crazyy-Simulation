import pygame
import math
import os
import random
from settings import *

# Fonts Setup
pygame.font.init()
pygame.display.set_caption("Crazyy Simulation")
FONT_TITLE       = pygame.font.SysFont("Impact", 80)
FONT_MSG         = pygame.font.SysFont("Impact", 50)
FONT_MODAL_TITLE = pygame.font.SysFont("Impact", 42)
FONT_MODAL_SUB   = pygame.font.SysFont("Impact", 26)
FONT_UI          = pygame.font.SysFont("Impact", 30)
FONT_HUD         = pygame.font.SysFont("Impact", 34)
FONT_SMALL       = pygame.font.SysFont("Arial Black", 16)
FONT_HP          = pygame.font.SysFont("Arial Black", 14)
FONT_TINY        = pygame.font.SysFont("Arial Black", 12)

# Text Surface Cache (LRU) for performance
_text_cache = {}
_TEXT_CACHE_MAX = 256

def get_cached_text(font, text, color):
    """Return cached rendered text surface to avoid re-rendering every frame."""
    key = (id(font), text, color)
    if key not in _text_cache:
        if len(_text_cache) >= _TEXT_CACHE_MAX:
            # Remove oldest quarter of entries
            keys_to_remove = list(_text_cache.keys())[:_TEXT_CACHE_MAX // 4]
            for k in keys_to_remove:
                del _text_cache[k]
        _text_cache[key] = font.render(text, True, color)
    return _text_cache[key]

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

# ===========================================================
# DRAW HELPERS
# ===========================================================

def draw_text(text, font, color, x, y, center=True):
    surf = font.render(str(text), True, color)
    target_screen = pygame.display.get_surface()
    if target_screen:
        rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
        target_screen.blit(surf, rect)

def draw_text_shadow(text, font, color, x, y, shadow_color=(0,0,0), offset=2, center=True):
    """Draw text with a drop shadow."""
    sc = pygame.display.get_surface()
    if not sc: return
    s_surf = font.render(str(text), True, shadow_color)
    t_surf = font.render(str(text), True, color)
    if center:
        s_rect = s_surf.get_rect(center=(x + offset, y + offset))
        t_rect = t_surf.get_rect(center=(x, y))
    else:
        s_rect = s_surf.get_rect(topleft=(x + offset, y + offset))
        t_rect = t_surf.get_rect(topleft=(x, y))
    sc.blit(s_surf, s_rect)
    sc.blit(t_surf, t_rect)

def get_highlight(color):
    return (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))

# -----------------------------------------------------------
# NEON PANEL — deep space glass card with inner glow + border
# -----------------------------------------------------------
def draw_neon_panel(screen, rect, accent=NEON_CYAN, alpha=240, border_radius=18, border_width=2, bg=PANEL_BG):
    """Premium frosted-glass panel with neon border and inner glow."""
    # Drop shadow
    shadow = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=border_radius + 4)
    screen.blit(shadow, (rect.x - 2, rect.y + 6))

    # Main panel body
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*bg, alpha), panel.get_rect(), border_radius=border_radius)

    # Inner glow along top edge
    glow_h = max(6, rect.height // 8)
    glow = pygame.Surface((rect.width - 8, glow_h), pygame.SRCALPHA)
    for row in range(glow_h):
        a = int(30 * (1.0 - row / glow_h))
        pygame.draw.rect(glow, (*accent, a), (0, row, rect.width - 8, 1), border_radius=border_radius)
    panel.blit(glow, (4, 4))

    # Glass sheen (thin white strip at top)
    sheen = pygame.Surface((rect.width - 20, 3), pygame.SRCALPHA)
    sheen.fill((255, 255, 255, 22))
    panel.blit(sheen, (10, 6))

    screen.blit(panel, rect.topleft)

    # Neon border
    pygame.draw.rect(screen, accent, rect, width=border_width, border_radius=border_radius)

# Keep legacy draw_panel for backward compat
def draw_panel(screen, rect, alpha=200, bg_color=PANEL_BG, border_color=NEON_CYAN, border_width=2, border_radius=18):
    draw_neon_panel(screen, rect, accent=border_color, alpha=alpha, border_radius=border_radius,
                    border_width=border_width, bg=bg_color)

# -----------------------------------------------------------
# GLOWING BUTTON
# -----------------------------------------------------------
def draw_glowing_button(screen, text, font, font_color, rect, base_color, is_hover,
                         border_radius=14, accent=None, pulse_t=0, icon=None):
    """
    Premium button with depth shadow, hover glow, and optional pulse ring.
    pulse_t: a float that increases each frame (math.sin used for pulsation).
    """
    if accent is None:
        accent = get_highlight(base_color)

    # Outer glow ring on hover
    if is_hover:
        glow_size = 8
        glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
        glow_alpha = int(60 + 40 * math.sin(pulse_t * 4))
        pygame.draw.rect(glow_surf, (*accent, max(0, min(255, glow_alpha))),
                         glow_surf.get_rect(), border_radius=border_radius + glow_size)
        screen.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))

    # Drop shadow
    shadow_rect = rect.inflate(0, 0)
    shadow_rect.y += 4
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=border_radius)
    screen.blit(shadow_surf, shadow_rect.topleft)

    # Button body
    draw_col = get_highlight(base_color) if is_hover else base_color
    pygame.draw.rect(screen, draw_col, rect, border_radius=border_radius)

    # Top sheen
    sheen = pygame.Surface((rect.width - 10, 3), pygame.SRCALPHA)
    sheen.fill((255, 255, 255, 35 if is_hover else 18))
    screen.blit(sheen, (rect.x + 5, rect.y + 4))

    # Border
    border_col = accent if is_hover else tuple(max(0, c - 40) for c in base_color)
    pygame.draw.rect(screen, border_col, rect, width=2, border_radius=border_radius)

    # Text
    if text:
        draw_text(text, font, font_color, rect.centerx, rect.centery)

# Keep legacy draw_button for backward compat
def draw_button(screen, text, font, font_color, rect, base_color, is_hover,
                border_radius=14, outline_color=WHITE, outline_width=2):
    draw_glowing_button(screen, text, font, font_color, rect, base_color, is_hover,
                        border_radius=border_radius, accent=outline_color)

# -----------------------------------------------------------
# GRADIENT BAR — HP / Boss HP / sliders / progress
# -----------------------------------------------------------
def draw_gradient_bar(screen, rect, fraction, color_low, color_high, bg_color=(20,20,30),
                       border_radius=8, border_color=None, show_glow=True):
    """
    Draws a horizontal bar that transitions color from color_high (full) to color_low (empty).
    fraction: 0.0 – 1.0
    """
    # Background
    pygame.draw.rect(screen, bg_color, rect, border_radius=border_radius)

    fill_w = max(0, int(rect.width * fraction))
    if fill_w > 2:
        # Interpolate color
        r = int(color_low[0] + (color_high[0] - color_low[0]) * fraction)
        g = int(color_low[1] + (color_high[1] - color_low[1]) * fraction)
        b = int(color_low[2] + (color_high[2] - color_low[2]) * fraction)
        fill_col = (r, g, b)

        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(screen, fill_col, fill_rect, border_radius=border_radius)

        # Sheen
        sheen_surf = pygame.Surface((fill_w, rect.height // 2), pygame.SRCALPHA)
        sheen_surf.fill((255, 255, 255, 28))
        screen.blit(sheen_surf, (rect.x, rect.y))

        # Tip glow
        if show_glow and fill_w > 10:
            tip_glow = pygame.Surface((16, rect.height), pygame.SRCALPHA)
            for px in range(16):
                a = max(0, 80 - px * 8)
                pygame.draw.line(tip_glow, (255, 255, 255, a), (15 - px, 0), (15 - px, rect.height))
            screen.blit(tip_glow, (rect.x + fill_w - 8, rect.y))

    # Border
    bc = border_color if border_color else tuple(min(255, c + 40) for c in bg_color)
    pygame.draw.rect(screen, bc, rect, width=1, border_radius=border_radius)

# -----------------------------------------------------------
# BADGE / PILL TAG
# -----------------------------------------------------------
def draw_badge(screen, text, font, x, y, bg_color, text_color=WHITE, padding_x=14, padding_y=6, border_radius=20, border_color=None):
    """Draws a pill-shaped badge centered at (x, y)."""
    surf = font.render(str(text), True, text_color)
    w = surf.get_width() + padding_x * 2
    h = surf.get_height() + padding_y * 2
    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
    pygame.draw.rect(screen, bg_color, rect, border_radius=border_radius)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=1, border_radius=border_radius)
    screen.blit(surf, surf.get_rect(center=(x, y)))

# -----------------------------------------------------------
# ANIMATED STARFIELD (menu backgrounds)
# -----------------------------------------------------------
_menu_stars = [[__import__('random').randint(0, 800),
                __import__('random').randint(0, 600),
                __import__('random').uniform(0.2, 1.4),
                __import__('random').randint(80, 220)] for _ in range(180)]

def draw_menu_starfield(screen, width=800, height=600):
    """Draws and animates a gentle drifting starfield for menu screens."""
    for s in _menu_stars:
        s[1] += s[2]
        if s[1] > height:
            s[0] = random.randint(0, width)
            s[1] = 0
            s[3] = random.randint(80, 220)
        r = max(1, int(s[2] * 1.2))
        brightness = s[3]
        col = (min(255, brightness // 2), min(255, brightness // 2 + 20), min(255, brightness))
        pygame.draw.circle(screen, col, (int(s[0]), int(s[1])), r)

# -----------------------------------------------------------
# SECTION DIVIDER
# -----------------------------------------------------------
def draw_divider(screen, x1, y, x2, color=NEON_CYAN, alpha=60):
    surf = pygame.Surface((x2 - x1, 2), pygame.SRCALPHA)
    surf.fill((*color, alpha))
    screen.blit(surf, (x1, y))
