"""Protocol definitions for Phase 3.10 rendering pipeline.

This module defines the interfaces (Protocols) that will be implemented
by the infrastructure layer and used by the application layer.

These are CONTRACT definitions - they specify WHAT, not HOW.
"""

from typing import Protocol, Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


# ============================================================================
# Entity 1: VideoRenderingContext
# ============================================================================

@dataclass
class VideoRenderingContext:
    """Single source of truth for all rendering inputs.

    This context is prepared once by _prepare_all_context() and passed
    to all rendering functions, eliminating redundant computations.

    Attributes:
        item: Original JSON configuration from user
        layout: Computed layout from domain.layout.compute_layout_bboxes
        timeline: Time markers from domain.timing.calculate_timeline
        entry_ctx: Entry video context (path, duration, enabled)
        ending_ctx: Ending video context (path, duration, enabled)
        letters_ctx: Letter images context (paths, bbox, missing)
        metadata: Additional computed info (durations, paths, etc.)

    Example:
        ctx = VideoRenderingContext(
            item={"letters": "I i", "word_en": "Ice", ...},
            layout={"letters_bbox": {"x": 64, "y": 48, ...}, ...},
            timeline={"countdown_start": 0.0, "reveal_start": 3.0, ...},
            entry_ctx={"enabled": True, "path": "assets/entry.mp4", ...},
            ending_ctx={"enabled": True, "path": "assets/ending.mp4", ...},
            letters_ctx={"letters": [...], "missing": []},
            metadata={"video_size": (1920, 1080), "fps": 24, ...}
        )
    """
    item: Dict[str, Any]
    layout: Dict[str, Any]
    timeline: Dict[str, Any]
    entry_ctx: Dict[str, Any]
    ending_ctx: Dict[str, Any]
    letters_ctx: Dict[str, Any]
    metadata: Dict[str, Any]


# ============================================================================
# Entity 2: Layer Protocol
# ============================================================================

class Layer(Protocol):
    """Protocol for renderable video layers.

    Each layer represents a visual element in the final video.
    Layers are composed together by the IVideoComposer.

    Contract:
        - render() must return a MoviePy Clip
        - get_bbox() must return Dict with x, y, w, h keys
        - get_duration() must return positive float

    Example Implementation:
        class LettersLayer:
            def __init__(self, ctx: VideoRenderingContext):
                self.ctx = ctx

            def render(self) -> Any:
                # Load letter images, position according to ctx
                return clip

            def get_bbox(self) -> Dict[str, int]:
                return self.ctx.layout["letters_bbox"]

            def get_duration(self) -> float:
                return self.ctx.timeline["total_duration"]
    """

    def render(self) -> Any:
        """Render this layer and return a MoviePy Clip.

        Returns:
            MoviePy Clip (ImageClip, TextClip, VideoFileClip, etc.)

        Raises:
            RuntimeError: If rendering fails
        """
        ...

    def get_bbox(self) -> Dict[str, int]:
        """Get the bounding box for this layer.

        Returns:
            Dict with keys: x, y, w, h (pixel coordinates)
        """
        ...

    def get_duration(self) -> float:
        """Get the duration of this layer in seconds.

        Returns:
            Duration in seconds (positive float)
        """
        ...


# ============================================================================
# Entity 3: IVideoComposer Protocol (Existing)
# ============================================================================

class IVideoComposer(Protocol):
    """Protocol for video composition engines.

    Abstraction over MoviePy or other video libraries.
    This Protocol already exists in infrastructure/video/interface.py

    Contract:
        - compose_layers() must handle overlapping layers (z-order)
        - export() must produce valid MP4 file
        - Must support headless rendering (no GUI)

    Example Implementation:
        class MoviePyComposer:
            def compose_layers(self, layers, audio=None):
                # Use CompositeVideoClip to combine layers
                return composite_clip

            def export(self, clip, output_path, **kwargs):
                # Use clip.write_videofile() with FFmpeg
                clip.write_videofile(output_path, ...)
    """

    def compose_layers(
        self,
        layers: List[Any],  # List of MoviePy Clips
        audio: Optional[Any] = None  # Optional AudioClip
    ) -> Any:
        """Combine multiple layers into a single video.

        Args:
            layers: List of MoviePy Clips (visual layers)
            audio: Optional AudioClip (background music + beeps)

        Returns:
            CompositeVideoClip (MoviePy)

        Raises:
            ValueError: If layers list is empty
            RuntimeError: If composition fails
        """
        ...

    def export(
        self,
        clip: Any,  # CompositeVideoClip
        output_path: str,
        **kwargs  # codec, fps, etc.
    ) -> None:
        """Export composed video to file.

        Args:
            clip: CompositeVideoClip to export
            output_path: Output MP4 file path
            **kwargs: Additional FFmpeg arguments (codec, fps, etc.)

        Side Effects:
            Writes MP4 file to output_path

        Raises:
            IOError: If file cannot be written
            RuntimeError: If FFmpeg fails
        """
        ...


# ============================================================================
# Function Signatures (Application Layer)
# ============================================================================

# These are the 11 sub-functions that will be extracted from render_video_moviepy

def _prepare_all_context(item: Dict[str, Any]) -> VideoRenderingContext:
    """Prepare all rendering context data upfront.

    Args:
        item: JSON configuration dict (validated against SCHEMA)

    Returns:
        VideoRenderingContext with all computed data

    Raises:
        ValueError: If item fails validation
        FileNotFoundError: If required assets missing (unless dry_run)

    Example:
        item = {"letters": "I i", "word_en": "Ice", ...}
        ctx = _prepare_all_context(item)
        assert "letters_bbox" in ctx.layout
    """
    ...


def _create_background_clip(ctx: VideoRenderingContext) -> Any:
    """Create background clip (image or solid color).

    Args:
        ctx: VideoRenderingContext with item and metadata

    Returns:
        MoviePy Clip (ImageClip or ColorClip)

    Raises:
        FileNotFoundError: If image_path specified but not found
        RuntimeError: If clip creation fails
    """
    ...


def _render_letters_layer(ctx: VideoRenderingContext) -> Any:
    """Render letter images in top-left.

    Args:
        ctx: VideoRenderingContext with letters_ctx and layout

    Returns:
        MoviePy CompositeVideoClip with positioned letter images

    Raises:
        FileNotFoundError: If letter assets missing
        RuntimeError: If rendering fails
    """
    ...


def _render_chinese_zhuyin_layer(ctx: VideoRenderingContext) -> Any:
    """Render Chinese text + Zhuyin annotations in top-right.

    Args:
        ctx: VideoRenderingContext with item (word_zh) and layout

    Returns:
        MoviePy ImageClip with rendered text

    Raises:
        ValueError: If word_zh format invalid
        RuntimeError: If font rendering fails
    """
    ...


def _render_timer_layer(ctx: VideoRenderingContext) -> Any:
    """Render countdown timer in top-left corner.

    Args:
        ctx: VideoRenderingContext with timeline (countdown_sec)

    Returns:
        MoviePy Clip with dynamic countdown text

    Raises:
        RuntimeError: If timer rendering fails
    """
    ...


def _render_reveal_layer(ctx: VideoRenderingContext) -> Any:
    """Render word reveal animation (typing effect) in bottom center.

    Args:
        ctx: VideoRenderingContext with item (word_en) and timeline

    Returns:
        MoviePy Clip with typing animation

    Raises:
        RuntimeError: If reveal effect fails
    """
    ...


def _render_progress_bar_layer(ctx: VideoRenderingContext) -> Any:
    """Render progress bar at bottom of video.

    Args:
        ctx: VideoRenderingContext with timeline (total_duration)

    Returns:
        MoviePy Clip with animated progress bar

    Raises:
        RuntimeError: If progress bar rendering fails
    """
    ...


def _process_audio_tracks(ctx: VideoRenderingContext) -> Any:
    """Mix background music + countdown beeps.

    Args:
        ctx: VideoRenderingContext with item (music_path) and timeline

    Returns:
        MoviePy AudioClip (mixed audio)

    Raises:
        FileNotFoundError: If music_path not found
        RuntimeError: If audio mixing fails
    """
    ...


def _load_entry_ending_clips(
    ctx: VideoRenderingContext
) -> Tuple[Optional[Any], Optional[Any]]:
    """Load optional entry and ending video clips.

    Args:
        ctx: VideoRenderingContext with entry_ctx and ending_ctx

    Returns:
        Tuple of (entry_clip, ending_clip)
        Either or both may be None if disabled

    Raises:
        FileNotFoundError: If enabled but path not found
        RuntimeError: If video loading fails
    """
    ...


def _compose_and_export(
    ctx: VideoRenderingContext,
    layers: List[Any],
    audio: Any,
    output_path: str,
    composer: Optional[IVideoComposer] = None
) -> None:
    """Combine all layers + audio and export to MP4.

    Args:
        ctx: VideoRenderingContext with metadata
        layers: List of MoviePy Clips (background, letters, etc.)
        audio: MoviePy AudioClip
        output_path: Output MP4 file path
        composer: IVideoComposer implementation (None = default MoviePy)

    Side Effects:
        Writes MP4 file to output_path

    Raises:
        ValueError: If layers list is empty
        IOError: If output_path cannot be written
        RuntimeError: If composition or export fails
    """
    ...


def render_video(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
    composer: Optional[IVideoComposer] = None,
) -> Dict[str, Any]:
    """Orchestrate complete video rendering pipeline (PUBLIC API).

    This is the main entry point for video rendering.
    It coordinates all 11 sub-functions to produce the final video.

    Args:
        item: JSON configuration dict (validated against SCHEMA)
        out_path: Output MP4 file path
        dry_run: If True, only compute metadata without rendering
        skip_ending: If True, skip ending video (for batch processing)
        composer: IVideoComposer implementation (None = default MoviePy)

    Returns:
        Result dict:
        {
            "success": True,
            "duration": 13.0,
            "output_path": "out/Ice.mp4",
            "metadata": {...}
        }

    Raises:
        ValueError: If item fails validation
        FileNotFoundError: If required assets missing (unless dry_run)
        RuntimeError: If rendering fails

    Example:
        item = {"letters": "I i", "word_en": "Ice", ...}
        result = render_video(item, "out/Ice.mp4")
        assert result["success"]
        assert os.path.exists("out/Ice.mp4")
    """
    ...


# ============================================================================
# Deprecated API (Backward Compatibility)
# ============================================================================

def render_video_moviepy(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.video_service.render_video 代替

    Args:
        item: JSON configuration dict
        out_path: Output MP4 file path
        dry_run: If True, only compute metadata without rendering
        skip_ending: If True, skip ending video (for batch processing)

    Returns:
        Result dict (same as render_video)

    Warnings:
        DeprecationWarning: Always raised to guide migration

    Example:
        # OLD (deprecated)
        from spellvid.utils import render_video_moviepy
        result = render_video_moviepy(item, "out/test.mp4")

        # NEW (recommended)
        from spellvid.application.video_service import render_video
        result = render_video(item, "out/test.mp4")
    """
    ...


# ============================================================================
# Contract Validation
# ============================================================================

def validate_context(ctx: VideoRenderingContext) -> bool:
    """Validate that VideoRenderingContext has all required fields.

    Args:
        ctx: VideoRenderingContext to validate

    Returns:
        True if valid

    Raises:
        ValueError: If ctx missing required fields or invalid

    Checks:
        - item passes JSON schema
        - layout has all required bboxes
        - timeline has valid time markers
        - All file paths exist (if not dry_run)
    """
    ...


def validate_layer(layer: Any) -> bool:
    """Validate that a layer implementation satisfies Layer protocol.

    Args:
        layer: Object to validate

    Returns:
        True if valid

    Raises:
        TypeError: If layer doesn't satisfy Layer protocol

    Checks:
        - Has render() method
        - Has get_bbox() method
        - Has get_duration() method
        - render() returns MoviePy Clip
        - get_bbox() returns valid Dict[str, int]
        - get_duration() returns positive float
    """
    ...


def validate_composer(composer: Any) -> bool:
    """Validate that a composer satisfies IVideoComposer protocol.

    Args:
        composer: Object to validate

    Returns:
        True if valid

    Raises:
        TypeError: If composer doesn't satisfy IVideoComposer protocol

    Checks:
        - Has compose_layers() method
        - Has export() method
        - Methods have correct signatures
    """
    ...
