#!/usr/bin/env python3
"""
冗餘函數刪除工具 - 根據使用分析報告刪除 test_only 和 unused 函數
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="刪除冗餘函數")
    parser.add_argument("--report", required=True,
                        help="FUNCTION_USAGE_REPORT.json 路徑")
    parser.add_argument("--category", choices=["test_only", "unused"], required=True,
                        help="要刪除的函數類別")
    parser.add_argument("--target", default="spellvid/utils.py", help="目標檔案")
    parser.add_argument("--dry-run", action="store_true", help="僅預覽,不實際刪除")

    args = parser.parse_args()
    print(f"將刪除類別: {args.category}")
    print(f"目標檔案: {args.target}")
    print("(工具尚未實作,這是骨架腳本)")


if __name__ == "__main__":
    main()
