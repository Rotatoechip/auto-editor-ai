# System Architecture & AI Agent Instructions

## Project Overview
This project is an applied AI engineering pipeline that automates video editing. The tool analyzes video/audio files and generates a non-destructive Final Cut Pro XML (FCPXML v1.9) file for import into CapCut.

## Core Rules for the AI Agent
1. **No Placeholders:** Never write comments like `# logic goes here`. Implement the full, functional code.
2. **Type Hinting:** Strictly use Python 3.10+ type hinting for all functions.
3. **Modular Design:** Separate the logic into distinct modules (e.g., `audio_processing`, `xml_generation`, `cli_interface`) rather than a single monolithic script.
4. **FCPXML Strictness:** When generating FCPXML, ensure strictly valid XML syntax. Missing closing tags will cause CapCut import failures. Use Python's `xml.etree.ElementTree` or specialized XML builders rather than raw string concatenation.
5. **FCPXML Version:** FCPXML generation must strictly adhere to the v1.9 schema. Use xml.etree.ElementTree to build the tree; never use raw string concatenation.
6. **language** The tool handles Mandarin Chinese (zh). All string encoding must be UTF-8.

## Phase 1 Target: Volume-Based Editing (RMS)
- Parse `--threshold` and `--margin` from the CLI.
- Use `subprocess` and `ffmpeg` to extract a mono WAV file.
- Use `numpy` and `scipy` for RMS volume analysis in 1/30s chunks.
- Output an FCPXML referencing the original video file and mapping the non-silent tuple segments to the primary sequence track.

## Phase 2 Target: NLP-Based Editing (Whisper Integration)
- Prepare the architecture to accept JSON transcript data (timestamps + words) instead of raw RMS tuples.
- Implement text-filtering rules to identify and drop timestamps associated with filler words, repetitions, and pauses.