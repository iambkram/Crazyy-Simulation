"""Keep a logical 800x600 playfield and scale it to any phone aspect (16:9, 19.5:9, 20:9)."""
import pygame
from settings import WIDTH, HEIGHT


def display_flags():
    flags = pygame.FULLSCREEN
    if hasattr(pygame, "SCALED"):
        flags |= pygame.SCALED
    return flags


def create_window():
    """Fullscreen hardware-scaled window. pygame.SCALED letterboxes extra-tall 19.5:9 / 20:9 screens."""
    return pygame.display.set_mode((WIDTH, HEIGHT), display_flags())


def logical_from_finger(event):
    """Convert normalized FINGER* coordinates (0..1) into logical 800x600 pixels."""
    return int(event.x * WIDTH), int(event.y * HEIGHT)
