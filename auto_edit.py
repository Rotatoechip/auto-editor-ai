import sys
from typing import List, Dict, Any
from tqdm import tqdm
from cli_interface import parse_arguments
from audio_processing import extract_mono_audio, cleanup_temp_files
from nlp_processing import filter_words
from draft_generation import generate_jianying_draft


import os
import json
from openai import OpenAI
from pydub import AudioSegment

def transcribe_audio(audio_path: str) -> List[Dict[str, Any]]:
    """
    Transcribes the given audio file using the OpenAI Cloud API (whisper-1).
    Performs dynamic 25MB chunking natively if the file is too large.

    Args:
        audio_path: Path to the audio file (MP3/M4A/WAV).

    Returns:
        A list of dictionaries containing 'word', 'start', and 'end' for each word.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Please export it to use the cloud API.")
        
    client = OpenAI(api_key=api_key)
    
    from audio_processing import chunk_audio_for_api, cleanup_temp_files
    print(f"Chunking {audio_path} for Cloud API safety...")
    chunk_paths = chunk_audio_for_api(audio_path)
    
    word_results = []
    current_time_offset = 0.0
    
    print("Transcribing via OpenAI Cloud Whisper GPU cluster...")
    for idx, chunk_path in enumerate(chunk_paths):
        print(f"  Uploading Chunk {idx+1}/{len(chunk_paths)}...")
        
        with open(chunk_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                language="zh",
                prompt="请完整保留所有语气词，如嗯、啊、那个。"
            )
            
        if hasattr(response, 'words') and response.words:
            for word_obj in response.words:
                # Word-level timestamps mapped back to original timeline via accumulated chunk offset
                word_results.append({
                    "word": word_obj.word,
                    "start": word_obj.start + current_time_offset,
                    "end": word_obj.end + current_time_offset
                })
                
        # Increment exact delta offset utilizing pydub's native ms length calculation
        # to ensure the next chunk falls flawlessly into the correct sequence.
        chunk_segment = AudioSegment.from_file(chunk_path)
        current_time_offset += len(chunk_segment) / 1000.0
        
        # Cleanup processed chunk artifact immediately
        cleanup_temp_files(chunk_path)

    return word_results


def main() -> None:
    """
    Main entry point for the automated video editing pipeline.
    """
    args = parse_arguments()

    print(f"Starting processing for: {args.input_file}")
    print(f"Pause Threshold: {args.pause_threshold}s")
    print(f"Margin: {args.margin}s")

    print("\nPreparing audio...")
    try:
        # Check if the input is already a lightweight audio file
        ext = os.path.splitext(args.input_file)[1].lower()
        is_audio = ext in [".m4a", ".mp3", ".wav", ".aac", ".flac"]
        file_size_mb = os.path.getsize(args.input_file) / (1024 * 1024)
        
        # If it's already a small audio file, we might skip extraction
        # but we still want it to be mono and 16k for best Whisper results
        # So we'll still extract to a temp mono MP3, but it's now much faster/smaller.
        out_audio = extract_mono_audio(args.input_file)
        print(f"Audio processed successfully: {out_audio}")

        print("\nStarting transcription phase...")
        word_data = transcribe_audio(out_audio)
        print(
            f"Transcription complete. Extracted {len(word_data)} typed words.")

        if args.transcribe_only:
            output_json = os.path.splitext(args.input_file)[0] + "_transcript.json"
            print(f"\nTranscribe-only mode active. Saving to: {output_json}")
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(word_data, f, ensure_ascii=False, indent=2)
            cleanup_temp_files(out_wav)
            print("Done.")
            return

        print("\nFiltering and generating keep segments...")
        keep_segments = filter_words(
            word_data, args.pause_threshold, args.margin)
        print(f"Generated {len(keep_segments)} keep segments after filtering.")

        for idx, (start, end) in enumerate(keep_segments):
            print(f"  Segment {idx+1}: {start:.2f}s - {end:.2f}s")

        print("\nGenerating Native JianYing Pro Project Draft...")
        original_name = os.path.basename(args.input_file)
        draft_dir = generate_jianying_draft(args.input_file, keep_segments)
        print(f"Native Draft 'AI Edited: {original_name}' has been injected. Open JianYing Pro to see it in your Local Drafts.")

        print("\nCleaning up environment...")
        cleanup_temp_files(out_audio)
        print("\nPipeline entirely completed!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
