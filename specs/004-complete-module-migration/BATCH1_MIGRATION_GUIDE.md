# 批次 1: Domain Layer 遷移完成指南

## 當前進度

✅ **已完成** (2/13):
- `domain/timing.py`: `_coerce_non_negative_float`, `_coerce_bool`

⏳ **待完成** (11/13):
- `domain/layout.py`: 5 個函數
- `domain/effects.py`: 6 個函數

---

## 遷移策略

由於這些函數有複雜的內部依賴和 import 需求,建議採用以下方法:

### 方法 1: 手動遷移 (推薦)

使用 IDE (VS Code) 的重構功能:

1. **定位函數** (在 utils.py 中)
2. **複製函數完整程式碼** (包含所有 import)
3. **貼上到目標模組末尾**
4. **更新 import 語句** (確保所有依賴可用)
5. **執行測試** (`pytest tests/ -x`)

### 方法 2: 使用 Git 分支策略

每遷移一個模組就建立 commit:

```bash
# 遷移 domain/layout.py
git add spellvid/domain/layout.py
git commit -m "feat: 遷移 5 個函數至 domain/layout.py"

# 測試
pytest tests/ -x

# 失敗則回退
git reset --hard HEAD~1
```

---

## domain/layout.py 遷移詳細步驟

### 需要遷移的 5 個函數

從 `utils.py` 提取以下函數及其完整程式碼:

#### 1. `_normalize_letters_sequence` (行 305-313)

```python
def _normalize_letters_sequence(letters: str) -> List[str]:
    if not letters:
        return []
    seq: List[str] = []
    for ch in letters:
        if not ch or ch.isspace():
            continue
        seq.append(ch)
    return seq
```

**依賴**: 無額外依賴

---

#### 2. `_letter_asset_filename` (行 316-323)

```python
def _letter_asset_filename(ch: str) -> Optional[str]:
    if not ch:
        return None
    if ch.isalpha():
        if ch.isupper():
            return f"{ch}.png"
        if ch.islower():
            return f"{ch}_small.png"
    return None
```

**依賴**: `Optional` (已在 layout.py)

---

#### 3. `_plan_letter_images` (行 326-449)

**警告**: 此函數非常長 (~124 行) 且依賴:
- `os`
- `Image` (from PIL)
- Constants: `LETTER_BASE_GAP`, `LETTER_AVAILABLE_WIDTH`, `LETTER_TARGET_HEIGHT`, `LETTER_EXTRA_SCALE`
- 內部函數: `_normalize_letters_sequence`, `_letter_asset_filename`

**建議**: 此函數實際上是 **infrastructure 層的邏輯** (因為它使用 PIL),應該遷移至:
- `infrastructure/rendering/letter_planning.py` (新檔案)

或者重構為:
- Pure logic → `domain/layout.py`
- PIL integration → `infrastructure/rendering/`

---

#### 4. `_letters_missing_names` (行 452-458)

```python
def _letters_missing_names(letters_result: Dict[str, Any]) -> List[str]:
    missing = letters_result.get("missing", [])
    if not missing:
        return []
    names = [entry.get("char", "?") for entry in missing]
    return names
```

**依賴**: `Dict`, `Any`, `List`

---

#### 5. `_layout_zhuyin_column` (行 735-800)

**警告**: 此函數也很長 (~65 行) 且依賴:
- `_zhuyin_main_gap` (from domain/typography)
- Constants: `ZHUYIN_*` 系列

**建議**: 檢查此函數是否已在 `domain/typography.py` 實作

---

## 遷移前的重要檢查

### 檢查常數導入

確保 `domain/layout.py` 頂部有:

```python
from spellvid.shared.constants import (
    LETTER_BASE_GAP,
    LETTER_AVAILABLE_WIDTH,
    LETTER_TARGET_HEIGHT,
    LETTER_EXTRA_SCALE,
    # ... 其他需要的常數
)
```

### 檢查依賴模組

如果函數需要 PIL:

```python
from PIL import Image
import os
```

---

## domain/effects.py 遷移詳細步驟

### 需要遷移的 6 個函數

#### 1-4. Progress Bar 系列 (4 個函數)

```
_progress_bar_band_layout (行 519-542)
_progress_bar_base_arrays (行 545-575)
_make_progress_bar_mask (行 578-617)
_build_progress_bar_segments (行 620-692)
```

**依賴**:
- `numpy`
- Constants: `PROGRESS_BAR_*`
- 這些函數高度相關,建議一次性遷移

#### 5-6. Fade 效果 (2 個函數)

```
_apply_fadeout (行 1905-1952)
_apply_fadein (行 1955-2002)
```

**依賴**:
- MoviePy (`_mpy`)
- 這些實際上是 **infrastructure 層邏輯**!

**建議**: 應遷移至 `infrastructure/video/effects.py`

---

## 遷移後驗證清單

每完成一個模組的遷移:

- [ ] 執行 `pytest tests/ -x -k "layout"`
- [ ] 執行 `pytest tests/ -x -k "effects"`
- [ ] 執行 `pytest tests/ -x -k "timing"`
- [ ] 檢查 import 錯誤: `python -c "from spellvid.domain.layout import _normalize_letters_sequence"`
- [ ] 完整測試: `.\scripts\run_tests.ps1`

---

## 已知問題與解決方案

### 問題 1: 循環 import

**症狀**: `ImportError: cannot import name X from partially initialized module`

**解決**: 將共用的 helper 函數提取到 `shared/` 層

---

### 問題 2: 函數職責不清晰

部分函數同時包含:
- 純邏輯 (應在 domain)
- 框架整合 (應在 infrastructure)

**解決**: 重構函數,拆分職責

---

## 時間預估

- `domain/layout.py`: 2-3h (5 個函數,部分複雜)
- `domain/effects.py`: 1.5-2h (6 個函數,但需重新分類)
- **批次 1 總計**: 3.5-5h

---

## 下一步建議

1. **先完成簡單的**: `_normalize_letters_sequence`, `_letter_asset_filename`, `_letters_missing_names`
2. **暫緩複雜的**: `_plan_letter_images`, `_layout_zhuyin_column` (考慮重構或重新分類)
3. **重新評估 effects.py**: 許多函數實際上屬於 infrastructure 層

---

## 結論

批次 1 的遷移比預期複雜,主要原因:

1. ✅ **職責混淆**: 許多函數同時包含 domain logic 和 infrastructure integration
2. ✅ **依賴複雜**: 函數間高度耦合
3. ✅ **需要重構**: 部分函數需要先重構才能正確分層

**建議**:
- 暫停全量遷移
- 先重新評估 MIGRATION_MAPPING.json 的分類
- 考慮採用漸進式遷移策略 (只遷移明確屬於各層的函數)

---

**當前狀態**: 2/37 函數已遷移,建議重新評估遷移策略
