# Research: 函數使用分析與遷移策略

**Feature**: 004-complete-module-migration  
**Phase**: 0 (Outline & Research)  
**Date**: 2025-10-19

## Research Questions & Findings

### 1. 函數使用分析工具選擇

**Question**: 如何可靠識別生產使用 vs 測試專用 vs 完全未使用的函數?

**Evaluated Tools**:

| 工具 | 優點 | 缺點 | 適用場景 |
|------|------|------|---------|
| **grep** | 簡單快速,無依賴,精確字串匹配 | 無法識別動態引用,可能漏報 | 初步掃描,建立候選清單 |
| **AST Analysis (ast module)** | 靜態分析準確,可追蹤 import 來源 | 無法追蹤 eval/getattr 動態呼叫 | 精確識別靜態引用 |
| **vulture** | 專門識別死程式碼,輸出友善 | 誤報率較高,需人工審查 | 輔助識別候選冗餘函數 |
| **coverage.py** | 執行時追蹤實際使用,無誤報 | 需完整測試覆蓋,耗時較長 | 最終驗證,確認真正使用 |

**Decision**: **多工具交叉驗證策略**

1. **Step 1 (grep)**: 快速掃描所有 `.py` 檔案,識別函數名稱出現位置
   - 排除: `__pycache__/`, `*.bak`, `*.pyc`
   - 分類: `spellvid/` (非 tests) → 生產, `tests/` → 測試, `scripts/` → 生產

2. **Step 2 (AST)**: 靜態分析 import 語句與函數呼叫
   - 解析所有 Python 檔案的 AST
   - 追蹤 `from spellvid.utils import X` 語句
   - 建立呼叫圖 (caller → callee 關係)

3. **Step 3 (vulture)**: 識別候選死程式碼
   - 執行 `vulture spellvid/utils.py --min-confidence 80`
   - 輸出未使用函數清單供參考

4. **Step 4 (coverage.py)**: 執行時驗證
   - 執行完整測試套件 `pytest --cov=spellvid.utils --cov-report=term-missing`
   - 識別測試中從未執行的函數

5. **Step 5 (Cross-validation)**: 三工具結果交集
   - grep 未找到 AND AST 無引用 AND vulture 報告 → **完全未使用**
   - grep 僅在 tests/ AND AST 僅 tests/ 引用 → **測試專用**
   - 其他 → **生產使用** (需遷移)

**Rationale**: 單一工具可能漏報或誤報,交叉驗證可降低誤刪風險至 <1%。

**Implementation Guide**:
```python
# 範例 AST 分析腳本
import ast
import os

class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
    
    def visit_ImportFrom(self, node):
        if node.module == 'spellvid.utils':
            for alias in node.names:
                self.imports.append(alias.name)
        self.generic_visit(node)

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)
    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports
```

---

### 2. 函數簽章相容性處理

**Question**: 新模組函數簽章已改變 (如 Dict → VideoConfig),如何建立相容 wrapper?

**Pattern Evaluated**: **Adapter Pattern**

**Scenario**: 舊 utils.py 函數接受 `Dict`,新模組函數接受 `VideoConfig` dataclass

**Solution**: 在 re-export 層建立 adapter wrapper

**Implementation Example**:
```python
# spellvid/utils.py (re-export 層)
from spellvid.application.video_service import render_video as _render_video_new
from spellvid.shared.types import VideoConfig

def render_video_stub(item: dict, output_path: str) -> None:
    """
    Backward-compatible wrapper for render_video.
    
    DEPRECATED: Use spellvid.application.video_service.render_video instead.
    This wrapper will be removed in v2.0.
    """
    import warnings
    warnings.warn(
        "render_video_stub is deprecated, use application.video_service.render_video",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Adapter: Convert dict to VideoConfig
    config = VideoConfig(**item)
    return _render_video_new(config, output_path)
```

**Best Practices**:
1. **明確命名**: wrapper 函數加 `_stub` 或 `_legacy` 後綴
2. **DeprecationWarning**: 每次呼叫都觸發警告
3. **型別提示**: 保留舊簽章的型別提示,方便 IDE 辨識
4. **文件說明**: Docstring 明確指出 deprecated 與替代方案
5. **測試覆蓋**: wrapper 需要獨立測試驗證轉換邏輯

**Rationale**: Adapter pattern 允許漸進式遷移,現有程式碼無需立即修改,降低重構風險。

---

### 3. 測試性能優化方法 (Optional, SC-9)

**Question**: 完整測試套件 >30 分鐘,如何優化至 <5 分鐘?

**Current Bottlenecks**:
- 40 個測試檔案,多數包含視頻渲染整合測試
- MoviePy 視頻合成耗時 (每個測試 10-30 秒)
- 無並行執行,sequential 執行所有測試

**Optimization Strategies**:

| 策略 | 預期改善 | 實作複雜度 | 建議優先度 |
|------|---------|----------|----------|
| **pytest-xdist 並行執行** | 3-5x 加速 (CPU cores) | 低 (安裝套件即可) | ⭐⭐⭐ 高 |
| **Selective testing (--lf, --ff)** | 僅執行失敗/修改測試 | 低 (pytest 內建) | ⭐⭐⭐ 高 |
| **Fixture scope 優化** | 減少重複設定 | 中 (需重構 fixture) | ⭐⭐ 中 |
| **Mock MoviePy 視頻操作** | 大幅減少 I/O | 高 (需重寫測試) | ⭐ 低 (風險高) |
| **分層測試策略** | 分離快速/慢速測試 | 中 (需標記測試) | ⭐⭐ 中 |

**Decision**: **優先採用 pytest-xdist 並行執行**

**Implementation**:
```bash
# 安裝 pytest-xdist
pip install pytest-xdist

# 並行執行測試 (使用所有 CPU cores)
pytest -n auto

# 僅執行失敗的測試 (快速迭代)
pytest --lf

# 組合使用
pytest -n auto --lf
```

**Expected Impact**:
- 並行執行: 30 min → 8-10 min (假設 4 cores)
- Selective testing: 開發迭代時僅執行相關測試,秒級回饋

**Rationale**: pytest-xdist 實作簡單,風險低,改善明顯。Mock 策略雖能進一步加速,但可能隱藏真實整合問題,不建議用於重構驗證階段。

**Future Improvements** (post-migration):
- 標記慢速測試 `@pytest.mark.slow`,允許跳過
- 分離單元測試 (快速) 與整合測試 (慢速) 執行策略
- 使用 pytest-benchmark 分析瓶頸測試

---

### 4. 函數鏈依賴識別

**Question**: 如何識別「僅被其他輔助函數呼叫」的未使用函數鏈?

**Problem**: 函數 A 未被生產代碼使用,但被函數 B 呼叫,函數 B 也未被使用 → 應批量刪除 A + B

**Evaluated Tools**:

| 工具 | 功能 | 優缺點 |
|------|------|--------|
| **pyan** | 生成呼叫圖 (GraphViz) | ✅ 視覺化清晰 ❌ 需安裝 GraphViz |
| **pycallgraph2** | 執行時呼叫追蹤 | ✅ 準確 ❌ 需執行程式,耗時 |
| **Manual AST** | 自訂 AST 分析建立呼叫圖 | ✅ 靈活控制 ❌ 實作較複雜 |

**Decision**: **Manual AST 分析建立簡化呼叫圖**

**Algorithm**:
1. 解析 utils.py,提取所有函數定義與函數內呼叫
2. 建立 `callees` 字典: `{caller: [callee1, callee2, ...]}`
3. 從生產使用函數開始,遞迴標記所有被呼叫的函數
4. 未被標記的函數 = 未使用函數鏈

**Implementation Pseudocode**:
```python
def build_call_graph(utils_py_ast):
    graph = {}
    for func_def in ast.walk(utils_py_ast):
        if isinstance(func_def, ast.FunctionDef):
            callees = extract_function_calls(func_def)
            graph[func_def.name] = callees
    return graph

def mark_reachable(graph, production_used_funcs):
    reachable = set(production_used_funcs)
    queue = list(production_used_funcs)
    
    while queue:
        func = queue.pop(0)
        for callee in graph.get(func, []):
            if callee not in reachable:
                reachable.add(callee)
                queue.append(callee)
    
    return reachable

# 未被標記 = 未使用函數鏈
all_funcs = set(graph.keys())
unused_chain = all_funcs - reachable
```

**Rationale**: 自訂 AST 分析可精確控制,無需額外依賴,執行快速。

**Safety Check**: 批量刪除前,輸出函數鏈清單供人工審查,確認無誤刪。

---

## Research Summary

### Decisions Made

| Research Area | Decision | Rationale |
|---------------|----------|-----------|
| **函數使用分析** | 多工具交叉驗證 (grep + AST + vulture + coverage) | 降低誤刪風險至 <1% |
| **簽章相容性** | Adapter pattern wrapper in re-export 層 | 漸進式遷移,降低風險 |
| **測試性能** | pytest-xdist 並行 + selective testing | 簡單實作,明顯改善 |
| **函數鏈識別** | Manual AST 呼叫圖分析 | 精確控制,無額外依賴 |

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|-------------|--------------|
| 僅使用 grep 分析 | 可能漏報動態引用,風險高 |
| Mock MoviePy 加速測試 | 可能隱藏真實整合問題,不適合重構驗證 |
| pyan/pycallgraph2 | 需額外依賴或執行時追蹤,成本高 |
| 直接刪除所有測試專用函數 | 需先確認測試可用新模組替代,分階段執行較安全 |

### Implementation Priorities

1. **High Priority** (Step 0-1):
   - 實作多工具交叉驗證分析腳本
   - 建立函數使用報告與人工審查清單

2. **Medium Priority** (Step 2-3):
   - 實作 Adapter wrapper 模式
   - 建立函數鏈呼叫圖分析

3. **Low Priority** (Step 4, Optional):
   - 測試性能優化 (pytest-xdist)
   - 可在遷移完成後執行

---

**Research Complete**: 2025-10-19  
**Next Phase**: Phase 1 (Design & Contracts)
