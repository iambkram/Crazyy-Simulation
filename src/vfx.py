import pygame
import math
import random
from settings import *


class VisualEffectsEngine:
    """
    Next-Level Visual Effects Engine for Crazyy Simulation.
    Provides:
      - Multi-layer plasma bullet trails
      - 5-stage cinematic explosion system
      - Electric discharge arcs
      - Impact ripple shockwaves
      - Ambient environment particles
      - Engine thruster plumes for all ships
      - 'Supernova Cataclysm' multi-stage Boss destruction
    """

    def __init__(self):
        self.visual_quality = 'high'

        # Thruster particles: [x, y, vx, vy, life, max_life, col, size]
        self.thruster_particles = []

        # Bullet trail particles: [x, y, vx, vy, life, max_life, col, size]
        self.trail_particles = []

        # Explosion particles: {'x','y','vx','vy','life','max_life','col','size','stage'}
        self.explosion_particles = []

        # Impact ripples: {'x','y','r','max_r','alpha','spd','col'}
        self.impact_ripples = []

        # Electric arcs: {'pts','life','col','width'}
        self.electric_arcs = []

        # Ambient environment particles
        self.ambient_particles = []

        # Boss cataclysm state
        self.boss_shockwaves  = []
        self.boss_debris      = []
        self.boss_sparks      = []
        self.boss_lightning   = []
        self.boss_flash_alpha = 0.0
        self.screen_shake     = [0.0, 0.0]

        # Reusable surfaces
        self._thruster_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        self._trail_surf    = pygame.Surface((12, 12), pygame.SRCALPHA)

        # Ambient ticker
        self._ambient_t = 0.0

    def set_quality(self, quality):
        self.visual_quality = quality

    def reset_boss_effects(self):
        self.boss_shockwaves.clear()
        self.boss_debris.clear()
        self.boss_sparks.clear()
        self.boss_lightning.clear()
        self.boss_flash_alpha = 0.0
        self.screen_shake = [0.0, 0.0]

    def clear_all(self):
        self.thruster_particles.clear()
        self.trail_particles.clear()
        self.explosion_particles.clear()
        self.impact_ripples.clear()
        self.electric_arcs.clear()
        self.ambient_particles.clear()
        self.reset_boss_effects()

    # =========================================================================
    # 1. ENGINE THRUSTERS
    # =========================================================================

    def emit_player_thruster(self, centerx, bottom_y):
        """Dual glowing cyan/teal plasma plumes for the player ship."""
        q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
        if random.random() > q['thruster_density']:
            return
        for ox in [-14, 14]:
            self.thruster_particles.append([
                centerx + ox + random.uniform(-2, 2),
                bottom_y,
                random.uniform(-0.5, 0.5),
                random.uniform(3.5, 7.0),
                14, 14,
                random.choice([NEON_TEAL, NEON_CYAN, (180, 255, 255), WHITE]),
                random.uniform(2.5, 4.5)
            ])
            # Inner bright core
            self.thruster_particles.append([
                centerx + ox + random.uniform(-0.5, 0.5),
                bottom_y + 2,
                random.uniform(-0.2, 0.2),
                random.uniform(4.5, 8.0),
                8, 8,
                WHITE,
                random.uniform(1.0, 2.0)
            ])

    def emit_enemy_thruster(self, centerx, top_y, enemy_type='fighter', width=40):
        """Color-coded thrusters for each enemy type."""
        q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
        if random.random() > q['thruster_density']:
            return

        if enemy_type == 'fighter':
            for ox in [-8, 8]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1, 1), top_y + 4,
                    random.uniform(-0.4, 0.4), random.uniform(-5.0, -2.5),
                    10, 10,
                    random.choice([(255, 80, 20), (255, 140, 0), (255, 60, 0)]),
                    random.uniform(2.0, 3.5)
                ])
        elif enemy_type == 'elite':
            for ox in [-14, 14]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1.5, 1.5), top_y + 4,
                    random.uniform(-0.5, 0.5), random.uniform(-4.5, -2.0),
                    12, 12,
                    random.choice([NEON_PURPLE, NEON_PINK, MAGENTA, WHITE]),
                    random.uniform(2.5, 4.0)
                ])
        elif enemy_type == 'heavy':
            for ox in [-20, 0, 20]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-2, 2), top_y + 6,
                    random.uniform(-0.8, 0.8), random.uniform(-3.5, -1.8),
                    16, 16,
                    random.choice([ORANGE, YELLOW, (255, 100, 30), WHITE]),
                    random.uniform(3.5, 6.0)
                ])
        elif enemy_type == 'phantom':
            # Phantom: faint violet wisps
            for ox in [-10, 10]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-2, 2), top_y + 4,
                    random.uniform(-0.6, 0.6), random.uniform(-4.0, -2.0),
                    10, 10,
                    random.choice([NEON_VIOLET, (180, 80, 255), (140, 60, 220)]),
                    random.uniform(2.0, 3.5)
                ])
        elif enemy_type == 'berserker':
            # Berserker: chaotic red/orange gouts
            for ox in [-22, -8, 8, 22]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-3, 3), top_y + 6,
                    random.uniform(-1.5, 1.5), random.uniform(-6.0, -3.0),
                    18, 18,
                    random.choice([NEON_SCARLET, RED, ORANGE, WHITE]),
                    random.uniform(4.0, 7.0)
                ])
        elif enemy_type == 'commander':
            # Commander: gold/white command signal jets
            for ox in [-16, 0, 16]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1, 1), top_y + 4,
                    random.uniform(-0.5, 0.5), random.uniform(-4.0, -2.0),
                    14, 14,
                    random.choice([NEON_GOLD, (255, 240, 160), WHITE]),
                    random.uniform(3.0, 5.0)
                ])

    def emit_boss_thrusters(self, boss_rect):
        """Quad heavy plasma fire jets from Boss rear nozzles."""
        for ox in [-55, -22, 22, 55]:
            self.thruster_particles.append([
                boss_rect.centerx + ox + random.uniform(-3, 3),
                boss_rect.top + 6,
                random.uniform(-1.2, 1.2),
                random.uniform(-7.0, -3.5),
                18, 18,
                random.choice([RED, ORANGE, YELLOW, (255, 60, 20), WHITE]),
                random.uniform(4.5, 8.0)
            ])

    def update_and_draw_thrusters(self, screen):
        """Render all active thruster particles with additive glow."""
        for p in self.thruster_particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self.thruster_particles.remove(p)
                continue
            frac = p[4] / max(1.0, p[5])
            r = max(1, int(p[7] * frac))
            alpha = int(220 * frac)
            self._thruster_surf.fill((0, 0, 0, 0))
            pygame.draw.circle(self._thruster_surf, (*p[6], alpha), (r + 2, r + 2), r)
            screen.blit(self._thruster_surf, (int(p[0]) - r, int(p[1]) - r))

    # =========================================================================
    # 2. PLASMA BULLET TRAILS
    # =========================================================================

    def emit_bullet_trail(self, x, y, color=NEON_CYAN, is_enemy=False):
        """Emit trail particles behind a bullet."""
        q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
        count = q.get('trail', 5)
        for _ in range(count // 3 + 1):
            spread = 1.5 if not is_enemy else 1.0
            self.trail_particles.append([
                x + random.uniform(-spread, spread),
                y + random.uniform(-spread, spread),
                random.uniform(-0.5, 0.5),
                random.uniform(0.3, 1.2) * (1 if is_enemy else -1),
                6, 6,
                color,
                random.uniform(1.0, 3.0)
            ])

    def update_and_draw_trails(self, screen):
        """Render bullet trail wake particles."""
        for p in self.trail_particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self.trail_particles.remove(p)
                continue
            frac = p[4] / max(1.0, p[5])
            r = max(1, int(p[7] * frac))
            alpha = int(180 * frac)
            self._trail_surf.fill((0, 0, 0, 0))
            pygame.draw.circle(self._trail_surf, (*p[6], alpha), (r + 2, r + 2), r)
            screen.blit(self._trail_surf, (int(p[0]) - r, int(p[1]) - r))

    # =========================================================================
    # 3. 5-STAGE EXPLOSION SYSTEM
    # =========================================================================

    def spawn_explosion(self, cx, cy, size='medium', enemy_type='fighter'):
        """
        Spawn a 5-stage cinematic explosion:
        Stage 1: White flash core
        Stage 2: Orange fireball expansion
        Stage 3: Red/yellow blast ring
        Stage 4: Smoke puffs (gray)
        Stage 5: Ember sparks that drift and fade
        """
        q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
        n = q.get('explosion', 30)

        size_mult = {'small': 0.6, 'medium': 1.0, 'large': 1.6, 'boss': 2.5}.get(size, 1.0)

        # Stage 1: White flash core
        for _ in range(int(n * 0.15)):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.5, 4.0) * size_mult
            self.explosion_particles.append({
                'x': cx, 'y': cy,
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd,
                'life': int(8 * size_mult), 'max_life': int(8 * size_mult),
                'col': WHITE, 'size': random.uniform(4, 10) * size_mult,
                'stage': 1, 'decay': 0.85
            })

        # Stage 2: Orange fireball
        for _ in range(int(n * 0.3)):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2.0, 7.0) * size_mult
            col = random.choice([(255, 160, 0), (255, 100, 20), (255, 200, 50)])
            self.explosion_particles.append({
                'x': cx, 'y': cy,
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd,
                'life': int(20 * size_mult), 'max_life': int(20 * size_mult),
                'col': col, 'size': random.uniform(5, 14) * size_mult,
                'stage': 2, 'decay': 0.90
            })

        # Stage 3: Red/yellow blast ring
        num_ring = int(n * 0.2)
        for i in range(num_ring):
            ang = (i / num_ring) * 2 * math.pi
            spd = random.uniform(5.0, 12.0) * size_mult
            col = random.choice([RED, YELLOW, ORANGE, NEON_ORANGE])
            self.explosion_particles.append({
                'x': cx, 'y': cy,
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd,
                'life': int(16 * size_mult), 'max_life': int(16 * size_mult),
                'col': col, 'size': random.uniform(2, 5) * size_mult,
                'stage': 3, 'decay': 0.88
            })

        # Stage 4: Smoke puffs
        for _ in range(int(n * 0.15)):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(0.5, 2.5) * size_mult
            gray = random.randint(60, 110)
            self.explosion_particles.append({
                'x': cx + random.uniform(-8, 8),
                'y': cy + random.uniform(-8, 8),
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd - 0.5,
                'life': int(35 * size_mult), 'max_life': int(35 * size_mult),
                'col': (gray, gray, gray), 'size': random.uniform(6, 18) * size_mult,
                'stage': 4, 'decay': 0.96
            })

        # Stage 5: Ember sparks
        for _ in range(int(n * 0.2)):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(3.0, 10.0) * size_mult
            col = random.choice([NEON_GOLD, (255, 220, 80), NEON_ORANGE, WHITE])
            self.explosion_particles.append({
                'x': cx, 'y': cy,
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd,
                'life': int(40 * size_mult), 'max_life': int(40 * size_mult),
                'col': col, 'size': random.uniform(1.5, 4.0),
                'stage': 5, 'decay': 0.94
            })

        # Impact ripple
        self.impact_ripples.append({
            'x': cx, 'y': cy,
            'r': 4.0, 'max_r': 60.0 * size_mult,
            'spd': 4.5 * size_mult,
            'alpha': 220.0,
            'col': random.choice([NEON_ORANGE, NEON_CYAN, WHITE])
        })

    def update_and_draw_explosions(self, screen):
        """Update and render explosion particles."""
        for p in self.explosion_particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= p['decay']
            p['vy'] *= p['decay']
            p['life'] -= 1
            if p['life'] <= 0:
                self.explosion_particles.remove(p)
                continue
            frac = p['life'] / max(1.0, p['max_life'])
            sz = max(1.0, p['size'] * frac)
            col = p['col']

            if p['stage'] in (1, 2, 3, 5):
                # Bright particle
                psurf = pygame.Surface((int(sz * 2) + 4, int(sz * 2) + 4), pygame.SRCALPHA)
                alpha = int(240 * frac)
                pygame.draw.circle(psurf, (*col, alpha), (int(sz) + 2, int(sz) + 2), int(sz))
                screen.blit(psurf, (int(p['x']) - int(sz) - 2, int(p['y']) - int(sz) - 2))
            else:
                # Smoke puff — gray circle with soft edge
                psurf = pygame.Surface((int(sz * 2) + 4, int(sz * 2) + 4), pygame.SRCALPHA)
                alpha = int(120 * frac)
                pygame.draw.circle(psurf, (*col, alpha), (int(sz) + 2, int(sz) + 2), int(sz))
                screen.blit(psurf, (int(p['x']) - int(sz) - 2, int(p['y']) - int(sz) - 2))

    # =========================================================================
    # 4. IMPACT RIPPLES
    # =========================================================================

    def update_and_draw_ripples(self, screen):
        for rip in self.impact_ripples[:]:
            rip['r'] += rip['spd']
            rip['alpha'] = max(0.0, 255.0 * (1.0 - rip['r'] / rip['max_r']))
            if rip['alpha'] <= 0 or rip['r'] >= rip['max_r']:
                self.impact_ripples.remove(rip)
                continue
            r_int = int(rip['r'])
            rsurf = pygame.Surface((r_int * 2 + 8, r_int * 2 + 8), pygame.SRCALPHA)
            a_int = int(rip['alpha'])
            pygame.draw.circle(rsurf, (*rip['col'], a_int), (r_int + 4, r_int + 4), r_int, 2)
            screen.blit(rsurf, (int(rip['x']) - r_int - 4, int(rip['y']) - r_int - 4))

    # =========================================================================
    # 5. ELECTRIC DISCHARGE ARCS
    # =========================================================================

    def spawn_electric_arc(self, x1, y1, x2, y2, color=NEON_ELECTRIC, segments=5, life=8):
        """Spawn a jagged electric arc between two points."""
        if self.visual_quality == 'low':
            return
        pts = [(x1, y1)]
        for i in range(1, segments):
            t = i / segments
            mx = x1 + (x2 - x1) * t + random.uniform(-25, 25)
            my = y1 + (y2 - y1) * t + random.uniform(-15, 15)
            pts.append((mx, my))
        pts.append((x2, y2))
        self.electric_arcs.append({'pts': pts, 'life': life, 'max_life': life, 'col': color, 'width': 2})

    def update_and_draw_arcs(self, screen):
        for arc in self.electric_arcs[:]:
            arc['life'] -= 1
            if arc['life'] <= 0:
                self.electric_arcs.remove(arc)
                continue
            frac = arc['life'] / arc['max_life']
            alpha = int(220 * frac)
            asurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pts_int = [(int(p[0]), int(p[1])) for p in arc['pts']]
            if len(pts_int) >= 2:
                pygame.draw.lines(asurf, (*arc['col'], alpha), False, pts_int, arc['width'])
            screen.blit(asurf, (0, 0))

    # =========================================================================
    # 6. AMBIENT ENVIRONMENT PARTICLES
    # =========================================================================

    def update_and_draw_ambient(self, screen, env=1):
        """Ambient background particles for each environment."""
        if self.visual_quality == 'low':
            return

        self._ambient_t += 0.016

        # Spawn
        if random.random() < 0.25:
            if env == 1:  # Galaxy: slow drifting energy motes
                col = random.choice([NEON_BLUE, NEON_CYAN, (80, 120, 200)])
                self.ambient_particles.append({
                    'x': float(random.randint(0, WIDTH)),
                    'y': float(random.randint(0, HEIGHT)),
                    'vx': random.uniform(-0.3, 0.3),
                    'vy': random.uniform(0.2, 0.8),
                    'life': random.randint(80, 160),
                    'max_life': 160,
                    'col': col, 'size': random.uniform(1.0, 2.5)
                })
            elif env == 2:  # Nebula: dense purple/cyan fog motes
                col = random.choice([NEON_PURPLE, NEON_CYAN, MAGENTA, (160, 60, 200)])
                self.ambient_particles.append({
                    'x': float(random.randint(-20, WIDTH + 20)),
                    'y': float(random.randint(0, HEIGHT)),
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(-0.2, 0.5),
                    'life': random.randint(60, 120),
                    'max_life': 120,
                    'col': col, 'size': random.uniform(2.0, 5.0)
                })
            elif env == 3:  # Blackhole: swirling debris
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(200, 380)
                col = random.choice([(60, 40, 80), (100, 60, 120), (40, 30, 60)])
                self.ambient_particles.append({
                    'x': 400 + math.cos(angle) * dist,
                    'y': 300 + math.sin(angle) * dist,
                    'vx': -math.sin(angle) * 0.5,
                    'vy': math.cos(angle) * 0.5,
                    'life': random.randint(120, 200),
                    'max_life': 200,
                    'col': col, 'size': random.uniform(1.0, 3.0)
                })

        # Update + Draw
        for p in self.ambient_particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.ambient_particles.remove(p)
                continue
            frac = p['life'] / p['max_life']
            sz = max(1, int(p['size'] * frac))
            alpha = int(80 * frac)
            asurf = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(asurf, (*p['col'], alpha), (sz + 1, sz + 1), sz)
            screen.blit(asurf, (int(p['x']) - sz, int(p['y']) - sz))

    # =========================================================================
    # 7. MUZZLE FLASH
    # =========================================================================

    def draw_muzzle_flash(self, screen, cx, cy, intensity=1.0):
        """Bright bloom circle at the player gun muzzle when firing."""
        for r, alpha, col in [
            (int(16 * intensity), 220, WHITE),
            (int(22 * intensity), 120, NEON_CYAN),
            (int(30 * intensity), 50, NEON_TEAL),
        ]:
            msurf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(msurf, (*col, alpha), (r + 2, r + 2), r)
            screen.blit(msurf, (cx - r - 2, cy - r - 2))

    # =========================================================================
    # 8. LEGENDARY SUPERNOVA BOSS DESTRUCTION CATACLYSM
    # =========================================================================

    def trigger_boss_detonation(self, boss_rect, current_boss_img):
        """Initialize the final cataclysmic explosion when boss HP hits zero."""
        # Triple chromatic shockwaves
        self.boss_shockwaves.append({'r': 12.0, 'max_r': 560.0, 'spd': 18.0, 'col': NEON_CYAN,    'w': 7, 'alpha': 255.0})
        self.boss_shockwaves.append({'r': 12.0, 'max_r': 460.0, 'spd': 13.5, 'col': NEON_GOLD,    'w': 5, 'alpha': 255.0})
        self.boss_shockwaves.append({'r': 12.0, 'max_r': 370.0, 'spd': 9.5,  'col': NEON_SCARLET, 'w': 4, 'alpha': 255.0})
        self.boss_shockwaves.append({'r': 12.0, 'max_r': 280.0, 'spd': 7.0,  'col': NEON_PINK,    'w': 3, 'alpha': 255.0})

        # Screen flash
        self.boss_flash_alpha = 255.0

        # Molten debris
        q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
        for _ in range(q['debris']):
            ang  = random.uniform(0, 2 * math.pi)
            spd  = random.uniform(4.0, 22.0)
            life = random.randint(40, 90)
            size = random.uniform(4.0, 11.0)
            col  = random.choice([WHITE, NEON_GOLD, NEON_ORANGE, NEON_CYAN, NEON_PINK, (255, 80, 20), (255, 220, 100)])
            self.boss_debris.append({
                'x': boss_rect.centerx, 'y': boss_rect.centery,
                'vx': math.cos(ang) * spd, 'vy': math.sin(ang) * spd,
                'life': life, 'max_life': life,
                'col': col, 'size': size,
                'rot': random.uniform(0, 360), 'vrot': random.uniform(-14, 14),
                'decay': random.uniform(0.92, 0.97)
            })

    def update_and_draw_boss_death(self, screen, boss_rect, current_boss_img, boss_death_timer, expl_snd=None):
        """Multi-stage cinematic boss destruction (runs from timer 180 → 0)."""
        cx = boss_rect.centerx
        cy = boss_rect.centery

        self.screen_shake[0] *= 0.85
        self.screen_shake[1] *= 0.85

        # STAGE 1 (180 → 110): Structural overload
        if boss_death_timer > 110:
            shake_ox = random.uniform(-7, 7)
            shake_oy = random.uniform(-6, 6)
            self.screen_shake[0] = shake_ox * 0.85
            self.screen_shake[1] = shake_oy * 0.85

            if boss_death_timer % 3 == 0:
                if expl_snd and boss_death_timer % 12 == 0:
                    expl_snd.play()
                lx = cx + random.randint(-boss_rect.width // 2 + 10, boss_rect.width // 2 - 10)
                ly = cy + random.randint(-boss_rect.height // 2 + 10, boss_rect.height // 2 - 10)
                for _ in range(14):
                    self.boss_sparks.append({
                        'x': lx, 'y': ly,
                        'vx': random.uniform(-7, 7), 'vy': random.uniform(-7, 7),
                        'life': 20, 'max_life': 20,
                        'col': random.choice(BLAST_COLORS + [NEON_GOLD, NEON_CYAN]),
                        'size': random.uniform(3, 7)
                    })

            if random.random() < 0.8:
                p1  = (cx + random.randint(-70, 70), cy + random.randint(-45, 45))
                mid = (cx + random.randint(-35, 35), cy + random.randint(-25, 25))
                p2  = (cx + random.randint(-70, 70), cy + random.randint(-45, 45))
                self.boss_lightning.append({'pts': [p1, mid, p2], 'life': 5,
                                            'col': random.choice([CYAN, MAGENTA, WHITE, NEON_ELECTRIC])})

            draw_rect = boss_rect.copy()
            draw_rect.x += int(shake_ox)
            draw_rect.y += int(shake_oy)

            if (boss_death_timer // 3) % 2 == 0:
                white_surf = pygame.Surface(current_boss_img.get_size(), pygame.SRCALPHA)
                white_surf.blit(current_boss_img, (0, 0))
                white_mask = pygame.mask.from_surface(current_boss_img)
                white_overlay = white_mask.to_surface(setcolor=(255, 255, 255, 220), unsetcolor=(0, 0, 0, 0))
                white_surf.blit(white_overlay, (0, 0))
                screen.blit(white_surf, draw_rect)
            else:
                screen.blit(current_boss_img, draw_rect)

        # STAGE 2 (110 → 40): Core singularity overheat
        elif boss_death_timer > 40:
            shake_ox = random.uniform(-10, 10)
            shake_oy = random.uniform(-9, 9)
            self.screen_shake[0] = shake_ox
            self.screen_shake[1] = shake_oy

            for _ in range(4):
                p_ang  = random.uniform(0, 2 * math.pi)
                p_dist = random.uniform(90, 180)
                self.boss_sparks.append({
                    'x': cx + math.cos(p_ang) * p_dist,
                    'y': cy + math.sin(p_ang) * p_dist,
                    'vx': -math.cos(p_ang) * random.uniform(7.0, 13.0),
                    'vy': -math.sin(p_ang) * random.uniform(7.0, 13.0),
                    'life': 16, 'max_life': 16,
                    'col': random.choice([NEON_GOLD, WHITE, NEON_CYAN, NEON_SCARLET]),
                    'size': random.uniform(3.0, 5.5)
                })

            ray_t = (110 - boss_death_timer) / 70.0
            q = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])
            num_rays = q.get('god_rays', 14)
            for i in range(num_rays):
                ray_ang = (i / float(num_rays)) * 2 * math.pi + (pygame.time.get_ticks() * 0.016)
                ray_len = 170.0 + 90.0 * math.sin(ray_ang * 3 + pygame.time.get_ticks() * 0.022)
                rx2 = cx + math.cos(ray_ang) * ray_len
                ry2 = cy + math.sin(ray_ang) * ray_len
                ray_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ray_alpha = int(200 * ray_t)
                pygame.draw.line(ray_surf, (255, 255, 255, ray_alpha), (cx, cy), (rx2, ry2), 3)
                pygame.draw.line(ray_surf, (*NEON_GOLD, ray_alpha // 2), (cx, cy), (rx2, ry2), 9)
                screen.blit(ray_surf, (0, 0))

            silhouette_alpha = max(0, int(255 * (boss_death_timer - 40) / 70.0))
            if silhouette_alpha > 0:
                sil_surf = current_boss_img.copy()
                sil_surf.set_alpha(silhouette_alpha)
                screen.blit(sil_surf, (boss_rect.x + int(shake_ox), boss_rect.y + int(shake_oy)))

            core_r = int(16 + 20 * ray_t)
            core_surf = pygame.Surface((core_r * 4, core_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (255, 255, 255, 255), (core_r * 2, core_r * 2), core_r)
            pygame.draw.circle(core_surf, (*NEON_CYAN, 170), (core_r * 2, core_r * 2), core_r + 8)
            screen.blit(core_surf, (cx - core_r * 2, cy - core_r * 2))

        # STAGE 3 (timer == 40): Cataclysm detonation
        if boss_death_timer == 40:
            self.trigger_boss_detonation(boss_rect, current_boss_img)

        # RENDER ACTIVE PARTICLES
        for lit in self.boss_lightning[:]:
            lit['life'] -= 1
            if lit['life'] <= 0:
                self.boss_lightning.remove(lit)
            else:
                pygame.draw.lines(screen, lit['col'], False, lit['pts'], 2)

        for s in self.boss_sparks[:]:
            s['x'] += s['vx']
            s['y'] += s['vy']
            s['life'] -= 1
            if s['life'] <= 0:
                self.boss_sparks.remove(s)
            else:
                frac = s['life'] / max(1.0, s['max_life'])
                r = max(1, int(s['size'] * frac))
                pygame.draw.circle(screen, s['col'], (int(s['x']), int(s['y'])), r)

        for sw in self.boss_shockwaves[:]:
            sw['r'] += sw['spd']
            sw['alpha'] = max(0.0, 255.0 * (1.0 - (sw['r'] / sw['max_r'])))
            if sw['alpha'] <= 0 or sw['r'] >= sw['max_r']:
                self.boss_shockwaves.remove(sw)
            else:
                r_int = int(sw['r'])
                sw_surf = pygame.Surface((r_int * 2 + 20, r_int * 2 + 20), pygame.SRCALPHA)
                a_int = int(sw['alpha'])
                pygame.draw.circle(sw_surf, (*sw['col'], a_int // 3), (r_int + 10, r_int + 10), r_int + 4, sw['w'] + 3)
                pygame.draw.circle(sw_surf, (*sw['col'], a_int),      (r_int + 10, r_int + 10), r_int,     sw['w'])
                screen.blit(sw_surf, (cx - r_int - 10, cy - r_int - 10))

        for d in self.boss_debris[:]:
            d['x'] += d['vx']
            d['y'] += d['vy']
            d['vx'] *= d['decay']
            d['vy'] *= d['decay']
            d['rot'] += d['vrot']
            d['life'] -= 1
            if d['life'] <= 0:
                self.boss_debris.remove(d)
            else:
                frac = d['life'] / float(d['max_life'])
                sz = max(1, int(d['size'] * frac))
                deb_surf = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
                d_alpha = int(255 * frac)
                pts = [
                    (sz * 2, sz * 2 - sz),
                    (sz * 2 + sz, sz * 2),
                    (sz * 2, sz * 2 + sz),
                    (sz * 2 - sz, sz * 2)
                ]
                pygame.draw.polygon(deb_surf, (*d['col'], d_alpha), pts)
                rotated = pygame.transform.rotate(deb_surf, d['rot'])
                screen.blit(rotated, rotated.get_rect(center=(int(d['x']), int(d['y']))).topleft)

        if self.boss_flash_alpha > 0.0:
            f_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            f_surf.fill((255, 255, 255, min(255, int(self.boss_flash_alpha))))
            screen.blit(f_surf, (0, 0))
            self.boss_flash_alpha = max(0.0, self.boss_flash_alpha - 9.0)


# ===========================================================
# NEON VIGNETTE — Seamless Cinematic Radial Edge Glow (NO BOX BORDERS)
# ===========================================================

_vignette_cache = {}

def _create_smooth_vignette(W, H, color, alpha_edge):
    """
    Renders an ultra-smooth, continuous radial gradient vignette surface.
    Starts transparent in the center and softly ramps up towards the screen boundary.
    Zero sharp edges, zero nested boxes.
    """
    sw, sh = max(40, W // 4), max(30, H // 4)
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = sw / 2.0, sh / 2.0
    rx, ry = sw / 2.0, sh / 2.0

    for y in range(sh):
        ny = (y - cy) / ry
        ny2 = ny * ny
        for x in range(sw):
            nx = (x - cx) / rx
            dist_sq = nx * nx + ny2
            # Smooth radial decay: clear in inner 60% of viewport, feathering softly towards edges
            if dist_sq > 0.36:
                dist = math.sqrt(dist_sq)
                t = max(0.0, min(1.0, (dist - 0.60) / 0.65))
                smooth_t = t * t * (3.0 - 2.0 * t)  # Cubic smoothstep
                a = int(alpha_edge * smooth_t)
                if a > 0:
                    surf.set_at((x, y), (*color, min(255, a)))

    return pygame.transform.smoothscale(surf, (W, H))

def draw_neon_vignette(screen, color=(80, 0, 120), alpha_edge=120, steps=None):
    """Draw a silky-smooth radial vignette with zero stepped borders."""
    W, H = screen.get_size()
    a_quant = int(round(alpha_edge / 5.0) * 5)
    if a_quant <= 0:
        return
    key = (W, H, color, a_quant)
    if key not in _vignette_cache:
        if len(_vignette_cache) > 40:
            _vignette_cache.clear()
        _vignette_cache[key] = _create_smooth_vignette(W, H, color, a_quant)
    screen.blit(_vignette_cache[key], (0, 0))


# ===========================================================
# NEBULA OVERLAY — Volumetric Interstellar Gas Clouds & Thunderstorm
# ===========================================================

_gas_puff_cache = {}

def _get_soft_gas_puff(radius, color):
    """
    Returns a precomputed silky-smooth radial gas puff with quadratic falloff.
    Completely seamless with 0 alpha at outer rim (no circle lines).
    """
    r_int = max(16, int(round(radius / 4.0) * 4))
    key = (r_int, color)
    if key in _gas_puff_cache:
        return _gas_puff_cache[key]

    surf = pygame.Surface((r_int * 2, r_int * 2), pygame.SRCALPHA)
    cx, cy = r_int, r_int
    steps = min(36, r_int)
    for i in range(steps, 0, -1):
        cur_r = int(r_int * (i / steps))
        d = cur_r / r_int
        # Quadratic smooth falloff: dense core, silky outer edge reaching 0
        ring_alpha = int(255 * ((1.0 - d) ** 1.8))
        if ring_alpha > 0 and cur_r > 0:
            pygame.draw.circle(surf, (*color, ring_alpha), (cx, cy), cur_r)

    if len(_gas_puff_cache) > 150:
        _gas_puff_cache.clear()
    _gas_puff_cache[key] = surf
    return surf


_nebula_clouds = []
_nebula_lightning_timer = 0
_nebula_lightning_bolts = []   # each: {'pts': list, 'life': int, 'max_life': int}
_nebula_t = 0.0

def _spawn_nebula_cloud(W, H):
    """Creates a multi-layered organic nebula gas formation."""
    col_palettes = [
        # Deep cosmic violet & magenta
        [(130, 20, 210), (170, 30, 220), (90, 10, 160), (220, 40, 180)],
        # Cyan-ionized nebula filaments
        [(0, 180, 220), (20, 140, 200), (60, 220, 255), (100, 40, 220)],
        # Electric indigo & crimson dust
        [(150, 20, 180), (200, 30, 120), (80, 30, 220), (240, 60, 140)],
    ]
    palette = random.choice(col_palettes)

    # Generate 5-8 organic sub-puffs drifting together
    sub_puffs = []
    num_puffs = random.randint(5, 8)
    main_r = random.uniform(50, 110)
    for _ in range(num_puffs):
        ang = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, main_r * 0.75)
        sub_puffs.append({
            'ox': math.cos(ang) * dist,
            'oy': math.sin(ang) * dist,
            'r': random.uniform(main_r * 0.5, main_r * 1.1),
            'col': random.choice(palette),
            'alpha_weight': random.uniform(0.7, 1.0)
        })

    return {
        'x': float(random.randint(-40, W + 40)),
        'y': float(random.randint(-40, H + 40)),
        'vx': random.uniform(-0.18, 0.25),
        'vy': random.uniform(0.05, 0.35),
        'angle': random.uniform(0, 2 * math.pi),
        'vrot': random.uniform(-0.003, 0.003),
        'scale': random.uniform(0.9, 1.2),
        'pulse_phase': random.uniform(0, 2 * math.pi),
        'sub_puffs': sub_puffs,
        'base_alpha': random.randint(28, 48), # Soft transparent cosmic mist
        'life': random.randint(350, 700),
        'max_life': 700
    }

def draw_nebula_overlay(screen, pulse_t):
    """
    Immersive Nebula Zone overlay:
    - Volumetric organic multi-puff gas clouds with seamless gaussian falloff
    - Periodic thunderstorm lightning arcs with bright flash bloom
    - Ultra-smooth radial edge tint (no stepped borders)
    """
    global _nebula_clouds, _nebula_lightning_timer, _nebula_lightning_bolts, _nebula_t
    W, H = screen.get_size()
    _nebula_t += 0.016

    # Maintain 7-10 organic cloud formations
    if len(_nebula_clouds) < 8:
        _nebula_clouds.append(_spawn_nebula_cloud(W, H))

    # --- Render Organic Nebula Clouds ---
    for cloud in _nebula_clouds[:]:
        cloud['x'] += cloud['vx']
        cloud['y'] += cloud['vy']
        cloud['angle'] += cloud['vrot']
        cloud['life'] -= 1

        # Wrap around screen edges softly
        if cloud['y'] > H + 120:
            cloud['y'] = -100
            cloud['x'] = random.randint(-40, W + 40)
        if cloud['x'] > W + 120:
            cloud['x'] = -100
        elif cloud['x'] < -120:
            cloud['x'] = W + 100

        if cloud['life'] <= 0:
            _nebula_clouds.remove(cloud)
            continue

        # Smooth sine-based fade in and fade out
        life_frac = cloud['life'] / cloud['max_life']
        fade = math.sin(life_frac * math.pi)
        pulse = 1.0 + 0.08 * math.sin(_nebula_t * 1.5 + cloud['pulse_phase'])
        master_alpha = int(cloud['base_alpha'] * fade * pulse)

        if master_alpha <= 0:
            continue

        cos_a = math.cos(cloud['angle'])
        sin_a = math.sin(cloud['angle'])

        for p in cloud['sub_puffs']:
            # Rotate offset
            rx = p['ox'] * cos_a - p['oy'] * sin_a
            ry = p['ox'] * sin_a + p['oy'] * cos_a
            px = cloud['x'] + rx
            py = cloud['y'] + ry
            pr = p['r'] * cloud['scale'] * pulse

            puff_surf = _get_soft_gas_puff(pr, p['col']).copy()
            puff_a = min(255, int(master_alpha * p['alpha_weight']))
            puff_surf.set_alpha(puff_a)
            screen.blit(puff_surf, (int(px - pr), int(py - pr)))

    # --- Lightning / Thunderstorm system ---
    _nebula_lightning_timer -= 1

    # Update & render existing lightning bolts
    for bolt in _nebula_lightning_bolts[:]:
        bolt['life'] -= 1
        if bolt['life'] <= 0:
            _nebula_lightning_bolts.remove(bolt)
            continue
        frac = bolt['life'] / bolt['max_life']
        a = int(220 * frac)
        col = random.choice([(180, 60, 255), (220, 110, 255), (255, 180, 255), WHITE])

        lsurf = pygame.Surface((W, H), pygame.SRCALPHA)
        if len(bolt['pts']) >= 2:
            # Outer electric aura
            pygame.draw.lines(lsurf, (*col, a // 3), False, bolt['pts'], 7)
            # Mid glow
            pygame.draw.lines(lsurf, (*col, a // 2), False, bolt['pts'], 4)
            # Bright hot core
            pygame.draw.lines(lsurf, (255, 255, 255, a), False, bolt['pts'], 2)
            # Flash point at branch nodes
            for pt in bolt['pts'][1:-1:2]:
                pygame.draw.circle(lsurf, (255, 255, 255, a), pt, random.randint(2, 4))
        screen.blit(lsurf, (0, 0))

    # Spawn new forked lightning bolt
    if _nebula_lightning_timer <= 0:
        _nebula_lightning_timer = random.randint(110, 240)
        x1 = random.randint(40, W - 40)
        y1 = random.randint(0, 100)
        x2 = random.randint(40, W - 40)
        y2 = random.randint(H - 120, H)
        pts = [(x1, y1)]
        segs = random.randint(7, 12)
        for i in range(1, segs):
            t = i / segs
            mx = int(x1 + (x2 - x1) * t + random.uniform(-45, 45))
            my = int(y1 + (y2 - y1) * t + random.uniform(-15, 15))
            pts.append((mx, my))
        pts.append((x2, y2))
        life = random.randint(8, 16)
        _nebula_lightning_bolts.append({'pts': pts, 'life': life, 'max_life': life})

    # --- Smooth cinematic radial edge glow (NO stepped boxes) ---
    pulse_a = int(35 + 15 * math.sin(pulse_t * 1.5))
    draw_neon_vignette(screen, color=(90, 0, 160), alpha_edge=pulse_a)


# ===========================================================
# BLACKHOLE OVERLAY — Cosmic Civil War: Blackhole Horizon
# ===========================================================

_bh_debris = []
_bh_star_pull = []
_bh_t = 0.0
BH_CX, BH_CY = 400, 200   # Gravity center (upper center)

def _init_bh_stars():
    global _bh_star_pull
    if not _bh_star_pull:
        for _ in range(60):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(80, 400)
            _bh_star_pull.append({
                'angle': angle, 'dist': dist,
                'spd': random.uniform(0.005, 0.025),
                'brightness': random.randint(80, 240),
                'r': random.choice([1, 1, 2]),
                'born_dist': dist,
            })

def draw_blackhole_overlay(screen, pulse_t, bh_cx=400, bh_cy=200):
    """
    Immersive Blackhole Horizon overlay:
    - Pulsing gravity ring with chromatic distortion
    - Stars spiraling inward and vanishing at the event horizon
    - Glowing debris trails pulled toward the singularity
    - Crimson edge vignette
    - Subtle screen-edge chromatic aberration color strips
    """
    global _bh_debris, _bh_star_pull, _bh_t
    W, H = screen.get_size()
    _bh_t += 0.016
    _init_bh_stars()

    # --- Gravity ring layers (pulsing concentric rings) ---
    for i, (ring_r, ring_col, ring_a) in enumerate([
        (55,  (255, 40, 80),  120),   # Inner red hot ring
        (75,  (200, 20, 60),  70),    # Mid ring
        (100, (120, 0, 40),   40),    # Outer dim ring
    ]):
        pulse_offset = math.sin(pulse_t * 2.5 + i * 1.1) * 6
        r = int(ring_r + pulse_offset)
        rsurf = pygame.Surface((r * 2 + 12, r * 2 + 12), pygame.SRCALPHA)
        a = int(ring_a + 30 * math.sin(pulse_t * 3 + i))
        pygame.draw.circle(rsurf, (*ring_col, a), (r + 6, r + 6), r, 3)
        screen.blit(rsurf, (bh_cx - r - 6, bh_cy - r - 6))

    # Singularity core glow
    core_r = int(30 + 8 * math.sin(pulse_t * 4))
    for cr, ca in [(core_r + 20, 15), (core_r + 10, 35), (core_r, 80), (core_r - 10, 200)]:
        if cr > 0:
            csurf = pygame.Surface((cr * 2 + 4, cr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(csurf, (180, 10, 50, ca), (cr + 2, cr + 2), cr)
            screen.blit(csurf, (bh_cx - cr - 2, bh_cy - cr - 2))
    # Black void center
    pygame.draw.circle(screen, (0, 0, 0), (bh_cx, bh_cy), int(core_r - 8))

    # --- Stars spiraling inward ---
    for s in _bh_star_pull:
        # Tighten orbit & pull inward
        s['angle'] += s['spd'] * (1.0 + (s['born_dist'] - s['dist']) / s['born_dist'] * 3)
        s['dist'] = max(0, s['dist'] - s['spd'] * 1.8)
        if s['dist'] < 15:  # Consumed — reset
            s['angle'] = random.uniform(0, 2 * math.pi)
            s['dist'] = random.uniform(260, 420)
            s['born_dist'] = s['dist']
            s['brightness'] = random.randint(80, 240)
        sx = bh_cx + math.cos(s['angle']) * s['dist']
        sy = bh_cy + math.sin(s['angle']) * s['dist']
        frac = min(1.0, s['dist'] / s['born_dist'])
        a = int(s['brightness'] * frac)
        col = (min(255, a // 2 + 80), min(255, int(a * 0.7)), min(255, a))
        r = max(1, s['r'] if frac > 0.3 else 1)
        if 0 <= int(sx) < W and 0 <= int(sy) < H:
            pygame.draw.circle(screen, col, (int(sx), int(sy)), r)

    # --- Glowing debris trail particles ---
    if len(_bh_debris) < 25 and random.random() < 0.4:
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(180, 360)
        col = random.choice([(200, 80, 30), (255, 120, 40), (180, 50, 80), (255, 60, 90)])
        _bh_debris.append({
            'x': bh_cx + math.cos(angle) * dist,
            'y': bh_cy + math.sin(angle) * dist,
            'angle': angle, 'dist': dist,
            'spd': random.uniform(0.012, 0.03),
            'life': random.randint(80, 200),
            'max_life': 200,
            'col': col, 'size': random.uniform(1.5, 3.5),
        })

    for d in _bh_debris[:]:
        d['angle'] += d['spd']
        d['dist'] = max(0, d['dist'] - d['spd'] * 3.5)
        d['x'] = bh_cx + math.cos(d['angle']) * d['dist']
        d['y'] = bh_cy + math.sin(d['angle']) * d['dist']
        d['life'] -= 1
        if d['life'] <= 0 or d['dist'] < 20:
            _bh_debris.remove(d)
            continue
        frac = d['life'] / d['max_life']
        a = int(200 * frac)
        sz = max(1, int(d['size'] * frac))
        dsurf = pygame.Surface((sz * 2 + 4, sz * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(dsurf, (*d['col'], a), (sz + 2, sz + 2), sz)
        screen.blit(dsurf, (int(d['x']) - sz - 2, int(d['y']) - sz - 2))

    # --- Chromatic aberration edge strips ---
    edge_a = int(18 + 12 * math.sin(pulse_t * 2.2))
    edge_w = 30
    # Left edge: red tint
    esurf_l = pygame.Surface((edge_w, H), pygame.SRCALPHA)
    for ex in range(edge_w):
        a = int(edge_a * (1 - ex / edge_w))
        pygame.draw.line(esurf_l, (180, 0, 0, a), (ex, 0), (ex, H))
    screen.blit(esurf_l, (0, 0))
    # Right edge: blue tint
    esurf_r = pygame.Surface((edge_w, H), pygame.SRCALPHA)
    for ex in range(edge_w):
        a = int(edge_a * (1 - ex / edge_w))
        pygame.draw.line(esurf_r, (0, 0, 180, a), (ex, 0), (ex, H))
    screen.blit(esurf_r, (W - edge_w, 0))

    # --- Crimson vignette ---
    pulse_a = int(40 + 20 * math.sin(pulse_t * 2.0))
    draw_neon_vignette(screen, color=(120, 0, 20), alpha_edge=pulse_a)



_auth_stars = [
    [random.uniform(0, 800), random.uniform(0, 600),
     random.uniform(0.2, 1.5), random.uniform(0.5, 2.5),
     random.randint(80, 200)]
    for _ in range(160)
]
_auth_glitch_t = 0.0

def draw_neon_auth_bg(screen, now):
    """
    Next-level procedural cyberpunk background:
    - Deep space gradient
    - Moving parallax star layers
    - Animated synthwave grid with perspective
    - Pulsing sun with chromatic halo
    - Random glitch scan lines
    - Shooting stars
    """
    global _auth_glitch_t
    _auth_glitch_t += 0.03

    WIDTH, HEIGHT = screen.get_size()
    screen.fill(DEEP_SPACE)

    # Gradient sky (vertical — deep dark to slightly lighter at horizon)
    grad_surf = pygame.Surface((WIDTH, HEIGHT // 2), pygame.SRCALPHA)
    for y in range(HEIGHT // 2):
        t = y / (HEIGHT // 2)
        r = int(5 + 15 * t)
        g = int(3 + 8 * t)
        b = int(20 + 40 * t)
        pygame.draw.rect(grad_surf, (r, g, b, 255), (0, y, WIDTH, 1))
    screen.blit(grad_surf, (0, 0))

    center_x = WIDTH // 2
    center_y = int(HEIGHT * 0.42)

    # Parallax star layers
    for s in _auth_stars:
        s[1] += s[3] * 0.15  # very slow drift
        if s[1] > HEIGHT:
            s[0] = random.uniform(0, WIDTH)
            s[1] = 0.0
        r = max(1, int(s[2]))
        brightness = s[4]
        col = (min(255, brightness // 2), min(255, brightness // 2 + 30), min(255, brightness))
        pygame.draw.circle(screen, col, (int(s[0]), int(s[1])), r)

    # Sun glow
    pulse = (math.sin(now / 520.0) + 1) / 2
    sun_r = 100 + int(10 * pulse)
    sun_col = (255, 60 + int(40 * pulse), 160)

    for gr, ga in [(sun_r * 3, 8), (sun_r * 2, 20), (sun_r + 30, 60), (sun_r, 180)]:
        gsurf = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (*sun_col, ga), (gr, gr), gr)
        screen.blit(gsurf, (center_x - gr, center_y - gr))

    # Cut sun bottom with solid horizon
    pygame.draw.rect(screen, DEEP_SPACE, (0, center_y, WIDTH, HEIGHT - center_y))

    # Animated perspective grid
    speed   = 0.055
    offset  = (now * speed) % 44

    # Horizontal lines
    for i in range(18):
        raw_y = center_y + ((i * 44 + offset) ** 1.28) * 0.14
        y = int(raw_y)
        if y < HEIGHT:
            thickness = max(1, int((y - center_y) / 120))
            alpha = max(30, min(200, int(200 * (y - center_y) / (HEIGHT - center_y))))
            line_surf = pygame.Surface((WIDTH, thickness + 1), pygame.SRCALPHA)
            line_surf.fill((0, 120, 255, alpha))
            screen.blit(line_surf, (0, y))

    # Vertical perspective lines
    for i in range(-14, 15):
        x_bottom = center_x + i * 160
        line_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = max(30, min(140, 140 - abs(i) * 8))
        pygame.draw.line(line_surf, (0, 120, 255, alpha), (center_x, center_y), (x_bottom, HEIGHT), 1)
        screen.blit(line_surf, (0, 0))

    # Horizon neon line
    horizon_surf = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
    horizon_surf.fill((0, 255, 255, 220))
    screen.blit(horizon_surf, (0, center_y))
    thin_surf = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
    thin_surf.fill((255, 255, 255, 180))
    screen.blit(thin_surf, (0, center_y))

    # Random glitch scanlines
    if random.random() < 0.04:
        for _ in range(random.randint(1, 3)):
            gy = random.randint(0, HEIGHT)
            gw = random.randint(20, 200)
            gx = random.randint(0, WIDTH - gw)
            gsurf = pygame.Surface((gw, random.randint(1, 3)), pygame.SRCALPHA)
            gcol = random.choice([NEON_CYAN, NEON_ELECTRIC, WHITE])
            gsurf.fill((*gcol, random.randint(80, 160)))
            screen.blit(gsurf, (gx, gy))
