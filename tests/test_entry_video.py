import array
import ast
import math
import os
import pathlib
import shutil
import subprocess

import pytest

from spellvid import cli, utils


def _find_ff_bin(name: str) -> str | None:
    """Locate ffmpeg/ffprobe executables."""
    env_key = "IMAGEIO_FFMPEG_EXE" if name == "ffmpeg" else None
    if env_key:
        env_path = os.environ.get(env_key)
        if env_path and os.path.isfile(env_path):
            return env_path
    candidate = shutil.which(name)
    if candidate:
        return candidate
    root = pathlib.Path(__file__).resolve().parents[1]
    repo_path = root / "FFmpeg" / (f"{name}.exe")
    if repo_path.is_file():
        return str(repo_path)
    alt_repo = root / "FFmpeg" / name
    if alt_repo.is_file():
        return str(alt_repo)
    return None


def _to_ff_path(exe: str, path: pathlib.Path) -> str:
    abspath = str(path.resolve())
    if exe.lower().endswith(".exe") and os.name != "nt":
        try:
            proc = subprocess.run(
                ["wslpath", "-w", abspath],
                capture_output=True,
                text=True,
                check=True,
            )
            converted = proc.stdout.strip()
            if converted:
                return converted
        except Exception:
            pass
    return abspath


def _probe_duration(ffprobe: str, path: pathlib.Path) -> float:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        _to_ff_path(ffprobe, path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise AssertionError(
            f"ffprobe 無法讀取 {path}: {proc.stderr.strip()}"
        )
    return float(proc.stdout.strip())


def _measure_audio_rms(
    ffmpeg: str, path: pathlib.Path, *, duration: float | None = None
) -> float:
    args = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        _to_ff_path(ffmpeg, path),
        "-map",
        "0:a:0",
        "-ac",
        "1",
        "-ar",
        "16000",
    ]
    if duration is not None:
        args += ["-t", f"{duration:.3f}"]
    args += ["-f", "s16le", "pipe:1"]
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", "ignore")
        if "matches no streams" in stderr:
            return 0.0
        raise AssertionError(
            f"ffmpeg 萃取音訊失敗 ({path}): {stderr.strip()}"
        )
    pcm = proc.stdout
    if not pcm:
        return 0.0
    samples = array.array("h")
    samples.frombytes(pcm)
    if not samples:
        return 0.0
    mean_sq = sum(int(s) ** 2 for s in samples) / len(samples)
    return math.sqrt(mean_sq) / 32768.0


def test_entry_stub_metadata_reflects_hold():
    """TCS-ENTRY-002: 確認開頭影片停留秒數納入總前置時間。"""
    hold = 1.25
    item = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰塊",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 5,
        "reveal_hold_sec": 2,
        "entry_hold_sec": hold,
    }

    res = utils.render_video_stub(item, "out/entry_stub.mp4", dry_run=True)
    entry_info = res["entry_info"]

    assert entry_info["path"].replace("/", os.sep).endswith(
        os.path.join("assets", "entry.mp4")
    )
    assert entry_info["exists"] is True
    assert res["entry_hold_sec"] == pytest.approx(hold)

    duration = entry_info.get("duration_sec")
    expected_offset = hold + (duration or 0.0)
    assert res["entry_offset_sec"] == pytest.approx(
        expected_offset, rel=0.05, abs=0.2)

    for ts in res["beep_schedule_timeline"]:
        assert ts >= res["entry_offset_sec"]


def test_cli_make_respects_entry_hold_flag(tmp_path, capsys):
    """TCS-CLI-ENTRY-001: CLI `--entry-hold` 在 dry-run 中正確反映。"""
    parser = cli.build_parser()
    out_path = tmp_path / "cli_entry.mp4"
    args = parser.parse_args(
        [
            "make",
            "--letters",
            "A",
            "--word-en",
            "Alpha",
            "--word-zh",
            "阿法",
            "--image",
            "",
            "--music",
            "",
            "--entry-hold",
            "1.5",
            "--dry-run",
            "--out",
            str(out_path),
        ]
    )

    rc = cli.make(args)
    assert rc == 0

    captured = capsys.readouterr()
    payload = ast.literal_eval(captured.out.strip())
    assert payload["entry_hold_sec"] == pytest.approx(1.5)
    entry_info = payload["entry_info"]
    assert entry_info["exists"] is True
    assert entry_info["hold_sec"] == pytest.approx(1.5)


@pytest.mark.skipif(not utils._HAS_MOVIEPY, reason="MoviePy 未安裝")
def test_moviepy_entry_clip_offsets(monkeypatch, tmp_path):
    """TCS-ENTRY-001: MoviePy 合成含開頭影片與停留秒數。"""
    monkeypatch.setenv("SPELLVID_DEBUG_SKIP_WRITE", "1")
    snapshot_path = None
    item = {
        "letters": "E",
        "word_en": "Entry",
        "word_zh": "入",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 3,
        "reveal_hold_sec": 1,
        "entry_hold_sec": 1.2,
    }

    out_path = tmp_path / "entry_moviepy.mp4"
    try:
        res = utils.render_video_moviepy(item, str(out_path), dry_run=False)
        snapshot_path = res.get("snapshot")
        if res["entry_info"].get("loaded") is not True:
            pytest.skip("開頭影片未載入，可能缺少 FFmpeg/codec")

        entry_info = res["entry_info"]
        entry_duration = entry_info.get("duration_sec") or 0.0
        expected_offset = entry_duration + item["entry_hold_sec"]
        assert res["entry_offset_sec"] == pytest.approx(
            expected_offset, rel=0.05, abs=0.2
        )

        assert res["beep_schedule_timeline"]
        for rel, abs_ts in zip(res["beep_schedule"], res["beep_schedule_timeline"]):
            assert abs_ts == pytest.approx(
                res["entry_offset_sec"] + rel, rel=0.02, abs=0.1
            )

        total_expected = (
            res["entry_offset_sec"]
            + item["countdown_sec"]
            + len(item["word_en"])
            + item["reveal_hold_sec"]
        )
        assert res["total_duration_sec"] == pytest.approx(
            total_expected, rel=0.05, abs=0.5
        )
    finally:
        if snapshot_path and os.path.exists(snapshot_path):
            os.remove(snapshot_path)


def test_entry_clip_audio_present_in_sample_render():
    """TCS-ENTRY-AUDIO-001: 驗證開頭影片音訊應在輸出影片開頭播放。"""
    ffmpeg = _find_ff_bin("ffmpeg")
    ffprobe = _find_ff_bin("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("ffmpeg/ffprobe 未就緒，略過音訊驗證")

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    primary_entry = repo_root / "assets" / "entry.mp4"
    fallback_entry = repo_root / "assets" / "entry_with_music.mp4"
    sample_output = repo_root / "out" / "test-entry01.mp4"

    if not sample_output.exists():
        pytest.skip("缺少 out/test-entry01.mp4，請先執行 scripts/render_example.ps1")

    entry_candidates = [p for p in (
        primary_entry, fallback_entry) if p.exists()]
    if not entry_candidates:
        pytest.skip("找不到任何開頭影片資產")

    ref_entry_path = None
    ref_duration = None
    ref_rms = 0.0
    for candidate in entry_candidates:
        duration = _probe_duration(ffprobe, candidate)
        rms = _measure_audio_rms(
            ffmpeg, candidate, duration=min(duration, 5.0))
        if rms > 0.001:
            ref_entry_path = candidate
            ref_duration = min(duration, 5.0)
            ref_rms = rms
            break
    if ref_entry_path is None:
        pytest.fail("開頭影片資產未提供可偵測的音訊")

    sample_rms = _measure_audio_rms(
        ffmpeg, sample_output, duration=ref_duration)
    assert sample_rms >= ref_rms * 0.5, (
        "輸出影片開頭音量明顯低於原始 entry 影片，"
        f"entry={ref_rms:.4f}, output={sample_rms:.4f}, 使用來源: {ref_entry_path.name}"
    )
