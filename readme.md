# Miscrits Stealth Automation Suite

An external, computer-vision desktop automation suite designed for *Miscrits: World of Creatures*. Powered by OpenCV, MSS, and CustomTkinter, this utility operates completely outside the game process—utilizing visual template matching, biomechanical mouse movement curves, and adaptive elemental combat logic without memory injection or packet tampering.

---

## Features

###  Anti-Detection & Biomechanical Stealth
* **Cubic Bézier Mouse Curves:** Moves the cursor along natural, randomized arcs with smooth acceleration and deceleration rather than linear or instant snaps.
* **Gaussian Click Dispersion:** Replaces robotic single-pixel clicks with a 2D Gaussian bell-curve distribution across button surfaces.
* **Variable Log-Normal Delays:** Reaction times and mouse-down holding durations vary dynamically to mimic human physical switch action.
* **Human AFK Simulation:** Periodically introduces randomized fatigue pauses (35–85s every 15–25 minutes).

###  Adaptive 4-Miscrit Combat Engine
* **Elemental Advantage Matrix:** Built-in table covering all six primary elements (*Water, Fire, Nature, Earth, Lightning, Wind*).
* **Dynamic Attack Switching:** Automatically detects active Miscrit and enemy element type:
  * **Weakness Detected:** Automatically switches to the physical attack (`mX_phys_atk`) to bypass elemental resistance.
  * **Advantage/Neutral:** Prioritizes elemental moves (`mX_elem_atk`) for maximum burst damage.
* **HP-Gated Capture & Chip Logic:** Uses HSV color filtering across the calibrated enemy health bar to use heavy attacks at high HP, switch to chip moves under 60%, and throw capture items when below the target threshold.
* **Post-Capture Grade Filtering:** Evaluates captured Miscrits (`S+`, `S`, `A+`) and auto-releases anything below your configured grade threshold.

### 4-Slot Auto-Training & Evolution Pipeline
* **Pre-Train Revive Routine:** Automatically triggers team healing before opening the Training window, ensuring fainted or dead Miscrits are restored and eligible to level up.
* **4-Slot Position Memory:** Cycles through all four party slots via fixed screen coordinates (`F9`) or edge-detection fallback if portraits are darkened.
* **Popup & Evolution Resolver:** Automatically clears stat allocation screens, handles the *New Ability Added* prompt, and confirms level milestones/evolutions.

###  Built-In Workflow Tools
* **In-App Screen Snipper:** Snip game buttons directly into `/assets` via an interactive overlay—no third-party snipping tools needed.
* **Discord Webhook Telemetry:** Transmits event embeds alongside in-game screenshots for rare encounters, captures, and evolutions.
* **Coordinate Persistence:** All hotkey-calibrated coordinates and GUI parameters persist to `config.json`.

---

## Hotkey Reference

| Hotkey | Function | Scope |
| :---: | :--- | :--- |
| **`F6`** | Save Overworld Bush/Patrol Coordinate | Overworld |
| **`F7`** | Calibrate Enemy HP Bar (Click 1: Top-Left, Click 2: Bottom-Right) | Combat |
| **`F8`** | **Emergency Stop / Killswitch** | Global |
| **`F9`** | Save Miscrit Slot Position (Press 4 times for Slots 1 to 4) | Training Window |
| **`F10`** | Save Overworld "Train" HUD Button Position | Overworld |
| **`F11`** | Save Overworld "Heal" HUD Button Position | Overworld |

---

## Installation & Setup

### Prerequisites
* Windows 10 / 11
* Python 3.10 to 3.12 (with `pip` added to PATH)
* Game display scaling set to match native screen resolution (100% recommended)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/miscrits-stealth-suite.git
cd miscrits-stealth-suite
pip install opencv-python mss numpy pydirectinput keyboard customtkinter requests pillow pyinstaller
```

### 2. Launch the Application
```bash
python bot.py
```
> **Note:** Run your terminal or IDE with Administrator privileges so global hotkeys and simulated hardware inputs register while the game window is focused.

---

## First-Time Configuration Guide

1. **Set Overworld HUD Hotkeys:**
   * Stand in the overworld with your team visible.
   * Hover over the HUD **Heal** button and press **`F11`**.
   * Hover over the HUD **Train** button and press **`F10`**.
2. **Calibrate Training Slots:**
   * Open the Training window manually.
   * Hover your cursor over **Miscrit #1** on the list and press **`F9`**.
   * Repeat sequentially for **#2 (`F9`)**, **#3 (`F9`)**, and **#4 (`F9`)**.
3. **Calibrate the Enemy HP Bar:**
   * Enter any battle and press **`F7`** while hovering over the **top-left corner** of the enemy health bar.
   * Move your cursor to the **bottom-right corner** of the enemy health bar and press **`F7`** again.
4. **Snip Core Buttons via the GUI Dropdown:**
   * Select a target from the dropdown, click **Snip Selected**, and drag a tight box around the element:
     * `train_now_btn`: The base level-up button inside the training window.
     * `train_confirm_btn`: The "Continue" button after stats increase.
     * `bush_1` to `bush_3`: Your primary overworld search objects.
     * `m1_elem_atk` & `m1_phys_atk`: Active moves for your team.

---

## Template Directory Structure (`assets/`)

```text
assets/
├── bush_1.png ... bush_5.png      # Overworld clickable nodes
├── m1_elem_atk.png ...            # Team elemental abilities
├── m1_phys_atk.png ...            # Team neutral physical abilities
├── enemy_water.png ...            # Enemy element badges next to HP
├── train_now_btn.png              # Primary training button
├── train_confirm_btn.png          # Post-training continue button
├── new_ability_btn.png            # New move unlock dialog confirm
├── evolve_continue_btn.png        # Evolution animation dismiss
├── close_train_btn.png            # Training window close button
├── keep_btn.png / release_btn.png # Capture review actions
└── continue_btn.png               # Post-battle reward dismiss
```

---

## Compiling to Standalone `.exe`

To generate a portable executable including all dark-mode CustomTkinter assets:

```bash
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "MiscritsStealthSuite" --collect-all customtkinter bot.py
```

Move your `assets/` folder and any existing `config.json` into the `dist/` folder alongside `MiscritsStealthSuite.exe` before running.

---

## Disclaimer

This software is developed strictly for educational, automation research, and accessibility testing purposes. Use of third-party automation tools may violate the target platform's Terms of Service. The maintainers assume no liability for account suspensions or penalties incurred through the use of this project.