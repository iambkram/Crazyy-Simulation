# 🚀 Crazyy Simulation

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Pygame Version](https://img.shields.io/badge/Pygame-2.5.0%2B-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

**Official Repository:** [https://github.com/iambkram/Crazyy-Simulation](https://github.com/iambkram/Crazyy-Simulation)  
**Developer:** `@iambkram`  
**Edition:** *Survival & Galaxy Warfare Edition*

A high-octane, top-down cosmic arcade space shooter engineered in Python & Pygame. Battle through dynamic galactic sectors, survive escalating enemy squadrons, overcome terrifying multi-tier sector bosses, upgrade your starship attachments in the Space Store, and seamlessly sync your save data across cloud and guest profiles.

---

## 🌟 Key Features

### 🌌 3 Dynamic Cosmic Sectors
* **Galaxy Sector (Sector 1):** Classic stellar battlegrounds with asteroid hazards and escalating enemy squadrons.
* **Nebula Zone (Sector 2):** Dense purple gas clouds featuring high-speed fighter strikes and elite interceptors *(Unlocks after completing 30 Galaxy missions)*.
* **Black Hole Singularity (Sector 3):** Extreme gravitational hazard zone where asteroids and ships are relentlessly dragged toward the central event horizon *(Unlocks after completing 30 Nebula missions)*.

### 🎯 40 Progressive Missions Per Sector (120 Total)
* **120 Unique Mission Tiers:** Progress sequentially from novice skirmishes to mythic boss encounters.
* **Smart Unlock Progression:** Clear missions one by one to forge your path across the galaxy.

### 👾 Tiered Boss Battle & State Machine
* **Levels 1 – 10 (Easy Tier):** Balanced entry-level HP pool, gentle drift movement, calm straight-line fire, and relaxed attack rhythms.
* **Levels 11 – 30 (Moderate – Hard Tier):** Unlocks aggressive screen sweeps with dynamic banking turn tilt animations, and corner hunt tracking.
* **Levels 31 – 40 (Hard / Expert Tier):** Full bullet-hell mastery! Features 360-degree nova ring bursts, spiral bullet storms, dive-bomb swoop shakes, and violent rage tremors.

### 🛒 Space Store & Upgrades
* **Shield HP:** Boost maximum ship durability.
* **Engine Speed:** Increase maneuvering and dodging agility.
* **Parallel Bullets:** Multiply your forward laser cannon output.
* **Permanent Persistence:** Upgrades automatically save locally and sync securely with MongoDB cloud storage.

### ✨ Advanced VFX & Combat Engine
* **Cinematic Visual Quality Modes:**
  * **Cinematic (High):** Dynamic thruster flame trails on all enemy ships, rapid asteroid rotations, glowing cannon muzzle flashes, and player damage blink feedback.
  * **Balanced (Medium):** Stable performance with natural asteroid rotation and streamlined particles.
  * **Performance (Low):** Ultra-lightweight rendering optimized for high framerates on low-spec hardware.
* **Supernova Cataclysm:** Multi-layered boss death sequence featuring screen shake, shockwaves, debris shards, pulsing god-rays, and multi-stage explosions.
* **Live Main Menu Combat AI:** Autonomous background dogfights between player and enemy starships right on the main menu.
* **Cinematic Neon Branding:** 5.2s atmospheric "IAMBKRAM" intro sequence with synchronized audio.

### 🔐 Secure Cloud Authentication & Save Sync
* **Google OAuth 2.0:** Secure single-sign-on for persistent cloud saves.
* **Guest Mode:** Instant local play with encrypted session tokens and seamless one-click Google account migration.
* **Encrypted Token Storage:** Local sessions encrypted via AES/Fernet encryption.

---

## 🎮 Controls & Keybindings Reference

### 💻 PC / Desktop Controls

| Action | Primary Key | Secondary Key | Notes |
| :--- | :--- | :--- | :--- |
| **Move Starship** | `W` `A` `S` `D` | `↑` `↓` `←` `→` (Arrows) | 2D tactical maneuvering & dodging |
| **Fire Laser Cannon** | `Spacebar` | `Left Mouse Button` | Continuous laser cannon barrage |
| **Pause / Resume** | `P` | `Escape` | Toggles in-game pause modal |
| **Toggle Fullscreen** | `F11` | In-game Settings | Seamless Fullscreen ↔ Windowed toggle |
| **Toggle FPS Counter** | `F` | In-game Settings | Real-time color-coded performance monitor |
| **Mute / Unmute Music** | `M` | In-game Settings | Instant background audio toggle |
| **Menu Navigation** | `↑` `↓` (Arrows) / `Tab` | `Mouse Hover` | Focuses buttons with neon indicator |
| **Menu Confirm / Select**| `Enter` / `Return` | `Mouse Click` | Activates focused button |
| **Menu Back / Dismiss** | `Escape` | `← Back` Button | Closes popups or returns to previous screen |
| **Quick Retry (Defeat)** | `R` | `↻ Retry` Button | Instantly restarts current mission |

### 📱 Mobile / Touch Controls

| Action | Gesture | Notes |
| :--- | :--- | :--- |
| **Move & Steer** | Slide / Drag Finger | Starship follows drag vector with speed clamping |
| **Fire Weapons** | Hold Screen / Auto-Fire | Fires lasers continuously while touching |
| **Scroll Menus** | Vertical Drag / Mouse Wheel | Smooth velocity scrolling with click debouncing |

---

## ⚙️ In-Game Settings Configuration

Accessible via **⚙ SETTINGS** on the Main Menu or In-Game Pause:

1. **Control Scheme:** Switch between **📱 MOBILE (Touch)** and **💻 PC / DESKTOP (WASD + Space)**.
2. **Music & SFX Sliders:** Independent 0%–100% volume control with live audio feedback for all music and sound effects (including cannon firing).
3. **Display Mode:** Toggle between **FULLSCREEN** and **WINDOWED** mode (`F11`).
4. **Show FPS Counter:** Displays a lightweight, real-time FPS overlay in the top-right corner.
5. **Screen Shake Effects:** Toggle camera rumble and impact feedback.
6. **Visual Quality:**
   * **PERFORMANCE:** Streamlined rendering for low-spec systems.
   * **BALANCED:** Optimal blend of visual effects and 60 FPS performance.
   * **CINEMATIC:** Maximum visual fidelity with procedural thruster exhaust, muzzle flares, and fast debris rotation.

---

## 📁 Project Structure

```
Crazyy-Simulation/
├── game_assets/             # Audio tracks, sound effects, backgrounds & ship sprites
├── src/
│   ├── ui/
│   │   ├── auth_ui.py       # Google OAuth, user registration & login screens
│   │   ├── level_select_ui.py # Sector and 40-mission grid selection UI
│   │   ├── settings_ui.py   # Settings menu, audio sliders & controls UI
│   │   └── store_ui.py      # Space Store and attachment upgrade modals
│   ├── assets.py            # Font/Sound loaders, LRU text cache & UI render helpers
│   ├── branding.py          # Cinematic 5.2s "IAMBKRAM" intro logo animation
│   ├── cloud_sync.py        # MongoDB Atlas sync, Google OAuth & token encryption
│   ├── main.py              # Main game loop, state machine & combat coordinator
│   ├── menu_battle.py       # Autonomous live combat AI simulation for Main Menu
│   ├── settings.py          # Global constants, color palette & upgrade definitions
│   └── vfx.py               # Visual effects engine (Thrusters, Supernova, Shakes)
├── .env.example             # Template for MongoDB URI and OAuth credentials
├── .gitignore               # Excludes secrets, binaries, build caches & tokens
├── icon.ico                 # Application window and build icon
├── LICENSE                  # MIT License
├── README.md                # Comprehensive documentation
├── requirements.txt         # Project Python dependencies
└── setup.py                 # Windows installer wizard packager
```

---

## 🚀 Installation & Setup

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

# 3. Configure environment variables (Optional for local-only play)
cp .env.example .env

# 4. Launch the game
python src/main.py
```

### Build Standalone Executables (PyInstaller)
To compile the standalone Windows executable and installer wizard:
```bash
# Build main game binary
pyinstaller --noconfirm --clean --onefile --windowed --icon=icon.ico --name "Crazyy-Simulation" --add-data="game_assets;game_assets" --add-data="icon.ico;." src/main.py

# Build setup wizard installer
pyinstaller --noconfirm --clean --onefile --windowed --icon=icon.ico --name "setup" --add-data="Crazyy-Simulation.exe;." --add-data="game_assets;game_assets" --add-data="icon.ico;." setup.py
```

---

## 🔒 Security & Environment Configuration

The `.env` file contains your private database connection strings and OAuth client keys. **Never commit `.env` or session tokens to version control.**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the keys with your credentials:
   ```ini
   MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/CrazyySimulation?retryWrites=true&w=majority
   GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```
3. All authentication sessions stored locally (`session.token`) are encrypted with AES/Fernet encryption for privacy.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by **[@iambkram](https://github.com/iambkram)**
