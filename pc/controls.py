"""PC keyboard + mouse mapping (WASD / arrows / Space / Enter / Esc / F11)."""
import pygame


MENU_CONFIRM = (pygame.K_RETURN, pygame.K_KP_ENTER)
MENU_BACK = (pygame.K_ESCAPE,)
PAUSE = (pygame.K_p, pygame.K_ESCAPE)
FIRE = (pygame.K_SPACE,)
MOVE_LEFT = (pygame.K_a, pygame.K_LEFT)
MOVE_RIGHT = (pygame.K_d, pygame.K_RIGHT)
MOVE_UP = (pygame.K_w, pygame.K_UP)
MOVE_DOWN = (pygame.K_s, pygame.K_DOWN)
FULLSCREEN = (pygame.K_F11,)


def is_move_left(keys):
    return keys[pygame.K_a] or keys[pygame.K_LEFT]


def is_move_right(keys):
    return keys[pygame.K_d] or keys[pygame.K_RIGHT]


def is_move_up(keys):
    return keys[pygame.K_w] or keys[pygame.K_UP]


def is_move_down(keys):
    return keys[pygame.K_s] or keys[pygame.K_DOWN]


def is_firing(keys, mouse_pressed, auto_fire, pause_hovered):
    return keys[pygame.K_SPACE] or (mouse_pressed and not pause_hovered) or auto_fire
