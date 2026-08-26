"""
PC edition entry point.

Run:  python main_pc.py
Pack: pyinstaller Crazyy-Simulation.spec
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
    from src.platform_config import configure_pc
except ImportError:
    from platform_config import configure_pc

configure_pc()

try:
    import src.game  # noqa: F401  — shared engine; starts the PC game loop
except ImportError:
    import game  # noqa: F401

