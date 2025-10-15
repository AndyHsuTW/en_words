# T036 Implementation Plan: utils.py Backward Compatibility Layer

## 策略
將 utils.py 轉換為輕量級 re-export 層,保持向後相容性。

## 函數映射表 (舊 utils.py → 新架構)

### 公開函數 (Public API)

| 舊函數 | 新模組路徑 | 說明 |
|--------|-----------|------|
| `load_json()` | `spellvid.shared.validation.load_json` | JSON 載入 |
| `validate_schema()` | `spellvid.shared.validation.validate_schema` | Schema 驗證 |
| `compute_layout_bboxes()` | `spellvid.domain.layout.compute_layout_bboxes` | 佈局計算 |
| `zhuyin_for()` | `spellvid.domain.typography.zhuyin_for` | 注音查詢 |
| `check_assets()` | `spellvid.application.resource_checker.check_assets` | 資源檢查 |
| `render_video_stub()` | `spellvid.application.video_service.render_video` | 視頻渲染(需適配) |
| `render_video_moviepy()` | ❌ 已棄用,未在新架構實作 | MoviePy 渲染 |
| `concatenate_videos_with_transitions()` | ❌ 已棄用,功能整合到 batch_service | 視頻串接 |
| `synthesize_beeps()` | `spellvid.application.resource_checker` or utils (小型 helper) | 音效合成 |

### 內部函數 (Used by tests)

| 舊函數 | 新模組路徑 | 使用測試 |
|--------|-----------|---------|
| `_make_text_imageclip()` | `spellvid.infrastructure.rendering.pillow_adapter` | test_layout.py |
| `_HAS_MOVIEPY` | `spellvid.infrastructure.video.moviepy_adapter.HAS_MOVIEPY` | test_transition_fadeout.py, test_*.py |
| `_mpy` | `spellvid.infrastructure.video.moviepy_adapter.get_moviepy_module()` | test_transition_fadeout.py |
| `_apply_fadeout()` | `spellvid.domain.effects.apply_fadeout` | test_transition_fadeout.py, test_batch_concatenation.py |
| `_apply_fadein()` | `spellvid.domain.effects.apply_fadein` | test_transition_fadeout.py, test_batch_concatenation.py |
| `_find_and_set_ffmpeg()` | `spellvid.infrastructure.media.ffmpeg_wrapper` | 可能被 utils 使用 |

### 常數 (Constants)

| 舊常數 | 新模組路徑 | 使用測試 |
|--------|-----------|---------|
| `PROGRESS_BAR_*` | `spellvid.shared.constants` | test_progress_bar.py |
| `FADE_OUT_DURATION` | `spellvid.shared.constants` | test_transition_fadeout.py |
| `FADE_IN_DURATION` | `spellvid.shared.constants` | test_transition_fadeout.py |
| `SCHEMA` | `spellvid.shared.validation.SCHEMA` | test_integration.py |

### 特殊處理項目

1. **render_video_stub() 適配**:
   - 舊簽名: `render_video_stub(item, out="out.mp4", dry_run=False, skip_ending=False, use_moviepy=False)`
   - 新簽名: `render_video(config: VideoConfig, output_path: str, dry_run: bool, skip_ending: bool, composer: IVideoComposer | None)`
   - 需要包裝函數轉換 dict → VideoConfig

2. **concatenate_videos_with_transitions()**:
   - 功能已整合到 `batch_service.render_batch()`
   - 可能需要保留舊函數簽名作為 wrapper

3. **MoviePy 相關導入**:
   - `_mpy` 模組需要通過 `get_moviepy_module()` 獲取
   - `_HAS_MOVIEPY` 改為 `HAS_MOVIEPY`

## Re-export 策略

### utils.py 新結構 (目標 < 200 lines)

```python
"""Backward compatibility layer for spellvid.utils

This module is deprecated. All functions have been moved to their
respective layers in the new architecture:
- spellvid.shared: Types, constants, validation
- spellvid.domain: Layout, typography, effects, timing
- spellvid.infrastructure: MoviePy, Pillow, FFmpeg adapters
- spellvid.application: Video service, batch service, resource checker
- spellvid.cli: CLI commands and parsers

Future versions may remove this compatibility layer.
"""

import warnings

# === Deprecation Warning ===
warnings.warn(
    "The spellvid.utils module is deprecated and will be removed in a future version. "
    "Please import from the new modular architecture instead. "
    "See documentation for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# === Re-exports from new modules ===

# Shared layer
from .shared.validation import load_json, validate_schema, SCHEMA, ValidationError
from .shared.constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    PROGRESS_BAR_SAFE_X,
    PROGRESS_BAR_MAX_X,
    PROGRESS_BAR_WIDTH,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_COLORS,
    PROGRESS_BAR_RATIOS,
    SAFE_MARGIN_LEFT,
    SAFE_MARGIN_RIGHT,
    SAFE_MARGIN_TOP,
    SAFE_MARGIN_BOTTOM,
    FADE_OUT_DURATION,
    FADE_IN_DURATION,
)

# Domain layer
from .domain.layout import compute_layout_bboxes
from .domain.typography import zhuyin_for
from .domain.effects import apply_fadeout as _apply_fadeout, apply_fadein as _apply_fadein

# Infrastructure layer
from .infrastructure.video.moviepy_adapter import HAS_MOVIEPY as _HAS_MOVIEPY
# TODO: _mpy wrapper
# TODO: _make_text_imageclip wrapper

# Application layer
from .application.resource_checker import check_assets

# === Adapter wrappers for changed signatures ===

def render_video_stub(item: dict, out: str = "out.mp4", dry_run: bool = False, 
                     skip_ending: bool = False, use_moviepy: bool = False):
    """Adapter wrapper for backward compatibility.
    
    Converts old dict-based API to new VideoConfig-based API.
    """
    from .shared.types import VideoConfig
    from .application.video_service import render_video
    
    # Convert dict to VideoConfig
    config = VideoConfig(...)
    
    # Call new API
    return render_video(config, output_path=out, dry_run=dry_run, 
                       skip_ending=skip_ending, composer=None)

def concatenate_videos_with_transitions(...):
    """Legacy function - use batch_service.render_batch() instead."""
    warnings.warn(
        "concatenate_videos_with_transitions() is deprecated. "
        "Use spellvid.application.batch_service.render_batch() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Minimal implementation or raise NotImplementedError
    raise NotImplementedError("This function has been replaced by batch_service")

# === Keep minimal helpers ===
def synthesize_beeps(duration_sec: int = 3, rate_hz: int = 1) -> bytes:
    """Small audio stub - keep in utils for now."""
    # Original implementation (~8 lines)
    ...
```

## 執行步驟

1. ✅ 分析完成 - 建立函數映射表
2. ⏳ 備份 utils.py → utils_old.py.bak
3. ⏳ 重寫 utils.py (僅 re-export + adapters)
4. ⏳ 執行測試驗證: `pytest tests/test_*.py -v`
5. ⏳ 修正任何失敗測試
6. ⏳ 確認 utils.py < 200 lines

## 測試影響分析

### 需要 utils 內部函數的測試檔案 (18 個)

1. test_zhuyin.py - `utils.zhuyin_for()`
2. test_layout.py - `compute_layout_bboxes`, `_make_text_imageclip`
3. test_transition_fadeout.py - `_apply_fadeout`, `_apply_fadein`, `_HAS_MOVIEPY`, `_mpy`
4. test_batch_concatenation.py - `_apply_fadeout`, `_apply_fadein`, `concatenate_videos_with_transitions`
5. test_integration.py - `utils.check_assets`, `utils.load_json`, `SCHEMA`
6. test_countdown.py - `utils.render_video_stub`
7. test_ending_video.py - `utils.render_video_stub`
8. test_image_inclusion.py - `utils.render_video_stub`
9. test_music_inclusion.py - `utils.render_video_stub`
10. test_progress_bar.py - `utils.render_video_stub`, PROGRESS_BAR 常數
11. test_reveal_stable_positions.py - `utils.compute_layout_bboxes`
12. test_reveal_underline.py - `utils.compute_layout_bboxes`
13. test_letters_images.py - `utils.check_assets`
14. test_video_arm_sizing.py - `utils.render_video_stub`
15. test_video_inclusion.py - `utils.render_video_stub`
16. test_video_mode.py - `utils.render_video_stub`
17. test_video_overlap.py - `utils.render_video_stub`
18. test_entry_video.py - `utils.render_video_stub`

### 預期結果

- 所有測試仍能 import 成功
- 會看到 DeprecationWarning (預期行為)
- 功能保持不變

## 風險評估

**低風險**:
- load_json, validate_schema, compute_layout_bboxes - 簽名未變
- zhuyin_for, check_assets - 簽名未變
- Constants - 僅路徑變更

**中風險**:
- render_video_stub - 需要 dict → VideoConfig 轉換
- _apply_fadeout, _apply_fadein - 可能有參數差異

**高風險**:
- concatenate_videos_with_transitions - 功能已整合到 batch_service
- render_video_moviepy - 新架構中未實作

## 決策

**Phase 1 (T036)**: 實作基本 re-export
- 處理低風險項目
- render_video_stub 提供簡化 adapter
- concatenate_videos_with_transitions 拋出 NotImplementedError 並建議使用新 API

**Phase 2 (T037)**: 測試驗證
- 執行所有現有測試
- 修正失敗項目
- 記錄 DeprecationWarning

**Phase 3 (T038)**: 清理
- 確保 utils.py < 200 lines
- 移除所有舊實作代碼
