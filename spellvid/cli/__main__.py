"""CLI 模組的 __main__ 入口點

允許使用 `python -m spellvid.cli` 執行。
委派給 parser 和 commands 模組直接執行。
"""

from .parser import build_parser
from .commands import make_command, batch_command


def main(argv: list[str] | None = None) -> int:
    """CLI 入口點 - 解析參數並執行命令"""
    p = build_parser()
    args = p.parse_args(argv)
    if args.cmd == "make":
        return make_command(args)
    if args.cmd == "batch":
        return batch_command(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
