"""
enemy_ai.py — Full AI/NPC scripting system for Crazyy Simulation
=================================================================
Provides:
  - EnemyAI: Per-entity FSM with Fighter, Elite, Heavy, Phantom,
              Berserker, Commander behaviors
  - WaveComposer: Builds structured enemy formations per level
  - SpawnDirector: Adaptive difficulty — monitors kill rate and
                   adjusts wave intensity in real-time
"""

import math
import random
import pygame
from settings import *


# ============================================================
# CONSTANTS
# ============================================================

WIDTH, HEIGHT = 800, 600

# Formation templates: list of (x_offset, y_offset, enemy_type)
FORMATIONS = {
    'v_formation':   [(0, 0, 'fighter'), (-50, 30, 'fighter'), (50, 30, 'fighter'),
                      (-100, 60, 'elite'),  (100, 60, 'elite')],
    'pincer':        [(-160, 0, 'elite'), (160, 0, 'elite'), (-80, -30, 'fighter'),
                      (80, -30, 'fighter'), (0, 0, 'heavy')],
    'column':        [(0, 0, 'fighter'), (0, -60, 'fighter'), (0, -120, 'elite'),
                      (0, -180, 'heavy')],
    'diamond':       [(0, -60, 'elite'), (-60, 0, 'fighter'), (60, 0, 'fighter'),
                      (0, 60, 'heavy')],
    'swarm':         [(random.randint(-200, 200), random.randint(-80, 0), 'fighter')
                      for _ in range(8)],
    'bh_spiral':     [(int(80 * math.cos(i * math.pi / 3)), int(80 * math.sin(i * math.pi / 3)), 'elite')
                      for i in range(6)],
    'elite_squad':   [(-80, 0, 'elite'), (0, -40, 'elite'), (80, 0, 'elite'),
                      (-40, 40, 'fighter'), (40, 40, 'fighter')],
    'siege_line':    [(-120, 0, 'heavy'), (-60, 0, 'heavy'), (0, 0, 'heavy'),
                      (60, 0, 'heavy'), (120, 0, 'heavy')],
    'phantom_raid':  [(0, 0, 'phantom'), (-70, 30, 'fighter'), (70, 30, 'fighter')],
    'berserker_vanguard': [(0, 0, 'berserker'), (-90, 20, 'fighter'), (90, 20, 'fighter')],
    'command_squad': [(0, 0, 'commander'), (-60, 40, 'fighter'), (60, 40, 'fighter'),
                      (-30, -40, 'elite'), (30, -40, 'elite')],
}


# ============================================================
# ENEMY AI FSM
# ============================================================

class EnemyAI:
    """
    Per-entity AI controller. Drives movement, shooting, and
    behavioral state transitions for a single enemy ship.
    """

    def __init__(self, enemy_type, level, rect, player_rect_ref, all_enemies_ref,
                 env_speed_mult=1.0):
        self.enemy_type     = enemy_type   # 'fighter','elite','heavy','phantom','berserker','commander'
        self.level          = level
        self.rect           = rect
        self.player_ref     = player_rect_ref
        self.all_enemies    = all_enemies_ref
        self.env_speed_mult = env_speed_mult

        # Shared difficulty factors
        self.ai_aggression = min(1.0, level / 16.0)
        self.ai_accuracy   = min(1.0, level / 24.0)

        # Per-entity state
        self.state      = 'descend'
        self.timer      = random.randint(0, 60)
        self.start_x    = float(rect.centerx)
        self.target_x   = float(rect.centerx)
        self.dodge_dir  = random.choice([-1, 1])
        self.sub_timer  = 0

        # Phantom-specific
        self.cloak_timer    = 0
        self.is_cloaked     = False
        self.cloak_duration = 180  # frames

        # Commander-specific
        self.bodyguard_spawned = False

        # Berserker-specific
        self.berserk_charge = False

        # Group sync reference (set externally by SpawnDirector)
        self.squad_id = None

        # Bullet output buffer: list of bullet dicts to add
        self.pending_bullets = []

    def update(self, bullets, now_ms=0):
        """
        Run one frame of AI logic. Returns list of new bullet dicts to spawn.
        Modifies self.rect in place.
        """
        self.timer     += 1
        self.sub_timer += 1
        self.pending_bullets.clear()

        dispatch = {
            'fighter':    self._update_fighter,
            'elite':      self._update_elite,
            'heavy':      self._update_heavy,
            'phantom':    self._update_phantom,
            'berserker':  self._update_berserker,
            'commander':  self._update_commander,
        }
        fn = dispatch.get(self.enemy_type)
        if fn:
            fn(bullets, now_ms)

        # Clamp x
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

        return list(self.pending_bullets)

    # ----------------------------------------------------------
    # FIGHTER: Fast dive-bombers with dodge logic
    # ----------------------------------------------------------

    def _update_fighter(self, bullets, now_ms):
        base_spd  = (2.8 + self.ai_aggression * 1.8) * self.env_speed_mult
        level_spd = min(self.level, 12) * 0.15

        # Dodge incoming player bullets
        if self.ai_aggression > 0.35:
            for b in bullets:
                if (abs(b['rect'].centerx - self.rect.centerx) < 45 and
                        b['rect'].top < self.rect.bottom + 40 and b['rect'].centery < self.rect.centery):
                    self.dodge_dir = 1 if self.rect.centerx < 400 else -1
                    break

        # Strafe + player-tracking
        track_w = self.ai_aggression * 0.55
        target_x = self.player_ref.centerx * track_w + self.start_x * (1 - track_w)
        strafe   = math.sin(self.timer * 0.09) * (3.5 + self.ai_aggression * 3.0) * self.env_speed_mult

        # Suicide dive at level 30+
        if self.level >= 30 and self.ai_aggression > 0.9 and self.timer % 180 < 30:
            # Kamikaze direct charge at player
            dx = self.player_ref.centerx - self.rect.centerx
            dy = self.player_ref.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += int((dx / dist) * (base_spd + level_spd) * 2.2)
            self.rect.y += int((dy / dist) * (base_spd + level_spd) * 2.2)
        else:
            self.rect.x += int(strafe) + int((target_x - self.rect.centerx) * 0.012 * self.ai_aggression)
            self.rect.y += int(base_spd + level_spd)

    # ----------------------------------------------------------
    # ELITE: Flanking interceptors with prediction
    # ----------------------------------------------------------

    def _update_elite(self, bullets, now_ms):
        base_spd = (2.2 + self.ai_aggression * 1.4) * self.env_speed_mult

        # State machine transition
        cooldown = max(50, int(130 - self.ai_aggression * 90))
        if self.timer % cooldown == 0:
            roll = random.random()
            if roll < self.ai_aggression * 0.6:
                self.state = 'dive'
                predicted_x = (self.player_ref.centerx +
                               (self.player_ref.centerx - self.rect.centerx) * 0.25 * self.ai_accuracy)
                self.target_x = float(max(30, min(WIDTH - 30, int(predicted_x))))
            elif roll < 0.75:
                self.state = 'strafe'
                self.target_x = float(random.randint(60, WIDTH - 60))
            else:
                self.state = 'flank'
                # Go to whichever side of the player has more open space
                self.target_x = float(
                    self.player_ref.right + 80
                    if self.player_ref.centerx < WIDTH // 2
                    else self.player_ref.left - 80
                )

        if self.state == 'dive':
            dx = self.target_x - self.rect.centerx
            self.rect.x += int(dx * 0.06 * (1 + self.ai_aggression))
            self.rect.y += int(base_spd * 1.4)
        elif self.state == 'flank':
            dx = self.target_x - self.rect.centerx
            self.rect.x += int(dx * 0.05)
            self.rect.y += int(base_spd * 0.8)
        else:  # strafe
            wave = math.sin(self.timer * 0.055) * 7
            self.rect.x = int(self.start_x + wave)
            if self.rect.centerx < self.player_ref.centerx - 12:
                self.start_x += max(1, int(self.ai_aggression * 3.5))
            elif self.rect.centerx > self.player_ref.centerx + 12:
                self.start_x -= max(1, int(self.ai_aggression * 3.5))
            self.rect.y += int(base_spd)

        # Coordinated strike (Level 25+): sync fire with squad
        if self.level >= 25 and self.squad_id is not None:
            pass  # Managed by SpawnDirector

    # ----------------------------------------------------------
    # HEAVY: Siege tankers with suppression fire
    # ----------------------------------------------------------

    def _update_heavy(self, bullets, now_ms):
        base_spd = (1.5 + self.ai_aggression * 0.9) * self.env_speed_mult

        cooldown = max(70, int(200 - self.ai_aggression * 120))
        if self.timer % cooldown == 0:
            if random.random() < self.ai_aggression * 0.8:
                # Artillery: stop and fire
                self.state = 'artillery'
                self.sub_timer = 0
            elif random.random() < 0.5:
                self.state = 'position'
                self.target_x = float(max(40, min(WIDTH - 40,
                    self.player_ref.centerx + random.randint(-50, 50))))
            else:
                self.state = 'advance'
                self.target_x = float(random.randint(80, WIDTH - 80))

        if self.state == 'artillery':
            # Hold position, fire 5-way spread
            if self.sub_timer == 0 or self.sub_timer == 40:
                self._fire_heavy_spread()
            self.sub_timer += 1
            if self.sub_timer > 80:
                self.state = 'advance'
        else:
            dx = self.target_x - self.rect.centerx
            move_x = min(abs(dx), max(1, int(2.5 + self.ai_aggression * 3)))
            if dx > 0:
                self.rect.x += move_x
            elif dx < 0:
                self.rect.x -= move_x
            self.rect.y += int(base_spd)

    def _fire_heavy_spread(self):
        dmg = max(3, min(self.level, 5)) * 5
        for angle_deg in [-30, -15, 0, 15, 30]:
            rad = math.radians(angle_deg + 90)
            spd = 6.8
            self.pending_bullets.append({
                'rect': pygame.Rect(self.rect.centerx - 5, self.rect.bottom, 10, 16),
                'damage': dmg, 'color': ORANGE,
                'vx': math.cos(rad) * spd,
                'vy': math.sin(rad) * spd,
                'btype': 'heavy'
            })

    # ----------------------------------------------------------
    # PHANTOM: Cloaking ambush predator (Level 31+)
    # ----------------------------------------------------------

    def _update_phantom(self, bullets, now_ms):
        base_spd = (2.0 + self.ai_aggression * 1.5) * self.env_speed_mult

        # Cloak cycle
        if not self.is_cloaked and self.timer % 240 < 60:
            self.is_cloaked  = True
            self.cloak_timer = self.cloak_duration
        if self.is_cloaked:
            self.cloak_timer -= 1
            if self.cloak_timer <= 0:
                self.is_cloaked = False

        if self.is_cloaked:
            # While cloaked: flank and get behind the player
            target_x = self.player_ref.centerx
            target_y = self.player_ref.bottom + 60  # Behind the player
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += int((dx / dist) * base_spd * 1.8)
            self.rect.y += int((dy / dist) * base_spd * 1.8)
        else:
            # Uncloaked: fire homing missiles and normal strafe
            strafe = math.sin(self.timer * 0.07) * 4 * self.env_speed_mult
            self.rect.x += int(strafe)
            self.rect.y += int(base_spd * 0.8)

            # Homing missile (fires periodically after uncloaking)
            if self.timer % 60 == 0:
                px = self.player_ref.centerx
                py = self.player_ref.centery
                dx = px - self.rect.centerx
                dy = py - self.rect.centery
                dist = max(1, math.hypot(dx, dy))
                spd = 7.2
                dmg = max(4, min(self.level // 3, 15))
                self.pending_bullets.append({
                    'rect': pygame.Rect(self.rect.centerx - 5, self.rect.bottom, 10, 14),
                    'damage': dmg,
                    'color': NEON_VIOLET,
                    'vx': (dx / dist) * spd,
                    'vy': (dy / dist) * spd,
                    'btype': 'phantom',
                    'homing': True,
                    'player_ref': self.player_ref,
                })

    def get_alpha(self):
        """Returns draw alpha (30 = cloaked, 255 = visible)."""
        return 40 if self.is_cloaked else 255

    # ----------------------------------------------------------
    # BERSERKER: Hyper-aggressive tank (Level 35+)
    # ----------------------------------------------------------

    def _update_berserker(self, bullets, now_ms):
        base_spd = (3.5 + self.ai_aggression * 2.0) * self.env_speed_mult

        # Alternate between charging and 360-fire
        cycle = self.timer % 240
        if cycle < 180:
            # Charge directly at player
            dx = self.player_ref.centerx - self.rect.centerx
            dy = self.player_ref.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += int((dx / dist) * base_spd)
            self.rect.y += int((dy / dist) * base_spd)
        elif cycle == 180:
            # 360-degree fire burst
            for angle_deg in range(0, 360, 30):
                rad = math.radians(angle_deg)
                spd = 6.6
                dmg = max(5, min(self.level // 2, 18))
                self.pending_bullets.append({
                    'rect': pygame.Rect(self.rect.centerx - 5, self.rect.centery, 10, 10),
                    'damage': dmg, 'color': NEON_SCARLET,
                    'vx': math.cos(rad) * spd,
                    'vy': math.sin(rad) * spd,
                    'btype': 'berserker'
                })
        else:
            # Brief retreat
            self.rect.y -= int(base_spd * 0.5)

    # ----------------------------------------------------------
    # COMMANDER: Squad leader with bodyguards (Level 38+)
    # ----------------------------------------------------------

    def _update_commander(self, bullets, now_ms):
        base_spd = (1.8 + self.ai_aggression * 1.0) * self.env_speed_mult

        # Orbit slowly above player
        orbit_r = 120
        a = self.timer * 0.025
        target_x = float(max(80, min(WIDTH - 80,
            self.player_ref.centerx + int(math.cos(a) * orbit_r * 0.5))))
        dx = target_x - self.rect.centerx
        self.rect.x += int(dx * 0.04)
        self.rect.y = max(50, min(200, self.rect.y + int(base_spd * 0.3)))

        # Periodic guided burst fire at player
        if self.timer % 35 == 0:
            px = self.player_ref.centerx
            py = self.player_ref.centery
            dx2 = px - self.rect.centerx
            dy2 = py - self.rect.centery
            dist = max(1, math.hypot(dx2, dy2))
            spd = 8.0
            dmg = max(6, min(self.level // 2, 20))
            self.pending_bullets.append({
                'rect': pygame.Rect(self.rect.centerx - 5, self.rect.bottom, 10, 18),
                'damage': dmg, 'color': NEON_GOLD,
                'vx': (dx2 / dist) * spd * 0.3,
                'vy': (dy2 / dist) * spd,
                'btype': 'commander'
            })


# ============================================================
# WAVE COMPOSER — Builds structured waves per level
# ============================================================

class WaveComposer:
    """
    Builds enemy wave templates based on current level and environment.
    Returns a list of spawn instructions: [(type, x, y), ...]
    """

    @staticmethod
    def compose(level, env=1):
        """
        Returns list of (enemy_type, spawn_x, spawn_y) tuples for a wave.
        env: 1=Galaxy, 2=Nebula, 3=Blackhole
        """
        cx = WIDTH // 2

        if level <= 3:
            # Tutorial: single column of fighters
            return [('fighter', cx + (i - 1) * 80, -60) for i in range(level)]

        elif level <= 6:
            # Warm-up: V-formation fighters
            return [
                ('fighter', cx - 80, -60), ('fighter', cx, -30), ('fighter', cx + 80, -60),
            ] + ([('elite', cx, -90)] if level >= 5 else [])

        elif level <= 10:
            # Mixed formation
            tmpl = random.choice(['v_formation', 'diamond', 'column'])
            return WaveComposer._from_template(tmpl, cx, level)

        elif level <= 20:
            # Nebula zone: flanking and squad patterns
            tmpl = random.choice(['pincer', 'elite_squad', 'v_formation', 'diamond'])
            return WaveComposer._from_template(tmpl, cx, level)

        elif level <= 30:
            # Advanced: siege lines and coordinated elites
            tmpl = random.choice(['siege_line', 'elite_squad', 'pincer', 'swarm'])
            return WaveComposer._from_template(tmpl, cx, level)

        else:
            # Blackhole: phantom raids, berserker vanguard, command squads
            options = ['swarm', 'phantom_raid', 'berserker_vanguard']
            if level >= 38:
                options.append('command_squad')
            tmpl = random.choice(options)
            return WaveComposer._from_template(tmpl, cx, level)

    @staticmethod
    def _from_template(tmpl_name, cx, level):
        template = FORMATIONS.get(tmpl_name, FORMATIONS['v_formation'])
        result = []
        for (ox, oy, etype) in template:
            x = max(30, min(WIDTH - 30, cx + ox))
            y = oy - 80  # Off-screen above
            # Upgrade fighter→elite at high levels
            if level >= 25 and etype == 'fighter' and random.random() < 0.3:
                etype = 'elite'
            result.append((etype, x, y))
        return result


# ============================================================
# SPAWN DIRECTOR — Adaptive difficulty system
# ============================================================

class SpawnDirector:
    """
    Monitors kill rate and dynamically adjusts spawn intensity.
    Called once per frame during gameplay.
    """

    def __init__(self, level, env=1):
        self.level       = level
        self.kill_count  = 0
        self.timer       = 0           # Frame counter
        self.kpm_window  = []          # [(tick_of_kill), ...] for rolling window

        # Env 2 (Nebula) starts 25% more intense; Env 3 (Blackhole) starts 50% more intense
        # This ensures the player's unlocked skills are needed from Level 1 in higher envs
        env_start_intensity = {1: 1.0, 2: 1.25, 3: 1.5}.get(env, 1.0)
        self.intensity   = env_start_intensity
        self.wave_queue  = []          # [(etype, x, y), ...] waiting to spawn
        self.next_wave_t = 0           # Frame to spawn next wave
        self.squad_clock = {}          # squad_id → last fire tick (for coord strikes)
        # Shorter initial interval for higher envs (faster first wave)
        base_interval = max(180, 400 - level * 5)
        env_interval_mult = {1: 1.0, 2: 0.80, 3: 0.65}.get(env, 1.0)
        self._wave_interval = max(120, int(base_interval * env_interval_mult))

    def record_kill(self):
        self.kill_count += 1
        self.kpm_window.append(self.timer)

    def update(self, fighters, elites, heavies, phantoms, berserkers, commanders,
               fighter_img, elite_img, heavy_img, player_rect, level,
               env_speed_mult=1.0):
        """
        Called every frame. Returns list of new enemy dicts to add.
        """
        self.timer += 1
        new_enemies = []

        # Prune kill window to last 30 seconds (1800 frames)
        self.kpm_window = [t for t in self.kpm_window if self.timer - t < 1800]

        # Adaptive intensity: adjust based on kills per 10 seconds (600 frames)
        recent = sum(1 for t in self.kpm_window if self.timer - t < 600)
        # If player is killing fast → increase intensity; if slow → ease off a bit
        if recent >= 12:
            self.intensity = min(1.5, self.intensity + 0.02)
        elif recent <= 3:
            self.intensity = max(0.7, self.intensity - 0.015)

        # Enforce maximum active enemies based on level
        total_enemies = len(fighters) + len(elites) + len(heavies) + len(phantoms) + len(berserkers) + len(commanders)
        max_active = 15 + min(level // 3, 15)  # Cap at ~28 enemies total

        # Spawn queued enemies one at a time (pause if too many enemies)
        if self.wave_queue and self.timer >= self.next_wave_t and total_enemies < max_active:
            etype, ex, ey = self.wave_queue.pop(0)
            enemy = self._make_enemy(etype, ex, ey, player_rect, level,
                                     fighters, elites, heavies, env_speed_mult)
            if enemy:
                new_enemies.append((etype, enemy))
            self.next_wave_t = self.timer + max(8, int(30 / self.intensity))

        # Trigger new wave
        if not self.wave_queue and self.timer >= self.next_wave_t + self._wave_interval:
            # Wait until enemies clear out a bit before launching next wave
            if total_enemies < max_active - 5:
                wave = WaveComposer.compose(level)
                self.wave_queue.extend(wave)
                self.next_wave_t = self.timer
                # Significantly increased interval for higher levels
                base_interval = max(240, 500 - level * 4) 
                self._wave_interval = max(200, int(base_interval / self.intensity))
            else:
                self.next_wave_t += 30  # Delay wave if screen is crowded

        return new_enemies

    def _make_enemy(self, etype, ex, ey, player_rect, level, fighters, elites, heavies,
                    env_speed_mult):
        """Create a raw enemy dict (same schema as main.py)."""
        rect = pygame.Rect(ex, ey, 50, 50)  # Size adjusted in main.py at draw time

        if etype == 'fighter':
            return {
                'rect': rect, 'hp': 1, 'max_hp': 1,
                'start_x': float(ex), 'time': 0, 'type': 'fighter',
                'dive_speed': random.uniform(2.8, 4.5),
                'ai_state': 'descend', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': random.choice([-1, 1]),
                'ai_controller': None  # Will be set in main.py
            }
        elif etype == 'elite':
            hp = max(2, min(level // 3 + 1, 6))
            return {
                'rect': rect, 'hp': hp, 'max_hp': hp,
                'start_x': float(ex), 'time': 0, 'type': 'elite',
                'ai_state': 'strafe', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': random.choice([-1, 1]),
                'ai_controller': None
            }
        elif etype == 'heavy':
            hp = max(5, min(level // 2, 16))
            return {
                'rect': pygame.Rect(ex - 15, ey, 80, 80),
                'hp': hp, 'max_hp': hp,
                'start_x': float(ex), 'time': 0, 'type': 'heavy',
                'ai_state': 'advance', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': 1,
                'ai_controller': None
            }
        elif etype == 'phantom':
            hp = max(3, min(level // 4, 8))
            return {
                'rect': rect, 'hp': hp, 'max_hp': hp,
                'start_x': float(ex), 'time': 0, 'type': 'phantom',
                'ai_state': 'descend', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': 1,
                'is_cloaked': False, 'cloak_timer': 0,
                'ai_controller': None
            }
        elif etype == 'berserker':
            hp = max(10, min(level // 2 + 5, 22))
            return {
                'rect': pygame.Rect(ex - 10, ey, 90, 90),
                'hp': hp, 'max_hp': hp,
                'start_x': float(ex), 'time': 0, 'type': 'berserker',
                'ai_state': 'charge', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': 1,
                'ai_controller': None
            }
        elif etype == 'commander':
            hp = max(15, min(level // 2 + 10, 30))
            return {
                'rect': pygame.Rect(ex - 20, ey, 100, 80),
                'hp': hp, 'max_hp': hp,
                'start_x': float(ex), 'time': 0, 'type': 'commander',
                'ai_state': 'orbit', 'ai_timer': 0,
                'target_x': float(ex), 'dodge_dir': 1,
                'bodyguard_spawned': False,
                'ai_controller': None
            }
        return None

    def reset(self, level):
        self.level       = level
        self.kill_count  = 0
        self.timer       = 0
        self.kpm_window  = []
        self.intensity   = 1.0
        self.wave_queue  = []
        self.next_wave_t = 0
        self._wave_interval = max(180, 400 - level * 5)


# ============================================================
# STANDALONE AI UPDATE — Used by main.py per-enemy per-frame
# ============================================================

def run_enemy_ai(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy, BH_X=400, BH_Y=300, is_blackhole=False):
    """
    Full per-enemy AI update. Modifies e['rect'] in place.
    Returns list of new bullet dicts to add to enemy_bullets.
    """
    new_bullets = []
    e_type = e.get('type', 'fighter')
    e['time'] = e.get('time', 0) + 1
    e['start_x'] = e.get('start_x', float(e['rect'].x))

    if 'ai_state' not in e:
        e['ai_state'] = 'descend'
        e['ai_timer'] = 0
        e['target_x'] = float(e['rect'].x)
        e['dodge_dir'] = random.choice([-1, 1])

    e['ai_timer'] = e.get('ai_timer', 0) + 1

    if e_type == 'fighter':
        _ai_fighter(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy)
    elif e_type == 'elite':
        _ai_elite(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy)
    elif e_type == 'heavy':
        new_bullets = _ai_heavy(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy)
    elif e_type == 'phantom':
        _ai_phantom(e, bullets, player_rect, level, env_speed_mult, ai_aggression)
    elif e_type == 'berserker':
        new_bullets = _ai_berserker(e, bullets, player_rect, level, env_speed_mult, ai_aggression)
    elif e_type == 'commander':
        new_bullets = _ai_commander(e, bullets, player_rect, level, env_speed_mult, ai_aggression)

    # Blackhole gravity
    if is_blackhole:
        edx = BH_X - e['rect'].centerx
        edy = BH_Y - e['rect'].centery
        edist = math.hypot(edx, edy)
        if edist > 0:
            e_pull = max(0.9, min(4.5, 600.0 / (edist + 70.0)))
            e['rect'].x += int((edx / edist) * e_pull)
            e['rect'].y += int((edy / edist) * e_pull)

    e['rect'].x = max(0, min(WIDTH - e['rect'].width, e['rect'].x))
    return new_bullets


def _ai_fighter(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy):
    base_spd = (2.8 + ai_aggression * 1.8) * env_speed_mult
    level_spd = min(level, 12) * 0.15

    # Dodge
    if ai_aggression > 0.35:
        for b in bullets:
            if (abs(b['rect'].centerx - e['rect'].centerx) < 45 and
                    b['rect'].top < e['rect'].bottom + 40 and b['rect'].centery < e['rect'].centery):
                e['dodge_dir'] = 1 if e['rect'].centerx < 400 else -1
                break

    # Suicide dive at level 30+
    if level >= 30 and ai_aggression > 0.88 and e['time'] % 200 < 25:
        dx = player_rect.centerx - e['rect'].centerx
        dy = player_rect.centery - e['rect'].centery
        dist = max(1, math.hypot(dx, dy))
        e['rect'].x += int((dx / dist) * (base_spd + level_spd) * 2.2)
        e['rect'].y += int((dy / dist) * (base_spd + level_spd) * 2.2)
    else:
        track_w = ai_aggression * 0.55
        target_x = player_rect.centerx * track_w + e['start_x'] * (1 - track_w)
        strafe = math.sin(e['time'] * 0.09) * (3.5 + ai_aggression * 3.0) * env_speed_mult
        e['rect'].x += int(strafe) + int((target_x - e['rect'].centerx) * 0.012 * ai_aggression)
        e['rect'].y += int(base_spd + level_spd)


def _ai_elite(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy):
    base_spd = (2.2 + ai_aggression * 1.4) * env_speed_mult
    cooldown = max(50, int(130 - ai_aggression * 90))

    if e['ai_timer'] % cooldown == 0:
        roll = random.random()
        if roll < ai_aggression * 0.6:
            e['ai_state'] = 'dive'
            predicted_x = (player_rect.centerx +
                           (player_rect.centerx - e['rect'].centerx) * 0.25 * ai_accuracy)
            e['target_x'] = float(max(30, min(WIDTH - 30, int(predicted_x))))
        elif roll < 0.75:
            e['ai_state'] = 'strafe'
            e['target_x'] = float(random.randint(60, WIDTH - 60))
        else:
            e['ai_state'] = 'flank'
            e['target_x'] = float(
                player_rect.right + 80 if player_rect.centerx < WIDTH // 2
                else player_rect.left - 80
            )

    if e['ai_state'] == 'dive':
        dx = e['target_x'] - e['rect'].centerx
        e['rect'].x += int(dx * 0.06 * (1 + ai_aggression))
        e['rect'].y += int(base_spd * 1.4)
    elif e['ai_state'] == 'flank':
        dx = e['target_x'] - e['rect'].centerx
        e['rect'].x += int(dx * 0.05)
        e['rect'].y += int(base_spd * 0.8)
    else:
        wave = math.sin(e['time'] * 0.055) * 7
        e['rect'].x = int(e['start_x'] + wave)
        if e['rect'].centerx < player_rect.centerx - 12:
            e['start_x'] += max(1, int(ai_aggression * 3.5))
        elif e['rect'].centerx > player_rect.centerx + 12:
            e['start_x'] -= max(1, int(ai_aggression * 3.5))
        e['rect'].y += int(base_spd)


def _ai_heavy(e, bullets, player_rect, level, env_speed_mult, ai_aggression, ai_accuracy):
    new_bullets = []
    base_spd = (1.5 + ai_aggression * 0.9) * env_speed_mult
    cooldown = max(70, int(200 - ai_aggression * 120))

    if e['ai_timer'] % cooldown == 0:
        if random.random() < ai_aggression * 0.7:
            e['ai_state'] = 'artillery'
            e['sub_timer'] = 0 if 'sub_timer' not in e else e['sub_timer']
        elif random.random() < 0.5:
            e['ai_state'] = 'position'
            e['target_x'] = float(max(40, min(WIDTH - 40,
                player_rect.centerx + random.randint(-50, 50))))
        else:
            e['ai_state'] = 'advance'

    e.setdefault('sub_timer', 0)

    if e['ai_state'] == 'artillery':
        if e['sub_timer'] in (0, 40):
            dmg = max(3, min(level, 5)) * 5
            for angle_deg in [-30, -15, 0, 15, 30]:
                rad = math.radians(angle_deg + 90)
                spd = 6.8
                new_bullets.append({
                    'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].bottom, 10, 16),
                    'damage': dmg, 'color': ORANGE,
                    'vx': math.cos(rad) * spd,
                    'vy': math.sin(rad) * spd,
                    'btype': 'heavy'
                })
        e['sub_timer'] += 1
        if e['sub_timer'] > 80:
            e['ai_state'] = 'advance'
            e['sub_timer'] = 0
    else:
        dx = e['target_x'] - e['rect'].centerx
        move_x = min(abs(dx), max(1, int(2.5 + ai_aggression * 3)))
        if dx > 0:
            e['rect'].x += move_x
        elif dx < 0:
            e['rect'].x -= move_x
        e['rect'].y += int(base_spd)

    return new_bullets


def _ai_phantom(e, bullets, player_rect, level, env_speed_mult, ai_aggression):
    base_spd = (2.0 + ai_aggression * 1.5) * env_speed_mult
    e.setdefault('is_cloaked', False)
    e.setdefault('cloak_timer', 0)

    cycle = e['time'] % 280
    if not e['is_cloaked'] and cycle == 0:
        e['is_cloaked']  = True
        e['cloak_timer'] = 180

    if e['is_cloaked']:
        e['cloak_timer'] -= 1
        if e['cloak_timer'] <= 0:
            e['is_cloaked'] = False

    if e['is_cloaked']:
        target_x = player_rect.centerx
        target_y = player_rect.bottom + 50
        dx = target_x - e['rect'].centerx
        dy = target_y - e['rect'].centery
        dist = max(1, math.hypot(dx, dy))
        e['rect'].x += int((dx / dist) * base_spd * 1.8)
        e['rect'].y += int((dy / dist) * base_spd * 1.8)
    else:
        strafe = math.sin(e['time'] * 0.07) * 4 * env_speed_mult
        e['rect'].x += int(strafe)
        e['rect'].y += int(base_spd * 0.8)


def _ai_berserker(e, bullets, player_rect, level, env_speed_mult, ai_aggression):
    new_bullets = []
    base_spd = (3.5 + ai_aggression * 2.0) * env_speed_mult
    cycle = e['time'] % 240

    if cycle < 180:
        dx = player_rect.centerx - e['rect'].centerx
        dy = player_rect.centery - e['rect'].centery
        dist = max(1, math.hypot(dx, dy))
        e['rect'].x += int((dx / dist) * base_spd)
        e['rect'].y += int((dy / dist) * base_spd)
    elif cycle == 180:
        for angle_deg in range(0, 360, 30):
            rad = math.radians(angle_deg)
            spd = 6.6
            dmg = max(5, min(level // 2, 18))
            new_bullets.append({
                'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].centery, 10, 10),
                'damage': dmg, 'color': NEON_SCARLET,
                'vx': math.cos(rad) * spd,
                'vy': math.sin(rad) * spd,
                'btype': 'berserker'
            })
    else:
        e['rect'].y -= int(base_spd * 0.4)

    return new_bullets


def _ai_commander(e, bullets, player_rect, level, env_speed_mult, ai_aggression):
    new_bullets = []
    base_spd = (1.8 + ai_aggression * 1.0) * env_speed_mult
    a = e['time'] * 0.025
    orbit_r = 120
    target_x = float(max(80, min(WIDTH - 80,
        player_rect.centerx + int(math.cos(a) * orbit_r * 0.5))))
    dx = target_x - e['rect'].centerx
    e['rect'].x += int(dx * 0.04)
    e['rect'].y = max(50, min(200, e['rect'].y + int(base_spd * 0.3)))

    if e['ai_timer'] % 35 == 0:
        px = player_rect.centerx
        py = player_rect.centery
        dx2 = px - e['rect'].centerx
        dy2 = py - e['rect'].centery
        dist = max(1, math.hypot(dx2, dy2))
        spd = 8.0
        dmg = max(6, min(level // 2, 20))
        new_bullets.append({
            'rect': pygame.Rect(e['rect'].centerx - 5, e['rect'].bottom, 10, 18),
            'damage': dmg, 'color': NEON_GOLD,
            'vx': (dx2 / dist) * spd * 0.3,
            'vy': (dy2 / dist) * spd,
            'btype': 'commander'
        })

    return new_bullets
