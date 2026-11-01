"""Guitar-specific geometry: tunings, chord forms, CAGED shapes, pentatonic boxes.

Strings are indexed 0..5 from the lowest to the highest; frets are ints with 0 for
an open string and None for a muted one.  No GUI imports.

Every shape in this module is written for standard tuning.  Other tunings are
handled by a "reference tuning": the same shapes sounding `shift` semitones lower.
A drop tuning also lowers its lowest string a further whole step, so a note on
that string needs a fret two higher than in the reference tuning; the dropped
string can also reach two semitones below the reference range, which is what
makes one-finger power chords possible.
"""
from __future__ import annotations

from dataclasses import dataclass

from .theory import LETTER_PC, SHARP_NAMES

STANDARD_OPEN = (40, 45, 50, 55, 59, 64)  # E2 A2 D3 G3 B3 E4
STRING_LABELS = ("E", "A", "D", "G", "B", "e")
X = None  # muted string

CAGED_ORDER = "CAGED"
PENT_BOXES = 5


@dataclass(frozen=True)
class Tuning:
    name: str
    shift: int = 0      # semitones every string sits below standard (ignoring the drop)
    drop: bool = False  # lowest string a further whole step down

    @property
    def open(self) -> tuple:
        pitches = [m + self.shift for m in STANDARD_OPEN]
        if self.drop:
            pitches[0] -= 2
        return tuple(pitches)

    @property
    def low_offset(self) -> int:
        """Frets to add on the lowest string to sound the same note as in the reference tuning."""
        return 2 if self.drop else 0

    @property
    def labels(self) -> tuple:
        if self.shift == 0 and not self.drop:
            return STRING_LABELS
        return tuple(SHARP_NAMES[m % 12] for m in self.open)

    @property
    def description(self) -> str:
        return " ".join(self.labels)


STANDARD = Tuning("Standard")
TUNINGS = (STANDARD, Tuning("Drop D", 0, True), Tuning("Drop C#", -1, True), Tuning("Drop C", -2, True))
TUNING_BY_NAME = {t.name: t for t in TUNINGS}

OPEN_MIDI = STANDARD.open


def fret_pc(string: int, fret: int, tuning: Tuning = STANDARD) -> int:
    return (tuning.open[string] + fret) % 12


def midi_freq(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


# --- chord forms ---------------------------------------------------------

@dataclass(frozen=True)
class Form:
    """An open-position chord shape that can be slid up the neck as a barre chord."""
    name: str
    ctype: str
    frets: tuple
    root_pc: int
    caged: str = ""  # C, A, G, E or D for the five CAGED triad shapes


def _form(name, ctype, frets, root, caged=""):
    return Form(name, ctype, frets, LETTER_PC[root], caged)


_CAGED_MAJOR = {"C": (X, 3, 2, 0, 1, 0), "A": (X, 0, 2, 2, 2, 0), "G": (3, 2, 0, 0, 0, 3),
                "E": (0, 2, 2, 1, 0, 0), "D": (X, X, 0, 2, 3, 2)}
_CAGED_MINOR = {"C": (X, 3, 1, 0, 1, X), "A": (X, 0, 2, 2, 1, 0), "G": (3, 1, 0, 0, 3, 3),
                "E": (0, 2, 2, 0, 0, 0), "D": (X, X, 0, 2, 3, 1)}

FORMS: tuple[Form, ...] = (
    *(_form(f"{k} shape", "maj", f, k, k) for k, f in _CAGED_MAJOR.items()),
    *(_form(f"{k} shape", "min", f, k, k) for k, f in _CAGED_MINOR.items()),
    _form("E shape", "7", (0, 2, 0, 1, 0, 0), "E"),
    _form("A shape", "7", (X, 0, 2, 0, 2, 0), "A"),
    _form("D shape", "7", (X, X, 0, 2, 1, 2), "D"),
    _form("C shape", "7", (X, 3, 2, 3, 1, 0), "C"),
    _form("E shape", "maj7", (0, 2, 1, 1, 0, 0), "E"),
    _form("A shape", "maj7", (X, 0, 2, 1, 2, 0), "A"),
    _form("D shape", "maj7", (X, X, 0, 2, 2, 2), "D"),
    _form("C shape", "maj7", (X, 3, 2, 0, 0, 0), "C"),
    _form("E shape", "m7", (0, 2, 0, 0, 0, 0), "E"),
    _form("A shape", "m7", (X, 0, 2, 0, 1, 0), "A"),
    _form("D shape", "m7", (X, X, 0, 2, 1, 1), "D"),
    _form("A shape", "sus2", (X, 0, 2, 2, 0, 0), "A"),
    _form("D shape", "sus2", (X, X, 0, 2, 3, 0), "D"),
    _form("E shape", "sus4", (0, 2, 2, 2, 0, 0), "E"),
    _form("A shape", "sus4", (X, 0, 2, 2, 3, 0), "A"),
    _form("D shape", "sus4", (X, X, 0, 2, 3, 3), "D"),
    _form("E shape", "dim", (0, 1, 2, 0, X, X), "E"),
    _form("A shape", "dim", (X, 0, 1, 2, 1, X), "A"),
    _form("E shape", "aug", (0, 3, 2, 1, 1, 0), "E"),
    _form("A shape", "aug", (X, 0, 3, 2, 2, 1), "A"),
    _form("E shape", "6", (0, 2, 2, 1, 2, 0), "E"),
    _form("A shape", "6", (X, 0, 2, 2, 2, 2), "A"),
    _form("C shape", "add9", (X, 3, 2, 0, 3, 0), "C"),
    _form("A shape", "add9", (X, 0, 2, 4, 2, 0), "A"),
    _form("E shape", "9", (0, 2, 0, 1, 0, 2), "E"),
    _form("A shape", "9", (X, 0, 2, 4, 2, 3), "A"),
    _form("E shape", "m7b5", (0, 1, 0, 0, X, X), "E"),
    _form("A shape", "m7b5", (X, 0, 1, 0, 1, X), "A"),
    _form("E shape", "5", (0, 2, 2, X, X, X), "E"),
    _form("A shape", "5", (X, 0, 2, 2, X, X), "A"),
)


@dataclass(frozen=True)
class Voicing:
    form: Form
    root_pc: int
    frets: tuple
    tuning: Tuning = STANDARD

    @property
    def played(self) -> list[tuple[int, int]]:
        return [(s, f) for s, f in enumerate(self.frets) if f is not None]

    @property
    def position(self) -> int:
        """Lowest fret used (0 for open chords); handy for ordering up the neck."""
        return min(f for _, f in self.played)

    @property
    def midis(self) -> list[int]:
        return [self.tuning.open[s] + f for s, f in self.played]

    @property
    def label(self) -> str:
        f = self.frets
        if self.tuning.drop and self.form.ctype == "5" and f[0] is not None and f[0] == f[1] == f[2]:
            return "one-finger"
        return self.form.name

    def up_octave(self) -> "Voicing":
        return Voicing(self.form, self.root_pc,
                       tuple(None if f is None else f + 12 for f in self.frets), self.tuning)


def transpositions(form: Form, root_pc: int, tuning: Tuning = STANDARD) -> list[Voicing]:
    """The playable positions of a form for a chord root, lowest first.

    Usually one.  A drop tuning can offer a second, lower one because its dropped
    string reaches below the reference range (the open C5 of Drop C, for instance).
    """
    std_root = (root_pc - tuning.shift) % 12
    base = (std_root - form.root_pc) % 12
    found = []
    for offset in (base - 12, base):
        frets = [None if f is None else f + offset for f in form.frets]
        if frets[0] is not None:
            frets[0] += tuning.low_offset
        played = [f for f in frets if f is not None]
        if min(played) >= 0 and min(played) < 12:
            found.append(Voicing(form, root_pc, tuple(frets), tuning))
    if not found:  # every fret above the 12th: keep the form rather than lose it
        frets = [None if f is None else f + base + (tuning.low_offset if i == 0 else 0)
                 for i, f in enumerate(form.frets)]
        found.append(Voicing(form, root_pc, tuple(frets), tuning))
    return sorted(found, key=lambda v: v.position)


def voicings(root_pc: int, ctype: str, tuning: Tuning = STANDARD) -> list[Voicing]:
    """Every known voicing of a chord, ordered from the nut up the neck."""
    found, seen = [], set()
    for form in FORMS:
        if form.ctype != ctype:
            continue
        for v in transpositions(form, root_pc, tuning):
            if v.frets not in seen:
                seen.add(v.frets)
                found.append(v)
    return sorted(found, key=lambda v: v.position)


def caged_voicings(root_pc: int, minor: bool = False, tuning: Tuning = STANDARD) -> list[Voicing]:
    """The five CAGED shapes for a triad, ordered up the neck."""
    ctype = "min" if minor else "maj"
    found = [transpositions(f, root_pc, tuning)[0] for f in FORMS if f.caged and f.ctype == ctype]
    return sorted(found, key=lambda v: v.position)


def caged_instances(root_pc: int, minor: bool, nfrets: int, tuning: Tuning = STANDARD) -> list[Voicing]:
    """CAGED shapes plus their copies an octave higher, if they fit on the neck."""
    out = []
    for v in caged_voicings(root_pc, minor, tuning):
        out.append(v)
        high = v.up_octave()
        if max(f for _, f in high.played) <= nfrets:
            out.append(high)
    return out


# Where a player wants a chord to sit on the neck: target mean fret.
AREAS = {"Open / low": 0.0, "Frets 3–5": 4.0, "Frets 6–8": 7.0, "Frets 9–12": 10.0}


def pick_voicing(root_pc: int, ctype: str, target: float, tuning: Tuning = STANDARD) -> Voicing:
    cands = voicings(root_pc, ctype, tuning)
    if tuning.drop and ctype == "5":  # the whole point of a drop tuning: one finger, three strings
        cands = [v for v in cands if v.label == "one-finger"] or cands
    cands += [v.up_octave() for v in cands if max(f for _, f in v.played) + 12 <= 15]

    def cost(v: Voicing) -> float:
        frets = [f for _, f in v.played]
        return abs(sum(frets) / len(frets) - target) + 0.25 * (6 - len(frets))

    return min(cands, key=cost)


# --- pentatonic boxes ----------------------------------------------------

def pentatonic_boxes(root_pc: int, kind: str, nfrets: int,
                     tuning: Tuning = STANDARD) -> dict[int, list[tuple]]:
    """The five pentatonic box positions for a key.

    Returns {box_number: [instance, ...]} where an instance is a tuple of
    (string, fret) pairs, two per string.  Boxes are numbered the usual way from
    the minor pentatonic: box 1 starts on the minor-pentatonic root on the lowest
    string.  A major pentatonic uses the same five shapes, numbered from its
    relative minor root (3 semitones down), so both scales share one set of boxes.

    In a drop tuning the shapes are worked out in the reference tuning and the
    lowest string is then re-fretted, so its two notes sit two frets higher.
    """
    minor_root = root_pc if kind == "minor_pent" else (root_pc + 9) % 12
    pcs = {(minor_root + s) % 12 for s in (0, 3, 5, 7, 10)}
    ref = [m + tuning.shift for m in STANDARD_OPEN]
    seq = [m for m in range(16, 120) if m % 12 in pcs]
    base = next(i for i, m in enumerate(seq) if m >= ref[0] and m % 12 == minor_root)
    boxes: dict[int, list[tuple]] = {}
    for n in range(PENT_BOXES):
        instances = []
        for shift in (-5, 0, 5):  # five scale notes = one octave
            k0 = base + n + shift
            if k0 < 0 or k0 + 11 >= len(seq):
                continue
            inst = tuple((s, seq[k0 + 2 * s + t] - ref[s] + (tuning.low_offset if s == 0 else 0))
                         for s in range(6) for t in (0, 1))
            if all(0 <= f <= nfrets for _, f in inst):
                instances.append(inst)
        boxes[n + 1] = instances
    return boxes


def best_box(voicing: Voicing, boxes: dict[int, list[tuple]]):
    """(box_number, instance) of the pentatonic box that overlaps a shape the most."""
    shape = set(voicing.played)
    shape_mid = sum(f for _, f in shape) / len(shape)
    best, best_score = None, None
    for n, instances in boxes.items():
        for inst in instances:
            mid = sum(f for _, f in inst) / len(inst)
            score = (len(shape & set(inst)), -abs(mid - shape_mid))
            if best_score is None or score > best_score:
                best, best_score = (n, inst), score
    return best


def scale_positions(pcs, nfrets: int, tuning: Tuning = STANDARD) -> list[tuple[int, int]]:
    return [(s, f) for s in range(6) for f in range(nfrets + 1) if fret_pc(s, f, tuning) in pcs]
