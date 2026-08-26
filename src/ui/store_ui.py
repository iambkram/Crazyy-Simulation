import pygame
import math
from assets import (draw_menu_starfield, draw_text, draw_text_shadow,
                    draw_holographic_panel, draw_neon_panel, draw_divider,
                    draw_chromatic_bar, draw_gradient_bar, draw_badge,
                    draw_plasma_button, draw_glowing_button, draw_corner_brackets,
                    FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE,
                    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE,
                    RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, NEON_TEAL, NEON_AMBER)
from settings import WIDTH, HEIGHT


def _draw_upgrade_card(screen, card_rect, name, icon, color, curr_val_str,
                       step, max_steps, costs, total_coins,
                       is_hovered, is_selected, ui_pulse_t):
    """Draw a premium upgrade card with stat bar, before/after, price."""
    # Card body
    bg_col = PANEL_MID
    accent = color if (is_hovered or is_selected) else (70, 80, 100)
    draw_holographic_panel(screen, card_rect, accent=accent, alpha=235, border_radius=18,
                           border_width=3 if is_selected else 2, bg=bg_col,
                           show_scanlines=True, show_corners=is_selected, pulse_t=ui_pulse_t)

    # Selection pulse ring
    if is_selected:
        pa = int(90 + 70 * math.sin(ui_pulse_t * 3))
        psurf = pygame.Surface((card_rect.width + 14, card_rect.height + 14), pygame.SRCALPHA)
        pygame.draw.rect(psurf, (*color, pa), psurf.get_rect(), border_radius=22, width=3)
        screen.blit(psurf, (card_rect.x - 7, card_rect.y - 7))

    # Icon swatch
    icon_rect = pygame.Rect(card_rect.centerx - 20, card_rect.y + 12, 40, 40)
    icon_bg = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.rect(icon_bg, (*color, 50), icon_bg.get_rect(), border_radius=10)
    pygame.draw.rect(icon_bg, (*color, 200), icon_bg.get_rect(), width=2, border_radius=10)
    screen.blit(icon_bg, icon_rect.topleft)
    draw_text(icon, FONT_TINY, color, icon_rect.centerx, icon_rect.centery)

    # Name
    draw_text(name, FONT_SMALL, color, card_rect.centerx, card_rect.y + 62)
    draw_divider(screen, card_rect.x + 8, card_rect.y + 74, card_rect.right - 8, color, alpha=50)

    # Current value (big)
    draw_text(curr_val_str, FONT_HUD, WHITE, card_rect.centerx, card_rect.y + 98)

    # Upgrade progress bar
    prog_frac = min(1.0, step / max(1, max_steps))
    bar_rect = pygame.Rect(card_rect.x + 10, card_rect.y + 125, card_rect.width - 20, 9)
    draw_chromatic_bar(screen, bar_rect, prog_frac, border_radius=4, show_glow=False,
                       color_full=color, color_mid=color, color_low=(60, 70, 90))
    draw_text(f"{step}/{max_steps}", FONT_TINY, LIGHT_GRAY, card_rect.centerx, card_rect.y + 148)

    # MAX badge
    if step >= max_steps:
        draw_badge(screen, "MAXED", FONT_TINY, card_rect.centerx, card_rect.y + 180,
                   bg_color=(20, 50, 30), text_color=NEON_GREEN, border_color=NEON_GREEN)
        return

    # Cost
    next_cost = costs[step] if step < max_steps else None
    if next_cost is not None:
        can_afford = total_coins >= next_cost
        cost_col = NEON_GOLD if can_afford else RED
        draw_text(f"$ {next_cost}", FONT_SMALL, cost_col, card_rect.centerx, card_rect.y + 180)
        # "Can afford" indicator dot
        dot_col = NEON_GREEN if can_afford else RED
        dot_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, dot_col, (5, 5), 5)
        screen.blit(dot_surf, (card_rect.right - 16, card_rect.y + 8))


def render_store(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t,
                 menu_bg, coin_icon, total_coins,
                 hp_step, speed_step, bullet_step, firerate_step,
                 hp_costs, speed_costs, bullet_costs, firerate_costs,
                 store_selection, unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate):
    """Premium Store UI with holographic upgrade cards."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 192))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("UPGRADE STORE", FONT_MSG, NEON_CYAN, 400, 44, shadow_color=(0, 80, 120), offset=2)

    # Animated coin display
    coin_panel = pygame.Rect(300, 73, 200, 38)
    draw_holographic_panel(screen, coin_panel, accent=NEON_GOLD, alpha=210,
                           border_radius=19, border_width=1, show_corners=False, pulse_t=ui_pulse_t)
    screen.blit(coin_icon, (308, 79))
    draw_text(str(total_coins), FONT_UI, NEON_GOLD, 390, 92)

    draw_divider(screen, 60, 120, 740, NEON_CYAN, alpha=45)

    # Store upgrade items
    store_items = [
        ("MAX HP",    "❤",  NEON_GREEN,  42,  'hp', str(unlocked_hp),
         hp_step,       len(hp_costs),       hp_costs),
        ("SPEED",     ">>>", NEON_ORANGE, 232, 'sp', str(unlocked_speed),
         speed_step,    len(speed_costs),    speed_costs),
        ("BULLETS",   "-", NEON_PINK,   422, 'pb', str(unlocked_bullets),
         bullet_step,   len(bullet_costs),   bullet_costs),
        ("FIRE RATE", "+", NEON_CYAN,   612, 'fr', f"{unlocked_firerate}x",
         firerate_step, len(firerate_costs), firerate_costs),
    ]

    next_state = 6
    next_store_selection = store_selection
    next_click_cooldown = 0

    for (name, icon, col, card_x, key, curr_val_str, step, max_steps, costs) in store_items:
        card = pygame.Rect(card_x, 136, 168, 220)
        is_h = card.collidepoint(mx, my)
        is_sel = (store_selection == key)

        _draw_upgrade_card(screen, card, name, icon, col, curr_val_str,
                           step, max_steps, costs, total_coins,
                           is_h, is_sel, ui_pulse_t)

        if m_c and is_h and not store_selection:
            tap_snd.play()
            next_store_selection = key
            next_click_cooldown = 12
            m_c = False

    # Upgrade detail popup
    if store_selection:
        pop_ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_ovl.fill((0, 0, 0, 210))
        screen.blit(pop_ovl, (0, 0))

        pop_box = pygame.Rect(130, 130, 540, 340)
        draw_holographic_panel(screen, pop_box, accent=NEON_CYAN, alpha=250, border_radius=22,
                               border_width=2, show_scanlines=True, show_corners=True, pulse_t=ui_pulse_t)

        desc_map = {
            "hp": ("MAX HP UPGRADE",     "❤", "Reinforce Starship Hull Armor",        "+50 HP",   NEON_GREEN),
            "sp": ("SPEED UPGRADE",      ">>>","Boost Thruster Output",                 "+1 Speed", NEON_ORANGE),
            "pb": ("BULLET UPGRADE",     "-","Unlock Extra Weapon Stream",            "+1 Stream",NEON_PINK),
            "fr": ("FIRE RATE OVERCLOCK","+", "Overclock Weapon Systems",             "+15% Rate",NEON_CYAN),
        }
        d = desc_map.get(store_selection, ("UPGRADE", ">", "", "", NEON_CYAN))
        title, d_icon, d_desc, d_bonus, d_col = d

        if store_selection == 'hp':
            cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
        elif store_selection == 'sp':
            cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
        elif store_selection == 'pb':
            cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"
        else:
            cost = firerate_costs[firerate_step] if firerate_step < len(firerate_costs) else "MAX"

        draw_text_shadow(title, FONT_MODAL_TITLE, d_col, 400, 172, shadow_color=(0, 60, 80), offset=2)
        draw_divider(screen, 175, 196, 625, d_col, alpha=60)

        # Feature card
        feat = pygame.Rect(160, 208, 480, 65)
        feat_surf = pygame.Surface((feat.width, feat.height), pygame.SRCALPHA)
        pygame.draw.rect(feat_surf, (*PANEL_MID, 200), feat_surf.get_rect(), border_radius=14)
        pygame.draw.rect(feat_surf, (*d_col, 120), feat_surf.get_rect(), width=1, border_radius=14)
        screen.blit(feat_surf, feat.topleft)

        draw_text(d_icon, FONT_HUD, d_col, feat.x + 40, feat.centery)
        draw_text(d_desc, FONT_SMALL, WHITE, feat.x + 200, feat.centery - 8, center=False)
        draw_text(f"Bonus: {d_bonus}", FONT_TINY, d_col, feat.x + 202, feat.centery + 14, center=False)

        # Before → After comparison
        if cost != "MAX":
            compare_bg = pygame.Rect(160, 282, 480, 40)
            cs = pygame.Surface((480, 40), pygame.SRCALPHA)
            pygame.draw.rect(cs, (*PANEL_BG, 180), cs.get_rect(), border_radius=10)
            screen.blit(cs, compare_bg.topleft)
            draw_text("Current Level:", FONT_TINY, LIGHT_GRAY, 200, 302, center=False)
            from settings import hp_costs as hpc
            step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
            draw_text(str(step_map.get(store_selection, 0)), FONT_SMALL, WHITE, 360, 302)
            draw_text("→", FONT_SMALL, d_col, 395, 302)
            draw_text(str(step_map.get(store_selection, 0) + 1), FONT_SMALL, NEON_GREEN, 435, 302)

        # Cost display
        can_afford = cost != "MAX" and total_coins >= cost
        cost_col2 = NEON_GREEN if can_afford else (RED if cost != "MAX" else MID_GRAY)
        cost_txt2 = f"$  {cost} COINS" if cost != "MAX" else "⭐  ALREADY MAXED OUT"
        draw_text(cost_txt2, FONT_UI, cost_col2, 400, 340)

        if cost != "MAX":
            afford_txt = f"You have: {total_coins} coins" + (" ✓" if can_afford else " — not enough")
            draw_text(afford_txt, FONT_TINY, NEON_GREEN if can_afford else RED, 400, 368)

        btn_st_bk = pygame.Rect(160, 395, 185, 52)
        btn_buy   = pygame.Rect(455, 395, 185, 52)
        is_h_bk   = btn_st_bk.collidepoint(mx, my)
        is_h_buy  = btn_buy.collidepoint(mx, my)

        draw_plasma_button(screen, "< BACK", FONT_UI, WHITE, btn_st_bk,
                          (140, 20, 50), is_h_bk, pulse_t=0, accent=NEON_PINK, border_radius=14)
        if cost != "MAX":
            buy_col = (0, 120, 50) if can_afford else (60, 60, 70)
            draw_plasma_button(screen, "BUY NOW ✓", FONT_UI, WHITE, btn_buy,
                              buy_col, is_h_buy, pulse_t=ui_pulse_t,
                              accent=NEON_GREEN if can_afford else MID_GRAY, border_radius=14)

        if m_c or key_escape or key_enter:
            if is_h_bk or key_escape:
                tap_snd.play()
                next_store_selection = None
                next_click_cooldown = 12
                m_c = False
                key_escape = False
            elif (is_h_buy or key_enter) and cost != "MAX":
                if total_coins >= cost:
                    next_state = 7
                else:
                    tap_snd.play()
                    next_state = 8
                next_click_cooldown = 12
                m_c = False
                key_enter = False

    if not store_selection:
        btn_b_m = pygame.Rect(245, 385, 310, 54)
        is_h_bm = btn_b_m.collidepoint(mx, my)
        draw_plasma_button(screen, "< BACK TO MENU", FONT_UI, WHITE, btn_b_m,
                          (140, 20, 50), is_h_bm, border_radius=16,
                          accent=NEON_PINK, pulse_t=ui_pulse_t)
        if (m_c and is_h_bm) or key_escape:
            tap_snd.play()
            next_state = 0
            next_click_cooldown = 12
            m_c = False

    return next_state, next_store_selection, next_click_cooldown, m_c, key_escape, key_enter


def render_store_confirm(screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t,
                         total_coins, store_selection,
                         hp_step, speed_step, bullet_step, firerate_step,
                         hp_costs, speed_costs, bullet_costs, firerate_costs):
    """State 7: Confirm Purchase with animated coin deduction."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(148, 160, 504, 280)
    draw_holographic_panel(screen, box, accent=NEON_GOLD, alpha=252, border_radius=22,
                           border_width=2, show_corners=True, pulse_t=ui_pulse_t)

    draw_text_shadow("CONFIRM UPGRADE?", FONT_MODAL_TITLE, NEON_GOLD, 400, 202,
                     shadow_color=(80, 60, 0), offset=2)
    draw_divider(screen, 195, 226, 605, NEON_GOLD, alpha=60)

    step_map = {'hp': hp_step, 'sp': speed_step, 'pb': bullet_step, 'fr': firerate_step}
    cost_map = {'hp': hp_costs, 'sp': speed_costs, 'pb': bullet_costs, 'fr': firerate_costs}
    costs = cost_map.get(store_selection, hp_costs)
    step  = step_map.get(store_selection, 0)
    cost  = costs[step] if step < len(costs) else 0

    draw_text(f"Spend  $ {cost} coins  to upgrade?", FONT_SMALL, WHITE, 400, 265)
    draw_text(f"Remaining after purchase: {total_coins - cost}", FONT_TINY,
              NEON_GREEN if total_coins >= cost else RED, 400, 295)

    b_n = pygame.Rect(165, 352, 188, 52)
    b_y = pygame.Rect(447, 352, 188, 52)
    is_h_n = b_n.collidepoint(mx, my)
    is_h_y = b_y.collidepoint(mx, my)

    draw_plasma_button(screen, "CANCEL", FONT_UI, WHITE, b_n,
                      (120, 20, 50), is_h_n, pulse_t=0, accent=NEON_PINK, border_radius=14)
    draw_plasma_button(screen, "CONFIRM ✓", FONT_UI, WHITE, b_y,
                      (0, 120, 50), is_h_y, pulse_t=ui_pulse_t, accent=NEON_GREEN, border_radius=14)

    next_state = 7
    action = None
    next_click_cooldown = 0

    if m_c or key_escape or key_enter:
        if is_h_n or key_escape:
            tap_snd.play()
            next_state = 6
            next_click_cooldown = 12
            m_c = False
            key_escape = False
        elif is_h_y or key_enter:
            coin_snd.play()
            action = {"type": "buy", "cost": cost, "item": store_selection}
            next_state = 6
            next_click_cooldown = 12
            m_c = False
            key_enter = False

    return next_state, action, next_click_cooldown, m_c, key_escape, key_enter


def render_store_error(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t):
    """State 8: Not Enough Coins."""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 215))
    screen.blit(pop_overlay, (0, 0))

    box = pygame.Rect(175, 205, 450, 195)
    draw_holographic_panel(screen, box, accent=NEON_PINK, alpha=252, border_radius=20,
                           border_width=2, show_corners=True, pulse_t=0)

    draw_text_shadow("NOT ENOUGH COINS", FONT_MODAL_TITLE, RED, 400, 248,
                     shadow_color=(80, 0, 0), offset=2)
    draw_text("Earn coins by completing missions!", FONT_SMALL, LIGHT_GRAY, 400, 292)
    draw_text("Boss kills give bonus coins *", FONT_TINY, NEON_GOLD, 400, 316)

    b_ok = pygame.Rect(290, 340, 220, 44)
    is_h_ok = b_ok.collidepoint(mx, my)
    draw_plasma_button(screen, "UNDERSTOOD", FONT_UI, WHITE, b_ok,
                      (140, 20, 50), is_h_ok, pulse_t=ui_pulse_t, accent=NEON_PINK, border_radius=14)

    next_state = 8
    next_click_cooldown = 0
    if m_c or key_escape or key_enter:
        if is_h_ok or key_escape or key_enter:
            tap_snd.play()
            next_state = 6
            next_click_cooldown = 12
            m_c = False
            key_escape = False
            key_enter = False

    return next_state, next_click_cooldown, m_c, key_escape, key_enter
