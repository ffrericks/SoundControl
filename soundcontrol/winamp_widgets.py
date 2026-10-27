"""Small Canvas-drawn widgets that mimic Winamp's flat-chrome, beveled skin look."""

from __future__ import annotations

from collections.abc import Callable

from skins import Skin


class WinampSlider:
    """A horizontal groove-and-thumb slider, like Winamp's main-window volume slider."""

    def __init__(
        self,
        parent,
        skin: Skin,
        width: int,
        height: int,
        value: int,
        on_change: Callable[[int], None],
    ) -> None:
        import tkinter as tk

        self.width = width
        self.height = height
        self.value = value
        self.on_change = on_change
        self.thumb_w = 10

        self.canvas = tk.Canvas(
            parent, width=width, height=height, highlightthickness=0, bd=0
        )
        self.apply_skin(skin, redraw=False)
        self._redraw()
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_press)

    def apply_skin(self, skin: Skin, redraw: bool = True) -> None:
        self.skin = skin
        self.canvas.configure(bg=skin.body_bg)
        if redraw:
            self._redraw()

    def set(self, value: int) -> None:
        self.value = max(0, min(100, value))
        self._redraw()

    def _on_press(self, event) -> None:
        usable = self.width - self.thumb_w
        x = max(0, min(usable, event.x - self.thumb_w / 2))
        value = round((x / usable) * 100) if usable else 0
        self.value = value
        self._redraw()
        self.on_change(value)

    def _redraw(self) -> None:
        c = self.canvas
        skin = self.skin
        c.delete("all")
        groove_y0 = self.height / 2 - 3
        groove_y1 = self.height / 2 + 3
        c.create_rectangle(
            0,
            groove_y0,
            self.width,
            groove_y1,
            fill=skin.groove_bg,
            outline=skin.bevel_dark,
        )

        usable = self.width - self.thumb_w
        thumb_x = (self.value / 100) * usable if usable else 0
        c.create_rectangle(
            0, groove_y0, thumb_x, groove_y1, fill=skin.fill_bg, outline=""
        )

        tx0, tx1 = thumb_x, thumb_x + self.thumb_w
        ty0, ty1 = 1, self.height - 1
        c.create_rectangle(
            tx0, ty0, tx1, ty1, fill=skin.thumb_bg, outline=skin.thumb_border
        )
        c.create_line(tx0 + 1, ty0 + 1, tx1 - 1, ty0 + 1, fill="#ffffff")
        c.create_line(tx0 + 3, ty0 + 2, tx0 + 3, ty1 - 2, fill=skin.thumb_border)
        c.create_line(tx0 + 6, ty0 + 2, tx0 + 6, ty1 - 2, fill=skin.thumb_border)


class WinampToggle:
    """A small beveled square button that lights up when active, like Winamp's shuffle/repeat."""

    def __init__(
        self,
        parent,
        skin: Skin,
        text: str,
        size_w: int,
        size_h: int,
        active: bool,
        on_toggle: Callable[[bool], None],
    ) -> None:
        import tkinter as tk

        self.width = size_w
        self.height = size_h
        self.text = text
        self.active = active
        self.on_toggle = on_toggle

        self.canvas = tk.Canvas(
            parent, width=size_w, height=size_h, highlightthickness=0, bd=0
        )
        self.apply_skin(skin, redraw=False)
        self._redraw()
        self.canvas.bind("<Button-1>", self._on_click)

    def apply_skin(self, skin: Skin, redraw: bool = True) -> None:
        self.skin = skin
        self.canvas.configure(bg=skin.body_bg)
        if redraw:
            self._redraw()

    def set(self, active: bool) -> None:
        self.active = active
        self._redraw()

    def _on_click(self, event) -> None:
        self.active = not self.active
        self._redraw()
        self.on_toggle(self.active)

    def _redraw(self) -> None:
        c = self.canvas
        skin = self.skin
        c.delete("all")
        fill = skin.toggle_on_bg if self.active else skin.toggle_off_bg
        c.create_rectangle(
            0, 0, self.width - 1, self.height - 1, fill=fill, outline=skin.toggle_border
        )
        if not self.active:
            c.create_line(1, 1, self.width - 2, 1, fill=skin.bevel_light)
            c.create_line(1, 1, 1, self.height - 2, fill=skin.bevel_light)
        c.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=skin.toggle_fg,
            font=("Tahoma", 7, "bold"),
        )
