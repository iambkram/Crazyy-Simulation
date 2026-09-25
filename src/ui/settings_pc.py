"""
PC Edition Tactical Settings UI.
Features:
  - Precision audio volume sliders
  - Visual quality toggles
  - PC keyboard controls overview
  - Guaranteed click-through immunity via UIManager
"""
import pygame
import math
from assets import (
    draw_menu_starfield, draw_text, draw_text_shadow,
    draw_holographic_panel, draw_divider, draw_badge,
    FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD,
    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK,
    NEON_BLUE, RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID,
    NEON_TEAL, NEON_AMBER
)
from settings import WIDTH, HEIGHT
from ui.ui_system import ui_manager, play_sfx
import cloud_sync


def _draw_ios_toggle(screen, cx, cy, active, accent_on=NEON_GREEN, pulse_t=0.0):
    """Draw a smooth pill-shaped toggle switch."""
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
    """Draw an audio volume slider with precision tracking."""
    h = 8
    track_rect = pygame.Rect(x, y + 16, width, h)
    thumb_x = x + int(width * value)
    thumb_r = 10

    active_rect = track_rect.inflate(40, 60)
    if m_down and active_rect.collidepoint(mx, my):
        value = max(0.0, min(1.0, (mx - x) / width))
        thumb_x = x + int(width * value)

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


def render_settings_pc(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
                       control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
                       screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    """PC Settings Screen with protected interactive widgets."""
    if menu_bg:
        screen.blit(menu_bg, (0, 0))
    else:
        screen.fill((10, 15, 26))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("SYSTEM CONFIGURATION", FONT_MSG, NEON_CYAN, 400, 40, shadow_color=(0, 80, 120), offset=2)
    draw_text("// GRAPHICS, AUDIO & FLIGHT TELEMETRY  ·  [PC EDITION] //", FONT_TINY, (100, 160, 220), 400, 68)
    draw_divider(screen, 80, 82, 720, NEON_CYAN, alpha=50)

    next_state = 9

    # 1. Visual Quality
    draw_text("RENDER QUALITY PRESET", FONT_TINY, (120, 150, 190), 90, 96, center=False)
    quality_btns = [
        ("PERFORMANCE", 'low',    NEON_PINK,   pygame.Rect(90,  116, 180, 36)),
        ("BALANCED",    'medium', NEON_GOLD,   pygame.Rect(290, 116, 180, 36)),
        ("CINEMATIC",   'high',   NEON_CYAN,   pygame.Rect(490, 116, 180, 36)),
    ]
    for (qtxt, qval, qcol, qrect) in quality_btns:
        q_clicked, _, _ = ui_manager.button(
            screen, f"pc_qual_{qval}", qrect, qtxt,
            is_mobile=False, accent=qcol,
            base_color=(min(255, qcol[0] // 3), min(255, qcol[1] // 3), min(255, qcol[2] // 3)) if visual_quality == qval else (18, 24, 38),
            text_color=WHITE if visual_quality == qval else LIGHT_GRAY,
            font=FONT_TINY, border_radius=10
        )
        if q_clicked:
            visual_quality = qval

    draw_divider(screen, 90, 168, 710, NEON_CYAN, alpha=30)

    # 2. Gameplay Options
    draw_text("GAMEPLAY & DISPLAY OPTIONS", FONT_TINY, (120, 150, 190), 90, 182, center=False)
    toggles = [
        ("DAMAGE POPUPS",   show_damage_enabled,  NEON_GOLD,   90,  210, "dmg"),
        ("AUTO-FIRING",     auto_fire_enabled,     NEON_GREEN,  410, 210, "auto"),
        ("SCREEN SHAKE",    screen_shake_enabled,  NEON_PINK,   90,  260, "shake"),
        ("FPS TELEMETRY",   show_fps,              NEON_CYAN,   410, 260, "fps"),
    ]
    toggle_states = [show_damage_enabled, auto_fire_enabled, screen_shake_enabled, show_fps]

    for i, (tlabel, tval, taccent, tx, ty, tid) in enumerate(toggles):
        row = pygame.Rect(tx - 4, ty - 12, 280, 42)
        row_clicked, _, _ = ui_manager.button(
            screen, f"pc_tog_{tid}", row, "",
            is_mobile=False, accent=taccent if tval else (50, 60, 80),
            base_color=PANEL_MID, border_radius=10
        )
        draw_text(tlabel, FONT_TINY, LIGHT_GRAY if not tval else WHITE, tx + 12, ty + 9, center=False)
        _draw_ios_toggle(screen, tx + 240, ty + 9, tval, accent_on=taccent, pulse_t=ui_pulse_t)

        if row_clicked:
            toggle_states[i] = not tval

    show_damage_enabled  = toggle_states[0]
    auto_fire_enabled    = toggle_states[1]
    screen_shake_enabled = toggle_states[2]
    show_fps             = toggle_states[3]

    draw_divider(screen, 90, 316, 710, NEON_CYAN, alpha=30)

    # 3. Audio Volume
    draw_text("AUDIO CONFIGURATION", FONT_TINY, (120, 150, 190), 90, 330, center=False)
    music_vol, _ = _draw_neon_slider(screen, 90, 355, 270, music_vol, "MUSIC VOLUME", accent=NEON_TEAL, mx=mx, my=my, m_down=m_down)
    sfx_vol, _   = _draw_neon_slider(screen, 410, 355, 270, sfx_vol, "SFX VOLUME", accent=NEON_AMBER, mx=mx, my=my, m_down=m_down)

    if m_down:
        pygame.mixer.music.set_volume(music_vol)

    draw_divider(screen, 90, 425, 710, NEON_CYAN, alpha=30)

    # 4. Action & Navigation Buttons (Non-overlapping!)
    btn_bind = pygame.Rect(90, 455, 210, 46)
    btn_ctrl = pygame.Rect(320, 455, 200, 46)
    btn_back = pygame.Rect(540, 455, 170, 46)

    is_cloud = bool(cloud_sync.current_username)
    bind_clicked, _, _ = ui_manager.button(
        screen, "pc_set_bind", btn_bind, "LOGOUT" if is_cloud else "BIND GOOGLE",
        is_mobile=False, accent=RED if is_cloud else NEON_GOLD,
        base_color=(36, 14, 20) if is_cloud else (40, 30, 15),
        hotkey_text="", border_radius=12
    )
    if bind_clicked:
        if is_cloud:
            cloud_sync.clear_local_session()
            next_state = -3
        else:
            cloud_sync.login_google_async()
            next_state = -5

    ctrl_clicked, _, _ = ui_manager.button(
        screen, "pc_set_ctrl", btn_ctrl, "KEYBINDS & TIPS",
        is_mobile=False, accent=NEON_CYAN, base_color=(14, 28, 48),
        hotkey_text="[F1]", border_radius=12
    )
    if ctrl_clicked:
        next_state = 11

    back_clicked, _, _ = ui_manager.button(
        screen, "pc_set_back", btn_back, "< BACK",
        is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
        hotkey_text="[ESC]", border_radius=12
    )
    if back_clicked or key_escape:
        next_state = 3 if settings_from_pause else 0

    return (next_state, "PC", visual_quality, show_damage_enabled,
            auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, False)
