import random

# --- Display Settings ---
WIDTH, HEIGHT = 800, 600

# --- Base Colors ---
WHITE, BLACK    = (255, 255, 255), (5, 5, 15)
RED, BLUE       = (255, 50, 50),   (30, 144, 255)
GREEN           = (50, 255, 50)
YELLOW          = (220, 220, 0)
CYAN            = (0, 255, 255)
MAGENTA         = (255, 0, 255)
PURPLE          = (150, 0, 255)
ORANGE          = (255, 140, 0)
DARK_GRAY       = (30, 30, 40)
LIGHT_GRAY      = (60, 60, 70)

# --- Extended Neon Palette ---
NEON_CYAN       = (0, 230, 255)       # Primary accent — borders, titles
NEON_PINK       = (255, 50, 140)      # Danger, boss, game over
NEON_GOLD       = (255, 210, 50)      # Coins, rewards, revive
NEON_GREEN      = (50, 255, 120)      # Success, health, victory
NEON_ORANGE     = (255, 160, 30)      # Warnings, retries
NEON_PURPLE     = (190, 60, 255)      # Blackhole accent
NEON_BLUE       = (30, 120, 255)      # Info, store, nav

# --- UI Surface Colors ---
PANEL_BG        = (10, 14, 24)        # Deep space panel fill
PANEL_MID       = (18, 24, 38)        # Slightly lighter panel
PANEL_DARK      = (6, 8, 16)          # Extra dark layer
DARK_BLUE       = (10, 20, 50)        # Dark blue tint
MID_GRAY        = (45, 50, 65)        # Mid-tone for inactive elements

# --- Particle / Blast Colors ---
BLAST_COLORS = [
    (255, 255, 255),
    (255, 200, 0),
    (255, 100, 0),
    (80, 80, 80)
]

# --- Game Costs & Settings ---
hp_costs     = [10, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
speed_costs  = [100, 200, 400, 600]
bullet_costs = [1000, 2000, 4000]