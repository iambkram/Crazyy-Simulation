"""
Combat Zone & Mission Selection UI Dispatcher.
Routes to dedicated PC or Mobile implementations.
"""
from platform_config import is_mobile
from ui.level_select_pc import render_env_select_pc, render_level_select_pc
from ui.level_select_mobile import render_env_select_mobile, render_level_select_mobile


def render_env_select(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
                      tap_snd, ui_pulse_t, menu_bg, lock_icon,
                      max_galaxy_level, max_nebula_level, max_blackhole_level,
                      env2_unlocked, env3_unlocked, current_selected_env, focused_btn):
    """Dispatches Combat Zone selection to PC or Mobile engine."""
    if is_mobile():
        return render_env_select_mobile(
            screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
            tap_snd, ui_pulse_t, menu_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            env2_unlocked, env3_unlocked, current_selected_env, focused_btn
        )
    else:
        return render_env_select_pc(
            screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
            tap_snd, ui_pulse_t, menu_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            env2_unlocked, env3_unlocked, current_selected_env, focused_btn
        )


def render_level_select(screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
                        current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
                        max_galaxy_level, max_nebula_level, max_blackhole_level,
                        level_scroll_y, is_dragging_missions, max_scroll_y,
                        mouse_y_prev, m_wheel, level_drag_dist):
    """Dispatches Mission Selection to PC or Mobile engine."""
    if is_mobile():
        return render_level_select_mobile(
            screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
            current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            level_scroll_y, is_dragging_missions, max_scroll_y,
            mouse_y_prev, m_wheel, level_drag_dist
        )
    else:
        return render_level_select_pc(
            screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
            current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
            max_galaxy_level, max_nebula_level, max_blackhole_level,
            level_scroll_y, is_dragging_missions, max_scroll_y,
            mouse_y_prev, m_wheel, level_drag_dist
        )
