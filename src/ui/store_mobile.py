"""
Mobile Edition Touch & Slide Upgrade Store UI.
Ergonomic thumb layout with:
  - 4 large tactile upgrade cards with clear cost badges and progress bars
  - High-visibility modal popups with oversized 54px touch buttons
  - Guaranteed click-through immunity via UIManager
"""
import pygame
import math
from assets import (
    draw_menu_starfield, draw_text, draw_text_shadow,
    draw_holographic_panel, draw_divider, draw_chromatic_bar,
    draw_badge, draw_corner_brackets, FONT_MSG, FONT_UI,
    FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE,
    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK,
    NEON_BLUE, RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID
)
from settings import WIDTH, HEIGHT
from ui.ui_system import ui_manager, play_sfx


def render_store_mobile(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
                       menu_bg, coin_icon, total_coins,
                       hp_step, speed_step, bullet_step, firerate_step,
                       hp_costs, speed_costs, bullet_costs, firerate_costs,
                       store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate):
    """Mobile Store Main Screen."""
    if menu_bg:
        screen.blit(menu_bg, (0, 0))
    else:
        screen.fill((10, 15, 26))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 192))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("STARSHIP ARMORY", FONT_MSG, NEON_CYAN, WIDTH // 2, 38, shadow_color=(0, 80, 120), offset=2)
    draw_text("TAP ANY MODULE TO UPGRADE YOUR SHIP", FONT_TINY, (110, 170, 230), WIDTH // 2, 68)

    # Credits pill
    coin_panel = pygame.Rect(WIDTH // 2 - 120, 82, 240, 36)
    draw_holographic_panel(screen, coin_panel, accent=NEON_GOLD, alpha=210,
                           border_radius=18, border_width=1, show_corners=False, pulse_t=ui_pulse_t)
    if coin_icon:
        screen.blit(coin_icon, (coin_panel.x + 12, coin_panel.y + 9))
    draw_text(f"{total_coins:,} CC", FONT_UI, NEON_GOLD, coin_panel.centerx + 12, coin_panel.centery)

    draw_divider(screen, 50, 126, WIDTH - 50, NEON_CYAN, alpha=45)

    store_items = [
        ("HULL ARMOR",  "❤",  NEON_GREEN,  50,  138, 'hp', f"{unlocked_hp} HP",
         hp_step,       len(hp_costs),       hp_costs),
        ("ION THRUST",  ">>>", NEON_ORANGE, 410, 138, 'sp', f"{unlocked_speed * 10}%",
         speed_step,    len(speed_costs),    speed_costs),
        ("CANNONS",     "-", NEON_PINK,   50,  268, 'pb', f"{unlocked_bullets}x",
         bullet_step,   len(bullet_costs),   bullet_costs),
        ("OVERCLOCK",   "+", NEON_CYAN,   410, 268, 'fr', f"{unlocked_firerate:.1f}s",
         firerate_step, len(firerate_costs), firerate_costs),
    ]

    next_state = 6
    next_store_selection = store_selection

    for (name, icon, col, card_x, card_y, key, curr_val_str, step, max_steps, costs) in store_items:
        card = pygame.Rect(card_x, card_y, 340, 116)

        card_clicked, is_h, _ = ui_manager.button(
            screen, f"mob_store_{key}", card, "",
            is_mobile=True, accent=col, base_color=(18, 26, 46), border_radius=18
        )

        # Internal card graphics
        # Icon
        icon_rect = pygame.Rect(card.x + 16, card.centery - 24, 48, 48)
        pygame.draw.rect(screen, (*col[:3], 40), icon_rect, border_radius=12)
        pygame.draw.rect(screen, (*col[:3], 180), icon_rect, width=2, border_radius=12)
        draw_text(icon, FONT_HUD, col, icon_rect.centerx, icon_rect.centery)

        # Name & current stat
        draw_text(name, FONT_SMALL, col, card.x + 76, card.y + 20, center=False)
        draw_text(curr_val_str, FONT_HUD, WHITE, card.x + 76, card.y + 42, center=False)

        # Progress bar
        prog_frac = min(1.0, step / max(1, max_steps))
        bar_rect = pygame.Rect(card.x + 76, card.y + 80, 160, 8)
        pygame.draw.rect(screen, (30, 35, 50), bar_rect, border_radius=4)
        if step > 0:
            fill_w = int(bar_rect.width * prog_frac)
            pygame.draw.rect(screen, col, pygame.Rect(bar_rect.x, bar_rect.y, fill_w, 8), border_radius=4)

        # Cost badge
        if step >= max_steps:
            draw_badge(screen, "MAX", FONT_TINY, card.right - 44, card.centery,
                       bg_color=(20, 50, 30), text_color=NEON_GREEN, border_color=NEON_GREEN)
        else:
            next_cost = costs[step] if step < max_steps else None
            if next_cost is not None:
                can_afford = total_coins >= next_cost
                cost_col = NEON_GOLD if can_afford else RED
                draw_badge(screen, f"$ {next_cost:,}", FONT_SMALL, card.right - 50, card.centery,
                           bg_color=(12, 16, 28), text_color=cost_col, border_color=cost_col)

        if card_clicked and not store_selection:
            next_store_selection = key

    # --- UPGRADE DETAIL MODAL ---
    if store_selection:
        pop_ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_ovl.fill((0, 0, 0, 215))
        screen.blit(pop_ovl, (0, 0))

        pop_box = pygame.Rect(110, 110, 580, 380)
        draw_holographic_panel(screen, pop_box, accent=NEON_CYAN, alpha=252, border_radius=24,
                               border_width=2, show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

        desc_map = {
            "hp": ("HULL ARMOR UPGRADE",     "❤", "Reinforce Starship Titanium Armor", "+50 HP",     NEON_GREEN),
            "sp": ("ION THRUST OVERDRIVE",   ">>>", "Boost Sub-Light Thruster Speed",    "+10% Speed", NEON_ORANGE),
            "pb": ("PLASMA CANNONS ARRAY",   "-", "Unlock Additional Plasma Cannon Stream", "+1 Stream",   NEON_PINK),
            "fr": ("WEAPON OVERCLOCK",       "+", "Accelerate Weapon Cooling Cycle Rate", "-0.15s CD",  NEON_CYAN),
        }
        title, d_icon, d_desc, d_bonus, d_col = desc_map.get(store_selection, ("UPGRADE", ">", "", "", NEON_CYAN))

        if store_selection == 'hp':
            cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
        elif store_selection == 'sp':
            cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
        elif store_selection == 'pb':
            cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"
        else:
            cost = firerate_costs[firerate_step] if firerate_step < len(firerate_costs) else "MAX"

        draw_text_shadow(title, FONT_MODAL_TITLE, d_col, 400, 150, shadow_color=(0, 60, 80), offset=2)
        draw_divider(screen, 150, 176, 650, d_col, alpha=60)

        feat = pygame.Rect(140, 192, 520, 68)
        pygame.draw.rect(screen, (22, 28, 48), feat, border_radius=16)
        pygame.draw.rect(screen, (*d_col[:3], 120), feat, width=1, border_radius=16)
        draw_text(d_icon, FONT_HUD, d_col, feat.x + 36, feat.centery)
        draw_text(d_desc, FONT_SMALL, WHITE, feat.x + 72, feat.centery - 10, center=False)
        draw_text(f"Upgrade Benefit: {d_bonus}", FONT_TINY, d_col, feat.x + 74, feat.centery + 12, center=False)

        # Before -> After
        if cost != "MAX":
            step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
            cur_s = step_map.get(store_selection, 0)
            draw_text(f"Upgrade Tier: Level {cur_s}  →  Level {cur_s + 1}", FONT_SMALL, WHITE, 400, 285)

        can_afford = cost != "MAX" and total_coins >= cost
        cost_col2 = NEON_GREEN if can_afford else (RED if cost != "MAX" else MID_GRAY)
        cost_txt2 = f"COST: $ {cost:,} CC" if cost != "MAX" else "ALREADY MAXED OUT"
        draw_text(cost_txt2, FONT_HUD, cost_col2, 400, 325)

        # Large thumb-friendly action buttons (height 52px)
        btn_st_bk = pygame.Rect(140, 388, 245, 52)
        btn_buy   = pygame.Rect(415, 388, 245, 52)

        cancel_clicked, _, _ = ui_manager.button(
            screen, "mob_store_cancel", btn_st_bk, "CANCEL",
            is_mobile=True, accent=NEON_PINK, base_color=(45, 16, 24),
            font=FONT_UI, border_radius=16
        )

        if cost != "MAX":
            buy_clicked, _, _ = ui_manager.button(
                screen, "mob_store_buy", btn_buy, "BUY NOW ✓",
                is_mobile=True, accent=NEON_GREEN if can_afford else MID_GRAY,
                base_color=(15, 60, 30) if can_afford else (35, 35, 45),
                font=FONT_UI, enabled=can_afford, border_radius=16
            )
        else:
            buy_clicked = False

        if cancel_clicked or key_escape:
            next_store_selection = None
            ui_manager.notify_modal_change()
        elif buy_clicked and cost != "MAX":
            if total_coins >= cost:
                next_state = 7
                ui_manager.notify_state_change(7)
            else:
                next_state = 8
                ui_manager.notify_state_change(8)

    # Main Screen Back Button safely placed at y=465 (zero overlap with modal buttons at y=388..440)
    if not store_selection:
        btn_b_m = pygame.Rect(WIDTH // 2 - 170, 465, 340, 52)
        back_clicked, _, _ = ui_manager.button(
            screen, "mob_store_main_back", btn_b_m, "<  BACK TO MAIN MENU",
            is_mobile=True, accent=NEON_PINK, base_color=(40, 16, 24),
            font=FONT_UI, border_radius=18
        )
        if back_clicked or key_escape:
            next_state = 0
            ui_manager.notify_state_change(0)

    if next_store_selection != store_selection and not next_state in (7, 8):
        ui_manager.notify_modal_change()

    return next_state, next_store_selection, 14 if next_state != 6 else 0, False, key_escape, key_enter


def render_store_confirm_mobile(screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
                               total_coins, store_selection,
                               hp_step, speed_step, bullet_step, firerate_step,
                               hp_costs, speed_costs, bullet_costs, firerate_costs):
    """Mobile Confirm Modal with well-spaced large thumb buttons."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(130, 140, 540, 310)
    draw_holographic_panel(screen, box, accent=NEON_GOLD, alpha=252, border_radius=24,
                           border_width=2, show_corners=True, pulse_t=ui_pulse_t)

    draw_text_shadow("CONFIRM UPGRADE?", FONT_MODAL_TITLE, NEON_GOLD, 400, 185, shadow_color=(80, 60, 0), offset=2)
    draw_divider(screen, 180, 212, 620, NEON_GOLD, alpha=60)

    step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
    cost_map = {'hp': hp_costs, 'sp': speed_costs, 'pb': bullet_costs, 'fr': firerate_costs}
    costs = cost_map.get(store_selection, hp_costs)
    step  = step_map.get(store_selection, 0)
    cost  = costs[step] if step < len(costs) else 0

    draw_text(f"Spend  $ {cost:,} CC  to upgrade?", FONT_UI, WHITE, 400, 250)
    draw_text(f"Credits Remaining After: {total_coins - cost:,} CC", FONT_TINY,
              NEON_GREEN if total_coins >= cost else RED, 400, 282)

    b_n = pygame.Rect(160, 350, 220, 56)
    b_y = pygame.Rect(420, 350, 220, 56)

    cancel_clicked, _, _ = ui_manager.button(
        screen, "mob_store_conf_cancel", b_n, "CANCEL",
        is_mobile=True, accent=NEON_PINK, base_color=(45, 16, 24),
        font=FONT_UI, border_radius=18
    )
    confirm_clicked, _, _ = ui_manager.button(
        screen, "mob_store_conf_ok", b_y, "CONFIRM ✓",
        is_mobile=True, accent=NEON_GREEN, base_color=(15, 60, 30),
        font=FONT_UI, border_radius=18
    )

    next_state = 7
    action = None

    if cancel_clicked or key_escape:
        next_state = 6
    elif confirm_clicked or key_enter:
        play_sfx('ui_buy')
        action = {"type": "buy", "cost": cost, "item": store_selection}
        next_state = 6

    return next_state, action, 14 if next_state != 7 else 0, False, key_escape, key_enter


def render_store_error_mobile(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t):
    """Mobile Store Error Modal."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(160, 190, 480, 215)
    draw_holographic_panel(screen, box, accent=RED, alpha=252, border_radius=22,
                           border_width=2, show_corners=True, pulse_t=0)

    draw_text_shadow("NOT ENOUGH COINS", FONT_MODAL_TITLE, RED, 400, 235, shadow_color=(80, 0, 0), offset=2)
    draw_text("Play more missions to earn coins!", FONT_SMALL, LIGHT_GRAY, 400, 275)

    b_ok = pygame.Rect(WIDTH // 2 - 130, 325, 260, 50)
    ok_clicked, _, _ = ui_manager.button(
        screen, "mob_store_err_ok", b_ok, "UNDERSTOOD",
        is_mobile=True, accent=NEON_PINK, base_color=(45, 16, 24),
        font=FONT_UI, border_radius=18
    )

    next_state = 8
    if ok_clicked or key_escape or key_enter:
        next_state = 6

    return next_state, 14 if next_state != 8 else 0, False, key_escape, key_enter
