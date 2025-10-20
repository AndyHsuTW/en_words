# _plan_letter_images 重構分析與計劃

**日期**: 2025-10-21  
**函數**: `_plan_letter_images(letters: str, asset_dir: str) -> Dict[str, Any]`  
**位置**: `spellvid/utils.py` line 327-460 (134 行)

---

## 📋 函數職責分析

### 當前職責 (混合)

這個函數目前混合了 **3 種職責**:

1. **Domain 邏輯** (純計算):
   - 正規化字母序列 → 已遷移 `_normalize_letters_sequence`
   - 生成檔名 → 已遷移 `_letter_asset_filename`
   - 計算縮放比例、間距、位置

2. **Infrastructure - 檔案系統**:
   - 檢查檔案是否存在 (`os.path.isfile`)
   - 構建檔案路徑 (`os.path.join`)

3. **Infrastructure - 圖像處理**:
   - 讀取圖片尺寸 (`Image.open` → PIL)
   - 處理圖片讀取異常

---

## 🎯 重構策略

### 方案: 分離為 3 層

```
┌─────────────────────────────────────────┐
│ domain/layout.py                        │
│ _calculate_letter_layout()              │
│ - 接收 letter_specs (含尺寸資訊)        │
│ - 純邏輯計算: 縮放、間距、位置         │
│ - 返回佈局數據                          │
└─────────────────────────────────────────┘
                 ▲
                 │ 呼叫
                 │
┌─────────────────────────────────────────┐
│ application/video_service.py            │
│ _plan_letter_images() (保留函數名)      │
│ - 編排流程: 檢查 → 讀取 → 計算         │
│ - 呼叫 infrastructure 與 domain         │
└─────────────────────────────────────────┘
                 │
                 ├──→ infrastructure/rendering/image_loader.py
                 │    _load_letter_image_specs()
                 │    - 檢查檔案存在
                 │    - 讀取圖片尺寸 (PIL)
                 │    - 返回 specs 列表
                 │
                 └──→ domain/layout.py
                      _calculate_letter_layout()
                      - 純邏輯計算佈局
```

---

## 📝 重構步驟

### Step 1: 創建 infrastructure 函數 (1-1.5h)

**文件**: `infrastructure/rendering/image_loader.py` (新建)

**函數**: `_load_letter_image_specs(letters, asset_dir) -> (specs, missing)`

**職責**:
- 接收字母字串與素材目錄
- 呼叫 `_normalize_letters_sequence`, `_letter_asset_filename` (domain)
- 檢查檔案存在 (`os.path.isfile`)
- 讀取圖片尺寸 (`PIL.Image.open`)
- 返回 (成功列表, 缺失列表)

**返回**:
```python
specs: List[Dict[str, Any]] = [
    {"char": "I", "filename": "I.png", "path": "...", "width": 800, "height": 1000},
    ...
]
missing: List[Dict[str, Any]] = [
    {"char": "X", "filename": None, "reason": "unsupported"},
    ...
]
```

---

### Step 2: 創建 domain 函數 (1h)

**文件**: `domain/layout.py`

**函數**: `_calculate_letter_layout(specs, target_height, available_width, ...) -> Dict`

**職責**:
- 接收圖片規格 (已知尺寸)
- 計算基礎縮放比例
- 計算總寬度與調整係數
- 計算每個字母的最終位置與尺寸
- 處理邊界對齊

**參數**:
```python
def _calculate_letter_layout(
    specs: List[Dict[str, Any]],
    target_height: int = LETTER_TARGET_HEIGHT,
    available_width: int = LETTER_AVAILABLE_WIDTH,
    base_gap: int = LETTER_BASE_GAP,
    extra_scale: float = LETTER_EXTRA_SCALE,
    safe_x: int = LETTER_SAFE_X,
) -> Dict[str, Any]:
```

**返回**:
```python
{
    "letters": [...],  # 佈局列表
    "gap": 10,         # 實際間距
    "bbox": {"w": 800, "h": 600, "x_offset": 0}
}
```

---

### Step 3: 更新 application 編排 (30min)

**選項 A**: 保留在 `utils.py` 作為向後兼容函數

```python
def _plan_letter_images(letters: str, asset_dir: str) -> Dict[str, Any]:
    """向後兼容層 - 將在 v2.0 移除"""
    from infrastructure.rendering.image_loader import _load_letter_image_specs
    from domain.layout import _calculate_letter_layout
    
    specs, missing = _load_letter_image_specs(letters, asset_dir)
    if not specs:
        return {"letters": [], "missing": missing, "gap": 0, "bbox": {"w": 0, "h": 0}}
    
    result = _calculate_letter_layout(specs)
    result["missing"] = missing
    return result
```

**選項 B**: 遷移至 `application/video_service.py`

(移動完整函數,但使用新的 infrastructure + domain 函數)

---

### Step 4: 測試驗證 (30min)

1. 單元測試 `_load_letter_image_specs`:
   - 測試檔案存在/缺失
   - 測試圖片可讀/不可讀
   
2. 單元測試 `_calculate_letter_layout`:
   - 測試單個字母
   - 測試多個字母
   - 測試寬度超限調整

3. 整合測試 `_plan_letter_images`:
   - 使用真實素材測試
   - 驗證結果與原函數一致

---

## ⚠️ 潛在風險

### 風險 1: PIL 依賴位置

**問題**: 
- `Image` 在 utils.py 中導入為頂層
- 需要在新模組中正確導入

**解決**:
```python
# infrastructure/rendering/image_loader.py
try:
    from PIL import Image
except ImportError:
    Image = None  # Graceful degradation
```

---

### 風險 2: 常數依賴

**問題**: 使用多個 `LETTER_*` 常數

**檢查清單**:
- ✅ `LETTER_BASE_GAP` - shared/constants.py
- ✅ `LETTER_AVAILABLE_WIDTH` - shared/constants.py
- ✅ `LETTER_TARGET_HEIGHT` - shared/constants.py
- ✅ `LETTER_EXTRA_SCALE` - shared/constants.py
- ✅ `LETTER_SAFE_X` - shared/constants.py

**解決**: 所有常數已在 `shared/constants.py`,可直接導入

---

### 風險 3: 測試覆蓋

**問題**: 現有測試可能依賴 `_plan_letter_images` 在 utils.py

**解決**:
- 保留 utils.py 中的函數作為 re-export
- 確保行為完全一致
- 運行完整測試套件驗證

---

## 📊 預估時間

| 步驟 | 任務 | 時間 |
|------|------|------|
| 1 | 創建 infrastructure/rendering/image_loader.py | 1-1.5h |
| 2 | 創建 domain/layout.py 中的 _calculate_letter_layout | 1h |
| 3 | 更新 utils.py 編排函數 (re-export) | 30min |
| 4 | 測試驗證 | 30min |
| **總計** | | **3-3.5h** |

---

## ✅ 成功標準

1. ✅ infrastructure 函數獨立可測試 (無 domain 邏輯)
2. ✅ domain 函數純邏輯 (無 PIL/os 依賴)
3. ✅ 所有現有測試通過
4. ✅ 新函數有完整 docstring
5. ✅ 架構清晰分層

---

## 💡 建議

### 立即開始

**建議執行順序**:
1. 先創建 `infrastructure/rendering/image_loader.py`
2. 再創建 `domain/layout.py` 中的計算函數
3. 更新 utils.py 為簡單編排
4. 驗證測試

### 或者暫停評估

如果覺得風險過高,可以選擇:
- 保留 `_plan_letter_images` 在 utils.py
- 直接進入 Phase 3.6 建立 re-export 層
- 將此函數標記為「待重構」

---

## ❓ 決策

**您希望**:

**A.** 立即開始重構 (3-3.5h, 完成 Domain Layer)  
**B.** 暫停重構,保留此函數,進入 Phase 3.6  
**C.** 先看看其他選項 (Infrastructure Layer)

---

**當前狀態**: 已準備好詳細重構計劃  
**風險評估**: 中等 (有完整分析,風險可控)  
**建議**: 選擇 A,完成最後的 Domain Layer 挑戰
