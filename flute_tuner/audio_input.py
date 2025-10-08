from __future__ import annotations

import queue
from typing import Optional, Union, List

import numpy as np
import sounddevice as sd


class AudioInput:
	"""Simple wrapper around sounddevice.InputStream to capture mono audio blocks.

	The stream callback enqueues incoming blocks into a Queue so callers can
	pull data without blocking the audio thread.
	"""

	def __init__(
		self,
		sample_rate: int = 44100,
		block_size: int = 2048,
		device: Optional[Union[int, str]] = None,
	):
		self.sample_rate = int(sample_rate)
		self.block_size = int(block_size)
		self.device = device
		self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=16)
		self._stream: Optional[sd.InputStream] = None

	def _callback(self, indata, frames, time, status):  # noqa: D401 - sd signature
		if status:
			print(f"[sounddevice] Status: {status}")
		# Convert to mono float32 numpy array
		mono = np.mean(indata, axis=1).astype(np.float32)
		try:
			self._queue.put_nowait(mono)
		except queue.Full:
			# Drop if consumer is slow; real-time safety
			pass

	def __enter__(self):
		self._stream = sd.InputStream(
			samplerate=self.sample_rate,
			blocksize=self.block_size,
			channels=1,
			callback=self._callback,
			device=self.device,
			dtype="float32",
		)
		self._stream.start()
		return self

	def __exit__(self, exc_type, exc, tb):
		if self._stream is not None:
			self._stream.stop()
			self._stream.close()
			self._stream = None

	def read(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
		"""Return the next audio block, or None on timeout."""
		try:
			return self._queue.get(timeout=timeout)
		except queue.Empty:
			return None


def list_input_devices() -> List[str]:
	"""Return a list of human-readable device strings with indexes."""
	devices = sd.query_devices()
	result = []
	for idx, dev in enumerate(devices):
		if dev.get("max_input_channels", 0) > 0:
			name = dev.get("name", f"Device {idx}")
			rate = int(dev.get("default_samplerate", 0))
			result.append(f"[{idx}] {name} (default_sr={rate})")
	return result