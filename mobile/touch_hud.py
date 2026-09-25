"""
Next-Gen Mobile Touch HUD & Smooth Motion Controller for Crazyy Simulation.
Provides:
  - Multi-touch finger isolation (steering vs fire)
  - Silky-smooth relative touch sliding with exponential smoothing & deadband damping
  - Holographic touch reticle & ripple under dragging finger
  - Tactile plasma Fire Button with depression physics & pulse ring
  - Quick thumb-accessible Auto-Fire toggle switch
  - Non-overlapping safe-zone Pause button
"""
import pygame
import math
try:
    from settings import WIDTH, HEIGHT, NEON_CYAN, NEON_GOLD, WHITE, NEON_GREEN, NEON_PINK, MID_GRAY
except ImportError:
    from src.settings import WIDTH, HEIGHT, NEON_CYAN, NEON_GOLD, WHITE, NEON_GREEN, NEON_PINK, MID_GRAY


class MobileTouchEngine:
    """Manages multi-touch steering and firing with buttery-smooth interpolation."""
    def __init__(self):
        self.steering_active = False
        self.prev_touch_pos = (0.0, 0.0)
        self.target_ship_pos = [WIDTH // 2, HEIGHT - 100]
        self.smoothed_ship_pos = [float(WIDTH // 2), float(HEIGHT - 100)]
        self.steering_finger_id = None
        self.touch_ripples = []
        self.smooth_factor = 0.72  # Instant response, zero jitter
        
    def reset(self, initial_x, initial_y):
        self.steering_active = False
        self.target_ship_pos = [float(initial_x), float(initial_y)]
        self.smoothed_ship_pos = [float(initial_x), float(initial_y)]
        self.prev_touch_pos = (float(initial_x), float(initial_y))
        self.steering_finger_id = None
        self.touch_ripples.clear()

    def on_touch_down(self, pos, finger_id=None, current_ship_x=0, current_ship_y=0):
        """Called when a touch down occurs on the playfield."""
        if hits_hud(pos):
            return False
        # If already steering with an active physical finger, ignore synthetic mouse events
        if self.steering_active and self.steering_finger_id is not None and finger_id == 'mouse':
            return False

        self.steering_active = True
        self.steering_finger_id = finger_id
        self.prev_touch_pos = (float(pos[0]), float(pos[1]))
        self.target_ship_pos = [float(current_ship_x), float(current_ship_y)]
        self.smoothed_ship_pos = [float(current_ship_x), float(current_ship_y)]
        # Add visual touch ripple
        self.touch_ripples.append({'x': pos[0], 'y': pos[1], 'r': 8, 'max_r': 38, 'alpha': 220})
        return True

    def on_touch_motion(self, pos, finger_id=None):
        """Called during touch dragging with zero deadzone lag."""
        if not self.steering_active:
            return
        if finger_id is not None and self.steering_finger_id is not None and finger_id != self.steering_finger_id:
            return

        dx = pos[0] - self.prev_touch_pos[0]
        dy = pos[1] - self.prev_touch_pos[1]
        self.prev_touch_pos = (float(pos[0]), float(pos[1]))

        # Incremental target update responds immediately even when turning around against boundaries
        self.target_ship_pos[0] += dx
        self.target_ship_pos[1] += dy

    def on_touch_up(self, finger_id=None):
        """Called on touch release."""
        if finger_id is None or self.steering_finger_id is None or finger_id == self.steering_finger_id:
            self.steering_active = False
            self.steering_finger_id = None

    def update_smooth_ship_pos(self, current_rect, min_x=0, max_x=WIDTH-60, min_y=60, max_y=HEIGHT-60):
        """Applies smooth exponential moving average to glide ship like butter."""
        if self.steering_active:
            # Clamp target to safe bounds
            self.target_ship_pos[0] = max(min_x, min(max_x, self.target_ship_pos[0]))
            self.target_ship_pos[1] = max(min_y, min(max_y, self.target_ship_pos[1]))

            # Smooth exponential lerp
            self.smoothed_ship_pos[0] += (self.target_ship_pos[0] - self.smoothed_ship_pos[0]) * self.smooth_factor
            self.smoothed_ship_pos[1] += (self.target_ship_pos[1] - self.smoothed_ship_pos[1]) * self.smooth_factor
            if abs(self.target_ship_pos[0] - self.smoothed_ship_pos[0]) < 0.2:
                self.smoothed_ship_pos[0] = self.target_ship_pos[0]
            if abs(self.target_ship_pos[1] - self.smoothed_ship_pos[1]) < 0.2:
                self.smoothed_ship_pos[1] = self.target_ship_pos[1]
            current_rect.x = int(round(self.smoothed_ship_pos[0]))
            current_rect.y = int(round(self.smoothed_ship_pos[1]))
        else:
            self.smoothed_ship_pos[0] = float(current_rect.x)
            self.smoothed_ship_pos[1] = float(current_rect.y)
            self.target_ship_pos = [float(current_rect.x), float(current_rect.y)]

    def draw_touch_feedback(self, screen, current_pos=None):
        """Draws glowing holographic touch ripples under player's dragging finger."""
        for rip in self.touch_ripples[:]:
            rip['r'] += 2.5
            rip['alpha'] -= 14
            if rip['alpha'] <= 0 or rip['r'] >= rip['max_r']:
                self.touch_ripples.remove(rip)
                continue
            r_surf = pygame.Surface((rip['r'] * 2 + 4, rip['r'] * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(r_surf, (*NEON_CYAN[:3], max(0, int(rip['alpha']))),
                               (int(rip['r'] + 2), int(rip['r'] + 2)), int(rip['r']), 2)
            screen.blit(r_surf, (rip['x'] - rip['r'] - 2, rip['y'] - rip['r'] - 2))


touch_engine = MobileTouchEngine()


def pause_rect():
    """Top-right safe zone pause button with ample padding (never overlaps health bar!)."""
    return pygame.Rect(WIDTH - 52, 14, 40, 40)


def fire_rect():
    """Generous 96x96 thumb target for rapid weapons fire."""
    return pygame.Rect(WIDTH - 112, HEIGHT - 124, 96, 96)


def auto_toggle_rect():
    """One-thumb quick toggle for Auto-Fire."""
    return pygame.Rect(WIDTH - 186, HEIGHT - 84, 64, 44)


def hits_hud(pos):
    """Returns True if coordinate collides with any mobile on-screen control."""
    return (pause_rect().collidepoint(pos) or
            fire_rect().collidepoint(pos) or
            auto_toggle_rect().collidepoint(pos))


def draw_fire_button(screen, held, font, pulse_t=0.0):
    """Draw a tactile plasma fire button with glowing halo and depth depression."""
    rect = fire_rect()
    cx, cy = rect.center
    outer_r = rect.width // 2

    # Depress downward by 2px on hold for tactile sensation
    if held:
        cy += 2

    # Pulsing outer glow ring
    glow_alpha = int(90 + 70 * math.sin(pulse_t * 5)) if not held else 200
    glow_r = outer_r + (6 if held else 4)
    glow_surf = pygame.Surface((glow_r * 2 + 8, glow_r * 2 + 8), pygame.SRCALPHA)
    glow_center = (glow_r + 4, glow_r + 4)
    glow_color = NEON_GOLD if held else NEON_CYAN
    pygame.draw.circle(glow_surf, (*glow_color, glow_alpha), glow_center, glow_r, 4)
    pygame.draw.circle(glow_surf, (*glow_color, glow_alpha // 3), glow_center, glow_r + 4, 2)
    screen.blit(glow_surf, (cx - glow_r - 4, cy - glow_r - 4))

    # Main Button Glass Body
    btn_surf = pygame.Surface((outer_r * 2 + 4, outer_r * 2 + 4), pygame.SRCALPHA)
    btn_center = (outer_r + 2, outer_r + 2)
    fill_alpha = 180 if held else 120
    fill_color = (60, 120, 70, fill_alpha) if held else (15, 30, 50, fill_alpha)
    pygame.draw.circle(btn_surf, fill_color, btn_center, outer_r)
    screen.blit(btn_surf, (cx - outer_r - 2, cy - outer_r - 2))

    # Crisp neon border
    border_color = NEON_GOLD if held else NEON_CYAN
    pygame.draw.circle(screen, border_color, (cx, cy), outer_r, 3 if held else 2)

    # Inner tech ring
    inner_r = outer_r - 8
    pygame.draw.circle(screen, (*border_color, 160 if held else 80), (cx, cy), inner_r, 1)

    # Label with drop shadow
    shadow = font.render("FIRE", True, (0, 0, 0))
    label = font.render("FIRE", True, WHITE)
    screen.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
    screen.blit(label, label.get_rect(center=(cx, cy)))

    return rect


def draw_auto_toggle_button(screen, auto_fire_enabled, font, is_hover=False):
    """Draw a tactile AUTO fire pill switch right beside the Fire Button."""
    rect = auto_toggle_rect()
    bg_col = (15, 50, 25) if auto_fire_enabled else (25, 30, 42)
    border_col = NEON_GREEN if auto_fire_enabled else (60, 70, 90)

    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, (*bg_col, 220), btn_surf.get_rect(), border_radius=12)
    pygame.draw.rect(btn_surf, border_col, btn_surf.get_rect(), width=2, border_radius=12)
    screen.blit(btn_surf, rect.topleft)

    tag_col = NEON_GREEN if auto_fire_enabled else MID_GRAY
    status_txt = "AUTO ON" if auto_fire_enabled else "AUTO"
    lbl = font.render(status_txt, True, tag_col)
    screen.blit(lbl, lbl.get_rect(center=rect.center))
    return rect
