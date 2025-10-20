#!/usr/bin/env python3
"""
生成 Re-export 層 - 將 utils.py 轉換為輕量級向後相容層

目標: 3,714 行 → 80-120 行 (≥95% 縮減)

結構:
  Section 1: Module docstring + DeprecationWarning (15 行)
  Section 2: Import statements (30-50 行)
  Section 3: Aliases (如需要, 15-30 行)
  Section 4: __all__ list (20-25 行)
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List, Set


DEPRECATION_WARNING = '''"""
spellvid.utils - 向後相容層 (Backward Compatibility Layer)

⚠️  DEPRECATED: 此模組將在 v2.0 移除

所有功能已遷移至分層架構:
  - spellvid.domain.*       (純邏輯: 佈局、注音、效果、時間)
  - spellvid.infrastructure.* (框架整合: MoviePy、Pillow、FFmpeg)
  - spellvid.application.*   (業務邏輯: 視頻服務、批次處理)
  - spellvid.shared.*        (共用: 型別、驗證、常數)

請更新 import 路徑至新模組,此相容層僅供過渡使用。

範例遷移:
  舊: from spellvid.utils import compute_layout_bboxes
  新: from spellvid.domain.layout import compute_layout_bboxes
  
  舊: from spellvid.utils import render_video
  新: from spellvid.application.video_service import render_video

更多資訊: doc/ARCHITECTURE.md
"""

import warnings as _warnings

_warnings.warn(
    "spellvid.utils is deprecated and will be removed in v2.0. "
    "Please update imports to use the new modular architecture. "
    "See doc/ARCHITECTURE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)
'''


def load_utils_functions(utils_py_path: Path) -> List[str]:
    """提取 utils.py 中所有函數名稱"""
    content = utils_py_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 排除內部類別方法 (如 _SimpleImageClip 的方法)
            if not node.name.startswith("__") or node.name in ["__init__"]:
                functions.append(node.name)

    return functions


def load_migrated_functions() -> Dict[str, str]:
    """載入已遷移函數的新位置"""
    # 已知已遷移的函數
    migrated = {
        # shared/validation.py
        "load_json": "spellvid.shared.validation",
        "validate_schema": "spellvid.shared.validation",

        # domain/typography.py
        "zhuyin_for": "spellvid.domain.typography",
        "_zhuyin_main_gap": "spellvid.domain.typography",

        # domain/layout.py
        "compute_layout_bboxes": "spellvid.domain.layout",

        # application/resource_checker.py
        "check_assets": "spellvid.application.resource_checker",
    }

    return migrated


def generate_import_section(
    functions: List[str], migrated: Dict[str, str]
) -> tuple[str, List[str]]:
    """生成 import section + 識別未遷移函數"""

    imports_by_module = {}
    unmigrated = []

    for func in functions:
        if func in migrated:
            module = migrated[func]
            if module not in imports_by_module:
                imports_by_module[module] = []
            imports_by_module[module].append(func)
        else:
            # 未遷移,保留在 utils.py
            unmigrated.append(func)

    # 生成 import 語句
    import_lines = ["# Re-exports from new modular architecture\n"]

    # 按 layer 分組
    layers = {
        "shared": [],
        "domain": [],
        "infrastructure": [],
        "application": [],
    }

    for module, funcs in sorted(imports_by_module.items()):
        for layer in layers:
            if f".{layer}." in module:
                layers[layer].append((module, funcs))
                break

    # 生成分層 imports
    for layer_name, imports in layers.items():
        if imports:
            import_lines.append(f"# {layer_name.capitalize()} Layer")
            for module, funcs in sorted(imports):
                funcs_str = ", ".join(sorted(funcs))
                import_lines.append(f"from {module} import {funcs_str}")
            import_lines.append("")

    return "\n".join(import_lines), unmigrated


def generate_all_section(functions: List[str]) -> str:
    """生成 __all__ export list"""

    # 排除 private 函數 (以 _ 開頭但保留 __init__)
    public_funcs = [
        f for f in functions
        if not f.startswith("_") or f == "__init__"
    ]

    # 分行輸出 (每行 4 個)
    lines = ["__all__ = ["]

    for i in range(0, len(public_funcs), 4):
        chunk = public_funcs[i:i+4]
        items = ", ".join(f'"{f}"' for f in chunk)
        lines.append(f"    {items},")

    lines.append("]")

    return "\n".join(lines)


def generate_reexport_layer(
    utils_py_path: Path,
    output_path: Path,
    dry_run: bool = False
) -> Dict[str, int]:
    """生成完整的 re-export 層"""

    print("🔨 生成 Re-export 層")
    print("=" * 60)

    # Step 1: 載入函數清單
    print("\nStep 1: 載入 utils.py 函數清單...")
    functions = load_utils_functions(utils_py_path)
    print(f"  找到 {len(functions)} 個函數")

    # Step 2: 載入遷移對應
    print("\nStep 2: 載入已遷移函數對應...")
    migrated = load_migrated_functions()
    print(f"  已遷移: {len(migrated)} 個")

    # Step 3: 生成各 section
    print("\nStep 3: 生成各 section...")

    sections = []
    stats = {}

    # Section 1: Deprecation warning
    sections.append(DEPRECATION_WARNING)
    stats["deprecation"] = DEPRECATION_WARNING.count("\n")

    # Section 2: Imports
    import_section, unmigrated = generate_import_section(functions, migrated)
    sections.append(import_section)
    stats["imports"] = import_section.count("\n")
    stats["unmigrated_count"] = len(unmigrated)

    # Section 3: Note about unmigrated functions
    if unmigrated:
        note = f"""
# ⚠️  以下 {len(unmigrated)} 個函數仍保留在此檔案 (未遷移):
# {', '.join(unmigrated[:10])}{"..." if len(unmigrated) > 10 else ""}
# 這些函數將在後續版本中遷移至適當模組

"""
        sections.append(note)
        stats["note"] = note.count("\n")

    # Section 4: __all__ list
    all_section = generate_all_section(functions)
    sections.append(all_section)
    stats["all_list"] = all_section.count("\n")

    # 組合完整內容
    content = "\n".join(sections)
    stats["total_lines"] = content.count("\n") + 1

    # 統計
    print(f"\n📊 生成統計:")
    print(f"  Deprecation warning: {stats['deprecation']} 行")
    print(f"  Imports:             {stats['imports']} 行")
    print(f"  Note:                {stats.get('note', 0)} 行")
    print(f"  __all__ list:        {stats['all_list']} 行")
    print(f"  總計:                {stats['total_lines']} 行")

    print(f"\n📈 縮減統計:")
    original_lines = sum(1 for _ in utils_py_path.read_text(
        encoding="utf-8").splitlines())
    reduction = (1 - stats['total_lines'] / original_lines) * 100
    print(f"  原始: {original_lines} 行")
    print(f"  新版: {stats['total_lines']} 行")
    print(f"  縮減: {reduction:.1f}%")

    # 驗證目標
    if 80 <= stats['total_lines'] <= 120:
        print(f"  ✅ 符合目標 (80-120 行)")
    else:
        print(f"  ⚠️  超出目標範圍 (80-120 行)")

    if reduction >= 95:
        print(f"  ✅ 達成 ≥95% 縮減目標")
    else:
        print(f"  ⚠️  未達 95% 縮減目標")

    # 輸出
    if dry_run:
        print("\n🔍 Dry-run 模式,不寫入檔案")
        print("\n--- Preview (前 50 行) ---")
        preview_lines = content.split("\n")[:50]
        print("\n".join(preview_lines))
        if len(content.split("\n")) > 50:
            print(f"\n... (還有 {len(content.split('\n')) - 50} 行)")
    else:
        output_path.write_text(content, encoding="utf-8")
        print(f"\n✅ Re-export 層已儲存: {output_path}")

    stats["original_lines"] = original_lines
    stats["reduction_percent"] = reduction

    return stats


def main():
    parser = argparse.ArgumentParser(description="生成 Re-export 層")
    parser.add_argument(
        "--input",
        default="spellvid/utils.py",
        help="原始 utils.py 路徑"
    )
    parser.add_argument(
        "--output",
        default="spellvid/utils_reexport.py",
        help="輸出 re-export 層路徑 (預設不覆寫原檔)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="預覽模式,不實際寫入檔案"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="直接覆寫原始 utils.py (危險!建議先備份)"
    )

    args = parser.parse_args()

    utils_py_path = Path(args.input)

    # 決定輸出路徑
    if args.replace:
        output_path = utils_py_path
        print("⚠️  警告: 將直接覆寫 utils.py!")
    else:
        output_path = Path(args.output)

    # 執行生成
    stats = generate_reexport_layer(utils_py_path, output_path, args.dry_run)

    # 建議後續步驟
    if not args.dry_run:
        print("\n💡 後續步驟:")
        print("  1. 檢查生成的檔案")
        print(f"     cat {output_path}")
        print("  2. 執行契約測試驗證")
        print("     pytest tests/contract/test_reexport_layer_contract.py -v")
        if not args.replace:
            print("  3. 備份原始 utils.py")
            print("     cp spellvid/utils.py spellvid/utils.py.backup_before_reexport")
            print("  4. 替換 utils.py")
            print(f"     cp {output_path} spellvid/utils.py")


if __name__ == "__main__":
    main()
