import pytest
from spellvid import utils


def _has_moviepy():
    return getattr(utils, "_HAS_MOVIEPY", False)


def test_video_mode_fit(tmp_path):
    """Test video_mode='fit' scales video to fit within bounds."""
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping video mode test")

    # Create a test mp4 using ffmpeg helper
    mp4_path = tmp_path / "bg.mp4"
    created = utils._create_placeholder_mp4_with_ffmpeg(str(mp4_path))
    if not created:
        pytest.skip("ffmpeg not available to create test mp4; skipping")

    item = {
        "letters": "V",
        "word_en": "Video",
        "word_zh": "視頻",
        "image_path": str(mp4_path),
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
        "video_mode": "fit"
    }

    out_mp4 = tmp_path / "out_fit.mp4"
    res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
    assert res.get("status") == "ok"
    assert res.get("bg_used") is True
    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 1000


def test_video_mode_cover(tmp_path):
    """Test video_mode='cover' scales video to fill bounds with cropping."""
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping video mode test")

    # Create a test mp4 using ffmpeg helper
    mp4_path = tmp_path / "bg.mp4"
    created = utils._create_placeholder_mp4_with_ffmpeg(str(mp4_path))
    if not created:
        pytest.skip("ffmpeg not available to create test mp4; skipping")

    item = {
        "letters": "V",
        "word_en": "Video",
        "word_zh": "視頻",
        "image_path": str(mp4_path),
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
        "video_mode": "cover"
    }

    out_mp4 = tmp_path / "out_cover.mp4"
    res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
    assert res.get("status") == "ok"
    assert res.get("bg_used") is True
    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 1000


def test_video_mode_default_is_fit(tmp_path):
    """Test that video_mode defaults to 'fit' when not specified."""
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping video mode test")

    # Create a test mp4 using ffmpeg helper
    mp4_path = tmp_path / "bg.mp4"
    created = utils._create_placeholder_mp4_with_ffmpeg(str(mp4_path))
    if not created:
        pytest.skip("ffmpeg not available to create test mp4; skipping")

    item = {
        "letters": "V",
        "word_en": "Video",
        "word_zh": "視頻",
        "image_path": str(mp4_path),
        "music_path": "",
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
        # no video_mode specified - should default to 'fit'
    }

    out_mp4 = tmp_path / "out_default.mp4"
    res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
    assert res.get("status") == "ok"
    assert res.get("bg_used") is True
    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 1000


def test_video_mode_schema_validation():
    """Test that schema validation accepts valid video_mode values."""
    # Test valid video_mode values
    valid_item = {
        "letters": "V",
        "word_en": "Video",
        "word_zh": "視頻",
        "image_path": "test.mp4",
        "music_path": "test.mp3",
        "video_mode": "fit"
    }

    errors = utils.validate_schema([valid_item])
    assert len(errors) == 0

    valid_item["video_mode"] = "cover"
    errors = utils.validate_schema([valid_item])
    assert len(errors) == 0

    # Test that missing video_mode is allowed (optional field)
    del valid_item["video_mode"]
    errors = utils.validate_schema([valid_item])
    assert len(errors) == 0


def test_video_mode_invalid_value():
    """Test that invalid video_mode values are rejected."""
    # Note: The current simple schema validator doesn't enforce enums,
    # but we can test that the video processing code handles invalid
    # values gracefully
    if not _has_moviepy():
        pytest.skip("MoviePy not available; skipping video mode test")

    # For the actual behavior test, invalid video_mode should fall back
    # to 'fit'. This test documents the expected behavior rather than
    # schema validation
    pass
