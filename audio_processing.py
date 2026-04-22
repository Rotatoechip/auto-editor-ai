import subprocess
import os


def extract_mono_audio(
        input_file: str,
        output_file: str = "temp_audio.mp3") -> str:
    """
    Extracts a mono, 16KHz WAV file from the given input file using FFmpeg.

    Args:
        input_file: Path to the source media file.
        output_file: Output path for the extracted WAV audio.

    Returns:
        The path to the generated audio file.

    Raises:
        FileNotFoundError: If the input file is missing.
        RuntimeError: If the FFmpeg command fails.
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    command = [
        "ffmpeg",
        "-y",                   # Overwrite output files without asking
        "-i", input_file,       # Input file
        "-vn",                  # Disable video
        "-acodec", "libmp3lame", # Use MP3 codec
        "-q:a", "4",            # High quality VBR
        "-ar", "16000",         # Audio sample rate: 16kHz
        "-ac", "1",             # Audio channels: 1 (mono)
        output_file             # Output file path
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        return output_file
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg extraction failed: {error_msg}")


def cleanup_temp_files(temp_file: str = "temp_audio.mp3") -> None:
    """
    Carefully deletes the intermediate temporary WAV file used during processing.
    """
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
            print(f"Cleaned up temporary audio artifact: {temp_file}")
        except Exception as e:
            print(f"Failed to cleanly delete {temp_file}: {e}")

from typing import List

def chunk_audio_for_api(audio_path: str, chunk_length_ms: int = 1500000) -> List[str]:
    """
    Safely splits the main WAV into 10-minute API payload chunks
    to stay precisely under the strict 25 MB payload payload threshold.
    """
    from pydub import AudioSegment
    audio = AudioSegment.from_file(audio_path)
    chunks = []
    
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_name = f"{audio_path}_chunk_{len(chunks)}.mp3"
        chunk.export(chunk_name, format="mp3", bitrate="64k")
        chunks.append(chunk_name)
        
    return chunks
