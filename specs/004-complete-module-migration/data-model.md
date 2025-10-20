# Data Model: 函數遷移對應表

**Feature**: 004-complete-module-migration  
**Phase**: 1 (Design & Contracts)  
**Date**: 2025-10-19

## Entity Definitions

### 1. FunctionUsageReport (函數使用分析報告)

**Purpose**: 記錄 utils.py 中每個函數的使用情況,用於分類決策

**Attributes**:
```python
@dataclass
class FileReference:
    filepath: str          # 引用檔案路徑 (相對於專案根目錄)
    line_number: int       # 引用行號
    context: str           # 引用上下文 (前後各 1 行)

@dataclass
class FunctionUsageReport:
    function_name: str     # 函數名稱 (如 _progress_bar_band_layout)
    category: Literal["production", "test_only", "unused"]  # 使用分類
    references: List[FileReference]  # 所有引用位置
    call_count: int        # 總引用次數
    analysis_confidence: float  # 分析信心度 (0.0-1.0, 三工具一致=1.0)
    notes: str            # 人工審查註記
```

**Classification Rules**:
- **production**: 
  - 被 `spellvid/*.py` (排除 `spellvid/utils.py` 自身與 tests) 引用 **OR**
  - 被 `scripts/*.py` 引用
- **test_only**: 
  - **僅**被 `tests/*.py` 引用
  - 不被生產代碼引用
- **unused**: 
  - 無任何 `.py` 檔案引用 (排除 `__pycache__/`, `*.bak`, `*.pyc`)

**Validation Rules**:
- `category` 必須為三者之一,互斥
- `call_count == len(references)`
- `analysis_confidence >= 0.8` 才可自動處理,< 0.8 需人工審查
- `references` 中的 `filepath` 必須存在且為 `.py` 檔案

**Example**:
```json
{
  "function_name": "_progress_bar_band_layout",
  "category": "test_only",
  "references": [
    {
      "filepath": "tests/test_progress_bar.py",
      "line_number": 45,
      "context": "def test_layout():\n    result = _progress_bar_band_layout(...)\n    assert ..."
    }
  ],
  "call_count": 1,
  "analysis_confidence": 1.0,
  "notes": "僅測試使用,生產代碼已用 domain.effects.create_progress_bar 替代"
}
```

---

### 2. FunctionMigration (函數遷移對應)

**Purpose**: 記錄函數的遷移決策與新位置

**Attributes**:
```python
@dataclass
class FunctionMigration:
    function_name: str     # 函數名稱
    old_location: str      # 舊位置 (固定為 "spellvid/utils.py")
    new_location: Optional[str]  # 新位置 (模組路徑, None 表示已刪除)
    migration_status: Literal["deleted", "migrated", "kept"]  # 處理狀態
    reason: str           # 處理理由
    wrapper_needed: bool  # 是否需要 adapter wrapper
    signature_notes: str  # 簽章差異說明
    dependencies: List[str]  # 依賴的其他函數 (from call graph)
```

**Migration Status**:
- **deleted**: 函數已從 utils.py 刪除,無遷移
  - Applies to: `category == "test_only"` OR `category == "unused"`
- **migrated**: 函數已遷移至新模組
  - Applies to: `category == "production"`
  - `new_location` 必須非 None
- **kept**: 函數保留在 utils.py (例外情況,需特殊理由)
  - Applies to: 極少數無法遷移的特殊案例

**Mapping Rules** (category="production" 函數):

| 函數類別 | 新模組位置 | Rationale |
|---------|----------|-----------|
| Progress bar 相關 | `spellvid/domain/effects.py` | 純視覺效果邏輯,屬領域層 |
| Video effects (_apply_fadeout, etc) | `spellvid/infrastructure/video/effects.py` | MoviePy 整合,屬基礎設施層 |
| Letter/layout 輔助 | `spellvid/domain/layout.py` | 佈局計算邏輯,屬領域層 |
| Media 處理 (_probe_duration, etc) | `spellvid/infrastructure/media/utils.py` | FFmpeg/媒體整合,屬基礎設施層 |
| Entry/Ending 視頻 | `spellvid/application/video_service.py` | 業務流程編排,屬應用層 |

**Validation Rules**:
- `migration_status == "deleted"` → `new_location` 必須為 None
- `migration_status == "migrated"` → `new_location` 必須存在且為有效模組路徑
- `wrapper_needed == True` → `signature_notes` 必須非空
- `dependencies` 中的函數必須在同批或已遷移

**Example**:
```json
{
  "function_name": "_apply_fadeout",
  "old_location": "spellvid/utils.py",
  "new_location": "spellvid/infrastructure/video/effects.py",
  "migration_status": "migrated",
  "reason": "生產代碼使用,遷移至基礎設施層 (MoviePy 整合)",
  "wrapper_needed": false,
  "signature_notes": "簽章無變更,直接 re-export",
  "dependencies": ["_ensure_dimensions"]
}
```

---

### 3. ReexportLayer (Re-export 層定義)

**Purpose**: 定義新 utils.py 的內容結構,確保向後相容

**Attributes**:
```python
@dataclass
class ReexportLayer:
    exported_functions: List[str]  # 需 re-export 的函數名稱清單
    import_statements: List[str]   # Import 語句清單
    aliases: Dict[str, str]        # Alias 對應 {old_name: new_import_path}
    deprecation_warnings: List[str]  # DeprecationWarning 訊息清單
    target_line_count: Tuple[int, int]  # 目標行數範圍 (80, 120)
```

**Structure Template**:
```python
# spellvid/utils.py (Re-export Layer)
# Target: 80-120 lines, ≥95% reduction from 3,714 lines

# ===== DeprecationWarning (15 lines) =====
import warnings as _warnings

_warnings.warn(
    "The 'spellvid.utils' module is deprecated and will be removed in v2.0. "
    "Please import from the new modular structure:\n"
    "  - spellvid.domain.* (pure logic)\n"
    "  - spellvid.infrastructure.* (framework adapters)\n"
    "  - spellvid.application.* (business services)\n"
    "See doc/ARCHITECTURE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# ===== Import Statements (30-50 lines, depends on migrated count) =====
# Domain layer
from spellvid.domain.effects import (
    create_progress_bar,
    apply_reveal_effect,
    # ... other domain functions
)

# Infrastructure layer
from spellvid.infrastructure.video.effects import (
    apply_fadeout,
    apply_fadein,
    concatenate_with_transitions,
    # ... other video effects
)

# Application layer
from spellvid.application.video_service import (
    render_video,
    create_entry_video,
    create_ending_video,
    # ... other application services
)

# ===== Aliases (15-30 lines, for backward compatibility) =====
# Preserve old function names
render_video_stub = render_video
_apply_fadeout = apply_fadeout
_apply_fadein = apply_fadein
# ... other aliases

# ===== __all__ Export List (20-25 lines) =====
__all__ = [
    # Domain
    'create_progress_bar',
    'apply_reveal_effect',
    # Infrastructure
    'apply_fadeout',
    'apply_fadein',
    # Application
    'render_video',
    'render_video_stub',  # deprecated alias
    # ... full export list
]
```

**Validation Rules**:
- 實際行數必須在 `target_line_count` 範圍內 (80-120 行)
- 所有 `exported_functions` 都必須在 `import_statements` 或 `aliases` 中定義
- `__all__` 列表必須與 `exported_functions` 一致
- 每個 import 的模組必須存在且可匯入
- DeprecationWarning 必須在檔案開頭觸發

**Metrics**:
- **Reduction Rate**: `(old_lines - new_lines) / old_lines * 100%`
  - Target: ≥95% (3,714 → 80-120 lines)
- **Re-export Count**: len(exported_functions)
  - Expected: 15-25 個函數 (基於生產使用函數數量)

---

## State Transitions

### Overall Flow

```
utils.py (3,714 行, ~50 函數)
  ↓ [Step 0: 函數使用分析]
FunctionUsageReport (三類分類)
  ├─ production (15-25 個) → [Step 2: 遷移] → 新模組
  ├─ test_only (10-15 個) → [Step 1: 刪除] → ✗
  └─ unused (5-10 個) → [Step 1: 刪除] → ✗
  ↓ [Step 3: 建立 re-export]
ReexportLayer (80-120 行)
  ↓ [Step 4: 驗證]
✅ 所有測試通過, render_example.ps1 產出 7 MP4
```

### Detailed State Machine

```
State 1: INITIAL
  - utils.py 包含所有函數實作 (3,714 行)
  - 狀態: 完整實作 + DeprecationWarning

State 2: ANALYZED
  - FunctionUsageReport 已產生
  - 每個函數都有明確分類 (production/test_only/unused)
  - 觸發條件: Step 0 完成

State 3: REDUNDANT_REMOVED
  - test_only 與 unused 函數已從 utils.py 刪除
  - 剩餘函數數量: 15-25 個 (僅 production)
  - 觸發條件: Step 1 完成

State 4: MIGRATED
  - production 函數已遷移至新模組
  - utils.py 僅保留空殼 (函數定義為 pass 或簡單 wrapper)
  - 觸發條件: Step 2 完成

State 5: REEXPORT_CREATED
  - utils.py 重寫為 re-export 層 (80-120 行)
  - 所有現有 import 路徑仍有效
  - 觸發條件: Step 3 完成

State 6: VALIDATED (FINAL)
  - 所有測試通過 (SC-5)
  - render_example.ps1 產出 7 MP4 (SC-6)
  - utils.py 無實作邏輯 (SC-7)
  - 觸發條件: Step 4-5 完成
```

---

## Function Migration Mapping Table

### Template (待 Step 0 分析後填入實際數據)

| 函數名稱 | 分類 | 新位置 | 狀態 | 理由 | Wrapper |
|---------|------|--------|------|------|---------|
| `_progress_bar_band_layout` | TBD | TBD | pending | 待分析 | TBD |
| `_progress_bar_base_arrays` | TBD | TBD | pending | 待分析 | TBD |
| `_make_progress_bar_mask` | TBD | TBD | pending | 待分析 | TBD |
| `_apply_fadeout` | TBD | TBD | pending | 待分析 | TBD |
| ... | ... | ... | ... | ... | ... |

**Note**: 此表將在 Step 0 (函數使用分析) 完成後更新為實際數據。預期結果:
- **production** 分類: 15-25 個函數,需遷移
- **test_only** 分類: 10-15 個函數,直接刪除
- **unused** 分類: 5-10 個函數,直接刪除

### Expected Final Distribution

| 新模組位置 | 預估函數數量 | 函數類型範例 |
|-----------|-------------|-------------|
| `domain/effects.py` | 5-8 | Progress bar, reveal effects |
| `infrastructure/video/effects.py` | 4-6 | Fadeout, fadein, concatenation |
| `domain/layout.py` | 3-5 | Letter layout helpers |
| `infrastructure/media/utils.py` | 2-3 | Media probing, placeholder creation |
| `application/video_service.py` | 1-3 | Entry/ending video logic |
| **Total (Migrated)** | **15-25** | Production-used functions |
| **Deleted (test_only)** | **10-15** | Test-specific helpers |
| **Deleted (unused)** | **5-10** | Dead code |
| **Grand Total** | **~35-50** | All functions in utils.py |

---

## Relationships & Dependencies

### Call Graph Dependencies (Example)

```
# 範例: Progress bar 函數依賴鏈
create_progress_bar (public, production)
  ├─ calls → _progress_bar_band_layout (internal)
  │   └─ calls → _progress_bar_base_arrays (internal)
  └─ calls → _build_progress_bar_segments (internal)

# 決策:
# - create_progress_bar: 遷移至 domain/effects.py (public API)
# - _progress_bar_*: 
#   - 如果僅被 create_progress_bar 呼叫 → 一起遷移 (internal helpers)
#   - 如果被測試直接呼叫 → 分析是否為 test_only
```

### Migration Dependency Rules

1. **函數鏈一起遷移**: 
   - 如果函數 A 呼叫函數 B,且 B 僅被 A 呼叫 → A, B 一起遷移至同一模組

2. **Public API 優先**:
   - 先遷移被外部引用的 public 函數
   - 再遷移其依賴的 internal 函數

3. **循環依賴檢查**:
   - 不允許函數間循環依賴 (如 A 呼叫 B, B 呼叫 A)
   - 如發現循環依賴 → 重構拆分或保留在同一模組

---

## Validation Criteria

### Data Model Completeness

- [ ] 所有 utils.py 函數都有 FunctionUsageReport 記錄
- [ ] 所有 production 函數都有 FunctionMigration 對應
- [ ] ReexportLayer 包含所有需 re-export 的函數
- [ ] 函數依賴關係圖已建立且無循環依賴
- [ ] 所有 wrapper_needed=true 的函數都有簽章說明

### Metrics Validation

- [ ] Reduction rate ≥ 95% (3,714 → 80-120 lines)
- [ ] Migrated functions: 15-25 個
- [ ] Deleted functions: 15-30 個
- [ ] Re-export count == Migrated functions count

---

**Data Model Complete**: 2025-10-19  
**Next**: Generate Contracts (usage_analysis.md, migration_mapping.md, reexport_layer.md)
