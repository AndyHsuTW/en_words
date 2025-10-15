"""CLI 參數解析器模組

此模組負責定義所有 CLI 命令的參數結構。
按照新架構,將參數解析邏輯從主 CLI 檔案分離。
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """建立主 ArgumentParser 並註冊所有子命令

    Returns:
        配置完成的 ArgumentParser 實例
    """
    parser = argparse.ArgumentParser(
        prog="spellvid",
        description="視頻教學內容生成工具 - 字母與中文對照視頻製作"
    )

    subparsers = parser.add_subparsers(dest="cmd", help="可用命令")

    # 註冊子命令
    _register_make_command(subparsers)
    _register_batch_command(subparsers)

    return parser


def _register_make_command(subparsers) -> None:
    """註冊 make 子命令的參數

    make 命令用於生成單支視頻。

    Args:
        subparsers: ArgumentParser 的 subparsers 物件
    """
    make_parser = subparsers.add_parser(
        "make",
        help="生成單支視頻"
    )

    # 必要參數
    make_parser.add_argument(
        "--letters",
        required=True,
        help="字母顯示文字 (例如: 'I i')"
    )
    make_parser.add_argument(
        "--word-en",
        dest="word_en",
        required=True,
        help="英文單字 (例如: 'Ice')"
    )
    make_parser.add_argument(
        "--word-zh",
        dest="word_zh",
        required=True,
        help="中文翻譯與注音 (例如: 'ㄅㄧㄥ 冰')"
    )

    # 可選資源參數
    make_parser.add_argument(
        "--image",
        dest="image",
        help="圖片路徑 (PNG/JPG)"
    )
    make_parser.add_argument(
        "--music",
        dest="music",
        help="音樂路徑 (MP3/WAV/M4A)"
    )

    # 時間參數
    make_parser.add_argument(
        "--countdown",
        type=int,
        dest="countdown",
        default=10,
        help="倒數秒數 (預設: 10)"
    )
    make_parser.add_argument(
        "--reveal-hold",
        type=int,
        dest="reveal_hold",
        default=5,
        help="揭示後停留秒數 (預設: 5)"
    )
    make_parser.add_argument(
        "--entry-hold",
        type=float,
        dest="entry_hold",
        default=0.0,
        help="入場影片後停留秒數 (預設: 0.0)"
    )

    # 輸出參數
    make_parser.add_argument(
        "--out",
        dest="out",
        default="out/output.mp4",
        help="輸出檔案路徑 (預設: out/output.mp4)"
    )
    make_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="僅驗證參數與資源,不實際渲染"
    )

    # 視覺元素開關
    make_parser.add_argument(
        "--progress-bar",
        dest="progress_bar",
        action="store_true",
        help="啟用底部進度條 (預設啟用)"
    )
    make_parser.add_argument(
        "--no-progress-bar",
        dest="progress_bar",
        action="store_false",
        help="停用底部進度條"
    )
    make_parser.add_argument(
        "--timer-visible",
        dest="timer_visible",
        action="store_true",
        help="顯示倒數計時器 (預設顯示)"
    )
    make_parser.add_argument(
        "--hide-timer",
        dest="timer_visible",
        action="store_false",
        help="隱藏倒數計時器"
    )
    make_parser.add_argument(
        "--letters-as-image",
        dest="letters_as_image",
        action="store_true",
        help="使用圖片資源渲染字母 (預設啟用)"
    )
    make_parser.add_argument(
        "--no-letters-as-image",
        dest="letters_as_image",
        action="store_false",
        help="使用文字渲染字母"
    )

    # 設定預設值
    make_parser.set_defaults(
        progress_bar=True,
        timer_visible=True,
        letters_as_image=True
    )

    # 實驗性參數
    make_parser.add_argument(
        "--use-moviepy",
        action="store_true",
        dest="use_moviepy",
        help="使用 MoviePy 渲染 (實驗性)"
    )


def _register_batch_command(subparsers) -> None:
    """註冊 batch 子命令的參數

    batch 命令用於批次生成多支視頻。

    Args:
        subparsers: ArgumentParser 的 subparsers 物件
    """
    batch_parser = subparsers.add_parser(
        "batch",
        help="批次生成多支視頻"
    )

    # 必要參數
    batch_parser.add_argument(
        "--json",
        required=True,
        help="JSON 配置檔案路徑"
    )
    batch_parser.add_argument(
        "--outdir",
        default="out",
        help="輸出目錄路徑 (預設: out)"
    )

    # 批次參數
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="僅驗證配置與資源,不實際渲染"
    )
    batch_parser.add_argument(
        "--entry-hold",
        type=float,
        dest="entry_hold",
        default=0.0,
        help="入場影片後停留秒數 (套用到所有視頻, 預設: 0.0)"
    )

    # 視覺元素開關 (套用到所有視頻)
    batch_parser.add_argument(
        "--progress-bar",
        dest="progress_bar",
        action="store_true",
        help="啟用底部進度條 (預設啟用)"
    )
    batch_parser.add_argument(
        "--no-progress-bar",
        dest="progress_bar",
        action="store_false",
        help="停用底部進度條"
    )
    batch_parser.add_argument(
        "--timer-visible",
        dest="timer_visible",
        action="store_true",
        help="顯示倒數計時器 (預設顯示)"
    )
    batch_parser.add_argument(
        "--hide-timer",
        dest="timer_visible",
        action="store_false",
        help="隱藏倒數計時器"
    )
    batch_parser.add_argument(
        "--letters-as-image",
        dest="letters_as_image",
        action="store_true",
        help="使用圖片資源渲染字母 (預設啟用)"
    )
    batch_parser.add_argument(
        "--no-letters-as-image",
        dest="letters_as_image",
        action="store_false",
        help="使用文字渲染字母"
    )

    # 設定預設值
    batch_parser.set_defaults(
        progress_bar=True,
        timer_visible=True,
        letters_as_image=True
    )

    # 串接參數
    batch_parser.add_argument(
        "--out-file",
        dest="out_file",
        default=None,
        help="將所有視頻串接成單一輸出檔案 (含轉場效果)"
    )
    batch_parser.add_argument(
        "--fade-out-duration",
        type=float,
        dest="fade_out_duration",
        default=None,
        help="自訂淡出持續時間(秒) (預設: 3.0)"
    )
    batch_parser.add_argument(
        "--fade-in-duration",
        type=float,
        dest="fade_in_duration",
        default=None,
        help="自訂淡入持續時間(秒) (預設: 1.0)"
    )
    batch_parser.add_argument(
        "--no-audio-fadein",
        dest="no_audio_fadein",
        action="store_true",
        help="停用音訊淡入 (視頻仍會淡入,但音訊立即開始)"
    )

    # 實驗性參數
    batch_parser.add_argument(
        "--use-moviepy",
        action="store_true",
        dest="use_moviepy",
        help="使用 MoviePy 渲染 (實驗性)"
    )


def parse_make_args(args: argparse.Namespace) -> dict:
    """從 Namespace 提取 make 命令所需參數並轉換為 dict

    此函數將 argparse.Namespace 轉換為 application 層可用的字典格式。

    Args:
        args: argparse 解析後的 Namespace 物件

    Returns:
        包含 make 命令所需參數的字典

    Example:
        >>> args = parser.parse_args(["make", "--letters", "I i", ...])
        >>> params = parse_make_args(args)
        >>> params["word_en"]
        'Ice'
    """
    return {
        "letters": args.letters,
        "word_en": args.word_en,
        "word_zh": args.word_zh,
        "image_path": args.image,
        "music_path": args.music,
        "countdown_sec": args.countdown,
        "reveal_hold_sec": args.reveal_hold,
        "entry_hold_sec": args.entry_hold,
        "timer_visible": args.timer_visible,
        "progress_bar": args.progress_bar,
        "letters_as_image": args.letters_as_image,
        "out": args.out,
        "dry_run": args.dry_run,
        "use_moviepy": getattr(args, "use_moviepy", False),
    }


def parse_batch_args(args: argparse.Namespace) -> dict:
    """從 Namespace 提取 batch 命令所需參數並轉換為 dict

    此函數將 argparse.Namespace 轉換為 application 層可用的字典格式。

    Args:
        args: argparse 解析後的 Namespace 物件

    Returns:
        包含 batch 命令所需參數的字典

    Example:
        >>> args = parser.parse_args(["batch", "--json", "config.json", ...])
        >>> params = parse_batch_args(args)
        >>> params["json_path"]
        'config.json'
    """
    return {
        "json_path": args.json,
        "outdir": args.outdir,
        "dry_run": args.dry_run,
        "entry_hold": args.entry_hold,
        "progress_bar": args.progress_bar,
        "timer_visible": args.timer_visible,
        "letters_as_image": args.letters_as_image,
        "out_file": getattr(args, "out_file", None),
        "fade_out_duration": getattr(args, "fade_out_duration", None),
        "fade_in_duration": getattr(args, "fade_in_duration", None),
        "no_audio_fadein": getattr(args, "no_audio_fadein", False),
        "use_moviepy": getattr(args, "use_moviepy", False),
    }
