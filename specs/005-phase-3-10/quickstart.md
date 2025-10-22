# Quickstart: Phase 3.10 TDD Workflow

**Date**: 2025-10-22  
**Purpose**: Step-by-step guide for TDD-based refactoring  
**Audience**: Developers implementing Phase 3.10

---

## Prerequisites

1. **Environment Setup**:
   ```powershell
   # Activate virtual environment
   .\.venv\Scripts\Activate.ps1
   
   # Ensure all dependencies installed
   pip install -r requirements-dev.txt
   
   # Verify tests run
   pytest tests/ -x
   ```

2. **Phase 3.1-3.8 Complete**:
   - 44/64 functions migrated ✅
   - utils.py at 2,944 lines ✅
   - All tests passing ✅

3. **Branch Setup**:
   ```powershell
   git checkout 005-phase-3-10
   git pull origin 005-phase-3-10
   ```

---

## TDD Workflow Example: Extract `_prepare_all_context()`

This example demonstrates the complete TDD cycle for extracting one sub-function from `render_video_moviepy`.

### Step 1: Write the Test (RED) 🔴

**File**: `tests/unit/application/test_video_service.py` (new file)

```python
"""Unit tests for video_service sub-functions."""

import pytest
from spellvid.application.video_service import (
    _prepare_all_context,
    VideoRenderingContext
)


def test_prepare_all_context_with_valid_item():
    """Test context preparation with valid JSON item."""
    # Arrange
    item = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "countdown_sec": 3,
        "reveal_hold_sec": 2,
        "image_path": "assets/ice.png",
        "music_path": "assets/ice.mp3"
    }
    
    # Act
    ctx = _prepare_all_context(item)
    
    # Assert
    assert isinstance(ctx, VideoRenderingContext)
    assert ctx.item == item
    
    # Verify layout computed
    assert "letters_bbox" in ctx.layout
    assert "chinese_bbox" in ctx.layout
    assert ctx.layout["letters_bbox"]["x"] == 64  # LETTER_SAFE_X
    
    # Verify timeline computed
    assert "countdown_start" in ctx.timeline
    assert "reveal_start" in ctx.timeline
    assert ctx.timeline["countdown_start"] == 0.0
    assert ctx.timeline["reveal_start"] == 3.0  # After countdown
    
    # Verify contexts prepared
    assert "enabled" in ctx.entry_ctx
    assert "enabled" in ctx.ending_ctx
    assert "letters" in ctx.letters_ctx


def test_prepare_all_context_validates_schema():
    """Test context preparation rejects invalid item."""
    # Arrange - missing required field
    item = {
        "letters": "I i",
        # Missing word_en, word_zh, image_path, music_path
    }
    
    # Act & Assert
    with pytest.raises(ValueError, match="validation"):
        _prepare_all_context(item)
```

**Run the test** (expect FAILURE):
```powershell
pytest tests/unit/application/test_video_service.py::test_prepare_all_context_with_valid_item -v
```

**Expected output**:
```
FAILED - ImportError: cannot import name '_prepare_all_context'
```

✅ **Test fails correctly** - function doesn't exist yet

---

### Step 2: Extract the Function (GREEN) 🟢

**File**: `spellvid/application/video_service.py`

**Before** (in utils.py):
```python
def render_video_moviepy(item, out_path, dry_run=False, skip_ending=False):
    # ... 1,630 lines of code ...
    
    # Context preparation (lines 1320-1400)
    layout = compute_layout_bboxes(item)
    timeline = calculate_timeline(...)
    entry_ctx = _prepare_entry_context(item)
    ending_ctx = _prepare_ending_context(item)
    letters_ctx = _prepare_letters_context(item)
    
    # ... more rendering code ...
```

**After** (extract to video_service.py):
```python
# spellvid/application/video_service.py

from dataclasses import dataclass
from typing import Dict, Any

from spellvid.domain.layout import compute_layout_bboxes
from spellvid.domain.timing import calculate_timeline
from spellvid.application.context_builder import (
    prepare_entry_context,
    prepare_ending_context,
    prepare_letters_context
)


@dataclass
class VideoRenderingContext:
    """Single source of truth for all rendering inputs."""
    item: Dict[str, Any]
    layout: Dict[str, Any]
    timeline: Dict[str, Any]
    entry_ctx: Dict[str, Any]
    ending_ctx: Dict[str, Any]
    letters_ctx: Dict[str, Any]
    metadata: Dict[str, Any]


def _prepare_all_context(item: Dict[str, Any]) -> VideoRenderingContext:
    """Prepare all rendering context data upfront.
    
    Args:
        item: JSON configuration dict (validated against SCHEMA)
    
    Returns:
        VideoRenderingContext with all computed data
    
    Raises:
        ValueError: If item fails validation
    """
    # Validate schema first
    from spellvid.shared.validation import validate_schema, SCHEMA
    errors = validate_schema([item])  # validate_schema expects list
    if errors:
        raise ValueError(f"Item validation failed: {errors}")
    
    # Compute layout
    layout = compute_layout_bboxes(item)
    
    # Compute timeline
    countdown_sec = item.get("countdown_sec", 3)
    reveal_hold_sec = item.get("reveal_hold_sec", 2)
    per_letter_time = 1.0
    reveal_time = len(item.get("word_en", "")) * per_letter_time
    total_duration = countdown_sec + reveal_time + reveal_hold_sec
    
    timeline = calculate_timeline(
        video_duration=total_duration,
        fadeout_duration=0.0
    )
    
    # Prepare entry/ending/letters contexts
    entry_ctx = prepare_entry_context(item)
    ending_ctx = prepare_ending_context(item)
    letters_ctx = prepare_letters_context(item)
    
    # Prepare metadata
    metadata = {
        "video_size": (1920, 1080),
        "fps": 24,
        "bg_color": (255, 250, 233),
        "total_duration": total_duration,
    }
    
    return VideoRenderingContext(
        item=item,
        layout=layout,
        timeline=timeline,
        entry_ctx=entry_ctx,
        ending_ctx=ending_ctx,
        letters_ctx=letters_ctx,
        metadata=metadata
    )
```

**Run the test again**:
```powershell
pytest tests/unit/application/test_video_service.py::test_prepare_all_context_with_valid_item -v
```

**Expected output**:
```
PASSED ✅
```

---

### Step 3: Commit the Change 📝

```powershell
git add tests/unit/application/test_video_service.py
git add spellvid/application/video_service.py
git commit -m "test: add test for _prepare_all_context()

- Test validates context structure
- Test checks layout, timeline, contexts computed
- Expected to fail (function not yet implemented)
"

git add spellvid/application/video_service.py
git commit -m "feat: extract _prepare_all_context() from render_video_moviepy

- Extracts context preparation logic (~80 lines)
- Creates VideoRenderingContext dataclass
- Validates JSON schema
- Computes layout, timeline, entry/ending/letters contexts
- Test now passes
"
```

---

### Step 4: Update render_video_moviepy to Use New Function

**File**: `spellvid/utils.py`

**Before**:
```python
def render_video_moviepy(item, out_path, dry_run=False, skip_ending=False):
    # ... context preparation code ...
    layout = compute_layout_bboxes(item)
    timeline = calculate_timeline(...)
    # ... (80 lines removed)
    
    # ... rest of rendering ...
```

**After**:
```python
def render_video_moviepy(item, out_path, dry_run=False, skip_ending=False):
    from spellvid.application.video_service import _prepare_all_context
    
    ctx = _prepare_all_context(item)
    
    # Now use ctx.layout, ctx.timeline, etc. instead of local variables
    # ... rest of rendering ...
```

**Run ALL tests**:
```powershell
pytest tests/ -x
```

**Expected**: All tests still pass ✅

**Commit**:
```powershell
git add spellvid/utils.py
git commit -m "refactor: use _prepare_all_context() in render_video_moviepy

- Replace inline context preparation with function call
- Reduces render_video_moviepy by ~80 lines
- All tests still pass
"
```

---

### Step 5: Verify Integration

**Run integration test**:
```powershell
# Test single video render
python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4

# Verify MP4 created
ls out/Ice.mp4
```

**Run example script**:
```powershell
.\scripts\render_example.ps1
```

**Expected**: 7 MP4 files created ✅

---

## Repeat for Remaining 10 Functions

Follow the same TDD cycle for each sub-function:

1. **_create_background_clip()** (~100-150 lines)
2. **_render_letters_layer()** (~150-180 lines)
3. **_render_chinese_zhuyin_layer()** (~180-200 lines)
4. **_render_timer_layer()** (~70-90 lines)
5. **_render_reveal_layer()** (~150-200 lines)
6. **_render_progress_bar_layer()** (~80-120 lines)
7. **_process_audio_tracks()** (~180-270 lines)
8. **_load_entry_ending_clips()** (~100-150 lines)
9. **_compose_and_export()** (~150-200 lines)
10. **render_video()** (~50-80 lines orchestration)

---

## Rollback Strategy

If a test fails after extraction:

```powershell
# View last 3 commits
git log --oneline -3

# Rollback last commit
git reset --hard HEAD~1

# Or rollback to specific commit
git reset --hard <commit-hash>

# Re-run tests to verify
pytest tests/ -x
```

---

## Performance Monitoring

After each function extraction:

```powershell
# Measure single video render time
Measure-Command { 
    python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 
}

# Measure test suite time
Measure-Command { pytest tests/ }
```

**Baseline** (Phase 3.1-3.8):
- Single video: ~15-20 seconds
- Test suite: ~2-3 minutes

**Threshold**: <5% increase (spec requirement)

---

## Success Criteria Checklist

After extracting all 11 functions:

- [ ] All contract tests pass (tests/contract/test_phase310_rendering_protocol.py)
- [ ] All unit tests pass (tests/unit/application/test_video_service.py)
- [ ] All existing tests pass (>30 test files, 0 failures)
- [ ] Integration test passes (render_example.ps1 produces 7 MP4s)
- [ ] Performance within threshold (<5% overhead)
- [ ] utils.py reduced to ~120 lines
- [ ] Documentation updated (AGENTS.md, ARCHITECTURE.md)

---

## Troubleshooting

### Import Errors

**Problem**: `ImportError: cannot import name 'VideoRenderingContext'`

**Solution**:
```python
# Add to spellvid/application/__init__.py
from spellvid.application.video_service import VideoRenderingContext

__all__ = ["VideoRenderingContext"]
```

### Test Failures

**Problem**: Test fails with "AttributeError: 'VideoRenderingContext' object has no attribute 'layout'"

**Solution**: Check VideoRenderingContext has all required fields in `__init__` or dataclass definition

### Performance Regression

**Problem**: Video render time increased by >5%

**Solution**:
```powershell
# Profile the code
python -m cProfile -o profile.stats -m spellvid.cli make --letters "I i" ...

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

Optimize hot paths (likely progress bar or text rendering).

---

## Next Steps

After completing all 11 functions:

1. **Create deprecated wrappers** in utils.py
2. **Update tests** to use new API (optional, wrappers work)
3. **Update documentation**:
   - AGENTS.md (migration status)
   - ARCHITECTURE.md (new architecture)
   - IMPLEMENTATION_SUMMARY.md (Phase 3.10 summary)
4. **Final validation** (T064-T066 in tasks.md)

---

**Document Version**: 1.0  
**Author**: GitHub Copilot  
**Status**: Ready for TDD execution
