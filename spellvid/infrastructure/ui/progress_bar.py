"""Progress bar rendering infrastructure.

This module provides functions for generating and rendering segmented
progress bars with color transitions (safe→warn→danger) for video
countdown timers.

Architecture:
- Band Layout: Calculates color band positions based on ratios
- Base Arrays: Generates cached RGB and alpha mask arrays
- Mask Creation: Converts alpha arrays to MoviePy ImageClip masks
- Segment Planning: Plans frame-by-frame progress bar updates

Technical Details:
- Uses numpy for efficient array operations
- Implements caching for base arrays (performance)
- Supports rounded corners via PIL ImageDraw
- Generates time-synced color transitions
"""

from typing import Any, Dict, List, Tuple

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False
    np = None  # type: ignore

try:
    from PIL import Image, ImageDraw

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore

try:
    import moviepy.editor as mpy

    _HAS_MOVIEPY = True
except ImportError:
    _HAS_MOVIEPY = False
    mpy = None  # type: ignore

# Import constants from shared layer
from spellvid.shared.constants import (
    PROGRESS_BAR_COLORS,
    PROGRESS_BAR_CORNER_RADIUS,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_RATIOS,
    PROGRESS_BAR_WIDTH,
)

# Module-level cache for base arrays (performance optimization)
_progress_bar_cache: Dict[int, Tuple[Any, Any]] = {}


def calculate_band_layout(bar_width: int) -> List[Dict[str, Any]]:
    """Calculate color band positions with absolute pixel spans.

    Divides the progress bar into three color zones (safe, warn, danger)
    based on predefined ratios. Each band gets an absolute start/end
    position in pixels.

    Args:
        bar_width: Total width of the progress bar in pixels.

    Returns:
        List of band dictionaries with keys:
            - name: Band identifier ("safe", "warn", "danger")
            - color: RGB tuple (e.g., (0, 255, 0))
            - start: Starting x-coordinate (pixels)
            - end: Ending x-coordinate (pixels)

    Example:
        >>> bands = calculate_band_layout(1792)
        >>> len(bands)
        3
        >>> bands[0]['name']
        'safe'
        >>> bands[0]['color']
        (0, 255, 0)
        >>> bands[0]['start']
        0
        >>> bands[0]['end']  # ~50% of width
        896

    Technical Notes:
        - Bands are ordered: safe (green) → warn (yellow) → danger (red)
        - Last band always extends to full width (handles rounding errors)
        - Uses PROGRESS_BAR_RATIOS from shared constants
    """
    order = ("safe", "warn", "danger")
    layout: List[Dict[str, Any]] = []
    cursor = 0

    for idx, key in enumerate(order):
        if idx == len(order) - 1:
            # Last band extends to full width
            end = bar_width
        else:
            width = int(round(bar_width * PROGRESS_BAR_RATIOS[key]))
            end = min(bar_width, cursor + width)

        end = max(cursor, end)  # Ensure end >= start
        layout.append(
            {
                "name": key,
                "color": PROGRESS_BAR_COLORS[key],
                "start": cursor,
                "end": end,
            }
        )
        cursor = end

    # Ensure last band extends to exact width
    if layout:
        layout[-1]["end"] = bar_width

    return layout


def generate_base_arrays(
    bar_width: int,
) -> Tuple[Any, Any]:
    """Generate cached RGB and alpha mask arrays for progress bar.

    Creates a full-width progress bar with three color zones and
    rounded corners. Results are cached for performance (same width
    = reuse arrays).

    Args:
        bar_width: Total width of the progress bar in pixels.

    Returns:
        Tuple of (color_rgb, alpha_mask):
            - color_rgb: numpy array of shape (height, width, 3), dtype uint8
            - alpha_mask: numpy array of shape (height, width), dtype uint8

    Raises:
        RuntimeError: If numpy or PIL is not available.

    Example:
        >>> color, mask = generate_base_arrays(1792)
        >>> color.shape
        (32, 1792, 3)
        >>> mask.shape
        (32, 1792)
        >>> mask[16, 16]  # Inside rounded corner
        255
        >>> mask[0, 0]  # Outside rounded corner
        0

    Technical Details:
        - Height: PROGRESS_BAR_HEIGHT (32px)
        - Corner radius: PROGRESS_BAR_CORNER_RADIUS (16px)
        - Uses PIL for rounded rectangle mask generation
        - Cache key: bar_width (assumes height/radius constant)

    Performance:
        - First call: Generates arrays (~10ms for 1792px width)
        - Subsequent calls: Returns cached arrays (~0.1ms)
    """
    if not _HAS_NUMPY:
        raise RuntimeError("numpy is required for progress bar rendering")
    if not _HAS_PIL:
        raise RuntimeError("PIL is required for progress bar rendering")

    # Check cache first
    cached = _progress_bar_cache.get(bar_width)
    if cached:
        return cached

    height = PROGRESS_BAR_HEIGHT

    # Create RGB color array
    color = np.zeros((height, bar_width, 3), dtype=np.uint8)
    layout = calculate_band_layout(bar_width)

    # Fill each color band
    for band in layout:
        start = max(0, int(band["start"]))
        end = max(start, min(bar_width, int(band["end"])))
        if end <= start:
            continue

        # Set RGB channels
        color[:, start:end, 0] = band["color"][0]
        color[:, start:end, 1] = band["color"][1]
        color[:, start:end, 2] = band["color"][2]

    # Create alpha mask with rounded corners
    mask_img = Image.new("L", (bar_width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.rounded_rectangle(
        (0, 0, bar_width - 1, height - 1),
        radius=PROGRESS_BAR_CORNER_RADIUS,
        fill=255,
    )
    mask = np.array(mask_img, dtype=np.uint8)

    # Cache results
    _progress_bar_cache[bar_width] = (color, mask)
    return color, mask


def create_mask_clip(mask_slice: Any, duration: float) -> Any:
    """Create a MoviePy ImageClip mask from an alpha slice array.

    Converts a numpy alpha mask (0-255) to a MoviePy mask clip (0.0-1.0 float).
    Handles different MoviePy versions (is_mask vs ismask parameter).

    Args:
        mask_slice: numpy array of shape (height, width), dtype uint8,
            values 0-255.
        duration: Duration of the mask clip in seconds.

    Returns:
        MoviePy ImageClip configured as a mask with specified duration.

    Raises:
        RuntimeError: If numpy or MoviePy is not available.

    Example:
        >>> import numpy as np
        >>> mask = np.ones((32, 100), dtype=np.uint8) * 255
        >>> clip = create_mask_clip(mask, 0.5)
        >>> clip.duration
        0.5
        >>> clip.ismask  # or clip.is_mask depending on MoviePy version
        True

    Technical Details:
        - Normalizes mask: 255 → 1.0, 0 → 0.0
        - Auto-detects MoviePy parameter name (is_mask vs ismask)
        - Returns ImageClip with mask flag set
    """
    if not _HAS_NUMPY:
        raise RuntimeError("numpy is required for mask clip creation")
    if not _HAS_MOVIEPY:
        raise RuntimeError("MoviePy is required for mask clip creation")

    # Normalize to 0.0-1.0 range
    mask_arr = mask_slice.astype(np.float32) / 255.0

    # Auto-detect MoviePy parameter name (version compatibility)
    import inspect

    mask_kwargs = {}
    try:
        params = inspect.signature(mpy.ImageClip.__init__).parameters
        if "is_mask" in params:
            mask_kwargs["is_mask"] = True
        elif "ismask" in params:
            mask_kwargs["ismask"] = True
    except Exception:
        # Fallback to legacy parameter
        mask_kwargs["ismask"] = True

    if not mask_kwargs:
        mask_kwargs["ismask"] = True

    # Create and return mask clip
    clip = mpy.ImageClip(mask_arr, **mask_kwargs).with_duration(duration)
    return clip


def plan_segments(
    countdown: float,
    total_duration: float,
    *,
    fps: int = 10,
    bar_width: int = PROGRESS_BAR_WIDTH,
) -> List[Dict[str, Any]]:
    """Plan frame-by-frame progress bar segments across countdown duration.

    Generates a timeline of progress bar states, each with width, position, and
    color spans. The bar shrinks from right to left as countdown decreases.

    Args:
        countdown: Countdown duration in seconds (time when bar reaches zero).
        total_duration: Total video duration in seconds (≥ countdown).
        fps: Frames per second for segment planning (default: 10).
        bar_width: Total width of the progress bar in pixels.

    Returns:
        List of segment dictionaries with keys:
            - start: Segment start time (seconds)
            - end: Segment end time (seconds)
            - width: Visible bar width (pixels)
            - x_start: Left edge x-coordinate (pixels)
            - color_spans: List of {"color": (R,G,B), "start": x, "end": x}
            - corner_radius: Rounded corner radius (pixels)

        Final segment has width=0 (bar disappears after countdown).

    Example:
        >>> segments = plan_segments(countdown=10, total_duration=15, fps=10)
        >>> len(segments)  # 10 sec × 10 fps + 1 final = 101
        101
        >>> segments[0]['width']  # Full width at start
        1792
        >>> segments[0]['x_start']
        0
        >>> segments[-2]['width']  # Almost zero near end
        18
        >>> segments[-1]['width']  # Zero after countdown
        0

    Behavior:
        - Bar width decreases proportionally to remaining time
        - Color zones (green→yellow→red) disappear in order
        - Segments are uniform in duration (countdown / fps)
        - Final segment (after countdown) has zero width

    Edge Cases:
        - countdown=0: Returns single zero-width segment
        - fps≤0 or bar_width≤0: Returns empty list
        - total_duration < countdown: Uses countdown as total

    Performance:
        - 10 sec × 10 fps = 100 segments (~1ms computation)
        - Uses math.ceil for step count (ensures coverage)
    """
    if not _HAS_NUMPY:
        raise RuntimeError("numpy is required for progress bar planning")

    countdown = float(max(0.0, countdown))
    total_duration = float(max(total_duration, countdown))

    if fps <= 0 or bar_width <= 0:
        return []

    # Special case: No countdown
    if countdown == 0.0:
        return [
            {
                "start": 0.0,
                "end": round(total_duration, 6),
                "width": 0,
                "x_start": bar_width,
                "color_spans": [],
                "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
            }
        ]

    import math

    layout = calculate_band_layout(bar_width)

    # Calculate number of steps
    step_count = max(1, int(math.ceil(countdown * float(fps))))
    step = countdown / step_count

    segments: List[Dict[str, Any]] = []
    prev_width = bar_width

    for idx in range(step_count):
        start = min(countdown, idx * step)
        end = min(countdown, (idx + 1) * step)

        if end <= start:
            continue

        # Calculate remaining time and width
        remaining = max(0.0, countdown - start)
        ratio = remaining / countdown if countdown else 0.0
        raw_width = int(round(bar_width * ratio))

        # Ensure width decreases monotonically
        visible_width = min(prev_width, max(0, raw_width))

        # Keep at least 1px if ratio > 0 and previous was > 0
        if ratio > 0.0:
            if prev_width > 0:
                visible_width = max(1, visible_width)
            else:
                visible_width = 0
        else:
            visible_width = 0

        # Calculate x position (right-aligned shrinkage)
        x_start = bar_width - visible_width if visible_width > 0 else bar_width

        # Calculate color spans (which bands are visible)
        color_spans: List[Dict[str, Any]] = []
        if visible_width > 0:
            span_start = x_start
            span_end = x_start + visible_width

            for band in layout:
                overlap_start = max(span_start, band["start"])
                overlap_end = min(span_end, band["end"])

                if overlap_end > overlap_start:
                    color_spans.append(
                        {
                            "color": band["color"],
                            "start": int(overlap_start),
                            "end": int(overlap_end),
                        }
                    )

        segments.append(
            {
                "start": round(float(start), 6),
                "end": round(float(end), 6),
                "width": int(visible_width),
                "x_start": int(x_start),
                "color_spans": color_spans,
                "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
            }
        )
        prev_width = visible_width

    # Add final zero-width segment (after countdown ends)
    segments.append(
        {
            "start": round(float(countdown), 6),
            "end": round(float(total_duration), 6),
            "width": 0,
            "x_start": bar_width,
            "color_spans": [],
            "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
        }
    )

    return segments
