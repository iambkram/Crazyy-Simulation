"""
Main Menu UI Dispatcher.
Seamlessly routes rendering and interaction to the dedicated Mobile or PC engine.
"""
from platform_config import is_mobile
from ui.main_menu_pc import render_main_menu_pc
from ui.main_menu_mobile import render_main_menu_mobile


def render_main_menu(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
                     tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
                     unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
                     hp_step, speed_step, bullet_step, firerate_step, focused_btn):
    """
    Dispatches to dedicated PC Command Deck or Mobile Touch Suite.
    Returns: (target_state, focused_btn, running, click_cooldown, m_c, should_logout)
    """
    if is_mobile():
        return render_main_menu_mobile(
            screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
            tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
            unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
            hp_step, speed_step, bullet_step, firerate_step, focused_btn
        )
    else:
        return render_main_menu_pc(
            screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
            tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
            unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
            hp_step, speed_step, bullet_step, firerate_step, focused_btn
        )
