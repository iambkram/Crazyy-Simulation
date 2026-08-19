# 🚀 Crazyy Simulation

**Official Repository:** [https://github.com/iambkram/Crazyy-Simulation](https://github.com/iambkram/Crazyy-Simulation)  
**Developer:** `@iambkram`  
**Version:** `1.0.0` · Survival & Galaxy Warfare Edition  

A high-octane, top-down cosmic arcade space shooter engineered in Python & Pygame. Battle through dynamic galactic environments, survive intense enemy barrages, overcome terrifying sector bosses, and customize your starship to supremacy.

---

## 🌟 Key Features

### 🌌 3 Dynamic Cosmic Sectors
* **Galaxy Sector (Sector 1):** Classic stellar battlegrounds with asteroid hazards and escalating enemy squadrons.
* **Nebula Zone (Sector 2):** Dense purple gas clouds featuring high-speed fighter strikes and elite interceptors *(Unlocks after completing 30 Galaxy missions)*.
* **Black Hole Singularity (Sector 3):** Extreme gravitational hazard zone where asteroids and ships are relentlessly dragged toward the central event horizon *(Unlocks after completing 30 Nebula missions)*.

### 🎯 40 Progressive Missions Per Sector
* **120 Unique Mission Tiers:** Progress sequentially from Novice skirmishes to Mythic boss encounters.
* **Smart Unlock Progression:** Clear missions one by one to forge your path across the galaxy.

### 💥 Advanced VFX & Combat Engine
* **Supernova Cataclysm:** Multi-layered boss death sequence featuring screen shake, shockwaves, 150+ debris shards, pulsing god-rays, and multi-stage explosions.
* **Dynamic Engine Thrusters:** Real-time particle propulsion systems for player and enemy starships.
* **Live Main Menu Combat AI:** Autonomous background dogfights between player and enemy starships right on the main menu.
* **Cinematic Neon Branding:** 5.2s atmospheric "IAMBKRAM" intro sequence with audio synchronization.

### 🎮 Dual Control Schemes & Full Keyboard Navigation
* **100% Keyboard Playable:** Full menu navigation (arrows, Tab, Enter, Escape) and flight controls.
* **Mobile / Touch Friendly:** Relative drag-to-steer mechanics, auto-fire, and touch debounce scrolling.

### 🖥 Seamless Display & Performance Suite
* **Instant F11 Fullscreen / Windowed Toggle:** Hardware-scaled rendering (`pygame.SCALED`) supporting any monitor aspect ratio without distortion.
* **Surface Caching & Extreme Optimization:** Pre-allocated scratch surfaces and LRU text caching ensuring smooth 60 FPS gameplay on low-end PCs and mobile devices.
* **Visual Quality Presets:** Switch between `LOW`, `MEDIUM`, and `HIGH` visual fidelity to scale particle counts and god-ray densities.

---

## 🕹 Controls & Keybindings Reference

### 🖥 PC / Desktop Controls

| Action | Primary Key | Secondary Key | Notes |
| :--- | :--- | :--- | :--- |
| **Move Starship** | `W` `A` `S` `D` | `↑` `←` `↓` `→` (Arrows) | 2D tactical maneuvering & dodging |
| **Fire Laser Cannon** | `Spacebar` | `Left Mouse Button` | Continuous auto-fire barrage |
| **Pause / Resume** | `P` | `Escape` | Toggles in-game pause modal |
| **Toggle Fullscreen** | `F11` | In-game Settings | Seamless Fullscreen ↔ Windowed toggle |
| **Toggle FPS Counter** | `F` | In-game Settings | Real-time color-coded performance monitor |
| **Mute / Unmute Music** | `M` | In-game Settings | Instant background audio mute |
| **Menu Navigation** | `↑` `↓` (Arrows) / `Tab` | `Mouse Hover` | Focuses buttons with neon indicator |
| **Menu Confirm / Select**| `Enter` / `Return` | `Mouse Click` | Activates focused button |
| **Menu Back / Dismiss** | `Escape` | `← Back` Button | Closes popups or returns to previous screen |
| **Quick Retry (Defeat)** | `R` | `↻ Retry` Button | Instantly restarts current mission |

### 📱 Mobile / Touch Controls

| Action | Gesture | Notes |
| :--- | :--- | :--- |
| **Move & Steer** | Slide / Drag Finger | Starship follows drag vector with speed clamping |
| **Fire Weapons** | Hold Screen | Auto-fires lasers continuously while touching |
| **Scroll Menus** | Vertical Drag | Drag-scroll mission grids with touch velocity filtering |

---

## ⚙️ In-Game Settings Configuration

Accessible via **⚙ SETTINGS** on the Main Menu or In-Game Pause:

1. **Control Scheme:** Switch between **📱 MOBILE (Touch)** and **🖥 PC / DESKTOP (WASD + Space)**.
2. **Music & SFX Sliders:** Independent 0%–100% volume control with live audio feedback.
3. **Display Mode:** Toggle between **FULLSCREEN** and **WINDOWED** mode.
4. **Show FPS Counter:** Displays a lightweight, real-time FPS overlay in the top-right corner.
5. **Screen Shake Effects:** Toggle camera rumble and impact feedback.
6. **Visual Quality:**
   * **LOW:** 50 debris particles, 4 god-rays, 40% thruster density, 60 background stars *(Best for low-spec hardware)*.
   * **MEDIUM:** 100 debris particles, 8 god-rays, 70% thruster density, 120 background stars.
   * **HIGH:** 150 debris particles, 12 god-rays, 100% thruster density, 180 background stars *(Maximum visual spectacle)*.

---

## 💾 Save Data Format (`save.json`)

Player progress, unlocked sectors, upgrade stats, and settings are automatically saved in `save.json`:

```json
{
    "coins": 0,
    "hp": 200,
    "hp_step": 0,
    "speed": 7,
    "speed_step": 0,
    "bullets": 1,
    "bullet_step": 0,
    "max_galaxy_level": 1,
    "max_nebula_level": 1,
    "max_blackhole_level": 1,
    "env2_unlocked": false,
    "env3_unlocked": false,
    "control_type": "PC",
    "music_vol": 0.5,
    "sfx_vol": 0.7,
    "show_fps": false,
    "visual_quality": "high",
    "screen_shake": true,
    "display_mode": "fullscreen"
}
```

---

## 📦 Installation & Setup

### Prerequisites
* Python 3.9+ or higher
* [Pygame](https://www.pygame.org/) (`pygame>=2.5.0`)

### Quick Start (Run Directly)
```bash
# 1. Clone the repository
git clone https://github.com/iambkram/Crazyy-Simulation.git
cd Crazyy-Simulation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the game
python main.py
```

### Windows Setup Wizard
You can also run the cyber-themed Windows Setup Wizard to install desktop and start menu shortcuts:
```bash
python setup.py
```

---

## 📁 Codebase Architecture

```
Crazyy-Simulation/
├── main.py              # Main game loop, state machine (States 0-20), combat logic & HUD
├── settings.py          # Global constants, color palette, upgrade costs & quality presets
├── assets.py            # Font/Sound loaders, LRU text cache & UI drawing helpers
├── branding.py          # Cinematic 5.2s "IAMBKRAM" intro logo animation
├── menu_battle.py       # Autonomous live combat AI simulation for Main Menu background
├── vfx.py               # Particle engine (Thrusters, Supernova Boss Cataclysm, Screen Shake)
├── setup.py             # 5-step cyber-neon Windows installer wizard
├── launcher.c           # Native C Windows launcher (compiles to Crazyy-Simulation.exe)
├── save.json            # Persistent player profile & game configuration
├── game_assets/         # Audio files, backgrounds, enemy sprites & textures
└── icon.ico             # Application icon
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by **[@iambkram](https://github.com/iambkram)**
