"""Custom Tk canvases: fretboard, chord diagram and circle of fifths.

All drawing is computed from the canvas size, so the widgets rescale with the window.
"""
from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass

from . import guitar, theory
from .theory import pretty

BG = "#1b1f27"
PANEL = "#242a35"
PANEL_HI = "#2f3745"
FG = "#e8ecf2"
MUTED = "#9aa5b8"
ACCENT = "#f5a623"
BLUE = "#4fc3f7"
FONT = "Segoe UI"

CAGED_COLORS = {"C": "#ef5350", "A": "#ffa726", "G": "#66bb6a", "E": "#42a5f5", "D": "#ab47bc"}

BOARD = "#3a2a1c"
FRET_WIRE = "#b9b9b9"
STRING = "#d9d9d9"
INLAY = "#6b5a48"


def font(px: float, weight: str = "normal") -> tuple:
    """Pixel-sized font so canvas text scales with the drawing."""
    return (FONT, -max(8, int(px)), weight)


# --- fretboard -----------------------------------------------------------

@dataclass
class Dot:
    string: int
    fret: int
    fill: str
    text: str = ""
    text_color: str = "#ffffff"
    ring: bool = False   # accent ring, used to mark roots
    size: float = 1.0


@dataclass
class Outline:
    """Dashed rectangle around a group of notes (a pentatonic box or CAGED footprint)."""
    strings: tuple   # (low string, high string)
    frets: tuple     # (lowest fret, highest fret)
    color: str
    dash: bool = True


class FretboardCanvas(tk.Canvas):
    def __init__(self, master, nfrets: int = 17, on_click=None, **kw):
        super().__init__(master, bg=PANEL, highlightthickness=0, height=250, **kw)
        self.nfrets = nfrets
        self.on_click = on_click
        self.tuning = guitar.STANDARD
        self.dots: list[Dot] = []
        self.outlines: list[Outline] = []
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self._clicked)

    def show(self, dots, outlines=()) -> None:
        self.dots, self.outlines = list(dots), list(outlines)
        self.redraw()

    # geometry: returns x for each fret wire, y for each string, and the dot radius
    def _geom(self):
        w, h = max(self.winfo_width(), 300), max(self.winfo_height(), 150)
        left, right = w * 0.05, w * 0.015
        top, bottom = h * 0.10, h * 0.20
        n = self.nfrets
        total = 1 - 2 ** (-n / 12)
        fx = [left + (w - left - right) * (1 - 2 ** (-i / 12)) / total for i in range(n + 1)]
        gap = (h - top - bottom) / 5
        sy = [top + (5 - s) * gap for s in range(6)]
        radius = min(gap * 0.40, (fx[n] - fx[n - 1]) * 0.46)
        return w, h, left, fx, sy, gap, radius

    def _xy(self, string, fret, left, fx, sy):
        x = left * 0.5 if fret == 0 else (fx[fret - 1] + fx[fret]) / 2
        return x, sy[string]

    def redraw(self) -> None:
        self.delete("all")
        w, h, left, fx, sy, gap, r = self._geom()
        n = self.nfrets
        board_top, board_bot = sy[5] - gap * 0.5, sy[0] + gap * 0.5
        self.create_rectangle(left, board_top, fx[n], board_bot, fill=BOARD, outline="")
        for fret in (3, 5, 7, 9, 15, 17, 12):
            if fret > n:
                continue
            cx = (fx[fret - 1] + fx[fret]) / 2
            ys = [(sy[2] + sy[3]) / 2] if fret != 12 else [(sy[1] + sy[2]) / 2, (sy[3] + sy[4]) / 2]
            for cy in ys:
                self.create_oval(cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5,
                                 fill=INLAY, outline="")
        for i in range(1, n + 1):
            self.create_line(fx[i], board_top, fx[i], board_bot, fill=FRET_WIRE, width=2)
        self.create_rectangle(left - 4, board_top, left, board_bot, fill="#efe6d2", outline="")
        for s in range(6):
            self.create_line(left, sy[s], fx[n], sy[s], fill=STRING, width=1 + (5 - s) * 0.5)
            self.create_text(left * 0.1, sy[s], text=self.tuning.labels[s], fill=MUTED,
                             font=font(gap * 0.34))
        for i in range(1, n + 1):
            bold = i in (3, 5, 7, 9, 12, 15, 17)
            self.create_text((fx[i - 1] + fx[i]) / 2, board_bot + gap * 0.42, text=str(i),
                             fill=FG if bold else MUTED, font=font(gap * 0.36, "bold" if bold else "normal"))

        for o in self.outlines:
            x1 = (fx[o.frets[0] - 1] if o.frets[0] >= 1 else left * 0.24) + 2
            x2 = fx[o.frets[1]] - 2
            self.create_rectangle(x1, sy[o.strings[1]] - gap * 0.45, x2, sy[o.strings[0]] + gap * 0.45,
                                  outline=o.color, width=2, dash=(6, 4) if o.dash else ())

        for d in self.dots:
            if d.fret > n:
                continue
            x, y = self._xy(d.string, d.fret, left, fx, sy)
            rr = r * d.size
            self.create_oval(x - rr, y - rr, x + rr, y + rr, fill=d.fill,
                             outline=ACCENT if d.ring else "#10141a", width=3 if d.ring else 1)
            if d.text:
                self.create_text(x, y, text=d.text, fill=d.text_color, font=font(rr * 0.95, "bold"))

    def _clicked(self, event) -> None:
        if not self.on_click:
            return
        w, h, left, fx, sy, gap, r = self._geom()
        string = min(range(6), key=lambda s: abs(sy[s] - event.y))
        if abs(sy[string] - event.y) > gap * 0.6 or event.x > fx[-1]:
            return
        if event.x < left:
            fret = 0
        else:
            fret = next((i for i in range(1, self.nfrets + 1) if event.x <= fx[i]), None)
            if fret is None:
                return
        self.on_click(string, fret)


# --- chord diagram -------------------------------------------------------

class ChordDiagram(tk.Canvas):
    """A vertical chord box.  Click to hear it."""
    W, H = 120, 164

    def __init__(self, master, scale: float = 1.0, **kw):
        self.u = scale
        super().__init__(master, width=int(self.W * scale), height=int(self.H * scale),
                         bg=PANEL, highlightthickness=0, **kw)
        self._args = None
        self._command = None
        self._active = False
        self.bind("<Button-1>", lambda e: self._command and self._command())

    def show(self, title: str, frets, root_pc: int, subtitle: str = "", command=None,
             title_color: str = FG, tuning: guitar.Tuning = guitar.STANDARD) -> None:
        self._args = (title, tuple(frets), root_pc, subtitle, title_color, tuning)
        self._command = command
        self.config(cursor="hand2" if command else "")
        self.redraw()

    def set_active(self, active: bool) -> None:
        self._active = active
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        if not self._args:
            return
        title, frets, root_pc, subtitle, title_color, tuning = self._args
        u = self.u
        self.config(bg=PANEL_HI if self._active else PANEL)
        self.create_text(self.W * u / 2, 15 * u, text=pretty(title), fill=ACCENT if self._active else title_color,
                         font=font(16 * u, "bold"))
        x0, x1, y0, fh, rows = 22 * u, 92 * u, 48 * u, 16 * u, 5
        sx = [x0 + (x1 - x0) * i / 5 for i in range(6)]

        played = [(s, f) for s, f in enumerate(frets) if f is not None]
        fretted = [f for _, f in played if f > 0]
        has_open = any(f == 0 for _, f in played)
        base = 1 if (not fretted or has_open or min(fretted) == 1) else min(fretted)

        for i in range(rows + 1):
            y = y0 + i * fh
            heavy = i == 0 and base == 1
            self.create_line(x0, y, x1, y, fill=FG if heavy else MUTED, width=(4 if heavy else 1) * u)
        for x in sx:
            self.create_line(x, y0, x, y0 + rows * fh, fill=MUTED, width=1)
        if base > 1:
            self.create_text(x1 + 13 * u, y0 + fh / 2, text=f"{base}fr", fill=MUTED, font=font(11 * u))

        r = 5.2 * u
        for s, f in enumerate(frets):
            if f is None:
                self.create_text(sx[s], y0 - 9 * u, text="×", fill=MUTED, font=font(13 * u, "bold"))
            elif f == 0:
                is_root = guitar.fret_pc(s, 0, tuning) == root_pc
                self.create_oval(sx[s] - 3.5 * u, y0 - 12.5 * u, sx[s] + 3.5 * u, y0 - 5.5 * u,
                                 outline=ACCENT if is_root else MUTED, width=2 if is_root else 1)

        def cell(s, f):
            return sx[s], y0 + (f - base + 0.5) * fh

        if fretted and not has_open:  # barre: several strings share the lowest fret
            lowest = min(fretted)
            strings = [s for s, f in played if f == lowest]
            if len(strings) >= 2 and lowest - base < rows:
                y = cell(strings[0], lowest)[1]
                self.create_line(sx[strings[0]], y, sx[strings[-1]], y, width=2 * r, capstyle=tk.ROUND, fill=FG)
        for s, f in played:
            if f == 0 or f - base >= rows:
                continue
            x, y = cell(s, f)
            is_root = guitar.fret_pc(s, f, tuning) == root_pc
            self.create_oval(x - r, y - r, x + r, y + r, fill=ACCENT if is_root else FG, outline="")
        if subtitle:
            self.create_text(self.W * u / 2, 150 * u, text=subtitle, fill=MUTED, font=font(11.5 * u))


# --- circle of fifths ----------------------------------------------------

OUTER_LABELS = [pretty(n) for n in theory.CIRCLE_MAJOR]
OUTER_LABELS[6] = pretty("F#") + "/" + pretty("Gb")
INNER_LABELS = [pretty(n + "m") for n in theory.CIRCLE_MINOR]


class CircleCanvas(tk.Canvas):
    """Clickable circle of fifths: majors outside, relative minors inside."""

    def __init__(self, master, on_select, **kw):
        super().__init__(master, bg=PANEL, highlightthickness=0, **kw)
        self.on_select = on_select  # called with (pitch class, mode)
        self.pc, self.mode = 0, "major"
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self._clicked)

    def render(self, pc: int, mode: str) -> None:
        self.pc, self.mode = pc, mode
        self.redraw()

    def _dims(self):
        w, h = max(self.winfo_width(), 200), max(self.winfo_height(), 200)
        s = min(w, h)
        return w / 2, h / 2, s, 0.43 * s, 0.31 * s, 0.19 * s

    @staticmethod
    def _angle(i: int) -> float:
        return 90 - 30 * i  # degrees, counter-clockwise from 3 o'clock

    def _polar(self, cx, cy, i, radius):
        a = math.radians(self._angle(i))
        return cx + radius * math.cos(a), cy - radius * math.sin(a)

    def redraw(self) -> None:
        self.delete("all")
        cx, cy, s, r_out, r_mid, r_in = self._dims()
        index = theory.circle_index(self.pc, self.mode)
        family = theory.FAMILY_MAJOR if self.mode == "major" else theory.FAMILY_MINOR
        roles = {(ring, (index + off) % 12): roman for (ring, off), roman in family.items()}

        for ring, radius, base in (("major", r_out, "#2c3442"), ("minor", r_mid, "#232a36")):
            for i in range(12):
                role = roles.get((ring, i))
                tonic = role is not None and ring == self.mode and i == index
                fill = ACCENT if tonic else ("#35587f" if ring == "major" else "#2e4c6e") if role else base
                self.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                                start=self._angle(i) - 15, extent=30, style=tk.PIESLICE,
                                fill=fill, outline=BG, width=2)
        self.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, fill="#171b22", outline=BG, width=2)

        for ring, r_a, r_b, labels, size in (("major", r_out, r_mid, OUTER_LABELS, 0.052),
                                             ("minor", r_mid, r_in, INNER_LABELS, 0.040)):
            mid = (r_a + r_b) / 2
            for i in range(12):
                role = roles.get((ring, i))
                tonic = role is not None and ring == self.mode and i == index
                color = "#1b1f27" if tonic else FG if role else "#c2cad8"
                if role:
                    x, y = self._polar(cx, cy, i, mid + (r_a - r_b) * 0.14)
                    self.create_text(x, y, text=labels[i], fill=color, font=font(s * size, "bold"))
                    x, y = self._polar(cx, cy, i, mid - (r_a - r_b) * 0.22)
                    self.create_text(x, y, text=pretty(role), fill="#1b1f27" if tonic else BLUE,
                                     font=font(s * 0.030, "bold"))
                else:
                    x, y = self._polar(cx, cy, i, mid)
                    self.create_text(x, y, text=labels[i], fill=color, font=font(s * size))

        for i in range(12):  # key signature ring
            count, kind = theory.key_signature(i)
            mark = "♯" if kind == "sharp" else "♭"
            text = "0" if count == 0 else f"{count}{mark}"
            if i == 6:
                text = "6♯/6♭"
            x, y = self._polar(cx, cy, i, r_out + 0.045 * s)
            self.create_text(x, y, text=text, fill=MUTED, font=font(s * 0.028))

        tonic = theory.key_name(self.pc, self.mode)
        count, kind = theory.key_signature(index)
        sig = "no sharps or flats" if count == 0 else f"{count} {kind}{'s' if count > 1 else ''}"
        self.create_text(cx, cy - r_in * 0.42, text=pretty(tonic) + (" minor" if self.mode == "minor" else " major"),
                         fill=ACCENT, font=font(s * 0.050, "bold"))
        self.create_text(cx, cy, text=sig, fill=FG, font=font(s * 0.032))
        rel_pc, rel_mode = theory.relative_key(self.pc, self.mode)
        self.create_text(cx, cy + r_in * 0.42, text="relative " + pretty(theory.key_name(rel_pc, rel_mode))
                         + (" minor" if rel_mode == "minor" else " major"), fill=MUTED, font=font(s * 0.030))

    def _clicked(self, event) -> None:
        cx, cy, s, r_out, r_mid, r_in = self._dims()
        dx, dy = event.x - cx, cy - event.y
        r = math.hypot(dx, dy)
        if not r_in < r <= r_out:
            return
        i = round((90 - math.degrees(math.atan2(dy, dx))) / 30) % 12
        mode = "major" if r > r_mid else "minor"
        self.on_select(theory.key_pc(i, mode), mode)
