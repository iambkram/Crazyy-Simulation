"""
PC Edition Tactical Armory & Upgrade Store UI.
High-density desktop layout with detailed weapon specs, before/after stat comparison bars,
keyboard hotkeys, and guaranteed click-through immunity.
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


def _draw_upgrade_card_pc(screen, card_rect, name, icon, color, curr_val_str,
                          step, max_steps, costs, total_coins, ui_pulse_t, hotkey_txt):
    """Tactical PC Armory upgrade card with holographic telemetry."""
    # Body
    is_hover = card_rect.collidepoint(ui_manager.pointer_pos)
    draw_holographic_panel(screen, card_rect, accent=color if is_hover else (70, 80, 100),
                           alpha=235, border_radius=16, border_width=3 if is_hover else 2,
                           bg=PANEL_MID, show_scanlines=True, show_corners=is_hover, pulse_t=ui_pulse_t)

    # Icon swatch
    icon_rect = pygame.Rect(card_rect.centerx - 20, card_rect.y + 12, 40, 40)
    icon_bg = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.rect(icon_bg, (*color, 50), icon_bg.get_rect(), border_radius=10)
    pygame.draw.rect(icon_bg, (*color, 200), icon_bg.get_rect(), width=2, border_radius=10)
    screen.blit(icon_bg, icon_rect.topleft)
    draw_text(icon, FONT_TINY, color, icon_rect.centerx, icon_rect.centery)

    # Hotkey tag
    draw_badge(screen, hotkey_txt, FONT_TINY, card_rect.right - 24, card_rect.y + 18,
               bg_color=(12, 16, 28), text_color=color, border_color=color)

    # Name
    draw_text(name, FONT_SMALL, color, card_rect.centerx, card_rect.y + 64)
    draw_divider(screen, card_rect.x + 8, card_rect.y + 76, card_rect.right - 8, color, alpha=50)

    # Current value
    draw_text(curr_val_str, FONT_HUD, WHITE, card_rect.centerx, card_rect.y + 100)

    # Progress bar
    prog_frac = min(1.0, step / max(1, max_steps))
    bar_rect = pygame.Rect(card_rect.x + 10, card_rect.y + 128, card_rect.width - 20, 9)
    draw_chromatic_bar(screen, bar_rect, prog_frac, border_radius=4, show_glow=False,
                       color_full=color, color_mid=color, color_low=(60, 70, 90))
    draw_text(f"TIER {step}/{max_steps}", FONT_TINY, LIGHT_GRAY, card_rect.centerx, card_rect.y + 152)

    # MAX badge or Cost
    if step >= max_steps:
        draw_badge(screen, "MAXED", FONT_TINY, card_rect.centerx, card_rect.y + 184,
                   bg_color=(20, 50, 30), text_color=NEON_GREEN, border_color=NEON_GREEN)
    else:
        next_cost = costs[step] if step < max_steps else None
        if next_cost is not None:
            can_afford = total_coins >= next_cost
            cost_col = NEON_GOLD if can_afford else RED
            draw_text(f"$ {next_cost:,} CC", FONT_SMALL, cost_col, card_rect.centerx, card_rect.y + 184)


def render_store_pc(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
                    menu_bg, coin_icon, total_coins,
                    hp_step, speed_step, bullet_step, firerate_step,
                    hp_costs, speed_costs, bullet_costs, firerate_costs,
                    store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate):
    """PC Store Main Screen."""
    if menu_bg:
        screen.blit(menu_bg, (0, 0))
    else:
        screen.fill((10, 15, 26))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 192))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("STARSHIP ARMORY", FONT_MSG, NEON_CYAN, 400, 44, shadow_color=(0, 80, 120), offset=2)
    draw_text("// HULL UPGRADES, WEAPON SYSTEMS & OVERCLOCKS  ·  [PC TACTICAL] //", FONT_TINY, (100, 160, 220), 400, 74)

    # Coin display
    coin_panel = pygame.Rect(WIDTH // 2 - 110, 88, 220, 34)
    draw_holographic_panel(screen, coin_panel, accent=NEON_GOLD, alpha=210,
                           border_radius=17, border_width=1, show_corners=False, pulse_t=ui_pulse_t)
    if coin_icon:
        screen.blit(coin_icon, (coin_panel.x + 10, coin_panel.y + 8))
    draw_text(f"{total_coins:,} CC", FONT_UI, NEON_GOLD, coin_panel.centerx + 10, coin_panel.centery)

    draw_divider(screen, 60, 130, 740, NEON_CYAN, alpha=45)

    store_items = [
        ("HULL ARMOR",  "❤",  NEON_GREEN,  42,  'hp', f"{unlocked_hp} HP",
         hp_step,       len(hp_costs),       hp_costs,       "[1]"),
        ("ION THRUST",  ">>>", NEON_ORANGE, 232, 'sp', f"{unlocked_speed * 10}%",
         speed_step,    len(speed_costs),    speed_costs,    "[2]"),
        ("CANNONS",     "-", NEON_PINK,   422, 'pb', f"{unlocked_bullets}x",
         bullet_step,   len(bullet_costs),   bullet_costs,   "[3]"),
        ("OVERCLOCK",   "+", NEON_CYAN,   612, 'fr', f"{unlocked_firerate:.1f}s",
         firerate_step, len(firerate_costs), firerate_costs, "[4]"),
    ]

    next_state = 6
    next_store_selection = store_selection

    keys = pygame.key.get_pressed()
    if not store_selection:
        if keys[pygame.K_1]: next_store_selection = 'hp'
        elif keys[pygame.K_2]: next_store_selection = 'sp'
        elif keys[pygame.K_3]: next_store_selection = 'pb'
        elif keys[pygame.K_4]: next_store_selection = 'fr'

    for (name, icon, col, card_x, key, curr_val_str, step, max_steps, costs, hk) in store_items:
        card = pygame.Rect(card_x, 148, 168, 224)
        
        # Protected button check
        card_clicked, is_h, _ = ui_manager.button(
            screen, f"pc_store_{key}", card, "",
            is_mobile=False, accent=col, base_color=PANEL_MID, border_radius=16
        )

        _draw_upgrade_card_pc(screen, card, name, icon, col, curr_val_str,
                              step, max_steps, costs, total_coins, ui_pulse_t, hk)

        if card_clicked and not store_selection:
            next_store_selection = key

    # --- UPGRADE DETAIL POPUP ---
    if store_selection:
        pop_ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_ovl.fill((0, 0, 0, 210))
        screen.blit(pop_ovl, (0, 0))

        pop_box = pygame.Rect(130, 115, 540, 360)
        draw_holographic_panel(screen, pop_box, accent=NEON_CYAN, alpha=250, border_radius=22,
                               border_width=2, show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

        desc_map = {
            "hp": ("HULL ARMOR UPGRADE",     "❤", "Reinforce Starship Titanium Hull Armor", "+50 HP",     NEON_GREEN),
            "sp": ("ION THRUSTER OVERDRIVE", ">>>", "Boost Sub-Light Thruster Velocity",     "+10% Speed", NEON_ORANGE),
            "pb": ("PLASMA CANNON ARRAY",    "-", "Unlock Additional Plasma Cannon Stream", "+1 Stream",   NEON_PINK),
            "fr": ("WEAPON OVERCLOCK",       "+", "Accelerate Weapon Cooling and Cycle Rate", "-0.15s CD",  NEON_CYAN),
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

        draw_text_shadow(title, FONT_MODAL_TITLE, d_col, 400, 155, shadow_color=(0, 60, 80), offset=2)
        draw_divider(screen, 175, 180, 625, d_col, alpha=60)

        feat = pygame.Rect(160, 195, 480, 65)
        feat_surf = pygame.Surface((feat.width, feat.height), pygame.SRCALPHA)
        pygame.draw.rect(feat_surf, (*PANEL_MID, 200), feat_surf.get_rect(), border_radius=14)
        pygame.draw.rect(feat_surf, (*d_col, 120), feat_surf.get_rect(), width=1, border_radius=14)
        screen.blit(feat_surf, feat.topleft)

        draw_text(d_icon, FONT_HUD, d_col, feat.x + 40, feat.centery)
        draw_text(d_desc, FONT_SMALL, WHITE, feat.x + 190, feat.centery - 8, center=False)
        draw_text(f"Bonus: {d_bonus}", FONT_TINY, d_col, feat.x + 192, feat.centery + 14, center=False)

        # Before -> After
        if cost != "MAX":
            compare_bg = pygame.Rect(160, 272, 480, 38)
            cs = pygame.Surface((480, 38), pygame.SRCALPHA)
            pygame.draw.rect(cs, (*PANEL_BG, 180), cs.get_rect(), border_radius=10)
            screen.blit(cs, compare_bg.topleft)
            draw_text("Current Tier Level:", FONT_TINY, LIGHT_GRAY, 200, 291, center=False)
            step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
            draw_text(str(step_map.get(store_selection, 0)), FONT_SMALL, WHITE, 360, 291)
            draw_text("→", FONT_SMALL, d_col, 395, 291)
            draw_text(str(step_map.get(store_selection, 0) + 1), FONT_SMALL, NEON_GREEN, 435, 291)

        can_afford = cost != "MAX" and total_coins >= cost
        cost_col2 = NEON_GREEN if can_afford else (RED if cost != "MAX" else MID_GRAY)
        cost_txt2 = f"$  {cost:,} CC" if cost != "MAX" else "⭐  ALREADY MAXED OUT"
        draw_text(cost_txt2, FONT_UI, cost_col2, 400, 328)

        # Action Buttons inside Popup — Protected
        btn_st_bk = pygame.Rect(160, 400, 190, 50)
        btn_buy   = pygame.Rect(450, 400, 190, 50)

        cancel_clicked, _, _ = ui_manager.button(
            screen, "pc_store_cancel", btn_st_bk, "< CANCEL",
            is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
            hotkey_text="[ESC]", border_radius=14
        )
        if cost != "MAX":
            buy_clicked, _, _ = ui_manager.button(
                screen, "pc_store_buy", btn_buy, "BUY NOW ✓",
                is_mobile=False, accent=NEON_GREEN if can_afford else MID_GRAY,
                base_color=(15, 60, 30) if can_afford else (35, 35, 45),
                enabled=can_afford, hotkey_text="[ENTER]", border_radius=14
            )
        else:
            buy_clicked = False

        if cancel_clicked or key_escape:
            next_store_selection = None
            ui_manager.notify_modal_change()
        elif (buy_clicked or (key_enter and can_afford)) and cost != "MAX":
            if total_coins >= cost:
                next_state = 7
                ui_manager.notify_state_change(7)
            else:
                next_state = 8
                ui_manager.notify_state_change(8)

    # Main Screen Back Button safely placed at y=485 so it never collides with popup buttons
    if not store_selection:
        btn_b_m = pygame.Rect(260, 485, 280, 46)
        back_clicked, _, _ = ui_manager.button(
            screen, "pc_store_main_back", btn_b_m, "< BACK TO MAIN MENU",
            is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
            hotkey_text="[ESC]", border_radius=14
        )
        if back_clicked or key_escape:
            next_state = 0
            ui_manager.notify_state_change(0)

    if next_store_selection != store_selection and not next_state in (7, 8):
        ui_manager.notify_modal_change()

    return next_state, next_store_selection, 14 if next_state != 6 else 0, False, key_escape, key_enter


def render_store_confirm_pc(screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
                            total_coins, store_selection,
                            hp_step, speed_step, bullet_step, firerate_step,
                            hp_costs, speed_costs, bullet_costs, firerate_costs):
    """PC Confirm Purchase Modal with non-overlapping button positions."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(148, 150, 504, 290)
    draw_holographic_panel(screen, box, accent=NEON_GOLD, alpha=252, border_radius=22,
                           border_width=2, show_corners=True, pulse_t=ui_pulse_t)

    draw_text_shadow("CONFIRM UPGRADE?", FONT_MODAL_TITLE, NEON_GOLD, 400, 195, shadow_color=(80, 60, 0), offset=2)
    draw_divider(screen, 195, 222, 605, NEON_GOLD, alpha=60)

    step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
    cost_map = {'hp': hp_costs, 'sp': speed_costs, 'pb': bullet_costs, 'fr': firerate_costs}
    costs = cost_map.get(store_selection, hp_costs)
    step  = step_map.get(store_selection, 0)
    cost  = costs[step] if step < len(costs) else 0

    draw_text(f"Authorize transaction of  $ {cost:,} CC ?", FONT_SMALL, WHITE, 400, 258)
    draw_text(f"Remaining Bank Credits: {total_coins - cost:,} CC", FONT_TINY,
              NEON_GREEN if total_coins >= cost else RED, 400, 288)

    # Buttons placed safely with ample spacing
    b_n = pygame.Rect(175, 348, 200, 52)
    b_y = pygame.Rect(425, 348, 200, 52)

    cancel_clicked, _, _ = ui_manager.button(
        screen, "pc_store_conf_cancel", b_n, "CANCEL",
        is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
        hotkey_text="[ESC]", border_radius=14
    )
    confirm_clicked, _, _ = ui_manager.button(
        screen, "pc_store_conf_ok", b_y, "AUTHORIZE ✓",
        is_mobile=False, accent=NEON_GREEN, base_color=(15, 60, 30),
        hotkey_text="[ENTER]", border_radius=14
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


def render_store_error_pc(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t):
    """PC Store Error Modal."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(175, 200, 450, 200)
    draw_holographic_panel(screen, box, accent=RED, alpha=252, border_radius=20,
                           border_width=2, show_corners=True, pulse_t=0)

    draw_text_shadow("INSUFFICIENT CREDITS", FONT_MODAL_TITLE, RED, 400, 245, shadow_color=(80, 0, 0), offset=2)
    draw_text("Complete combat operations to earn more credits!", FONT_SMALL, LIGHT_GRAY, 400, 288)

    b_ok = pygame.Rect(290, 335, 220, 46)
    ok_clicked, _, _ = ui_manager.button(
        screen, "pc_store_err_ok", b_ok, "UNDERSTOOD",
        is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
        hotkey_text="[ENTER]", border_radius=14
    )

    next_state = 8
    if ok_clicked or key_escape or key_enter:
        next_state = 6

    return next_state, 14 if next_state != 8 else 0, False, key_escape, key_enter
