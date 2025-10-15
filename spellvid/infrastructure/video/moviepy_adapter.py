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
