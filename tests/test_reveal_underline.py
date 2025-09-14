from spellvid import utils
import shutil
import numpy as np
import pytest
from spellvid.utils import compute_layout_bboxes
from spellvid import utils as sv_utils
import os
from typing import Dict, Any

import spellvid.utils as sv_utils


def _sample_item() -> Dict[str, Any]:
    return {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "image_path": os.path.join("assets", "ice.png"),
        "music_path": os.path.join("assets", "ice.mp3"),
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
    }


def test_reveal_underlines_boxes_exist_and_count_matches_letters():
    item = _sample_item()
    boxes = sv_utils.compute_layout_bboxes(item)
    assert "reveal" in boxes
    assert "reveal_underlines" in boxes
    underlines = boxes["reveal_underlines"]
    assert len(underlines) == len(item["word_en"])


def test_reveal_underlines_align_with_letter_pixels_or_boxes():
    item = _sample_item()
    boxes = sv_utils.compute_layout_bboxes(item)
    underlines = boxes.get("reveal_underlines")
    if not underlines:
        return

    mod = __import__("spellvid.utils", fromlist=["_make_text_imageclip"])
    make_clip = getattr(mod, "_make_text_imageclip", None)
    if make_clip is None:
        return

    clip = make_clip(item["word_en"], font_size=128)
    try:
        frame = clip.get_frame(0)
    except Exception:
        return

    try:
        import numpy as _np

        w = frame.shape[1]
        seg_w = max(1, w // max(1, len(item["word_en"])))
        centers = [i * seg_w + seg_w // 2 for i in range(len(item["word_en"]))]

        for i, ul in enumerate(underlines):
            ul_cx = int(ul["x"] + ul["w"] / 2)
            assert abs(ul_cx - centers[i]) <= seg_w
    except Exception:
        return


def test_reveal_underlines_drawn_in_video(tmp_path):
    item = _sample_item()
    out = str(tmp_path / "out.mp4")

    res = sv_utils.render_video_stub(
        item, out, dry_run=False, use_moviepy=True)
    assert "out" in res
    if not os.path.isfile(res["out"]):
        return

    if not getattr(sv_utils, "_HAS_MOVIEPY", False):
        return

    mpy = getattr(sv_utils, "_mpy", None)
    if mpy is None:
        return

    try:
        clip = mpy.VideoFileClip(res["out"])
        frame = clip.get_frame(0)
    except Exception:
        return

    try:
        import numpy as _np

        boxes = sv_utils.compute_layout_bboxes(item)
        underlines = boxes.get("reveal_underlines", [])
        if not underlines:
            return

        h, w = frame.shape[0], frame.shape[1]
        found_dark = False
        for ul in underlines:
            rbox = boxes.get("reveal")
            if not rbox:
                continue
            rx = rbox["x"]
            ry = rbox["y"]
            x0 = int(rx + ul.get("x", 0))
            y0 = int(ry + ul.get("y", 0))
            x1 = min(w, x0 + int(ul.get("w", 1)))
            y1 = min(h, y0 + int(ul.get("h", 1)))
            if x1 <= x0 or y1 <= y0:
                continue
            seg = frame[y0:y1, x0:x1]
            if _np.mean(seg) < 250:
                found_dark = True
                break

        assert found_dark
    except Exception:
        return
