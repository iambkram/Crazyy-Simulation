import pygame
import math
from assets import draw_menu_starfield, draw_text, draw_text_shadow, draw_neon_panel, draw_divider, draw_glowing_button, FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE, NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, NEON_BLUE, RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID, NEON_PURPLE
from settings import WIDTH, HEIGHT

def render_env_select(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, tap_snd, ui_pulse_t, menu_bg, lock_icon, max_galaxy_level, max_nebula_level, max_blackhole_level, env2_unlocked, env3_unlocked, current_selected_env, focused_btn):
    from assets import draw_menu_starfield, draw_badge, draw_text, draw_text_shadow, draw_divider, draw_neon_panel, draw_glowing_button, FONT_MSG, FONT_HUD, FONT_TINY, FONT_UI, NEON_CYAN, NEON_BLUE, NEON_PURPLE, NEON_PINK, NEON_GREEN, WHITE, LIGHT_GRAY, MID_GRAY, RED, PANEL_MID, PANEL_BG
    import math, pygame

    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 190))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)

    draw_text_shadow("SELECT ENVIRONMENT", FONT_MSG, NEON_CYAN, 400, 52, shadow_color=(0,80,120), offset=2)
    draw_text("Choose your combat zone", FONT_TINY, (80, 130, 180), 400, 82)
    draw_divider(screen, 80, 98, 720, NEON_CYAN, alpha=40)

    env2_unlocked = (max_galaxy_level > 30) or env2_unlocked
    env3_unlocked = (max_nebula_level > 30) or env3_unlocked

    envs = [
        (1, "GALAXY SECTOR", "Stellar battlefields", NEON_BLUE, True, max_galaxy_level),
        (2, "NEBULA ZONE", "Purple gas clouds", NEON_PURPLE, env2_unlocked, max_nebula_level),
        (3, "BLACK HOLE", "Singularity hazard", NEON_PINK, env3_unlocked, max_blackhole_level),
    ]
    card_y_positions = [118, 248, 378]

    next_state = 20
    next_click_cooldown = 0
    next_focused = focused_btn

    for idx, (env_id, name, base_sub, accent, unlocked, max_lvl) in enumerate(envs):
        card = pygame.Rect(80, card_y_positions[idx], 640, 112)
        is_selected = (current_selected_env == env_id)
        is_hover = card.collidepoint(mx, my) and unlocked

        if is_hover: next_focused = idx
        is_focused = (next_focused == idx)

        bg_col = PANEL_MID if unlocked else PANEL_BG
        draw_neon_panel(screen, card, accent=accent if unlocked else (70, 30, 40),
                        alpha=230, border_radius=16, border_width=2 if not is_selected else 3, bg=bg_col)

        if is_selected or (is_focused and unlocked):
            pulse_alpha = int(100 + 80 * math.sin(ui_pulse_t * 3))
            pulse_surf = pygame.Surface((card.width + 12, card.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(pulse_surf, (*accent, pulse_alpha), pulse_surf.get_rect(), border_radius=20, width=2)
            screen.blit(pulse_surf, (card.x - 6, card.y - 6))

        col = WHITE if unlocked else (160, 160, 170)
        draw_text(name, FONT_HUD, col, card.x + 100, card.centery - 20, center=False)

        if unlocked:
            draw_text(f"{base_sub}  *  Max Mission: {max_lvl}/40", FONT_TINY, accent, card.x + 102, card.centery + 14, center=False)
        else:
            if env_id == 2:
                req_text = f"COMPLETE 30 GALAXY MISSIONS ({min(30, max_galaxy_level - 1)}/30 COMPLETED)"
            else:
                req_text = f"COMPLETE 30 NEBULA MISSIONS ({min(30, max_nebula_level - 1)}/30 COMPLETED)"
            draw_text(req_text, FONT_TINY, (255, 100, 100), card.x + 102, card.centery + 14, center=False)

        if not unlocked:
            draw_badge(screen, "LOCKED", FONT_TINY, card.right - 80, card.centery, bg_color=(50, 18, 22), text_color=(255, 100, 100), border_color=RED)
        elif is_selected:
            draw_badge(screen, "SELECTED", FONT_TINY, card.right - 82, card.centery, bg_color=(20, 50, 30), text_color=NEON_GREEN, border_color=NEON_GREEN)
        else:
            draw_badge(screen, f"LVL {max_lvl}/40", FONT_TINY, card.right - 72, card.centery, bg_color=PANEL_BG, text_color=accent, border_color=accent)

        if not unlocked:
            lock_sm = pygame.transform.scale(lock_icon, (48, 48))
            screen.blit(lock_sm, (card.x + 24, card.centery - 24))
        else:
            swatch_rect = pygame.Rect(card.x + 22, card.centery - 26, 52, 52)
            pygame.draw.rect(screen, (10, 20, 40), swatch_rect, border_radius=12)
            pygame.draw.rect(screen, accent, swatch_rect, width=2, border_radius=12)
            draw_text(str(env_id), FONT_UI, accent, swatch_rect.centerx, swatch_rect.centery)

        if (m_c and is_hover) or (key_enter and is_focused and unlocked):
            tap_snd.play()
            current_selected_env = env_id
            next_state = 1
            next_click_cooldown = 12
            m_c = False

    if key_down: next_focused = (next_focused + 1) % 4
    if key_up: next_focused = (next_focused - 1) % 4

    btn_back = pygame.Rect(260, 504, 280, 54)
    is_h_back = btn_back.collidepoint(mx, my)
    if is_h_back: next_focused = 3
    is_focused_back = (next_focused == 3) or is_h_back

    draw_glowing_button(screen, "BACK TO MENU", FONT_UI, WHITE, btn_back, NEON_PINK, is_focused_back,
                        border_radius=16, accent=RED, pulse_t=ui_pulse_t)
    if (m_c and is_h_back) or (key_enter and next_focused == 3) or key_escape:
        tap_snd.play()
        next_state = 0
        next_click_cooldown = 12
        m_c = False

    return next_state, current_selected_env, next_click_cooldown, m_c, next_focused


def render_level_select(screen, mx, my, m_c, m_u, key_escape, tap_snd, ui_pulse_t, current_selected_env, galaxy_bg, nebula_bg, blackhole_bg, lock_icon, max_galaxy_level, max_nebula_level, max_blackhole_level, level_scroll_y, is_dragging_missions, max_scroll_y, mouse_y_prev, m_wheel, level_drag_dist):
    if current_selected_env == 1:
        screen.blit(galaxy_bg, (0, 0))
    elif current_selected_env == 2:
        screen.blit(nebula_bg, (0, 0))
    else:
        screen.blit(blackhole_bg, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    env_acc2 = {1: NEON_BLUE, 2: NEON_PURPLE, 3: NEON_PINK}[current_selected_env]
    env_names = {1: "GALAXY SECTOR", 2: "NEBULA ZONE", 3: "BLACKHOLE HORIZON"}
    curr_env_title = env_names.get(current_selected_env, "GALAXY SECTOR")

    draw_text_shadow("MISSIONS", FONT_MSG, NEON_CYAN, 400, 40, shadow_color=(0,60,120), offset=2)
    draw_text(curr_env_title, FONT_SMALL, env_acc2, 400, 75)
    draw_divider(screen, 150, 95, 650, env_acc2, alpha=60)

    grid_x = 100
    grid_y = 120
    cell_size = 90
    spacing = 30
    cols = 5

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
        level_scroll_y += m_wheel * 40
        level_drag_dist += abs(m_wheel * 40)

    level_scroll_y = max(-max_scroll_y, min(0, level_scroll_y))
    mouse_y_prev = my

    max_lvl = max_galaxy_level if current_selected_env == 1 else (max_nebula_level if current_selected_env == 2 else max_blackhole_level)
    
    selected_level = None
    next_state = 1

    for lvl in range(1, 41):
        row = (lvl - 1) // cols
        col = (lvl - 1) % cols
        cx = grid_x + col * (cell_size + spacing)
        cy = grid_y + row * (cell_size + spacing) + level_scroll_y

        if cy < 50 or cy > 520:
            continue

        btn = pygame.Rect(cx, cy, cell_size, cell_size)
        is_h = btn.collidepoint(mx, my)
        is_unlocked = (lvl <= max_lvl)

        border_col = env_acc2 if is_unlocked else MID_GRAY
        bg_c = (border_col[0]//5, border_col[1]//5, border_col[2]//5) if (is_h and is_unlocked) else PANEL_BG

        draw_neon_panel(screen, btn, accent=border_col, alpha=230, border_radius=12, border_width=2 if not is_h else 3, bg=bg_c)

        if is_unlocked:
            draw_text(str(lvl), FONT_UI, WHITE, cx + cell_size//2, cy + cell_size//2)
            if m_u and is_h and level_drag_dist < 10:
                tap_snd.play()
                selected_level = lvl
                next_state = 2
                m_c = False
        else:
            lock_sm = pygame.transform.scale(lock_icon, (32, 32))
            screen.blit(lock_sm, (cx + (cell_size-32)//2, cy + (cell_size-32)//2))

    top_fade = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
    for y in range(100):
        alpha = int(255 * (1 - y/100))
        pygame.draw.line(top_fade, (0, 0, 20, alpha), (0, y), (WIDTH, y))
    screen.blit(top_fade, (0, 0))

    bot_fade = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    for y in range(80):
        alpha = int(255 * (y/80))
        pygame.draw.line(bot_fade, (0, 0, 20, alpha), (0, y), (WIDTH, y))
    screen.blit(bot_fade, (0, 520))

    b_back = pygame.Rect(250, 530, 300, 50)
    is_h_b = b_back.collidepoint(mx, my)
    draw_glowing_button(screen, "BACK", FONT_UI, WHITE, b_back, NEON_PINK, is_h_b, pulse_t=0)

    if (m_u and is_h_b and level_drag_dist < 10) or key_escape:
        tap_snd.play()
        next_state = 20
        m_c = False

    return next_state, selected_level, level_scroll_y, is_dragging_missions, mouse_y_prev, m_c, level_drag_dist
