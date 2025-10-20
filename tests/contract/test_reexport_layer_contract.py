"""
契約測試: Re-export 層 (reexport_layer.md)

這些測試驗證重寫後的 utils.py 是否符合 re-export 層契約。
根據 TDD 原則,這些測試必須先寫且必須失敗 (因為 re-export 層尚未建立)。
"""

import importlib
import sys
import warnings
from pathlib import Path
from typing import List

import pytest


# ===== Test Fixtures =====

@pytest.fixture
def utils_py_path() -> Path:
    """utils.py 的路徑"""
    return Path("spellvid/utils.py")


@pytest.fixture
def utils_py_content(utils_py_path: Path) -> str:
    """讀取 utils.py 內容"""
    return utils_py_path.read_text(encoding="utf-8")


@pytest.fixture
def utils_py_lines(utils_py_content: str) -> List[str]:
    """utils.py 的行列表"""
    return utils_py_content.splitlines()


@pytest.fixture
def mapping_path() -> Path:
    """MIGRATION_MAPPING.json 的路徑"""
    return Path("specs/004-complete-module-migration/MIGRATION_MAPPING.json")


@pytest.fixture
def expected_exports(mapping_path: Path) -> List[str]:
    """從 MIGRATION_MAPPING.json 提取預期的 export 清單"""
    import json

    if not mapping_path.exists():
        pytest.skip(f"遷移對應表不存在: {mapping_path}")

    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    return [item["function_name"] for item in mapping]


# ===== Contract Test 1: Line Count in Range =====

def test_utils_line_count_in_range(utils_py_lines: List[str]):
    """
    Contract Test 1: 驗證 utils.py 行數在 80-120 範圍

    Re-export 層目標: 80-120 行 (從 3,714 行縮減 ≥95%)
    """
    line_count = len(utils_py_lines)

    assert 80 <= line_count <= 120, (
        f"utils.py 行數超出目標範圍: {line_count} 行\n"
        f"目標範圍: 80-120 行"
    )

    print(f"\n行數驗證:")
    print(f"  當前行數: {line_count}")
    print(f"  目標範圍: 80-120")


# ===== Contract Test 2: Reduction Rate Above 95% =====

def test_reduction_rate_above_95_percent(utils_py_lines: List[str]):
    """
    Contract Test 2: 驗證縮減率 ≥95%

    原始行數: 3,714 行
    目標: 80-120 行
    縮減率: (3714 - current) / 3714 * 100%
    """
    original_lines = 3714
    current_lines = len(utils_py_lines)

    reduction_rate = (original_lines - current_lines) / original_lines * 100

    assert reduction_rate >= 95.0, (
        f"縮減率未達目標: {reduction_rate:.2f}%\n"
        f"原始: {original_lines} 行\n"
        f"當前: {current_lines} 行\n"
        f"目標: ≥95% 縮減"
    )

    print(f"\n縮減率驗證:")
    print(f"  原始行數: {original_lines}")
    print(f"  當前行數: {current_lines}")
    print(f"  縮減率: {reduction_rate:.2f}%")


# ===== Contract Test 3: All Migrated Functions Exported =====

def test_all_migrated_functions_exported(
    utils_py_content: str,
    expected_exports: List[str]
):
    """
    Contract Test 3: 驗證所有已遷移函數都在 __all__ 中

    __all__ 必須包含 MIGRATION_MAPPING.json 中所有函數名稱。
    """
    # 提取 __all__ 內容
    # 簡單啟發式: 找到 __all__ = [...] 區塊
    import re

    all_pattern = re.compile(
        r"__all__\s*=\s*\[(.*?)\]",
        re.DOTALL | re.MULTILINE
    )

    match = all_pattern.search(utils_py_content)
    assert match, "utils.py 中找不到 __all__ 定義"

    all_content = match.group(1)

    # 提取所有字串字面值 (單引號或雙引號)
    exports_in_all = re.findall(r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']',
                                all_content)

    # 檢查遺漏的 export
    missing = set(expected_exports) - set(exports_in_all)

    assert not missing, (
        f"以下函數已遷移但未在 __all__ 中:\n" +
        "\n".join(f"  - {fn}" for fn in sorted(missing))
    )

    print(f"\nExport 完整性驗證:")
    print(f"  預期 export: {len(expected_exports)}")
    print(f"  __all__ 中的項目: {len(exports_in_all)}")
    print(f"  完整性: 100%")


# ===== Contract Test 4: DeprecationWarning Triggers =====

def test_deprecation_warning_triggers(utils_py_path: Path):
    """
    Contract Test 4: 驗證 DeprecationWarning 觸發

    import spellvid.utils 時應觸發 DeprecationWarning。
    """
    # 清除已 import 的模組 (強制重新 import)
    if "spellvid.utils" in sys.modules:
        del sys.modules["spellvid.utils"]
    if "spellvid" in sys.modules:
        del sys.modules["spellvid"]

    # 捕獲警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import utils
        importlib.import_module("spellvid.utils")

        # 驗證至少有一個 DeprecationWarning
        deprecation_warnings = [
            warn for warn in w
            if issubclass(warn.category, DeprecationWarning)
        ]

        assert len(deprecation_warnings) > 0, (
            f"import spellvid.utils 未觸發 DeprecationWarning\n"
            f"捕獲到的警告: {[warn.category.__name__ for warn in w]}"
        )

        # 驗證警告訊息包含關鍵字
        warning_msg = str(deprecation_warnings[0].message)
        assert "deprecated" in warning_msg.lower(), (
            f"警告訊息未包含 'deprecated': {warning_msg}"
        )
        assert "v2.0" in warning_msg or "2.0" in warning_msg, (
            f"警告訊息未提及版本: {warning_msg}"
        )

    print(f"\nDeprecationWarning 驗證:")
    print(f"  觸發警告數量: {len(deprecation_warnings)}")
    print(f"  警告訊息: {warning_msg[:80]}...")


# ===== Contract Test 5: All Exports Importable =====

def test_all_exports_importable(expected_exports: List[str]):
    """
    Contract Test 5: 驗證所有 export 可 import

    從 spellvid.utils import <function> 應成功。
    """
    import importlib

    # 重新載入 utils 模組
    if "spellvid.utils" in sys.modules:
        importlib.reload(sys.modules["spellvid.utils"])
    else:
        importlib.import_module("spellvid.utils")

    utils_module = sys.modules["spellvid.utils"]

    import_errors = []

    for func_name in expected_exports:
        if not hasattr(utils_module, func_name):
            import_errors.append(func_name)

    assert not import_errors, (
        f"以下函數無法從 spellvid.utils import:\n" +
        "\n".join(f"  - {fn}" for fn in import_errors[:10]) +
        (f"\n  ... 以及其他 {len(import_errors)-10} 個"
         if len(import_errors) > 10 else "")
    )

    print(f"\nImport 驗證:")
    print(f"  可 import 函數數: {len(expected_exports)}")
    print(f"  Import 成功率: 100%")


# ===== Contract Test 6: No Implementation Code =====

def test_no_implementation_code(utils_py_content: str):
    """
    Contract Test 6: 驗證無實作程式碼

    Re-export 層不應包含函數實作,僅包含:
    - import 語句
    - 別名賦值 (=)
    - 簡單 wrapper (adapter)
    - __all__ 定義

    檢查指標:
    - 不應有大量縮排的程式碼區塊 (>10 行連續 4+ 空格縮排)
    - 不應有 class 定義 (除了簡單 dataclass)
    """
    lines = utils_py_content.splitlines()

    # 統計連續深度縮排行數
    consecutive_indented = 0
    max_consecutive = 0

    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        # 計算縮排深度
        indent = len(line) - len(stripped)

        if indent >= 4:  # 至少一層縮排
            consecutive_indented += 1
            max_consecutive = max(max_consecutive, consecutive_indented)
        else:
            consecutive_indented = 0

    assert max_consecutive < 15, (
        f"檢測到過多連續縮排行 ({max_consecutive} 行)\n"
        f"Re-export 層不應包含大量實作程式碼"
    )

    # 檢查 class 定義數量
    class_count = utils_py_content.count("\nclass ")
    assert class_count == 0, (
        f"檢測到 {class_count} 個 class 定義\n"
        f"Re-export 層不應定義新 class"
    )

    print(f"\n實作程式碼檢查:")
    print(f"  最大連續縮排行數: {max_consecutive}")
    print(f"  Class 定義數: {class_count}")
    print(f"  驗證: 無實作程式碼 ✓")


# ===== Contract Test 7: Backward Compatibility Imports =====

def test_backward_compatibility_imports():
    """
    Contract Test 7: 驗證向後相容性 import

    確保常見的舊 import 路徑仍然有效:
    - from spellvid.utils import render_video_stub
    - from spellvid.utils import _make_text_imageclip
    等等
    """
    import importlib

    # 重新載入模組
    if "spellvid.utils" in sys.modules:
        importlib.reload(sys.modules["spellvid.utils"])
    else:
        importlib.import_module("spellvid.utils")

    # 測試幾個關鍵函數 (從 baseline 測試中提取)
    critical_imports = [
        "render_video_stub",  # 最常用的入口函數
        # 其他關鍵函數會在遷移完成後補充
    ]

    utils_module = sys.modules["spellvid.utils"]

    missing = []
    for func_name in critical_imports:
        if not hasattr(utils_module, func_name):
            missing.append(func_name)

    if missing:
        pytest.fail(
            f"關鍵函數缺失,向後相容性受影響:\n" +
            "\n".join(f"  - {fn}" for fn in missing)
        )

    print(f"\n向後相容性驗證:")
    print(f"  關鍵函數檢查: {len(critical_imports)}")
    print(f"  全部可用: ✓")
