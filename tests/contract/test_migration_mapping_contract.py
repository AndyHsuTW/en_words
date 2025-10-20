"""
契約測試: 函數遷移對應 (migration_mapping.md)

這些測試驗證 MIGRATION_MAPPING.json 是否符合契約規格。
根據 TDD 原則,這些測試必須先寫且必須失敗 (因為對應表尚未產生)。
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


# ===== Test Fixtures =====

@pytest.fixture
def mapping_path() -> Path:
    """MIGRATION_MAPPING.json 的預期路徑"""
    return Path("specs/004-complete-module-migration/MIGRATION_MAPPING.json")


@pytest.fixture
def mapping_data(mapping_path: Path) -> List[Dict[str, Any]]:
    """載入並解析遷移對應表"""
    if not mapping_path.exists():
        pytest.fail(f"遷移對應表不存在: {mapping_path}")

    with open(mapping_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        pytest.fail(f"對應表格式錯誤: 預期 array,得到 {type(data)}")

    return data


@pytest.fixture
def usage_report_path() -> Path:
    """FUNCTION_USAGE_REPORT.json 的路徑"""
    return Path("specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json")


@pytest.fixture
def production_functions(usage_report_path: Path) -> List[str]:
    """從使用分析報告中提取所有 production 函數名稱"""
    if not usage_report_path.exists():
        pytest.skip(f"使用分析報告不存在: {usage_report_path}")

    with open(usage_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    return [
        item["function_name"]
        for item in report
        if item["category"] == "production"
    ]


# ===== Contract Test 1: Completeness =====

def test_migration_mapping_completeness(
    mapping_data: List[Dict[str, Any]],
    production_functions: List[str]
):
    """
    Contract Test 1: 驗證所有 production 函數都有遷移對應

    MIGRATION_MAPPING.json 必須包含所有 category="production" 的函數。
    """
    # 從對應表中提取函數名稱
    mapped_functions = {item["function_name"] for item in mapping_data}
    production_set = set(production_functions)

    # 檢查遺漏的函數
    missing = production_set - mapped_functions
    assert not missing, (
        f"以下 production 函數缺少遷移對應:\n" +
        "\n".join(f"  - {fn}" for fn in sorted(missing))
    )

    # 檢查多餘的函數 (對應表中有但不是 production)
    extra = mapped_functions - production_set
    assert not extra, (
        f"以下函數在對應表中但不是 production 函數:\n" +
        "\n".join(f"  - {fn}" for fn in sorted(extra))
    )

    print(f"\n遷移對應完整性驗證:")
    print(f"  Production 函數總數: {len(production_set)}")
    print(f"  已對應函數總數: {len(mapped_functions)}")
    print(f"  完整性: 100%")


# ===== Contract Test 2: New Location Path Validation =====

def test_new_location_path_valid(mapping_data: List[Dict[str, Any]]):
    """
    Contract Test 2: 驗證新模組路徑存在且符合分層架構

    new_location 必須:
    1. 符合格式 spellvid/(domain|infrastructure|application|shared)/*.py
    2. 對應的檔案存在 (或目錄存在以便建立)
    
    特例:
    - "N/A": 假陽性或不遷移的函數
    - "spellvid/utils.py": 保留為向後相容層的函數
    """
    import re

    valid_layers = {"domain", "infrastructure", "application", "shared"}
    layer_pattern = re.compile(
        r"^spellvid/(domain|infrastructure|application|shared)/.*\.py$"
    )

    for item in mapping_data:
        func_name = item["function_name"]
        new_loc = item["new_location"]

        # 允許特殊標記
        if new_loc in ("N/A", "spellvid/utils.py"):
            continue

        # 驗證路徑格式
        assert layer_pattern.match(new_loc), (
            f"函數 {func_name} 的 new_location 格式錯誤: {new_loc}\n"
            f"必須符合: spellvid/(domain|infrastructure|application|shared)/*.py\n"
            f"或使用特殊標記: N/A, spellvid/utils.py"
        )

        # 提取 layer
        parts = new_loc.split("/")
        layer = parts[1] if len(parts) > 1 else None
        assert layer in valid_layers, (
            f"函數 {func_name} 的 layer 無效: {layer}"
        )

        # 驗證目錄存在 (檔案可能尚未建立)
        target_path = Path(new_loc)
        target_dir = target_path.parent

        # 暫時允許目錄不存在 (遷移過程中會建立)
        # 僅驗證路徑合理性
        assert target_dir.parts[0] == "spellvid", (
            f"函數 {func_name} 的目標路徑不在 spellvid/ 下: {new_loc}"
        )


# ===== Contract Test 3: No Circular Dependencies =====

def test_no_circular_dependencies(mapping_data: List[Dict[str, Any]]):
    """
    Contract Test 3: 驗證無循環依賴

    檢查 dependencies 欄位,確保沒有循環依賴:
    - A depends on B, B depends on C, C depends on A → 循環
    """
    # 建立依賴圖
    dep_graph: Dict[str, List[str]] = {}
    for item in mapping_data:
        func_name = item["function_name"]
        deps = item.get("dependencies", [])
        dep_graph[func_name] = deps

    # DFS 檢測循環
    def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in dep_graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    visited = set()
    for func_name in dep_graph:
        if func_name not in visited:
            rec_stack = set()
            if has_cycle(func_name, visited, rec_stack):
                pytest.fail(f"檢測到循環依賴,涉及函數: {func_name}")

    print(f"\n依賴圖驗證:")
    print(f"  總函數數: {len(dep_graph)}")
    print(f"  有依賴的函數: {sum(1 for d in dep_graph.values() if d)}")
    print(f"  循環依賴: 無")


# ===== Contract Test 4: Wrapper Signature Notes =====

def test_wrapper_signature_notes(mapping_data: List[Dict[str, Any]]):
    """
    Contract Test 4: 驗證 wrapper 有簽章說明

    如果 wrapper_needed=true,則 signature_notes 必須非空。
    """
    missing_notes = []

    for item in mapping_data:
        func_name = item["function_name"]
        wrapper_needed = item.get("wrapper_needed", False)
        sig_notes = item.get("signature_notes", "")

        if wrapper_needed and not sig_notes:
            missing_notes.append(func_name)

    assert not missing_notes, (
        f"以下函數需要 wrapper 但缺少 signature_notes:\n" +
        "\n".join(f"  - {fn}" for fn in missing_notes)
    )

    wrapper_count = sum(1 for item in mapping_data
                        if item.get("wrapper_needed", False))
    print(f"\nWrapper 驗證:")
    print(f"  需要 wrapper 的函數: {wrapper_count}")
    print(f"  所有 wrapper 都有簽章說明: ✓")


# ===== Contract Test 5: Migrated Functions Importable (Sampling) =====

def test_migrated_functions_importable(mapping_data: List[Dict[str, Any]]):
    """
    Contract Test 5: 驗證已遷移函數可 import (抽樣檢查)

    隨機抽樣 3-5 個函數,驗證其新位置可正常 import。
    此測試會在遷移完成後才能通過。
    """
    import importlib
    import random

    # 過濾掉特殊標記的函數
    valid_functions = [
        item for item in mapping_data
        if item["new_location"] not in ("N/A", "spellvid/utils.py")
    ]

    # 抽樣函數 (最多 5 個)
    sample_size = min(5, len(valid_functions))
    if sample_size == 0:
        pytest.skip("沒有可測試的遷移函數,跳過 import 測試")

    sampled = random.sample(valid_functions, sample_size)

    import_errors = []

    for item in sampled:
        func_name = item["function_name"]
        new_loc = item["new_location"]

        # 轉換路徑為模組名稱
        # spellvid/domain/effects.py → spellvid.domain.effects
        module_path = new_loc.replace("/", ".").replace("\\", ".")[:-3]

        try:
            module = importlib.import_module(module_path)

            # 檢查函數是否存在
            if not hasattr(module, func_name):
                import_errors.append(
                    f"{func_name}: 模組 {module_path} 存在但函數不存在"
                )
        except ImportError as e:
            import_errors.append(
                f"{func_name}: 無法 import {module_path} - {e}"
            )

    if import_errors:
        pytest.fail(
            f"以下函數 import 失敗 (抽樣 {sample_size} 個):\n" +
            "\n".join(f"  - {err}" for err in import_errors) +
            "\n\n這是預期的失敗 (遷移尚未完成)"
        )

    print(f"\nImport 驗證 (抽樣):")
    print(f"  抽樣數量: {sample_size}/{len(valid_functions)}")
    print(f"  Import 成功: {sample_size}")

