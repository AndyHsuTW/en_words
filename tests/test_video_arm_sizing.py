"""Test video sizing with real arm.mp4 asset to verify no overlap."""
import os
import pytest
from spellvid import utils


def test_arm_video_sizing():
    """Test that arm.mp4 is properly constrained to not exceed target size."""
    # Use the actual arm.mp4 asset that was showing sizing issues
    real_video = os.path.join(
        os.path.dirname(__file__), "..", "assets", "arm.mp4"
    )
    if not os.path.isfile(real_video):
        pytest.skip("arm.mp4 asset not found")

    item = {
        "letters": "Aa",
        "word_en": "Arm",
        "word_zh": "手臂",
        "image_path": real_video,
        "music_path": "assets/arm_60s.mp3",
        "countdown_sec": 10,
        "reveal_hold_sec": 10,
    }

    # Get layout boxes to compare
    boxes = utils.compute_layout_bboxes(item)
    reveal_box = boxes.get("reveal")
    assert reveal_box is not None, (
        "compute_layout_bboxes did not return reveal"
    )

    # Run renderer in debug mode to get actual placement
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "test_arm.mp4")
        os.environ["SPELLVID_DEBUG_SKIP_WRITE"] = "1"
        try:
            result = utils.render_video_moviepy(item, out, dry_run=False)
        finally:
            os.environ.pop("SPELLVID_DEBUG_SKIP_WRITE", None)

        # Verify video was used and positioned
        assert result.get("bg_used", False), (
            "Renderer did not use background video"
        )
        placement = result.get("bg_placement")
        assert placement is not None, "No bg_placement returned"

        px, py, pw, ph = placement

        # Verify video dimensions don't exceed target constraints
        target_box_side = int(min(1920, 1080) * 0.7)  # 756px
        assert pw <= target_box_side, (
            f"Video width {pw} exceeds limit {target_box_side}"
        )
        assert ph <= target_box_side, (
            f"Video height {ph} exceeds limit {target_box_side}"
        )

        # Verify no overlap with reveal area
        bg_bottom = py + ph
        reveal_top = int(reveal_box.get("y", 0))

        # Should have at least small margin to avoid visual overlap
        margin = 8  # minimum gap
        assert bg_bottom <= reveal_top - margin, (
            f"Video bottom {bg_bottom} too close to reveal top {reveal_top}, "
            f"need at least {margin}px margin"
        )


def test_video_frame_constraints():
    """Test that video frames are strictly enforced to stay within bounds."""
    # This test verifies the core constraint logic works even with
    # difficult videos
    real_video = os.path.join(
        os.path.dirname(__file__), "..", "assets", "arm.mp4"
    )
    if not os.path.isfile(real_video):
        pytest.skip("arm.mp4 asset not found")

    item = {
        "letters": "Bb",
        "word_en": "Big",
        "word_zh": "大",
        "image_path": real_video,
        "music_path": "assets/arm_60s.mp3",
        "countdown_sec": 5,
        "reveal_hold_sec": 3,
    }

    # Compute target limits
    target_box_side = int(min(1920, 1080) * 0.7)  # 756px

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "test_constraints.mp4")
        os.environ["SPELLVID_DEBUG_SKIP_WRITE"] = "1"
        try:
            result = utils.render_video_moviepy(item, out, dry_run=False)
        finally:
            os.environ.pop("SPELLVID_DEBUG_SKIP_WRITE", None)

        placement = result.get("bg_placement")
        if placement:
            px, py, pw, ph = placement
            # Both width and height must be within the box
            assert pw <= target_box_side, f"Width {pw} > {target_box_side}"
            assert ph <= target_box_side, f"Height {ph} > {target_box_side}"
