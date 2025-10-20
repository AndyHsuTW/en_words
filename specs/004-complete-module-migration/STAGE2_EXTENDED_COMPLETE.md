# 階段 2 延伸完成報告

**日期**: 2025-10-20  
**狀態**: ✅ domain/layout.py 100% 完成  
**總耗時**: ~1.5 小時

---

## 🎉 重要里程碑

### domain/layout.py 模組遷移完成!

成功將 **5 個函數**從 `utils.py` 遷移至 `domain/layout.py`:

| # | 函數 | 行數 | 複雜度 | 狀態 |
|---|------|------|--------|------|
| 1 | `_normalize_letters_sequence` | 9 | ⭐ | ✅ |
| 2 | `_letter_asset_filename` | 8 | ⭐ | ✅ |
| 3 | `_letters_missing_names` | 7 | ⭐ | ✅ |
| 4 | `_layout_zhuyin_column` | 65 | ⭐⭐⭐ | ✅ |
| **總計** | **4 個函數** | **89 行** | - | **100%** |

---

## 📊 總體進度更新

### 已完成遷移

| 模組 | 函數數 | 狀態 | 提交 |
|------|--------|------|------|
| domain/timing.py | 2 | ✅ 100% | 61fd9e2 |
| **domain/layout.py** | **4** | **✅ 100%** | **1aeb0d1, ad01031** |

**總進度**: 6/37 函數 (16.2%)

---

## ✅ 最新遷移: _layout_zhuyin_column

### 函數資訊
- **位置**: `domain/layout.py` (line ~427)
- **功能**: 計算注音符號直行的垂直位置佈局
- **複雜度**: ⭐⭐⭐ (中等複雜)
- **行數**: 65 行 (含文檔 131 行)

### 關鍵特性
1. **輕聲特殊處理**: 輕聲符號(˙)置於主要符號上方,居中對齊
2. **一般聲調處理**: 其他聲調置於主要符號右側,垂直置中
3. **邊界檢查**: 確保所有元素不超出可用高度

### 驗證結果 ✅

```python
# 測試 1: 一般聲調 - 右側垂直置中
_layout_zhuyin_column(cursor_y=100, col_h=200, total_main_h=80,
                      tone_syms=["ˊ"], tone_sizes=[(10, 15)])
# ✅ tone_alignment == "right", tone_start_y == 140

# 測試 2: 輕聲 - 上方居中
_layout_zhuyin_column(cursor_y=100, col_h=200, total_main_h=80,
                      tone_syms=["˙"], tone_sizes=[(10, 12)])
# ✅ tone_alignment == "center", main_start_y == 122

# 測試 3: 無聲調
_layout_zhuyin_column(cursor_y=100, col_h=200, total_main_h=80,
                      tone_syms=[], tone_sizes=[])
# ✅ tone_start_y is None
```

---

## 📈 Batch 1 (Domain Layer) 進度

```
已完成: █████████████░░░░░░░░░  6/13 (46%)
```

### 已完成模組
- ✅ domain/timing.py (2/2, 100%)
- ✅ domain/layout.py (4/4, 100%)

### 待處理模組
- ⏳ domain/effects.py (0/6, 0%)
- ⚠️ _plan_letter_images (需重構,暫未包含在上述統計)

---

## 🎯 關鍵發現

### ✅ 成功因素

1. **函數獨立性高**
   - `_layout_zhuyin_column` 雖然有 65 行,但無外部依賴
   - 純計算邏輯,易於測試與驗證

2. **文檔完整**
   - 詳細的 docstring 說明參數與返回值
   - 包含使用範例與邊界情況處理

3. **驗證快速**
   - Pylance MCP 直接執行測試
   - 3 個測試案例覆蓋主要場景

---

### ⚠️ 下一步挑戰

#### 剩餘 Batch 1 函數分析

| 模組 | 函數 | 狀態 | 挑戰 |
|------|------|------|------|
| **domain/effects.py** | `_progress_bar_*` (4個) | 待遷移 | 使用 numpy arrays |
| | `_apply_fadeout` | ❌ 誤分類 | 使用 MoviePy,應屬 infrastructure |
| | `_apply_fadein` | ❌ 誤分類 | 使用 MoviePy,應屬 infrastructure |
| **未歸類** | `_plan_letter_images` | 需重構 | 124行,混合 domain + infrastructure |

---

## 💡 策略建議

### 選項 A: 繼續 domain/effects.py (推薦)
遷移 4 個 progress bar 函數 (`_progress_bar_*`)

**優點**:
- ✅ 職責相對單純 (雖然使用 numpy)
- ✅ 函數間有清晰的呼叫關係
- ✅ 預估 1.5-2h

**需要**:
- 檢查是否需要添加 numpy 導入
- 驗證函數間的依賴關係

---

### 選項 B: 重新分類 fade 函數
將 `_apply_fadeout` 與 `_apply_fadein` 移至 `infrastructure/video/effects.py`

**優點**:
- ✅ 更正架構分類
- ✅ 函數相對簡單 (~20-30 行)
- ✅ 預估 1h

**需要**:
- 可能需要創建新模組 `infrastructure/video/effects.py`
- 更新 MIGRATION_MAPPING.json

---

### 選項 C: 挑戰重構 _plan_letter_images
拆分 124 行複雜函數為 domain + infrastructure

**優點**:
- ✅ 完成最大挑戰
- ✅ 清理架構債務

**缺點**:
- ⚠️ 高風險 (3-4h, 可能影響測試)
- ⚠️ 需要詳細規劃

---

### 選項 D: 暫停並切換策略
接受當前進度 (6/37),跳到 Phase 3.6 建立 re-export 層

**優點**:
- ✅ 快速完成 (2-3h)
- ✅ 低風險

**缺點**:
- ⚠️ 未達成「完全移除」目標
- ⚠️ utils.py 仍保留大量代碼

---

## ⏱️ 時間統計

### 已投入
- 階段 1: 30 分鐘 ✅
- 階段 2: 1 小時 ✅
- **總計**: 1.5 小時

### 預估剩餘 (策略 A - 漸進式遷移)
- domain/effects.py: 1.5-2h
- 重構複雜函數: 3-4h
- Infrastructure: 4-5h
- 測試驗證: 1-2h
- **總計**: 9.5-13h

### 預估剩餘 (快速方案)
- 選擇性遷移: 2-3h
- Re-export 層: 1h
- 測試驗證: 1-2h
- **總計**: 4-6h

---

## 📋 決策時間

**您希望**:

**A.** 繼續遷移 domain/effects.py progress bar 函數 (1.5-2h)  
**B.** 重新分類 fade 函數至 infrastructure (1h)  
**C.** 挑戰重構 _plan_letter_images (3-4h)  
**D.** 切換至快速方案,建立 re-export 層 (4-6h)

---

## 提交記錄

```
commit ad01031
feat: 遷移 _layout_zhuyin_column 至 domain/layout.py

階段 2 延伸完成:
- _layout_zhuyin_column (65行,注音符號垂直佈局)
- 添加 Dict, Any 型別導入
- 完整 docstring 與測試驗證

批次 1 (Domain Layer) 進度: 6/13 (46%)
```

---

**當前成就**: 🏆 domain/layout.py 模組 100% 完成!  
**總進度**: 6/37 (16.2%)  
**時間投入**: 1.5h / 預估 11-14.5h 總計
