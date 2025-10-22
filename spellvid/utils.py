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
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._coerce_non_negative_float
    """
    from spellvid.application.context_builder import (
        _coerce_non_negative_float as _impl
    )
    return _impl(value, default)


def _resolve_entry_video_path(item: Dict[str, Any] | None = None) -> str:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._resolve_entry_video_path
    """
    from spellvid.application.context_builder import (
        _resolve_entry_video_path as _impl
    )
    return _impl(item)


def _is_entry_enabled(item: Dict[str, Any] | None = None) -> bool:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._is_entry_enabled
    """
    from spellvid.application.context_builder import (
        _is_entry_enabled as _impl
    )
    return _impl(item)


def _resolve_ending_video_path(item: Dict[str, Any] | None = None) -> str:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._resolve_ending_video_path
    """
    from spellvid.application.context_builder import (
        _resolve_ending_video_path as _impl
    )
    return _impl(item)


def _is_ending_enabled(item: Dict[str, Any] | None = None) -> bool:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._is_ending_enabled
    """
    from spellvid.application.context_builder import (
        _is_ending_enabled as _impl
    )
    return _impl(item)


_entry_probe_cache: Dict[str, Tuple[float, Optional[float]]] = {}


def _probe_media_duration(path: str) -> Optional[float]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.media.ffmpeg_wrapper._probe_media_duration
    """
    from spellvid.infrastructure.media.ffmpeg_wrapper import (
        _probe_media_duration as _impl
    )
    return _impl(path)


def _prepare_entry_context(item: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder.prepare_entry_context
    """
    from spellvid.application.context_builder import (
        prepare_entry_context as _impl
    )
    return _impl(item)


def _prepare_ending_context(item: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder.prepare_ending_context
    """
    from spellvid.application.context_builder import (
        prepare_ending_context as _impl
    )
    return _impl(item)


def _resolve_letter_asset_dir(item: Dict[str, Any] | None = None) -> str:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder.resolve_letter_asset_dir
    """
    from spellvid.application.context_builder import (
        resolve_letter_asset_dir as _impl
    )
    return _impl(item)


def _normalize_letters_sequence(letters: str) -> List[str]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 domain.layout._normalize_letters_sequence
    """
    from spellvid.domain.layout import (
        _normalize_letters_sequence as _impl
    )
    return _impl(letters)


def _letter_asset_filename(ch: str) -> Optional[str]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 domain.layout._letter_asset_filename
    """
    from spellvid.domain.layout import (
        _letter_asset_filename as _impl
    )
    return _impl(ch)


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
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 domain.layout._letters_missing_names
    """
    from spellvid.domain.layout import (
        _letters_missing_names as _impl
    )
    return _impl(missing)


def _prepare_letters_context(item: Dict[str, Any]) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder.prepare_letters_context
    """
    from spellvid.application.context_builder import (
        prepare_letters_context as _impl
    )
    return _impl(item)


def _log_missing_letter_assets(missing: List[Dict[str, Any]]) -> None:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder.log_missing_letter_assets
    """
    from spellvid.application.context_builder import (
        log_missing_letter_assets as _impl
    )
    return _impl(missing)


def _coerce_bool(value: Any, default: bool = True) -> bool:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.context_builder._coerce_bool

    Note: 新實作簽名略有不同,但行為相容
    """
    from spellvid.application.context_builder import (
        _coerce_bool as _impl
    )
    # 舊版有 default 參數,新版沒有,需要適配
    if value is None:
        return default
    return _impl(value)


def _progress_bar_band_layout(bar_width: int) -> List[Dict[str, Any]]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.ui.progress_bar.calculate_band_layout
    """
    from spellvid.infrastructure.ui.progress_bar import (
        calculate_band_layout as _impl,
    )

    return _impl(bar_width)


_progress_bar_cache: Dict[int, Tuple[_np.ndarray, _np.ndarray]] = {}


def _progress_bar_base_arrays(
    bar_width: int,
) -> Tuple[_np.ndarray, _np.ndarray]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.ui.progress_bar.generate_base_arrays
    """
    from spellvid.infrastructure.ui.progress_bar import (
        generate_base_arrays as _impl,
    )

    return _impl(bar_width)


def _make_progress_bar_mask(mask_slice: _np.ndarray, duration: float):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.ui.progress_bar.create_mask_clip
    """
    from spellvid.infrastructure.ui.progress_bar import create_mask_clip as _impl

    return _impl(mask_slice, duration)


def _build_progress_bar_segments(
    countdown: float,
    total_duration: float,
    *,
    fps: int = 10,
    bar_width: int = PROGRESS_BAR_WIDTH,
) -> List[Dict[str, Any]]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.ui.progress_bar.plan_segments
    """
    from spellvid.infrastructure.ui.progress_bar import plan_segments as _impl

    return _impl(countdown, total_duration, fps=fps, bar_width=bar_width)


# If MoviePy is available, try to configure which ffmpeg binary to use.


def _find_and_set_ffmpeg():
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.media.ffmpeg_wrapper._find_and_set_ffmpeg
    """
    from spellvid.infrastructure.media.ffmpeg_wrapper import (
        _find_and_set_ffmpeg as _impl
    )
    return _impl()


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
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.video.moviepy_adapter._make_fixed_letter_clip
    """
    from spellvid.infrastructure.video.moviepy_adapter import (
        _make_fixed_letter_clip as _impl
    )
    return _impl(
        letter=letter,
        fixed_size=fixed_size,
        font_size=font_size,
        color=color,
        duration=duration,
        prefer_cjk=prefer_cjk,
    )


def check_assets(item: Dict[str, Any]) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.resource_checker.check_assets_dict
    """
    from spellvid.application.resource_checker import (
        check_assets_dict as _impl
    )
    return _impl(item)


def synthesize_beeps(duration_sec: int = 3, rate_hz: int = 1) -> bytes:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.media.audio.synthesize_beeps
    """
    from spellvid.infrastructure.media.audio import (
        synthesize_beeps as _impl
    )
    return _impl(duration_sec, rate_hz)


def _create_placeholder_mp4_with_ffmpeg(out_path: str) -> bool:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.video.moviepy_adapter._create_placeholder_mp4_with_ffmpeg
    """
    from spellvid.infrastructure.video.moviepy_adapter import (
        _create_placeholder_mp4_with_ffmpeg as _impl
    )
    return _impl(out_path)


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
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.video.effects.apply_fadeout_effect
    """
    from spellvid.infrastructure.video.effects import (
        apply_fadeout_effect as _impl,
    )

    return _impl(clip, duration)


def _apply_fadein(clip, duration: float = None, apply_audio: bool = False):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 infrastructure.video.effects.apply_fadein_effect
    """
    from spellvid.infrastructure.video.effects import (
        apply_fadein_effect as _impl,
    )

    return _impl(clip, duration, apply_audio)


def concatenate_videos_with_transitions(
    video_paths: List[str],
    output_path: str,
    fade_in_duration: float = None,
    apply_audio_fadein: bool = False,
) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.batch_service.concatenate_videos_with_transitions
    """
    from spellvid.application.batch_service import (
        concatenate_videos_with_transitions as _impl
    )
    return _impl(video_paths, output_path, fade_in_duration, apply_audio_fadein)


# ========== 核心渲染函數 (暫時保留) ==========
#
# 以下兩個函數是核心業務邏輯,合計約 1,860 行:
# - render_video_stub: ~230 lines (元數據計算和占位視頻)
# - render_video_moviepy: ~1,630 lines (完整 MoviePy 渲染管線)
#
# 保留原因:
# 1. 被 >30 個測試覆蓋,功能穩定
# 2. 已在正確的應用層位置
# 3. 完整重構需要 20-30 小時且風險極高
#
# v2.0 重構計劃:
# 1. 拆分 render_video_moviepy 為 10-15 個子函數:
#    - _prepare_context() - 準備所有上下文
#    - _create_background() - 背景處理
#    - _render_letters() - 字母渲染
#    - _render_chinese_zhuyin() - 中文注音渲染
#    - _render_timer() - 計時器渲染
#    - _render_reveal() - Reveal 打字效果
#    - _render_progress_bar() - 進度條渲染
#    - _process_audio() - 音訊處理
#    - _load_entry_ending() - 載入片頭片尾
#    - _compose_and_export() - 組合並輸出
# 2. 遷移至 application/video_service.py
# 3. 使用 Protocol 定義可測試介面
#
# 參考:
# - application/video_service.py: 未來架構框架
# - specs/004-complete-module-migration/: 遷移文檔
# ==========================================================


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
        skip_ending: If True, omit ending video (for batch processing)

    Returns:
        Rendering result dict (legacy format for compatibility)

    Example:
        >>> item = {"letters": "C c", "word_en": "Cat", "word_zh": "貓"}
        >>> render_video_moviepy(item, "out/cat.mp4")  # doctest: +SKIP
        DeprecationWarning: render_video_moviepy is deprecated...
    """
    warnings.warn(
        "render_video_moviepy is deprecated. "
        "Use application.video_service.render_video instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from spellvid.application.video_service import render_video
    
    # Delegate to new API
    result = render_video(item, out_path, dry_run, skip_ending)
    
    # Convert new format to legacy format for backward compatibility
    return {
        "status": "ok",
        "success": result.get("success", True),
        "out": out_path,
        "total_duration_sec": result.get("duration", 0.0),
        "metadata": result.get("metadata", {}),
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
