"""PC windowing: 800x600 windowed, resizable, desktop fullscreen (F11 / settings)."""
import pygame
from settings import WIDTH, HEIGHT


def display_flags(use_scaled=True, resizable=True, fullscreen=False):
    flags = 0
    if use_scaled:
        flags |= pygame.SCALED
    if resizable and not fullscreen:
        flags |= pygame.RESIZABLE
    if fullscreen:
        flags |= pygame.FULLSCREEN
    return flags


def create_window(fullscreen=False, use_scaled=True, resizable=True):
    return pygame.display.set_mode(
        (WIDTH, HEIGHT),
        display_flags(use_scaled=use_scaled, resizable=resizable, fullscreen=fullscreen),
    )


def apply_display_mode(screen, fullscreen):
    """Toggle desktop fullscreen while keeping SCALED letterboxing."""
    target = bool(fullscreen)
    current = bool(screen.get_flags() & pygame.FULLSCREEN)
    if current != target:
        pygame.display.toggle_fullscreen()
    return pygame.display.get_surface(), target
