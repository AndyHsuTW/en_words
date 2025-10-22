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
from spellvid.domain.timing import calculate_timeline

# Shared layer imports
from spellvid.shared.types import VideoConfig
from spellvid.shared.constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    COLOR_WHITE,
)

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
# Public API
# ============================================================================


def render_video(
    config: VideoConfig,
    output_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
    composer: Optional[IVideoComposer] = None,
) -> Dict[str, Any]:
    """渲染單支視頻

    協調 domain 層(佈局、注音、時間軸)與 infrastructure 層(視頻組合)
    完成視頻渲染。

    Args:
        config: 視頻配置
        output_path: 輸出檔案路徑
        dry_run: True 則僅計算 metadata 不渲染
        skip_ending: True 則不加入片尾視頻(批次處理用)
        composer: IVideoComposer 實作,None 則使用預設 MoviePy

    Returns:
        渲染結果字典:
        - success: bool
        - duration: float (總時長)
        - output_path: str
        - metadata: dict (佈局、資源資訊)

    Raises:
        FileNotFoundError: 資源檔案不存在(dry_run=False 時)
        RuntimeError: 渲染失敗

    Example:
        >>> config = VideoConfig(
        ...     letters="I i",
        ...     word_en="Ice",
        ...     word_zh="ㄅㄧㄥ 冰"
        ... )
        >>> result = render_video(config, "out/ice.mp4", dry_run=True)
        >>> result["success"]
        True
    """
    # Phase 1: Domain 層計算(不依賴外部資源)
    layout_result = compute_layout_bboxes(config)

    # 計算主視頻時長(簡化版本:countdown + 每字母1秒 + reveal_hold)
    per_letter_time = 1.0
    reveal_time = len(config.word_en) * per_letter_time
    main_duration = config.countdown_sec + reveal_time + config.reveal_hold_sec

    # 計算時間軸
    timeline = calculate_timeline(
        video_duration=main_duration,
        fadeout_duration=0.0,  # 簡化版本暫不處理淡出
    )

    # 計算總時長
    entry_duration = 0.0  # 簡化版本暫不處理片頭
    ending_duration = 0.0 if skip_ending else 0.0  # 簡化版本暫不處理片尾

    total_duration = entry_duration + main_duration + ending_duration

    # 建立 metadata
    metadata = {
        "layout": layout_result.to_dict(),  # 使用 to_dict() 轉換
        "timeline": timeline,
        "config": {
            "letters": config.letters,
            "word_en": config.word_en,
            "word_zh": config.word_zh,
            "countdown_sec": config.countdown_sec,
            "reveal_hold_sec": config.reveal_hold_sec,
        },
        "duration": {
            "entry": entry_duration,
            "main": main_duration,
            "ending": ending_duration,
            "total": total_duration,
        },
    }

    # Dry-run 模式:僅回傳 metadata
    if dry_run:
        return {
            "success": True,
            "duration": total_duration,
            "output_path": output_path,
            "metadata": metadata,
            "status": "dry-run",
        }

    # Phase 2: Infrastructure 層渲染(需要外部資源)
    if composer is None:
        # 使用預設 MoviePy adapter
        from spellvid.infrastructure.video.moviepy_adapter import (
            MoviePyAdapter,
        )
        composer = MoviePyAdapter()

    # 檢查資源檔案(簡化版本:僅檢查必要資源)
    if config.image_path and not Path(config.image_path).exists():
        raise FileNotFoundError(f"Image file not found: {config.image_path}")

    # 建立輸出目錄
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 組裝視頻 clips(簡化版本:僅建立背景)
    # 完整實作需要:
    # 1. 建立背景色 clip
    # 2. 建立圖片 clip
    # 3. 建立文字 clips(letters, word_en, word_zh, zhuyin, timer)
    # 4. 建立進度條 clips
    # 5. 組合所有 clips
    # 6. 套用淡出效果
    # 7. 渲染到檔案

    try:
        # 簡化實作:建立基本背景視頻
        background_clip = composer.create_color_clip(
            size=(CANVAS_WIDTH, CANVAS_HEIGHT),
            color=COLOR_WHITE,
            duration=total_duration,
        )

        # 組合 clips(目前僅背景)
        final_clip = composer.compose_clips(
            clips=[background_clip],
            size=(CANVAS_WIDTH, CANVAS_HEIGHT),
        )

        # 套用淡出效果(簡化版本:跳過)
        # if config.fadeout_sec > 0:
        #     final_clip = composer.apply_fadeout(
        #         clip=final_clip,
        #         duration=config.fadeout_sec,
        #     )

        # 渲染到檔案
        composer.render_to_file(
            clip=final_clip,
            output_path=output_path,
            fps=30,  # 預設 30 fps
            codec="libx264",
        )

        return {
            "success": True,
            "duration": total_duration,
            "output_path": output_path,
            "metadata": metadata,
            "status": "rendered",
        }

    except Exception as e:
        raise RuntimeError(f"Failed to render video: {e}")


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
