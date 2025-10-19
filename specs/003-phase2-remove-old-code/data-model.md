# Data Model: utils.py → 新模組對應表

**Branch**: `003-phase2-remove-old-code`  
**Date**: 2025-10-18  
**Phase**: 1 - Design

## 目的
記錄 `spellvid/utils.py` 中的函數與新模組化架構的對應關係,作為遷移與 re-export 的依據。

---

## 函數對應表

### 1. 核心渲染函數

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `render_video_stub()` | `application.video_service.render_video()` | ✅ 已遷移 | 函數名稱已改變,簽章相似 |
| `render_video_moviepy()` | `application.video_service.render_video()` | ✅ 已整合 | 整合進 render_video 的內部邏輯 |

**遷移策略**: 
- 在 utils.py 建立 wrapper: `render_video_stub = lambda *args, **kwargs: ...`
- render_example.py 更新為直接 import 新函數

---

### 2. 佈局與版面計算

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `compute_layout_bboxes()` | `domain.layout.compute_layout_bboxes()` | ✅ 已遷移 | 簽章完全相同 |
| `_compute_letter_layout()` | `domain.layout` (internal) | ✅ 已遷移 | 內部函數 |
| `_fit_letters_in_width()` | `domain.layout` (internal) | ✅ 已遷移 | 內部函數 |

**遷移策略**:
- 公開函數: 直接 re-export
- 內部函數: 測試需更新 import 路徑

---

### 3. 文字與注音渲染

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `_make_text_imageclip()` | `infrastructure.rendering.make_text_imageclip()` | ✅ 已遷移 | 移除底線(公開API) |
| `_render_zhuyin()` | `domain.typography.render_zhuyin()` | ✅ 已遷移 | 移除底線 |
| `_split_zhuyin()` | `domain.typography.split_zhuyin()` | ✅ 已遷移 | 內部輔助函數 |

**測試影響**:
- `test_layout.py` 使用 `_make_text_imageclip` 進行像素驗證
- 需決定: re-export 為 `_make_text_imageclip` 或要求測試更新

---

### 4. 資源檢查與驗證

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `check_assets()` | `application.resource_checker.check_assets()` | ✅ 已遷移 | 簽章相同 |
| `_check_file_exists()` | `application.resource_checker` (internal) | ✅ 已遷移 | 內部函數 |

---

### 5. FFmpeg 與媒體處理

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `_find_and_set_ffmpeg()` | `infrastructure.media.ffmpeg_wrapper.find_and_set_ffmpeg()` | ✅ 已遷移 | 移除底線 |
| `synthesize_beeps()` | `infrastructure.media.audio.synthesize_beeps()` | ❓ 待確認 | 需檢查是否存在 |

---

### 6. 常數與配置

| 舊 utils.py | 新模組位置 | 狀態 | 備註 |
|------------|-----------|------|------|
| `PROGRESS_BAR_*` 常數 | `shared.constants` | ✅ 已遷移 | 所有進度條相關常數 |
| `LETTER_*` 常數 | `shared.constants` | ✅ 已遷移 | 字母相關常數 |
| `SCHEMA` (JSON schema) | `shared.validation.SCHEMA` | ✅ 已遷移 | 配置驗證 schema |

---

### 7. 內部輔助函數(測試專用)

這些函數在 tests/ 中被直接使用,需特別處理:

| 舊 utils.py | 新模組位置 | 測試依賴數量 | 處理方式 |
|------------|-----------|------------|---------|
| `_make_text_imageclip` | `infrastructure.rendering` | ~5 個測試 | ⚠️ 需 re-export 或更新測試 |
| `_mpy` (MoviePy module) | `infrastructure.video` | ~10 個測試 | ⚠️ 需 re-export |
| `_HAS_MOVIEPY` (flag) | `infrastructure.video` | ~8 個測試 | ⚠️ 需 re-export |
| `_compute_letter_layout` | `domain.layout` (internal) | ~2 個測試 | 測試更新 import |

**決策**: 
- 保留 utils.py 中對測試輔助函數的 re-export
- 添加註釋說明這些是測試專用,不應在生產代碼使用

---

## Re-export 策略

### 方案 A: 完整 re-export (推薦)

建立新的 `spellvid/utils.py`:

```python
"""⚠️ DEPRECATED: Backward compatibility layer

This module will be removed in v2.0.
Please migrate to the new modular architecture.
"""

import warnings

warnings.warn(
    "spellvid.utils is deprecated. Use specific modules instead.",
    DeprecationWarning,
    stacklevel=2
)

# === 核心函數 ===
from spellvid.application.video_service import render_video as render_video_stub
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.application.resource_checker import check_assets

# === 常數 ===
from spellvid.shared.constants import (
    PROGRESS_BAR_SAFE_X,
    PROGRESS_BAR_MAX_X,
    PROGRESS_BAR_WIDTH,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_COLORS,
    PROGRESS_BAR_RATIOS,
    PROGRESS_BAR_CORNER_RADIUS,
    LETTER_SAFE_X,
    LETTER_SAFE_Y,
    LETTER_AVAILABLE_WIDTH,
    LETTER_TARGET_HEIGHT,
    LETTER_BASE_GAP,
    LETTER_EXTRA_SCALE,
)

from spellvid.shared.validation import SCHEMA

# === 測試輔助 (僅供測試使用) ===
from spellvid.infrastructure.rendering import make_text_imageclip as _make_text_imageclip
from spellvid.infrastructure.video import _mpy, _HAS_MOVIEPY

# === __all__ ===
__all__ = [
    # 核心函數
    'render_video_stub',
    'compute_layout_bboxes',
    'check_assets',
    # 常數
    'PROGRESS_BAR_SAFE_X',
    'PROGRESS_BAR_MAX_X',
    # ... (完整列表)
    'SCHEMA',
    # 測試輔助
    '_make_text_imageclip',
    '_mpy',
    '_HAS_MOVIEPY',
]
```

**優點**:
- 最小化破壞性變更
- 測試無需修改
- render_example.py 可繼續使用 importlib.util

**缺點**:
- utils.py 仍然存在(雖然已極簡化)

---

### 方案 B: 移除 utils.py + 更新所有 import (激進)

**優點**:
- 徹底清理
- 強制遷移到新架構

**缺點**:
- 需修改 20+ 檔案
- render_example.py 需重寫
- 風險高

**不推薦**: 與本階段目標不符,應在後續版本處理

---

## render_example.py 更新策略

### 當前代碼 (問題)
```python
# 硬編碼路徑,脆弱
import importlib.util
utils_path = os.path.join(ROOT, 'spellvid', 'utils.py')
spec = importlib.util.spec_from_file_location('spellvid.utils', utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)
render_video_stub = utils.render_video_stub
```

### 更新後代碼 (方案 A - 使用 re-export)
```python
# 標準 import,依賴 utils.py re-export 層
from spellvid.utils import render_video_stub
```

### 更新後代碼 (方案 B - 直接使用新模組)
```python
# 直接使用新架構
from spellvid.application.video_service import render_video

# 包裝成相同介面
def render_video_stub(item, out_path, dry_run=False, use_moviepy=False, skip_ending=False):
    # 轉換參數格式...
    return render_video(...)
```

**推薦**: 方案 A(階段性) → 方案 B(未來版本)

---

## 測試遷移計畫

### 優先級分類

#### P0 - 立即處理(影響 render_example.ps1)
- `scripts/render_example.py` ✅

#### P1 - 保持向後相容(透過 re-export)
- `tests/test_layout.py` (使用 `_make_text_imageclip`)
- `tests/test_integration.py` (使用多個函數)
- 其他 20+ 測試檔案

#### P2 - 未來遷移(可選)
- 逐步更新測試 import 到新模組
- 在 v2.0 完全移除 utils.py 時一併處理

---

## 驗證檢查清單

### Phase 1 完成前必須確認:
- [ ] `application.video_service.render_video` 存在且可用
- [ ] `domain.layout.compute_layout_bboxes` 存在且可用
- [ ] `infrastructure.rendering.make_text_imageclip` 存在且可用
- [ ] 所有常數已遷移至 `shared.constants`
- [ ] `SCHEMA` 已遷移至 `shared.validation`
- [ ] `_mpy` 和 `_HAS_MOVIEPY` 在 `infrastructure.video` 可用

### Phase 2 任務生成依據:
1. 建立新的 utils.py (re-export 層)
2. 更新 render_example.py (移除 importlib.util)
3. 執行測試驗證向後相容性
4. 更新文件(AGENTS.md, copilot-instructions.md)

---

## 風險與依賴

### 外部依賴
- MoviePy 可用性(可選)
- FFmpeg 配置
- 測試資源檔案

### 內部依賴
- 新模組的 `__init__.py` 必須正確 export
- render_video 與 render_video_stub 的參數相容性
- 測試輔助函數的可見性

---

**完成日期**: 2025-10-18  
**下一步**: 驗證清單項目 → 生成 tasks.md
