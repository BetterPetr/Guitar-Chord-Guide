"""Text for the Guide tab as (style, line) pairs.  Styles: h1, h2, p, li."""

GUIDE = [
    ("h1", "Guitar Chord Guide"),
    ("p", "Three ideas organise almost everything a guitarist needs to know about chords and "
          "soloing. This app lets you explore each one and see how they connect."),

    ("h2", "How the three systems fit together"),
    ("li", "•  The circle of fifths tells you which chords belong together in a key, and how keys relate."),
    ("li", "•  The CAGED system tells you where to find any of those chords all over the neck."),
    ("li", "•  The pentatonic scale tells you which five notes are safe to play over them."),
    ("p", "Pick a key in the bar at the top and every tab follows it."),

    ("h2", "The pentatonic scale"),
    ("p", "Five notes per octave. Minor pentatonic is 1  ♭3  4  5  ♭7. Major pentatonic is 1  2  3  5  6. "
          "A major pentatonic contains exactly the same notes as the minor pentatonic whose root is three "
          "semitones (three frets) lower: C major pentatonic and A minor pentatonic are the same five notes, "
          "so every shape you learn works for both."),
    ("p", "On the guitar the scale is played as five box positions that interlock to cover the whole neck. "
          "Each box has two notes on every string. Boxes are numbered from the minor pentatonic: Box 1 starts on "
          "the minor root on the low E string, and Box 2 to Box 5 follow up the neck, repeating after 12 frets. "
          "The major pentatonic uses the same five shapes, numbered from its relative minor root."),
    ("p", "The blue note (♭5 in minor, ♭3 in major) is a passing note that gives the blues its bite. "
          "Use it briefly rather than landing on it. Orange dots are always the root: finish phrases there."),

    ("h2", "The CAGED system"),
    ("p", "There are five open chord shapes named C, A, G, E and D. Any of them can be slid up the neck: "
          "the open strings become a barre at the new fret. That gives five different ways to play the same "
          "chord, and they chain together in the order C → A → G → E → D, then repeat twelve "
          "frets higher. Where the chain starts depends on the key (in G it runs G → E → D → C → A), "
          "and the Fretboard tab always lists the shapes in neck order."),
    ("p", "A major triad (1  3  5) sits entirely inside the major pentatonic, and a minor triad "
          "(1  ♭3  5) sits inside the minor pentatonic. So every CAGED shape lives inside a pentatonic box. "
          "Turn on CAGED shapes in the Fretboard tab and choose one shape: the dashed outline shows the "
          "pentatonic box that overlaps it most. Learn the chord, and you already know where to solo."),
    ("p", "Minor chords use the same five forms with the third lowered. The C-minor and G-minor forms are "
          "less common in practice than the E, A and D forms but are included for completeness."),

    ("h2", "The circle of fifths"),
    ("p", "The twelve major keys arranged in fifths. Going clockwise adds one sharp each step; going "
          "anticlockwise adds one flat. The inner ring holds each key's relative minor, which shares the same "
          "key signature (A minor goes with C major)."),
    ("li", "•  Neighbours: one step anticlockwise is the IV chord, one step clockwise is the V chord. "
           "I, IV and V are the three main major chords of a key."),
    ("li", "•  Beneath them sit their relative minors: ii (under IV), vi (under I) and iii (under V). "
           "Those six segments are the chords of the key; the seventh, vii°, is the diminished chord."),
    ("li", "•  Moving a fifth down (anticlockwise) is the strongest resolution in harmony: V → I, "
           "or ii → V → I."),
    ("li", "•  Transposing a progression just means picking a new tonic; the numerals stay the same."),
    ("p", "The bottom of the circle is both 6 sharps (F♯ major) and 6 flats (G♭ major): one key "
          "with two spellings."),

    ("h2", "Drop tunings"),
    ("p", "In a drop tuning the lowest string is tuned a whole step down, so it sits a fifth below the next "
          "string instead of a fourth. Drop D is D A D G B E. Drop C is C G C F A D: every string a whole step "
          "below Drop D. Drop C♯ sits half a step above Drop C. The three lowest strings now spell root, fifth "
          "and octave, so one finger barred across them is a power chord, and an open low string gives you the "
          "tonic power chord for free. That is why drop tunings suit heavy riffs and pedal-point playing."),
    ("p", "Choose a tuning in the bar at the top. Chord diagrams, voicings, the fretboard and playback all follow it. "
          "The CAGED shapes and pentatonic boxes are the standard-tuning shapes sounding lower, with the dropped "
          "string re-fretted two frets higher. Roots are named by pitch, so a power chord on the open strings of "
          "Drop C is C5. Choose a progression from the Drop tunings group and the app offers to switch to the "
          "tuning it was written for."),

    ("h2", "Using the app"),
    ("li", "•  Circle of Fifths: click a segment to change key. See the key signature, scale, "
           "pentatonic and the chords in the key as chord diagrams. Click a diagram to hear it."),
    ("li", "•  Fretboard: show the pentatonic across the neck, isolate one box, add the blue note, switch "
           "labels between note names and intervals. Turn on CAGED shapes to see a chord's five shapes with "
           "the pentatonic around them. Click the neck to hear a note."),
    ("li", "•  Chord Library: any root, 14 chord types, all the voicings in neck order, plus the keys on the "
           "circle in which that chord is diatonic."),
    ("li", "•  Progressions: classic, alternative/indie and heavy power-chord progressions in any key, with diagrams, playback with a moving "
           "highlight, loop, and a suggestion of which pentatonic to solo with. Type your own with Roman "
           "numerals (upper case major, lower case minor, add 7, maj7 or °; ♭ before the numeral to flatten)."),
    ("li", "•  Chord voicings (top right) decides how high up the neck the diagrams sit."),

    ("h2", "Practice ideas"),
    ("li", "1.  Choose a key and a progression, hit Play with Loop on, and solo with Box 1 of the suggested "
           "pentatonic. Then move to Box 2, and so on up the neck."),
    ("li", "2.  Pick one chord and learn its five CAGED shapes one at a time, always noticing which box "
           "surrounds each."),
    ("li", "3.  Play the same progression in the next key round the circle, using a different voicing area each time."),
    ("li", "4.  Over the 12-bar blues, solo with the minor pentatonic plus the blue note, then try the major "
           "pentatonic over the same chords and listen to the difference."),
    ("p", "Playback is a synthesised plucked string, good for checking pitches and rhythm rather than "
          "replacing a real guitar."),
]
