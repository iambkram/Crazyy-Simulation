"""Android hardware back button and auto-pause when the app is minimized."""
import pygame


def android_back_key():
    return getattr(pygame, "K_AC_BACK", None)


def is_android_back(event):
    if event.type != pygame.KEYDOWN:
        return False
    key = android_back_key()
    return bool(key is not None and event.key == key)


def background_event_types():
    types = []
    for name in ("APP_WILLENTERBACKGROUND", "APP_DIDENTERBACKGROUND"):
        value = getattr(pygame, name, None)
        if value is not None:
            types.append(value)
    return tuple(types)


def foreground_event_types():
    types = []
    for name in ("APP_DIDENTERFOREGROUND", "APP_WILLENTERFOREGROUND"):
        value = getattr(pygame, name, None)
        if value is not None:
            types.append(value)
    return tuple(types)


def is_app_minimized(event):
    return event.type in background_event_types()


def is_app_restored(event):
    return event.type in foreground_event_types()


def on_minimize():
    try:
        pygame.mixer.pause()
        pygame.mixer.music.pause()
    except Exception:
        pass


def on_restore():
    try:
        pygame.mixer.unpause()
        pygame.mixer.music.unpause()
    except Exception:
        pass
