import pygame
import math
import random
from settings import (WIDTH, HEIGHT, NEON_CYAN, NEON_PURPLE, NEON_PINK,
                      NEON_BLUE, NEON_GOLD, NEON_GREEN, NEON_ORANGE,
                      WHITE, RED)
from assets import draw_text, draw_text_shadow, draw_divider, draw_badge


class CinematicBranding:
    """
    Hollywood-Grade Cinematic Cyberpunk Branding Intro for 'IAMBKRAM'.
    Engineered with pure Python / Pygame procedural rendering:
      - Deep-space hyper-warp relativistic radial star streaks with chromatic trails
      - Retro-futuristic 3D perspective cyber grid with depth fog and horizon laser
      - Singularity genesis with inward spiral energy streamers & procedural arc lightning
      - Elastic ease-out quantum emblem slam with supersonic shockwave blasts (BLEND_ADD)
      - Triple concentric counter-rotating holographic orbital HUD telemetry rings
      - 3D faceted Hexagonal Titanium Shield with perimeter laser trace and swept delta wings
      - Multi-layer neon 'IAMBKRAM' typography with 3D chromatic aberration split
      - Hollywood anamorphic laser lens flare sweep with individual letter super-ignition
      - Cyberpunk telemetry HUD framing, corner brackets, and audio frequency visualizer
      - High-energy hyperspace jump flash and cinematic crossfade into Main Menu
    """
    def __init__(self):
        self.duration = 5200          # Total duration in milliseconds (~5.2s)
        self.start_time = None
        self.finished = False

        # Center coordinates
        self.cx, self.cy = 400, 205   # Emblem center
        self.text_y = 356             # "IAMBKRAM" text center
        self.sub_y = 422              # "PRESENTS" subtitle center

        # Audio triggers
        self.snd_ignition_played = False
        self.snd_impact_played = False
        self.snd_sweep_played = False

        # Screen shake
        self.shake_x = 0.0
        self.shake_y = 0.0

        # Warp Starfield (180 relativistic warp stars)
        self.warp_stars = []
        for _ in range(180):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(15, 540)
            spd = random.uniform(2.5, 8.5)
            col = random.choice([
                NEON_CYAN,
                NEON_PURPLE,
                NEON_PINK,
                NEON_BLUE,
                NEON_GOLD,
                (220, 240, 255),
                WHITE
            ])
            self.warp_stars.append({
                'ang': ang,
                'dist': dist,
                'spd': spd,
                'col': col,
                'size': random.uniform(1.2, 2.8)
            })

        # Dynamic Particles & Lightning Arcs
        self.particles = []
        self.shockwaves = []
        self.lightning_arcs = []

        # Perspective Grid scrolling offset
        self.grid_scroll = 0.0

        # Typography — Sleek Futuristic Sci-Fi Font Stack
        font_candidates = ["Bahnschrift", "Segoe UI", "Trebuchet MS", "Century Gothic", "Arial Black"]
        self.font_brand = None
        for fc in font_candidates:
            try:
                self.font_brand = pygame.font.SysFont(fc, 52, bold=True)
                if self.font_brand:
                    break
            except Exception:
                continue
        if not self.font_brand:
            self.font_brand = pygame.font.SysFont(None, 52, bold=True)

        self.font_sub = pygame.font.SysFont("Consolas", 13, bold=True)
        self.font_hud = pygame.font.SysFont("Consolas", 11)

        # Pre-calculated letter positions for "IAMBKRAM" with wide cinematic tracking
        self.letters = ["I", "A", "M", "B", "K", "R", "A", "M"]
        self.letter_surfs = [self.font_brand.render(ch, True, WHITE) for ch in self.letters]
        self.letter_widths = [s.get_width() for s in self.letter_surfs]
        self.letter_spacing = 16  # Wide, elegant sci-fi tracking
        total_text_w = sum(self.letter_widths) + (len(self.letters) - 1) * self.letter_spacing
        
        curr_x = self.cx - total_text_w // 2
        self.letter_x_centers = []
        for w in self.letter_widths:
            cx_letter = curr_x + w // 2
            self.letter_x_centers.append(cx_letter)
            curr_x += w + self.letter_spacing

        # Pre-render letter glow halos (soft, diffused, non-blocking)
        self.letter_glow_surfs = [
            self.font_brand.render(ch, True, (0, 235, 255)) for ch in self.letters
        ]
        self.letter_shadow_surfs = [
            self.font_brand.render(ch, True, (8, 12, 28)) for ch in self.letters
        ]
        self.letter_chroma_r = [
            self.font_brand.render(ch, True, (255, 40, 90)) for ch in self.letters
        ]
        self.letter_chroma_b = [
            self.font_brand.render(ch, True, (0, 200, 255)) for ch in self.letters
        ]

        # Scratch surfaces for performance
        self._streak_surf = pygame.Surface((220, 220), pygame.SRCALPHA)
        self._hex_glow_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        self._dissolve_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        self._hud_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def reset(self):
        """Reset animation state for fresh re-runs."""
        self.start_time = None
        self.finished = False
        self.snd_ignition_played = False
        self.snd_impact_played = False
        self.snd_sweep_played = False
        self.particles.clear()
        self.shockwaves.clear()
        self.lightning_arcs.clear()
        self.shake_x = 0.0
        self.shake_y = 0.0

    def skip(self):
        """Immediately conclude animation and transition to menu."""
        self.finished = True

    def is_finished(self):
        return self.finished

    def _spawn_shockwave(self, x, y, max_radius=420, speed=12.0, color=NEON_CYAN, width=3):
        self.shockwaves.append({
            'x': x, 'y': y,
            'r': 6.0,
            'max_r': max_radius,
            'spd': speed,
            'col': color,
            'w': width,
            'alpha': 255.0
        })

    def _spawn_radial_burst(self, x, y, count=90, speed_range=(4.0, 18.0)):
        """Spawn 360-degree supernova blast sparks."""
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed_range[0], speed_range[1])
            life = random.randint(45, 90)
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
                'size': random.uniform(2.5, 6.5),
                'decay': random.uniform(0.92, 0.96)
            })

    def _generate_lightning(self, start_pt, end_pt, segments=5, jitter=18):
        """Generate jagged procedural lightning path."""
        pts = [start_pt]
        cur = start_pt
        for i in range(1, segments):
            frac = i / segments
            base_x = start_pt[0] + (end_pt[0] - start_pt[0]) * frac
            base_y = start_pt[1] + (end_pt[1] - start_pt[1]) * frac
            jitter_x = random.uniform(-jitter, jitter)
            jitter_y = random.uniform(-jitter, jitter)
            pts.append((int(base_x + jitter_x), int(base_y + jitter_y)))
        pts.append(end_pt)
        return pts

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

        # =========================================================================
        # 1. SCREEN SHAKE & AUDIO SYNCHRONIZATION
        # =========================================================================
        self.shake_x *= 0.84
        self.shake_y *= 0.84
        if abs(self.shake_x) < 0.2: self.shake_x = 0.0
        if abs(self.shake_y) < 0.2: self.shake_y = 0.0

        # Audio Cue 1: Singularity Ignition (t = 200ms)
        if elapsed >= 200 and not self.snd_ignition_played:
            if tap_snd: tap_snd.play()
            self.snd_ignition_played = True
            self._spawn_shockwave(self.cx, self.cy, max_radius=320, speed=7.5, color=NEON_PURPLE, width=2)

        # Audio Cue 2: Quantum Emblem Slam Impact (t = 1500ms)
        if elapsed >= 1500 and not self.snd_impact_played:
            if hit_snd: hit_snd.play()
            if expl_snd: expl_snd.play()
            self.snd_impact_played = True
            # Visceral multi-frequency screen shake
            self.shake_x = random.choice([-1, 1]) * random.uniform(8.0, 14.0)
            self.shake_y = random.choice([-1, 1]) * random.uniform(7.0, 11.0)
            # High-speed expanding chromatic shockwaves (fast expansion, no lingering rings)
            self._spawn_shockwave(self.cx, self.cy, max_radius=480, speed=16.0, color=NEON_CYAN, width=3)
            self._spawn_shockwave(self.cx, self.cy, max_radius=380, speed=13.5, color=NEON_PINK, width=2)
            # 100-particle supernova blast
            self._spawn_radial_burst(self.cx, self.cy, count=90, speed_range=(4.0, 18.0))

        # Audio Cue 3: Specular Laser Flare Sweep (t = 2750ms)
        if elapsed >= 2750 and not self.snd_sweep_played:
            if tap_snd: tap_snd.play()
            self.snd_sweep_played = True
            self._spawn_shockwave(self.cx, self.text_y, max_radius=300, speed=9.5, color=NEON_GOLD, width=2)

        ox = int(self.shake_x)
        oy = int(self.shake_y)

        # =========================================================================
        # 2. HYPERSPACE RELATIVISTIC WARP STARFIELD
        # =========================================================================
        if elapsed < 1200:
            warp_mult = 1.0 + (elapsed / 1200.0) * 3.0
        elif elapsed < 4200:
            warp_mult = 1.3 + 0.35 * math.sin(t_sec * 3.5)
        else:
            warp_mult = 1.6 + ((elapsed - 4200) / 1000.0) * 5.0

        for s in self.warp_stars:
            s['dist'] += s['spd'] * warp_mult * dt
            if s['dist'] > 560:
                s['dist'] = random.uniform(10, 35)
                s['ang'] = random.uniform(0, 2 * math.pi)
                s['spd'] = random.uniform(2.5, 8.5)

            x1 = self.cx + ox + math.cos(s['ang']) * s['dist']
            y1 = self.cy + oy + math.sin(s['ang']) * s['dist']
            
            streak_len = max(2.5, (s['dist'] * 0.09) * (warp_mult * 0.75))
            x2 = self.cx + ox + math.cos(s['ang']) * (s['dist'] + streak_len)
            y2 = self.cy + oy + math.sin(s['ang']) * (s['dist'] + streak_len)

            alpha = min(255, int((s['dist'] / 160.0) * 255))
            if alpha > 10:
                self._streak_surf.fill((0, 0, 0, 0))
                min_x = min(x1, x2)
                min_y = min(y1, y2)
                lx1 = x1 - min_x + 3
                ly1 = y1 - min_y + 3
                lx2 = x2 - min_x + 3
                ly2 = y2 - min_y + 3
                if lx2 < 220 and ly2 < 220 and lx1 < 220 and ly1 < 220:
                    pygame.draw.line(self._streak_surf, (*s['col'], alpha), (lx1, ly1), (lx2, ly2), max(1, int(s['size'])))
                    screen.blit(self._streak_surf, (min_x - 3, min_y - 3), special_flags=pygame.BLEND_ADD)

        # =========================================================================
        # 3. 3D PERSPECTIVE CYBER MATRIX FLOOR GRID
        # =========================================================================
        self.grid_scroll += 2.0 * warp_mult * dt
        if self.grid_scroll >= 40.0:
            self.grid_scroll -= 40.0

        grid_surf = pygame.Surface((WIDTH, 220), pygame.SRCALPHA)
        horizon_y = 380
        vanish_x = self.cx + ox

        # Radial perspective lines fanning down
        for fan_x in range(-200, WIDTH + 220, 48):
            pygame.draw.line(grid_surf, (*NEON_PURPLE, 28), (vanish_x, 0), (fan_x, 220), 1)

        # Horizontal depth lines with perspective compression
        for i in range(1, 11):
            depth_frac = (i * 20 + self.grid_scroll) / 220.0
            if depth_frac <= 1.0:
                py = int(depth_frac * depth_frac * 220)
                grid_alpha = int(55 * depth_frac)
                pygame.draw.line(grid_surf, (*NEON_CYAN, grid_alpha), (0, py), (WIDTH, py), 1)

        # Horizon laser glow line
        pygame.draw.line(grid_surf, (*NEON_CYAN, 120), (0, 0), (WIDTH, 0), 2)
        screen.blit(grid_surf, (0, horizon_y))

        # =========================================================================
        # 4. SINGULARITY CORE & ARC LIGHTNING GENESIS (t < 1.5s)
        # =========================================================================
        if elapsed < 1500:
            # Inward flowing energy sparks
            if random.random() < 0.75:
                p_ang = random.uniform(0, 2 * math.pi)
                p_dist = random.uniform(160, 340)
                self.particles.append({
                    'x': self.cx + math.cos(p_ang) * p_dist,
                    'y': self.cy + math.sin(p_ang) * p_dist,
                    'vx': -math.cos(p_ang) * random.uniform(5.0, 10.5),
                    'vy': -math.sin(p_ang) * random.uniform(5.0, 10.5),
                    'life': 28,
                    'max_life': 28,
                    'col': random.choice([NEON_CYAN, NEON_PURPLE, NEON_PINK, WHITE]),
                    'size': random.uniform(2.5, 4.5),
                    'decay': 1.0
                })

            # Procedural Arc Lightning Genesis
            if random.random() < 0.45:
                l_ang = random.uniform(0, 2 * math.pi)
                l_dist = random.uniform(120, 260)
                l_start = (int(self.cx + math.cos(l_ang) * l_dist), int(self.cy + math.sin(l_ang) * l_dist))
                l_end = (self.cx + ox, self.cy + oy)
                l_pts = self._generate_lightning(l_start, l_end, segments=6, jitter=16)
                l_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                l_col = random.choice([NEON_CYAN, NEON_PURPLE, (220, 240, 255)])
                pygame.draw.lines(l_surf, (*l_col, 200), False, l_pts, 2)
                pygame.draw.lines(l_surf, (255, 255, 255, 240), False, l_pts, 1)
                screen.blit(l_surf, (0, 0), special_flags=pygame.BLEND_ADD)

            # Pulsing singularity core
            sing_r = int(14 + 10 * math.sin(t_sec * 12.0))
            sing_surf = pygame.Surface((sing_r * 4, sing_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(sing_surf, (*NEON_CYAN, 80), (sing_r * 2, sing_r * 2), sing_r * 2)
            pygame.draw.circle(sing_surf, (*NEON_PURPLE, 150), (sing_r * 2, sing_r * 2), sing_r + 5)
            pygame.draw.circle(sing_surf, (255, 255, 255, 250), (sing_r * 2, sing_r * 2), sing_r // 2)
            screen.blit(sing_surf, (self.cx + ox - sing_r * 2, self.cy + oy - sing_r * 2), special_flags=pygame.BLEND_ADD)

        # =========================================================================
        # 5. SHOCKWAVES UPDATE & ADDITIVE RENDER
        # =========================================================================
        for sw in self.shockwaves[:]:
            sw['r'] += sw['spd'] * dt
            progress_sw = sw['r'] / sw['max_r']
            sw['alpha'] = max(0.0, 255.0 * (1.0 - progress_sw))

            if progress_sw >= 1.0 or sw['alpha'] <= 0:
                self.shockwaves.remove(sw)
                continue

            r_int = int(sw['r'])
            sw_surf = pygame.Surface((r_int * 2 + 18, r_int * 2 + 18), pygame.SRCALPHA)
            a_int = int(sw['alpha'])
            center_sw = (r_int + 9, r_int + 9)
            # Soft outer halo
            pygame.draw.circle(sw_surf, (*sw['col'], a_int // 3), center_sw, r_int + 3, sw['w'] + 3)
            # Sharp intense inner ring
            pygame.draw.circle(sw_surf, (*sw['col'], a_int), center_sw, r_int, sw['w'])
            screen.blit(sw_surf, (int(sw['x']) + ox - r_int - 9, int(sw['y']) + oy - r_int - 9), special_flags=pygame.BLEND_ADD)

        # =========================================================================
        # 6. DYNAMIC PARTICLES (Sparks & Embers)
        # =========================================================================
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
            screen.blit(p_surf, (int(p['x']) + ox - p_size * 2, int(p['y']) + oy - p_size * 2), special_flags=pygame.BLEND_ADD)

        # =========================================================================
        # 7. THE "IAMBKRAM" APEX CYBER EMBLEM
        # =========================================================================
        if elapsed >= 500:
            if elapsed < 1500:
                e_t = (elapsed - 500) / 1000.0
                emblem_scale = 1.0 + 1.6 * ((1.0 - e_t) ** 2.4)
                emblem_alpha = min(255, int(e_t * 255))
            else:
                emblem_scale = 1.0 + 0.03 * math.sin(t_sec * 3.5)
                emblem_alpha = 255

            emblem_cx = self.cx + ox
            emblem_cy = self.cy + oy

            # --- A. TRIPLE CONCENTRIC COUNTER-ROTATING HUD ORBITAL RINGS ---
            # 1. Outer Ring (Cyan segmented with tick marks)
            rot_outer = t_sec * 1.3
            outer_r = int(76 * emblem_scale)
            ring_surf_outer = pygame.Surface((outer_r * 2 + 24, outer_r * 2 + 24), pygame.SRCALPHA)
            center_ro = outer_r + 12

            for arc_i in range(4):
                start_ang = rot_outer + arc_i * (math.pi / 2) + 0.16
                end_ang = start_ang + (math.pi / 2) - 0.32
                arc_pts = []
                for step in range(12):
                    theta = start_ang + (step / 11.0) * (end_ang - start_ang)
                    arc_pts.append((
                        center_ro + math.cos(theta) * outer_r,
                        center_ro + math.sin(theta) * outer_r
                    ))
                if len(arc_pts) > 1:
                    pygame.draw.lines(ring_surf_outer, (*NEON_CYAN, min(255, int(emblem_alpha * 0.85))), False, arc_pts, 2)

            for tick_i in range(8):
                tick_ang = rot_outer + tick_i * (math.pi / 4)
                tx1 = center_ro + math.cos(tick_ang) * (outer_r - 4)
                ty1 = center_ro + math.sin(tick_ang) * (outer_r - 4)
                tx2 = center_ro + math.cos(tick_ang) * (outer_r + 4)
                ty2 = center_ro + math.sin(tick_ang) * (outer_r + 4)
                t_col = NEON_PINK if tick_i % 2 == 0 else NEON_GOLD
                pygame.draw.line(ring_surf_outer, (*t_col, emblem_alpha), (tx1, ty1), (tx2, ty2), 2)

            screen.blit(ring_surf_outer, (emblem_cx - center_ro, emblem_cy - center_ro), special_flags=pygame.BLEND_ADD)

            # 2. Middle Ring (Golden planetary orbit with satellite node)
            rot_mid = -t_sec * 1.6
            mid_r = int(62 * emblem_scale)
            ring_surf_mid = pygame.Surface((mid_r * 2 + 18, mid_r * 2 + 18), pygame.SRCALPHA)
            center_rm = mid_r + 9
            pygame.draw.circle(ring_surf_mid, (*NEON_GOLD, int(emblem_alpha * 0.45)), (center_rm, center_rm), mid_r, 1)
            # Orbiting satellite node
            node_x = center_rm + math.cos(rot_mid) * mid_r
            node_y = center_rm + math.sin(rot_mid) * mid_r
            pygame.draw.circle(ring_surf_mid, (255, 255, 255, emblem_alpha), (int(node_x), int(node_y)), 3)
            pygame.draw.circle(ring_surf_mid, (*NEON_GOLD, emblem_alpha), (int(node_x), int(node_y)), 6, 1)
            screen.blit(ring_surf_mid, (emblem_cx - center_rm, emblem_cy - center_rm), special_flags=pygame.BLEND_ADD)

            # 3. Inner Ring (Purple diamond pulse)
            rot_inner = t_sec * 2.2
            inner_r = int(50 * emblem_scale)
            ring_surf_inner = pygame.Surface((inner_r * 2 + 16, inner_r * 2 + 16), pygame.SRCALPHA)
            center_ri = inner_r + 8
            for dot_i in range(8):
                dot_ang = rot_inner + dot_i * (math.pi / 4)
                dx = center_ri + math.cos(dot_ang) * inner_r
                dy = center_ri + math.sin(dot_ang) * inner_r
                pygame.draw.circle(ring_surf_inner, (*NEON_PURPLE, min(255, int(emblem_alpha * 0.9))), (int(dx), int(dy)), 2)
            screen.blit(ring_surf_inner, (emblem_cx - center_ri, emblem_cy - center_ri), special_flags=pygame.BLEND_ADD)

            # --- B. 3D FACETED HEXAGONAL TITANIUM SHIELD ---
            hex_r = 44 * emblem_scale
            hex_pts = []
            for i in range(6):
                ang = i * (math.pi / 3) - math.pi / 2
                hex_pts.append((
                    emblem_cx + math.cos(ang) * hex_r,
                    emblem_cy + math.sin(ang) * hex_r
                ))

            # Shield glow halo
            self._hex_glow_surf.fill((0, 0, 0, 0))
            pygame.draw.polygon(self._hex_glow_surf, (*NEON_PURPLE, int(emblem_alpha * 0.3)), hex_pts, width=10)
            screen.blit(self._hex_glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

            # Translucent dark acrylic fill
            self._hex_glow_surf.fill((0, 0, 0, 0))
            pygame.draw.polygon(self._hex_glow_surf, (14, 18, 36, int(emblem_alpha * 0.85)), hex_pts)
            screen.blit(self._hex_glow_surf, (0, 0))

            # Neon Cyan Border
            pygame.draw.polygon(screen, NEON_CYAN, hex_pts, width=2)

            # Orbiting perimeter laser tracer on hex edge
            trace_prog = (t_sec * 1.5) % 6.0
            edge_i = int(trace_prog)
            edge_frac = trace_prog - edge_i
            p1 = hex_pts[edge_i]
            p2 = hex_pts[(edge_i + 1) % 6]
            tracer_x = p1[0] + (p2[0] - p1[0]) * edge_frac
            tracer_y = p1[1] + (p2[1] - p1[1]) * edge_frac
            pygame.draw.circle(screen, WHITE, (int(tracer_x), int(tracer_y)), 3)
            pygame.draw.circle(screen, NEON_CYAN, (int(tracer_x), int(tracer_y)), 6, 1)

            # --- C. SWEPT DELTA STARSHIP WINGS ---
            w_scale = emblem_scale
            wing_l = [
                (emblem_cx - 25 * w_scale, emblem_cy + 24 * w_scale),
                (emblem_cx,                emblem_cy - 28 * w_scale),
                (emblem_cx - 7 * w_scale,  emblem_cy - 4 * w_scale)
            ]
            wing_r = [
                (emblem_cx + 25 * w_scale, emblem_cy + 24 * w_scale),
                (emblem_cx,                emblem_cy - 28 * w_scale),
                (emblem_cx + 7 * w_scale,  emblem_cy - 4 * w_scale)
            ]
            w_fill = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(w_fill, (*NEON_BLUE, int(emblem_alpha * 0.85)), wing_l)
            pygame.draw.polygon(w_fill, (*NEON_BLUE, int(emblem_alpha * 0.85)), wing_r)
            screen.blit(w_fill, (0, 0))
            pygame.draw.polygon(screen, WHITE, wing_l, width=1)
            pygame.draw.polygon(screen, WHITE, wing_r, width=1)

            # Ion thruster trail sparks on wings
            if random.random() < 0.6:
                self.particles.append({
                    'x': emblem_cx - 24 * w_scale,
                    'y': emblem_cy + 24 * w_scale,
                    'vx': random.uniform(-1.0, 1.0),
                    'vy': random.uniform(2.0, 5.0),
                    'life': 16,
                    'max_life': 16,
                    'col': NEON_CYAN,
                    'size': 2.5,
                    'decay': 0.92
                })
                self.particles.append({
                    'x': emblem_cx + 24 * w_scale,
                    'y': emblem_cy + 24 * w_scale,
                    'vx': random.uniform(-1.0, 1.0),
                    'vy': random.uniform(2.0, 5.0),
                    'life': 16,
                    'max_life': 16,
                    'col': NEON_CYAN,
                    'size': 2.5,
                    'decay': 0.92
                })

            # --- D. CENTRAL PULSING 3D DIAMOND CRYSTAL ---
            core_r = (11 + 4 * math.sin(t_sec * 6.0)) * emblem_scale
            core_pts = [
                (emblem_cx,                emblem_cy - core_r * 1.3),
                (emblem_cx + core_r * 0.9, emblem_cy),
                (emblem_cx,                emblem_cy + core_r * 1.3),
                (emblem_cx - core_r * 0.9, emblem_cy)
            ]
            core_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(core_surf, (255, 255, 255, emblem_alpha), core_pts)
            pygame.draw.polygon(core_surf, (*NEON_GOLD, int(emblem_alpha * 0.8)), core_pts, width=2)
            screen.blit(core_surf, (0, 0), special_flags=pygame.BLEND_ADD)

        # =========================================================================
        # 8. MULTI-LAYER NEON "IAMBKRAM" TYPOGRAPHY & LENS FLARE
        # =========================================================================
        if elapsed >= 1650:
            text_alpha_t = min(1.0, (elapsed - 1650) / 600.0)
            text_alpha = int(text_alpha_t * 255)

            # Anamorphic Laser Lens Flare X sweep (t = 2750 to 4200)
            if 2750 <= elapsed <= 4200:
                sweep_progress = (elapsed - 2750) / 1450.0
                sweep_x = 100 + (sweep_progress * sweep_progress * (3.0 - 2.0 * sweep_progress)) * 600
            else:
                sweep_x = -999.0

            # Render each letter with crisp multi-pass chrome/neon styling
            for i, ch in enumerate(self.letters):
                lx = self.letter_x_centers[i] + ox
                ly = self.text_y + oy

                dist_to_flare = abs(lx - sweep_x)
                if dist_to_flare < 50.0:
                    specular_boost = 1.0 - (dist_to_flare / 50.0)
                else:
                    specular_boost = 0.0

                # --- Layer 1: Soft Ambient Neon Bloom (Delicate halo, not solid box) ---
                bloom_s = self.letter_glow_surfs[i].copy()
                bloom_alpha = min(160, int(text_alpha * (0.28 + 0.45 * specular_boost)))
                bloom_s.set_alpha(bloom_alpha)
                for bx, by in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                    screen.blit(bloom_s, bloom_s.get_rect(center=(lx + bx, ly + by)), special_flags=pygame.BLEND_ADD)

                # --- Layer 2: 3D Dark Elevation Shadow ---
                shadow_s = self.letter_shadow_surfs[i].copy()
                shadow_s.set_alpha(int(text_alpha * 0.85))
                screen.blit(shadow_s, shadow_s.get_rect(center=(lx + 2, ly + 3)))

                # --- Layer 3: 3D Chromatic Aberration Edge Split ---
                if text_alpha > 60:
                    chr_r = self.letter_chroma_r[i].copy()
                    chr_r.set_alpha(int(text_alpha * 0.35))
                    screen.blit(chr_r, chr_r.get_rect(center=(lx - 1, ly)))
                    chr_b = self.letter_chroma_b[i].copy()
                    chr_b.set_alpha(int(text_alpha * 0.35))
                    screen.blit(chr_b, chr_b.get_rect(center=(lx + 1, ly)))

                # --- Layer 4: Razor-Sharp Titanium White Face with Specular Scale ---
                if specular_boost > 0.05:
                    face_s = self.letter_surfs[i].copy()
                    face_s.set_alpha(255)
                    sc = 1.0 + 0.10 * specular_boost
                    if sc > 1.01:
                        face_s = pygame.transform.scale(
                            face_s,
                            (int(face_s.get_width() * sc), int(face_s.get_height() * sc))
                        )
                    screen.blit(face_s, face_s.get_rect(center=(lx, ly - int(2 * specular_boost))))
                else:
                    face_s = self.letter_surfs[i].copy()
                    face_s.set_alpha(text_alpha)
                    screen.blit(face_s, face_s.get_rect(center=(lx, ly)))

            # =========================================================================
            # 9. HOLLYWOOD ANAMORPHIC LASER LENS FLARE
            # =========================================================================
            if 2750 <= elapsed <= 4200 and sweep_x > 0:
                fx = int(sweep_x) + ox
                fy = self.text_y + oy

                flare_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                # A. 45-degree angled laser beam streak
                pygame.draw.line(flare_surf, (255, 255, 255, 160), (fx - 30, fy - 45), (fx + 30, fy + 45), 2)
                pygame.draw.line(flare_surf, (*NEON_CYAN, 70), (fx - 40, fy - 60), (fx + 40, fy + 60), 6)

                # B. Wide horizontal anamorphic flare beam (220px wide)
                pygame.draw.line(flare_surf, (255, 255, 255, 220), (fx - 110, fy), (fx + 110, fy), 2)
                pygame.draw.line(flare_surf, (*NEON_CYAN, 90), (fx - 150, fy), (fx + 150, fy), 4)

                # C. Diamond lens flare core with gold aura
                f_diamond = [(fx, fy - 16), (fx + 10, fy), (fx, fy + 16), (fx - 10, fy)]
                pygame.draw.polygon(flare_surf, (255, 255, 255, 255), f_diamond)
                pygame.draw.circle(flare_surf, (*NEON_GOLD, 160), (fx, fy), 18)

                screen.blit(flare_surf, (0, 0), special_flags=pygame.BLEND_ADD)

                # Trailing sparkle motes
                if random.random() < 0.7:
                    self.particles.append({
                        'x': fx + random.uniform(-10, 10),
                        'y': fy + random.uniform(-18, 18),
                        'vx': random.uniform(-1.5, 1.5),
                        'vy': random.uniform(-2.5, -0.5),
                        'life': 20,
                        'max_life': 20,
                        'col': random.choice([WHITE, NEON_GOLD, NEON_CYAN]),
                        'size': random.uniform(2.0, 3.5),
                        'decay': 0.94
                    })

            # =========================================================================
            # 10. SUBTITLE & SLEEK CYBER STUDIO FRAMING
            # =========================================================================
            if elapsed >= 2100:
                sub_alpha_t = min(1.0, (elapsed - 2100) / 500.0)
                sub_alpha = int(sub_alpha_t * 255)

                # Laser Dividers flanking subtitle with glowing endpoint diamonds
                div_len = int(120 * sub_alpha_t)
                draw_divider(screen, self.cx + ox - 200, self.sub_y + oy, self.cx + ox - 200 + div_len, color=NEON_CYAN, alpha=int(sub_alpha * 0.6))
                draw_divider(screen, self.cx + ox + 200 - div_len, self.sub_y + oy, self.cx + ox + 200, color=NEON_CYAN, alpha=int(sub_alpha * 0.6))

                # Subtitle: [  G A M I N G   S T U D I O S  ]
                sub_text = "[  G A M I N G   S T U D I O S  ]"
                sub_surf = self.font_sub.render(sub_text, True, NEON_GOLD)
                sub_surf.set_alpha(sub_alpha)
                screen.blit(sub_surf, sub_surf.get_rect(center=(self.cx + ox, self.sub_y + oy)))

            # =========================================================================
            # 11. CYBERPUNK HUD CORNER TELEMETRY & AUDIO WAVEFORM
            # =========================================================================
            if elapsed >= 2300:
                hud_alpha_t = min(1.0, (elapsed - 2300) / 500.0)
                hud_alpha = int(hud_alpha_t * 180)

                self._hud_surf.fill((0, 0, 0, 0))
                bracket_col = (*NEON_CYAN, hud_alpha)

                # Corner Brackets
                pygame.draw.lines(self._hud_surf, bracket_col, False, [(30, 50), (30, 30), (50, 30)], 2)
                tl_txt = self.font_hud.render("// SYS_BOOT :: QUANTUM_V9.4 //", True, NEON_CYAN)
                tl_txt.set_alpha(hud_alpha)
                self._hud_surf.blit(tl_txt, (58, 25))

                pygame.draw.lines(self._hud_surf, bracket_col, False, [(WIDTH - 30, 50), (WIDTH - 30, 30), (WIDTH - 50, 30)], 2)
                tr_txt = self.font_hud.render("// GPU CORE :: 100% NOMINAL //", True, NEON_CYAN)
                tr_txt.set_alpha(hud_alpha)
                self._hud_surf.blit(tr_txt, (WIDTH - tr_txt.get_width() - 58, 25))

                pygame.draw.lines(self._hud_surf, bracket_col, False, [(30, HEIGHT - 50), (30, HEIGHT - 30), (50, HEIGHT - 30)], 2)
                bl_txt = self.font_hud.render("// CREATED BY :: IAMBKRAM //", True, NEON_PINK)
                bl_txt.set_alpha(hud_alpha)
                self._hud_surf.blit(bl_txt, (58, HEIGHT - 38))

                pygame.draw.lines(self._hud_surf, bracket_col, False, [(WIDTH - 30, HEIGHT - 50), (WIDTH - 30, HEIGHT - 30), (WIDTH - 50, HEIGHT - 30)], 2)
                br_txt = self.font_hud.render("// CRAZYY ENGINE :: ONLINE //", True, NEON_GREEN)
                br_txt.set_alpha(hud_alpha)
                self._hud_surf.blit(br_txt, (WIDTH - br_txt.get_width() - 58, HEIGHT - 38))

                # Equalizer audio wave frequency bars at bottom center
                eq_cx = WIDTH // 2
                eq_y = HEIGHT - 28
                for b_i in range(-12, 13):
                    b_h = int(3 + 12 * abs(math.sin(t_sec * 8.0 + b_i * 0.4)))
                    b_x = eq_cx + b_i * 6
                    pygame.draw.line(self._hud_surf, (*NEON_CYAN, hud_alpha // 2), (b_x, eq_y - b_h // 2), (b_x, eq_y + b_h // 2), 2)

                screen.blit(self._hud_surf, (0, 0))

        # =========================================================================
        # 12. HYPERSPACE JUMP FLASH & SEAMLESS DISSOLVE
        # =========================================================================
        if elapsed >= 4400:
            fade_progress = (elapsed - 4400) / 800.0
            flash_alpha = min(255, int(fade_progress * 240))
            
            self._dissolve_surf.fill((0, 0, 0, 0))
            self._dissolve_surf.fill((0, 0, 15, flash_alpha))
            screen.blit(self._dissolve_surf, (0, 0))

