import pygame
import math
from assets import (draw_menu_starfield, draw_text, draw_text_shadow,
                    draw_holographic_panel, draw_neon_panel, draw_divider,
                    draw_plasma_button, draw_glowing_button, draw_badge,
                    FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE,
                    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE,
                    RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, NEON_TEAL, NEON_AMBER)
from settings import WIDTH, HEIGHT
from platform_config import is_mobile, is_pc
import cloud_sync


def _draw_ios_toggle(screen, cx, cy, active, accent_on=NEON_GREEN, pulse_t=0.0):
    """Draw a smooth pill-shaped iOS-style toggle switch."""
    w, h = 48, 26
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    bg_col = accent_on if active else (40, 48, 65)

    track = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(track, (*bg_col, 220), track.get_rect(), border_radius=h // 2)
    border_col = accent_on if active else (70, 80, 105)
    pygame.draw.rect(track, border_col, track.get_rect(), width=2, border_radius=h // 2)
    screen.blit(track, rect.topleft)

    knob_r = (h - 6) // 2
    knob_x = (rect.right - 4 - knob_r) if active else (rect.left + 4 + knob_r)
    knob_y = rect.centery

    if active:
        glow_s = pygame.Surface((knob_r * 4, knob_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*accent_on, 60), (knob_r * 2, knob_r * 2), knob_r * 2)
        screen.blit(glow_s, (knob_x - knob_r * 2, knob_y - knob_r * 2))

    pygame.draw.circle(screen, WHITE, (knob_x, knob_y), knob_r)
    pygame.draw.circle(screen, (200, 210, 225), (knob_x, knob_y), knob_r, 1)
    return rect


def _draw_neon_slider(screen, x, y, width, value, label, accent=NEON_CYAN, mx=0, my=0, m_down=False):
    """Draw an audio volume slider."""
    h = 8
    track_rect = pygame.Rect(x, y + 16, width, h)
    thumb_x = x + int(width * value)
    thumb_r = 10
    thumb_rect = pygame.Rect(thumb_x - thumb_r, y + 16 + h // 2 - thumb_r, thumb_r * 2, thumb_r * 2)

    active_rect = track_rect.inflate(40, 60)
    if m_down and active_rect.collidepoint(mx, my):
        value = max(0.0, min(1.0, (mx - x) / width))
        thumb_x = x + int(width * value)
        thumb_rect.centerx = thumb_x

    draw_text(label, FONT_TINY, LIGHT_GRAY, x, y - 2, center=False)
    draw_text(f"{int(value * 100)}%", FONT_TINY, accent, x + width, y - 2, center=False)

    pygame.draw.rect(screen, (25, 30, 45), track_rect, border_radius=h // 2)
    pygame.draw.rect(screen, (50, 60, 80), track_rect, width=1, border_radius=h // 2)

    fill_w = int(width * value)
    if fill_w > 0:
        fill_r = pygame.Rect(x, y + 16, fill_w, h)
        pygame.draw.rect(screen, accent, fill_r, border_radius=h // 2)

    pygame.draw.circle(screen, WHITE, (thumb_x, y + 16 + h // 2), thumb_r)
    pygame.draw.circle(screen, accent, (thumb_x, y + 16 + h // 2), thumb_r, 2)
    return value, track_rect


def render_settings(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
                    control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
                    screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    """Clean, non-overlapping settings screen without redundant control mode selection."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    # ── Header ──────────────────────────────────────────────
    draw_text_shadow("GAME SETTINGS", FONT_MSG, NEON_CYAN, 400, 40, shadow_color=(0, 80, 120), offset=2)
    platform_tag = "PC EDITION" if is_pc() else "MOBILE EDITION"
    draw_text(f"// COSMIC CIVIL WAR  ·  {platform_tag} //", FONT_TINY, (100, 160, 220), 400, 68)
    draw_divider(screen, 80, 82, 720, NEON_CYAN, alpha=50)

    next_state = 9

    # ── 1. Visual Quality ──────────────────────────────────
    draw_text("VISUAL QUALITY", FONT_TINY, (120, 150, 190), 90, 96, center=False)

    quality_btns = [
        ("PERFORMANCE", 'low',    NEON_PINK,   pygame.Rect(90,  116, 180, 36)),
        ("BALANCED",    'medium', NEON_GOLD,   pygame.Rect(290, 116, 180, 36)),
        ("CINEMATIC",   'high',   NEON_CYAN,   pygame.Rect(490, 116, 180, 36)),
    ]
    for (qtxt, qval, qcol, qrect) in quality_btns:
        is_h_q = qrect.collidepoint(mx, my)
        active = (visual_quality == qval)
        bg_surf = pygame.Surface((qrect.width, qrect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (*qcol, 60 if active else 20), bg_surf.get_rect(), border_radius=10)
        screen.blit(bg_surf, qrect.topleft)
        bw = 3 if active else 2
        pygame.draw.rect(screen, qcol if active else (60, 70, 90), qrect, width=bw, border_radius=10)
        draw_text(qtxt, FONT_TINY, WHITE if active else LIGHT_GRAY, qrect.centerx, qrect.centery)
        if m_c and is_h_q:
            tap_snd.play()
            visual_quality = qval
            m_c = False

    draw_divider(screen, 90, 168, 710, NEON_CYAN, alpha=30)

    # ── 2. Gameplay Options ────────────────────────────────
    draw_text("GAMEPLAY OPTIONS", FONT_TINY, (120, 150, 190), 90, 182, center=False)

    toggles = [
        ("DAMAGE NUMBERS",  show_damage_enabled,  NEON_GOLD,   90,  210),
        ("AUTO-FIRE",       auto_fire_enabled,     NEON_GREEN,  410, 210),
        ("SCREEN SHAKE",    screen_shake_enabled,  NEON_PINK,   90,  260),
        ("SHOW FPS",        show_fps,              NEON_CYAN,   410, 260),
    ]
    toggle_states = [show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps]

    for i, (tlabel, tval, taccent, tx, ty) in enumerate(toggles):
        row = pygame.Rect(tx - 4, ty - 12, 280, 42)
        row_surf = pygame.Surface((row.width, row.height), pygame.SRCALPHA)
        pygame.draw.rect(row_surf, (*PANEL_MID, 160), row_surf.get_rect(), border_radius=10)
        screen.blit(row_surf, row.topleft)

        draw_text(tlabel, FONT_TINY, LIGHT_GRAY, tx + 12, ty + 9, center=False)

        toggle_cx = tx + 240
        _draw_ios_toggle(screen, toggle_cx, ty + 9, tval, accent_on=taccent, pulse_t=ui_pulse_t)

        if m_c and row.collidepoint(mx, my):
            tap_snd.play()
            toggle_states[i] = not tval
            m_c = False

    show_damage_enabled  = toggle_states[0]
    auto_fire_enabled    = toggle_states[1]
    screen_shake_enabled = toggle_states[2]
    show_fps             = toggle_states[3]

    draw_divider(screen, 90, 316, 710, NEON_CYAN, alpha=30)

    # ── 3. Audio ───────────────────────────────────────────
    draw_text("AUDIO CONFIGURATION", FONT_TINY, (120, 150, 190), 90, 330, center=False)

    music_vol, _ = _draw_neon_slider(screen, 90,  355, 270, music_vol,
                                     "MUSIC VOLUME", accent=NEON_TEAL, mx=mx, my=my, m_down=m_down)
    sfx_vol, _   = _draw_neon_slider(screen, 410, 355, 270, sfx_vol,
                                     "SFX VOLUME",   accent=NEON_AMBER, mx=mx, my=my, m_down=m_down)

    if m_down:
        pygame.mixer.music.set_volume(music_vol)

    draw_divider(screen, 90, 425, 710, NEON_CYAN, alpha=30)

    # ── 4. Account & Navigation Buttons ────────────────────
    btn_bind = pygame.Rect(90, 455, 210, 46)
    is_h_bind = btn_bind.collidepoint(mx, my)

    current_account_type = "guest" if not cloud_sync.current_username else "cloud"
    if current_account_type == "guest":
        draw_plasma_button(screen, "BIND GOOGLE", FONT_SMALL, WHITE, btn_bind,
                           (140, 100, 0), is_h_bind, pulse_t=ui_pulse_t, accent=NEON_GOLD, border_radius=12)
        if m_c and is_h_bind:
            tap_snd.play()
            cloud_sync.login_google_async()
            next_state = -5
            m_c = False
    else:
        draw_plasma_button(screen, "LOGOUT", FONT_SMALL, WHITE, btn_bind,
                           (120, 20, 30), is_h_bind, pulse_t=0, accent=NEON_PINK, border_radius=12)
        if m_c and is_h_bind:
            tap_snd.play()
            cloud_sync.clear_local_session()
            next_state = -3
            m_c = False

    # VIEW CONTROLS BUTTON
    btn_ctrl = pygame.Rect(320, 455, 200, 46)
    is_h_ctrl = btn_ctrl.collidepoint(mx, my)
    draw_plasma_button(screen, "VIEW CONTROLS", FONT_SMALL, WHITE, btn_ctrl,
                       (0, 60, 150), is_h_ctrl, pulse_t=0, accent=NEON_CYAN, border_radius=12)
    if m_c and is_h_ctrl:
        tap_snd.play()
        next_state = 12 if is_mobile() else 11
        m_c = False

    # BACK BUTTON
    btn_back = pygame.Rect(540, 455, 170, 46)
    is_h_back = btn_back.collidepoint(mx, my)
    draw_plasma_button(screen, "< BACK", FONT_SMALL, WHITE, btn_back,
                       (120, 20, 50), is_h_back, pulse_t=0, accent=NEON_PINK, border_radius=12)

    if (m_c and is_h_back) or key_escape:
        tap_snd.play()
        next_state = 3 if settings_from_pause else 0
        m_c = False

    # Safe enforcement of control_type based on platform
    control_type = "MOBILE" if is_mobile() else "PC"

    return (next_state, control_type, visual_quality, show_damage_enabled,
            auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, m_c)