"""FFmpeg progress tracking utility for audiobook-dl."""

import re
import subprocess
from typing import Optional, Callable
from rich.progress import Progress, TaskID

from .. import logging


def parse_duration(duration_str: str) -> float:
    """Parse ffmpeg duration string (HH:MM:SS.ms or SS.ms) to seconds."""
    try:
        if ":" in duration_str:
            # Format: HH:MM:SS.ms or MM:SS.ms
            parts = duration_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
        else:
            # Format: SS.ms
            return float(duration_str)
    except (ValueError, AttributeError):
        return 0.0


def get_media_duration(filepath: str) -> Optional[float]:
    """Get the duration of a media file using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def run_ffmpeg_with_progress(
    command: list[str],
    progress: Progress,
    task: TaskID,
    total_duration: Optional[float] = None,
    description: Optional[str] = None
) -> tuple[int, str, str]:
    """
    Run an ffmpeg command with progress tracking.

    Args:
        command: The ffmpeg command as a list of arguments
        progress: Rich Progress instance
        task: Rich Progress task ID to update
        total_duration: Total duration in seconds (for percentage calculation)
        description: Optional description override for the progress bar

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # If ffmpeg output is enabled, run without progress tracking and show all output
    if logging.ffmpeg_output:
        # Don't capture output - let it go directly to console for debugging
        result = subprocess.run(command)
        # Mark task as complete in debug mode
        if total_duration:
            progress.update(task, completed=total_duration)
        return result.returncode, "", ""

    # Run ffmpeg with progress tracking
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    stdout_lines = []
    stderr_lines = []

    # Patterns for parsing ffmpeg output
    time_pattern = re.compile(r'time=(\d+:\d+:\d+\.\d+|\d+\.\d+)')
    duration_pattern = re.compile(r'Duration: (\d+:\d+:\d+\.\d+)')

    # Try to get duration from ffmpeg output if not provided
    detected_duration = total_duration

    while True:
        stderr_line = process.stderr.readline()
        if not stderr_line and process.poll() is not None:
            break

        if stderr_line:
            stderr_lines.append(stderr_line)

            # Try to detect duration from ffmpeg output
            if detected_duration is None:
                duration_match = duration_pattern.search(stderr_line)
                if duration_match:
                    detected_duration = parse_duration(duration_match.group(1))
                    if detected_duration:
                        progress.update(task, total=detected_duration)

            # Parse progress information
            time_match = time_pattern.search(stderr_line)
            if time_match and detected_duration:
                current_time = parse_duration(time_match.group(1))
                progress.update(task, completed=current_time)

                # Update description with speed if available
                if description and 'speed=' in stderr_line:
                    speed_match = re.search(r'speed=\s*(\S+)x', stderr_line)
                    if speed_match:
                        speed = speed_match.group(1)
                        progress.update(task, description=f"{description} (speed: {speed}x)")

    # Get any remaining output
    stdout, stderr = process.communicate()
    if stdout:
        stdout_lines.append(stdout)
    if stderr:
        stderr_lines.append(stderr)

    return process.returncode, ''.join(stdout_lines), ''.join(stderr_lines)


def create_progress_task(
    progress: Progress,
    description: str,
    total: Optional[float] = None
) -> TaskID:
    """
    Create a progress task for ffmpeg operations.

    Args:
        progress: Rich Progress instance
        description: Description for the progress bar
        total: Total duration/size (optional, can be updated later)

    Returns:
        TaskID for the created task
    """
    if total:
        return progress.add_task(description, total=total)
    else:
        # Start with unknown total, will be updated when detected
        return progress.add_task(description, total=100)
