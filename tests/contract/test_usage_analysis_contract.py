"""
契約測試: 函數使用分析 (usage_analysis.md)

這些測試驗證 FUNCTION_USAGE_REPORT.json 是否符合契約規格。
根據 TDD 原則,這些測試必須先寫且必須失敗 (因為報告尚未產生)。
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


# ===== Test Fixtures =====

@pytest.fixture
def report_path() -> Path:
    """FUNCTION_USAGE_REPORT.json 的預期路徑"""
    return Path("specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json")


@pytest.fixture
def report_data(report_path: Path) -> List[Dict[str, Any]]:
    """載入並解析使用分析報告"""
    if not report_path.exists():
        pytest.fail(f"使用分析報告不存在: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        pytest.fail(f"報告格式錯誤: 預期 array,得到 {type(data)}")

    return data


@pytest.fixture
def utils_py_path() -> Path:
    """utils.py 的路徑"""
    return Path("spellvid/utils.py")


# ===== Contract Test 1: Schema Validation =====

def test_usage_report_schema_valid(report_data: List[Dict[str, Any]]):
    """
    Contract Test 1: 驗證 JSON schema

    每個 FunctionUsageReport 必須包含:
    - function_name: str (有效 Python identifier)
    - category: "production" | "test_only" | "unused"
    - references: array of FileReference
    - call_count: int >= 0
    - analysis_confidence: float [0.0, 1.0]
    - notes: str (可選)
    """
    assert len(report_data) > 0, "報告不能為空"

    required_fields = {"function_name", "category", "references",
                       "call_count", "analysis_confidence"}
    valid_categories = {"production", "test_only", "unused"}

    for i, func_report in enumerate(report_data):
        # 檢查必填欄位
        missing = required_fields - set(func_report.keys())
        assert not missing, (
            f"函數報告 #{i} 缺少欄位: {missing}\n"
            f"Function: {func_report.get('function_name', 'unknown')}"
        )

        # 驗證 function_name 格式
        func_name = func_report["function_name"]
        assert isinstance(
            func_name, str), f"function_name 必須是 string: {func_name}"
        assert func_name.isidentifier(), (
            f"function_name 必須是有效 Python identifier: {func_name}"
        )

        # 驗證 category 枚舉值
        category = func_report["category"]
        assert category in valid_categories, (
            f"函數 {func_name} 的 category 無效: {category}\n"
            f"有效值: {valid_categories}"
        )

        # 驗證 references 結構
        refs = func_report["references"]
        assert isinstance(refs, list), f"references 必須是 array: {func_name}"

        for j, ref in enumerate(refs):
            assert "filepath" in ref, f"{func_name} reference #{j} 缺少 filepath"
            assert "line_number" in ref, f"{func_name} reference #{j} 缺少 line_number"
            assert "context" in ref, f"{func_name} reference #{j} 缺少 context"

            assert isinstance(ref["line_number"], int), (
                f"{func_name} reference #{j} line_number 必須是 int"
            )
            assert ref["line_number"] >= 1, (
                f"{func_name} reference #{j} line_number 必須 >= 1"
            )

        # 驗證 call_count
        call_count = func_report["call_count"]
        assert isinstance(call_count, int), f"call_count 必須是 int: {func_name}"
        assert call_count >= 0, f"call_count 必須 >= 0: {func_name}"

        # 驗證 analysis_confidence
        confidence = func_report["analysis_confidence"]
        assert isinstance(confidence, (int, float)), (
            f"analysis_confidence 必須是 number: {func_name}"
        )
        assert 0.0 <= confidence <= 1.0, (
            f"analysis_confidence 必須在 [0.0, 1.0]: {func_name} = {confidence}"
        )


# ===== Contract Test 2: Completeness Check =====

def test_all_utils_functions_analyzed(report_data: List[Dict[str, Any]],
                                      utils_py_path: Path):
    """
    Contract Test 2: 驗證完整性

    報告必須包含 utils.py 中所有函數定義 (包括 private functions)。
    預期至少 50+ 個函數。
    """
    # 從報告中提取函數名稱
    analyzed_functions = {item["function_name"] for item in report_data}

    # 簡單啟發式: 統計 utils.py 中的 'def ' 定義數量
    # (完整實作應使用 AST 解析,但測試僅需基本驗證)
    utils_content = utils_py_path.read_text(encoding="utf-8")
    def_count = utils_content.count(
        "\ndef ") + utils_content.count("\n    def ")

    # 驗證數量合理性 (實際 utils.py 有 48 個函數)
    assert len(analyzed_functions) >= 45, (
        f"報告中函數數量過少: {len(analyzed_functions)}\n"
        f"預期至少 45 個函數 (utils.py 包含 ~{def_count} 個 'def' 定義)"
    )

    # 驗證沒有重複
    func_names = [item["function_name"] for item in report_data]
    duplicates = [name for name in func_names if func_names.count(name) > 1]
    assert not duplicates, f"報告中有重複函數: {set(duplicates)}"


# ===== Contract Test 3: Category Mutual Exclusivity =====

def test_category_mutual_exclusivity(report_data: List[Dict[str, Any]]):
    """
    Contract Test 3: 驗證分類互斥

    根據契約定義:
    - production: 被 spellvid/*.py (非測試) 或 scripts/*.py 引用
    - test_only: 僅被 tests/*.py 引用
    - unused: 無任何引用

    這三個類別必須互斥且完整 (每個函數屬於且僅屬於一個類別)。
    """
    categories_count = {"production": 0, "test_only": 0, "unused": 0}

    for func_report in report_data:
        func_name = func_report["function_name"]
        category = func_report["category"]
        refs = func_report["references"]

        # 統計引用來源
        has_production_ref = False
        has_test_ref = False

        for ref in refs:
            filepath = ref["filepath"]

            # 排除 utils.py 自身
            if filepath == "spellvid/utils.py" or filepath == "spellvid\\utils.py":
                continue

            # 檢查是否為生產路徑
            if (filepath.startswith("spellvid/") or filepath.startswith("spellvid\\")) and "tests" not in filepath:
                has_production_ref = True
            elif filepath.startswith("scripts/") or filepath.startswith("scripts\\"):
                has_production_ref = True

            # 檢查是否為測試路徑
            if filepath.startswith("tests/") or filepath.startswith("tests\\"):
                has_test_ref = True

        # 驗證分類邏輯
        if len(refs) == 0:
            assert category == "unused", (
                f"函數 {func_name} 無引用但分類為 {category},應為 unused"
            )
        elif has_production_ref:
            assert category == "production", (
                f"函數 {func_name} 有生產引用但分類為 {category},應為 production\n"
                f"References: {[r['filepath'] for r in refs]}"
            )
        elif has_test_ref and not has_production_ref:
            assert category == "test_only", (
                f"函數 {func_name} 僅有測試引用但分類為 {category},應為 test_only\n"
                f"References: {[r['filepath'] for r in refs]}"
            )

        categories_count[category] += 1

    # 驗證分佈合理性
    total = sum(categories_count.values())
    assert total == len(report_data), "分類統計錯誤"

    print(f"\n分類分佈:")
    print(f"  production: {categories_count['production']}")
    print(f"  test_only:  {categories_count['test_only']}")
    print(f"  unused:     {categories_count['unused']}")


# ===== Contract Test 4: Call Count Consistency =====

def test_call_count_consistency(report_data: List[Dict[str, Any]]):
    """
    Contract Test 4: 驗證 call_count 一致性

    call_count 必須等於 len(references)
    """
    for func_report in report_data:
        func_name = func_report["function_name"]
        call_count = func_report["call_count"]
        refs = func_report["references"]

        assert call_count == len(refs), (
            f"函數 {func_name} 的 call_count 不一致:\n"
            f"  call_count: {call_count}\n"
            f"  len(references): {len(refs)}"
        )


# ===== Contract Test 5: Confidence Threshold =====

def test_confidence_threshold(report_data: List[Dict[str, Any]]):
    """
    Contract Test 5: 驗證信心度門檻

    至少 80% 的函數應有 confidence >= 0.8 (三工具一致)。
    低信心度函數應有人工審查註記。
    """
    high_confidence = []
    low_confidence = []

    for func_report in report_data:
        func_name = func_report["function_name"]
        confidence = func_report["analysis_confidence"]

        if confidence >= 0.8:
            high_confidence.append(func_name)
        else:
            low_confidence.append(func_name)
            # 低信心度函數應有註記
            notes = func_report.get("notes", "")
            assert notes and len(notes) > 0, (
                f"函數 {func_name} 信心度低 ({confidence}) 但缺少人工審查註記"
            )

    total = len(report_data)
    high_pct = len(high_confidence) / total * 100 if total > 0 else 0

    assert high_pct >= 80.0, (
        f"高信心度函數比例過低: {high_pct:.1f}%\n"
        f"預期至少 80% 的函數 confidence >= 0.8\n"
        f"低信心度函數 ({len(low_confidence)}): {low_confidence[:10]}..."
    )

    print(f"\n信心度分佈:")
    print(f"  >= 0.8: {len(high_confidence)} ({high_pct:.1f}%)")
    print(f"  <  0.8: {len(low_confidence)} ({100-high_pct:.1f}%)")
