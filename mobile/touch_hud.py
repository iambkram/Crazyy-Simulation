"""On-screen touch buttons. Drag on the playfield is 1:1 and does not start on these rects."""
import pygame
import math
from settings import WIDTH, HEIGHT, NEON_CYAN, NEON_GOLD, WHITE


def pause_rect():
    return pygame.Rect(WIDTH - 55, 15, 40, 40)


def fire_rect():
    return pygame.Rect(WIDTH - 108, HEIGHT - 118, 92, 92)


def hits_hud(pos):
    return pause_rect().collidepoint(pos) or fire_rect().collidepoint(pos)


def draw_fire_button(screen, held, font, pulse_t=0.0):
    """Draw a premium, responsive fire button with pulsing glow ring."""
    rect = fire_rect()
    cx, cy = rect.center
    outer_r = rect.width // 2

    # Outer pulsing glow ring (always visible, intensifies on hold)
    glow_alpha = int(80 + 60 * math.sin(pulse_t * 4)) if not held else 180
    glow_r = outer_r + (6 if held else 4)
    glow_surf = pygame.Surface((glow_r * 2 + 8, glow_r * 2 + 8), pygame.SRCALPHA)
    glow_center = (glow_r + 4, glow_r + 4)
    glow_color = NEON_GOLD if held else NEON_CYAN
    pygame.draw.circle(glow_surf, (*glow_color, glow_alpha), glow_center, glow_r, 4)
    # Soft outer halo
    pygame.draw.circle(glow_surf, (*glow_color, glow_alpha // 3), glow_center, glow_r + 3, 2)
    screen.blit(glow_surf, (cx - glow_r - 4, cy - glow_r - 4))

    # Main button body — semi-transparent glass fill
    btn_surf = pygame.Surface((outer_r * 2 + 4, outer_r * 2 + 4), pygame.SRCALPHA)
    btn_center = (outer_r + 2, outer_r + 2)
    fill_alpha = 120 if held else 50
    fill_color = (40, 100, 50, fill_alpha) if held else (15, 35, 50, fill_alpha)
    pygame.draw.circle(btn_surf, fill_color, btn_center, outer_r)
    screen.blit(btn_surf, (cx - outer_r - 2, cy - outer_r - 2))

    # Crisp neon border ring
    border_color = NEON_GOLD if held else NEON_CYAN
    border_w = 3 if held else 2
    pygame.draw.circle(screen, border_color, (cx, cy), outer_r, border_w)

    # Inner accent ring
    inner_r = outer_r - 8
    inner_alpha = 160 if held else 80
    inner_surf = pygame.Surface((inner_r * 2 + 4, inner_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(inner_surf, (*border_color, inner_alpha),
                       (inner_r + 2, inner_r + 2), inner_r, 1)
    screen.blit(inner_surf, (cx - inner_r - 2, cy - inner_r - 2))

    # "FIRE" label with subtle shadow
    shadow = font.render("FIRE", True, (0, 0, 0))
    label = font.render("FIRE", True, WHITE)
    screen.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
    screen.blit(label, label.get_rect(center=(cx, cy)))

    return rect
