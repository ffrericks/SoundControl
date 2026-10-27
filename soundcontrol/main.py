"""DinAmp: a tiny Winamp-skinned tray app to see and fix Windows audio devices at a glance."""

from __future__ import annotations

import contextlib
import threading
import tkinter as tk
from _ctypes import COMError
from collections.abc import Callable
from tkinter import font as tkfont

import audio
import autostart
import pystray
from icons import speaker_icon
from paths import resource_path
from PIL import Image, ImageTk
from skins import SKINS, Skin
from winamp_widgets import WinampSlider, WinampToggle

REFRESH_MS = 800
WINDOW_WIDTH = 340
WINDOW_MARGIN = 12
TASKBAR_HEIGHT = 56
TITLEBAR_HEIGHT = 22
LCD_HEIGHT = 34


class DinAmpApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("DinAmp")

        self.popup: tk.Toplevel | None = None
        self.dragging = False
        self.row_widgets: dict[str, dict] = {}
        self._drag_offset = (0, 0)
        self._title_icon: ImageTk.PhotoImage | None = None
        self.skin_index = 0
        self.skin: Skin = SKINS[self.skin_index]

        self.icon = pystray.Icon(
            "DinAmp",
            speaker_icon(muted=False),
            "DinAmp",
            menu=self._build_menu(),
        )

        self.root.after(0, self._refresh_icon)
        self.root.after(REFRESH_MS, self._tick)

    # ---- tray menu -------------------------------------------------
    def _build_menu(self) -> pystray.Menu:
        theme_items = tuple(
            pystray.MenuItem(
                skin.name,
                self._make_skin_setter(index),
                radio=True,
                checked=self._make_skin_checker(index),
            )
            for index, skin in enumerate(SKINS)
        )
        return pystray.Menu(
            pystray.MenuItem("Openen", self._open_popup_from_tray, default=True),
            pystray.MenuItem("Thema", pystray.Menu(*theme_items)),
            pystray.MenuItem(
                "Automatisch starten bij inloggen",
                self._toggle_autostart,
                checked=lambda item: autostart.is_enabled(),
            ),
            pystray.MenuItem("Afsluiten", self._quit),
        )

    def _make_skin_setter(self, index: int) -> Callable:
        def setter(icon=None, item=None) -> None:
            self.root.after(0, lambda: self._set_skin(index))

        return setter

    def _make_skin_checker(self, index: int) -> Callable:
        return lambda item: self.skin_index == index

    def _open_popup_from_tray(self, icon=None, item=None) -> None:
        self.root.after(0, self._show_popup)

    def _toggle_autostart(self, icon=None, item=None) -> None:
        autostart.set_enabled(not autostart.is_enabled())

    def _quit(self, icon=None, item=None) -> None:
        self.icon.stop()
        self.root.after(0, self.root.quit)

    # ---- tray icon appearance ---------------------------------------
    def _refresh_icon(self) -> None:
        mic = audio.default_microphone()
        muted = mic.muted if mic else False
        self.icon.icon = speaker_icon(muted=muted)
        self.icon.title = "DinAmp - microfoon gemute" if muted else "DinAmp"

    def _tick(self) -> None:
        self._refresh_icon()
        if self.popup is not None and not self.dragging:
            self._refresh_popup_values()
        self.root.after(REFRESH_MS, self._tick)

    # ---- skin switching: right-click the popup, or the tray menu -------
    def _cycle_skin(self, event=None) -> None:
        self._set_skin((self.skin_index + 1) % len(SKINS))

    def _set_skin(self, index: int) -> None:
        self.skin_index = index
        self.skin = SKINS[index]
        self.icon.update_menu()
        if self.popup is not None:
            at = (self.popup.winfo_x(), self.popup.winfo_y())
            self._render_popup(at)

    # ---- popup window -------------------------------------------------
    def _show_popup(self) -> None:
        self._render_popup(at=None)

    def _render_popup(self, at: tuple[int, int] | None) -> None:
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

        skin = self.skin
        popup = tk.Toplevel(self.root)
        self.popup = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=skin.bevel_dark)

        frame = tk.Frame(popup, bg=skin.body_bg)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        devices = audio.list_devices()
        playback = [d for d in devices if not d.is_capture]
        capture = [d for d in devices if d.is_capture]

        self._build_titlebar(frame)
        self._build_lcd(frame, playback, capture)

        body = tk.Frame(frame, bg=skin.body_bg)
        body.pack(fill="both", expand=True, padx=6, pady=(6, 8))

        self.row_widgets = {}

        if playback:
            self._add_section(body, "AFSPELEN", playback)
        if capture:
            self._add_section(body, "OPNEMEN", capture)

        popup.update_idletasks()
        if at is None:
            self._position_popup(popup)
        else:
            x, y = at
            height = popup.winfo_reqheight()
            popup.geometry(f"{WINDOW_WIDTH}x{height}+{x}+{y}")
        popup.deiconify()
        popup.focus_force()
        popup.protocol("WM_DELETE_WINDOW", self._close_popup)
        popup.bind("<FocusOut>", lambda e: self._close_popup())
        self.root.bind_all("<Button-3>", self._cycle_skin)

    def _build_titlebar(self, frame: tk.Frame) -> None:
        titlebar = tk.Canvas(frame, height=TITLEBAR_HEIGHT, highlightthickness=0, bd=0)
        titlebar.pack(fill="x", side="top")
        titlebar.bind("<Configure>", lambda e: self._paint_titlebar(titlebar))
        titlebar.bind("<ButtonPress-1>", self._start_drag)
        titlebar.bind("<B1-Motion>", self._do_drag)

    def _paint_titlebar(self, canvas: tk.Canvas) -> None:
        skin = self.skin
        canvas.delete("all")
        width = canvas.winfo_width()
        height = TITLEBAR_HEIGHT
        for x in range(width):
            t = x / max(width - 1, 1)
            r = round(
                skin.titlebar_start[0]
                + (skin.titlebar_end[0] - skin.titlebar_start[0]) * t
            )
            g = round(
                skin.titlebar_start[1]
                + (skin.titlebar_end[1] - skin.titlebar_start[1]) * t
            )
            b = round(
                skin.titlebar_start[2]
                + (skin.titlebar_end[2] - skin.titlebar_start[2]) * t
            )
            canvas.create_line(x, 0, x, height, fill=f"#{r:02x}{g:02x}{b:02x}")
        # brushed-metal texture: faint darker horizontal lines
        for y in range(2, height, 3):
            canvas.create_line(0, y, width, y, fill="#000000", stipple="gray25")

        if self._title_icon is None:
            img = Image.open(resource_path("assets/icon.png")).convert("RGBA")
            img = img.resize((14, 14), Image.LANCZOS)
            self._title_icon = ImageTk.PhotoImage(img)
        canvas.create_image(5, height // 2, image=self._title_icon, anchor="w")

        title_font = tkfont.Font(family="Tahoma", size=8, weight="bold")
        canvas.create_text(
            22,
            height // 2,
            text="D I N A M P",
            anchor="w",
            fill=skin.title_fg,
            font=title_font,
        )

        close_size = 14
        cx1 = width - close_size - 4
        cy1 = (height - close_size) // 2
        close_btn = canvas.create_rectangle(
            cx1,
            cy1,
            cx1 + close_size,
            cy1 + close_size,
            fill=skin.close_bg,
            outline=skin.close_border,
        )
        close_x = canvas.create_text(
            cx1 + close_size / 2,
            cy1 + close_size / 2,
            text="x",
            fill="#0a0a0a",
            font=tkfont.Font(family="Tahoma", size=8, weight="bold"),
        )
        for tag in (close_btn, close_x):
            canvas.tag_bind(tag, "<Button-1>", lambda e: self._close_popup())

    def _build_lcd(
        self, frame: tk.Frame, playback: list[audio.Device], capture: list[audio.Device]
    ) -> None:
        skin = self.skin
        lcd = tk.Frame(frame, bg=skin.lcd_bg, height=LCD_HEIGHT)
        lcd.pack(fill="x", padx=6, pady=(6, 0))
        lcd.pack_propagate(False)

        speaker = next((d for d in playback if d.is_default), None)
        mic = next((d for d in capture if d.is_default), None)
        mono_font = ("Consolas", 8, "bold")

        speaker_line = f"SPKR: {speaker.name[:28]}" if speaker else "SPKR: (geen)"
        mic_status = " [MUTED]" if mic and mic.muted else ""
        mic_line = f"MIC:  {mic.name[:24] if mic else '(geen)'}{mic_status}"

        tk.Label(
            lcd,
            text=speaker_line,
            bg=skin.lcd_bg,
            fg=skin.lcd_fg,
            font=mono_font,
            anchor="w",
        ).pack(fill="x", padx=6, pady=(4, 0))
        tk.Label(
            lcd,
            text=mic_line,
            bg=skin.lcd_bg,
            fg=skin.lcd_fg,
            font=mono_font,
            anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_offset = (event.x, event.y)

    def _do_drag(self, event: tk.Event) -> None:
        if self.popup is None:
            return
        x = self.popup.winfo_x() + event.x - self._drag_offset[0]
        y = self.popup.winfo_y() + event.y - self._drag_offset[1]
        self.popup.geometry(f"+{x}+{y}")

    def _close_popup(self) -> None:
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None
        self.root.unbind_all("<Button-3>")

    def _position_popup(self, popup: tk.Toplevel) -> None:
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        height = popup.winfo_reqheight()
        x = screen_w - WINDOW_WIDTH - WINDOW_MARGIN
        y = screen_h - TASKBAR_HEIGHT - height - WINDOW_MARGIN
        popup.geometry(f"{WINDOW_WIDTH}x{height}+{x}+{y}")

    def _add_section(self, parent: tk.Frame, title: str, devices: list) -> None:
        skin = self.skin
        header = tk.Frame(parent, bg=skin.bevel_dark)
        header.pack(fill="x", pady=(8, 0))
        tk.Frame(header, bg=skin.bevel_light, height=1).pack(fill="x")
        tk.Label(
            header,
            text=title,
            bg=skin.bevel_dark,
            fg=skin.group_fg,
            font=("Tahoma", 7, "bold"),
            anchor="w",
        ).pack(fill="x", padx=4, pady=1)

        list_panel = tk.Frame(parent, bg=skin.list_bg)
        list_panel.pack(fill="x")
        for device in devices:
            self._add_device_row(list_panel, device)

    def _add_device_row(self, parent: tk.Frame, device: audio.Device) -> None:
        skin = self.skin
        row = tk.Frame(parent, bg=skin.list_bg)
        row.pack(fill="x", padx=6, pady=(4, 4))

        name = device.name + (" *" if device.is_default else "")
        name_label = tk.Label(
            row,
            text=name,
            bg=skin.list_bg,
            fg=skin.list_fg,
            font=("Consolas", 8, "bold" if device.is_default else "normal"),
            anchor="w",
            wraplength=WINDOW_WIDTH - 40,
        )
        name_label.pack(fill="x")

        controls = tk.Frame(row, bg=skin.list_bg)
        controls.pack(fill="x", pady=(3, 0))

        pct_label = tk.Label(
            controls,
            text=f"{device.volume:>3}%",
            bg=skin.list_bg,
            fg=skin.list_fg,
            font=("Consolas", 8),
            width=4,
            anchor="e",
        )

        def on_set_default(active: bool, device=device):
            if not active:
                # can't un-default a device directly; restore the lit state
                widgets = self.row_widgets.get(device.id)
                if widgets:
                    widgets["default_btn"].set(True)
                return
            with contextlib.suppress(OSError):
                device.set_as_default()
            at = (self.popup.winfo_x(), self.popup.winfo_y()) if self.popup else None
            self._render_popup(at)

        default_btn = WinampToggle(
            controls,
            skin,
            "D",
            20,
            16,
            active=device.is_default,
            on_toggle=on_set_default,
        )
        default_btn.canvas.pack(side="left", padx=(0, 4))

        def on_toggle(active: bool, device=device):
            device.muted = active
            self._refresh_icon()

        mute_btn = WinampToggle(
            controls, skin, "M", 20, 16, active=device.muted, on_toggle=on_toggle
        )
        mute_btn.canvas.pack(side="left")

        def on_volume(value: int, device=device, pct_label=pct_label):
            device.volume = value
            pct_label.configure(text=f"{value:>3}%")
            self._refresh_icon()

        slider = WinampSlider(
            controls,
            skin,
            width=180,
            height=16,
            value=device.volume,
            on_change=on_volume,
        )
        slider.canvas.pack(side="left", padx=(8, 6))

        pct_label.pack(side="left")

        self.row_widgets[device.id] = {
            "pct_label": pct_label,
            "default_btn": default_btn,
            "mute_btn": mute_btn,
            "slider": slider,
            "device": device,
        }

    def _refresh_popup_values(self) -> None:
        current = {d.id: d for d in audio.list_devices()}
        for widgets in self.row_widgets.values():
            device = widgets["device"]
            with contextlib.suppress(COMError):
                widgets["mute_btn"].set(device.muted)
                volume = device.volume
                widgets["slider"].set(volume)
                widgets["pct_label"].configure(text=f"{volume:>3}%")
            fresh = current.get(device.id)
            if fresh is not None:
                widgets["default_btn"].set(fresh.is_default)

    # ---- lifecycle -------------------------------------------------
    def run(self) -> None:
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()
        self.root.mainloop()


def main() -> None:
    app = DinAmpApp()
    app.run()


if __name__ == "__main__":
    main()
