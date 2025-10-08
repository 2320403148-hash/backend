from __future__ import annotations

from typing import Optional

import numpy as np
import matplotlib.pyplot as plt


class Visualizer:
	"""Simple live waveform + spectrogram visualizer.

	Designed for occasional updates using the latest analysis window.
	"""

	def __init__(self, sample_rate: int, window_size: int):
		self.sample_rate = int(sample_rate)
		self.window_size = int(window_size)
		self._initialized = False
		self._waveform_line = None
		self._spec_mesh = None
		self._fig = None
		self._ax_wave = None
		self._ax_spec = None

	def _init_plots(self, y: np.ndarray):
		self._fig, (self._ax_wave, self._ax_spec) = plt.subplots(2, 1, figsize=(8, 6))
		self._fig.suptitle("Live Flute Tuning - Waveform & Spectrogram")

		t = np.arange(y.size) / self.sample_rate
		(self._waveform_line,) = self._ax_wave.plot(t, y, lw=1.0)
		self._ax_wave.set_xlim(0, t[-1] if t.size > 0 else 1.0)
		self._ax_wave.set_ylim(-1.0, 1.0)
		self._ax_wave.set_xlabel("Time (s)")
		self._ax_wave.set_ylabel("Amplitude")

		Pxx, freqs, bins, im = self._ax_spec.specgram(
			y,
			NFFT=1024,
			Fs=self.sample_rate,
			noverlap=256,
			cmap="magma",
		)
		self._spec_mesh = im
		self._ax_spec.set_xlabel("Time (s)")
		self._ax_spec.set_ylabel("Frequency (Hz)")

		plt.tight_layout()
		plt.ion()
		plt.show(block=False)
		self._initialized = True

	def update(self, y: np.ndarray):
		"""Update the plots with the latest window."""
		if not self._initialized:
			self._init_plots(y)

		# Update waveform
		t = np.arange(y.size) / self.sample_rate
		self._waveform_line.set_xdata(t)
		self._waveform_line.set_ydata(y)
		self._ax_wave.set_xlim(0, t[-1] if t.size > 0 else 1.0)

		# Update spectrogram by replotting (simple approach)
		self._ax_spec.cla()
		self._ax_spec.specgram(y, NFFT=1024, Fs=self.sample_rate, noverlap=256, cmap="magma")
		self._ax_spec.set_xlabel("Time (s)")
		self._ax_spec.set_ylabel("Frequency (Hz)")

		self._fig.canvas.draw()
		self._fig.canvas.flush_events()
		plt.pause(0.001)