"""Winamp-inspired color skins for the DinAmp popup. Switchable via the tray menu
or a right-click anywhere on the popup."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skin:
    name: str
    titlebar_start: tuple[int, int, int]
    titlebar_end: tuple[int, int, int]
    title_fg: str
    body_bg: str
    bevel_light: str
    bevel_dark: str
    lcd_bg: str
    lcd_fg: str
    list_bg: str
    list_fg: str
    group_fg: str
    groove_bg: str
    fill_bg: str
    thumb_bg: str
    thumb_border: str
    toggle_off_bg: str
    toggle_on_bg: str
    toggle_fg: str
    toggle_border: str
    close_bg: str
    close_border: str


SKINS: list[Skin] = [
    Skin(
        name="Blauw",
        titlebar_start=(10, 26, 58),
        titlebar_end=(120, 168, 214),
        title_fg="#f4f8ff",
        body_bg="#3b4a63",
        bevel_light="#8fa4c4",
        bevel_dark="#161d29",
        lcd_bg="#00130d",
        lcd_fg="#39e67a",
        list_bg="#00130d",
        list_fg="#39e67a",
        group_fg="#dce8fb",
        groove_bg="#12181f",
        fill_bg="#4a7fa0",
        thumb_bg="#d6e2f2",
        thumb_border="#161d29",
        toggle_off_bg="#4a5972",
        toggle_on_bg="#39c15a",
        toggle_fg="#f4f8ff",
        toggle_border="#161d29",
        close_bg="#c0392b",
        close_border="#5c1a12",
    ),
    Skin(
        name="Groen",
        titlebar_start=(6, 10, 6),
        titlebar_end=(46, 58, 40),
        title_fg="#39ff14",
        body_bg="#111611",
        bevel_light="#4a5f42",
        bevel_dark="#000000",
        lcd_bg="#000000",
        lcd_fg="#39ff14",
        list_bg="#000000",
        list_fg="#39ff14",
        group_fg="#a8ffb0",
        groove_bg="#050505",
        fill_bg="#2f6a1f",
        thumb_bg="#39ff14",
        thumb_border="#000000",
        toggle_off_bg="#1c2a1c",
        toggle_on_bg="#39ff14",
        toggle_fg="#0a0a0a",
        toggle_border="#000000",
        close_bg="#39ff14",
        close_border="#0a4a05",
    ),
    Skin(
        name="Zilver",
        titlebar_start=(150, 168, 196),
        titlebar_end=(226, 234, 244),
        title_fg="#13233f",
        body_bg="#c7d0de",
        bevel_light="#f5f7fb",
        bevel_dark="#8b96a8",
        lcd_bg="#04120c",
        lcd_fg="#33e07a",
        list_bg="#e7ecf3",
        list_fg="#13233f",
        group_fg="#13233f",
        groove_bg="#a4afc0",
        fill_bg="#5b84b8",
        thumb_bg="#ffffff",
        thumb_border="#3d4a5f",
        toggle_off_bg="#dbe1ea",
        toggle_on_bg="#39c15a",
        toggle_fg="#13233f",
        toggle_border="#3d4a5f",
        close_bg="#c0392b",
        close_border="#5c1a12",
    ),
]
