# Crazyy Simulation

**Repository:** [https://github.com/iambkram/Crazyy-Simulation](https://github.com/iambkram/Crazyy-Simulation)

A top-down arcade space shooter built with Python and Pygame. Navigate through various cosmic environments, battle waves of enemy ships, defeat powerful bosses, and upgrade your ship using collected coins.

## Features

- **Multiple Environments:** Unlock and explore different cosmic backdrops including the Galaxy, Nebula, and Blackhole.
- **Dynamic Combat:** Fight against diverse enemy types (Fighters, Elites, Heavies) and dodge their attacks.
- **Boss Battles:** Face off against powerful boss ships that scale in difficulty as you progress through the levels.
- **Upgrades & Store:** Collect coins during gameplay to upgrade your ship's health (HP), speed, and firepower (bullets).
- **Save System:** Your progress, including unlocked levels and purchased upgrades, is automatically saved.
- **Customizable Controls:** Choose between PC or Mobile control layouts (as configured in settings).

## Prerequisites

- Python 3.x
- [Pygame](https://www.pygame.org/)

## Installation

1. Clone or download the repository.
2. Install the required dependency:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

1. Run the game via the main script:
   ```bash
   python main.py
   ```
2. Navigate the main menu to select an environment and level.
3. If this is your first time playing, be sure to visit the **Settings** menu to select your preferred control type.
4. **Missions:** Select an environment to start playing. Unlock new environments by completing levels.
5. **Store:** Use your collected coins to buy upgrades for your ship.

## Project Structure

- `main.py`: The core game loop, state management, and rendering logic.
- `assets.py`: Handles loading and managing images, sounds, and fonts.
- `settings.py`: Contains game configurations, constants, and color definitions.
- `game_assets/`: Directory containing all the images, sounds, and music used in the game.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
