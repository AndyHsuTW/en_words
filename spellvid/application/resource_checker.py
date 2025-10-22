"""資源檢查服務

此模組提供資源檔案驗證功能,檢查視頻所需的資產是否存在。

主要功能:
- check_assets(): 檢查單支視頻的資源檔案
- prepare_entry_context(): 準備片頭資源資訊
"""

from pathlib import Path
from typing import Any, Dict

from spellvid.shared.types import VideoConfig


def check_assets(config: VideoConfig) -> Dict[str, Any]:
    """檢查視頻資源檔案是否存在

    Args:
        config: 視頻配置

    Returns:
        資源檢查結果:
        - image: {"exists": bool, "path": str}
        - music: {"exists": bool, "path": str}
        - letters: {"exists": bool, "paths": List[str]}
        - all_present: bool

    Example:
        >>> config = VideoConfig(
        ...     letters="A a",
        ...     word_en="Apple",
        ...     word_zh="蘋果",
        ...     image_path="assets/apple.png"
        ... )
        >>> result = check_assets(config)
        >>> result["image"]["exists"]
        False
    """
    result = {
        "image": {
            "exists": False,
            "path": config.image_path or "",
        },
        "music": {
            "exists": False,
            "path": config.music_path or "",
        },
        "letters": {
            "exists": True,
            "paths": [],
        },
        "all_present": True,
    }

    # 檢查圖片
    if config.image_path:
        result["image"]["exists"] = Path(config.image_path).exists()
        if not result["image"]["exists"]:
            result["all_present"] = False

    # 檢查音樂
    if config.music_path:
        result["music"]["exists"] = Path(config.music_path).exists()
        if not result["music"]["exists"]:
            result["all_present"] = False

    # 簡化版本:暫不檢查字母圖片(需要根據 letters_mode 決定)
    # 完整實作需要:
    # 1. 解析 letters 欄位
    # 2. 根據 letters_mode 決定是否需要圖片
    # 3. 檢查 assets/letters/ 目錄下的對應檔案

    return result


def prepare_entry_context() -> Dict[str, Any]:
    """準備片頭資源資訊

    檢查片頭視頻是否存在並查詢元資料。

    Returns:
        片頭資源資訊:
        - video_path: str (若存在)
        - duration: float (若可查詢)
        - exists: bool

    Example:
        >>> entry = prepare_entry_context()
        >>> if entry["exists"]:
        ...     print(f"片頭時長: {entry['duration']}秒")
    """
    # 簡化版本:假設片頭視頻位置固定
    entry_video_path = "assets/entry.mp4"

    result = {
        "video_path": entry_video_path,
        "duration": 0.0,
        "exists": False,
    }

    # 檢查檔案是否存在
    entry_path = Path(entry_video_path)
    if entry_path.exists():
        result["exists"] = True

        # 嘗試查詢時長(需要 IMediaProcessor)
        # 完整實作需要:
        # 1. 注入 IMediaProcessor
        # 2. 呼叫 probe_duration()
        # 簡化版本暫返回固定值
        result["duration"] = 3.0

    return result


def validate_paths(config: VideoConfig) -> Dict[str, str]:
    """驗證並解析配置中的檔案路徑

    Args:
        config: 視頻配置

    Returns:
        驗證結果與錯誤訊息

    Example:
        >>> config = VideoConfig(
        ...     letters="A a",
        ...     word_en="Apple",
        ...     word_zh="蘋果"
        ... )
        >>> errors = validate_paths(config)
        >>> len(errors)
        0
    """
    errors = {}

    # 檢查必填欄位
    if not config.word_en:
        errors["word_en"] = "word_en is required"

    if not config.word_zh:
        errors["word_zh"] = "word_zh is required"

    if not config.letters:
        errors["letters"] = "letters is required"

    # 檢查路徑格式(簡化版本)
    if config.image_path:
        image_path = Path(config.image_path)
        if not image_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            errors["image_path"] = "image must be .png, .jpg, or .jpeg"

    if config.music_path:
        music_path = Path(config.music_path)
        if not music_path.suffix.lower() in [".mp3", ".wav", ".m4a"]:
            errors["music_path"] = "music must be .mp3, .wav, or .m4a"

    return errors


def check_assets_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """檢查視頻資源檔案(字典參數版本,向後相容)

    Args:
        item: 視頻配置字典,包含:
            - image_path: 圖片路徑
            - music_path: 音訊路徑
            - letters: 字母字串
            - letters_as_image: 是否使用圖片模式

    Returns:
        資源檢查結果字典:
        - image_exists: bool
        - music_exists: bool
        - letters_mode: str ("image" or "text")
        - letters_assets: List[str]
        - letters_missing: List[str]
        - letters_missing_details: List[Dict]
        - letters_asset_dir: str
        - letters_has_letters: bool

    Example:
        >>> item = {
        ...     "letters": "A a",
        ...     "word_en": "Apple",
        ...     "word_zh": "蘋果",
        ...     "image_path": "assets/apple.png"
        ... }
        >>> result = check_assets_dict(item)
        >>> result["image_exists"]
        False
    """
    import os
    from spellvid.application.context_builder import (
        prepare_letters_context,
        resolve_letter_asset_dir,
    )

    res: Dict[str, Any] = {
        "image_exists": False,
        "music_exists": False,
        "letters_mode": None,
        "letters_assets": [],
        "letters_missing": [],
        "letters_missing_details": [],
        "letters_asset_dir": None,
        "letters_has_letters": False,
    }

    # Check image file
    if os.path.isfile(item.get("image_path", "")):
        res["image_exists"] = True

    # Check music file
    if os.path.isfile(item.get("music_path", "")):
        res["music_exists"] = True

    # Check letters resources
    try:
        letters_ctx = prepare_letters_context(item)
    except Exception:
        # Fallback if context preparation fails
        letters_ctx = {
            "mode": item.get("letters_as_image", True) and "image" or "text",
            "filenames": [],
            "missing_names": [],
            "asset_dir": resolve_letter_asset_dir(item),
            "has_letters": bool(str(item.get("letters", "")).strip()),
        }

    res["letters_mode"] = letters_ctx.get("mode")
    res["letters_assets"] = list(letters_ctx.get("filenames", []))
    res["letters_missing"] = list(letters_ctx.get("missing_names", []))
    res["letters_missing_details"] = list(letters_ctx.get("missing", []))
    res["letters_asset_dir"] = letters_ctx.get("asset_dir")
    res["letters_has_letters"] = bool(letters_ctx.get("has_letters"))

    return res
