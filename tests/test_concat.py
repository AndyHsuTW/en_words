import json
import os
import subprocess
import shutil
import sys


def _find_ffprobe():
    # prefer repo local FFprobe
    repo_fp = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'FFmpeg', 'ffprobe.exe')
    )
    if os.path.isfile(repo_fp):
        return repo_fp
    # fallback to PATH
    ff = shutil.which('ffprobe')
    return ff


def _duration_seconds(path):
    ffprobe = _find_ffprobe()
    if not ffprobe:
        return None
    cmd = [
        ffprobe,
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        path,
    ]
    out = subprocess.check_output(cmd)
    return float(out.strip())


def test_concat_two_items(tmp_path):
    ffprobe = _find_ffprobe()
    if not ffprobe:
        # skip test when ffprobe not available in environment
        import pytest

        pytest.skip('ffprobe not available; skipping concat integration test')

    # create two simple config items
    cfg = [
        {
            'letters': 'A',
            'word_en': 'One',
            'word_zh': '一',
            'image_path': 'assets/arm.png',
            'music_path': 'assets/arm_20s.mp3',
            'countdown_sec': 1,
            'reveal_hold_sec': 1,
        },
        {
            'letters': 'B',
            'word_en': 'Two',
            'word_zh': '二',
            'image_path': 'assets/ball.png',
            'music_path': 'assets/ball_20s.mp3',
            'countdown_sec': 1,
            'reveal_hold_sec': 1,
        },
    ]

    out_dir = tmp_path / 'out'
    out_dir.mkdir()

    # Render each item individually to determine their durations
    indiv_files = []
    indiv_durs = []
    for i, item in enumerate(cfg):
        single_cfg = [item]
        single_cfg_path = tmp_path / f'cfg_{i}.json'
        with open(single_cfg_path, 'w', encoding='utf-8') as f:
            json.dump(single_cfg, f, ensure_ascii=False)
        out_file = str(out_dir / f'part_{i}.mp4')
        cmd = [
            sys.executable,
            'scripts/render_example.py',
            '--json',
            str(single_cfg_path),
            '--out-dir',
            str(out_dir),
            '--out-file',
            out_file,
        ]
        # try to use moviepy if available; allow script to decide
        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if not os.path.isfile(out_file):
            candidates = list(out_dir.glob('*.mp4'))
            if candidates:
                out_file = str(candidates[-1])
            else:
                raise AssertionError(
                    'No output mp4 produced for single item; stdout='
                    + proc.stdout
                )
        dur = _duration_seconds(out_file)
        assert dur is not None and dur > 0
        indiv_files.append(out_file)
        indiv_durs.append(dur)

    # Now produce the merged output
    merged_cfg_path = tmp_path / 'cfg.json'
    with open(merged_cfg_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    merged_out = str(out_dir / 'merged.mp4')
    cmd = [
        sys.executable,
        'scripts/render_example.py',
        '--json',
        str(merged_cfg_path),
        '--out-dir',
        str(out_dir),
        '--out-file',
        merged_out,
    ]
    proc = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )
    if not os.path.isfile(merged_out):
        candidates = list(out_dir.glob('*.mp4'))
        if candidates:
            merged_out = str(candidates[-1])
        else:
            raise AssertionError(
                'No merged output found; stdout=' + proc.stdout
            )

    merged_dur = _duration_seconds(merged_out)
    assert merged_dur is not None and merged_dur > 0

    expected = sum(indiv_durs)
    # allow reasonable tolerance (1s)
    assert abs(merged_dur - expected) < 1.0, (
        f'expected merged duration ~{expected}s, got {merged_dur}s'
    )
