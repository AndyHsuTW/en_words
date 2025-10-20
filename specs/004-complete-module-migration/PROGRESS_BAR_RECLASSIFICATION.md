# Progress Bar 函數分類修正

**日期**: 2025-10-21  
**發現**: 原計劃將 4 個 progress bar 函數遷移至 `domain/effects.py`,但檢查後發現職責混淆

---

## 🚨 問題分析

### 原 MIGRATION_MAPPING.json 分類

| 函數 | 原計劃位置 | 問題 |
|------|-----------|------|
| `_progress_bar_band_layout` | domain/effects.py | ✅ 正確 (純邏輯) |
| `_progress_bar_base_arrays` | domain/effects.py | ❌ 錯誤 (使用 PIL) |
| `_make_progress_bar_mask` | domain/effects.py | ❌ 錯誤 (使用 MoviePy) |
| `_build_progress_bar_segments` | domain/effects.py | ✅ 正確 (純邏輯) |

---

## 📋 函數詳細分析

### 1. `_progress_bar_band_layout` ✅ Domain

**職責**: 計算顏色帶的像素範圍

**依賴**:
- Constants: `PROGRESS_BAR_RATIOS`, `PROGRESS_BAR_COLORS`
- 純數學計算,無外部框架

**建議**: 遷移至 `domain/effects.py`

```python
def _progress_bar_band_layout(bar_width: int) -> List[Dict[str, Any]]:
    """Return color bands with absolute pixel spans for the progress bar."""
    # 純邏輯計算顏色帶範圍
```

---

### 2. `_progress_bar_base_arrays` ❌ Infrastructure

**職責**: 生成進度條的 RGB 顏色陣列與 alpha 遮罩

**依賴**:
- **PIL**: `Image.new()`, `ImageDraw.Draw()`, `draw.rounded_rectangle()`
- **numpy**: `_np.zeros()`, `_np.array()`
- `_progress_bar_band_layout()` (domain 函數)

**問題**: 使用 PIL 進行圖像操作,屬於基礎設施

**建議**: 遷移至 `infrastructure/rendering/progress_bar.py` (新模組)

```python
def _progress_bar_base_arrays(bar_width: int) -> Tuple[_np.ndarray, _np.ndarray]:
    """Return (color_rgb, alpha_mask) arrays for the segmented progress bar."""
    # 使用 PIL 生成遮罩圖像
    mask_img = Image.new("L", (bar_width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.rounded_rectangle(...)  # ← PIL 依賴
```

---

### 3. `_make_progress_bar_mask` ❌ Infrastructure

**職責**: 從 numpy 陣列創建 MoviePy ImageClip 遮罩

**依賴**:
- **MoviePy**: `_mpy.ImageClip()`
- **numpy**: array 轉換

**問題**: 直接使用 MoviePy API,屬於視頻基礎設施

**建議**: 遷移至 `infrastructure/video/moviepy_adapter.py`

```python
def _make_progress_bar_mask(mask_slice: _np.ndarray, duration: float):
    """Create a MoviePy ImageClip mask from an alpha slice."""
    clip = _mpy.ImageClip(mask_arr, **mask_kwargs)  # ← MoviePy 依賴
    return clip.with_duration(duration)
```

---

### 4. `_build_progress_bar_segments` ✅ Domain

**職責**: 規劃進度條在倒數計時中的各個分段

**依賴**:
- Constants: `PROGRESS_BAR_WIDTH`, `PROGRESS_BAR_CORNER_RADIUS`
- `_progress_bar_band_layout()` (domain 函數)
- 純數學計算

**建議**: 遷移至 `domain/effects.py`

```python
def _build_progress_bar_segments(
    countdown: float,
    total_duration: float,
    *,
    fps: int = 10,
    bar_width: int = PROGRESS_BAR_WIDTH,
) -> List[Dict[str, Any]]:
    """Plan progress bar slices (start, end, width, spans) across countdown."""
    # 純邏輯計算各時間段的進度條狀態
```

---

## 💡 修正後的遷移計劃

### 階段 A: Domain Layer (2 個函數)
- ✅ `_progress_bar_band_layout` → `domain/effects.py`
- ✅ `_build_progress_bar_segments` → `domain/effects.py`

**預估時間**: 1 小時

---

### 階段 B: Infrastructure Layer (2 個函數)
- ❌ `_progress_bar_base_arrays` → `infrastructure/rendering/progress_bar.py` (新建)
- ❌ `_make_progress_bar_mask` → `infrastructure/video/moviepy_adapter.py`

**預估時間**: 1.5 小時

---

## 🎯 建議行動

### 選項 1: 只遷移 Domain 函數 (推薦)

**行動**:
1. 遷移 `_progress_bar_band_layout` 至 `domain/effects.py`
2. 遷移 `_build_progress_bar_segments` 至 `domain/effects.py`
3. 暫時保留 `_progress_bar_base_arrays` 與 `_make_progress_bar_mask` 在 utils.py

**優點**:
- ✅ 保持架構純淨 (domain 不依賴 PIL/MoviePy)
- ✅ 快速完成 (1 小時)
- ✅ 低風險

**缺點**:
- ⚠️ infrastructure 函數需要後續處理

---

### 選項 2: 全部遷移並修正分類

**行動**:
1. 遷移 2 個 domain 函數至 `domain/effects.py`
2. 創建 `infrastructure/rendering/progress_bar.py`
3. 遷移 `_progress_bar_base_arrays` 至新模組
4. 遷移 `_make_progress_bar_mask` 至 `infrastructure/video/moviepy_adapter.py`

**優點**:
- ✅ 完整處理所有 progress bar 函數
- ✅ 架構正確

**缺點**:
- ⚠️ 需要創建新模組
- ⚠️ 時間較長 (2.5 小時)
- ⚠️ 風險較高

---

### 選項 3: 跳過,繼續其他函數

**行動**:
- 保留所有 progress bar 函數在 utils.py
- 轉而處理其他模組 (fade 函數、_plan_letter_images 等)

**優點**:
- ✅ 避開複雜問題
- ✅ 保持進度

**缺點**:
- ⚠️ 留下技術債務

---

## 📊 更新後的統計

### 原計劃 (錯誤)
- domain/effects.py: 6 個函數
  - 4 個 progress bar
  - 2 個 fade

### 修正後
- domain/effects.py: 4 個函數
  - 2 個 progress bar (純邏輯)
  - 2 個 fade (需檢查是否也有誤分類)
  
- infrastructure/rendering/progress_bar.py: 1 個函數
  - `_progress_bar_base_arrays`
  
- infrastructure/video/moviepy_adapter.py: 1 個函數
  - `_make_progress_bar_mask`

---

## ❓ 決策

**您希望**:

**A1.** 只遷移 2 個 domain 函數 (1h, 低風險) - 推薦  
**A2.** 全部遷移並修正分類 (2.5h, 中風險)  
**A3.** 跳過 progress bar,轉而處理其他函數  

---

**現在時間**: 2025-10-21  
**當前進度**: 6/37 (16.2%)  
**建議**: 選擇 A1,保持架構純淨與進度穩定
