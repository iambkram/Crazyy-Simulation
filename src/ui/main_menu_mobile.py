"""
Mobile Edition Next-Level Cyberpunk Main Menu UI.
Ergonomic touch-first mobile layout featuring:
  - Hero starship showcase with rotating plasma shield and live particle thrusters
  - Thumb-friendly primary action buttons with large tap targets (56px-70px)
  - Quick-glance pilot identity and cloud credits
  - Zero click-through immunity via UIManager
"""
import pygame
import math
import random
import webbrowser
from settings import (
    WIDTH, HEIGHT, NEON_CYAN, NEON_PURPLE, NEON_PINK,
    NEON_BLUE, NEON_GOLD, NEON_GREEN, NEON_ORANGE,
    WHITE, RED, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID,
    NEON_TEAL
)
from assets import (
    FONT_MENU_TITLE, FONT_MENU_SUB, FONT_MENU_CARD_MAIN,
    FONT_MENU_CARD_DESC, FONT_MENU_TELEMETRY, FONT_TINY,
    FONT_UI, FONT_HUD, FONT_MODAL_TITLE, FONT_SMALL, draw_text, draw_text_shadow,
    draw_corner_brackets, draw_badge, draw_divider
)
from ui.ui_system import ui_manager

_mobile_particles = []


def render_main_menu_mobile(screen, mx, my, m_c, key_escape, key_enter, key_up, key_down, key_tab,
                            tap_snd, ui_pulse_t, total_coins, coin_icon, cloud_sync, current_selected_env,
                            unlocked_hp, unlocked_speed, unlocked_bullets, unlocked_firerate,
                            hp_step, speed_step, bullet_step, firerate_step, focused_btn):
    """
    Renders the Mobile Edition Main Menu with thumb-optimized layout, hero ship spotlight,
    and guaranteed click-through immunity.
    """
    global _mobile_particles

    target_state = 0
    should_logout = False

    # 1. TOP MOBILE STATUS BAR (Safe Area)
    # --- Pilot Card (Left) ---
    prof_name = cloud_sync.current_username or "Mobile Pilot"
    if len(prof_name) > 12:
        prof_name = prof_name[:10] + ".."

    prof_card = pygame.Rect(16, 12, 175, 42)
    prof_bg = pygame.Surface((prof_card.width, prof_card.height), pygame.SRCALPHA)
    pygame.draw.rect(prof_bg, (12, 16, 32, 230), prof_bg.get_rect(), border_radius=12)
    pygame.draw.rect(prof_bg, (*NEON_CYAN[:3], 120), prof_bg.get_rect(), width=2, border_radius=12)
    screen.blit(prof_bg, prof_card.topleft)

    dot_glow = int(170 + 85 * math.sin(ui_pulse_t * 6.0))
    pygame.draw.circle(screen, (*NEON_GREEN[:3], dot_glow), (prof_card.x + 16, prof_card.centery), 5)
    pygame.draw.circle(screen, WHITE, (prof_card.x + 16, prof_card.centery), 2)
    draw_text(prof_name, FONT_MENU_SUB, WHITE, prof_card.x + 30, prof_card.centery - 7, center=False)
    draw_text("PILOT // ONLINE", FONT_MENU_TELEMETRY, NEON_CYAN, prof_card.x + 30, prof_card.centery + 7, center=False)

    # --- Title (Center) ---
    draw_text_shadow("CRAZYY SIMULATION", FONT_MENU_CARD_MAIN, NEON_CYAN, WIDTH // 2, 22, shadow_color=(0, 50, 90), offset=1)
    draw_text("MOBILE TOUCH EDITION", FONT_TINY, NEON_GOLD, WIDTH // 2, 42)

    # --- Credits (Right) ---
    credit_card = pygame.Rect(WIDTH - 186, 12, 170, 42)
    cr_bg = pygame.Surface((credit_card.width, credit_card.height), pygame.SRCALPHA)
    pygame.draw.rect(cr_bg, (14, 18, 34, 230), cr_bg.get_rect(), border_radius=12)
    pygame.draw.rect(cr_bg, (*NEON_GOLD[:3], 120), cr_bg.get_rect(), width=2, border_radius=12)
    screen.blit(cr_bg, credit_card.topleft)
    screen.blit(coin_icon, (credit_card.x + 10, credit_card.y + 12))
    draw_text(f"{total_coins:,} CC", FONT_MENU_SUB, NEON_GOLD, credit_card.x + 38, credit_card.centery - 7, center=False)
    draw_text("SAVED TO CLOUD", FONT_MENU_TELEMETRY, NEON_GREEN, credit_card.x + 38, credit_card.centery + 7, center=False)

    pygame.draw.line(screen, (30, 45, 75), (16, 62), (WIDTH - 16, 62), 1)

    # 2. CENTER HERO STARSHIP SPOTLIGHT
    hero_rect = pygame.Rect(80, 74, WIDTH - 160, 240)
    hero_surf = pygame.Surface((hero_rect.width, hero_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(hero_surf, (10, 15, 30, 190), hero_surf.get_rect(), border_radius=20)
    pygame.draw.rect(hero_surf, (*NEON_CYAN[:3], 90), hero_surf.get_rect(), width=2, border_radius=20)
    screen.blit(hero_surf, hero_rect.topleft)
    draw_corner_brackets(screen, hero_rect, NEON_CYAN, size=16, width=2)

    env_names = {1: "GALAXY SECTOR", 2: "NEBULA EXPANSE", 3: "BLACK HOLE CORE"}
    env_name = env_names.get(current_selected_env, "GALAXY SECTOR")
    draw_badge(screen, f"ACTIVE COMBAT ZONE: {env_name}", FONT_TINY, hero_rect.centerx, hero_rect.y + 20,
               bg_color=(15, 25, 48), text_color=NEON_CYAN, border_color=NEON_CYAN)

    ship_cx = hero_rect.centerx
    ship_cy = hero_rect.y + 115
    float_y = int(math.sin(ui_pulse_t * 3.0) * 6)

    # Rotating energy shield halo
    shield_r = 58
    for i in range(2):
        s_surf = pygame.Surface((shield_r * 2 + 10, shield_r * 2 + 10), pygame.SRCALPHA)
        s_col = NEON_CYAN if i == 0 else NEON_BLUE
        rot_ang = ui_pulse_t * (2.0 if i == 0 else -1.5)
        rect_arc = pygame.Rect(5, 5, shield_r * 2, shield_r * 2)
        pygame.draw.arc(s_surf, (*s_col, 160), rect_arc, rot_ang, rot_ang + math.pi * 1.2, 2)
        pygame.draw.arc(s_surf, (*s_col, 160), rect_arc, rot_ang + math.pi, rot_ang + math.pi * 2.2, 2)
        screen.blit(s_surf, (ship_cx - shield_r - 5, ship_cy + float_y - shield_r - 5))

    # Thruster particles
    if random.random() < 0.9:
        for ox in [-14, 14]:
            _mobile_particles.append({
                'x': ship_cx + ox + random.uniform(-2, 2),
                'y': ship_cy + float_y + 22,
                'vx': random.uniform(-0.6, 0.6),
                'vy': random.uniform(3.0, 7.0),
                'life': 16, 'max_life': 16,
                'col': random.choice([NEON_TEAL, NEON_CYAN, WHITE])
            })

    for p in _mobile_particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        if p['life'] <= 0:
            _mobile_particles.remove(p)
            continue
        p_frac = p['life'] / p['max_life']
        p_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*p['col'], int(255 * p_frac)), (5, 5), max(1, int(4 * p_frac)))
        screen.blit(p_surf, (int(p['x']) - 5, int(p['y']) - 5), special_flags=pygame.BLEND_ADD)

    # Stylized Starship Geometry
    ship_poly = [
        (ship_cx, ship_cy + float_y - 32),
        (ship_cx + 28, ship_cy + float_y + 20),
        (ship_cx + 14, ship_cy + float_y + 14),
        (ship_cx, ship_cy + float_y + 20),
        (ship_cx - 14, ship_cy + float_y + 14),
        (ship_cx - 28, ship_cy + float_y + 20),
    ]
    wing_l = [(ship_cx - 28, ship_cy + float_y + 20), (ship_cx - 40, ship_cy + float_y + 30), (ship_cx - 12, ship_cy + float_y + 8)]
    wing_r = [(ship_cx + 28, ship_cy + float_y + 20), (ship_cx + 40, ship_cy + float_y + 30), (ship_cx + 12, ship_cy + float_y + 8)]
    pygame.draw.polygon(screen, (15, 35, 75), ship_poly)
    pygame.draw.polygon(screen, (22, 50, 105), wing_l)
    pygame.draw.polygon(screen, (22, 50, 105), wing_r)
    pygame.draw.polygon(screen, NEON_CYAN, ship_poly, width=3)
    pygame.draw.polygon(screen, NEON_BLUE, wing_l, width=2)
    pygame.draw.polygon(screen, NEON_BLUE, wing_r, width=2)
    pygame.draw.circle(screen, WHITE, (ship_cx, ship_cy + float_y - 6), 5)
    pygame.draw.circle(screen, NEON_CYAN, (ship_cx, ship_cy + float_y - 6), 8, 2)

    # Starship Stat Badges (Horizontal thumb bar)
    quick_stats = [
        (f"HULL: {unlocked_hp} HP", NEON_CYAN),
        (f"SPEED: {unlocked_speed * 10}%", NEON_BLUE),
        (f"BURST: {unlocked_bullets}X", NEON_PURPLE),
        (f"FIRE: {unlocked_firerate:.1f}s", NEON_GOLD),
    ]
    stat_spacing = (hero_rect.width - 40) // 4
    for si, (stxt, scol) in enumerate(quick_stats):
        sx = hero_rect.x + 20 + si * stat_spacing + stat_spacing // 2
        draw_badge(screen, stxt, FONT_TINY, sx, hero_rect.bottom - 22,
                   bg_color=(14, 20, 38), text_color=scol, border_color=scol)

    # 3. ERGONOMIC THUMB NAVIGATION DOCK (BOTTOM AREA)
    # --- Primary Hero Action Button: DEPLOY CAMPAIGN (Large, Centered) ---
    btn_deploy = pygame.Rect(WIDTH // 2 - 240, 332, 480, 68)
    deploy_clicked, _, _ = ui_manager.button(
        screen, "mob_btn_deploy", btn_deploy, "▶  DEPLOY MISSION",
        is_mobile=True, accent=NEON_GREEN, base_color=(15, 60, 35),
        font=FONT_HUD, border_radius=22
    )
    if deploy_clicked:
        target_state = 20
        ui_manager.notify_state_change(20)

    # --- Secondary Action Buttons (Armory & Settings) ---
    btn_armory = pygame.Rect(WIDTH // 2 - 240, 412, 234, 62)
    armory_clicked, _, _ = ui_manager.button(
        screen, "mob_btn_armory", btn_armory, "⚔  ARMORY",
        is_mobile=True, accent=NEON_PURPLE, base_color=(32, 18, 52),
        font=FONT_UI, border_radius=18
    )
    if armory_clicked:
        target_state = 6
        ui_manager.notify_state_change(6)

    btn_settings = pygame.Rect(WIDTH // 2 + 6, 412, 234, 62)
    settings_clicked, _, _ = ui_manager.button(
        screen, "mob_btn_settings", btn_settings, "⚙  SETTINGS",
        is_mobile=True, accent=NEON_ORANGE, base_color=(45, 26, 16),
        font=FONT_UI, border_radius=18
    )
    if settings_clicked:
        target_state = 9
        ui_manager.notify_state_change(9)

    # --- Bottom Mobile Utility Bar ---
    btn_logout = pygame.Rect(WIDTH // 2 - 240, 486, 234, 48)
    logout_clicked, _, _ = ui_manager.button(
        screen, "mob_btn_logout", btn_logout, "LOG OUT",
        is_mobile=True, accent=RED, base_color=(28, 14, 18),
        font=FONT_SMALL, border_radius=14
    )
    if logout_clicked:
        should_logout = True
        ui_manager.notify_state_change(-3)

    btn_issues = pygame.Rect(WIDTH // 2 + 6, 486, 234, 48)
    issues_clicked, _, _ = ui_manager.button(
        screen, "mob_btn_issues", btn_issues, "HELP & ISSUES",
        is_mobile=True, accent=NEON_CYAN, base_color=(14, 24, 40),
        font=FONT_SMALL, border_radius=14
    )
    if issues_clicked:
        try:
            webbrowser.open("https://github.com/iambkram/Crazyy-Simulation/issues")
        except Exception:
            pass

    # Safe bottom watermark
    draw_text("● TOUCH & SLIDE OPTIMIZED  •  CRAZYY ENGINE MOBILE", FONT_MENU_TELEMETRY, (70, 95, 130), WIDTH // 2, 558)

    return target_state, focused_btn, True, 14 if target_state != 0 else 0, False, should_logout
