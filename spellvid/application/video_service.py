"""視頻生成服務

此模組提供高層次的視頻渲染服務,協調 domain 層和 infrastructure 層。

主要功能:
- render_video(): 單支視頻渲染
- 整合佈局計算、文字渲染、視頻組合
- 支援 dry-run 和 skip_ending 模式
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# Domain layer imports
from spellvid.domain.layout import compute_layout_bboxes

# Shared layer imports
from spellvid.shared.types import VideoConfig

# Infrastructure layer imports
from spellvid.infrastructure.video.interface import IVideoComposer


# ============================================================================
# VideoRenderingContext - Single source of truth for rendering inputs
# ============================================================================

@dataclass
class VideoRenderingContext:
    """Encapsulates all data needed for video rendering.

    This context is prepared once and passed to all rendering functions,
    eliminating the need to recompute layouts, timelines, or contexts.

    Attributes:
        item: Original JSON configuration from user
        layout: Computed layout from domain.layout.compute_layout_bboxes
        timeline: Time markers from domain.timing.calculate_timeline
        entry_ctx: Entry video context (path, duration, enabled)
        ending_ctx: Ending video context (path, duration, enabled)
        letters_ctx: Letter images context (paths, bbox, missing)
        metadata: Additional computed info (durations, paths, etc.)
    """
    item: Dict[str, Any]
    layout: Dict[str, Any]
    timeline: Dict[str, Any]
    entry_ctx: Dict[str, Any]
    ending_ctx: Dict[str, Any]
    letters_ctx: Dict[str, Any]
    metadata: Dict[str, Any]


# ============================================================================
# Private Helper Functions
# ============================================================================

def _prepare_all_context(item: Dict[str, Any]) -> VideoRenderingContext:
    """Prepare all rendering context data upfront.

    Gathers all necessary data for video rendering:
    - Layout computation (bboxes for all elements)
    - Timeline calculation (timing for countdown, reveal, etc.)
    - Entry/ending video contexts
    - Letters resource contexts
    - Metadata (video size, fps, etc.)

    Args:
        item: JSON configuration dict (must pass schema validation)

    Returns:
        VideoRenderingContext with all computed data

    Raises:
        ValueError: If item fails validation
        FileNotFoundError: If required assets missing (unless dry_run)

    Example:
        >>> item = {"letters": "C c", "word_en": "Cat", "word_zh": "貓", ...}
        >>> ctx = _prepare_all_context(item)
        >>> assert "letters_bbox" in ctx.layout
    """
    # Import context_builder functions
    from spellvid.application.context_builder import (
        prepare_entry_context,
        prepare_ending_context,
        prepare_letters_context,
    )

    # Set defaults for optional fields
    if "countdown_sec" not in item:
        item["countdown_sec"] = 10
    if "reveal_hold_sec" not in item:
        item["reveal_hold_sec"] = 5

    # Validate required fields
    required_fields = [
        "letters", "word_en", "word_zh", "image_path", "music_path"
    ]
    missing = [f for f in required_fields if f not in item]
    if missing:
        raise ValueError(
            f"Missing required fields: {', '.join(missing)}"
        )

    # Convert item dict to VideoConfig for layout computation
    from spellvid.shared.types import VideoConfig as VC
    config = VC(
        letters=item["letters"],
        word_en=item["word_en"],
        word_zh=item["word_zh"],
        image_path=item.get("image_path", ""),
        music_path=item.get("music_path", ""),
        countdown_sec=int(item.get("countdown_sec", 10)),
        reveal_hold_sec=int(item.get("reveal_hold_sec", 5)),
    )

    # Compute layout
    layout_result = compute_layout_bboxes(config)
    layout = layout_result.to_dict()

    # Compute timeline
    per_letter_time = 1.0
    word_en = item.get("word_en", "")
    reveal_time = len(word_en) * per_letter_time
    countdown = int(item.get("countdown_sec", 10))
    reveal_hold = int(item.get("reveal_hold_sec", 5))
    main_duration = countdown + reveal_time + reveal_hold

    timeline = {
        "countdown_start": 0.0,
        "countdown_end": float(countdown),
        "reveal_start": float(countdown),
        "reveal_end": float(countdown + reveal_time),
        "hold_start": float(countdown + reveal_time),
        "hold_end": main_duration,
        "total_duration": main_duration,
    }

    # Prepare entry context
    entry_ctx = prepare_entry_context(item)

    # Prepare ending context
    ending_ctx = prepare_ending_context(item)

    # Prepare letters context
    letters_ctx = prepare_letters_context(item)

    # Prepare metadata
    metadata = {
        "video_size": (1920, 1080),  # CANVAS_WIDTH, CANVAS_HEIGHT
        "fps": 24,
        "bg_color": (255, 250, 233),  # COLOR_WHITE
        "main_duration": main_duration,
    }

    return VideoRenderingContext(
        item=item,
        layout=layout,
        timeline=timeline,
        entry_ctx=entry_ctx,
        ending_ctx=ending_ctx,
        letters_ctx=letters_ctx,
        metadata=metadata,
    )


def _create_background_clip(ctx: VideoRenderingContext) -> Any:
    """Create background clip (image or solid color).

    Creates either:
    - Image/video background (if image_path present)
    - Solid color background (if no image)

    Args:
        ctx: VideoRenderingContext with item and metadata

    Returns:
        MoviePy Clip (ImageClip, VideoFileClip, or ColorClip)

    Raises:
        FileNotFoundError: If image_path specified but not found
        RuntimeError: If clip creation fails

    Example:
        >>> ctx = _prepare_all_context(item)
        >>> bg_clip = _create_background_clip(ctx)
        >>> assert bg_clip.duration == ctx.timeline["total_duration"]
    """
    # Import MoviePy (try editor first, fall back to top-level)
    mpy = None
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        try:
            import moviepy as mpy  # type: ignore
        except ImportError:
            raise RuntimeError("MoviePy not available")

    duration = ctx.timeline["total_duration"]
    video_size = ctx.metadata["video_size"]
    bg_color = ctx.metadata["bg_color"]

    # Always create base color clip
    bg_clip = mpy.ColorClip(
        size=video_size,
        color=bg_color,
        duration=duration
    )

    # If image/video provided, load and overlay
    img_path = ctx.item.get("image_path", "")
    if img_path and os.path.exists(img_path):
        img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
        vid_exts = (".mp4", ".mov", ".mkv", ".avi", ".webm")

        if img_path.lower().endswith(img_exts):
            # Static image - load with Pillow and create ImageClip
            from PIL import Image as PILImage
            import numpy as np

            pil_img = PILImage.open(img_path).convert("RGBA")
            # Scale to fit centered region (70% of canvas)
            square_size = int(min(video_size) * 0.7)
            w0, h0 = pil_img.size
            scale = min(square_size / w0, square_size / h0)
            new_w = max(1, int(w0 * scale))
            new_h = max(1, int(h0 * scale))
            pil_img = pil_img.resize((new_w, new_h), PILImage.LANCZOS)

            arr = np.array(pil_img)
            img_clip = mpy.ImageClip(arr, duration=duration)

            # Center the image
            img_clip = img_clip.with_position(("center", "center"))

            # Composite: background + centered image
            bg_clip = mpy.CompositeVideoClip([bg_clip, img_clip])

        elif img_path.lower().endswith(vid_exts):
            # Video file - load as VideoFileClip
            vid_clip = mpy.VideoFileClip(img_path)

            # Get video mode (cover/contain)
            video_mode = ctx.item.get("video_mode", "cover")

            if video_mode == "cover":
                # Scale to cover entire canvas
                vid_w, vid_h = vid_clip.size
                canvas_w, canvas_h = video_size
                scale_w = canvas_w / vid_w
                scale_h = canvas_h / vid_h
                scale = max(scale_w, scale_h)
                vid_clip = vid_clip.resized(scale)
                vid_clip = vid_clip.with_position(("center", "center"))
            else:
                # Contain mode - fit within canvas
                vid_w, vid_h = vid_clip.size
                canvas_w, canvas_h = video_size
                scale_w = canvas_w / vid_w
                scale_h = canvas_h / vid_h
                scale = min(scale_w, scale_h)
                vid_clip = vid_clip.resized(scale)
                vid_clip = vid_clip.with_position(("center", "center"))

            # Loop video if shorter than duration
            if vid_clip.duration < duration:
                vid_clip = vid_clip.loop(duration=duration)
            else:
                vid_clip = vid_clip.subclipped(0, duration)

            # Composite: background + video
            bg_clip = mpy.CompositeVideoClip([bg_clip, vid_clip])

    return bg_clip


def _render_letters_layer(ctx: VideoRenderingContext) -> Any:
    """Render letter images in top-left.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with letters_ctx and layout

    Returns:
        MoviePy CompositeVideoClip with positioned letter images
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Load letter images from letters_ctx
    # TODO: Position according to layout["letters"]
    # TODO: Create composite clip

    # Stub: return empty clip for now
    return mpy.ColorClip(size=(1, 1), color=(0, 0, 0), duration=1.0)


def _render_chinese_zhuyin_layer(ctx: VideoRenderingContext) -> Any:
    """Render Chinese text + Zhuyin annotations in top-right.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with item (word_zh) and layout

    Returns:
        MoviePy ImageClip with rendered text
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Parse zhuyin from word_zh
    # TODO: Render Chinese + zhuyin using Pillow
    # TODO: Position according to layout["word_zh"]

    # Stub: return empty clip
    return mpy.ColorClip(size=(1, 1), color=(0, 0, 0), duration=1.0)


def _render_timer_layer(ctx: VideoRenderingContext) -> Any:
    """Render countdown timer in top-left corner.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with timeline (countdown_sec)

    Returns:
        MoviePy Clip with dynamic countdown text
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Create timer clips for each second
    # TODO: Position according to layout["timer"]

    # Stub: return empty clip
    return mpy.ColorClip(size=(1, 1), color=(0, 0, 0), duration=1.0)


def _render_reveal_layer(ctx: VideoRenderingContext) -> Any:
    """Render word reveal animation (typing effect) in bottom center.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with item (word_en) and timeline

    Returns:
        MoviePy Clip with typing animation
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Create reveal animation clips
    # TODO: Add underlines
    # TODO: Position according to layout["reveal"]

    # Stub: return empty clip
    return mpy.ColorClip(size=(1, 1), color=(0, 0, 0), duration=1.0)


def _render_progress_bar_layer(ctx: VideoRenderingContext) -> Any:
    """Render progress bar at bottom of video.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with timeline (total_duration)

    Returns:
        MoviePy Clip with animated progress bar
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Create progress bar segments
    # TODO: Position at bottom

    # Stub: return empty clip
    return mpy.ColorClip(size=(1, 1), color=(0, 0, 0), duration=1.0)


def _process_audio_tracks(ctx: VideoRenderingContext) -> Any:
    """Mix background music + countdown beeps.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with item (music_path) and timeline

    Returns:
        MoviePy AudioClip (mixed audio)
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Load music file
    # TODO: Generate beeps
    # TODO: Mix audio tracks

    # Stub: return silent audio
    from moviepy.audio.AudioClip import AudioClip
    return AudioClip(lambda t: [0, 0], duration=ctx.timeline["total_duration"])


def _load_entry_ending_clips(
    ctx: VideoRenderingContext
) -> tuple[Optional[Any], Optional[Any]]:
    """Load optional entry and ending video clips.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with entry_ctx and ending_ctx

    Returns:
        Tuple of (entry_clip, ending_clip) - either or both may be None
    """
    # TODO: Load entry video if enabled
    # TODO: Load ending video if enabled

    # Stub: return None for both
    return (None, None)


def validate_context(ctx: VideoRenderingContext) -> bool:
    """Validate that VideoRenderingContext has all required fields.

    Args:
        ctx: VideoRenderingContext to validate

    Returns:
        True if valid

    Raises:
        ValueError: If ctx missing required fields or invalid
    """
    # Check required fields
    if not ctx.item:
        raise ValueError("Context missing item")
    if not ctx.layout:
        raise ValueError("Context missing layout")
    if not ctx.timeline:
        raise ValueError("Context missing timeline")

    return True


def validate_layer(layer: Any) -> bool:
    """Validate that a layer implementation satisfies Layer protocol.

    Args:
        layer: Object to validate

    Returns:
        True if valid

    Raises:
        TypeError: If layer doesn't satisfy Layer protocol
    """
    # Check required methods
    if not hasattr(layer, 'render'):
        raise TypeError("Layer must have render() method")
    if not hasattr(layer, 'get_bbox'):
        raise TypeError("Layer must have get_bbox() method")
    if not hasattr(layer, 'get_duration'):
        raise TypeError("Layer must have get_duration() method")

    return True


def validate_composer(composer: Any) -> bool:
    """Validate that a composer satisfies IVideoComposer protocol.

    Args:
        composer: Object to validate

    Returns:
        True if valid

    Raises:
        TypeError: If composer doesn't satisfy IVideoComposer protocol
    """
    # Check required methods
    if not hasattr(composer, 'compose_layers'):
        raise TypeError("Composer must have compose_layers() method")
    if not hasattr(composer, 'export'):
        raise TypeError("Composer must have export() method")

    return True


def _compose_and_export(
    ctx: VideoRenderingContext,
    layers: list[Any],
    audio: Any,
    output_path: str,
    composer: Optional[IVideoComposer] = None
) -> None:
    """Combine all layers + audio and export to MP4.

    TODO: Extract full implementation from render_video_moviepy

    Args:
        ctx: VideoRenderingContext with metadata
        layers: List of MoviePy Clips (background, letters, etc.)
        audio: MoviePy AudioClip
        output_path: Output MP4 file path
        composer: IVideoComposer implementation (None = default MoviePy)

    Side Effects:
        Writes MP4 file to output_path
    """
    # Import MoviePy
    try:
        from moviepy import editor as mpy  # type: ignore
    except (ImportError, AttributeError):
        import moviepy as mpy  # type: ignore

    # TODO: Composite all layers
    # TODO: Set audio
    # TODO: Export to file

    # Stub: create simple composite and export
    if layers:
        final_clip = mpy.CompositeVideoClip(layers)
        if audio:
            final_clip = final_clip.with_audio(audio)

        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Export (simplified)
        final_clip.write_videofile(
            output_path,
            fps=ctx.metadata.get("fps", 24),
            codec="libx264",
            audio_codec="aac"
        )


# ============================================================================
# Public API
# ============================================================================


def render_video(
    item: Dict[str, Any] | None = None,
    output_path: str = "",
    dry_run: bool = False,
    skip_ending: bool = False,
    composer: Optional[IVideoComposer] = None,
    config: Optional[VideoConfig] = None,  # Backward compatibility
) -> Dict[str, Any]:
    """Orchestrate complete video rendering pipeline.

    New implementation that delegates to 11 specialized sub-functions,
    replacing the monolithic render_video_moviepy (~1,630 lines).

    Args:
        item: JSON configuration dict (see SCHEMA in shared.validation)
        output_path: Output MP4 file path
        dry_run: If True, only compute metadata without rendering
        skip_ending: If True, omit ending video (for batch processing)
        composer: IVideoComposer implementation (None = default MoviePy)
        config: VideoConfig object (DEPRECATED, use item dict instead)

    Returns:
        Rendering result dict:
        - success: bool
        - duration: float (total duration)
        - output_path: str
        - metadata: dict (layout, resources, timing)

    Raises:
        ValueError: Invalid item configuration
        FileNotFoundError: Required assets missing (when dry_run=False)
        RuntimeError: Rendering failure

    Example:
        >>> item = {
        ...     "letters": "I i",
        ...     "word_en": "Ice",
        ...     "word_zh": "冰",
        ...     "image_path": "assets/ice.png",
        ...     "music_path": "assets/ice.mp3",
        ... }
        >>> result = render_video(item, "out/ice.mp4", dry_run=True)
        >>> result["success"]
        True
    """
    # Backward compatibility: convert VideoConfig to dict
    if config is not None and item is None:
        item = {
            "letters": config.letters,
            "word_en": config.word_en,
            "word_zh": config.word_zh,
            "image_path": config.image_path,
            "music_path": config.music_path,
            "countdown_sec": config.countdown_sec,
            "reveal_hold_sec": config.reveal_hold_sec,
        }
    
    if item is None:
        raise ValueError(
            "Either 'item' dict or 'config' VideoConfig must be provided"
        )
    
    # Step 1: Prepare all context data upfront
    # (layout, timeline, entry/ending/letters contexts, metadata)
    ctx = _prepare_all_context(item)

    # Dry-run mode: return metadata without rendering
    if dry_run:
        return {
            "success": True,
            "duration": ctx.timeline["total_duration"],
            "output_path": output_path,
            "metadata": {
                "layout": ctx.layout,
                "timeline": ctx.timeline,
                "config": ctx.item,
            },
            "status": "dry-run",
        }

    # Step 2: Create background clip (image/video or solid color)
    bg_clip = _create_background_clip(ctx)

    # Step 3: Render letters layer (top-left letter images)
    letters_clip = _render_letters_layer(ctx)

    # Step 4: Render Chinese + Zhuyin layer (top-right)
    chinese_clip = _render_chinese_zhuyin_layer(ctx)

    # Step 5: Render timer layer (countdown in top-left corner)
    timer_clip = _render_timer_layer(ctx)

    # Step 6: Render reveal layer (typing animation in bottom center)
    reveal_clip = _render_reveal_layer(ctx)

    # Step 7: Render progress bar layer (bottom of video)
    progress_clip = _render_progress_bar_layer(ctx)

    # Step 8: Process audio tracks (music + countdown beeps)
    audio_clip = _process_audio_tracks(ctx)

    # Step 9: Load optional entry and ending clips
    entry_clip, ending_clip = _load_entry_ending_clips(ctx)

    # Step 10: Collect all layers for composition
    layers = [bg_clip]

    # Add main content layers (only if not stub clips)
    if letters_clip and hasattr(letters_clip, 'size'):
        if letters_clip.size != (1, 1):  # Skip stub clips
            layers.append(letters_clip)

    if chinese_clip and hasattr(chinese_clip, 'size'):
        if chinese_clip.size != (1, 1):
            layers.append(chinese_clip)

    if timer_clip and hasattr(timer_clip, 'size'):
        if timer_clip.size != (1, 1):
            layers.append(timer_clip)

    if reveal_clip and hasattr(reveal_clip, 'size'):
        if reveal_clip.size != (1, 1):
            layers.append(reveal_clip)

    if progress_clip and hasattr(progress_clip, 'size'):
        if progress_clip.size != (1, 1):
            layers.append(progress_clip)

    # Step 11: Compose and export final video
    _compose_and_export(ctx, layers, audio_clip, output_path, composer)

    return {
        "success": True,
        "duration": ctx.timeline["total_duration"],
        "output_path": output_path,
        "metadata": {
            "layout": ctx.layout,
            "timeline": ctx.timeline,
            "config": ctx.item,
        },
        "status": "rendered",
    }


def _validate_resources(config: VideoConfig) -> Dict[str, Any]:
    """驗證資源檔案是否存在

    Args:
        config: 視頻配置

    Returns:
        驗證結果字典
    """
    result = {
        "all_present": True,
        "image": {"exists": False, "path": config.image_path},
        "music": {"exists": False, "path": config.music_path},
    }

    if config.image_path:
        result["image"]["exists"] = Path(config.image_path).exists()
        if not result["image"]["exists"]:
            result["all_present"] = False

    if config.music_path:
        result["music"]["exists"] = Path(config.music_path).exists()
        if not result["music"]["exists"]:
            result["all_present"] = False

    return result
