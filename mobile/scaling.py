"""Keep a logical 800x600 playfield and scale it to any phone aspect (16:9, 19.5:9, 20:9)."""
import pygame
from settings import WIDTH, HEIGHT


import os
import sys

def is_android_device():
    return ('ANDROID_ARGUMENT' in os.environ or 
            'ANDROID_ROOT' in os.environ or 
            getattr(sys, 'platform', '') == 'android' or
            'ANDROID_BOOTLOGO' in os.environ)

def display_flags():
    flags = 0
    if is_android_device():
        flags |= pygame.FULLSCREEN
    else:
        flags |= pygame.RESIZABLE
    if hasattr(pygame, "SCALED"):
        flags |= pygame.SCALED
    return flags


def create_window():
    """Hardware-scaled window. Fullscreen on Android, windowed test simulator on PC."""
    win = pygame.display.set_mode((WIDTH, HEIGHT), display_flags())
    if not is_android_device():
        pygame.display.set_caption("Crazyy Simulation [Mobile Edition — Touch Simulator]")
    return win


def logical_from_finger(event):
    """Convert normalized FINGER* coordinates (0..1) into logical 800x600 pixels."""
    return int(event.x * WIDTH), int(event.y * HEIGHT)
