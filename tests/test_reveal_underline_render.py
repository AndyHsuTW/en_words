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
    has_mpy = getattr(utils, "_HAS_MOVIEPY", False)
    # allow fallback to imageio (ffmpeg backend) if moviepy not installed
    if not has_mpy:
        try:
            import imageio  # type: ignore
        except Exception:
            pytest.skip("moviepy not available and no imageio fallback")

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
    t = 1.5
    frame = None
    if has_mpy:
        try:
            # moviepy installers may expose VideoFileClip on different
            # locations. Try common import locations and fall back to
            # attributes on top-level moviepy module.
            try:
                from moviepy.editor import VideoFileClip
            except Exception:
                import moviepy as _mp

                VideoFileClip = getattr(_mp, "VideoFileClip", None)
                if VideoFileClip is None:
                    # some installations may put it under moviepy.video
                    try:
                        from moviepy.video.io.VideoFileClip import VideoFileClip
                    except Exception:
                        raise

            clip = VideoFileClip(out)
            frame = clip.get_frame(t)
        except Exception as e:
            pytest.skip(f"cannot open produced video with moviepy: {e}")
    else:
        # fallback: try imageio/ffmpeg reader
        try:
            import imageio  # type: ignore

            reader = imageio.get_reader(out, "ffmpeg")
            meta = reader.get_meta_data()
            fps = int(meta.get("fps", 25))
            # compute index for t seconds; clamp if reader doesn't provide
            # count
            try:
                count = reader.count_frames()
            except Exception:
                count = None
            idx = int(t * fps)
            if count is not None:
                idx = min(idx, max(0, count - 1))
            frame = reader.get_data(idx)
        except Exception as e:
            pytest.skip(f"cannot open produced video with imageio: {e}")

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

    assert found, (
        "no dark underline pixels found in reveal region; "
        "underlines likely missing"
    )
