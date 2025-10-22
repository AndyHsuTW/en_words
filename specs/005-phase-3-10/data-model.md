# Data Model: Phase 3.10 - Core Rendering Refactor

**Date**: 2025-10-22  
**Source**: Feature spec + research.md decisions  
**Scope**: Data structures for video rendering pipeline

---

## Overview

This data model defines the key entities used in the refactored video rendering pipeline. All entities support the split of `render_video_moviepy` into 11 testable sub-functions.

---

## Entity 1: VideoRenderingContext

**Purpose**: Single source of truth for all rendering inputs

**Lifecycle**: Created by `_prepare_all_context()`, used by all rendering functions

**Structure**:
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class VideoRenderingContext:
    """Encapsulates all data needed for video rendering.
    
    This context is prepared once and passed to all rendering functions,
    eliminating the need to recompute layouts, timelines, or contexts.
    
    Attributes:
        item: Original JSON configuration from user
        layout: Computed layout from domain.layout.compute_layout_bboxes
        timeline: Time markers from domain.timing.calculate_timeline
        entry_ctx: Entry video context (path, duration, enabled)
        ending_ctx: Ending video context (path, duration, enabled)
        letters_ctx: Letter images context (paths, bbox, missing)
        metadata: Additional computed info (durations, paths, etc.)
    """
    item: Dict[str, Any]           # Original JSON config
    layout: Dict[str, Any]         # Layout bboxes for all elements
    timeline: Dict[str, Any]       # Time markers (countdown, reveal, etc.)
    entry_ctx: Dict[str, Any]      # Entry video info
    ending_ctx: Dict[str, Any]     # Ending video info
    letters_ctx: Dict[str, Any]    # Letter images info
    metadata: Dict[str, Any]       # Computed metadata
```

**Validation Rules**:
- `item` must pass JSON schema validation (shared.validation.SCHEMA)
- `layout` must contain all required bboxes (letters, chinese, timer, etc.)
- `timeline` must have valid time markers (countdown_start, reveal_start, etc.)
- All file paths in contexts must exist (unless dry_run=True)

**Relationships**:
- **Created by**: `_prepare_all_context()`
- **Used by**: All 10 rendering functions (`_render_*`, `_process_*`, `_load_*`, `_compose_*`)
- **Sources**: 
  - domain.layout (layout computation)
  - domain.timing (timeline calculation)
  - application.context_builder (entry/ending/letters contexts)

**Example**:
```python
ctx = VideoRenderingContext(
    item={
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "countdown_sec": 3,
        # ... other config
    },
    layout={
        "letters_bbox": {"x": 64, "y": 48, "w": 800, "h": 220},
        "chinese_bbox": {"x": 1000, "y": 48, "w": 400, "h": 300},
        # ... other bboxes
    },
    timeline={
        "countdown_start": 0.0,
        "reveal_start": 3.0,
        "total_duration": 13.0,
    },
    entry_ctx={"enabled": True, "path": "assets/entry.mp4", "duration": 2.0},
    ending_ctx={"enabled": True, "path": "assets/ending.mp4", "duration": 3.0},
    letters_ctx={
        "letters": [
            {"char": "I", "path": "assets/AZ/I.png", "bbox": {...}},
            {"char": "i", "path": "assets/AZ/i_small.png", "bbox": {...}}
        ],
        "missing": []
    },
    metadata={
        "video_size": (1920, 1080),
        "fps": 24,
        "bg_color": (255, 250, 233),
    }
)
```

---

## Entity 2: Layer (Protocol)

**Purpose**: Define interface for renderable layers

**Lifecycle**: Implemented by infrastructure layer, used by application layer

**Structure**:
```python
from typing import Protocol, Any, Dict

class Layer(Protocol):
    """Protocol for renderable video layers.
    
    Each layer represents a visual or audio element in the final video.
    Layers are composed together by the IVideoComposer.
    """
    
    def render(self) -> Any:
        """Render this layer and return a MoviePy Clip.
        
        Returns:
            MoviePy Clip (ImageClip, TextClip, VideoFileClip, etc.)
        """
        ...
    
    def get_bbox(self) -> Dict[str, int]:
        """Get the bounding box for this layer.
        
        Returns:
            Dict with keys: x, y, w, h (pixel coordinates)
        """
        ...
    
    def get_duration(self) -> float:
        """Get the duration of this layer in seconds.
        
        Returns:
            Duration in seconds (float)
        """
        ...
```

**Concrete Implementations** (in infrastructure layer):
```python
class LettersLayer:
    """Layer for letter images (top-left)."""
    def __init__(self, ctx: VideoRenderingContext):
        self.ctx = ctx
    
    def render(self) -> Any:
        # Load letter images, position according to ctx.letters_ctx
        ...
    
    def get_bbox(self) -> Dict[str, int]:
        return self.ctx.layout["letters_bbox"]
    
    def get_duration(self) -> float:
        return self.ctx.timeline["total_duration"]

class ChineseZhuyinLayer:
    """Layer for Chinese + Zhuyin text (top-right)."""
    # Similar structure...

class TimerLayer:
    """Layer for countdown timer (top-left corner)."""
    # Similar structure...

class RevealLayer:
    """Layer for word reveal animation (bottom center)."""
    # Similar structure...

class ProgressBarLayer:
    """Layer for progress bar (bottom)."""
    # Similar structure...
```

**Validation Rules**:
- `render()` must return a valid MoviePy Clip
- `get_bbox()` must return Dict with x, y, w, h keys
- `get_duration()` must return positive float

**Relationships**:
- **Implemented by**: infrastructure.video.layers (new module)
- **Used by**: application.video_service rendering functions
- **Composed by**: IVideoComposer (existing Protocol)

---

## Entity 3: IVideoComposer (Existing Protocol)

**Purpose**: Interface for video composition and export

**Lifecycle**: Implemented by infrastructure.video.moviepy_adapter

**Structure**:
```python
from typing import Protocol, List, Any, Optional

class IVideoComposer(Protocol):
    """Protocol for video composition engines.
    
    Abstraction over MoviePy or other video libraries.
    """
    
    def compose_layers(
        self, 
        layers: List[Any],  # List of MoviePy Clips
        audio: Optional[Any] = None  # Optional AudioClip
    ) -> Any:
        """Combine multiple layers into a single video.
        
        Args:
            layers: List of MoviePy Clips (visual layers)
            audio: Optional AudioClip (background music + beeps)
        
        Returns:
            CompositeVideoClip (MoviePy)
        """
        ...
    
    def export(
        self, 
        clip: Any,  # CompositeVideoClip
        output_path: str,
        **kwargs  # codec, fps, etc.
    ) -> None:
        """Export composed video to file.
        
        Args:
            clip: CompositeVideoClip to export
            output_path: Output MP4 file path
            **kwargs: Additional FFmpeg arguments
        
        Side Effects:
            Writes MP4 file to output_path
        """
        ...
```

**Validation Rules**:
- `compose_layers()` must handle overlapping layers (z-order)
- `export()` must produce valid MP4 file
- Must support headless rendering (no GUI)

**Relationships**:
- **Implemented by**: infrastructure.video.moviepy_adapter.MoviePyComposer
- **Used by**: application.video_service._compose_and_export()
- **Existing**: Already defined in Phase 3.1-3.8

---

## Entity 4: RenderingPipeline

**Purpose**: Orchestrate the complete rendering process

**Lifecycle**: Created and executed by `render_video()`

**Structure**:
```python
from typing import List, Optional, Any

class RenderingPipeline:
    """Coordinates the 11-step rendering process.
    
    This is NOT a required entity for implementation - it's a conceptual
    model showing how the sub-functions work together.
    
    Attributes:
        context: VideoRenderingContext with all inputs
        composer: IVideoComposer for final composition
    """
    
    def __init__(
        self, 
        context: VideoRenderingContext,
        composer: Optional[IVideoComposer] = None
    ):
        self.context = context
        self.composer = composer or self._default_composer()
    
    def execute(self, output_path: str) -> Dict[str, Any]:
        """Execute the complete rendering pipeline.
        
        Steps:
            1. Create background clip
            2. Render letters layer
            3. Render Chinese/Zhuyin layer
            4. Render timer layer
            5. Render reveal layer
            6. Render progress bar layer
            7. Process audio tracks
            8. Load entry/ending clips
            9. Compose all layers + audio
            10. Export to output_path
        
        Returns:
            Metadata dict with success, duration, output_path
        """
        # Step 1-6: Render layers
        background = _create_background_clip(self.context)
        letters = _render_letters_layer(self.context)
        chinese_zhuyin = _render_chinese_zhuyin_layer(self.context)
        timer = _render_timer_layer(self.context)
        reveal = _render_reveal_layer(self.context)
        progress_bar = _render_progress_bar_layer(self.context)
        
        # Step 7: Audio
        audio = _process_audio_tracks(self.context)
        
        # Step 8: Entry/Ending
        entry_clip, ending_clip = _load_entry_ending_clips(self.context)
        
        # Step 9-10: Compose and export
        all_layers = [background, letters, chinese_zhuyin, timer, reveal, progress_bar]
        if entry_clip:
            all_layers.insert(0, entry_clip)
        if ending_clip:
            all_layers.append(ending_clip)
        
        _compose_and_export(self.context, all_layers, audio, output_path, self.composer)
        
        return {
            "success": True,
            "duration": self.context.timeline["total_duration"],
            "output_path": output_path
        }
```

**Note**: This is a **conceptual model** to show how sub-functions work together. The actual implementation may use simple function calls in `render_video()` instead of a class.

**Validation Rules**:
- All layers must be non-None (unless optional like entry/ending)
- Audio duration must match video duration
- Output file must be created successfully

**Relationships**:
- **Uses**: All 11 sub-functions
- **Created by**: `render_video()` (orchestration function)
- **Optional**: May be implemented as class or simple function calls

---

## Entity 5: DeprecatedWrapper

**Purpose**: Maintain backward compatibility during transition

**Lifecycle**: Temporary (will be removed in v2.0)

**Structure**:
```python
import warnings
from typing import Dict, Any

def render_video_moviepy(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.video_service.render_video 代替
    
    Args:
        item: JSON configuration dict
        out_path: Output MP4 file path
        dry_run: If True, only compute metadata without rendering
        skip_ending: If True, skip ending video (for batch processing)
    
    Returns:
        Result dict with success, duration, output_path
    
    Raises:
        DeprecationWarning: Always raised to guide migration
    """
    warnings.warn(
        "render_video_moviepy is deprecated and will be removed in v2.0. "
        "Use application.video_service.render_video instead. "
        "See ARCHITECTURE.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from spellvid.application.video_service import render_video
    return render_video(item, out_path, dry_run, skip_ending)
```

**Validation Rules**:
- Must maintain exact same function signature as old implementation
- Must trigger DeprecationWarning
- Must delegate to new implementation (no duplicate logic)

**Relationships**:
- **Wraps**: application.video_service.render_video
- **Used by**: All existing tests (>30 files)
- **Timeline**: Remove in v2.0 after all tests migrated

---

## State Transitions

### VideoRenderingContext Lifecycle

```
[Input: item dict] 
    ↓
_prepare_all_context()
    ↓
[VideoRenderingContext created]
    ↓
Passed to all rendering functions
    ↓
[Rendering complete]
    ↓
Context discarded (no persistent state)
```

### Rendering Pipeline Flow

```
1. _prepare_all_context(item) → ctx
2. _create_background_clip(ctx) → background
3. _render_letters_layer(ctx) → letters
4. _render_chinese_zhuyin_layer(ctx) → chinese_zhuyin
5. _render_timer_layer(ctx) → timer
6. _render_reveal_layer(ctx) → reveal
7. _render_progress_bar_layer(ctx) → progress_bar
8. _process_audio_tracks(ctx) → audio
9. _load_entry_ending_clips(ctx) → entry, ending
10. _compose_and_export(ctx, layers, audio, output_path)
11. Return metadata dict
```

**No mutable state** - each function returns new data, context is read-only.

---

## Validation Summary

### Required Validations

**VideoRenderingContext**:
- ✅ JSON schema validation (shared.validation.SCHEMA)
- ✅ Layout bbox validation (all required keys present)
- ✅ Timeline validation (valid time markers)
- ✅ File path validation (check_assets)

**Layer Protocol**:
- ✅ render() returns MoviePy Clip
- ✅ get_bbox() returns valid Dict[str, int]
- ✅ get_duration() returns positive float

**IVideoComposer**:
- ✅ compose_layers() handles overlapping layers
- ✅ export() produces valid MP4 file

**DeprecatedWrapper**:
- ✅ Maintains exact function signature
- ✅ Triggers DeprecationWarning
- ✅ Delegates to new implementation

---

## Testing Strategy

### Unit Tests (tests/unit/application/test_video_service.py)

```python
def test_prepare_all_context():
    """Test context preparation with valid item."""
    item = {"letters": "I i", "word_en": "Ice", ...}
    ctx = _prepare_all_context(item)
    
    assert isinstance(ctx, VideoRenderingContext)
    assert ctx.item == item
    assert "letters_bbox" in ctx.layout
    assert "countdown_start" in ctx.timeline

def test_create_background_clip():
    """Test background clip creation."""
    ctx = VideoRenderingContext(...)
    clip = _create_background_clip(ctx)
    
    assert clip is not None
    assert clip.size == (1920, 1080)

# ... similar tests for each sub-function
```

### Contract Tests (tests/contract/test_rendering_protocol.py)

```python
def test_layer_protocol_compliance():
    """Test that all layer implementations satisfy Layer protocol."""
    from spellvid.infrastructure.video.layers import (
        LettersLayer, ChineseZhuyinLayer, TimerLayer
    )
    
    ctx = VideoRenderingContext(...)
    
    for layer_cls in [LettersLayer, ChineseZhuyinLayer, TimerLayer]:
        layer = layer_cls(ctx)
        assert hasattr(layer, "render")
        assert hasattr(layer, "get_bbox")
        assert hasattr(layer, "get_duration")
```

### Integration Tests (tests/integration/test_end_to_end.py)

```python
def test_complete_rendering_pipeline():
    """Test complete render from JSON to MP4."""
    item = load_json("config.json")[0]
    output = "out/test_ice.mp4"
    
    result = render_video(item, output)
    
    assert result["success"]
    assert os.path.exists(output)
    # Validate MP4 with opencv-python...
```

---

## Migration Path

### From Old API (utils.py)

```python
# OLD (deprecated)
from spellvid.utils import render_video_moviepy
result = render_video_moviepy(item, "out/test.mp4")

# NEW (recommended)
from spellvid.application.video_service import render_video
result = render_video(item, "out/test.mp4")
```

### Timeline

- **Phase 3.10**: Both APIs work (wrappers in utils.py)
- **v2.0**: Remove wrappers, only new API available

---

**Document Version**: 1.0  
**Author**: GitHub Copilot  
**Status**: Ready for contract generation
