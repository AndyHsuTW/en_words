"""上下文構建服務

此模組提供構建視頻渲染所需上下文資訊的函數。

主要功能:
- prepare_entry_context(): 準備片頭視頻上下文
- prepare_ending_context(): 準備片尾視頻上下文
- prepare_letters_context(): 準備字母資源上下文
- resolve_letter_asset_dir(): 解析字母素材目錄路徑
- log_missing_letter_assets(): 記錄缺失的字母素材
"""

import os
from typing import Any, Dict, List, Optional

from spellvid.shared.constants import (
    LETTER_AVAILABLE_WIDTH,
    LETTER_BASE_GAP,
    LETTER_EXTRA_SCALE,
    LETTER_SAFE_X,
    LETTER_TARGET_HEIGHT,
)
from spellvid.infrastructure.media.ffmpeg_wrapper import _probe_media_duration


# ============================================================================
# Constants
# ============================================================================

_DEFAULT_LETTER_ASSET_DIR = os.path.abspath("assets/letters")


# ============================================================================
# Helper Functions
# ============================================================================

def _is_entry_enabled(item: Dict[str, Any] | None = None) -> bool:
    """檢查片頭視頻是否啟用。

    Args:
        item: 視頻配置字典

    Returns:
        True 如果片頭視頻啟用,否則 False

    Note:
        預設為 True,除非明確設為 False
    """
    if item is None:
        return True
    # 檢查 entry_enabled 欄位
    entry_enabled = item.get("entry_enabled")
    if entry_enabled is None:
        return True
    # 強制轉型為布林值
    if isinstance(entry_enabled, bool):
        return entry_enabled
    if isinstance(entry_enabled, str):
        return entry_enabled.lower() not in ("false", "0", "no", "off", "")
    return bool(entry_enabled)


def _is_ending_enabled(item: Dict[str, Any] | None = None) -> bool:
    """檢查片尾視頻是否啟用。

    Args:
        item: 視頻配置字典

    Returns:
        True 如果片尾視頻啟用,否則 False

    Note:
        預設為 True,除非明確設為 False
    """
    if item is None:
        return True
    # 檢查 ending_enabled 欄位
    ending_enabled = item.get("ending_enabled")
    if ending_enabled is None:
        return True
    # 強制轉型為布林值
    if isinstance(ending_enabled, bool):
        return ending_enabled
    if isinstance(ending_enabled, str):
        return ending_enabled.lower() not in ("false", "0", "no", "off", "")
    return bool(ending_enabled)


def _resolve_entry_video_path(item: Dict[str, Any] | None = None) -> str:
    """解析片頭視頻路徑。

    Args:
        item: 視頻配置字典

    Returns:
        片頭視頻檔案路徑 (絕對路徑)

    Note:
        優先順序:
        1. item["entry_video_path"]
        2. 環境變數 SPELLVID_ENTRY_VIDEO_PATH
        3. 預設值 "assets/entry.mp4"
    """
    if item:
        override = item.get("entry_video_path")
        if override:
            return os.path.abspath(str(override))
    # 環境變數
    env_path = os.environ.get("SPELLVID_ENTRY_VIDEO_PATH")
    if env_path:
        return os.path.abspath(env_path)
    # 預設值
    return os.path.abspath("assets/entry.mp4")


def _resolve_ending_video_path(item: Dict[str, Any] | None = None) -> str:
    """解析片尾視頻路徑。

    Args:
        item: 視頻配置字典

    Returns:
        片尾視頻檔案路徑 (絕對路徑)

    Note:
        優先順序:
        1. item["ending_video_path"]
        2. 環境變數 SPELLVID_ENDING_VIDEO_PATH
        3. 預設值 "assets/ending.mp4"
    """
    if item:
        override = item.get("ending_video_path")
        if override:
            return os.path.abspath(str(override))
    # 環境變數
    env_path = os.environ.get("SPELLVID_ENDING_VIDEO_PATH")
    if env_path:
        return os.path.abspath(env_path)
    # 預設值
    return os.path.abspath("assets/ending.mp4")


def _coerce_non_negative_float(
    value: Any, default: float = 0.0
) -> float:
    """強制轉型為非負浮點數。

    Args:
        value: 輸入值
        default: 預設值 (當轉型失敗時)

    Returns:
        非負浮點數

    Example:
        >>> _coerce_non_negative_float("3.5")
        3.5
        >>> _coerce_non_negative_float(-1.0, default=0.0)
        0.0
        >>> _coerce_non_negative_float("invalid", default=1.0)
        1.0
    """
    try:
        result = float(value)
        return max(0.0, result)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any) -> bool:
    """強制轉型為布林值。

    Args:
        value: 輸入值

    Returns:
        布林值

    Note:
        - False 字串: "false", "0", "no", "off", ""
        - True 字串: 其他非空字串
        - None 視為 False
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() not in ("false", "0", "no", "off", "")
    return bool(value)


def _normalize_letters_sequence(letters: str) -> List[str]:
    """正規化字母序列,移除空白字元。

    Args:
        letters: 字母字串

    Returns:
        字母字元列表 (不含空白)

    Example:
        >>> _normalize_letters_sequence("A a B b")
        ['A', 'a', 'B', 'b']
        >>> _normalize_letters_sequence("  ")
        []
    """
    if not letters:
        return []
    seq: List[str] = []
    for ch in letters:
        if not ch or ch.isspace():
            continue
        seq.append(ch)
    return seq


def _letter_asset_filename(ch: str) -> Optional[str]:
    """取得字母對應的素材檔名。

    Args:
        ch: 單一字元

    Returns:
        素材檔名,或 None (如果字元不是字母)

    Example:
        >>> _letter_asset_filename('A')
        'A.png'
        >>> _letter_asset_filename('a')
        'a_small.png'
        >>> _letter_asset_filename(' ')
        None
    """
    if not ch:
        return None
    if ch.isalpha():
        if ch.isupper():
            return f"{ch}.png"
        if ch.islower():
            return f"{ch}_small.png"
    return None


def _letters_missing_names(missing: List[Dict[str, Any]]) -> List[str]:
    """從缺失清單中提取檔名列表。

    Args:
        missing: 缺失素材資訊列表

    Returns:
        缺失素材檔名列表 (去重複)

    Example:
        >>> missing = [
        ...     {"filename": "A.png", "char": "A"},
        ...     {"filename": "a_small.png", "char": "a"},
        ... ]
        >>> _letters_missing_names(missing)
        ['A.png', 'a_small.png']
    """
    names: List[str] = []
    for entry in missing or []:
        name = entry.get("filename") or entry.get("char")
        if name:
            name_str = str(name)
            if name_str not in names:
                names.append(name_str)
    return names


# ============================================================================
# Public API
# ============================================================================

def prepare_entry_context(
    item: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """準備片頭視頻上下文資訊。

    檢查片頭視頻是否存在、查詢時長、計算總前導時間。

    Args:
        item: 視頻配置字典,包含可選的片頭設定:
            - entry_video_path: 片頭視頻路徑
            - entry_enabled: 是否啟用片頭 (預設 True)
            - entry_hold_sec: 片頭結束後保留時間 (秒)

    Returns:
        片頭上下文資訊:
        - path: str (片頭視頻路徑)
        - exists: bool (檔案是否存在)
        - duration_sec: float | None (視頻時長)
        - hold_sec: float (保留時間)
        - total_lead_sec: float (總前導時間 = duration + hold)
        - enabled: bool (是否啟用)

    Example:
        >>> ctx = prepare_entry_context({"entry_hold_sec": 1.0})
        >>> if ctx["exists"]:
        ...     print(f"片頭時長: {ctx['duration_sec']}秒")
        ...     print(f"總前導: {ctx['total_lead_sec']}秒")
    """
    path = _resolve_entry_video_path(item)
    enabled = _is_entry_enabled(item)

    if not enabled:
        return {
            "path": path,
            "exists": False,
            "duration_sec": 0.0,
            "hold_sec": 0.0,
            "total_lead_sec": 0.0,
            "enabled": False,
        }

    exists = os.path.isfile(path)
    hold = _coerce_non_negative_float(
        (item or {}).get("entry_hold_sec"), default=0.0
    )
    duration = _probe_media_duration(path) if exists else None
    total_lead = (duration or 0.0) + hold

    return {
        "path": path,
        "exists": bool(exists),
        "duration_sec": duration,
        "hold_sec": hold,
        "total_lead_sec": total_lead,
        "enabled": True,
    }


def prepare_ending_context(
    item: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """準備片尾視頻上下文資訊。

    檢查片尾視頻是否存在、查詢時長。

    Args:
        item: 視頻配置字典,包含可選的片尾設定:
            - ending_video_path: 片尾視頻路徑
            - ending_enabled: 是否啟用片尾 (預設 True)

    Returns:
        片尾上下文資訊:
        - path: str (片尾視頻路徑)
        - exists: bool (檔案是否存在)
        - duration_sec: float | None (視頻時長)
        - total_tail_sec: float (總尾部時間)
        - enabled: bool (是否啟用)

    Example:
        >>> ctx = prepare_ending_context()
        >>> if ctx["exists"]:
        ...     print(f"片尾時長: {ctx['duration_sec']}秒")
    """
    path = _resolve_ending_video_path(item)
    enabled = _is_ending_enabled(item)

    if not enabled:
        return {
            "path": path,
            "exists": False,
            "duration_sec": 0.0,
            "total_tail_sec": 0.0,
            "enabled": False,
        }

    exists = os.path.isfile(path)
    duration = _probe_media_duration(path) if exists else None
    total_tail = float(duration or 0.0) if duration else 0.0

    return {
        "path": path,
        "exists": bool(exists),
        "duration_sec": duration,
        "total_tail_sec": total_tail,
        "enabled": True,
    }


def resolve_letter_asset_dir(
    item: Dict[str, Any] | None = None
) -> str:
    """解析字母素材目錄路徑。

    Args:
        item: 視頻配置字典,包含可選的目錄設定:
            - letters_asset_dir: 字母素材目錄
            - letters_assets_dir: 字母素材目錄 (別名)

    Returns:
        字母素材目錄絕對路徑

    Note:
        優先順序:
        1. item["letters_asset_dir"] / item["letters_assets_dir"]
        2. 環境變數 SPELLVID_LETTER_ASSET_DIR
        3. 預設值 "assets/letters"

    Example:
        >>> dir_path = resolve_letter_asset_dir()
        >>> print(dir_path)
        C:\\Projects\\en_words\\assets\\letters
    """
    override = None
    if item:
        override = item.get("letters_asset_dir") or item.get(
            "letters_assets_dir"
        )
    if not override:
        override = os.environ.get("SPELLVID_LETTER_ASSET_DIR")
    if override:
        try:
            return os.path.abspath(str(override))
        except Exception:
            return os.path.abspath(str(override))
    return _DEFAULT_LETTER_ASSET_DIR


def prepare_letters_context(item: Dict[str, Any]) -> Dict[str, Any]:
    """準備字母資源上下文資訊。

    解析字母字串、檢查素材檔案、計算佈局。

    Args:
        item: 視頻配置字典,包含:
            - letters: 字母字串 (如 "A a B b")
            - letters_as_image: 是否使用圖片模式 (預設 True)
            - letters_asset_dir: 字母素材目錄 (可選)

    Returns:
        字母上下文資訊:
        - letters: str (原始字母字串)
        - mode: str ("image" | "text")
        - asset_dir: str (素材目錄路徑)
        - layout: dict (佈局資訊,包含 letters, missing, gap, bbox)
        - filenames: List[str] (已找到的素材檔名)
        - missing: List[dict] (缺失素材詳情)
        - missing_names: List[str] (缺失素材檔名)
        - has_letters: bool (是否有字母)

    Example:
        >>> ctx = prepare_letters_context({"letters": "A a", "letters_as_image": True})
        >>> ctx["mode"]
        'image'
        >>> ctx["has_letters"]
        True
        >>> len(ctx["filenames"])
        2
    """
    from spellvid.infrastructure.rendering.image_loader import (
        _load_letter_image_specs,
    )
    from spellvid.domain.layout import _calculate_letter_layout

    letters_text = str(item.get("letters", "") or "")
    asset_dir = resolve_letter_asset_dir(item)
    mode = "image" if _coerce_bool(
        item.get("letters_as_image", True)
    ) else "text"
    has_letters = bool(letters_text.strip())

    layout = {
        "letters": [],
        "missing": [],
        "gap": 0,
        "bbox": {"w": 0, "h": 0}
    }
    missing: List[Dict[str, Any]] = []

    if has_letters and mode == "image":
        # 載入圖片規格
        specs, missing = _load_letter_image_specs(letters_text, asset_dir)

        # 計算佈局
        if specs:
            layout_result = _calculate_letter_layout(
                specs,
                target_height=LETTER_TARGET_HEIGHT,
                available_width=LETTER_AVAILABLE_WIDTH,
                base_gap=LETTER_BASE_GAP,
                extra_scale=LETTER_EXTRA_SCALE,
                safe_x=LETTER_SAFE_X,
            )
            layout = layout_result
            layout["missing"] = missing
        else:
            layout["missing"] = missing

    filenames = [
        entry.get("filename") for entry in layout.get("letters", [])
    ]
    missing_names = _letters_missing_names(missing)

    return {
        "letters": letters_text,
        "mode": mode,
        "asset_dir": asset_dir,
        "layout": layout,
        "filenames": filenames,
        "missing": missing,
        "missing_names": missing_names,
        "has_letters": has_letters,
    }


def log_missing_letter_assets(missing: List[Dict[str, Any]]) -> None:
    """記錄缺失的字母素材。

    將缺失素材資訊輸出到 stdout (警告訊息)。

    Args:
        missing: 缺失素材資訊列表,每個元素包含:
            - filename: 素材檔名
            - char: 字元
            - path: 預期路徑
            - reason: 缺失原因

    Example:
        >>> missing = [
        ...     {
        ...         "filename": "A.png",
        ...         "char": "A",
        ...         "path": "assets/letters/A.png",
        ...         "reason": "file not found"
        ...     }
        ... ]
        >>> log_missing_letter_assets(missing)
        WARNING: letters asset missing A.png (file not found) at assets/letters/A.png
    """
    if not missing:
        return

    for entry in missing:
        name = entry.get("filename") or entry.get("char") or "?"
        path = entry.get("path")
        reason = entry.get("reason") or "unavailable"
        if path:
            print(
                f"WARNING: letters asset missing {name} ({reason}) at {path}"
            )
        else:
            print(f"WARNING: letters asset missing {name} ({reason})")
