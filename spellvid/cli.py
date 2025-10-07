import argparse
import os
from . import utils


def make(args: argparse.Namespace) -> int:
    item = {
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
    }
    out = args.out
    res = utils.render_video_stub(
        item,
        out,
        dry_run=args.dry_run,
        use_moviepy=getattr(args, "use_moviepy", False),
    )
    print(res)
    return 0 if res.get("status") in ("ok", "dry-run") else 1


def batch(args: argparse.Namespace) -> int:
    data = utils.load_json(args.json)
    errors = utils.validate_schema(data)
    if errors:
        for e in errors:
            print("SCHEMA-ERROR:", e)
        return 2
    summary = {"ok": 0, "skipped": 0, "errors": []}
    output_paths = []  # Collect successful output paths for concatenation
    
    for item in data:
        if "letters_as_image" not in item:
            item["letters_as_image"] = getattr(args, "letters_as_image", True)
        assets = utils.check_assets(item)
        if not assets["image_exists"]:
            print("WARNING: image missing for", item.get("word_en"))
        if assets.get("letters_mode") == "image" and assets.get("letters_missing"):
            details = assets.get("letters_missing_details") or []
            if details:
                for detail in details:
                    name = detail.get("filename") or detail.get("char")
                    path = detail.get("path")
                    word = item.get("word_en")
                    if path:
                        print(f"WARNING: letters asset missing {name} at {path} for {word}")
                    else:
                        print(f"WARNING: letters asset missing {name} for {word}")
            else:
                for name in assets.get("letters_missing", []):
                    print("WARNING: letters asset missing", name, "for", item.get("word_en"))
        out_path = os.path.join(args.outdir, f"{item['word_en']}.mp4")
        if "progress_bar" not in item:
            item["progress_bar"] = getattr(args, "progress_bar", True)
        if "timer_visible" not in item:
            item["timer_visible"] = getattr(args, "timer_visible", True)
        if "entry_hold_sec" not in item:
            item["entry_hold_sec"] = getattr(args, "entry_hold", 0.0)

        try:
            res = utils.render_video_stub(
                item,
                out_path,
                dry_run=args.dry_run,
                use_moviepy=getattr(args, "use_moviepy", False),
            )
            if res.get("status") == "ok":
                summary["ok"] += 1
                output_paths.append(out_path)  # Track successful outputs
            else:
                summary["skipped"] += 1
        except Exception as e:
            summary["errors"].append(str(e))
    
    # If --out-file is specified and we have successful outputs, concatenate them
    out_file = getattr(args, "out_file", None)
    if out_file and output_paths and not args.dry_run:
        print(f"\nConcatenating {len(output_paths)} videos into {out_file}...")
        # D4 Decision: Audio fade-in is now enabled by default (Phase 3)
        # Can be disabled with --no-audio-fadein flag
        apply_audio_fadein = not getattr(args, "no_audio_fadein", False)
        concat_result = utils.concatenate_videos_with_transitions(
            output_paths,
            out_file,
            fade_in_duration=getattr(args, "fade_in_duration", None),
            apply_audio_fadein=apply_audio_fadein,
        )
        
        if concat_result.get("status") == "ok":
            print(f"✓ Concatenation successful: {out_file}")
            print(f"  - Total clips: {concat_result.get('clips_count', 0)}")
            print(f"  - Total duration: {concat_result.get('total_duration', 0):.2f}s")
            summary["concatenated"] = True
            summary["concat_output"] = out_file
        else:
            print(f"✗ Concatenation failed: {concat_result.get('message', 'Unknown error')}")
            summary["concat_error"] = concat_result.get("message")
            return 3  # Return error code for concatenation failure
    
    print(summary)
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="spellvid")
    sub = p.add_subparsers(dest="cmd")

    p_make = sub.add_parser("make")
    p_make.add_argument("--letters")
    p_make.add_argument("--word-en", dest="word_en")
    p_make.add_argument("--word-zh", dest="word_zh")
    p_make.add_argument("--image", dest="image")
    p_make.add_argument("--music", dest="music")
    p_make.add_argument("--countdown", type=int, dest="countdown", default=10)
    p_make.add_argument(
        "--reveal-hold", type=int, dest="reveal_hold", default=5
    )
    p_make.add_argument(
        "--entry-hold",
        type=float,
        dest="entry_hold",
        default=0.0,
        help="seconds to hold after entry video before main timeline",
    )
    p_make.add_argument("--out", dest="out", default="out/output.mp4")
    p_make.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_make.add_argument(
        "--progress-bar",
        dest="progress_bar",
        action="store_true",
        help="enable bottom progress bar (default)",
    )
    p_make.add_argument(
        "--no-progress-bar",
        dest="progress_bar",
        action="store_false",
        help="disable bottom progress bar overlay",
    )
    p_make.add_argument(
        "--timer-visible",
        dest="timer_visible",
        action="store_true",
        help="show countdown timer (default)",
    )
    p_make.add_argument(
        "--hide-timer",
        dest="timer_visible",
        action="store_false",
        help="hide countdown timer overlay",
    )
    p_make.add_argument(
        "--letters-as-image",
        dest="letters_as_image",
        action="store_true",
        help="render top-left letters using image assets (default)",
    )
    p_make.add_argument(
        "--no-letters-as-image",
        dest="letters_as_image",
        action="store_false",
        help="render top-left letters using text fallback",
    )
    p_make.set_defaults(progress_bar=True, timer_visible=True, letters_as_image=True)

    p_make.add_argument(
        "--use-moviepy", action="store_true", dest="use_moviepy"
    )

    p_batch = sub.add_parser("batch")
    p_batch.add_argument("--json")
    p_batch.add_argument("--outdir", default="out")
    p_batch.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_batch.add_argument(
        "--entry-hold",
        type=float,
        dest="entry_hold",
        default=0.0,
        help="seconds to hold after entry video before main timeline",
    )
    p_batch.add_argument(
        "--progress-bar",
        dest="progress_bar",
        action="store_true",
        help="enable bottom progress bar (default)",
    )
    p_batch.add_argument(
        "--no-progress-bar",
        dest="progress_bar",
        action="store_false",
        help="disable bottom progress bar overlay",
    )
    p_batch.add_argument(
        "--timer-visible",
        dest="timer_visible",
        action="store_true",
        help="show countdown timer (default)",
    )
    p_batch.add_argument(
        "--hide-timer",
        dest="timer_visible",
        action="store_false",
        help="hide countdown timer overlay",
    )
    p_batch.add_argument(
        "--letters-as-image",
        dest="letters_as_image",
        action="store_true",
        help="render top-left letters using image assets (default)",
    )
    p_batch.add_argument(
        "--no-letters-as-image",
        dest="letters_as_image",
        action="store_false",
        help="render top-left letters using text fallback",
    )
    p_batch.set_defaults(progress_bar=True, timer_visible=True, letters_as_image=True)

    p_batch.add_argument(
        "--out-file",
        dest="out_file",
        default=None,
        help="concatenate all videos into a single output file (with transitions)",
    )
    
    # Phase 3: Transition effect customization parameters
    p_batch.add_argument(
        "--fade-out-duration",
        type=float,
        dest="fade_out_duration",
        default=None,
        help="custom fade-out duration in seconds (default: 3.0)",
    )
    
    p_batch.add_argument(
        "--fade-in-duration",
        type=float,
        dest="fade_in_duration",
        default=None,
        help="custom fade-in duration in seconds (default: 1.0)",
    )
    
    p_batch.add_argument(
        "--no-audio-fadein",
        dest="no_audio_fadein",
        action="store_true",
        help="disable audio fade-in (video will still fade in, but audio starts immediately)",
    )
    
    p_batch.add_argument(
        "--use-moviepy", action="store_true", dest="use_moviepy"
    )

    return p


def main(argv=None):
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
