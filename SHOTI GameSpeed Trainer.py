"""
shotilive_trainer.py
SHOTI's Very Legit Game Speed Adjuster With A Short And Cool Name

Put this file + all PNG assets + Chewy.ttf in the same folder.
Requirements: pip install Pillow
"""

import ctypes
import ctypes.wintypes
import struct
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════════
# When frozen by PyInstaller, files are in sys._MEIPASS (temp extraction folder).
# When running as a .py, they're next to the script.
if getattr(sys, "frozen", False):
    HERE = os.path.join(sys._MEIPASS, "Look")
else:
    HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Look")

def A(name):
    return os.path.join(HERE, name)

# ═══════════════════════════════════════════════════════════════════
#  LAYOUT CONSTANTS  (all measured from the reference screenshot)
# ═══════════════════════════════════════════════════════════════════
WIN_W, WIN_H = 619, 853

# Slider
SL_LEFT    = 32
SL_RIGHT   = 587
SL_WIDTH   = SL_RIGHT - SL_LEFT          # 555 px
SL_MIN     = 0.05
SL_MAX     = 4.00
SL_TRACK_Y = 360                          # vertical centre of the track image

# Crane head thumb  (image is 104 × 117)
THUMB_W, THUMB_H = 104, 100
THUMB_TOP_Y = SL_TRACK_Y - THUMB_H // 2  # 302

# Speed readout sits below the thumb
READOUT_Y = 390

# Status indicator (top-left corner of image)
STATUS_X, STATUS_Y = 10, 185

# Preset buttons  (images are 95 × 95 each)
BTN_SIZE = 95
PRESET_BTNS = [
    (0.25,  37, 485, "0.25x_button.png",  "0.25x_button_pressed.png"),
    (0.50, 191, 485, "0.50x_button.png",  "0.50x_button_pressed.png"),
    (1.00, 345, 485, "1.00x_button.png",  "1.00x_button_pressed.png"),
    (4.00, 499, 485, "4.00x_button.png",  "4.00x_button_pressed.png"),
]

# 100× button
# not-pressed: 557 × 105   pressed: 557 × 251  (bottom-aligned)
BTN100_X    = 31
BTN100_NP_Y = 716
BTN100_NP_H = 105
BTN100_PR_H = 251
BTN100_PR_Y = 580   # 570

# ═══════════════════════════════════════════════════════════════════
#  GAME / SHM CONSTANTS
# ═══════════════════════════════════════════════════════════════════
PROCESS_NAME        = "DyingLightGame.exe"
SHM_NAME            = "DL1Hook_v3"
SHM_SIZE            = 16
FILE_MAP_ALL_ACCESS = 0x000F001F

SPEED_NORMAL = 1.00
SPEED_LOWEST = 0.05
SPEED_SLOW   = 0.25
SPEED_FAST   = 4.00
SPEED_CHAOS  = 100.0

VK_F1, VK_F2, VK_F3, VK_F4 = 0x70, 0x71, 0x72, 0x73

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
class SHMWriter:
    def __init__(self):
        self._handle = self._view = None

    @property
    def connected(self):
        return self._view is not None

    def try_connect(self):
        if self.connected:
            return True
        h = _OpenFileMapping(FILE_MAP_ALL_ACCESS, False, SHM_NAME)
        if not h:
            return False
        v = _MapViewOfFile(h, FILE_MAP_ALL_ACCESS, 0, 0, SHM_SIZE)
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
    """Check if DyingLightGame.exe is running via Toolhelp32 — pure Win32, no subprocess."""
    TH32CS_SNAPPROCESS = 0x00000002

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

    k32    = ctypes.windll.kernel32
    snap   = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.wintypes.HANDLE(-1).value:
        return False
    entry          = PROCESSENTRY32()
    entry.dwSize   = ctypes.sizeof(PROCESSENTRY32)
    target         = PROCESS_NAME.lower().encode()
    found          = False
    try:
        if k32.Process32First(snap, ctypes.byref(entry)):
            while True:
                if entry.szExeFile.lower() == target:
                    found = True
                    break
                if not k32.Process32Next(snap, ctypes.byref(entry)):
                    break
    finally:
        k32.CloseHandle(snap)
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

def _render_readout(value: float, chaos: bool = False) -> Image.Image:
    global _FONT
    if _FONT is None:
        _FONT = _get_font(30)

    text  = f"{int(value)}×" if chaos else f"{value:.2f}"
    color = (255, 55, 55, 255) if chaos else (255, 255, 255, 255)

    dummy = Image.new("RGBA", (1, 1))
    bbox  = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=_FONT)
    tw, th = bbox[2] - bbox[0] + 6, bbox[3] - bbox[1] + 6

    img  = Image.new("RGBA", (tw + 6, th + 6), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)
    d.text((3, 3), text, font=_FONT, fill=(0, 0, 0, 180))
    d.text((1, 1), text, font=_FONT, fill=color)
    return img

# ═══════════════════════════════════════════════════════════════════
#  APP
# ═══════════════════════════════════════════════════════════════════
class TrainerApp(tk.Tk):

    POLL_MS   = 1000
    HOTKEY_MS = 80

    def __init__(self):
        super().__init__()
        self.title("SHOTI GameSpeed Trainer")
        self.resizable(False, False)

        self._shm         = SHMWriter()
        self._speed       = 1.0
        self._chaos       = False
        self._chaos_on    = False  # 100x toggle: True = latched on
        self._pre_chaos   = 1.0   # speed to restore when toggling off
        self._dragging    = False
        self._btn_down    = None   # index 0-3 of pressed preset button
        self._100_down    = False
        self._refs        = []     # PhotoImage reference pool (dynamic, cycling)
        self._static_refs = []     # PhotoImage reference pool (static, permanent)

        self._load_assets()
        self._build_canvas()
        self._redraw_all()
        self._register_hotkeys()
        self._poll_game()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── asset loading ─────────────────────────────────────────────
    def _load_assets(self):
        self._bg         = _load("body.png")
        self._connected  = _load("game_connected.png")
        self._disconn    = _load("game_not_connected.png")
        self._track      = _load("game_speed_slider_body.png")
        self._crane      = _load("crane_head.png")
        self._b100_np    = _load("100x_speed_not_pressed.png")
        self._b100_pr    = _load("100x_speed pressed.png")

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

        # Create all canvas image items (z-order: first = bottom)
        self._id_bg      = c.create_image(0, 0, anchor="nw")
        self._id_status  = c.create_image(STATUS_X, STATUS_Y, anchor="nw")
        self._id_track   = c.create_image(SL_LEFT, SL_TRACK_Y - 10, anchor="nw")
        self._id_thumb   = c.create_image(0, THUMB_TOP_Y, anchor="nw")
        self._id_readout = c.create_image(0, READOUT_Y, anchor="n")
        self._id_btns    = [c.create_image(bx, by, anchor="nw")
                            for _, bx, by, _, _ in PRESET_BTNS]
        self._id_100     = c.create_image(BTN100_X, BTN100_NP_Y, anchor="nw")

        c.bind("<ButtonPress-1>",   self._on_press)
        c.bind("<B1-Motion>",       self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)

    # ── reference management ──────────────────────────────────────
    def _static_ref(self, pil_img):
        """Permanent reference — never garbage collected."""
        ph = _to_tk(pil_img)
        self._static_refs.append(ph)
        return ph

    def _dyn_ref(self, pil_img):
        """Dynamic reference — small cycling pool for readout only."""
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

    def _draw_status(self, connected: bool):
        img = self._connected if connected else self._disconn
        self._c.itemconfig(self._id_status, image=self._static_ref(img))

    def _draw_thumb_and_readout(self):
        px = _val_to_px(self._speed)
        self._c.coords(self._id_thumb, px - THUMB_W // 2, THUMB_TOP_Y)
        self._c.itemconfig(self._id_thumb, image=self._static_ref(self._crane))
        self._c.coords(self._id_readout, px, READOUT_Y)
        rd = _render_readout(SPEED_CHAOS if self._chaos else self._speed,
                             chaos=self._chaos)
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

    # ── speed control ─────────────────────────────────────────────
    def _apply_speed(self, val: float, chaos: bool = False):
        self._chaos = chaos
        if chaos:
            self._speed = SL_MAX
            self._shm.write(SPEED_CHAOS)
        else:
            self._chaos_on = False
            self._speed = max(SL_MIN, min(SL_MAX, val))
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
                    # Toggle OFF — restore previous speed
                    self._chaos_on = False
                    self._chaos    = False
                    self._apply_speed(self._pre_chaos)
                else:
                    # Toggle ON — save current speed, go chaos
                    self._chaos_on  = True
                    self._pre_chaos = self._speed
                    self._apply_speed(0, chaos=True)
            self._draw_100()

    def _slide_to(self, x):
        self._chaos    = False
        self._chaos_on = False
        self._speed = _px_to_val(x)
        self._shm.write(self._speed)
        self._draw_thumb_and_readout()
        self._draw_100()

    # ── hotkeys  (GetAsyncKeyState polling — no callbacks, no GIL risk) ─
    # GetAsyncKeyState works globally regardless of which window has focus.
    # We poll it from the tkinter loop (main thread) every HOTKEY_MS ms.
    # High bit set = key is currently held down.  We track previous state
    # so each press fires exactly once even if the key is held.

    def _register_hotkeys(self):
        self._key_down = {VK_F1: False, VK_F2: False,
                          VK_F3: False, VK_F4: False}
        self._poll_hotkeys()

    def _poll_hotkeys(self):
        _gas = _u32.GetAsyncKeyState
        for vk, speed in (
            (VK_F1, SPEED_NORMAL),
            (VK_F2, SPEED_LOWEST),
            (VK_F3, SPEED_SLOW),
            (VK_F4, SPEED_FAST),
        ):
            pressed = bool(_gas(vk) & 0x8000)
            if pressed and not self._key_down[vk]:
                self._apply_speed(speed)
            self._key_down[vk] = pressed
        self.after(self.HOTKEY_MS, self._poll_hotkeys)

    def _unregister_hotkeys(self):
        pass  # nothing to clean up

    # ── game poll ─────────────────────────────────────────────────
    def _poll_game(self):
        game = _game_running()
        if game:
            ok = self._shm.try_connect()
        else:
            # Game closed — disconnect SHM so stale mapping doesn't
            # keep the status green after the process exits.
            self._shm.disconnect()
            ok = False
        self._draw_status(ok)
        self.after(self.POLL_MS, self._poll_game)

    # ── cleanup ───────────────────────────────────────────────────
    def _on_close(self):
        """Called when user clicks the X button."""
        self._shm.write(1.0)
        self._unregister_hotkeys()
        self._shm.disconnect()
        self.destroy()

    def destroy(self):
        super().destroy()


if __name__ == "__main__":
    try:
        app = TrainerApp()
        app.mainloop()
    except Exception as e:
        import traceback
        msg = traceback.format_exc()
        # Write log file next to script
        # Write log next to the exe, not inside the bundled temp folder
        exe_dir  = os.path.dirname(os.path.abspath(
                   sys.executable if getattr(sys, "frozen", False) else __file__))
        log_path = os.path.join(exe_dir, "trainer_error.log")
        with open(log_path, "w") as f:
            f.write(msg)
        # Try to show a message box
        try:
            import tkinter.messagebox as mb
            root = tk.Tk()
            root.withdraw()
            mb.showerror("Trainer Startup Error",
                         f"Crash logged to trainer_error.log\n\n{msg[:800]}")
            root.destroy()
        except Exception:
            print(msg)
            input("Press Enter to close...")
