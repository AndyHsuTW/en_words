from spellvid import utils


def test_video_does_not_overlap_reveal_box(tmp_path):
    """Ensure the computed/used background box does not overlap the reveal box.

    Reproduces the reported bug where a video background can overlap the bottom
    reveal (word) area. We check layout bboxes from
    `compute_layout_bboxes` and also the renderer placement when available.
    """
    # create a tiny placeholder mp4 (reuse helper if present)
    bg_mp4 = tmp_path / "bg.mp4"
    utils._create_placeholder_mp4_with_ffmpeg(str(bg_mp4))

    # small item using the video as the `image` field
    item = {
        "letters": "T t",
        "word_en": "Test",
        "word_zh": "測試",
        "image_path": str(bg_mp4),
        # use short countdown/reveal so output is small
        "countdown": 1,
        "reveal_time": 0.5,
        "reveal_hold": 0.5,
    }

    # get the computed layout boxes (deterministic; independent of moviepy)
    boxes = utils.compute_layout_bboxes(item)

    # compute_layout_bboxes returns 'reveal' and related metadata
    reveal_box = boxes.get("reveal")
    assert (
        reveal_box is not None
    ), "compute_layout_bboxes did not return reveal"

    # helper to detect rectangle intersection; accept dict or tuple/list
    def rects_intersect(a, b):
        ax, ay, aw, ah = a
        if isinstance(b, dict):
            bx = int(b.get("x", 0))
            by = int(b.get("y", 0))
            bw = int(b.get("w", 0))
            bh = int(b.get("h", 0))
        else:
            bx, by, bw, bh = b
        no_overlap = (
            ax + aw <= bx
            or bx + bw <= ax
            or ay + ah <= by
            or by + bh <= ay
        )
        return not no_overlap

    # We'll validate using the renderer placement below; compute_layout_bboxes
    # provides the reveal_box which we use as the authoritative bottom area.

    # Run the moviepy renderer in debug-snapshot mode to avoid writing
    # a full mp4; the renderer will return bg_placement in its metadata.
    out = tmp_path / "out.mp4"
    import os as _os
    _os.environ["SPELLVID_DEBUG_SKIP_WRITE"] = "1"
    result = utils.render_video_moviepy(item, str(out), dry_run=False)
    _os.environ.pop("SPELLVID_DEBUG_SKIP_WRITE", None)

    # If renderer provided bg placement, check coordinates
    used = result.get("bg_used", False)
    assert used, "Renderer did not use background video"
    placement = result.get("bg_placement")
    # if placement present, it should also not overlap reveal_box
    if placement:
        px, py, pw, ph = placement
        assert not rects_intersect((px, py, pw, ph), reveal_box), (
            "Rendered background placement "
            f"{placement} overlaps reveal box {reveal_box}"
        )
