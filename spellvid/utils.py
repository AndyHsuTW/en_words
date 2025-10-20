"""⚠️ DEPRECATED: spellvid.utils module

This module is deprecated and will be removed in a future version.
All functions are being migrated to the new modular architecture:
- spellvid.shared: Types, constants, validation
- spellvid.domain: Layout, typography, effects, timing
- spellvid.infrastructure: MoviePy, Pillow, FFmpeg adapters
- spellvid.application: Video service, batch service, resource checker
- spellvid.cli: CLI commands and parsers

See ARCHITECTURE.md for migration guide.
"""

import warnings
import json
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Any, Tuple, Optional
import numpy as _np
from PIL import Image, ImageDraw, ImageFont

# Issue deprecation warning
warnings.warn(
    "The spellvid.utils module is deprecated. "
    "Please migrate to the new modular architecture. "
    "See ARCHITECTURE.md for details.",
    DeprecationWarning,
    stacklevel=2
)

# moviepy imports are optional; try several fallbacks so utils can detect
# moviepy whether it's packaged as `moviepy.editor` or `moviepy` module.
_mpy = None
_mpy_config = None
_HAS_MOVIEPY = False
try:
    # try editor submodule first (preferred)
    from moviepy import editor as _mpy  # type: ignore
    try:
        from moviepy import config as _mpy_config  # type: ignore
    except Exception:
        _mpy_config = None  # type: ignore
    _HAS_MOVIEPY = True
except Exception:
    try:
        # fall back to top-level moviepy module
        import moviepy as _mpy  # type: ignore
        try:
            from moviepy import config as _mpy_config  # type: ignore
        except Exception:
            _mpy_config = None  # type: ignore
        # verify it exposes the core classes we need
        if hasattr(_mpy, "ImageClip") and hasattr(_mpy, "AudioFileClip"):
            _HAS_MOVIEPY = True
        else:
            _mpy = None
    except Exception:
        _mpy = None
        _mpy_config = None
        _HAS_MOVIEPY = False

PROGRESS_BAR_SAFE_X = 64
PROGRESS_BAR_MAX_X = 1856
PROGRESS_BAR_WIDTH = PROGRESS_BAR_MAX_X - PROGRESS_BAR_SAFE_X
PROGRESS_BAR_HEIGHT = 32
PROGRESS_BAR_COLORS = {
    "safe": (164, 223, 195),
    "warn": (247, 228, 133),
    "danger": (248, 187, 166),
}
PROGRESS_BAR_RATIOS = {
    "safe": 0.5,
    "warn": 0.2,
    "danger": 0.3,
}
PROGRESS_BAR_CORNER_RADIUS = 16


LETTER_SAFE_X = 64
LETTER_SAFE_Y = 48
LETTER_AVAILABLE_WIDTH = 1920 - (LETTER_SAFE_X * 2)
LETTER_TARGET_HEIGHT = 220
LETTER_BASE_GAP = -40  # 調整字母間距 (像素) - experimental negative gap
LETTER_EXTRA_SCALE = 1.5

_DEFAULT_LETTER_ASSET_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "AZ")
)


_DEFAULT_ENTRY_VIDEO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "entry.mp4")
)

_DEFAULT_ENDING_VIDEO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "ending.mp4")
)

# Main background color for render_video_moviepy (RGB tuple).
# Change this constant to control the default full-screen background color.
MAIN_BG_COLOR = (255, 250, 233)

# Video transition effects constants
FADE_OUT_DURATION = 3.0  # seconds - duration of fade to black at video end
FADE_IN_DURATION = 1.0   # seconds - duration of fade from black at video start


def _coerce_non_negative_float(value: Any, default: float = 0.0) -> float:
    try:
        fv = float(value)
    except (TypeError, ValueError):
        return float(default)
    if fv < 0:
        return 0.0
    if not (fv < float("inf")):
        return float(default)
    return float(fv)


def _resolve_entry_video_path(item: Dict[str, Any] | None = None) -> str:
    if item:
        override = item.get("entry_video_path") or item.get("entry_path")
        if override:
            return os.path.abspath(str(override))
    env_override = os.environ.get("SPELLVID_ENTRY_VIDEO_PATH")
    if env_override:
        return os.path.abspath(env_override)
    return _DEFAULT_ENTRY_VIDEO_PATH


def _is_entry_enabled(item: Dict[str, Any] | None = None) -> bool:
    if not item:
        return True
    if "entry_enabled" in item:
        return _coerce_bool(item.get("entry_enabled"), True)
    if "entry_disabled" in item:
        return not _coerce_bool(item.get("entry_disabled"), False)
    return True


def _resolve_ending_video_path(item: Dict[str, Any] | None = None) -> str:
    if item:
        override = item.get("ending_video_path") or item.get("ending_path")
        if override:
            return os.path.abspath(str(override))
    env_override = os.environ.get("SPELLVID_ENDING_VIDEO_PATH")
    if env_override:
        return os.path.abspath(env_override)
    return _DEFAULT_ENDING_VIDEO_PATH


def _is_ending_enabled(item: Dict[str, Any] | None = None) -> bool:
    if not item:
        return True
    if "ending_enabled" in item:
        return _coerce_bool(item.get("ending_enabled"), True)
    if "ending_disabled" in item:
        return not _coerce_bool(item.get("ending_disabled"), False)
    return True


_entry_probe_cache: Dict[str, Tuple[float, Optional[float]]] = {}


def _probe_media_duration(path: str) -> Optional[float]:
    """Best-effort probe for a media file duration in seconds."""
    if not path or not os.path.isfile(path):
        return None

    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0.0

    cache_key = os.path.abspath(path)
    cached = _entry_probe_cache.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]

    duration: Optional[float] = None

    if _HAS_MOVIEPY:
        try:
            clip = _mpy.VideoFileClip(path)
            try:
                raw = getattr(clip, "duration", None)
                if raw is not None:
                    duration = float(raw)
            finally:
                try:
                    clip.close()
                except Exception:
                    pass
        except Exception:
            duration = None

    if duration is None:
        candidates = [
            shutil.which("ffprobe"),
            shutil.which("ffprobe.exe"),
            None,
        ]
        ffmpeg_dir = os.path.join(os.path.dirname(__file__), "..", "FFmpeg")
        for exe in ("ffprobe", "ffprobe.exe"):
            candidate = os.path.join(ffmpeg_dir, exe)
            if os.path.isfile(candidate):
                candidates.append(candidate)
        for cand in candidates:
            if not cand:
                continue
            cmd = [
                cand,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ]
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                text = out.decode("utf-8", errors="ignore").strip()
                if text:
                    duration = float(text)
                    break
            except Exception:
                continue

    if duration is not None and duration < 0:
        duration = None

    _entry_probe_cache[cache_key] = (mtime, duration)
    return duration


def _prepare_entry_context(item: Dict[str, Any] | None = None) -> Dict[str, Any]:
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


def _prepare_ending_context(item: Dict[str, Any] | None = None) -> Dict[str, Any]:
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


def _resolve_letter_asset_dir(item: Dict[str, Any] | None = None) -> str:
    override = None
    if item:
        override = item.get("letters_asset_dir") or item.get(
            "letters_assets_dir")
    if not override:
        override = os.environ.get("SPELLVID_LETTER_ASSET_DIR")
    if override:
        try:
            return os.path.abspath(str(override))
        except Exception:
            return os.path.abspath(str(override))
    return _DEFAULT_LETTER_ASSET_DIR


def _normalize_letters_sequence(letters: str) -> List[str]:
    if not letters:
        return []
    seq: List[str] = []
    for ch in letters:
        if not ch or ch.isspace():
            continue
        seq.append(ch)
    return seq


def _letter_asset_filename(ch: str) -> Optional[str]:
    if not ch:
        return None
    if ch.isalpha():
        if ch.isupper():
            return f"{ch}.png"
        if ch.islower():
            return f"{ch}_small.png"
    return None


def _plan_letter_images(letters: str, asset_dir: str) -> Dict[str, Any]:
    """規劃字母圖片的佈局 (向後兼容層)

    此函數是重構後的向後兼容層,內部呼叫分層後的新函數:
    - infrastructure.rendering.image_loader: 載入圖片資訊
    - domain.layout: 計算佈局

    Note:
        此函數將在 v2.0 移除,請改用新的分層 API

    Args:
        letters: 字母字串
        asset_dir: 素材目錄路徑

    Returns:
        佈局結果字典,包含 letters, missing, gap, bbox
    """
    from spellvid.infrastructure.rendering.image_loader import (
        _load_letter_image_specs
    )
    from spellvid.domain.layout import _calculate_letter_layout

    # Step 1: 載入圖片規格
    specs, missing = _load_letter_image_specs(letters, asset_dir)

    # Step 2: 若無可用圖片,返回空結果
    if not specs:
        return {
            "letters": [],
            "missing": missing,
            "gap": 0,
            "bbox": {"w": 0, "h": 0}
        }

    # Step 3: 計算佈局
    result = _calculate_letter_layout(
        specs,
        target_height=LETTER_TARGET_HEIGHT,
        available_width=LETTER_AVAILABLE_WIDTH,
        base_gap=LETTER_BASE_GAP,
        extra_scale=LETTER_EXTRA_SCALE,
        safe_x=LETTER_SAFE_X,
    )

    # Step 4: 添加 missing 資訊並返回
    result["missing"] = missing
    return result


def _letters_missing_names(missing: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    for entry in missing or []:
        name = entry.get("filename") or entry.get("char")
        if name:
            name_str = str(name)
            if name_str not in names:
                names.append(name_str)
    return names


def _prepare_letters_context(item: Dict[str, Any]) -> Dict[str, Any]:
    letters_text = str(item.get("letters", "") or "")
    asset_dir = _resolve_letter_asset_dir(item)
    mode = "image" if _coerce_bool(
        item.get("letters_as_image", True)) else "text"
    has_letters = bool(letters_text.strip())
    layout = {"letters": [], "missing": [], "gap": 0, "bbox": {"w": 0, "h": 0}}
    missing: List[Dict[str, Any]] = []
    if has_letters and mode == "image":
        layout = _plan_letter_images(letters_text, asset_dir)
        missing = layout.get("missing", [])
    filenames = [entry.get("filename") for entry in layout.get("letters", [])]
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


def _log_missing_letter_assets(missing: List[Dict[str, Any]]) -> None:
    if not missing:
        return
    for entry in missing:
        name = entry.get("filename") or entry.get("char") or "?"
        path = entry.get("path")
        reason = entry.get("reason") or "unavailable"
        if path:
            print(
                f"WARNING: letters asset missing {name} ({reason}) at {path}")
        else:
            print(f"WARNING: letters asset missing {name} ({reason})")


def _coerce_bool(value: Any, default: bool = True) -> bool:
    """Return a boolean, accepting common string/int representations."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        val = value.strip().lower()
        if not val:
            return default
        if val in {"false", "0", "off", "no", "n"}:
            return False
        if val in {"true", "1", "on", "yes", "y"}:
            return True
    return bool(value)


def _progress_bar_band_layout(bar_width: int) -> List[Dict[str, Any]]:
    """Return color bands with absolute pixel spans for the progress bar."""
    order = ("safe", "warn", "danger")
    layout: List[Dict[str, Any]] = []
    cursor = 0
    for idx, key in enumerate(order):
        if idx == len(order) - 1:
            end = bar_width
        else:
            width = int(round(bar_width * PROGRESS_BAR_RATIOS[key]))
            end = min(bar_width, cursor + width)
        end = max(cursor, end)
        layout.append(
            {
                "name": key,
                "color": PROGRESS_BAR_COLORS[key],
                "start": cursor,
                "end": end,
            }
        )
        cursor = end
    if layout:
        layout[-1]["end"] = bar_width
    return layout


_progress_bar_cache: Dict[int, Tuple[_np.ndarray, _np.ndarray]] = {}


def _progress_bar_base_arrays(bar_width: int) -> Tuple[_np.ndarray, _np.ndarray]:
    """Return (color_rgb, alpha_mask) arrays for the segmented progress bar."""
    cached = _progress_bar_cache.get(bar_width)
    if cached:
        return cached
    height = PROGRESS_BAR_HEIGHT
    color = _np.zeros((height, bar_width, 3), dtype=_np.uint8)
    layout = _progress_bar_band_layout(bar_width)
    for band in layout:
        start = max(0, int(band["start"]))
        end = max(start, min(bar_width, int(band["end"])))
        if end <= start:
            continue
        color[:, start:end, 0] = band["color"][0]
        color[:, start:end, 1] = band["color"][1]
        color[:, start:end, 2] = band["color"][2]
    mask_img = Image.new("L", (bar_width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.rounded_rectangle(
        (0, 0, bar_width - 1, height - 1),
        radius=PROGRESS_BAR_CORNER_RADIUS,
        fill=255,
    )
    mask = _np.array(mask_img, dtype=_np.uint8)
    _progress_bar_cache[bar_width] = (color, mask)
    return color, mask


def _make_progress_bar_mask(mask_slice: _np.ndarray, duration: float):
    """Create a MoviePy ImageClip mask from an alpha slice."""
    mask_arr = (mask_slice.astype(_np.float32) / 255.0)
    import inspect as _inspect

    mask_kwargs = {}
    try:
        params = _inspect.signature(_mpy.ImageClip.__init__).parameters
        if "is_mask" in params:
            mask_kwargs["is_mask"] = True
        elif "ismask" in params:
            mask_kwargs["ismask"] = True
    except Exception:
        mask_kwargs["ismask"] = True
    if not mask_kwargs:
        mask_kwargs["ismask"] = True
    clip = _mpy.ImageClip(mask_arr, **mask_kwargs).with_duration(duration)
    return clip


def _build_progress_bar_segments(
    countdown: float,
    total_duration: float,
    *,
    fps: int = 10,
    bar_width: int = PROGRESS_BAR_WIDTH,
) -> List[Dict[str, Any]]:
    """Plan progress bar slices (start, end, width, spans) across countdown."""
    countdown = float(max(0.0, countdown))
    total_duration = float(max(total_duration, countdown))
    if fps <= 0 or bar_width <= 0:
        return []
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

    import math as _math_local

    layout = _progress_bar_band_layout(bar_width)
    step_count = max(1, int(_math_local.ceil(countdown * float(fps))))
    step = countdown / step_count
    segments: List[Dict[str, Any]] = []
    prev_width = bar_width
    for idx in range(step_count):
        start = min(countdown, idx * step)
        end = min(countdown, (idx + 1) * step)
        if end <= start:
            continue
        remaining = max(0.0, countdown - start)
        ratio = remaining / countdown if countdown else 0.0
        raw_width = int(round(bar_width * ratio))
        visible_width = min(prev_width, max(0, raw_width))
        if ratio > 0.0:
            if prev_width > 0:
                visible_width = max(1, visible_width)
            else:
                visible_width = 0
        else:
            visible_width = 0
        x_start = bar_width - visible_width if visible_width > 0 else bar_width
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
# If MoviePy is available, try to configure which ffmpeg binary to use.


def _find_and_set_ffmpeg():
    """Locate ffmpeg and set IMAGEIO_FFMPEG_EXE and moviepy config when found.

     Priority:
     1) environment FFMPEG_PATH (if given and points to ffprobe,
         try sibling ffmpeg)
     2) repo-local FFmpeg/ffmpeg.exe
     3) imageio_ffmpeg.get_ffmpeg_exe()
    """
    # 1: env-provided
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    if not ffmpeg_path:
        ffmpeg_path = os.environ.get("IMAGEIO_FFMPEG_EXE")
    if ffmpeg_path:
        # if user accidentally pointed to ffprobe, try sibling ffmpeg.exe
        base = os.path.basename(ffmpeg_path).lower()
        if "ffprobe" in base:
            candidate = os.path.join(
                os.path.dirname(ffmpeg_path), "ffmpeg.exe"
            )
            if os.path.isfile(candidate):
                ffmpeg_path = candidate
    # 2: repo-local
    if not ffmpeg_path:
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)
        )
        candidate = os.path.join(root, "FFmpeg", "ffmpeg.exe")
        if os.path.isfile(candidate):
            ffmpeg_path = candidate
    # 3: imageio-ffmpeg
    if not ffmpeg_path:
        try:
            import imageio_ffmpeg as _iioff  # type: ignore

            exe = _iioff.get_ffmpeg_exe()
            if exe:
                ffmpeg_path = exe
        except Exception:
            pass

    if ffmpeg_path and os.path.isfile(ffmpeg_path):
        os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_path)
        try:
            if _mpy_config is not None:
                _mpy_config.change_settings({"FFMPEG_BINARY": ffmpeg_path})
        except Exception:
            pass


def _measure_text_with_pil(text: str, pil_font: ImageFont.ImageFont):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    已遷移至: spellvid.infrastructure.rendering.pillow_adapter._measure_text_with_pil

    Measure text size (w, h) using Pillow's textbbox reliably.

    Returns fallback heuristics on error.
    """
    from spellvid.infrastructure.rendering.pillow_adapter import (
        _measure_text_with_pil as _migrated_measure_text_with_pil
    )
    return _migrated_measure_text_with_pil(text, pil_font)


def _find_system_font(prefer_cjk: bool, size: int):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    已遷移至: spellvid.infrastructure.rendering.pillow_adapter._find_system_font

    Try common system font paths; return PIL ImageFont (truetype)
    or load_default.
    """
    from spellvid.infrastructure.rendering.pillow_adapter import (
        _find_system_font as _migrated_find_system_font
    )
    return _migrated_find_system_font(prefer_cjk, size)


def _make_text_imageclip(
    text: str,
    font_size: int = 48,
    color=(0, 0, 0),
    bg=None,
    duration: float = None,
    prefer_cjk: bool = False,
    extra_bottom: int = 0,
    fixed_size: tuple | None = None,
):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除
    
    已遷移至: spellvid.infrastructure.rendering.pillow_adapter._make_text_imageclip
    
    Render text with Pillow and return a MoviePy ImageClip.

    prefer_cjk: if True, tries CJK fonts first.
    bg: background color tuple or None for transparent.
    """
    from spellvid.infrastructure.rendering.pillow_adapter import (
        _make_text_imageclip as _migrated_make_text_imageclip
    )
    return _migrated_make_text_imageclip(
        text=text,
        font_size=font_size,
        color=color,
        bg=bg,
        duration=duration,
        prefer_cjk=prefer_cjk,
        extra_bottom=extra_bottom,
        fixed_size=fixed_size
    )


# configure ffmpeg as early as possible
_find_and_set_ffmpeg()

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "letters",
            "word_en",
            "word_zh",
            "image_path",
            "music_path",
        ],
        "properties": {
            "letters": {"type": "string"},
            "word_en": {"type": "string"},
            "word_zh": {"type": "string"},
            "image_path": {"type": "string"},
            "music_path": {"type": "string"},
            "countdown_sec": {"type": "integer"},
            "reveal_hold_sec": {"type": "integer"},
            "entry_hold_sec": {
                "type": "number",
                "minimum": 0,
            },
            "entry_enabled": {"type": "boolean", "default": True},
            "progress_bar": {"type": "boolean", "default": True},
            "timer_visible": {"type": "boolean", "default": True},
            "letters_as_image": {"type": "boolean", "default": True},
            "theme": {"type": "string"},
            "video_mode": {
                "type": "string",
                "enum": ["fit", "cover"],
                "default": "fit"
            }
        },
        "additionalProperties": False
    }
}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data: Any) -> List[str]:
    """Very small schema validator: returns list of errors (empty if ok)."""
    errors = []
    if not isinstance(data, list):
        errors.append("root must be array")
        return errors
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"item[{i}] not object")
            continue
        for req in SCHEMA["items"]["required"]:
            if req not in item:
                errors.append(f"item[{i}] missing required {req}")
        # detect additional properties
        allowed = set(SCHEMA["items"]["properties"].keys())
        for k in item.keys():
            if k not in allowed:
                errors.append(f"item[{i}] has additional property {k}")
    return errors


# Simple zhuyin map for basic characters used in tests
_ZHUYIN_MAP = {
    "冰": "ㄅㄧㄥ",
    "塊": "ㄎㄨㄞˋ",
    "動": "ㄉㄨㄥˋ",
    "物": "ㄨˋ",
}

ZHUYIN_BASE_HEIGHT_RATIO = 0.65
ZHUYIN_MIN_FONT_SIZE = 10

ZHUYIN_GAP_FOR_TWO = 12
ZHUYIN_GAP_FOR_THREE = 8


def _zhuyin_main_gap(symbol_count: int) -> int:
    """Return vertical gap (px) between stacked zhuyin symbols."""
    if symbol_count <= 1:
        return 0
    if symbol_count == 2:
        return ZHUYIN_GAP_FOR_TWO
    return ZHUYIN_GAP_FOR_THREE


def zhuyin_for(text: str) -> str:
    """Return a naive zhuyin by joining per-character lookup.

    Missing chars are skipped.
    """
    parts = []
    # Prefer using pypinyin's Bopomofo output if available for broader coverage
    try:
        from pypinyin import pinyin, Style  # type: ignore
        for ch in text:
            if not ch.strip():
                continue
            try:
                p = pinyin(
                    ch,
                    style=Style.BOPOMOFO,
                    heteronym=False,
                    errors='ignore',
                )
                if p and p[0] and p[0][0]:
                    parts.append(p[0][0])
                    continue
            except Exception:
                pass
            # fallback to map if pypinyin didn't return anything
            parts.append(_ZHUYIN_MAP.get(ch, ""))
        return " ".join([p for p in parts if p])
    except Exception:
        # pypinyin not available; use small internal map
        for ch in text:
            parts.append(_ZHUYIN_MAP.get(ch, ""))
        return " ".join([p for p in parts if p])


def _layout_zhuyin_column(
    cursor_y: int,
    col_h: int,
    total_main_h: int,
    tone_syms: List[str],
    tone_sizes: List[Tuple[int, int]],
    tone_gap: int = 10,
) -> Dict[str, Any]:
    """Compute vertical offsets for bopomofo main symbols and tone marks."""
    tone_is_neutral = len(tone_syms) == 1 and tone_syms[0] == "˙"
    top = int(cursor_y)
    col_height = max(0, int(col_h))
    safe_total_main_h = max(0, int(total_main_h))

    base_main_start_y = top
    if safe_total_main_h > 0:
        limit_main_start = top + col_height - safe_total_main_h
        if limit_main_start < base_main_start_y:
            base_main_start_y = limit_main_start
    layout: Dict[str, Any] = {
        "main_start_y": base_main_start_y,
        "tone_start_y": None,
        "tone_box_height": 0,
        "tone_alignment": "right",
        "tone_is_neutral": tone_is_neutral,
    }
    if not tone_syms or not tone_sizes:
        return layout

    tone_total_h = 0
    for idx, (_, height) in enumerate(tone_sizes):
        tone_total_h += max(0, int(height))
        if idx < len(tone_sizes) - 1:
            tone_total_h += tone_gap
    tone_total_h = max(0, tone_total_h)

    if tone_is_neutral:
        gap_to_main = tone_gap if safe_total_main_h > 0 and tone_total_h > 0 else 0
        block_h = safe_total_main_h + tone_total_h + gap_to_main
        block_start_y = top
        if block_h > 0:
            limit_block_start = top + col_height - block_h
            if limit_block_start < block_start_y:
                block_start_y = limit_block_start
        layout["tone_start_y"] = block_start_y
        layout["main_start_y"] = block_start_y + tone_total_h + gap_to_main
        layout["tone_box_height"] = tone_total_h
        layout["tone_alignment"] = "center"
    else:
        layout["main_start_y"] = base_main_start_y
        tone_start_y = base_main_start_y + max(0, safe_total_main_h // 2)
        if tone_total_h > 0:
            max_tone_start = top + col_height - tone_total_h
            if tone_start_y > max_tone_start:
                tone_start_y = max_tone_start
        layout["tone_start_y"] = tone_start_y
        layout["tone_box_height"] = tone_total_h or safe_total_main_h

    return layout


def compute_layout_bboxes(
    item: Dict[str, Any], video_size=(1920, 1080)
) -> Dict[str, Dict[str, int]]:
    """Compute bounding boxes for main text elements without using MoviePy.

    Returns a dict with keys 'letters', 'zh', 'timer', 'reveal' each mapping
    to a dict {'x':, 'y':, 'w':, 'h':} representing pixel bbox. Uses the same
    candidates and sizes as the renderer to emulate layout.
    """
    """Headless text bbox calculator using Pillow.

    Returns bounding boxes for keys: letters, zh, timer, reveal.
    """
    w_vid, h_vid = video_size
    boxes: Dict[str, Dict[str, int]] = {}

    # helper alias to module-level measurer
    measure_text = _measure_text_with_pil

    letters_ctx = _prepare_letters_context(item)

    # Letters (top-left)
    if letters_ctx.get("has_letters"):
        if letters_ctx.get("mode") == "image":
            layout = letters_ctx.get("layout", {})
            bbox = layout.get("bbox", {}) or {}
            min_x = int(bbox.get("x_offset", 0) or 0)
            boxes["letters"] = {
                "x": LETTER_SAFE_X + min_x,
                "y": LETTER_SAFE_Y,
                "w": int(bbox.get("w", 0) or 0),
                "h": int(bbox.get("h", 0) or 0),
                "mode": "image",
                "gap": layout.get("gap", 0),
                "missing": list(letters_ctx.get("missing_names", [])),
            }
        else:
            letters = letters_ctx.get("letters", "")
            if letters:
                letters_y = LETTER_SAFE_Y
                font_size = 140
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None
                if font is None:
                    text_w = int(len(letters) * font_size * 0.6)
                    text_h = font_size
                else:
                    text_w, text_h = measure_text(letters, font)
                boxes["letters"] = {
                    "x": LETTER_SAFE_X,
                    "y": letters_y,
                    "w": text_w,
                    "h": text_h,
                    "mode": "text",
                    "missing": [],
                }

    # Chinese + zhuyin (top-right)
    word_zh = item.get("word_zh", "")
    zhuyin = zhuyin_for(word_zh)
    if word_zh:
        # split zhuyin into groups per character (space-separated)
        zh_groups = zhuyin.split() if zhuyin else []
        font_candidates = [
            r"C:\Windows\Fonts\msjh.ttf",
            r"C:\Windows\Fonts\msjhbd.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        font_path = None
        for p in font_candidates:
            if os.path.isfile(p):
                font_path = p
                break

        # scale base font size up 1.5x to increase CJK/zhuyin visibility
        base_font_size = 96
        try:
            if font_path:
                ch_font = ImageFont.truetype(font_path, base_font_size)
            else:
                ch_font = ImageFont.load_default()

            padding = 8
            total_w = 0
            max_h = 0
            for i, ch in enumerate(word_zh):
                # measure CJK glyph
                ch_w, ch_h = measure_text(ch, ch_font)
                zh_grp = zh_groups[i] if i < len(zh_groups) else ""

                # break zhuyin into tone vs main symbols so we can
                # vertically center the main symbols and place tone
                # marks centered on the whole zh column.
                tone_marks = set(["ˊ", "ˇ", "ˋ", "˙"])
                lines = list(zh_grp) if zh_grp else []
                main_syms = [s for s in lines if s not in tone_marks]
                tone_syms = [s for s in lines if s in tone_marks]

                # choose a smaller zh font and iteratively reduce its size
                # until the stacked main symbols fit within the CJK height.
                n_main = max(
                    1, (len(main_syms) if main_syms else len(lines)) or 1
                )
                # start with an estimate of zh size and shrink if necessary
                zh_font_size = max(ZHUYIN_MIN_FONT_SIZE, int(ch_h / n_main))
                symbols = main_syms if main_syms else lines
                symbol_count = len(symbols)
                gap = _zhuyin_main_gap(symbol_count)
                zh_w = 0
                zh_h = 0
                # tone_h not needed in render path
                try:
                    while True:
                        try:
                            zh_font = (
                                ImageFont.truetype(font_path, zh_font_size)
                                if font_path
                                else ImageFont.load_default()
                            )
                        except Exception:
                            zh_font = ImageFont.load_default()

                        zh_w = 0
                        zh_h = 0
                        for idx_sym, sym in enumerate(symbols):
                            sw, sh = measure_text(sym, zh_font)
                            zh_w = max(zh_w, sw)
                            zh_h += sh
                            if idx_sym < symbol_count - 1:
                                zh_h += gap

                        if tone_syms:
                            tw, th = measure_text(tone_syms[0], zh_font)

                        # stop when fit or reached min size
                        if zh_h <= ch_h or zh_font_size <= ZHUYIN_MIN_FONT_SIZE:
                            break
                        zh_font_size -= 1

                except Exception:
                    zh_w = zh_w or 0
                    zh_h = zh_h or 0

                # ensure column width accounts for bopomofo and small padding
                col_w = ch_w + (zh_w if zh_w else 0) + padding
                # fix column height to the CJK glyph height so green box
                # won't exceed red box; stacked symbols were already scaled
                # to fit within ch_h.
                col_h = ch_h
                total_w += col_w
                max_h = max(max_h, col_h)

            img_w = int(total_w + padding)
            img_h = int(max_h + padding * 2)
        except Exception:
            img_w = len(word_zh) * base_font_size // 2
            img_h = base_font_size * 2

        pos_x = w_vid - 64 - img_w
        boxes["zh"] = {"x": pos_x, "y": 64, "w": img_w, "h": img_h}
    timer_visible = _coerce_bool(item.get("timer_visible", True))
    timer_font_size = 64
    try:
        # use the same font selection logic as _make_text_imageclip so
        # measured size matches rendered image. We don't have timer_text
        # in this scope yet; measure a sample "00:00" string to estimate.
        timer_font = _find_system_font(False, timer_font_size)
        tw, th = measure_text("00:00", timer_font)
    except Exception:
        tw, th = timer_font_size, timer_font_size // 2
    # match _make_text_imageclip padding so predicted box
    # equals rendered image size
    pad_x = max(12, timer_font_size // 6)
    pad_y = max(8, timer_font_size // 6)
    bottom_safe_margin = 32
    img_w = int(tw + pad_x * 2)
    img_h = int(th + pad_y * 2 + bottom_safe_margin)
    # updated to match renderer position; include font_size for tests
    boxes["timer"] = {
        "x": 64,
        "y": 450,
        "w": img_w,
        "h": img_h,
        "font_size": timer_font_size,
        "visible": timer_visible,
    }

    # Reveal area (center bottom) - approximate width for longest word_en
    word_en = item.get("word_en", "")
    if word_en:
        reveal_font_size = 128
        try:
            # Use the same font selection as the renderer to get consistent
            # measurements (avoid tiny default bitmap font causing tiny boxes)
            rf = _find_system_font(False, reveal_font_size)
            rw, rh = measure_text(word_en, rf)
        except Exception:
            rw = int(len(word_en) * reveal_font_size * 0.6)
            rh = reveal_font_size
        # match _make_text_imageclip padding so predicted box equals rendered
        pad_x = max(12, reveal_font_size // 6)
        pad_y = max(8, reveal_font_size // 6)
        # reserve extra bottom space inside the reveal image so underlines
        # can be drawn beneath the glyphs without overlapping. This must
        # mirror the extra_bottom used when creating reveal ImageClips.
        reveal_extra_bottom = 48
        img_w = int(rw + pad_x * 2)
        img_h = int(rh + pad_y * 2 + reveal_extra_bottom)

        # For headless layout calculations we should return the reveal box
        # x as an absolute coordinate in the video frame (centered). The
        # renderer composes the reveal ImageClip centered on the video
        # and previously compute_layout_bboxes returned rx=0 which made
        # the caller treat underline positions as local to the reveal
        # image. That mismatch meant underlines were placed at the left
        # edge. Return an absolute centered x so downstream code can
        # overlay underlines at correct absolute positions.
        rx = max(0, (w_vid - img_w) // 2)
        # place reveal so it sits above the bottom of the video with a
        # safe margin to avoid glyph descent clipping on some fonts
        safe_bottom_margin = 48
        ry = max(0, h_vid - img_h - safe_bottom_margin)
        boxes["reveal"] = {
            "x": rx,
            "y": ry,
            "w": img_w,
            "h": img_h,
            "font_size": reveal_font_size,
        }

        # compute per-letter underline boxes (absolute positions)
        # each underline is a small horizontal bar beneath a letter position.
        # Approximate per-letter horizontal region by splitting the measured
        # text width into equal segments. Previously these underline boxes
        # were returned relative to the reveal image (local coords). Since
        # the reveal box now reports an absolute x, return underline boxes
        # with absolute x/y so tests and renderer align.
        num_letters = len(word_en)
        if num_letters > 0:
            # available width for letters inside reveal image (exclude padding)
            inner_w = rw
            # avoid zero-division
            seg_w = max(1, inner_w // num_letters)
            underline_h = 4
            # leave a slightly larger margin between glyph baseline and
            # underline so they don't overlap across fonts
            underline_margin_bottom = 24
            underlines = []
            # left padding used when constructing the image in
            # _make_text_imageclip
            pad_x = max(24, reveal_font_size // 6)
            pad_y = max(8, reveal_font_size // 6)
            # Introduce a small horizontal gap between adjacent underlines so
            # they don't visually touch. Compute a gap as a fraction of the
            # segment width but clamp to a few pixels to remain stable across
            # small fonts. Center each underline inside its segment and reduce
            # its width accordingly.
            # Instead of equal segments, measure each glyph's actual width
            # using Pillow so the underline centers under the glyph. This
            # produces more accurate alignment especially for variable-width
            # fonts. Keep a small horizontal gap between adjacent underlines.
            try:
                # get a PIL font similar to what renderer uses
                pil_font = _find_system_font(False, reveal_font_size)
                # measure each character
                char_widths = []
                for ch in word_en:
                    cw, _ch_h = measure_text(ch, pil_font)
                    char_widths.append(max(1, int(cw)))
            except Exception:
                # fallback: equal-width approximation
                char_widths = [max(1, seg_w) for _ in range(num_letters)]

            gap = max(4, seg_w // 10)
            # compute the starting x of the first glyph relative to
            # the reveal image. This mirrors how text is drawn at pad_x
            cursor = pad_x
            for i, ch_w in enumerate(char_widths):
                seg_start = cursor
                avail = min(ch_w, max(0, (pad_x + inner_w) - seg_start))
                uw = max(1, avail - gap)
                # center underline under the glyph box
                local_ux = seg_start + max(0, (avail - uw) // 2)
                # advance cursor by the glyph width (not by seg_w)
                cursor += ch_w
                # y relative to reveal image: prefer placing underline
                # inside the reserved extra-bottom area so it won't overlap
                # drawn glyph pixels. Compute two candidates and choose the
                # lower (visually further down) one.
                candidate_from_text = pad_y + rh + underline_margin_bottom
                # start of the reserved extra bottom zone
                extra_zone_start = img_h - reveal_extra_bottom
                # prefer placing underline inside extra zone (with small
                # inset), otherwise fall back to candidate_from_text
                # add a small inset into the extra zone to avoid touching
                # antialiased glyph pixels
                local_uy = max(candidate_from_text, extra_zone_start + 6)
                # ensure underline fits inside image
                if local_uy + underline_h > img_h:
                    local_uy = max(0, img_h - underline_h)
                # keep underline coords relative to the reveal image.
                # The renderer composes the reveal image at absolute
                # position r_box['x']/['y'] and will add those offsets
                # when overlaying underlines.
                ux = local_ux
                uy = local_uy
                underlines.append(
                    {"x": ux, "y": uy, "w": uw, "h": underline_h}
                )
            boxes["reveal_underlines"] = underlines

    return boxes


def _make_fixed_letter_clip(
    letter: str,
    fixed_size: tuple,
    font_size: int = 128,
    color=(0, 0, 0),
    duration: float = None,
    prefer_cjk: bool = False,
):
    """Render a single letter centered on a fixed transparent canvas and
    return an ImageClip. This ensures per-letter clips have identical
    dimensions to avoid pushing other clips when they appear/disappear."""
    # delegate to _make_text_imageclip which now supports fixed_size
    return _make_text_imageclip(
        text=letter,
        font_size=font_size,
        color=color,
        duration=duration,
        prefer_cjk=prefer_cjk,
        extra_bottom=0,
        fixed_size=fixed_size,
    )


def check_assets(item: Dict[str, Any]) -> Dict[str, Any]:
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
    if os.path.isfile(item.get("image_path", "")):
        res["image_exists"] = True
    if os.path.isfile(item.get("music_path", "")):
        res["music_exists"] = True
    try:
        letters_ctx = _prepare_letters_context(item)
    except Exception:
        letters_ctx = {
            "mode": item.get("letters_as_image", True) and "image" or "text",
            "filenames": [],
            "missing_names": [],
            "asset_dir": _resolve_letter_asset_dir(item),
            "has_letters": bool(str(item.get("letters", "")).strip()),
        }
    res["letters_mode"] = letters_ctx.get("mode")
    res["letters_assets"] = list(letters_ctx.get("filenames", []))
    res["letters_missing"] = list(letters_ctx.get("missing_names", []))
    res["letters_missing_details"] = list(letters_ctx.get("missing", []))
    res["letters_asset_dir"] = letters_ctx.get("asset_dir")
    res["letters_has_letters"] = bool(letters_ctx.get("has_letters"))
    return res


def synthesize_beeps(duration_sec: int = 3, rate_hz: int = 1) -> bytes:
    """Return a stub bytes object representing beep audio.

    This is intentionally simple to avoid binary deps.
    """
    return b"BEEP" * max(1, duration_sec * rate_hz)


def _create_placeholder_mp4_with_ffmpeg(out_path: str) -> bool:
    """Create a tiny valid mp4 using ffmpeg if available.

    Returns True on success, False otherwise.
    """
    try:
        ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE") or shutil.which("ffmpeg")
        if not ffmpeg:
            return False
    # create a single white frame PNG and encode to mp4
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
                "-y",
                "-loop",
                "1",
                "-i",
                png,
                "-t",
                "1",
                "-vf",
                "scale=1920:1080",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
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


def render_video_stub(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    use_moviepy: bool = False,
    skip_ending: bool = False,
) -> Dict[str, Any]:
    """Render video.

    Args:
        item: Video configuration dictionary with word, letters, assets.
        out_path: Output file path for the rendered video.
        dry_run: If True, only compute metadata without rendering.
        use_moviepy: If True and MoviePy available, use real renderer.
        skip_ending: If True, skip ending video (for batch processing).
                     Default False maintains backward compatibility.

    Returns:
        Dictionary with rendering results and metadata.

    Note:
        skip_ending is for batch video processing to prevent ending
        video after every word. In batch mode, only the last video
        should have skip_ending=False.
    """
    if use_moviepy and _HAS_MOVIEPY:
        return render_video_moviepy(
            item, out_path, dry_run=dry_run, skip_ending=skip_ending
        )

    letters_ctx = _prepare_letters_context(item)
    letters_mode = letters_ctx.get("mode")
    letters_assets = list(letters_ctx.get("filenames", []))
    letters_missing_names = list(letters_ctx.get("missing_names", []))
    letters_plan_entries = [
        dict(entry) for entry in letters_ctx.get("layout", {}).get("letters", [])
    ]
    letters_layout = [
        {
            "filename": entry.get("filename"),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "x": entry.get("x"),
        }
        for entry in letters_plan_entries
    ]
    letters_asset_dir = letters_ctx.get("asset_dir")
    letters_has_letters = bool(letters_ctx.get("has_letters"))
    letters_missing_details = list(letters_ctx.get("missing", []))
    if letters_mode == "image" and letters_missing_details:
        _log_missing_letter_assets(letters_missing_details)

    entry_ctx = _prepare_entry_context(item)
    entry_offset = float(entry_ctx.get("total_lead_sec", 0.0))
    entry_duration = float(entry_ctx.get("duration_sec") or 0.0)
    entry_hold = float(entry_ctx.get("hold_sec", 0.0))
    entry_offset_runtime = entry_offset
    entry_duration_runtime = entry_duration

    ending_ctx = _prepare_ending_context(item)
    ending_duration_runtime = float(ending_ctx.get(
        "total_tail_sec") or ending_ctx.get("duration_sec") or 0.0)
    ending_offset_runtime = 0.0

    countdown = int(item.get("countdown_sec", 10))
    reveal_hold = int(item.get("reveal_hold_sec", 5))
    word_en = item.get("word_en", "")
    n_for_timing = max(1, len(word_en))
    per = 1.0
    total_reveal_time = per * n_for_timing
    main_duration = float(countdown + total_reveal_time + reveal_hold)
    runtime_after_main = float(entry_offset_runtime + main_duration)
    total_duration_runtime = runtime_after_main

    progress_enabled = bool(item.get("progress_bar", True))
    progress_segments: List[Dict[str, Any]] = []
    if progress_enabled:
        progress_segments = _build_progress_bar_segments(
            countdown, main_duration)

    progress_with_timeline: List[Dict[str, Any]] = []
    for seg in progress_segments:
        seg_copy = dict(seg)
        try:
            seg_copy["timeline_start"] = round(
                entry_offset_runtime + float(seg_copy.get("start", 0.0)), 6
            )
        except Exception:
            seg_copy["timeline_start"] = entry_offset_runtime
        try:
            seg_copy["timeline_end"] = round(
                entry_offset_runtime + float(
                    seg_copy.get("end", seg_copy.get("start", 0.0))
                ),
                6,
            )
        except Exception:
            seg_copy["timeline_end"] = seg_copy["timeline_start"]
        progress_with_timeline.append(seg_copy)
    progress_segments = progress_with_timeline

    timer_visible = _coerce_bool(item.get("timer_visible", True))
    timer_plan: List[Dict[str, Any]] = []
    if timer_visible:
        for i in range(countdown + 1):
            sec_left = max(0, countdown - i)
            mm = sec_left // 60
            ss = sec_left % 60
            timer_text = f"{mm:02d}:{ss:02d}"
            timer_duration = float(
                main_duration - i) if i == countdown else 1.0
            if timer_duration < 0:
                timer_duration = 0.0
            entry = {
                "start": float(i),
                "text": timer_text,
                "duration": float(timer_duration),
            }
            entry["timeline_start"] = round(
                entry_offset_runtime + entry["start"], 6
            )
            entry["timeline_end"] = round(
                entry["timeline_start"] + entry["duration"], 6
            )
            timer_plan.append(entry)

    beep_schedule: List[float] = []
    for S in (3, 2, 1):
        if S <= countdown:
            beep_schedule.append(float(max(0.0, countdown - S)))

    ending_offset_runtime = runtime_after_main
    # Apply skip_ending logic: if skip_ending=True, set duration to 0
    if skip_ending:
        ending_duration_runtime = 0.0
    elif not ending_ctx.get("enabled", True) or not ending_ctx.get("exists"):
        ending_duration_runtime = 0.0
    total_duration_runtime = float(
        ending_offset_runtime + ending_duration_runtime)
    ending_runtime = dict(ending_ctx)
    ending_runtime["loaded"] = bool(ending_ctx.get("exists"))
    ending_runtime["error"] = None
    ending_runtime["duration_sec"] = ending_duration_runtime
    ending_runtime["total_tail_sec"] = ending_duration_runtime
    ending_runtime["size"] = (1920, 1080) if ending_ctx.get("exists") else None

    beep_schedule_timeline = [
        round(entry_offset_runtime + t, 6) for t in beep_schedule
    ]

    if dry_run:
        return {
            "status": "dry-run",
            "out": out_path,
            "progress_bar_segments": progress_segments,
            "timer_visible": timer_visible,
            "timer_plan": timer_plan,
            "beep_schedule": beep_schedule,
            "beep_schedule_timeline": beep_schedule_timeline,
            "letters_mode": letters_mode,
            "letters_assets": letters_assets,
            "letters_missing": letters_missing_names,
            # provide both a simple per-entry summary and the full
            # layout plan (includes gap and bbox) for inspection
            "letters_layout": letters_layout,
            "letters_layout_plan": letters_ctx.get("layout", {}),
            "letters_asset_dir": letters_asset_dir,
            "letters_has_letters": letters_has_letters,
            "letters_missing_details": letters_missing_details,
            "entry_info": entry_ctx,
            "entry_offset_sec": entry_offset_runtime,
            "entry_duration_sec": entry_duration_runtime,
            "entry_hold_sec": entry_hold,
            "ending_info": ending_runtime,
            "ending_offset_sec": ending_offset_runtime,
            "ending_duration_sec": ending_duration_runtime,
            "total_duration_sec": total_duration_runtime,
        }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    created = _create_placeholder_mp4_with_ffmpeg(out_path)
    if not created:
        with open(out_path, "wb") as f:
            f.write(b"MP4")
    return {
        "status": "ok",
        "out": out_path,
        "progress_bar_segments": progress_segments,
        "timer_visible": timer_visible,
        "timer_plan": timer_plan,
        "beep_schedule": beep_schedule,
        "beep_schedule_timeline": beep_schedule_timeline,
        "letters_mode": letters_mode,
        "letters_assets": letters_assets,
        "letters_missing": letters_missing_names,
        "letters_layout": letters_layout,
        "letters_asset_dir": letters_asset_dir,
        "letters_has_letters": letters_has_letters,
        "letters_missing_details": letters_missing_details,
        "entry_info": entry_ctx,
        "entry_offset_sec": entry_offset_runtime,
        "entry_duration_sec": entry_duration_runtime,
        "entry_hold_sec": entry_hold,
        "ending_info": ending_runtime,
        "ending_offset_sec": ending_offset_runtime,
        "ending_duration_sec": ending_duration_runtime,
        "total_duration_sec": total_duration_runtime,
    }


def _apply_fadeout(clip, duration: float = None):
    """Apply fade-out effect to video clip (both video and audio).

    Args:
        clip: MoviePy VideoClip object
        duration: Fade-out duration in seconds. If None, uses FADE_OUT_DURATION.

    Returns:
        VideoClip with fade-out effect applied, or original clip if conditions not met.
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip

    if duration is None:
        duration = FADE_OUT_DURATION

    # Skip fade-out if video is too short
    if clip.duration < duration:
        return clip

    # Apply video fade-out using MoviePy FX
    try:
        from moviepy.video.fx.FadeOut import FadeOut
        effect = FadeOut(duration)
        clip_with_fadeout = effect.apply(clip)
    except Exception:
        # Fallback if FadeOut not available
        return clip

    # Apply audio fade-out if audio exists
    if clip_with_fadeout.audio is not None:
        try:
            from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
            audio_effect = AudioFadeOut(duration)
            clip_with_fadeout = clip_with_fadeout.with_audio(
                audio_effect.apply(clip_with_fadeout.audio)
            )
        except Exception:
            # If audio fadeout fails, continue with video fadeout only
            pass

    return clip_with_fadeout


def _apply_fadein(clip, duration: float = None, apply_audio: bool = False):
    """Apply fade-in effect to video clip.

    Args:
        clip: MoviePy VideoClip object
        duration: Fade-in duration in seconds. If None, uses FADE_IN_DURATION.
        apply_audio: If True, also apply fade-in to audio (Phase 3 feature).

    Returns:
        VideoClip with fade-in effect applied, or original clip if conditions not met.
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip

    if duration is None:
        duration = FADE_IN_DURATION

    # Skip fade-in if video is too short
    if clip.duration < duration:
        return clip

    # Apply video fade-in using MoviePy FX
    try:
        from moviepy.video.fx.FadeIn import FadeIn
        effect = FadeIn(duration)
        clip_with_fadein = effect.apply(clip)
    except Exception:
        # Fallback if FadeIn not available
        return clip

    # Phase 3: Apply audio fade-in if requested
    if apply_audio and clip_with_fadein.audio is not None:
        try:
            from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
            audio_effect = AudioFadeIn(duration)
            clip_with_fadein = clip_with_fadein.with_audio(
                audio_effect.apply(clip_with_fadein.audio)
            )
        except Exception:
            # If audio fadein fails, continue with video fadein only
            pass

    return clip_with_fadein


def concatenate_videos_with_transitions(
    video_paths: List[str],
    output_path: str,
    fade_in_duration: float = None,
    apply_audio_fadein: bool = False,
) -> Dict[str, Any]:
    """Concatenate multiple videos with transition effects.

    This function loads multiple video files, applies fade-in effects to all videos
    except the first one (per D2 decision), and concatenates them into a single output.
    Each input video is expected to already have fade-out applied (from render phase).

    Args:
        video_paths: List of video file paths to concatenate (in order)
        output_path: Path for the final concatenated output video
        fade_in_duration: Fade-in duration in seconds. If None, uses FADE_IN_DURATION.
        apply_audio_fadein: If True, also apply fade-in to audio (Phase 3 feature).

    Returns:
        Dictionary with status information:
        - status: "ok" | "error" | "skipped"
        - message: Error message if status is "error"
        - output: Output file path if successful
        - clips_count: Number of clips concatenated
        - total_duration: Total duration of concatenated video

    Decision References:
        - D1: All videos have fade-out (applied during render)
        - D2: First video does not have fade-in; subsequent videos have 1s fade-in
        - D4: Audio fade-in is controlled by apply_audio_fadein parameter
    """
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
                clip = _mpy.VideoFileClip(path)
                cleanup_clips.append(clip)

                # D2 Decision: First video does not fade in
                if idx == 0:
                    # First video: use as-is (already has fade-out from render)
                    clips.append(clip)
                else:
                    # Subsequent videos: apply fade-in
                    clip_with_fadein = _apply_fadein(
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
            final_clip = _mpy.concatenate_videoclips(clips, method="compose")
        except Exception:
            # Fallback to default method if 'compose' fails
            try:
                final_clip = _mpy.concatenate_videoclips(clips)
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


def render_video_moviepy(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
) -> Dict[str, Any]:
    """Real video rendering using MoviePy.

    This implementation creates a simple layout:
    - background: image if present, otherwise white color
    - letters (top-left), chinese+zhuyin (top-right)
    - countdown timer on left side (updates every second)
    - reveal (bottom center) appears after countdown with typewriter effect
    - optional music and short beeps in last 3 seconds

    Args:
        skip_ending: If True, skip appending ending video (batch mode).
    """
    if not _HAS_MOVIEPY:
        raise RuntimeError("MoviePy not available")

    entry_ctx = _prepare_entry_context(item)
    entry_offset = float(entry_ctx.get("total_lead_sec", 0.0))
    entry_duration = float(entry_ctx.get("duration_sec") or 0.0)
    entry_hold = float(entry_ctx.get("hold_sec", 0.0))
    entry_offset_runtime = entry_offset
    entry_duration_runtime = entry_duration

    ending_ctx = _prepare_ending_context(item)
    ending_duration_runtime = float(ending_ctx.get(
        "total_tail_sec") or ending_ctx.get("duration_sec") or 0.0)
    ending_offset_runtime = 0.0
    ending_clip_obj = None
    ending_loaded = False
    ending_error: Optional[str] = None

    countdown = int(item.get("countdown_sec", 10))
    # reveal_hold_sec is now the time to hold AFTER the reveal completes
    reveal_hold = int(item.get("reveal_hold_sec", 5))

    # Word length affects total reveal time because each letter appears
    # at a fixed interval (1 second per letter).
    word_en = item.get("word_en", "")
    n_for_timing = max(1, len(word_en))
    # fixed per-letter interval (seconds)
    per = 1.0
    total_reveal_time = per * n_for_timing
    # total video duration = countdown + time to reveal all letters
    # plus post-reveal hold
    duration = float(countdown + total_reveal_time + reveal_hold)
    main_duration = duration
    runtime_after_main = float(entry_offset_runtime + main_duration)
    total_duration_runtime = runtime_after_main

    progress_enabled = bool(item.get("progress_bar", True))
    progress_segments: List[Dict[str, Any]] = []
    if progress_enabled:
        progress_segments = _build_progress_bar_segments(
            countdown, main_duration)

    progress_with_timeline: List[Dict[str, Any]] = []
    for seg in progress_segments:
        seg_copy = dict(seg)
        try:
            seg_copy["timeline_start"] = round(
                entry_offset_runtime + float(seg_copy.get("start", 0.0)), 6
            )
        except Exception:
            seg_copy["timeline_start"] = entry_offset_runtime
        try:
            seg_copy["timeline_end"] = round(
                entry_offset_runtime + float(
                    seg_copy.get("end", seg_copy.get("start", 0.0))
                ),
                6,
            )
        except Exception:
            seg_copy["timeline_end"] = seg_copy["timeline_start"]
        progress_with_timeline.append(seg_copy)
    progress_segments = progress_with_timeline

    timer_visible = _coerce_bool(item.get("timer_visible", True))
    timer_plan: List[Dict[str, Any]] = []
    if timer_visible:
        for i in range(countdown + 1):
            sec_left = max(0, countdown - i)
            mm = sec_left // 60
            ss = sec_left % 60
            timer_text = f"{mm:02d}:{ss:02d}"
            timer_duration = float(
                main_duration - i) if i == countdown else 1.0
            if timer_duration < 0:
                timer_duration = 0.0
            entry_timer = {
                "start": float(i),
                "text": timer_text,
                "duration": float(timer_duration),
            }
            entry_timer["timeline_start"] = round(
                entry_offset_runtime + entry_timer["start"], 6
            )
            entry_timer["timeline_end"] = round(
                entry_timer["timeline_start"] + entry_timer["duration"], 6
            )
            timer_plan.append(entry_timer)

    beep_schedule: List[float] = []
    for S in (3, 2, 1):
        if S <= countdown:
            beep_schedule.append(float(max(0.0, countdown - S)))

    beep_schedule_timeline = [
        round(entry_offset_runtime + t, 6) for t in beep_schedule
    ]

    ending_runtime = dict(ending_ctx)
    ending_runtime["loaded"] = ending_loaded
    ending_runtime["error"] = ending_error
    ending_runtime["duration_sec"] = ending_duration_runtime
    ending_runtime["total_tail_sec"] = ending_duration_runtime
    try:
        size_attr = getattr(ending_clip_obj, "size", None)
        if size_attr:
            ending_runtime["size"] = (int(size_attr[0]), int(size_attr[1]))
        else:
            ending_runtime["size"] = None
    except Exception:
        ending_runtime["size"] = None

    letters_ctx = _prepare_letters_context(item)
    letters_mode = letters_ctx.get("mode")
    letters_assets = list(letters_ctx.get("filenames", []))
    letters_missing_names = list(letters_ctx.get("missing_names", []))
    letters_plan_entries = [dict(entry) for entry in letters_ctx.get(
        "layout", {}).get("letters", [])]
    letters_layout = [
        {
            "filename": entry.get("filename"),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "x": entry.get("x"),
        }
        for entry in letters_plan_entries
    ]
    letters_asset_dir = letters_ctx.get("asset_dir")
    letters_has_letters = bool(letters_ctx.get("has_letters"))
    letters_missing_details = list(letters_ctx.get("missing", []))
    if letters_mode == "image" and letters_missing_details:
        _log_missing_letter_assets(letters_missing_details)

    if dry_run:
        return {
            "status": "dry-run",
            "out": out_path,
            "progress_bar_segments": progress_segments,
            "timer_visible": timer_visible,
            "timer_plan": timer_plan,
            "beep_schedule": beep_schedule,
            "beep_schedule_timeline": beep_schedule_timeline,
            "letters_mode": letters_mode,
            "letters_assets": letters_assets,
            "letters_missing": letters_missing_names,
            "letters_layout": letters_layout,
            "letters_asset_dir": letters_asset_dir,
            "letters_has_letters": letters_has_letters,
            "letters_missing_details": letters_missing_details,
            "entry_info": entry_ctx,
            "entry_offset_sec": entry_offset_runtime,
            "entry_duration_sec": entry_duration_runtime,
            "entry_hold_sec": entry_hold,
            "total_duration_sec": total_duration_runtime,
        }

    # compute reveal clip size early so we can avoid placing the background
    # such that it overlaps the reveal area. This uses the same _make_text
    # path the renderer uses later so runtime sizes match what gets placed.
    reveal_placement = None
    try:
        word_en = item.get("word_en", "")
        if word_en:
            # create a sample full reveal clip to measure the runtime size
            full_rc = _make_text_imageclip(
                text=word_en, font_size=128, color=(0, 0, 0),
                extra_bottom=32, duration=1,
            )
            full_w = (
                getattr(full_rc, "w", None)
                or getattr(full_rc, "size", (None, None))[0]
            )
            full_h = (
                getattr(full_rc, "h", None)
                or getattr(full_rc, "size", (None, None))[1]
            )
            full_w = int(full_w) if full_w is not None else None
            full_h = int(full_h) if full_h is not None else None
            # compute the y position used later in the renderer
            safe_bottom_margin = 32
            if full_h is not None:
                reveal_pos_y = max(0, 1080 - full_h - safe_bottom_margin)
                reveal_pos_x = None
                if full_w is not None:
                    reveal_pos_x = max(0, (1920 - full_w) // 2)
                reveal_placement = (
                    reveal_pos_x, reveal_pos_y, full_w, full_h
                )
    except Exception:
        reveal_placement = None

    # prepare background: always use a white full-screen ColorClip
    bg = (
        _mpy.ColorClip(size=(1920, 1080), color=MAIN_BG_COLOR)
        .with_duration(duration)
    )
    clips = [bg]

    # If an image is provided, load via Pillow, scale to fit a centered
    # square region and overlay it in the center of the video.
    img_path = item.get("image_path")
    bg_used = False
    bg_error = None
    bg_placement = None
    if img_path and os.path.isfile(img_path):
        # support both static images and video files as central background
        img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
        vid_exts = (".mp4", ".mov", ".mkv", ".avi", ".webm")
        try:
            if img_path.lower().endswith(img_exts):
                # Image path: render single ImageClip stretched to a centered
                from PIL import Image as _PILImage

                pil_img = _PILImage.open(img_path).convert("RGBA")
                # define centered square size (max square side)
                square_size = int(min(1920, 1080) * 0.7)  # 70% of shorter dim
                w0, h0 = pil_img.size
                scale = min(square_size / w0, square_size / h0)
                new_w = max(1, int(w0 * scale))
                new_h = max(1, int(h0 * scale))
                pil_img = pil_img.resize((new_w, new_h), _PILImage.LANCZOS)
                arr = _np.array(pil_img)
                # Ensure the centered image won't overlap the reveal area.
                # Cap its height if necessary so centered placement stays
                # above the reveal top.
                try:
                    # determine reveal_top using runtime measurement or
                    # fallback to compute_layout_bboxes
                    rbox = None
                    if (
                        reveal_placement is not None
                        and reveal_placement[1] is not None
                    ):
                        reveal_top = int(reveal_placement[1])
                    else:
                        rbox = compute_layout_bboxes(item).get(
                            "reveal"
                        )
                        reveal_top = None
                        if rbox is not None:
                            reveal_top = int(rbox.get("y", 0))
                    if reveal_top is not None:
                        margin = 16
                        # allowed_h ensures (center_y - new_h/2) + new_h
                        # <= reveal_top - margin; solve for allowed_h
                        allowed_h = int(
                            max(1, 2 * reveal_top - 2 * margin - 1080)
                        )
                        if new_h > allowed_h:
                            scale2 = allowed_h / float(new_h)
                            new_h = max(1, int(new_h * scale2))
                            new_w = max(1, int(new_w * scale2))
                            pil_img = pil_img.resize(
                                (new_w, new_h), _PILImage.LANCZOS
                            )
                            arr = _np.array(pil_img)
                except Exception:
                    pass
                img_clip = _mpy.ImageClip(arr).with_duration(duration)
                # position centered
                pos_x = (1920 - new_w) // 2
                pos_y = (1080 - new_h) // 2
                # avoid overlapping the reveal area using runtime reveal
                # placement if available (preferred), otherwise fall back
                # to compute_layout_bboxes estimate.
                try:
                    if (
                        reveal_placement is not None
                        and reveal_placement[1] is not None
                    ):
                        reveal_top = int(reveal_placement[1])
                    else:
                        rbox = compute_layout_bboxes(item).get("reveal")
                        reveal_top = (
                            int(rbox.get("y", 0)) if rbox is not None else None
                        )
                    if reveal_top is not None and pos_y + new_h > reveal_top:
                        pos_y = max(0, reveal_top - new_h - 8)
                except Exception:
                    pass

                img_clip = img_clip.with_position((pos_x, pos_y))
                clips.append(img_clip)
                bg_used = True
                bg_placement = (pos_x, pos_y, new_w, new_h)
            elif img_path.lower().endswith(vid_exts):
                # Video path: load VideoFileClip and apply scaling based on
                # video_mode. 'fit' scales to fit within bounds (no cropping),
                # 'cover' scales to fill bounds (with center cropping).
                try:
                    VideoFileClip = None
                    try:
                        # import VideoFileClip from moviepy.editor if available
                        from moviepy.editor import (
                            VideoFileClip as _V,
                        )
                        VideoFileClip = _V
                    except Exception:
                        # fallback to top-level
                        try:
                            import moviepy as _m

                            VideoFileClip = getattr(_m, "VideoFileClip", None)
                        except Exception:
                            VideoFileClip = None

                    if VideoFileClip is not None:
                        vclip = VideoFileClip(img_path)
                        # target centered square size (70% of shorter dim)
                        box_side = int(min(1920, 1080) * 0.7)

                        # Get video_mode from config, default to 'fit'
                        video_mode = item.get("video_mode", "fit")

                        # Get original video dimensions
                        vw, vh = vclip.size
                        vw = max(1, vw)  # avoid division by zero
                        vh = max(1, vh)

                        # Before scaling, ensure the target box won't force
                        # the centered video to overlap the reveal area.
                        target_box_side = box_side
                        try:
                            if (
                                reveal_placement is not None
                                and reveal_placement[1] is not None
                            ):
                                reveal_top = int(reveal_placement[1])
                            else:
                                rbox = compute_layout_bboxes(item).get(
                                    "reveal"
                                )
                                reveal_top = None
                                if rbox is not None:
                                    reveal_top = int(rbox.get("y", 0))
                            if reveal_top is not None:
                                margin = 16
                                # For centered video: height should be at most
                                # 2 * (reveal_top - margin) to avoid overlap
                                max_allowed_h = max(
                                    1, 2 * (reveal_top - margin))
                                target_box_side = min(
                                    target_box_side, max_allowed_h)
                        except Exception:
                            pass

                        if video_mode == "cover":
                            # Cover mode: scale to fill the target box,
                            # then crop to exact box dimensions
                            scale = max(target_box_side / vw,
                                        target_box_side / vh)
                            scaled_w = max(1, int(vw * scale))
                            scaled_h = max(1, int(vh * scale))

                            # Resize video to scaled dimensions
                            v_resized = None
                            try:
                                v_resized = vclip.resized((scaled_w, scaled_h))
                            except Exception:
                                try:
                                    v_resized = _mpy.vfx.resize(
                                        vclip, newsize=(scaled_w, scaled_h)
                                    )
                                except Exception:
                                    try:
                                        v_resized = vclip.fx(
                                            _mpy.vfx.resize,
                                            newsize=(scaled_w, scaled_h)
                                        )
                                    except Exception:
                                        v_resized = vclip
                                        scaled_w, scaled_h = vw, vh

                            # Center crop to target box size
                            crop_x = max(0, (scaled_w - target_box_side) // 2)
                            crop_y = max(0, (scaled_h - target_box_side) // 2)

                            try:
                                v_cropped = v_resized.cropped(
                                    x1=crop_x, y1=crop_y,
                                    x2=crop_x + target_box_side,
                                    y2=crop_y + target_box_side
                                )
                                new_w = new_h = target_box_side
                            except Exception:
                                # If cropping fails, use the resized video
                                v_cropped = v_resized
                                new_w, new_h = scaled_w, scaled_h

                        else:  # fit mode (default)
                            # Fit mode: scale to fit within target box bounds
                            scale = min(target_box_side / vw,
                                        target_box_side / vh)
                            new_w = max(1, int(vw * scale))
                            new_h = max(1, int(vh * scale))

                            # Resize using whichever API is available
                            try:
                                v_cropped = vclip.resized((new_w, new_h))
                            except Exception:
                                try:
                                    v_cropped = _mpy.vfx.resize(
                                        vclip, newsize=(new_w, new_h)
                                    )
                                except Exception:
                                    try:
                                        v_cropped = vclip.fx(
                                            _mpy.vfx.resize,
                                            newsize=(new_w, new_h)
                                        )
                                    except Exception:
                                        v_cropped = vclip
                                        new_w, new_h = vw, vh

                        # Ensure the clip spans the full composition duration
                        # by looping it if needed
                        video_duration = getattr(v_cropped, "duration", 0)
                        try:
                            if video_duration < duration:
                                # Try approaches to create looped video
                                v_looped = None

                                # First, try the modern moviepy loop approach
                                try:
                                    v_looped = _mpy.vfx.loop(
                                        v_cropped, duration=duration
                                    )
                                except Exception:
                                    try:
                                        v_looped = v_cropped.fx(
                                            _mpy.vfx.loop, duration=duration
                                        )
                                    except Exception:
                                        v_looped = None

                                # If loop failed, try concatenate approach
                                if v_looped is None:
                                    try:
                                        import math as _math

                                        # Calculate how many copies we need
                                        n = max(1, int(
                                            _math.ceil(
                                                duration / max(
                                                    0.001, video_duration
                                                )
                                            )
                                        ))
                                        clips_to_concat = [v_cropped] * n

                                        # Try different concatenate approaches
                                        try:
                                            v_concat = (
                                                _mpy.concatenate_videoclips(
                                                    clips_to_concat,
                                                    method="compose"
                                                )
                                            )
                                            v_looped = v_concat.with_duration(
                                                duration
                                            )
                                        except Exception:
                                            try:
                                                # Alt concatenate method
                                                _concat_fn = getattr(
                                                    _mpy,
                                                    "concatenate_videoclips"
                                                )
                                                v_concat = _concat_fn(
                                                    clips_to_concat
                                                )
                                                v_looped = (
                                                    v_concat.with_duration(
                                                        duration
                                                    )
                                                )
                                            except Exception:
                                                # Manual loop using subclip
                                                loop_clips = []
                                                current_time = 0
                                                while current_time < duration:
                                                    remaining = (
                                                        duration - current_time
                                                    )
                                                    if (
                                                        remaining >=
                                                        video_duration
                                                    ):
                                                        loop_clips.append(
                                                            v_cropped
                                                        )
                                                        current_time += (
                                                            video_duration
                                                        )
                                                    else:
                                                        # Partial clip for end
                                                        loop_clips.append(
                                                            v_cropped.subclip(
                                                                0, remaining
                                                            )
                                                        )
                                                        current_time = duration
                                                try:
                                                    v_looped = (
                                                        _mpy.concatenate_videoclips(  # noqa: E501
                                                            loop_clips,
                                                            method="compose"
                                                        )
                                                    )
                                                except Exception:
                                                    # Ultimate fallback
                                                    v_looped = (
                                                        v_cropped
                                                        .with_duration(
                                                            duration
                                                        )
                                                    )
                                    except Exception:
                                        # Ultimate fallback: extend duration
                                        v_looped = v_cropped.with_duration(
                                            duration
                                        )

                                # Ensure we have a valid looped clip
                                if v_looped is None:
                                    v_looped = v_cropped.with_duration(
                                        duration
                                    )
                            else:
                                # if clip >= duration, trim to exact duration
                                try:
                                    v_looped = (
                                        v_cropped.subclip(0, duration)
                                        .with_duration(
                                            duration
                                        )
                                    )
                                except Exception:
                                    try:
                                        v_looped = (
                                            v_cropped.with_duration(
                                                duration
                                            )
                                        )
                                    except Exception:
                                        v_looped = v_cropped
                        except Exception:
                            try:
                                v_looped = (
                                    v_cropped.with_duration(
                                        duration
                                    )
                                )
                            except Exception:
                                v_looped = v_cropped

                        # Position the video in the center
                        pos_x = (1920 - new_w) // 2
                        pos_y = (1080 - new_h) // 2

                        # Adjust position if needed to avoid reveal area
                        try:
                            if (
                                reveal_placement is not None
                                and reveal_placement[1] is not None
                            ):
                                reveal_top = int(reveal_placement[1])
                            else:
                                rbox = compute_layout_bboxes(item).get(
                                    "reveal"
                                )
                                reveal_top = None
                                if rbox is not None:
                                    reveal_top = int(rbox.get("y", 0))
                            if (
                                reveal_top is not None
                                and pos_y + new_h > reveal_top
                            ):
                                pos_y = max(0, reveal_top - new_h - 8)
                        except Exception:
                            pass

                        v_final = v_looped.with_position((pos_x, pos_y))
                        clips.append(v_final)
                        bg_used = True
                        bg_placement = (pos_x, pos_y, new_w, new_h)
                    else:
                        # VideoFileClip couldn't be imported; treat as missing
                        bg_error = "moviepy VideoFileClip unavailable"
                except Exception as e:
                    bg_error = str(e)
            else:
                # unknown extension: ignore and keep white bg
                pass
        except Exception as e:
            bg_error = str(e)

    # Letters (top-left) — move lower to avoid clipping
    letters_text = letters_ctx.get("letters", "")
    if letters_has_letters:
        if letters_mode == "image":
            for entry in letters_plan_entries:
                path = entry.get("path")
                if not path or not os.path.isfile(path):
                    detail = {
                        "char": entry.get("char"),
                        "filename": entry.get("filename"),
                        "path": path,
                        "reason": "missing",
                    }
                    if detail not in letters_missing_details:
                        letters_missing_details.append(detail)
                    name = entry.get("filename") or entry.get("char")
                    if name and name not in letters_missing_names:
                        letters_missing_names.append(name)
                    continue
                try:
                    clip_letter = _mpy.ImageClip(path)
                    target_height = entry.get("height")
                    if target_height:
                        clip_letter = clip_letter.resized(
                            height=max(1, int(target_height)))
                    clip_letter = clip_letter.with_duration(duration)
                    clip_letter = clip_letter.with_position(
                        (LETTER_SAFE_X + int(entry.get("x", 0)), LETTER_SAFE_Y)
                    )
                    clips.append(clip_letter)
                except Exception as exc:
                    detail = {
                        "char": entry.get("char"),
                        "filename": entry.get("filename"),
                        "path": path,
                        "reason": "load-error",
                        "error": str(exc),
                    }
                    letters_missing_details.append(detail)
                    name = entry.get("filename") or entry.get("char")
                    if name and name not in letters_missing_names:
                        letters_missing_names.append(name)
        else:
            txt_letters = _make_text_imageclip(
                text=letters_text, font_size=140, color=(0, 0, 0), duration=duration
            )
            txt_letters = txt_letters.with_position(
                (LETTER_SAFE_X, LETTER_SAFE_Y))
            clips.append(txt_letters)

    # Chinese + zhuyin (top-right) — render per-character with vertical zhuyin
    word_zh = item.get("word_zh", "")
    zhuyin = zhuyin_for(word_zh)
    if word_zh:
        font_candidates = [
            r"C:\Windows\Fonts\msjh.ttf",
            r"C:\Windows\Fonts\msjhbd.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        font_path = None
        for p in font_candidates:
            if os.path.isfile(p):
                font_path = p
                break

        try:
            from PIL import Image, ImageDraw, ImageFont

            # increase main CJK font size by 1.5x for clearer rendering
            font_size = 96
            if font_path:
                pil_font = ImageFont.truetype(font_path, font_size)
            else:
                pil_font = ImageFont.load_default()

            # split zhuyin per character (space separated by zhuyin_for)
            zh_groups = zhuyin.split() if zhuyin else []

            # measure columns to compute starting x so columns are
            # right-aligned
            cols = []
            total_w = 0
            padding = 8
            for i, ch in enumerate(word_zh):
                ch_w, ch_h = _measure_text_with_pil(ch, pil_font)
                zh_grp = zh_groups[i] if i < len(zh_groups) else ""
                zh_lines = list(zh_grp) if zh_grp else []
                symbol_count = len(zh_lines)
                gap = _zhuyin_main_gap(symbol_count)
                zh_w = 0
                zh_h = 0
                for idx_sym, sym in enumerate(zh_lines):
                    sw, sh = _measure_text_with_pil(sym, pil_font)
                    zh_w = max(zh_w, sw)
                    zh_h += sh
                    if idx_sym < symbol_count - 1:
                        zh_h += gap

                col_w = ch_w + (zh_w if zh_w else 0) + padding
                col_h = max(ch_h, zh_h)
                cols.append((ch, zh_lines, col_w, col_h))
                total_w += col_w

            img_w = int(total_w + padding)
            # create a single wide transparent image for the whole zh region
            img_h = int(max([c[3] for c in cols]) + padding * 2) if cols else 0
            img = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # draw columns left-to-right but we'll position this image anchored
            # to the right when composing (so columns appear at the right side)
            cursor_x = padding
            cursor_y = padding
            # keep coords for optional overlay/debugging
            overlay_boxes = []
            for ch, zh_lines, col_w, col_h in cols:
                # draw the main CJK char at top-left of its column
                draw.text(
                    (cursor_x, cursor_y), ch, font=pil_font, fill=(0, 0, 0)
                )
                ch_w, ch_h = _measure_text_with_pil(ch, pil_font)

                # separate main bopomofo symbols from tone marks
                tone_marks = set(["ˊ", "ˇ", "ˋ", "˙"])
                lines = zh_lines or []
                main_syms = [s for s in lines if s not in tone_marks]
                tone_syms = [s for s in lines if s in tone_marks]

                # choose a smaller zh font and iteratively reduce size until
                # stacked main symbols fit within the CJK glyph height.
                target_base = max(
                    ZHUYIN_MIN_FONT_SIZE,
                    int(ch_h * ZHUYIN_BASE_HEIGHT_RATIO),
                )
                zh_font_size = min(target_base, int(ch_h))
                zh_w = 0
                total_main_h = 0
                tone_dims: List[Tuple[int, int]] = []
                tone_max_w = 0
                symbols = main_syms if main_syms else lines
                symbol_count = len(symbols)
                main_gap = _zhuyin_main_gap(symbol_count)
                try:
                    while True:
                        try:
                            zh_font = (
                                ImageFont.truetype(font_path, zh_font_size)
                                if font_path
                                else ImageFont.load_default()
                            )
                        except Exception:
                            zh_font = ImageFont.load_default()

                        zh_w = 0
                        total_main_h = 0
                        for idx_sym, sym in enumerate(symbols):
                            sw, sh = _measure_text_with_pil(sym, zh_font)
                            zh_w = max(zh_w, sw)
                            total_main_h += sh
                            if idx_sym < symbol_count - 1:
                                total_main_h += main_gap

                        if total_main_h <= ch_h or zh_font_size <= ZHUYIN_MIN_FONT_SIZE:
                            break
                        zh_font_size -= 1
                except Exception:
                    zh_w = zh_w or 0
                    total_main_h = total_main_h or 0

                if tone_syms:
                    tone_dims = []
                    tone_max_w = 0
                    for ts in tone_syms:
                        tw, th = _measure_text_with_pil(ts, zh_font)
                        tone_dims.append((tw, th))
                        tone_max_w = max(tone_max_w, tw)

                tone_layout = _layout_zhuyin_column(
                    cursor_y=cursor_y,
                    col_h=col_h,
                    total_main_h=total_main_h,
                    tone_syms=tone_syms,
                    tone_sizes=tone_dims,
                    tone_gap=10,
                )

                # x position for bopomofo (immediately to the right)
                zh_x = cursor_x + ch_w + 2
                # force column height to CJK glyph height so overlay box won't
                # exceed the red bbox
                col_h = ch_h

                symbols = main_syms if main_syms else lines
                symbol_count = len(symbols)
                main_gap = _zhuyin_main_gap(symbol_count)

                # draw main symbols stacked vertically
                main_start_y = tone_layout["main_start_y"]
                cur_y = main_start_y
                for idx_sym, sym in enumerate(symbols):
                    draw.text((zh_x, cur_y), sym, font=zh_font, fill=(0, 0, 0))
                    sw, sh = _measure_text_with_pil(sym, zh_font)
                    cur_y += sh
                    if idx_sym < symbol_count - 1:
                        cur_y += main_gap

                # draw tone marks (if any). Neutral tone (˙) is centered above the main block.
                tone_box = None
                tone_start_y = tone_layout.get("tone_start_y")
                tone_box_height = tone_layout.get("tone_box_height", 0)
                tone_alignment = tone_layout.get("tone_alignment", "right")

                if tone_syms and tone_start_y is not None:
                    if tone_alignment == "center":
                        tone_w = tone_dims[0][0] if tone_dims else 0
                        tone_x = zh_x + max(0, (int(zh_w) - tone_w) // 2)
                    else:
                        # place tone touching bopomofo, then shift left 2px
                        # (small visual nudge to sit closer to bopomofo)
                        tone_x = zh_x + int(zh_w) - 2
                    tcur = tone_start_y
                    for idx, ts in enumerate(tone_syms):
                        if idx < len(tone_dims):
                            tw, th = tone_dims[idx]
                        else:
                            tw, th = _measure_text_with_pil(ts, zh_font)
                        draw.text((tone_x, tcur), ts,
                                  font=zh_font, fill=(0, 0, 0))
                        tcur += th + 2

                    if tone_alignment == "center":
                        tone_w = tone_dims[0][0] if tone_dims else 0
                        tone_h = tone_box_height or (
                            tone_dims[0][1] if tone_dims else 0)
                        tone_box = (
                            tone_x,
                            tone_start_y,
                            tone_x + max(1, int(tone_w)),
                            tone_start_y + max(1, int(tone_h)),
                        )
                    else:
                        half_tone_w = max(1, int(tone_max_w / 2))
                        tone_box = (
                            tone_x,
                            tone_start_y,
                            tone_x + half_tone_w,
                            tone_start_y +
                            int(tone_box_height or total_main_h),
                        )

                # record overlay boxes for debugging
                overlay_boxes.append(
                    {
                        "ch": (
                            cursor_x,
                            cursor_y,
                            cursor_x + ch_w,
                            cursor_y + ch_h,
                        ),
                        # bopomofo box (red)
                        "zh": (
                            zh_x,
                            main_start_y,
                            zh_x + max(1, int(zh_w)),
                            main_start_y + int(total_main_h),
                        ),
                        # tone box (green) - may be absent if no tone
                        "tone": tone_box if tone_syms else None,
                        "col_h": col_h,
                    }
                )

                cursor_x += col_w

            # optional debug overlay: save an annotated image when requested
                try:
                    dbg_overlay = os.environ.get("SPELLVID_DEBUG_OVERLAY")
                    dbg_skip = os.environ.get("SPELLVID_DEBUG_SKIP_WRITE")
                    if dbg_overlay or dbg_skip:
                        import time as _time

                        overlay_img = img.copy()
                        od = ImageDraw.Draw(overlay_img)
                        for i, b in enumerate(overlay_boxes):
                            # draw CJK char bbox in gray (neutral)
                            try:
                                od.rectangle(
                                    b["ch"], outline=(128, 128, 128), width=1
                                )
                            except Exception:
                                pass
                            # draw bopomofo (zh) in RED
                            try:
                                od.rectangle(
                                    b["zh"], outline=(255, 0, 0), width=2
                                )
                            except Exception:
                                pass
                            # draw tone in GREEN if present
                            try:
                                if b.get("tone"):
                                    od.rectangle(
                                        b["tone"],
                                        outline=(0, 255, 0),
                                        width=2,
                                    )
                            except Exception:
                                pass
                            # write index label near top-left of CJK char box
                            try:
                                od.text(
                                    (b["ch"][0], b["ch"][1] - 12),
                                    str(i + 1),
                                    fill=(0, 0, 0),
                                )
                            except Exception:
                                pass

                        snapshot_dir = os.path.join(
                            os.path.dirname(__file__), "..", "scripts"
                        )
                        snapshot_dir = os.path.abspath(snapshot_dir)
                        os.makedirs(snapshot_dir, exist_ok=True)
                        overlay_path = os.path.join(
                            snapshot_dir, f"zh_overlay-{int(_time.time())}.png"
                        )
                        overlay_img.save(overlay_path)
                        print("Wrote zh overlay debug image:", overlay_path)
                except Exception:
                    pass

            arr = _np.array(img)
            txt_zh_clip = _mpy.ImageClip(arr).with_duration(duration)
            pos_x = 1920 - 64 - txt_zh_clip.w
            txt_zh_clip = txt_zh_clip.with_position((pos_x, 64))
            clips.append(txt_zh_clip)
        except Exception:
            # fallback: small TextClip with default font
            t = _mpy.TextClip(
                text=word_zh, font_size=48, font=None, color="black"
            )
            t = t.with_position((1920 - 64 - t.w, 64)).with_duration(duration)
            clips.append(t)

    # Timer overlay: create per-second TextClips when visible.
    if timer_visible and timer_plan:
        for entry in timer_plan:
            timer_text = entry.get("text", "")
            timer_duration = max(0.0, float(entry.get("duration", 0.0)))
            if timer_duration == 0.0:
                continue
            start_time = float(entry.get("start", 0.0))
            tclip = _make_text_imageclip(
                text=timer_text,
                font_size=64,
                color=(255, 255, 255),
                bg=(0, 0, 0),
                duration=timer_duration,
            )
            # moved down from 420 to 450 to avoid bottom clipping
            tclip = tclip.with_position((64, 450)).with_start(start_time)
            clips.append(tclip)

    # Reveal typewriter: show substrings sequentially. Each letter appears
    # at a fixed interval (`per` seconds). Each substring clip is started
    # at the appropriate time and kept visible until the end of the video
    # so the word grows cumulatively. The `reveal_hold_sec` only controls
    # how long the finished reveal remains on screen after the last letter.
    word_en = item.get("word_en", "")
    if word_en:
        n = max(1, len(word_en))
        # per defined earlier as fixed 1.0s; ensure it's present in scope
        try:
            per
        except NameError:
            per = 1.0
        safe_bottom_margin = 48
        # Compute the full reveal image size once so every substring
        # clip can be rendered on that fixed canvas. This avoids changing
        # clip widths during the typewriter effect which would otherwise
        # shift other positioned clips.
        try:
            full_rc = _make_text_imageclip(
                text=word_en, font_size=128, color=(0, 0, 0),
                extra_bottom=48, duration=1,
            )
            full_w = (
                getattr(full_rc, "w", None)
                or getattr(full_rc, "size", (None, None))[0]
            )
            full_h = (
                getattr(full_rc, "h", None)
                or getattr(full_rc, "size", (None, None))[1]
            )
            if full_w is None or full_h is None:
                raise Exception("could not determine full reveal size")
            fixed_canvas = (int(full_w), int(full_h))
        except Exception:
            # fallback to a reasonable fixed size based on font heuristics
            fixed_canvas = (int(len(word_en) * 128 * 0.6) + 48, 128 + 48 + 32)

        for idx in range(1, n + 1):
            sub = word_en[:idx]
            # start time for this substring
            start = countdown + (idx - 1) * per
            # keep substring visible until end of video
            remaining = max(0.0, duration - start)
            # reserve extra bottom space inside reveal image so underlines
            # can be drawn below glyphs without overlapping.
            rc = _make_text_imageclip(
                text=sub, font_size=128, color=(0, 0, 0), duration=remaining,
                extra_bottom=48, fixed_size=fixed_canvas,
            )
            # compute a y position so the reveal clip sits above the bottom
            # by safe_bottom_margin to avoid glyph descent clipping
            try:
                clip_h = getattr(rc, "h", None)
                if clip_h is None:
                    clip_h = getattr(rc, "size", (None, None))[1]
                clip_h = int(clip_h)
            except Exception:
                clip_h = 128 + max(8, 128 // 6) * 2
            pos_y = max(0, 1080 - clip_h - safe_bottom_margin)
            rc = rc.with_position(("center", pos_y)).with_start(start)
            clips.append(rc)

        # If reveal_underlines metadata exists (from compute_layout_bboxes),
        # create small ImageClips for each underline and overlay them at
        # absolute positions so they appear under the reveal text.
        # Default style: white underline, 4px height.
        try:
            r_meta = compute_layout_bboxes(item).get("reveal_underlines")
            r_box = compute_layout_bboxes(item).get("reveal")
        except Exception:
            r_meta = None
            r_box = None

        if r_meta and r_box and _HAS_MOVIEPY:
            try:
                for ul in r_meta:
                    abs_x = int(r_box["x"] + ul.get("x", 0))
                    abs_y = int(r_box["y"] + ul.get("y", 0))
                    w = max(1, int(ul.get("w", 1)))
                    h = max(1, int(ul.get("h", 1)))
                    # create solid RGBA image for underline
                    try:
                        import numpy as _np_local

                        rgba = _np_local.zeros(
                            (h, w, 4), dtype=_np_local.uint8)
                        rgba[..., :3] = _np_local.array(
                            (0, 0, 0), dtype=_np_local.uint8)
                        rgba[..., 3] = 255
                        ul_clip = _mpy.ImageClip(rgba).with_duration(duration)
                        ul_clip = ul_clip.with_position((abs_x, abs_y))
                        clips.append(ul_clip)
                    except Exception:
                        # fallback: draw using ColorClip if numpy unavailable
                        try:
                            ul_clip = _mpy.ColorClip(size=(w, h), color=(
                                0, 0, 0)).with_duration(duration)
                            ul_clip = ul_clip.with_position((abs_x, abs_y))
                            clips.append(ul_clip)
                        except Exception:
                            pass
            except Exception:
                pass

    if progress_enabled and progress_segments:
        base_bar_y = 1080 - PROGRESS_BAR_HEIGHT - 24
        bar_y = base_bar_y
        if reveal_placement:
            try:
                _, rp_y, _, rp_h = reveal_placement
                if rp_y is not None and rp_h is not None:
                    reveal_bottom = int(rp_y) + int(rp_h)
                    candidate = reveal_bottom + 24
                    bar_y = min(max(0, candidate), base_bar_y)
            except Exception:
                bar_y = base_bar_y
        try:
            base_color, base_mask = _progress_bar_base_arrays(
                PROGRESS_BAR_WIDTH)
        except Exception:
            base_color = None
            base_mask = None
        for seg in progress_segments:
            width = int(seg.get("width", 0))
            if width <= 0:
                continue
            seg_start = float(seg.get("start", 0.0))
            seg_end = float(seg.get("end", seg_start))
            seg_duration = max(0.0, seg_end - seg_start)
            if seg_duration <= 0.0:
                continue
            x_start = int(seg.get("x_start", PROGRESS_BAR_WIDTH - width))
            if base_color is None or base_mask is None:
                continue
            if x_start < 0:
                x_start = 0
            x_end = min(PROGRESS_BAR_WIDTH, x_start + width)
            if x_end <= x_start:
                continue
            color_slice = base_color[:, x_start:x_end, :]
            mask_slice = base_mask[:, x_start:x_end]
            if color_slice.size == 0 or mask_slice.size == 0:
                continue
            try:
                clip = _mpy.ImageClip(
                    color_slice.copy()).with_duration(seg_duration)
            except Exception:
                continue
            mask_clip = None
            try:
                mask_clip = _make_progress_bar_mask(mask_slice, seg_duration)
            except Exception:
                mask_clip = None
            if mask_clip is not None:
                try:
                    clip = clip.with_mask(mask_clip)
                except Exception:
                    mask_clip = None
            clip = clip.with_start(seg_start).with_position(
                (PROGRESS_BAR_SAFE_X + x_start, bar_y)
            )
            clips.append(clip)

    main_clip = _mpy.CompositeVideoClip(clips, size=(1920, 1080))
    main_clip = main_clip.with_duration(duration)

    # Audio: optional music + beep in last 3 seconds
    audio_clips = []
    music_path = item.get("music_path")
    audio_loaded = False
    audio_error = None
    if music_path and os.path.isfile(music_path):
        try:
            # ensure ffmpeg is available for moviepy to read audio
            ffprobe_ok = shutil.which("ffprobe")
            if not ffprobe_ok:
                ffprobe_ok = os.environ.get("IMAGEIO_FFMPEG_EXE")
                # no ffprobe on PATH; will try IMAGEIO_FFMPEG_EXE if set
            af = _mpy.AudioFileClip(music_path)
            try:
                src_dur = float(getattr(af, "duration", 0.0) or 0.0)
            except Exception:
                src_dur = 0.0

            # If source audio shorter than desired duration, concatenate
            # multiple copies so the writer won't read past EOF.
            try:
                if src_dur <= 0.0:
                    # unusable source duration
                    raise RuntimeError("source audio has zero duration")

                if src_dur < duration:
                    # figure how many repeats needed
                    import math as _math

                    n = int(_math.ceil(duration / src_dur))
                    # create repeated clips with start offsets so the
                    # composite covers the whole duration. Avoid calling
                    # .subclip on CompositeAudioClip which may not exist.
                    comp_clips = []
                    start = 0.0
                    for _ in range(n):
                        comp_clips.append(af.with_start(start))
                        start += src_dur
                    music = _mpy.CompositeAudioClip(comp_clips)
                else:
                    # source is long enough; take beginning portion
                    if hasattr(af, "subclip"):
                        music = af.subclip(0, duration)
                    else:
                        # try with_duration as fallback
                        try:
                            music = af.with_duration(duration)
                        except Exception:
                            music = af

                # best-effort: ensure final clip has expected duration
                try:
                    music = music.with_duration(duration)
                except Exception:
                    pass

            except Exception:
                # propagate to outer except so audio_error is recorded
                raise

            audio_clips.append(music)
            audio_loaded = True
        except Exception as e:
            # record failure to load music so callers/tests can detect it
            audio_loaded = False
            try:
                audio_error = str(e)
            except Exception:
                audio_error = "(error stringify failed)"
            # keep going — renderer can still produce video without music
            pass

    # beep: generate short sine beeps aligned to the countdown display
    # using the precomputed schedule from timer visibility planning.
    def make_beep(start_sec):
        freq = 1000.0
        length = 0.3

        def make_frame(t):
            # t may be array-like; compute sine and return mono samples
            mono = (_np.sin(2 * _np.pi * freq * t) * 0.2).astype(_np.float32)
            # ensure a 2-channel (stereo) array to match common audio
            # track shapes and avoid broadcasting errors during mix
            try:
                stereo = _np.column_stack((mono, mono))
            except Exception:
                stereo = mono.reshape(-1, 1)
            return stereo

        ac = _mpy.AudioClip(make_frame, duration=length, fps=44100)
        return ac.with_start(start_sec)

    for start in beep_schedule:
        try:
            audio_clips.append(make_beep(start))
        except Exception:
            pass

    if audio_clips:
        try:
            final_audio = _mpy.CompositeAudioClip(audio_clips)
            main_clip = main_clip.with_audio(final_audio)
        except Exception:
            pass

    # Apply fade-out effect to main content (D1: all videos fade out uniformly)
    # This is applied before concatenating with entry/ending clips
    # Note: ending.mp4 will not have additional fade-out (D8 decision)
    main_clip = _apply_fadeout(main_clip, duration=FADE_OUT_DURATION)

    entry_loaded = False
    entry_error = None
    entry_clip_obj = None
    hold_clip = None
    cleanup_clips: List[Any] = []

    def _ensure_dimensions(clip):
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

    def _ensure_fullscreen_cover(clip):
        try:
            size = getattr(clip, "size", None)
            if not size:
                return clip
            w, h = float(size[0]), float(size[1])
            if w <= 0 or h <= 0:
                return clip
            target_w, target_h = 1920.0, 1080.0
            # 總是執行非等比例縮放，確保完整畫面無裁剪
            try:
                clip = clip.resized(new_size=(int(target_w), int(target_h)))
            except Exception:
                return clip
        except Exception:
            pass
        return clip

    def _auto_letterbox_crop(clip):
        try:
            sample_points = [0.0]
            try:
                dur = float(getattr(clip, "duration", 0.0) or 0.0)
            except Exception:
                dur = 0.0
            if dur > 0.5:
                sample_points.append(max(0.0, dur / 2.0))
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
            arr = _np.asarray(frame)
            if arr.ndim == 3:
                gray = arr.mean(axis=2)
            else:
                gray = arr.astype(float)
            valid = gray > 15.0
            if not valid.any():
                return clip
            rows = _np.where(valid.any(axis=1))[0]
            cols = _np.where(valid.any(axis=0))[0]
            if rows.size == 0 or cols.size == 0:
                return clip
            top, bottom = int(rows[0]), int(rows[-1])
            left, right = int(cols[0]), int(cols[-1])
            if top <= 2 and left <= 2 and bottom >= arr.shape[0] - 3 and right >= arr.shape[1] - 3:
                return clip
            pad = 2
            top = max(0, top - pad)
            left = max(0, left - pad)
            bottom = min(arr.shape[0] - 1, bottom + pad)
            right = min(arr.shape[1] - 1, right + pad)
            return clip.cropped(x1=float(left), y1=float(top), x2=float(right + 1), y2=float(bottom + 1))
        except Exception:
            return clip

    if entry_ctx.get("exists"):
        try:
            entry_clip_obj = _mpy.VideoFileClip(entry_ctx["path"])
            cleanup_clips.append(entry_clip_obj)
            entry_clip_obj = _ensure_dimensions(entry_clip_obj)
            entry_loaded = True
            # If the primary entry clip lacks audio, try a fallback
            # asset (entry_with_music.mp4) that ships with the repo so
            # the composed output will include an audible entry intro.
            try:
                has_audio = getattr(entry_clip_obj, "audio", None) is not None
                aud_dur = 0.0
                if has_audio:
                    try:
                        aud_dur = float(
                            getattr(
                                entry_clip_obj.audio, "duration", 0.0
                            )
                            or 0.0
                        )
                    except Exception:
                        aud_dur = 0.0
                if not has_audio or aud_dur <= 0.001:
                    # attempt to load fallback file from repo assets
                    try:
                        repo_root = os.path.abspath(
                            os.path.join(os.path.dirname(__file__), "..")
                        )
                        fallback = os.path.join(
                            repo_root, "assets", "entry_with_music.mp4"
                        )
                        if os.path.isfile(fallback):
                            # close previous clip before replacing
                            try:
                                entry_clip_obj.close()
                            except Exception:
                                pass
                            entry_clip_obj = _mpy.VideoFileClip(fallback)
                            cleanup_clips.append(entry_clip_obj)
                            entry_clip_obj = _ensure_dimensions(entry_clip_obj)
                            entry_ctx["path"] = fallback
                            entry_loaded = True
                    except Exception:
                        # ignore fallback failure and continue with primary
                        pass
            except Exception:
                # non-fatal: don't block rendering if audio introspection fails
                pass
            try:
                probed = getattr(entry_clip_obj, "duration", None)
                if probed is not None and probed > 0:
                    entry_duration_runtime = float(probed)
                    entry_offset_runtime = entry_duration_runtime + entry_hold
                    total_duration_runtime = (
                        entry_offset_runtime + main_duration
                    )
            except Exception:
                pass
        except Exception as exc:
            entry_clip_obj = None
            entry_loaded = False
            try:
                entry_error = str(exc)
            except Exception:
                entry_error = "failed to load entry clip"

    if entry_hold > 0:
        try:
            if entry_clip_obj is not None:
                last_t = float(
                    max(0.0, (entry_clip_obj.duration or 0.0) - 0.04)
                )
                try:
                    hold_source = entry_clip_obj.to_ImageClip(t=last_t)
                except Exception:
                    frame = entry_clip_obj.get_frame(last_t)
                    hold_source = _mpy.ImageClip(frame)
                hold_clip = hold_source.with_duration(entry_hold)
                hold_clip = _ensure_dimensions(hold_clip)
            else:
                hold_clip = _mpy.ColorClip(
                    size=(1920, 1080), color=(0, 0, 0)
                ).with_duration(entry_hold)
            cleanup_clips.append(hold_clip)
        except Exception as exc:
            hold_clip = None
            if entry_error is None:
                try:
                    entry_error = f"entry hold failed: {exc}"
                except Exception:
                    entry_error = "entry hold failed"

    # Apply skip_ending logic: if skip_ending=True, don't load ending
    if skip_ending:
        ending_duration_runtime = 0.0
        ending_clip_obj = None
    elif not ending_ctx.get("enabled", True):
        ending_duration_runtime = 0.0
        ending_clip_obj = None
    elif ending_ctx.get("exists"):
        try:
            ending_clip_raw = _mpy.VideoFileClip(ending_ctx["path"])
            cleanup_clips.append(ending_clip_raw)
            processed_clip = ending_clip_raw
            transformers = (
                _auto_letterbox_crop,
                _ensure_dimensions,
                _ensure_fullscreen_cover,
            )
            for transformer in transformers:
                try:
                    candidate = transformer(processed_clip)
                except Exception:
                    candidate = processed_clip
                if candidate is None:
                    candidate = processed_clip
                if candidate is not processed_clip:
                    cleanup_clips.append(candidate)
                    processed_clip = candidate
            ending_clip_obj = processed_clip
            ending_loaded = True
            try:
                clip_dur = float(
                    getattr(ending_clip_obj, "duration", 0.0) or 0.0)
            except Exception:
                clip_dur = 0.0
            if clip_dur > 0.0:
                ending_duration_runtime = clip_dur
        except Exception as exc:
            ending_clip_obj = None
            ending_loaded = False
            try:
                ending_error = f"ending load failed: {exc}"
            except Exception:
                ending_error = "ending load failed"
    else:
        ending_clip_obj = None

    concat_clips = []
    if entry_clip_obj is not None:
        concat_clips.append(entry_clip_obj)
        if hold_clip is not None and hold_clip is not entry_clip_obj:
            concat_clips.append(hold_clip)
    elif hold_clip is not None:
        concat_clips.append(hold_clip)
    concat_clips.append(main_clip)
    # Only append ending if not skipped
    if ending_clip_obj is not None and not skip_ending:
        concat_clips.append(ending_clip_obj)

    if len(concat_clips) == 1:
        final_clip = main_clip
    else:
        try:
            final_clip = _mpy.concatenate_videoclips(
                concat_clips, method="compose"
            )
        except Exception:
            final_clip = _mpy.concatenate_videoclips(concat_clips)

    final_duration = (
        float(
            getattr(final_clip, "duration", total_duration_runtime)
            or total_duration_runtime
        )
        if final_clip is not None
        else total_duration_runtime
    )
    total_duration_runtime = final_duration
    ending_offset_runtime = runtime_after_main
    if ending_ctx.get("enabled", True) and (ending_clip_obj is not None or ending_ctx.get("exists")):
        ending_duration_runtime = max(
            0.0, final_duration - ending_offset_runtime)
    else:
        ending_duration_runtime = 0.0
    if ending_duration_runtime < 0.0:
        ending_duration_runtime = 0.0

    try:
        for seg in progress_segments:
            rel_start = float(seg.get("start", 0.0))
            rel_end = float(seg.get("end", seg.get("start", 0.0)))
            seg["timeline_start"] = round(
                entry_offset_runtime + rel_start, 6
            )
            seg["timeline_end"] = round(
                entry_offset_runtime + rel_end, 6
            )
    except Exception:
        pass

    try:
        for tp in timer_plan:
            rel_start = float(tp.get("start", 0.0))
            tp["timeline_start"] = round(
                entry_offset_runtime + rel_start, 6
            )
            tp["timeline_end"] = round(
                tp["timeline_start"] + float(tp.get("duration", 0.0)), 6
            )
    except Exception:
        pass

    beep_schedule_timeline = [
        round(entry_offset_runtime + t, 6) for t in beep_schedule
    ]

    # Update ending_runtime after actual loading
    ending_runtime = dict(ending_ctx)
    ending_runtime["loaded"] = ending_loaded
    ending_runtime["error"] = ending_error
    ending_runtime["duration_sec"] = ending_duration_runtime
    ending_runtime["total_tail_sec"] = ending_duration_runtime
    try:
        size_attr = getattr(ending_clip_obj, "size", None)
        if size_attr:
            ending_runtime["size"] = (int(size_attr[0]), int(size_attr[1]))
        else:
            ending_runtime["size"] = None
    except Exception:
        ending_runtime["size"] = None

    # ensure out dir
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # debug mode: optionally skip full mp4 write to avoid ffmpeg overwriting
    if os.environ.get('SPELLVID_DEBUG_SKIP_WRITE'):
        try:
            import time as _time
            # write a final frame snapshot instead of full mp4
            snapshot_dir = os.path.join(
                os.path.dirname(__file__), '..', 'scripts'
            )
            snapshot_dir = os.path.abspath(snapshot_dir)
            os.makedirs(snapshot_dir, exist_ok=True)
            snapshot_path = os.path.join(
                snapshot_dir, f'final_snapshot-{int(_time.time())}.png'
            )
            try:
                final_clip.save_frame(snapshot_path, t=0)
                print(f'Wrote final composite snapshot: {snapshot_path}')
            except Exception as _e:
                print('Failed to write final snapshot:', _e)
        finally:
            try:
                final_clip.close()
            except Exception:
                pass
            for extra in cleanup_clips:
                try:
                    extra.close()
                except Exception:
                    pass
        return {
            "status": "debug-snapshot",
            "snapshot": snapshot_path,
            "out": out_path,
            "bg_placement": bg_placement,
            "bg_used": bg_used,
            "bg_error": bg_error,
            "audio_loaded": audio_loaded,
            "audio_error": audio_error,
            "progress_bar_segments": progress_segments,
            "timer_visible": timer_visible,
            "timer_plan": timer_plan,
            "beep_schedule": beep_schedule,
            "beep_schedule_timeline": beep_schedule_timeline,
            "entry_info": {
                **entry_ctx,
                "loaded": entry_loaded,
                "error": entry_error,
                "duration_sec": entry_duration_runtime,
                "total_lead_sec": entry_offset_runtime,
            },
            "entry_offset_sec": entry_offset_runtime,
            "entry_duration_sec": entry_duration_runtime,
            "entry_hold_sec": entry_hold,
            "ending_info": ending_runtime,
            "ending_offset_sec": ending_offset_runtime,
            "ending_duration_sec": ending_duration_runtime,
            "total_duration_sec": total_duration_runtime,
        }

    # write the file
    try:
        # if ffmpeg is available via IMAGEIO_FFMPEG_EXE,
        # write with explicit codecs
        ffmpeg_exe = os.environ.get("IMAGEIO_FFMPEG_EXE")
        if ffmpeg_exe:
            final_clip.write_videofile(
                out_path,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="medium",
            )
        else:
            # fallback: simple call
            final_clip.write_videofile(out_path, fps=30)
    finally:
        # close resources
        try:
            final_clip.close()
        except Exception:
            pass
        for extra in cleanup_clips:
            try:
                extra.close()
            except Exception:
                pass

    entry_runtime = {
        **entry_ctx,
        "loaded": entry_loaded,
        "error": entry_error,
        "duration_sec": entry_duration_runtime,
        "total_lead_sec": entry_offset_runtime,
    }

    return {
        "status": "ok",
        "out": out_path,
        "bg_used": bg_used,
        "bg_error": bg_error,
        "audio_loaded": audio_loaded,
        "audio_error": audio_error,
        "bg_placement": bg_placement,
        "progress_bar_segments": progress_segments,
        "timer_visible": timer_visible,
        "timer_plan": timer_plan,
        "beep_schedule": beep_schedule,
        "beep_schedule_timeline": beep_schedule_timeline,
        "entry_info": entry_runtime,
        "entry_offset_sec": entry_offset_runtime,
        "entry_duration_sec": entry_duration_runtime,
        "entry_hold_sec": entry_hold,
        "ending_info": ending_runtime,
        "ending_offset_sec": ending_offset_runtime,
        "ending_duration_sec": ending_duration_runtime,
        "total_duration_sec": total_duration_runtime,
    }


# ========== Public API Definition ==========
# Export list for backward compatibility
__all__ = [
    # Core rendering functions
    'render_video_stub',
    'render_video_moviepy',
    'compute_layout_bboxes',
    'check_assets',
    'synthesize_beeps',
    # Constants - Canvas
    'CANVAS_WIDTH',
    'CANVAS_HEIGHT',
    # Constants - Progress bar
    'PROGRESS_BAR_SAFE_X',
    'PROGRESS_BAR_MAX_X',
    'PROGRESS_BAR_WIDTH',
    'PROGRESS_BAR_HEIGHT',
    'PROGRESS_BAR_COLORS',
    'PROGRESS_BAR_RATIOS',
    'PROGRESS_BAR_CORNER_RADIUS',
    # Constants - Letters
    'LETTER_SAFE_X',
    'LETTER_SAFE_Y',
    'LETTER_AVAILABLE_WIDTH',
    'LETTER_TARGET_HEIGHT',
    'LETTER_BASE_GAP',
    'LETTER_EXTRA_SCALE',
    # Constants - Colors
    'MAIN_BG_COLOR',
    'COLOR_WHITE',
    # Schema
    'SCHEMA',
    # Test helpers (internal, for testing only)
    '_make_text_imageclip',
    '_mpy',
    '_HAS_MOVIEPY',
    '_find_and_set_ffmpeg',
]
