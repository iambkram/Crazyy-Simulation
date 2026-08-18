import random

# --- Display Settings ---
WIDTH, HEIGHT = 800, 600

# --- Colors ---
WHITE, BLACK = (255, 255, 255), (5, 5, 15)
RED, BLUE = (255, 50, 50), (30, 144, 255)
GREEN = (50, 255, 50)
YELLOW = (220, 220, 0)
CYAN, MAGENTA, PURPLE, ORANGE = (0, 255, 255), (255, 0, 255), (150, 0, 255), (255, 140, 0)
DARK_GRAY, LIGHT_GRAY = (30, 30, 40), (60, 60, 70)

BLAST_COLORS = [
    (255, 255, 255),  # White (Ekdam core blast ki chamak)
    (255, 200, 0),    # Bright Yellow (Aag)
    (255, 100, 0),    # Orange (Failti hui aag)
    (80, 80, 80)      # Dark Gray (Dhuaan / Smoke)
]

# --- Game Costs & Settings ---
hp_costs = [10, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
speed_costs = [100, 200, 400, 600]
bullet_costs = [1000, 2000, 4000]

# --- Loading Logic ---
# 0.5 speed par 60 FPS mein 10 seconds (600 frames) lagenge 300 tak pahunchne mein
LOAD_SPEED_FIXED = 0.5
STUTTER_POINTS = [60, 150, 220, 280]