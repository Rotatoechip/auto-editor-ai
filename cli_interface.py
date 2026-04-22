import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parses core command-line arguments for the auto editor.
    """
    parser = argparse.ArgumentParser(
        description="Automated video editing via AI analysis.")
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input video or audio file."
    )
    parser.add_argument(
        "--pause_threshold",
        type=float,
        default=1.8,
        help="Threshold duration in seconds to define a pause (default: 1.8)."
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.4,
        help="Padding in seconds around kept segments (default: 0.6)."
    )
    parser.add_argument(
        "--transcribe_only",
        action="store_true",
        help="If set, only transcribe the video and save to a JSON file without editing."
    )
    return parser.parse_args()
