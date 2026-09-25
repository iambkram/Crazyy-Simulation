"""
PC Edition Combat Zone & Mission Selection UI.
High-density desktop grid with mouse wheel navigation, keyboard hotkeys,
and guaranteed click-through immunity.
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


def render_env_select_pc(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
                         tap_snd, ui_pulse_t, menu_bg, lock_icon,
                         max_galaxy_level, max_nebula_level, max_blackhole_level,
                         env2_unlocked, env3_unlocked, current_selected_env, focused_btn):
    """PC Combat Zone selection with tactical holographic cards."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("SELECT COMBAT ZONE", FONT_MSG, NEON_CYAN, 400, 48,
                     shadow_color=(0, 80, 120), offset=2)
    draw_text("// CHOOSE YOUR THEATER OF OPERATIONS  ·  [PC TACTICAL] //", FONT_TINY, (100, 160, 220), 400, 80)
    draw_divider(screen, 80, 96, 720, NEON_CYAN, alpha=50)

    env2_unlocked = (max_galaxy_level > 30) or env2_unlocked
    env3_unlocked = (max_nebula_level > 30) or env3_unlocked

    envs = [
        (1, "GALAXY SECTOR",     "Deep-space starfield warfare",     "LEVELS 1-40",  NEON_BLUE,   True,           max_galaxy_level,   "[1]"),
        (2, "NEBULA EXPANSE",    "Dense ionized purple gas fields",  "LEVELS 1-40",  NEON_PURPLE, env2_unlocked,  max_nebula_level,   "[2]"),
        (3, "BLACK HOLE CORE",   "Singularity event horizon hazard", "LEVELS 1-40",  NEON_PINK,   env3_unlocked,  max_blackhole_level, "[3]"),
    ]
    card_y_positions = [112, 256, 400]

    next_state = 20
    next_focused = focused_btn

    keys = pygame.key.get_pressed()
    if keys[pygame.K_1]:
        current_selected_env = 1
        next_state = 1
    elif keys[pygame.K_2] and env2_unlocked:
        current_selected_env = 2
        next_state = 1
    elif keys[pygame.K_3] and env3_unlocked:
        current_selected_env = 3
        next_state = 1

    for idx, (env_id, name, sub, range_txt, accent, unlocked, max_lvl, hotkey) in enumerate(envs):
        card = pygame.Rect(70, card_y_positions[idx], 660, 126)
        is_selected = (current_selected_env == env_id)

        # Protected click handling
        card_clicked, is_hover, _ = ui_manager.button(
            screen, f"pc_env_{env_id}", card, "",
            is_mobile=False, accent=accent if unlocked else (60, 40, 50),
            base_color=PANEL_MID if unlocked else PANEL_BG,
            enabled=unlocked, border_radius=18
        )
        if is_hover and unlocked:
            next_focused = idx

        is_focused = (next_focused == idx)

        # Content inside card
        text_col = WHITE if unlocked else (120, 120, 135)
        draw_text(name, FONT_HUD, text_col, card.x + 36, card.y + 22, center=False)
        draw_text(f"{sub}  ·  {range_txt}", FONT_TINY, accent if unlocked else (70, 70, 85),
                  card.x + 38, card.y + 66, center=False)

        if unlocked:
            prog_frac = min(1.0, max_lvl / 40.0)
            prog_rect = pygame.Rect(card.x + 38, card.y + 92, 340, 8)
            pygame.draw.rect(screen, (25, 30, 45), prog_rect, border_radius=4)
            if max_lvl > 0:
                fill_w = int(prog_rect.width * prog_frac)
                pygame.draw.rect(screen, accent, pygame.Rect(prog_rect.x, prog_rect.y, fill_w, 8), border_radius=4)
            draw_text(f"Mission {max_lvl}/40", FONT_TINY, accent, prog_rect.right + 45, prog_rect.centery)

            badge_col = NEON_GREEN if is_selected else accent
            badge_txt = "ACTIVE ZONE" if is_selected else f"MAX LVL {max_lvl}"
            draw_badge(screen, badge_txt, FONT_TINY, card.right - 80, card.centery - 12,
                       bg_color=(15, 45, 25) if is_selected else PANEL_BG,
                       text_color=badge_col, border_color=badge_col)
            draw_badge(screen, hotkey, FONT_TINY, card.right - 80, card.centery + 18,
                       bg_color=(10, 14, 25), text_color=accent, border_color=accent)
        else:
            lock_sm = pygame.transform.scale(lock_icon, (36, 36))
            screen.blit(lock_sm, (card.right - 70, card.centery - 18))
            req_txt = (f"Complete 30 Galaxy Missions ({min(30, max_galaxy_level - 1)}/30)"
                       if env_id == 2 else
                       f"Complete 30 Nebula Missions ({min(30, max_nebula_level - 1)}/30)")
            draw_text(req_txt, FONT_TINY, RED, card.x + 38, card.centery + 24, center=False)

        if card_clicked or (key_enter and is_focused and unlocked):
            current_selected_env = env_id
            next_state = 1
            ui_manager.notify_state_change(1)

    if key_down:
        next_focused = (next_focused + 1) % 4
    if key_up:
        next_focused = (next_focused - 1) % 4

    # Back to Menu button
    btn_back = pygame.Rect(260, 542, 280, 44)
    back_clicked, is_h_b, _ = ui_manager.button(
        screen, "pc_env_back", btn_back, "< BACK TO MAIN MENU",
        is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
        hotkey_text="[ESC]", border_radius=14
    )

    if back_clicked or (key_enter and next_focused == 3) or key_escape:
        next_state = 0
        ui_manager.notify_state_change(0)

    return next_state, current_selected_env, 14 if next_state != 20 else 0, False, next_focused


def render_level_select_pc(screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
                           current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
                           max_galaxy_level, max_nebula_level, max_blackhole_level,
                           level_scroll_y, is_dragging_missions, max_scroll_y,
                           mouse_y_prev, m_wheel, level_drag_dist):
    """PC Mission selection grid with smooth mousewheel scrolling and protected clicks."""
    # Background
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

    draw_text_shadow("MISSION CONTROL", FONT_MSG, NEON_CYAN, 400, 36, shadow_color=(0, 60, 120), offset=2)
    draw_text(f"// THEATER: {curr_env}  ·  SELECT AN OPERATION //", FONT_SMALL, env_acc, 400, 66)
    draw_divider(screen, 130, 82, 670, env_acc, alpha=60)

    # Mouse wheel smooth scroll
    if m_wheel != 0:
        level_scroll_y += m_wheel * 50

    # Drag scrolling
    m_down = pygame.mouse.get_pressed()[0]
    if m_down:
        if not is_dragging_missions:
            is_dragging_missions = True
            level_drag_dist = 0
        else:
            dy = my - mouse_y_prev
            level_scroll_y += dy
            level_drag_dist += abs(dy)
    else:
        is_dragging_missions = False

    level_scroll_y = max(-max_scroll_y, min(0, level_scroll_y))
    mouse_y_prev = my

    max_lvl = (max_galaxy_level if current_selected_env == 1
               else (max_nebula_level if current_selected_env == 2
                     else max_blackhole_level))

    selected_level = None
    next_state = 1

    # 5-Column Grid
    grid_x    = 78
    grid_y    = 105
    cell_w    = 118
    cell_h    = 78
    spacing_x = 10
    spacing_y = 10
    cols      = 5

    tier_colors = {
        1: NEON_GREEN, 2: NEON_TEAL, 3: NEON_CYAN, 4: NEON_BLUE,
        5: NEON_AMBER, 6: NEON_ORANGE, 7: NEON_PINK, 8: (220, 20, 60)
    }

    for lvl in range(1, 41):
        row = (lvl - 1) // cols
        col = (lvl - 1) % cols
        cx = grid_x + col * (cell_w + spacing_x)
        cy = grid_y + row * (cell_h + spacing_y) + int(level_scroll_y)

        # Clip vertically to view window
        if cy + cell_h < 88 or cy > 516:
            continue

        btn = pygame.Rect(cx, cy, cell_w, cell_h)
        is_unlocked = (lvl <= max_lvl)
        tier = min((lvl - 1) // 5 + 1, 8)
        card_accent = tier_colors.get(tier, NEON_CYAN) if is_unlocked else (50, 50, 65)

        # Protected interactive button
        clicked, is_h, _ = ui_manager.button(
            screen, f"pc_lvl_{lvl}", btn, "",
            is_mobile=False, accent=card_accent,
            base_color=PANEL_MID if is_unlocked else PANEL_BG,
            enabled=is_unlocked, border_radius=12
        )

        if is_unlocked:
            draw_text(str(lvl), FONT_UI, WHITE, btn.centerx, btn.centery - 10)
            diff_names = {1:"NOVICE", 2:"RECRUIT", 3:"VETERAN", 4:"ELITE",
                          5:"CMDR", 6:"OVERLORD", 7:"LEGEND", 8:"MYTHIC"}
            draw_text(diff_names.get(tier, "?"), FONT_TINY, card_accent, btn.centerx, btn.centery + 14)

            # 3-star rating display
            for si in range(3):
                star_col = NEON_GOLD if lvl < max_lvl else (60, 65, 80)
                pygame.draw.circle(screen, star_col, (btn.x + 22 + si * 14, btn.bottom - 12), 4)

            if clicked and level_drag_dist < 12:
                selected_level = lvl
                next_state = 2
                ui_manager.notify_state_change(2)
        else:
            lock_sm = pygame.transform.scale(lock_icon, (28, 28))
            screen.blit(lock_sm, (btn.centerx - 14, btn.centery - 14))

    # Top & bottom smooth gradient fade masks
    top_fade = pygame.Surface((WIDTH, 92), pygame.SRCALPHA)
    for fy in range(92):
        a = int(255 * (1 - fy / 92))
        pygame.draw.line(top_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(top_fade, (0, 0))

    bot_fade = pygame.Surface((WIDTH, 84), pygame.SRCALPHA)
    for fy in range(84):
        a = int(255 * (fy / 84))
        pygame.draw.line(bot_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(bot_fade, (0, 516))

    # Back button safely positioned at bottom
    btn_b = pygame.Rect(250, 536, 300, 48)
    back_clicked, _, _ = ui_manager.button(
        screen, "pc_lvl_back", btn_b, "< BACK TO COMBAT ZONES",
        is_mobile=False, accent=NEON_PINK, base_color=(45, 16, 24),
        hotkey_text="[ESC]", border_radius=14
    )

    if back_clicked or key_escape:
        next_state = 20
        ui_manager.notify_state_change(20)

    return next_state, selected_level, level_scroll_y, is_dragging_missions, mouse_y_prev, False, level_drag_dist
