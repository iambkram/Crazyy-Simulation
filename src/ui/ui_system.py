"""
Next-Generation Unified UI Engine & Click Protection System for Crazyy Simulation.
Handles:
  - Definitive button click-through prevention across page/state transitions
  - Platform-adaptive rendering (distinct PC and Mobile styling)
  - Pure Python procedural sci-fi audio synthesizer (tap, hover, confirm, buy, warning, fanfare)
  - Momentum-based smooth touch & wheel scroll areas
  - Dynamic button animations (hover glow, press depth, neon glints, scanlines)
"""
import os
import math
import wave
import struct
import pygame
from settings import (
    WIDTH, HEIGHT, NEON_CYAN, NEON_PURPLE, NEON_PINK,
    NEON_BLUE, NEON_GOLD, NEON_GREEN, NEON_ORANGE,
    WHITE, RED, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID,
    NEON_TEAL, NEON_AMBER
)
from assets import (
    FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE,
    FONT_MENU_CARD_MAIN, FONT_MENU_CARD_DESC, FONT_MENU_TELEMETRY,
    draw_text, draw_text_shadow, draw_corner_brackets, draw_badge,
    draw_divider
)

# =========================================================================
# 1. PROCEDURAL SCI-FI AUDIO ENGINE (PURE PYTHON / WAVE)
# =========================================================================

_PROC_SFX_CACHE = {}

def _synthesize_wav_bytes(samples_func, duration=0.15, sample_rate=44100, volume=0.7):
    """Synthesizes PCM audio frames directly into memory as a standard WAV byte stream."""
    import io
    num_samples = int(sample_rate * duration)
    frames = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        val = samples_func(t, duration)
        val = max(-1.0, min(1.0, val))
        sample = int(32767 * volume * val)
        frames += struct.pack('<h', max(-32768, min(32767, sample)))
    
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(frames)
    return bio.getvalue()

def init_procedural_sfx():
    """Generates next-level sci-fi UI and game sound effects if not already initialized."""
    if _PROC_SFX_CACHE:
        return _PROC_SFX_CACHE

    try:
        # 1. Holographic UI Tap (Crisp laser click with transient chirp)
        def tap_fn(t, d):
            f = 1350 * math.exp(-t * 32)
            env = math.exp(-t * 26)
            return (0.75 * math.sin(2 * math.pi * f * t) + 0.25 * math.sin(4 * math.pi * f * t)) * env

        # 2. UI Hover tick (Micro-frequency sci-fi radar tick)
        def hover_fn(t, d):
            f = 2600 + 400 * math.sin(t * 120)
            env = math.exp(-t * 55)
            return math.sin(2 * math.pi * f * t) * env * 0.25

        # 3. Upgrade / Buy Ascend Chime (Cosmic harmonic synth sweep)
        def buy_fn(t, d):
            f1 = 440 + t * 900
            f2 = 660 + t * 1400
            f3 = 880 + t * 1800
            env = math.exp(-t * 7.5)
            return (0.45 * math.sin(2 * math.pi * f1 * t) +
                    0.35 * math.sin(2 * math.pi * f2 * t) +
                    0.20 * math.sin(2 * math.pi * f3 * t)) * env

        # 4. Cancel / Back chirp (Descending soft negative tone)
        def back_fn(t, d):
            f = 650 * math.exp(-t * 10)
            env = math.exp(-t * 18)
            return math.sin(2 * math.pi * f * t) * env * 0.5

        # 5. Victory Fanfare Chime (Heroic triad chord)
        def fanfare_fn(t, d):
            chord = [523.25, 659.25, 783.99, 1046.50]  # C Major chord
            s = 0.0
            for idx, c_freq in enumerate(chord):
                offset_t = t - idx * 0.08
                if offset_t > 0:
                    env = math.exp(-offset_t * 5.0)
                    s += 0.25 * math.sin(2 * math.pi * c_freq * offset_t) * env
            return s

        # 6. Boss Warning Klaxon (Dual-tone menacing pulse)
        # 6. Boss Warning Klaxon (Dual-tone menacing pulse)
        def boss_warn_fn(t, d):
            f = 380 if (int(t * 10) % 2 == 0) else 440
            f += 30 * math.sin(2 * math.pi * 8 * t)
            env = 0.5 + 0.5 * math.sin(2 * math.pi * 4 * t)
            return math.sin(2 * math.pi * f * t) * env * 0.65

        # 7. Next-Gen Plasma Laser Blast (Punchy transient chirp)
        def laser_fn(t, d):
            f = 240 + 1650 * math.exp(-t * 32)
            env = math.exp(-t * 22)
            return (0.7 * math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t)) * env

        # 8. Forcefield Shield Shimmer (Resonant magnetic barrier)
        def shield_fn(t, d):
            f = 340 + 50 * math.sin(2 * math.pi * 16 * t)
            env = math.sin(math.pi * min(1.0, t / d))
            return (0.65 * math.sin(2 * math.pi * f * t) + 0.35 * math.sin(2 * math.pi * (f * 1.5) * t)) * env

        # 9. Starship Quantum Revive Resonator (Ascending multi-harmonic surge)
        def revive_fn(t, d):
            f = 260 + t * 950
            env = math.exp(-t * 5.0)
            return (0.5 * math.sin(2 * math.pi * f * t) +
                    0.3 * math.sin(2 * math.pi * (f * 1.5) * t) +
                    0.2 * math.sin(2 * math.pi * (f * 2.0) * t)) * env

        # Load into pygame mixer sounds
        sounds_def = {
            'ui_tap':        (tap_fn, 0.14, 0.65),
            'ui_hover':      (hover_fn, 0.07, 0.25),
            'ui_buy':        (buy_fn, 0.40, 0.70),
            'ui_back':       (back_fn, 0.15, 0.50),
            'ui_fanfare':    (fanfare_fn, 0.65, 0.75),
            'ui_warn':       (boss_warn_fn, 0.50, 0.70),
            'ui_laser_fire': (laser_fn, 0.18, 0.60),
            'ui_shield':     (shield_fn, 0.45, 0.65),
            'ui_revive':     (revive_fn, 0.55, 0.75),
        }

        import io
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "game_assets", "sfx_procedural")
        os.makedirs(out_dir, exist_ok=True)
        for name, (fn, dur, vol) in sounds_def.items():
            wav_bytes = _synthesize_wav_bytes(fn, duration=dur, volume=vol)
            _PROC_SFX_CACHE[name] = pygame.mixer.Sound(io.BytesIO(wav_bytes))
            try:
                disk_path = os.path.join(out_dir, f"{name}.wav")
                if not os.path.exists(disk_path):
                    with open(disk_path, "wb") as df:
                        df.write(wav_bytes)
            except Exception:
                pass

    except Exception as e:
        print("[UIManager] Procedural SFX initialization notice:", e)

    return _PROC_SFX_CACHE

def play_sfx(name):
    """Play a procedural sound effect safely if available."""
    snd = _PROC_SFX_CACHE.get(name)
    if snd:
        try:
            snd.play()
        except Exception:
            pass


# =========================================================================
# 2. DEFINITIVE CLICK-THROUGH PREVENTION & POINTER MANAGER
# =========================================================================

class UIManager:
    """
    Centralized UI Controller that guarantees:
      1. Pointer UP only activates a button if Pointer DOWN started inside that same button.
      2. When any state/page transition occurs, active button targets are cleared and an
         input debounce cooldown is enforced.
      3. If a finger/mouse is held down across page transitions, it is flagged as 'ignore_until_release'
         so that releasing on the new page can NEVER trigger an accidental click!
      4. Smooth inertial momentum scrolling on mobile and desktop.
    """
    def __init__(self):
        self.pointer_pos = (0, 0)
        self.pointer_down = False
        self.pointer_just_down = False
        self.pointer_just_up = False
        self.pointer_down_pos = (0, 0)
        
        self.active_button_id = None
        self.hover_button_id = None
        self.last_hover_button_id = None
        
        self.transition_cooldown = 0
        self.ignore_until_release = False
        self.current_state = 0
        self.prev_state = 0
        
        self.pulse_t = 0.0
        self.scroll_offsets = {}
        self.scroll_velocities = {}
        self.scroll_drag_states = {}
        
        # Pre-cache button surfaces for high-performance blits
        self._btn_cache = {}
        
        # Initialize sound suite
        init_procedural_sfx()

    def update_frame(self, events, dt=1.0):
        """
        Must be called at the very beginning of each frame's main loop.
        Extracts pointer events and manages cooldown states.
        """
        self.pulse_t += 0.05 * dt
        self.pointer_just_down = False
        self.pointer_just_up = False
        self.last_hover_button_id = self.hover_button_id
        self.hover_button_id = None

        if self.transition_cooldown > 0:
            self.transition_cooldown -= 1
            if self.pointer_down:
                self.ignore_until_release = True

        mouse_pos = pygame.mouse.get_pos()
        self.pointer_pos = mouse_pos

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.pointer_down = True
                self.pointer_down_pos = event.pos
                if not self.ignore_until_release and self.transition_cooldown <= 0:
                    self.pointer_just_down = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.pointer_down = False
                if not self.ignore_until_release and self.transition_cooldown <= 0:
                    self.pointer_just_up = True
                # Reset ignore flag once the pointer has cleanly been lifted
                self.ignore_until_release = False

            elif event.type == pygame.MOUSEMOTION:
                self.pointer_pos = event.pos

        # Update smooth momentum scrolling
        for area_id in list(self.scroll_velocities.keys()):
            vel = self.scroll_velocities[area_id]
            if abs(vel) > 0.1:
                self.scroll_offsets[area_id] = self.scroll_offsets.get(area_id, 0.0) + vel * dt
                self.scroll_velocities[area_id] *= math.pow(0.88, dt)
            else:
                self.scroll_velocities[area_id] = 0.0

    def notify_state_change(self, new_state):
        """
        Call whenever the game switches state/page.
        Instantly clears any pending button activations and arms click-through guards.
        """
        if new_state != self.current_state:
            self.prev_state = self.current_state
            self.current_state = new_state
            self.active_button_id = None
            self.pointer_just_down = False
            self.pointer_just_up = False
            self.transition_cooldown = 14  # ~230ms transition guard
            is_down = self.pointer_down
            try:
                if pygame.display.get_init():
                    is_down = is_down or pygame.mouse.get_pressed()[0]
            except Exception:
                pass
            if is_down:
                self.ignore_until_release = True
                self.pointer_down = True

    def notify_modal_change(self):
        """
        Call whenever an in-state modal dialog (revive confirm, store detail, blackhole alert) opens or closes.
        Guarantees zero button click-through between sub-pages without altering the global state ID.
        """
        self.active_button_id = None
        self.pointer_just_down = False
        self.pointer_just_up = False
        self.transition_cooldown = 12
        is_down = self.pointer_down
        try:
            if pygame.display.get_init():
                is_down = is_down or pygame.mouse.get_pressed()[0]
        except Exception:
            pass
        if is_down:
            self.ignore_until_release = True
            self.pointer_down = True

    def reset_input_state(self):
        """Reset all pointer and input states."""
        self.pointer_down = False
        self.pointer_just_down = False
        self.pointer_just_up = False
        self.active_button_id = None
        self.hover_button_id = None
        self.last_hover_button_id = None
        self.transition_cooldown = 0
        self.ignore_until_release = False

    def is_pointer_available(self):
        """Returns True if the pointer is free to click without cooldown or suppression."""
        return not self.ignore_until_release and self.transition_cooldown <= 0

    # =========================================================================
    # 3. INTERACTIVE BUTTON COMPONENT (PC & MOBILE ADAPTIVE)
    # =========================================================================

    def button(self, screen, btn_id, rect, label, is_mobile=False,
               accent=NEON_CYAN, base_color=None, text_color=WHITE,
               font=None, icon=None, hotkey_text=None, enabled=True,
               border_radius=None, height_pad=0):
        """
        Stateful interactive button with full click-through immunity.
        Returns: (clicked: bool, is_hovered: bool, is_pressed: bool)
        """
        if font is None:
            font = FONT_UI

        if border_radius is None:
            border_radius = 24 if is_mobile else 12

        if base_color is None:
            base_color = (18, 26, 46)

        is_hover = rect.collidepoint(self.pointer_pos) and enabled

        if is_hover:
            self.hover_button_id = btn_id
            if self.last_hover_button_id != btn_id and not is_mobile:
                play_sfx('ui_hover')

        # Check button press
        if self.pointer_just_down and is_hover and self.is_pointer_available():
            self.active_button_id = btn_id

        is_pressed = (self.active_button_id == btn_id and self.pointer_down and is_hover)

        just_clicked = False
        if (self.pointer_just_up and self.active_button_id == btn_id and
                is_hover and self.is_pointer_available()):
            just_clicked = True
            self.active_button_id = None
            play_sfx('ui_tap')

        # If pointer was released outside button, cancel active state
        if self.pointer_just_up and self.active_button_id == btn_id:
            self.active_button_id = None

        # --- RENDERING ---
        self._render_adaptive_button(
            screen, rect, label, is_mobile, is_hover, is_pressed,
            enabled, accent, base_color, text_color, font, icon,
            hotkey_text, border_radius
        )

        return just_clicked, is_hover, is_pressed

    def _render_adaptive_button(self, screen, rect, label, is_mobile, is_hover,
                                is_pressed, enabled, accent, base_color, text_color,
                                font, icon, hotkey_text, border_radius):
        """Renders either desktop tactical cyberpunk or ergonomic mobile tactile styling."""
        pulse = (math.sin(self.pulse_t * 3.5) + 1.0) * 0.5

        # Pressed displacement for tactile feedback
        draw_rect = rect.copy()
        if is_pressed:
            draw_rect.y += 2

        # 1. Outer Neon Glow (Intense on hover, pulsing on mobile)
        if enabled and (is_hover or (is_mobile and not is_pressed)):
            glow_pad = 6 if is_mobile else 8
            glow_surf = pygame.Surface((draw_rect.width + glow_pad * 2, draw_rect.height + glow_pad * 2), pygame.SRCALPHA)
            glow_alpha = int(70 + 60 * pulse) if is_hover else int(25 + 15 * pulse)
            pygame.draw.rect(
                glow_surf, (*accent[:3], glow_alpha),
                glow_surf.get_rect(),
                border_radius=border_radius + (4 if is_mobile else 6)
            )
            screen.blit(glow_surf, (draw_rect.x - glow_pad, draw_rect.y - glow_pad))

        # 2. Main Button Body
        btn_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        bg_alpha = 245 if is_hover else (210 if enabled else 140)
        btn_bg = (*base_color[:3], bg_alpha) if not is_pressed else (min(255, base_color[0] + 30), min(255, base_color[1] + 30), min(255, base_color[2] + 40), 250)
        pygame.draw.rect(btn_surf, btn_bg, btn_surf.get_rect(), border_radius=border_radius)

        # Subtle top sheen
        sheen_h = max(2, draw_rect.height // 3)
        sheen_surf = pygame.Surface((draw_rect.width, sheen_h), pygame.SRCALPHA)
        sheen_a = 45 if is_hover else 25
        pygame.draw.rect(sheen_surf, (255, 255, 255, sheen_a), sheen_surf.get_rect(),
                         border_top_left_radius=border_radius, border_top_right_radius=border_radius)
        btn_surf.blit(sheen_surf, (0, 0))

        # 3. Dynamic Border
        border_w = 3 if is_pressed else (2 if is_hover else 1)
        border_col = (*accent[:3], 255 if is_hover else 140) if enabled else (*MID_GRAY[:3], 100)
        pygame.draw.rect(btn_surf, border_col, btn_surf.get_rect(), width=border_w, border_radius=border_radius)

        screen.blit(btn_surf, draw_rect.topleft)

        # 4. PC Tactical Corner Brackets
        if not is_mobile and enabled and is_hover:
            draw_corner_brackets(screen, draw_rect, accent, size=10, width=2)

        # 5. Icon & Typography
        content_cx = draw_rect.centerx
        content_cy = draw_rect.centery

        # Render Icon if provided
        if icon:
            icon_surf = font.render(str(icon), True, accent if enabled else MID_GRAY)
            screen.blit(icon_surf, icon_surf.get_rect(center=(draw_rect.x + 28, content_cy)))
            content_cx += 12

        # Text Label with Drop Shadow
        lbl_col = text_color if enabled else MID_GRAY
        if is_hover and enabled:
            lbl_col = WHITE
        draw_text_shadow(label, font, lbl_col, content_cx, content_cy,
                         shadow_color=(0, 0, 0), offset=1, center=True)

        # 6. PC Hotkey Badge on right edge (e.g. [ESC], [ENTER], [1])
        if not is_mobile and hotkey_text and enabled:
            hk_rect = pygame.Rect(draw_rect.right - 54, content_cy - 9, 44, 18)
            pygame.draw.rect(screen, (10, 14, 25), hk_rect, border_radius=4)
            pygame.draw.rect(screen, (*accent[:3], 160 if is_hover else 90), hk_rect, width=1, border_radius=4)
            draw_text(hotkey_text, FONT_TINY, accent if is_hover else LIGHT_GRAY, hk_rect.centerx, hk_rect.centery)


# Global UIManager Singleton instance
ui_manager = UIManager()
