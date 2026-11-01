"""Music theory core: note spelling, scales, chords, circle of fifths, progressions.

Pure Python with no GUI imports so it can be unit tested headlessly.  Notes are
plain strings such as "F#" or "Bb"; call pretty() to get the display form.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

MAJOR_STEPS = (0, 2, 4, 5, 7, 9, 11)
MINOR_STEPS = (0, 2, 3, 5, 7, 8, 10)

# Circle of fifths, clockwise from the top (index i is i fifths above C).
CIRCLE_MAJOR = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
CIRCLE_MINOR = ["A", "E", "B", "F#", "C#", "G#", "D#", "Bb", "F", "C", "G", "D"]
SHARP_ORDER = ["F#", "C#", "G#", "D#", "A#", "E#", "B#"]
FLAT_ORDER = ["Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Fb"]


def pretty(text: str) -> str:
    """Swap ASCII accidentals for ♯/♭.  Only meant for note, chord and numeral names."""
    return text.replace("#", "♯").replace("b", "♭")


# --- notes ---------------------------------------------------------------

_NOTE_RE = re.compile(r"([A-G])(#*|b*)$")


def _accidentals(acc: str) -> int:
    return len(acc) if acc.startswith("#") else -len(acc)


def note_pc(name: str) -> int:
    m = _NOTE_RE.match(name)
    if not m:
        raise ValueError(f"not a note name: {name!r}")
    return (LETTER_PC[m.group(1)] + _accidentals(m.group(2))) % 12


def shift_note(name: str, delta: int) -> str:
    """Raise or lower a note name by `delta` semitones keeping its letter."""
    letter, acc = _NOTE_RE.match(name).groups()
    n = _accidentals(acc) + delta
    return letter + ("#" * n if n > 0 else "b" * -n)


def pc_name(pc: int, flats: bool = False) -> str:
    return (FLAT_NAMES if flats else SHARP_NAMES)[pc % 12]


def spell(root: str, steps, degrees) -> list[str]:
    """Name the notes `steps` semitones above `root`, one letter per scale degree."""
    letter0, pc0 = LETTERS.index(root[0]), note_pc(root)
    out = []
    for step, degree in zip(steps, degrees):
        letter = LETTERS[(letter0 + degree - 1) % 7]
        diff = (pc0 + step - LETTER_PC[letter]) % 12
        if diff > 6:
            diff -= 12
        out.append(letter + ("#" * diff if diff > 0 else "b" * -diff))
    return out


def interval_label(step: int, degree: int) -> str:
    """'b3', '5', '#5', '9' ... for a note `step` semitones up on scale degree `degree`."""
    major = MAJOR_STEPS[(degree - 1) % 7] + 12 * ((degree - 1) // 7)
    diff = step - major
    return ("#" * diff if diff > 0 else "b" * -diff) + str(degree)


# --- scales --------------------------------------------------------------

@dataclass(frozen=True)
class ScaleType:
    key: str
    name: str
    steps: tuple
    degrees: tuple


SCALES = {s.key: s for s in (
    ScaleType("major", "Major", MAJOR_STEPS, (1, 2, 3, 4, 5, 6, 7)),
    ScaleType("minor", "Natural minor", MINOR_STEPS, (1, 2, 3, 4, 5, 6, 7)),
    ScaleType("major_pent", "Major pentatonic", (0, 2, 4, 7, 9), (1, 2, 3, 5, 6)),
    ScaleType("minor_pent", "Minor pentatonic", (0, 3, 5, 7, 10), (1, 3, 4, 5, 7)),
)}

# The extra "blue note" each pentatonic picks up in blues playing: (step, degree).
BLUE_NOTES = {"major_pent": (3, 3), "minor_pent": (6, 5)}


@dataclass(frozen=True)
class ScaleNote:
    name: str
    pc: int
    label: str  # interval from the tonic: "1", "b3", ...
    step: int


def scale_degrees(tonic: str, scale_key: str, blue: bool = False) -> list[ScaleNote]:
    sc = SCALES[scale_key]
    pairs = list(zip(sc.steps, sc.degrees))
    if blue and scale_key in BLUE_NOTES:
        pairs = sorted(pairs + [BLUE_NOTES[scale_key]])
    names = spell(tonic, [p[0] for p in pairs], [p[1] for p in pairs])
    return [ScaleNote(n, note_pc(n), interval_label(s, d), s) for n, (s, d) in zip(names, pairs)]


def scale_notes(tonic: str, scale_key: str, blue: bool = False) -> list[str]:
    return [n.name for n in scale_degrees(tonic, scale_key, blue)]


# --- chords --------------------------------------------------------------

@dataclass(frozen=True)
class ChordType:
    key: str
    suffix: str
    name: str
    steps: tuple
    degrees: tuple

    @property
    def labels(self) -> tuple:
        return tuple(interval_label(s, d) for s, d in zip(self.steps, self.degrees))


CHORD_TYPES = {c.key: c for c in (
    ChordType("maj", "", "Major", (0, 4, 7), (1, 3, 5)),
    ChordType("min", "m", "Minor", (0, 3, 7), (1, 3, 5)),
    ChordType("7", "7", "Dominant 7th", (0, 4, 7, 10), (1, 3, 5, 7)),
    ChordType("maj7", "maj7", "Major 7th", (0, 4, 7, 11), (1, 3, 5, 7)),
    ChordType("m7", "m7", "Minor 7th", (0, 3, 7, 10), (1, 3, 5, 7)),
    ChordType("sus2", "sus2", "Suspended 2nd", (0, 2, 7), (1, 2, 5)),
    ChordType("sus4", "sus4", "Suspended 4th", (0, 5, 7), (1, 4, 5)),
    ChordType("dim", "dim", "Diminished", (0, 3, 6), (1, 3, 5)),
    ChordType("aug", "aug", "Augmented", (0, 4, 8), (1, 3, 5)),
    ChordType("6", "6", "Major 6th", (0, 4, 7, 9), (1, 3, 5, 6)),
    ChordType("add9", "add9", "Add 9", (0, 4, 7, 14), (1, 3, 5, 9)),
    ChordType("9", "9", "Dominant 9th", (0, 4, 7, 10, 14), (1, 3, 5, 7, 9)),
    ChordType("m7b5", "m7b5", "Half-diminished", (0, 3, 6, 10), (1, 3, 5, 7)),
    ChordType("5", "5", "Power chord", (0, 7), (1, 5)),
)}


@dataclass(frozen=True)
class Chord:
    root: str
    ctype: str
    roman: str = ""

    @property
    def name(self) -> str:
        return self.root + CHORD_TYPES[self.ctype].suffix

    @property
    def pc(self) -> int:
        return note_pc(self.root)

    @property
    def notes(self) -> list[str]:
        ct = CHORD_TYPES[self.ctype]
        return spell(self.root, ct.steps, ct.degrees)

    @property
    def pcs(self) -> frozenset:
        return frozenset((self.pc + s) % 12 for s in CHORD_TYPES[self.ctype].steps)


# --- circle of fifths ----------------------------------------------------

def circle_pc(index: int) -> int:
    """Pitch class of the major key `index` fifths above C."""
    return (index * 7) % 12


def circle_index(pc: int, mode: str) -> int:
    """Position on the circle of a key; a minor key shares its relative major's slot."""
    major_pc = pc if mode == "major" else (pc + 3) % 12
    return (major_pc * 7) % 12  # 7 is its own inverse mod 12


def key_pc(index: int, mode: str) -> int:
    return circle_pc(index) if mode == "major" else (circle_pc(index) + 9) % 12


def key_name(pc: int, mode: str) -> str:
    return (CIRCLE_MAJOR if mode == "major" else CIRCLE_MINOR)[circle_index(pc, mode)]


def key_signature(index: int) -> tuple[int, str]:
    """(count, 'sharp' | 'flat' | '') for the circle position."""
    if index == 0:
        return 0, ""
    return (index, "sharp") if index <= 6 else (12 - index, "flat")


def signature_accidentals(index: int) -> list[str]:
    count, kind = key_signature(index)
    return (SHARP_ORDER if kind == "sharp" else FLAT_ORDER)[:count]


def relative_key(pc: int, mode: str) -> tuple[int, str]:
    return ((pc + 9) % 12, "minor") if mode == "major" else ((pc + 3) % 12, "major")


# Chords of the "key family" around a circle position: (ring, offset) -> numeral.
FAMILY_MAJOR = {("major", 0): "I", ("major", -1): "IV", ("major", 1): "V",
                ("minor", 0): "vi", ("minor", -1): "ii", ("minor", 1): "iii"}
FAMILY_MINOR = {("minor", 0): "i", ("minor", -1): "iv", ("minor", 1): "v",
                ("major", 0): "III", ("major", -1): "VI", ("major", 1): "VII"}


# --- diatonic harmony ----------------------------------------------------

ROMAN_MAJOR = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
ROMAN_MINOR = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
_TRIADS = {"major": ["maj", "min", "min", "maj", "maj", "min", "dim"],
           "minor": ["min", "dim", "maj", "min", "min", "maj", "maj"]}
_SEVENTHS = {"major": ["maj7", "m7", "m7", "maj7", "7", "m7", "m7b5"],
             "minor": ["m7", "m7b5", "maj7", "m7", "m7", "maj7", "7"]}
_SEVENTH_ROMAN = {"maj7": "maj7", "7": "7", "m7": "7", "m7b5": "ø7"}


def diatonic_chords(tonic: str, mode: str, sevenths: bool = False) -> list[Chord]:
    sc = SCALES["major" if mode == "major" else "minor"]
    roots = spell(tonic, sc.steps, sc.degrees)
    romans = ROMAN_MAJOR if mode == "major" else ROMAN_MINOR
    types = (_SEVENTHS if sevenths else _TRIADS)[mode]
    out = []
    for root, roman, ctype in zip(roots, romans, types):
        if sevenths:
            roman = roman.rstrip("°") + _SEVENTH_ROMAN[ctype]
        out.append(Chord(root, ctype, roman))
    return out


def keys_containing(root_pc: int, ctype: str) -> list[tuple[str, str]]:
    """(numeral, 'G major') for every circle key in which this chord is diatonic."""
    sevenths = ctype in ("7", "maj7", "m7", "m7b5")
    found = []
    for mode, names in (("major", CIRCLE_MAJOR), ("minor", CIRCLE_MINOR)):
        for tonic in names:
            for c in diatonic_chords(tonic, mode, sevenths):
                if c.pc == root_pc and c.ctype == ctype:
                    found.append((c.roman, f"{tonic} {mode}"))
    return found


# --- progressions --------------------------------------------------------

_ROMAN_RE = re.compile(r"^([b#]?)(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(.*)$")
_DEGREE = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
_UPPER_SUFFIX = {"": "maj", "7": "7", "maj7": "maj7", "sus2": "sus2", "sus4": "sus4",
                 "6": "6", "add9": "add9", "9": "9", "5": "5"}
_LOWER_SUFFIX = {"": "min", "7": "m7", "°": "dim", "dim": "dim", "ø": "m7b5",
                 "ø7": "m7b5", "m7b5": "m7b5", "5": "5"}


def parse_numeral(token: str) -> tuple[int, int, str]:
    """'bVII' -> (-1, 6, 'maj'); 'ii7' -> (0, 1, 'm7').  Raises ValueError if unreadable."""
    m = _ROMAN_RE.match(token.strip())
    if not m:
        raise ValueError(f"can't read '{token}' as a Roman numeral chord")
    accidental, numeral, suffix = m.groups()
    table = _UPPER_SUFFIX if numeral.isupper() else _LOWER_SUFFIX
    if suffix not in table:
        raise ValueError(f"can't read '{token}': unrecognised ending '{suffix}' "
                         "(try 7, maj7, ° or nothing)")
    delta = {"b": -1, "#": 1, "": 0}[accidental]
    return delta, _DEGREE[numeral.lower()], table[suffix]


def resolve_progression(numerals, tonic: str, mode: str) -> list[Chord]:
    sc = SCALES["major" if mode == "major" else "minor"]
    roots = spell(tonic, sc.steps, sc.degrees)
    chords = []
    for token in numerals:
        delta, degree, ctype = parse_numeral(token)
        chords.append(Chord(shift_note(roots[degree], delta), ctype, token))
    return chords


@dataclass(frozen=True)
class Progression:
    name: str
    mode: str
    numerals: tuple
    description: str
    solo: str       # pentatonic that sits over it: "major_pent" | "minor_pent"
    blue: bool = False
    solo_tip: str = ""
    category: str = "Classic"
    tuning: str = ""  # tuning it is written for ("" = any); see guitar.TUNINGS


CLASSIC, ALTERNATIVE, HEAVY = "Classic", "Alternative / indie", "Heavy / power chords"
DROP = "Drop tunings"

PROGRESSIONS = (
    Progression("Pop four (I–V–vi–IV)", "major", ("I", "V", "vi", "IV"),
                "The most-used progression in modern pop and rock. Works in every key; "
                "the vi gives it a wistful turn before IV resets it.",
                "major_pent", solo_tip="Major pentatonic of the key is the safe choice."),
    Progression("Fifties (I–vi–IV–V)", "major", ("I", "vi", "IV", "V"),
                "Doo-wop and early rock 'n' roll. The V pulls hard back to I.",
                "major_pent"),
    Progression("Three chord (I–IV–V)", "major", ("I", "IV", "V", "I"),
                "The foundation of rock, country and folk: the three major chords "
                "that sit next to each other on the circle of fifths.",
                "major_pent"),
    Progression("Country (I–IV–I–V)", "major", ("I", "IV", "I", "V"),
                "Same three chords, slower harmonic rhythm. Strum it with a boom-chick feel.",
                "major_pent"),
    Progression("Sensitive (vi–IV–I–V)", "major", ("vi", "IV", "I", "V"),
                "The pop four chords starting on the relative minor, so it feels minor "
                "while staying in the major key.",
                "major_pent", solo_tip="The key's major pentatonic is the same five notes as the "
                "relative minor pentatonic (starting on the vi), so either label works."),
    Progression("Canon (I–V–vi–iii–IV–I–IV–V)", "major",
                ("I", "V", "vi", "iii", "IV", "I", "IV", "V"),
                "Pachelbel's descending-bass sequence: a walk once round the circle of "
                "fifths neighbourhood.",
                "major_pent"),
    Progression("Mixolydian rock (I–♭VII–IV–I)", "major",
                ("I", "bVII", "IV", "I"),
                "Borrows the flat seventh chord for that classic-rock swagger.",
                "major_pent", blue=True,
                solo_tip="Major pentatonic with the blue note, or minor pentatonic for grit."),
    Progression("Jazz ii–V–I", "major", ("ii7", "V7", "Imaj7", "Imaj7"),
                "The cadence of jazz harmony: each chord is a fifth below the last, "
                "straight round the circle of fifths.",
                "major_pent", solo_tip="Major pentatonic works over the I; chase chord tones on ii and V."),
    Progression("12-bar blues", "major",
                ("I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"),
                "Every chord is a dominant 7th. Twelve bars, three chords, endless variations.",
                "minor_pent", blue=True,
                solo_tip="Minor pentatonic of the tonic plus the blue note is the blues sound."),
    Progression("Minor rock (i–VII–VI–VII)", "minor",
                ("i", "VII", "VI", "VII"),
                "Driving natural-minor vamp: the three chords just below the tonic.",
                "minor_pent"),
    Progression("Andalusian (i–VII–VI–V)", "minor",
                ("i", "VII", "VI", "V"),
                "Flamenco-flavoured descent. The final V is major, pulling back to i.",
                "minor_pent", blue=True),
    Progression("Epic minor (i–VI–III–VII)", "minor",
                ("i", "VI", "III", "VII"),
                "Big, cinematic minor progression; three major chords around the minor home.",
                "minor_pent"),
    Progression("Minor pop (i–iv–VII–III)", "minor",
                ("i", "iv", "VII", "III"),
                "Moody but warm. The iv is the minor key's subdominant.",
                "minor_pent"),
    Progression("Minor ii°–V–i", "minor", ("ii°", "V7", "i", "i"),
                "The minor-key jazz cadence. V7 borrows the raised 7th from harmonic minor.",
                "minor_pent", blue=True),
    Progression("Minor blues", "minor",
                ("i7", "i7", "i7", "i7", "iv7", "iv7", "i7", "i7", "VI", "V7", "i7", "V7"),
                "The 12-bar form in a minor key.",
                "minor_pent", blue=True,
                solo_tip="Minor pentatonic plus the blue note. Here the pentatonic fits everywhere."),

    # --- alternative / indie -------------------------------------------------
    # Idioms common in alternative rock rather than transcriptions of particular songs.
    Progression("Ringing add9 (Iadd9–V–vi7–IVadd9)", "major", ("Iadd9", "V", "vi7", "IVadd9"),
                "The pop four chords dressed with add9 and minor 7th colours so the open strings "
                "ring on. A staple of indie and alternative guitar.",
                "major_pent", category=ALTERNATIVE,
                solo_tip="The added 9th is already in the major pentatonic, so it fits all the way through."),
    Progression("Sus2 shimmer (Isus2–IV–vi7–Vsus4)", "major", ("Isus2", "IV", "vi7", "Vsus4"),
                "Suspended chords never quite settle, which gives a floating, wide-open sound. "
                "Let the chords ring and pick the top strings.",
                "major_pent", category=ALTERNATIVE),
    Progression("Major III + minor iv (I–III–IV–iv)", "major", ("I", "III", "IV", "iv"),
                "The bittersweet 'Creep' progression: a major chord on the 3rd degree, then the IV "
                "turning minor. Both borrow notes from outside the key.",
                "major_pent", category=ALTERNATIVE,
                solo_tip="The III and iv contain notes outside the key's pentatonic, so aim for "
                         "their chord tones when you land on them."),
    Progression("Borrowed lift (I–♭III–IV–I)", "major", ("I", "bIII", "IV", "I"),
                "The ♭III is borrowed from the parallel minor. It brightens straight into the IV for a "
                "big, anthemic alt-rock lift.",
                "minor_pent", blue=True, category=ALTERNATIVE,
                solo_tip="Minor pentatonic with the blue note matches the borrowed ♭III."),
    Progression("Borrowed climb (I–♭VII–♭VI–♭VII)", "major", ("I", "bVII", "bVI", "bVII"),
                "Borrows ♭VI and ♭VII from the parallel minor for a widescreen, driving feel.",
                "minor_pent", blue=True, category=ALTERNATIVE),
    Progression("Alt-rock lift (i–VI–VII–i)", "minor", ("i", "VI", "VII", "i"),
                "Rise from the minor home through the two major chords above it and fall back. "
                "Works as a verse or a chorus.",
                "minor_pent", category=ALTERNATIVE),
    Progression("Ringing minor (i–VIadd9–IIIadd9–VII)", "minor", ("i", "VIadd9", "IIIadd9", "VII"),
                "Minor key with open, ringing add9 colours: moody but not heavy. Strum it or arpeggiate it.",
                "minor_pent", category=ALTERNATIVE),
    Progression("Rising anthem (i–III–VII–VI)", "minor", ("i", "III", "VII", "VI"),
                "The i–III–VII–VI loop is everywhere in modern rock: dark verse, big chorus.",
                "minor_pent", category=ALTERNATIVE),
    Progression("Minor to major V (i–iv–V–i)", "minor", ("i", "iv", "V", "i"),
                "The V is major, borrowed from harmonic minor, so it pulls much harder back to i "
                "than the natural-minor v would.",
                "minor_pent", blue=True, category=ALTERNATIVE,
                solo_tip="The major V has a note (the raised 7th) that the pentatonic lacks; "
                         "target the chord's root and 3rd there."),
    Progression("Dark cadence (i–VI–iv–V)", "minor", ("i", "VI", "iv", "V"),
                "Falls from the home chord, then builds back up through the iv to the dominant.",
                "minor_pent", category=ALTERNATIVE),

    # --- heavy / power chords ------------------------------------------------
    # Played with power chords (root and fifth, 5 chords) and palm muting.
    Progression("Power-chord riff (i5–VI5–VII5–i5)", "minor", ("i5", "VI5", "VII5", "i5"),
                "The core hard-rock and metal riff shape: root and fifth only, palm-muted on the "
                "low strings.",
                "minor_pent", blue=True, category=HEAVY,
                solo_tip="Minor pentatonic with the blue note is the heavy-rock lead sound."),
    Progression("Heavy anthem (i5–VI5–III5–VII5)", "minor", ("i5", "VI5", "III5", "VII5"),
                "The epic minor loop played as power chords.",
                "minor_pent", blue=True, category=HEAVY),
    Progression("Phrygian riff (i5–♭II5–i5–♭VII5)", "minor", ("i5", "bII5", "i5", "VII5"),
                "The ♭II a semitone above the root gives the dark, menacing Phrygian sound of "
                "thrash and metal.",
                "minor_pent", blue=True, category=HEAVY,
                solo_tip="Minor pentatonic works, and the ♭II is a good note to bend or slide into."),
    Progression("Tritone riff (i5–♭V5–i5–VII5)", "minor", ("i5", "bV5", "i5", "VII5"),
                "The ♭V is a tritone from the root, the 'devil's interval' behind a lot of "
                "doom and heavy metal.",
                "minor_pent", blue=True, category=HEAVY,
                solo_tip="The blue note is the ♭5, the same note as the ♭V chord's root."),
    Progression("Punk power chords (I5–IV5–V5–IV5)", "major", ("I5", "IV5", "V5", "IV5"),
                "Three-chord punk: fast downstrokes on power chords, no thirds to muddy things up.",
                "minor_pent", blue=True, category=HEAVY),
    Progression("Hard rock (I5–♭III5–IV5–♭VII5)", "major", ("I5", "bIII5", "IV5", "bVII5"),
                "Power chords moving through borrowed ♭III and ♭VII for a classic hard-rock riff.",
                "minor_pent", blue=True, category=HEAVY),

    # --- drop tunings ----------------------------------------------------------
    # In a drop tuning the lowest string is a fifth below the next, so the three lowest
    # strings give root-fifth-octave and one finger across them makes a power chord.
    # With the numerals relative to the key, these sit best when the key's tonic is the
    # dropped string (C in Drop C, D in Drop D): the open strings are then the tonic power chord.
    Progression("Pedal chug (i5–i5–VII5–i5)", "minor", ("i5", "i5", "VII5", "i5"),
                "Return to the open tonic power chord between every move. In C minor in Drop C the open "
                "strings are C5 for free, and the VII5 is one finger on the 10th fret. Palm-mute the pedal.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C",
                solo_tip="Minor pentatonic plus the blue note; land on the tonic over the open pedal."),
    Progression("Gallop (i5–i5–VI5–VII5)", "minor", ("i5", "i5", "VI5", "VII5"),
                "Two bars of open tonic, then climb through the VI and VII. Play the pedal as a "
                "galloping eighth-note chug and let the chord changes land on the beat.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C"),
    Progression("Chromatic climb (i5–♭II5–II5–♭III5)", "minor", ("i5", "bII5", "II5", "III5"),
                "One-finger power chord slid up a fret at a time: open, 1st, 2nd, 3rd fret in the "
                "tonic's drop tuning. Easy to play, very heavy.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C",
                solo_tip="Chromatic roots are outside the pentatonic; lean on the blue note and bends."),
    Progression("Power descent (i5–VII5–VI5–V5)", "minor", ("i5", "VII5", "VI5", "V5"),
                "The Andalusian descent as power chords. In C minor that is open, 10th, 8th and 7th "
                "frets: the whole riff is one shape moving down the dropped string.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C"),
    Progression("Blues-rock turnaround (i7–iv7–i7–V7)", "minor", ("i7", "iv7", "i7", "V7"),
                "Seventh chords with the dropped string supplying a low root underneath. Let the "
                "voicings ring and leave space for fills.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C",
                solo_tip="Minor pentatonic with the blue note; the V7 wants its major third as a target."),
    Progression("Clean drop arpeggio (i–VI–III–VII)", "minor", ("i", "VI", "III", "VII"),
                "A clean, ringing minor loop. Arpeggiate the chords and use the dropped string for a "
                "low root under each one.",
                "minor_pent", category=DROP, tuning="Drop C"),
    Progression("Major pedal (I5–♭VII5–IV5–I5)", "major", ("I5", "bVII5", "IV5", "I5"),
                "The tonic power chord on the open strings with the ♭VII and IV above it: a major-key "
                "riff that still uses the dropped string as a pedal.",
                "minor_pent", blue=True, category=DROP, tuning="Drop C",
                solo_tip="Minor pentatonic with the blue note over major-key power chords is the "
                         "classic rock sound."),
    Progression("Drop D chug (I5–IV5–♭VII5–IV5)", "major", ("I5", "IV5", "bVII5", "IV5"),
                "The classic Drop D riff move: open D5, then the IV and ♭VII as one-finger power "
                "chords on the 5th and 10th frets.",
                "minor_pent", blue=True, category=DROP, tuning="Drop D"),
)


def progressions_for(mode: str) -> list[Progression]:
    return [p for p in PROGRESSIONS if p.mode == mode]
