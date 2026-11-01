import unittest

from guitar_guide import audio, guitar, theory


def names(chords):
    return [c.name for c in chords]


class SpellingTests(unittest.TestCase):
    def test_major_scales(self):
        self.assertEqual(theory.spell("F#", theory.MAJOR_STEPS, range(1, 8)),
                         ["F#", "G#", "A#", "B", "C#", "D#", "E#"])
        self.assertEqual(theory.spell("Bb", theory.MAJOR_STEPS, range(1, 8)),
                         ["Bb", "C", "D", "Eb", "F", "G", "A"])

    def test_pentatonics(self):
        self.assertEqual(theory.scale_notes("A", "minor_pent"), ["A", "C", "D", "E", "G"])
        self.assertEqual(theory.scale_notes("C", "major_pent"), ["C", "D", "E", "G", "A"])
        self.assertEqual(theory.scale_notes("A", "minor_pent", blue=True),
                         ["A", "C", "D", "Eb", "E", "G"])
        self.assertEqual(theory.scale_notes("C#", "minor_pent"), ["C#", "E", "F#", "G#", "B"])

    def test_interval_labels(self):
        labels = [n.label for n in theory.scale_degrees("A", "minor_pent", blue=True)]
        self.assertEqual(labels, ["1", "b3", "4", "b5", "5", "b7"])
        self.assertEqual(theory.CHORD_TYPES["9"].labels, ("1", "3", "5", "b7", "9"))


class CircleTests(unittest.TestCase):
    def test_index_matches_lists(self):
        for i, name in enumerate(theory.CIRCLE_MAJOR):
            self.assertEqual(theory.note_pc(name), theory.circle_pc(i))
            self.assertEqual(theory.circle_index(theory.circle_pc(i), "major"), i)
            self.assertEqual(theory.key_name(theory.circle_pc(i), "major"), name)
        for i, name in enumerate(theory.CIRCLE_MINOR):
            pc = theory.key_pc(i, "minor")
            self.assertEqual(theory.note_pc(name), pc)
            self.assertEqual(theory.circle_index(pc, "minor"), i)
            self.assertEqual(theory.key_name(pc, "minor"), name)

    def test_signatures(self):
        self.assertEqual(theory.key_signature(0), (0, ""))
        self.assertEqual(theory.key_signature(2), (2, "sharp"))
        self.assertEqual(theory.key_signature(9), (3, "flat"))
        self.assertEqual(theory.signature_accidentals(2), ["F#", "C#"])
        self.assertEqual(theory.signature_accidentals(11), ["Bb"])

    def test_signature_matches_scale(self):
        # the sharps/flats in each major scale are exactly the key signature
        for i, tonic in enumerate(theory.CIRCLE_MAJOR):
            accidentals = [n for n in theory.scale_notes(tonic, "major") if len(n) > 1]
            if i != 6:
                self.assertEqual(sorted(accidentals), sorted(theory.signature_accidentals(i)))

    def test_relative(self):
        self.assertEqual(theory.relative_key(0, "major"), (9, "minor"))
        self.assertEqual(theory.relative_key(9, "minor"), (0, "major"))


class HarmonyTests(unittest.TestCase):
    def test_diatonic_triads(self):
        self.assertEqual(names(theory.diatonic_chords("C", "major")),
                         ["C", "Dm", "Em", "F", "G", "Am", "Bdim"])
        self.assertEqual(names(theory.diatonic_chords("A", "minor")),
                         ["Am", "Bdim", "C", "Dm", "Em", "F", "G"])

    def test_diatonic_sevenths(self):
        self.assertEqual(names(theory.diatonic_chords("G", "major", True)),
                         ["Gmaj7", "Am7", "Bm7", "Cmaj7", "D7", "Em7", "F#m7b5"])

    def test_progressions(self):
        def resolve(numerals, tonic, mode="major"):
            return names(theory.resolve_progression(numerals, tonic, mode))
        self.assertEqual(resolve(["I", "V", "vi", "IV"], "G"), ["G", "D", "Em", "C"])
        self.assertEqual(resolve(["ii7", "V7", "Imaj7"], "C"), ["Dm7", "G7", "Cmaj7"])
        self.assertEqual(resolve(["I", "bVII", "IV"], "D"), ["D", "C", "G"])
        self.assertEqual(resolve(["i", "VII", "VI", "V"], "A", "minor"), ["Am", "G", "F", "E"])
        self.assertEqual(resolve(["ii°", "V7", "i"], "A", "minor"), ["Bdim", "E7", "Am"])

    def test_blues_in_a(self):
        blues = next(p for p in theory.PROGRESSIONS if p.name == "12-bar blues")
        self.assertEqual(names(theory.resolve_progression(blues.numerals, "A", "major")),
                         ["A7"] * 4 + ["D7"] * 2 + ["A7"] * 2 + ["E7", "D7", "A7", "E7"])

    def test_every_progression_resolves_in_every_key(self):
        for p in theory.PROGRESSIONS:
            tonics = theory.CIRCLE_MAJOR if p.mode == "major" else theory.CIRCLE_MINOR
            for tonic in tonics:
                self.assertEqual(len(theory.resolve_progression(p.numerals, tonic, p.mode)),
                                 len(p.numerals))

    def test_bad_numeral(self):
        with self.assertRaises(ValueError):
            theory.parse_numeral("IX")
        with self.assertRaises(ValueError):
            theory.parse_numeral("Vfoo")

    def test_keys_containing(self):
        found = dict((k, r) for r, k in theory.keys_containing(7, "maj"))
        self.assertEqual(found["G major"], "I")
        self.assertEqual(found["D major"], "IV")
        self.assertEqual(found["C major"], "V")
        self.assertEqual(found["A minor"], "VII")


class FormTests(unittest.TestCase):
    def test_every_form_plays_exactly_its_chord_tones(self):
        for form in guitar.FORMS:
            for root_pc in range(12):
                v = guitar.transpose(form, root_pc)
                played = {guitar.fret_pc(s, f) for s, f in v.played}
                steps = theory.CHORD_TYPES[form.ctype].steps
                expected = {(root_pc + s) % 12 for s in steps}
                fifth = {(root_pc + 7) % 12}
                # guitar voicings may legitimately drop the 5th (e.g. the classic C7), nothing else
                self.assertTrue(played == expected or (len(steps) > 3 and played == expected - fifth),
                                f"{form.name} {form.ctype} root {root_pc}: {played} vs {expected}")
                self.assertTrue(all(0 <= f <= 15 for _, f in v.played), (form, root_pc, v.frets))

    def test_form_root_is_actually_in_form(self):
        for form in guitar.FORMS:
            played = {guitar.fret_pc(s, f) for s, f in enumerate(form.frets) if f is not None}
            self.assertIn(form.root_pc, played)

    def test_every_chord_type_has_forms(self):
        for key in theory.CHORD_TYPES:
            self.assertTrue(guitar.voicings(0, key), key)

    def test_caged_in_c(self):
        shapes = guitar.caged_voicings(0)
        self.assertEqual([v.form.caged for v in shapes], list("CAGED"))
        self.assertEqual(shapes[0].frets, (None, 3, 2, 0, 1, 0))
        self.assertEqual(shapes[3].frets, (8, 10, 10, 9, 8, 8))

    def test_caged_order_rotates_with_key(self):
        order = [v.form.caged for v in guitar.caged_voicings(7)]  # G
        self.assertEqual(order, list("GEDCA"))

    def test_pick_voicing_prefers_open(self):
        self.assertEqual(guitar.pick_voicing(0, "maj", 0.0).frets, (None, 3, 2, 0, 1, 0))
        self.assertEqual(guitar.pick_voicing(5, "maj", 0.0).position, 1)  # F barre


class PentatonicBoxTests(unittest.TestCase):
    def test_a_minor_box_one(self):
        boxes = guitar.pentatonic_boxes(9, "minor_pent", 17)
        self.assertEqual(len(boxes), 5)
        box1 = [inst for inst in boxes[1] if min(f for _, f in inst) >= 5][0]
        expected = ((0, 5), (0, 8), (1, 5), (1, 7), (2, 5), (2, 7),
                    (3, 5), (3, 7), (4, 5), (4, 8), (5, 5), (5, 8))
        self.assertEqual(box1, expected)

    def test_a_minor_box_two_and_five(self):
        boxes = guitar.pentatonic_boxes(9, "minor_pent", 17)
        self.assertEqual(boxes[2][0][:2], ((0, 8), (0, 10)))
        low_box5 = min(boxes[5], key=lambda inst: inst[0][1])
        self.assertEqual(low_box5[:2], ((0, 3), (0, 5)))

    def test_boxes_use_only_scale_notes_two_per_string(self):
        for root in range(12):
            for kind in ("minor_pent", "major_pent"):
                pcs = {(root + s) % 12 for s in
                       (theory.SCALES[kind].steps)}
                boxes = guitar.pentatonic_boxes(root, kind, 17)
                self.assertTrue(all(boxes[n] for n in range(1, 6)), (root, kind))
                for insts in boxes.values():
                    for inst in insts:
                        self.assertEqual(len(inst), 12)
                        self.assertTrue(all(guitar.fret_pc(s, f) in pcs for s, f in inst))
                        for s in range(6):
                            self.assertEqual(sum(1 for t, _ in inst if t == s), 2)

    def test_major_boxes_share_shapes_with_relative_minor(self):
        self.assertEqual(guitar.pentatonic_boxes(0, "major_pent", 17),
                         guitar.pentatonic_boxes(9, "minor_pent", 17))

    def test_best_box_for_shape_overlaps(self):
        boxes = guitar.pentatonic_boxes(0, "major_pent", 17)
        for v in guitar.caged_instances(0, False, 17):
            n, inst = guitar.best_box(v, boxes)
            self.assertGreaterEqual(len(set(v.played) & set(inst)), 4)


class AudioTests(unittest.TestCase):
    def test_strum_renders_wav(self):
        import wave
        player = audio.Player()
        path = player.render_strum([40, 47, 52, 56, 59, 64])
        with wave.open(path) as w:
            self.assertEqual(w.getframerate(), audio.SAMPLE_RATE)
            self.assertGreater(w.getnframes(), audio.SAMPLE_RATE)

    def test_progression_length(self):
        import wave
        player = audio.Player()
        path = player.render_progression([[40, 47, 52], [45, 52, 57]], bpm=120, beats=4)
        with wave.open(path) as w:
            seconds = w.getnframes() / w.getframerate()
        self.assertAlmostEqual(seconds, 2 * 2.0 + 0.6, delta=0.05)


if __name__ == "__main__":
    unittest.main()
