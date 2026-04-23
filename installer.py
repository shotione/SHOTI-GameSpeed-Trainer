"""
installer.py  —  SHOTI GameSpeed Trainer Installer
Handles only the DLL side. Trainer runs from wherever the zip was extracted.

PyInstaller command (non-admin terminal):
    py -m PyInstaller --onefile --noconsole --name "Install" installer.py
"""

import ctypes
import ctypes.wintypes
import os
import shutil
import sys
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as mb

# ── UAC self-elevation ────────────────────────────────────────────
def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not _is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv),
        None, 1)
    sys.exit(0)

# ── Paths ─────────────────────────────────────────────────────────
SELF_DIR  = os.path.dirname(os.path.abspath(
            sys.executable if getattr(sys, "frozen", False) else __file__))
WINMM_SRC = os.path.join(SELF_DIR, "winmm.dll")
WINMM_REAL= os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                         "System32", "winmm.dll")

STEAM_CANDIDATES = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Dying Light",
    r"C:\Program Files\Steam\steamapps\common\Dying Light",
    r"D:\Steam\steamapps\common\Dying Light",
    r"D:\SteamLibrary\steamapps\common\Dying Light",
    r"D:\Games\Steam\steamapps\common\Dying Light",
    r"E:\Steam\steamapps\common\Dying Light",
    r"E:\SteamLibrary\steamapps\common\Dying Light",
    r"F:\Steam\steamapps\common\Dying Light",
    r"F:\SteamLibrary\steamapps\common\Dying Light",
]

def _detect_game():
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sub in (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 239140",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 239140",
            ):
                try:
                    with winreg.OpenKey(hive, sub) as k:
                        path, _ = winreg.QueryValueEx(k, "InstallLocation")
                        if os.path.exists(os.path.join(path, "DyingLightGame.exe")):
                            return path
                except Exception:
                    pass
    except Exception:
        pass
    for p in STEAM_CANDIDATES:
        if os.path.exists(os.path.join(p, "DyingLightGame.exe")):
            return p
    return ""

# ── Colours ───────────────────────────────────────────────────────
BG    = "#0d0d0d"
PANEL = "#1a1a1a"
RED   = "#e8003a"
FG    = "#cccccc"
DIM   = "#555555"
GREEN = "#4caf50"
BORDER= "#2a2a2a"

# ── GUI ───────────────────────────────────────────────────────────
class Installer(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("SHOTI GameSpeed Trainer — Installer")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("540x360")
        self._build_ui()
        self._game_var.set(_detect_game())

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=RED, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="SHOTI GameSpeed Trainer",
                 bg=RED, fg="white",
                 font=("Impact", 22, "bold")).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="Installer",
                 bg=RED, fg="white",
                 font=("Consolas", 10)).pack(side="right", padx=20)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(body,
                 text="Installs the speed hook DLL into your Dying Light folder.\n"
                      "Run the trainer directly from this folder after installing.",
                 bg=BG, fg=FG, font=("Consolas", 9),
                 justify="left").pack(anchor="w", pady=(0, 16))

        # Game path row
        tk.Label(body, text="DYING LIGHT FOLDER",
                 bg=BG, fg=DIM, font=("Consolas", 8)).pack(anchor="w")

        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(2, 14))

        self._game_var = tk.StringVar()
        tk.Entry(row, textvariable=self._game_var,
                 bg=PANEL, fg=FG, insertbackground=FG,
                 relief="flat", font=("Consolas", 9),
                 highlightthickness=1,
                 highlightcolor=RED,
                 highlightbackground=BORDER
                 ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(row, text="Browse",
                  bg=PANEL, fg=FG, relief="flat",
                  activebackground=RED, activeforeground="white",
                  font=("Consolas", 9), cursor="hand2",
                  command=self._browse).pack(side="right", ipady=5, ipadx=10)

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

        # Log
        tk.Label(body, text="STATUS",
                 bg=BG, fg=DIM, font=("Consolas", 8)).pack(anchor="w")
        self._log = tk.Text(body, height=4, bg=PANEL, fg=FG,
                            font=("Consolas", 9), relief="flat",
                            state="disabled", wrap="word",
                            highlightthickness=0)
        self._log.pack(fill="x", pady=(2, 14))
        self._log.tag_config("ok",  foreground=GREEN)
        self._log.tag_config("err", foreground=RED)
        self._log.tag_config("dim", foreground=DIM)
        self._log_write("Ready. Click Install when you've confirmed the path above.", "dim")

        # Install button
        self._btn = tk.Button(body, text="INSTALL",
                              bg=RED, fg="white", relief="flat",
                              activebackground="#c0002d",
                              activeforeground="white",
                              font=("Impact", 16), cursor="hand2",
                              command=self._install)
        self._btn.pack(fill="x", ipady=10)

    def _browse(self):
        path = fd.askdirectory(title="Select Dying Light folder")
        if path:
            self._game_var.set(path.replace("/", "\\"))

    def _log_write(self, msg, tag=""):
        self._log.config(state="normal")
        self._log.insert("end", msg + "\n", tag)
        self._log.see("end")
        self._log.config(state="disabled")
        self.update()

    def _log_clear(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def _install(self):
        self._log_clear()
        self._btn.config(state="disabled", text="Installing...")
        self.update()

        game_dir = self._game_var.get().strip()

        if not game_dir:
            self._log_write("ERROR: No folder selected.", "err")
            self._btn.config(state="normal", text="INSTALL")
            return

        if not os.path.exists(os.path.join(game_dir, "DyingLightGame.exe")):
            self._log_write(
                f"ERROR: DyingLightGame.exe not found in:\n  {game_dir}\n"
                "Use Browse to find the correct folder.", "err")
            self._btn.config(state="normal", text="INSTALL")
            return

        if not os.path.exists(WINMM_SRC):
            self._log_write(
                "ERROR: winmm.dll not found next to Install.exe.\n"
                "Make sure you extracted the full zip.", "err")
            self._btn.config(state="normal", text="INSTALL")
            return

        try:
            shutil.copy2(WINMM_SRC,  os.path.join(game_dir, "winmm.dll"))
            self._log_write("winmm.dll copied to game folder.", "ok")

            shutil.copy2(WINMM_REAL, os.path.join(game_dir, "winmm_real.dll"))
            self._log_write("winmm_real.dll copied to game folder.", "ok")

            self._log_write("\n✔  Done! Launch Dying Light then run the trainer.", "ok")
            self._btn.config(bg="#1a1a1a", fg=DIM,
                             text="INSTALLED ✔", cursor="arrow")

            mb.showinfo("Done",
                        "Installation complete!\n\n"
                        "Launch Dying Light, then run:\n"
                        "SHOTI GameSpeed Trainer.exe")

        except PermissionError:
            self._log_write(
                "ERROR: Permission denied.\n"
                "Right-click Install.exe and choose Run as administrator.", "err")
            self._btn.config(state="normal", text="INSTALL")
        except Exception as e:
            self._log_write(f"ERROR: {e}", "err")
            self._btn.config(state="normal", text="INSTALL")


if __name__ == "__main__":
    app = Installer()
    app.mainloop()
