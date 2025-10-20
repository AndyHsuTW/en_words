# Infrastructure Layer Migration Plan

## 概述

**目標**: 完成所有 Infrastructure Layer 函數遷移 (16 個函數)  
**預估時間**: 5-7 小時  
**優先級**: 高 (完成架構完整性)  

**當前狀態**:
- ✅ 已完成: 1/16 (`_load_letter_image_specs` in image_loader.py)
- ⏳ 待遷移: 15/16

---

## 函數清單分析

### 分類 1: Pillow/PIL 文字渲染 (3 函數)

**目標模組**: `infrastructure/rendering/pillow_adapter.py`

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `_make_text_imageclip` | ~60 | 高 | PIL, MoviePy | 測試廣泛使用 |
| `_measure_text_with_pil` | ~30 | 高 | PIL | 佈局計算依賴 |
| `_find_system_font` | ~40 | 高 | os, pathlib | 字型解析 |

**預估時間**: 1.5 小時

### 分類 2: MoviePy 視頻適配 (5 函數)

**目標模組**: `infrastructure/video/moviepy_adapter.py`

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `_make_fixed_letter_clip` | ~25 | 低 | MoviePy, PIL | 字母圖片 clip |
| `_ensure_dimensions` | ~50 | 高 | MoviePy | 視頻尺寸調整 |
| `_ensure_fullscreen_cover` | ~35 | 低 | MoviePy | Cover 模式 |
| `_auto_letterbox_crop` | ~40 | 低 | MoviePy | Letterbox 偵測 |
| `_create_placeholder_mp4_with_ffmpeg` | ~30 | 中 | subprocess, ffmpeg | 占位視頻 |

**預估時間**: 2 小時

### 分類 3: FFmpeg 包裝 (2 函數)

**目標模組**: `infrastructure/media/ffmpeg_wrapper.py`

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `_probe_media_duration` | ~40 | 中 | subprocess, ffprobe | 媒體時長偵測 |
| `_find_and_set_ffmpeg` | ~60 | 中 | os, imageio-ffmpeg | FFmpeg 路徑解析 |

**預估時間**: 1 小時

### 分類 4: 音訊處理 (2 函數)

**目標模組**: `infrastructure/media/audio.py`

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `make_beep` | ~20 | 低 | pydub, numpy | 單一 beep 生成 |
| `synthesize_beeps` | ~40 | 中 | pydub | 多 beep 合成 |

**預估時間**: 0.5 小時

### 分類 5: 進度條 Infrastructure (2 函數) - 重新分類

**目標模組**: `infrastructure/rendering/progress_bar.py` (新建)

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `_progress_bar_base_arrays` | ~35 | 中 | numpy, PIL | 基礎圖層生成 |
| `_make_progress_bar_mask` | ~30 | 中 | MoviePy | 動態遮罩 |

**預估時間**: 1 小時

### 分類 6: 視覺效果 (2 函數) - 重新分類

**目標模組**: `infrastructure/video/effects.py` (新建)

| 函數名 | 行數 | 優先級 | 依賴 | 備註 |
|--------|------|--------|------|------|
| `_apply_fadeout` | ~25 | 中 | MoviePy | 淡出效果 |
| `_apply_fadein` | ~20 | 中 | MoviePy | 淡入效果 |

**預估時間**: 0.5 小時

---

## 遷移策略

### 階段 1: 高優先級函數 (2-3 小時)

**目標**: 遷移最常用、測試依賴最多的函數

1. **pillow_adapter.py** (1.5h)
   - `_make_text_imageclip` (call_count: 50)
   - `_measure_text_with_pil` (call_count: 22)
   - `_find_system_font` (call_count: 11)

2. **moviepy_adapter.py - 核心** (1h)
   - `_ensure_dimensions` (call_count: 10)

### 階段 2: 中優先級函數 (2-3 小時)

**目標**: 完成媒體處理相關函數

3. **ffmpeg_wrapper.py** (1h)
   - `_probe_media_duration`
   - `_find_and_set_ffmpeg`

4. **audio.py** (0.5h)
   - `synthesize_beeps`
   - `make_beep`

5. **progress_bar.py** (1h)
   - `_progress_bar_base_arrays`
   - `_make_progress_bar_mask`

6. **effects.py** (0.5h)
   - `_apply_fadeout`
   - `_apply_fadein`

### 階段 3: 低優先級函數 (1-1.5 小時)

**目標**: 完成剩餘 moviepy 適配函數

7. **moviepy_adapter.py - 其他** (1h)
   - `_create_placeholder_mp4_with_ffmpeg`
   - `_make_fixed_letter_clip`
   - `_ensure_fullscreen_cover`
   - `_auto_letterbox_crop`

---

## 執行步驟 (每個函數)

### 1. 準備階段 (5 分鐘)
- [ ] 定位函數在 utils.py 中的位置
- [ ] 檢查函數依賴 (imports, 呼叫其他函數)
- [ ] 檢查函數被呼叫的地方 (使用 grep_search)

### 2. 遷移階段 (10-15 分鐘)
- [ ] 在目標模組建立/更新檔案
- [ ] 複製函數程式碼 (保持原樣)
- [ ] 添加必要的 imports
- [ ] 添加/更新 docstring (標註來源)

### 3. 更新階段 (5-10 分鐘)
- [ ] 在 utils.py 中保留薄層包裝 (向後相容)
- [ ] 添加 deprecation 標記
- [ ] 更新 imports (從新位置 import)

### 4. 驗證階段 (5-10 分鐘)
- [ ] 執行快速測試 (使用 pylance snippet)
- [ ] 執行相關測試套件
- [ ] 檢查 lint 錯誤

### 5. 提交階段 (5 分鐘)
- [ ] Git add & commit (清晰的 commit message)
- [ ] 更新進度追蹤

**單個函數總時間**: 30-45 分鐘

---

## 風險評估

### 高風險

⚠️ **`_make_text_imageclip`**: 
- 測試廣泛依賴 (call_count: 50)
- 複雜的 padding/margin 邏輯
- **緩解**: 先執行小規模測試,逐步驗證

⚠️ **`_ensure_dimensions`**:
- 視頻渲染核心函數
- 影響所有視頻輸出
- **緩解**: 保留完整向後相容層

### 中風險

⚠️ **FFmpeg 函數**:
- 環境依賴 (ffmpeg/ffprobe 可執行檔)
- 跨平台問題
- **緩解**: 保留原有邏輯不變,僅遷移位置

### 低風險

✅ **音訊函數**: 獨立性高  
✅ **低 call_count 函數**: 影響範圍小  

---

## 成功指標

### 量化指標

- [ ] Infrastructure 函數遷移率: 16/16 (100%)
- [ ] utils.py 新增縮減: ~500-800 行
- [ ] 測試通過率: ≥187 passed (維持或提升)
- [ ] 核心功能測試: 100% 通過

### 質量指標

- [ ] 每個新模組有清晰的職責
- [ ] Docstrings 完整且準確
- [ ] 無循環依賴
- [ ] 向後相容性 100%

---

## 下一步行動

### 立即開始: 階段 1 - pillow_adapter.py

**第一個函數**: `_find_system_font`

**原因**:
1. 相對獨立 (無複雜依賴)
2. 純 infrastructure (os/pathlib)
3. 為其他函數鋪路 (`_make_text_imageclip` 依賴它)

**執行**:
```bash
# 1. 定位函數
grep -n "def _find_system_font" spellvid/utils.py

# 2. 建立新模組
touch spellvid/infrastructure/rendering/pillow_adapter.py

# 3. 遷移 & 測試
# 4. Commit
```

---

**準備開始?** 輸入 "start" 開始第一個函數遷移!
