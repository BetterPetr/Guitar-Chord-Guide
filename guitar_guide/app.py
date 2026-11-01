"""Guitar Chord Guide: main window and tabs."""
from __future__ import annotations

import ctypes
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk

from . import guitar, theory
from .audio import Player
from .guide_text import GUIDE
from .theory import pretty
from .widgets import (ACCENT, BG, BLUE, CAGED_COLORS, FG, FONT, MUTED, PANEL, PANEL_HI,
                      ChordDiagram, CircleCanvas, Dot, FretboardCanvas, Outline)

INTERVALS12 = ["1", "b2", "2", "b3", "3", "4", "b5", "5", "b6", "6", "b7", "7"]
DARK_TEXT = "#1b1f27"


class KeyState:
    """The key every tab follows: a tonic pitch class plus major/minor."""

    def __init__(self) -> None:
        self.pc, self.mode = 0, "major"
        self._listeners = []

    def subscribe(self, fn) -> None:
        self._listeners.append(fn)

    def set(self, pc=None, mode=None) -> None:
        new = ((self.pc if pc is None else pc % 12), (mode or self.mode))
        if new == (self.pc, self.mode):
            return
        self.pc, self.mode = new
        for fn in self._listeners:
            fn()

    @property
    def tonic(self) -> str:
        return theory.key_name(self.pc, self.mode)

    @property
    def index(self) -> int:
        return theory.circle_index(self.pc, self.mode)


class Tab(ttk.Frame):
    def __init__(self, master, app: "App") -> None:
        super().__init__(master, padding=12)
        self.app = app

    def refresh(self) -> None:
        """Called whenever the global key changes."""


def clear(frame: tk.Widget) -> None:
    for child in frame.winfo_children():
        child.destroy()


def notes_text(names) -> str:
    return "  ".join(pretty(n) for n in names)


# --- circle of fifths tab --------------------------------------------------

class CircleTab(Tab):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.columnconfigure(0, weight=3, uniform="c")
        self.columnconfigure(1, weight=2, uniform="c")
        self.rowconfigure(0, weight=1)
        self.circle = CircleCanvas(self, on_select=app.key.set)
        self.circle.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        side = ttk.Frame(self)
        side.grid(row=0, column=1, sticky="nsew")
        wrap = int(470 * app.scale)
        self.title = ttk.Label(side, style="Title.TLabel")
        self.title.pack(anchor="w")
        self.facts = ttk.Label(side, style="Body.TLabel", justify="left", wraplength=wrap)
        self.facts.pack(anchor="w", pady=(4, 8))
        bar = ttk.Frame(side)
        bar.pack(anchor="w", fill="x")
        self.sevenths = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Show 7th chords", variable=self.sevenths,
                        command=self.refresh).pack(side="left")
        ttk.Button(bar, text="Pentatonic on fretboard →",
                   command=lambda: app.show_scale(None)).pack(side="right")
        self.diagrams = ttk.Frame(side)
        self.diagrams.pack(anchor="w", pady=8)
        ttk.Label(side, style="Muted.TLabel", justify="left", wraplength=wrap, text=(
            "Click any segment to change key. Clockwise is up a fifth (towards V), "
            "anticlockwise is up a fourth (towards IV). The six highlighted segments are the "
            "chords that belong to the key; the seventh, the diminished chord, sits just "
            "outside the family. Click a chord diagram to hear it.")).pack(anchor="w")

    def refresh(self) -> None:
        st = self.app.key
        self.circle.render(st.pc, st.mode)
        mode_name = "major" if st.mode == "major" else "minor"
        self.title.config(text=f"{pretty(st.tonic)} {mode_name}")
        count, kind = theory.key_signature(st.index)
        accidentals = notes_text(theory.signature_accidentals(st.index))
        sig = "No sharps or flats" if count == 0 else f"{count} {kind}{'s' if count > 1 else ''}: {accidentals}"
        scale = theory.scale_notes(st.tonic, st.mode)
        pent_key = "major_pent" if st.mode == "major" else "minor_pent"
        rel_pc, rel_mode = theory.relative_key(st.pc, st.mode)
        rel = theory.key_name(rel_pc, rel_mode)
        self.facts.config(text=(
            f"Key signature: {sig}\n"
            f"{theory.SCALES[st.mode].name} scale: {notes_text(scale)}\n"
            f"{theory.SCALES[pent_key].name}: {notes_text(theory.scale_notes(st.tonic, pent_key))}\n"
            f"Same five notes as {pretty(rel)} {theory.SCALES[('minor_pent' if rel_mode == 'minor' else 'major_pent')].name.lower()}"))
        clear(self.diagrams)
        for i, chord in enumerate(theory.diatonic_chords(st.tonic, st.mode, self.sevenths.get())):
            v = self.app.voicing_for(chord)
            d = ChordDiagram(self.diagrams, scale=self.app.scale * 0.92)
            d.show(chord.name, v.frets, chord.pc, subtitle=pretty(chord.roman),
                   command=lambda v=v: self.app.play(v))
            d.grid(row=i // 4, column=i % 4, padx=3, pady=3)


# --- fretboard tab ---------------------------------------------------------

class FretboardTab(Tab):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.chords: list[theory.Chord] = []
        self._mode = None
        self.scale_var = tk.StringVar(value="major_pent")
        self.pent_var = tk.BooleanVar(value=True)
        self.blue_var = tk.BooleanVar(value=False)
        self.box_var = tk.StringVar(value="All")
        self.label_var = tk.StringVar(value="names")
        self.caged_var = tk.BooleanVar(value=False)
        self.shape_var = tk.StringVar(value="All")

        row1 = ttk.Frame(self)
        row1.pack(fill="x")
        ttk.Checkbutton(row1, text="Pentatonic", variable=self.pent_var).pack(side="left")
        ttk.Radiobutton(row1, text="Major", variable=self.scale_var, value="major_pent").pack(side="left", padx=(10, 0))
        ttk.Radiobutton(row1, text="Minor", variable=self.scale_var, value="minor_pent").pack(side="left", padx=(8, 0))
        ttk.Checkbutton(row1, text="+ blue note", variable=self.blue_var).pack(side="left", padx=(14, 0))
        ttk.Label(row1, text="Box").pack(side="left", padx=(18, 4))
        self.box_combo = ttk.Combobox(row1, textvariable=self.box_var, width=5, state="readonly",
                                      values=["All", "1", "2", "3", "4", "5"])
        self.box_combo.pack(side="left")
        ttk.Label(row1, text="Labels").pack(side="left", padx=(18, 4))
        for text, value in (("Notes", "names"), ("Intervals", "intervals"), ("None", "none")):
            ttk.Radiobutton(row1, text=text, variable=self.label_var, value=value).pack(side="left", padx=(0, 6))

        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=(8, 8))
        ttk.Checkbutton(row2, text="CAGED shapes", variable=self.caged_var).pack(side="left")
        ttk.Label(row2, text="Chord").pack(side="left", padx=(14, 4))
        self.chord_combo = ttk.Combobox(row2, width=12, state="readonly")
        self.chord_combo.pack(side="left")
        ttk.Label(row2, text="Shape").pack(side="left", padx=(14, 4))
        self.shape_combo = ttk.Combobox(row2, textvariable=self.shape_var, width=5, state="readonly",
                                        values=["All", *guitar.CAGED_ORDER])
        self.shape_combo.pack(side="left")
        ttk.Label(row2, style="Muted.TLabel",
                  text="   Click the fretboard to hear a note.").pack(side="left")

        for var in (self.scale_var, self.pent_var, self.blue_var, self.box_var, self.label_var,
                    self.caged_var, self.shape_var):
            var.trace_add("write", lambda *a: self.redraw())
        self.chord_combo.bind("<<ComboboxSelected>>", lambda e: self.redraw())

        self.canvas = FretboardCanvas(self, on_click=self._note_clicked)
        self.canvas.config(height=int(260 * app.scale))
        self.canvas.pack(fill="both", expand=True)

        self.info = ttk.Label(self, style="Body.TLabel", justify="left", wraplength=int(1180 * app.scale))
        self.info.pack(anchor="w", pady=(8, 4), fill="x")

        self.strip = ttk.Frame(self)
        self.strip_diagrams = []
        for i in range(5):
            d = ChordDiagram(self.strip, scale=app.scale * 0.9)
            d.grid(row=0, column=i, padx=4)
            self.strip_diagrams.append(d)
        ttk.Label(self.strip, style="Muted.TLabel", justify="left", wraplength=int(430 * app.scale),
                  text="The five shapes, in order up the neck. Click one to isolate it and hear it. "
                       "Orange dots are the chord root."
                  ).grid(row=0, column=5, padx=14, sticky="w")

    def apply_scale(self, kind: str | None, blue: bool = False) -> None:
        if kind:
            self.scale_var.set(kind)
        self.pent_var.set(True)
        self.blue_var.set(blue)
        self.box_var.set("All")
        self.caged_var.set(False)

    def refresh(self) -> None:
        st = self.app.key
        if st.mode != self._mode:
            self.scale_var.set("major_pent" if st.mode == "major" else "minor_pent")
            self._mode = st.mode
        self.chords = [c for c in theory.diatonic_chords(st.tonic, st.mode) if c.ctype in ("maj", "min")]
        self.chord_combo.config(values=[f"{pretty(c.roman)}  {pretty(c.name)}" for c in self.chords])
        self.chord_combo.current(0)
        self.redraw()

    def _note_clicked(self, string: int, fret: int) -> None:
        self.app.player.strum([guitar.OPEN_MIDI[string] + fret])

    def _pick_shape(self, letter: str, voicing) -> None:
        self.shape_var.set(letter)
        self.app.play(voicing)

    def redraw(self) -> None:
        if not self.chords:
            return
        st, n_frets = self.app.key, self.canvas.nfrets
        kind = self.scale_var.get()
        scale_mode = "minor" if kind == "minor_pent" else "major"
        scale_tonic = theory.key_name(st.pc, scale_mode)
        blue_on = self.blue_var.get() and kind in theory.BLUE_NOTES
        notes = theory.scale_degrees(scale_tonic, kind, blue_on)
        by_pc = {n.pc: n for n in notes}
        blue_pc = (st.pc + theory.BLUE_NOTES[kind][0]) % 12 if blue_on else None
        flats = theory.key_signature(theory.circle_index(st.pc, scale_mode))[1] == "flat"
        label_mode = self.label_var.get()

        def label(pc: int) -> str:
            if label_mode == "none":
                return ""
            if label_mode == "intervals":
                return pretty(INTERVALS12[(pc - st.pc) % 12])
            return pretty(by_pc[pc].name if pc in by_pc else theory.pc_name(pc, flats))

        boxes = guitar.pentatonic_boxes(st.pc, kind, n_frets)
        box_choice = self.box_var.get()
        box_n = None if box_choice == "All" else int(box_choice)
        caged_on = self.caged_var.get()
        chord = self.chords[min(self.chord_combo.current(), len(self.chords) - 1)]
        shapes = []
        if caged_on:
            shapes = [v for v in guitar.caged_instances(chord.pc, chord.ctype == "min", n_frets)
                      if self.shape_var.get() in ("All", v.form.caged)]

        def with_blue(instance):
            """The box's own notes plus any blue-note positions beside it."""
            frets = [f for _, f in instance]
            extra = set()
            if blue_pc is not None:
                extra = {(s, f) for s, f in guitar.scale_positions({blue_pc}, n_frets)
                         if min(frets) - 1 <= f <= max(frets)}
            return set(instance) | extra

        outlines, focus = [], None  # focus None means "every scale note at full strength"
        best_box_numbers = []
        if box_n:
            focus = set()
            for inst in boxes[box_n]:
                focus |= with_blue(inst)
                frets = [f for _, f in inst]
                outlines.append(Outline((0, 5), (min(frets), max(frets)), "#d7dde8"))
        elif shapes:
            focus = set()
            if self.shape_var.get() != "All":
                for v in shapes:
                    num, inst = guitar.best_box(v, boxes)
                    best_box_numbers.append(num)
                    focus |= with_blue(inst)
                    frets = [f for _, f in inst]
                    outlines.append(Outline((0, 5), (min(frets), max(frets)), "#d7dde8"))

        dots: dict[tuple, Dot] = {}
        if self.pent_var.get():
            for s, f in guitar.scale_positions(set(by_pc), n_frets):
                pc = guitar.fret_pc(s, f)
                if focus is not None and (s, f) not in focus:
                    dots[(s, f)] = Dot(s, f, "#3a3f4b", label(pc), MUTED, size=0.72)
                elif pc == st.pc:
                    dots[(s, f)] = Dot(s, f, ACCENT, label(pc), DARK_TEXT)
                elif pc == blue_pc:
                    dots[(s, f)] = Dot(s, f, "#1e88e5", label(pc))
                else:
                    dots[(s, f)] = Dot(s, f, "#2a8c78", label(pc))

        for v in shapes:
            color = CAGED_COLORS[v.form.caged]
            strings = [s for s, _ in v.played]
            frets = [f for _, f in v.played]
            outlines.append(Outline((min(strings), max(strings)), (min(frets), max(frets)), color, dash=False))
            for s, f in v.played:
                pc = guitar.fret_pc(s, f)
                dots[(s, f)] = Dot(s, f, color, label(pc), ring=(pc == chord.pc), size=1.1)
        self.canvas.show(dots.values(), outlines)
        self._update_info(kind, scale_tonic, notes, chord, shapes, box_n, boxes, best_box_numbers, by_pc)

        if caged_on:
            self.strip.pack(anchor="w", pady=(0, 2))
            for d, v in zip(self.strip_diagrams, guitar.caged_voicings(chord.pc, chord.ctype == "min")):
                letter = v.form.caged
                d.show(f"{letter} shape", v.frets, chord.pc,
                       subtitle="open" if v.position == 0 else f"fret {v.position}",
                       title_color=CAGED_COLORS[letter],
                       command=lambda l=letter, v=v: self._pick_shape(l, v))
        else:
            self.strip.pack_forget()

    def _update_info(self, kind, scale_tonic, notes, chord, shapes, box_n, boxes, best_numbers, by_pc) -> None:
        sc = theory.SCALES[kind]
        lines = [f"{pretty(scale_tonic)} {sc.name.lower()}:  {notes_text(n.name for n in notes)}"]
        if kind == "major_pent":
            rel = theory.key_name((self.app.key.pc + 9) % 12, "minor")
            lines[0] += f"      (the same five notes as {pretty(rel)} minor pentatonic)"
        if box_n:
            spans = []
            for inst in boxes[box_n]:
                frets = [f for _, f in inst]
                spans.append(f"frets {min(frets)}–{max(frets)}")
            lines.append(f"Box {box_n}: " + " and ".join(spans) + ". Boxes are numbered from the minor-pentatonic "
                         "root on the low E string (Box 1); the major pentatonic uses the same shapes.")
        if self.caged_var.get():
            tones = sum(1 for pc in chord.pcs if pc in by_pc)
            fit = "all" if tones == len(chord.pcs) else f"{tones} of {len(chord.pcs)}"
            lines.append(f"{pretty(chord.name)}  ({notes_text(chord.notes)}): {fit} of its notes belong to this pentatonic.")
            if shapes and self.shape_var.get() != "All":
                v = shapes[0]
                where = "open position" if v.position == 0 else f"lowest fret {v.position}"
                box = f"; it sits inside pentatonic Box {best_numbers[0]}" if best_numbers else ""
                lines.append(f"{v.form.caged} shape ({where}){box}. Dashed box = the pentatonic notes around it.")
        self.info.config(text="\n".join(lines))


# --- chord library tab -----------------------------------------------------

class ChordsTab(Tab):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.root_name = "C"
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        ttk.Label(left, text="Root", style="Head.TLabel").pack(anchor="w")
        self.root_combo = ttk.Combobox(left, width=8, state="readonly",
                                       values=[pretty(theory.key_name(pc, "major")) for pc in range(12)])
        self.root_combo.pack(anchor="w", pady=(2, 10))
        self.root_combo.bind("<<ComboboxSelected>>", self._root_picked)
        ttk.Label(left, text="Chord type", style="Head.TLabel").pack(anchor="w")
        self.type_keys = list(theory.CHORD_TYPES)
        self.types = tk.Listbox(left, exportselection=False, width=26, height=len(self.type_keys),
                                bg=PANEL, fg=FG, selectbackground=ACCENT, selectforeground=DARK_TEXT,
                                highlightthickness=0, borderwidth=0, activestyle="none", font=(FONT, 11))
        for key in self.type_keys:
            ct = theory.CHORD_TYPES[key]
            self.types.insert("end", f"{ct.name}   ({pretty(ct.suffix) or 'maj'})")
        self.types.selection_set(0)
        self.types.pack(anchor="w", pady=(2, 0))
        self.types.bind("<<ListboxSelect>>", lambda e: self.update_view())

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew")
        self.title = ttk.Label(right, style="Title.TLabel")
        self.title.pack(anchor="w")
        self.facts = ttk.Label(right, style="Body.TLabel", justify="left", wraplength=int(860 * app.scale))
        self.facts.pack(anchor="w", pady=(2, 10))
        self.gallery = ttk.Frame(right)
        self.gallery.pack(anchor="w")
        ttk.Label(right, text="Chords in the current key", style="Head.TLabel").pack(anchor="w", pady=(16, 4))
        self.quick = ttk.Frame(right)
        self.quick.pack(anchor="w")
        self.keys_label = ttk.Label(right, style="Body.TLabel", justify="left", wraplength=int(860 * app.scale))
        self.keys_label.pack(anchor="w", pady=(16, 0))

    def _root_picked(self, _event=None) -> None:
        self.root_name = theory.key_name(self.root_combo.current(), "major")
        self.update_view()

    def _set_chord(self, chord: theory.Chord) -> None:
        self.root_name = chord.root
        self.types.selection_clear(0, "end")
        self.types.selection_set(self.type_keys.index(chord.ctype))
        self.update_view()

    def refresh(self) -> None:
        st = self.app.key
        chord = theory.diatonic_chords(st.tonic, st.mode)[0]
        self.root_name = chord.root
        self.types.selection_clear(0, "end")
        self.types.selection_set(self.type_keys.index(chord.ctype))
        clear(self.quick)
        for chord in theory.diatonic_chords(st.tonic, st.mode):
            ttk.Button(self.quick, text=f"{pretty(chord.roman)}  {pretty(chord.name)}", width=11,
                       command=lambda c=chord: self._set_chord(c)).pack(side="left", padx=(0, 4))
        self.update_view()

    def update_view(self) -> None:
        sel = self.types.curselection()
        if not sel:
            return
        ctype = self.type_keys[sel[0]]
        ct = theory.CHORD_TYPES[ctype]
        chord = theory.Chord(self.root_name, ctype)
        self.root_combo.set(pretty(self.root_name))
        self.title.config(text=f"{pretty(chord.name)}   {ct.name}")
        formula = pretty("  –  ".join(ct.labels))
        self.facts.config(text=f"Formula:  {formula}\nNotes:  {notes_text(chord.notes)}")
        clear(self.gallery)
        for i, v in enumerate(guitar.voicings(chord.pc, ctype)):
            d = ChordDiagram(self.gallery, scale=self.app.scale)
            d.show(chord.name, v.frets, chord.pc,
                   subtitle=f"{v.form.name} · " + ("open" if v.position == 0 else f"fret {v.position}"),
                   command=lambda v=v: self.app.play(v))
            d.grid(row=0, column=i, padx=4, pady=2)
        found = theory.keys_containing(chord.pc, ctype)
        if found:
            text = "   ·   ".join(f"{pretty(roman)} in {pretty(key)}" for roman, key in found)
            self.keys_label.config(text=f"On the circle of fifths this chord lives in:\n{text}")
        else:
            self.keys_label.config(text="This chord isn't diatonic to any major or natural minor key; "
                                        "it's a colour chord borrowed for effect.")


# --- progressions tab ------------------------------------------------------

class ProgressionsTab(Tab):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.items: list[theory.Progression] = []
        self.current: theory.Progression | None = None
        self.chords: list[theory.Chord] = []
        self.voicings: list[guitar.Voicing] = []
        self.diagrams: list[ChordDiagram] = []
        self._after_ids: list[str] = []
        self._playing_path = None
        self._playing = False
        self._mode = None

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        ttk.Label(left, text="Progressions", style="Head.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(left, exportselection=False, width=34, height=15, bg=PANEL, fg=FG,
                                  selectbackground=ACCENT, selectforeground=DARK_TEXT, highlightthickness=0,
                                  borderwidth=0, activestyle="none", font=(FONT, 11))
        self.listbox.pack(anchor="w", pady=(2, 10))
        self.listbox.bind("<<ListboxSelect>>", self._picked)
        ttk.Label(left, text="Your own (Roman numerals)", style="Head.TLabel").pack(anchor="w")
        self.custom = tk.StringVar(value="I vi ii V7")
        entry = ttk.Entry(left, textvariable=self.custom, width=32)
        entry.pack(anchor="w", pady=(2, 4))
        entry.bind("<Return>", lambda e: self._apply_custom())
        ttk.Button(left, text="Use these chords", command=self._apply_custom).pack(anchor="w")
        self.error = ttk.Label(left, style="Error.TLabel", wraplength=int(260 * app.scale))
        self.error.pack(anchor="w", pady=4)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew")
        self.title = ttk.Label(right, style="Title.TLabel")
        self.title.pack(anchor="w")
        self.sub = ttk.Label(right, style="Body.TLabel", justify="left", wraplength=int(860 * app.scale))
        self.sub.pack(anchor="w", pady=(2, 8))

        controls = ttk.Frame(right)
        controls.pack(anchor="w", pady=(0, 8))
        self.play_btn = ttk.Button(controls, text="▶ Play", command=self.play)
        self.play_btn.pack(side="left")
        ttk.Button(controls, text="■ Stop", command=self.stop).pack(side="left", padx=(6, 14))
        ttk.Label(controls, text="Tempo").pack(side="left")
        self.bpm = tk.IntVar(value=96)
        ttk.Spinbox(controls, from_=50, to=200, width=5, textvariable=self.bpm).pack(side="left", padx=(4, 12))
        ttk.Label(controls, text="Beats per chord").pack(side="left")
        self.beats = tk.IntVar(value=4)
        ttk.Spinbox(controls, from_=1, to=8, width=3, textvariable=self.beats).pack(side="left", padx=(4, 12))
        self.loop = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="Loop", variable=self.loop).pack(side="left")
        self.status = ttk.Label(controls, style="Muted.TLabel")
        self.status.pack(side="left", padx=12)
        if not app.player.available:
            self.play_btn.state(["disabled"])
            self.status.config(text="Audio playback needs Windows (winsound).")

        self.grid_frame = ttk.Frame(right)
        self.grid_frame.pack(anchor="w")
        self.solo = ttk.Label(right, style="Body.TLabel", justify="left", wraplength=int(860 * app.scale))
        self.solo.pack(anchor="w", pady=(14, 4))
        ttk.Button(right, text="Show this scale on the fretboard →",
                   command=self._show_solo_scale).pack(anchor="w")

    # -- data --

    def refresh(self) -> None:
        st = self.app.key
        if st.mode != self._mode:
            self._mode = st.mode
            self.items = theory.progressions_for(st.mode)
            self.listbox.delete(0, "end")
            for p in self.items:
                self.listbox.insert("end", p.name)
            self.listbox.selection_set(0)
            self.current = self.items[0]
        self.stop()
        self._rebuild()

    def _picked(self, _event=None) -> None:
        sel = self.listbox.curselection()
        if sel:
            self.current = self.items[sel[0]]
            self.error.config(text="")
            self.stop()
            self._rebuild()

    def _apply_custom(self) -> None:
        tokens = [t for t in re.split(r"[\s,\-–]+", self.custom.get().strip()) if t]
        st = self.app.key
        try:
            if not tokens:
                raise ValueError("type some Roman numerals, e.g. I vi IV V")
            theory.resolve_progression(tokens, st.tonic, st.mode)
        except ValueError as exc:
            self.error.config(text=str(exc))
            return
        self.error.config(text="")
        self.listbox.selection_clear(0, "end")
        solo = "major_pent" if st.mode == "major" else "minor_pent"
        self.current = theory.Progression("Your progression", st.mode, tuple(tokens),
                                          "Numerals are read relative to the key: upper case major, lower case "
                                          "minor, add 7, maj7 or ° as needed, and b before the numeral to flatten.",
                                          solo)
        self.stop()
        self._rebuild()

    def _rebuild(self) -> None:
        st, p = self.app.key, self.current
        if p is None:
            return
        self.chords = theory.resolve_progression(p.numerals, st.tonic, st.mode)
        self.voicings = [self.app.voicing_for(c) for c in self.chords]
        self.title.config(text=p.name)
        numerals = pretty(" – ".join(p.numerals))
        self.sub.config(text=f"{numerals}   in   {pretty(st.tonic)} {st.mode}\n{p.description}")
        clear(self.grid_frame)
        self.diagrams = []
        for i, (chord, v) in enumerate(zip(self.chords, self.voicings)):
            d = ChordDiagram(self.grid_frame, scale=self.app.scale * 0.95)
            d.show(chord.name, v.frets, chord.pc, subtitle=pretty(chord.roman), command=lambda v=v: self.app.play(v))
            d.grid(row=i // 4, column=i % 4, padx=4, pady=4)
            self.diagrams.append(d)
        scale_mode = "minor" if p.solo == "minor_pent" else "major"
        scale_tonic = theory.key_name(st.pc, scale_mode)
        names = notes_text(theory.scale_notes(scale_tonic, p.solo, p.blue))
        blue = " (with the blue note)" if p.blue else ""
        self.solo.config(text=f"Solo with: {pretty(scale_tonic)} {theory.SCALES[p.solo].name.lower()}{blue}:  {names}"
                              + (f"\n{p.solo_tip}" if p.solo_tip else ""))

    def _show_solo_scale(self) -> None:
        if self.current:
            self.app.show_scale(self.current.solo, self.current.blue)

    # -- playback --

    def play(self) -> None:
        if not self.app.player.available or not self.voicings:
            return
        self.stop()
        try:
            bpm, beats = int(self.bpm.get()), int(self.beats.get())
        except (tk.TclError, ValueError):
            self.status.config(text="Tempo and beats must be whole numbers.")
            return
        bpm, beats = max(40, min(220, bpm)), max(1, min(8, beats))
        midis = [v.midis for v in self.voicings]
        self.status.config(text="Rendering…")
        self._playing = True
        player = self.app.player
        self.app.run_bg(lambda: player.render_progression(midis, bpm, beats),
                        lambda result: self._begin(result, bpm, beats))

    def _begin(self, result, bpm: int, beats: int) -> None:
        if not self._playing:
            return
        if isinstance(result, Exception):
            self._playing = False
            self.status.config(text=f"Couldn't render audio: {result}")
            return
        self._playing_path = result
        self._launch(bpm, beats)

    def _launch(self, bpm: int, beats: int) -> None:
        self.app.player.play_file(self._playing_path)
        self.status.config(text="Playing")
        dur_ms = int(beats * 60000 / bpm)
        for i, d in enumerate(self.diagrams):
            self._after_ids.append(self.after(i * dur_ms, lambda i=i: self._highlight(i)))
        self._after_ids.append(self.after(len(self.diagrams) * dur_ms, lambda: self._finished(bpm, beats)))

    def _highlight(self, index: int) -> None:
        for i, d in enumerate(self.diagrams):
            d.set_active(i == index)

    def _finished(self, bpm: int, beats: int) -> None:
        self._after_ids.clear()
        for d in self.diagrams:
            d.set_active(False)
        if self.loop.get() and self._playing:
            self._launch(bpm, beats)
        else:
            self.stop()

    def stop(self) -> None:
        self._playing = False
        for after_id in self._after_ids:
            self.after_cancel(after_id)
        self._after_ids.clear()
        for d in self.diagrams:
            d.set_active(False)
        self.app.player.stop()
        if self.app.player.available:
            self.status.config(text="")


# --- guide tab -------------------------------------------------------------

class GuideTab(Tab):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        text = tk.Text(self, wrap="word", bg=PANEL, fg=FG, borderwidth=0, highlightthickness=0,
                       padx=24, pady=18, font=(FONT, 11), spacing1=2, spacing3=4, cursor="arrow")
        scroll = ttk.Scrollbar(self, command=text.yview)
        text.config(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        text.tag_config("h1", font=(FONT, 20, "bold"), foreground=ACCENT, spacing1=6, spacing3=8)
        text.tag_config("h2", font=(FONT, 14, "bold"), foreground=BLUE, spacing1=14, spacing3=4)
        text.tag_config("li", lmargin1=22, lmargin2=38)
        for kind, line in GUIDE:
            text.insert("end", line + "\n", kind)
        text.config(state="disabled")


# --- application -----------------------------------------------------------

class App(tk.Tk):
    TAB_ORDER = (("circle", "Circle of Fifths", CircleTab), ("fretboard", "Fretboard", FretboardTab),
                 ("chords", "Chord Library", ChordsTab), ("progressions", "Progressions", ProgressionsTab),
                 ("guide", "Guide", GuideTab))

    def __init__(self) -> None:
        super().__init__()
        self.title("Guitar Chord Guide")
        self.scale = max(1.0, min(2.5, float(self.tk.call("tk", "scaling")) / (96 / 72)))
        width, height = int(1360 * self.scale), int(900 * self.scale)
        width, height = min(width, self.winfo_screenwidth() - 40), min(height, self.winfo_screenheight() - 80)
        self.geometry(f"{width}x{height}+20+20")
        self.minsize(int(1000 * self.scale), int(680 * self.scale))
        self.configure(bg=BG)
        self._style()

        self.key = KeyState()
        self.player = Player()
        self._queue: queue.Queue = queue.Queue()
        self.area_var = tk.StringVar(value=next(iter(guitar.AREAS)))

        self._build_header()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tabs = {}
        for key, title, cls in self.TAB_ORDER:
            tab = cls(self.notebook, self)
            self.tabs[key] = tab
            self.notebook.add(tab, text=title)
        self.key.subscribe(self._key_changed)
        self.area_var.trace_add("write", lambda *a: self._key_changed())
        self._key_changed()
        self.after(60, self._poll)

    def _style(self) -> None:
        self.option_add("*TCombobox*Listbox.background", PANEL_HI)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", DARK_TEXT)
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL_HI, font=(FONT, 10),
                    bordercolor=PANEL_HI, lightcolor=PANEL_HI, darkcolor=PANEL_HI, troughcolor=PANEL)
        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 4, 0, 0))
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(18, 8), font=(FONT, 11))
        s.map("TNotebook.Tab", background=[("selected", PANEL_HI)], foreground=[("selected", ACCENT)])
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Title.TLabel", font=(FONT, 20, "bold"), foreground=ACCENT)
        s.configure("Head.TLabel", font=(FONT, 11, "bold"), foreground=BLUE)
        s.configure("Body.TLabel", font=(FONT, 11))
        s.configure("Muted.TLabel", foreground=MUTED, font=(FONT, 10))
        s.configure("Error.TLabel", foreground="#ef5350")
        s.configure("TButton", background=PANEL_HI, foreground=FG, padding=(10, 5), borderwidth=0)
        s.map("TButton", background=[("active", "#3b4557"), ("disabled", PANEL)],
              foreground=[("disabled", MUTED)])
        for name in ("TRadiobutton", "TCheckbutton"):
            s.configure(name, background=BG, foreground=FG, indicatorbackground=PANEL_HI,
                        indicatorforeground=ACCENT)
            s.map(name, background=[("active", BG)], indicatorbackground=[("selected", PANEL_HI)])
        s.configure("TCombobox", arrowcolor=FG, selectbackground=PANEL_HI, selectforeground=FG)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL_HI)], foreground=[("readonly", FG)])
        s.configure("TEntry", insertcolor=FG, padding=4)
        s.configure("TSpinbox", arrowcolor=FG, padding=3)
        s.configure("Vertical.TScrollbar", background=PANEL_HI, arrowcolor=FG)

    def _build_header(self) -> None:
        bar = ttk.Frame(self, padding=(14, 10, 14, 6))
        bar.pack(fill="x")
        ttk.Label(bar, text="Key", style="Head.TLabel").pack(side="left")
        self.key_combo = ttk.Combobox(bar, width=6, state="readonly")
        self.key_combo.pack(side="left", padx=(6, 10))
        self.key_combo.bind("<<ComboboxSelected>>", lambda e: self.key.set(pc=self.key_combo.current()))
        self.mode_var = tk.StringVar(value="major")
        for text, value in (("Major", "major"), ("Minor", "minor")):
            ttk.Radiobutton(bar, text=text, variable=self.mode_var, value=value,
                            command=lambda: self.key.set(mode=self.mode_var.get())).pack(side="left", padx=(0, 8))
        self.summary = ttk.Label(bar, style="Muted.TLabel")
        self.summary.pack(side="left", padx=14)
        ttk.Label(bar, text="Chord voicings").pack(side="right", padx=(0, 0))
        area = ttk.Combobox(bar, textvariable=self.area_var, width=12, state="readonly", values=list(guitar.AREAS))
        area.pack(side="right", padx=(0, 8))

    # -- shared helpers for the tabs --

    def voicing_for(self, chord: theory.Chord) -> guitar.Voicing:
        return guitar.pick_voicing(chord.pc, chord.ctype, guitar.AREAS[self.area_var.get()])

    def play(self, voicing: guitar.Voicing) -> None:
        self.player.strum(voicing.midis)

    def show_scale(self, kind: str | None, blue: bool = False) -> None:
        tab = self.tabs["fretboard"]
        tab.apply_scale(kind or ("major_pent" if self.key.mode == "major" else "minor_pent"), blue)
        self.notebook.select(tab)

    def run_bg(self, work, done) -> None:
        """Run `work` on a thread and hand its result (or exception) to `done` on the Tk thread."""
        def target() -> None:
            try:
                result = work()
            except Exception as exc:  # reported back to the caller
                result = exc
            self._queue.put((done, result))
        threading.Thread(target=target, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                done, result = self._queue.get_nowait()
                done(result)
        except queue.Empty:
            pass
        self.after(60, self._poll)

    def _key_changed(self) -> None:
        st = self.key
        self.mode_var.set(st.mode)
        self.key_combo.config(values=[pretty(theory.key_name(pc, st.mode)) for pc in range(12)])
        self.key_combo.current(st.pc)
        rel_pc, rel_mode = theory.relative_key(st.pc, st.mode)
        self.summary.config(text=f"relative {pretty(theory.key_name(rel_pc, rel_mode))} {rel_mode}   ·   "
                                 + notes_text(theory.scale_notes(st.tonic, st.mode)))
        for tab in self.tabs.values():
            tab.refresh()


def main() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    App().mainloop()
