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
