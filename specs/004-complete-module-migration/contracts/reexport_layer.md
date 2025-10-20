# Contract: Re-export 層 (reexport_layer.md)

**Feature**: 004-complete-module-migration  
**Contract Type**: Backward Compatibility Layer Specification  
**Version**: 1.0  
**Date**: 2025-10-19

## Purpose

定義 utils.py 重寫為最小 re-export 層的規格,確保向後相容性,同時達成 ≥95% 程式碼縮減目標。

## Input Specification

### Input Data
- **Source**: `MIGRATION_MAPPING.json` (來自 migration_mapping contract)
- **Filter**: `migration_status == "migrated"` (已遷移函數)
- **Expected Count**: 15-25 個函數

### Input Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["function_name", "new_location", "wrapper_needed"],
    "properties": {
      "function_name": {"type": "string"},
      "new_location": {"type": "string"},
      "wrapper_needed": {"type": "boolean"},
      "signature_notes": {"type": "string"}
    }
  }
}
```

## Output Specification

### Target File
- **Path**: `spellvid/utils.py`
- **Target Size**: 80-120 lines
- **Reduction Rate**: ≥95% (from 3,714 lines)
- **Format**: Python module with re-exports

### File Structure Template

```python
# spellvid/utils.py - Re-export Layer (Deprecated)
# 
# This module is deprecated and will be removed in v2.0.
# Please import from the new modular structure:
#   - spellvid.domain.* (pure logic)
#   - spellvid.infrastructure.* (framework adapters)
#   - spellvid.application.* (business services)
#
# See doc/ARCHITECTURE.md for migration guide.

# ===== Section 1: DeprecationWarning (15 lines) =====
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

# ===== Section 2: Import Statements (30-50 lines) =====
# Domain layer - Pure logic, no external dependencies
from spellvid.domain.effects import (
    create_progress_bar,
    apply_reveal_effect,
    # ... other domain functions
)

from spellvid.domain.layout import (
    compute_layout_bboxes,
    # ... other layout functions
)

# Infrastructure layer - Framework integrations
from spellvid.infrastructure.video.effects import (
    apply_fadeout,
    apply_fadein,
    concatenate_with_transitions,
    # ... other video effects
)

from spellvid.infrastructure.media.utils import (
    probe_media_duration,
    # ... other media utilities
)

# Application layer - Business services
from spellvid.application.video_service import (
    render_video,
    create_entry_video,
    create_ending_video,
    # ... other application services
)

# ===== Section 3: Aliases & Wrappers (15-30 lines) =====
# Backward compatibility aliases (direct re-export)
render_video_stub = render_video
_apply_fadeout = apply_fadeout
_apply_fadein = apply_fadein

# Adapter wrappers (for signature changes)
def _legacy_function_with_dict(item: dict, **kwargs):
    """Deprecated: Use new signature with VideoConfig."""
    from spellvid.shared.types import VideoConfig
    config = VideoConfig(**item)
    return new_function(config, **kwargs)

# ===== Section 4: __all__ Export List (20-25 lines) =====
__all__ = [
    # Domain exports
    'create_progress_bar',
    'apply_reveal_effect',
    'compute_layout_bboxes',
    
    # Infrastructure exports
    'apply_fadeout',
    'apply_fadein',
    'concatenate_with_transitions',
    'probe_media_duration',
    
    # Application exports
    'render_video',
    'create_entry_video',
    'create_ending_video',
    
    # Deprecated aliases (for backward compatibility)
    'render_video_stub',
    '_apply_fadeout',
    '_apply_fadein',
    # ... all re-exported functions
]
```

### Section Breakdown & Line Count

| Section | Purpose | Target Lines | Required |
|---------|---------|-------------|----------|
| 1. Module Docstring | 說明 deprecated 狀態 | 5-10 | ✅ Yes |
| 2. DeprecationWarning | 執行時警告觸發 | 10-15 | ✅ Yes |
| 3. Import Statements | 從新模組 import | 30-50 | ✅ Yes |
| 4. Aliases | 向後相容別名 | 5-15 | ⚠️ If needed |
| 5. Wrappers | Adapter 函數 | 0-20 | ⚠️ If needed |
| 6. __all__ List | Export 清單 | 20-25 | ✅ Yes |
| **Total** | | **80-120** | |

## Content Generation Rules

### Rule 1: Import Statement Organization

**Grouping by Layer** (按層級分組):
```python
# Domain imports first (pure logic)
from spellvid.domain.effects import ...
from spellvid.domain.layout import ...

# Infrastructure imports second (framework adapters)
from spellvid.infrastructure.video.effects import ...
from spellvid.infrastructure.media.utils import ...

# Application imports third (business services)
from spellvid.application.video_service import ...
```

**Alphabetical within group** (組內按字母排序):
```python
from spellvid.domain.effects import (
    apply_reveal_effect,      # A
    create_progress_bar,       # C
)
```

### Rule 2: Alias Naming Convention

**Direct re-export** (簽章無變更):
```python
# Pattern: old_name = new_name
render_video_stub = render_video
_internal_helper = internal_helper
```

**Preserve underscore prefix** (保留私有標記):
```python
# Public function → keep as-is
create_progress_bar = create_progress_bar

# Private helper → preserve underscore
_progress_bar_layout = _progress_bar_layout
```

### Rule 3: Wrapper Generation (僅當 wrapper_needed=true)

**Template**:
```python
def {old_function_name}({old_signature}):
    """
    Deprecated wrapper for {new_function_name}.
    
    This function is deprecated and will be removed in v2.0.
    Use {new_module_path}.{new_function_name} instead.
    
    Signature changed: {signature_notes}
    """
    import warnings
    warnings.warn(
        f"{old_function_name} is deprecated, use {new_module_path}.{new_function_name}",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Adapter logic here
    {conversion_code}
    return {new_function_name}({adapted_params})
```

**Example** (Dict → VideoConfig):
```python
def render_video_stub(item: dict, output_path: str) -> None:
    """Deprecated: Use application.video_service.render_video with VideoConfig."""
    import warnings
    warnings.warn(
        "render_video_stub is deprecated, use application.video_service.render_video",
        DeprecationWarning,
        stacklevel=2
    )
    from spellvid.shared.types import VideoConfig
    config = VideoConfig(**item)
    return render_video(config, output_path)
```

### Rule 4: __all__ List Completeness

**Include**:
- All functions in MIGRATION_MAPPING (migrated functions)
- All aliases (old names for backward compatibility)
- All wrappers

**Exclude**:
- Module-level imports not meant for public use (如 `_warnings`)
- Internal helpers only used within utils.py

**Validation**:
```python
# All names in __all__ must be defined in the module
for name in __all__:
    assert name in globals(), f"{name} in __all__ but not defined"
```

## Validation Rules

### Structure Validation
- [ ] File contains exactly 4 required sections (Docstring, Warning, Imports, __all__)
- [ ] DeprecationWarning appears before any imports
- [ ] Imports grouped by layer (domain → infrastructure → application)
- [ ] __all__ list appears at the end of file

### Size Validation
- [ ] Total line count: 80-120 lines
- [ ] Reduction rate: `(3714 - actual_lines) / 3714 >= 0.95` (≥95%)
- [ ] No function implementation bodies (除了 wrapper 函數)

### Content Validation
- [ ] 所有 MIGRATION_MAPPING 中的函數都有對應 import 或 alias
- [ ] 所有 `wrapper_needed=true` 函數都有 wrapper 實作
- [ ] 所有 import 路徑有效 (模組存在且可匯入)
- [ ] 無殘留的舊實作程式碼 (def body with logic)

### Backward Compatibility Validation
- [ ] 所有現有 `from spellvid.utils import X` 仍可正常執行
- [ ] DeprecationWarning 會在 import 時觸發
- [ ] 函數簽章與舊版一致 (或有 wrapper 轉換)

## Expected Metrics

Based on spec.md targets:

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Line Count** | 80-120 | `wc -l spellvid/utils.py` |
| **Reduction Rate** | ≥95% | `(3714 - new_lines) / 3714` |
| **Re-export Count** | 15-25 | `len(__all__)` |
| **Wrapper Count** | 0-5 | Count `def` statements (excluding module-level) |
| **Import Count** | 15-25 | Count imported function names |

**Validation**: 所有 metrics 必須在預期範圍內,否則需審查原因

## Deprecation Warning Behavior

### Trigger Timing
```python
# Warning triggers on module import
import spellvid.utils  # ← DeprecationWarning appears here
from spellvid.utils import render_video  # ← Also triggers warning
```

### Warning Content
```
DeprecationWarning: The 'spellvid.utils' module is deprecated and will be removed in v2.0. 
Please import from the new modular structure:
  - spellvid.domain.* (pure logic)
  - spellvid.infrastructure.* (framework adapters)
  - spellvid.application.* (business services)
See doc/ARCHITECTURE.md for migration guide.
```

### Suppression (for legacy code)
```python
# Temporarily suppress for backward compatibility
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from spellvid.utils import render_video_stub
```

## Contract Test Specification

**File**: `tests/contract/test_reexport_layer_contract.py`

### Test Cases

```python
def test_utils_line_count_in_range():
    """驗證 utils.py 行數在 80-120 範圍"""
    with open("spellvid/utils.py") as f:
        line_count = len(f.readlines())
    assert 80 <= line_count <= 120, f"Line count {line_count} 不在 80-120 範圍"

def test_reduction_rate_above_95_percent():
    """驗證程式碼縮減率 ≥95%"""
    original_lines = 3714
    with open("spellvid/utils.py") as f:
        new_lines = len(f.readlines())
    reduction_rate = (original_lines - new_lines) / original_lines
    assert reduction_rate >= 0.95, f"Reduction rate {reduction_rate:.1%} < 95%"

def test_all_migrated_functions_exported():
    """驗證所有已遷移函數都在 __all__ 中"""
    migration_mapping = load_migration_mapping()
    migrated_funcs = [m["function_name"] for m in migration_mapping]
    
    import spellvid.utils
    assert hasattr(spellvid.utils, "__all__"), "Missing __all__ list"
    
    for func in migrated_funcs:
        assert func in spellvid.utils.__all__, f"{func} 未在 __all__ 中"

def test_deprecation_warning_triggers():
    """驗證 DeprecationWarning 在 import 時觸發"""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Re-import to trigger warning
        import importlib
        import spellvid.utils
        importlib.reload(spellvid.utils)
        
        assert len(w) > 0, "DeprecationWarning 未觸發"
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()

def test_all_exports_importable():
    """驗證 __all__ 中所有名稱都可 import"""
    import spellvid.utils
    
    for name in spellvid.utils.__all__:
        assert hasattr(spellvid.utils, name), f"{name} in __all__ but not importable"
        obj = getattr(spellvid.utils, name)
        assert callable(obj), f"{name} is not callable"

def test_no_implementation_code():
    """驗證無實作程式碼 (除了 wrapper)"""
    with open("spellvid/utils.py") as f:
        content = f.read()
    
    # 允許的 def: wrapper 函數 (有 DeprecationWarning)
    # 不允許: 複雜邏輯實作 (如 for 迴圈、多層 if-else)
    
    # Simple heuristic: 檢查是否有大量邏輯程式碼
    lines = content.split("\n")
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    
    # Wrapper 函數應該很短 (< 10 行 per function)
    # Re-export 層總程式碼行數應該 < 150 (含註解)
    assert len(code_lines) < 150, "Too much code, possible implementation not removed"

def test_backward_compatibility_imports():
    """驗證現有 import 路徑仍有效 (抽樣測試)"""
    # Sample: 測試常見的 import patterns
    try:
        from spellvid.utils import render_video
        from spellvid.utils import apply_fadeout
        from spellvid.utils import create_progress_bar
    except ImportError as e:
        pytest.fail(f"Backward compatibility broken: {e}")
```

## Safety Checklist

Before deploying re-export layer:
- [ ] 備份原始 utils.py (git commit + tag)
- [ ] 所有遷移函數已在新模組中實作
- [ ] 契約測試 `test_migration_mapping_contract.py` 通過
- [ ] 手動測試至少 3 個常用函數可正常 import

During deployment:
- [ ] 逐步替換 utils.py 內容 (section by section)
- [ ] 每個 section 完成後執行 import test
- [ ] 發現問題立即 rollback

After deployment:
- [ ] 執行完整測試套件 (`.\scripts\run_tests.ps1`)
- [ ] 執行 render_example.ps1 驗證功能
- [ ] 檢查 DeprecationWarning 是否正確觸發
- [ ] 更新 IMPLEMENTATION_SUMMARY.md

## Success Criteria

- [x] File structure template 已定義
- [x] Content generation rules 明確
- [x] Section line count targets 已設定
- [x] Validation rules 完整
- [x] Deprecation warning behavior 已規範
- [x] Contract tests 已定義

**Contract Version**: 1.0  
**Next**: Implement re-export layer (Task T034-T037)
