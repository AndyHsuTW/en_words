# Research: Phase 2 重構 - 移除舊程式碼

**Branch**: `003-phase2-remove-old-code`  
**Date**: 2025-10-18  
**Phase**: 0 - Research

## 研究目標
調查當前專案對 `spellvid/utils.py` 的依賴情況,評估安全移除的可行性,並確認新模組化架構的完整性。

---

## 1. 當前依賴分析

### 1.1 直接依賴 utils.py 的檔案清單

#### 測試檔案 (tests/)
透過 `grep` 搜尋發現 **20+ 個測試檔案** 直接 import utils:

```python
# 完整模組導入
from spellvid import utils
```

影響的測試檔案:
- `test_zhuyin.py`
- `test_video_overlap.py`
- `test_video_inclusion.py`
- `test_video_mode.py`
- `test_video_arm_sizing.py`
- `test_reveal_stable_positions.py`
- `test_reveal_underline.py`
- `test_progress_bar.py`
- `test_music_inclusion.py`
- `test_letters_images.py`
- `test_integration.py`
- `test_image_inclusion.py`
- `test_ending_video.py`
- `test_countdown.py`

```python
# 選擇性導入
from spellvid.utils import compute_layout_bboxes
from spellvid.utils import (
    # multiple items
)
```

影響的測試檔案:
- `test_layout.py`
- `test_reveal_underline.py`
- `test_batch_concatenation.py`
- `test_transition_fadeout.py`

#### 腳本檔案 (scripts/)
**關鍵發現**: `scripts/render_example.py` 使用特殊方式載入 utils:

```python
# line 14-19
import importlib.util
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils_path = os.path.join(ROOT, 'spellvid', 'utils.py')
spec = importlib.util.spec_from_file_location('spellvid.utils', utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)
render_video_stub = utils.render_video_stub
```

其他腳本:
- `scripts/render_letter_previews.py`: `from spellvid import utils`

### 1.2 utils.py 當前狀態

**檔案大小**: 3675 行 (巨大!)

**頂部警告**:
```python
"""⚠️ DEPRECATED: spellvid.utils module

This module is deprecated and will be removed in a future version.
All functions are being migrated to the new modular architecture:
...
"""

warnings.warn(
    "The spellvid.utils module is deprecated. "
    "Please migrate to the new modular architecture. "
    "See ARCHITECTURE.md for details.",
    DeprecationWarning,
    stacklevel=2
)
```

**關鍵問題**: utils.py **沒有 re-export** 新模組的函數!
- 搜尋結果顯示無 `from spellvid.shared import ...` 等語句
- 這意味著 utils.py 仍然是獨立的舊實作,而非向後相容層

---

## 2. 新模組化架構完整性檢查

### 2.1 模組結構
```
spellvid/
├── shared/
│   └── __init__.py
├── domain/
│   ├── effects.py
│   ├── layout.py
│   ├── timing.py
│   ├── typography.py
│   └── __init__.py
├── infrastructure/
│   ├── media/
│   ├── rendering/
│   ├── video/
│   └── __init__.py
├── application/
│   ├── batch_service.py
│   ├── resource_checker.py
│   ├── video_service.py
│   └── __init__.py
├── cli/
│   └── __init__.py
└── utils.py (待處理)
```

### 2.2 功能對應表 (需驗證)

| 舊 utils.py 函數 | 新模組位置 (推測) | 驗證狀態 |
|-----------------|----------------|---------|
| `compute_layout_bboxes` | `domain.layout` | ❓ 待確認 |
| `render_video_stub` | `application.video_service` | ❓ 待確認 |
| `_make_text_imageclip` | `infrastructure.rendering` | ❓ 待確認 |
| `_find_and_set_ffmpeg` | `infrastructure.media.ffmpeg_wrapper` | ❓ 待確認 |
| `check_assets` | `application.resource_checker` | ❓ 待確認 |
| `synthesize_beeps` | `domain.effects` or `infrastructure.media` | ❓ 待確認 |

---

## 3. render_example.ps1 工作流程分析

### 3.1 執行鏈
```
render_example.ps1
  ↓ (啟動 venv)
  ↓ (設置 FFMPEG env vars)
  ↓ (呼叫)
scripts/render_example.py
  ↓ (透過 importlib.util 載入)
spellvid/utils.py
  ↓ (使用)
utils.render_video_stub()
```

### 3.2 風險評估
- **高風險**: render_example.py 硬編碼 `utils.py` 路徑
- **中風險**: 20+ 測試檔案直接依賴 utils
- **低風險**: 新模組架構已建立

---

## 4. 關鍵發現與決策點

### 4.1 ⚠️ 重大發現
1. **utils.py 不是向後相容層**: 它仍然包含 3675 行的原始實作,而非 re-export
2. **render_example.py 依賴路徑硬編碼**: 使用 importlib.util 直接載入 utils.py 檔案
3. **測試檔案大量依賴**: 估計需要更新 20+ 個測試檔案的 import 語句

### 4.2 可行性評估
**Question 1**: 新模組是否已完整實作所有 utils.py 功能?
- **Status**: ❓ 未驗證
- **Action Required**: 需要檢查新模組的 __init__.py 是否 export 對應函數

**Question 2**: render_video_stub 是否已遷移?
- **Critical**: 這是 render_example.py 唯一使用的函數
- **Action Required**: 檢查 `application.video_service` 是否有對應實作

**Question 3**: 內部測試輔助函數(如 `_make_text_imageclip`)是否可用?
- **Impact**: 多個測試依賴這些 `_` 開頭的內部函數
- **Action Required**: 確認新模組是否保留這些測試輔助函數

### 4.3 移除策略建議

#### 選項 A: 完全移除 + 更新所有 import (激進)
- **優點**: 徹底清理,避免混淆
- **缺點**: 需要大量修改,風險高
- **估計工作量**: 20+ 檔案修改

#### 選項 B: utils.py 轉為 re-export 層 (保守)
- **優點**: 最小化修改,向後相容
- **缺點**: 仍保留 utils.py 檔案
- **估計工作量**: 1 個檔案修改(utils.py)

#### 選項 C: 混合策略 (務實) ✅ **推薦**
1. 將 utils.py 改為輕量 re-export 層(保留檔案但移除實作)
2. 更新 render_example.py 使用正常 import
3. 逐步遷移測試 import(可選,非必要)
4. 在後續版本中完全移除 utils.py

---

## 5. 下一步行動項目

### Phase 1 需要完成的工作:
1. **驗證新模組完整性**:
   - 檢查 `application.video_service.render_video_stub` 是否存在
   - 檢查 `domain.layout.compute_layout_bboxes` 是否存在
   - 確認所有關鍵函數已遷移

2. **建立 data-model.md**:
   - 記錄 utils.py → 新模組的完整對應表
   - 列出 re-export 對應關係

3. **更新 render_example.py**:
   - 移除 importlib.util 硬編碼
   - 改用正常 import: `from spellvid.application.video_service import render_video_stub`

4. **建立 utils.py re-export 層**:
   ```python
   # spellvid/utils.py (new minimal version)
   """Backward compatibility layer - will be removed in v2.0"""
   from spellvid.domain.layout import compute_layout_bboxes
   from spellvid.application.video_service import render_video_stub
   # ... other re-exports
   __all__ = ['compute_layout_bboxes', 'render_video_stub', ...]
   ```

---

## 6. 風險緩解計畫

### 測試策略
1. **基準測試**: 在任何修改前執行 `.\scripts\run_tests.ps1` 建立 baseline
2. **增量驗證**: 每次修改後立即執行測試
3. **核心驗證**: 確保 `render_example.ps1` 在每個階段都能執行

### 回滾計畫
- 保留 `utils_old.py.bak` 作為備份
- 使用 git 分支隔離變更
- 建立驗收測試腳本驗證核心功能

---

## 7. 待解決問題 (Blockers)

### 🚨 Critical Questions
1. **Q1**: `application.video_service` 是否有 `render_video_stub` 函數?
   - **Why Critical**: render_example.py 完全依賴此函數
   - **Resolution**: 需要檢查檔案內容

2. **Q2**: 新模組的 `__init__.py` 是否正確 export 公開 API?
   - **Why Critical**: import 路徑能否正常工作
   - **Resolution**: 檢查各模組 __init__.py

3. **Q3**: 測試內部輔助函數(如 `_make_text_imageclip`)如何處理?
   - **Why Critical**: 多個測試依賴這些函數
   - **Resolution**: 決定是 re-export 或要求測試直接 import 新模組

---

## 結論

**可行性**: ✅ 移除舊程式碼是可行的,但需要謹慎執行

**推薦路徑**: 混合策略(選項 C)
- 保留 utils.py 作為輕量 re-export 層
- 更新 render_example.py 使用標準 import
- 移除 utils.py 中的 3675 行實作,僅保留 import 語句

**關鍵前提**: 必須先驗證新模組完整性(Phase 1 首要任務)

**估計時程**:
- Phase 1 (Design): 2-4 小時
- Phase 2 (Tasks): 1 小時
- Phase 3-4 (Implementation): 4-8 小時
- Total: 1-2 個工作天

---

**研究完成日期**: 2025-10-18  
**下一階段**: Phase 1 - Design (驗證新模組 + 建立對應表)
