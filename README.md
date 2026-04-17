# AI Auto-Editor for JianYing Pro 🎬
An automated, zero-touch video editing pipeline that precisely purges awkward pauses, filler words, and semantic slips directly into a native JianYing Pro (CapCut Chinese) timeline draft.

## Core Architecture
- **OpenAI Cloud Acceleration**: Uses lightning-fast OpenAI `whisper-1` inference bypassing local CPU limitations, safely slicing media dynamically to preserve strict 25 MB payload ceilings.
- **Smart Stutter Eradication**: Generatively leverages Google `gemini-2.5-flash` to extract human semantic mistakes, conversational false-starts, and tongue slips natively.
- **Clamped Padding Integrations**: Advanced margin math boundaries explicitly trap `.6s` user margin padding so it physically cannot overlap onto resurrected "zombie" filler word segments.
- **Micro-Pop Crossfades**: Built to natively bridge timeline jump-fades via 0.05s JianYing audio crossfade injections to eliminate waveform pop audio clicking.
- **Native JSON Hooking**: Eliminates fragile FCPXML compatibility logic securely dropping media logic directly into macOS JianYing Pro Local Draft architecture (`com.lveditor.draft`).

## Dependencies
Ensure you have the core sub-routine dependency installed actively via brew for audio extraction chunks handling natively via `pydub`:
```bash
brew install ffmpeg
```

Authenticate your local terminal layers to talk freely with the backend cloud providers:
```bash
export OPENAI_API_KEY="sk-proj-your-openai-secret"
export GEMINI_API_KEY="AIzaSy-your-gemini-secret" 
```

## Local Setup
Ensure you operate cleanly out of the active Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## System Usage
Execute the automated wrapper straight off your master media MP4 file location natively!
```bash
python auto_edit.py /path/to/video.mp4
```

### Core Advanced Adjustments
Command-line tweaking configurations directly target NLP segmentation:
- `--pause_threshold`: Minimum safe gap necessary to legally trigger an AI sequence cut (default: `1.8s`).
- `--margin`: The raw exact duration of "safety" buffer space intentionally left untouched wrapping retained sentence words (default: `0.4s`).

Example:
```bash
python auto_edit.py /path/to/video.mp4 --pause_threshold 2.0 --margin 0.6
```
