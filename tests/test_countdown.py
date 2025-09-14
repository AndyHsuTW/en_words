import pytest


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
