import pytest
from spellvid import utils


def _has_moviepy():
    return getattr(utils, "_HAS_MOVIEPY", False)


def test_video_included_in_render(tmp_path):
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping video inclusion test")

    # try to create a tiny mp4 using ffmpeg helper; fallback: skip
    mp4_path = tmp_path / "bg.mp4"
    created = utils._create_placeholder_mp4_with_ffmpeg(str(mp4_path))
    if not created:
        pytest.skip("ffmpeg not available to create test mp4; skipping")

    item = {
        "letters": "V",
        "word_en": "Video",
        "word_zh": "\u56fe\u7247",
        "image_path": str(mp4_path),
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
    }

    out_mp4 = tmp_path / "out.mp4"
    res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
    assert res.get("status") == "ok"
    assert res.get("bg_used") is True
    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 1000
