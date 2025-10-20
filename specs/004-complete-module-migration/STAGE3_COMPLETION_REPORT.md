# 階段 3 完成報告 - Domain Effects (純邏輯部分)

**日期**: 2025-10-21  
**狀態**: ✅ 完成  
**耗時**: ~1 小時

---

## 執行摘要

成功將 **2 個純邏輯進度條函數**從 `utils.py` 遷移至 `domain/effects.py`,並發現原計劃中的架構分類問題,做出明智的調整決策。

---

## ✅ 已遷移函數

### 1. `_progress_bar_band_layout(bar_width: int) -> List[Dict[str, Any]]`

**位置**: `domain/effects.py` (line ~214)  
**功能**: 計算進度條顏色帶的像素範圍佈局  
**複雜度**: ⭐⭐ (中等)  
**行數**: 25 行核心邏輯 + 40 行文檔 = 65 行總計

**職責**:
- 根據 PROGRESS_BAR_RATIOS 計算 safe/warn/danger 三個顏色帶的範圍
- 返回每個顏色帶的 start/end 像素位置
- 純數學計算,無外部依賴

**驗證結果** ✅:
```python
layout = _progress_bar_band_layout(1792)
# Band 1: safe (0-896)
# Band 2: warn (896-1254)  
# Band 3: danger (1254-1792)
```

---

### 2. `_build_progress_bar_segments(...) -> List[Dict[str, Any]]`

**位置**: `domain/effects.py` (line ~278)  
**功能**: 規劃倒數計時中進度條的各個時間分段  
**複雜度**: ⭐⭐⭐⭐ (複雜)  
**行數**: 89 行核心邏輯 + 80 行文檔 = 169 行總計

**職責**:
- 將倒數時間分割為多個 segment (基於 fps)
- 計算每個 segment 的進度條寬度、位置、顏色區段
- 處理邊界情況 (countdown=0, fps<=0 等)
- 純邏輯計算,呼叫 `_progress_bar_band_layout`

**驗證結果** ✅:
```python
# 10 秒倒數,10fps
segments = _build_progress_bar_segments(10.0, 15.0, fps=10)
# 101 個分段 (100 倒數 + 1 結束)
# First: start=0.0, width=1792
# Last: start=10.0, width=0
```

---

## 📊 架構決策

### 🚨 發現的問題

原計劃將 6 個函數遷移至 `domain/effects.py`:
- 4 個 progress bar 函數
- 2 個 fade 函數

**但檢查後發現**:

| 函數 | 原計劃 | 實際依賴 | 正確歸屬 |
|------|--------|---------|---------|
| `_progress_bar_band_layout` | domain | 無 | ✅ domain |
| `_progress_bar_base_arrays` | domain | **PIL** | ❌ infrastructure |
| `_make_progress_bar_mask` | domain | **MoviePy** | ❌ infrastructure |
| `_build_progress_bar_segments` | domain | 無 | ✅ domain |
| `_apply_fadeout` | domain | **MoviePy** | ❌ infrastructure |
| `_apply_fadein` | domain | **MoviePy** | ❌ infrastructure |

---

### ✅ 做出的決策

**選擇策略 A1**: 只遷移純 domain 函數

**理由**:
1. ✅ 保持架構純淨 - domain 層不依賴 PIL/MoviePy
2. ✅ 降低風險 - 避免創建新模組與複雜重構
3. ✅ 快速完成 - 1 小時 vs 3-4 小時
4. ✅ 技術債可控 - 剩餘函數清楚標記為 infrastructure

**保留在 utils.py**:
- `_progress_bar_base_arrays` (使用 PIL)
- `_make_progress_bar_mask` (使用 MoviePy)
- `_apply_fadeout` (使用 MoviePy)
- `_apply_fadein` (使用 MoviePy)

**未來處理**: 這 4 個函數將在 Infrastructure Layer 遷移階段處理

---

## 📈 進度更新

### 已完成模組

| 模組 | 函數數 | 狀態 | 提交 |
|------|--------|------|------|
| domain/timing.py | 2 | ✅ 100% | 61fd9e2 |
| domain/layout.py | 4 | ✅ 100% | 1aeb0d1, ad01031 |
| **domain/effects.py** | **2** | **✅ 純邏輯完成** | **0512b3c** |

**總進度**: 8/37 函數 (21.6%)

---

### Batch 1 (Domain Layer) 進度

```
已完成: ████████████████░░░░░  8/13 (61.5%)
```

**剩餘 Domain 函數**:
- _plan_letter_images (需重構,124 行)
- 4 個 infrastructure 函數 (暫不計入 domain)

**實際 Pure Domain 完成度**: 8/9 (88.9%)

---

## 🎯 關鍵發現

### ✅ 成功因素

1. **及時發現架構問題**
   - 在開始遷移前檢查依賴
   - 避免了錯誤的架構決策

2. **靈活調整策略**
   - 從「遷移 6 個」調整為「遷移 2 個純邏輯」
   - 保持架構原則優先於進度數字

3. **完整測試驗證**
   - 4 個測試案例覆蓋主要場景
   - 驗證顏色帶計算、分段邏輯、邊界情況

4. **詳細文檔**
   - 每個函數 80+ 行 docstring
   - 包含參數說明、返回值、範例、注意事項

---

### 📚 學到的教訓

1. **MIGRATION_MAPPING.json 需要驗證**
   - 不能只看函數名稱,要檢查實際實作
   - 依賴分析比名稱分析更重要

2. **架構純淨性 > 進度數字**
   - 寧可少遷移幾個函數,也要保持 domain 層純淨
   - 技術債務要明確標記與規劃

3. **分批遷移的優勢**
   - 每個批次可以重新評估
   - 發現問題可以及時調整策略

---

## 📋 未來待處理

### Infrastructure 函數 (4 個)

**Progress Bar** (2 個):
- `_progress_bar_base_arrays` → `infrastructure/rendering/progress_bar.py` (新建)
- `_make_progress_bar_mask` → `infrastructure/video/moviepy_adapter.py`

**Fade Effects** (2 個):
- `_apply_fadeout` → `infrastructure/video/effects.py` (新建或併入 moviepy_adapter)
- `_apply_fadein` → `infrastructure/video/effects.py`

**預估時間**: 2-3 小時 (需創建新模組)

---

## 💡 下一步建議

### 選項 1: 挑戰重構 _plan_letter_images (推薦)

完成 Domain Layer 最後一個複雜函數

**優點**:
- ✅ Domain 層 100% 完成
- ✅ 解決最大難題
- ✅ 為 Infrastructure 遷移鋪路

**缺點**:
- ⚠️ 時間較長 (3-4h)
- ⚠️ 風險較高 (需重構)

---

### 選項 2: 轉向 Infrastructure Layer

先處理 4 個 PIL/MoviePy 函數

**優點**:
- ✅ 完成 progress bar 與 fade 的完整遷移
- ✅ 清理已知的架構債務

**缺點**:
- ⚠️ 需創建新模組
- ⚠️ Domain Layer 仍有未完成項目

---

### 選項 3: 快速方案

跳過複雜重構,直接建立 re-export 層

**優點**:
- ✅ 快速達成 ≥95% 縮減目標
- ✅ 低風險

**缺點**:
- ⚠️ 留下重構債務
- ⚠️ 未達「完全移除」目標

---

## ⏱️ 時間統計

### 已投入
- 階段 1: 30 分鐘 ✅
- 階段 2: 1 小時 ✅
- 階段 3: 1 小時 ✅
- **總計**: 2.5 小時

### 預估剩餘 (各選項)
- **選項 1** (重構 _plan_letter_images): 3-4h
- **選項 2** (Infrastructure 4 函數): 2-3h
- **選項 3** (快速方案): 4-6h 總計

---

## 提交記錄

```
commit 0512b3c
feat: 遷移 2 個純邏輯進度條函數至 domain/effects.py

階段 3 完成 (Domain Effects - 純邏輯部分):
- _progress_bar_band_layout: 計算顏色帶佈局
- _build_progress_bar_segments: 規劃倒數分段

架構決策:
- 保留 PIL/MoviePy 依賴函數在 utils.py
- 僅遷移純邏輯計算函數至 domain 層
- 維持架構純淨性

總進度: 8/37 (21.6%)
參考: PROGRESS_BAR_RECLASSIFICATION.md
```

---

## ❓ 決策時間

**您希望**:

**1.** 挑戰重構 _plan_letter_images (3-4h, 完成 Domain Layer)  
**2.** 轉向 Infrastructure Layer (2-3h, 處理 PIL/MoviePy 函數)  
**3.** 快速方案 (4-6h 總計, 跳至 re-export 層)

---

**當前成就**: 🏆 Domain 層純邏輯函數 88.9% 完成!  
**總進度**: 8/37 (21.6%)  
**時間投入**: 2.5h
