import pygame
import os
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