"""CLI 模組 - 命令列介面層

此模組提供命令列介面相關功能:
- parser.py: 參數解析
- commands.py: 命令處理

向後相容性:
- Re-export deprecated wrappers from commands.py directly
"""

from .parser import build_parser, parse_make_args, parse_batch_args
from .commands import make_command, batch_command

# 為向後相容創建 alias (deprecated wrappers 直接在此定義)


def make(args):
    """Deprecated: Use make_command() instead."""
    import warnings
    warnings.warn(
        "cli.make() is deprecated. Use cli.make_command() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return make_command(args)


def batch(args):
    """Deprecated: Use batch_command() instead."""
    import warnings
    warnings.warn(
        "cli.batch() is deprecated. Use cli.batch_command() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return batch_command(args)


__all__ = [
    "build_parser",
    "parse_make_args",
    "parse_batch_args",
    "make_command",
    "batch_command",
    # Deprecated (for backward compatibility)
    "make",
    "batch",
]
