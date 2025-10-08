from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Set, Tuple

import numpy as np

from .music_theory import (
	frequency_to_note_name,
	midi_to_frequency,
	parse_note_name_to_midi,
	cents_difference,
)
from .pitch_detection import estimate_pitch_from_window


@dataclass
class TuningResult:
	"""Aggregate result for a detected note event."""
	note_name: str
	measured_frequency_hz: float
	reference_frequency_hz: float
	cents: float
	status: str  # In Tune, Slightly Flat, Slightly Sharp, Off, Non-scale note
	confidence: float


class LiveTuner:
	"""Coordinating class for live tuning analysis."""

	def __init__(
		self,
		allowed_notes: Set[str],
		sample_rate: int = 44100,
		analysis_window_seconds: float = 0.5,
		frame_length: int = 2048,
		hop_length: int = 512,
		fmin_note: str = "C3",
		fmax_note: str = "C7",
		in_tune_cents: float = 5.0,
		slightly_cents: float = 20.0,
	):
		self.allowed_notes = allowed_notes
		self.sample_rate = int(sample_rate)
		self.analysis_window_samples = int(analysis_window_seconds * self.sample_rate)
		self.frame_length = int(frame_length)
		self.hop_length = int(hop_length)
		self.fmin_hz = float(midi_to_frequency(parse_note_name_to_midi(fmin_note)))
		self.fmax_hz = float(midi_to_frequency(parse_note_name_to_midi(fmax_note)))
		self.in_tune_cents = float(in_tune_cents)
		self.slightly_cents = float(slightly_cents)

		self._buffer = np.zeros(self.analysis_window_samples, dtype=np.float32)
		self._buffer_filled = 0

	def push_block(self, block: np.ndarray) -> Optional[TuningResult]:
		"""Push a new block of audio and analyze if enough samples accumulated."""
		if block is None or block.size == 0:
			return None
		if block.ndim != 1:
			raise ValueError("Expected mono block")

		# Roll buffer and append new block
		incoming = block.astype(np.float32)
		if incoming.size >= self._buffer.size:
			self._buffer[:] = incoming[-self._buffer.size :]
			self._buffer_filled = self._buffer.size
		else:
			shift = self._buffer.size - incoming.size
			self._buffer[:shift] = self._buffer[incoming.size :]
			self._buffer[shift:] = incoming
			self._buffer_filled = min(self._buffer.size, self._buffer_filled + incoming.size)

		if self._buffer_filled < self._buffer.size:
			return None

		estimate = estimate_pitch_from_window(
			signal_window=self._buffer,
			sample_rate=self.sample_rate,
			fmin_hz=self.fmin_hz,
			fmax_hz=self.fmax_hz,
			frame_length=self.frame_length,
			hop_length=self.hop_length,
		)
		if estimate is None:
			return None
		f0_hz, confidence = estimate
		if not np.isfinite(f0_hz) or f0_hz <= 0:
			return None

		note_name = frequency_to_note_name(f0_hz, prefer_sharps=True)
		midi_num = parse_note_name_to_midi(note_name)
		reference_hz = float(midi_to_frequency(midi_num))
		cents = float(cents_difference(f0_hz, reference_hz))

		# Determine status
		status = self._status_from_cents(cents)
		if note_name not in self.allowed_notes:
			status = "Non-scale note"

		return TuningResult(
			note_name=note_name,
			measured_frequency_hz=float(f0_hz),
			reference_frequency_hz=reference_hz,
			cents=cents,
			status=status,
			confidence=float(confidence),
		)

	def _status_from_cents(self, cents: float) -> str:
		abs_cents = abs(cents)
		if abs_cents <= self.in_tune_cents:
			return "In Tune"
		if abs_cents <= self.slightly_cents:
			return "Slightly Sharp" if cents > 0 else "Slightly Flat"
		return "Off"