"""
Armory & Upgrade Store UI Dispatcher.
Routes to dedicated PC or Mobile implementations.
"""
from platform_config import is_mobile
from ui.store_pc import render_store_pc, render_store_confirm_pc, render_store_error_pc
from ui.store_mobile import render_store_mobile, render_store_confirm_mobile, render_store_error_mobile


def render_store(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
                 menu_bg, coin_icon, total_coins,
                 hp_step, speed_step, bullet_step, firerate_step,
                 hp_costs, speed_costs, bullet_costs, firerate_costs,
                 store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate):
    """Dispatches Armory Store rendering to PC or Mobile engine."""
    if is_mobile():
        return render_store_mobile(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
            menu_bg, coin_icon, total_coins,
            hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs,
            store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate
        )
    else:
        return render_store_pc(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
            menu_bg, coin_icon, total_coins,
            hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs,
            store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate
        )


def render_store_confirm(screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
                         total_coins, store_selection,
                         hp_step, speed_step, bullet_step, firerate_step,
                         hp_costs, speed_costs, bullet_costs, firerate_costs):
    """Dispatches Store Confirmation Modal to PC or Mobile engine."""
    if is_mobile():
        return render_store_confirm_mobile(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
            total_coins, store_selection,
            hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs
        )
    else:
        return render_store_confirm_pc(
            screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
            total_coins, store_selection,
            hp_step, speed_step, bullet_step, firerate_step,
            hp_costs, speed_costs, bullet_costs, firerate_costs
        )


def render_store_error(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t):
    """Dispatches Store Error Modal to PC or Mobile engine."""
    if is_mobile():
        return render_store_error_mobile(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t)
    else:
        return render_store_error_pc(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t)
