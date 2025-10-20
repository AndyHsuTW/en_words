# Phase 3.5 遷移進度儀表板

**最後更新**: 2025-10-21 (階段 3 完成 - Domain Effects 純邏輯)

---

## 📊 總體進度

```
已完成: ████████░░░░░░░░░░░░░░░░░░░░░░░░░░  8/37 (21.6%)

時間: ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2.5h / 12-16h (策略A)
```

---

## ✅ 完成清單

### 階段 1: 工具函數 (domain/timing.py) ✅
- [x] `_coerce_non_negative_float` - 轉換非負浮點數
- [x] `_coerce_bool` - 智能布林轉換

### 階段 2: 純邏輯函數 (domain/layout.py) 🏆 100% 完成!
- [x] `_normalize_letters_sequence` - 正規化字母序列
- [x] `_letter_asset_filename` - 生成素材檔名
- [x] `_letters_missing_names` - 提取缺失素材名稱
- [x] `_layout_zhuyin_column` - 注音符號垂直佈局 (65 行)

### 階段 3: Domain Effects (純邏輯) 🎯 完成!
- [x] `_progress_bar_band_layout` - 計算顏色帶佈局
- [x] `_build_progress_bar_segments` - 規劃倒數分段

---

## ⏳ 待處理清單

### Batch 1: Domain Layer (剩餘 8/13)

#### domain/layout.py (剩餘 2 個)
- [ ] `_plan_letter_images` - ⭐⭐⭐⭐⭐ (124 行, **需重構**)
- [ ] `_layout_zhuyin_column` - ⭐⭐⭐ (65 行, 可直接遷移)

#### domain/effects.py (剩餘 6 個)
- [ ] `_progress_bar_band_layout` - ⭐⭐
- [ ] `_progress_bar_base_arrays` - ⭐⭐⭐
- [ ] `_make_progress_bar_mask` - ⭐⭐⭐
- [ ] `_build_progress_bar_segments` - ⭐⭐⭐⭐
- [ ] `_apply_fadeout` - ⭐⭐ (**應移至 infrastructure**)
- [ ] `_apply_fadein` - ⭐⭐ (**應移至 infrastructure**)

---

### Batch 2: Infrastructure Layer (12 個)
- [ ] infrastructure/rendering/pillow_adapter.py (3 個)
- [ ] infrastructure/video/moviepy_adapter.py (5 個)
- [ ] infrastructure/media/ffmpeg_wrapper.py (2 個)
- [ ] infrastructure/media/audio.py (2 個)

---

### Batch 3: Application Layer (12 個)
- [ ] application/video_service.py (12 個業務邏輯函數)

---

## 📈 模組狀態

| 模組 | 目標函數數 | 已遷移 | 剩餘 | 進度 |
|------|-----------|--------|------|------|
| domain/timing.py | 2 | 2 | 0 | ✅ 100% |
| domain/layout.py | 4 | 4 | 0 | ✅ 100% |
| domain/effects.py | 2 | 2 | 0 | ✅ 100% (純邏輯) |
| infrastructure/* | 16 | 0 | 16 | 🔴 0% (含 4 個重分類) |
| application/* | 12 | 0 | 12 | 🔴 0% |
| _plan_letter_images | 1 | 0 | 1 | 🔴 需重構 |
| **總計** | **37** | **8** | **29** | **21.6%** |

---

## ⏱️ 時間統計

### 已投入時間
- 階段 1 (工具函數): 30 分鐘 ✅
- 階段 2 (純邏輯 4 函數): 1 小時 ✅
- 階段 3 (進度條純邏輯 2 函數): 1 小時 ✅
- **總計**: 2.5 小時

### 預估剩餘時間 (策略 A)
- domain/effects.py: 1.5-2 小時
- 階段 3 (複雜重構): 3-4 小時
- 階段 4 (Infrastructure): 4-5 小時
- 測試與驗證: 1-2 小時
- **總計**: 10-13 小時

### 預估剩餘時間 (策略 B - 快速方案)
- 選擇性遷移: 2-3 小時
- Re-export 層: 1 小時
- 測試與驗證: 1-2 小時
- **總計**: 4-6 小時

---

## 🎯 關鍵指標

| 指標 | 當前值 | 目標值 | 達成率 |
|------|--------|--------|--------|
| utils.py 行數 | 3,713 | 80-120 | 0% (尚未縮減) |
| 函數遷移數 | 8 | 37 | 21.6% |
| 模組完成數 | 3 | 8 | 37.5% |
| 測試通過率 | 100% | 100% | ✅ 100% |
| 文檔完整度 | 高 | 高 | ✅ 完整 |
| 架構純淨度 | 高 | 高 | ✅ 100% |

---

## 🔍 品質檢查

### ✅ 已驗證
- [x] 所有遷移函數通過單元測試
- [x] 函數行為與原始實作一致
- [x] 完整的 docstring 與型別提示
- [x] Git 提交記錄清晰

### ⏳ 待驗證
- [ ] 整合測試 (pytest tests/)
- [ ] render_example.ps1 執行
- [ ] 效能測試 (佈局計算 < 50ms)

---

## 🚨 風險評估

### 低風險 (✅ 可安全繼續)
- 階段 1-2 函數: 簡單、獨立、無外部依賴
- 當前進度: 無測試失敗、無回歸問題

### 中風險 (⚠️ 需謹慎處理)
- `_layout_zhuyin_column`: 65 行,有模組間依賴
- domain/effects.py 函數: 部分需重新分類至 infrastructure

### 高風險 (🚨 需重構)
- `_plan_letter_images`: 124 行,職責混淆 (domain + infrastructure)
- 可能影響: `_parse_letters_data`, `render_video`, 批次處理流程

---

## 💡 建議行動

### 立即可執行 (低風險)
1. 遷移 `_layout_zhuyin_column` (~30 分鐘)
2. 檢查 domain/effects.py 函數的正確歸屬

### 需規劃執行 (中高風險)
3. 重構 `_plan_letter_images` (3-4 小時)
4. 重新分類 fade 函數至 infrastructure

### 戰略決策點
5. 決定是否繼續全量遷移 (策略 A)
6. 或改用部分遷移 + re-export (策略 B)

---

## 📋 決策樹

```
當前位置: 階段 2 完成 (5/37, 13.5%)
                    |
        ┌───────────┼───────────┐
        │           │           │
     選項 A      選項 B      選項 C
   繼續遷移    快速方案    接受現狀
        │           │           │
    _layout_   部分遷移   建立 re-
    zhuyin_      +       export
    column    re-export     層
        │           │           │
    30 min      4-6h        2-3h
        │           │           │
    評估是否     Phase      Phase
    重構大函數    3.6-3.8    3.6-3.8
        │
    3-4h (重構)
        │
    8.5-10.5h 總計
```

---

## 📞 需要決策

**請選擇下一步**:
- **A**: 遷移 `_layout_zhuyin_column` (繼續策略 A)
- **B**: 挑戰重構 `_plan_letter_images`
- **C**: 改用快速方案 (部分遷移)
- **D**: 接受當前進度,建立 re-export 層

---

**檔案位置**:
- 詳細報告: `STAGE2_COMPLETION_REPORT.md`
- 實際情況評估: `PHASE3.5_REALITY_CHECK.md`
- 批次 1 指南: `BATCH1_MIGRATION_GUIDE.md`
