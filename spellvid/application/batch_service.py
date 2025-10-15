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
