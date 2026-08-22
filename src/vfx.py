import pygame
import math
import random
from settings import *

class VisualEffectsEngine:
    """
    High-performance visual effects engine for Crazyy Simulation.
    Provides:
      - Multi-layer engine thruster plumes & particle streams for all starships
      - The 'Supernova Cataclysm' multi-stage Boss destruction sequence
      - Chromatic shockwaves, lightning arcs, and molten debris physics
    """
    def __init__(self):
        # Thruster particle pools: [x, y, vx, vy, life, max_life, col, size]
        self.thruster_particles = []
        
        self.visual_quality = 'high'
        self._thruster_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        
        # Boss Cataclysm state
        self.boss_shockwaves = []
        self.boss_debris = []
        self.boss_sparks = []
        self.boss_lightning = []
        self.boss_flash_alpha = 0.0
        self.screen_shake = [0.0, 0.0]

    def set_quality(self, quality):
        """Set visual quality level: 'low', 'medium', or 'high'."""
        self.visual_quality = quality

    def reset_boss_effects(self):
        """Reset boss explosion pools."""
        self.boss_shockwaves.clear()
        self.boss_debris.clear()
        self.boss_sparks.clear()
        self.boss_lightning.clear()
        self.boss_flash_alpha = 0.0
        self.screen_shake = [0.0, 0.0]

    # =========================================================================
    # 1. ENGINE THRUSTERS (FOR ALL SHIPS)
    # =========================================================================
    def emit_player_thruster(self, centerx, bottom_y):
        """Emit dual glowing cyan/blue engine exhaust plumes for the player ship."""
        from settings import QUALITY_PARTICLES
        density = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high']).get('thruster_density', 1.0)
        if random.random() > density:
            return
            
        for ox in [-12, 12]:
            # Flame core particle
            self.thruster_particles.append([
                centerx + ox + random.uniform(-1.5, 1.5),
                bottom_y - 2,
                random.uniform(-0.6, 0.6),
                random.uniform(3.5, 6.5),
                12, 12,
                random.choice([WHITE, NEON_CYAN, (180, 240, 255), NEON_BLUE]),
                random.uniform(2.5, 4.5)
            ])

    def emit_enemy_thruster(self, centerx, top_y, enemy_type='fighter', width=40): # width is unused
        """Emit upward engine exhaust plumes for enemy ships."""
        from settings import QUALITY_PARTICLES
        density = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high']).get('thruster_density', 1.0)
        if random.random() > density:
            return
        if enemy_type == 'fighter':
            # Dual red/orange thrusters
            for ox in [-8, 8]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1, 1),
                    top_y + 4,
                    random.uniform(-0.5, 0.5),
                    random.uniform(-4.5, -2.5),
                    10, 10,
                    random.choice([RED, ORANGE, (255, 200, 50)]),
                    random.uniform(2.0, 3.5)
                ])
        elif enemy_type == 'elite':
            # Twin ionic purple/magenta thrusters
            for ox in [-14, 14]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1.5, 1.5),
                    top_y + 4,
                    random.uniform(-0.6, 0.6),
                    random.uniform(-4.0, -2.0),
                    11, 11,
                    random.choice([MAGENTA, NEON_PURPLE, NEON_PINK, WHITE]),
                    random.uniform(2.5, 4.0)
                ])
        elif enemy_type == 'heavy':
            # Triple roaring orange/yellow plasma thrusters
            for ox in [-18, 0, 18]:
                self.thruster_particles.append([
                    centerx + ox + random.uniform(-1.5, 1.5),
                    top_y + 6,
                    random.uniform(-0.8, 0.8),
                    random.uniform(-3.5, -1.8),
                    14, 14,
                    random.choice([ORANGE, YELLOW, (255, 100, 30), WHITE]),
                    random.uniform(3.0, 5.0)
                ])

    def emit_boss_thrusters(self, boss_rect):
        """Emit quad heavy plasma fire jets from the Boss rear nozzles."""
        nozzle_offsets = [-55, -22, 22, 55]
        for ox in nozzle_offsets:
            self.thruster_particles.append([
                boss_rect.centerx + ox + random.uniform(-2, 2),
                boss_rect.top + 6,
                random.uniform(-1.0, 1.0),
                random.uniform(-6.0, -3.0),
                16, 16,
                random.choice([RED, ORANGE, YELLOW, (255, 60, 20), WHITE]),
                random.uniform(4.0, 7.0)
            ])

    def update_and_draw_thrusters(self, screen):
        """Update and render all active thruster flame particles with additive blending."""
        for p in self.thruster_particles[:]:
            p[0] += p[2]  # x += vx
            p[1] += p[3]  # y += vy
            p[4] -= 1     # life -= 1

            if p[4] <= 0:
                self.thruster_particles.remove(p)
                continue

            # Life ratio for size and alpha tapering
            frac = p[4] / max(1.0, p[5])
            r = max(1, int(p[7] * frac))
            alpha = int(240 * frac)

            # Draw glowing circular plume
            self._thruster_surf.fill((0, 0, 0, 0))
            p_surf = self._thruster_surf
            pygame.draw.circle(p_surf, (*p[6], alpha), (r + 1, r + 1), r)
            screen.blit(p_surf, (int(p[0]) - r, int(p[1]) - r))

    # =========================================================================
    # 2. LEGENDARY SUPERNOVA BOSS DESTRUCTION CATACLYSM
    # =========================================================================
    def trigger_boss_detonation(self, boss_rect, current_boss_img): # current_boss_img is unused
        """Initialize the final cataclysmic explosion when boss death timer reaches peak."""
        # 1. Triple Expanding Chromatic Shockwave Rings
        self.boss_shockwaves.append({'r': 10.0, 'max_r': 520.0, 'spd': 16.0, 'col': NEON_CYAN, 'w': 6, 'alpha': 255.0})
        self.boss_shockwaves.append({'r': 10.0, 'max_r': 440.0, 'spd': 12.5, 'col': NEON_GOLD, 'w': 4, 'alpha': 255.0})
        self.boss_shockwaves.append({'r': 10.0, 'max_r': 360.0, 'spd': 9.0,  'col': NEON_PINK, 'w': 3, 'alpha': 255.0})

        # 2. Screen Flash
        self.boss_flash_alpha = 245.0

        # 3. Molten Shrapnel & Hull Debris Fragments
        from settings import QUALITY_PARTICLES
        debris_count = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high'])['debris']
        for _ in range(debris_count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(4.0, 20.0)
            life = random.randint(35, 75)
            size = random.uniform(3.5, 9.0)
            col = random.choice([
                WHITE,
                NEON_GOLD,
                NEON_ORANGE,
                NEON_CYAN,
                NEON_PINK,
                (255, 80, 20),
                (255, 220, 100)
            ])
            self.boss_debris.append({
                'x': boss_rect.centerx,
                'y': boss_rect.centery,
                'vx': math.cos(ang) * spd,
                'vy': math.sin(ang) * spd,
                'life': life,
                'max_life': life,
                'col': col,
                'size': size,
                'rot': random.uniform(0, 360),
                'vrot': random.uniform(-12, 12),
                'decay': random.uniform(0.93, 0.97)
            })

    def update_and_draw_boss_death(self, screen, boss_rect, current_boss_img, boss_death_timer, expl_snd=None):
        """
        Multi-stage cinematic Boss destruction sequence (Runs from timer 180 down to 0).
        """
        cx = boss_rect.centerx
        cy = boss_rect.centery

        # Decay screen shake
        self.screen_shake[0] *= 0.85
        self.screen_shake[1] *= 0.85

        # -----------------------------------------------------------------
        # STAGE 1 (Timer 180 -> 110): Structural Overload & Secondary Detonations
        # -----------------------------------------------------------------
        if boss_death_timer > 110:
            # Boss sprite vibrates violently
            shake_ox = random.uniform(-6, 6)
            shake_oy = random.uniform(-5, 5)
            self.screen_shake[0] = shake_ox * 0.8
            self.screen_shake[1] = shake_oy * 0.8

            # Staggered localized secondary explosions
            if boss_death_timer % 3 == 0:
                if expl_snd and boss_death_timer % 12 == 0:
                    expl_snd.play()
                lx = cx + random.randint(-boss_rect.width // 2 + 10, boss_rect.width // 2 - 10)
                ly = cy + random.randint(-boss_rect.height // 2 + 10, boss_rect.height // 2 - 10)
                for _ in range(12):
                    self.boss_sparks.append({
                        'x': lx, 'y': ly,
                        'vx': random.uniform(-6, 6),
                        'vy': random.uniform(-6, 6),
                        'life': 18, 'max_life': 18,
                        'col': random.choice(BLAST_COLORS + [NEON_GOLD]),
                        'size': random.uniform(3, 6)
                    })

            # Crackling Electric Lightning Arcs across hull
            if random.random() < 0.75:
                p1 = (cx + random.randint(-60, 60), cy + random.randint(-40, 40))
                mid = (cx + random.randint(-30, 30), cy + random.randint(-20, 20))
                p2 = (cx + random.randint(-60, 60), cy + random.randint(-40, 40))
                self.boss_lightning.append({'pts': [p1, mid, p2], 'life': 4, 'col': random.choice([CYAN, MAGENTA, WHITE])})

            # Render flashing Boss Ship with damage tint
            draw_rect = boss_rect.copy()
            draw_rect.x += int(shake_ox)
            draw_rect.y += int(shake_oy)

            if (boss_death_timer // 3) % 2 == 0:
                # White-hot hull overload flash
                white_surf = pygame.Surface(current_boss_img.get_size(), pygame.SRCALPHA)
                white_surf.blit(current_boss_img, (0, 0))
                white_mask = pygame.mask.from_surface(current_boss_img)
                white_overlay = white_mask.to_surface(setcolor=(255, 255, 255, 210), unsetcolor=(0, 0, 0, 0))
                white_surf.blit(white_overlay, (0, 0))
                screen.blit(white_surf, draw_rect)
            else:
                screen.blit(current_boss_img, draw_rect)

        # -----------------------------------------------------------------
        # STAGE 2 (Timer 110 -> 40): Core Singularity Overheat & Piercing God-Rays
        # -----------------------------------------------------------------
        elif boss_death_timer > 40:
            shake_ox = random.uniform(-8, 8)
            shake_oy = random.uniform(-7, 7)
            self.screen_shake[0] = shake_ox
            self.screen_shake[1] = shake_oy

            # Inward particle attraction into core
            for _ in range(3):
                p_ang = random.uniform(0, 2 * math.pi)
                p_dist = random.uniform(80, 160)
                self.boss_sparks.append({
                    'x': cx + math.cos(p_ang) * p_dist,
                    'y': cy + math.sin(p_ang) * p_dist,
                    'vx': -math.cos(p_ang) * random.uniform(6.0, 11.0),
                    'vy': -math.sin(p_ang) * random.uniform(6.0, 11.0),
                    'life': 14, 'max_life': 14,
                    'col': random.choice([NEON_GOLD, WHITE, NEON_CYAN]),
                    'size': random.uniform(2.5, 4.5)
                })

            # Piercing God-Ray Laser Spikes radiating from Core
            ray_t = (110 - boss_death_timer) / 70.0
            from settings import QUALITY_PARTICLES
            num_rays = QUALITY_PARTICLES.get(self.visual_quality, QUALITY_PARTICLES['high']).get('god_rays', 12)
            for i in range(num_rays):
                ray_ang = (i / float(num_rays)) * 2 * math.pi + (pygame.time.get_ticks() * 0.015)
                ray_len = 160.0 + 80.0 * math.sin(ray_ang * 3 + pygame.time.get_ticks() * 0.02)
                rx2 = cx + math.cos(ray_ang) * ray_len
                ry2 = cy + math.sin(ray_ang) * ray_len
                
                ray_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ray_alpha = int(180 * ray_t)
                pygame.draw.line(ray_surf, (255, 255, 255, ray_alpha), (cx, cy), (rx2, ry2), 3)
                pygame.draw.line(ray_surf, (*NEON_GOLD, ray_alpha // 2), (cx, cy), (rx2, ry2), 8)
                screen.blit(ray_surf, (0, 0))

            # Fading Boss Silhouette
            silhouette_alpha = max(0, int(255 * (boss_death_timer - 40) / 70.0))
            if silhouette_alpha > 0:
                sil_surf = current_boss_img.copy()
                sil_surf.set_alpha(silhouette_alpha)
                screen.blit(sil_surf, (boss_rect.x + int(shake_ox), boss_rect.y + int(shake_oy)))

            # Pulsing Core Singularity
            core_r = int(14 + 16 * ray_t)
            core_surf = pygame.Surface((core_r * 4, core_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (255, 255, 255, 250), (core_r * 2, core_r * 2), core_r)
            pygame.draw.circle(core_surf, (*NEON_CYAN, 160), (core_r * 2, core_r * 2), core_r + 6)
            screen.blit(core_surf, (cx - core_r * 2, cy - core_r * 2))

        # -----------------------------------------------------------------
        # STAGE 3 (Trigger Detonation at Timer == 40): Cataclysm Detonation
        # -----------------------------------------------------------------
        if boss_death_timer == 40:
            self.trigger_boss_detonation(boss_rect, current_boss_img)

        # -----------------------------------------------------------------
        # RENDER ACTIVE PARTICLES, SHOCKWAVES & DEBRIS
        # -----------------------------------------------------------------
        # Lightning
        for lit in self.boss_lightning[:]:
            lit['life'] -= 1
            if lit['life'] <= 0:
                self.boss_lightning.remove(lit)
            else:
                pygame.draw.lines(screen, lit['col'], False, lit['pts'], 2)

        # Sparks
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

        # Shockwaves
        for sw in self.boss_shockwaves[:]:
            sw['r'] += sw['spd']
            sw['alpha'] = max(0.0, 255.0 * (1.0 - (sw['r'] / sw['max_r'])))
            if sw['alpha'] <= 0 or sw['r'] >= sw['max_r']:
                self.boss_shockwaves.remove(sw)
            else:
                r_int = int(sw['r'])
                sw_surf = pygame.Surface((r_int * 2 + 16, r_int * 2 + 16), pygame.SRCALPHA)
                a_int = int(sw['alpha'])
                pygame.draw.circle(sw_surf, (*sw['col'], a_int // 3), (r_int + 8, r_int + 8), r_int + 3, sw['w'] + 2)
                pygame.draw.circle(sw_surf, (*sw['col'], a_int), (r_int + 8, r_int + 8), r_int, sw['w'])
                screen.blit(sw_surf, (cx - r_int - 8, cy - r_int - 8))

        # Molten Hull Debris
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
                # Draw rotating glowing diamond/shard
                deb_surf = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
                d_alpha = int(255 * frac)
                # Diamond vertices
                pts = [
                    (sz * 2, sz * 2 - sz),
                    (sz * 2 + sz, sz * 2),
                    (sz * 2, sz * 2 + sz),
                    (sz * 2 - sz, sz * 2)
                ]
                pygame.draw.polygon(deb_surf, (*d['col'], d_alpha), pts)
                screen.blit(deb_surf, (int(d['x']) - sz * 2, int(d['y']) - sz * 2))

        # Supernova Flash Decay
        if self.boss_flash_alpha > 0.0:
            f_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            f_surf.fill((255, 255, 255, min(255, int(self.boss_flash_alpha))))
            screen.blit(f_surf, (0, 0))
            self.boss_flash_alpha = max(0.0, self.boss_flash_alpha - 10.0)

def draw_neon_auth_bg(screen, now):
    """Draws a next-level procedural synthwave/cyberpunk grid without images."""
    import pygame, math
    WIDTH, HEIGHT = screen.get_size()
    # Deep Cyberpunk gradient
    screen.fill((5, 5, 12))
    
    # Grid properties
    grid_color = (0, 150, 255)
    center_x = WIDTH // 2
    center_y = int(HEIGHT * 0.4)
    
    # Draw sun/glow
    pulse = (math.sin(now / 500.0) + 1) / 2
    sun_radius = 120 + int(10 * pulse)
    sun_color = (255, 50 + int(50*pulse), 150)
    
    # Outer glow
    glow_surf = pygame.Surface((sun_radius*3, sun_radius*3), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*sun_color, 20), (sun_radius*1.5, sun_radius*1.5), sun_radius*1.5)
    pygame.draw.circle(glow_surf, (*sun_color, 40), (sun_radius*1.5, sun_radius*1.5), sun_radius*1.2)
    pygame.draw.circle(glow_surf, (*sun_color, 150), (sun_radius*1.5, sun_radius*1.5), sun_radius)
    screen.blit(glow_surf, (center_x - int(sun_radius*1.5), center_y - int(sun_radius*1.5)))
    
    # Cut the sun bottom with horizon
    horizon_rect = pygame.Rect(0, center_y, WIDTH, HEIGHT - center_y)
    pygame.draw.rect(screen, (5, 5, 15), horizon_rect)
    
    # Perspective grid lines (moving towards viewer)
    speed = 0.05
    offset = (now * speed) % 40
    
    # Horizontal lines
    for i in range(15):
        y = center_y + ((i * 40 + offset) ** 1.3) * 0.15
        if y < HEIGHT:
            line_thickness = 1 + int((y - center_y) / 100)
            pygame.draw.line(screen, grid_color, (0, int(y)), (WIDTH, int(y)), line_thickness)
            
    # Vertical perspective lines
    num_v_lines = 20
    for i in range(-num_v_lines, num_v_lines):
        x_bottom = center_x + i * 150
        pygame.draw.line(screen, grid_color, (center_x, center_y), (x_bottom, HEIGHT), 1)
        
    # Draw glowing horizon line
    pygame.draw.line(screen, (0, 255, 255), (0, center_y), (WIDTH, center_y), 4)
    pygame.draw.line(screen, (255, 255, 255), (0, center_y), (WIDTH, center_y), 1)
