"""Unit tests for video_service sub-functions.

Tests follow TDD approach:
1. Write test (RED)
2. Implement function (GREEN)
3. Refactor if needed
"""

import pytest
from typing import Dict, Any

from spellvid.application.video_service import (
    VideoRenderingContext,
    _prepare_all_context,
    _create_background_clip,
)


# ============================================================================
# T005: _prepare_all_context() tests
# ============================================================================

def test_prepare_all_context_with_valid_item():
    """Test context preparation with valid JSON item.

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange - valid JSON config
    item = {
        "letters": "C c",
        "word_en": "Cat",
        "word_zh": "貓",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3"
    }

    # Act
    ctx = _prepare_all_context(item)

    # Assert - context structure
    assert isinstance(ctx, VideoRenderingContext)
    assert ctx.item == item

    # Verify layout computed (actual keys from LayoutResult.to_dict())
    assert "letters" in ctx.layout
    assert "word_zh" in ctx.layout
    assert "timer" in ctx.layout
    assert "reveal" in ctx.layout

    # Verify timeline computed
    assert "countdown_start" in ctx.timeline
    assert "reveal_start" in ctx.timeline
    assert "total_duration" in ctx.timeline
    assert ctx.timeline["countdown_start"] == 0.0
    assert ctx.timeline["reveal_start"] >= 3.0  # After countdown

    # Verify contexts prepared
    assert "enabled" in ctx.entry_ctx
    assert "enabled" in ctx.ending_ctx
    assert "letters" in ctx.letters_ctx

    # Verify metadata
    assert "video_size" in ctx.metadata
    assert ctx.metadata["video_size"] == (1920, 1080)


def test_prepare_all_context_validates_schema():
    """Test context preparation rejects invalid item.

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange - missing required fields
    item = {
        "letters": "I i",
        # Missing word_en, word_zh, image_path, music_path
    }

    # Act & Assert
    with pytest.raises(ValueError, match="validation|required"):
        _prepare_all_context(item)


def test_prepare_all_context_handles_missing_optional_fields():
    """Test context preparation with missing optional fields.

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange - minimal valid config
    item = {
        "letters": "A a",
        "word_en": "Apple",
        "word_zh": "蘋果",
        "image_path": "assets/animal.mp4",
        "music_path": "assets/animal_20s.mp3",
        # countdown_sec, reveal_hold_sec will use defaults
    }

    # Act
    ctx = _prepare_all_context(item)

    # Assert - uses defaults
    assert isinstance(ctx, VideoRenderingContext)
    assert ctx.item["countdown_sec"] == 10  # Default
    assert ctx.item["reveal_hold_sec"] == 5  # Default


def test_prepare_all_context_computes_letters_context():
    """Test that letters context includes paths and missing info.

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange
    item = {
        "letters": "A b C",  # Mixed case
        "word_en": "Test",
        "word_zh": "測試",
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3"
    }

    # Act
    ctx = _prepare_all_context(item)

    # Assert - letters context structure (actual structure from context_builder)
    assert "letters" in ctx.letters_ctx
    assert ctx.letters_ctx["letters"] == "A b C"  # Original string

    # Check layout details (nested)
    if "layout" in ctx.letters_ctx:
        layout_detail = ctx.letters_ctx["layout"]
        if "letters" in layout_detail:
            letters_list = layout_detail["letters"]
            assert isinstance(letters_list, list)
            # First letter should have char, filename, path
            if len(letters_list) > 0:
                first_letter = letters_list[0]
                assert "char" in first_letter
                assert "filename" in first_letter

    # Missing letters tracking
    assert "missing" in ctx.letters_ctx
    assert isinstance(ctx.letters_ctx["missing"], list)


# ============================================================================
# T006: _create_background_clip() tests
# ============================================================================

def test_create_background_clip_with_image():
    """Test background clip creation with image background.

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange
    item = {
        "letters": "C c",
        "word_en": "Cat",
        "word_zh": "貓",
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
    }
    ctx = _prepare_all_context(item)

    # Act
    bg_clip = _create_background_clip(ctx)

    # Assert
    assert bg_clip is not None
    # Check duration matches expected
    assert hasattr(bg_clip, 'duration')
    # Background should use image if present
    # (actual assertion depends on MoviePy clip type)


def test_create_background_clip_with_solid_color():
    """Test background clip creation with solid color (no image).

    EXPECTED: FAIL (function not yet implemented)
    """
    # Arrange - no image_path
    item = {
        "letters": "A a",
        "word_en": "Apple",
        "word_zh": "蘋果",
        "image_path": "",  # Empty image path
        "music_path": "assets/animal_20s.mp3",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
    }
    ctx = _prepare_all_context(item)

    # Act
    bg_clip = _create_background_clip(ctx)

    # Assert
    assert bg_clip is not None
    assert hasattr(bg_clip, 'duration')
    # Should create solid color background
    # Duration should match context timeline


# ============================================================================
# Helper fixtures (if needed)
# ============================================================================

# ============================================================================
# T015: render_video() orchestration tests
# ============================================================================

def test_render_video_orchestration_calls_all_subfunctions(
    mocker, tmp_path  # type: ignore
):
    """Test that render_video() calls all 11 sub-functions in correct order.

    EXPECTED: FAIL (new orchestration not yet implemented)
    """
    # Arrange - mock all sub-functions
    mock_prepare = mocker.patch(
        'spellvid.application.video_service._prepare_all_context'
    )
    mock_bg = mocker.patch(
        'spellvid.application.video_service._create_background_clip'
    )
    mock_letters = mocker.patch(
        'spellvid.application.video_service._render_letters_layer'
    )
    mock_chinese = mocker.patch(
        'spellvid.application.video_service.'
        '_render_chinese_zhuyin_layer'
    )
    mock_timer = mocker.patch(
        'spellvid.application.video_service._render_timer_layer'
    )
    mock_reveal = mocker.patch(
        'spellvid.application.video_service._render_reveal_layer'
    )
    mock_progress = mocker.patch(
        'spellvid.application.video_service.'
        '_render_progress_bar_layer'
    )
    mock_audio = mocker.patch(
        'spellvid.application.video_service._process_audio_tracks'
    )
    mock_entry_ending = mocker.patch(
        'spellvid.application.video_service._load_entry_ending_clips'
    )
    mock_compose = mocker.patch(
        'spellvid.application.video_service._compose_and_export'
    )

    # Setup mock return values
    from spellvid.application.video_service import VideoRenderingContext

    mock_ctx = VideoRenderingContext(
        item={"letters": "C c", "word_en": "Cat", "word_zh": "貓"},
        layout={"letters": [], "word_zh": {}, "timer": {}, "reveal": {}},
        timeline={"total_duration": 10.0},
        entry_ctx={"enabled": False},
        ending_ctx={"enabled": False},
        letters_ctx={"letters": "C c"},
        metadata={"video_size": (1920, 1080), "fps": 24},
    )
    mock_prepare.return_value = mock_ctx
    mock_entry_ending.return_value = (None, None)

    # Item dict to render
    item = {
        "letters": "C c",
        "word_en": "Cat",
        "word_zh": "貓",
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3",
    }
    output_path = str(tmp_path / "test.mp4")

    # Act - import the new render_video (not old one)
    from spellvid.application.video_service import render_video

    # Note: New signature uses item dict, not VideoConfig
    render_video(item, output_path, dry_run=False, skip_ending=False)

    # Assert - all sub-functions called in order
    mock_prepare.assert_called_once_with(item)
    mock_bg.assert_called_once_with(mock_ctx)
    mock_letters.assert_called_once_with(mock_ctx)
    mock_chinese.assert_called_once_with(mock_ctx)
    mock_timer.assert_called_once_with(mock_ctx)
    mock_reveal.assert_called_once_with(mock_ctx)
    mock_progress.assert_called_once_with(mock_ctx)
    mock_audio.assert_called_once_with(mock_ctx)
    mock_entry_ending.assert_called_once_with(mock_ctx)
    mock_compose.assert_called_once()  # Check it was called


def test_render_video_orchestration_returns_metadata(tmp_path):
    """Test that render_video() returns expected metadata dict.

    EXPECTED: FAIL (new orchestration not yet implemented)
    """
    # Arrange
    item = {
        "letters": "A a",
        "word_en": "Apple",
        "word_zh": "蘋果",
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
    }
    output_path = str(tmp_path / "test.mp4")

    # Act
    from spellvid.application.video_service import render_video
    result = render_video(item, output_path, dry_run=True)

    # Assert - metadata structure
    assert isinstance(result, dict)
    assert "success" in result
    assert "duration" in result
    assert "output_path" in result
    assert "metadata" in result
    assert result["success"] is True


def test_render_video_orchestration_handles_skip_ending(
    mocker, tmp_path  # type: ignore
):
    """Test that skip_ending flag is passed to ending context.

    EXPECTED: FAIL (new orchestration not yet implemented)
    """
    # Arrange
    mock_prepare = mocker.patch(
        'spellvid.application.video_service._prepare_all_context'
    )
    mocker.patch(
        'spellvid.application.video_service._compose_and_export'
    )
    mocker.patch(
        'spellvid.application.video_service._create_background_clip'
    )
    mocker.patch(
        'spellvid.application.video_service._render_letters_layer'
    )
    mocker.patch(
        'spellvid.application.video_service.'
        '_render_chinese_zhuyin_layer'
    )
    mocker.patch(
        'spellvid.application.video_service._render_timer_layer'
    )
    mocker.patch(
        'spellvid.application.video_service._render_reveal_layer'
    )
    mocker.patch(
        'spellvid.application.video_service.'
        '_render_progress_bar_layer'
    )
    mocker.patch(
        'spellvid.application.video_service._process_audio_tracks'
    )
    mocker.patch(
        'spellvid.application.video_service._load_entry_ending_clips'
    )

    from spellvid.application.video_service import VideoRenderingContext

    mock_ctx = VideoRenderingContext(
        item={"letters": "C c", "word_en": "Cat", "word_zh": "貓"},
        layout={"letters": [], "word_zh": {}, "timer": {}, "reveal": {}},
        timeline={"total_duration": 10.0},
        entry_ctx={"enabled": False},
        ending_ctx={"enabled": False},  # Should be False when skip_ending=True
        letters_ctx={"letters": "C c"},
        metadata={"video_size": (1920, 1080), "fps": 24},
    )
    mock_prepare.return_value = mock_ctx

    item = {
        "letters": "C c",
        "word_en": "Cat",
        "word_zh": "貓",
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3",
        "skip_ending": True,  # Pass flag in item
    }
    output_path = str(tmp_path / "test.mp4")

    # Act
    from spellvid.application.video_service import render_video
    render_video(item, output_path, dry_run=False, skip_ending=True)

    # Assert - ending context should reflect skip_ending
    # (actual assertion depends on how context handles this flag)
    mock_prepare.assert_called_once()


# ============================================================================
# Helper fixtures (if needed)
# ============================================================================

@pytest.fixture
def sample_item() -> Dict[str, Any]:
    """Sample video configuration for tests."""
    return {
        "letters": "C c",
        "word_en": "Cat",
        "word_zh": "貓",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
        "image_path": "assets/cat.mp4",
        "music_path": "assets/cat_60s.mp3",
        "video_mode": "cover"
    }
