import os
import sys
import io
import json
import time
import math
import random
import ctypes
import threading
import tkinter as tk
import cv2
import numpy as np
import mss
import requests
import pydirectinput
import keyboard
import customtkinter as ctk
from PIL import Image, ImageTk

# Fix Windows 125%/150% DPI scaling so mouse clicks match OpenCV coordinates 1:1
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

pydirectinput.PAUSE = 0.001

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

BUSH_TEMPLATES = ["bush_1", "bush_2", "bush_3", "bush_4", "bush_5"]
SLOT_TEMPLATES = ["slot_1", "slot_2", "slot_3", "slot_4"]

ELEMENTS = ["Water", "Fire", "Nature", "Earth", "Lightning", "Wind"]

# Which element each element is WEAK against (triggers Physical Attack switch)
WEAK_AGAINST = {
    "Water": "Nature",
    "Fire": "Water",
    "Nature": "Fire",
    "Earth": "Wind",
    "Lightning": "Earth",
    "Wind": "Lightning"
}

# Which element each element is STRONG against (triggers Elemental Attack boost)
STRONG_AGAINST = {
    "Water": "Fire",
    "Fire": "Nature",
    "Nature": "Water",
    "Earth": "Lightning",
    "Lightning": "Wind",
    "Wind": "Earth"
}

ENEMY_ELEMENT_TEMPLATES = {
    "Water": "enemy_water",
    "Fire": "enemy_fire",
    "Nature": "enemy_nature",
    "Earth": "enemy_earth",
    "Lightning": "enemy_lightning",
    "Wind": "enemy_wind"
}

POST_TRAIN_MODALS = [
    "new_ability_btn",
    "evolve_continue_btn",
    "evolve_btn",
    "train_confirm_btn",
    "continue_btn"
]

TEMPLATE_NAMES = [
    # Overworld Bushes
    "bush_1", "bush_2", "bush_3", "bush_4", "bush_5",
    # 4-Miscrit Elemental & Physical Combat Buttons
    "m1_elem_atk", "m1_phys_atk",  # Miscrit #1 Elemental & Physical attacks
    "m2_elem_atk", "m2_phys_atk",  # Miscrit #2 Elemental & Physical attacks
    "m3_elem_atk", "m3_phys_atk",  # Miscrit #3 Elemental & Physical attacks
    "m4_elem_atk", "m4_phys_atk",  # Miscrit #4 Elemental & Physical attacks
    # Enemy Element Icons (Snip the element badge next to enemy name/HP bar)
    "enemy_water", "enemy_fire", "enemy_nature",
    "enemy_earth", "enemy_lightning", "enemy_wind",
    # Fallback & Capture Combat Buttons
    "battle_attack", "chip_attack", "capture_btn", "target_miscrit",
    # Auto-Training, New Abilities & Evolution Templates
    "open_train_menu_btn", "ready_to_train",
    "slot_1", "slot_2", "slot_3", "slot_4",
    "train_now_btn", "train_confirm_btn", "new_ability_btn",
    "evolve_btn", "evolve_continue_btn", "close_train_btn",
    # Post-Battle & Rating Filter Templates
    "keep_btn", "release_btn", "confirm_release",
    "rating_s_plus", "rating_s", "rating_a_plus",
    "continue_btn", "level_up", "heal_btn"
]


class HumanInputEngine:
    """Precise biomechanical mouse movement with zero post-click stray cursor jumps."""

    @staticmethod
    def sleep_human(base_sec, variance=0.20):
        delay = base_sec * random.lognormvariate(0, variance)
        time.sleep(max(0.04, min(delay, base_sec * 2.2)))

    @staticmethod
    def gaussian_point_in_box(x, y, w, h):
        cx, cy = x + w / 2.0, y + h / 2.0
        gx = random.gauss(cx, w * 0.10)
        gy = random.gauss(cy, h * 0.10)
        clamped_x = int(max(x + w * 0.25, min(x + w * 0.75, gx)))
        clamped_y = int(max(y + h * 0.25, min(y + h * 0.75, gy)))
        return clamped_x, clamped_y

    @classmethod
    def bezier_move(cls, target_x, target_y):
        start_x, start_y = pydirectinput.position()
        dist = math.hypot(target_x - start_x, target_y - start_y)
        if dist < 4:
            pydirectinput.moveTo(int(target_x), int(target_y))
            return

        steps = max(8, min(32, int(dist / 22)))

        ctrl1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-25, 25)
        ctrl1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-25, 25)
        ctrl2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-15, 15)
        ctrl2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-15, 15)

        for i in range(1, steps + 1):
            t = i / steps
            u = t * t * (3 - 2 * t)
            bx = int((1 - u)**3 * start_x + 3 * (1 - u)**2 * u * ctrl1_x +
                     3 * (1 - u) * u**2 * ctrl2_x + u**3 * target_x)
            by = int((1 - u)**3 * start_y + 3 * (1 - u)**2 * u * ctrl1_y +
                     3 * (1 - u) * u**2 * ctrl2_y + u**3 * target_y)
            pydirectinput.moveTo(bx, by)
            time.sleep(random.uniform(0.002, 0.004))

        pydirectinput.moveTo(int(target_x), int(target_y))

    @classmethod
    def bezier_move_and_click(cls, target_x, target_y):
        cls.bezier_move(target_x, target_y)
        time.sleep(random.uniform(0.05, 0.09))
        pydirectinput.mouseDown(x=int(target_x), y=int(target_y))
        time.sleep(random.uniform(0.04, 0.08))
        pydirectinput.mouseUp(x=int(target_x), y=int(target_y))
        time.sleep(random.uniform(0.12, 0.18))


class SnippingOverlay(tk.Toplevel):
    """Full-screen interactive bounding-box snipper to crop templates directly in-app."""

    def __init__(self, parent, target_template_name, on_complete_callback):
        super().__init__(parent)
        self.target_name = target_template_name
        self.on_complete = on_complete_callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None

        with mss.mss() as sct:
            mon = sct.monitors[1]
            raw = np.array(sct.grab(mon))
            self.full_bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
            rgb = cv2.cvtColor(self.full_bgr, cv2.COLOR_BGR2RGB)
            self.pil_img = Image.fromarray(rgb)

        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.config(cursor="cross")

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.tk_img = ImageTk.PhotoImage(self.pil_img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        self.canvas.create_text(
            self.pil_img.width // 2, 40,
            text=f"Hold Left-Click & Drag tightly inside '{self.target_name}' (Press ESC to cancel)",
            fill="#00ffcc", font=("Arial", 18, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.cancel())

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="#00ff66", width=2
        )

    def on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, x2 = sorted([self.start_x, event.x])
        y1, y2 = sorted([self.start_y, event.y])
        self.destroy()

        if (x2 - x1) >= 6 and (y2 - y1) >= 6:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            crop = self.full_bgr[y1:y2, x1:x2]
            save_path = os.path.join(ASSETS_DIR, f"{self.target_name}.png")
            cv2.imwrite(save_path, crop)
            self.on_complete(True, f"Saved {self.target_name}.png ({x2 - x1}x{y2 - y1} px)")
        else:
            self.on_complete(False, "Snip cancelled (box too small).")

    def cancel(self):
        self.destroy()
        self.on_complete(False, "Snip cancelled.")


class MiscritsStealthBot:
    def __init__(self, log_callback):
        self.running = False
        self.mode = "XP_GRIND"
        self.rating_filter = "S or Higher"
        self.capture_hp_threshold = 28
        self.afk_breaks_enabled = True
        self.auto_train_enabled = True
        self.webhook_url = ""
        self.log = log_callback

        # Element assigned to each of your 4 party Miscrits
        self.team_elements = ["Fire", "Water", "Nature", "Earth"]

        with mss.mss() as sct:
            mon = sct.monitors[1]
            self.monitor = {
                "top": mon["top"],
                "left": mon["left"],
                "width": mon["width"],
                "height": mon["height"]
            }

        self.hp_bar_box = [980, 115, 1185, 132]
        self.hp_calib_stage = 0

        self.waypoints = []
        self.wp_index = 0
        self.bush_index = 0

        self.train_slots = []
        self.cached_slot_coords = {}
        self.open_train_pos = None
        self.heal_pos = None

        self.battles_since_heal = 0
        self.battles_since_train_check = 0
        self.train_needed_flag = False
        self.last_train_attempt_time = 0.0
        self.alerted_current_encounter = False

        self.last_modal_name = None
        self.same_modal_count = 0

        self.templates = {}
        self.load_config()
        self.load_templates()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.webhook_url = data.get("webhook_url", "")
                    self.hp_bar_box = data.get("hp_bar_box", self.hp_bar_box)
                    self.waypoints = [tuple(pt) for pt in data.get("waypoints", [])]
                    self.train_slots = [tuple(pt) for pt in data.get("train_slots", [])]
                    ot_pos = data.get("open_train_pos", None)
                    self.open_train_pos = tuple(ot_pos) if ot_pos else None
                    hl_pos = data.get("heal_pos", None)
                    self.heal_pos = tuple(hl_pos) if hl_pos else None
                    cached = data.get("cached_slot_coords", {})
                    self.cached_slot_coords = {k: tuple(v) for k, v in cached.items()}
                    self.rating_filter = data.get("rating_filter", "S or Higher")
                    self.capture_hp_threshold = data.get("capture_hp_threshold", 28)
                    self.auto_train_enabled = data.get("auto_train_enabled", True)
                    saved_elems = data.get("team_elements", None)
                    if saved_elems and len(saved_elems) == 4:
                        self.team_elements = saved_elems
            except Exception as e:
                self.log(f"Config load warning: {e}")

    def save_config(self):
        data = {
            "webhook_url": self.webhook_url.strip(),
            "hp_bar_box": self.hp_bar_box,
            "waypoints": self.waypoints,
            "train_slots": self.train_slots,
            "open_train_pos": list(self.open_train_pos) if self.open_train_pos else None,
            "heal_pos": list(self.heal_pos) if self.heal_pos else None,
            "cached_slot_coords": {k: list(v) for k, v in self.cached_slot_coords.items()},
            "rating_filter": self.rating_filter,
            "capture_hp_threshold": self.capture_hp_threshold,
            "auto_train_enabled": self.auto_train_enabled,
            "team_elements": self.team_elements
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log(f"Config save error: {e}")

    def load_templates(self):
        os.makedirs(ASSETS_DIR, exist_ok=True)
        self.templates.clear()
        for name in TEMPLATE_NAMES:
            path = os.path.join(ASSETS_DIR, f"{name}.png")
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.templates[name] = img

    def get_snipped_bushes(self):
        return [b for b in BUSH_TEMPLATES if b in self.templates]

    def send_discord_alert(self, title, description, bgr_frame=None, color=0x2ECC71):
        url = self.webhook_url.strip()
        if not url:
            return

        def _worker():
            try:
                payload = {
                    "username": "Miscrits Stealth Watcher",
                    "embeds": [{
                        "title": title,
                        "description": description,
                        "color": color,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }]
                }
                files = {}
                if bgr_frame is not None:
                    ok, buf = cv2.imencode(".png", bgr_frame)
                    if ok:
                        files["file"] = ("capture.png", io.BytesIO(buf.tobytes()), "image/png")
                        payload["embeds"][0]["image"] = {"url": "attachment://capture.png"}

                if files:
                    requests.post(url, data={"payload_json": json.dumps(payload)}, files=files, timeout=10)
                else:
                    requests.post(url, json=payload, timeout=10)
            except Exception as e:
                self.log(f"Webhook error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def record_waypoint(self):
        x, y = pydirectinput.position()
        self.waypoints.append((x, y))
        self.save_config()
        self.log(f"Bush Waypoint #{len(self.waypoints)} saved at ({x}, {y})")

    def record_train_slot(self):
        if len(self.train_slots) >= 4:
            self.train_slots.clear()
            self.log("Resetting 4-Slot Training positions...")
        x, y = pydirectinput.position()
        self.train_slots.append((x, y))
        self.save_config()
        self.log(f"Training Slot #{len(self.train_slots)}/4 saved at ({x}, {y})")

    def record_open_train_btn(self):
        x, y = pydirectinput.position()
        self.open_train_pos = (x, y)
        self.save_config()
        self.log(f"Overworld 'Train' Button (F10) saved at ({x}, {y})!")

    def record_heal_btn(self):
        x, y = pydirectinput.position()
        self.heal_pos = (x, y)
        self.save_config()
        self.log(f"Overworld 'Heal' Button (F11) saved at ({x}, {y})!")

    def calibrate_hp_bar(self):
        x, y = pydirectinput.position()
        if self.hp_calib_stage == 0:
            self.hp_bar_box[0], self.hp_bar_box[1] = x, y
            self.hp_calib_stage = 1
            self.log(f"HP Top-Left set ({x}, {y}). Press F7 on Bottom-Right.")
        else:
            self.hp_bar_box[2], self.hp_bar_box[3] = x, y
            self.hp_calib_stage = 0
            self.save_config()
            self.log(f"HP Bar calibrated & saved: {self.hp_bar_box}")

    def grab_frames(self, sct):
        raw = np.array(sct.grab(self.monitor))
        bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        return bgr, gray

    def get_best_score(self, gray_frame, name):
        if name not in self.templates:
            return -1.0
        tmpl = self.templates[name]
        res = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return round(float(max_val), 2)

    def find_ui(self, gray_frame, name, threshold=0.82):
        if name not in self.templates:
            return None
        tmpl = self.templates[name]
        h, w = tmpl.shape
        res = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            abs_x = self.monitor["left"] + max_loc[0]
            abs_y = self.monitor["top"] + max_loc[1]
            cx, cy = HumanInputEngine.gaussian_point_in_box(abs_x, abs_y, w, h)
            return (cx, cy, max_val)
        return None

    def detect_enemy_element(self, gray_frame):
        """Scans the battle screen for the enemy's elemental badge icon."""
        best_elem = None
        best_score = 0.78
        for elem_name, tmpl_key in ENEMY_ELEMENT_TEMPLATES.items():
            if tmpl_key in self.templates:
                tmpl = self.templates[tmpl_key]
                res = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val >= best_score:
                    best_score = max_val
                    best_elem = elem_name
        return best_elem

    def select_adaptive_combat_move(self, gray_frame):
        """
        Detects which of your 4 Miscrits is currently fighting, checks the enemy's element,
        and picks Physical if your Miscrit is weak to the enemy, or Elemental if strong/neutral!
        Returns: (click_x, click_y, log_description) or None if not in battle.
        """
        enemy_elem = self.detect_enemy_element(gray_frame)

        # Check Miscrit #1 through #4 in order
        for idx in range(4):
            slot_num = idx + 1
            my_elem = self.team_elements[idx]
            elem_btn = self.find_ui(gray_frame, f"m{slot_num}_elem_atk", threshold=0.79)
            phys_btn = self.find_ui(gray_frame, f"m{slot_num}_phys_atk", threshold=0.79)

            if elem_btn or phys_btn:
                is_weak = (enemy_elem is not None and WEAK_AGAINST.get(my_elem) == enemy_elem)
                is_strong = (enemy_elem is not None and STRONG_AGAINST.get(my_elem) == enemy_elem)

                if is_weak:
                    if phys_btn:
                        return (
                            phys_btn[0], phys_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) is WEAK vs {enemy_elem} -> Switched to PHYSICAL attack!"
                        )
                    else:
                        return (
                            elem_btn[0], elem_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) weak vs {enemy_elem}, but m{slot_num}_phys_atk not snipped -> Using Elemental."
                        )
                elif is_strong:
                    if elem_btn:
                        return (
                            elem_btn[0], elem_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) is STRONG vs {enemy_elem} -> Using ELEMENTAL attack!"
                        )
                    else:
                        return (
                            phys_btn[0], phys_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) strong vs {enemy_elem} -> Using Physical fallback."
                        )
                else:
                    # Neutral or enemy element not snipped: prefer strong Elemental move, fallback to Physical
                    if elem_btn:
                        vs_txt = f"vs {enemy_elem}" if enemy_elem else "(Neutral)"
                        return (
                            elem_btn[0], elem_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) {vs_txt} -> Using Elemental attack."
                        )
                    else:
                        return (
                            phys_btn[0], phys_btn[1],
                            f"Miscrit #{slot_num} ({my_elem}) -> Using Physical attack."
                        )

        # Fallback to single default battle_attack if m1..m4 aren't snipped yet
        default_atk = self.find_ui(gray_frame, "battle_attack", threshold=0.80)
        if default_atk:
            return (default_atk[0], default_atk[1], "Combat -> Using default battle_attack.")

        return None

    def find_slot_dead_or_alive(self, gray_frame, slot_name):
        normal_match = self.find_ui(gray_frame, slot_name, threshold=0.65)
        if normal_match:
            self.cached_slot_coords[slot_name] = (normal_match[0], normal_match[1])
            self.save_config()
            return (normal_match[0], normal_match[1], "Alive/Matched")

        if slot_name in self.templates:
            tmpl = self.templates[slot_name]
            h, w = tmpl.shape
            edges_screen = cv2.Canny(gray_frame, 50, 150)
            edges_tmpl = cv2.Canny(tmpl, 50, 150)
            res = cv2.matchTemplate(edges_screen, edges_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val >= 0.45:
                abs_x = self.monitor["left"] + max_loc[0]
                abs_y = self.monitor["top"] + max_loc[1]
                cx, cy = HumanInputEngine.gaussian_point_in_box(abs_x, abs_y, w, h)
                self.cached_slot_coords[slot_name] = (cx, cy)
                self.save_config()
                return (cx, cy, f"Dead/Edge-Match ({round(max_val, 2)})")

        if slot_name in self.cached_slot_coords:
            cx, cy = self.cached_slot_coords[slot_name]
            jx, jy = HumanInputEngine.gaussian_point_in_box(cx - 8, cy - 8, 16, 16)
            return (jx, jy, "Dead/Cached-Pos")

        return None

    def trigger_overworld_heal(self, sct, reason=""):
        _, gray = self.grab_frames(sct)
        if self.find_ui(gray, "close_train_btn", threshold=0.78):
            return False

        heal_match = self.find_ui(gray, "heal_btn", threshold=0.78)
        if heal_match:
            self.log(f"Healing/Reviving team ({reason}) via heal_btn...")
            HumanInputEngine.bezier_move_and_click(heal_match[0], heal_match[1])
            self.battles_since_heal = 0
            HumanInputEngine.sleep_human(1.4, 0.2)
            return True
        elif self.heal_pos is not None:
            hx, hy = self.heal_pos
            jx, jy = HumanInputEngine.gaussian_point_in_box(hx - 8, hy - 8, 16, 16)
            self.log(f"Healing/Reviving team ({reason}) via F11 position ({jx}, {jy})...")
            HumanInputEngine.bezier_move_and_click(jx, jy)
            self.battles_since_heal = 0
            HumanInputEngine.sleep_human(1.4, 0.2)
            return True
        return False

    def clear_post_train_modals(self, sct, label_str):
        deadline = time.time() + 9.0
        click_counts = {name: 0 for name in POST_TRAIN_MODALS}
        any_modal_clicked = False

        while time.time() < deadline:
            if keyboard.is_pressed("F8"):
                break

            bgr_sub, gray_sub = self.grab_frames(sct)
            matched_modal = None

            for modal_name in POST_TRAIN_MODALS:
                if click_counts[modal_name] >= 2:
                    continue
                m_btn = self.find_ui(gray_sub, modal_name, threshold=0.82)
                if m_btn:
                    matched_modal = (modal_name, m_btn)
                    break

            if matched_modal:
                modal_name, m_btn = matched_modal
                click_counts[modal_name] += 1
                self.log(f"Post-train popup cleared: {modal_name} (score={round(m_btn[2], 2)})")

                if modal_name in ("evolve_btn", "evolve_continue_btn"):
                    self.send_discord_alert(
                        "Miscrit Evolved!",
                        f"Your Miscrit in **{label_str}** evolved during Auto-Training!",
                        bgr_frame=bgr_sub, color=0x9B59B6
                    )
                elif modal_name == "new_ability_btn":
                    self.log(f"New ability unlocked for {label_str}!")

                HumanInputEngine.bezier_move_and_click(m_btn[0], m_btn[1])
                any_modal_clicked = True
                deadline = min(time.time() + 4.5, deadline + 2.5)
                HumanInputEngine.sleep_human(1.4, 0.2)
                continue

            if any_modal_clicked and self.find_ui(gray_sub, "close_train_btn", threshold=0.78):
                break

            time.sleep(0.4)

    def train_single_selected_miscrit(self, sct, label_str):
        if "train_now_btn" not in self.templates:
            self.log("Cannot train: You haven't snipped 'train_now_btn' yet!")
            return False

        leveled_any = False
        for _ in range(3):
            _, gray = self.grab_frames(sct)
            train_btn = self.find_ui(gray, "train_now_btn", threshold=0.75)
            if not train_btn:
                if not leveled_any:
                    score = self.get_best_score(gray, "train_now_btn")
                    self.log(f"{label_str}: Not ready (train_now_btn match={score})")
                break

            self.log(f"Leveling up Miscrit in {label_str}!")
            HumanInputEngine.bezier_move_and_click(train_btn[0], train_btn[1])
            leveled_any = True

            HumanInputEngine.sleep_human(2.2, 0.2)
            self.clear_post_train_modals(sct, label_str)
            HumanInputEngine.sleep_human(0.8, 0.2)

        return leveled_any

    def open_training_window_reliably(self, sct):
        self.trigger_overworld_heal(sct, reason="Pre-Train Revive")

        for attempt in range(2):
            if keyboard.is_pressed("F8"):
                return False

            _, gray = self.grab_frames(sct)
            if self.find_ui(gray, "close_train_btn", threshold=0.78) or self.find_ui(gray, "train_now_btn", threshold=0.76):
                return True

            open_btn = (
                self.find_ui(gray, "open_train_menu_btn", threshold=0.78)
                or self.find_ui(gray, "ready_to_train", threshold=0.78)
            )

            if open_btn:
                self.log("Opening Training window via template...")
                HumanInputEngine.bezier_move_and_click(open_btn[0], open_btn[1])
            elif self.open_train_pos is not None:
                ox, oy = self.open_train_pos
                jx, jy = HumanInputEngine.gaussian_point_in_box(ox - 8, oy - 8, 16, 16)
                self.log(f"Opening Training window via F10 position ({jx}, {jy})...")
                HumanInputEngine.bezier_move_and_click(jx, jy)
            else:
                self.log("Could not open Training window! Hover over the HUD 'Train' button and press F10.")
                return False

            wait_end = time.time() + 2.5
            while time.time() < wait_end:
                _, g_check = self.grab_frames(sct)
                if self.find_ui(g_check, "close_train_btn", threshold=0.77) or self.find_ui(g_check, "train_now_btn", threshold=0.76):
                    return True
                if "slot_1" in self.templates and self.find_ui(g_check, "slot_1", threshold=0.70):
                    return True
                time.sleep(0.35)

            if "close_train_btn" not in self.templates and len(self.train_slots) > 0:
                return True

        return False

    def execute_4_slot_training_sequence(self, sct, manual_test=False):
        self.log("Checking party for Miscrits ready to level up...")

        if not self.open_training_window_reliably(sct):
            return False

        self.train_needed_flag = False
        self.battles_since_train_check = 0
        self.last_train_attempt_time = time.time()

        trained_count = 0
        snipped_slots = [s for s in SLOT_TEMPLATES if s in self.templates]

        if len(self.train_slots) > 0:
            for idx, (sx, sy) in enumerate(self.train_slots):
                if (not self.running and not manual_test) or keyboard.is_pressed("F8"):
                    break
                jx, jy = HumanInputEngine.gaussian_point_in_box(sx - 8, sy - 8, 16, 16)
                self.log(f"Clicking F9 Miscrit Slot #{idx + 1}/{len(self.train_slots)} at ({jx}, {jy})...")
                HumanInputEngine.bezier_move_and_click(jx, jy)
                HumanInputEngine.sleep_human(1.0, 0.2)

                if self.train_single_selected_miscrit(sct, f"Slot #{idx + 1}"):
                    trained_count += 1

        elif len(snipped_slots) > 0:
            for slot_name in snipped_slots:
                if (not self.running and not manual_test) or keyboard.is_pressed("F8"):
                    break
                _, gray_slot = self.grab_frames(sct)
                s_match = self.find_slot_dead_or_alive(gray_slot, slot_name)
                if s_match:
                    self.log(f"Clicking {slot_name} [{s_match[2]}] at ({s_match[0]}, {s_match[1]})...")
                    HumanInputEngine.bezier_move_and_click(s_match[0], s_match[1])
                    HumanInputEngine.sleep_human(1.0, 0.2)
                    if self.train_single_selected_miscrit(sct, slot_name):
                        trained_count += 1
                else:
                    self.log(f"Could not see {slot_name} (Tip: Press F9 on all 4 slots!).")

        else:
            self.log("No 4-Slot positions set! Press F9 on each of the 4 Miscrits in Training window.")
            if self.train_single_selected_miscrit(sct, "Default Slot #1"):
                trained_count += 1

        _, gray_end = self.grab_frames(sct)
        close_btn = self.find_ui(gray_end, "close_train_btn", threshold=0.76)
        if close_btn:
            self.log(f"Training complete ({trained_count} Miscrits leveled up). Closing window...")
            HumanInputEngine.bezier_move_and_click(close_btn[0], close_btn[1])
            HumanInputEngine.sleep_human(1.6, 0.2)
        else:
            self.log(f"Training finished ({trained_count} leveled up). Note: 'close_train_btn' not found.")

        return trained_count > 0

    def read_enemy_hp_percent(self, bgr_frame):
        x1, y1, x2, y2 = self.hp_bar_box
        roi = bgr_frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 100.0

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 90, 90]), np.array([85, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([165, 90, 90]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask1, mask2)

        col_has_hp = np.any(mask > 0, axis=0)
        hp_pct = (np.sum(col_has_hp) / max(1, roi.shape[1])) * 100.0
        return round(hp_pct, 1)

    def evaluate_captured_rating(self, gray_frame):
        s_plus = self.find_ui(gray_frame, "rating_s_plus", threshold=0.86)
        s_norm = self.find_ui(gray_frame, "rating_s", threshold=0.86)
        a_plus = self.find_ui(gray_frame, "rating_a_plus", threshold=0.86)

        if s_plus:
            detected = "S+"
        elif s_norm:
            detected = "S"
        elif a_plus:
            detected = "A+"
        else:
            detected = "Below A+ / Unknown"

        if self.rating_filter == "Keep All":
            return True, detected
        if self.rating_filter == "S+ Only":
            return (detected == "S+"), detected
        if self.rating_filter == "S or Higher":
            return (detected in ("S+", "S")), detected
        if self.rating_filter == "A+ or Higher":
            return (detected in ("S+", "S", "A+")), detected
        return True, detected

    def run_loop(self):
        self.log(f"Bot active! Team Elements: {self.team_elements}")
        next_afk_time = time.time() + random.uniform(900, 1500)

        with mss.mss() as sct:
            while self.running:
                if keyboard.is_pressed("F8"):
                    self.running = False
                    self.log("Emergency stop (F8) triggered.")
                    break

                if self.afk_breaks_enabled and time.time() >= next_afk_time:
                    pause_sec = random.uniform(35, 85)
                    self.log(f"Taking human AFK break for {int(pause_sec)}s...")
                    time.sleep(pause_sec)
                    next_afk_time = time.time() + random.uniform(900, 1500)

                bgr, gray = self.grab_frames(sct)

                # Priority 1: Post-Capture Rating Filter (Keep vs. Release Screen)
                keep_match = self.find_ui(gray, "keep_btn", threshold=0.84)
                release_match = self.find_ui(gray, "release_btn", threshold=0.84)
                if keep_match:
                    should_keep, rating_str = self.evaluate_captured_rating(gray)
                    if should_keep or not release_match:
                        self.log(f"Captured [{rating_str}] meets ({self.rating_filter}) -> Keeping!")
                        self.send_discord_alert(
                            "Miscrit Captured & Kept!",
                            f"**Detected Rating:** `{rating_str}`\n**Filter:** `{self.rating_filter}`",
                            bgr_frame=bgr, color=0x2ECC71
                        )
                        HumanInputEngine.bezier_move_and_click(keep_match[0], keep_match[1])
                    else:
                        self.log(f"Captured [{rating_str}] below ({self.rating_filter}) -> Releasing.")
                        self.send_discord_alert(
                            "Miscrit Auto-Released",
                            f"**Detected Rating:** `{rating_str}` (Below `{self.rating_filter}`)",
                            bgr_frame=bgr, color=0xE67E22
                        )
                        HumanInputEngine.bezier_move_and_click(release_match[0], release_match[1])
                        HumanInputEngine.sleep_human(1.1, 0.2)
                        _, gray_confirm = self.grab_frames(sct)
                        confirm_btn = self.find_ui(gray_confirm, "confirm_release", threshold=0.83)
                        if confirm_btn:
                            HumanInputEngine.bezier_move_and_click(confirm_btn[0], confirm_btn[1])

                    self.alerted_current_encounter = False
                    HumanInputEngine.sleep_human(1.8, 0.2)
                    continue

                # Priority 2: Standard Post-Battle Modals ONLY
                modal_cleared = False
                for modal in ["confirm_release", "level_up", "continue_btn"]:
                    match = self.find_ui(gray, modal, threshold=0.83)
                    if match:
                        if self.last_modal_name == modal:
                            self.same_modal_count += 1
                        else:
                            self.last_modal_name = modal
                            self.same_modal_count = 1

                        if self.same_modal_count > 3:
                            self.log(f"Skipping '{modal}' (clicked 3x without screen changing).")
                            self.same_modal_count = 0
                            break

                        self.log(f"Clearing post-battle modal: {modal}")
                        if modal == "level_up":
                            self.train_needed_flag = True
                        if modal == "continue_btn":
                            if self.find_ui(gray, "ready_to_train", threshold=0.78):
                                self.train_needed_flag = True
                            self.battles_since_heal += 1
                            self.battles_since_train_check += 1
                            self.alerted_current_encounter = False

                        HumanInputEngine.bezier_move_and_click(match[0], match[1])
                        if modal == "continue_btn":
                            HumanInputEngine.sleep_human(2.5, 0.2)
                        else:
                            HumanInputEngine.sleep_human(1.4, 0.2)
                        modal_cleared = True
                        break
                if modal_cleared:
                    continue

                self.last_modal_name = None
                self.same_modal_count = 0

                # Priority 3: Adaptive 4-Miscrit Combat (Elemental vs Physical + Rare Capture)
                combat_move = self.select_adaptive_combat_move(gray)
                if combat_move:
                    if self.mode == "RARE_HUNT":
                        is_target = self.find_ui(gray, "target_miscrit", threshold=0.84)
                        target_valid = (is_target is not None) or ("target_miscrit" not in self.templates)

                        if target_valid:
                            if not self.alerted_current_encounter and is_target is not None:
                                self.alerted_current_encounter = True
                                self.log("Rare Target Miscrit spotted! Sending Discord alert...")
                                self.send_discord_alert(
                                    "Rare Target Encountered!",
                                    "Target template matched in battle. Weakening for capture...",
                                    bgr_frame=bgr, color=0x3498DB
                                )

                            enemy_hp = self.read_enemy_hp_percent(bgr)
                            cap_btn = self.find_ui(gray, "capture_btn", threshold=0.81)
                            chip_btn = self.find_ui(gray, "chip_attack", threshold=0.81)

                            if enemy_hp <= self.capture_hp_threshold and cap_btn:
                                self.log(f"Enemy HP {enemy_hp}% <= {self.capture_hp_threshold}% -> Capturing!")
                                HumanInputEngine.bezier_move_and_click(cap_btn[0], cap_btn[1])
                                HumanInputEngine.sleep_human(3.4, 0.2)
                                continue
                            elif enemy_hp <= 60.0 and chip_btn:
                                self.log(f"Enemy HP {enemy_hp}% -> Using chip attack.")
                                HumanInputEngine.bezier_move_and_click(chip_btn[0], chip_btn[1])
                                HumanInputEngine.sleep_human(2.8, 0.2)
                                continue

                    self.log(combat_move[2])
                    HumanInputEngine.bezier_move_and_click(combat_move[0], combat_move[1])
                    HumanInputEngine.sleep_human(2.9, 0.2)
                    continue

                # Priority 4: Overworld Team Healing (every 2 battles)
                if self.battles_since_heal >= 2:
                    if self.trigger_overworld_heal(sct, reason="Post-Battle Revive"):
                        continue
                    else:
                        self.battles_since_heal = 0

                # Priority 5: Auto-Training & 4-Slot Level-Up Check
                if self.auto_train_enabled and (time.time() - self.last_train_attempt_time > 12.0):
                    ready_hud = self.find_ui(gray, "ready_to_train", threshold=0.79)
                    train_win_open = self.find_ui(gray, "close_train_btn", threshold=0.79)
                    can_open_train = ("open_train_menu_btn" in self.templates) or (self.open_train_pos is not None)
                    periodic_due = (self.battles_since_train_check >= 3 and can_open_train)

                    if ready_hud or train_win_open or self.train_needed_flag or periodic_due:
                        self.execute_4_slot_training_sequence(sct)
                        continue

                # Priority 6: Overworld Multi-Bush Rotation
                snipped_bushes = self.get_snipped_bushes()
                if snipped_bushes:
                    clicked_bush = False
                    for offset in range(len(snipped_bushes)):
                        idx = (self.bush_index + offset) % len(snipped_bushes)
                        bush_name = snipped_bushes[idx]
                        bush_match = self.find_ui(gray, bush_name, threshold=0.79)

                        if bush_match:
                            self.log(f"Walking to & searching {bush_name} at ({bush_match[0]}, {bush_match[1]})...")
                            HumanInputEngine.bezier_move_and_click(bush_match[0], bush_match[1])
                            self.bush_index = (idx + 1) % len(snipped_bushes)
                            clicked_bush = True
                            HumanInputEngine.sleep_human(4.2, 0.2)
                            break

                    if not clicked_bush:
                        time.sleep(0.4)
                elif self.waypoints:
                    wx, wy = self.waypoints[self.wp_index]
                    jx, jy = HumanInputEngine.gaussian_point_in_box(wx - 10, wy - 10, 20, 20)
                    self.log(f"Searching Waypoint #{self.wp_index + 1} at ({jx}, {jy})")
                    HumanInputEngine.bezier_move_and_click(jx, jy)
                    self.wp_index = (self.wp_index + 1) % len(self.waypoints)
                    HumanInputEngine.sleep_human(4.2, 0.2)
                else:
                    time.sleep(0.4)


class UltimateSuiteGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Miscrits Stealth Suite v4.0 (4-Miscrit Elemental & Physical AI)")
        self.geometry("560x840")
        ctk.set_appearance_mode("dark")

        self.bot = MiscritsStealthBot(self.log_message)
        self.bot_thread = None

        keyboard.add_hotkey("F6", self.bot.record_waypoint)
        keyboard.add_hotkey("F7", self.bot.calibrate_hp_bar)
        keyboard.add_hotkey("F9", self.bot.record_train_slot)
        keyboard.add_hotkey("F10", self.bot.record_open_train_btn)
        keyboard.add_hotkey("F11", self.bot.record_heal_btn)

        # --- Section 1: Mode & Stat Rating Filter ---
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=14, pady=(8, 4))

        ctk.CTkLabel(top_frame, text="Mode:", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=8, pady=5)
        self.mode_var = ctk.StringVar(value=self.bot.mode)
        ctk.CTkSegmentedButton(
            top_frame, values=["XP_GRIND", "RARE_HUNT"],
            variable=self.mode_var, command=self.change_mode
        ).grid(row=0, column=1, padx=8, pady=5)

        ctk.CTkLabel(top_frame, text="Keep Rating:", font=("Arial", 13, "bold")).grid(row=1, column=0, padx=8, pady=5)
        self.rating_var = ctk.StringVar(value=self.bot.rating_filter)
        ctk.CTkOptionMenu(
            top_frame, values=["Keep All", "A+ or Higher", "S or Higher", "S+ Only"],
            variable=self.rating_var, command=self.change_rating
        ).grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        # --- Section 2: 4-Miscrit Element Selector ---
        elem_frame = ctk.CTkFrame(self)
        elem_frame.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(
            elem_frame, text="Your 4 Miscrits' Elements (Auto-switches to Physical if Weak):",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=8, pady=(5, 2), sticky="w")

        self.elem_vars = []
        for i in range(4):
            var = ctk.StringVar(value=self.bot.team_elements[i])
            self.elem_vars.append(var)
            ctk.CTkLabel(elem_frame, text=f"M{i+1}:", font=("Arial", 11, "bold")).grid(row=1, column=i, padx=4, pady=(2, 0))
            menu = ctk.CTkOptionMenu(
                elem_frame, values=ELEMENTS, variable=var, width=115,
                command=lambda val, idx=i: self.update_team_element(idx, val)
            )
            menu.grid(row=2, column=i, padx=6, pady=(0, 6))

        # --- Section 3: Built-In Screen Snipping Tool ---
        snip_frame = ctk.CTkFrame(self)
        snip_frame.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(
            snip_frame, text="Built-in Snipper (Snip m1..m4_elem_atk, m1..m4_phys_atk & enemy_*):",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=3, padx=8, pady=(5, 2), sticky="w")

        self.snip_target_var = ctk.StringVar(value=TEMPLATE_NAMES[0])
        ctk.CTkOptionMenu(
            snip_frame, values=TEMPLATE_NAMES, variable=self.snip_target_var, width=200
        ).grid(row=1, column=0, padx=6, pady=6)

        ctk.CTkButton(
            snip_frame, text="Snip Selected", fg_color="#0066cc", width=130, command=self.launch_snipper
        ).grid(row=1, column=1, padx=4, pady=6)

        ctk.CTkButton(
            snip_frame, text="Delete Selected", fg_color="#802020", width=120, command=self.delete_selected_template
        ).grid(row=1, column=2, padx=6, pady=6)

        # --- Section 4: Discord Webhook Settings ---
        wh_frame = ctk.CTkFrame(self)
        wh_frame.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(wh_frame, text="Discord Webhook URL:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(4, 2), sticky="w"
        )
        self.wh_entry = ctk.CTkEntry(wh_frame, width=350, placeholder_text="https://discord.com/api/webhooks/...")
        self.wh_entry.insert(0, self.bot.webhook_url)
        self.wh_entry.grid(row=1, column=0, padx=8, pady=5)

        ctk.CTkButton(
            wh_frame, text="Save & Test", width=110, command=self.save_and_test_webhook
        ).grid(row=1, column=1, padx=8, pady=5)

        # --- Section 5: Auto-Training & Stealth Controls ---
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.pack(fill="x", padx=14, pady=4)

        self.hp_label = ctk.CTkLabel(
            ctrl_frame, text=f"Capture Enemy Below HP: {self.bot.capture_hp_threshold}%"
        )
        self.hp_label.pack(pady=(4, 1))
        self.hp_slider = ctk.CTkSlider(
            ctrl_frame, from_=5, to=80, number_of_steps=75, command=self.update_hp
        )
        self.hp_slider.set(self.bot.capture_hp_threshold)
        self.hp_slider.pack(pady=2)

        sub_ctrl = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        sub_ctrl.pack(pady=3)

        self.train_switch = ctk.CTkSwitch(
            sub_ctrl, text="Auto-Train All 4 Miscrits", command=self.toggle_auto_train
        )
        if self.bot.auto_train_enabled:
            self.train_switch.select()
        self.train_switch.grid(row=0, column=0, padx=8, pady=2)

        self.afk_switch = ctk.CTkSwitch(sub_ctrl, text="Human AFK Breaks", command=self.toggle_afk)
        self.afk_switch.select()
        self.afk_switch.grid(row=0, column=1, padx=8, pady=2)

        btn_ctrl = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_ctrl.pack(pady=4)

        ctk.CTkButton(
            btn_ctrl, text="Clear F6 Bushes", width=120, command=self.clear_wps
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            btn_ctrl, text="Clear F9 Train Slots", width=135, command=self.clear_train_slots
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            btn_ctrl, text="Test Auto-Train Now", fg_color="#7b2cbf", width=150, command=self.test_auto_train
        ).grid(row=0, column=2, padx=5)

        # --- Section 6: Start / Stop & Live Telemetry Log ---
        self.start_btn = ctk.CTkButton(
            self, text="Start Stealth Suite", fg_color="#1f7a1f",
            height=38, font=("Arial", 14, "bold"), command=self.toggle_bot
        )
        self.start_btn.pack(pady=6, padx=14, fill="x")

        self.log_box = ctk.CTkTextbox(self, width=530, height=185, font=("Consolas", 11))
        self.log_box.pack(padx=14, pady=(2, 8))
        self.log_message(f"Team Elements loaded: M1={self.bot.team_elements[0]}, M2={self.bot.team_elements[1]}, M3={self.bot.team_elements[2]}, M4={self.bot.team_elements[3]}")
        self.log_message("Hotkeys: [F9] 4 Slots | [F10] HUD Train | [F11] HUD Heal | [F8] Stop")

    def update_team_element(self, idx, val):
        self.bot.team_elements[idx] = val
        self.bot.save_config()
        self.log_message(f"Miscrit #{idx + 1} element set to: {val} (Weak vs {WEAK_AGAINST[val]}, Strong vs {STRONG_AGAINST[val]})")

    def delete_selected_template(self):
        target = self.snip_target_var.get()
        path = os.path.join(ASSETS_DIR, f"{target}.png")
        if os.path.exists(path):
            os.remove(path)
            self.bot.load_templates()
            self.log_message(f"Deleted {target}.png! Total loaded: {len(self.bot.templates)}")
        else:
            self.log_message(f"{target}.png does not exist in assets folder.")

    def test_auto_train(self):
        self.bot.load_templates()
        self.log_message("Running manual 4-Slot Auto-Train diagnostic in 1.5 seconds...")

        def _run_test():
            time.sleep(1.5)
            with mss.mss() as sct:
                self.bot.execute_4_slot_training_sequence(sct, manual_test=True)

        threading.Thread(target=_run_test, daemon=True).start()

    def launch_snipper(self):
        target = self.snip_target_var.get()
        self.iconify()
        time.sleep(0.25)

        def on_snip_done(success, msg):
            self.deiconify()
            self.bot.load_templates()
            self.log_message(f"{msg} | Total templates: {len(self.bot.templates)}")

        SnippingOverlay(self, target, on_snip_done)

    def save_and_test_webhook(self):
        self.bot.webhook_url = self.wh_entry.get().strip()
        self.bot.save_config()
        if not self.bot.webhook_url:
            self.log_message("Webhook cleared and saved.")
            return
        self.log_message("Sending test alert with screen capture to Discord...")
        with mss.mss() as sct:
            bgr, _ = self.bot.grab_frames(sct)
            self.bot.send_discord_alert(
                "Miscrits Suite Connected",
                "Webhook & live screenshot telemetry verified.",
                bgr_frame=bgr
            )

    def change_mode(self, val):
        self.bot.mode = val
        self.log_message(f"Mode set to: {val}")

    def change_rating(self, val):
        self.bot.rating_filter = val
        self.bot.save_config()
        self.log_message(f"Post-capture filter set to: {val}")

    def update_hp(self, val):
        pct = int(val)
        self.bot.capture_hp_threshold = pct
        self.hp_label.configure(text=f"Capture Enemy Below HP: {pct}%")
        self.bot.save_config()

    def toggle_auto_train(self):
        self.bot.auto_train_enabled = bool(self.train_switch.get())
        self.bot.save_config()
        self.log_message(f"4-Slot Auto-Training: {'Enabled' if self.bot.auto_train_enabled else 'Disabled'}")

    def toggle_afk(self):
        self.bot.afk_breaks_enabled = bool(self.afk_switch.get())
        self.log_message(f"Human AFK breaks: {'Enabled' if self.bot.afk_breaks_enabled else 'Disabled'}")

    def clear_wps(self):
        self.bot.waypoints.clear()
        self.bot.wp_index = 0
        self.bot.save_config()
        self.log_message("Cleared all saved F6 bush waypoints.")

    def clear_train_slots(self):
        self.bot.train_slots.clear()
        self.bot.cached_slot_coords.clear()
        self.bot.save_config()
        self.log_message("Cleared all 4 F9 Training Slot positions & cached slot coordinates.")

    def log_message(self, msg):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")

    def toggle_bot(self):
        if not self.bot.running:
            self.bot.webhook_url = self.wh_entry.get().strip()
            self.bot.save_config()
            self.bot.load_templates()
            self.bot.running = True
            self.start_btn.configure(text="Stop Bot (or Press F8)", fg_color="#b32424")
            self.bot_thread = threading.Thread(target=self.bot.run_loop, daemon=True)
            self.bot_thread.start()
        else:
            self.bot.running = False
            self.start_btn.configure(text="Start Stealth Suite", fg_color="#1f7a1f")
            self.log_message("Stopped by user.")


if __name__ == "__main__":
    app = UltimateSuiteGUI()
    app.mainloop()