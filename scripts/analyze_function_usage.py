#!/usr/bin/env python3
"""
函數使用分析工具 - 分析 utils.py 中每個函數的使用情況

使用多工具交叉驗證 (grep + AST) 識別函數分類:
- production: 被生產代碼使用 (spellvid/*.py 非測試, scripts/*.py)
- test_only: 僅被測試使用 (tests/*.py)
- unused: 無任何引用
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List


# ===== Data Structures =====

class FileReference:
    """檔案引用位置"""

    def __init__(self, filepath: str, line_number: int, context: str):
        self.filepath = filepath
        self.line_number = line_number
        self.context = context

    def to_dict(self):
        return {
            "filepath": self.filepath,
            "line_number": self.line_number,
            "context": self.context,
        }


class FunctionUsageReport:
    """函數使用報告"""

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.references: List[FileReference] = []
        self.category = "unused"  # production | test_only | unused
        self.analysis_confidence = 0.0
        self.notes = ""

    @property
    def call_count(self) -> int:
        return len(self.references)

    def to_dict(self):
        return {
            "function_name": self.function_name,
            "category": self.category,
            "references": [ref.to_dict() for ref in self.references],
            "call_count": self.call_count,
            "analysis_confidence": self.analysis_confidence,
            "notes": self.notes,
        }


# ===== Tool 1: grep 掃描 =====


def grep_scan_references(
    function_name: str, repo_root: Path, verbose: bool = False
) -> List[FileReference]:
    """
    使用 grep 掃描函數名稱出現位置

    Returns:
        List[FileReference]: 引用位置清單
    """
    references = []

    # 使用 Python 自己掃描 (跨平台相容)
    for py_file in repo_root.rglob("*.py"):
        # 排除路徑
        rel_path = py_file.relative_to(repo_root)
        rel_str = str(rel_path).replace("\\", "/")

        # 跳過排除的路徑
        if any(
            exclude in rel_str
            for exclude in ["__pycache__", ".venv", "venv", ".git", ".bak"]
        ):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines, start=1):
                # 檢查函數名稱是否出現 (簡單字串匹配)
                if function_name in line:
                    # 提取上下文 (前後各 1 行)
                    context_lines = []
                    if i > 1:
                        context_lines.append(lines[i - 2])
                    context_lines.append(line)
                    if i < len(lines):
                        context_lines.append(lines[i])

                    context = "\n".join(context_lines)

                    references.append(FileReference(rel_str, i, context))

                    if verbose:
                        print(f"  Found in {rel_str}:{i}")

        except (UnicodeDecodeError, PermissionError):
            continue

    return references


# ===== Tool 3: 呼叫圖分析 =====


def build_call_graph(utils_py_path: Path) -> Dict[str, List[str]]:
    """
    建立 utils.py 內部的呼叫圖

    Returns:
        Dict[str, List[str]]: {caller: [callee1, callee2, ...]}
    """
    call_graph = {}

    try:
        content = utils_py_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # 提取所有函數名稱
        all_functions = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }

        # 分析每個函數的呼叫
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                callees = []

                # 掃描函數體中的 Call nodes
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        # 提取被呼叫的函數名稱
                        if isinstance(child.func, ast.Name):
                            callee = child.func.id
                            if callee in all_functions:
                                callees.append(callee)

                call_graph[func_name] = callees

    except SyntaxError:
        pass

    return call_graph


# ===== 分類邏輯 =====


def classify_function(
    function_name: str, references: List[FileReference], utils_filepath: str
) -> str:
    """
    根據引用位置分類函數

    Returns:
        "production" | "test_only" | "unused"
    """
    if len(references) == 0:
        return "unused"

    has_production = False
    has_test = False

    for ref in references:
        filepath = ref.filepath

        # 排除 utils.py 自身
        if filepath == utils_filepath or filepath.replace("\\", "/") == utils_filepath:
            continue

        # 檢查是否為生產代碼
        if filepath.startswith("spellvid/") or filepath.startswith("spellvid\\"):
            if "tests" not in filepath:
                has_production = True

        if filepath.startswith("scripts/") or filepath.startswith("scripts\\"):
            has_production = True

        # 檢查是否為測試代碼
        if filepath.startswith("tests/") or filepath.startswith("tests\\"):
            has_test = True

    # 分類決策
    if has_production:
        return "production"
    elif has_test:
        return "test_only"
    else:
        return "unused"


# ===== 主函數 =====


def extract_functions_from_utils(utils_py_path: Path) -> List[str]:
    """提取 utils.py 中所有函數名稱"""
    content = utils_py_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    functions = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]

    return functions


def main():
    parser = argparse.ArgumentParser(description="分析 utils.py 函數使用情況")
    parser.add_argument("--input", default="spellvid/utils.py", help="要分析的檔案")
    parser.add_argument(
        "--output",
        default="specs/004-complete-module-migration/FUNCTION_USAGE_REPORT.json",
        help="輸出的 JSON 報告",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    utils_py_path = Path(args.input)
    output_path = Path(args.output)
    repo_root = Path(".")

    print(f"🔍 分析檔案: {utils_py_path}")
    print(f"📊 輸出報告: {output_path}")
    print()

    # 提取所有函數
    print("Step 1: 提取函數定義...")
    functions = extract_functions_from_utils(utils_py_path)
    print(f"  找到 {len(functions)} 個函數")

    # 建立呼叫圖
    print("\nStep 2: 建立內部呼叫圖...")
    call_graph = build_call_graph(utils_py_path)
    print(f"  呼叫關係: {sum(len(v) for v in call_graph.values())} 個")

    # 分析每個函數
    print("\nStep 3: 掃描引用位置 (grep)...")
    reports = []

    for i, func_name in enumerate(functions, 1):
        if args.verbose:
            print(f"\n[{i}/{len(functions)}] {func_name}")
        else:
            if i % 10 == 0:
                print(f"  進度: {i}/{len(functions)}")

        # 使用 grep 掃描
        references = grep_scan_references(func_name, repo_root, args.verbose)

        # 分類
        category = classify_function(func_name, references, args.input)

        # 建立報告
        report = FunctionUsageReport(func_name)
        report.references = references
        report.category = category

        # 計算信心度 (grep掃描 + 分類邏輯)
        # - 基礎 grep 掃描: 0.6
        # - 有 production 引用: +0.2
        # - 引用數 >= 5: +0.2
        base_confidence = 0.6
        if category == "production":
            base_confidence += 0.2
        if len(references) >= 5:
            base_confidence += 0.2
        report.analysis_confidence = min(base_confidence, 1.0)

        # 添加註記
        if category == "unused" and len(references) > 0:
            report.notes = "僅在 utils.py 內部被引用"
        elif category == "test_only":
            report.notes = "僅被測試使用,生產代碼未引用"
        elif report.analysis_confidence < 0.8:
            report.notes = f"低信心分類 (refs={len(references)}), 需人工審查"

        reports.append(report)

    # 統計結果
    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)

    categories = {"production": 0, "test_only": 0, "unused": 0}
    for report in reports:
        categories[report.category] += 1

    print(f"\n分類統計:")
    print(f"  production: {categories['production']} 個")
    print(f"  test_only:  {categories['test_only']} 個")
    print(f"  unused:     {categories['unused']} 個")

    # 輸出 JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = [report.to_dict() for report in reports]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 報告已儲存: {output_path}")
    print(f"📄 總計: {len(reports)} 個函數")


if __name__ == "__main__":
    main()
