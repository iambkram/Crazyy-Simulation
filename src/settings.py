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

# --- Extended Premium Palette (NEW) ---
NEON_TEAL       = (0, 255, 200)       # Plasma bullets, shield
NEON_AMBER      = (255, 180, 0)       # Elite enemy, warm glow
NEON_CRIMSON    = (220, 20, 60)       # Boss health, danger
NEON_ELECTRIC   = (120, 200, 255)     # Electric discharge arcs
NEON_LIME       = (160, 255, 0)       # Victory accent, XP
NEON_VIOLET     = (160, 50, 255)      # Phantom enemy, cloaking
NEON_SCARLET    = (255, 40, 80)       # Berserker, rage mode
GLASS_WHITE     = (220, 240, 255)     # Glassmorphism highlight
DEEP_SPACE      = (3, 4, 12)          # Deepest BG fill
PANEL_GLOW      = (0, 180, 255)       # Holographic panel glow
PLASMA_CORE     = (200, 240, 255)     # Bullet inner core
PLASMA_TRAIL    = (0, 200, 255)       # Bullet trail

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
# Extended skill trees up to 25-30 levels each based on progression math
hp_costs = [int(50 * (1.25 ** i)) for i in range(25)]
speed_costs = [int(150 * (1.35 ** i)) for i in range(15)]
bullet_costs = [int(800 * (1.45 ** i)) for i in range(12)]
firerate_costs = [int(250 * (1.30 ** i)) for i in range(20)]

# Quality Presets
QUALITY_LOW = 'low'
QUALITY_MEDIUM = 'medium'
QUALITY_HIGH = 'high'

# Quality-scaled particle counts
QUALITY_PARTICLES = {
    'low':    {'debris': 50,  'god_rays': 4,  'thruster_density': 0.4, 'stars': 60,  'trail': 2,  'explosion': 12},
    'medium': {'debris': 100, 'god_rays': 8,  'thruster_density': 0.7, 'stars': 120, 'trail': 5,  'explosion': 24},
    'high':   {'debris': 180, 'god_rays': 14, 'thruster_density': 1.0, 'stars': 200, 'trail': 8,  'explosion': 40},
}

# ============================================================
# DIFFICULTY CURVE — Levels 1–40
# Controls how hard each level feels. Each environment starts
# harder than where the previous one ended.
# ============================================================
def get_difficulty(level):
    """Returns (spawn_chance, fire_chance, enemy_speed_mult, boss_aggression)
    for a given level (1-40)."""
    # Levels 1–10 (Galaxy intro)
    if level == 1:
        return 80, 200, 0.6, 0.1
    elif level == 2:
        return 70, 180, 0.65, 0.15
    elif level == 3:
        return 62, 160, 0.7, 0.2
    elif level == 4:
        return 55, 145, 0.75, 0.25
    elif level == 5:
        return 50, 130, 0.8, 0.3
    elif level <= 10:
        t = (level - 5) / 5.0  # 0.0 to 1.0
        sc = int(50 - t * 18)
        fc = int(130 - t * 50)
        sm = 0.8 + t * 0.15
        ba = 0.3 + t * 0.2
        return sc, fc, sm, ba
    # Levels 11–20 (Nebula zone — starts harder than Galaxy Lvl 10)
    elif level <= 20:
        t = (level - 11) / 9.0  # 0.0 to 1.0
        sc = int(28 - t * 8)
        fc = int(75 - t * 25)
        sm = 0.98 + t * 0.12
        ba = 0.52 + t * 0.18
        return sc, fc, sm, ba
    # Levels 21–30 (Nebula advanced — harder again)
    elif level <= 30:
        t = (level - 21) / 9.0
        sc = int(18 - t * 5)
        fc = int(48 - t * 14)
        sm = 1.12 + t * 0.08
        ba = 0.72 + t * 0.16
        return sc, fc, sm, ba
    # Levels 31–40 (Blackhole — maximum difficulty)
    else:
        t = (level - 31) / 9.0
        sc = int(12 - t * 4)
        fc = int(32 - t * 10)
        sm = 1.22 + t * 0.1
        ba = 0.90 + t * 0.1
        return max(8, sc), max(20, fc), sm, min(1.0, ba)


# ============================================================
# ENEMY CONFIGURATION — Per type, per level range
# ============================================================
ENEMY_CAPS = {
    # (max_fighters, max_elites, max_heavies) per level range
    'galaxy_easy':   (3, 0, 0),    # Levels 1-2
    'galaxy_warm':   (5, 2, 0),    # Levels 3-4
    'galaxy_mixed':  (6, 3, 1),    # Levels 5-7
    'galaxy_hard':   (8, 4, 2),    # Levels 8-10
    'nebula_start':  (9, 5, 3),    # Levels 11-15
    'nebula_mid':    (10, 6, 4),   # Levels 16-20
    'nebula_hard':   (11, 7, 5),   # Levels 21-25
    'nebula_elite':  (12, 8, 5),   # Levels 26-30
    'bh_hard':       (12, 8, 6),   # Levels 31-35
    'bh_extreme':    (13, 9, 6),   # Levels 36-40
}

def get_enemy_caps(level):
    """Return (max_fighters, max_elites, max_heavies, enable_phantom, enable_berserker, enable_commander)."""
    phantom   = level >= 31
    berserker = level >= 35
    commander = level >= 38
    if level <= 2:
        return 3, 0, 0, phantom, berserker, commander
    elif level <= 4:
        return 5, 2, 0, phantom, berserker, commander
    elif level <= 7:
        return 6, 3, 1, phantom, berserker, commander
    elif level <= 10:
        return 8, 4, 2, phantom, berserker, commander
    elif level <= 15:
        return 9, 5, 3, phantom, berserker, commander
    elif level <= 20:
        return 10, 6, 4, phantom, berserker, commander
    elif level <= 25:
        return 11, 7, 5, phantom, berserker, commander
    elif level <= 30:
        return 12, 8, 5, phantom, berserker, commander
    elif level <= 35:
        return 12, 8, 6, phantom, berserker, commander
    else:
        return 13, 9, 6, phantom, berserker, commander


# ============================================================
# BOSS KILL REQUIREMENTS — Levels 1–40
# ============================================================
def get_boss_kill_req(level):
    """How many enemies the player must kill before the boss spawns."""
    if level == 1:
        return 12
    elif level <= 5:
        return 10 + level * 4        # 14–30
    elif level <= 10:
        return 30 + (level - 5) * 8  # 38–70
    elif level <= 20:
        return 75 + (level - 10) * 6  # 81–135
    elif level <= 30:
        return 140 + (level - 20) * 5  # 145–190
    else:
        return 195 + (level - 30) * 3  # 198–222 (capped at ~225)