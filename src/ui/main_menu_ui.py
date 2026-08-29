import pygame
import math
import random
import webbrowser
from settings import (WIDTH, HEIGHT, NEON_CYAN, NEON_PURPLE, NEON_PINK,
                      NEON_BLUE, NEON_GOLD, NEON_GREEN, NEON_ORANGE,
                      WHITE, RED, LIGHT_GRAY, MID_GRAY)
from assets import (FONT_MENU_TITLE, FONT_MENU_SUB, FONT_MENU_CARD_MAIN,
                    FONT_MENU_CARD_DESC, FONT_MENU_TELEMETRY, FONT_TINY,
                    FONT_UI, draw_text, draw_text_shadow, draw_corner_brackets,
                    draw_badge)

# Reusable scratch surfaces for menu performance
_menu_card_surf = pygame.Surface((340, 66), pygame.SRCALPHA)
_hangar_surf = pygame.Surface((396, 440), pygame.SRCALPHA)
_hangar_particles = []


def draw_vector_icon(screen, icon_type, center_x, center_y, color, scale=1.0):
    """Draw crisp pure vector iconography for menu cards."""
    cx, cy = int(center_x), int(center_y)
    
    if icon_type == "campaign":
        pts = [(cx, cy - int(9 * scale)), (cx + int(9 * scale), cy),
               (cx, cy + int(9 * scale)), (cx - int(9 * scale), cy)]
        pygame.draw.polygon(screen, color, pts, 2)
        pygame.draw.circle(screen, color, (cx, cy), max(2, int(3 * scale)))
        
    elif icon_type == "armory":
        pts = [(cx, cy - int(10 * scale)), (cx + int(8 * scale), cy - int(3 * scale)),
               (cx + int(5 * scale), cy + int(9 * scale)), (cx, cy + int(12 * scale)),
               (cx - int(5 * scale), cy + int(9 * scale)), (cx - int(8 * scale), cy - int(3 * scale))]
        pygame.draw.polygon(screen, color, pts, 2)
        pygame.draw.line(screen, color, (cx, cy - int(5 * scale)), (cx, cy + int(6 * scale)), 2)
        
    elif icon_type == "settings":
        pygame.draw.circle(screen, color, (cx, cy), int(7 * scale), 2)
        for i in range(4):
            ang = i * (math.pi / 4)
            tx1 = cx + math.cos(ang) * int(5 * scale)
            ty1 = cy + math.sin(ang) * int(5 * scale)
            tx2 = cx + math.cos(ang) * int(11 * scale)
            ty2 = cy + math.sin(ang) * int(11 * scale)
            pygame.draw.line(screen, color, (int(tx1), int(ty1)), (int(tx2), int(ty2)), 2)
            
    elif icon_type == "multiplayer":
        rect = pygame.Rect(cx - int(7 * scale), cy - int(3 * scale), int(14 * scale), int(12 * scale))
        pygame.draw.rect(screen, color, rect, width=2, border_radius=3)
        pygame.draw.arc(screen, color, (cx - int(5 * scale), cy - int(11 * scale), int(10 * scale), int(12 * scale)),
                        0, math.pi, 2)
        pygame.draw.circle(screen, color, (cx, cy + int(3 * scale)), 2)
        
    elif icon_type == "quit":
        pygame.draw.arc(screen, color, (cx - int(8 * scale), cy - int(8 * scale), int(16 * scale), int(16 * scale)),
                        0.5, math.pi * 2 - 0.5, 2)
        pygame.draw.line(screen, color, (cx, cy - int(9 * scale)), (cx, cy - int(1 * scale)), 2)


def render_main_menu(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
                     tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
                     unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
                     hp_step, speed_step, bullet_step, firerate_step, focused_btn):
    """
    Renders the AAA Sci-Fi Cyberpunk Main Menu.
    Returns: (next_state, focused_btn, running, click_cooldown, m_c, should_logout)
    """
    global _hangar_particles
    
    nav_items = [
        ("DEPLOY CAMPAIGN",     "Sector Conquest • Boss Battles",      "campaign",    NEON_CYAN,                  20),
        ("STARSHIP ARMORY",     "Weapons, Hull & Overclocks",         "armory",      NEON_PURPLE,                6),
        ("TACTICAL SETTINGS",   "Audio, Controls & VFX Performance",  "settings",    NEON_ORANGE,                9),
        ("MULTIPLAYER OPS",     "Classified Fleet Raids (v2.0)",       "multiplayer", (90, 105, 130),             "locked"),
        ("DISCONNECT & EXIT",   "Save Flight Data & Exit",            "quit",        NEON_PINK,                  "quit"),
    ]

    if key_down or key_tab:
        focused_btn = (focused_btn + 1) % len(nav_items)
    if key_up:
        focused_btn = (focused_btn - 1) % len(nav_items)
    if key_escape:
        return 0, focused_btn, False, 12, False, False

    # =========================================================================
    # 1. TOP COMMAND DECK (HEADER)
    # =========================================================================
    profile_name = cloud_sync.current_username or "Guest Pilot"
    if len(profile_name) > 13:
        profile_name = profile_name[:11] + ".."

    prof_card = pygame.Rect(24, 14, 185, 38)
    prof_bg = pygame.Surface((prof_card.width, prof_card.height), pygame.SRCALPHA)
    pygame.draw.rect(prof_bg, (12, 16, 30, 210), prof_bg.get_rect(), border_radius=10)
    pygame.draw.rect(prof_bg, (*NEON_CYAN[:3], 90), prof_bg.get_rect(), width=1, border_radius=10)
    screen.blit(prof_bg, prof_card.topleft)

    dot_glow = int(180 + 75 * math.sin(ui_pulse_t * 3.5))
    pygame.draw.circle(screen, (*NEON_GREEN[:3], dot_glow), (prof_card.x + 16, prof_card.centery - 5), 4)
    pygame.draw.circle(screen, WHITE, (prof_card.x + 16, prof_card.centery - 5), 2)
    draw_text(profile_name, FONT_MENU_SUB, WHITE, prof_card.x + 28, prof_card.centery - 6, center=False)
    draw_text("FLIGHT CDR // ONLINE", FONT_MENU_TELEMETRY, (100, 140, 180), prof_card.x + 28, prof_card.centery + 7, center=False)

    # Title
    title_glow_a = int(70 + 35 * math.sin(ui_pulse_t * 2.0))
    for goff, ga in [(3, title_glow_a // 3), (1, title_glow_a)]:
        ts = FONT_MENU_TITLE.render("CRAZYY SIMULATION", True, NEON_CYAN)
        ts.set_alpha(ga)
        screen.blit(ts, ts.get_rect(center=(WIDTH // 2 + goff, 28)))
    draw_text_shadow("CRAZYY SIMULATION", FONT_MENU_TITLE, WHITE, WIDTH // 2, 28,
                     shadow_color=(0, 40, 80), offset=2)

    sub_text = "//  COSMIC CIVIL WAR  //"
    draw_text(sub_text, FONT_MENU_SUB, NEON_GOLD, WIDTH // 2, 54, center=True)
    pygame.draw.line(screen, (*NEON_CYAN, 80), (WIDTH // 2 - 180, 54), (WIDTH // 2 - 95, 54), 1)
    pygame.draw.line(screen, (*NEON_CYAN, 80), (WIDTH // 2 + 95, 54), (WIDTH // 2 + 180, 54), 1)

    # Credits & Sync
    coin_pill = pygame.Rect(WIDTH - 224, 14, 124, 38)
    coin_bg = pygame.Surface((coin_pill.width, coin_pill.height), pygame.SRCALPHA)
    pygame.draw.rect(coin_bg, (12, 16, 30, 210), coin_bg.get_rect(), border_radius=10)
    pygame.draw.rect(coin_bg, (*NEON_GOLD[:3], 100), coin_bg.get_rect(), width=1, border_radius=10)
    screen.blit(coin_bg, coin_pill.topleft)
    screen.blit(coin_icon, (coin_pill.x + 8, coin_pill.y + 7))
    draw_text(f"{total_coins:,}", FONT_MENU_SUB, NEON_GOLD, coin_pill.x + 36, coin_pill.centery - 6, center=False)
    draw_text("CREDITS (CC)", FONT_MENU_TELEMETRY, (160, 140, 90), coin_pill.x + 36, coin_pill.centery + 7, center=False)

    cloud_pill = pygame.Rect(WIDTH - 92, 14, 68, 38)
    cloud_bg = pygame.Surface((cloud_pill.width, cloud_pill.height), pygame.SRCALPHA)
    pygame.draw.rect(cloud_bg, (12, 16, 30, 210), cloud_bg.get_rect(), border_radius=10)
    pygame.draw.rect(cloud_bg, (*NEON_CYAN[:3], 80), cloud_bg.get_rect(), width=1, border_radius=10)
    screen.blit(cloud_bg, cloud_pill.topleft)
    draw_text("CLOUD", FONT_MENU_TELEMETRY, NEON_CYAN, cloud_pill.centerx, cloud_pill.centery - 6, center=True)
    draw_text("SYNCED", FONT_MENU_TELEMETRY, NEON_GREEN, cloud_pill.centerx, cloud_pill.centery + 7, center=True)

    pygame.draw.line(screen, (30, 45, 75), (24, 70), (WIDTH - 24, 70), 1)

    # =========================================================================
    # 2. LEFT NAVIGATION CONSOLE (CYBER GLASS CARDS)
    # =========================================================================
    card_y = 85
    card_w = 340
    card_h = 66
    card_gap = 10
    
    target_state = 0
    should_quit = False
    
    for idx, (title, sub, icon_t, accent_col, target) in enumerate(nav_items):
        cur_y = card_y + idx * (card_h + card_gap)
        card_rect = pygame.Rect(24, cur_y, card_w, card_h)
        
        is_hover = card_rect.collidepoint(mx, my)
        is_focused = (idx == focused_btn)
        
        if is_hover and target != "locked":
            focused_btn = idx
            
        active = (is_hover or is_focused) and target != "locked"
        
        slide_ox = 6 if active else 0
        render_rect = pygame.Rect(card_rect.x + slide_ox, card_rect.y, card_rect.width - slide_ox, card_rect.height)
        
        _menu_card_surf.fill((0, 0, 0, 0))
        bg_alpha = 240 if active else 190
        card_fill = (18, 24, 44, bg_alpha) if active else (10, 14, 26, bg_alpha)
        border_col = (*accent_col[:3], 230 if active else 90)
        
        pygame.draw.rect(_menu_card_surf, card_fill, _menu_card_surf.get_rect(), border_radius=12)
        pygame.draw.rect(_menu_card_surf, border_col, _menu_card_surf.get_rect(), width=2 if active else 1, border_radius=12)
        
        stripe_h = _menu_card_surf.get_height() if active else 28
        stripe_y = (_menu_card_surf.get_height() - stripe_h) // 2
        pygame.draw.rect(_menu_card_surf, accent_col, (0, stripe_y, 4 if active else 3, stripe_h), border_radius=2)
        
        if active:
            scan_y = int((ui_pulse_t * 60) % card_h)
            pygame.draw.line(_menu_card_surf, (*accent_col[:3], 60), (4, scan_y), (card_w - 4, scan_y), 1)
            
        screen.blit(_menu_card_surf, render_rect.topleft)
        
        icon_cx = render_rect.x + 30
        icon_cy = render_rect.centery
        draw_vector_icon(screen, icon_t, icon_cx, icon_cy, accent_col if active else (130, 150, 180), scale=1.0)
        
        title_col = WHITE if active else (220, 230, 245) if target != "locked" else (120, 130, 150)
        desc_col = accent_col if active else (100, 130, 160) if target != "locked" else (80, 90, 110)
        
        draw_text(title, FONT_MENU_CARD_MAIN, title_col, render_rect.x + 56, render_rect.centery - 11, center=False)
        draw_text(sub, FONT_MENU_CARD_DESC, desc_col, render_rect.x + 56, render_rect.centery + 10, center=False)
        
        if target == "locked":
            badge_r = pygame.Rect(render_rect.right - 96, render_rect.centery - 10, 88, 20)
            pygame.draw.rect(screen, (35, 15, 20), badge_r, border_radius=10)
            pygame.draw.rect(screen, (*RED[:3], 180), badge_r, width=1, border_radius=10)
            draw_text("COMING v2.0", FONT_TINY, RED, badge_r.centerx, badge_r.centery)
        elif active:
            draw_text("▶", FONT_MENU_SUB, accent_col, render_rect.right - 18, render_rect.centery)
            
        activated = (m_c and is_hover) or (key_enter and is_focused)
        if activated and target != "locked":
            tap_snd.play()
            if target == "quit":
                should_quit = True
            else:
                target_state = target

    # =========================================================================
    # 3. RIGHT SHIP HANGAR & LIVE TELEMETRY BAY
    # =========================================================================
    hangar_rect = pygame.Rect(380, 85, 396, 440)
    
    _hangar_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(_hangar_surf, (8, 12, 24, 200), _hangar_surf.get_rect(), border_radius=14)
    pygame.draw.rect(_hangar_surf, (*NEON_CYAN[:3], 80), _hangar_surf.get_rect(), width=1, border_radius=14)
    screen.blit(_hangar_surf, hangar_rect.topleft)
    
    draw_corner_brackets(screen, hangar_rect, NEON_CYAN, size=12, width=1)
    
    env_names = {1: "GALAXY SECTOR", 2: "NEBULA EXPANSE", 3: "BLACK HOLE CORE"}
    env_name = env_names.get(current_selected_env, "GALAXY SECTOR")
    draw_text("// ACTIVE STARSHIP HANGAR BAY //", FONT_MENU_TELEMETRY, NEON_CYAN, hangar_rect.centerx, hangar_rect.y + 16)
    draw_text(f"THEATER: {env_name}", FONT_TINY, (120, 150, 190), hangar_rect.centerx, hangar_rect.y + 32)
    
    ship_cx = hangar_rect.centerx
    ship_cy = hangar_rect.y + 155
    pedestal_y = ship_cy + 52
    
    for i in range(3):
        pr_w = int(120 - i * 22)
        pr_h = int(32 - i * 6)
        p_surf = pygame.Surface((pr_w * 2, pr_h * 2), pygame.SRCALPHA)
        p_col = NEON_CYAN if i == 0 else NEON_PURPLE if i == 1 else NEON_BLUE
        pygame.draw.ellipse(p_surf, (*p_col[:3], 90 - i * 20), p_surf.get_rect(), width=1)
        screen.blit(p_surf, (ship_cx - pr_w, pedestal_y - pr_h))
        
    float_y = int(math.sin(ui_pulse_t * 2.8) * 5)
    
    if random.random() < 0.8:
        _hangar_particles.append({
            'x': ship_cx - 12 + random.uniform(-2, 2),
            'y': ship_cy + float_y + 20,
            'vx': random.uniform(-0.5, 0.5),
            'vy': random.uniform(2.5, 6.0),
            'life': 18,
            'max_life': 18,
            'col': random.choice([NEON_CYAN, NEON_BLUE, WHITE])
        })
        _hangar_particles.append({
            'x': ship_cx + 12 + random.uniform(-2, 2),
            'y': ship_cy + float_y + 20,
            'vx': random.uniform(-0.5, 0.5),
            'vy': random.uniform(2.5, 6.0),
            'life': 18,
            'max_life': 18,
            'col': random.choice([NEON_CYAN, NEON_BLUE, WHITE])
        })
        
    for p in _hangar_particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        if p['life'] <= 0:
            _hangar_particles.remove(p)
            continue
        p_frac = p['life'] / p['max_life']
        p_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*p['col'], int(255 * p_frac)), (4, 4), max(1, int(3 * p_frac)))
        screen.blit(p_surf, (int(p['x']) - 4, int(p['y']) - 4), special_flags=pygame.BLEND_ADD)
        
    ship_poly = [
        (ship_cx, ship_cy + float_y - 28),
        (ship_cx + 24, ship_cy + float_y + 18),
        (ship_cx + 12, ship_cy + float_y + 12),
        (ship_cx, ship_cy + float_y + 18),
        (ship_cx - 12, ship_cy + float_y + 12),
        (ship_cx - 24, ship_cy + float_y + 18),
    ]
    ship_wing_l = [(ship_cx - 24, ship_cy + float_y + 18), (ship_cx - 34, ship_cy + float_y + 26), (ship_cx - 10, ship_cy + float_y + 6)]
    ship_wing_r = [(ship_cx + 24, ship_cy + float_y + 18), (ship_cx + 34, ship_cy + float_y + 26), (ship_cx + 10, ship_cy + float_y + 6)]
    
    pygame.draw.polygon(screen, (15, 35, 75), ship_poly)
    pygame.draw.polygon(screen, (20, 45, 95), ship_wing_l)
    pygame.draw.polygon(screen, (20, 45, 95), ship_wing_r)
    pygame.draw.polygon(screen, NEON_CYAN, ship_poly, width=2)
    pygame.draw.polygon(screen, NEON_BLUE, ship_wing_l, width=1)
    pygame.draw.polygon(screen, NEON_BLUE, ship_wing_r, width=1)
    pygame.draw.circle(screen, WHITE, (ship_cx, ship_cy + float_y - 4), 4)
    pygame.draw.circle(screen, NEON_CYAN, (ship_cx, ship_cy + float_y - 4), 7, 1)

    # Telemetry stat grid
    stat_box_y = hangar_rect.y + 265
    pygame.draw.line(screen, (30, 45, 75), (hangar_rect.x + 16, stat_box_y - 12), (hangar_rect.right - 16, stat_box_y - 12), 1)
    
    stats = [
        ("HULL ARMOR",      f"{unlocked_hp} HP",              f"MK-{hp_step + 1}",      NEON_CYAN),
        ("ION THRUST",      f"{unlocked_speed * 10}% SPEED",  f"TIER {speed_step + 1}",  NEON_BLUE),
        ("PLASMA CANNONS",  f"{unlocked_bullets}x BURST",     f"LVL {bullet_step + 1}",  NEON_PURPLE),
        ("RAPID CYCLE",     f"{unlocked_firerate:.1f}s CD",    f"LVL {firerate_step + 1}", NEON_GOLD),
    ]
    
    for i, (label, val, sub_stat, col) in enumerate(stats):
        bx = hangar_rect.x + 18 + (i % 2) * 182
        by = stat_box_y + (i // 2) * 50
        s_rect = pygame.Rect(bx, by, 174, 42)
        
        s_bg = pygame.Surface((s_rect.width, s_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s_bg, (14, 18, 34, 180), s_bg.get_rect(), border_radius=8)
        pygame.draw.rect(s_bg, (*col[:3], 60), s_bg.get_rect(), width=1, border_radius=8)
        screen.blit(s_bg, s_rect.topleft)
        
        draw_text(label, FONT_MENU_TELEMETRY, (120, 140, 170), s_rect.x + 8, s_rect.centery - 8, center=False)
        draw_text(val, FONT_MENU_SUB, WHITE, s_rect.x + 8, s_rect.centery + 7, center=False)
        draw_text(sub_stat, FONT_MENU_TELEMETRY, col, s_rect.right - 8, s_rect.centery, center=False)

    ready_pill = pygame.Rect(hangar_rect.x + 24, hangar_rect.bottom - 34, hangar_rect.width - 48, 22)
    pygame.draw.rect(screen, (10, 30, 20), ready_pill, border_radius=11)
    pygame.draw.rect(screen, (*NEON_GREEN[:3], 120), ready_pill, width=1, border_radius=11)
    draw_text("● ALL SYSTEMS 100% COMBAT READY", FONT_MENU_TELEMETRY, NEON_GREEN, ready_pill.centerx, ready_pill.centery)

    # =========================================================================
    # 4. BOTTOM ACTION DOCK
    # =========================================================================
    btn_logout = pygame.Rect(24, 552, 130, 32)
    is_h_logout = btn_logout.collidepoint(mx, my)
    
    lo_bg = pygame.Surface((btn_logout.width, btn_logout.height), pygame.SRCALPHA)
    pygame.draw.rect(lo_bg, (30, 12, 18, 210) if is_h_logout else (16, 12, 20, 180), lo_bg.get_rect(), border_radius=8)
    pygame.draw.rect(lo_bg, (*RED[:3], 200 if is_h_logout else 80), lo_bg.get_rect(), width=1, border_radius=8)
    screen.blit(lo_bg, btn_logout.topleft)
    draw_text("⎋  LOG OUT", FONT_MENU_SUB, RED if is_h_logout else (220, 120, 130), btn_logout.centerx, btn_logout.centery)
    
    should_logout = False
    if m_c and is_h_logout:
        tap_snd.play()
        should_logout = True

    draw_text("CRAZYY ENGINE  •  v1.0.0  •  CREATED BY @IAMBKRAM", FONT_MENU_TELEMETRY, (70, 95, 130), WIDTH // 2 + 10, 568)

    btn_report = pygame.Rect(WIDTH - 164, 552, 140, 32)
    is_h_report = btn_report.collidepoint(mx, my)
    
    rep_bg = pygame.Surface((btn_report.width, btn_report.height), pygame.SRCALPHA)
    pygame.draw.rect(rep_bg, (12, 24, 38, 210) if is_h_report else (10, 16, 28, 180), rep_bg.get_rect(), border_radius=8)
    pygame.draw.rect(rep_bg, (*NEON_CYAN[:3], 200 if is_h_report else 80), rep_bg.get_rect(), width=1, border_radius=8)
    screen.blit(rep_bg, btn_report.topleft)
    draw_text("🐛  REPORT ISSUES", FONT_MENU_SUB, NEON_CYAN if is_h_report else (120, 180, 220), btn_report.centerx, btn_report.centery)
    
    if m_c and is_h_report:
        tap_snd.play()
        try:
            webbrowser.open("https://github.com/iambkram/Crazyy-Simulation/issues")
        except Exception as e:
            print("Error opening issues page:", e)

    return target_state, focused_btn, not should_quit, 12, False, should_logout
