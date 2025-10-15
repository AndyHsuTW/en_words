"""CLI 命令處理器模組

此模組負責將 CLI 參數委派給 application 層服務。
遵循薄 CLI 層原則,不包含業務邏輯。
"""

import argparse
import sys
from typing import List
from pathlib import Path

from ..shared.types import VideoConfig
from ..shared.validation import load_json
from ..application.video_service import render_video
from ..application.batch_service import render_batch
from ..application.resource_checker import check_assets


def make_command(args: argparse.Namespace) -> int:
    """處理 make 命令 - 生成單支視頻

    此函數將 CLI 參數轉換為 VideoConfig,並委派給 video_service。

    Args:
        args: argparse 解析後的 Namespace 物件

    Returns:
        exit code: 0 成功, 非 0 失敗

    Example:
        $ python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰
    """
    try:
        # 轉換參數為 VideoConfig
        config = VideoConfig(
            letters=args.letters,
            word_en=args.word_en,
            word_zh=args.word_zh,
            image_path=args.image,
            music_path=args.music,
            countdown_sec=args.countdown,
            reveal_hold_sec=args.reveal_hold,
            entry_hold_sec=args.entry_hold,
            timer_visible=args.timer_visible,
            progress_bar=args.progress_bar,
            letters_as_image=args.letters_as_image,
        )

        # 檢查資源 (dry-run 或實際渲染都需要)
        assets_result = check_assets(config)

        # 顯示資源檢查結果
        image_exists = assets_result.get("image", {}).get("exists")
        if config.image_path and not image_exists:
            print(
                f"WARNING: Image not found: {config.image_path}",
                file=sys.stderr
            )
        music_exists = assets_result.get("music", {}).get("exists")
        if config.music_path and not music_exists:
            print(
                f"WARNING: Music not found: {config.music_path}",
                file=sys.stderr
            )

        # 呼叫 video_service
        result = render_video(
            config=config,
            output_path=args.out,
            dry_run=args.dry_run,
            skip_ending=False,  # make 命令單支視頻包含 ending
            composer=None  # 使用預設 composer
        )

        # 輸出結果
        if result.get("success"):
            status = "dry-run" if args.dry_run else "rendered"
            print(f"[OK] Video {status} successfully")
            print(f"  Duration: {result['duration']:.2f}s")
            print(f"  Output: {result['output_path']}")
            return 0
        else:
            print("[FAIL] Video generation failed", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: Invalid parameter - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def batch_command(args: argparse.Namespace) -> int:
    """處理 batch 命令 - 批次生成多支視頻

    此函數載入 JSON 配置,轉換為 VideoConfig 列表,並委派給 batch_service。

    Args:
        args: argparse 解析後的 Namespace 物件

    Returns:
        exit code: 0 全部成功, 非 0 部分/全部失敗

    Example:
        $ python -m spellvid.cli batch --json config.json --outdir out/
    """
    try:
        # 載入與驗證 JSON
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"ERROR: JSON file not found: {args.json}", file=sys.stderr)
            return 1

        data = load_json(str(json_path))

        # 驗證資料必須是列表
        if not isinstance(data, list):
            print("ERROR: JSON must be an array of items", file=sys.stderr)
            return 2

        if len(data) == 0:
            print("ERROR: JSON array is empty", file=sys.stderr)
            return 2

        # 轉換為 VideoConfig 列表
        configs: List[VideoConfig] = []
        for item in data:
            # 套用全域參數 (如果 JSON 中沒有指定)
            if "letters_as_image" not in item:
                item["letters_as_image"] = args.letters_as_image
            if "progress_bar" not in item:
                item["progress_bar"] = args.progress_bar
            if "timer_visible" not in item:
                item["timer_visible"] = args.timer_visible
            if "entry_hold_sec" not in item:
                item["entry_hold_sec"] = args.entry_hold

            config = VideoConfig(
                letters=item["letters"],
                word_en=item["word_en"],
                word_zh=item["word_zh"],
                image_path=item.get("image_path"),
                music_path=item.get("music_path"),
                countdown_sec=item.get("countdown_sec", 10),
                reveal_hold_sec=item.get("reveal_hold_sec", 5),
                entry_hold_sec=item.get("entry_hold_sec", 0.0),
                timer_visible=item.get("timer_visible", True),
                progress_bar=item.get("progress_bar", True),
                letters_as_image=item.get("letters_as_image", True),
            )
            configs.append(config)

        # 檢查資源 (顯示警告,但不中斷)
        for i, config in enumerate(configs):
            assets_result = check_assets(config)
            image_ok = assets_result.get("image", {}).get("exists")
            if config.image_path and not image_ok:
                msg = f"WARNING: Image missing for {config.word_en}"
                print(f"{msg}: {config.image_path}", file=sys.stderr)
            music_ok = assets_result.get("music", {}).get("exists")
            if config.music_path and not music_ok:
                msg = f"WARNING: Music missing for {config.word_en}"
                print(f"{msg}: {config.music_path}", file=sys.stderr)

        # 呼叫 batch_service
        result = render_batch(
            configs=configs,
            output_dir=args.outdir,
            dry_run=args.dry_run,
            entry_hold=args.entry_hold,
            skip_ending_per_video=True  # 批次模式:只有最後一支有 ending
        )

        # 輸出結果摘要
        print("\n" + "="*60)
        print("Batch Processing Summary:")
        print(f"  Total: {result['total']}")
        print(f"  Success: {result['success']}")
        print(f"  Failed: {result['failed']}")
        print("="*60)

        # 如果有失敗,顯示失敗詳情
        if result["failed"] > 0:
            print("\nFailed items:", file=sys.stderr)
            for item in result["results"]:
                if not item.get("success", False):
                    word = item.get("config", {}).get("word_en", "unknown")
                    error = item.get("error", "Unknown error")
                    print(f"  - {word}: {error}", file=sys.stderr)

        # TODO: 處理 --out-file 串接功能 (需要 concatenate_videos 實作)
        if hasattr(args, "out_file") and args.out_file and not args.dry_run:
            msg = "Video concatenation not yet implemented in new architecture"
            print(f"\nWARNING: {msg}", file=sys.stderr)

        # 回傳 exit code
        return 0 if result["failed"] == 0 else 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Unexpected error - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
