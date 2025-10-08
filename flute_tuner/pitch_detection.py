from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import librosa


def estimate_pitch_from_window(
	signal_window: np.ndarray,
	sample_rate: int,
	fmin_hz: float,
	fmax_hz: float,
	frame_length: int = 2048,
	hop_length: int = 512,
) -> Optional[Tuple[float, float]]:
	"""Estimate fundamental frequency from a window using librosa's YIN.

	Returns (f0_hz, confidence) or None if no reliable pitch is found.
	"""
	if signal_window.size < frame_length:
		return None
	# librosa expects float32 in range [-1, 1]
	y = signal_window.astype(np.float32)

	try:
		f0 = librosa.yin(
			y=y,
			sr=sample_rate,
			fmin=fmin_hz,
			fmax=fmax_hz,
			frame_length=frame_length,
			hop_length=hop_length,
			center=False,
		)
		# Confidence can be approximated by voicing probability using librosa.pyin if needed
		# Here we compute a simple stability metric using IQR of detected f0s
		valid = np.isfinite(f0)
		f0_valid = f0[valid]
		if f0_valid.size == 0:
			return None
		median_f0 = float(np.median(f0_valid))
		spread = float(np.subtract(*np.percentile(f0_valid, [75, 25])))
		confidence = float(np.clip(1.0 - (spread / max(median_f0, 1e-6)), 0.0, 1.0))
		return median_f0, confidence
	except Exception:
		# In real-time, robustness is more important than raising
		return None