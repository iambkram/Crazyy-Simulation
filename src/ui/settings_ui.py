"""
Settings UI Dispatcher.
Routes to dedicated PC or Mobile implementations.
"""
from platform_config import is_mobile
from ui.settings_pc import render_settings_pc
from ui.settings_mobile import render_settings_mobile


def render_settings(screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
                    control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
                    screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a):
    """Dispatches Settings rendering to PC or Mobile engine."""
    if is_mobile():
        return render_settings_mobile(
            screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
            control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
            screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a
        )
    else:
        return render_settings_pc(
            screen, mx, my, m_c, m_down, key_escape, tap_snd, ui_pulse_t, menu_bg,
            control_type, visual_quality, show_damage_enabled, auto_fire_enabled,
            screen_shake_enabled, show_fps, settings_from_pause, music_vol, sfx_vol, pulse_a
        )