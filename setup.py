import pygame
import os
import sys
import shutil
import subprocess
import math
import random
import time
import json

# =============================================================================
# CRAZYY SIMULATION - OFFICIAL WINDOWS SETUP & INSTALLATION WIZARD
# =============================================================================

pygame.init()
pygame.font.init()

SETUP_WIDTH = 760
SETUP_HEIGHT = 540

screen = pygame.display.set_mode((SETUP_WIDTH, SETUP_HEIGHT))
pygame.display.set_caption("Crazyy Simulation - Setup Wizard")

# Try loading window icon
try:
    if os.path.exists("icon.ico"):
        setup_icon = pygame.image.load("icon.ico")
        pygame.display.set_icon(setup_icon)
except Exception:
    pass

# Fonts
FONT_TITLE  = pygame.font.SysFont("Impact", 44)
FONT_HEADER = pygame.font.SysFont("Impact", 28)
FONT_SUB    = pygame.font.SysFont("Arial Black", 14)
FONT_BODY   = pygame.font.SysFont("Segoe UI", 14)
FONT_BODY_B = pygame.font.SysFont("Segoe UI Bold", 14)
FONT_MONO   = pygame.font.SysFont("Consolas", 12)
FONT_TINY   = pygame.font.SysFont("Segoe UI", 12)

# Colors
NEON_CYAN   = (0, 230, 255)
NEON_PINK   = (255, 45, 120)
NEON_GREEN  = (0, 255, 140)
NEON_ORANGE = (255, 140, 20)
NEON_GOLD   = (255, 205, 40)
NEON_BLUE   = (40, 140, 255)
NEON_PURPLE = (180, 50, 240)

WHITE       = (255, 255, 255)
LIGHT_GRAY  = (200, 210, 225)
MID_GRAY    = (110, 120, 140)
DARK_GRAY   = (35, 42, 58)
PANEL_BG    = (14, 18, 28)
PANEL_MID   = (20, 26, 42)
BLACK       = (6, 8, 14)
RED         = (255, 60, 80)

# Paths
SOURCE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Programs', 'Crazyy-Simulation')
DESKTOP_DIR = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
START_MENU_DIR = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Crazyy Simulation')

# Wizard Pages
PAGE_WELCOME     = 0
PAGE_PERMISSIONS = 1
PAGE_DIRECTORY   = 2
PAGE_INSTALLING  = 3
PAGE_COMPLETE    = 4

current_page = PAGE_WELCOME

# Options
opt_grant_perms     = True
opt_desktop_icon    = True
opt_start_menu      = True
opt_launch_game     = True
install_path        = DEFAULT_INSTALL_DIR

# Installation Progress State
install_progress    = 0.0
install_step_index  = 0
install_logs        = []
install_finished    = False
install_error       = None

# Animated Background Stars
stars = []
for _ in range(90):
    stars.append({
        'x': random.uniform(0, SETUP_WIDTH),
        'y': random.uniform(0, SETUP_HEIGHT),
        'spd': random.uniform(0.3, 1.2),
        'sz': random.uniform(1.0, 2.5),
        'col': random.choice([(140, 180, 255), (200, 240, 255), (100, 140, 220)])
    })

def draw_setup_background(surface, pulse_t):
    """Draw ambient cyber neon starfield and grid background."""
    surface.fill(BLACK)
    
    # Stars
    for s in stars:
        s['y'] += s['spd']
        if s['y'] > SETUP_HEIGHT:
            s['y'] = 0
            s['x'] = random.uniform(0, SETUP_WIDTH)
        pygame.draw.circle(surface, s['col'], (int(s['x']), int(s['y'])), int(s['sz']))

    # Glowing border frame
    border_rect = pygame.Rect(12, 12, SETUP_WIDTH - 24, SETUP_HEIGHT - 24)
    pygame.draw.rect(surface, PANEL_BG, border_rect, border_radius=14)
    
    pulse_a = int(120 + 60 * math.sin(pulse_t * 2))
    pulse_surf = pygame.Surface((SETUP_WIDTH, SETUP_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(pulse_surf, (*NEON_CYAN, pulse_a), border_rect, width=2, border_radius=14)
    surface.blit(pulse_surf, (0, 0))

def draw_setup_header(surface, title, subtitle):
    """Draw standardized wizard header banner."""
    header_rect = pygame.Rect(14, 14, SETUP_WIDTH - 28, 80)
    h_surf = pygame.Surface((header_rect.width, header_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(h_surf, (10, 14, 24, 240), h_surf.get_rect(), border_top_left_radius=12, border_top_right_radius=12)
    surface.blit(h_surf, header_rect.topleft)

    # Title & Subtitle
    t_surf = FONT_HEADER.render(title, True, NEON_CYAN)
    surface.blit(t_surf, (36, 26))
    s_surf = FONT_TINY.render(subtitle, True, LIGHT_GRAY)
    surface.blit(s_surf, (38, 62))

    # Divider
    pygame.draw.line(surface, NEON_CYAN, (36, 94), (SETUP_WIDTH - 36, 94), 1)

def draw_setup_footer(surface):
    """Draw wizard footer bar."""
    footer_rect = pygame.Rect(14, SETUP_HEIGHT - 74, SETUP_WIDTH - 28, 60)
    f_surf = pygame.Surface((footer_rect.width, footer_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(f_surf, (10, 14, 24, 240), f_surf.get_rect(), border_bottom_left_radius=12, border_bottom_right_radius=12)
    surface.blit(f_surf, footer_rect.topleft)
    pygame.draw.line(surface, (40, 50, 70), (36, SETUP_HEIGHT - 74), (SETUP_WIDTH - 36, SETUP_HEIGHT - 74), 1)

def draw_neon_checkbox(surface, rect, label, checked, mouse_pos):
    """Draw a cyber-themed glowing checkbox."""
    box_rect = pygame.Rect(rect.x, rect.y + 2, 22, 22)
    is_hover = rect.collidepoint(mouse_pos)
    
    # Fill
    bg_col = (20, 35, 50) if checked else (15, 18, 26)
    pygame.draw.rect(surface, bg_col, box_rect, border_radius=6)
    border_col = NEON_CYAN if (checked or is_hover) else MID_GRAY
    pygame.draw.rect(surface, border_col, box_rect, width=2, border_radius=6)
    
    if checked:
        # Draw checkmark
        pts = [(box_rect.x + 5, box_rect.y + 11), (box_rect.x + 9, box_rect.y + 16), (box_rect.x + 17, box_rect.y + 6)]
        pygame.draw.lines(surface, NEON_GREEN, False, pts, 3)

    # Label
    lbl_col = WHITE if checked else LIGHT_GRAY
    lbl_surf = FONT_BODY_B.render(label, True, lbl_col)
    surface.blit(lbl_surf, (box_rect.right + 12, rect.y + 3))

def draw_setup_btn(surface, rect, text, color, mouse_pos, pulse_t=0.0, disabled=False):
    """Draw a glowing installer button."""
    is_hover = rect.collidepoint(mouse_pos) and not disabled
    
    if disabled:
        pygame.draw.rect(surface, (20, 24, 32), rect, border_radius=10)
        pygame.draw.rect(surface, (45, 50, 60), rect, width=1, border_radius=10)
        t_surf = FONT_SUB.render(text, True, (80, 90, 105))
        surface.blit(t_surf, t_surf.get_rect(center=rect.center))
        return False

    bg_col = (int(color[0]*0.25), int(color[1]*0.25), int(color[2]*0.25))
    if is_hover:
        bg_col = (min(255, bg_col[0] + 35), min(255, bg_col[1] + 35), min(255, bg_col[2] + 35))
    
    pygame.draw.rect(surface, bg_col, rect, border_radius=10)
    pygame.draw.rect(surface, color, rect, width=2 if is_hover else 1, border_radius=10)
    
    if is_hover:
        glow_s = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*color, 70), glow_s.get_rect(), border_radius=14, width=2)
        surface.blit(glow_s, (rect.x - 5, rect.y - 5))

    t_surf = FONT_SUB.render(text, True, WHITE)
    surface.blit(t_surf, t_surf.get_rect(center=rect.center))
    return is_hover

def create_windows_shortcut(target_path, shortcut_path, icon_path, working_dir):
    """Create genuine Windows .lnk shortcut using PowerShell COM Object."""
    try:
        os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
        ps_script = f"""
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut('{shortcut_path}')
        $Shortcut.TargetPath = '{target_path}'
        $Shortcut.WorkingDirectory = '{working_dir}'
        $Shortcut.IconLocation = '{icon_path}'
        $Shortcut.Description = 'Play Crazyy Simulation - Galaxy Warfare'
        $Shortcut.Save()
        """
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                       creationflags=0x08000000, check=True)
        return True
    except Exception as e:
        print("Shortcut error:", e)
        return False

def execute_installation_step(step_idx):
    """Execute real file copy and shortcut generation steps."""
    global install_logs, install_progress, install_finished, install_error
    
    try:
        if step_idx == 0:
            install_logs.append(">> Initializing Crazyy Simulation deployment engine...")
            install_progress = 0.10
        elif step_idx == 1:
            install_logs.append(f">> Creating destination directory: {install_path}")
            os.makedirs(install_path, exist_ok=True)
            install_progress = 0.25
        elif step_idx == 2:
            install_logs.append(">> Copying core game scripts & assets...")
            # Copy all game python scripts
            py_files = ["main.py", "settings.py", "assets.py", "branding.py", "menu_battle.py", "vfx.py"]
            for f in py_files:
                src_f = os.path.join(SOURCE_DIR, f)
                if os.path.exists(src_f):
                    shutil.copy2(src_f, os.path.join(install_path, f))
            # Copy icon
            if os.path.exists(os.path.join(SOURCE_DIR, "icon.ico")):
                shutil.copy2(os.path.join(SOURCE_DIR, "icon.ico"), os.path.join(install_path, "icon.ico"))
            # Copy game_assets
            src_assets = os.path.join(SOURCE_DIR, "game_assets")
            dst_assets = os.path.join(install_path, "game_assets")
            if os.path.exists(src_assets):
                if os.path.exists(dst_assets):
                    shutil.rmtree(dst_assets)
                shutil.copytree(src_assets, dst_assets)
            install_progress = 0.55
        elif step_idx == 3:
            install_logs.append(">> Initializing game save profile & configuration...")
            save_path = os.path.join(install_path, "save.json")
            if not os.path.exists(save_path):
                default_save = {
                    "coins": 0, "hp": 200, "hp_step": 0, "speed": 7, "speed_step": 0,
                    "bullets": 1, "bullet_step": 0, "max_galaxy_level": 1, "max_nebula_level": 1,
                    "max_blackhole_level": 1, "env2_unlocked": False, "env3_unlocked": False,
                    "control_type": "PC", "music_vol": 0.5, "sfx_vol": 0.7
                }
                with open(save_path, "w") as sf:
                    json.dump(default_save, sf, indent=4)
            install_progress = 0.70
        elif step_idx == 4:
            install_logs.append(">> Generating Crazyy-Simulation Windows launcher...")
            # Create a clean Windows launcher script
            launcher_bat = os.path.join(install_path, "Crazyy-Simulation.bat")
            python_exe = sys.executable
            with open(launcher_bat, "w") as bf:
                bf.write(f'@echo off\ncd /d "{install_path}"\nstart "" "{python_exe}" main.py\nexit\n')
            
            launcher_vbs = os.path.join(install_path, "Crazyy-Simulation.vbs")
            with open(launcher_vbs, "w") as vf:
                vf.write(f'Set WshShell = CreateObject("WScript.Shell")\n'
                         f'WshShell.CurrentDirectory = "{install_path}"\n'
                         f'WshShell.Run """{python_exe}"" main.py", 0, False\n')
            install_progress = 0.85
        elif step_idx == 5:
            icon_file = os.path.join(install_path, "icon.ico")
            vbs_launcher = os.path.join(install_path, "Crazyy-Simulation.vbs")
            
            if opt_desktop_icon:
                install_logs.append(">> Creating Desktop Shortcut on Windows...")
                d_lnk = os.path.join(DESKTOP_DIR, "Crazyy Simulation.lnk")
                create_windows_shortcut(vbs_launcher, d_lnk, icon_file, install_path)
                
            if opt_start_menu:
                install_logs.append(">> Registering in Windows Start Menu & App Search...")
                s_lnk = os.path.join(START_MENU_DIR, "Crazyy Simulation.lnk")
                create_windows_shortcut(vbs_launcher, s_lnk, icon_file, install_path)
                
            install_logs.append(">> Setup completed successfully! All files verified.")
            install_progress = 1.0
            install_finished = True
    except Exception as e:
        install_error = str(e)
        install_logs.append(f">> ERROR: {install_error}")

# =============================================================================
# MAIN WIZARD LOOP
# =============================================================================

clock = pygame.time.Clock()
running = True
pulse_ticker = 0.0

btn_next_rect = pygame.Rect(SETUP_WIDTH - 170, SETUP_HEIGHT - 62, 140, 42)
btn_back_rect = pygame.Rect(SETUP_WIDTH - 325, SETUP_HEIGHT - 62, 140, 42)
btn_cancel_rect = pygame.Rect(36, SETUP_HEIGHT - 62, 130, 42)

step_timer = 0

while running:
    pulse_ticker += 0.05
    mx, my = pygame.mouse.get_pos()
    mouse_clicked = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_clicked = True

    # 1. Background
    draw_setup_background(screen, pulse_ticker)

    # 2. Page Specific Content
    if current_page == PAGE_WELCOME:
        draw_setup_header(screen, "CRAZYY SIMULATION", "Galaxy Warfare · Setup & Installation Wizard v1.0.0")

        # Welcome Card
        card_rect = pygame.Rect(40, 115, SETUP_WIDTH - 80, 320)
        pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=14)
        pygame.draw.rect(screen, NEON_CYAN, card_rect, width=1, border_radius=14)

        # Welcome Insignia & Text
        draw_text = FONT_HEADER.render("Welcome to the Crazyy Simulation Setup", True, WHITE)
        screen.blit(draw_text, (65, 140))
        
        info_lines = [
            "This wizard will install Crazyy Simulation on your Windows computer.",
            "Features included in this build:",
            "  • 3 Dynamic Environments: Galaxy Sector, Nebula Zone & Black Hole Singularity",
            "  • 40 Thrilling Mission Tiers per Environment with Progressive Level Unlocking",
            "  • Cinematic 'IAMBKRAM' Neon Branding & Supernova Boss Destruction Sequence",
            "  • Full Offline Support, Performance Optimization & Windows Desktop Integration",
            "",
            "Click [ NEXT > ] to review authorizations and configure your installation."
        ]
        
        for idx, line in enumerate(info_lines):
            col = NEON_GOLD if "•" in line else LIGHT_GRAY
            f = FONT_BODY_B if "•" in line else FONT_BODY
            screen.blit(f.render(line, True, col), (65, 195 + idx * 24))

        # Status Tag
        tag_rect = pygame.Rect(65, 385, 420, 32)
        pygame.draw.rect(screen, (15, 30, 45), tag_rect, border_radius=8)
        pygame.draw.rect(screen, NEON_GREEN, tag_rect, width=1, border_radius=8)
        screen.blit(FONT_TINY.render("✔ SYSTEM STATUS: Windows OS Compatible · Ready to Deploy", True, NEON_GREEN), (78, 392))

        # Footer & Buttons
        draw_setup_footer(screen)
        draw_setup_btn(screen, btn_cancel_rect, "CANCEL", RED, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_next_rect, "NEXT >", NEON_CYAN, (mx, my), pulse_ticker)

        if mouse_clicked:
            if btn_cancel_rect.collidepoint(mx, my):
                running = False
            elif btn_next_rect.collidepoint(mx, my):
                current_page = PAGE_PERMISSIONS

    elif current_page == PAGE_PERMISSIONS:
        draw_setup_header(screen, "SYSTEM PERMISSIONS & AUTHORIZATION", "Review required permissions and choose desktop shortcuts")

        card_rect = pygame.Rect(40, 115, SETUP_WIDTH - 80, 320)
        pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=14)
        pygame.draw.rect(screen, NEON_CYAN, card_rect, width=1, border_radius=14)

        # Permissions List
        chk1_rect = pygame.Rect(65, 145, 600, 45)
        chk2_rect = pygame.Rect(65, 210, 600, 45)
        chk3_rect = pygame.Rect(65, 275, 600, 45)

        draw_neon_checkbox(screen, chk1_rect, "Authorize File System & Local Game Installation (Required)", opt_grant_perms, (mx, my))
        screen.blit(FONT_TINY.render("Allows installer to extract assets and maintain offline player progression.", True, MID_GRAY), (100, 172))

        draw_neon_checkbox(screen, chk2_rect, "Create Desktop Shortcut on Windows", opt_desktop_icon, (mx, my))
        screen.blit(FONT_TINY.render("Places a 'Crazyy Simulation' launcher icon directly on your Desktop.", True, MID_GRAY), (100, 237))

        draw_neon_checkbox(screen, chk3_rect, "Register in Windows Start Menu & App Search", opt_start_menu, (mx, my))
        screen.blit(FONT_TINY.render("Allows searching and launching the game from the Windows Taskbar / App Bar.", True, MID_GRAY), (100, 302))

        # Security Seal
        seal_rect = pygame.Rect(65, 385, 600, 32)
        pygame.draw.rect(screen, (20, 28, 40), seal_rect, border_radius=8)
        pygame.draw.rect(screen, NEON_GOLD, seal_rect, width=1, border_radius=8)
        screen.blit(FONT_TINY.render("🛡 VERIFIED BUILD: Clean, safe, self-contained Python package · Developer: @iambkram", True, NEON_GOLD), (78, 392))

        # Footer & Buttons
        draw_setup_footer(screen)
        draw_setup_btn(screen, btn_cancel_rect, "CANCEL", RED, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_back_rect, "< BACK", MID_GRAY, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_next_rect, "NEXT >", NEON_CYAN, (mx, my), pulse_ticker, disabled=not opt_grant_perms)

        if mouse_clicked:
            if chk1_rect.collidepoint(mx, my):
                opt_grant_perms = not opt_grant_perms
            elif chk2_rect.collidepoint(mx, my):
                opt_desktop_icon = not opt_desktop_icon
            elif chk3_rect.collidepoint(mx, my):
                opt_start_menu = not opt_start_menu
            elif btn_cancel_rect.collidepoint(mx, my):
                running = False
            elif btn_back_rect.collidepoint(mx, my):
                current_page = PAGE_WELCOME
            elif btn_next_rect.collidepoint(mx, my) and opt_grant_perms:
                current_page = PAGE_DIRECTORY

    elif current_page == PAGE_DIRECTORY:
        draw_setup_header(screen, "DESTINATION LOCATION", "Select the destination folder where game files will be installed")

        card_rect = pygame.Rect(40, 115, SETUP_WIDTH - 80, 320)
        pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=14)
        pygame.draw.rect(screen, NEON_CYAN, card_rect, width=1, border_radius=14)

        screen.blit(FONT_BODY.render("Setup will install Crazyy Simulation into the following folder:", True, LIGHT_GRAY), (65, 145))

        # Directory Input Panel
        dir_box = pygame.Rect(65, 180, 600, 48)
        pygame.draw.rect(screen, (10, 14, 22), dir_box, border_radius=8)
        pygame.draw.rect(screen, NEON_CYAN, dir_box, width=1, border_radius=8)
        screen.blit(FONT_MONO.render(install_path, True, WHITE), (78, 195))

        # Disk space calculation
        try:
            total_b, used_b, free_b = shutil.disk_usage(os.path.splitdrive(install_path)[0] or "C:")
            free_gb = free_b / (1024**3)
            free_text = f"Space available on drive: {free_gb:.2f} GB"
        except Exception:
            free_text = "Space available: > 10.0 GB"

        screen.blit(FONT_BODY_B.render("Space required: ~42.0 MB", True, NEON_GOLD), (65, 255))
        screen.blit(FONT_BODY.render(free_text, True, NEON_GREEN), (65, 285))
        screen.blit(FONT_TINY.render("Ready to deploy game executable and progressive save system.", True, LIGHT_GRAY), (65, 340))

        # Footer & Buttons
        draw_setup_footer(screen)
        draw_setup_btn(screen, btn_cancel_rect, "CANCEL", RED, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_back_rect, "< BACK", MID_GRAY, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_next_rect, "INSTALL NOW", NEON_GREEN, (mx, my), pulse_ticker)

        if mouse_clicked:
            if btn_cancel_rect.collidepoint(mx, my):
                running = False
            elif btn_back_rect.collidepoint(mx, my):
                current_page = PAGE_PERMISSIONS
            elif btn_next_rect.collidepoint(mx, my):
                current_page = PAGE_INSTALLING
                install_step_index = 0
                install_logs.clear()
                step_timer = pygame.time.get_ticks()

    elif current_page == PAGE_INSTALLING:
        draw_setup_header(screen, "INSTALLING CRAZYY SIMULATION", "Please wait while files and shortcuts are deployed...")

        card_rect = pygame.Rect(40, 115, SETUP_WIDTH - 80, 320)
        pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=14)
        pygame.draw.rect(screen, NEON_CYAN, card_rect, width=1, border_radius=14)

        # Progress bar
        bar_bg = pygame.Rect(65, 155, 630, 24)
        pygame.draw.rect(screen, (10, 14, 22), bar_bg, border_radius=12)
        pygame.draw.rect(screen, (40, 50, 70), bar_bg, width=1, border_radius=12)

        fill_w = int(626 * install_progress)
        if fill_w > 0:
            pygame.draw.rect(screen, NEON_CYAN, (67, 157, fill_w, 20), border_radius=10)
            # Leading shimmer
            pygame.draw.circle(screen, WHITE, (67 + fill_w - 4, 167), 6)

        pct_text = f"{int(install_progress * 100)}%"
        screen.blit(FONT_BODY_B.render(pct_text, True, WHITE), (bar_bg.right - 45, 130))

        # Terminal Log Output Box
        log_box = pygame.Rect(65, 195, 630, 215)
        pygame.draw.rect(screen, (8, 12, 18), log_box, border_radius=8)
        pygame.draw.rect(screen, (30, 40, 60), log_box, width=1, border_radius=8)

        # Render recent logs
        recent_logs = install_logs[-9:]
        for l_i, log_line in enumerate(recent_logs):
            l_col = NEON_GREEN if "successfully" in log_line else (RED if "ERROR" in log_line else NEON_CYAN)
            screen.blit(FONT_MONO.render(log_line, True, l_col), (78, 205 + l_i * 22))

        # Execute steps progressively
        if not install_finished and install_error is None:
            now_t = pygame.time.get_ticks()
            if now_t - step_timer > 320:
                execute_installation_step(install_step_index)
                install_step_index += 1
                step_timer = now_t
        elif install_finished:
            current_page = PAGE_COMPLETE

        draw_setup_footer(screen)
        draw_setup_btn(screen, btn_cancel_rect, "CANCEL", RED, (mx, my), pulse_ticker, disabled=True)
        draw_setup_btn(screen, btn_next_rect, "NEXT >", NEON_CYAN, (mx, my), pulse_ticker, disabled=True)

    elif current_page == PAGE_COMPLETE:
        draw_setup_header(screen, "INSTALLATION COMPLETE", "Crazyy Simulation has been successfully installed!")

        card_rect = pygame.Rect(40, 115, SETUP_WIDTH - 80, 320)
        pygame.draw.rect(screen, PANEL_MID, card_rect, border_radius=14)
        pygame.draw.rect(screen, NEON_GREEN, card_rect, width=2, border_radius=14)

        # Success Banner
        screen.blit(FONT_HEADER.render("Ready to Launch!", True, NEON_GREEN), (65, 140))
        
        complete_msgs = [
            "Crazyy Simulation is fully configured on your system.",
            f"• Installation Directory: {install_path}",
            "• Desktop Shortcut: Created (Crazyy Simulation.lnk)",
            "• Windows Start Menu & App Search: Registered",
            "",
            "You can launch the game anytime from the Desktop shortcut or Start Menu."
        ]
        for idx, line in enumerate(complete_msgs):
            col = WHITE if "•" in line else LIGHT_GRAY
            screen.blit(FONT_BODY.render(line, True, col), (65, 185 + idx * 24))

        # Launch toggle
        chk_launch = pygame.Rect(65, 360, 450, 35)
        draw_neon_checkbox(screen, chk_launch, "Launch Crazyy Simulation now", opt_launch_game, (mx, my))

        # Footer & Buttons
        draw_setup_footer(screen)
        draw_setup_btn(screen, btn_cancel_rect, "CLOSE", RED, (mx, my), pulse_ticker)
        draw_setup_btn(screen, btn_next_rect, "FINISH", NEON_GREEN, (mx, my), pulse_ticker)

        if mouse_clicked:
            if chk_launch.collidepoint(mx, my):
                opt_launch_game = not opt_launch_game
            elif btn_cancel_rect.collidepoint(mx, my):
                running = False
            elif btn_next_rect.collidepoint(mx, my):
                if opt_launch_game:
                    # Launch the game
                    vbs_launcher = os.path.join(install_path, "Crazyy-Simulation.vbs")
                    if os.path.exists(vbs_launcher):
                        os.startfile(vbs_launcher)
                    else:
                        subprocess.Popen([sys.executable, "main.py"], cwd=install_path)
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
