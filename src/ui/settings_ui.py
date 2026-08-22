import pygame
import math
from assets import draw_menu_starfield, draw_text, draw_text_shadow, draw_neon_panel, draw_divider, draw_glowing_button, FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE, RED, WHITE, LIGHT_GRAY, MID_GRAY, DARK_GRAY
from settings import WIDTH, HEIGHT
from cloud_sync import current_account_type

def render_settings(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg, control_type, visual_quality, show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 190))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("GAME SETTINGS", FONT_MSG, NEON_CYAN, 400, 50, shadow_color=(0,80,120), offset=2)
    draw_divider(screen, 80, 78, 720, NEON_CYAN, alpha=40)

    # --- Device Selection Cards ---
    mob_active = control_type == 'MOBILE'
    pc_active  = control_type == 'PC'

    btn_mob = pygame.Rect(80,  95, 280, 90)
    btn_pc  = pygame.Rect(440, 95, 280, 90)

    is_h_mob = btn_mob.collidepoint(mx, my)
    is_h_pc  = btn_pc.collidepoint(mx, my)

    mob_accent = NEON_CYAN if mob_active else (NEON_BLUE if is_h_mob else MID_GRAY)
    pc_accent  = NEON_GREEN if pc_active else (NEON_BLUE if is_h_pc else MID_GRAY)

    draw_neon_panel(screen, btn_mob, accent=mob_accent, alpha=230, border_radius=15, border_width=3 if mob_active else 2)
    draw_text("📱  MOBILE LAYOUT", FONT_UI, WHITE if mob_active else LIGHT_GRAY, btn_mob.centerx, btn_mob.centery - 12)
    draw_text("Virtual Joystick & Touch", FONT_TINY, LIGHT_GRAY if mob_active else DARK_GRAY, btn_mob.centerx, btn_mob.centery + 15)

    draw_neon_panel(screen, btn_pc, accent=pc_accent, alpha=230, border_radius=15, border_width=3 if pc_active else 2)
    draw_text("⌨  PC LAYOUT", FONT_UI, WHITE if pc_active else LIGHT_GRAY, btn_pc.centerx, btn_pc.centery - 12)
    draw_text("WASD + Mouse Aim", FONT_TINY, LIGHT_GRAY if pc_active else DARK_GRAY, btn_pc.centerx, btn_pc.centery + 15)

    if m_c:
        if is_h_mob:
            tap_snd.play()
            control_type = 'MOBILE'
            m_c = False
        elif is_h_pc:
            tap_snd.play()
            control_type = 'PC'
            m_c = False

    draw_divider(screen, 120, 205, 680, NEON_CYAN, alpha=30)

    # --- Quality Settings ---
    draw_text("VISUAL QUALITY", FONT_SMALL, LIGHT_GRAY, 160, 230, center=False)
    btn_q_low  = pygame.Rect(320, 220, 90, 36)
    btn_q_med  = pygame.Rect(420, 220, 110, 36)
    btn_q_high = pygame.Rect(540, 220, 90, 36)

    is_h_q_low = btn_q_low.collidepoint(mx, my)
    is_h_q_med = btn_q_med.collidepoint(mx, my)
    is_h_q_high = btn_q_high.collidepoint(mx, my)

    def draw_q_btn(rect, txt, active, hover, col):
        acc = col if active else (NEON_BLUE if hover else MID_GRAY)
        pygame.draw.rect(screen, (30,30,50) if active else (15,15,25), rect, border_radius=8)
        pygame.draw.rect(screen, acc, rect, width=2, border_radius=8)
        draw_text(txt, FONT_TINY, WHITE if active else LIGHT_GRAY, rect.centerx, rect.centery)

    draw_q_btn(btn_q_low, "PERFORMANCE", visual_quality == 'low', is_h_q_low, NEON_PINK)
    draw_q_btn(btn_q_med, "BALANCED", visual_quality == 'medium', is_h_q_med, NEON_GOLD)
    draw_q_btn(btn_q_high, "CINEMATIC", visual_quality == 'high', is_h_q_high, NEON_CYAN)

    if m_c:
        if is_h_q_low:
            tap_snd.play()
            visual_quality = 'low'
        elif is_h_q_med:
            tap_snd.play()
            visual_quality = 'medium'
        elif is_h_q_high:
            tap_snd.play()
            visual_quality = 'high'

    # --- Toggles ---
    def draw_toggle(x, y, txt, active, hover, accent):
        btn = pygame.Rect(x, y, 220, 40)
        col = accent if active else (NEON_BLUE if hover else MID_GRAY)
        draw_neon_panel(screen, btn, accent=col, alpha=180, border_radius=8, border_width=2)
        status = "ON" if active else "OFF"
        draw_text(txt, FONT_TINY, LIGHT_GRAY, btn.x + 15, btn.centery, center=False)
        draw_text(status, FONT_SMALL, accent if active else DARK_GRAY, btn.right - 40, btn.centery)
        return btn

    btn_dmg = draw_toggle(90, 280, "DAMAGE NUMBERS", show_damage_enabled, False, NEON_GOLD)
    btn_auto = draw_toggle(325, 280, "AUTO-FIRE", auto_fire_enabled, False, NEON_GREEN)
    btn_shake = draw_toggle(90, 335, "SCREEN SHAKE", screen_shake_enabled, False, NEON_PINK)
    btn_fps = draw_toggle(325, 335, "SHOW FPS", show_fps, False, NEON_CYAN)
    
    is_h_dmg = btn_dmg.collidepoint(mx, my)
    is_h_auto = btn_auto.collidepoint(mx, my)
    is_h_shake = btn_shake.collidepoint(mx, my)
    is_h_fps = btn_fps.collidepoint(mx, my)

    if m_c:
        if is_h_dmg: show_damage_enabled = not show_damage_enabled
        if is_h_auto: auto_fire_enabled = not auto_fire_enabled
        if is_h_shake: screen_shake_enabled = not screen_shake_enabled
        if is_h_fps: show_fps = not show_fps
        if any([is_h_dmg, is_h_auto, is_h_shake, is_h_fps]):
            tap_snd.play()
            m_c = False

    # --- Sliders ---
    def draw_slider(y, label, val):
        draw_text(label, FONT_TINY, LIGHT_GRAY, 590, y, center=False)
        s_rect = pygame.Rect(590, y + 20, 160, 10)
        pygame.draw.rect(screen, (20,20,30), s_rect, border_radius=5)
        fill_w = int(160 * val)
        if fill_w > 0:
            pygame.draw.rect(screen, NEON_CYAN, (s_rect.x, s_rect.y, fill_w, 10), border_radius=5)
        
        handle_x = s_rect.x + fill_w
        is_hover = math.hypot(mx - handle_x, my - s_rect.centery) < 15
        pygame.draw.circle(screen, WHITE if is_hover else LIGHT_GRAY, (handle_x, s_rect.centery), 8)
        
        pct_txt = f"{int(val*100)}%"
        draw_text(pct_txt, FONT_TINY, NEON_CYAN, s_rect.right + 25, s_rect.centery)
        
        return s_rect, handle_x
        
    vol_rect, h1 = draw_slider(275, "MUSIC VOLUME", music_vol)
    sfx_rect, h2 = draw_slider(330, "SFX VOLUME", sfx_vol)

    if m_down:
        if vol_rect.collidepoint(mx, my) or math.hypot(mx - h1, my - vol_rect.centery) < 15:
            new_val = max(0, min(1, (mx - vol_rect.x) / vol_rect.width))
            if new_val != music_vol:
                music_vol = new_val
                pygame.mixer.music.set_volume(music_vol)
        
        if sfx_rect.collidepoint(mx, my) or math.hypot(mx - h2, my - sfx_rect.centery) < 15:
            new_val = max(0, min(1, (mx - sfx_rect.x) / sfx_rect.width))
            if new_val != sfx_vol:
                sfx_vol = new_val
                tap_snd.set_volume(sfx_vol)

    draw_divider(screen, 120, 400, 680, NEON_CYAN, alpha=30)
    
    # --- Account & System ---
    btn_bind = pygame.Rect(120, 425, 260, 50)
    is_h_bind = btn_bind.collidepoint(mx, my)
    
    next_state = 9
    
    if current_account_type == "guest":
        draw_glowing_button(screen, "🔗 BIND TO GOOGLE", FONT_UI, WHITE, btn_bind, NEON_GOLD, is_h_bind, pulse_t=ui_pulse_t)
        if m_c and is_h_bind:
            tap_snd.play()
            import cloud_sync
            cloud_sync.login_google_async()
            next_state = 11 # We use 11 or wait for it
            m_c = False
    else:
        btn_logout = pygame.Rect(120, 425, 260, 50)
        is_h_logout = btn_logout.collidepoint(mx, my)
        draw_glowing_button(screen, "✕ LOGOUT ACCOUNT", FONT_UI, WHITE, btn_logout, RED, is_h_logout, pulse_t=0)
        if m_c and is_h_logout:
            tap_snd.play()
            import cloud_sync
            cloud_sync.clear_local_session()
            next_state = -3
            m_c = False

    btn_win = pygame.Rect(420, 425, 260, 50)
    is_h_win = btn_win.collidepoint(mx, my)
    draw_glowing_button(screen, "PC CONTROLS INFO", FONT_UI, WHITE, btn_win, NEON_CYAN, is_h_win, pulse_t=0)
    if m_c and is_h_win:
        tap_snd.play()
        next_state = 11
        m_c = False

    btn_back = pygame.Rect(250, 510, 300, 50)
    is_h_back = btn_back.collidepoint(mx, my)
    draw_glowing_button(screen, "← BACK", FONT_UI, WHITE, btn_back, NEON_PINK, is_h_back, pulse_t=0)

    if m_c or key_escape:
        if is_h_back or key_escape:
            tap_snd.play()
            next_state = 3 if settings_from_pause else 0
            m_c = False

    return (next_state, control_type, visual_quality, show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, m_c)
