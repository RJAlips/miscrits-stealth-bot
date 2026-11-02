# MiscritsBot

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg)

An open-source visual automation tool for **Miscrits: World of Creatures**. Built in Python, **MiscritsBot** automates bush searching, wild encounter combat routines, and multi-slot team leveling through high-speed screen capture and real-time computer vision template matching.

---

## ✨ Features

- **Blazing Fast Capture**: Utilizes `mss` for ultra-low-latency screen grabbing with minimal CPU/GPU overhead.
- **Visual State Engine**: OpenCV template matching tracks bushes, battle screens, turn phases, attack prompts, and post-battle rewards.
- **Automated Combat & Rotation**:
  - Automatically executes primary attack abilities.
  - Clears reward windows, level-up popups, and victory screens.
  - Supports 4-slot team rotation to distribute XP across under-leveled Miscrits.
- **Configurable Failsafes**:
  - Randomized click offsets and humanized sleep intervals to minimize rigid macro behavior.
  - Global emergency killswitch (`F12` or `ESC`) to stop execution instantly.
  - Window focus check to prevent misclicks across unrelated applications.
- **Standalone Executable Support**: Cleanly bundles into a single `.exe` using PyInstaller without external Python environment dependencies.

---

## 🛠️ Tech Stack

- **Core**: Python 3.10+
- **Vision**: `opencv-python`, `numpy`
- **Screen Capture**: `mss`
- **Input & Controls**: `pyautogui`, `pynput`
- **GUI / Setup**: `tkinter` (optional dashboard/status display)
- **Packaging**: `pyinstaller`

---

## 📁 Repository Structure

```text
MiscritsBot/
│
├── assets/                  # Target template images for OpenCV
│   ├── bushes/              # Bush and spawn node visual templates
│   ├── buttons/             # Fight, attack, keep, and next buttons
│   └── states/              # Victory, defeat, and level-up indicators
│
├── src/
│   ├── core/
│   │   ├── capture.py       # High-speed mss frame grabber
│   │   ├── detector.py      # OpenCV template matching & thresholding
│   │   └── controller.py    # Randomized inputs and mouse jitter logic
│   ├── bot.py               # Main state machine loop
│   └── gui.py               # Tkinter status & toggle window
│
├── config.json              # Custom thresholds, timings, and hotkeys
├── main.py                  # Entry point
├── requirements.txt         # Project dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Windows 10 / 11
- Python 3.10 or higher
- The Miscrits client or browser running at **100% display scaling** (1920x1080 recommended for default templates)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RJAlips/MiscritsBot.git
   cd MiscritsBot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

Tune your timings and match thresholds in `config.json`:

```json
{
  "confidence_threshold": 0.85,
  "action_delay_range": [0.35, 0.75],
  "killswitch_key": "f12",
  "enable_random_jitter": true,
  "max_search_attempts": 5,
  "auto_heal_at_hp_percent": 25
}
```

> **Tip:** If the bot fails to detect nodes or buttons due to resolution or visual style differences, capture custom `.png` crops of your target elements and replace the corresponding images in the `assets/` folder.

---

## 🎮 Usage

1. Start your **Miscrits: World of Creatures** client and navigate to your target farming area.
2. Launch the bot:
   ```bash
   python main.py
   ```
3. Switch focus back to the Miscrits window.
4. Press the designated start key (default: `F8`).
5. **Emergency Stop**: Press `F12` at any time to immediately kill the script.

### Building a Standalone Executable

To generate a standalone `.exe`:

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "assets;assets" main.py
```

---

## ⚠️ Disclaimer

This project is developed strictly for **educational and research purposes** exploring computer vision and automated input interaction in desktop environments. 

- Use of automation software may violate the Terms of Service of third-party game services.
- The repository authors and contributors assume no liability for account penalties, bans, or unintended gameplay outcomes resulting from the use of this software. Use at your own discretion.

---

## 📄 License

Distributed under the [MIT License](LICENSE).