from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple, Set

# --- Frequency/Note conversion utilities ---

A4_FREQUENCY_HZ: float = 440.0
A4_MIDI: int = 69
SEMITONES_PER_OCTAVE: int = 12

NOTE_NAMES_SHARP: List[str] = [
	"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]
NOTE_NAMES_FLAT: List[str] = [
	"C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
]

ENHARMONIC_EQUIV: Dict[str, str] = {
	"Db": "C#",
	"Eb": "D#",
	"Gb": "F#",
	"Ab": "G#",
	"Bb": "A#",
}


def midi_to_frequency(midi: int, a4_hz: float = A4_FREQUENCY_HZ) -> float:
	"""Convert MIDI note number to frequency in Hz using 12-TET."""
	return float(a4_hz) * (2.0 ** ((midi - A4_MIDI) / SEMITONES_PER_OCTAVE))


def frequency_to_midi(frequency_hz: float, a4_hz: float = A4_FREQUENCY_HZ) -> float:
	"""Convert frequency to fractional MIDI note number (can include cents)."""
	if frequency_hz <= 0:
		raise ValueError("Frequency must be positive")
	return A4_MIDI + SEMITONES_PER_OCTAVE * math.log2(frequency_hz / a4_hz)


def midi_to_note_name(midi: int, prefer_sharps: bool = True) -> str:
	"""Convert MIDI to note name like 'A4'."""
	note_names = NOTE_NAMES_SHARP if prefer_sharps else NOTE_NAMES_FLAT
	pitch_class = midi % 12
	octave = midi // 12 - 1
	return f"{note_names[pitch_class]}{octave}"


def normalize_note_name(note: str) -> str:
	"""Normalize note name to sharp representation (e.g., Db -> C#)."""
	note = note.strip().upper()
	# Rebuild with case: letter uppercase, accidental as given
	# Handle flats: map to sharps
	if len(note) >= 2 and note[1] in {'B', 'b'}:
		candidate = note[0].upper() + 'b' + note[2:]
		return ENHARMONIC_EQUIV.get(candidate.replace('b', 'b').title().replace('B', 'b'), note)
	# Simple mapping via dict using title-case keys
	flat_title_map = {k: v for k, v in ENHARMONIC_EQUIV.items()}
	key = note[0].upper() + (note[1:].replace('♭', 'b').replace('♯', '#'))
	key_t = key.replace('b', 'b').replace('#', '#')
	key_t = key_t[0].upper() + key_t[1:]
	return flat_title_map.get(key_t, key_t)


def parse_note_name_to_midi(note_name: str) -> int:
	"""Parse a note like 'C#4' or 'Db5' into MIDI number."""
	if not note_name:
		raise ValueError("Empty note name")
	name = note_name.strip()
	# Extract pitch and octave
	pitch_part = ''.join([c for c in name if c.isalpha() or c in ['#', 'b', '♭', '♯']])
	octave_part = ''.join([c for c in name if c.isdigit() or c == '-'])
	if octave_part == '':
		raise ValueError(f"No octave in note name: {note_name}")
	octave = int(octave_part)
	pitch_norm = normalize_note_name(pitch_part)
	if pitch_norm not in NOTE_NAMES_SHARP:
		raise ValueError(f"Unknown pitch class: {pitch_part}")
	pitch_class = NOTE_NAMES_SHARP.index(pitch_norm)
	return (octave + 1) * 12 + pitch_class


def frequency_to_note_name(frequency_hz: float, prefer_sharps: bool = True) -> str:
	"""Map a frequency to the nearest tempered note name."""
	midi_fractional = frequency_to_midi(frequency_hz)
	midi_nearest = int(round(midi_fractional))
	return midi_to_note_name(midi_nearest, prefer_sharps=prefer_sharps)


def cents_difference(measured_hz: float, reference_hz: float) -> float:
	"""Return cents difference (positive if measured is sharp)."""
	if measured_hz <= 0 or reference_hz <= 0:
		raise ValueError("Frequencies must be positive")
	return 1200.0 * math.log2(measured_hz / reference_hz)


# --- Scales ---

MAJOR_INTERVALS: List[int] = [2, 2, 1, 2, 2, 2, 1]  # Ionian
MINOR_INTERVALS: List[int] = [2, 1, 2, 2, 1, 2, 2]  # Natural minor (Aeolian)


def build_scale(root_note: str, scale_type: str, octave_range: Tuple[int, int] = (4, 6)) -> Set[str]:
	"""Build set of note names (without octaves) or with octaves across given range.

	We return full note names with octaves across the range for precise matching.
	"""
	root = normalize_note_name(root_note)
	if root not in NOTE_NAMES_SHARP:
		raise ValueError(f"Invalid root note: {root_note}")
	intervals = MAJOR_INTERVALS if scale_type.lower() in {"major", "ionian"} else MINOR_INTERVALS
	pitch_class = NOTE_NAMES_SHARP.index(root)

	# Construct scale pitch classes
	scale_pcs = [pitch_class]
	for step in intervals[:-1]:  # 7-note diatonic scale
		pitch_class = (pitch_class + step) % 12
		scale_pcs.append(pitch_class)

	allowed: Set[str] = set()
	low_oct, high_oct = octave_range
	for octave in range(low_oct, high_oct + 1):
		for pc in scale_pcs:
			name = NOTE_NAMES_SHARP[pc] + str(octave)
			allowed.add(name)
	return allowed


# --- Example flute frequency table (A4=440 Hz) ---
# These can be extended as needed.
FLUTE_FREQ_TABLE: Dict[str, float] = {
	"C4": 261.63,
	"C#4": 277.18,
	"D4": 293.66,
	"D#4": 311.13,
	"E4": 329.63,
	"F4": 349.23,
	"F#4": 369.99,
	"G4": 392.00,
	"G#4": 415.30,
	"A4": 440.00,
	"A#4": 466.16,
	"B4": 493.88,
	"C5": 523.25,
	"D5": 587.33,
	"E5": 659.25,
	"F5": 698.46,
	"G5": 783.99,
	"A5": 880.00,
	"B5": 987.77,
}