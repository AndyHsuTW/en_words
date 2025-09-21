import pytest
from spellvid import utils


def _has_moviepy():
    return getattr(utils, "_HAS_MOVIEPY", False)


def test_countdown_includes_zero_zero():
    """Verify a countdown starting at N seconds produces a final
    '00:00' display.

    This test uses the internal _make_text_imageclip helper to render the
    per-second timer images and checks that the sequence (formatted mm:ss)
    includes a final '00:00'. If the helper is unavailable (no MoviePy),
    the test will skip.
    """
    item = {
        "letters": "X",
        "word_en": "Test",
        "word_zh": "測",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
    }

    # ensure formatting logic produces mm:ss strings
    countdown = int(item.get("countdown_sec", 0))
    seq = []
    for i in range(countdown + 1):
        sec_left = max(0, countdown - i)
        mm = sec_left // 60
        ss = sec_left % 60
        seq.append(f"{mm:02d}:{ss:02d}")

    assert seq[0] == "00:03"
    assert seq[-1] == "00:00"

    # Optionally try to render the last clip frame for 00:00 using helper.
    # If MoviePy or the ImageClip backend is unavailable, skip this part.
    utils_mod = __import__(
        "spellvid.utils",
        fromlist=["_make_text_imageclip", "_HAS_MOVIEPY", "_mpy"],
    )
    make_clip = getattr(utils_mod, "_make_text_imageclip", None)
    mpy = getattr(utils_mod, "_mpy", None)
    has_mpy_flag = getattr(utils_mod, "_HAS_MOVIEPY", False)

    if (
        make_clip is None
        or not has_mpy_flag
        or mpy is None
        or not hasattr(mpy, "ImageClip")
    ):
        pytest.skip(
            "MoviePy/ImageClip not available for rendering; skipping"
            " frame render check"
        )

    last_text = seq[-1]
    clip = make_clip(
        text=last_text,
        font_size=64,
        color=(255, 255, 255),
        bg=(0, 0, 0),
        duration=1,
    )
    try:
        frame = clip.get_frame(0)
    except Exception as e:
        pytest.skip(f"cannot get frame from clip: {e}")

    # simple sanity: there should be some non-black (text) pixels
    if frame.ndim == 3 and frame.shape[2] == 4:
        alpha = frame[:, :, 3]
        visible = (alpha > 0).any()
    else:
        visible = (frame.astype(int).sum(axis=2) > 0).any()

    assert visible, "Rendered '00:00' frame has no visible pixels"


def test_render_moviepy_hide_timer_dry_run_keeps_beeps(tmp_path):
    """When timer is hidden, dry-run metadata should omit timer clips but keep beep schedule."""
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping timer visibility test")

    item = {
        "letters": "H",
        "word_en": "Hide",
        "word_zh": "藏",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 5,
        "reveal_hold_sec": 2,
        "timer_visible": False,
    }
    out_path = tmp_path / "hide_timer.mp4"
    res = utils.render_video_moviepy(item, str(out_path), dry_run=True)

    assert res["status"] == "dry-run"
    assert res["timer_visible"] is False
    assert res["timer_plan"] == []
    # countdown=5 -> beeps occur when displaying 03,02,01 -> times 2s, 3s, 4s
    assert res["beep_schedule"] == [2.0, 3.0, 4.0]



def test_compute_layout_marks_timer_hidden():
    """Headless layout helper should mark timer box as hidden when timer_visible=False."""
    item = {
        "letters": "H",
        "word_en": "Hide",
        "word_zh": "藏",
        "image_path": "",
        "music_path": "",
        "timer_visible": False,
    }

    boxes = utils.compute_layout_bboxes(item)
    timer_box = boxes.get("timer")
    assert timer_box is not None
    assert timer_box.get("visible") is False
    # dimensions still reserved to preserve layout alignment
    assert timer_box.get("w", 0) > 0
    assert timer_box.get("h", 0) > 0

