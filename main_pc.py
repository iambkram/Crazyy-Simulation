"""
PC edition entry point.

Run:  python main_pc.py
Pack: pyinstaller Crazyy-Simulation.spec
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)

from platform_config import configure_pc

configure_pc()
import game  # noqa: F401  — shared engine; starts the PC game loop
