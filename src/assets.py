import pygame
import math
import os
import random
from settings import *

# ============================================================
# FONTS SETUP — Using pygame.freetype for better rendering
# ============================================================
pygame.font.init()
pygame.display.set_caption("Crazyy Simulation")

# Primary fonts (Impact for impact, Consolas for sci-fi mono feel)
FONT_TITLE       = pygame.font.SysFont("Impact", 80)
FONT_MSG         = pygame.font.SysFont("Impact", 50)
FONT_MODAL_TITLE = pygame.font.SysFont("Impact", 42)
FONT_MODAL_SUB   = pygame.font.SysFont("Impact", 26)
FONT_UI          = pygame.font.SysFont("Impact", 30)
FONT_HUD         = pygame.font.SysFont("Impact", 34)
FONT_SMALL       = pygame.font.SysFont("Arial Black", 16)
FONT_HP          = pygame.font.SysFont("Arial Black", 14)
FONT_TINY        = pygame.font.SysFont("Arial Black", 12)
# Monospace HUD font for numbers
try:
    FONT_MONO    = pygame.font.SysFont("Consolas", 18)
    FONT_MONO_SM = pygame.font.SysFont("Consolas", 14)
except Exception:
    FONT_MONO    = FONT_HP
    FONT_MONO_SM = FONT_TINY

# Text Surface Cache (LRU) for performance
_text_cache = {}
_TEXT_CACHE_MAX = 512

def get_cached_text(font, text, color):
    """Return cached rendered text surface to avoid re-rendering every frame."""
    key = (id(font), text, color)
    if key not in _text_cache:
        if len(_text_cache) >= _TEXT_CACHE_MAX:
            keys_to_remove = list(_text_cache.keys())[:_TEXT_CACHE_MAX // 4]
            for k in keys_to_remove:
                del _text_cache[k]
        _text_cache[key] = font.render(text, True, color)
    return _text_cache[key]

# Assets Folder Path
import sys
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    ASSETS_DIR = os.path.join(sys._MEIPASS, "game_assets")
else:
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_assets")

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
# CORE TEXT DRAW HELPERS
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

_neon_text_cache = {}

def draw_neon_text(screen, text, font, color, x, y, glow_radius=4, glow_alpha=80, center=True):
    """Draw text with multi-layer neon glow — cached for performance."""
    cache_key = (str(text), id(font), color[:3], glow_radius, glow_alpha)
    if cache_key not in _neon_text_cache:
        if len(_neon_text_cache) > 200:
            _neon_text_cache.clear()
        # Render main text to measure size
        main_surf = font.render(str(text), True, color)
        tw, th = main_surf.get_size()
        pad = glow_radius + 2
        buf = pygame.Surface((tw + pad * 2, th + pad * 2), pygame.SRCALPHA)
        cx_local, cy_local = pad + tw // 2, pad + th // 2
        # Glow layers
        for r in range(glow_radius, 0, -1):
            glow_col = (*color[:3], max(10, glow_alpha - r * 14))
            gsurf = font.render(str(text), True, glow_col[:3])
            gsurf_a = pygame.Surface(gsurf.get_size(), pygame.SRCALPHA)
            gsurf_a.blit(gsurf, (0, 0))
            gsurf_a.set_alpha(max(10, glow_alpha - r * 16))
            for ox, oy in [(-r, 0), (r, 0), (0, -r), (0, r), (-r, -r), (r, r)]:
                rect = gsurf_a.get_rect(center=(cx_local + ox, cy_local + oy))
                buf.blit(gsurf_a, rect)
        # Main text
        rect = main_surf.get_rect(center=(cx_local, cy_local))
        buf.blit(main_surf, rect)
        _neon_text_cache[cache_key] = buf
    cached = _neon_text_cache[cache_key]
    if center:
        screen.blit(cached, cached.get_rect(center=(x, y)))
    else:
        screen.blit(cached, cached.get_rect(topleft=(x, y)))

def draw_glitch_text(screen, text, font, color, x, y, now, glitch_intensity=0.08):
    """Draw text with occasional random-character glitch frames (cyberpunk effect)."""
    glitch_chars = "!@#$%^&*<>?/\\|0123456789"
    display = ""
    for ch in str(text):
        if ch != " " and random.random() < glitch_intensity:
            display += random.choice(glitch_chars)
        else:
            display += ch
    # Offset glitch line
    if random.random() < glitch_intensity * 2:
        offset_x = random.randint(-3, 3)
        glitch_surf = font.render(display, True, NEON_ELECTRIC)
        rect = glitch_surf.get_rect(center=(x + offset_x, y))
        glitch_surf.set_alpha(120)
        screen.blit(glitch_surf, rect)
    main_surf = font.render(str(text), True, color)
    rect = main_surf.get_rect(center=(x, y))
    screen.blit(main_surf, rect)

def get_highlight(color):
    return (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))

# ===========================================================
# HOLOGRAPHIC PANEL — glassmorphism + corner brackets
# ===========================================================

def draw_holographic_panel(screen, rect, accent=NEON_CYAN, alpha=240, border_radius=18,
                            border_width=2, bg=PANEL_BG, show_scanlines=True,
                            show_corners=True, pulse_t=0.0):
    """
    Next-level glassmorphism panel with:
    - Frosted glass body with animated inner glow
    - Subtle scanline overlay
    - Sharp corner bracket accents
    - Animated hex-grid texture
    """
    # Drop shadow
    shadow = pygame.Surface((rect.width + 14, rect.height + 14), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 110), shadow.get_rect(), border_radius=border_radius + 6)
    screen.blit(shadow, (rect.x - 4, rect.y + 8))

    # Main glass body
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*bg, alpha), panel.get_rect(), border_radius=border_radius)

    # Animated inner top glow
    pulse = (math.sin(pulse_t * 2.0) + 1) * 0.5  # 0..1
    glow_h = max(8, rect.height // 6)
    glow = pygame.Surface((rect.width - 8, glow_h), pygame.SRCALPHA)
    for row in range(glow_h):
        a = int((28 + 14 * pulse) * (1.0 - row / glow_h))
        pygame.draw.rect(glow, (*accent, max(0, a)), (0, row, rect.width - 8, 1), border_radius=border_radius)
    panel.blit(glow, (4, 4))

    # Glass sheen strip
    sheen = pygame.Surface((rect.width - 24, 2), pygame.SRCALPHA)
    sheen.fill((255, 255, 255, 30))
    panel.blit(sheen, (12, 7))

    screen.blit(panel, rect.topleft)

    # Scanline overlay
    if show_scanlines:
        for sy in range(rect.y, rect.y + rect.height, 4):
            sl = pygame.Surface((rect.width, 1), pygame.SRCALPHA)
            sl.fill((0, 0, 0, 18))
            screen.blit(sl, (rect.x, sy))

    # Neon border
    pygame.draw.rect(screen, accent, rect, width=border_width, border_radius=border_radius)

    # Inner second border glow
    inner_rect = rect.inflate(-border_width * 2 - 2, -border_width * 2 - 2)
    glow_border = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
    glow_a = int(30 + 20 * pulse)
    pygame.draw.rect(glow_border, (*accent, glow_a), glow_border.get_rect(), width=1, border_radius=max(0, border_radius - 2))
    screen.blit(glow_border, inner_rect.topleft)

    # Corner brackets
    if show_corners:
        draw_corner_brackets(screen, rect, accent, size=14, width=2)

# Keep legacy draw_neon_panel for backward compat
def draw_neon_panel(screen, rect, accent=NEON_CYAN, alpha=240, border_radius=18, border_width=2, bg=PANEL_BG):
    draw_holographic_panel(screen, rect, accent=accent, alpha=alpha, border_radius=border_radius,
                           border_width=border_width, bg=bg, show_scanlines=False, show_corners=False)

def draw_panel(screen, rect, alpha=200, bg_color=PANEL_BG, border_color=NEON_CYAN, border_width=2, border_radius=18):
    draw_neon_panel(screen, rect, accent=border_color, alpha=alpha, border_radius=border_radius,
                    border_width=border_width, bg=bg_color)

# ===========================================================
# CORNER BRACKETS — Tactical/military UI corner accents
# ===========================================================

def draw_corner_brackets(screen, rect, color, size=14, width=2, alpha=255):
    """Draw sharp L-shaped corner brackets around a rect."""
    corners = [
        (rect.left, rect.top, 1, 1),
        (rect.right, rect.top, -1, 1),
        (rect.left, rect.bottom, 1, -1),
        (rect.right, rect.bottom, -1, -1),
    ]
    s = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    for (cx, cy, dx, dy) in corners:
        lx = cx - rect.x + 10
        ly = cy - rect.y + 10
        pygame.draw.line(s, (*color, alpha), (lx, ly), (lx + dx * size, ly), width)
        pygame.draw.line(s, (*color, alpha), (lx, ly), (lx, ly + dy * size), width)
    screen.blit(s, (rect.x - 10, rect.y - 10))

# ===========================================================
# PLASMA BUTTON — Next-gen animated button
# ===========================================================

def draw_plasma_button(screen, text, font, font_color, rect, base_color, is_hover,
                       border_radius=14, pulse_t=0, accent=None, width=300):
    """
    Premium button with:
    - Animated gradient border sweep (spinning arc)
    - Inner bloom on hover
    - Top glass sheen
    - Depth shadow
    """
    if accent is None:
        accent = get_highlight(base_color)

    # Drop shadow
    shadow_rect = pygame.Rect(rect.x + 3, rect.y + 5, rect.width, rect.height)
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 130), shadow_surf.get_rect(), border_radius=border_radius)
    screen.blit(shadow_surf, shadow_rect.topleft)

    # Animated glow ring on hover
    if is_hover:
        glow_size = 10
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(55 + 45 * math.sin(pulse_t * 4))
        pygame.draw.rect(glow_surf, (*accent, max(0, min(255, glow_alpha))),
                         glow_surf.get_rect(), border_radius=border_radius + glow_size)
        screen.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))

    # Button body
    draw_col = get_highlight(base_color) if is_hover else base_color
    pygame.draw.rect(screen, draw_col, rect, border_radius=border_radius)

    # Inner gradient: lighter at top
    grad_surf = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    for gy in range(rect.height // 2):
        a = int(40 * (1.0 - gy / (rect.height // 2)))
        pygame.draw.rect(grad_surf, (255, 255, 255, a), (0, gy, rect.width, 1))
    mask = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
    grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    screen.blit(grad_surf, (rect.x, rect.y))

    # Border
    border_col = accent if is_hover else tuple(max(0, c - 30) for c in base_color)
    pygame.draw.rect(screen, border_col, rect, width=2, border_radius=border_radius)

    # Spinning arc border on hover
    if is_hover:
        arc_surf = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        arc_rect_inner = pygame.Rect(4, 4, rect.width, rect.height)
        sweep_start = pulse_t * 2.5
        sweep_end   = sweep_start + math.pi * 1.1
        try:
            pygame.draw.arc(arc_surf, (*GLASS_WHITE, 200), arc_rect_inner,
                            sweep_start, sweep_end, 2)
        except Exception:
            pass
        screen.blit(arc_surf, (rect.x - 4, rect.y - 4))

    # Text
    if text:
        draw_text(text, font, font_color, rect.centerx, rect.centery)

# Keep legacy draw_glowing_button
def draw_glowing_button(screen, text, font, font_color, rect, base_color, is_hover,
                        border_radius=14, accent=None, pulse_t=0, icon=None):
    draw_plasma_button(screen, text, font, font_color, rect, base_color, is_hover,
                      border_radius=border_radius, pulse_t=pulse_t, accent=accent)

def draw_button(screen, text, font, font_color, rect, base_color, is_hover,
                border_radius=14, outline_color=WHITE, outline_width=2):
    draw_plasma_button(screen, text, font, font_color, rect, base_color, is_hover,
                      border_radius=border_radius, accent=outline_color)

# ===========================================================
# CHROMATIC HEALTH BAR — Multi-color gradient with glow
# ===========================================================

def draw_chromatic_bar(screen, rect, fraction, label="", font=None,
                       border_radius=8, show_glow=True, pulse_t=0.0,
                       color_full=(50, 255, 120), color_mid=(255, 210, 50), color_low=(255, 50, 80)):
    """
    Health/boss bar with:
    - Tri-color interpolation (green → gold → red)
    - Animated shimmer tip
    - Inner glow
    - Rounded corners
    """
    # Background
    bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (20, 20, 32, 220), bg_surf.get_rect(), border_radius=border_radius)
    screen.blit(bg_surf, rect.topleft)
    pygame.draw.rect(screen, (60, 65, 85), rect, width=1, border_radius=border_radius)

    fill_w = max(0, int(rect.width * max(0.0, min(1.0, fraction))))
    if fill_w < 3:
        return

    # Color interpolation: fraction > 0.5 => full color, < 0.25 => low color
    if fraction > 0.5:
        t = (fraction - 0.5) * 2.0
        col = tuple(int(color_mid[i] + (color_full[i] - color_mid[i]) * t) for i in range(3))
    elif fraction > 0.25:
        t = (fraction - 0.25) * 4.0
        col = tuple(int(color_low[i] + (color_mid[i] - color_low[i]) * t) for i in range(3))
    else:
        col = color_low

    fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
    pygame.draw.rect(screen, col, fill_rect, border_radius=border_radius)

    # Gradient fill top highlight
    highlight_h = max(2, rect.height // 3)
    hl_surf = pygame.Surface((fill_w, highlight_h), pygame.SRCALPHA)
    for hy in range(highlight_h):
        a = int(70 * (1.0 - hy / highlight_h))
        pygame.draw.rect(hl_surf, (255, 255, 255, a), (0, hy, fill_w, 1))
    screen.blit(hl_surf, (rect.x, rect.y))

    # Animated shimmer at fill tip
    if show_glow and fill_w > 16:
        shimmer_a = int(100 + 80 * math.sin(pulse_t * 5))
        sh_surf = pygame.Surface((24, rect.height), pygame.SRCALPHA)
        for px in range(24):
            a = max(0, shimmer_a - abs(px - 12) * 14)
            pygame.draw.line(sh_surf, (255, 255, 255, a), (px, 0), (px, rect.height))
        screen.blit(sh_surf, (rect.x + fill_w - 12, rect.y))

    # Label text
    if label and font:
        draw_text(label, font, WHITE, rect.centerx, rect.centery)

# Keep legacy draw_gradient_bar for backward compat
def draw_gradient_bar(screen, rect, fraction, color_low, color_high, bg_color=(20,20,30),
                      border_radius=8, border_color=None, show_glow=True):
    draw_chromatic_bar(screen, rect, fraction, border_radius=border_radius, show_glow=show_glow,
                       color_full=color_high, color_low=color_low)

_bullet_cache = {}
def _get_rotated_bullet(bullet_type, width, height, color, angle_deg, pulse_t=0.0):
    """Generate and cache high-quality stylized bullets with neon bloom and directional ion wakes."""
    angle_quant = int(angle_deg / 15) * 15
    pulse_quant = int((math.sin(pulse_t * 6) + 1) * 3)  # 0 to 6
    key = (bullet_type, width, height, color[:3], angle_quant, pulse_quant)
    if key in _bullet_cache:
        return _bullet_cache[key]

    pad = 12
    surf_w, surf_h = width + pad * 2, height + pad * 2
    base = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
    rect = pygame.Rect(pad, pad, width, height)

    if bullet_type == 'plasma':
        # Up-facing player plasma bolt with radiant bloom
        halo_alpha = int(45 + pulse_quant * 8)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(10, 10), border_radius=width)
        pygame.draw.rect(base, color[:3], rect, border_radius=max(2, width // 2))
        core_rect = rect.inflate(-2, -4)
        if core_rect.width > 0 and core_rect.height > 0:
            pygame.draw.rect(base, (255, 255, 255), core_rect, border_radius=max(1, core_rect.width // 2))
        # Tapered ion wake tail
        pygame.draw.polygon(base, (*color[:3], int(65 + pulse_quant * 8)), [
            (rect.left + 1, rect.bottom), (rect.right - 1, rect.bottom), (rect.centerx, rect.bottom + 7)
        ])

    elif bullet_type == 'commander':
        # Hyper-Laser — broad dual-beam with radiant corona and starburst tip
        halo_alpha = int(60 + pulse_quant * 10)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(10, 8), border_radius=4)
        # Outer beam rail
        pygame.draw.rect(base, (*color[:3], 150), pygame.Rect(rect.centerx - 4, rect.y, 8, rect.height), border_radius=3)
        pygame.draw.rect(base, color[:3], pygame.Rect(rect.centerx - 3, rect.y, 6, rect.height))
        # Intense white-gold laser core
        pygame.draw.rect(base, (255, 255, 220), pygame.Rect(rect.centerx - 1, rect.y + 1, 2, rect.height - 2))
        # Starburst lens flare at tip
        flare_y = rect.y + 2
        pygame.draw.circle(base, (255, 255, 255), (rect.centerx, flare_y), 3)
        pygame.draw.circle(base, (*color[:3], 100), (rect.centerx, flare_y), 5, 1)

    elif bullet_type == 'heavy':
        # Heavy Plasma Torpedo — dense armored shell + pulsating energy core
        halo_alpha = int(55 + pulse_quant * 10)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(8, 6), border_radius=max(3, width // 2))
        pygame.draw.rect(base, color[:3], rect, border_radius=max(2, width // 2))
        # Superheated white core
        core_rect = rect.inflate(-2, -4)
        if core_rect.width > 0 and core_rect.height > 0:
            pygame.draw.rect(base, (255, 255, 230), core_rect, border_radius=max(1, core_rect.width // 2))
        # Tip spark
        pygame.draw.circle(base, (255, 255, 255), (rect.centerx, rect.top + 2), 2)
        # Exhaust wake
        pygame.draw.polygon(base, (*color[:3], 85), [
            (rect.left, rect.bottom), (rect.right, rect.bottom), (rect.centerx, rect.bottom + 8)
        ])

    elif bullet_type == 'elite':
        # Violet/Magenta Twin-Core Beam — sleek high-energy dart
        halo_alpha = int(50 + pulse_quant * 9)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(8, 6), border_radius=width)
        pygame.draw.rect(base, color[:3], rect, border_radius=max(2, width // 2))
        core_w = max(1, width - 2)
        core_rect = pygame.Rect(rect.x + 1, rect.y + 2, core_w, max(2, height - 4))
        pygame.draw.rect(base, (255, 240, 255), core_rect, border_radius=max(1, core_w // 2))
        # Tip spark & trailing tail
        pygame.draw.circle(base, (255, 255, 255), (rect.centerx, rect.top + 1), 2)
        pygame.draw.polygon(base, (*color[:3], 80), [
            (rect.left + 1, rect.bottom), (rect.right - 1, rect.bottom), (rect.centerx, rect.bottom + 6)
        ])

    elif bullet_type == 'phantom':
        # Spectral Phase Shard — ethereal violet-cyan missile
        halo_alpha = int(60 + pulse_quant * 12)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(8, 8), border_radius=width)
        pygame.draw.polygon(base, color[:3], [
            (rect.centerx, rect.top), (rect.right, rect.centery),
            (rect.centerx, rect.bottom), (rect.left, rect.centery)
        ])
        pygame.draw.circle(base, (220, 255, 255), (rect.centerx, rect.centery), max(1, width // 4))

    elif bullet_type == 'berserker':
        # Scarlet Spiked Bolt — aggressive angular projectile
        halo_alpha = int(55 + pulse_quant * 10)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(6, 8), border_radius=width)
        pygame.draw.rect(base, color[:3], rect, border_radius=max(2, width // 2))
        core_rect = rect.inflate(-2, -4)
        if core_rect.width > 0 and core_rect.height > 0:
            pygame.draw.rect(base, (255, 255, 255), core_rect, border_radius=max(1, core_rect.width // 2))
        pygame.draw.circle(base, (255, 255, 255), (rect.centerx, rect.top + 1), 2)
        pygame.draw.polygon(base, (*color[:3], 90), [
            (rect.left, rect.bottom), (rect.right, rect.bottom), (rect.centerx, rect.bottom + 6)
        ])

    else:
        # Standard Fighter Needle — bright crimson bolt with glowing white core
        halo_alpha = int(45 + pulse_quant * 8)
        pygame.draw.rect(base, (*color[:3], halo_alpha), rect.inflate(8, 8), border_radius=width)
        pygame.draw.rect(base, color[:3], rect, border_radius=max(2, width // 2))
        core_w = max(1, width - 2)
        core_rect = pygame.Rect(rect.x + 1, rect.y + 2, core_w, max(2, height - 4))
        pygame.draw.rect(base, (255, 255, 255), core_rect, border_radius=max(1, core_w // 2))
        pygame.draw.circle(base, (255, 240, 240), (rect.centerx, rect.top + 1), 2)
        pygame.draw.polygon(base, (*color[:3], 70), [
            (rect.left + 1, rect.bottom), (rect.right - 1, rect.bottom), (rect.centerx, rect.bottom + 6)
        ])

    rotated = pygame.transform.rotate(base, angle_quant)
    if len(_bullet_cache) > 1000:
        _bullet_cache.clear()
    _bullet_cache[key] = rotated
    return rotated

# ===========================================================
# PLASMA BULLET — Next-gen bullet visuals
# ===========================================================

def draw_plasma_bullet(screen, rect, color=NEON_CYAN, trail_particles=None, pulse_t=0.0, angle=0):
    """Draw a high-quality, directional plasma bullet."""
    rotated = _get_rotated_bullet('plasma', rect.width, rect.height, color, angle, pulse_t)
    # Center the rotated surface on the rect's center
    draw_rect = rotated.get_rect(center=rect.center)
    screen.blit(rotated, draw_rect.topleft)

def draw_enemy_bullet(screen, rect, color=RED, bullet_type='fighter', pulse_t=0.0, angle=180):
    """Draw a directional enemy bullet (default points down = 180 deg)."""
    rotated = _get_rotated_bullet(bullet_type, rect.width, rect.height, color, angle, pulse_t)
    draw_rect = rotated.get_rect(center=rect.center)
    screen.blit(rotated, draw_rect.topleft)


def draw_boss_bullet(screen, rect, color=NEON_PINK, pulse_t=0.0):
    """Large pulsing boss bullet orb with rotating outer ring."""
    r = max(rect.width, rect.height) // 2
    cx, cy = rect.centerx, rect.centery

    # Outer pulsing ring
    ring_r = r + int(3 + 2 * math.sin(pulse_t * 6))
    ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(ring_surf, (*color, 80), (ring_r + 2, ring_r + 2), ring_r, 2)
    screen.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))

    # Main orb
    pygame.draw.circle(screen, color, (cx, cy), r)
    pygame.draw.circle(screen, PLASMA_CORE, (cx, cy), max(1, r - 3))

    # Rotating tick marks
    for i in range(6):
        a = pulse_t * 3 + i * math.pi / 3
        tx = cx + int(math.cos(a) * (r + 4))
        ty = cy + int(math.sin(a) * (r + 4))
        pygame.draw.circle(screen, color, (tx, ty), 2)

# ===========================================================
# POWERUP ORBS — Next-gen powerup visuals
# ===========================================================

def draw_powerup_orb(screen, center, orb_type, now, pulse_t):
    """
    Draw a next-level powerup orb:
    - Shield: animated rotating hex shield
    - Double: dual spinning bullet icons
    """
    cx, cy = center
    pulse = math.sin(pulse_t * 3)
    r = 18 + int(3 * pulse)

    if orb_type == 'immortal':
        # Hex shield orb
        color = NEON_TEAL
        # Outer glow
        glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 40 + int(20 * pulse)), (r * 2, r * 2), r * 2)
        screen.blit(glow_surf, (cx - r * 2, cy - r * 2))
        # Hexagon body
        pts = []
        for i in range(6):
            a = pulse_t * 1.5 + i * math.pi / 3
            pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
        pygame.draw.polygon(screen, (*color, 180), pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)
        # Inner shield icon
        inner_pts = []
        for i in range(6):
            a = -pulse_t * 1.5 + i * math.pi / 3
            inner_pts.append((cx + int((r // 2) * math.cos(a)), cy + int((r // 2) * math.sin(a))))
        pygame.draw.polygon(screen, (*GLASS_WHITE, 120), inner_pts)
        draw_text("S", FONT_HP, BLACK, cx, cy)
    else:
        # Double shot orb
        color = NEON_AMBER
        glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 40 + int(20 * pulse)), (r * 2, r * 2), r * 2)
        screen.blit(glow_surf, (cx - r * 2, cy - r * 2))
        pygame.draw.circle(screen, (*color, 180), (cx, cy), r)
        pygame.draw.circle(screen, WHITE, (cx, cy), r, 2)
        # Spinning mini bullets
        for side in [-1, 1]:
            a = pulse_t * 4
            bx = cx + int(side * 8 * math.cos(a))
            by = cy + int(side * 8 * math.sin(a))
            pygame.draw.rect(screen, WHITE, pygame.Rect(bx - 2, by - 5, 4, 10), border_radius=2)
        draw_text("2X", FONT_TINY, BLACK, cx, cy)

# ===========================================================
# KILL PROGRESS RING — Circular progress indicator
# ===========================================================

def draw_kill_ring(screen, cx, cy, fraction, kills, req, color=NEON_CYAN, radius=26, pulse_t=0.0):
    """
    Draw a circular kill-count progress ring around a skull icon.
    fraction = kills / req (0.0 to 1.0)
    """
    # Background ring
    bg_surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(bg_surf, (30, 35, 50, 200), (radius + 4, radius + 4), radius, 5)
    screen.blit(bg_surf, (cx - radius - 4, cy - radius - 4))

    # Progress arc
    if fraction > 0:
        arc_surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        arc_rect = pygame.Rect(4, 4, radius * 2, radius * 2)
        end_angle = -math.pi / 2 + fraction * 2 * math.pi  # Start from top
        try:
            pygame.draw.arc(arc_surf, (*color, 220),
                            arc_rect, -math.pi / 2, end_angle, 5)
        except Exception:
            pass
        screen.blit(arc_surf, (cx - radius - 4, cy - radius - 4))

    # Glow tip at arc end
    if 0 < fraction < 1.0:
        tip_a = -math.pi / 2 + fraction * 2 * math.pi
        tip_x = cx + int(radius * math.cos(tip_a))
        tip_y = cy + int(radius * math.sin(tip_a))
        tip_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(tip_surf, (*color, 255), (7, 7), 5)
        pygame.draw.circle(tip_surf, (255, 255, 255, 200), (7, 7), 3)
        screen.blit(tip_surf, (tip_x - 7, tip_y - 7))

    # Center skull icon text
    draw_text("☠", FONT_TINY, color, cx, cy - 2)
    draw_text(f"{kills}", FONT_TINY, WHITE, cx, cy + 9)

# ===========================================================
# ORBITAL SKILL TIMER — Rotating ring for powerup duration
# ===========================================================

def draw_orbital_skill_timer(screen, cx, cy, fraction, label, color, pulse_t):
    """
    Draw a rotating orbital ring showing remaining powerup time.
    fraction = remaining_time / total_duration
    """
    r = 22
    # Dark bg
    bg = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
    pygame.draw.circle(bg, (*PANEL_BG, 200), (r + 5, r + 5), r + 2)
    screen.blit(bg, (cx - r - 5, cy - r - 5))

    # Rotating outer orbit dots
    for i in range(8):
        a = pulse_t * 3 + i * (math.pi * 2 / 8)
        dot_r = r + 4
        dx = cx + int(math.cos(a) * dot_r)
        dy = cy + int(math.sin(a) * dot_r)
        dot_alpha = int(100 + 100 * ((math.cos(a - pulse_t * 3) + 1) / 2))
        dot_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (*color, dot_alpha), (3, 3), 3)
        screen.blit(dot_surf, (dx - 3, dy - 3))

    # Progress arc (remaining time)
    if fraction > 0:
        arc_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
        arc_rect_inner = pygame.Rect(5, 5, r * 2, r * 2)
        end_angle = -math.pi / 2 + fraction * 2 * math.pi
        try:
            pygame.draw.arc(arc_surf, (*color, 220), arc_rect_inner, -math.pi / 2, end_angle, 4)
        except Exception:
            pass
        screen.blit(arc_surf, (cx - r - 5, cy - r - 5))

    # Label inside
    draw_text(label[:2], FONT_TINY, color, cx, cy)

# ===========================================================
# BADGE / PILL TAG
# ===========================================================

def draw_badge(screen, text, font, x, y, bg_color, text_color=WHITE,
               padding_x=14, padding_y=6, border_radius=20, border_color=None):
    """Draws a pill-shaped badge centered at (x, y)."""
    surf = font.render(str(text), True, text_color)
    w = surf.get_width() + padding_x * 2
    h = surf.get_height() + padding_y * 2
    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
    pygame.draw.rect(screen, bg_color, rect, border_radius=border_radius)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=1, border_radius=border_radius)
    screen.blit(surf, surf.get_rect(center=(x, y)))

# ===========================================================
# SECTION DIVIDER
# ===========================================================

def draw_divider(screen, x1, y, x2, color=NEON_CYAN, alpha=60):
    surf = pygame.Surface((x2 - x1, 2), pygame.SRCALPHA)
    surf.fill((*color, alpha))
    screen.blit(surf, (x1, y))

# ===========================================================
# ANIMATED STARFIELD — Menu backgrounds
# ===========================================================

_menu_stars = [
    [random.randint(0, 800), random.randint(0, 600),
     random.uniform(0.2, 1.8), random.randint(80, 255)]
    for _ in range(220)
]
_menu_shooting_stars = []

def draw_menu_starfield(screen, width=800, height=600):
    """Enhanced starfield with occasional shooting stars."""
    for s in _menu_stars:
        s[1] += s[2]
        if s[1] > height:
            s[0] = random.randint(0, width)
            s[1] = 0
            s[3] = random.randint(80, 255)
        r = max(1, int(s[2] * 1.4))
        brightness = s[3]
        col = (min(255, brightness // 2), min(255, brightness // 2 + 30), min(255, brightness))
        pygame.draw.circle(screen, col, (int(s[0]), int(s[1])), r)

    # Shooting star generation
    if random.random() < 0.012:
        _menu_shooting_stars.append({
            'x': float(random.randint(0, width)),
            'y': float(random.randint(0, height // 3)),
            'vx': random.uniform(4, 9),
            'vy': random.uniform(2, 5),
            'life': random.randint(18, 36),
            'max_life': 36,
        })

    for ss in _menu_shooting_stars[:]:
        ss['x'] += ss['vx']
        ss['y'] += ss['vy']
        ss['life'] -= 1
        if ss['life'] <= 0 or ss['x'] > width or ss['y'] > height:
            _menu_shooting_stars.remove(ss)
        else:
            frac = ss['life'] / ss['max_life']
            trail_len = int(30 * frac)
            s_surf = pygame.Surface((trail_len + 4, 3), pygame.SRCALPHA)
            for tx in range(trail_len):
                a = int(200 * (tx / max(1, trail_len)) * frac)
                pygame.draw.line(s_surf, (200, 220, 255, a), (tx, 1), (tx + 1, 1), 1)
            angle = math.atan2(ss['vy'], ss['vx'])
            rotated = pygame.transform.rotate(s_surf, -math.degrees(angle))
            rot_rect = rotated.get_rect(center=(int(ss['x']), int(ss['y'])))
            screen.blit(rotated, rot_rect)