import pygame
import math
from assets import draw_menu_starfield, draw_text, draw_text_shadow, draw_neon_panel, draw_divider, draw_gradient_bar, draw_glowing_button, FONT_MSG, FONT_UI, FONT_SMALL, FONT_TINY, FONT_HUD, FONT_MODAL_TITLE, NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_ORANGE, NEON_PINK, RED, WHITE, LIGHT_GRAY, MID_GRAY, PANEL_BG, PANEL_MID
from settings import WIDTH, HEIGHT

def render_store(screen, mx, my, m_c, key_escape, key_enter, tap_snd, ui_pulse_t, menu_bg, coin_icon, total_coins, hp_step, speed_step, bullet_step, hp_costs, speed_costs, bullet_costs, store_selection, unlocked_hp, unlocked_speed, unlocked_bullets):
    """Renders the store menu (State 6). Returns (next_state, next_store_selection, click_cooldown, m_c, key_escape, key_enter)"""
    
    
    screen.blit(menu_bg, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 185))
    screen.blit(overlay, (0, 0))
    draw_menu_starfield(screen)
    
    draw_text_shadow("SPACE STORE", FONT_MSG, NEON_CYAN, 400, 48, shadow_color=(0,80,120), offset=2)
    
    # Coin badge
    coin_panel = pygame.Rect(318, 78, 164, 36)
    pygame.draw.rect(screen, PANEL_BG, coin_panel, border_radius=18)
    pygame.draw.rect(screen, NEON_GOLD, coin_panel, width=1, border_radius=18)
    screen.blit(coin_icon, (326, 70))
    draw_text(str(total_coins), FONT_UI, NEON_GOLD, 395, 96)
    
    draw_divider(screen, 80, 124, 720, NEON_CYAN, alpha=40)
    
    # Store item cards
    store_items = [
        ("❤  MAX HP",   NEON_GREEN,   70,  'hp', unlocked_hp,      hp_step,    len(hp_costs),     hp_costs),
        ("⚡  SPEED",    NEON_ORANGE,  280, 'sp', unlocked_speed,   speed_step, len(speed_costs),  speed_costs),
        ("🔫  BULLETS",  NEON_PINK,    490, 'pb', unlocked_bullets, bullet_step,len(bullet_costs), bullet_costs),
    ]
    
    next_state = 6
    next_store_selection = store_selection
    next_click_cooldown = 0
    
    for name, col, x, key, curr_val, step, max_steps, costs in store_items:
        card = pygame.Rect(x, 148, 190, 220)
        is_h = card.collidepoint(mx, my)
        is_sel = (store_selection == key)
        
        draw_neon_panel(screen, card, accent=col if (is_h or is_sel) else MID_GRAY,
                        alpha=235, border_radius=16, border_width=2 if not is_sel else 3, bg=PANEL_MID)
        
        if is_sel:
            pa = int(100 + 80 * math.sin(ui_pulse_t * 3))
            gls = pygame.Surface((card.width+12, card.height+12), pygame.SRCALPHA)
            pygame.draw.rect(gls, (*col, pa), gls.get_rect(), border_radius=20, width=2)
            screen.blit(gls, (card.x-6, card.y-6))
            
        draw_text(name, FONT_SMALL, col, card.centerx, card.y + 34)
        draw_divider(screen, card.x + 12, card.y + 52, card.right - 12, col, alpha=60)
        
        # Current value
        draw_text(str(curr_val), FONT_HUD, WHITE, card.centerx, card.y + 90)
        
        # Upgrade progress bar
        prog_frac = min(1.0, step / max(1, max_steps))
        bar_rect = pygame.Rect(card.x + 14, card.y + 120, card.width - 28, 10)
        draw_gradient_bar(screen, bar_rect, prog_frac, color_low=(40,40,60), color_high=col,
                          bg_color=(20,22,35), border_radius=5, show_glow=False)
        draw_text(f"{step}/{max_steps}", FONT_TINY, LIGHT_GRAY, card.centerx, card.y + 144)
        
        # Cost
        next_cost = costs[step] if step < max_steps else "MAX"
        cost_col = NEON_GOLD if next_cost != "MAX" and total_coins >= (next_cost if next_cost != "MAX" else 0) else (RED if next_cost != "MAX" else MID_GRAY)
        cost_txt = f"COINS {next_cost}" if next_cost != "MAX" else "MAX"
        draw_text(cost_txt, FONT_SMALL, cost_col, card.centerx, card.y + 178)
        
        # Select on click
        if m_c and is_h and not store_selection:
            tap_snd.play()
            next_store_selection = key
            next_click_cooldown = 12
            m_c = False
            
    # Item detail popup
    if store_selection:
        pop_ovl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pop_ovl.fill((0, 0, 0, 200))
        screen.blit(pop_ovl, (0, 0))
        
        pop_box = pygame.Rect(145, 148, 510, 304)
        draw_neon_panel(screen, pop_box, accent=NEON_CYAN, alpha=248, border_radius=20)
        
        desc_map = {"hp": "Increase Maximum HP Capacity", "sp": "Boost Ship Navigation Speed", "pb": "Unlock Extra Bullet Streams"}
        desc = desc_map.get(store_selection, "")
        if store_selection == 'hp':
            cost = hp_costs[hp_step] if hp_step < len(hp_costs) else "MAX"
        elif store_selection == 'sp':
            cost = speed_costs[speed_step] if speed_step < len(speed_costs) else "MAX"
        else:
            cost = bullet_costs[bullet_step] if bullet_step < len(bullet_costs) else "MAX"
            
        draw_text("UPGRADE DETAILS", FONT_MODAL_TITLE, NEON_GOLD, 400, 194)
        draw_divider(screen, 185, 218, 615, NEON_GOLD, alpha=50)
        draw_text(desc, FONT_SMALL, WHITE, 400, 252)
        
        can_afford = cost != "MAX" and total_coins >= cost
        cost_col2 = NEON_GREEN if can_afford else (RED if cost != "MAX" else MID_GRAY)
        cost_txt2 = f"COINS  {cost} COINS" if cost != "MAX" else "ALREADY MAXED"
        draw_text(cost_txt2, FONT_UI, cost_col2, 400, 300)
        
        btn_st_bk = pygame.Rect(175, 368, 192, 54)
        btn_buy   = pygame.Rect(433, 368, 192, 54)
        is_h_bk   = btn_st_bk.collidepoint(mx, my)
        is_h_buy  = btn_buy.collidepoint(mx, my)
        
        draw_glowing_button(screen, "BACK", FONT_UI, WHITE, btn_st_bk, NEON_PINK, is_h_bk, pulse_t=ui_pulse_t)
        if cost != "MAX":
            draw_glowing_button(screen, "BUY", FONT_UI, WHITE, btn_buy, NEON_GREEN if can_afford else MID_GRAY, is_h_buy, pulse_t=ui_pulse_t)
            
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
        btn_b_m = pygame.Rect(255, 430, 290, 56)
        is_h_bm = btn_b_m.collidepoint(mx, my)
        draw_glowing_button(screen, "BACK TO MENU", FONT_UI, WHITE, btn_b_m, NEON_PINK, is_h_bm,
                            border_radius=16, accent=RED, pulse_t=ui_pulse_t)
        if (m_c and is_h_bm) or key_escape:
            tap_snd.play()
            next_state = 0
            next_click_cooldown = 12
            m_c = False

    return next_state, next_store_selection, next_click_cooldown, m_c, key_escape, key_enter

def render_store_confirm(screen, mx, my, m_c, key_escape, key_enter, tap_snd, coin_snd, ui_pulse_t, total_coins, store_selection, hp_step, speed_step, bullet_step, hp_costs, speed_costs, bullet_costs):
    """State 7: Confirm Purchase"""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 210))
    screen.blit(pop_overlay, (0, 0))
    
    box = pygame.Rect(160, 170, 480, 260)
    draw_neon_panel(screen, box, accent=NEON_GOLD, alpha=250, border_radius=20)
    
    draw_text("CONFIRM UPGRADE?", FONT_MODAL_TITLE, NEON_GOLD, 400, 212)
    draw_divider(screen, 195, 238, 605, NEON_GOLD, alpha=50)
    cost = hp_costs[hp_step] if store_selection == 'hp' else speed_costs[speed_step] if store_selection == 'sp' else bullet_costs[bullet_step]
    draw_text(f"Spend  COINS {cost} coins  to upgrade?", FONT_SMALL, WHITE, 400, 275)
    draw_text(f"You have: {total_coins} coins", FONT_TINY, LIGHT_GRAY, 400, 302)
    
    b_n = pygame.Rect(185, 340, 192, 54)
    b_y = pygame.Rect(423, 340, 192, 54)
    is_h_n = b_n.collidepoint(mx, my)
    is_h_y = b_y.collidepoint(mx, my)
    
    draw_glowing_button(screen, "CANCEL", FONT_UI, WHITE, b_n, NEON_PINK, is_h_n, pulse_t=ui_pulse_t)
    draw_glowing_button(screen, "CONFIRM", FONT_UI, WHITE, b_y, NEON_GREEN, is_h_y, pulse_t=ui_pulse_t)
    
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
    """State 8: Not Enough Coins"""
    pop_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pop_overlay.fill((0, 0, 0, 210))
    screen.blit(pop_overlay, (0, 0))
    
    box = pygame.Rect(180, 210, 440, 180)
    draw_neon_panel(screen, box, accent=RED, alpha=250, border_radius=20)
    
    draw_text("NOT ENOUGH COINS", FONT_MODAL_TITLE, RED, 400, 250)
    draw_text("Play more missions to earn coins!", FONT_SMALL, LIGHT_GRAY, 400, 290)
    
    b_ok = pygame.Rect(300, 330, 200, 44)
    is_h_ok = b_ok.collidepoint(mx, my)
    draw_glowing_button(screen, "OK", FONT_UI, WHITE, b_ok, NEON_PINK, is_h_ok, pulse_t=ui_pulse_t)
    
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
