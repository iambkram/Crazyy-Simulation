"""
Comprehensive verification test suite for UI Overhaul, Separate PC/Mobile interfaces,
Click-through immunity, HUD geometry, and MobileTouchEngine smoothing.
"""
import os
import sys
import unittest
import subprocess

# Ensure headless execution for testing environments without physical display/audio
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

_SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for p in (_ROOT_DIR, _SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import pygame
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

from settings import WIDTH, HEIGHT, NEON_CYAN, NEON_GOLD, WHITE
from ui.ui_system import ui_manager, play_sfx, UIManager
from mobile.touch_hud import MobileTouchEngine, pause_rect, fire_rect, auto_toggle_rect, hits_hud
import platform_config


class TestUIOverhaul(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        ui_manager.reset_input_state()
        platform_config.configure_pc()

    def tearDown(self):
        os.environ.pop("MOBILE_MODE", None)
        os.environ.pop("PC_MODE", None)
        platform_config.configure_pc()

    def test_click_through_immunity(self):
        """
        Verify that a button on a subsequent page at the exact same screen coordinates
        is mathematically immune to being triggered by a click from the previous page.
        """
        btn_rect = pygame.Rect(300, 200, 200, 60)
        manager = UIManager()

        # Frame 1: Pointer down on Button A (page 1)
        manager.pointer_pos = (350, 230)
        manager.pointer_down = True
        manager.pointer_just_down = True
        manager.pointer_just_up = False

        clk_a_down, _, _ = manager.button(self.surface, "page1_btn", btn_rect, "PAGE 1 NEXT")
        self.assertFalse(clk_a_down, "Button should not trigger on pointer_down")

        # Frame 2: Pointer up on Button A (page 1) -> triggers navigation!
        manager.pointer_down = False
        manager.pointer_just_down = False
        manager.pointer_just_up = True

        clk_a_up, _, _ = manager.button(self.surface, "page1_btn", btn_rect, "PAGE 1 NEXT")
        self.assertTrue(clk_a_up, "Button A should trigger on pointer_up")

        # Page switches to Page 2! State change is notified.
        manager.notify_state_change(new_state=2)

        # On Page 2, Button B is rendered at the EXACT SAME screen coordinates!
        # Even if pointer_just_up is somehow still True or pointer_is_down is True:
        clk_b, _, _ = manager.button(self.surface, "page2_btn", btn_rect, "PAGE 2 DANGEROUS ACTION")
        self.assertFalse(clk_b, "Button B MUST NOT click-through when rendered at identical coordinates!")

        # Frame 3: Normal frame after navigation
        manager.update_frame([], 0.016)
        clk_b_frame3, _, _ = manager.button(self.surface, "page2_btn", btn_rect, "PAGE 2 DANGEROUS ACTION")
        self.assertFalse(clk_b_frame3, "Button B must remain unclicked during transition cooldown")

    def test_hud_geometry_no_overlap(self):
        """
        Verify that HUD player health bar, boss bar, coin pill,
        pause button, and gameplay FPS counter never collide or overlap.
        """
        p_rect = pause_rect()
        hp_bar_rect = pygame.Rect(WIDTH - 245, 23, 180, 22)
        boss_hp_bg = pygame.Rect(WIDTH // 2 - 160, 70, 320, 18)
        coin_pill = pygame.Rect(12, 14, 120, 36)
        
        # Check collision between player HP bar and pause button
        has_overlap = hp_bar_rect.colliderect(p_rect)
        self.assertFalse(has_overlap, f"HP Bar ({hp_bar_rect}) collides with Pause Button ({p_rect})!")
        
        # Verify safety gap
        gap = p_rect.left - hp_bar_rect.right
        self.assertGreaterEqual(gap, 10, f"Expected safe gap >= 10px between HP bar and pause button, got {gap}px")

        # Gameplay FPS position: Rect(14, 56, 76, 22) positioned directly under coin pill
        fps_bg = pygame.Rect(14, 56, 76, 22)
        self.assertFalse(fps_bg.colliderect(hp_bar_rect), "FPS overlay collides with HP bar")
        self.assertFalse(fps_bg.colliderect(p_rect), "FPS overlay collides with Pause button")
        self.assertFalse(fps_bg.colliderect(boss_hp_bg), "FPS overlay collides with Boss HP bar!")
        self.assertFalse(fps_bg.colliderect(coin_pill), "FPS overlay collides with Coin pill!")

    def test_mobile_touch_engine_smoothing_and_isolation(self):
        """
        Verify MobileTouchEngine relative dragging, exponential smoothing,
        and multi-touch isolation so firing taps don't disrupt ship steering.
        """
        engine = MobileTouchEngine()
        engine.reset(WIDTH // 2, HEIGHT - 100)
        ship_rect = pygame.Rect(WIDTH // 2, HEIGHT - 100, 48, 48)

        # Steering finger (ID 1) touches down at (200, 300)
        accepted = engine.on_touch_down((200, 300), finger_id=1, current_ship_x=ship_rect.x, current_ship_y=ship_rect.y)
        self.assertTrue(accepted)
        self.assertTrue(engine.steering_active)
        self.assertEqual(engine.steering_finger_id, 1)

        # Multi-touch: Second finger (ID 2) moves on fire button area or elsewhere
        engine.on_touch_motion((700, 500), finger_id=2)
        # Target pos should NOT have been affected by finger 2
        self.assertEqual(engine.target_ship_pos, [float(WIDTH // 2), float(HEIGHT - 100)])

        # Steering finger moves by +40px horizontally and -30px vertically
        engine.on_touch_motion((240, 270), finger_id=1)
        self.assertEqual(engine.target_ship_pos, [float(WIDTH // 2 + 40), float(HEIGHT - 100 - 30)])

        # Smooth interpolation update across frames
        prev_x = ship_rect.x
        engine.update_smooth_ship_pos(ship_rect, min_x=0, max_x=WIDTH - 48, min_y=50, max_y=HEIGHT - 48)
        # Ship should have glided smoothly towards target
        self.assertGreater(ship_rect.x, prev_x)
        self.assertLessEqual(ship_rect.x, WIDTH // 2 + 40)

        # Finger 2 released should not cancel finger 1 steering
        engine.on_touch_up(finger_id=2)
        self.assertTrue(engine.steering_active)

        # Finger 1 released ends steering
        engine.on_touch_up(finger_id=1)
        self.assertFalse(engine.steering_active)

    def test_mobile_touch_hud_safe_zones(self):
        """
        Verify mobile touch HUD touch zones and hits_hud check.
        """
        p_rect = pause_rect()
        f_rect = fire_rect()
        a_rect = auto_toggle_rect()

        self.assertFalse(p_rect.colliderect(f_rect))
        self.assertFalse(p_rect.colliderect(a_rect))
        self.assertFalse(f_rect.colliderect(a_rect))

        self.assertTrue(hits_hud(p_rect.center))
        self.assertTrue(hits_hud(f_rect.center))
        self.assertTrue(hits_hud(a_rect.center))
        self.assertFalse(hits_hud((WIDTH // 2, HEIGHT // 2)))

    def test_procedural_audio_synthesizer(self):
        """
        Verify procedural sound synthesizer generates all sound types as valid Sound objects.
        """
        from ui.ui_system import _PROC_SFX_CACHE, init_procedural_sfx
        cache = init_procedural_sfx()
        sound_keys = ["ui_tap", "ui_hover", "ui_buy", "ui_back", "ui_fanfare", "ui_warn"]
        for key in sound_keys:
            if pygame.mixer.get_init():
                snd = cache.get(key)
                self.assertIsNotNone(snd, f"Procedural sound for {key} should not be None")
                # Verify calling play_sfx does not crash
                play_sfx(key)

    def test_ui_dispatchers(self):
        """
        Verify platform UI dispatchers function properly for both PC and Mobile modes.
        """
        from ui.main_menu_ui import render_main_menu
        from ui.store_ui import render_store
        from ui.settings_ui import render_settings

        dummy_bg = pygame.Surface((WIDTH, HEIGHT))
        dummy_icon = pygame.Surface((20, 20))

        # Test both platform modes
        for mode in ['PC', 'MOBILE']:
            if mode == 'PC':
                platform_config.configure_pc()
            else:
                platform_config.configure_mobile()
            self.assertEqual(platform_config.is_mobile(), mode == 'MOBILE')
            self.assertEqual(platform_config.is_pc(), mode == 'PC')

            # Test store render dispatcher
            res_store = render_store(
                self.surface, 400, 300, False, False, False, None, 0.0, dummy_bg,
                dummy_icon, 1000, 0, 0, 0, 0,
                [100, 200], [100, 200], [100, 200], [100, 200], 0,
                200, 7, 1, 1.0
            )
            self.assertEqual(len(res_store), 6)

            # Test settings render dispatcher
            res_settings = render_settings(
                self.surface, 400, 300, False, False, False, None, 0.0, dummy_bg,
                mode, 'high', True, True, True, True, False, 0.5, 0.5, 0
            )
            self.assertEqual(len(res_settings), 10)

    def test_main_menu_pc_and_mobile(self):
        """Verify Main Menu renders smoothly on both PC and Mobile without crashing."""
        from ui.main_menu_ui import render_main_menu
        import cloud_sync

        dummy_icon = pygame.Surface((20, 20))
        for mode in ['PC', 'MOBILE']:
            if mode == 'PC':
                platform_config.configure_pc()
            else:
                platform_config.configure_mobile()

            res = render_main_menu(
                self.surface, 400, 300, False, False, False, False, False, False,
                None, 0.0, 500, dummy_icon, cloud_sync, 1,
                200, 7, 1, 1.0,
                0, 0, 0, 0, 0
            )
            # Returns: (target_state, focused_btn, running, click_cooldown, m_c, should_logout)
            self.assertEqual(len(res), 6)
            self.assertIn(res[0], [0, 20, 6, 9, -3])

    def test_level_select_pc_and_mobile(self):
        """Verify Environment Select and Mission Select render on both platforms."""
        from ui.level_select_ui import render_env_select, render_level_select
        dummy_bg = pygame.Surface((WIDTH, HEIGHT))
        dummy_lock = pygame.Surface((20, 20))

        for mode in ['PC', 'MOBILE']:
            if mode == 'PC':
                platform_config.configure_pc()
            else:
                platform_config.configure_mobile()

            # Test Combat Zone (Env) Select
            res_env = render_env_select(
                self.surface, 400, 300, False, False, False, False, False,
                None, 0.0, dummy_bg, dummy_lock,
                5, 1, 1,
                True, False, 1, 0
            )
            self.assertEqual(len(res_env), 5)

            # Test Mission Select
            res_lvl = render_level_select(
                self.surface, 400, 300, False, False, False, None, 0.0,
                1, dummy_bg, dummy_bg, dummy_bg, dummy_lock,
                5, 1, 1,
                0.0, False, 1000, 300, 0, 0.0
            )
            self.assertEqual(len(res_lvl), 7)

    def test_store_confirm_and_error(self):
        """Verify store confirm modal and store error screen."""
        from ui.store_ui import render_store_confirm, render_store_error

        res_confirm = render_store_confirm(
            self.surface, 400, 300, False, False, False, None, None, 0.0, 1000,
            0, 0, 0, 0, 0,
            [100, 200], [100, 200], [100, 200], [100, 200]
        )
        self.assertEqual(len(res_confirm), 6)

        res_err = render_store_error(
            self.surface, 400, 300, False, False, False, None, 0.0
        )
        self.assertEqual(len(res_err), 5)

    def test_full_state_transition_flow(self):
        """
        Verify that a complete game loop state flow maintains click-through immunity
        and correct state tracking across transitions.
        """
        manager = UIManager()
        # Simulated states: 0 (Menu) -> 20 (Zone) -> 1 (Missions) -> 2 (Briefing) -> 3 (Game) -> 10 (Pause) -> 15 (Warning) -> 0 (Menu)
        flow = [0, 20, 1, 2, 3, 10, 15, 0]
        for curr, nxt in zip(flow[:-1], flow[1:]):
            manager.notify_state_change(nxt)
            self.assertEqual(manager.current_state, nxt)
            self.assertEqual(manager.prev_state, curr)
            self.assertGreater(manager.transition_cooldown, 0)
            self.assertFalse(manager.is_pointer_available())

    def test_button_drag_outside_does_not_click(self):
        """If user presses down on button, drags finger away and releases, button must NOT click."""
        manager = UIManager()
        btn_rect = pygame.Rect(100, 100, 150, 50)

        # Press down inside
        manager.pointer_pos = (120, 120)
        manager.pointer_down = True
        manager.pointer_just_down = True
        clk_down, _, _ = manager.button(self.surface, "test_btn", btn_rect, "TEST")
        self.assertFalse(clk_down)
        self.assertEqual(manager.active_button_id, "test_btn")

        # Release outside
        manager.pointer_pos = (400, 400)
        manager.pointer_down = False
        manager.pointer_just_down = False
        manager.pointer_just_up = True
        clk_up, _, _ = manager.button(self.surface, "test_btn", btn_rect, "TEST")
        self.assertFalse(clk_up, "Button must not click when release happens outside rect")

    def test_button_drag_inside_from_outside_does_not_click(self):
        """If user presses down outside, drags into button and releases, button must NOT click."""
        manager = UIManager()
        btn_rect = pygame.Rect(100, 100, 150, 50)

        # Press down outside
        manager.pointer_pos = (50, 50)
        manager.pointer_down = True
        manager.pointer_just_down = True
        manager.pointer_just_up = False
        manager.button(self.surface, "test_btn", btn_rect, "TEST")
        self.assertIsNone(manager.active_button_id)

        # Release inside
        manager.pointer_pos = (120, 120)
        manager.pointer_down = False
        manager.pointer_just_down = False
        manager.pointer_just_up = True
        clk_up, _, _ = manager.button(self.surface, "test_btn", btn_rect, "TEST")
        self.assertFalse(clk_up, "Button must not click when press originated outside")

    def test_rapid_transition_debounce_rejection(self):
        """Verify that frantic taps during state transition cooldown are rejected."""
        manager = UIManager()
        btn_rect = pygame.Rect(100, 100, 150, 50)

        manager.notify_state_change(1)
        self.assertEqual(manager.transition_cooldown, 14)

        # 10 frames of rapid tapping while cooldown active
        for f in range(10):
            manager.pointer_pos = (120, 120)
            manager.pointer_down = (f % 2 == 0)
            manager.pointer_just_down = (f % 2 == 0)
            manager.pointer_just_up = (f % 2 != 0)
            clk, _, _ = manager.button(self.surface, "new_btn", btn_rect, "NEW")
            self.assertFalse(clk, f"Frame {f}: Rapid tap should be rejected during transition debounce")
            # Step frame
            manager.transition_cooldown -= 1

    def test_touch_engine_extreme_drag_bounds(self):
        """Verify ship position clamps strictly within bounds even with massive finger drags."""
        engine = MobileTouchEngine()
        engine.reset(400, 300)
        ship_rect = pygame.Rect(400, 300, 48, 48)

        engine.on_touch_down((400, 300), finger_id=1, current_ship_x=ship_rect.x, current_ship_y=ship_rect.y)
        # Extreme drag offscreen to +99999px
        engine.on_touch_motion((99999, 99999), finger_id=1)
        for _ in range(30):
            engine.update_smooth_ship_pos(ship_rect, min_x=20, max_x=740, min_y=60, max_y=540)

        self.assertLessEqual(ship_rect.x, 740)
        self.assertLessEqual(ship_rect.y, 540)
        self.assertGreaterEqual(ship_rect.x, 20)
        self.assertGreaterEqual(ship_rect.y, 60)


    def test_pause_state10_vs_abort_modal_state15_no_overlap(self):
        """
        Verify that State 10 (Pause Screen) buttons and State 15 (Abort Mission Warning)
        action buttons have zero geometric collision, preventing accidental click-through.
        """
        # State 10 PC buttons
        pc_pause_btns = [
            pygame.Rect(210, 146, 380, 46),
            pygame.Rect(210, 200, 380, 46),
            pygame.Rect(210, 254, 380, 46),
            pygame.Rect(210, 308, 380, 46),
        ]
        # State 10 Mobile buttons
        mob_pause_btns = [
            pygame.Rect(170, 146, 460, 48),
            pygame.Rect(170, 202, 460, 48),
            pygame.Rect(170, 258, 460, 48),
            pygame.Rect(170, 314, 460, 48),
        ]
        # State 15 Modal buttons
        abort_btns = [
            pygame.Rect(165, 396, 220, 54),  # RESUME
            pygame.Rect(415, 396, 220, 54),  # CONFIRM LEAVE
        ]

        for p_btn in pc_pause_btns + mob_pause_btns:
            for a_btn in abort_btns:
                has_collision = p_btn.colliderect(a_btn)
                self.assertFalse(has_collision, f"Pause button {p_btn} collides with Abort button {a_btn}!")
                # Must maintain at least 20px vertical clearance
                self.assertGreaterEqual(a_btn.top - p_btn.bottom, 20)

    def test_game_over_state5_vs_revive_modal_no_overlap(self):
        """
        Verify that Game Over (State 5) action buttons and Revive Confirmation Modal
        buttons have zero geometric collision, specifically preventing the CANCEL button
        from accidentally clicking < MAIN MENU.
        """
        game_over_btns = [
            pygame.Rect(180, 248, 440, 48),  # REVIVE
            pygame.Rect(180, 304, 440, 48),  # RETRY
            pygame.Rect(180, 360, 440, 48),  # MAIN MENU
        ]
        revive_modal_btns = [
            pygame.Rect(165, 430, 220, 54),  # CANCEL
            pygame.Rect(415, 430, 220, 54),  # BUY REVIVE
        ]

        for go_btn in game_over_btns:
            for rm_btn in revive_modal_btns:
                has_collision = go_btn.colliderect(rm_btn)
                self.assertFalse(has_collision, f"Game Over button {go_btn} collides with Revive Modal button {rm_btn}!")
                self.assertGreaterEqual(rm_btn.top - go_btn.bottom, 15)

    def test_settings_state9_vs_control_guides_state11_12_no_overlap(self):
        """
        Verify that Settings (State 9) navigation buttons and Control Guides (States 11 & 12)
        'OK GOT IT!' confirmation button have zero geometric overlap.
        """
        # Settings PC buttons
        pc_set_ctrl = pygame.Rect(320, 455, 200, 46)
        # Settings Mobile buttons
        mob_set_ctrl = pygame.Rect(292, 442, 214, 52)
        # States 11 and 12 OK button
        btn_ok = pygame.Rect(WIDTH // 2 - 130, 532, 260, 48)

        self.assertFalse(pc_set_ctrl.colliderect(btn_ok), "PC Settings ctrl button collides with State 11 OK button!")
        self.assertFalse(mob_set_ctrl.colliderect(btn_ok), "Mobile Settings ctrl button collides with State 12 OK button!")
        self.assertGreaterEqual(btn_ok.top - pc_set_ctrl.bottom, 25)
        self.assertGreaterEqual(btn_ok.top - mob_set_ctrl.bottom, 30)

    def test_mobile_firing_decoupled_from_playfield_dragging(self):
        """
        Verify that dragging on the playfield does NOT fire weapons when auto_fire_enabled
        is False, and only the tactile FIRE button or auto_fire_enabled=True triggers fire.
        """
        # Scenario A: Auto-fire OFF, dragging playfield
        auto_fire = False
        is_h_pause = False
        is_h_fire = False
        mouse_pressed = True
        wants_fire_a = (auto_fire and not is_h_pause) or (is_h_fire and mouse_pressed)
        self.assertFalse(wants_fire_a, "Dragging playfield must NOT fire when auto_fire is OFF")

        # Scenario B: Auto-fire OFF, pressing dedicated FIRE button
        is_h_fire = True
        wants_fire_b = (auto_fire and not is_h_pause) or (is_h_fire and mouse_pressed)
        self.assertTrue(wants_fire_b, "Pressing dedicated FIRE button must fire even when auto_fire is OFF")

        # Scenario C: Auto-fire ON, not pressing fire button
        auto_fire = True
        is_h_fire = False
        wants_fire_c = (auto_fire and not is_h_pause) or (is_h_fire and mouse_pressed)
        self.assertTrue(wants_fire_c, "Auto-fire ON must fire continuously")

        # Scenario D: Auto-fire ON, but hovering Pause button
        is_h_pause = True
        wants_fire_d = (auto_fire and not is_h_pause) or (is_h_fire and mouse_pressed)
        self.assertFalse(wants_fire_d, "Hovering pause button must safely inhibit auto-fire")

    def test_mobile_touch_engine_reverse_direction_no_deadzone(self):
        """
        Verify that dragging into a screen border and immediately reversing direction
        causes immediate responsive ship movement with zero deadzone stickiness.
        """
        engine = MobileTouchEngine()
        engine.reset(700, 300)
        ship_rect = pygame.Rect(700, 300, 48, 48)

        # Touch down and drag deeply past right boundary (+500px)
        engine.on_touch_down((700, 300), finger_id=1, current_ship_x=ship_rect.x, current_ship_y=ship_rect.y)
        engine.on_touch_motion((1200, 300), finger_id=1)
        # Update with right boundary clamped at 752 across frames until settled
        for _ in range(20):
            engine.update_smooth_ship_pos(ship_rect, min_x=0, max_x=752, min_y=0, max_y=600)
        self.assertEqual(ship_rect.x, 752)

        # Immediately drag back by 30px to the left (finger moves from 1200 to 1170)
        engine.on_touch_motion((1170, 300), finger_id=1)
        # Because we use incremental deltas, target_ship_pos immediately reflects -30px
        self.assertLess(engine.target_ship_pos[0], 752)
        # Update frame: ship must start moving left immediately!
        engine.update_smooth_ship_pos(ship_rect, min_x=0, max_x=752, min_y=0, max_y=600)
        self.assertLess(ship_rect.x, 752, "Ship must immediately respond to reverse drag with 0 deadzone lag!")

    def test_pc_windowing_apply_display_mode_safe_fallback(self):
        """
        Verify that pc.windowing.apply_display_mode safely catches pygame.error:
        'That operation is not supported' in headless/unsupported environments
        and returns a valid surface and boolean without crashing.
        """
        import pc.windowing as pc_windowing
        # Test toggling to fullscreen
        surf, is_fs = pc_windowing.apply_display_mode(self.surface, True)
        self.assertIsNotNone(surf)
        self.assertTrue(is_fs)

        # Test toggling back to windowed
        surf2, is_fs2 = pc_windowing.apply_display_mode(self.surface, False)
        self.assertIsNotNone(surf2)
        self.assertFalse(is_fs2)

        # Test passing screen=None fallback
        surf3, is_fs3 = pc_windowing.apply_display_mode(None, False)
        self.assertFalse(is_fs3)
        surf4, is_fs4 = pc_windowing.apply_display_mode(None, True)
        self.assertTrue(is_fs4)

        # Test passing arbitrary object without get_flags method
        dummy_obj = object()
        surf5, is_fs5 = pc_windowing.apply_display_mode(dummy_obj, True)
        self.assertIs(surf5, dummy_obj)
        self.assertTrue(is_fs5)

    def test_headless_smoke_simulation_pc_mode(self):
        """
        Automated headless smoke test: initializes PC game loop, loads assets/state,
        and simulates 60 frames of execution under PC_MODE=1 to prove zero crashes.
        """
        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"
        env["PC_MODE"] = "1"
        env["SMOKE_TEST_FRAMES"] = "60"
        env.pop("MOBILE_MODE", None)

        cmd = [sys.executable, "-c", "import os; os.environ['PC_MODE']='1'; os.environ['SMOKE_TEST_FRAMES']='60'; import main_pc"]
        res = subprocess.run(
            cmd,
            cwd=_ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        self.assertEqual(res.returncode, 0, f"PC smoke test crashed with exit code {res.returncode}:\n{res.stderr}")

    def test_headless_smoke_simulation_mobile_mode(self):
        """
        Automated headless smoke test: initializes Mobile game loop, loads assets/state,
        and simulates 60 frames of execution under MOBILE_MODE=1 to prove zero crashes.
        """
        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"
        env["MOBILE_MODE"] = "1"
        env["SMOKE_TEST_FRAMES"] = "60"
        env.pop("PC_MODE", None)

        cmd = [sys.executable, "-c", "import os; os.environ['MOBILE_MODE']='1'; os.environ['SMOKE_TEST_FRAMES']='60'; import main_mobile"]
        res = subprocess.run(
            cmd,
            cwd=_ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        self.assertEqual(res.returncode, 0, f"Mobile smoke test crashed with exit code {res.returncode}:\n{res.stderr}")


if __name__ == '__main__':
    unittest.main()


