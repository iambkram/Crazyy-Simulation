import pygame
import math
import cloud_sync
from assets import (draw_text, draw_text_shadow, draw_neon_text, draw_divider, draw_badge,
                    draw_plasma_button, draw_glowing_button, draw_holographic_panel,
                    FONT_TITLE, FONT_MSG, FONT_MODAL_TITLE, FONT_MODAL_SUB, FONT_UI,
                    FONT_SMALL, FONT_TINY, FONT_MONO, FONT_MONO_SM,
                    FONT_AUTH_TITLE, FONT_AUTH_SUB, FONT_AUTH_INPUT,
                    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_BLUE, NEON_PINK, NEON_ORANGE,
                    RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, PLASMA_CORE)
from vfx import draw_neon_auth_bg
from settings import WIDTH, HEIGHT


class AuthUI:
    """
    Next-Gen Cyberpunk & Web-Style Authentication Suite.
    Renders multi-layer frosted acrylic cards, authentic vector Google emblems,
    neon segmented tabs, floating inputs with active focus bloom, and clean vector icons.
    """
    def __init__(self):
        self.setup_username = ""
        self.setup_password = ""
        self.setup_active_field = "username"
        self.login_error_msg = ""
        self.setup_google_info = None
        self.show_password = False
        self.active_tab = "login"  # 'login' or 'signup'
        self._pulse = 0.0
        self._keyboard_active = False

    def reset_form(self):
        self.setup_username = ""
        self.setup_password = ""
        self.setup_active_field = "username"
        self.login_error_msg = ""
        self.show_password = False
        if self._keyboard_active:
            try:
                if hasattr(pygame.key, "stop_text_input"):
                    pygame.key.stop_text_input()
            except Exception:
                pass
            self._keyboard_active = False

    def _ensure_keyboard(self, active=True):
        """Trigger native on-screen virtual keyboard on Android/touch devices."""
        try:
            if active and not self._keyboard_active:
                if hasattr(pygame.key, "start_text_input"):
                    pygame.key.start_text_input()
                self._keyboard_active = True
            elif not active and self._keyboard_active:
                if hasattr(pygame.key, "stop_text_input"):
                    pygame.key.stop_text_input()
                self._keyboard_active = False
        except Exception:
            pass

    def handle_input(self, key_unicode, key_backspace, key_tab):
        if key_tab:
            self.setup_active_field = "password" if self.setup_active_field == "username" else "username"
            self._ensure_keyboard(True)
        elif key_backspace:
            if self.setup_active_field == "username":
                self.setup_username = self.setup_username[:-1]
            else:
                self.setup_password = self.setup_password[:-1]
        elif key_unicode:
            if self.setup_active_field == "username" and len(self.setup_username) < 16:
                self.setup_username += key_unicode
            elif self.setup_active_field == "password" and len(self.setup_password) < 16:
                self.setup_password += key_unicode

    # =========================================================================
    # PROCEDURAL VECTOR & GLASS COMPONENT HELPERS
    # =========================================================================

    def _draw_cyberpunk_card(self, screen, rect, accent_color=NEON_CYAN, pulse_t=0.0):
        """Draws a multi-layered neon glassmorphic card with glowing borders."""
        cx, cy, w, h = rect.x, rect.y, rect.width, rect.height

        # 1. Outer ambient drop shadow
        shadow_surf = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 140), pygame.Rect(12, 12, w, h), border_radius=20)
        screen.blit(shadow_surf, (cx - 12, cy - 12))

        # 2. Main frosted glass background
        card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        card_surf.fill((10, 14, 26, 238))

        # Cyberpunk horizontal scanline grid
        for sy in range(0, h, 6):
            pygame.draw.line(card_surf, (0, 220, 255, 6), (0, sy), (w, sy), 1)

        # 3. Outer Neon Pulsing Glow Border
        glow_a = int(120 + 50 * math.sin(pulse_t * 3.5))
        pygame.draw.rect(card_surf, (*accent_color[:3], glow_a), card_surf.get_rect(), width=2, border_radius=18)

        # 4. Top-edge highlight bar
        pygame.draw.line(card_surf, (*accent_color[:3], 240), (20, 0), (w - 20, 0), 3)

        # 5. Corner tech brackets
        blen = 16
        for bx, by in [(0, 0), (w, 0), (0, h), (w, h)]:
            dx = blen if bx == 0 else -blen
            dy = blen if by == 0 else -blen
            pygame.draw.line(card_surf, (*accent_color[:3], 255), (bx, by), (bx + dx, by), 2)
            pygame.draw.line(card_surf, (*accent_color[:3], 255), (bx, by), (bx, by + dy), 2)

        screen.blit(card_surf, (cx, cy))

    def _draw_google_g_logo(self, screen, cx, cy, radius=14):
        """Renders authentic Google 'G' quad-color vector emblem."""
        BLUE   = (66, 133, 244)
        RED_C  = (234, 67, 53)
        YELLOW = (251, 188, 5)
        GREEN  = (52, 168, 83)

        surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        center = (radius + 4, radius + 4)
        r_rect = pygame.Rect(4, 4, radius * 2, radius * 2)
        w = max(3, radius // 3)

        # Arc segments
        pygame.draw.arc(surf, BLUE, r_rect, -math.pi / 4, math.pi / 4, width=w)
        pygame.draw.arc(surf, RED_C, r_rect, math.pi / 4, 3 * math.pi / 4, width=w)
        pygame.draw.arc(surf, YELLOW, r_rect, 3 * math.pi / 4, 5 * math.pi / 4, width=w)
        pygame.draw.arc(surf, GREEN, r_rect, 5 * math.pi / 4, 7 * math.pi / 4, width=w)

        # Horizontal bar
        pygame.draw.rect(surf, BLUE, pygame.Rect(center[0] - 1, center[1] - w // 2, radius + 1, w), border_radius=1)
        screen.blit(surf, (cx - radius - 4, cy - radius - 4))

    def _draw_vector_rocket(self, screen, cx, cy, color=NEON_GOLD):
        """Draws a crisp geometric rocket icon."""
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        pts = [(14, 3), (22, 18), (17, 24), (11, 24), (6, 18)]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, WHITE, [(14, 7), (18, 17), (10, 17)])
        # Thruster flame
        pygame.draw.polygon(surf, NEON_ORANGE, [(14, 27), (17, 24), (11, 24)])
        screen.blit(surf, (cx - 14, cy - 14))

    def _draw_vector_eye(self, screen, cx, cy, is_open=True, color=NEON_CYAN):
        """Draws a clean vector eye icon for password reveal."""
        surf = pygame.Surface((28, 22), pygame.SRCALPHA)
        # Eye contour
        r_rect = pygame.Rect(2, 2, 24, 18)
        pygame.draw.ellipse(surf, color, r_rect, width=2)
        if is_open:
            pygame.draw.circle(surf, color, (14, 11), 4)
            pygame.draw.circle(surf, WHITE, (13, 10), 1)
        else:
            pygame.draw.line(surf, RED, (4, 18), (24, 4), 2)
        screen.blit(surf, (cx - 14, cy - 11))

    def _draw_modern_input(self, screen, rect, label, value, is_active, is_password, show_pass, now, char_limit=16):
        """Draws a high-visibility neon input box with floating label."""
        # 1. Background fill
        bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg_col = (18, 24, 42, 245) if not is_active else (24, 34, 58, 255)
        pygame.draw.rect(bg_surf, bg_col, bg_surf.get_rect(), border_radius=12)
        screen.blit(bg_surf, rect.topleft)

        # 2. Focus Glow Ring
        if is_active:
            glow_surf = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*NEON_CYAN[:3], 60), glow_surf.get_rect(), border_radius=15)
            pygame.draw.rect(glow_surf, (*NEON_CYAN[:3], 120), glow_surf.get_rect().inflate(-4, -4), border_radius=13)
            screen.blit(glow_surf, (rect.x - 4, rect.y - 4))

        # 3. Border
        border_col = NEON_CYAN if is_active else (55, 70, 98)
        border_w = 2 if is_active else 1
        pygame.draw.rect(screen, border_col, rect, width=border_w, border_radius=12)

        # 4. Floating Label (Always crisp, above value)
        lbl_col = NEON_CYAN if is_active else (130, 155, 190)
        lbl_surf = FONT_AUTH_SUB.render(label.upper(), True, lbl_col)
        screen.blit(lbl_surf, (rect.x + 14, rect.y + 7))

        # 5. Value Text
        val_str = ("*" * len(value)) if (is_password and not show_pass) else value
        val_surf = FONT_AUTH_INPUT.render(val_str, True, WHITE)
        screen.blit(val_surf, (rect.x + 14, rect.y + 26))

        # Cursor
        if is_active and (now // 450) % 2 == 0:
            cx = rect.x + 14 + val_surf.get_width() + 2
            cy = rect.y + 25
            pygame.draw.line(screen, NEON_CYAN, (cx, cy), (cx, cy + 20), 2)

        # Character limit tag
        cnt_surf = FONT_AUTH_SUB.render(f"{len(value)}/{char_limit}", True, (70, 85, 115))
        screen.blit(cnt_surf, (rect.right - cnt_surf.get_width() - 12, rect.y + 7))

    def _draw_toast_alert(self, screen, message, cx, cy, is_error=True):
        """Draws a responsive, web-style toast notification pill."""
        if not message:
            return
        tw, th = FONT_AUTH_SUB.size(message)
        pw, ph = max(340, tw + 44), 32
        toast_rect = pygame.Rect(cx - pw // 2, cy - ph // 2, pw, ph)

        toast_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg = (60, 15, 25, 235) if is_error else (15, 50, 30, 235)
        border = RED if is_error else NEON_GREEN
        pygame.draw.rect(toast_surf, bg, toast_surf.get_rect(), border_radius=16)
        pygame.draw.rect(toast_surf, border, toast_surf.get_rect(), width=1, border_radius=16)
        screen.blit(toast_surf, toast_rect.topleft)

        icon_txt = "[!]" if is_error else "[v]"
        draw_text(icon_txt, FONT_AUTH_SUB, border, toast_rect.x + 18, toast_rect.centery)
        draw_text(message, FONT_AUTH_SUB, WHITE, toast_rect.centerx + 8, toast_rect.centery)

    # =========================================================================
    # 1. METHOD SELECTION SCREEN (STATE -3)
    # =========================================================================

    def render_method_select(self, screen, mx, my, m_c, key_enter, key_escape, tap_snd, menu_bg, ui_pulse_t, now):
        """State -3: Cyberpunk Web-Style Method Selection Screen"""
        draw_neon_auth_bg(screen, now)

        card_rect = pygame.Rect(140, 50, 520, 500)
        self._draw_cyberpunk_card(screen, card_rect, accent_color=NEON_CYAN, pulse_t=ui_pulse_t)

        # Header Status Badge
        draw_badge(screen, "// PILOT AUTHENTICATION GATEWAY //", FONT_AUTH_SUB, 400, 82,
                   bg_color=(10, 25, 45), text_color=NEON_CYAN, border_color=NEON_CYAN)

        # Title & Subtitle
        draw_text_shadow("CRAZYY SIMULATION", FONT_MSG, NEON_CYAN, 400, 122, shadow_color=(0, 60, 100), offset=2)
        draw_text("SELECT YOUR SIGN-IN METHOD", FONT_AUTH_SUB, (130, 160, 205), 400, 162)
        draw_divider(screen, 175, 178, 625, NEON_CYAN, alpha=50)

        # ── Primary Option: Continue with Google ──
        btn_google = pygame.Rect(175, 200, 450, 82)
        is_h_g = btn_google.collidepoint(mx, my)

        g_surf = pygame.Surface((btn_google.width, btn_google.height), pygame.SRCALPHA)
        g_bg = (18, 26, 46, 240) if not is_h_g else (26, 38, 68, 255)
        pygame.draw.rect(g_surf, g_bg, g_surf.get_rect(), border_radius=16)
        g_border = (66, 133, 244) if is_h_g else (50, 70, 100)
        pygame.draw.rect(g_surf, g_border, g_surf.get_rect(), width=2 if is_h_g else 1, border_radius=16)
        screen.blit(g_surf, btn_google.topleft)

        # Google Vector Icon
        self._draw_google_g_logo(screen, btn_google.x + 36, btn_google.centery, radius=15)

        # Google Text (Explicit Non-Overlapping Layout)
        t_g1 = FONT_AUTH_TITLE.render("Continue with Google", True, WHITE)
        t_g2 = FONT_AUTH_SUB.render("Instant Cloud Sync  ·  Cross-Platform Save", True, (130, 160, 205))
        screen.blit(t_g1, (btn_google.x + 68, btn_google.y + 16))
        screen.blit(t_g2, (btn_google.x + 68, btn_google.y + 48))

        # ── Secondary Option: Play as Guest Pilot ──
        btn_guest = pygame.Rect(175, 302, 450, 82)
        is_h_guest = btn_guest.collidepoint(mx, my)

        gst_surf = pygame.Surface((btn_guest.width, btn_guest.height), pygame.SRCALPHA)
        gst_bg = (24, 22, 34, 240) if not is_h_guest else (38, 32, 50, 255)
        pygame.draw.rect(gst_surf, gst_bg, gst_surf.get_rect(), border_radius=16)
        gst_border = NEON_GOLD if is_h_guest else (70, 65, 80)
        pygame.draw.rect(gst_surf, gst_border, gst_surf.get_rect(), width=2 if is_h_guest else 1, border_radius=16)
        screen.blit(gst_surf, btn_guest.topleft)

        # Rocket Vector Icon
        self._draw_vector_rocket(screen, btn_guest.x + 36, btn_guest.centery, color=NEON_GOLD)

        # Guest Text (Explicit Non-Overlapping Layout)
        t_gst1 = FONT_AUTH_TITLE.render("Play as Guest Pilot", True, WHITE)
        t_gst2 = FONT_AUTH_SUB.render("Instant Offline Play  ·  Link Account Later", True, (190, 170, 130))
        screen.blit(t_gst1, (btn_guest.x + 68, btn_guest.y + 16))
        screen.blit(t_gst2, (btn_guest.x + 68, btn_guest.y + 48))

        # ── Auth Status Messages / Toast ──
        if cloud_sync.auth_status == "WAITING":
            self._draw_toast_alert(screen, "Opening browser for Google Authentication...", 400, 420, is_error=False)
        elif cloud_sync.auth_status == "SUCCESS":
            self.setup_google_info = cloud_sync.auth_result_info
            cloud_sync.auth_status = None
            if self.setup_google_info and self.setup_google_info.get("auto_logged_in", False):
                self.reset_form()
                return -6
            self.reset_form()
            return -4
        elif cloud_sync.auth_status in ("FAILED", "CANCELLED"):
            self.login_error_msg = cloud_sync.auth_result_info.get("error", "Google Sign-In Cancelled")
            cloud_sync.auth_status = None

        if self.login_error_msg:
            self._draw_toast_alert(screen, self.login_error_msg, 400, 420, is_error=True)

        # Security footer
        draw_text("256-BIT ENCRYPTED CLOUD ARCHITECTURE", FONT_AUTH_SUB, (70, 95, 130), 400, 515)

        # Handle Clicks
        if (m_c or key_enter) and cloud_sync.auth_status != "WAITING":
            if is_h_g:
                tap_snd.play()
                self.login_error_msg = ""
                cloud_sync.login_google_async()
            elif is_h_guest:
                tap_snd.play()
                cloud_sync.login_guest()
                self.login_error_msg = ""
                return -6

        return -3

    # =========================================================================
    # 2. GOOGLE VERIFIED ROUTE (STATE -4)
    # =========================================================================

    def render_google_action(self, screen, mx, my, m_c, key_enter, key_escape, tap_snd, menu_bg, ui_pulse_t, now):
        """State -4: Google Account Verified — Choose Sign Up vs Log In"""
        draw_neon_auth_bg(screen, now)

        card_rect = pygame.Rect(150, 60, 500, 480)
        self._draw_cyberpunk_card(screen, card_rect, accent_color=NEON_GREEN, pulse_t=ui_pulse_t)

        draw_badge(screen, "[ GOOGLE OAUTH VERIFIED ]", FONT_AUTH_SUB, 400, 96,
                   bg_color=(15, 45, 25), text_color=NEON_GREEN, border_color=NEON_GREEN)

        name = self.setup_google_info.get("name", "Pilot") if self.setup_google_info else "Pilot"
        draw_text_shadow("ACCOUNT LINKED", FONT_MSG, NEON_GREEN, 400, 140, shadow_color=(0, 60, 30), offset=2)
        draw_text(f"Welcome, Commander {name}", FONT_AUTH_TITLE, WHITE, 400, 180)
        draw_divider(screen, 190, 202, 610, NEON_GREEN, alpha=40)

        btn_signup = pygame.Rect(185, 230, 430, 70)
        btn_login  = pygame.Rect(185, 320, 430, 70)
        is_h_signup = btn_signup.collidepoint(mx, my)
        is_h_login  = btn_login.collidepoint(mx, my)

        draw_plasma_button(screen, "CREATE NEW PILOT PROFILE", FONT_UI, WHITE, btn_signup,
                           (0, 140, 60), is_h_signup, pulse_t=ui_pulse_t, accent=NEON_GREEN, border_radius=14)
        draw_plasma_button(screen, "CONNECT EXISTING PROFILE", FONT_UI, WHITE, btn_login,
                           (0, 70, 160), is_h_login, pulse_t=ui_pulse_t, accent=NEON_BLUE, border_radius=14)

        btn_back = pygame.Rect(250, 440, 300, 42)
        is_h_bk = btn_back.collidepoint(mx, my)
        draw_plasma_button(screen, "< BACK", FONT_SMALL, WHITE, btn_back,
                           (120, 20, 40), is_h_bk, pulse_t=0, accent=NEON_PINK, border_radius=10)

        if m_c or key_enter or key_escape:
            if is_h_signup:
                tap_snd.play()
                self.reset_form()
                self.active_tab = "signup"
                return -4.1
            elif is_h_login:
                tap_snd.play()
                self.reset_form()
                self.active_tab = "login"
                return -4.2
            elif is_h_bk or key_escape:
                tap_snd.play()
                return -3

        return -4

    # =========================================================================
    # 3. AUTH FORM SCREEN (STATES -4.1, -4.2, -5)
    # =========================================================================

    def render_auth_form(self, screen, mx, my, m_c, key_enter, key_escape, tap_snd, menu_bg, ui_pulse_t, now, is_signup, is_bind=False):
        """State -4.1 (Sign Up), -4.2 (Log In), or -5 (Bind Account) with Segmented Tabs"""
        draw_neon_auth_bg(screen, now)

        card_rect = pygame.Rect(140, 45, 520, 510)
        accent = NEON_GOLD if is_bind else (NEON_GREEN if is_signup else NEON_CYAN)
        self._draw_cyberpunk_card(screen, card_rect, accent_color=accent, pulse_t=ui_pulse_t)

        # ── Segmented Tab Switcher ──
        if not is_bind:
            tab_bar = pygame.Rect(175, 72, 450, 44)
            t_surf = pygame.Surface((tab_bar.width, tab_bar.height), pygame.SRCALPHA)
            pygame.draw.rect(t_surf, (14, 18, 30, 230), t_surf.get_rect(), border_radius=22)
            pygame.draw.rect(t_surf, (45, 55, 80), t_surf.get_rect(), width=1, border_radius=22)
            screen.blit(t_surf, tab_bar.topleft)

            tab_login_rect = pygame.Rect(tab_bar.x + 4, tab_bar.y + 4, 218, 36)
            tab_signup_rect = pygame.Rect(tab_bar.x + 228, tab_bar.y + 4, 218, 36)
            is_h_tlogin = tab_login_rect.collidepoint(mx, my)
            is_h_tsignup = tab_signup_rect.collidepoint(mx, my)

            # Active Tab Slider
            active_rect = tab_signup_rect if is_signup else tab_login_rect
            pill_surf = pygame.Surface((active_rect.width, active_rect.height), pygame.SRCALPHA)
            pill_col = (0, 140, 60, 240) if is_signup else (0, 90, 160, 240)
            pygame.draw.rect(pill_surf, pill_col, pill_surf.get_rect(), border_radius=18)
            pygame.draw.rect(pill_surf, accent, pill_surf.get_rect(), width=1, border_radius=18)
            screen.blit(pill_surf, active_rect.topleft)

            draw_text("LOG IN", FONT_AUTH_TITLE, WHITE if not is_signup else (130, 150, 180), tab_login_rect.centerx, tab_login_rect.centery)
            draw_text("SIGN UP", FONT_AUTH_TITLE, WHITE if is_signup else (130, 150, 180), tab_signup_rect.centerx, tab_signup_rect.centery)

            if m_c:
                if is_h_tlogin and is_signup:
                    tap_snd.play()
                    self.login_error_msg = ""
                    return -4.2
                elif is_h_tsignup and not is_signup:
                    tap_snd.play()
                    self.login_error_msg = ""
                    return -4.1
        else:
            draw_badge(screen, "// BIND GOOGLE ACCOUNT //", FONT_AUTH_SUB, 400, 84,
                       bg_color=(35, 25, 10), text_color=NEON_GOLD, border_color=NEON_GOLD)

        # ── Form Inputs ──
        user_rect = pygame.Rect(175, 136, 450, 56)
        pass_rect = pygame.Rect(175, 210, 395, 56)
        eye_rect  = pygame.Rect(576, 210, 49, 56)

        is_h_user = user_rect.collidepoint(mx, my)
        is_h_pass = pass_rect.collidepoint(mx, my)
        is_h_eye  = eye_rect.collidepoint(mx, my)

        if m_c:
            if is_h_user:
                self.setup_active_field = "username"
                self._ensure_keyboard(True)
            elif is_h_pass:
                self.setup_active_field = "password"
                self._ensure_keyboard(True)
            elif is_h_eye:
                tap_snd.play()
                self.show_password = not self.show_password

        # Draw Inputs
        self._draw_modern_input(screen, user_rect, "Pilot Codename (Username)", self.setup_username,
                                self.setup_active_field == "username", False, False, now)
        self._draw_modern_input(screen, pass_rect, "Security Key (Password)", self.setup_password,
                                self.setup_active_field == "password", True, self.show_password, now)

        # Eye Toggle Button
        eye_surf = pygame.Surface((eye_rect.width, eye_rect.height), pygame.SRCALPHA)
        eye_bg = (25, 34, 58, 240) if is_h_eye else (18, 24, 42, 220)
        pygame.draw.rect(eye_surf, eye_bg, eye_surf.get_rect(), border_radius=12)
        pygame.draw.rect(eye_surf, NEON_CYAN if is_h_eye else (55, 70, 98), eye_surf.get_rect(), width=1, border_radius=12)
        screen.blit(eye_surf, eye_rect.topleft)
        self._draw_vector_eye(screen, eye_rect.centerx, eye_rect.centery, is_open=self.show_password, color=NEON_CYAN if self.show_password else LIGHT_GRAY)

        # ── Forgot Password Link ──
        is_h_forgot = False
        if not is_signup and not is_bind:
            forgot_rect = pygame.Rect(175, 276, 450, 22)
            is_h_forgot = forgot_rect.collidepoint(mx, my)
            f_col = NEON_CYAN if is_h_forgot else (120, 150, 190)
            draw_text("Forgot Password? (Requires Google link)", FONT_AUTH_SUB, f_col, 400, 286)
            if is_h_forgot:
                pygame.draw.line(screen, f_col, (260, 294), (540, 294), 1)

        # ── Toast Error Alert ──
        if self.login_error_msg:
            self._draw_toast_alert(screen, self.login_error_msg, 400, 324, is_error=True)

        # ── Submit Button ──
        btn_submit = pygame.Rect(175, 356, 450, 60)
        is_h_sub = btn_submit.collidepoint(mx, my)
        submit_txt = "CONFIRM ACCOUNT BINDING" if is_bind else ("CREATE PILOT ACCOUNT" if is_signup else "LAUNCH MISSION / LOG IN")
        sub_col = (0, 140, 60) if is_signup else ((140, 90, 0) if is_bind else (0, 80, 170))
        draw_plasma_button(screen, submit_txt, FONT_UI, WHITE, btn_submit,
                           sub_col, is_h_sub, pulse_t=ui_pulse_t, accent=accent, border_radius=14)

        # ── Back Button ──
        btn_back = pygame.Rect(235, 436, 330, 40)
        is_h_bk = btn_back.collidepoint(mx, my)
        draw_plasma_button(screen, "< BACK", FONT_SMALL, WHITE, btn_back,
                           (120, 20, 40), is_h_bk, pulse_t=0, accent=NEON_PINK, border_radius=10)

        # ── Handlers ──
        if (m_c and is_h_forgot):
            tap_snd.play()
            if not self.setup_google_info:
                self.login_error_msg = "Must Continue with Google to reset password."
            elif len(self.setup_username) < 3 or len(self.setup_password) < 3:
                self.login_error_msg = "Enter codename & new password above first."
            else:
                success, msg = cloud_sync.reset_password(self.setup_google_info, self.setup_username, self.setup_password)
                if success:
                    cloud_sync.queue_sync({})
                    self._ensure_keyboard(False)
                    return -6
                else:
                    self.login_error_msg = msg
            return -4.2

        if (m_c and is_h_bk) or key_escape:
            tap_snd.play()
            self.login_error_msg = ""
            self._ensure_keyboard(False)
            return 9 if is_bind else -4

        if (m_c and is_h_sub) or key_enter:
            if len(self.setup_username) < 3:
                self.login_error_msg = "Username must be at least 3 characters."
            elif len(self.setup_password) < 3:
                self.login_error_msg = "Password must be at least 3 characters."
            else:
                tap_snd.play()
                success = False
                msg = ""
                if is_bind:
                    success = cloud_sync.bind_guest_to_google(self.setup_google_info, self.setup_username, self.setup_password)
                    if not success:
                        msg = "Account binding failed."
                elif is_signup:
                    success, msg = cloud_sync.register_new_user(self.setup_google_info, self.setup_username, self.setup_password)
                else:
                    success, msg = cloud_sync.login_existing_user(self.setup_username, self.setup_password)

                if success:
                    cloud_sync.queue_sync({})
                    self._ensure_keyboard(False)
                    return -6
                else:
                    self.login_error_msg = msg
                    if not is_signup:
                        self.setup_password = ""

        if is_bind:
            return -5
        return -4.1 if is_signup else -4.2


