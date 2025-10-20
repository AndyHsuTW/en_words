#!/usr/bin/env python3
"""
驗證遷移完整性 - 檢查 utils.py 的函數是否已在新模組實作

使用方式:
    python scripts/verify_migration_completeness.py
    python scripts/verify_migration_completeness.py --verbose
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List, Set


def extract_functions_from_file(filepath: Path) -> List[str]:
    """提取檔案中所有函數名稱"""
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except (SyntaxError, UnicodeDecodeError):
        return []


def scan_new_modules(spellvid_dir: Path) -> Dict[str, List[str]]:
    """掃描新模組中的所有函數"""
    modules = {}

    for py_file in spellvid_dir.rglob("*.py"):
        rel_path = py_file.relative_to(spellvid_dir)
        rel_str = str(rel_path).replace("\\", "/")

        # 排除 utils.py 和相關備份檔
        if "utils" in py_file.name or "__pycache__" in str(py_file):
            continue

        funcs = extract_functions_from_file(py_file)
        if funcs:
            modules[rel_str] = funcs

    return modules


def load_usage_report(report_path: Path) -> List[Dict]:
    """載入函數使用報告"""
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


def find_function_in_modules(
    func_name: str, modules: Dict[str, List[str]]
) -> List[str]:
    """在新模組中尋找函數"""
    locations = []
    for module_path, funcs in modules.items():
        if func_name in funcs:
            locations.append(module_path)
    return locations


def main():
    parser = argparse.ArgumentParser(description="驗證函數遷移完整性")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")
    parser.add_argument(
        "--report",
        default="specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json",
        help="函數使用報告路徑",
    )
    parser.add_argument(
        "--output",
        default="specs/004-complete-module-migration/MIGRATION_STATUS.json",
        help="輸出遷移狀態報告",
    )

    args = parser.parse_args()

    print("🔍 驗證函數遷移完整性")
    print("=" * 60)

    # 載入使用報告
    print("\nStep 1: 載入函數使用報告...")
    report_path = Path(args.report)
    usage_report = load_usage_report(report_path)
    print(f"  找到 {len(usage_report)} 個函數記錄")

    # 掃描新模組
    print("\nStep 2: 掃描新模組...")
    spellvid_dir = Path("spellvid")
    new_modules = scan_new_modules(spellvid_dir)
    total_new_funcs = sum(len(funcs) for funcs in new_modules.values())
    print(f"  找到 {len(new_modules)} 個新模組")
    print(f"  總計 {total_new_funcs} 個函數")

    # 對比分析
    print("\nStep 3: 對比分析...")

    migration_status = {
        "migrated": [],      # 已遷移至新模組
        "in_utils_only": [],  # 僅在 utils.py
        "duplicated": [],    # 同時存在於 utils.py 和新模組
    }

    for func_record in usage_report:
        func_name = func_record["function_name"]

        # 在新模組中尋找
        locations = find_function_in_modules(func_name, new_modules)

        if locations:
            status_entry = {
                "function_name": func_name,
                "new_locations": locations,
                "category": func_record["category"],
            }

            # 檢查是否在 utils.py 中也有定義 (非 import)
            # 簡單檢查: 如果在 FUNCTION_USAGE_REPORT 中,表示在 utils.py 定義
            migration_status["duplicated"].append(status_entry)
        else:
            # 僅在 utils.py
            migration_status["in_utils_only"].append({
                "function_name": func_name,
                "category": func_record["category"],
                "call_count": func_record["call_count"],
            })

    # 統計結果
    print("\n" + "=" * 60)
    print("分析結果")
    print("=" * 60)

    print(f"\n📊 遷移狀態統計:")
    print(f"  已遷移至新模組: {len(migration_status['duplicated'])} 個")
    print(f"  僅在 utils.py:  {len(migration_status['in_utils_only'])} 個")

    # 詳細輸出
    if args.verbose:
        print(f"\n📋 已遷移函數 ({len(migration_status['duplicated'])} 個):")
        for item in migration_status["duplicated"][:10]:
            locs = ", ".join(item["new_locations"])
            print(f"  ✅ {item['function_name']} → {locs}")
        if len(migration_status["duplicated"]) > 10:
            print(f"  ... (還有 {len(migration_status['duplicated']) - 10} 個)")

        print(
            f"\n⚠️  僅在 utils.py 的函數 ({len(migration_status['in_utils_only'])} 個):")
        for item in migration_status["in_utils_only"][:10]:
            print(f"  - {item['function_name']} (calls: {item['call_count']})")
        if len(migration_status["in_utils_only"]) > 10:
            print(
                f"  ... (還有 {len(migration_status['in_utils_only']) - 10} 個)")

    # 輸出 JSON 報告
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(migration_status, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 遷移狀態報告已儲存: {output_path}")

    # 遷移建議
    print("\n💡 遷移建議:")

    if len(migration_status["duplicated"]) > 0:
        print(f"  1. 已有 {len(migration_status['duplicated'])} 個函數在新模組實作")
        print(f"     → 可直接建立 re-export 層")

    if len(migration_status["in_utils_only"]) > 0:
        print(
            f"  2. 還有 {len(migration_status['in_utils_only'])} 個函數僅在 utils.py")
        print(f"     → 需要先遷移至新模組或確認為 wrapper")

    # 決策建議
    print("\n🎯 下一步驟建議:")

    if len(migration_status["in_utils_only"]) == 0:
        print("  ✅ 所有函數已遷移,可直接進入 Phase 3.6 (建立 re-export 層)")
    elif len(migration_status["in_utils_only"]) < 10:
        print(f"  ⚠️  還有 {len(migration_status['in_utils_only'])} 個函數需要遷移")
        print("     建議: 手動檢查這些函數是否為 wrapper 或需要遷移")
    else:
        print(f"  ❌ 還有 {len(migration_status['in_utils_only'])} 個函數需要遷移")
        print("     建議: 執行完整的 Phase 3.5 遷移流程")


if __name__ == "__main__":
    main()
