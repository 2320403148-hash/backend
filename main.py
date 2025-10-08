from __future__ import annotations

import argparse
import sys
from typing import Optional, Union

import numpy as np

from flute_tuner import (
	build_scale,
	list_input_devices,
	AudioInput,
	LiveTuner,
	Visualizer,
)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Live Flute Tuning Checker (librosa + sounddevice)",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)
	parser.add_argument("--root", type=str, default="C", help="Root note (e.g., C, C#, Db)")
	parser.add_argument("--scale", type=str, default="major", choices=["major", "minor"], help="Scale type")
	parser.add_argument("--device", type=str, default=None, help="Input device index or substring name")
	parser.add_argument("--list-devices", action="store_true", help="List available input devices and exit")
	parser.add_argument("--sr", type=int, default=44100, help="Sample rate")
	parser.add_argument("--frame", type=int, default=2048, help="Frame length for analysis")
	parser.add_argument("--hop", type=int, default=512, help="Hop length for analysis")
	parser.add_argument("--window-seconds", type=float, default=0.5, help="Seconds of audio for pitch estimate")
	parser.add_argument("--in-tune", type=float, default=5.0, help="Cents within which note is considered in tune")
	parser.add_argument("--slightly", type=float, default=20.0, help="Cents within which note is slightly flat/sharp")
	parser.add_argument("--visualize", action="store_true", help="Enable waveform and spectrogram visualization")
	return parser.parse_args(argv)


def select_device(device_arg: Optional[str]) -> Optional[Union[str, int]]:
	if device_arg is None:
		return None
	# Try to parse as int index
	try:
		return int(device_arg)
	except ValueError:
		# Use as substring; we'll leave it to sounddevice to match by name
		return device_arg


def main(argv: Optional[list[str]] = None) -> int:
	args = parse_args(argv)

	if args.list_devices:
		print("Available input devices:")
		for line in list_input_devices():
			print(" ", line)
		return 0

	allowed_notes = build_scale(args.root, args.scale, octave_range=(3, 7))
	print(f"Using scale: root={args.root} type={args.scale} across octaves 3-7")

	device = select_device(args.device)
	print(f"Opening input device: {device}")

	tuner = LiveTuner(
		allowed_notes=allowed_notes,
		sample_rate=args.sr,
		analysis_window_seconds=args.window_seconds,
		frame_length=args.frame,
		hop_length=args.hop,
		in_tune_cents=args.in_tune,
		slightly_cents=args.slightly,
	)

	visualizer = Visualizer(args.sr, int(args.window_seconds * args.sr)) if args.visualize else None

	try:
		with AudioInput(sample_rate=args.sr, block_size=args.hop, device=device) as stream:
			print("Listening... Press Ctrl+C to stop.")
			while True:
				block = stream.read(timeout=1.0)
				if block is None:
					continue
				result = tuner.push_block(block)
				if result is not None:
					print(
						f"Note {result.note_name}: {result.status} | "
						f"{result.measured_frequency_hz:7.2f} Hz vs {result.reference_frequency_hz:7.2f} Hz | "
						f"{result.cents:+6.1f} cents | conf={result.confidence:.2f}"
					)
				if visualizer is not None:
					# Update plot with latest analysis buffer from tuner
					visualizer.update(tuner._buffer)  # small encapsulation tradeoff for demo
	except KeyboardInterrupt:
		print("\nStopping...")
		return 0
	except Exception as exc:
		print(f"Error: {exc}")
		return 1


if __name__ == "__main__":
	sys.exit(main())