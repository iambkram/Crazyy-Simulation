"""
Mobile Edition Touch & Slide Settings UI.
Ergonomic touch layout featuring:
  - Large 52px tap toggle rows with iOS/Android fluid toggle indicators
  - Finger-friendly volume touch sliders with oversized thumb targets
  - Touch control guide access
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


def _draw_mobile_toggle(screen, cx, cy, active, accent_on=NEON_GREEN, pulse_t=0.0):
    """Draw a large touch-friendly pill toggle switch."""
    w, h = 56, 30
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    bg_col = accent_on if active else (35, 42, 58)

    track = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(track, (*bg_col, 230), track.get_rect(), border_radius=h // 2)
    border_col = accent_on if active else (65, 75, 95)
    pygame.draw.rect(track, border_col, track.get_rect(), width=2, border_radius=h // 2)
    screen.blit(track, rect.topleft)

    knob_r = (h - 6) // 2
    knob_x = (rect.right - 4 - knob_r) if active else (rect.left + 4 + knob_r)
    knob_y = rect.centery

    if active:
        glow_s = pygame.Surface((knob_r * 4, knob_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*accent_on, 80), (knob_r * 2, knob_r * 2), knob_r * 2)
        screen.blit(glow_s, (knob_x - knob_r * 2, knob_y - knob_r * 2))

    pygame.draw.circle(screen, WHITE, (knob_x, knob_y), knob_r)
    return rect


def _draw_mobile_slider(screen, x, y, width, value, label, accent=NEON_CYAN, mx=0, my=0, m_down=False):
    """Draw an oversized finger-friendly audio volume slider."""
    h = 10
    track_rect = pygame.Rect(x, y + 20, width, h)
    thumb_x = x + int(width * value)
    thumb_r = 14  # Large 28px diameter touch target for thumbs

    active_rect = track_rect.inflate(50, 70)
    if m_down and active_rect.collidepoint(mx, my):
        value = max(0.0, min(1.0, (mx - x) / width))
        thumb_x = x + int(width * value)

    draw_text(label, FONT_SMALL, WHITE, x, y - 2, center=False)
    draw_text(f"{int(value * 100)}%", FONT_SMALL, accent, x + width, y - 2, center=False)

    pygame.draw.rect(screen, (22, 28, 42), track_rect, border_radius=h // 2)
    pygame.draw.rect(screen, (50, 60, 80), track_rect, width=1, border_radius=h // 2)

    fill_w = int(width * value)
    if fill_w > 0:
        fill_r = pygame.Rect(x, y + 20, fill_w, h)
        pygame.draw.rect(screen, accent, fill_r, border_radius=h // 2)

    # Large thumb
    pygame.draw.circle(screen, WHITE, (thumb_x, y + 20 + h // 2), thumb_r)
    pygame.draw.circle(screen, accent, (thumb_x, y + 20 + h // 2), thumb_r, 3)
    return value, track_rect


def render_settings_mobile(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
                          control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
                          screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    """Mobile Settings Screen with large touch targets."""
    if menu_bg:
        screen.blit(menu_bg, (0, 0))
    else:
        screen.fill((10, 15, 26))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("SETTINGS", FONT_MSG, NEON_CYAN, WIDTH // 2, 36, shadow_color=(0, 80, 120), offset=2)
    draw_text("MOBILE TOUCH CONFIGURATION", FONT_TINY, (110, 170, 230), WIDTH // 2, 64)
    draw_divider(screen, 60, 78, WIDTH - 60, NEON_CYAN, alpha=50)

    next_state = 9

    # 1. Quality Presets (3 Large Touch Tabs)
    draw_text("GRAPHICS & EFFECTS PERFORMANCE", FONT_TINY, (120, 150, 190), 60, 92, center=False)
    quality_btns = [
        ("FAST (LOW)",   'low',    NEON_PINK,   pygame.Rect(60,  110, 214, 42)),
        ("BALANCED",     'medium', NEON_GOLD,   pygame.Rect(292, 110, 214, 42)),
        ("ULTRA VFX",    'high',   NEON_CYAN,   pygame.Rect(524, 110, 214, 42)),
    ]
    for (qtxt, qval, qcol, qrect) in quality_btns:
        q_clicked, _, _ = ui_manager.button(
            screen, f"mob_qual_{qval}", qrect, qtxt,
            is_mobile=True, accent=qcol,
            base_color=(min(255, qcol[0] // 3), min(255, qcol[1] // 3), min(255, qcol[2] // 3)) if visual_quality == qval else (18, 24, 38),
            text_color=WHITE if visual_quality == qval else LIGHT_GRAY,
            font=FONT_SMALL, border_radius=14
        )
        if q_clicked:
            visual_quality = qval

    draw_divider(screen, 60, 164, WIDTH - 60, NEON_CYAN, alpha=30)

    # 2. Touch Gameplay Options (Large 48px Tap Rows)
    draw_text("TOUCH CONTROLS & HUD", FONT_TINY, (120, 150, 190), 60, 178, center=False)
    toggles = [
        ("AUTO-FIRING MODE", auto_fire_enabled,     NEON_GREEN, 60,  200, "auto"),
        ("DAMAGE NUMBERS",   show_damage_enabled,  NEON_GOLD,  415, 200, "dmg"),
        ("SCREEN VIBRATION", screen_shake_enabled,  NEON_PINK,  60,  256, "shake"),
        ("FPS TELEMETRY",    show_fps,              NEON_CYAN,  415, 256, "fps"),
    ]
    toggle_states = [auto_fire_enabled, show_damage_enabled, screen_shake_enabled, show_fps]

    for i, (tlabel, tval, taccent, tx, ty, tid) in enumerate(toggles):
        row = pygame.Rect(tx, ty - 6, 325, 48)
        row_clicked, _, _ = ui_manager.button(
            screen, f"mob_tog_{tid}", row, "",
            is_mobile=True, accent=taccent if tval else (50, 60, 80),
            base_color=PANEL_MID, border_radius=14
        )
        draw_text(tlabel, FONT_SMALL, WHITE if tval else LIGHT_GRAY, tx + 14, ty + 18, center=False)
        _draw_mobile_toggle(screen, tx + 280, ty + 18, tval, accent_on=taccent, pulse_t=ui_pulse_t)

        if row_clicked:
            toggle_states[i] = not tval

    auto_fire_enabled    = toggle_states[0]
    show_damage_enabled  = toggle_states[1]
    screen_shake_enabled = toggle_states[2]
    show_fps             = toggle_states[3]

    draw_divider(screen, 60, 316, WIDTH - 60, NEON_CYAN, alpha=30)

    # 3. Audio Volume (Large Touch Sliders)
    draw_text("VOLUME CONTROLS", FONT_TINY, (120, 150, 190), 60, 330, center=False)
    music_vol, _ = _draw_mobile_slider(screen, 60,  350, 310, music_vol, "MUSIC VOLUME", accent=NEON_TEAL, mx=mx, my=my, m_down=m_down)
    sfx_vol, _   = _draw_mobile_slider(screen, 425, 350, 310, sfx_vol,   "SFX VOLUME",   accent=NEON_AMBER, mx=mx, my=my, m_down=m_down)

    if m_down:
        pygame.mixer.music.set_volume(music_vol)

    draw_divider(screen, 60, 420, WIDTH - 60, NEON_CYAN, alpha=30)

    # 4. Large Thumb Action Buttons (Height 52px)
    btn_bind = pygame.Rect(60, 442, 214, 52)
    btn_ctrl = pygame.Rect(292, 442, 214, 52)
    btn_back = pygame.Rect(524, 442, 214, 52)

    is_cloud = bool(cloud_sync.current_username)
    bind_clicked, _, _ = ui_manager.button(
        screen, "mob_set_bind", btn_bind, "LOG OUT" if is_cloud else "LINK ACCOUNT",
        is_mobile=True, accent=RED if is_cloud else NEON_GOLD,
        base_color=(36, 14, 20) if is_cloud else (40, 30, 15),
        font=FONT_SMALL, border_radius=16
    )
    if bind_clicked:
        if is_cloud:
            cloud_sync.clear_local_session()
            next_state = -3
        else:
            cloud_sync.login_google_async()
            next_state = -5

    ctrl_clicked, _, _ = ui_manager.button(
        screen, "mob_set_ctrl", btn_ctrl, "TOUCH COMMANDS",
        is_mobile=True, accent=NEON_CYAN, base_color=(14, 28, 48),
        font=FONT_SMALL, border_radius=16
    )
    if ctrl_clicked:
        next_state = 12

    back_clicked, _, _ = ui_manager.button(
        screen, "mob_set_back", btn_back, "<  BACK",
        is_mobile=True, accent=NEON_PINK, base_color=(45, 16, 24),
        font=FONT_SMALL, border_radius=16
    )
    if back_clicked or key_escape:
        next_state = 3 if settings_from_pause else 0

    return (next_state, "MOBILE", visual_quality, show_damage_enabled,
            auto_fire_enabled, screen_shake_enabled, show_fps, music_vol, sfx_vol, False)
