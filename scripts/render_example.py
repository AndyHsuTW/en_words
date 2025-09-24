"""Small runner to call spellvid.render_video_stub.

Example: python scripts/render_example.py --use-moviepy
"""
import argparse
import os
import sys
import json
import importlib.util
import tempfile
import shutil
import subprocess

# load spellvid.utils by path to avoid import issues when running from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils_path = os.path.join(ROOT, 'spellvid', 'utils.py')
spec = importlib.util.spec_from_file_location('spellvid.utils', utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)  # type: ignore
render_video_stub = utils.render_video_stub


parser = argparse.ArgumentParser()
parser.add_argument("--json", dest="json_path", default="config.json",
                    help="path to JSON config (array of items)")
parser.add_argument("--out-dir", dest="out_dir", default="out",
                    help="output directory for generated videos")
parser.add_argument(
    "--out-file",
    dest="out_file",
    default=None,
    help=(
        "path to output file (overrides naming). "
        "If a relative filename is given, it will be placed inside "
        "--out-dir. Only supported when JSON has a single item."
    ),
)
parser.add_argument("--use-moviepy", action="store_true")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--hide-timer", dest="timer_visible",
                    action="store_false")
args = parser.parse_args()

os.makedirs(args.out_dir, exist_ok=True)


def sanitize_name(s: str) -> str:
    cleaned = "".join(
        c for c in s if c.isalnum() or c in (' ', '-', '_')
    ).rstrip()
    return cleaned.replace(' ', '_')


if args.json_path and os.path.isfile(args.json_path):
    with open(args.json_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    results = []
    # If --out-file is provided, determine final output path now.
    final_out = None
    if args.out_file:
        final_out = args.out_file
        if not os.path.isabs(final_out) and os.path.dirname(final_out) == '':
            final_out = os.path.join(args.out_dir, final_out)
        if not final_out.lower().endswith('.mp4'):
            final_out = final_out + '.mp4'

    # Helper: try to concat a list of mp4s into final_out using ffmpeg
    # concat demuxer.
    def _concat_mp4s(inputs, dest):
        # inputs: list of absolute paths to mp4 files
        # dest: absolute path to output mp4
        try:
            ffmpeg = (
                os.environ.get('IMAGEIO_FFMPEG_EXE') or shutil.which('ffmpeg')
            )
            if not ffmpeg:
                return False, 'ffmpeg not found'
            with tempfile.TemporaryDirectory() as td:
                listf = os.path.join(td, 'list.txt')
                with open(listf, 'w', encoding='utf-8') as f:
                    for p in inputs:
                        # concat demuxer expects lines like: file 'path'
                        safe = p.replace("'", "'\\''")
                        f.write("file '{}'\n".format(safe))
                cmd = [
                    ffmpeg,
                    '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', listf,
                    '-c', 'copy',
                    dest,
                ]
                # Try copy codecs first (fast). If it fails, fall back
                # to re-encode.
                try:
                    subprocess.run(
                        cmd,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True, None
                except subprocess.CalledProcessError:
                    # re-encode fallback using concat demuxer
                    cmd2 = [
                        ffmpeg,
                        '-y',
                        '-f',
                        'concat',
                        '-safe',
                        '0',
                        '-i',
                        listf,
                        '-c:v',
                        'libx264',
                        '-c:a',
                        'aac',
                        '-pix_fmt',
                        'yuv420p',
                        dest,
                    ]
                    try:
                        subprocess.run(
                            cmd2,
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        return True, None
                    except subprocess.CalledProcessError:
                        # final fallback: use filter_complex concat (re-encode)
                        try:
                            # build inputs args and filter_complex string
                            in_args = []
                            for p in inputs:
                                in_args.extend(['-i', p])
                            # build filter list like:
                            # [0:v:0][0:a:0][1:v:0][1:a:0]...
                            parts = []
                            for i in range(len(inputs)):
                                parts.append(f'[{i}:v:0]')
                                parts.append(f'[{i}:a:0]')
                            fc = ''.join(parts) + (
                                'concat=n=' + str(len(inputs))
                                + ':v=1:a=1[outv][outa]'
                            )
                            cmd3 = [ffmpeg, '-y'] + in_args + [
                                '-filter_complex', fc,
                                '-map', '[outv]',
                                '-map', '[outa]',
                                '-c:v', 'libx264',
                                '-c:a', 'aac',
                                '-pix_fmt', 'yuv420p',
                                dest,
                            ]
                            subprocess.run(
                                cmd3,
                                check=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            return True, None
                        except Exception as e:
                            return False, str(e)
        except Exception as e:
            return False, str(e)

    temp_outputs = []
    try:
        timer_override = args.timer_visible
        for idx, item in enumerate(cfg):
            name = item.get('word_en') or item.get('letters') or f'out_{idx}'
            if timer_override is not None:
                item['timer_visible'] = bool(timer_override)
            if final_out and len(cfg) > 1 and 'entry_enabled' not in item:
                item['entry_enabled'] = (idx == 0)
            # default filename from config
            fname = sanitize_name(name) + '.mp4'
            outp = os.path.join(args.out_dir, fname)

            # If final_out is specified and there's more than one item,
            # render to a temp file
            if final_out and len(cfg) > 1:
                td = tempfile.mkdtemp(prefix='spellvid_')
                outp = os.path.join(td, f'{idx}_{fname}')

            # If user provided --out-file and only a single item, use it
            # as the destination
            if final_out and len(cfg) == 1:
                outp = final_out

            print('rendering ->', outp)
            res = render_video_stub(
                item,
                outp,
                dry_run=args.dry_run,
                use_moviepy=args.use_moviepy,
            )
            print(json.dumps(res, ensure_ascii=False))
            results.append(res)
            # record successful temp outputs only (skip failed renders)
            if final_out and len(cfg) > 1:
                # dry-run: still record the planned temp output location so
                # the dry-run printout can show the paths
                if args.dry_run:
                    temp_outputs.append((td, outp))
                else:
                    # only append if the renderer produced the file
                    if os.path.isfile(outp):
                        temp_outputs.append((td, outp))
                    else:
                        # remove temp dir immediately if render failed
                        try:
                            shutil.rmtree(td)
                        except Exception:
                            pass

        # If final_out requested and multiple items, concat temp outputs
        if final_out and len(cfg) > 1:
            # collect rendered files (absolute paths) that actually exist
            inputs = []
            for (_td, p) in temp_outputs:
                if os.path.isfile(p):
                    inputs.append(os.path.abspath(p))
            print('would concatenate', inputs, '->', final_out)
            if not args.dry_run:
                # require ffmpeg to be present for concatenation
                ffmpeg = os.environ.get('IMAGEIO_FFMPEG_EXE')
                if not ffmpeg:
                    ffmpeg = shutil.which('ffmpeg')
                if not ffmpeg:
                    ffmpeg = os.environ.get('FFMPEG_PATH')
                if not ffmpeg:
                    print('error: ffmpeg not found.', file=sys.stderr)
                    print('Cannot concatenate videos without ffmpeg.',
                          file=sys.stderr)
                    print('Please install ffmpeg or set', file=sys.stderr)
                    print('IMAGEIO_FFMPEG_EXE or', file=sys.stderr)
                    print('FFMPEG_PATH.', file=sys.stderr)
                    # cleanup temp dirs before exiting
                    for (td, _) in temp_outputs:
                        try:
                            shutil.rmtree(td)
                        except Exception:
                            pass
                    raise SystemExit(1)

                if not inputs:
                    print('error: no rendered inputs available', file=sys.stderr)
                    print('for', file=sys.stderr)
                    print('concatenation', file=sys.stderr)
                    for (td, _) in temp_outputs:
                        try:
                            shutil.rmtree(td)
                        except Exception:
                            pass
                    raise SystemExit(1)

                ok, err = _concat_mp4s(inputs, final_out)
                if not ok:
                    print('concat failed:', err, file=sys.stderr)
                    for (td, _) in temp_outputs:
                        try:
                            shutil.rmtree(td)
                        except Exception:
                            pass
                    raise SystemExit(1)
    finally:
        # cleanup temp dirs
        for (td, _) in temp_outputs:
            try:
                shutil.rmtree(td)
            except Exception:
                pass
    print(json.dumps(results, ensure_ascii=False))
else:
    print('no json config provided or file does not exist; nothing to do')
