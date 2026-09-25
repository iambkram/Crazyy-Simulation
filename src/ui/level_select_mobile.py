"""
Mobile Edition Touch & Slide Mission Selection UI.
Ergonomic mobile layout with:
  - Buttery-smooth inertial momentum scrolling
  - Large 72px tactile level cards with 3-star ratings
  - Drag cancellation threshold to prevent accidental clicks while swiping
  - Guaranteed click-through immunity via UIManager
"""
import pygame
import math
from assets import (
    draw_menu_starfield, draw_text, draw_text_shadow,
    draw_holographic_panel, draw_divider, draw_badge,
    draw_corner_brackets, FONT_MSG, FONT_UI, FONT_SMALL,
    FONT_TINY, FONT_HUD, NEON_CYAN, NEON_GOLD, NEON_GREEN,
    NEON_ORANGE, NEON_PINK, NEON_BLUE, RED, WHITE, LIGHT_GRAY,
    MID_GRAY, PANEL_BG, PANEL_MID, NEON_PURPLE, NEON_TEAL, NEON_AMBER
)
from settings import WIDTH, HEIGHT, get_boss_kill_req, get_difficulty
from ui.ui_system import ui_manager


def render_env_select_mobile(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
                            tap_snd, ui_pulse_t, menu_bg, lock_icon,
                            max_galaxy_level, max_nebula_level, max_blackhole_level,
                            env2_unlocked, env3_unlocked, current_selected_env, focused_btn):
    """Mobile Combat Zone Selection with large touch-friendly cards."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("COMBAT ZONES", FONT_MSG, NEON_CYAN, WIDTH // 2, 42,
                     shadow_color=(0, 80, 120), offset=2)
    draw_text("TAP TO SELECT YOUR BATTLEFIELD", FONT_TINY, (110, 170, 230), WIDTH // 2, 74)
    draw_divider(screen, 60, 90, WIDTH - 60, NEON_CYAN, alpha=50)

    env2_unlocked = (max_galaxy_level > 30) or env2_unlocked
    env3_unlocked = (max_nebula_level > 30) or env3_unlocked

    envs = [
        (1, "GALAXY SECTOR",     "Stellar Deep-Space Combat",      "MISSIONS 1-40",  NEON_BLUE,   True,           max_galaxy_level),
        (2, "NEBULA EXPANSE",    "Dense Ionized Plasma Gas",       "MISSIONS 1-40",  NEON_PURPLE, env2_unlocked,  max_nebula_level),
        (3, "BLACK HOLE CORE",   "Singularity Gravitational Field", "MISSIONS 1-40",  NEON_PINK,   env3_unlocked,  max_blackhole_level),
    ]
    card_y_positions = [108, 252, 396]

    next_state = 20

    for idx, (env_id, name, sub, range_txt, accent, unlocked, max_lvl) in enumerate(envs):
        card = pygame.Rect(45, card_y_positions[idx], WIDTH - 90, 128)
        is_selected = (current_selected_env == env_id)

        card_clicked, is_hover, _ = ui_manager.button(
            screen, f"mob_env_{env_id}", card, "",
            is_mobile=True, accent=accent if unlocked else (60, 40, 50),
            base_color=(18, 24, 44) if unlocked else (14, 16, 26),
            enabled=unlocked, border_radius=20
        )

        # Card internal graphics
        text_col = WHITE if unlocked else (120, 120, 135)
        draw_text(name, FONT_HUD, text_col, card.x + 30, card.y + 20, center=False)
        draw_text(f"{sub}  •  {range_txt}", FONT_TINY, accent if unlocked else (70, 70, 85),
                  card.x + 32, card.y + 64, center=False)

        if unlocked:
            prog_frac = min(1.0, max_lvl / 40.0)
            prog_rect = pygame.Rect(card.x + 32, card.y + 92, 380, 10)
            pygame.draw.rect(screen, (25, 30, 45), prog_rect, border_radius=5)
            if max_lvl > 0:
                fill_w = int(prog_rect.width * prog_frac)
                pygame.draw.rect(screen, accent, pygame.Rect(prog_rect.x, prog_rect.y, fill_w, 10), border_radius=5)
            draw_text(f"{max_lvl}/40", FONT_TINY, accent, prog_rect.right + 30, prog_rect.centery)

            badge_col = NEON_GREEN if is_selected else accent
            badge_txt = "ACTIVE" if is_selected else f"LVL {max_lvl}"
            draw_badge(screen, badge_txt, FONT_TINY, card.right - 64, card.centery,
                       bg_color=(15, 45, 25) if is_selected else PANEL_BG,
                       text_color=badge_col, border_color=badge_col, border_radius=14)
        else:
            lock_sm = pygame.transform.scale(lock_icon, (38, 38))
            screen.blit(lock_sm, (card.right - 65, card.centery - 19))
            req_txt = (f"Unlock: Beat 30 Galaxy Missions ({min(30, max_galaxy_level - 1)}/30)"
                       if env_id == 2 else
                       f"Unlock: Beat 30 Nebula Missions ({min(30, max_nebula_level - 1)}/30)")
            draw_text(req_txt, FONT_TINY, RED, card.x + 32, card.centery + 24, center=False)

        if card_clicked:
            current_selected_env = env_id
            next_state = 1
            ui_manager.notify_state_change(1)

    # Large thumb-friendly Back button
    btn_back = pygame.Rect(WIDTH // 2 - 170, 538, 340, 50)
    back_clicked, _, _ = ui_manager.button(
        screen, "mob_env_back", btn_back, "<  BACK TO MENU",
        is_mobile=True, accent=NEON_PINK, base_color=(40, 16, 24),
        font=FONT_UI, border_radius=18
    )

    if back_clicked or key_escape:
        next_state = 0
        ui_manager.notify_state_change(0)

    return next_state, current_selected_env, 14 if next_state != 20 else 0, False, focused_btn


def render_level_select_mobile(screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
                               current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
                               max_galaxy_level, max_nebula_level, max_blackhole_level,
                               level_scroll_y, is_dragging_missions, max_scroll_y,
                               mouse_y_prev, m_wheel, level_drag_dist):
    """
    Mobile Mission Selection with buttery-smooth momentum scrolling, large 72px touch cards,
    and drag threshold to prevent accidental clicks while swiping.
    """
    if current_selected_env == 1:
        screen.blit(galaxy_bg, (0, 0))
    elif current_selected_env == 2:
        screen.blit(nebula_bg, (0, 0))
    else:
        screen.blit(blackhole_bg, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 205))
    screen.blit(overlay, (0, 0))

    env_acc = {1: NEON_BLUE, 2: NEON_PURPLE, 3: NEON_PINK}[current_selected_env]
    env_names = {1: "GALAXY SECTOR", 2: "NEBULA EXPANSE", 3: "BLACK HOLE CORE"}
    curr_env = env_names.get(current_selected_env, "GALAXY SECTOR")

    draw_text_shadow("MISSIONS", FONT_MSG, NEON_CYAN, WIDTH // 2, 34, shadow_color=(0, 60, 120), offset=2)
    draw_text(f"{curr_env}  •  SWIPE TO SCROLL", FONT_TINY, env_acc, WIDTH // 2, 64)
    draw_divider(screen, 80, 78, WIDTH - 80, env_acc, alpha=50)

    # --- TOUCH DRAG WITH MOMENTUM SCROLLING ---
    m_down = pygame.mouse.get_pressed()[0]
    scroll_vel = ui_manager.scroll_velocities.get('mob_missions', 0.0)

    if m_down:
        if not is_dragging_missions:
            is_dragging_missions = True
            level_drag_dist = 0
            ui_manager.scroll_velocities['mob_missions'] = 0.0
        else:
            dy = my - mouse_y_prev
            level_scroll_y += dy
            level_drag_dist += abs(dy)
            # Store instantaneous velocity for momentum
            ui_manager.scroll_velocities['mob_missions'] = dy * 0.8
    else:
        if is_dragging_missions:
            is_dragging_missions = False
        # Apply momentum decay
        if abs(scroll_vel) > 0.1:
            level_scroll_y += scroll_vel
            ui_manager.scroll_velocities['mob_missions'] *= 0.90
        else:
            ui_manager.scroll_velocities['mob_missions'] = 0.0

    if m_wheel != 0:
        level_scroll_y += m_wheel * 50

    # Bounds clamping with smooth elastic resistance
    level_scroll_y = max(-max_scroll_y, min(0, level_scroll_y))
    mouse_y_prev = my

    max_lvl = (max_galaxy_level if current_selected_env == 1
               else (max_nebula_level if current_selected_env == 2
                     else max_blackhole_level))

    selected_level = None
    next_state = 1

    # Mobile 4-Column Layout for comfortable thumb targets
    cols = 4
    cell_w = 142
    cell_h = 76
    spacing_x = 18
    spacing_y = 14
    grid_x = (WIDTH - (cols * cell_w + (cols - 1) * spacing_x)) // 2
    grid_y = 96

    tier_colors = {
        1: NEON_GREEN, 2: NEON_TEAL, 3: NEON_CYAN, 4: NEON_BLUE,
        5: NEON_AMBER, 6: NEON_ORANGE, 7: NEON_PINK, 8: (220, 20, 60)
    }

    for lvl in range(1, 41):
        row = (lvl - 1) // cols
        col = (lvl - 1) % cols
        cx = grid_x + col * (cell_w + spacing_x)
        cy = grid_y + row * (cell_h + spacing_y) + int(level_scroll_y)

        if cy + cell_h < 82 or cy > 520:
            continue

        btn = pygame.Rect(cx, cy, cell_w, cell_h)
        is_unlocked = (lvl <= max_lvl)
        tier = min((lvl - 1) // 5 + 1, 8)
        card_accent = tier_colors.get(tier, NEON_CYAN) if is_unlocked else (45, 45, 60)

        clicked, is_h, _ = ui_manager.button(
            screen, f"mob_lvl_{lvl}", btn, "",
            is_mobile=True, accent=card_accent,
            base_color=PANEL_MID if is_unlocked else PANEL_BG,
            enabled=is_unlocked, border_radius=16
        )

        if is_unlocked:
            draw_text(str(lvl), FONT_HUD, WHITE, btn.centerx, btn.centery - 10)
            diff_names = {1:"NOVICE", 2:"RECRUIT", 3:"VETERAN", 4:"ELITE",
                          5:"CMDR", 6:"OVERLORD", 7:"LEGEND", 8:"MYTHIC"}
            draw_text(diff_names.get(tier, "?"), FONT_TINY, card_accent, btn.centerx, btn.centery + 14)

            # 3-star rating display
            for si in range(3):
                star_col = NEON_GOLD if lvl < max_lvl else (60, 65, 80)
                pygame.draw.circle(screen, star_col, (btn.x + 32 + si * 18, btn.bottom - 12), 4)

            # Drag distance threshold prevents swipe-scrolling from accidentally opening missions!
            if clicked and level_drag_dist < 10:
                selected_level = lvl
                next_state = 2
                ui_manager.notify_state_change(2)
        else:
            lock_sm = pygame.transform.scale(lock_icon, (30, 30))
            screen.blit(lock_sm, (btn.centerx - 15, btn.centery - 15))

    # Top & bottom smooth gradient fade masks
    top_fade = pygame.Surface((WIDTH, 88), pygame.SRCALPHA)
    for fy in range(88):
        a = int(255 * (1 - fy / 88))
        pygame.draw.line(top_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(top_fade, (0, 0))

    bot_fade = pygame.Surface((WIDTH, 82), pygame.SRCALPHA)
    for fy in range(82):
        a = int(255 * (fy / 82))
        pygame.draw.line(bot_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(bot_fade, (0, 518))

    # Large thumb-friendly Back button
    btn_b = pygame.Rect(WIDTH // 2 - 170, 538, 340, 50)
    back_clicked, _, _ = ui_manager.button(
        screen, "mob_lvl_back", btn_b, "<  BACK TO COMBAT ZONES",
        is_mobile=True, accent=NEON_PINK, base_color=(40, 16, 24),
        font=FONT_UI, border_radius=18
    )

    if (back_clicked and level_drag_dist < 10) or key_escape:
        next_state = 20
        ui_manager.notify_state_change(20)

    return next_state, selected_level, level_scroll_y, is_dragging_missions, mouse_y_prev, False, level_drag_dist
