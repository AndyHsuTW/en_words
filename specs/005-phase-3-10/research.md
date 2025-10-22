# Research: Phase 3.10 - Core Rendering Refactor

**Date**: 2025-10-22  
**Researcher**: GitHub Copilot  
**Scope**: Technical decisions for splitting render_video_moviepy into 10-15 sub-functions

---

## Research Areas

### 1. Refactoring Patterns for Large Functions

**Decision**: Extract Method + Strategy Pattern with Protocol-based interfaces

**Rationale**:
- **Extract Method**: Break down ~1,630 lines into smaller, focused functions (~80-200 lines each)
- **Strategy Pattern**: Use Protocol to define testable interfaces (allows mocking infrastructure layer)
- **Proven Success**: Phase 3.1-3.8 used same approach for 44 functions (68.9% migration)

**Alternatives Considered**:
- ❌ **Big-Bang Refactor**: Rewrite entire function at once
  - Rejected: Too risky, hard to validate incrementally
- ❌ **State Machine**: Model rendering as state transitions
  - Rejected: Over-engineering for linear rendering pipeline
- ❌ **Event-Driven**: Publish/subscribe for rendering steps
  - Rejected: Adds complexity without clear benefit

**References**:
- Martin Fowler's "Refactoring" (Extract Method pattern)
- Phase 3.1-3.8 success with incremental migration
- Python typing.Protocol for structural subtyping

---

### 2. Protocol-Based Design for Testability

**Decision**: Define Protocol interfaces for each major rendering component

**Rationale**:
- **Testability**: Protocols allow mocking without inheritance
- **Flexibility**: Infrastructure layer can evolve independently
- **Type Safety**: MyPy can validate Protocol compliance

**Protocol Hierarchy**:
```python
# Layer Protocol (base)
class Layer(Protocol):
    def render(self) -> Any: ...  # MoviePy Clip
    def get_bbox(self) -> Dict[str, int]: ...

# Specific Layer Implementations
class LettersLayer(Protocol):
    def render_with_context(self, ctx: VideoRenderingContext) -> Any: ...

class ChineseZhuyinLayer(Protocol):
    def render_with_layout(self, layout: Dict[str, Any]) -> Any: ...

# Composer Protocol
class IVideoComposer(Protocol):
    def compose_layers(self, layers: List[Any]) -> Any: ...
    def export(self, output_path: str) -> None: ...
```

**Alternatives Considered**:
- ❌ **Abstract Base Classes (ABC)**: Requires inheritance
  - Rejected: Protocol is more Pythonic, less coupling
- ❌ **Duck Typing**: No type checking
  - Rejected: Want MyPy validation
- ❌ **Dependency Injection Container**: IoC framework
  - Rejected: Overkill for this scope

**References**:
- PEP 544 (Protocol specification)
- Existing `infrastructure/video/interface.py` (IVideoComposer)
- Phase 3.1-3.8 contract tests

---

### 3. Context Preparation Pattern

**Decision**: Single `_prepare_all_context()` function to gather all rendering inputs

**Rationale**:
- **Single Source of Truth**: All context prepared upfront
- **Testability**: Context can be mocked/stubbed
- **Clear Dependencies**: Makes data flow explicit

**Context Structure**:
```python
class VideoRenderingContext:
    item: Dict[str, Any]           # Original JSON config
    layout: Dict[str, Any]         # From domain.layout
    timeline: Dict[str, Any]       # From domain.timing
    entry_ctx: Dict[str, Any]      # From application.context_builder
    ending_ctx: Dict[str, Any]     # From application.context_builder
    letters_ctx: Dict[str, Any]    # From application.context_builder
    metadata: Dict[str, Any]       # Additional computed info
```

**Alternatives Considered**:
- ❌ **Lazy Loading**: Load context as needed
  - Rejected: Hard to track dependencies, error-prone
- ❌ **Builder Pattern**: Fluent API for context construction
  - Rejected: Over-engineering, unnecessary complexity
- ❌ **Separate Context Objects**: Multiple context types
  - Rejected: Too many parameters, hard to pass around

**References**:
- Existing `application/context_builder.py` functions
- Phase 3.1-3.8 context preparation pattern

---

### 4. Backward Compatibility Strategy

**Decision**: Lightweight wrappers in utils.py with DeprecationWarning

**Rationale**:
- **Zero Breakage**: All >30 existing tests pass without modification
- **Clear Migration Path**: Warnings guide developers to new API
- **Timeline**: v2.0 will remove wrappers entirely

**Wrapper Pattern**:
```python
def render_video_moviepy(item, out_path, dry_run=False, skip_ending=False):
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.video_service.render_video
    """
    warnings.warn(
        "render_video_moviepy is deprecated. "
        "Use application.video_service.render_video instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from spellvid.application.video_service import render_video
    return render_video(item, out_path, dry_run, skip_ending)
```

**Alternatives Considered**:
- ❌ **Direct Removal**: Delete old functions immediately
  - Rejected: Breaks >30 tests, high risk
- ❌ **Duplicate Code**: Keep both old and new implementations
  - Rejected: Maintenance burden, divergence risk
- ❌ **Proxy Classes**: Wrap new API with old interface
  - Rejected: Adds complexity, wrappers are simpler

**References**:
- Phase 3.1-3.8 ~30 deprecated wrappers (working well)
- Python warnings module best practices

---

### 5. TDD Workflow for Refactoring

**Decision**: Write tests for each sub-function before implementation

**Rationale**:
- **Constitutional Requirement**: TDD mandatory (Principle I)
- **Safety Net**: Tests catch regressions during refactoring
- **Design Validation**: Hard-to-test functions indicate design issues

**TDD Cycle**:
```
1. Write test for _prepare_all_context()
   - Test fails (function doesn't exist yet)
2. Extract context preparation code from render_video_moviepy
3. Run test - passes
4. Commit: "feat: extract _prepare_all_context()"
5. Repeat for next function (_create_background_clip, etc.)
```

**Test Types**:
- **Unit Tests**: Each sub-function in isolation
  - Mock infrastructure dependencies (MoviePy, FFmpeg)
  - Fast execution (<1 second per test)
- **Contract Tests**: Protocol compliance
  - Verify function signatures match Protocol
  - Type checking with MyPy
- **Integration Tests**: Complete pipeline
  - Use real MoviePy/FFmpeg
  - Validate 7 example videos render identically

**Alternatives Considered**:
- ❌ **Refactor First, Test Later**: Write tests after code
  - Rejected: Violates constitution, high risk
- ❌ **Only Integration Tests**: Skip unit tests
  - Rejected: Slow, hard to isolate failures
- ❌ **Manual Testing**: No automated tests
  - Rejected: Non-repeatable, error-prone

**References**:
- SpellVid Constitution (Principle I: TDD mandatory)
- Phase 3.1-3.8 TDD success (contract tests first)
- pytest best practices

---

### 6. Function Boundaries Analysis

**Decision**: Split render_video_moviepy into 11 functions based on logical responsibilities

**Rationale**: Each function should have a single, clear purpose with minimal side effects

**Function Breakdown** (~1,630 lines total):

1. **_prepare_all_context()** (~80-130 lines)
   - Responsibility: Gather all inputs (layout, timeline, entry/ending/letters contexts)
   - Input: `item: Dict[str, Any]`
   - Output: `VideoRenderingContext`
   - Dependencies: domain.layout, domain.timing, application.context_builder

2. **_create_background_clip()** (~100-150 lines)
   - Responsibility: Create background (image or color)
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: infrastructure.video.moviepy_adapter

3. **_render_letters_layer()** (~150-180 lines)
   - Responsibility: Render letter images in top-left
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: infrastructure.video.moviepy_adapter

4. **_render_chinese_zhuyin_layer()** (~180-200 lines)
   - Responsibility: Render Chinese + Zhuyin in top-right
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: domain.typography, infrastructure.rendering.pillow_adapter

5. **_render_timer_layer()** (~70-90 lines)
   - Responsibility: Countdown timer in top-left corner
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: infrastructure.rendering.pillow_adapter

6. **_render_reveal_layer()** (~150-200 lines)
   - Responsibility: Word reveal animation (typing effect)
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: infrastructure.rendering.pillow_adapter

7. **_render_progress_bar_layer()** (~80-120 lines)
   - Responsibility: Bottom progress bar
   - Input: `ctx: VideoRenderingContext`
   - Output: `Clip` (MoviePy)
   - Dependencies: infrastructure.ui.progress_bar

8. **_process_audio_tracks()** (~180-270 lines)
   - Responsibility: Mix music + beeps
   - Input: `ctx: VideoRenderingContext`
   - Output: `AudioClip` (MoviePy)
   - Dependencies: infrastructure.media.audio, infrastructure.media.ffmpeg_wrapper

9. **_load_entry_ending_clips()** (~100-150 lines)
   - Responsibility: Load optional entry/ending videos
   - Input: `ctx: VideoRenderingContext`
   - Output: `Tuple[Optional[Clip], Optional[Clip]]`
   - Dependencies: infrastructure.video.moviepy_adapter

10. **_compose_and_export()** (~150-200 lines)
    - Responsibility: Combine all layers + audio, export
    - Input: `ctx: VideoRenderingContext`, `layers: List[Clip]`, `audio: AudioClip`
    - Output: `None` (side effect: writes MP4)
    - Dependencies: infrastructure.video.interface.IVideoComposer

11. **render_video()** (~50-80 lines)
    - Responsibility: Orchestration (call all sub-functions)
    - Input: `item: Dict[str, Any]`, `out_path: str`, etc.
    - Output: `Dict[str, Any]` (result metadata)
    - Dependencies: All above functions

**Total**: ~1,240-1,650 lines (matches original ~1,630 lines)

**Alternatives Considered**:
- ❌ **Fewer Functions (5-7)**: Larger, multi-purpose functions
  - Rejected: Still too complex, hard to test
- ❌ **More Functions (15-20)**: Very granular functions
  - Rejected: Too many parameters to pass, over-fragmentation
- ❌ **Class-Based**: RenderingPipeline class with methods
  - Rejected: Functions are simpler, Protocol is sufficient

**References**:
- Single Responsibility Principle (SOLID)
- Existing render_video_moviepy structure analysis
- Phase 3.1-3.8 function sizes (~50-200 lines)

---

### 7. Git Strategy for Incremental Migration

**Decision**: Feature branch with commit-per-function approach

**Rationale**:
- **Rollback Safety**: Each commit is a stable checkpoint
- **Review Granularity**: Easy to review small changes
- **Bisect-Friendly**: Can pinpoint regressions

**Git Workflow**:
```bash
# Start from clean state
git checkout 005-phase-3-10
git pull origin 005-phase-3-10

# For each sub-function:
# 1. Write test
git add tests/unit/application/test_video_service.py
git commit -m "test: add test for _prepare_all_context()"

# 2. Extract function
git add spellvid/application/video_service.py
git commit -m "feat: extract _prepare_all_context() from render_video_moviepy"

# 3. Run tests
pytest tests/ -x  # Stop on first failure
# If fail: git reset --hard HEAD~1

# 4. Repeat for next function
```

**Branch Protection**:
- ✅ All tests must pass before merge
- ✅ Code review required
- ✅ CI/CD validation (pytest + render_example.ps1)

**Alternatives Considered**:
- ❌ **Single Large Commit**: All changes at once
  - Rejected: Hard to review, no rollback granularity
- ❌ **Separate Branch Per Function**: 11 feature branches
  - Rejected: Merge conflict nightmare
- ❌ **Squash All Commits**: Clean history but lose checkpoints
  - Rejected: Want bisect-friendly history

**References**:
- Git best practices (atomic commits)
- Phase 3.1-3.8 incremental approach
- Feature Branch Workflow (Constitution requirement)

---

### 8. Performance Validation Strategy

**Decision**: Baseline + continuous monitoring during migration

**Rationale**:
- **Regression Detection**: Catch slowdowns early
- **Optimization Targets**: Identify bottlenecks
- **Success Criteria**: <5% overhead (spec requirement)

**Baseline Measurement** (Phase 3.1-3.8):
```powershell
# Measure current performance
Measure-Command { python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 }
# Expected: ~15-20 seconds for 10-second video

Measure-Command { pytest tests/ }
# Expected: ~2-3 minutes (without pytest-xdist)
```

**Continuous Monitoring**:
```bash
# After each function extraction, measure:
pytest tests/integration/test_end_to_end_migration.py --durations=10

# If >5% slower:
# 1. Profile with cProfile
# 2. Optimize hot path
# 3. Re-measure
```

**Alternatives Considered**:
- ❌ **No Performance Testing**: Assume no regression
  - Rejected: Spec requires <5% overhead validation
- ❌ **Only Final Performance Test**: Test after all changes
  - Rejected: Can't pinpoint which function caused slowdown
- ❌ **Micro-Benchmarks**: Benchmark each function individually
  - Rejected: E2E performance more important

**References**:
- Spec FR-010 (performance requirement)
- pytest --durations flag
- Python cProfile profiler

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Refactoring Pattern** | Extract Method + Protocol | Proven in Phase 3.1-3.8, testable |
| **Interface Design** | typing.Protocol | Testability without inheritance |
| **Context Management** | Single VideoRenderingContext | Clear data flow, mockable |
| **Backward Compatibility** | Deprecated wrappers | Zero breakage, clear migration path |
| **TDD Workflow** | Test-first for each function | Constitutional requirement |
| **Function Count** | 11 functions (~80-200 lines each) | Single responsibility, testable |
| **Git Strategy** | Commit per function | Rollback safety, review granularity |
| **Performance** | Baseline + continuous monitoring | Catch regressions early |

---

## Unknowns Resolved

✅ All NEEDS CLARIFICATION items resolved:
- ✅ How to split 1,630 lines → 11 functions with clear boundaries
- ✅ How to maintain backward compatibility → Deprecated wrappers
- ✅ How to ensure testability → Protocol-based design
- ✅ How to validate no regressions → TDD + performance monitoring
- ✅ How to roll back if needed → Git commit-per-function

---

## Next Steps

**Phase 1**: Design & Contracts
1. Define VideoRenderingContext in data-model.md
2. Create Protocol definitions in contracts/
3. Write contract tests (must fail)
4. Generate quickstart.md with TDD example
5. Update .github/copilot-instructions.md

**Ready for Phase 1**: ✅ All research complete, no blockers
