"""CLI 入口點 - 向後相容層

此模組現在作為輕量入口點,委派給新的 CLI 架構。
保留舊函數簽名以維持向後相容性。

新架構使用:
- spellvid.cli.parser: 參數解析
- spellvid.cli.commands: 命令處理

舊函數 (make, batch, build_parser) 已標記為 deprecated,
但仍保留以維持向後相容性。
"""

import argparse
import warnings

# 新架構 imports
from .cli import build_parser as _new_build_parser
from .cli import make_command, batch_command


# === 向後相容層: 保留舊函數簽名 ===

def make(args: argparse.Namespace) -> int:
    """舊版 make 函數 - 向後相容

    已棄用: 請使用 spellvid.cli.commands.make_command
    此函數委派給新的 CLI 架構。
    """
    warnings.warn(
        "spellvid.cli.make() is deprecated. "
        "Use spellvid.cli.commands.make_command() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return make_command(args)


def batch(args: argparse.Namespace) -> int:
    """舊版 batch 函數 - 向後相容

    已棄用: 請使用 spellvid.cli.commands.batch_command
    此函數委派給新的 CLI 架構。
    """
    warnings.warn(
        "spellvid.cli.batch() is deprecated. "
        "Use spellvid.cli.commands.batch_command() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return batch_command(args)


def build_parser():
    """舊版 build_parser - 向後相容

    已棄用: 請使用 spellvid.cli.parser.build_parser
    此函數委派給新的 CLI 架構。
    """
    warnings.warn(
        "spellvid.cli.build_parser() is deprecated. "
        "Use spellvid.cli.parser.build_parser() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return _new_build_parser()


def main(argv: list[str] | None = None) -> int:
    """CLI 入口點 - 解析參數並執行命令"""
    p = build_parser()
    args = p.parse_args(argv)
    if args.cmd == "make":
        return make(args)
    if args.cmd == "batch":
        return batch(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
