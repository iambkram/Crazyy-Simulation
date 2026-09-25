"""PC windowing: 800x600 windowed, resizable, desktop fullscreen (F11 / settings)."""
import pygame
try:
    from settings import WIDTH, HEIGHT
except ImportError:
    from src.settings import WIDTH, HEIGHT


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
    if screen is None:
        screen = pygame.display.get_surface()
    if screen is not None:
        try:
            current = bool(screen.get_flags() & pygame.FULLSCREEN)
            if current != target:
                try:
                    pygame.display.toggle_fullscreen()
                except (pygame.error, Exception):
                    pass
        except Exception:
            pass
    surf = pygame.display.get_surface()
    return (surf if surf is not None else screen), target

