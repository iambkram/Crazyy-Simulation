import pygame
import cloud_sync
from assets import *
from vfx import draw_neon_auth_bg
from settings import *
from assets import draw_menu_starfield

class AuthUI:
    def __init__(self):
        self.setup_username = ""
        self.setup_password = ""
        self.setup_active_field = "username"
        self.login_error_msg = ""
        self.setup_google_info = None
        self.show_password = False
        
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

    def render_method_select(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now):
        """State -3: Choose between Google and Guest"""
        draw_neon_auth_bg(screen, now)
        
        draw_text_shadow("CRAZYY SIMULATION", FONT_TITLE, NEON_CYAN, 400, 150, shadow_color=(0,80,120), offset=4)
        draw_text("USER AUTHENTICATION", FONT_UI, WHITE, 400, 220)
        
        btn_google = pygame.Rect(250, 300, 300, 60)
        btn_guest = pygame.Rect(250, 380, 300, 60)
        
        is_h_google = btn_google.collidepoint(mx, my)
        is_h_guest = btn_guest.collidepoint(mx, my)
        
        draw_glowing_button(screen, "CONTINUE WITH GOOGLE", FONT_UI, WHITE, btn_google, NEON_CYAN, is_h_google, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "CONTINUE AS GUEST", FONT_UI, WHITE, btn_guest, NEON_GOLD, is_h_guest, pulse_t=ui_pulse_t)
        
        if cloud_sync.auth_status == "WAITING":
            draw_text("Waiting for browser...", FONT_TINY, NEON_CYAN, 400, 460)
        elif cloud_sync.auth_status == "SUCCESS":
            self.setup_google_info = cloud_sync.auth_result_info
            cloud_sync.auth_status = None
            self.reset_form()
            return -4  # Transition to Sign Up / Log In selection
        elif cloud_sync.auth_status in ("FAILED", "CANCELLED"):
            self.login_error_msg = cloud_sync.auth_result_info.get("error", "Google Auth Failed")
            cloud_sync.auth_status = None
            

        if self.login_error_msg:
            draw_text(self.login_error_msg, FONT_TINY, RED, 400, 460)
            
        if (m_c or key_enter) and cloud_sync.auth_status != "WAITING":
            if is_h_google:
                tap_snd.play()
                self.login_error_msg = ""
                cloud_sync.login_google_async()
            elif is_h_guest:
                tap_snd.play()
                cloud_sync.login_guest()
                self.login_error_msg = ""
                return -6  # Transition to Syncing Profile
                
        return -3

    def render_google_action(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now):
        """State -4: Choose Sign Up or Log In after Google Auth"""
        draw_neon_auth_bg(screen, now)
        
        draw_text_shadow("ACCOUNT LINKED", FONT_TITLE, NEON_CYAN, 400, 150, shadow_color=(0,80,120), offset=4)
        name = self.setup_google_info.get("name", "Pilot") if self.setup_google_info else "Pilot"
        draw_text(f"Google Account Verified: {name}", FONT_UI, WHITE, 400, 220)
        
        btn_signup = pygame.Rect(250, 300, 300, 60)
        btn_login = pygame.Rect(250, 380, 300, 60)
        
        is_h_signup = btn_signup.collidepoint(mx, my)
        is_h_login = btn_login.collidepoint(mx, my)
        
        draw_glowing_button(screen, "SIGN UP (NEW USER)", FONT_UI, WHITE, btn_signup, NEON_GREEN, is_h_signup, pulse_t=ui_pulse_t)
        draw_glowing_button(screen, "LOG IN (EXISTING USER)", FONT_UI, WHITE, btn_login, NEON_BLUE, is_h_login, pulse_t=ui_pulse_t)
        
        if (m_c or key_enter):
            if is_h_signup:
                tap_snd.play()
                self.reset_form()
                return -4.1  # Sign Up Form
            elif is_h_login:
                tap_snd.play()
                self.reset_form()
                return -4.2  # Log In Form
                
        return -4
        
    def render_auth_form(self, screen, mx, my, m_c, key_enter, tap_snd, menu_bg, ui_pulse_t, now, is_signup, is_bind=False):
        """State -4.1 (Sign Up), -4.2 (Log In), or -5 (Bind)"""
        draw_neon_auth_bg(screen, now)
        
        if is_bind:
            title_text = "BIND ACCOUNT"
            subtitle = "Create a new Username and Password"
        else:
            title_text = "CREATE ACCOUNT" if is_signup else "LOG IN"
            subtitle = "Choose a unique Username and Password" if is_signup else "Enter your existing Username and Password"
            
        draw_text_shadow(title_text, FONT_TITLE, NEON_CYAN, 400, 100, shadow_color=(0,80,120), offset=4)
        draw_text(subtitle, FONT_SMALL, LIGHT_GRAY, 400, 150)
        
        # Render input boxes
        user_rect = pygame.Rect(250, 200, 300, 50)
        pass_rect = pygame.Rect(250, 280, 300, 50)
        
        is_h_user = user_rect.collidepoint(mx, my)
        is_h_pass = pass_rect.collidepoint(mx, my)
        
        # We need a small cooldown manually here if we don't have click_cooldown passed.
        # It's better if main.py handles click cooldown.
        
        if m_c:
            if is_h_user: self.setup_active_field = "username"
            if is_h_pass: self.setup_active_field = "password"
            
        draw_neon_panel(screen, user_rect, accent=NEON_CYAN if self.setup_active_field == "username" else MID_GRAY, alpha=230, border_width=2)
        draw_neon_panel(screen, pass_rect, accent=NEON_CYAN if self.setup_active_field == "password" else MID_GRAY, alpha=230, border_width=2)
        
        draw_text("Username:", FONT_TINY, LIGHT_GRAY, 250, 185, center=False)
        user_cursor = "_" if self.setup_active_field == "username" and (now//500)%2==0 else ""
        draw_text(self.setup_username + user_cursor, FONT_UI, WHITE, 260, 225, center=False)
        
        draw_text("Password:", FONT_TINY, LIGHT_GRAY, 250, 265, center=False)
        pass_cursor = "_" if self.setup_active_field == "password" and (now//500)%2==0 else ""
        
        display_pass = self.setup_password if self.show_password else "*" * len(self.setup_password)
        draw_text(display_pass + pass_cursor, FONT_UI, WHITE, 260, 305, center=False)
        
        # Show/Hide Password Button
        toggle_rect = pygame.Rect(560, 290, 40, 30)
        is_h_toggle = toggle_rect.collidepoint(mx, my)
        toggle_color = NEON_CYAN if is_h_toggle else MID_GRAY
        pygame.draw.rect(screen, toggle_color, toggle_rect, 1, border_radius=4)
        draw_text("EYE" if self.show_password else "HIDE", FONT_TINY, toggle_color, 580, 305) # Need standard ascii text if font doesn't support emoji
        
        if m_c and is_h_toggle:
            tap_snd.play()
            self.show_password = not self.show_password
            

        # Forgot Password
        is_h_forgot = False
        if not is_signup and not is_bind:
            btn_forgot = pygame.Rect(250, 340, 300, 25)
            is_h_forgot = btn_forgot.collidepoint(mx, my)
            forgot_col = NEON_CYAN if is_h_forgot else LIGHT_GRAY
            draw_text("Forgot Password? (Requires Google)", FONT_TINY, forgot_col, 400, 352)

        if self.login_error_msg:
            draw_text(self.login_error_msg, FONT_TINY, RED, 400, 360)
            
        btn_submit = pygame.Rect(250, 400, 300, 60)
        is_h_submit = btn_submit.collidepoint(mx, my)
        
        if is_bind:
            btn_txt = "CONFIRM BINDING"
        else:
            btn_txt = "SIGN UP" if is_signup else "LOG IN"
            
        draw_glowing_button(screen, btn_txt, FONT_UI, WHITE, btn_submit, NEON_GREEN, is_h_submit, pulse_t=ui_pulse_t)
        
        btn_back = pygame.Rect(250, 480, 300, 40)
        is_h_back = btn_back.collidepoint(mx, my)
        draw_glowing_button(screen, "BACK", FONT_SMALL, WHITE, btn_back, RED, is_h_back, pulse_t=0)
        
        if m_c or key_enter:

            if not is_signup and not is_bind and is_h_forgot:
                tap_snd.play()
                if not self.setup_google_info:
                    self.login_error_msg = "You must Continue with Google to reset password."
                elif len(self.setup_username) < 3 or len(self.setup_password) < 3:
                    self.login_error_msg = "Enter username & NEW password above, then click this button."
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
                return 11 if is_bind else -4 # Back to Settings or Action Select
                
            if (is_h_submit or key_enter) and len(self.setup_username) >= 3 and len(self.setup_password) >= 3:
                tap_snd.play()
                success = False
                msg = ""
                
                if is_bind:
                    success = cloud_sync.bind_guest_to_google(self.setup_google_info, self.setup_username, self.setup_password)
                    if not success: msg = "Binding failed."
                elif is_signup:
                    success, msg = cloud_sync.register_new_user(self.setup_google_info, self.setup_username, self.setup_password)
                else:
                    success, msg = cloud_sync.login_existing_user(self.setup_username, self.setup_password)
                    
                if success:
                    cloud_sync.queue_sync({})
                    return -6 # Go to Syncing Profile
                else:
                    self.login_error_msg = msg
                    if not is_signup:
                        self.setup_password = ""
        
        if is_bind:
            return -5
        return -4.1 if is_signup else -4.2
