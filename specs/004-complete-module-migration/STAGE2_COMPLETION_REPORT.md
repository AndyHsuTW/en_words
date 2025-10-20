# 階段 2 完成報告

**日期**: 2025-10-20  
**狀態**: ✅ 完成  
**耗時**: ~30 分鐘

---

## 執行摘要

成功將 **3 個純邏輯函數**從 `utils.py` 遷移至 `domain/layout.py`,無任何外部依賴問題。

---

## ✅ 已遷移函數

### 1. `_normalize_letters_sequence(letters: str) -> List[str]`
- **位置**: `domain/layout.py` (line ~335)
- **功能**: 正規化字母序列,過濾空白與空字元
- **複雜度**: ⭐ (簡單)
- **依賴**: 無外部依賴,僅使用 Python 標準庫
- **驗證**: ✅ 通過

```python
# 測試案例
_normalize_letters_sequence("I  i\n") == ['I', 'i']
_normalize_letters_sequence("") == []
```

---

### 2. `_letter_asset_filename(ch: str) -> Optional[str]`
- **位置**: `domain/layout.py` (line ~358)
- **功能**: 根據字元產生對應的素材檔名 (大寫→".png", 小寫→"_small.png")
- **複雜度**: ⭐ (簡單)
- **依賴**: 無
- **驗證**: ✅ 通過

```python
# 測試案例
_letter_asset_filename("A") == "A.png"
_letter_asset_filename("z") == "z_small.png"
_letter_asset_filename("1") is None
```

---

### 3. `_letters_missing_names(missing: List[dict]) -> List[str]`
- **位置**: `domain/layout.py` (line ~384)
- **功能**: 從缺失素材列表中提取檔名或字元名稱,並去重
- **複雜度**: ⭐ (簡單)
- **依賴**: 無
- **驗證**: ✅ 通過

```python
# 測試案例
missing = [
    {"filename": "A.png", "char": "A"},
    {"char": "B"},
    {"filename": "A.png"}
]
_letters_missing_names(missing) == ["A.png", "B"]
```

---

## 📊 進度更新

| 階段 | 函數數量 | 狀態 | 耗時 |
|------|---------|------|------|
| 階段 1: 工具函數 | 2 | ✅ 完成 | 30 min |
| **階段 2: 純邏輯函數** | **3** | **✅ 完成** | **30 min** |
| 階段 3: 複雜重構 | TBD | ⏳ 待決策 | 3-4h |
| 階段 4: Infrastructure | TBD | ⏳ 待執行 | 4-5h |

**總進度**: 5/37 函數已遷移 (13.5%)

---

## 🎯 發現與結論

### ✅ 順利的部分

1. **純邏輯函數遷移非常順暢**
   - 無外部依賴 (PIL/MoviePy/FFmpeg)
   - 無常數引用問題
   - 函數獨立性高,無複雜呼叫鏈

2. **驗證快速**
   - 使用 Pylance MCP 直接執行測試
   - 所有函數行為與原始實作一致

3. **文檔完整**
   - 為每個函數添加詳細 docstring
   - 包含參數說明、返回值、使用範例

---

### ⚠️ 發現的問題

檢視 `domain/layout.py` 中剩餘待遷移的函數:

| 函數 | 行數 | 複雜度 | 外部依賴 | 建議 |
|------|------|--------|----------|------|
| `_plan_letter_images` | ~124 | ⭐⭐⭐⭐⭐ | PIL.Image, os.path | **需重構** |
| `_layout_zhuyin_column` | ~65 | ⭐⭐⭐ | typography 模組 | 可直接遷移 |

**關鍵發現**: `_plan_letter_images` 函數職責混淆:
- 包含 **domain logic** (字母序列正規化、尺寸計算)
- 包含 **infrastructure logic** (PIL 圖片讀取、檔案系統檢查)

---

## 💡 下一步建議

### 選項 A: 立即處理 `_layout_zhuyin_column` (推薦)
- **理由**: 函數相對獨立,雖然有 65 行,但職責單純
- **耗時**: 約 30 分鐘
- **風險**: 低

### 選項 B: 重構 `_plan_letter_images`
- **理由**: 這是 Batch 1 最複雜的函數,需要拆分為 domain + infrastructure
- **耗時**: 3-4 小時
- **風險**: 中高 (可能影響現有測試)

### 選項 C: 暫停並評估
- **理由**: 階段 2 已順利完成,可以在此決定是否繼續全量遷移
- **決策點**: 
  - 繼續策略 A (漸進式) → 執行選項 A 或 B
  - 改用策略 B (快速方案) → 跳到 Phase 3.6 建立 re-export 層
  - 改用策略 D (接受現狀) → 立即建立 re-export 層

---

## 提交記錄

```
commit 1aeb0d1
feat: 遷移 3 個純邏輯函數至 domain/layout.py

階段 2 完成:
- _normalize_letters_sequence
- _letter_asset_filename  
- _letters_missing_names

批次 1 (Domain Layer) 進度: 5/13
```

---

## ❓ 決策時間

**您希望**:

**A.** 繼續遷移 `_layout_zhuyin_column` (65 行,~30 min)  
**B.** 挑戰重構 `_plan_letter_images` (124 行, 3-4h)  
**C.** 暫停評估,決定是否調整策略  
**D.** 接受當前進度 (5/37),直接建立 re-export 層

---

**當前時間投入**: 階段 1 (30m) + 階段 2 (30m) = **1 小時**  
**原預估剩餘**: 11-15 小時 (策略 A 全量遷移)  
**快速方案剩餘**: 3-5 小時 (策略 B 部分遷移)
