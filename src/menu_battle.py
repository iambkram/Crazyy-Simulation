import pygame
import math
import random
from settings import *

class MenuBattleSimulation:
    """
    Live autonomous space combat background for the Main Menu (State 0).
    Features:
      - Autonomous immortal player starship with dodging & aimbot AI
      - Procedural balanced enemy squadron spawning (Fighters, Elites, Heavies)
      - Dynamic laser combat with muzzle flares, laser streams, and explosions
      - Adaptive background rendering based on current selected environment:
          * Galaxy / Nebula: Seamless vertical scrolling background + drifting stars
          * Black Hole: Gravitational singularity swirl with stars vanishing into the event horizon
      - Automatic freeze/pause when navigating away to other states, resuming seamlessly on return
    """
    def __init__(self, assets):
        self.assets = assets
        self.player_img = assets['player_img']
        self.fighter_img = assets['fighter_img']
        self.elite_img = assets['elite_img']
        self.heavy_img = assets['heavy_img']
        self.galaxy_bg = assets['galaxy_bg']
        self.nebula_bg = assets['nebula_bg']
        self.blackhole_bg = assets['blackhole_bg']

        # Sound references (optional ambient playback)
        self.shoot_snd = assets.get('shoot_snd')
        self.expl_snd = assets.get('expl_snd')
        self.hit_snd = assets.get('hit_snd')

        # Player Ship State (Autonomous & Immortal)
        self.player_x = float(WIDTH // 2)
        self.player_y = float(HEIGHT - 130)
        self.player_vx = 0.0
        self.player_vy = 0.0
        self.player_fire_cooldown = 0
        self.shield_flash_timer = 0
        self.thruster_timer = 0

        # Combat Entities
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.particles = []

        # Spawn Controllers (Balanced, never cluttered)
        self.spawn_timer = 30
        self.max_enemies = 3

        # Background Scrolling
        self.bg_scroll_y = 0.0
        self.bg_height = self.galaxy_bg.get_height()

        # Starfield (drifting for Galaxy/Nebula, orbital swirl for Blackhole)
        self.stars = []
        for _ in range(120):
            self.stars.append({
                'x': float(random.randint(0, WIDTH)),
                'y': float(random.randint(0, HEIGHT)),
                'spd': random.uniform(0.4, 1.8),
                'brightness': random.randint(80, 240),
                'r': random.choice([1, 1, 2])
            })

        self.tint_overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        self.tint_overlay.fill((5, 8, 18, 125))
        self.shield_surf = pygame.Surface((70, 70), pygame.SRCALPHA)

        # Pre-seed initial battlefield enemies so it's active immediately
        self._seed_initial_battle()

    def _seed_initial_battle(self):
        """Seed 2 initial enemies so the menu starts mid-battle."""
        self.enemies.append({
            'type': 'fighter',
            'img': self.fighter_img,
            'x': float(WIDTH // 2 - 120),
            'y': float(120),
            'hp': 1,
            'max_hp': 1,
            'spd': 1.8,
            't': 0.0,
            'fire_timer': 35
        })
        self.enemies.append({
            'type': 'elite',
            'img': self.elite_img,
            'x': float(WIDTH // 2 + 140),
            'y': float(90),
            'hp': 2,
            'max_hp': 2,
            'spd': 1.4,
            't': 1.5,
            'fire_timer': 60
        })

    def update(self, dt=1.0, current_env=1):
        """
        Advance one frame of the simulation.
        Only called while on Main Menu (State 0). Freezes in memory otherwise.
        """
        # ==========================================
        # 1. BACKGROUND SCROLLING & STARFIELD
        # ==========================================
        is_bh = (current_env == 3)
        if not is_bh:
            self.bg_scroll_y += 0.5 * dt
            if self.bg_scroll_y >= self.bg_height:
                self.bg_scroll_y = 0.0

            for s in self.stars:
                s['y'] += s['spd'] * dt
                if s['y'] > HEIGHT:
                    s['y'] = 0.0
                    s['x'] = float(random.randint(0, WIDTH))
        else:
            # Black Hole Gravitational Singularity at (400, 240)
            bh_x, bh_y = 400.0, 240.0
            for s in self.stars:
                dx = bh_x - s['x']
                dy = bh_y - s['y']
                dist = math.hypot(dx, dy)
                if dist < 20.0:
                    # Respawn along outer perimeter
                    ang = random.uniform(0, 2 * math.pi)
                    spawn_d = random.uniform(360, 500)
                    s['x'] = bh_x + math.cos(ang) * spawn_d
                    s['y'] = bh_y + math.sin(ang) * spawn_d
                else:
                    pull = max(0.6, min(2.8, s['spd'] * 0.5 + 0.6))
                    s['x'] += (dx / dist) * pull * dt
                    s['y'] += (dy / dist) * pull * dt

        # ==========================================
        # 2. ENEMY SPAWNING (Balanced & Cinematic)
        # ==========================================
        self.spawn_timer -= 1 * dt
        if self.spawn_timer <= 0 and len(self.enemies) < self.max_enemies:
            self.spawn_timer = random.randint(90, 160)
            e_type = random.choices(['fighter', 'elite', 'heavy'], weights=[55, 30, 15])[0]

            if e_type == 'fighter':
                self.enemies.append({
                    'type': 'fighter',
                    'img': self.fighter_img,
                    'x': float(random.randint(80, WIDTH - 80)),
                    'y': -45.0,
                    'hp': 1,
                    'max_hp': 1,
                    'spd': random.uniform(1.8, 2.6),
                    't': random.uniform(0, 10),
                    'fire_timer': random.randint(40, 90)
                })
            elif e_type == 'elite':
                self.enemies.append({
                    'type': 'elite',
                    'img': self.elite_img,
                    'x': float(random.randint(100, WIDTH - 100)),
                    'y': -55.0,
                    'hp': 2,
                    'max_hp': 2,
                    'spd': random.uniform(1.4, 2.0),
                    't': random.uniform(0, 10),
                    'fire_timer': random.randint(50, 100)
                })
            elif e_type == 'heavy':
                self.enemies.append({
                    'type': 'heavy',
                    'img': self.heavy_img,
                    'x': float(random.randint(120, WIDTH - 120)),
                    'y': -65.0,
                    'hp': 4,
                    'max_hp': 4,
                    'spd': random.uniform(1.0, 1.4),
                    't': 0.0,
                    'fire_timer': random.randint(60, 120)
                })

        # ==========================================
        # 3. AUTONOMOUS PLAYER SHIP AI
        # ==========================================
        # Engine exhaust particles
        self.thruster_timer += 1
        if self.thruster_timer % 2 == 0:
            for ox in [-12, 12]:
                self.particles.append({
                    'x': self.player_x + ox,
                    'y': self.player_y + 24,
                    'vx': random.uniform(-0.6, 0.6),
                    'vy': random.uniform(2.5, 4.5),
                    'life': 14,
                    'max_life': 14,
                    'col': random.choice([NEON_CYAN, (180, 240, 255), WHITE]),
                    'size': random.uniform(2.0, 4.0)
                })

        # AI Targeting & Threat Evaluation
        target_x = self.player_x
        target_y = float(HEIGHT - 130)

        # Threat Assessment: Scan for incoming enemy bullets
        nearest_bullet = None
        min_b_dist = 9999.0
        for b in self.enemy_bullets:
            dx = b['rect'].centerx - self.player_x
            dy = self.player_y - b['rect'].centery
            # Only consider bullets falling toward the player
            if 0 < dy < 180 and abs(dx) < 60:
                dist = math.hypot(dx, dy)
                if dist < min_b_dist:
                    min_b_dist = dist
                    nearest_bullet = b

        if nearest_bullet is not None:
            # Bullet avoidance: Dodge left or right away from bullet trajectory
            b_cx = nearest_bullet['rect'].centerx
            if self.player_x < b_cx:
                target_x = max(80.0, self.player_x - 55.0)
            else:
                target_x = min(WIDTH - 80.0, self.player_x + 55.0)
        else:
            # Offensive Tracking: Line up horizontally with closest enemy
            best_enemy = None
            max_y = -999.0
            for e in self.enemies:
                if e['y'] > max_y and e['y'] < self.player_y:
                    max_y = e['y']
                    best_enemy = e

            if best_enemy is not None:
                # Track enemy X
                target_x = best_enemy['x']
                # Add slight combat weave
                target_y = float(HEIGHT - 130 + math.sin(pygame.time.get_ticks() * 0.003) * 20)
            else:
                # Idle combat patrol
                target_x = float(WIDTH // 2 + math.sin(pygame.time.get_ticks() * 0.002) * 140)

        # Smooth Player Movement Physics
        dx = target_x - self.player_x
        dy = target_y - self.player_y
        max_speed = 5.2
        self.player_x += max(-max_speed, min(max_speed, dx * 0.14)) * dt
        self.player_y += max(-max_speed * 0.5, min(max_speed * 0.5, dy * 0.10)) * dt

        # Keep player within screen bounds
        self.player_x = max(60.0, min(WIDTH - 60.0, self.player_x))
        self.player_y = max(380.0, min(HEIGHT - 80.0, self.player_y))
        player_rect = self.player_img.get_rect(center=(int(self.player_x), int(self.player_y)))

        # Player Auto-Firing
        if self.player_fire_cooldown > 0:
            self.player_fire_cooldown -= 1 * dt
        elif len(self.enemies) > 0:
            # Fire twin laser bolts
            self.player_bullets.append({
                'rect': pygame.Rect(int(self.player_x - 14), int(self.player_y - 12), 5, 16)
            })
            self.player_bullets.append({
                'rect': pygame.Rect(int(self.player_x + 14), int(self.player_y - 12), 5, 16)
            })
            self.player_fire_cooldown = random.randint(12, 18)

        # ==========================================
        # 4. ENEMY SHIPS UPDATE & ATTACK
        # ==========================================
        for e in self.enemies[:]:
            e['t'] += 0.05 * dt
            e['y'] += e['spd'] * dt

            # Maneuver archetypes
            if e['type'] == 'fighter':
                e['x'] += math.sin(e['t'] * 1.5) * 3.2 * dt
            elif e['type'] == 'elite':
                # Track player smoothly
                if e['x'] < self.player_x - 15:
                    e['x'] += 1.2 * dt
                elif e['x'] > self.player_x + 15:
                    e['x'] -= 1.2 * dt
            elif e['type'] == 'heavy':
                e['x'] += math.sin(e['t'] * 0.6) * 1.2 * dt

            e['x'] = max(40.0, min(WIDTH - 40.0, e['x']))
            e_rect = e['img'].get_rect(center=(int(e['x']), int(e['y'])))

            # Enemy Shooting
            e['fire_timer'] -= 1 * dt
            if e['fire_timer'] <= 0 and e['y'] > 40:
                if e['type'] == 'fighter':
                    self.enemy_bullets.append({
                        'rect': pygame.Rect(int(e['x'] - 2), int(e['y'] + 18), 5, 14),
                        'col': RED,
                        'vy': 6.0
                    })
                    e['fire_timer'] = random.randint(55, 95)
                elif e['type'] == 'elite':
                    self.enemy_bullets.append({
                        'rect': pygame.Rect(int(e['x'] - 14), int(e['y'] + 18), 5, 14),
                        'col': MAGENTA,
                        'vy': 5.5
                    })
                    self.enemy_bullets.append({
                        'rect': pygame.Rect(int(e['x'] + 14), int(e['y'] + 18), 5, 14),
                        'col': MAGENTA,
                        'vy': 5.5
                    })
                    e['fire_timer'] = random.randint(65, 110)
                elif e['type'] == 'heavy':
                    self.enemy_bullets.append({
                        'rect': pygame.Rect(int(e['x'] - 4), int(e['y'] + 24), 8, 16),
                        'col': ORANGE,
                        'vy': 5.0
                    })
                    e['fire_timer'] = random.randint(70, 120)

            # Despawn if leaving bottom
            if e['y'] > HEIGHT + 60:
                self.enemies.remove(e)

        # ==========================================
        # 5. BULLETS & COMBAT HIT COLLISIONS
        # ==========================================
        # Player Bullets Movement & Enemy Hits
        for pb in self.player_bullets[:]:
            pb['rect'].y -= int(13 * dt)
            hit = False

            for e in self.enemies[:]:
                e_rect = e['img'].get_rect(center=(int(e['x']), int(e['y'])))
                if pb['rect'].colliderect(e_rect):
                    e['hp'] -= 1
                    hit = True

                    # Hit sparks
                    for _ in range(6):
                        self.particles.append({
                            'x': pb['rect'].centerx,
                            'y': pb['rect'].top,
                            'vx': random.uniform(-3, 3),
                            'vy': random.uniform(-3, 3),
                            'life': 10,
                            'max_life': 10,
                            'col': CYAN,
                            'size': random.uniform(2, 4)
                        })

                    if e['hp'] <= 0:
                        # Supernova ship explosion
                        for _ in range(22):
                            self.particles.append({
                                'x': e['x'],
                                'y': e['y'],
                                'vx': random.uniform(-5.5, 5.5),
                                'vy': random.uniform(-5.5, 5.5),
                                'life': random.randint(18, 32),
                                'max_life': 30,
                                'col': random.choice(BLAST_COLORS + [NEON_CYAN, NEON_GOLD]),
                                'size': random.uniform(3, 7)
                            })
                        if e in self.enemies:
                            self.enemies.remove(e)
                    break

            if hit or pb['rect'].bottom < 0:
                if pb in self.player_bullets:
                    self.player_bullets.remove(pb)

        # Enemy Bullets Movement & Player Hits (Immortal Shield Flash)
        for eb in self.enemy_bullets[:]:
            eb['rect'].y += int(eb.get('vy', 6.0) * dt)

            # Check collision with Immortal Player
            if eb['rect'].colliderect(player_rect):
                self.shield_flash_timer = 18  # Flash cyan barrier
                # Shield spark dissipation
                for _ in range(8):
                    self.particles.append({
                        'x': eb['rect'].centerx,
                        'y': eb['rect'].centery,
                        'vx': random.uniform(-3.5, 3.5),
                        'vy': random.uniform(-3.5, 3.5),
                        'life': 12,
                        'max_life': 12,
                        'col': random.choice([NEON_CYAN, WHITE, NEON_PURPLE]),
                        'size': random.uniform(2.5, 4.5)
                    })
                self.enemy_bullets.remove(eb)
            elif eb['rect'].top > HEIGHT:
                self.enemy_bullets.remove(eb)

        # ==========================================
        # 6. PARTICLES UPDATE
        # ==========================================
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= 1 * dt
            if p['life'] <= 0:
                self.particles.remove(p)

        if self.shield_flash_timer > 0:
            self.shield_flash_timer -= 1 * dt

    def draw(self, screen, current_env=1):
        """
        Render the live space combat background behind the Main Menu UI.
        """
        # --- A. Render Environment Background ---
        is_bh = (current_env == 3)
        if not is_bh:
            bg_tex = self.galaxy_bg if current_env == 1 else self.nebula_bg
            screen.blit(bg_tex, (0, int(self.bg_scroll_y)))
            screen.blit(bg_tex, (0, int(self.bg_scroll_y) - self.bg_height))

            # Drifting starfield
            for s in self.stars:
                col = (s['brightness'], s['brightness'], min(255, s['brightness'] + 20))
                pygame.draw.circle(screen, col, (int(s['x']), int(s['y'])), s['r'])
        else:
            screen.blit(self.blackhole_bg, (0, 0))
            # Inward swirling stars
            for s in self.stars:
                col = (s['brightness'], s['brightness'], 255)
                pygame.draw.circle(screen, col, (int(s['x']), int(s['y'])), s['r'])

        # --- B. Render Enemy Ships ---
        for e in self.enemies:
            e_rect = e['img'].get_rect(center=(int(e['x']), int(e['y'])))
            screen.blit(e['img'], e_rect)

        # --- C. Render Lasers / Bullets ---
        # Player Bullets (Glowing Neon Cyan with white core)
        for pb in self.player_bullets:
            pygame.draw.rect(screen, NEON_CYAN, pb['rect'], border_radius=3)
            pygame.draw.rect(screen, WHITE, pb['rect'].inflate(-2, -4), border_radius=2)

        # Enemy Bullets
        for eb in self.enemy_bullets:
            pygame.draw.rect(screen, eb['col'], eb['rect'], border_radius=3)
            pygame.draw.rect(screen, WHITE, eb['rect'].inflate(-2, -4), border_radius=2)

        # --- D. Render Particles ---
        for p in self.particles:
            alpha_frac = max(0.0, p['life'] / max(1.0, p.get('max_life', 14.0)))
            r = max(1, int(p['size'] * alpha_frac))
            pygame.draw.circle(screen, p['col'], (int(p['x']), int(p['y'])), r)

        # --- E. Render Player Ship & Immortal Shield Aura ---
        p_rect = self.player_img.get_rect(center=(int(self.player_x), int(self.player_y)))
        screen.blit(self.player_img, p_rect)

        # Shield Barrier Flash Ripple (on bullet impact)
        if self.shield_flash_timer > 0:
            shield_r = max(p_rect.width, p_rect.height) // 2 + 10
            shield_surf = pygame.Surface((shield_r * 2, shield_r * 2), pygame.SRCALPHA)
            s_alpha = int(140 * (self.shield_flash_timer / 18.0))
            pygame.draw.circle(shield_surf, (*NEON_CYAN, s_alpha), (shield_r, shield_r), shield_r, width=3)
            pygame.draw.circle(shield_surf, (255, 255, 255, s_alpha // 2), (shield_r, shield_r), shield_r - 2, width=1)
            screen.blit(shield_surf, (p_rect.centerx - shield_r, p_rect.centery - shield_r))

        # --- F. Frosted Menu Tint (Keeps text & buttons perfectly readable) ---
        screen.blit(self.tint_overlay, (0, 0))
