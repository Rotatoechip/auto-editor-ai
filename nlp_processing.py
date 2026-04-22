import string
import json
import os
from typing import List, Dict, Any, Tuple

FILLER_WORDS = {
    "嗯", "啊", "那个", "呃", "哎", "这", "就是",
    "然后", "你知道", "对", "的话", "啊啊", "嗯嗯", "那",
    "um", "uh", "ums", "uhs", "[breathing]", "[silence]",
    "(sigh)", "[hmm]", "[sigh]", "[咳嗽]", "[clears throat]"
}


def clean_word(word: str) -> str:
    """Removes common punctuation from word for equality checking."""
    to_remove = string.punctuation + "，。？！、：；“”（）《》"
    return word.strip().strip(to_remove)


def build_searchable_text(
        word_data: List[Dict[str, Any]]) -> Tuple[str, str, List[int]]:
    """Builds raw text, clean text, and a mapping from clean text chars to word indices."""
    clean_text = ""
    char_to_word_idx = []
    raw_text = ""

    to_remove = string.punctuation + "，。？！、：；“”（）《》 \t\n\r"

    for i, w in enumerate(word_data):
        raw_w_str = w["word"]
        raw_text += raw_w_str

        for char in raw_w_str:
            if char not in to_remove:
                clean_text += char
                char_to_word_idx.append(i)

    return raw_text, clean_text, char_to_word_idx


def identify_slips_of_tongue(full_text: str) -> List[str]:
    """Uses Google GenAI SDK to identify semantic slips of the tongue."""
    print("Calling Gemini API to identify complex slips of the tongue...")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment. Skipping LLM slip identification. (Please export GEMINI_API_KEY)")
        return []

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Warning: google-genai package not found. Skipping LLM slip identification.")
        print("Please run: pip install google-genai")
        return []

    client = genai.Client(api_key=api_key)

    system_instruction = "You are a video editor. Identify any false starts, corrected sentences, or semantic slips of the tongue in the following Mandarin transcript. Return ONLY a JSON list of the exact phrases that should be cut."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # In case the model returns an object containing the list
            for val in data.values():
                if isinstance(val, list):
                    return val
        return []
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return []


def filter_words(word_data: List[Dict[str,
                                      Any]],
                 pause_threshold: float,
                 margin: float) -> List[Tuple[float,
                                              float]]:
    """
    Processes transcribed word data to filter out pauses, filler words, repetitions, and semantic slips.
    Groups remaining words into safe continuous segments.
    """
    if not word_data:
        return []

    valid_indices = [True] * len(word_data)

    # 1. Identify repetitions and filler words (Hardcoded Rules)
    for i in range(len(word_data)):
        word_text = clean_word(word_data[i]["word"])

        # Identify Filler Words
        if word_text in FILLER_WORDS:
            valid_indices[i] = False

        # Identify Repetitions
        if i > 0:
            prev_word_text = clean_word(word_data[i - 1]["word"])
            if word_text == prev_word_text and word_text != "":
                valid_indices[i - 1] = False

    # 2. Identify Semantic Slips (LLM Processing)
    raw_text, clean_text, char_to_word_idx = build_searchable_text(word_data)
    slips = identify_slips_of_tongue(raw_text)

    to_remove_chars = string.punctuation + "，。？！、：；“”（）《》 \t\n\r"

    marked_slip_count = 0
    for slip in slips:
        clean_slip = "".join(c for c in slip if c not in to_remove_chars)
        if not clean_slip:
            continue

        start_idx = 0
        while True:
            # Find the slip phrase in the contiguous clean text
            idx = clean_text.find(clean_slip, start_idx)
            if idx == -1:
                break

            end_idx = idx + len(clean_slip)

            # Use char_to_word mapping to locate the exact discrete words that
            # make up the slip
            for c in range(idx, end_idx):
                w_i = char_to_word_idx[c]
                valid_indices[w_i] = False

            marked_slip_count += 1
            start_idx = end_idx

    if marked_slip_count > 0:
        print(
            f"LLM identified and removed {marked_slip_count} semantic slips of the tongue.")

    # 3. Group sequentially tracking boundary index limits
    segments = []
    current_segment = None

    for i, word in enumerate(word_data):
        if not valid_indices[i]:
            continue

        start_time = word["start"]
        end_time = word["end"]

        if current_segment is None:
            current_segment = [start_time, end_time, i, i]
        else:
            last_valid_index = current_segment[3]
            prev_word_end = word_data[last_valid_index]["end"]

            is_adjacent = (last_valid_index == i - 1)
            is_within_pause = (start_time - prev_word_end) <= pause_threshold

            if is_adjacent and is_within_pause:
                current_segment[1] = max(current_segment[1], end_time)
                current_segment[3] = i
            else:
                segments.append(current_segment)
                current_segment = [start_time, end_time, i, i]

    if current_segment is not None:
        segments.append(current_segment)

    # 4. Apply strictly Clamped margins bounded by explicit un-kept word edges
    clamped_segments: List[List[float]] = []
    for seg in segments:
        first_word_idx = seg[2]
        last_word_idx = seg[3]
        
        # Max boundary computation ensures margin absolutely mathematically never leaks into a deleted phrase
        lower_bound = word_data[first_word_idx - 1]["end"] if first_word_idx > 0 else 0.0
        upper_bound = word_data[last_word_idx + 1]["start"] if last_word_idx < len(word_data) - 1 else seg[1] + margin
        
        safe_start = max(lower_bound, seg[0] - margin)
        safe_start = max(0.0, safe_start) # ensure non-negative
        safe_end = min(upper_bound, seg[1] + margin)
        
        if not clamped_segments:
            clamped_segments.append([safe_start, safe_end])
        else:
            last_seg = clamped_segments[-1]
            if safe_start <= last_seg[1]:
                # Automatically merge overlap natively 
                last_seg[1] = max(last_seg[1], safe_end)
            else:
                clamped_segments.append([safe_start, safe_end])

    return [(s[0], s[1]) for s in clamped_segments]
