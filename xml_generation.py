import xml.etree.ElementTree as ET
import os
from typing import List, Tuple


def get_time_string(seconds: float) -> str:
    """Format time as a rational fraction string based on a 60000 timescale."""
    # Complying with FCPXML time sequence representations strictly
    return f"{int(seconds * 60000)}/60000s"


def generate_fcpxml(
        input_file: str,
        segments: List[Tuple[float, float]],
        output_file: str = "auto_edit_timeline.fcpxml") -> str:
    """
    Generates an FCPXML v1.9 sequence timeline accurately mapping out the kept segments.

    Args:
        input_file: Path to the original primary source media asset.
        segments: List of continuous valid tuples (start_time, end_time).
        output_file: Resulting XML path location.

    Returns:
        The generated FCPXML output file path.
    """
    if not segments:
        print("Warning: No valid segments found. Outputting an empty timeline.")

    fcpxml = ET.Element("fcpxml", version="1.9")

    # 1. Setup global resources & assets
    resources = ET.SubElement(fcpxml, "resources")

    # Create the generic format descriptor
    format_id = "r1"
    ET.SubElement(resources, "format", id=format_id, name="FFVideoFormat1080p30")

    # Define primary media asset securely
    asset_id = "r2"
    abs_input_file = os.path.abspath(input_file)
    file_uri = "file://" + abs_input_file.replace(" ", "%20")
    asset = ET.SubElement(
        resources,
        "asset",
        id=asset_id,
        name="SourceAsset",
        hasVideo="1",
        hasAudio="1"
    )
    ET.SubElement(
        asset,
        "media-rep",
        kind="original-media",
        src=file_uri
    )

    # 2. Build Library, Event, and Sequence timeline
    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name="Auto-Edited Pipeline Event")
    project = ET.SubElement(event, "project", name="AI Auto Editor")

    sequence = ET.SubElement(project, "sequence", format=format_id)
    spine = ET.SubElement(sequence, "spine")

    # 3. Track parsing logically into spine root
    current_timeline_time = 0.0

    for idx, (start_time, end_time) in enumerate(segments):
        duration = end_time - start_time
        if duration <= 0:
            continue

        ET.SubElement(
            spine,
            "asset-clip",
            name=f"Clip Segment {idx+1}",
            ref=asset_id,
            offset=get_time_string(current_timeline_time),  # placement in timeline
            start=get_time_string(start_time),              # reading extracted time from absolute media
            duration=get_time_string(duration)              # slicing size
        )

        current_timeline_time += duration

    # Compile the XML securely
    tree = ET.ElementTree(fcpxml)
    # Ensure standard XML indents
    ET.indent(tree, space="    ", level=0)
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)

    return output_file
