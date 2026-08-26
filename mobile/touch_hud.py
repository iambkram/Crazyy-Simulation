"""On-screen touch buttons. Drag on the playfield is 1:1 and does not start on these rects."""
import pygame
from settings import WIDTH, HEIGHT, NEON_CYAN, NEON_GOLD, WHITE


def pause_rect():
    return pygame.Rect(WIDTH - 55, 15, 40, 40)


def fire_rect():
    return pygame.Rect(WIDTH - 108, HEIGHT - 118, 92, 92)


def hits_hud(pos):
    return pause_rect().collidepoint(pos) or fire_rect().collidepoint(pos)


def draw_fire_button(screen, held, font):
    rect = fire_rect()
    fill = (40, 90, 40) if held else (18, 36, 28)
    border = NEON_GOLD if held else NEON_CYAN
    pygame.draw.circle(screen, fill, rect.center, rect.width // 2)
    pygame.draw.circle(screen, border, rect.center, rect.width // 2, 3)
    label = font.render("FIRE", True, WHITE)
    screen.blit(label, label.get_rect(center=rect.center))
    return rect
