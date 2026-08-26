"""
Mobile edition entry point.

Touch: 1:1 drag + on-screen FIRE / pause.
Screen: logical 800x600 scaled fullscreen (16:9, 19.5:9, 20:9).
Android: hardware back (K_AC_BACK) and auto-pause on minimize.

Buildozer uses root main.py which delegates here.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from src.platform_config import configure_mobile
except ImportError:
    from platform_config import configure_mobile

configure_mobile()

try:
    import src.game  # noqa: F401  — shared engine; starts the mobile game loop
except ImportError:
    import game  # noqa: F401