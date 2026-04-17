import os
import time
import uuid
import json
import subprocess
from typing import List, Tuple

def get_uuid() -> str:
    """Generate an uppercase UUID heavily preferred by JianYing."""
    return str(uuid.uuid4()).upper()

def get_video_duration_us(file_path: str, fallback_segments: List[Tuple[float, float]]) -> int:
    """Extracts the exact length of the media file using ffprobe. Essential for JianYing media-linking."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, text=True, check=True
        )
        return int(float(result.stdout.strip()) * 1000000)
    except Exception:
        # Fallback to the last cut timestamp plus some margin if ffprobe is blocked
        if fallback_segments:
            return int(fallback_segments[-1][1] * 1000000) + (10 * 1000000)
        return 0

def generate_jianying_draft(input_file: str, segments: List[Tuple[float, float]]) -> str:
    """
    Synthesizes a JianYing Pro draft folder strictly mapping segments into microsecond timelines.
    """
    if not segments:
        print("Warning: No valid segments found.")

    abs_input_file = os.path.abspath(input_file)
    original_name = os.path.basename(abs_input_file)
    
    total_duration_us = get_video_duration_us(abs_input_file, segments)
    
    timestamp = int(time.time())
    draft_folder_name = f"AI_Edit_{timestamp}"
    
    # Target Path logic explicitly mapped for macOS parity
    home_dir = os.path.expanduser("~")
    base_projects_dir = os.path.join(home_dir, "Movies", "JianyingPro", "User Data", "Projects", "com.lveditor.draft")
    
    if not os.path.exists(base_projects_dir):
        os.makedirs(base_projects_dir, exist_ok=True)
        
    draft_dir = os.path.join(base_projects_dir, draft_folder_name)
    os.makedirs(draft_dir, exist_ok=True)
    
    draft_id = get_uuid()
    
    # 1. Create the unique UUID bindings
    material_video_id = get_uuid()
    speed_id = get_uuid()
    canvas_id = get_uuid()
    audio_fade_id = get_uuid()
    track_id = get_uuid()
    
    # 2. Re-create the generic boilerplate required by Jianying's draft_info.json schema
    draft_info = {
        "id": draft_id,
        "materials": {
            "videos": [{
                "id": material_video_id,
                "type": "video",
                "path": abs_input_file,
                "local_path": abs_input_file,  # Explicitly mapping local POSIX path
                "material_name": original_name,
                "duration": total_duration_us, # Crucial: missing duration disconnects media!
                "local_material_id": ""
            }],
            "audios": [],
            "transitions": [],
            "speeds": [{
                "id": speed_id,
                "speed": 1.0,
                "type": "speed"
            }],
            "canvases": [{
                "id": canvas_id,
                "type": "canvas_color"
            }],
            "audio_fades": [{
                "id": audio_fade_id,
                "type": "audio_fade",
                "fade_in": 50000,
                "fade_out": 50000
            }],
            "sound_channel_mappings": [],
            "audio_balances": [],
            "vocal_separations": []
        },
        "tracks": [{
            "id": track_id,
            "type": "video",
            "segments": []
        }],
        "version": 410000  # Generic stable core version integer
    }
    
    # 3. Microsecond logic scaling for the main track timeline
    current_timeline_us = 0
    
    for idx, (start_time, end_time) in enumerate(segments):
        duration_s = end_time - start_time
        if duration_s <= 0:
            continue
            
        start_us = int(start_time * 1000000)
        duration_us = int(duration_s * 1000000)
        
        segment_id = get_uuid()
        
        segment_obj = {
            "id": segment_id,
            "material_id": material_video_id,
            "source_timerange": {
                "duration": duration_us,
                "start": start_us
            },
            "target_timerange": {
                "duration": duration_us,
                "start": current_timeline_us
            },
            "extra_material_refs": [
                speed_id,
                canvas_id,
                audio_fade_id
            ],
            "render_index": 0
        }
        
        # Inject the segment into the generic video track
        draft_info["tracks"][0]["segments"].append(segment_obj)
        current_timeline_us += duration_us
        
    # 4. Synthesize external draft metadata mapping
    draft_meta_info = {
        "id": draft_id,
        "draft_name": f"AI Edited: {original_name}",
        "draft_root_path": draft_dir,
        "draft_materials": [
            {
                "type": 0, # Usually 0 for standard media directories/nodes
                "value": [abs_input_file]
            }
        ]
    }
    # Notice: explicitly omitting `modDate` and `creator` tags to avoid project corruption.
    
    # 5. Flush directly to hard drive natively bypassing any framework APIs
    info_path = os.path.join(draft_dir, "draft_info.json")
    meta_path = os.path.join(draft_dir, "draft_meta_info.json")
    
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(draft_info, f, ensure_ascii=False, indent=4)
        
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(draft_meta_info, f, ensure_ascii=False, indent=4)
        
    return draft_dir
