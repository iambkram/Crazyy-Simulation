"""
PC Edition Tactical Cyberpunk Main Menu UI.
High-density desktop layout featuring:
  - Tactical navigation cards with keyboard hotkey pill badges
  - Live starship hangar bay with procedural 3D-perspective plasma thrusters
  - Real-time telemetry cards and system combat readiness monitor
  - Zero click-through immunity via UIManager
"""
import pygame
import math
import random
import webbrowser
from settings import (
    WIDTH, HEIGHT, NEON_CYAN, NEON_PURPLE, NEON_PINK,
    NEON_BLUE, NEON_GOLD, NEON_GREEN, NEON_ORANGE,
    WHITE, RED, LIGHT_GRAY, MID_GRAY
)
from assets import (
    FONT_MENU_TITLE, FONT_MENU_SUB, FONT_MENU_CARD_MAIN,
    FONT_MENU_CARD_DESC, FONT_MENU_TELEMETRY, FONT_TINY,
    FONT_UI, draw_text, draw_text_shadow, draw_corner_brackets,
    draw_badge
)
from ui.ui_system import ui_manager

_hangar_surf = pygame.Surface((408, 460), pygame.SRCALPHA)
_hangar_particles = []


def draw_vector_icon(screen, icon_type, center_x, center_y, color, scale=1.0):
    """Crisp vector iconography for PC command deck."""
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
    elif icon_type == "chevron":
        pts = [(cx - int(4 * scale), cy - int(6 * scale)),
               (cx + int(3 * scale), cy),
               (cx - int(4 * scale), cy + int(6 * scale))]
        pygame.draw.lines(screen, color, False, pts, 2)


def render_main_menu_pc(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
                        tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
                        unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
                        hp_step, speed_step, bullet_step, firerate_step, focused_btn):
    """
    Renders Desktop PC Command Deck UI with high-precision telemetry, keyboard hotkeys,
    and guaranteed click-through immunity.
    """
    global _hangar_particles

    nav_items = [
        ("DEPLOY CAMPAIGN",     "Sector Conquest • Boss Battles",      "campaign",    NEON_CYAN,   "[1]",       20),
        ("STARSHIP ARMORY",     "Weapons, Hull & Overclocks",         "armory",      NEON_PURPLE, "[2]",       6),
        ("TACTICAL SETTINGS",   "Audio, Controls & VFX Performance",  "settings",    NEON_ORANGE, "[3]",       9),
        ("MULTIPLAYER OPS",     "Classified Fleet Raids (v2.0)",       "multiplayer", (90, 105, 130), "[v2]",  "locked"),
        ("DISCONNECT & EXIT",   "Save Flight Data & Exit",            "quit",        NEON_PINK,   "[Q]",       "quit"),
    ]

    keys = pygame.key.get_pressed()
    # Direct numeric hotkeys for PC
    if keys[pygame.K_1]:
        focused_btn = 0
        key_enter = True
    elif keys[pygame.K_2]:
        focused_btn = 1
        key_enter = True
    elif keys[pygame.K_3]:
        focused_btn = 2
        key_enter = True
    elif keys[pygame.K_q]:
        focused_btn = 4
        key_enter = True

    if key_down or key_tab:
        focused_btn = (focused_btn + 1) % len(nav_items)
    if key_up:
        focused_btn = (focused_btn - 1) % len(nav_items)
    if key_escape:
        return 0, focused_btn, False, 14, False, False

    # 1. TOP HEADER BAR
    prof_name = cloud_sync.current_username or "Guest Pilot"
    if len(prof_name) > 11:
        prof_name = prof_name[:9] + ".."

    prof_card = pygame.Rect(16, 12, 164, 40)
    prof_bg = pygame.Surface((prof_card.width, prof_card.height), pygame.SRCALPHA)
    pygame.draw.rect(prof_bg, (12, 16, 30, 220), prof_bg.get_rect(), border_radius=8)
    pygame.draw.rect(prof_bg, (*NEON_CYAN[:3], 90), prof_bg.get_rect(), width=1, border_radius=8)
    screen.blit(prof_bg, prof_card.topleft)

    dot_glow = int(160 + 95 * math.sin(ui_pulse_t * 5.0))
    pygame.draw.circle(screen, (*NEON_GREEN[:3], dot_glow), (prof_card.x + 14, prof_card.centery - 4), 4)
    pygame.draw.circle(screen, WHITE, (prof_card.x + 14, prof_card.centery - 4), 2)
    draw_text(prof_name, FONT_MENU_SUB, WHITE, prof_card.x + 26, prof_card.centery - 6, center=False)
    draw_text("PILOT // ONLINE", FONT_MENU_TELEMETRY, (100, 150, 200), prof_card.x + 26, prof_card.centery + 6, center=False)

    # Center Title
    title_glow_a = int(60 + 35 * math.sin(ui_pulse_t * 2.5))
    for goff, ga in [(2, title_glow_a // 2), (1, title_glow_a)]:
        ts = FONT_MENU_TITLE.render("CRAZYY SIMULATION", True, NEON_CYAN)
        ts.set_alpha(ga)
        screen.blit(ts, ts.get_rect(center=(WIDTH // 2 + goff, 22)))
    draw_text_shadow("CRAZYY SIMULATION", FONT_MENU_TITLE, WHITE, WIDTH // 2, 22, shadow_color=(0, 40, 80), offset=2)
    draw_text("//  COSMIC CIVIL WAR  [PC EDITION]  //", FONT_MENU_SUB, NEON_GOLD, WIDTH // 2, 46, center=True)
    pygame.draw.line(screen, (*NEON_CYAN, 70), (WIDTH // 2 - 160, 46), (WIDTH // 2 - 85, 46), 1)
    pygame.draw.line(screen, (*NEON_CYAN, 70), (WIDTH // 2 + 85, 46), (WIDTH // 2 + 160, 46), 1)

    # Right Currency Deck
    credit_card = pygame.Rect(550, 12, 155, 40)
    cr_bg = pygame.Surface((credit_card.width, credit_card.height), pygame.SRCALPHA)
    pygame.draw.rect(cr_bg, (12, 16, 30, 220), cr_bg.get_rect(), border_radius=8)
    pygame.draw.rect(cr_bg, (*NEON_GOLD[:3], 90), cr_bg.get_rect(), width=1, border_radius=8)
    screen.blit(cr_bg, credit_card.topleft)
    screen.blit(coin_icon, (credit_card.x + 8, credit_card.y + 11))
    draw_text(f"{total_coins:,} CC", FONT_MENU_SUB, NEON_GOLD, credit_card.x + 36, credit_card.centery - 6, center=False)
    draw_text("CLOUD SYNCED", FONT_MENU_TELEMETRY, NEON_GREEN, credit_card.x + 36, credit_card.centery + 6, center=False)

    pygame.draw.line(screen, (30, 45, 75), (16, 58), (WIDTH - 16, 58), 1)

    # 2. LEFT COMMAND NAVIGATION
    card_y = 72
    card_w = 340
    card_h = 68
    card_gap = 10
    target_state = 0
    should_quit = False

    for idx, (title, sub, icon_t, accent_col, hotkey, target) in enumerate(nav_items):
        cur_y = card_y + idx * (card_h + card_gap)
        card_rect = pygame.Rect(16, cur_y, card_w, card_h)

        is_focused = (idx == focused_btn)
        
        # Protected button interaction
        clicked, is_hover, is_pressed = ui_manager.button(
            screen, f"pc_nav_{idx}", card_rect, "",
            is_mobile=False, accent=accent_col, enabled=(target != "locked")
        )
        if is_hover and target != "locked":
            focused_btn = idx

        active = (is_hover or is_focused) and target != "locked"

        # Content rendering inside card
        icon_cx = card_rect.x + 30
        icon_cy = card_rect.centery
        draw_vector_icon(screen, icon_t, icon_cx, icon_cy, accent_col if active else (120, 140, 170), scale=1.0)

        title_col = WHITE if active else (220, 230, 245) if target != "locked" else (110, 120, 140)
        desc_col = accent_col if active else (100, 130, 160) if target != "locked" else (70, 80, 100)
        draw_text(title, FONT_MENU_CARD_MAIN, title_col, card_rect.x + 56, card_rect.centery - 11, center=False)
        draw_text(sub, FONT_MENU_CARD_DESC, desc_col, card_rect.x + 56, card_rect.centery + 10, center=False)

        # Hotkey badge
        if target == "locked":
            badge_r = pygame.Rect(card_rect.right - 96, card_rect.centery - 10, 88, 20)
            pygame.draw.rect(screen, (35, 15, 20), badge_r, border_radius=10)
            pygame.draw.rect(screen, (*RED[:3], 180), badge_r, width=1, border_radius=10)
            draw_text("COMING v2.0", FONT_TINY, RED, badge_r.centerx, badge_r.centery)
        else:
            hk_rect = pygame.Rect(card_rect.right - 48, card_rect.centery - 10, 36, 20)
            pygame.draw.rect(screen, (10, 14, 25), hk_rect, border_radius=6)
            pygame.draw.rect(screen, (*accent_col[:3], 160 if active else 70), hk_rect, width=1, border_radius=6)
            draw_text(hotkey, FONT_TINY, accent_col if active else LIGHT_GRAY, hk_rect.centerx, hk_rect.centery)

        # Activation triggered via protected click or Enter key
        activated = clicked or (key_enter and is_focused and target != "locked")
        if activated and target != "locked":
            if target == "quit":
                should_quit = True
            else:
                target_state = target
                ui_manager.notify_state_change(target)

    # 3. RIGHT SHIP HANGAR & TELEMETRY
    hangar_rect = pygame.Rect(375, 72, 408, 460)
    _hangar_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(_hangar_surf, (8, 12, 24, 200), _hangar_surf.get_rect(), border_radius=12)
    pygame.draw.rect(_hangar_surf, (*NEON_CYAN[:3], 80), _hangar_surf.get_rect(), width=1, border_radius=12)
    screen.blit(_hangar_surf, hangar_rect.topleft)
    draw_corner_brackets(screen, hangar_rect, NEON_CYAN, size=12, width=1)

    env_names = {1: "GALAXY SECTOR", 2: "NEBULA EXPANSE", 3: "BLACK HOLE CORE"}
    draw_text("// STARSHIP COMBAT TELEMETRY //", FONT_MENU_TELEMETRY, NEON_CYAN, hangar_rect.centerx, hangar_rect.y + 16)
    draw_text(f"ACTIVE THEATER: {env_names.get(current_selected_env, 'GALAXY SECTOR')}", FONT_TINY, (120, 150, 190), hangar_rect.centerx, hangar_rect.y + 32)

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
        for ox in [-12, 12]:
            _hangar_particles.append({
                'x': ship_cx + ox + random.uniform(-2, 2),
                'y': ship_cy + float_y + 20,
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(2.5, 6.0),
                'life': 18, 'max_life': 18,
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

    # Render Starship Wireframe & Hull
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

    # Telemetry Grid
    stat_box_y = hangar_rect.y + 278
    pygame.draw.line(screen, (30, 45, 75), (hangar_rect.x + 16, stat_box_y - 12), (hangar_rect.right - 16, stat_box_y - 12), 1)

    stats = [
        ("HULL ARMOR",      f"{unlocked_hp} HP",              f"MK-{hp_step + 1}",      NEON_CYAN),
        ("ION THRUST",      f"{unlocked_speed * 10}% SPEED",  f"TIER {speed_step + 1}",  NEON_BLUE),
        ("PLASMA CANNONS",  f"{unlocked_bullets}x BURST",     f"LVL {bullet_step + 1}",  NEON_PURPLE),
        ("RAPID CYCLE",     f"{unlocked_firerate:.1f}s CD",    f"LVL {firerate_step + 1}", NEON_GOLD),
    ]

    for i, (label, val, sub_stat, col) in enumerate(stats):
        bx = hangar_rect.x + 16 + (i % 2) * 190
        by = stat_box_y + (i // 2) * 52
        s_rect = pygame.Rect(bx, by, 184, 44)
        s_bg = pygame.Surface((s_rect.width, s_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s_bg, (14, 18, 34, 190), s_bg.get_rect(), border_radius=8)
        pygame.draw.rect(s_bg, (*col[:3], 70), s_bg.get_rect(), width=1, border_radius=8)
        screen.blit(s_bg, s_rect.topleft)

        draw_text(label, FONT_MENU_TELEMETRY, (120, 140, 170), s_rect.x + 8, s_rect.y + 7, center=False)
        draw_text(val, FONT_MENU_SUB, WHITE, s_rect.x + 8, s_rect.y + 24, center=False)
        draw_badge(screen, sub_stat, FONT_TINY, s_rect.right - 34, s_rect.centery,
                   bg_color=(20, 24, 45), text_color=col, border_color=col)

    ready_pill = pygame.Rect(hangar_rect.x + 20, hangar_rect.bottom - 32, hangar_rect.width - 40, 22)
    pygame.draw.rect(screen, (10, 30, 20), ready_pill, border_radius=11)
    pygame.draw.rect(screen, (*NEON_GREEN[:3], 140), ready_pill, width=1, border_radius=11)
    draw_text("● ALL SHIP SYSTEMS 100% COMBAT READY", FONT_MENU_TELEMETRY, NEON_GREEN, ready_pill.centerx, ready_pill.centery)

    # 4. BOTTOM ACTION DOCK
    btn_logout = pygame.Rect(16, 552, 130, 32)
    logout_clicked, _, _ = ui_manager.button(screen, "pc_btn_logout", btn_logout, "[ ESC ] LOG OUT",
                                             is_mobile=False, accent=RED, base_color=(24, 14, 18))
    should_logout = logout_clicked

    draw_text("CRAZYY ENGINE  •  PC COMMAND DECK  •  @IAMBKRAM", FONT_MENU_TELEMETRY, (70, 95, 130), WIDTH // 2 + 10, 568)

    btn_report = pygame.Rect(WIDTH - 156, 552, 140, 32)
    report_clicked, _, _ = ui_manager.button(screen, "pc_btn_report", btn_report, "[ ! ] ISSUES",
                                             is_mobile=False, accent=NEON_CYAN, base_color=(12, 22, 36))
    if report_clicked:
        try:
            webbrowser.open("https://github.com/iambkram/Crazyy-Simulation/issues")
        except Exception:
            pass

    return target_state, focused_btn, not should_quit, 14 if target_state != 0 else 0, False, should_logout
