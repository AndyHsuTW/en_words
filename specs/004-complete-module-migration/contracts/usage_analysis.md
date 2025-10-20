# Contract: 函數使用分析 (usage_analysis.md)

**Feature**: 004-complete-module-migration  
**Contract Type**: Data Analysis Output  
**Version**: 1.0  
**Date**: 2025-10-19

## Purpose

定義函數使用分析的輸入、輸出格式與驗證規則,確保分析結果準確且可追溯。

## Input Specification

### Input File
- **Path**: `spellvid/utils.py`
- **Size**: 147,403 bytes (3,714 lines)
- **Format**: Python source code
- **Expected Functions**: ~50+ function definitions

### Analysis Scope
**Include**:
- All `.py` files in repository root
- Paths: `spellvid/`, `tests/`, `scripts/`

**Exclude**:
- `__pycache__/` directories
- `*.pyc`, `*.pyo` compiled files
- `*.bak`, `*.old`, `*.tmp` backup files
- `.git/`, `.venv/`, `venv/` version control & virtual env

## Output Specification

### Output Format
**File**: `specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json`  
**Schema**: Array of FunctionUsageReport objects

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["function_name", "category", "references", "call_count", "analysis_confidence"],
    "properties": {
      "function_name": {
        "type": "string",
        "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
        "description": "函數名稱 (有效 Python identifier)"
      },
      "category": {
        "type": "string",
        "enum": ["production", "test_only", "unused"],
        "description": "使用分類"
      },
      "references": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["filepath", "line_number", "context"],
          "properties": {
            "filepath": {
              "type": "string",
              "description": "相對於專案根目錄的檔案路徑"
            },
            "line_number": {
              "type": "integer",
              "minimum": 1,
              "description": "引用行號"
            },
            "context": {
              "type": "string",
              "description": "引用上下文 (前後各 1 行)"
            }
          }
        },
        "description": "所有引用位置"
      },
      "call_count": {
        "type": "integer",
        "minimum": 0,
        "description": "總引用次數"
      },
      "analysis_confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "分析信心度 (三工具一致=1.0)"
      },
      "notes": {
        "type": "string",
        "description": "人工審查註記"
      }
    }
  }
}
```

### Category Classification Rules

**production** (生產使用):
```python
def is_production_used(references: List[FileReference]) -> bool:
    for ref in references:
        # 排除 utils.py 自身引用
        if ref.filepath == "spellvid/utils.py":
            continue
        
        # 符合生產路徑
        if ref.filepath.startswith("spellvid/") and "tests" not in ref.filepath:
            return True
        
        if ref.filepath.startswith("scripts/"):
            return True
    
    return False
```

**test_only** (測試專用):
```python
def is_test_only(references: List[FileReference]) -> bool:
    if len(references) == 0:
        return False  # No references = unused
    
    for ref in references:
        # 如果有任何非測試引用 → 不是 test_only
        if not ref.filepath.startswith("tests/"):
            return False
    
    # 所有引用都在 tests/ → test_only
    return True
```

**unused** (完全未使用):
```python
def is_unused(references: List[FileReference]) -> bool:
    return len(references) == 0
```

**Validation**: Categories 必須互斥且完整 (每個函數必須屬於三者之一)

## Analysis Methodology

### Multi-Tool Cross-Validation Strategy

#### Tool 1: grep (快速掃描)
```bash
# 掃描函數名稱出現位置
grep -r "function_name" --include="*.py" --exclude-dir={__pycache__,.git,.venv} .
```

**Output**: 初步引用位置清單

#### Tool 2: AST Analysis (靜態分析)
```python
import ast

class ImportAnalyzer(ast.NodeVisitor):
    def visit_ImportFrom(self, node):
        if node.module == 'spellvid.utils':
            for alias in node.names:
                self.record_import(alias.name, node.lineno)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.record_call(node.func.id, node.lineno)
```

**Output**: 精確的 import 與函數呼叫位置

#### Tool 3: vulture (死程式碼偵測)
```bash
vulture spellvid/utils.py --min-confidence 80
```

**Output**: 候選未使用函數清單

#### Tool 4: coverage.py (執行時追蹤, Optional)
```bash
pytest --cov=spellvid.utils --cov-report=term-missing
```

**Output**: 測試執行時從未呼叫的函數

### Confidence Score Calculation

```python
def calculate_confidence(grep_found, ast_found, vulture_unused):
    # 三工具一致 = 1.0
    if grep_found == ast_found and (not vulture_unused or not grep_found):
        return 1.0
    
    # 兩工具一致 = 0.8
    if grep_found == ast_found:
        return 0.8
    
    # 工具不一致 = 0.5 (需人工審查)
    return 0.5
```

**Threshold**: 
- `confidence >= 0.8` → 自動分類
- `confidence < 0.8` → 標記為「待確認」,需人工審查

## Validation Rules

### Completeness Check
- [ ] 所有 utils.py 中的函數定義都有對應 FunctionUsageReport
- [ ] 函數總數與 utils.py 中 `def` 語句數量一致
- [ ] 無重複的 function_name

### Consistency Check
- [ ] `call_count == len(references)` (每個 report)
- [ ] `category` 分類互斥 (無函數同時屬於多個分類)
- [ ] `filepath` 在 references 中都為有效路徑 (檔案存在)

### Quality Check
- [ ] 至少 80% 的函數 `analysis_confidence >= 0.8`
- [ ] 所有 `confidence < 0.8` 的函數都有 `notes` 說明
- [ ] `category == "production"` 的函數至少有 1 個 reference

### Expected Distribution
Based on spec.md estimation:
- **production**: 15-25 functions (30-50%)
- **test_only**: 10-15 functions (20-30%)
- **unused**: 5-10 functions (10-20%)

**Validation**: 如果分布與預期嚴重偏離 (±10%),需人工審查原因

## Human Review Process

### Trigger Conditions
需人工審查的情況:
1. `analysis_confidence < 0.8`
2. `category == "production"` 但 `call_count == 0`
3. 函數名稱以 `_` 開頭但 `category == "production"` (可能為 internal helper)

### Review Checklist
For each flagged function:
- [ ] 確認分類正確 (手動檢查實際引用)
- [ ] 檢查是否為動態呼叫 (eval, getattr, `__import__`)
- [ ] 確認測試專用函數無生產代碼依賴
- [ ] 記錄審查結論於 `notes` 欄位

### Review Output
**File**: `specs/004-complete-module-migration/MANUAL_REVIEW_LOG.md`  
**Format**: Markdown table

| function_name | original_category | reviewed_category | rationale |
|---------------|------------------|------------------|-----------|
| _example_func | test_only | production | 被 scripts/helper.py 動態呼叫 |

## Contract Test Specification

**File**: `tests/contract/test_usage_analysis_contract.py`

### Test Cases

```python
def test_usage_report_schema_valid():
    """驗證 FunctionUsageReport JSON 符合 schema"""
    report = load_function_usage_report()
    validate(report, USAGE_REPORT_SCHEMA)  # jsonschema validation

def test_all_utils_functions_analyzed():
    """驗證所有 utils.py 函數都有分析結果"""
    utils_functions = extract_function_names("spellvid/utils.py")
    report_functions = [r["function_name"] for r in report]
    assert set(utils_functions) == set(report_functions)

def test_category_mutual_exclusivity():
    """驗證分類互斥 (每個函數僅屬一類)"""
    categories = [r["category"] for r in report]
    assert all(c in ["production", "test_only", "unused"] for c in categories)

def test_call_count_consistency():
    """驗證 call_count == len(references)"""
    for record in report:
        assert record["call_count"] == len(record["references"])

def test_production_category_accuracy():
    """驗證 production 分類準確性 (抽樣檢查)"""
    production_funcs = [r for r in report if r["category"] == "production"]
    sample = random.sample(production_funcs, min(5, len(production_funcs)))
    
    for func in sample:
        # 手動驗證至少一個引用在生產代碼中
        has_prod_ref = any(
            ref["filepath"].startswith("spellvid/") and "tests" not in ref["filepath"]
            for ref in func["references"]
        )
        assert has_prod_ref, f"{func['function_name']} 誤分類為 production"

def test_confidence_threshold():
    """驗證至少 80% 函數 confidence >= 0.8"""
    high_conf = [r for r in report if r["analysis_confidence"] >= 0.8]
    assert len(high_conf) / len(report) >= 0.8
```

## Success Criteria

- [x] JSON schema 定義完整
- [x] 分類規則明確且可執行
- [x] 多工具交叉驗證策略已定義
- [x] Confidence score 計算方法已定義
- [x] 人工審查流程已建立
- [x] 契約測試規格已完成

**Contract Version**: 1.0  
**Next**: Implement analysis script (Task T001-T004)
