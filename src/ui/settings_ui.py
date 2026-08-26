import pygame
import math
from assets import (draw_menu_starfield, draw_text, draw_text_shadow,
                    draw_holographic_panel, draw_neon_panel, draw_divider,
                    draw_plasma_button, draw_glowing_button, draw_badge, draw_corner_brackets,
                    FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD,
                    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE,
                    RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, DARK_GRAY,
                    NEON_TEAL, NEON_AMBER)
from settings import WIDTH, HEIGHT
from cloud_sync import current_account_type


def _draw_ios_toggle(screen, cx, cy, active, accent_on=NEON_GREEN, pulse_t=0.0):
    """Draw an iOS-style animated pill toggle switch."""
    track_w, track_h = 52, 26
    track_rect = pygame.Rect(cx - track_w // 2, cy - track_h // 2, track_w, track_h)

    # Track
    track_col = (*accent_on, 200) if active else (50, 55, 75, 200)
    track_surf = pygame.Surface((track_w, track_h), pygame.SRCALPHA)
    pygame.draw.rect(track_surf, track_col, track_surf.get_rect(), border_radius=13)
    screen.blit(track_surf, track_rect.topleft)

    # Thumb
    thumb_x = track_rect.x + (track_w - 22) if active else track_rect.x + 2
    thumb_rect = pygame.Rect(thumb_x, cy - 11, 22, 22)
    thumb_surf = pygame.Surface((22, 22), pygame.SRCALPHA)

    # Glow on active
    if active:
        gsurf = pygame.Surface((30, 30), pygame.SRCALPHA)
        ga = int(60 + 40 * math.sin(pulse_t * 4))
        pygame.draw.circle(gsurf, (*accent_on, ga), (15, 15), 15)
        screen.blit(gsurf, (thumb_x - 4, cy - 15))

    pygame.draw.circle(thumb_surf, WHITE, (11, 11), 11)
    pygame.draw.circle(thumb_surf, (200, 210, 220), (11, 11), 11, 1)
    screen.blit(thumb_surf, thumb_rect.topleft)

    return track_rect


def _draw_neon_slider(screen, sx, sy, sw, val, label, accent=NEON_CYAN, mx=0, my=0, m_down=False):
    """Draw a neon-styled horizontal slider with draggable thumb."""
    s_rect = pygame.Rect(sx, sy, sw, 10)

    # Track background
    track_bg = pygame.Surface((sw, 10), pygame.SRCALPHA)
    pygame.draw.rect(track_bg, (25, 30, 45, 200), track_bg.get_rect(), border_radius=5)
    screen.blit(track_bg, s_rect.topleft)

    # Filled portion
    fill_w = max(0, int(sw * val))
    if fill_w > 0:
        fill_surf = pygame.Surface((fill_w, 10), pygame.SRCALPHA)
        for px in range(fill_w):
            t = px / max(1, fill_w - 1)
            r = int(0 + accent[0] * t)
            g = int(accent[1] * (0.5 + 0.5 * t))
            b = int(accent[2])
            pygame.draw.line(fill_surf, (r, g, b, 220), (px, 0), (px, 10))
        screen.blit(fill_surf, s_rect.topleft)

    # Thumb
    handle_x = s_rect.x + fill_w
    is_hover = math.hypot(mx - handle_x, my - s_rect.centery) < 16
    thumb_r = 9 if is_hover else 7
    thumb_surf = pygame.Surface((thumb_r * 2 + 4, thumb_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(thumb_surf, (*accent, 200), (thumb_r + 2, thumb_r + 2), thumb_r)
    pygame.draw.circle(thumb_surf, WHITE, (thumb_r + 2, thumb_r + 2), thumb_r - 3)
    screen.blit(thumb_surf, (handle_x - thumb_r - 2, s_rect.centery - thumb_r - 2))

    # Label + percentage
    draw_text(label, FONT_TINY, LIGHT_GRAY, sx, sy - 14, center=False)
    draw_text(f"{int(val * 100)}%", FONT_TINY, accent, sx + sw + 26, s_rect.centery)

    new_val = val
    if m_down and (s_rect.inflate(0, 20).collidepoint(mx, my) or is_hover):
        new_val = max(0.0, min(1.0, (mx - s_rect.x) / s_rect.width))

    return new_val, s_rect


def render_settings(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
                    control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
                    screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    """Premium settings screen with iOS toggles and neon sliders."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("GAME SETTINGS", FONT_MSG, NEON_CYAN, 400, 44, shadow_color=(0, 80, 120), offset=2)
    draw_divider(screen, 80, 72, 720, NEON_CYAN, alpha=50)

    next_state = 9

    # ── Control Mode Cards ──────────────────────────────────
    draw_text("CONTROL MODE", FONT_TINY, (120, 150, 190), 90, 90, center=False)

    btn_pc  = pygame.Rect(90, 105, 270, 82)
    btn_mob = pygame.Rect(330, 105, 270, 82)

    is_h_pc  = btn_pc.collidepoint(mx, my)
    is_h_mob = btn_mob.collidepoint(mx, my)

    pc_active  = control_type == 'PC'
    mob_active = control_type == 'MOBILE'

    pc_accent  = NEON_GREEN if pc_active else (NEON_TEAL if is_h_pc else (60, 70, 90))
    mob_accent = NEON_ORANGE if mob_active else (NEON_AMBER if is_h_mob else (60, 70, 90))

    draw_holographic_panel(screen, btn_pc,  accent=pc_accent,  alpha=225, border_radius=14,
                           border_width=3 if pc_active else 2,
                           show_corners=pc_active, pulse_t=ui_pulse_t)
    draw_holographic_panel(screen, btn_mob, accent=mob_accent, alpha=225, border_radius=14,
                           border_width=3 if mob_active else 2,
                           show_corners=mob_active, pulse_t=ui_pulse_t)

    draw_text("⌨  PC LAYOUT", FONT_UI, WHITE if pc_active else LIGHT_GRAY,
              btn_pc.centerx, btn_pc.centery - 12)
    draw_text("WASD + Mouse / Space", FONT_TINY, pc_accent,
              btn_pc.centerx, btn_pc.centery + 14)

    draw_text("📱  MOBILE LAYOUT", FONT_UI, WHITE if mob_active else LIGHT_GRAY,
              btn_mob.centerx, btn_mob.centery - 12)
    draw_text("Touch Slide & Tap", FONT_TINY, mob_accent,
              btn_mob.centerx, btn_mob.centery + 14)

    if m_c:
        if is_h_pc:
            tap_snd.play()
            control_type = 'PC'
            m_c = False
        elif is_h_mob:
            tap_snd.play()
            control_type = 'MOBILE'
            m_c = False

    draw_divider(screen, 90, 200, 710, NEON_CYAN, alpha=30)

    # ── Visual Quality ──────────────────────────────────────
    draw_text("VISUAL QUALITY", FONT_TINY, (120, 150, 190), 90, 108, center=False)

    quality_btns = [
        ("PERFORMANCE", 'low',    NEON_PINK,   pygame.Rect(90,  122, 152, 36)),
        ("BALANCED",    'medium', NEON_GOLD,   pygame.Rect(254, 122, 152, 36)),
        ("CINEMATIC",   'high',   NEON_CYAN,   pygame.Rect(418, 122, 152, 36)),
    ]
    for (qtxt, qval, qcol, qrect) in quality_btns:
        is_h_q = qrect.collidepoint(mx, my)
        active  = (visual_quality == qval)
        bg_surf = pygame.Surface((qrect.width, qrect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (*qcol, 60 if active else 20), bg_surf.get_rect(), border_radius=10)
        screen.blit(bg_surf, qrect.topleft)
        bw = 2 if not active else 3
        pygame.draw.rect(screen, qcol if active else (60, 70, 90), qrect, width=bw, border_radius=10)
        draw_text(qtxt, FONT_TINY, WHITE if active else LIGHT_GRAY, qrect.centerx, qrect.centery)
        if m_c and is_h_q:
            tap_snd.play()
            visual_quality = qval
            m_c = False

    draw_divider(screen, 90, 172, 710, NEON_CYAN, alpha=30)

    # ── iOS-style Toggle Switches ────────────────────────────
    draw_text("GAMEPLAY OPTIONS", FONT_TINY, (120, 150, 190), 90, 188, center=False)

    toggles = [
        ("DAMAGE NUMBERS",  show_damage_enabled,  NEON_GOLD,   90,  218),
        ("AUTO-FIRE",       auto_fire_enabled,     NEON_GREEN,  340, 218),
        ("SCREEN SHAKE",    screen_shake_enabled,  NEON_PINK,   90,  264),
        ("SHOW FPS",        show_fps,              NEON_CYAN,   340, 264),
    ]
    toggle_states = [show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps]

    for i, (tlabel, tval, taccent, tx, ty) in enumerate(toggles):
        # Row background
        row = pygame.Rect(tx - 4, ty - 12, 240, 42)
        row_surf = pygame.Surface((row.width, row.height), pygame.SRCALPHA)
        pygame.draw.rect(row_surf, (*PANEL_MID, 160), row_surf.get_rect(), border_radius=10)
        screen.blit(row_surf, row.topleft)

        draw_text(tlabel, FONT_TINY, LIGHT_GRAY, tx + 8, ty + 9, center=False)

        toggle_cx = tx + 200
        tr = _draw_ios_toggle(screen, toggle_cx, ty + 9, tval, accent_on=taccent, pulse_t=ui_pulse_t)

        if m_c and row.collidepoint(mx, my):
            tap_snd.play()
            toggle_states[i] = not tval
            m_c = False

    show_damage_enabled = toggle_states[0]
    auto_fire_enabled   = toggle_states[1]
    screen_shake_enabled= toggle_states[2]
    show_fps            = toggle_states[3]

    draw_divider(screen, 90, 312, 710, NEON_CYAN, alpha=30)

    # ── Neon Volume Sliders ──────────────────────────────────
    draw_text("AUDIO", FONT_TINY, (120, 150, 190), 90, 330, center=False)

    music_vol, _ = _draw_neon_slider(screen, 90,  352, 240, music_vol,
                                     "MUSIC VOLUME", accent=NEON_TEAL, mx=mx, my=my, m_down=m_down)
    sfx_vol, _   = _draw_neon_slider(screen, 400, 352, 240, sfx_vol,
                                     "SFX VOLUME",   accent=NEON_AMBER, mx=mx, my=my, m_down=m_down)

    if m_down:
        pygame.mixer.music.set_volume(music_vol)

    draw_divider(screen, 90, 384, 710, NEON_CYAN, alpha=30)

    # ── Account & System Buttons ─────────────────────────────
    btn_bind = pygame.Rect(90, 400, 230, 44)
    is_h_bind = btn_bind.collidepoint(mx, my)

    if current_account_type == "guest":
        draw_plasma_button(screen, "🔗 BIND TO GOOGLE", FONT_SMALL, WHITE, btn_bind,
                          (140, 100, 0), is_h_bind, pulse_t=ui_pulse_t, accent=NEON_GOLD, border_radius=12)
        if m_c and is_h_bind:
            tap_snd.play()
            import cloud_sync
            cloud_sync.login_google_async()
            next_state = 11
            m_c = False
    else:
        draw_plasma_button(screen, "X LOGOUT", FONT_SMALL, WHITE, btn_bind,
                          (120, 20, 30), is_h_bind, pulse_t=0, accent=NEON_PINK, border_radius=12)
        if m_c and is_h_bind:
            tap_snd.play()
            import cloud_sync
            cloud_sync.clear_local_session()
            next_state = -3
            m_c = False

    btn_win = pygame.Rect(340, 400, 200, 44)
    is_h_win = btn_win.collidepoint(mx, my)
    draw_plasma_button(screen, "VIEW CONTROLS", FONT_SMALL, WHITE, btn_win,
                       (0, 60, 150), is_h_win, pulse_t=0, accent=NEON_CYAN, border_radius=12)
    if m_c and is_h_win:
        tap_snd.play()
        next_state = 11
        m_c = False

    btn_back = pygame.Rect(554, 400, 156, 44)
    is_h_back = btn_back.collidepoint(mx, my)
    draw_plasma_button(screen, "< BACK", FONT_SMALL, WHITE, btn_back,
                       (120, 20, 50), is_h_back, pulse_t=0, accent=NEON_PINK, border_radius=12)

    if m_c or key_escape:
        if (is_h_back and m_c) or key_escape:
            tap_snd.play()
            next_state = 3 if settings_from_pause else 0
            m_c = False

    return (next_state, control_type, visual_quality, show_damage_enabled,
            auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, m_c)
