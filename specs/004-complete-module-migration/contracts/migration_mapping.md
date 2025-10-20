# Contract: 函數遷移對應 (migration_mapping.md)

**Feature**: 004-complete-module-migration  
**Contract Type**: Migration Mapping & Execution Rules  
**Version**: 1.0  
**Date**: 2025-10-19

## Purpose

定義函數遷移的對應規則、新模組位置、簽章相容性處理策略,確保遷移過程可追溯且安全。

## Input Specification

### Input Data
- **Source**: `FUNCTION_USAGE_REPORT.json` (來自 usage_analysis contract)
- **Filter**: `category == "production"` (僅遷移生產使用函數)
- **Expected Count**: 15-25 個函數

### Input Schema
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["function_name", "category"],
    "properties": {
      "function_name": {"type": "string"},
      "category": {"type": "string", "enum": ["production"]},
      "references": {"type": "array"}
    }
  }
}
```

## Output Specification

### Output Format
**File**: `specs/004-complete-module-migration/MIGRATION_MAPPING.json`  
**Schema**: Array of FunctionMigration objects

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["function_name", "old_location", "new_location", "migration_status", "reason"],
    "properties": {
      "function_name": {
        "type": "string",
        "description": "函數名稱"
      },
      "old_location": {
        "type": "string",
        "const": "spellvid/utils.py",
        "description": "固定為 utils.py"
      },
      "new_location": {
        "type": "string",
        "pattern": "^spellvid/(domain|infrastructure|application)/.*\\.py$",
        "description": "新模組路徑 (必須符合分層架構)"
      },
      "migration_status": {
        "type": "string",
        "enum": ["migrated"],
        "description": "此契約僅處理 production 函數,status 固定為 migrated"
      },
      "reason": {
        "type": "string",
        "minLength": 10,
        "description": "遷移理由 (至少 10 字元)"
      },
      "wrapper_needed": {
        "type": "boolean",
        "description": "是否需要 adapter wrapper"
      },
      "signature_notes": {
        "type": "string",
        "description": "簽章差異說明 (wrapper_needed=true 時必填)"
      },
      "dependencies": {
        "type": "array",
        "items": {"type": "string"},
        "description": "依賴的其他函數名稱"
      }
    }
  }
}
```

## Migration Mapping Rules

### Rule 1: Category-Based Mapping (按功能分類)

| 函數類別識別 | 新模組位置 | Layer | Rationale |
|------------|----------|-------|-----------|
| 包含 `progress_bar`, `reveal`, `effect` | `spellvid/domain/effects.py` | Domain | 純視覺效果邏輯,無外部依賴 |
| 包含 `fade`, `transition`, `concat`, `video` | `spellvid/infrastructure/video/effects.py` | Infrastructure | MoviePy 整合,框架依賴 |
| 包含 `letter`, `layout`, `bbox`, `position` | `spellvid/domain/layout.py` | Domain | 佈局計算邏輯 |
| 包含 `media`, `probe`, `duration`, `ffmpeg` | `spellvid/infrastructure/media/utils.py` | Infrastructure | FFmpeg/媒體整合 |
| 包含 `entry`, `ending`, `render` | `spellvid/application/video_service.py` | Application | 業務流程編排 |

### Rule 2: Dependency-Based Grouping (依賴分組)

**原則**: 函數與其依賴的 internal helpers 應遷移至同一模組

```python
def should_migrate_together(func_a, func_b, call_graph):
    # 如果 A 呼叫 B,且 B 僅被 A 呼叫 → 一起遷移
    if func_b in call_graph.get(func_a, []):
        callers_of_b = [f for f, callees in call_graph.items() if func_b in callees]
        if len(callers_of_b) == 1 and callers_of_b[0] == func_a:
            return True
    return False
```

**Example**:
```json
{
  "function_name": "create_progress_bar",
  "new_location": "spellvid/domain/effects.py",
  "dependencies": ["_progress_bar_band_layout", "_progress_bar_base_arrays"]
}
```
→ `_progress_bar_*` helpers 也應遷移至 `domain/effects.py`

### Rule 3: Signature Compatibility Check (簽章相容性)

**需要 Wrapper 的情況**:
1. 參數型別改變 (如 `Dict` → `VideoConfig` dataclass)
2. 參數順序改變
3. 新增必填參數 (舊呼叫者未提供)
4. 返回值型別改變

**Wrapper Template**:
```python
# spellvid/utils.py (re-export layer)
from spellvid.application.video_service import render_video as _render_video_new
from spellvid.shared.types import VideoConfig

def render_video_stub(item: dict, output_path: str) -> None:
    """Deprecated wrapper for backward compatibility."""
    import warnings
    warnings.warn(
        "render_video_stub is deprecated, use application.video_service.render_video",
        DeprecationWarning,
        stacklevel=2
    )
    config = VideoConfig(**item)  # Dict → VideoConfig adapter
    return _render_video_new(config, output_path)
```

## Validation Rules

### Completeness Validation
- [ ] 所有 `category == "production"` 函數都有對應 FunctionMigration
- [ ] 所有 `new_location` 路徑符合分層架構 (domain/infrastructure/application)
- [ ] 無重複的 `function_name`

### Path Validation
- [ ] `new_location` 檔案存在於專案中
- [ ] `new_location` 可正常 import (無語法錯誤)
- [ ] 新模組路徑符合 naming convention (snake_case, .py 結尾)

### Dependency Validation
- [ ] `dependencies` 中的函數都在 FUNCTION_USAGE_REPORT 中
- [ ] 無循環依賴 (A → B → A)
- [ ] 依賴函數遷移至相同或相容模組

### Signature Validation
- [ ] `wrapper_needed == true` → `signature_notes` 必須非空
- [ ] `wrapper_needed == false` → 原始簽章與新模組簽章一致

## Expected Migration Distribution

Based on spec.md estimation and code analysis:

| 新模組位置 | 預估函數數 | 函數範例 |
|-----------|----------|---------|
| `domain/effects.py` | 5-8 | create_progress_bar, apply_reveal_effect, _progress_bar_* |
| `infrastructure/video/effects.py` | 4-6 | apply_fadeout, apply_fadein, concatenate_with_transitions |
| `domain/layout.py` | 3-5 | _normalize_letters, _plan_letter_images, _letter_asset_filename |
| `infrastructure/media/utils.py` | 2-3 | _probe_media_duration, _create_placeholder_mp4 |
| `application/video_service.py` | 1-3 | _resolve_entry_video, _is_ending_enabled |
| **Total** | **15-25** | Production-used functions |

**Validation**: 如果實際分布與預期差異 >30%,需人工審查原因

## Migration Execution Strategy

### Phase 1: Preparation (準備階段)
1. 為每個目標模組建立 migration branch
2. 確認目標模組檔案存在且可編輯
3. 建立函數依賴圖 (call graph)

### Phase 2: Function by Function Migration (逐函數遷移)
For each function in MIGRATION_MAPPING:
1. **Extract**: 從 utils.py 複製函數實作至新模組
2. **Adapt**: 調整 import 路徑 (如 internal helpers 位置變更)
3. **Test**: 執行相關測試驗證功能正常
4. **Mark**: 在 utils.py 中標記函數為「已遷移」(保留空殼或簡單 wrapper)

### Phase 3: Dependency Resolution (依賴解析)
1. 遷移所有依賴函數 (dependencies 列表)
2. 更新新模組中的 import 語句
3. 確保無殘留 `from spellvid.utils import` 在新模組中

### Phase 4: Validation (驗證)
1. 所有新模組函數可獨立 import
2. 執行契約測試 `test_migration_mapping_contract.py`
3. 執行完整測試套件,確認無破壞

## Migration Safety Checklist

Before migrating each function:
- [ ] 確認函數在 MIGRATION_MAPPING 中
- [ ] 確認所有 dependencies 已遷移或將同步遷移
- [ ] 備份 utils.py 當前版本
- [ ] 準備 rollback 方案 (git commit before migration)

During migration:
- [ ] 保留原始函數簽章 (除非有 wrapper)
- [ ] 複製所有 docstring 與註解
- [ ] 保留型別提示 (type hints)
- [ ] 測試通過才標記為「已遷移」

After migration:
- [ ] 更新 MIGRATION_MAPPING.json status
- [ ] 記錄遷移時間與 commit hash
- [ ] 更新 data-model.md 函數對應表

## Contract Test Specification

**File**: `tests/contract/test_migration_mapping_contract.py`

### Test Cases

```python
def test_migration_mapping_completeness():
    """驗證所有 production 函數都有遷移對應"""
    usage_report = load_function_usage_report()
    production_funcs = [r["function_name"] for r in usage_report if r["category"] == "production"]
    
    migration_mapping = load_migration_mapping()
    migrated_funcs = [m["function_name"] for m in migration_mapping]
    
    assert set(production_funcs) == set(migrated_funcs), "遺漏部分 production 函數"

def test_new_location_path_valid():
    """驗證所有新模組路徑存在且符合分層架構"""
    migration_mapping = load_migration_mapping()
    
    for record in migration_mapping:
        new_path = record["new_location"]
        # 檢查檔案存在
        assert os.path.exists(new_path), f"{new_path} 不存在"
        # 檢查符合分層架構
        assert new_path.startswith("spellvid/"), f"{new_path} 不在 spellvid/ 下"
        assert any(layer in new_path for layer in ["domain", "infrastructure", "application"]), \
            f"{new_path} 不符合分層架構"

def test_no_circular_dependencies():
    """驗證無循環依賴"""
    migration_mapping = load_migration_mapping()
    call_graph = {m["function_name"]: m.get("dependencies", []) for m in migration_mapping}
    
    def has_cycle(graph, node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(graph, neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False
    
    for func in call_graph.keys():
        assert not has_cycle(call_graph, func, set(), set()), f"發現循環依賴包含 {func}"

def test_wrapper_signature_notes():
    """驗證需要 wrapper 的函數都有簽章說明"""
    migration_mapping = load_migration_mapping()
    
    for record in migration_mapping:
        if record["wrapper_needed"]:
            assert record.get("signature_notes"), \
                f"{record['function_name']} 需要 wrapper 但缺少 signature_notes"

def test_migrated_functions_importable():
    """驗證已遷移函數可從新模組 import (抽樣測試)"""
    migration_mapping = load_migration_mapping()
    sample = random.sample(migration_mapping, min(5, len(migration_mapping)))
    
    for record in sample:
        module_path = record["new_location"].replace("/", ".").replace(".py", "")
        func_name = record["function_name"]
        
        try:
            module = importlib.import_module(module_path)
            assert hasattr(module, func_name), f"{func_name} 不存在於 {module_path}"
        except ImportError as e:
            pytest.fail(f"無法 import {module_path}: {e}")
```

## Human Review Triggers

需人工審查的情況:
1. 函數依賴超過 5 個其他函數 (複雜依賴)
2. 函數簽章需要 wrapper 且轉換邏輯複雜
3. 函數在 usage report 中 `analysis_confidence < 0.8`
4. 遷移後測試失敗且無法快速修復

## Success Criteria

- [x] JSON schema 定義完整
- [x] 分層架構對應規則明確
- [x] 依賴分組策略已定義
- [x] Wrapper 實作模板已提供
- [x] 遷移執行流程已規劃
- [x] 契約測試規格已完成

**Contract Version**: 1.0  
**Next**: Implement migration script (Task T010-T033)
