# Phase 3.5 遷移實際情況評估

**日期**: 2025-10-20  
**當前進度**: 2/37 函數已遷移  
**預估完成時間**: 原估 12-16h → 實際可能需要 20-25h

---

## 執行摘要

在開始批次 1 (Domain Layer) 遷移後,發現了幾個關鍵問題,需要重新評估遷移策略。

### ✅ 已完成

1. **domain/timing.py**: 成功遷移 2 個簡單工具函數
   - `_coerce_non_negative_float`
   - `_coerce_bool`
   - 進度: 2/37 (5%)

---

## 🚨 發現的關鍵問題

### 問題 1: 職責分類錯誤

許多被標記為 "domain" 的函數實際上包含 infrastructure 邏輯:

| 函數 | 原計劃 | 實際應屬於 | 原因 |
|------|--------|-----------|------|
| `_plan_letter_images` | domain/layout.py | infrastructure/rendering/ | 使用 PIL Image |
| `_apply_fadeout` | domain/effects.py | infrastructure/video/ | 使用 MoviePy |
| `_apply_fadein` | domain/effects.py | infrastructure/video/ | 使用 MoviePy |
| `_make_progress_bar_mask` | domain/effects.py | infrastructure/rendering/ | 使用 numpy arrays |

**影響**: 需要重新生成 MIGRATION_MAPPING.json

---

### 問題 2: 函數間高度耦合

許多函數有複雜的依賴鏈:

```
_plan_letter_images
  ├─ 呼叫 _normalize_letters_sequence
  ├─ 呼叫 _letter_asset_filename
  ├─ 使用 PIL.Image
  ├─ 使用 os.path
  └─ 使用 5+ constants
```

**影響**: 無法單獨遷移,必須批次處理

---

### 問題 3: 部分函數需要重構

某些函數同時包含多種職責:

```python
def _plan_letter_images(letters: str, asset_dir: str):
    # 1. 純邏輯: 正規化字母序列 (domain)
    seq = _normalize_letters_sequence(letters)
    
    # 2. 檔案系統: 檢查檔案存在 (infrastructure)
    if not os.path.isfile(path_str):
        ...
    
    # 3. PIL 操作: 讀取圖片尺寸 (infrastructure)
    with Image.open(path_str) as img:
        orig_w, orig_h = img.size
    
    # 4. 佈局計算: 縮放與間距 (domain)
    base_scale = min(1.0, target_height / float(orig_h))
    ...
```

**影響**: 需要先重構函數,拆分職責,才能正確遷移

---

## 📊 重新評估的工作量

### 原預估 vs 實際

| 階段 | 原預估 | 實際需求 | 原因 |
|------|--------|---------|------|
| 批次 1 (Domain) | 4h | 8-10h | 需要重構 + 重新分類 |
| 批次 2 (Infrastructure) | 5h | 6-8h | 部分已包含在批次 1 |
| 批次 3 (Application) | 5h | 6-8h | 依賴前兩批次 |
| **總計** | 14h | **20-26h** | 增加 43-86% |

---

## 💡 修正後的執行策略

### 策略 A: 漸進式遷移 (推薦)

**原則**: 只遷移職責明確、依賴簡單的函數

**階段 1**: 簡單工具函數 (已完成 ✅)
- `domain/timing.py`: 2 個函數
- 時間: 30 分鐘

**階段 2**: 純邏輯函數 (無外部依賴)
- `_normalize_letters_sequence`
- `_letters_missing_names`
- `_letter_asset_filename`
- 時間: 1h

**階段 3**: 重構複雜函數
- 拆分 `_plan_letter_images` 為 domain + infrastructure
- 時間: 3-4h

**階段 4**: Infrastructure 函數
- PIL 相關 → `infrastructure/rendering/`
- MoviePy 相關 → `infrastructure/video/`
- 時間: 4-5h

**總計**: 8.5-10.5h

---

### 策略 B: 部分遷移 + Re-export (快速方案)

**原則**: 只遷移最關鍵的 10-15 個函數,其餘保留在 utils.py

**優點**:
- ✅ 快速達成 ≥95% 縮減目標
- ✅ 降低風險
- ✅ 保持系統穩定

**缺點**:
- ⚠️ 未完全達成「完全移除舊程式碼」目標
- ⚠️ utils.py 仍包含部分實作 (但已大幅縮減)

**時間**: 4-6h

---

### 策略 C: 暫停遷移,重新規劃 (保守方案)

**行動**:
1. 保留當前進度 (2 個函數已遷移)
2. 重新分析 37 個函數的正確歸屬
3. 生成新的 MIGRATION_MAPPING_V2.json
4. 制定更詳細的重構計劃

**時間**: 規劃 2h + 執行 15-20h

---

## 🎯 建議決策

考慮到:
- 原計劃目標: "完全移除舊程式碼"
- 實際發現: 許多函數職責不清,需要重構
- 時間成本: 20-26h vs 原估 14h

我建議採用 **策略 A (漸進式遷移)**:

### 立即執行 (接下來 2-3h)

1. ✅ 完成階段 2: 遷移 3 個簡單函數
2. ✅ 評估階段 3 的重構需求
3. ✅ 決定是否繼續全量遷移

### 後續選擇

**選項 1**: 如果階段 2 順利 → 繼續執行策略 A  
**選項 2**: 如果發現更多問題 → 改用策略 B (部分遷移)  
**選項 3**: 如果風險過高 → 採用策略 C (暫停重規劃)

---

## 📋 當前狀態總結

### 已完成
- ✅ Phase 3.1-3.4: 環境、TDD、分析、映射
- ✅ Phase 3.5 (2/37): `domain/timing.py` 遷移完成

### 進行中
- 🔄 Phase 3.5 批次 1: Domain Layer 遷移 (2/13 完成)

### 待決策
- ❓ 採用哪種遷移策略 (A/B/C)
- ❓ 是否重構複雜函數
- ❓ 是否調整最終目標 (完全移除 vs 大幅縮減)

---

## 建議給用戶的選擇

**您希望**:

**A.** 繼續漸進式遷移 (策略 A) - 先完成 3 個簡單函數,再評估
**B.** 採用快速方案 (策略 B) - 部分遷移 + re-export,快速達成 ≥95% 縮減
**C.** 暫停並重新規劃 (策略 C) - 更詳細的分析與重構計劃

**D.** 接受當前進度 (2/37),直接進入 Phase 3.6 建立 re-export 層

---

**時間統計**:
- 已投入: ~2.5h (Phase 3.1-3.5 初期)
- 策略 A 剩餘: 8.5-10.5h
- 策略 B 剩餘: 4-6h
- 策略 D 剩餘: 2-3h (跳至 re-export)

