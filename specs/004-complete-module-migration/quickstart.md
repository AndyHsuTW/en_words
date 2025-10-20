# Quickstart: 完全移除舊程式碼驗證流程

**Feature**: 004-complete-module-migration  
**Purpose**: 提供完整的執行與驗證步驟,確保舊程式碼被完全移除且功能正常  
**Date**: 2025-10-19

## Overview

本文件對應 spec.md 的 9 個 Acceptance Scenarios,提供逐步驗證流程,確保 utils.py 從 3,714 行縮減至 80-120 行 (≥95%),所有功能正常運作。

---

## Prerequisites (前置條件)

### Environment Setup
```powershell
# 1. 確認在正確的分支
git branch --show-current  # 應顯示 004-complete-module-migration

# 2. 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 3. 確認 Python 版本
python --version  # 應為 Python 3.13.0

# 4. 安裝開發依賴 (如果尚未安裝)
pip install -r requirements-dev.txt
```

### Baseline Verification
```powershell
# 驗證當前 utils.py 狀態
Get-Content spellvid\utils.py | Measure-Object -Line  # 應顯示約 3,714 行

# 驗證測試套件可執行
.\scripts\run_tests.ps1  # 應全部通過 (baseline)

# 驗證 render_example.ps1 可執行
.\scripts\render_example.ps1  # 應產出 7 個 MP4
```

**Expected Baseline**:
- utils.py: 3,714 lines
- All tests: PASS
- render_example.ps1: 7 MP4 files generated

---

## Step 0: 函數使用分析 (Scenario 1)

### 目標
產生完整的函數使用報告,區分三類:
- **生產使用**: 被 `spellvid/` (非測試) 或 `scripts/` 引用
- **測試專用**: 僅被 `tests/` 引用
- **完全未使用**: 無任何引用

### Execution

```powershell
# 1. 執行函數使用分析腳本 (Task T001-T003 實作)
python scripts/analyze_function_usage.py --input spellvid/utils.py --output specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json

# 2. 檢視報告摘要
python -c "import json; data = json.load(open('specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json')); print(f'Production: {sum(1 for r in data if r[\"category\"]==\"production\")}'); print(f'Test-only: {sum(1 for r in data if r[\"category\"]==\"test_only\")}'); print(f'Unused: {sum(1 for r in data if r[\"category\"]==\"unused\")}')"
```

### Expected Output

```json
{
  "function_name": "_progress_bar_band_layout",
  "category": "test_only",
  "references": [
    {
      "filepath": "tests/test_progress_bar.py",
      "line_number": 45,
      "context": "..."
    }
  ],
  "call_count": 1,
  "analysis_confidence": 1.0,
  "notes": ""
}
```

### Validation Checklist
- [ ] FUNCTION_USAGE_REPORT.json 已產生
- [ ] 報告包含所有 ~50+ 函數
- [ ] 三類分類互斥且完整
- [ ] Production 函數數量: 15-25 個
- [ ] Test-only 函數數量: 10-15 個
- [ ] Unused 函數數量: 5-10 個
- [ ] Confidence ≥0.8 的函數佔比 ≥80%

**Success Criteria**: ✅ SC-1 (函數使用分析完成)

---

## Step 1: 冗餘函數清理 (Scenario 2)

### 目標
直接刪除未被生產代碼使用的函數 (test_only + unused),預估刪除 ~10-20 個

### Execution

```powershell
# 1. 備份 utils.py
Copy-Item spellvid\utils.py spellvid\utils.py.backup_before_deletion

# 2. 執行冗餘函數刪除腳本 (Task T006-T007 實作)
python scripts/delete_redundant_functions.py --report specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json --target spellvid/utils.py

# 3. 檢視刪除理由記錄
cat specs/004-complete-module-migration/DELETION_LOG.md

# 4. 驗證測試 (預期可能有部分測試失敗)
.\scripts\run_tests.ps1
```

### Expected Output

**DELETION_LOG.md**:
```markdown
| function_name | category | reason | references_count |
|---------------|----------|--------|------------------|
| _progress_bar_band_layout | test_only | 僅被 tests/test_progress_bar.py 使用,生產代碼已用 domain.effects.create_progress_bar | 1 |
| _unused_helper | unused | 無任何引用,死程式碼 | 0 |
```

**File Size Change**:
- Before: 3,714 lines
- After: ~3,500-3,600 lines (刪除 ~100-200 行,視函數大小)
- Deleted functions: 10-20 個

### Validation Checklist
- [ ] DELETION_LOG.md 已產生且完整
- [ ] 所有 test_only 函數已從 utils.py 刪除
- [ ] 所有 unused 函數已從 utils.py 刪除
- [ ] utils.py 行數減少 (但仍保留 production 函數實作)
- [ ] 測試可能失敗 (因測試專用函數已刪除,正常現象)

**Success Criteria**: ✅ SC-2 (冗餘函數清理,刪除 ~10-20 個)

---

## Step 2: 有效函數遷移 (Scenario 3)

### 目標
遷移所有 production 函數至新模組 (~15-25 個),100% 遷移率

### Execution

```powershell
# 1. 執行函數遷移腳本 (Task T010-T032 實作)
python scripts/migrate_functions.py --report specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json --mapping specs/004-complete-module-migration/MIGRATION_MAPPING.json

# 2. 檢視遷移對應表
cat specs/004-complete-module-migration/MIGRATION_MAPPING.json

# 3. 驗證新模組函數可 import
python -c "from spellvid.domain.effects import create_progress_bar; print('✅ domain.effects OK')"
python -c "from spellvid.infrastructure.video.effects import apply_fadeout; print('✅ video.effects OK')"

# 4. 執行契約測試
pytest tests/contract/test_migration_mapping_contract.py -v
```

### Expected Output

**MIGRATION_MAPPING.json** (sample):
```json
{
  "function_name": "create_progress_bar",
  "old_location": "spellvid/utils.py",
  "new_location": "spellvid/domain/effects.py",
  "migration_status": "migrated",
  "reason": "生產代碼使用,純視覺效果邏輯,遷移至領域層",
  "wrapper_needed": false,
  "signature_notes": "簽章無變更",
  "dependencies": ["_progress_bar_layout", "_progress_bar_base_arrays"]
}
```

**New Module Structure**:
```
spellvid/domain/effects.py       ← 新增 5-8 個函數
spellvid/infrastructure/video/effects.py  ← 新增 4-6 個函數
spellvid/domain/layout.py        ← 新增 3-5 個函數
spellvid/infrastructure/media/utils.py    ← 新增 2-3 個函數
spellvid/application/video_service.py     ← 新增 1-3 個函數
```

### Validation Checklist
- [ ] 所有 production 函數都有對應的新模組實作
- [ ] MIGRATION_MAPPING.json 完整且正確
- [ ] 新模組函數可獨立 import (無 ImportError)
- [ ] 契約測試 `test_migration_mapping_contract.py` 通過
- [ ] utils.py 仍保留完整實作 (尚未刪除,僅複製至新模組)

**Success Criteria**: ✅ SC-3 (有效函數遷移完成,100% 遷移率)

---

## Step 3: 建立最小 re-export 層 (Scenario 4)

### 目標
重寫 utils.py 為 80-120 行 re-export 層,維持所有現有 import 路徑有效

### Execution

```powershell
# 1. 備份當前 utils.py (包含完整實作)
Copy-Item spellvid\utils.py spellvid\utils.py.backup_before_reexport

# 2. 執行 re-export 層生成腳本 (Task T034-T035 實作)
python scripts/generate_reexport_layer.py --mapping specs/004-complete-module-migration/MIGRATION_MAPPING.json --output spellvid/utils.py

# 3. 檢視新 utils.py
cat spellvid\utils.py | Select-Object -First 30  # 檢視前 30 行
Get-Content spellvid\utils.py | Measure-Object -Line  # 檢視總行數

# 4. 驗證 DeprecationWarning 觸發
python -c "import warnings; warnings.simplefilter('always'); import spellvid.utils"
```

### Expected Output

**New utils.py** (80-120 lines):
```python
# spellvid/utils.py - Re-export Layer (Deprecated)

import warnings as _warnings
_warnings.warn(
    "The 'spellvid.utils' module is deprecated...",
    DeprecationWarning,
    stacklevel=2
)

# Imports from new modules
from spellvid.domain.effects import create_progress_bar
from spellvid.infrastructure.video.effects import apply_fadeout
# ... (30-50 lines of imports)

# Aliases
render_video_stub = render_video
# ... (15-30 lines of aliases)

__all__ = [
    'create_progress_bar',
    'apply_fadeout',
    # ... (20-25 lines)
]
```

**File Size**:
- Line count: 80-120 lines
- Reduction rate: (3,714 - 100) / 3,714 = 97.3% ✅

### Validation Checklist
- [ ] utils.py 行數在 80-120 範圍
- [ ] Reduction rate ≥ 95%
- [ ] DeprecationWarning 在 import 時觸發
- [ ] 所有現有 `from spellvid.utils import X` 仍可執行
- [ ] utils.py 無實作邏輯 (僅 import/alias/wrapper)
- [ ] 契約測試 `test_reexport_layer_contract.py` 通過

**Success Criteria**: ✅ SC-4 (utils.py 縮減至 80-120 行,≥95% 縮減率)

---

## Step 4: 測試更新 (Scenario 5-6)

### 目標
更新測試檔案 import 路徑,確保所有測試通過

### Execution (Scenario 5 - 預期測試失敗)

```powershell
# 1. 執行測試套件 (預期失敗)
.\scripts\run_tests.ps1

# Expected: 部分測試失敗,因為:
# - 測試專用函數已刪除 (test_only category)
# - 測試仍使用舊 import 路徑
```

**Expected Failures**:
```
tests/test_progress_bar.py::test_layout FAILED
ImportError: cannot import name '_progress_bar_band_layout' from 'spellvid.utils'
```

### Execution (Scenario 6 - 修復測試)

```powershell
# 2. 更新測試 import 路徑 (Task T038 實作)
python scripts/update_test_imports.py --test-dir tests/

# 3. 手動審查測試變更
git diff tests/

# 4. 再次執行測試套件 (預期全通過)
.\scripts\run_tests.ps1
```

**Expected Changes** (sample):
```diff
# tests/test_progress_bar.py
- from spellvid.utils import _progress_bar_band_layout
+ from spellvid.domain.effects import create_progress_bar

- def test_layout():
-     result = _progress_bar_band_layout(...)
+ def test_create_progress_bar():
+     result = create_progress_bar(...)
```

### Validation Checklist
- [ ] 所有測試檔案 import 已更新至新模組路徑
- [ ] 測試專用函數已改用新模組的 public API
- [ ] 執行 `.\scripts\run_tests.ps1` 結果: 0 failures
- [ ] 無 ImportError 或 AttributeError

**Success Criteria**: ✅ SC-5 (測試全通過,0 failures)

---

## Step 5: 核心功能驗證 (Scenario 7)

### 目標
執行 render_example.ps1,驗證成功產出 7 個有效 MP4 檔案

### Execution

```powershell
# 1. 清理舊輸出
Remove-Item out\*.mp4 -Force

# 2. 執行 render_example.ps1
.\scripts\render_example.ps1

# 3. 檢查輸出檔案
Get-ChildItem out\*.mp4 | Measure-Object  # 應為 7 個檔案
Get-ChildItem out\*.mp4 | Select-Object Name, Length
```

### Expected Output

```
Name          Length (bytes)
----          --------------
Ice.mp4       ~2,000,000
Apple.mp4     ~2,500,000
...           ...
(Total: 7 MP4 files)
```

### Validation Checklist
- [ ] 產出 7 個 MP4 檔案
- [ ] 所有檔案大小 > 0 bytes (非空檔案)
- [ ] 可用媒體播放器正常播放
- [ ] 視頻內容正確 (字母、中文、注音、圖片、音訊)

**Success Criteria**: ✅ SC-6 (render_example.ps1 成功產出 7 個有效 MP4)

---

## Step 6: 最終驗證 (Scenario 8-9)

### 目標
確認 utils.py 無實作邏輯,僅包含 import/re-export/DeprecationWarning

### Execution

```powershell
# 1. 檢查 utils.py 行數
Get-Content spellvid\utils.py | Measure-Object -Line

# 2. 檢查檔案內容 (無實作邏輯)
Select-String -Path spellvid\utils.py -Pattern "^def .+:" | Select-Object -First 5

# 3. 確認縮減率
python -c "original=3714; current=$(Get-Content spellvid\utils.py | Measure-Object -Line).Lines; rate=(original-current)/original; print(f'Reduction: {rate:.1%}')"

# 4. 執行最終契約測試
pytest tests/contract/ -v
```

### Expected Output

**Line Count**:
```
Lines: 95
(在 80-120 範圍內 ✅)
```

**Content Check**:
```
# 應僅看到 wrapper 函數定義,無複雜邏輯
def render_video_stub(item: dict, ...):
    warnings.warn(...)
    ...
    return render_video(...)
```

**Reduction Rate**:
```
Reduction: 97.4%
(≥95% ✅)
```

### Validation Checklist
- [ ] utils.py 行數: 80-120 lines ✅
- [ ] Reduction rate: ≥95% ✅
- [ ] 檔案僅包含: import, alias, wrapper, __all__
- [ ] 無實作邏輯 (無 for, while, class, 複雜 if-else)
- [ ] 所有契約測試通過

**Success Criteria**: 
- ✅ SC-7 (utils.py 無實作程式碼)
- ✅ SC-4 (utils.py 最小化至 80-120 行)

---

## Final Validation Summary

### Checklist

**Code Quality**:
- [ ] utils.py 從 3,714 行縮減至 80-120 行 (≥95%)
- [ ] 冗餘函數已刪除 (10-20 個)
- [ ] 有效函數已遷移至新模組 (15-25 個)
- [ ] Re-export 層已建立且正確

**Testing**:
- [ ] 所有契約測試通過 (tests/contract/)
- [ ] 完整測試套件通過 (0 failures)
- [ ] render_example.ps1 產出 7 個有效 MP4

**Documentation**:
- [ ] FUNCTION_USAGE_REPORT.json 完整
- [ ] MIGRATION_MAPPING.json 完整
- [ ] DELETION_LOG.md 記錄完整

**Backward Compatibility**:
- [ ] 現有 import 路徑仍有效
- [ ] DeprecationWarning 正常觸發
- [ ] 無破壞性變更

### Success Criteria Completion

- ✅ SC-1: 函數使用分析完成
- ✅ SC-2: 冗餘函數清理 (~10-20 個)
- ✅ SC-3: 有效函數遷移完成 (100%)
- ✅ SC-4: utils.py 最小化 (80-120 行,≥95%)
- ✅ SC-5: 測試全通過 (0 failures)
- ✅ SC-6: render_example.ps1 產出 7 MP4
- ✅ SC-7: utils.py 無實作程式碼
- ✅ SC-8: 文件更新完成
- 🎯 SC-9: (Optional) 測試性能改善 <5min

---

## Rollback Plan (緊急回退)

If any step fails critically:

```powershell
# 回退至原始 utils.py
Copy-Item spellvid\utils.py.backup_before_reexport spellvid\utils.py -Force

# 回退至刪除前
Copy-Item spellvid\utils.py.backup_before_deletion spellvid\utils.py -Force

# 驗證回退成功
.\scripts\run_tests.ps1
```

---

## Performance Benchmarks (Optional, SC-9)

### Test Suite Performance

**Before Optimization**:
```powershell
Measure-Command { .\scripts\run_tests.ps1 }
# Expected: >30 minutes
```

**After Optimization** (pytest-xdist):
```powershell
Measure-Command { pytest -n auto }
# Target: <5 minutes
```

---

**Quickstart Complete**: 2025-10-19  
**Next**: Execute implementation (Task T001-T045)  
**Estimated Time**: 30-42 hours
