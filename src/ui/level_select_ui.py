import pygame
import math
from assets import (draw_menu_starfield, draw_text, draw_text_shadow,
                    draw_holographic_panel, draw_neon_panel, draw_divider,
                    draw_plasma_button, draw_glowing_button, draw_badge, draw_corner_brackets,
                    FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE,
                    NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE,
                    RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, NEON_PURPLE,
                    GLASS_WHITE, NEON_TEAL, NEON_AMBER)
from settings import WIDTH, HEIGHT, get_boss_kill_req, get_difficulty


def render_env_select(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down,
                      tap_snd, ui_pulse_t, menu_bg, lock_icon,
                      max_galaxy_level, max_nebula_level, max_blackhole_level,
                      env2_unlocked, env3_unlocked, current_selected_env, focused_btn):
    """Environment selection screen with holographic cards."""
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 195))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("SELECT COMBAT ZONE", FONT_MSG, NEON_CYAN, 400, 48,
                     shadow_color=(0, 80, 120), offset=2)
    draw_text("Choose your battlefield environment", FONT_TINY, (80, 130, 180), 400, 80)
    draw_divider(screen, 80, 96, 720, NEON_CYAN, alpha=50)

    env2_unlocked = (max_galaxy_level > 30) or env2_unlocked
    env3_unlocked = (max_nebula_level > 30) or env3_unlocked

    envs = [
        (1, "GALAXY SECTOR",     "Stellar warfare", "LEVELS 1-40",  NEON_BLUE,   True,           max_galaxy_level,   "*"),
        (2, "NEBULA ZONE",       "Purple gas fields","LEVELS 1-40",  NEON_PURPLE, env2_unlocked,  max_nebula_level,   "@"),
        (3, "BLACKHOLE HORIZON", "Singularity zone", "LEVELS 1-40",  NEON_PINK,   env3_unlocked,  max_blackhole_level, "O"),
    ]
    card_y_positions = [112, 258, 404]

    next_state = 20
    next_click_cooldown = 0
    next_focused = focused_btn

    for idx, (env_id, name, sub, range_txt, accent, unlocked, max_lvl, icon) in enumerate(envs):
        card = pygame.Rect(70, card_y_positions[idx], 660, 125)
        is_selected = (current_selected_env == env_id)
        is_hover = card.collidepoint(mx, my) and unlocked
        if is_hover:
            next_focused = idx
        is_focused = (next_focused == idx)

        # Card panel
        bg_col = PANEL_MID if unlocked else PANEL_BG
        card_accent = accent if unlocked else (60, 30, 40)
        draw_holographic_panel(screen, card, accent=card_accent, alpha=230,
                               border_radius=18, border_width=3 if is_selected else 2,
                               bg=bg_col, show_scanlines=unlocked,
                               show_corners=is_selected or is_focused, pulse_t=ui_pulse_t)

        # Selected / hover pulsing ring
        if is_selected or (is_focused and unlocked):
            pa = int(90 + 70 * math.sin(ui_pulse_t * 3))
            psurf = pygame.Surface((card.width + 16, card.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(psurf, (*accent, pa), psurf.get_rect(), border_radius=22, width=3)
            screen.blit(psurf, (card.x - 8, card.y - 8))

        # Environment icon swatch
        swatch = pygame.Rect(card.x + 20, card.centery - 32, 64, 64)
        swatch_bg = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(swatch_bg, (*card_accent, 60), swatch_bg.get_rect(), border_radius=14)
        pygame.draw.rect(swatch_bg, (*card_accent, 200), swatch_bg.get_rect(), width=2, border_radius=14)
        screen.blit(swatch_bg, swatch.topleft)
        draw_text(icon, FONT_HUD, card_accent if unlocked else (80, 80, 90),
                  swatch.centerx, swatch.centery)

        # Text info
        text_col = WHITE if unlocked else (120, 120, 135)
        draw_text(name, FONT_HUD, text_col, card.x + 105, card.y + 20, center=False)
        draw_text(f"{sub}  ·  {range_txt}", FONT_TINY, card_accent if unlocked else (60, 60, 75),
                  card.x + 107, card.y + 65, center=False)

        if unlocked:
            # Progress bar
            prog_frac = max_lvl / 40.0
            prog_rect = pygame.Rect(card.x + 105, card.y + 90, 280, 8)
            pygame.draw.rect(screen, (30, 35, 50), prog_rect, border_radius=4)
            if max_lvl > 0:
                fill_w = int(280 * prog_frac)
                pygame.draw.rect(screen, accent, pygame.Rect(prog_rect.x, prog_rect.y, fill_w, 8), border_radius=4)
            draw_text(f"Mission {max_lvl}/40", FONT_TINY, accent, prog_rect.right + 35, prog_rect.centery)

            # Status badge
            badge_col = NEON_GREEN if is_selected else accent
            badge_txt = "ACTIVE ZONE" if is_selected else f"LVL {max_lvl}/40"
            draw_badge(screen, badge_txt, FONT_TINY, card.right - 72, card.centery - 10,
                       bg_color=(20, 50, 30) if is_selected else PANEL_BG,
                       text_color=badge_col, border_color=badge_col)
        else:
            # Locked overlay
            lock_sm = pygame.transform.scale(lock_icon, (40, 40))
            screen.blit(lock_sm, (card.right - 70, card.centery - 20))
            req_txt = (f"Complete 30 Galaxy Missions ({min(30, max_galaxy_level - 1)}/30)"
                       if env_id == 2 else
                       f"Complete 30 Nebula Missions ({min(30, max_nebula_level - 1)}/30)")
            draw_text(req_txt, FONT_TINY, (200, 80, 80), card.x + 107, card.centery + 24, center=False)

        if (m_c and is_hover) or (key_enter and is_focused and unlocked):
            tap_snd.play()
            current_selected_env = env_id
            next_state = 1
            next_click_cooldown = 12
            m_c = False

    if key_down:
        next_focused = (next_focused + 1) % 4
    if key_up:
        next_focused = (next_focused - 1) % 4

    btn_back = pygame.Rect(260, 548, 280, 46)
    is_h_back = btn_back.collidepoint(mx, my)
    if is_h_back:
        next_focused = 3
    is_focused_back = (next_focused == 3) or is_h_back

    draw_plasma_button(screen, "BACK TO MENU", FONT_UI, WHITE, btn_back,
                       (140, 20, 50), is_focused_back, border_radius=14,
                       accent=NEON_PINK, pulse_t=ui_pulse_t)

    if (m_c and is_h_back) or (key_enter and next_focused == 3) or key_escape:
        tap_snd.play()
        next_state = 0
        next_click_cooldown = 12
        m_c = False

    return next_state, current_selected_env, next_click_cooldown, m_c, next_focused


def render_level_select(screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t,
                        current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon,
                        max_galaxy_level, max_nebula_level, max_blackhole_level,
                        level_scroll_y, is_dragging_missions, max_scroll_y,
                        mouse_y_prev, m_wheel, level_drag_dist):
    """Level selection grid with rich level cards."""
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
    env_names = {1: "GALAXY SECTOR", 2: "NEBULA ZONE", 3: "BLACKHOLE HORIZON"}
    curr_env = env_names.get(current_selected_env, "GALAXY SECTOR")

    draw_text_shadow("MISSIONS", FONT_MSG, NEON_CYAN, 400, 36, shadow_color=(0, 60, 120), offset=2)
    draw_text(curr_env, FONT_SMALL, env_acc, 400, 66)
    draw_divider(screen, 130, 82, 670, env_acc, alpha=60)

    # Scrolling
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

    if m_wheel != 0:
        level_scroll_y += m_wheel * 45
        level_drag_dist += abs(m_wheel * 45)

    level_scroll_y = max(-max_scroll_y, min(0, level_scroll_y))
    mouse_y_prev = my

    max_lvl = (max_galaxy_level if current_selected_env == 1
               else (max_nebula_level if current_selected_env == 2
                     else max_blackhole_level))

    selected_level = None
    next_state = 1

    # Level grid — 5 columns of cards
    grid_x    = 78
    grid_y    = 105
    cell_w    = 118
    cell_h    = 78
    spacing_x = 10
    spacing_y = 10
    cols      = 5

    # Difficulty tiers for color coding
    tier_colors = {
        1: NEON_GREEN, 2: NEON_TEAL, 3: NEON_CYAN, 4: NEON_BLUE,
        5: NEON_AMBER, 6: NEON_ORANGE, 7: NEON_PINK, 8: (220, 20, 60)
    }

    for lvl in range(1, 41):
        row = (lvl - 1) // cols
        col = (lvl - 1) % cols
        cx = grid_x + col * (cell_w + spacing_x)
        cy = grid_y + row * (cell_h + spacing_y) + int(level_scroll_y)

        if cy + cell_h < 88 or cy > 520:
            continue

        btn = pygame.Rect(cx, cy, cell_w, cell_h)
        is_h = btn.collidepoint(mx, my)
        is_unlocked = (lvl <= max_lvl)

        tier = min((lvl - 1) // 5 + 1, 8)
        card_accent = tier_colors.get(tier, NEON_CYAN) if is_unlocked else (50, 50, 65)

        # Card background
        bg_surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
        if is_unlocked:
            bg_alpha = 230 if is_h else 190
            pygame.draw.rect(bg_surf, (*PANEL_MID, bg_alpha), bg_surf.get_rect(), border_radius=12)
        else:
            pygame.draw.rect(bg_surf, (*PANEL_BG, 160), bg_surf.get_rect(), border_radius=12)
        screen.blit(bg_surf, btn.topleft)

        # Border (thicker + glow on hover)
        bw = 2 if not is_h else 3
        pygame.draw.rect(screen, card_accent if is_unlocked else (40, 45, 60),
                         btn, width=bw, border_radius=12)

        if is_h and is_unlocked:
            draw_corner_brackets(screen, btn, card_accent, size=10, width=2)

        if is_unlocked:
            # Level number
            draw_text(str(lvl), FONT_UI, WHITE, btn.centerx, btn.centery - 10)

            # Difficulty name (tiny)
            diff_names = {1:"NOVICE", 2:"RECRUIT", 3:"VETERAN", 4:"ELITE",
                          5:"CMDR", 6:"OVERLORD", 7:"LEGEND", 8:"MYTHIC"}
            draw_text(diff_names.get(tier, "?"), FONT_TINY, card_accent,
                      btn.centerx, btn.centery + 14)

            # Star rating indicator (mini 3-star)
            for si in range(3):
                star_col = NEON_GOLD if is_unlocked else (50, 50, 50)
                pygame.draw.circle(screen, star_col,
                                   (btn.x + 22 + si * 14, btn.bottom - 12), 4)

            if m_u and is_h and level_drag_dist < 12:
                tap_snd.play()
                selected_level = lvl
                next_state = 2
                m_c = False
        else:
            # Lock icon
            lock_sm = pygame.transform.scale(lock_icon, (30, 30))
            screen.blit(lock_sm, (btn.centerx - 15, btn.centery - 15))

    # Top / bottom fade masks
    top_fade = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
    for fy in range(90):
        a = int(255 * (1 - fy / 90))
        pygame.draw.line(top_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(top_fade, (0, 0))

    bot_fade = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    for fy in range(80):
        a = int(255 * (fy / 80))
        pygame.draw.line(bot_fade, (0, 0, 20, a), (0, fy), (WIDTH, fy))
    screen.blit(bot_fade, (0, 520))

    b_back = pygame.Rect(250, 532, 300, 50)
    is_h_b = b_back.collidepoint(mx, my)
    draw_plasma_button(screen, "< BACK", FONT_UI, WHITE, b_back,
                       (140, 20, 50), is_h_b, pulse_t=0, accent=NEON_PINK, border_radius=14)

    if (m_u and is_h_b and level_drag_dist < 12) or key_escape:
        tap_snd.play()
        next_state = 20
        m_c = False

    return next_state, selected_level, level_scroll_y, is_dragging_missions, mouse_y_prev, m_c, level_drag_dist
