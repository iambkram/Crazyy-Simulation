import pygame
import math
import random
from settings import *
from assets import draw_text, draw_text_shadow, draw_divider

class CinematicBranding:
    """
    State-of-the-art cinematic neon branding intro animation for 'IAMBKRAM'.
    Features:
      - Deep-space hyper-warp radial star streaks
      - 3D perspective cyber matrix floor grid
      - Inward singularity particle gathering
      - Elastic ease-in emblem slam with screen shake & audio sync
      - Rotating dual concentric HUD orbital rings with tick marks
      - Holographic geometric hex-shield with delta starship wings
      - Multi-layer neon typography with chromatic aberration & bloom
      - Specular laser lens flare sweep with individual letter specular ignition
      - Cyberpunk corner HUD telemetry and glowing subtitle framing
      - Smooth cinematic crossfade into Main Menu (instant skip on click/key)
    """
    def __init__(self):
        self.duration = 5200          # Total duration in milliseconds (~5.2s)
        self.start_time = None
        self.finished = False

        # Center coordinates
        self.cx, self.cy = 400, 205   # Emblem center
        self.text_y = 356             # "IAMBKRAM" text center
        self.sub_y = 422              # "PRESENTS" subtitle center

        # Audio trigger state
        self.snd_ignition_played = False
        self.snd_impact_played = False
        self.snd_sweep_played = False

        # Screen shake
        self.shake_x = 0.0
        self.shake_y = 0.0

        # Warp Starfield (160 radial hyper-drive stars)
        self.warp_stars = []
        for _ in range(160):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(15, 520)
            spd = random.uniform(2.2, 7.5)
            col = random.choice([
                NEON_CYAN,
                NEON_PURPLE,
                NEON_PINK,
                NEON_BLUE,
                (220, 240, 255),
                WHITE
            ])
            self.warp_stars.append({
                'ang': ang,
                'dist': dist,
                'spd': spd,
                'col': col,
                'size': random.uniform(1.2, 2.6)
            })

        # Dynamic Particles (Sparks, Embers, Explosions)
        self.particles = []

        # Shockwave Rings
        self.shockwaves = []

        # Perspective Grid scrolling offset
        self.grid_scroll = 0.0

        # Fonts
        self.font_brand = pygame.font.SysFont("Impact", 86)
        self.font_sub = pygame.font.SysFont("Arial Black", 14)
        self.font_hud = pygame.font.SysFont("Consolas", 11)

        # Pre-calculated letter positions for "IAMBKRAM" for precise specular lighting
        self.letters = ["I", "A", "M", "B", "K", "R", "A", "M"]
        self.letter_surfs = [self.font_brand.render(ch, True, WHITE) for ch in self.letters]
        self.letter_widths = [s.get_width() for s in self.letter_surfs]
        self.letter_spacing = 8
        total_text_w = sum(self.letter_widths) + (len(self.letters) - 1) * self.letter_spacing
        
        # Calculate X center for each letter
        curr_x = self.cx - total_text_w // 2
        self.letter_x_centers = []
        for i, w in enumerate(self.letter_widths):
            cx_letter = curr_x + w // 2
            self.letter_x_centers.append(cx_letter)
            curr_x += w + self.letter_spacing

        # Pre-render letter glow halos
        self.letter_glow_surfs = [
            self.font_brand.render(ch, True, NEON_CYAN) for ch in self.letters
        ]
        self.letter_chroma_r = [
            self.font_brand.render(ch, True, (255, 40, 90)) for ch in self.letters
        ]
        self.letter_chroma_b = [
            self.font_brand.render(ch, True, (0, 220, 255)) for ch in self.letters
        ]

        # Pre-allocated reusable scratch surfaces for performance
        self._streak_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        self._hex_glow_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        self._dissolve_surf = pygame.Surface((800, 600), pygame.SRCALPHA)

    def reset(self):
        """Reset animation state for re-runs."""
        self.start_time = None
        self.finished = False
        self.snd_ignition_played = False
        self.snd_impact_played = False
        self.snd_sweep_played = False
        self.particles.clear()
        self.shockwaves.clear()
        self.shake_x = 0.0
        self.shake_y = 0.0

    def skip(self):
        """Immediately conclude animation and transition to menu."""
        self.finished = True

    def is_finished(self):
        return self.finished

    def _spawn_shockwave(self, x, y, max_radius=380, speed=11.0, color=NEON_CYAN, width=3):
        self.shockwaves.append({
            'x': x, 'y': y,
            'r': 6.0,
            'max_r': max_radius,
            'spd': speed,
            'col': color,
            'w': width,
            'alpha': 255.0
        })

    def _spawn_radial_burst(self, x, y, count=60, speed_range=(4.0, 16.0)):
        """Spawn 360-degree supernova blast sparks."""
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed_range[0], speed_range[1])
            life = random.randint(45, 80)
            col = random.choice([
                WHITE,
                NEON_CYAN,
                NEON_PINK,
                NEON_GOLD,
                NEON_PURPLE,
                (180, 240, 255)
            ])
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(ang) * spd,
                'vy': math.sin(ang) * spd,
                'life': life,
                'max_life': life,
                'col': col,
                'size': random.uniform(2.5, 6.0),
                'decay': random.uniform(0.93, 0.97)
            })

    def update_and_draw(self, screen, dt, now, tap_snd=None, hit_snd=None, expl_snd=None):
        if self.finished:
            return

        if self.start_time is None:
            self.start_time = now

        elapsed = now - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            return

        t_sec = elapsed / 1000.0  # seconds

        # ==========================================
        # 1. SCREEN SHAKE & AUDIO SYNCHRONIZATION
        # ==========================================
        self.shake_x *= 0.84
        self.shake_y *= 0.84
        if abs(self.shake_x) < 0.2: self.shake_x = 0.0
        if abs(self.shake_y) < 0.2: self.shake_y = 0.0

        # Audio Cue 1: Ignition (t = 200ms)
        if elapsed >= 200 and not self.snd_ignition_played:
            if tap_snd: tap_snd.play()
            self.snd_ignition_played = True
            self._spawn_shockwave(self.cx, self.cy, max_radius=300, speed=7.0, color=NEON_PURPLE, width=2)

        # Audio Cue 2: Slam Impact (t = 1600ms)
        if elapsed >= 1600 and not self.snd_impact_played:
            if hit_snd: hit_snd.play()
            self.snd_impact_played = True
            # Trigger screen shake
            self.shake_x = random.choice([-1, 1]) * random.uniform(7.0, 11.0)
            self.shake_y = random.choice([-1, 1]) * random.uniform(6.0, 9.0)
            # Twin supernova shockwaves
            self._spawn_shockwave(self.cx, self.cy, max_radius=450, speed=11.0, color=NEON_CYAN, width=4)
            self._spawn_shockwave(self.cx, self.cy, max_radius=360, speed=8.0, color=NEON_PINK, width=2)
            # Particle supernova
            self._spawn_radial_burst(self.cx, self.cy, count=70, speed_range=(4.0, 16.0))

        # Audio Cue 3: Specular Laser Sweep (t = 2850ms)
        if elapsed >= 2850 and not self.snd_sweep_played:
            if tap_snd: tap_snd.play()
            self.snd_sweep_played = True
            self._spawn_shockwave(self.cx, self.text_y, max_radius=280, speed=9.0, color=NEON_GOLD, width=2)

        # Offset target for all rendering
        ox = int(self.shake_x)
        oy = int(self.shake_y)

        # ==========================================
        # 2. HYPERSPACE RADIAL WARP STARFIELD
        # ==========================================
        # Dynamic warp speed multiplier (surges at start and during climax)
        if elapsed < 1200:
            warp_mult = 1.0 + (elapsed / 1200.0) * 2.5
        elif elapsed < 4200:
            warp_mult = 1.2 + 0.3 * math.sin(t_sec * 3.5)
        else:
            warp_mult = 1.5 + ((elapsed - 4200) / 1000.0) * 4.5

        for s in self.warp_stars:
            s['dist'] += s['spd'] * warp_mult * dt
            if s['dist'] > 540:
                s['dist'] = random.uniform(10, 35)
                s['ang'] = random.uniform(0, 2 * math.pi)
                s['spd'] = random.uniform(2.2, 7.5)

            # Calculate streak coordinates radiating from (cx, cy)
            x1 = self.cx + ox + math.cos(s['ang']) * s['dist']
            y1 = self.cy + oy + math.sin(s['ang']) * s['dist']
            
            streak_len = max(2.0, (s['dist'] * 0.08) * (warp_mult * 0.7))
            x2 = self.cx + ox + math.cos(s['ang']) * (s['dist'] + streak_len)
            y2 = self.cy + oy + math.sin(s['ang']) * (s['dist'] + streak_len)

            alpha = min(255, int((s['dist'] / 180.0) * 255))
            if alpha > 10:
                self._streak_surf.fill((0, 0, 0, 0))
                line_surf = self._streak_surf
                min_x = min(x1, x2)
                min_y = min(y1, y2)
                sw = max(8, int(abs(x2 - x1) + 8))
                sh = max(8, int(abs(y2 - y1) + 8))
                lx1 = x1 - min_x + 3
                ly1 = y1 - min_y + 3
                lx2 = x2 - min_x + 3
                ly2 = y2 - min_y + 3
                # Clamp to scratch surface bounds
                if lx2 < 200 and ly2 < 200 and lx1 < 200 and ly1 < 200:
                    pygame.draw.line(line_surf, (*s['col'], alpha), (lx1, ly1), (lx2, ly2), max(1, int(s['size'])))
                    screen.blit(line_surf, (min_x - 3, min_y - 3))

        # ==========================================
        # 3. 3D PERSPECTIVE CYBER MATRIX FLOOR GRID
        # ==========================================
        self.grid_scroll += 1.8 * warp_mult * dt
        if self.grid_scroll >= 40.0:
            self.grid_scroll -= 40.0

        grid_surf = pygame.Surface((WIDTH, 220), pygame.SRCALPHA)
        horizon_y = 380
        vanish_x = self.cx + ox

        # Radial perspective lines fanning down
        for fan_x in range(-200, WIDTH + 220, 50):
            pygame.draw.line(grid_surf, (*NEON_PURPLE, 24), (vanish_x, 0), (fan_x, 220), 1)

        # Horizontal depth lines with perspective compression
        for i in range(1, 10):
            depth_frac = (i * 22 + self.grid_scroll) / 220.0
            if depth_frac <= 1.0:
                py = int(depth_frac * depth_frac * 220)
                grid_alpha = int(45 * depth_frac)
                pygame.draw.line(grid_surf, (*NEON_CYAN, grid_alpha), (0, py), (WIDTH, py), 1)

        screen.blit(grid_surf, (0, horizon_y))

        # ==========================================
        # 4. SINGULARITY CORE & INWARD SPARK GATHERING
        # ==========================================
        if elapsed < 1600:
            # Spawn inward flowing particles
            if random.random() < 0.65:
                p_ang = random.uniform(0, 2 * math.pi)
                p_dist = random.uniform(160, 320)
                self.particles.append({
                    'x': self.cx + math.cos(p_ang) * p_dist,
                    'y': self.cy + math.sin(p_ang) * p_dist,
                    'vx': -math.cos(p_ang) * random.uniform(4.0, 9.0),
                    'vy': -math.sin(p_ang) * random.uniform(4.0, 9.0),
                    'life': 30,
                    'max_life': 30,
                    'col': random.choice([NEON_CYAN, NEON_PURPLE, WHITE]),
                    'size': random.uniform(2.0, 4.0),
                    'decay': 1.0
                })

            # Pulsing singularity core sphere
            sing_r = int(12 + 8 * math.sin(t_sec * 10.0))
            sing_surf = pygame.Surface((sing_r * 4, sing_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(sing_surf, (*NEON_CYAN, 80), (sing_r * 2, sing_r * 2), sing_r * 2)
            pygame.draw.circle(sing_surf, (*NEON_PURPLE, 140), (sing_r * 2, sing_r * 2), sing_r + 4)
            pygame.draw.circle(sing_surf, (255, 255, 255, 240), (sing_r * 2, sing_r * 2), sing_r // 2)
            screen.blit(sing_surf, (self.cx + ox - sing_r * 2, self.cy + oy - sing_r * 2))

        # ==========================================
        # 5. SHOCKWAVES UPDATE & RENDER
        # ==========================================
        for sw in self.shockwaves[:]:
            sw['r'] += sw['spd'] * dt
            progress_sw = sw['r'] / sw['max_r']
            sw['alpha'] = max(0.0, 255.0 * (1.0 - progress_sw))

            if progress_sw >= 1.0 or sw['alpha'] <= 0:
                self.shockwaves.remove(sw)
                continue

            r_int = int(sw['r'])
            sw_surf = pygame.Surface((r_int * 2 + 16, r_int * 2 + 16), pygame.SRCALPHA)
            a_int = int(sw['alpha'])
            # Soft outer glow ring
            pygame.draw.circle(sw_surf, (*sw['col'], a_int // 3), (r_int + 8, r_int + 8), r_int + 2, sw['w'] + 2)
            # Sharp intense inner ring
            pygame.draw.circle(sw_surf, (*sw['col'], a_int), (r_int + 8, r_int + 8), r_int, sw['w'])
            screen.blit(sw_surf, (int(sw['x']) + ox - r_int - 8, int(sw['y']) + oy - r_int - 8))

        # ==========================================
        # 6. DYNAMIC PARTICLES (Sparks, Embers)
        # ==========================================
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vx'] *= p['decay']
            p['vy'] *= p['decay']
            p['life'] -= 1

            if p['life'] <= 0:
                self.particles.remove(p)
                continue

            life_frac = p['life'] / p['max_life']
            p_alpha = int(255 * life_frac)
            p_size = max(1, int(p['size'] * life_frac))
            
            p_surf = pygame.Surface((p_size * 4, p_size * 4), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p['col'], p_alpha), (p_size * 2, p_size * 2), p_size)
            screen.blit(p_surf, (int(p['x']) + ox - p_size * 2, int(p['y']) + oy - p_size * 2))

        # ==========================================
        # 7. THE "IAMBKRAM" APEX CYBER EMBLEM
        # ==========================================
        if elapsed >= 600:
            # Scale calculation with elastic drop-in
            if elapsed < 1600:
                # Elastic ease-out descending: 2.5 -> 1.0
                e_t = (elapsed - 600) / 1000.0
                emblem_scale = 1.0 + 1.5 * ((1.0 - e_t) ** 2.2)
                emblem_alpha = min(255, int(e_t * 255))
            else:
                # Subtle breathing pulse
                emblem_scale = 1.0 + 0.03 * math.sin(t_sec * 3.5)
                emblem_alpha = 255

            emblem_cx = self.cx + ox
            emblem_cy = self.cy + oy

            # --- A. ROTATING DUAL CONCENTRIC HUD RINGS ---
            # Outer Ring (Radius ~74, rotating clockwise)
            rot_outer = t_sec * 1.2
            outer_r = int(74 * emblem_scale)
            ring_surf_outer = pygame.Surface((outer_r * 2 + 20, outer_r * 2 + 20), pygame.SRCALPHA)
            center_ro = outer_r + 10

            # Draw 4 segmented arcs in Neon Cyan
            for arc_i in range(4):
                start_ang = rot_outer + arc_i * (math.pi / 2) + 0.15
                end_ang = start_ang + (math.pi / 2) - 0.30
                arc_pts = []
                for step in range(12):
                    theta = start_ang + (step / 11.0) * (end_ang - start_ang)
                    arc_pts.append((
                        center_ro + math.cos(theta) * outer_r,
                        center_ro + math.sin(theta) * outer_r
                    ))
                if len(arc_pts) > 1:
                    pygame.draw.lines(ring_surf_outer, (*NEON_CYAN, min(255, int(emblem_alpha * 0.85))), False, arc_pts, 2)

            # Draw 4 cardinal tick markers
            for tick_i in range(4):
                tick_ang = rot_outer + tick_i * (math.pi / 2)
                tx1 = center_ro + math.cos(tick_ang) * (outer_r - 5)
                ty1 = center_ro + math.sin(tick_ang) * (outer_r - 5)
                tx2 = center_ro + math.cos(tick_ang) * (outer_r + 5)
                ty2 = center_ro + math.sin(tick_ang) * (outer_r + 5)
                pygame.draw.line(ring_surf_outer, (*NEON_PINK, emblem_alpha), (tx1, ty1), (tx2, ty2), 2)

            screen.blit(ring_surf_outer, (emblem_cx - center_ro, emblem_cy - center_ro))

            # Inner Ring (Radius ~56, counter-clockwise rotation)
            rot_inner = -t_sec * 1.8
            inner_r = int(56 * emblem_scale)
            ring_surf_inner = pygame.Surface((inner_r * 2 + 16, inner_r * 2 + 16), pygame.SRCALPHA)
            center_ri = inner_r + 8

            # Draw 8 mini diamond dots
            for dot_i in range(8):
                dot_ang = rot_inner + dot_i * (math.pi / 4)
                dx = center_ri + math.cos(dot_ang) * inner_r
                dy = center_ri + math.sin(dot_ang) * inner_r
                pygame.draw.circle(ring_surf_inner, (*NEON_PURPLE, min(255, int(emblem_alpha * 0.9))), (int(dx), int(dy)), 2)

            screen.blit(ring_surf_inner, (emblem_cx - center_ri, emblem_cy - center_ri))

            # --- B. HOLOGRAPHIC NEON HEXAGON SHIELD ---
            hex_r = 44 * emblem_scale
            hex_pts = []
            for i in range(6):
                ang = i * (math.pi / 3) - math.pi / 2
                hex_pts.append((
                    emblem_cx + math.cos(ang) * hex_r,
                    emblem_cy + math.sin(ang) * hex_r
                ))

            # Layer 1: Glow halo
            self._hex_glow_surf.fill((0, 0, 0, 0))
            glow_poly = self._hex_glow_surf
            pygame.draw.polygon(glow_poly, (*NEON_PURPLE, int(emblem_alpha * 0.25)), hex_pts, width=8)
            screen.blit(glow_poly, (0, 0))

            # Layer 2: Translucent Hex Fill
            self._hex_glow_surf.fill((0, 0, 0, 0))
            fill_poly = self._hex_glow_surf
            pygame.draw.polygon(fill_poly, (15, 20, 42, int(emblem_alpha * 0.75)), hex_pts)
            screen.blit(fill_poly, (0, 0))

            # Layer 3: Sharp Neon Cyan Border
            pygame.draw.polygon(screen, NEON_CYAN, hex_pts, width=2)

            # --- C. APEX DELTA STARSHIP WINGS ---
            w_scale = emblem_scale
            wing_l = [
                (emblem_cx - 24 * w_scale, emblem_cy + 22 * w_scale),
                (emblem_cx,                emblem_cy - 28 * w_scale),
                (emblem_cx - 6 * w_scale,  emblem_cy - 4 * w_scale)
            ]
            wing_r = [
                (emblem_cx + 24 * w_scale, emblem_cy + 22 * w_scale),
                (emblem_cx,                emblem_cy - 28 * w_scale),
                (emblem_cx + 6 * w_scale,  emblem_cy - 4 * w_scale)
            ]
            w_fill = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(w_fill, (*NEON_BLUE, int(emblem_alpha * 0.8)), wing_l)
            pygame.draw.polygon(w_fill, (*NEON_BLUE, int(emblem_alpha * 0.8)), wing_r)
            screen.blit(w_fill, (0, 0))
            pygame.draw.polygon(screen, WHITE, wing_l, width=1)
            pygame.draw.polygon(screen, WHITE, wing_r, width=1)

            # --- D. CENTRAL SINGULARITY CRYSTAL (Pulsing Diamond) ---
            core_r = (10 + 4 * math.sin(t_sec * 6.0)) * emblem_scale
            core_pts = [
                (emblem_cx,                emblem_cy - core_r * 1.3),
                (emblem_cx + core_r * 0.9, emblem_cy),
                (emblem_cx,                emblem_cy + core_r * 1.3),
                (emblem_cx - core_r * 0.9, emblem_cy)
            ]
            core_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(core_surf, (255, 255, 255, emblem_alpha), core_pts)
            pygame.draw.polygon(core_surf, (*NEON_GOLD, int(emblem_alpha * 0.7)), core_pts, width=2)
            screen.blit(core_surf, (0, 0))

        # ==========================================
        # 8. MULTI-LAYER NEON "IAMBKRAM" TYPOGRAPHY
        # ==========================================
        if elapsed >= 1700:
            text_alpha_t = min(1.0, (elapsed - 1700) / 600.0)
            text_alpha = int(text_alpha_t * 255)

            # Specular flare X position (sweeps left -> right from t=2800 to t=4200)
            if 2800 <= elapsed <= 4200:
                sweep_progress = (elapsed - 2800) / 1400.0
                # Smooth cubic ease
                sweep_x = 120 + (sweep_progress * sweep_progress * (3.0 - 2.0 * sweep_progress)) * 560
            else:
                sweep_x = -999.0

            # Render each letter with individual specular flare response
            for i, ch in enumerate(self.letters):
                lx = self.letter_x_centers[i] + ox
                ly = self.text_y + oy

                # Calculate specular flash for this letter based on flare distance
                dist_to_flare = abs(lx - sweep_x)
                if dist_to_flare < 45.0:
                    specular_boost = 1.0 - (dist_to_flare / 45.0)
                else:
                    specular_boost = 0.0

                # --- Layer 1: Soft Outer Neon Bloom ---
                bloom_s = self.letter_glow_surfs[i].copy()
                bloom_alpha = min(255, int(text_alpha * (0.45 + 0.55 * specular_boost)))
                bloom_s.set_alpha(bloom_alpha)
                for bx, by in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                    screen.blit(bloom_s, bloom_s.get_rect(center=(lx + bx, ly + by)))

                # --- Layer 2: Chromatic Aberration 3D Split ---
                if text_alpha > 50:
                    chr_r = self.letter_chroma_r[i].copy()
                    chr_r.set_alpha(int(text_alpha * 0.35))
                    screen.blit(chr_r, chr_r.get_rect(center=(lx - 2, ly)))
                    chr_b = self.letter_chroma_b[i].copy()
                    chr_b.set_alpha(int(text_alpha * 0.35))
                    screen.blit(chr_b, chr_b.get_rect(center=(lx + 2, ly)))

                # --- Layer 3: Solid Face with Specular Illumination ---
                if specular_boost > 0.05:
                    face_s = self.letter_surfs[i].copy()
                    face_s.set_alpha(255)
                    sc = 1.0 + 0.12 * specular_boost
                    if sc > 1.01:
                        face_s = pygame.transform.scale(
                            face_s,
                            (int(face_s.get_width() * sc), int(face_s.get_height() * sc))
                        )
                    screen.blit(face_s, face_s.get_rect(center=(lx, ly - int(3 * specular_boost))))
                else:
                    face_s = self.letter_surfs[i].copy()
                    face_s.set_alpha(text_alpha)
                    screen.blit(face_s, face_s.get_rect(center=(lx, ly)))

            # ==========================================
            # 9. SPECULAR LASER LENS FLARE
            # ==========================================
            if 2800 <= elapsed <= 4200 and sweep_x > 0:
                fx = int(sweep_x) + ox
                fy = self.text_y + oy

                flare_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                # A. 45-degree angled laser beam streak
                pygame.draw.line(flare_surf, (255, 255, 255, 140), (fx - 30, fy - 50), (fx + 30, fy + 50), 3)
                pygame.draw.line(flare_surf, (*NEON_CYAN, 70), (fx - 40, fy - 65), (fx + 40, fy + 65), 8)

                # B. Horizontal lens flare line (180px wide)
                pygame.draw.line(flare_surf, (255, 255, 255, 230), (fx - 90, fy), (fx + 90, fy), 2)
                pygame.draw.line(flare_surf, (*NEON_CYAN, 100), (fx - 130, fy), (fx + 130, fy), 5)

                # C. Central diamond lens flare core
                f_diamond = [(fx, fy - 18), (fx + 10, fy), (fx, fy + 18), (fx - 10, fy)]
                pygame.draw.polygon(flare_surf, (255, 255, 255, 255), f_diamond)
                pygame.draw.circle(flare_surf, (*NEON_GOLD, 160), (fx, fy), 20)

                screen.blit(flare_surf, (0, 0))

                # Emit trailing laser sparkle motes
                if random.random() < 0.7:
                    self.particles.append({
                        'x': fx + random.uniform(-10, 10),
                        'y': fy + random.uniform(-20, 20),
                        'vx': random.uniform(-1.5, 1.5),
                        'vy': random.uniform(-2.5, -0.5),
                        'life': 20,
                        'max_life': 20,
                        'col': random.choice([WHITE, NEON_GOLD, NEON_CYAN]),
                        'size': random.uniform(2.0, 3.5),
                        'decay': 0.94
                    })

            # ==========================================
            # 10. SUBTITLE & GLOWING HUD FRAMING
            # ==========================================
            if elapsed >= 2200:
                sub_alpha_t = min(1.0, (elapsed - 2200) / 500.0)
                sub_alpha = int(sub_alpha_t * 255)

                # A. Laser Divider Lines flanking subtitle
                div_len = int(140 * sub_alpha_t)
                draw_divider(screen, self.cx + ox - 240, self.sub_y + oy, self.cx + ox - 240 + div_len, color=NEON_CYAN, alpha=int(sub_alpha * 0.6))
                draw_divider(screen, self.cx + ox + 240 - div_len, self.sub_y + oy, self.cx + ox + 240, color=NEON_CYAN, alpha=int(sub_alpha * 0.6))

                # B. Subtitle: [ P R E S E N T S ]
                sub_text = "[  P R E S E N T S  ]"
                sub_surf = self.font_sub.render(sub_text, True, NEON_GOLD)
                sub_surf.set_alpha(sub_alpha)
                screen.blit(sub_surf, sub_surf.get_rect(center=(self.cx + ox, self.sub_y + oy)))

            # ==========================================
            # 11. CYBERPUNK CORNER HUD BRACKETS & TELEMETRY
            # ==========================================
            if elapsed >= 2400:
                hud_alpha_t = min(1.0, (elapsed - 2400) / 500.0)
                hud_alpha = int(hud_alpha_t * 160)

                hud_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                bracket_col = (*NEON_CYAN, hud_alpha)

                # Top-Left Bracket & Text
                pygame.draw.lines(hud_surf, bracket_col, False, [(30, 50), (30, 30), (50, 30)], 2)
                tl_txt = self.font_hud.render("SYS_BOOT // OK", True, NEON_CYAN)
                tl_txt.set_alpha(hud_alpha)
                hud_surf.blit(tl_txt, (58, 25))

                # Top-Right Bracket & Text
                pygame.draw.lines(hud_surf, bracket_col, False, [(WIDTH - 30, 50), (WIDTH - 30, 30), (WIDTH - 50, 30)], 2)
                tr_txt = self.font_hud.render("CORE // 100%", True, NEON_CYAN)
                tr_txt.set_alpha(hud_alpha)
                hud_surf.blit(tr_txt, (WIDTH - tr_txt.get_width() - 58, 25))

                # Bottom-Left Bracket & Text
                pygame.draw.lines(hud_surf, bracket_col, False, [(30, HEIGHT - 50), (30, HEIGHT - 30), (50, HEIGHT - 30)], 2)
                bl_txt = self.font_hud.render("STUDIO // IAMBKRAM", True, NEON_PINK)
                bl_txt.set_alpha(hud_alpha)
                hud_surf.blit(bl_txt, (58, HEIGHT - 38))

                # Bottom-Right Bracket & Text
                pygame.draw.lines(hud_surf, bracket_col, False, [(WIDTH - 30, HEIGHT - 50), (WIDTH - 30, HEIGHT - 30), (WIDTH - 50, HEIGHT - 30)], 2)
                br_txt = self.font_hud.render("INITIALIZED // READY", True, NEON_GREEN)
                br_txt.set_alpha(hud_alpha)
                hud_surf.blit(br_txt, (WIDTH - br_txt.get_width() - 58, HEIGHT - 38))

                screen.blit(hud_surf, (0, 0))

        # ==========================================
        # 12. CINEMATIC CLIMAX & SEAMLESS DISSOLVE
        # ==========================================
        if elapsed >= 4400:
            fade_progress = (elapsed - 4400) / 800.0
            flash_alpha = min(255, int(fade_progress * 240))
            
            # Subtle radial energy surge flash
            self._dissolve_surf.fill((0, 0, 0, 0))
            flash_surf = self._dissolve_surf
            flash_surf.fill((0, 0, 15, flash_alpha))
            screen.blit(flash_surf, (0, 0))
