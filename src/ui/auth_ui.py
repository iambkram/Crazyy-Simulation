import pygame
import math
import cloud_sync
from assets import *
from vfx import draw_neon_auth_bg
from settings import *

class AuthUI:
    def __init__(self):
        self.setup_username = ""
        self.setup_password = ""
        self.setup_active_field = "username"
        self.login_error_msg = ""
        self.setup_google_info = None
        self.show_password = False
        self._field_anim = {'username': 0.0, 'password': 0.0}  # Label float animation
        self._pulse = 0.0

    def reset_form(self):
        self.setup_username = ""
        self.setup_password = ""
        self.setup_active_field = "username"
        self.login_error_msg = ""
        self.show_password = False

    def handle_input(self, key_unicode, key_backspace, key_tab):
        if key_tab:
            self.setup_active_field = "password" if self.setup_active_field == "username" else "username"
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

    def _draw_field(self, screen, rect, label, value, is_active, is_password, show_pass, now):
        """Draw a modern floating-label input field."""
        # Background
        field_bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(field_bg, (*PANEL_MID, 200), field_bg.get_rect(), border_radius=10)
        screen.blit(field_bg, rect.topleft)

        # Animated bottom border (thicker + neon when active)
        border_w = 3 if is_active else 1
        border_col = NEON_CYAN if is_active else (80, 90, 110)
        pygame.draw.rect(screen, border_col,
                         pygame.Rect(rect.x, rect.bottom - border_w, rect.width, border_w),
                         border_radius=2)

        # Floating label
        has_content = bool(value)
        float_up = is_active or has_content
        label_y = rect.y + (8 if float_up else rect.height // 2 - 8)
        label_col = NEON_CYAN if is_active else (120, 140, 170)
        label_fnt = FONT_TINY if float_up else FONT_SMALL
        draw_text(label, label_fnt, label_col, rect.x + 12, label_y, center=False)

        # Value text
        display = ("*" * len(value)) if (is_password and not show_pass) else value
        if is_active:
            cursor = "_" if (now // 500) % 2 == 0 else ""
            display += cursor
        if display:
            draw_text(display, FONT_UI, WHITE, rect.x + 12, rect.y + rect.height // 2 + 8, center=False)

        # Side glow if active
        if is_active:
            glow = pygame.Surface((4, rect.height), pygame.SRCALPHA)
            glow.fill((*NEON_CYAN, 80))
            screen.blit(glow, (rect.x, rect.y))

    def render_method_select(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now):
        """State -3: Choose between Google and Guest"""
        draw_neon_auth_bg(screen, now)

        # === COSMIC CIVIL WAR TERMINAL BRANDING ===
        # Terminal header bar
        hbar = pygame.Surface((800, 44), pygame.SRCALPHA)
        hbar.fill((0, 20, 40, 200))
        screen.blit(hbar, (0, 0))
        draw_text("// COSMIC CIVIL WAR  //  AUTHENTICATION TERMINAL  //", FONT_MONO_SM, NEON_CYAN, 400, 22)
        # Scanline strip on header
        for sy in range(0, 44, 4):
            pygame.draw.line(screen, (0, 200, 255, 15), (0, sy), (800, sy), 1)

        # Title glow
        for goff in [6, 3, 1]:
            ts = FONT_TITLE.render("CRAZYY SIMULATION", True, NEON_CYAN)
            ts.set_alpha(30 if goff == 6 else (70 if goff == 3 else 160))
            screen.blit(ts, ts.get_rect(center=(400, 125)))
        draw_text_shadow("CRAZYY SIMULATION", FONT_TITLE, NEON_CYAN, 400, 125, shadow_color=(0, 60, 100), offset=3)

        # COSMIC CIVIL WAR gold subtitle
        ccw_a = int(190 + 55 * math.sin(ui_pulse_t * 3.0))
        ccw_col = (min(255, ccw_a), min(255, int(ccw_a * 0.82)), 30)
        ccw_s = FONT_MODAL_SUB.render("[ COSMIC CIVIL WAR ]", True, ccw_col)
        screen.blit(ccw_s, ccw_s.get_rect(center=(400, 180)))

        draw_text("USER AUTHENTICATION", FONT_SMALL, (100, 180, 240), 400, 215)
        draw_divider(screen, 140, 235, 660, NEON_CYAN, alpha=50)

        btn_google = pygame.Rect(200, 255, 400, 62)
        btn_guest  = pygame.Rect(200, 340, 400, 62)

        is_h_google = btn_google.collidepoint(mx, my)
        is_h_guest  = btn_guest.collidepoint(mx, my)

        draw_plasma_button(screen, "  CONTINUE WITH GOOGLE", FONT_UI, WHITE, btn_google,
                          (0, 160, 80), is_h_google, pulse_t=ui_pulse_t, accent=NEON_GREEN, border_radius=14)
        draw_plasma_button(screen, "  CONTINUE AS GUEST", FONT_UI, WHITE, btn_guest,
                          (140, 100, 0), is_h_guest, pulse_t=ui_pulse_t, accent=NEON_GOLD, border_radius=14)

        # Google badge
        badge_surf = pygame.Surface((120, 22), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, (0, 160, 80, 180), badge_surf.get_rect(), border_radius=11)
        screen.blit(badge_surf, (btn_google.x + 12, btn_google.y + btn_google.height // 2 - 11))
        draw_text("Google", FONT_TINY, WHITE, btn_google.x + 72, btn_google.centery)

        if cloud_sync.auth_status == "WAITING":
            draw_neon_text(screen, "Opening browser... please authenticate", FONT_TINY, NEON_CYAN, 400, 430, glow_radius=2)
        elif cloud_sync.auth_status == "SUCCESS":
            self.setup_google_info = cloud_sync.auth_result_info
            cloud_sync.auth_status = None
            if self.setup_google_info and self.setup_google_info.get("auto_logged_in", False):
                self.reset_form()
                return -6
            self.reset_form()
            return -4
        elif cloud_sync.auth_status in ("FAILED", "CANCELLED"):
            self.login_error_msg = cloud_sync.auth_result_info.get("error", "Google Auth Failed")
            cloud_sync.auth_status = None

        if self.login_error_msg:
            draw_text(self.login_error_msg, FONT_TINY, NEON_PINK, 400, 430)

        if (m_c or key_enter) and cloud_sync.auth_status != "WAITING":
            if is_h_google:
                tap_snd.play()
                self.login_error_msg = ""
                cloud_sync.login_google_async()
            elif is_h_guest:
                tap_snd.play()
                cloud_sync.login_guest()
                self.login_error_msg = ""
                return -6

        return -3

    def render_google_action(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now):
        """State -4: Choose Sign Up or Log In after Google Auth"""
        draw_neon_auth_bg(screen, now)

        draw_glitch_text(screen, "ACCOUNT LINKED", FONT_TITLE, NEON_CYAN, 400, 130, now, glitch_intensity=0.04)
        name = self.setup_google_info.get("name", "Pilot") if self.setup_google_info else "Pilot"
        draw_neon_text(screen, f"Google Account Verified: {name}", FONT_UI, NEON_GREEN, 400, 200, glow_radius=2)
        draw_divider(screen, 140, 225, 660, NEON_GREEN, alpha=60)

        btn_signup = pygame.Rect(200, 270, 400, 62)
        btn_login  = pygame.Rect(200, 355, 400, 62)

        is_h_signup = btn_signup.collidepoint(mx, my)
        is_h_login  = btn_login.collidepoint(mx, my)

        draw_plasma_button(screen, "SIGN UP (NEW USER)", FONT_UI, WHITE, btn_signup,
                          (0, 160, 60), is_h_signup, pulse_t=ui_pulse_t, accent=NEON_GREEN, border_radius=14)
        draw_plasma_button(screen, "LOG IN (EXISTING USER)", FONT_UI, WHITE, btn_login,
                          (0, 60, 200), is_h_login, pulse_t=ui_pulse_t, accent=NEON_BLUE, border_radius=14)

        if (m_c or key_enter):
            if is_h_signup:
                tap_snd.play()
                self.reset_form()
                return -4.1
            elif is_h_login:
                tap_snd.play()
                self.reset_form()
                return -4.2
        return -4

    def render_auth_form(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now, is_signup, is_bind=False):
        """State -4.1 (Sign Up), -4.2 (Log In), or -5 (Bind)"""
        draw_neon_auth_bg(screen, now)

        if is_bind:
            title_text = "BIND ACCOUNT"
            subtitle   = "Create a new Username & Password"
        else:
            title_text = "CREATE ACCOUNT" if is_signup else "MISSION LOG IN"
            subtitle   = "Choose a unique Username & Password" if is_signup else "Enter your existing credentials"

        draw_glitch_text(screen, title_text, FONT_TITLE, NEON_CYAN, 400, 110, now, glitch_intensity=0.05)
        draw_text(subtitle, FONT_SMALL, (140, 170, 210), 400, 168)
        draw_divider(screen, 140, 188, 660, NEON_CYAN, alpha=50)

        # Holographic form panel
        form_panel = pygame.Rect(160, 205, 480, 240)
        draw_holographic_panel(screen, form_panel, accent=NEON_CYAN, alpha=210,
                               border_radius=16, show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

        # Username field
        user_rect = pygame.Rect(180, 225, 440, 52)
        is_h_user = user_rect.collidepoint(mx, my)
        if m_c and is_h_user:
            self.setup_active_field = "username"
        self._draw_field(screen, user_rect, "Username", self.setup_username,
                         self.setup_active_field == "username", False, False, now)

        # Password field
        pass_rect = pygame.Rect(180, 300, 400, 52)
        is_h_pass = pass_rect.collidepoint(mx, my)
        if m_c and is_h_pass:
            self.setup_active_field = "password"
        self._draw_field(screen, pass_rect, "Password", self.setup_password,
                         self.setup_active_field == "password", True, self.show_password, now)

        # Eye toggle button
        toggle_rect = pygame.Rect(590, 310, 44, 34)
        is_h_toggle = toggle_rect.collidepoint(mx, my)
        toggle_col = NEON_CYAN if is_h_toggle else (80, 100, 130)
        eye_surf = pygame.Surface((44, 34), pygame.SRCALPHA)
        pygame.draw.rect(eye_surf, (*toggle_col, 80), eye_surf.get_rect(), border_radius=8)
        pygame.draw.rect(eye_surf, (*toggle_col, 200), eye_surf.get_rect(), width=1, border_radius=8)
        screen.blit(eye_surf, toggle_rect.topleft)
        draw_text("👁" if self.show_password else "🙈", FONT_TINY, toggle_col, toggle_rect.centerx, toggle_rect.centery)

        if m_c and is_h_toggle:
            tap_snd.play()
            self.show_password = not self.show_password

        # Forgot password link
        is_h_forgot = False
        if not is_signup and not is_bind:
            forgot_y = 368
            is_h_forgot = pygame.Rect(180, forgot_y - 10, 300, 22).collidepoint(mx, my)
            forgot_col = NEON_CYAN if is_h_forgot else (100, 130, 170)
            draw_text("Forgot Password? (Requires Google)", FONT_TINY, forgot_col, 400, forgot_y)

        # Error message
        if self.login_error_msg:
            err_surf = pygame.Surface((440, 28), pygame.SRCALPHA)
            pygame.draw.rect(err_surf, (180, 20, 40, 160), err_surf.get_rect(), border_radius=8)
            screen.blit(err_surf, (180, 395))
            draw_text(self.login_error_msg, FONT_TINY, (255, 180, 180), 400, 409)

        # Submit button
        btn_submit = pygame.Rect(180, 435, 440, 58)
        is_h_submit = btn_submit.collidepoint(mx, my)
        btn_txt = "CONFIRM BINDING" if is_bind else ("SIGN UP" if is_signup else "LOG IN")
        draw_plasma_button(screen, btn_txt, FONT_UI, WHITE, btn_submit,
                          (0, 150, 60), is_h_submit, pulse_t=ui_pulse_t, accent=NEON_GREEN, border_radius=16)

        # Back button
        btn_back = pygame.Rect(180, 508, 440, 40)
        is_h_back = btn_back.collidepoint(mx, my)
        draw_plasma_button(screen, "BACK", FONT_SMALL, WHITE, btn_back,
                          (120, 20, 40), is_h_back, pulse_t=0, accent=NEON_PINK, border_radius=10)

        if m_c or key_enter:
            if not is_signup and not is_bind and is_h_forgot:
                tap_snd.play()
                if not self.setup_google_info:
                    self.login_error_msg = "You must Continue with Google to reset password."
                elif len(self.setup_username) < 3 or len(self.setup_password) < 3:
                    self.login_error_msg = "Enter username & NEW password above, then click this."
                else:
                    success, msg = cloud_sync.reset_password(self.setup_google_info, self.setup_username, self.setup_password)
                    if success:
                        cloud_sync.queue_sync({})
                        return -6
                    else:
                        self.login_error_msg = msg
                return -4.2

            if is_h_back:
                tap_snd.play()
                self.login_error_msg = ""
                return 9 if is_bind else -4

            if (is_h_submit or key_enter) and len(self.setup_username) >= 3 and len(self.setup_password) >= 3:
                tap_snd.play()
                success = False
                msg = ""
                if is_bind:
                    success = cloud_sync.bind_guest_to_google(self.setup_google_info, self.setup_username, self.setup_password)
                    if not success:
                        msg = "Binding failed."
                elif is_signup:
                    success, msg = cloud_sync.register_new_user(self.setup_google_info, self.setup_username, self.setup_password)
                else:
                    success, msg = cloud_sync.login_existing_user(self.setup_username, self.setup_password)

                if success:
                    cloud_sync.queue_sync({})
                    return -6
                else:
                    self.login_error_msg = msg
                    if not is_signup:
                        self.setup_password = ""

        if is_bind:
            return -5
        return -4.1 if is_signup else -4.2
