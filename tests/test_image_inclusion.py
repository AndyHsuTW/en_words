from PIL import Image
import pytest

from spellvid import utils
# import VideoFileClip robustly: some moviepy builds expose it under
# moviepy.editor, others at top-level as moviepy.VideoFileClip.
VideoFileClip = None
try:
    from moviepy.editor import VideoFileClip  # preferred
except Exception:
    try:
        from moviepy import VideoFileClip
    except Exception:
        try:
            import moviepy as _m

            VideoFileClip = getattr(_m, "VideoFileClip", None)
        except Exception:
            VideoFileClip = None


def _has_moviepy():
    return getattr(utils, "_HAS_MOVIEPY", False)


def test_image_included_in_render(tmp_path):
    """Create a small image, render with MoviePy renderer, and assert
    the output video appears to use the image as background.

    This test intentionally exercises `render_video_moviepy` and will be
    skipped if MoviePy is not available. The current repository state
    should cause this test to fail (per task requirement), but we still
    add the test so it exists.
    """
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping image inclusion test")

    # create a simple 200x200 red square image
    img_path = tmp_path / "bg.png"
    img = Image.new("RGB", (200, 200), (255, 0, 0))
    img.save(img_path)

    item = {
        "letters": "B",
        "word_en": "Arm",
        "word_zh": "手臂",
        "image_path": str(img_path),
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
    }

    out_mp4 = tmp_path / "out.mp4"

    # Render real moviepy video; this may raise if ffmpeg not configured
    res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
    assert res.get("status") == "ok"
    # Ensure the renderer actually used the provided image as background.
    # If bg_used is False, the renderer fell back to a color background.
    assert (
        res.get("bg_used") is True
    ), "renderer did not use provided image as background"

    # Now do a basic sanity check: file exists and is non-empty
    assert out_mp4.exists(), "output video not created"
    assert (
        out_mp4.stat().st_size > 1000
    ), "output video too small to contain image"

    # Confirm check_assets reports the image exists
    assets = utils.check_assets(item)
    assert assets["image_exists"] is True

    # If MoviePy is available as an importable API, open the produced
    # video and compare the first frame's average color to the source
    # image average color. We do a loose check suitable for simple
    # solid-color test images.
    if VideoFileClip is None:
        pytest.skip(
            "moviepy.editor.VideoFileClip import failed; "
            "skip frame check"
        )

    clip = VideoFileClip(str(out_mp4))
    try:
        frame = clip.get_frame(0)
    except Exception:
        clip.close()
        pytest.fail("could not read frame from produced video")

    clip.close()

    import numpy as np

    # compute average RGB for frame and source image
    frame_avg = np.mean(frame.reshape(-1, frame.shape[-1])[:, :3], axis=0)
    src = Image.open(img_path).convert("RGB")
    src_arr = np.array(src)
    src_avg = src_arr.reshape(-1, 3).mean(axis=0)
    # Since source is pure red, expect encoded video's frame to be
    # dominated by red channel and reasonably similar to source.
    # This assertion ensures the final composite used for export
    # actually contains the background image. If the renderer dropped
    # or overlaid a white background, this will fail.
    diff = abs(frame_avg - src_avg)
    assert (
        frame_avg[0] > frame_avg[1] + 30
        and frame_avg[0] > frame_avg[2] + 30
    ), f"encoded frame not dominated by red channel: {frame_avg}"
    assert (
        diff[0] < 100
    ), f"encoded frame red channel too different from source: diff={diff}"

    # Note: the encoded frame can still be altered by codecs/color space.
    # For additional debugging we also sample the ImageClip directly below,
    # but the asserts above are the required test conditions.
    # Try top-level moviepy first (some installs expose ImageClip here)
    try:
        import moviepy as _mpy
        ImageClipCtor = getattr(_mpy, "ImageClip", None)
    except Exception:
        ImageClipCtor = None

    if ImageClipCtor is None:
        # fall back to editor submodule
        try:
            import moviepy.editor as _ed
            ImageClipCtor = getattr(_ed, "ImageClip", None)
        except Exception:
            ImageClipCtor = None

    if ImageClipCtor is not None:
        try:
            direct = ImageClipCtor(str(img_path)).get_frame(0)
            direct_avg = np.mean(
                direct.reshape(-1, direct.shape[-1])[:, :3], axis=0
            )
        except Exception:
            direct = None
            direct_avg = None
        # direct_avg used for debugging only; do not let it hide failures
        if direct_avg is not None:
            assert (
                direct_avg[0] > direct_avg[1] + 30
                and direct_avg[0] > direct_avg[2] + 30
            ), f"direct ImageClip frame not dominated by red: {direct_avg}"
