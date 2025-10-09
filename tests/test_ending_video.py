import os
import pathlib
import shutil
import subprocess

import pytest
import numpy as np
from PIL import Image

from spellvid import utils

ENDING_ASSET = pathlib.Path(__file__).resolve(
).parents[1] / "assets" / "ending.mp4"


def _find_ffmpeg_bin() -> str | None:
    for name in ("ffmpeg", "ffmpeg.exe"):
        path = shutil.which(name)
        if path:
            return path
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    for name in ("ffmpeg", "ffmpeg.exe"):
        candidate = repo_root / "FFmpeg" / name
        if candidate.exists():
            return str(candidate)
    return None


@pytest.mark.skipif(not ENDING_ASSET.exists(), reason="缺少 assets/ending.mp4")
def test_stub_reports_ending_metadata():
    """TCS-ENDING-001: dry-run metadata 包含片尾影片資訊。"""
    item = {
        "letters": "I",
        "word_en": "Ice",
        "word_zh": "冰",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 2,
        "reveal_hold_sec": 1,
    }

    res = utils.render_video_stub(item, "out/ending_stub.mp4", dry_run=True)
    ending_info = res["ending_info"]

    assert ending_info["exists"] is True
    assert ending_info["duration_sec"] > 0.1
    assert ending_info["path"].replace("/", os.sep).endswith(
        os.path.join("assets", "ending.mp4")
    )

    expected_offset = (
        res["entry_offset_sec"]
        + item["countdown_sec"]
        + len(item["word_en"])
        + item["reveal_hold_sec"]
    )
    assert res["ending_offset_sec"] == pytest.approx(
        expected_offset, rel=0.01, abs=0.05)
    assert ending_info["size"] == (1920, 1080)
    assert res["ending_duration_sec"] == pytest.approx(
        ending_info["duration_sec"], rel=0.05, abs=0.2
    )
    assert res["total_duration_sec"] == pytest.approx(
        res["ending_offset_sec"] + res["ending_duration_sec"], rel=0.01, abs=0.2
    )


@pytest.mark.skipif(not ENDING_ASSET.exists(), reason="缺少 assets/ending.mp4")
@pytest.mark.skipif(not getattr(utils, "_HAS_MOVIEPY", False), reason="缺少 MoviePy")
def test_moviepy_appends_ending_clip(monkeypatch, tmp_path):
    """TCS-ENDING-001: 實際渲染時會拼接片尾影片。"""
    monkeypatch.setenv("SPELLVID_DEBUG_SKIP_WRITE", "1")

    item = {
        "letters": "N",
        "word_en": "Ending",
        "word_zh": "尾",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
    }

    out_path = tmp_path / "ending_moviepy.mp4"
    res = utils.render_video_moviepy(item, str(out_path), dry_run=False)
    ending_info = res["ending_info"]

    if ending_info.get("loaded") is not True:
        pytest.skip("片尾影片無法載入，可能缺少編碼器")

    assert ending_info["duration_sec"] > 0.1

    expected_offset = (
        res["entry_offset_sec"]
        + item["countdown_sec"]
        + len(item["word_en"])
        + item["reveal_hold_sec"]
    )
    assert res["ending_offset_sec"] == pytest.approx(
        expected_offset, rel=0.05, abs=0.3)
    assert res["ending_duration_sec"] == pytest.approx(
        ending_info["duration_sec"], rel=0.05, abs=0.3
    )
    assert ending_info.get("size") == (1920, 1080)
    assert res["total_duration_sec"] == pytest.approx(
        res["ending_offset_sec"] + res["ending_duration_sec"], rel=0.05, abs=0.3
    )


@pytest.mark.skipif(not ENDING_ASSET.exists(), reason="缺少 assets/ending.mp4")
@pytest.mark.skipif(not getattr(utils, "_HAS_MOVIEPY", False), reason="缺少 MoviePy")
def test_moviepy_ending_no_letterbox(monkeypatch, tmp_path):
    ffmpeg_bin = _find_ffmpeg_bin()
    if not ffmpeg_bin:
        pytest.skip("缺少 ffmpeg")

    item = {
        "letters": "F",
        "word_en": "Full",
        "word_zh": "滿",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 2,
        "reveal_hold_sec": 1,
    }

    out_path = tmp_path / "ending_fullscreen.mp4"
    res = utils.render_video_moviepy(item, str(out_path), dry_run=False)
    ending_info = res["ending_info"]

    if ending_info.get("loaded") is not True:
        pytest.skip("片尾影片未載入，可能缺少編碼器")

    frame_path = tmp_path / "ending_last.png"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-sseof",
        "-0.2",
        "-i",
        str(out_path),
        "-frames:v",
        "1",
        str(frame_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)

    arr = np.asarray(Image.open(frame_path).convert("RGB"))
    gray = arr.mean(axis=2)
    mask = gray > 15.0
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    assert rows.size > 0 and cols.size > 0, "偵測不到片尾畫面內容"
    assert rows[0] <= 5 and cols[0] <= 5, "片尾畫面仍有明顯邊框 (前緣)"
    assert rows[-1] >= arr.shape[0] - \
        6 and cols[-1] >= arr.shape[1] - 6, "片尾畫面仍有明顯邊框 (後緣)"


@pytest.mark.skipif(not ENDING_ASSET.exists(), reason="缺少 assets/ending.mp4")
def test_render_video_stub_with_skip_ending_true():
    """T004: 測試 skip_ending=True 時不添加片尾影片。"""
    item = {
        "letters": "T",
        "word_en": "Test",
        "word_zh": "測試",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 2,
        "reveal_hold_sec": 1,
    }

    res = utils.render_video_stub(
        item, "out/test_skip.mp4", dry_run=True, skip_ending=True
    )

    # 當 skip_ending=True 時，ending_duration_sec 應該為 0
    assert res["ending_duration_sec"] == 0.0, "skip_ending=True 時應該跳過片尾"

    # total_duration 應該不包含片尾時長
    expected_main = (
        res["entry_offset_sec"]
        + item["countdown_sec"]
        + len(item["word_en"])
        + item["reveal_hold_sec"]
    )
    assert res["total_duration_sec"] == pytest.approx(
        expected_main, rel=0.01, abs=0.05
    )


@pytest.mark.skipif(not ENDING_ASSET.exists(), reason="缺少 assets/ending.mp4")
def test_render_video_stub_with_skip_ending_false():
    """T005: 測試 skip_ending=False (預設) 時添加片尾影片，確保向後兼容。"""
    item = {
        "letters": "T",
        "word_en": "Test",
        "word_zh": "測試",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 2,
        "reveal_hold_sec": 1,
    }

    # 測試明確傳入 skip_ending=False
    res1 = utils.render_video_stub(
        item, "out/test_with_ending.mp4", dry_run=True, skip_ending=False
    )
    assert res1["ending_duration_sec"] > 0.1, "skip_ending=False 時應該包含片尾"

    # 測試預設行為（不傳入 skip_ending 參數）
    res2 = utils.render_video_stub(item, "out/test_default.mp4", dry_run=True)
    assert res2["ending_duration_sec"] > 0.1, "預設應該包含片尾（向後兼容）"

    # 兩者應該有相同的片尾時長
    assert res1["ending_duration_sec"] == pytest.approx(
        res2["ending_duration_sec"], rel=0.01, abs=0.05
    )
