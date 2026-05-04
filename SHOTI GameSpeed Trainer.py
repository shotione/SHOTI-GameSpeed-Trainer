"""
SHOTI GameSpeed Trainer
Dying Light 1 — Real-time speed controller

Requirements: pip install Pillow
Assets: Look\ folder next to this script
"""

import ctypes
import ctypes.wintypes
import json
import os
import struct
import sys
import tkinter as tk
import tkinter.messagebox as mb
from PIL import Image, ImageTk, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════════
if getattr(sys, "frozen", False):
    HERE    = os.path.join(sys._MEIPASS, "Look")
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Look")
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(EXE_DIR, "hotkeys.json")

def A(name):
    return os.path.join(HERE, name)

# ═══════════════════════════════════════════════════════════════════
#  LAYOUT CONSTANTS  — edit these to move things around
# ═══════════════════════════════════════════════════════════════════
WIN_W, WIN_H = 619, 853

SL_LEFT    = 32
SL_RIGHT   = 587
SL_WIDTH   = SL_RIGHT - SL_LEFT
SL_MIN     = 0.05
SL_MAX     = 4.00
SL_TRACK_Y = 360

THUMB_W, THUMB_H = 104, 100
THUMB_TOP_Y = SL_TRACK_Y - THUMB_H // 2

READOUT_Y = 390

STATUS_X, STATUS_Y = 10, 185

# Hotkey changer button (hotkey_changer.png scaled to fit)
HKB_X, HKB_Y = 443, 208   # top-left position in window
HKB_W, HKB_H = 144, 30    # display size

BTN_SIZE = 95
PRESET_BTNS = [
    (0.25,  37, 485, "0.25x_button.png",  "0.25x_button_pressed.png"),
    (0.50, 191, 485, "0.50x_button.png",  "0.50x_button_pressed.png"),
    (1.00, 345, 485, "1.00x_button.png",  "1.00x_button_pressed.png"),
    (4.00, 499, 485, "4.00x_button.png",  "4.00x_button_pressed.png"),
]

BTN100_X    = 31
BTN100_NP_Y = 716
BTN100_NP_H = 105
BTN100_PR_H = 251
BTN100_PR_Y = 580

# ═══════════════════════════════════════════════════════════════════
#  SPEED CONSTANTS
# ═══════════════════════════════════════════════════════════════════
SPEED_NORMAL = 1.00
SPEED_LOWEST = 0.05
SPEED_SLOW   = 0.25
SPEED_FAST   = 4.00
SPEED_CHAOS  = 100.0
SPEED_FREEZE = 0.0001   # photo mode — near-freeze, mouse look still works

# ═══════════════════════════════════════════════════════════════════
#  VK CODE MAP  — used for hotkey display and config
# ═══════════════════════════════════════════════════════════════════
VK_NAMES = {
    # Mouse buttons
    0x01: "M1",    0x02: "M2",    0x04: "M3",
    0x05: "M4",    0x06: "M5",
    # Function keys
    0x70: "F1",  0x71: "F2",  0x72: "F3",  0x73: "F4",
    0x74: "F5",  0x75: "F6",  0x76: "F7",  0x77: "F8",
    0x78: "F9",  0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    # Number row
    0x30: "0",   0x31: "1",   0x32: "2",   0x33: "3",
    0x34: "4",   0x35: "5",   0x36: "6",   0x37: "7",
    0x38: "8",   0x39: "9",
    # Letters
    0x41: "A",   0x42: "B",   0x43: "C",   0x44: "D",
    0x45: "E",   0x46: "F",   0x47: "G",   0x48: "H",
    0x49: "I",   0x4A: "J",   0x4B: "K",   0x4C: "L",
    0x4D: "M",   0x4E: "N",   0x4F: "O",   0x50: "P",
    0x51: "Q",   0x52: "R",   0x53: "S",   0x54: "T",
    0x55: "U",   0x56: "V",   0x57: "W",   0x58: "X",
    0x59: "Y",   0x5A: "Z",
    # Numpad
    0x60: "Num0",0x61: "Num1",0x62: "Num2",0x63: "Num3",
    0x64: "Num4",0x65: "Num5",0x66: "Num6",0x67: "Num7",
    0x68: "Num8",0x69: "Num9",
    # Nav
    0x24: "Home",0x23: "End", 0x21: "PgUp",0x22: "PgDn",
    0x2D: "Ins", 0x2E: "Del",
    # Special
    0x08: "Back",0x0D: "Enter",0x20: "Space",
    0xBB: "=",   0xBD: "-",   0xDB: "[",   0xDD: "]",
    0xBA: ";",   0xDE: "'",   0xBC: ",",   0xBE: ".",
}
NAME_TO_VK = {v: k for k, v in VK_NAMES.items()}

# Default hotkey bindings: {slot_name: vk_code}
DEFAULT_HOTKEYS = {
    "normal": 0x70,   # F1
    "lowest": 0x71,   # F2
    "slow":   0x72,   # F3
    "fast":   0x73,   # F4
    "freeze": 0x74,   # F5
}
HOTKEY_LABELS = {
    "normal": "Normal (1.0×)",
    "lowest": "Lowest (0.05×)",
    "slow":   "Slow (0.25×)",
    "fast":   "Fast (4.0×)",
    "freeze": "Freeze (Photo)",
}

# ═══════════════════════════════════════════════════════════════════
#  WIN32
# ═══════════════════════════════════════════════════════════════════
_k32 = ctypes.windll.kernel32
_u32 = ctypes.windll.user32

_OpenFileMapping         = _k32.OpenFileMappingW
_MapViewOfFile           = _k32.MapViewOfFile
_UnmapViewOfFile         = _k32.UnmapViewOfFile
_CloseHandle             = _k32.CloseHandle
_OpenFileMapping.restype = ctypes.wintypes.HANDLE
_MapViewOfFile.restype   = ctypes.c_void_p

# ═══════════════════════════════════════════════════════════════════
#  SHARED MEMORY
# ═══════════════════════════════════════════════════════════════════
SHM_NAME        = "DL1Hook_v3"
SHM_SIZE        = 16
FILE_MAP_ALL    = 0x000F001F
PROCESS_NAME    = "DyingLightGame.exe"

class SHMWriter:
    def __init__(self):
        self._handle = self._view = None

    @property
    def connected(self):
        return self._view is not None

    def try_connect(self):
        if self.connected:
            return True
        h = _OpenFileMapping(FILE_MAP_ALL, False, SHM_NAME)
        if not h:
            return False
        v = _MapViewOfFile(h, FILE_MAP_ALL, 0, 0, SHM_SIZE)
        if not v:
            _CloseHandle(h)
            return False
        self._handle, self._view = h, v
        return True

    def write(self, speed: float):
        if self.connected:
            try:
                ctypes.memmove(self._view, struct.pack("f", speed), 4)
            except Exception:
                pass

    def disconnect(self):
        if self._view:   _UnmapViewOfFile(self._view)
        if self._handle: _CloseHandle(self._handle)
        self._handle = self._view = None

# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════
def _game_running():
    """Win32 process check — no subprocess, no CMD flash."""
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize",              ctypes.wintypes.DWORD),
            ("cntUsage",            ctypes.wintypes.DWORD),
            ("th32ProcessID",       ctypes.wintypes.DWORD),
            ("th32DefaultHeapID",   ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID",        ctypes.wintypes.DWORD),
            ("cntThreads",          ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase",      ctypes.c_long),
            ("dwFlags",             ctypes.wintypes.DWORD),
            ("szExeFile",           ctypes.c_char * 260),
        ]
    snap = _k32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return False
    entry        = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    target       = PROCESS_NAME.lower().encode()
    found        = False
    try:
        if _k32.Process32First(snap, ctypes.byref(entry)):
            while True:
                if entry.szExeFile.lower() == target:
                    found = True
                    break
                if not _k32.Process32Next(snap, ctypes.byref(entry)):
                    break
    finally:
        _k32.CloseHandle(snap)
    return found

def _load(filename):
    return Image.open(A(filename)).convert("RGBA")

def _to_tk(img):
    return ImageTk.PhotoImage(img)

def _val_to_px(val):
    t = (val - SL_MIN) / (SL_MAX - SL_MIN)
    return int(SL_LEFT + max(0.0, min(1.0, t)) * SL_WIDTH)

def _px_to_val(x):
    t = (x - SL_LEFT) / SL_WIDTH
    return round(SL_MIN + max(0.0, min(1.0, t)) * (SL_MAX - SL_MIN), 2)

def _get_font(size):
    for path in [A("Chewy.ttf"),
                 r"C:\Windows\Fonts\impact.ttf",
                 r"C:\Windows\Fonts\arialbd.ttf"]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

_FONT = None

def _render_readout(value: float, chaos: bool = False, freeze: bool = False) -> Image.Image:
    global _FONT
    if _FONT is None:
        _FONT = _get_font(30)
    if freeze:
        text  = "FREEZE"
        color = (100, 180, 255, 255)
    elif chaos:
        text  = f"{int(value)}×"
        color = (255, 55, 55, 255)
    else:
        text  = f"{value:.2f}"
        color = (255, 255, 255, 255)
    dummy = Image.new("RGBA", (1, 1))
    bbox  = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=_FONT)
    tw    = bbox[2] - bbox[0] + 6
    th    = bbox[3] - bbox[1] + 6
    img   = Image.new("RGBA", (tw + 6, th + 6), (0, 0, 0, 0))
    d     = ImageDraw.Draw(img)
    d.text((3, 3), text, font=_FONT, fill=(0, 0, 0, 180))
    d.text((1, 1), text, font=_FONT, fill=color)
    return img

def _load_hotkeys() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        # Validate — make sure all expected keys exist
        result = dict(DEFAULT_HOTKEYS)
        for k, v in data.items():
            if k in result and isinstance(v, int):
                result[k] = v
        return result
    except Exception:
        return dict(DEFAULT_HOTKEYS)

def _save_hotkeys(hk: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(hk, f, indent=2)
    except Exception:
        pass

def _vk_name(vk: int) -> str:
    return VK_NAMES.get(vk, f"0x{vk:02X}")

# ═══════════════════════════════════════════════════════════════════
#  HOTKEY SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════
class HotkeyDialog(tk.Toplevel):

    BG    = "#0d0d0d"
    PANEL = "#1a1a1a"
    RED   = "#e8003a"
    FG    = "#cccccc"
    DIM   = "#555555"
    BLUE  = "#3399ff"

    def __init__(self, parent, hotkeys: dict, callback):
        super().__init__(parent)
        self.title("Hotkey Settings")
        self.configure(bg=self.BG)
        self.resizable(False, False)
        self.grab_set()                      # modal
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._parent   = parent
        self._hotkeys  = dict(hotkeys)      # working copy
        self._callback = callback
        self._binding  = None               # slot currently being rebound
        self._poll_id  = None

        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        pw = self._parent.winfo_x() + self._parent.winfo_width() // 2
        ph = self._parent.winfo_y() + self._parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

    def _build_ui(self):
        tk.Label(self, text="HOTKEY SETTINGS",
                 bg=self.RED, fg="white",
                 font=("Impact", 14, "bold"),
                 width=30).pack(fill="x", ipady=8)

        tk.Label(self,
                 text="Click a key button then press any key to rebind.",
                 bg=self.BG, fg=self.DIM,
                 font=("Consolas", 8)).pack(pady=(8, 4))

        frame = tk.Frame(self, bg=self.BG)
        frame.pack(padx=20, pady=4)

        self._btn_refs = {}

        for slot, label in HOTKEY_LABELS.items():
            row = tk.Frame(frame, bg=self.BG)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=label, width=18, anchor="w",
                     bg=self.BG, fg=self.FG,
                     font=("Consolas", 9)).pack(side="left")

            btn = tk.Button(
                row,
                text=_vk_name(self._hotkeys[slot]),
                width=8,
                bg=self.PANEL, fg=self.FG, relief="flat",
                activebackground=self.RED, activeforeground="white",
                font=("Consolas", 9, "bold"),
                cursor="hand2",
                command=lambda s=slot: self._start_bind(s)
            )
            btn.pack(side="left", padx=(8, 0), ipady=4)
            self._btn_refs[slot] = btn

        # Buttons row
        brow = tk.Frame(self, bg=self.BG)
        brow.pack(pady=12, padx=20, fill="x")

        tk.Button(brow, text="Reset Defaults",
                  bg=self.PANEL, fg=self.DIM, relief="flat",
                  font=("Consolas", 8), cursor="hand2",
                  command=self._reset).pack(side="left")

        tk.Button(brow, text="Save & Close",
                  bg=self.RED, fg="white", relief="flat",
                  activebackground="#c0002d",
                  font=("Consolas", 9, "bold"), cursor="hand2",
                  command=self._save).pack(side="right", ipadx=10, ipady=4)

    def _start_bind(self, slot):
        """Highlight the button and start listening for a key."""
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None

        # Reset all buttons to normal state
        for s, b in self._btn_refs.items():
            b.config(bg=self.PANEL, fg=self.FG, text=_vk_name(self._hotkeys[s]))

        self._binding = slot
        self._btn_refs[slot].config(
            bg=self.BLUE, fg="white", text="Press a key...")

        self._poll_bind()

    def _poll_bind(self):
        """Poll GetAsyncKeyState for any key press."""
        if self._binding is None:
            return

        # Scan all keys in our VK map
        for vk in VK_NAMES:
            if _u32.GetAsyncKeyState(vk) & 0x8001:
                # Key pressed — bind it
                self._hotkeys[self._binding] = vk
                self._btn_refs[self._binding].config(
                    bg=self.PANEL, fg=self.FG, text=_vk_name(vk))
                self._binding = None
                return

        self._poll_id = self.after(50, self._poll_bind)

    def _reset(self):
        if self._binding:
            self._binding = None
            if self._poll_id:
                self.after_cancel(self._poll_id)
        self._hotkeys = dict(DEFAULT_HOTKEYS)
        for slot, btn in self._btn_refs.items():
            btn.config(text=_vk_name(self._hotkeys[slot]),
                       bg=self.PANEL, fg=self.FG)

    def _save(self):
        _save_hotkeys(self._hotkeys)
        self._callback(self._hotkeys)
        self._on_close()

    def _on_close(self):
        if self._poll_id:
            self.after_cancel(self._poll_id)
        self.grab_release()
        self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════
class TrainerApp(tk.Tk):

    POLL_MS   = 1000
    HOTKEY_MS = 80

    def __init__(self):
        super().__init__()
        self.title("SHOTI's Very Legit Game Speed Adjuster With A Short And Cool Name")
        self.resizable(False, False)

        self._shm         = SHMWriter()
        self._speed       = 1.0
        self._chaos       = False
        self._chaos_on    = False
        self._pre_chaos   = 1.0
        self._freeze_on   = False
        self._pre_freeze  = 1.0
        self._dragging    = False
        self._btn_down    = None
        self._100_down    = False
        self._hkb_down    = False
        self._closing     = False
        self._refs        = []
        self._static_refs = []
        self._hotkeys     = _load_hotkeys()
        self._key_down    = {vk: False for vk in self._hotkeys.values()}

        self._load_assets()
        self._build_canvas()
        self._redraw_all()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_game()
        self._poll_hotkeys()

    # ── asset loading ─────────────────────────────────────────────
    def _load_assets(self):
        self._bg         = _load("body.png")
        self._connected  = _load("game_connected.png")
        self._disconn    = _load("game_not_connected.png")
        self._track      = _load("game_speed_slider_body.png")
        self._crane      = _load("crane_head.png")
        self._b100_np    = _load("100x_speed_not_pressed.png")
        self._b100_pr    = _load("100x_speed pressed.png")

        # Hotkey changer button — scale to display size
        hkb_raw           = _load("hotkey_changer.png")
        self._hkb_normal  = hkb_raw.resize((HKB_W, HKB_H), Image.LANCZOS)
        # Pressed state: slightly darkened
        import PIL.ImageEnhance
        self._hkb_pressed = PIL.ImageEnhance.Brightness(self._hkb_normal).enhance(0.7)

        self._btn_normal  = []
        self._btn_pressed = []
        for _, _, _, fn, fp in PRESET_BTNS:
            self._btn_normal.append(_load(fn))
            self._btn_pressed.append(_load(fp))

    # ── canvas setup ──────────────────────────────────────────────
    def _build_canvas(self):
        self.geometry(f"{WIN_W}x{WIN_H}")
        c = tk.Canvas(self, width=WIN_W, height=WIN_H,
                      bd=0, highlightthickness=0)
        c.pack()
        self._c = c

        self._id_bg      = c.create_image(0, 0, anchor="nw")
        self._id_status  = c.create_image(STATUS_X, STATUS_Y, anchor="nw")
        self._id_track   = c.create_image(SL_LEFT, SL_TRACK_Y - 10, anchor="nw")
        self._id_thumb   = c.create_image(0, THUMB_TOP_Y, anchor="nw")
        self._id_readout = c.create_image(0, READOUT_Y, anchor="n")
        self._id_btns    = [c.create_image(bx, by, anchor="nw")
                            for _, bx, by, _, _ in PRESET_BTNS]
        self._id_100     = c.create_image(BTN100_X, BTN100_NP_Y, anchor="nw")

        # Right-click anywhere → open hotkey settings
        self._id_hkb = c.create_image(HKB_X, HKB_Y, anchor="nw")

        c.bind("<ButtonPress-1>",   self._on_press)
        c.bind("<B1-Motion>",       self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<ButtonPress-3>",   self._on_right_click)

    # ── reference management ──────────────────────────────────────
    def _static_ref(self, pil_img):
        ph = _to_tk(pil_img)
        self._static_refs.append(ph)
        return ph

    def _dyn_ref(self, pil_img):
        ph = _to_tk(pil_img)
        self._refs.append(ph)
        if len(self._refs) > 12:
            self._refs = self._refs[-12:]
        return ph

    # ── draw helpers ──────────────────────────────────────────────
    def _redraw_all(self):
        c = self._c
        c.itemconfig(self._id_bg,    image=self._static_ref(self._bg))
        c.itemconfig(self._id_track, image=self._static_ref(self._track))
        self._draw_status(self._shm.connected)
        self._draw_thumb_and_readout()
        self._draw_btns()
        self._draw_100()
        self._draw_hkb(False)

    def _draw_status(self, connected: bool):
        img = self._connected if connected else self._disconn
        self._c.itemconfig(self._id_status, image=self._static_ref(img))

    def _draw_thumb_and_readout(self):
        px = _val_to_px(self._speed)
        self._c.coords(self._id_thumb, px - THUMB_W // 2, THUMB_TOP_Y)
        self._c.itemconfig(self._id_thumb, image=self._static_ref(self._crane))
        self._c.coords(self._id_readout, px, READOUT_Y)
        rd = _render_readout(
            SPEED_CHAOS if self._chaos else self._speed,
            chaos=self._chaos,
            freeze=self._freeze_on)
        self._c.itemconfig(self._id_readout, image=self._dyn_ref(rd))

    def _draw_btns(self):
        for i, item in enumerate(self._id_btns):
            imgs = self._btn_pressed if i == self._btn_down else self._btn_normal
            self._c.itemconfig(item, image=self._static_ref(imgs[i]))

    def _draw_100(self):
        if self._100_down or self._chaos_on:
            self._c.coords(self._id_100, BTN100_X, BTN100_PR_Y)
            self._c.itemconfig(self._id_100, image=self._static_ref(self._b100_pr))
        else:
            self._c.coords(self._id_100, BTN100_X, BTN100_NP_Y)
            self._c.itemconfig(self._id_100, image=self._static_ref(self._b100_np))

    def _draw_hkb(self, pressed: bool):
        img = self._hkb_pressed if pressed else self._hkb_normal
        self._c.itemconfig(self._id_hkb, image=self._static_ref(img))

    # ── speed control ─────────────────────────────────────────────
    def _apply_speed(self, val: float, chaos: bool = False, freeze: bool = False):
        self._chaos  = chaos
        self._freeze_on = freeze
        if chaos:
            self._speed = SL_MAX
            self._shm.write(SPEED_CHAOS)
        elif freeze:
            self._speed = SL_MIN   # thumb at left edge visually
            self._shm.write(SPEED_FREEZE)
        else:
            self._chaos_on  = False
            self._freeze_on = False
            self._speed     = max(SL_MIN, min(SL_MAX, val))
            self._shm.write(self._speed)
        self._draw_thumb_and_readout()
        self._draw_100()

    # ── hit testing ───────────────────────────────────────────────
    def _hit_slider(self, x, y):
        return (SL_LEFT - THUMB_W // 2 <= x <= SL_RIGHT + THUMB_W // 2 and
                THUMB_TOP_Y - 10 <= y <= READOUT_Y + 30)

    def _hit_btn(self, x, y):
        for i, (_, bx, by, _, _) in enumerate(PRESET_BTNS):
            if bx <= x <= bx + BTN_SIZE and by <= y <= by + BTN_SIZE:
                return i
        return None

    def _hit_100(self, x, y):
        return (BTN100_X <= x <= BTN100_X + 557 and
                BTN100_NP_Y <= y <= BTN100_NP_Y + BTN100_NP_H)

    def _hit_hkb(self, x, y):
        return HKB_X <= x <= HKB_X + HKB_W and HKB_Y <= y <= HKB_Y + HKB_H

    # ── mouse events ──────────────────────────────────────────────
    def _on_press(self, e):
        if self._hit_slider(e.x, e.y):
            self._dragging = True
            self._slide_to(e.x)
            return
        idx = self._hit_btn(e.x, e.y)
        if idx is not None:
            self._btn_down = idx
            self._draw_btns()
            return
        if self._hit_100(e.x, e.y):
            self._100_down = True
            self._draw_100()
            return
        if self._hit_hkb(e.x, e.y):
            self._hkb_down = True
            self._draw_hkb(True)

    def _on_drag(self, e):
        if self._dragging:
            self._slide_to(e.x)

    def _on_release(self, e):
        if self._dragging:
            self._dragging = False

        if self._btn_down is not None:
            idx = self._btn_down
            self._btn_down = None
            self._draw_btns()
            val, bx, by, _, _ = PRESET_BTNS[idx]
            if bx <= e.x <= bx + BTN_SIZE and by <= e.y <= by + BTN_SIZE:
                self._apply_speed(val)

        if self._100_down:
            self._100_down = False
            if self._hit_100(e.x, e.y):
                if self._chaos_on:
                    self._chaos_on = False
                    self._chaos    = False
                    self._apply_speed(self._pre_chaos)
                else:
                    self._chaos_on  = True
                    self._pre_chaos = self._speed
                    self._apply_speed(0, chaos=True)
            self._draw_100()

        if self._hkb_down:
            self._hkb_down = False
            self._draw_hkb(False)
            if self._hit_hkb(e.x, e.y):
                self._open_hotkey_settings()

    def _on_right_click(self, e):
        """Right-click anywhere to open hotkey settings."""
        self._open_hotkey_settings()

    def _slide_to(self, x):
        self._chaos     = False
        self._chaos_on  = False
        self._freeze_on = False
        self._speed     = _px_to_val(x)
        self._shm.write(self._speed)
        self._draw_thumb_and_readout()
        self._draw_100()

    # ── hotkey settings ───────────────────────────────────────────
    def _open_hotkey_settings(self):
        HotkeyDialog(self, self._hotkeys, self._on_hotkeys_saved)

    def _on_hotkeys_saved(self, new_hotkeys: dict):
        self._hotkeys  = new_hotkeys
        self._key_down = {vk: False for vk in self._hotkeys.values()}

    # ── hotkey polling ────────────────────────────────────────────
    def _poll_hotkeys(self):
        if self._closing:
            return
        hk = self._hotkeys
        actions = {
            "normal": lambda: self._apply_speed(SPEED_NORMAL),
            "lowest": lambda: self._apply_speed(SPEED_LOWEST),
            "slow":   lambda: self._apply_speed(SPEED_SLOW),
            "fast":   lambda: self._apply_speed(SPEED_FAST),
            "freeze": self._toggle_freeze,
        }
        for slot, vk in hk.items():
            pressed = bool(_u32.GetAsyncKeyState(vk) & 0x8000)
            if pressed and not self._key_down.get(vk, False):
                if slot in actions:
                    actions[slot]()
            self._key_down[vk] = pressed
        self.after(self.HOTKEY_MS, self._poll_hotkeys)

    def _toggle_freeze(self):
        if self._freeze_on:
            self._freeze_on = False
            self._apply_speed(self._pre_freeze)
        else:
            self._pre_freeze = self._speed
            self._apply_speed(0, freeze=True)

    # ── game poll ─────────────────────────────────────────────────
    def _poll_game(self):
        if self._closing:
            return
        game = _game_running()
        if game:
            ok = self._shm.try_connect()
        else:
            self._shm.disconnect()
            ok = False
        self._draw_status(ok)
        self.after(self.POLL_MS, self._poll_game)

    # ── cleanup ───────────────────────────────────────────────────
    def _on_close(self):
        self._closing = True
        try:
            self._shm.write(1.0)
        except Exception:
            pass
        self._shm.disconnect()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        app = TrainerApp()
        app.mainloop()
    except Exception:
        import traceback
        msg = traceback.format_exc()
        log_path = os.path.join(EXE_DIR, "trainer_error.log")
        try:
            with open(log_path, "w") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            root = tk.Tk()
            root.withdraw()
            mb.showerror("Trainer Error",
                         f"Crash logged to trainer_error.log\n\n{msg[:800]}")
            root.destroy()
        except Exception:
            print(msg)
