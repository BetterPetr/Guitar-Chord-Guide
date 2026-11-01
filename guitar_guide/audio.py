"""Plucked-string synthesis (Karplus-Strong) with playback through winsound.

Pure Python, so it needs no extra packages; playback is Windows-only.  Every
render happens off the GUI thread.
"""
from __future__ import annotations

import atexit
import itertools
import random
import shutil
import tempfile
import threading
import wave
from array import array
from pathlib import Path

from .guitar import midi_freq

try:
    import winsound
except ImportError:  # not Windows
    winsound = None

SAMPLE_RATE = 22050
NOTE_SECONDS = 2.2
STRUM_DELAY = 0.028  # seconds between strings in a strum


class Player:
    def __init__(self) -> None:
        self.available = winsound is not None
        self._notes: dict[int, list[float]] = {}
        self._dir: Path | None = None
        self._files = itertools.count()
        self._lock = threading.Lock()

    # -- synthesis --

    def _pluck(self, midi: int) -> list[float]:
        if midi in self._notes:
            return self._notes[midi]
        n = max(2, round(SAMPLE_RATE / midi_freq(midi)))
        rng = random.Random(midi)
        noise = [rng.uniform(-1, 1) for _ in range(n)]
        buf = [(noise[i] + noise[i - 1]) * 0.5 for i in range(n)]  # soften the attack
        total = int(SAMPLE_RATE * NOTE_SECONDS)
        out = [0.0] * total
        idx = 0
        for k in range(total):
            nxt = idx + 1 if idx + 1 < n else 0
            v = buf[idx]
            out[k] = v
            buf[idx] = 0.997 * 0.5 * (v + buf[nxt])
            idx = nxt
        self._notes[midi] = out
        return out

    def _mix(self, events, length: float) -> list[float]:
        """events: (start_seconds, midi, gain, ring_seconds)."""
        out = [0.0] * (int(length * SAMPLE_RATE) + 1)
        for start_s, midi, gain, ring in events:
            note = self._pluck(midi)
            start = int(start_s * SAMPLE_RATE)
            n = min(len(note), int(ring * SAMPLE_RATE), len(out) - start)
            if n <= 0:
                continue
            seg = [v * gain for v in note[:n]]
            fade = min(n, int(0.08 * SAMPLE_RATE))
            for k in range(fade):
                seg[n - fade + k] *= 1 - k / fade
            out[start:start + n] = [a + b for a, b in zip(out[start:start + n], seg)]
        return out

    def _write(self, samples: list[float]) -> str:
        peak = max(max(samples), -min(samples), 1e-9)
        scale = 0.85 * 32767 / peak
        data = array("h", (int(v * scale) for v in samples))
        if self._dir is None:
            self._dir = Path(tempfile.mkdtemp(prefix="guitar_guide_"))
            atexit.register(shutil.rmtree, self._dir, True)
        path = self._dir / f"play{next(self._files) % 8}.wav"
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(data.tobytes())
        return str(path)

    def _strum_events(self, midis, start: float, ring: float, gain: float, down: bool = True):
        order = sorted(midis) if down else sorted(midis, reverse=True)
        return [(start + i * STRUM_DELAY, m, gain, ring) for i, m in enumerate(order)]

    # -- rendering to a wav file (call from a worker thread) --

    def render_strum(self, midis) -> str:
        return self._write(self._mix(self._strum_events(midis, 0.0, 1.8, 0.6), 2.0))

    def render_progression(self, chords_midis, bpm: float, beats: int) -> str:
        """One strum on beat 1 and, for 4+ beats, a lighter one at the half way point."""
        beat = 60.0 / bpm
        dur = beats * beat
        events = []
        for i, midis in enumerate(chords_midis):
            t = i * dur
            events += self._strum_events(midis, t, dur + 0.3, 0.6)
            if beats >= 4:
                events += self._strum_events(midis, t + dur / 2, dur / 2 + 0.3, 0.4, down=False)
        return self._write(self._mix(events, len(chords_midis) * dur + 0.6))

    # -- playback --

    def play_file(self, path: str) -> None:
        if self.available:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def stop(self) -> None:
        if self.available:
            winsound.PlaySound(None, winsound.SND_PURGE)

    def strum(self, midis) -> None:
        """Fire and forget: render in the background, then play."""
        if not self.available or not midis:
            return

        def work() -> None:
            with self._lock:
                self.play_file(self.render_strum(midis))

        threading.Thread(target=work, daemon=True).start()
