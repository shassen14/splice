"""Floating teleprompter script window — Tkinter overlay, no timeline modifications."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional


_SCROLL_INTERVAL_MS = 50
_DEFAULT_FONT = ("Helvetica", 28)
_BG = "#1a1a1a"
_FG = "#f0f0f0"


class TeleprompterWindow:
    def __init__(self, text: str, *, scroll_speed: int = 2) -> None:
        self._text = text
        self._speed = scroll_speed  # pixels per tick
        self._root: Optional[tk.Tk] = None

    def _build(self) -> None:
        self._root = tk.Tk()
        self._root.title("splice teleprompter")
        self._root.attributes("-topmost", True)
        self._root.configure(bg=_BG)
        self._root.geometry("800x300+100+50")

        self._canvas = tk.Canvas(self._root, bg=_BG, highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        self._text_id = self._canvas.create_text(
            400, 300, text=self._text, font=_DEFAULT_FONT, fill=_FG,
            width=780, anchor="n",
        )
        self._root.bind("<space>", self._toggle_scroll)
        self._root.bind("<Escape>", lambda _: self._root.destroy())
        self._root.bind("<Up>", lambda _: self._adjust_speed(1))
        self._root.bind("<Down>", lambda _: self._adjust_speed(-1))

        self._scrolling = False

    def _toggle_scroll(self, _event=None) -> None:
        self._scrolling = not self._scrolling
        if self._scrolling:
            self._tick()

    def _tick(self) -> None:
        if not self._scrolling:
            return
        self._canvas.move(self._text_id, 0, -self._speed)
        self._root.after(_SCROLL_INTERVAL_MS, self._tick)

    def _adjust_speed(self, delta: int) -> None:
        self._speed = max(1, self._speed + delta)

    def run(self) -> None:
        self._build()
        self._root.mainloop()


def show(script_path: Path, *, scroll_speed: int = 2) -> None:
    """Launch the teleprompter window with the contents of script_path."""
    text = script_path.read_text(encoding="utf-8")
    TeleprompterWindow(text, scroll_speed=scroll_speed).run()
