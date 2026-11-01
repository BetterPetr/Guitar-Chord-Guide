# Guitar Chord Guide

An interactive guitar chord and progression reference built around three ideas:
the **pentatonic scale**, the **CAGED system** and the **circle of fifths**.
Pure Python with the standard library only (tkinter), so there is nothing to install.

## Run it

```bash
python -m guitar_guide
```

or double-click `Guitar-Chord-Guide.pyw`. Needs Python 3.10+ with tkinter (included with the
standard Windows installer).

## What's in it

Pick a key in the bar at the top and every tab follows it.

| Tab | What it does |
| --- | --- |
| **Circle of Fifths** | Clickable wheel of major keys (outer) and relative minors (inner). Shows the key signature, scale, pentatonic and the key's diatonic chords (triads or 7ths) as chord diagrams. The six chords of the key are highlighted with their Roman numerals. |
| **Fretboard** | 17-fret neck. Show the major or minor pentatonic, isolate any of the five boxes, add the blue note, label by note name or interval. Turn on **CAGED shapes** to see the five shapes for any chord in the key, with the pentatonic box that surrounds each shape outlined. |
| **Chord Library** | Any root and 14 chord types (triads, 6ths, 7ths, 9ths, sus, dim, aug, power chords), every voicing in neck order, and the keys on the circle where the chord is diatonic. |
| **Progressions** | 15 classic progressions (pop, 50s, blues, jazz ii-V-I, Andalusian, minor...) resolved into any key, plus your own typed as Roman numerals. Play with a moving highlight, loop, and a suggestion of which pentatonic to solo with. |
| **Guide** | Short written reference for the three systems and practice ideas. |

Click any chord diagram to hear it strummed; click the fretboard to hear a note.
"Chord voicings" (top right) chooses how high up the neck the diagrams sit.
Audio is a synthesised plucked string rendered in pure Python and played with `winsound`,
so sound is Windows-only; everything else works anywhere tkinter does.

## Conventions

- **Pentatonic boxes** are numbered from the minor pentatonic: Box 1 starts on the minor root on the
  low E string. The major pentatonic uses the same five shapes, numbered from its relative minor
  root (so C major pentatonic Box 1 is the A minor Box 1 shape).
- **CAGED shapes** are the open C, A, G, E and D chord forms transposed with a barre. The minor
  versions use the same five forms with a minor third.
- Keys use the circle's spellings (F♯ major, D♯ minor, B♭, E♭, A♭, D♭ ...).
- Roman numerals in major progressions are relative to the major scale; in minor progressions
  they are relative to the natural minor scale (so the VII in A minor is G).

## Layout

```
guitar_guide/
  theory.py      notes, scales, chords, circle of fifths, Roman-numeral progressions (no GUI)
  guitar.py      tuning, chord forms, CAGED shapes, pentatonic boxes (no GUI)
  audio.py       Karplus-Strong synthesis + winsound playback
  widgets.py     fretboard, chord diagram and circle-of-fifths canvases
  app.py         main window and tabs
  guide_text.py  text of the Guide tab
tests/test_core.py
```

## Tests

```bash
python -m unittest discover -s tests
```

The tests check note spelling, the circle, diatonic chords, progression resolution, that every
chord form plays exactly its chord tones in all 12 keys, CAGED ordering, and the pentatonic boxes.
