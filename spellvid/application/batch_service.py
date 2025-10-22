"""批次處理服務

此模組提供批次視頻渲染服務,管理多支視頻的渲染流程。

主要功能:
- render_batch(): 批次渲染多支視頻
- 失敗處理:單支失敗不中斷批次
- 片尾管理:最後一支視頻才加片尾
"""

import os
from typing import Any, Dict, List

from spellvid.shared.types import VideoConfig
from spellvid.application.video_service import render_video


def render_batch(
    configs: List[VideoConfig],
    output_dir: str,
    dry_run: bool = False,
    entry_hold: float = 0.0,
    skip_ending_per_video: bool = True,
) -> Dict[str, Any]:
    """批次渲染多支視頻

    按順序渲染多支視頻,單支失敗不中斷批次處理。

    Args:
        configs: VideoConfig 列表
        output_dir: 輸出目錄
        dry_run: True 則僅計算 metadata 不渲染
        entry_hold: 片頭保留時間(秒)
        skip_ending_per_video: True 則只有最後一支視頻有片尾

    Returns:
        批次結果摘要:
        - total: int (總數)
        - success: int (成功數)
        - failed: int (失敗數)
        - results: List[dict] (每支視頻結果)

    Raises:
        FileNotFoundError: 輸出目錄不存在且無法建立

    Example:
        >>> configs = [
        ...     VideoConfig(letters="A a", word_en="Apple", word_zh="蘋果"),
        ...     VideoConfig(letters="B b", word_en="Ball", word_zh="球"),
        ... ]
        >>> result = render_batch(configs, "out/", dry_run=True)
        >>> result["total"]
        2
    """
    # 驗證參數
    if not configs:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "results": [],
            "status": "empty",
        }

    # 建立輸出目錄
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        raise FileNotFoundError(
            f"Cannot create output dir: {output_dir}"
        ) from e

    # 批次處理
    results: List[Dict[str, Any]] = []
    success_count = 0
    failed_count = 0

    for idx, config in enumerate(configs):
        # 決定是否跳過片尾
        is_last = (idx == len(configs) - 1)
        skip_ending = (not is_last) if skip_ending_per_video else False

        # 建立輸出路徑
        output_filename = f"{config.word_en}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        try:
            # 渲染視頻
            result = render_video(
                config=config,
                output_path=output_path,
                dry_run=dry_run,
                skip_ending=skip_ending,
            )

            result["index"] = idx
            result["config"] = {
                "word_en": config.word_en,
                "word_zh": config.word_zh,
                "letters": config.letters,
            }
            results.append(result)

            if result.get("success", False):
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            # 單支失敗不中斷批次
            failed_count += 1
            results.append({
                "success": False,
                "index": idx,
                "output_path": output_path,
                "error": str(e),
                "config": {
                    "word_en": config.word_en,
                    "word_zh": config.word_zh,
                    "letters": config.letters,
                },
            })

    return {
        "total": len(configs),
        "success": success_count,
        "failed": failed_count,
        "results": results,
        "status": "completed",
    }


def concatenate_videos_with_transitions(
    video_paths: List[str],
    output_path: str,
    fade_in_duration: float = None,
    apply_audio_fadein: bool = False,
) -> Dict[str, Any]:
    """拼接多支視頻並添加轉場效果

    載入多個視頻檔案,為除第一支外的視頻添加淡入效果,並拼接為單一輸出。
    每支輸入視頻應已在渲染階段套用淡出效果。

    Args:
        video_paths: 待拼接的視頻檔案路徑列表(按順序)
        output_path: 最終拼接輸出視頻的路徑
        fade_in_duration: 淡入時長(秒)。None 則使用預設值 1.0s
        apply_audio_fadein: True 則同時對音訊套用淡入(Phase 3 功能)

    Returns:
        狀態資訊字典:
        - status: "ok" | "error" | "skipped"
        - message: 錯誤訊息(若 status 為 "error")
        - output: 輸出檔案路徑(若成功)
        - clips_count: 拼接的片段數量
        - total_duration: 拼接視頻總時長

    Decision References:
        - D1: 所有視頻都有淡出(在渲染時套用)
        - D2: 第一支視頻不淡入;後續視頻有 1s 淡入
        - D4: 音訊淡入由 apply_audio_fadein 參數控制

    Example:
        >>> paths = ["out/word1.mp4", "out/word2.mp4", "out/word3.mp4"]
        >>> result = concatenate_videos_with_transitions(
        ...     paths, "out/batch.mp4", fade_in_duration=1.0
        ... )
        >>> result["status"]
        'ok'
        >>> result["clips_count"]
        3
    """
    # Import MoviePy and constants
    try:
        import moviepy.editor as mpy
        _HAS_MOVIEPY = True
    except ImportError:
        _HAS_MOVIEPY = False

    from spellvid.shared.constants import FADE_IN_DURATION
    from spellvid.infrastructure.video.effects import (
        apply_fadein_effect
    )

    if not _HAS_MOVIEPY:
        return {
            "status": "error",
            "message": "MoviePy not available for video concatenation"
        }

    if not video_paths:
        return {
            "status": "error",
            "message": "No video paths provided for concatenation"
        }

    if fade_in_duration is None:
        fade_in_duration = FADE_IN_DURATION

    clips = []
    cleanup_clips = []

    try:
        # Load and process each video
        for idx, path in enumerate(video_paths):
            if not os.path.exists(path):
                # Clean up already loaded clips
                for clip in cleanup_clips:
                    try:
                        clip.close()
                    except Exception:
                        pass
                return {
                    "status": "error",
                    "message": f"Video file not found: {path}"
                }

            try:
                # Load video clip
                clip = mpy.VideoFileClip(path)
                cleanup_clips.append(clip)

                # D2 Decision: First video does not fade in
                if idx == 0:
                    # First video: use as-is (already has fade-out)
                    clips.append(clip)
                else:
                    # Subsequent videos: apply fade-in
                    clip_with_fadein = apply_fadein_effect(
                        clip,
                        duration=fade_in_duration,
                        apply_audio=apply_audio_fadein
                    )
                    clips.append(clip_with_fadein)

            except Exception as e:
                # Clean up on error
                for clip in cleanup_clips:
                    try:
                        clip.close()
                    except Exception:
                        pass
                return {
                    "status": "error",
                    "message": f"Failed to load video {path}: {str(e)}"
                }

        # Concatenate all clips
        try:
            final_clip = mpy.concatenate_videoclips(clips, method="compose")
        except Exception:
            # Fallback to default method if 'compose' fails
            try:
                final_clip = mpy.concatenate_videoclips(clips)
            except Exception as e:
                # Clean up
                for clip in cleanup_clips:
                    try:
                        clip.close()
                    except Exception:
                        pass
                return {
                    "status": "error",
                    "message": f"Failed to concatenate videos: {str(e)}"
                }

        total_duration = float(getattr(final_clip, "duration", 0) or 0)

        # Write output video
        try:
            # Create output directory if needed
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # Use ffmpeg settings similar to render_video_moviepy
            ffmpeg_exe = os.environ.get("IMAGEIO_FFMPEG_EXE")
            if ffmpeg_exe:
                final_clip.write_videofile(
                    output_path,
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    threads=4,
                    preset="medium",
                )
            else:
                # Fallback: simple call
                final_clip.write_videofile(output_path, fps=30)

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to write output video: {str(e)}"
            }

        finally:
            # Clean up all clips
            try:
                final_clip.close()
            except Exception:
                pass

            for clip in cleanup_clips:
                try:
                    clip.close()
                except Exception:
                    pass

        return {
            "status": "ok",
            "output": output_path,
            "clips_count": len(clips),
            "total_duration": total_duration,
        }

    except Exception as e:
        # Catch-all error handler
        for clip in cleanup_clips:
            try:
                clip.close()
            except Exception:
                pass

        return {
            "status": "error",
            "message": f"Unexpected error during concatenation: {str(e)}"
        }
