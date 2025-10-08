# Live Flute Tuning Checker (Python)

A simple, modular Python project to check flute tuning live from a microphone. It detects pitch in real time, maps to the nearest musical note, compares with a selected scale, and reports whether notes are In Tune, Slightly Flat, or Slightly Sharp. Optional live waveform and spectrogram visualization.

## Features
- Select a musical scale (e.g., C major, D minor)
- Live microphone input using `sounddevice`
- Pitch detection with `librosa` (YIN) and FFT utilities
- Frequency-to-note mapping and cents deviation
- Scale matching and clear console output
- Optional waveform and spectrogram visualization with `matplotlib`

## Requirements
- Python 3.9+
- PortAudio backend (for `sounddevice`)

Install system dependencies (Linux):
```bash
sudo apt update
sudo apt install -y libportaudio2 python3-dev
```

## Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If `sounddevice` causes issues, try installing PortAudio dev headers:
```bash
sudo apt install -y portaudio19-dev
```

## Run
List audio devices:
```bash
python main.py --list-devices
```

Run tuner (C major by default):
```bash
python main.py --root C --scale major
```

Choose device and enable visualization:
```bash
python main.py --root D --scale minor --device 2 --visualize
```

Key options:
- `--root`: Root note (e.g., C, C#, Db, D, ...)
- `--scale`: `major` or `minor`
- `--device`: Sounddevice input index or name substring
- `--sr`: Sample rate (default 44100)
- `--frame`: Frame length for analysis (default 2048)
- `--hop`: Hop length for analysis (default 512)
- `--window-seconds`: Seconds of audio used for pitch estimation (default 0.5)
- `--visualize`: Show waveform and spectrogram updates

Stop with Ctrl+C.

## Example Flute Frequencies
This project includes an example frequency table for common flute notes (A4=440 Hz reference):
- C4 ≈ 261.63 Hz
- D4 ≈ 293.66 Hz
- E4 ≈ 329.63 Hz
- F4 ≈ 349.23 Hz
- G4 ≈ 392.00 Hz
- A4 = 440.00 Hz
- B4 ≈ 493.88 Hz
- C5 ≈ 523.25 Hz

The tuner uses 12-TET by default and compares cents deviation from the nearest tempered note, while also cross-checking against your selected scale.

## Notes
- Real-time performance depends on your hardware, buffer sizes, and Python environment.
- For very short frames or noisy environments, detection may be unstable; the tuner applies simple median smoothing.
- You can extend `flute_tuner/music_theory.py` to add more scales or custom temperament.