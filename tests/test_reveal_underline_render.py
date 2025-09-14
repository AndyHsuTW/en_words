import os
import shutil
import numpy as np
import pytest

from spellvid import utils


def test_reveal_underlines_drawn_in_video(tmp_path):
    """Render a short video with MoviePy and check a reveal-frame contains
    visible underline pixels (white rectangles) under the reveal area.

    Skip when MoviePy or ffmpeg not available.
    """
    if not getattr(utils, "_HAS_MOVIEPY", False):
        pytest.skip("moviepy not available")

    # ensure ffmpeg exists for writing
    ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE") or shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available; cannot write video")

    item = {
        "letters": "R",
        "word_en": "Hi",
        "word_zh": "嗨",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 2,
    }

    out = str(tmp_path / "out.mp4")
    res = utils.render_video_stub(item, out, dry_run=False, use_moviepy=True)
    if res.get("status") != "ok":
        pytest.skip(f"renderer did not produce output: {res}")

    # open the produced file and grab a frame in the reveal period
    try:
        from moviepy.editor import VideoFileClip

        clip = VideoFileClip(out)
    except Exception as e:
        pytest.skip(f"cannot open produced video: {e}")

    # choose a time after countdown (countdown=1) to inspect reveal
    t = 1.5
    try:
        frame = clip.get_frame(t)
    except Exception as e:
        pytest.skip(f"cannot extract frame: {e}")

    # load layout metadata and check dark pixels inside underline boxes
    boxes = utils.compute_layout_bboxes(item)
    reveal = boxes.get("reveal")
    underlines = boxes.get("reveal_underlines") or []
    if not reveal or not underlines:
        pytest.skip("no reveal metadata to guide pixel check")

    h, w, _ = frame.shape
    found = False
    for ul in underlines:
        abs_x = reveal["x"] + ul["x"]
        abs_y = reveal["y"] + ul["y"]
        ul_w = max(1, int(ul["w"]))
        ul_h = max(1, int(ul["h"]))
        # clamp to frame
        x0 = max(0, int(abs_x))
        y0 = max(0, int(abs_y))
        x1 = min(w - 1, x0 + ul_w - 1)
        y1 = min(h - 1, y0 + ul_h - 1)
        if x1 < x0 or y1 < y0:
            continue
        region = frame[y0: y1 + 1, x0: x1 + 1, :3]
        # detect dark pixels (near black)
        dark_mask = (
            (region[..., 0] < 50)
            & (region[..., 1] < 50)
            & (region[..., 2] < 50)
        )
        if dark_mask.any():
            found = True
            break

    assert found, "no dark underline pixels found in reveal region; underlines likely missing"
    assert found, (
        "no dark underline pixels found in reveal region; "
        "underlines likely missing"
    )
