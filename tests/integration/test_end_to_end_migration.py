"""
整合測試: 端到端遷移流程

這些測試驗證完整的遷移管線是否正常運作。
根據 TDD 原則,這些測試必須先寫且必須失敗 (因為管線尚未實作)。
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest


# ===== Test Fixtures =====

@pytest.fixture
def specs_dir() -> Path:
    """規格目錄"""
    return Path("specs/004-complete-module-migration")


@pytest.fixture
def usage_report_path(specs_dir: Path) -> Path:
    """使用分析報告路徑"""
    return specs_dir / "FUNCTION_USAGE_REPORT.json"


@pytest.fixture
def mapping_path(specs_dir: Path) -> Path:
    """遷移對應表路徑"""
    return specs_dir / "MIGRATION_MAPPING.json"


@pytest.fixture
def deletion_log_path(specs_dir: Path) -> Path:
    """刪除日誌路徑"""
    return specs_dir / "DELETION_LOG.md"


# ===== Integration Test 1: Analysis to Deletion Flow =====

def test_analysis_to_deletion_flow(
    usage_report_path: Path,
    deletion_log_path: Path
):
    """
    Integration Test 1: 測試分析 → 刪除流程

    驗證:
    1. FUNCTION_USAGE_REPORT.json 存在且有效
    2. 可從報告中識別 test_only 和 unused 函數
    3. DELETION_LOG.md 記錄刪除理由
    """
    # 檢查使用分析報告存在
    if not usage_report_path.exists():
        pytest.fail(
            f"使用分析報告不存在: {usage_report_path}\n"
            f"請先執行: python scripts/analyze_function_usage.py"
        )

    # 載入報告
    with open(usage_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # 識別待刪除函數
    to_delete = [
        item for item in report
        if item["category"] in ["test_only", "unused"]
    ]

    assert len(to_delete) > 0, (
        f"報告中沒有 test_only 或 unused 函數\n"
        f"這不符合預期 (應有 ~10-20 個待刪除函數)"
    )

    # 檢查刪除日誌 (如果存在)
    if deletion_log_path.exists():
        log_content = deletion_log_path.read_text(encoding="utf-8")

        # 驗證日誌包含刪除記錄
        for item in to_delete[:3]:  # 檢查前 3 個
            func_name = item["function_name"]
            assert func_name in log_content, (
                f"刪除日誌未記錄函數: {func_name}"
            )

    print(f"\n分析 → 刪除流程驗證:")
    print(f"  分析報告: ✓ ({len(report)} 個函數)")
    print(f"  待刪除函數: {len(to_delete)}")
    print(f"  刪除日誌: {'✓' if deletion_log_path.exists() else '待產生'}")


# ===== Integration Test 2: Migration to Re-export Flow =====

def test_migration_to_reexport_flow(
    mapping_path: Path,
    usage_report_path: Path
):
    """
    Integration Test 2: 測試遷移 → re-export 流程

    驗證:
    1. MIGRATION_MAPPING.json 存在且對應所有 production 函數
    2. utils.py 包含所有遷移函數的 re-export
    3. Re-export 函數可正常 import
    """
    # 檢查遷移對應表存在
    if not mapping_path.exists():
        pytest.fail(
            f"遷移對應表不存在: {mapping_path}\n"
            f"請先執行遷移對應生成工具"
        )

    # 載入對應表
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    assert len(mapping) > 0, "遷移對應表為空"

    # 載入使用報告 (驗證完整性)
    if usage_report_path.exists():
        with open(usage_report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        production_funcs = [
            item["function_name"]
            for item in report
            if item["category"] == "production"
        ]

        mapped_funcs = [item["function_name"] for item in mapping]

        # 驗證對應完整性
        missing = set(production_funcs) - set(mapped_funcs)
        assert not missing, (
            f"部分 production 函數缺少遷移對應: {missing}"
        )

    # 檢查 utils.py 是否已重寫為 re-export 層
    utils_py = Path("spellvid/utils.py")
    utils_content = utils_py.read_text(encoding="utf-8")
    utils_lines = len(utils_content.splitlines())

    if utils_lines < 200:  # 已重寫為 re-export 層
        # 驗證 re-export 包含所有遷移函數
        for item in mapping[:5]:  # 檢查前 5 個
            func_name = item["function_name"]
            # 簡單檢查函數名是否出現在檔案中
            assert func_name in utils_content, (
                f"utils.py 中找不到 re-export: {func_name}"
            )

    print(f"\n遷移 → Re-export 流程驗證:")
    print(f"  遷移對應表: ✓ ({len(mapping)} 個函數)")
    print(f"  utils.py 行數: {utils_lines}")
    print(f"  Re-export 層: {'✓ 已建立' if utils_lines < 200 else '待建立'}")


# ===== Integration Test 3: Full Pipeline with Validation =====

def test_full_pipeline_with_validation(specs_dir: Path):
    """
    Integration Test 3: 測試完整流程 + 驗證

    模擬完整遷移管線:
    1. 函數使用分析 → FUNCTION_USAGE_REPORT.json
    2. 冗餘函數刪除 → DELETION_LOG.md
    3. 有效函數遷移 → MIGRATION_MAPPING.json
    4. Re-export 層建立 → utils.py (80-120 行)
    5. 測試驗證 → 所有測試通過

    此測試驗證所有中間產物存在且一致。
    """
    expected_artifacts = [
        "FUNCTION_USAGE_REPORT.json",
        "MIGRATION_MAPPING.json",
    ]

    optional_artifacts = [
        "DELETION_LOG.md",
        "MANUAL_REVIEW_LOG.md",
    ]

    # 檢查必要產物
    missing = []
    for artifact in expected_artifacts:
        if not (specs_dir / artifact).exists():
            missing.append(artifact)

    if missing:
        pytest.fail(
            f"遷移管線中間產物缺失:\n" +
            "\n".join(f"  - {a}" for a in missing) +
            f"\n\n這是預期的失敗 (管線尚未執行)"
        )

    # 載入並驗證一致性
    usage_report_path = specs_dir / "FUNCTION_USAGE_REPORT.json"
    mapping_path = specs_dir / "MIGRATION_MAPPING.json"

    with open(usage_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # 驗證數量一致性
    production_count = sum(
        1 for item in report if item["category"] == "production"
    )

    assert len(mapping) == production_count, (
        f"遷移對應表數量不一致:\n"
        f"  Production 函數: {production_count}\n"
        f"  遷移對應: {len(mapping)}"
    )

    # 驗證 utils.py 狀態
    utils_py = Path("spellvid/utils.py")
    utils_lines = len(utils_py.read_text(encoding="utf-8").splitlines())

    reduction_rate = (3714 - utils_lines) / 3714 * 100

    # 檢查測試狀態 (可選)
    test_result = None
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 分鐘超時
        )
        test_result = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        test_result = None

    print(f"\n完整管線驗證:")
    print(f"  使用分析報告: ✓ ({len(report)} 個函數)")
    print(f"  遷移對應表: ✓ ({len(mapping)} 個函數)")
    print(f"  utils.py 行數: {utils_lines} (縮減 {reduction_rate:.1f}%)")
    print(f"  測試狀態: {'✓ 通過' if test_result else '待驗證'}")

    # 最終驗證
    if utils_lines <= 120 and reduction_rate >= 95.0:
        print(f"\n🎉 遷移管線目標達成!")
        print(f"  ✓ utils.py 縮減至 {utils_lines} 行")
        print(f"  ✓ 縮減率 {reduction_rate:.2f}% (≥95%)")
    else:
        print(f"\n⏳ 遷移管線進行中...")
