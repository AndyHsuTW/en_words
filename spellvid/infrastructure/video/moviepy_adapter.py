"""MoviePy 適配器實作

此模組實作 IVideoComposer Protocol,封裝 MoviePy 框架的視頻合成功能。

設計原則:
- 適配器模式:將 MoviePy 的 API 轉換為我們的 IVideoComposer 介面
- 依賴注入:不直接依賴 MoviePy 全域狀態,可測試性高
- 錯誤處理:將 MoviePy 的異常轉換為我們的業務異常

MoviePy 依賴:
    pip install moviepy

Example:
    >>> from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter
    >>> composer = MoviePyAdapter()
    >>> clip = composer.create_color_clip((1920, 1080), (255, 250, 233), 5.0)
    >>> composer.render_to_file(clip, "output.mp4")
"""

from typing import Any, List, Tuple
import numpy as np

# MoviePy imports (v2.x uses different import paths)
try:
    from moviepy import (
        ColorClip,
        ImageClip,
        VideoFileClip,
        CompositeVideoClip,
        concatenate_videoclips,
        vfx,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class MoviePyAdapter:
    """MoviePy 框架適配器

    實作 IVideoComposer Protocol,提供視頻合成功能。

    Attributes:
        默認無狀態,每個方法獨立運作

    Raises:
        ImportError: 如果 MoviePy 未安裝
    """

    def __init__(self):
        """初始化 MoviePy 適配器

        Raises:
            ImportError: MoviePy 未安裝時拋出
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "MoviePy 未安裝。請執行: pip install moviepy"
            )

    def create_color_clip(
        self,
        size: Tuple[int, int],
        color: Tuple[int, int, int],
        duration: float
    ) -> Any:
        """建立純色背景 Clip

        Args:
            size: (width, height) 畫布尺寸
            color: (R, G, B) 顏色值
            duration: 持續時間(秒)

        Returns:
            ColorClip 物件

        Example:
            >>> clip = adapter.create_color_clip((1920, 1080), (255, 250, 233), 5.0)
            >>> clip.duration
            5.0
        """
        return ColorClip(size=size, color=color, duration=duration)

    def create_image_clip(
        self,
        image_array: np.ndarray,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立圖片 Clip

        Args:
            image_array: NumPy 陣列 (H, W, C)
            duration: Clip 持續時間
            position: (x, y) 位置

        Returns:
            ImageClip 物件

        Example:
            >>> img = np.zeros((100, 200, 3), dtype=np.uint8)
            >>> clip = adapter.create_image_clip(img, 3.0, (50, 50))
        """
        clip = ImageClip(image_array, duration=duration)
        clip = clip.with_position(position)
        return clip

    def create_video_clip(
        self,
        video_path: str,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立視頻 Clip

        Args:
            video_path: 視頻檔案路徑
            duration: 目標持續時間
            position: (x, y) 位置

        Returns:
            VideoFileClip 物件

        Raises:
            FileNotFoundError: 視頻檔案不存在
        """
        try:
            clip = VideoFileClip(video_path)
        except (IOError, OSError) as e:
            raise FileNotFoundError(f"視頻檔案不存在: {video_path}") from e

        # 裁切或循環至目標時長
        if clip.duration > duration:
            clip = clip.subclip(0, duration)
        elif clip.duration < duration:
            # 循環播放至目標時長
            num_loops = int(np.ceil(duration / clip.duration))
            clip = concatenate_videoclips([clip] * num_loops)
            clip = clip.subclip(0, duration)

        clip = clip.with_position(position)
        return clip

    def compose_clips(
        self,
        clips: List[Any],
        size: Tuple[int, int] = (1920, 1080)
    ) -> Any:
        """組合多個 Clips

        Args:
            clips: Clip 列表(底層在前)
            size: 畫布尺寸

        Returns:
            CompositeVideoClip 物件

        Example:
            >>> bg = adapter.create_color_clip((1920, 1080), (255, 255, 255), 5.0)
            >>> fg = adapter.create_image_clip(img, 5.0, (100, 100))
            >>> composed = adapter.compose_clips([bg, fg])
        """
        return CompositeVideoClip(clips, size=size)

    def apply_fadeout(
        self,
        clip: Any,
        duration: float
    ) -> Any:
        """對 Clip 套用淡出效果

        Args:
            clip: 要處理的 Clip
            duration: 淡出持續時間(秒)

        Returns:
            套用淡出後的 Clip

        Example:
            >>> clip = adapter.create_color_clip((1920, 1080), (255, 0, 0), 10.0)
            >>> faded = adapter.apply_fadeout(clip, 3.0)
            >>> faded.duration
            10.0
        """
        return clip.with_effects([vfx.FadeOut(duration)])

    def render_to_file(
        self,
        clip: Any,
        output_path: str,
        fps: int = 30,
        codec: str = "libx264"
    ) -> None:
        """將 Clip 渲染為視頻檔案

        Args:
            clip: 要渲染的 Clip
            output_path: 輸出檔案路徑
            fps: 影格率
            codec: 視頻編碼器

        Raises:
            IOError: 無法寫入檔案
            RuntimeError: 渲染失敗

        Example:
            >>> clip = adapter.compose_clips([bg, fg])
            >>> adapter.render_to_file(clip, "output.mp4", fps=30)
        """
        try:
            clip.write_videofile(
                output_path,
                fps=fps,
                codec=codec,
                audio=False,  # 音訊由 IMediaProcessor 處理
                logger=None,  # 關閉 MoviePy 預設日誌
            )
        except (IOError, OSError) as e:
            raise IOError(f"無法寫入輸出檔案: {output_path}") from e
        except Exception as e:
            raise RuntimeError(f"視頻渲染失敗: {e}") from e

    def concatenate_clips(
        self,
        clips: List[Any],
        method: str = "compose"
    ) -> Any:
        """串接多個 Clips

        Args:
            clips: Clip 列表(按播放順序)
            method: 串接方法("compose" 或 "chain")

        Returns:
            串接後的 Clip

        Example:
            >>> clip1 = adapter.create_color_clip((1920, 1080), (255, 0, 0), 3.0)
            >>> clip2 = adapter.create_color_clip((1920, 1080), (0, 255, 0), 3.0)
            >>> combined = adapter.concatenate_clips([clip1, clip2], method="chain")
            >>> combined.duration
            6.0
        """
        if method == "compose":
            return CompositeVideoClip(clips)
        elif method == "chain":
            return concatenate_videoclips(clips, method="compose")
        else:
            raise ValueError(f"不支援的串接方法: {method}")


# ============================================================================
# Module-level utility functions for clip manipulation
# ============================================================================

def _ensure_dimensions(clip: Any) -> Any:
    """Ensure clip dimensions are exactly 1920x1080.

    If clip size differs from target, resizes using MoviePy's resized method.
    Silently returns original clip if:
    - Size attribute is missing
    - Size is already 1920x1080
    - Resize operation fails

    Args:
        clip: MoviePy VideoClip object with optional size attribute

    Returns:
        Resized clip (1920x1080) or original clip on error
    """
    try:
        size = getattr(clip, "size", None)
        if size:
            w, h = int(size[0]), int(size[1])
            if (w, h) != (1920, 1080):
                try:
                    clip = clip.resized(new_size=(1920, 1080))
                except Exception:
                    pass
    except Exception:
        pass
    return clip


def _ensure_fullscreen_cover(clip: Any) -> Any:
    """Resize clip to fill 1920x1080 frame without maintaining aspect ratio.

    Always performs non-proportional resize to exact dimensions, stretching
    content to fill the entire frame. Unlike _ensure_dimensions, this function
    guarantees full coverage without letterboxing or pillarboxing.

    Args:
        clip: MoviePy VideoClip object with optional size attribute

    Returns:
        Stretched clip (1920x1080) or original clip on error
    """
    try:
        size = getattr(clip, "size", None)
        if not size:
            return clip
        w, h = float(size[0]), float(size[1])
        if w <= 0 or h <= 0:
            return clip
        target_w, target_h = 1920.0, 1080.0
        # 總是執行非等比例縮放,確保完整畫面無裁剪
        try:
            clip = clip.resized(new_size=(int(target_w), int(target_h)))
        except Exception:
            return clip
    except Exception:
        pass
    return clip


def _auto_letterbox_crop(clip: Any) -> Any:
    """Automatically detect and crop letterbox/pillarbox bars from video clip.

    Samples frames at t=0 and t=duration/2 to detect black/dark bars
    (gray value < 15.0). If bars are found with sufficient content area,
    crops clip to content bounding box with 2-pixel padding.

    Algorithm:
    1. Extract frame at t=0 (and t=duration/2 if duration > 0.5s)
    2. Convert to grayscale (mean across color channels if RGB)
    3. Threshold: pixels with gray > 15.0 are considered content
    4. Find bounding box of valid content pixels
    5. If box is smaller than frame (>2px margins), apply crop
    6. Add 2-pixel padding to prevent edge artifacts

    Args:
        clip: MoviePy VideoClip object with get_frame method

    Returns:
        Cropped clip (content bounding box) or original clip if:
        - Frame extraction fails
        - No valid content detected (all dark)
        - Content already fills frame (no significant bars)
        - Any error occurs during processing

    Raises:
        No exceptions raised - all errors handled silently
    """
    try:
        # Sample frames at start and middle to detect bars
        sample_points = [0.0]
        try:
            dur = float(getattr(clip, "duration", 0.0) or 0.0)
        except Exception:
            dur = 0.0
        if dur > 0.5:
            sample_points.append(max(0.0, dur / 2.0))

        # Try to get a valid frame
        frame = None
        for t in sample_points:
            try:
                frame = clip.get_frame(t)
                if frame is not None:
                    break
            except Exception:
                frame = None
        if frame is None:
            return clip

        # Convert to numpy array and detect content
        arr = np.asarray(frame)
        if arr.ndim == 3:
            # RGB/RGBA - convert to grayscale by averaging channels
            gray = arr.mean(axis=2)
        else:
            # Already grayscale
            gray = arr.astype(float)

        # Threshold: pixels with gray > 15.0 are considered content
        valid = gray > 15.0
        if not valid.any():
            # All pixels are dark - cannot determine content area
            return clip

        # Find bounding box of valid content
        rows = np.where(valid.any(axis=1))[0]
        cols = np.where(valid.any(axis=0))[0]
        if rows.size == 0 or cols.size == 0:
            return clip

        top, bottom = int(rows[0]), int(rows[-1])
        left, right = int(cols[0]), int(cols[-1])

        # Check if content already fills frame (no significant bars)
        if (top <= 2 and left <= 2 and
                bottom >= arr.shape[0] - 3 and right >= arr.shape[1] - 3):
            return clip

        # Add 2-pixel padding to prevent edge artifacts
        pad = 2
        top = max(0, top - pad)
        left = max(0, left - pad)
        bottom = min(arr.shape[0] - 1, bottom + pad)
        right = min(arr.shape[1] - 1, right + pad)

        # Apply crop using MoviePy's cropped method
        # Note: x2/y2 are exclusive, hence +1
        return clip.cropped(
            x1=float(left),
            y1=float(top),
            x2=float(right + 1),
            y2=float(bottom + 1)
        )
    except Exception:
        # Any error during processing - return original clip
        return clip


def _make_fixed_letter_clip(
    letter: str,
    fixed_size: tuple,
    font_size: int = 128,
    color=(0, 0, 0),
    duration: float = None,
    prefer_cjk: bool = False,
):
    """Render a single letter centered on a fixed transparent canvas.

    Creates an ImageClip with a letter centered on a fixed-size transparent
    background. This ensures per-letter clips have identical dimensions,
    preventing layout shifts when letters appear/disappear in animations.

    Implementation delegates to the Pillow adapter's _make_text_imageclip
    which handles the actual rendering with fixed_size parameter.

    Args:
        letter: Single character to render
        fixed_size: (width, height) tuple for canvas dimensions
        font_size: Font size in pixels (default: 128)
        color: RGB tuple for text color (default: black (0,0,0))
        duration: Clip duration in seconds (None = image clip)
        prefer_cjk: If True, prefer CJK fonts over Western fonts

    Returns:
        MoviePy ImageClip with letter centered on fixed-size canvas

    Example:
        >>> clip = _make_fixed_letter_clip('A', (200, 200), font_size=96)
        >>> clip.size
        (200, 200)
    """
    # Import here to avoid circular dependency
    from spellvid.infrastructure.rendering.pillow_adapter import (
        _make_text_imageclip
    )

    return _make_text_imageclip(
        text=letter,
        font_size=font_size,
        color=color,
        duration=duration,
        prefer_cjk=prefer_cjk,
        extra_bottom=0,
        fixed_size=fixed_size,
    )


def _create_placeholder_mp4_with_ffmpeg(out_path: str) -> bool:
    """Create a minimal valid MP4 file using FFmpeg.

    Generates a 1-second white frame video (1920x1080) encoded with H.264.
    Uses Pillow to create the frame and FFmpeg for encoding.

    This is useful for creating placeholder videos or testing video pipelines
    without requiring actual video content. The output uses faststart flag
    to ensure the moov atom is at file start for web streaming compatibility.

    Args:
        out_path: Absolute path for output MP4 file

    Returns:
        True if MP4 was successfully created, False otherwise

    Raises:
        No exceptions raised - all errors handled silently and return False

    Technical details:
        - Frame: 1920x1080 white RGB (255,255,255)
        - Duration: 1 second
        - Codec: libx264 with yuv420p pixel format
        - Flags: +faststart for web optimization
        - FFmpeg resolution: Checks IMAGEIO_FFMPEG_EXE env var, then PATH

    Example:
        >>> success = _create_placeholder_mp4_with_ffmpeg("test.mp4")
        >>> if success:
        ...     print("Placeholder created successfully")
    """
    import os
    import shutil
    import subprocess
    import tempfile

    try:
        # Locate FFmpeg executable
        ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE") or shutil.which("ffmpeg")
        if not ffmpeg:
            return False

        # Create a single white frame PNG and encode to mp4
        # (use +faststart to ensure moov atom is at file start)
        with tempfile.TemporaryDirectory() as td:
            png = os.path.join(td, "frame.png")
            try:
                from PIL import Image

                img = Image.new("RGB", (1920, 1080), (255, 255, 255))
                img.save(png, "PNG")
            except Exception:
                return False

            cmd = [
                ffmpeg,
                "-y",  # Overwrite output file
                "-loop",
                "1",  # Loop input
                "-i",
                png,  # Input frame
                "-t",
                "1",  # Duration 1 second
                "-vf",
                "scale=1920:1080",  # Ensure resolution
                "-c:v",
                "libx264",  # H.264 codec
                "-pix_fmt",
                "yuv420p",  # Standard pixel format
                "-movflags",
                "+faststart",  # Web optimization
                out_path,
            ]
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return True
    except Exception:
        return False
