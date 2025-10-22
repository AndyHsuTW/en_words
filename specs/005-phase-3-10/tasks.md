# Tasks: Phase 3.10 - Core Rendering Refactor

**Input**: Design documents from `/specs/005-phase-3-10/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Generated**: 2025-10-22  
**Branch**: `005-phase-3-10`  
**Target**: Refactor render_video_moviepy (~1,630 lines) → 11 sub-functions, reduce utils.py to 120 lines

---

## Execution Flow

```
Phase 0: Setup (T001-T002)
  → Environment validation, branch verification

Phase 1: TDD Foundation (T003)
  → Run contract tests (expect 24 failures)

Phase 2: Context & Background (T004-T006)
  → VideoRenderingContext + 2 functions

Phase 3: Rendering Layers (T007-T011) [P]
  → 5 layer rendering functions (Letters, Chinese, Timer, Reveal, ProgressBar)

Phase 4: Media & Composition (T012-T014)
  → Audio processing + Entry/Ending + Compose/Export

Phase 5: Orchestration (T015)
  → render_video() refactor

Phase 6: Backward Compatibility (T016-T017)
  → Deprecated wrappers in utils.py

Phase 7: Cleanup (T018-T019)
  → Remove old code, reduce utils.py to 120 lines

Phase 8: Validation (T020-T022)
  → Test suite + integration + performance

Phase 9: Documentation (T023-T025)
  → AGENTS.md + ARCHITECTURE.md + IMPLEMENTATION_SUMMARY.md
```

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions
- **TDD Requirement**: Write test → verify FAIL → implement → verify PASS → commit

---

## Phase 0: Setup

- [x] **T001** Validate environment and dependencies ✅
  - **File**: N/A (environment check)
  - **Actions**:
    - Verify Python 3.11.9 active: `python --version`
    - Verify virtual environment: `.\.venv\Scripts\Activate.ps1`
    - Verify dependencies: `pip list | findstr "moviepy pillow numpy pydub jsonschema pytest"`
    - Verify branch: `git branch --show-current` (should be `005-phase-3-10`)
    - Verify all tests passing: `pytest tests/ -x` (baseline)
  - **Expected**: All checks pass, 0 test failures
  - **Rollback**: N/A (read-only)
  - **Commit**: No commit (validation only)
  - **Result**: Python 3.13.0, all dependencies installed, branch correct, 0 test failures

- [x] **T002** Establish performance baseline ✅
  - **File**: N/A (measurement)
  - **Actions**:
    - Measure render time: `Measure-Command { python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 }`
    - Measure test time: `Measure-Command { pytest tests/ }`
    - Record baseline metrics (render: ~15-20s, tests: ~2-3min)
  - **Expected**: Baseline metrics recorded
  - **Rollback**: N/A (read-only)
  - **Commit**: No commit (measurement only)
  - **Result**: Render time: 49.4s (Cat video), Test time: 1.8s

---

## Phase 1: TDD Foundation

- [x] **T003** Run contract tests to establish RED state ✅
  - **File**: `tests/contract/test_phase310_rendering_protocol.py`
  - **Actions**:
    - Run: `pytest tests/contract/test_phase310_rendering_protocol.py -v`
    - Verify: 24 tests FAIL (functions not yet implemented)
    - Document: Expected failures (VideoRenderingContext, 11 sub-functions, wrappers)
  - **Expected**: 24 failures ✅ (TDD RED state)
  - **Rollback**: N/A (read-only)
  - **Commit**: No commit (validation only)
  - **Result**: 22 FAILED, 1 PASSED (render_video exists), RED state confirmed ✅

---

## Phase 2: Context & Background

- [x] **T004** [P] Create VideoRenderingContext dataclass ✅
  - **File**: `spellvid/application/video_service.py`
  - **Actions**:
    - Copy dataclass definition from `specs/005-phase-3-10/contracts/rendering_protocol.py`
    - Add imports: `from typing import Dict, Any`, `from dataclasses import dataclass`
    - Add docstring (same as contract)
  - **Expected**: VideoRenderingContext defined, importable
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `feat: add VideoRenderingContext dataclass to video_service`
  - **Result**: Commit f212eac ✅

- [x] **T005** Extract _prepare_all_context() (TDD) ✅
  - **Files**: 
    - Test: `tests/unit/application/test_video_service.py` (NEW)
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴): Commit 6a02189 ✅
    2. **Extract function** (GREEN 🟢): Commit 8fd8515 ✅
  - **Result**: 4 tests passing, function extracted ✅

- [x] **T006** Extract _create_background_clip() (TDD) ✅
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴): Commit 4df44bf ✅
    2. **Extract function** (GREEN 🟢): Commit 32ac0c5 ✅
  - **Result**: 2 tests passing, handles image/video and solid color ✅

- [ ] **T007** [P] Extract _render_letters_layer() (TDD)
  - **Files**: 
    - Test: `tests/unit/application/test_video_service.py` (NEW)
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Create `tests/unit/application/test_video_service.py`
       - Copy test from `quickstart.md` (test_prepare_all_context_with_valid_item)
       - Run: `pytest tests/unit/application/test_video_service.py::test_prepare_all_context_with_valid_item -v`
       - **Verify FAIL**: ImportError (function doesn't exist)
       - Commit: `test: add test for _prepare_all_context()`
    2. **Extract function** (GREEN 🟢):
       - In `video_service.py`: Extract context preparation from render_video_moviepy (~80-130 lines)
       - Signature: `def _prepare_all_context(item: Dict[str, Any]) -> VideoRenderingContext:`
       - Gather: layout, timeline, entry_ctx, ending_ctx, letters_ctx, metadata
       - Dependencies: `domain.layout`, `domain.timing`, `application.context_builder`
       - Run: `pytest tests/unit/application/test_video_service.py::test_prepare_all_context_with_valid_item -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _prepare_all_context() from render_video_moviepy`
  - **Expected**: Test passes, function extractable, 0 new test failures
  - **Rollback**: `git reset --hard HEAD~2` (removes test + impl)

- [ ] **T006** Extract _create_background_clip() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_create_background_clip_with_image()` to test_video_service.py
       - Add `test_create_background_clip_with_solid_color()` to test_video_service.py
       - Run: `pytest tests/unit/application/test_video_service.py -k background -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add tests for _create_background_clip()`
    2. **Extract function** (GREEN 🟢):
       - Extract background rendering from render_video_moviepy (~100-150 lines)
       - Signature: `def _create_background_clip(ctx: VideoRenderingContext) -> Any:`
       - Handle: image background OR solid color background
       - Dependencies: `infrastructure.rendering.pillow_adapter`, `infrastructure.video.moviepy_adapter`
       - Run: `pytest tests/unit/application/test_video_service.py -k background -v`
       - **Verify PASS**: Tests green ✅
       - Commit: `feat: extract _create_background_clip() from render_video_moviepy`
  - **Expected**: 2 tests pass, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

---

## Phase 3: Rendering Layers (Parallelizable)

- [ ] **T007** [P] Extract _render_letters_layer() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_letters_layer()` to test_video_service.py
       - Test: letter images loaded, positioned, composited
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_letters_layer -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _render_letters_layer()`
    2. **Extract function** (GREEN 🟢):
       - Extract letters rendering from render_video_moviepy (~150-180 lines)
       - Signature: `def _render_letters_layer(ctx: VideoRenderingContext) -> Any:`
       - Load letter images from letters_ctx, position using layout["letters_bbox"]
       - Dependencies: `infrastructure.video.moviepy_adapter`, `domain.layout._letter_asset_filename`
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_letters_layer -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _render_letters_layer() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T008** [P] Extract _render_chinese_zhuyin_layer() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_chinese_zhuyin_layer()` to test_video_service.py
       - Test: Chinese text + zhuyin rendered, positioned correctly
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_chinese_zhuyin_layer -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _render_chinese_zhuyin_layer()`
    2. **Extract function** (GREEN 🟢):
       - Extract Chinese/Zhuyin rendering from render_video_moviepy (~180-200 lines)
       - Signature: `def _render_chinese_zhuyin_layer(ctx: VideoRenderingContext) -> Any:`
       - Render Chinese + Zhuyin using layout["chinese_bbox"]
       - Dependencies: `domain.typography.parse_zhuyin`, `infrastructure.rendering.pillow_adapter`
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_chinese_zhuyin_layer -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _render_chinese_zhuyin_layer() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T009** [P] Extract _render_timer_layer() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_timer_layer()` to test_video_service.py
       - Test: Timer shows countdown (3...2...1), positioned correctly
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_timer_layer -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _render_timer_layer()`
    2. **Extract function** (GREEN 🟢):
       - Extract timer rendering from render_video_moviepy (~70-90 lines)
       - Signature: `def _render_timer_layer(ctx: VideoRenderingContext) -> Any:`
       - Render countdown timer using timeline["countdown_start"], layout["timer_bbox"]
       - Dependencies: `infrastructure.rendering.pillow_adapter`, `domain.effects`
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_timer_layer -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _render_timer_layer() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T010** [P] Extract _render_reveal_layer() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_reveal_layer()` to test_video_service.py
       - Test: Word reveal animation (typing effect), positioned at bottom center
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_reveal_layer -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _render_reveal_layer()`
    2. **Extract function** (GREEN 🟢):
       - Extract reveal rendering from render_video_moviepy (~150-200 lines)
       - Signature: `def _render_reveal_layer(ctx: VideoRenderingContext) -> Any:`
       - Render typing effect using timeline["reveal_start"], layout["reveal_bbox"]
       - Dependencies: `infrastructure.video.effects`, `domain.effects`
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_reveal_layer -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _render_reveal_layer() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T011** [P] Extract _render_progress_bar_layer() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_progress_bar_layer()` to test_video_service.py
       - Test: Progress bar animates from 0% to 100%, positioned at bottom
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_progress_bar_layer -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _render_progress_bar_layer()`
    2. **Extract function** (GREEN 🟢):
       - Extract progress bar rendering from render_video_moviepy (~80-120 lines)
       - Signature: `def _render_progress_bar_layer(ctx: VideoRenderingContext) -> Any:`
       - Render progress bar using timeline["total_duration"], layout["progress_bar_bbox"]
       - Dependencies: `infrastructure.video.effects`, `infrastructure.rendering.pillow_adapter`
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_progress_bar_layer -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _render_progress_bar_layer() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

---

## Phase 4: Media & Composition

- [ ] **T012** Extract _process_audio_tracks() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_process_audio_tracks()` to test_video_service.py
       - Test: Music + beeps mixed, correct duration
       - Run: `pytest tests/unit/application/test_video_service.py::test_process_audio_tracks -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _process_audio_tracks()`
    2. **Extract function** (GREEN 🟢):
       - Extract audio processing from render_video_moviepy (~180-270 lines)
       - Signature: `def _process_audio_tracks(ctx: VideoRenderingContext) -> Any:`
       - Mix music + beeps using timeline["countdown_start"]
       - Dependencies: `infrastructure.media.audio`, `infrastructure.media.ffmpeg_wrapper`
       - Run: `pytest tests/unit/application/test_video_service.py::test_process_audio_tracks -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _process_audio_tracks() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T013** Extract _load_entry_ending_clips() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_load_entry_ending_clips()` to test_video_service.py
       - Test: Entry/ending clips loaded when enabled, None when disabled
       - Run: `pytest tests/unit/application/test_video_service.py::test_load_entry_ending_clips -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _load_entry_ending_clips()`
    2. **Extract function** (GREEN 🟢):
       - Extract entry/ending loading from render_video_moviepy (~100-150 lines)
       - Signature: `def _load_entry_ending_clips(ctx: VideoRenderingContext) -> Tuple[Optional[Any], Optional[Any]]:`
       - Load clips from entry_ctx, ending_ctx (respect skip_ending flag)
       - Dependencies: `infrastructure.video.moviepy_adapter`
       - Run: `pytest tests/unit/application/test_video_service.py::test_load_entry_ending_clips -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _load_entry_ending_clips() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

- [ ] **T014** Extract _compose_and_export() (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_compose_and_export()` to test_video_service.py
       - Test: All layers composited, MP4 exported
       - Run: `pytest tests/unit/application/test_video_service.py::test_compose_and_export -v`
       - **Verify FAIL**: ImportError
       - Commit: `test: add test for _compose_and_export()`
    2. **Extract function** (GREEN 🟢):
       - Extract composition from render_video_moviepy (~150-200 lines)
       - Signature: `def _compose_and_export(ctx, layers, audio, output_path, composer=None) -> None:`
       - Compose layers + audio, export using IVideoComposer
       - Dependencies: `infrastructure.video.interface.IVideoComposer`, `infrastructure.video.moviepy_adapter`
       - Run: `pytest tests/unit/application/test_video_service.py::test_compose_and_export -v`
       - **Verify PASS**: Test green ✅
       - Commit: `feat: extract _compose_and_export() from render_video_moviepy`
  - **Expected**: Test passes, function extractable
  - **Rollback**: `git reset --hard HEAD~2`

---

## Phase 5: Orchestration

- [ ] **T015** Refactor render_video() to orchestrate sub-functions (TDD)
  - **Files**:
    - Test: `tests/unit/application/test_video_service.py`
    - Impl: `spellvid/application/video_service.py`
  - **TDD Cycle**:
    1. **Write test** (RED 🔴):
       - Add `test_render_video_orchestration()` to test_video_service.py
       - Test: render_video() calls all sub-functions in correct order
       - Use mocks to verify call sequence
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_video_orchestration -v`
       - **Verify FAIL**: Test expects new API
       - Commit: `test: add orchestration test for render_video()`
    2. **Refactor function** (GREEN 🟢):
       - Create new `render_video()` in `video_service.py` (~50-80 lines)
       - Signature: `def render_video(item, out_path, dry_run=False, skip_ending=False, composer=None) -> Dict[str, Any]:`
       - Call all 10 sub-functions in sequence:
         1. ctx = _prepare_all_context(item)
         2. bg = _create_background_clip(ctx)
         3. letters = _render_letters_layer(ctx)
         4. chinese = _render_chinese_zhuyin_layer(ctx)
         5. timer = _render_timer_layer(ctx)
         6. reveal = _render_reveal_layer(ctx)
         7. progress = _render_progress_bar_layer(ctx)
         8. audio = _process_audio_tracks(ctx)
         9. entry, ending = _load_entry_ending_clips(ctx)
         10. _compose_and_export(ctx, layers, audio, out_path, composer)
       - Run: `pytest tests/unit/application/test_video_service.py::test_render_video_orchestration -v`
       - **Verify PASS**: Test green ✅
       - Commit: `refactor: rewrite render_video() to orchestrate 11 sub-functions`
  - **Expected**: Test passes, render_video() orchestrates all sub-functions
  - **Rollback**: `git reset --hard HEAD~2`
  - **Validation**: Run `pytest tests/integration/test_end_to_end_migration.py -v` (must pass)

---

## Phase 6: Backward Compatibility

- [ ] **T016** Create deprecated wrapper for render_video_moviepy
  - **File**: `spellvid/utils.py`
  - **Actions**:
    - Remove old render_video_moviepy implementation (~1,630 lines)
    - Add lightweight wrapper (~10-15 lines):
      ```python
      def render_video_moviepy(item, out_path, dry_run=False, skip_ending=False):
          """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除
          
          使用 application.video_service.render_video 代替
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
    - Add imports: `import warnings`
  - **Expected**: Wrapper delegates to new API, triggers DeprecationWarning
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `refactor: replace render_video_moviepy with deprecated wrapper`

- [ ] **T017** Create deprecated wrapper for render_video_stub
  - **File**: `spellvid/utils.py`
  - **Actions**:
    - Keep render_video_stub implementation (metadata computation, ~283 lines)
    - Add DeprecationWarning at top of function:
      ```python
      warnings.warn(
          "render_video_stub is deprecated. "
          "Use application.video_service.render_video with dry_run=True.",
          DeprecationWarning,
          stacklevel=2
      )
      ```
    - NOTE: render_video_stub will be fully refactored in future phase
  - **Expected**: Wrapper triggers DeprecationWarning, functionality unchanged
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `refactor: add deprecation warning to render_video_stub`

---

## Phase 7: Cleanup

- [ ] **T018** Remove old render_video_moviepy code
  - **File**: `spellvid/utils.py`
  - **Actions**:
    - Verify: render_video_moviepy is now a lightweight wrapper (~10-15 lines)
    - Remove: All old implementation code (~1,630 lines removed in T016)
    - Keep: ~30 deprecated wrappers + essential constants
    - Verify: All imports still valid, no broken references
  - **Expected**: utils.py reduced by ~1,630 lines (2,944 → ~1,314 lines)
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `cleanup: remove old render_video_moviepy implementation`

- [ ] **T019** Final utils.py reduction to target line count
  - **File**: `spellvid/utils.py`
  - **Actions**:
    - Review: Remaining ~1,314 lines
    - Target: ~120 lines (96.77% total reduction)
    - Keep: 
      - ~30 deprecated wrappers (~15-20 lines each = ~450-600 lines)
      - Essential constants re-exports (~50-100 lines)
      - DeprecationWarning helpers (~20 lines)
    - Remove: 
      - Redundant helper functions (move to appropriate layers if needed)
      - Commented-out code
      - Unnecessary imports
    - **NOTE**: If unable to reach exactly 120 lines, document justification
      - Minimum target: <200 lines (93.2% reduction)
      - Ideal target: ~120 lines (95.9% reduction)
  - **Expected**: utils.py at ~120 lines (or <200 lines with justification)
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `cleanup: reduce utils.py to target line count (~120 lines)`

---

## Phase 8: Validation

- [ ] **T020** Run full test suite (0 failures required)
  - **File**: N/A (test execution)
  - **Actions**:
    - Run: `pytest tests/ -v --tb=short`
    - Verify: 0 failures (all >30 test files pass)
    - Check: DeprecationWarnings visible in output (expected)
    - Fix: Any test failures (update tests if needed)
  - **Expected**: 0 failures, all tests green ✅
  - **Rollback**: Fix failures, re-run
  - **Commit**: No commit (validation only)

- [ ] **T021** Integration test with render_example.ps1
  - **File**: N/A (integration test)
  - **Actions**:
    - Run: `.\scripts\render_example.ps1`
    - Verify: 7 MP4 files generated in `out/` directory
    - Verify: Each MP4 playable, content correct (letters, Chinese, timer, reveal, progress bar)
    - Compare: File sizes similar to Phase 3.1-3.8 baseline (±10% acceptable)
  - **Expected**: 7 MP4 files, all valid, visually correct
  - **Rollback**: Investigate failures, fix bugs
  - **Commit**: No commit (validation only)

- [ ] **T022** Performance validation (<5% overhead)
  - **File**: N/A (performance measurement)
  - **Actions**:
    - Measure: Render time per video (compare to T002 baseline)
    - Measure: Test suite execution time (compare to T002 baseline)
    - Verify: <5% overhead (spec requirement)
    - If >5%: Profile with `python -m cProfile`, optimize hot paths
  - **Expected**: <5% overhead vs baseline
  - **Rollback**: Optimize if regression found
  - **Commit**: No commit (measurement only)

---

## Phase 9: Documentation

- [ ] **T023** [P] Update AGENTS.md with Phase 3.10 completion status
  - **File**: `AGENTS.md`
  - **Actions**:
    - Update migration status: 44/64 → 55/64 functions (or final count)
    - Update utils.py status: 2,944 → ~120 lines (95.9% reduction)
    - Document: 11 new functions in application/video_service.py
    - Update: Deprecation warnings section (render_video_moviepy, render_video_stub)
  - **Expected**: AGENTS.md reflects Phase 3.10 completion
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `docs: update AGENTS.md with Phase 3.10 completion`

- [ ] **T024** [P] Update ARCHITECTURE.md with new structure
  - **File**: `doc/ARCHITECTURE.md`
  - **Actions**:
    - Add: Section on video rendering architecture
    - Document: 11 sub-functions and their responsibilities
    - Document: VideoRenderingContext dataclass
    - Document: Protocol-based design (Layer, IVideoComposer)
    - Update: Deprecated layer (utils.py wrappers)
  - **Expected**: ARCHITECTURE.md reflects new rendering pipeline
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `docs: update ARCHITECTURE.md with Phase 3.10 changes`

- [ ] **T025** [P] Create IMPLEMENTATION_SUMMARY.md
  - **File**: `specs/005-phase-3-10/IMPLEMENTATION_SUMMARY.md`
  - **Actions**:
    - Summarize: What was implemented (11 functions, 24 tests, wrappers)
    - Document: Line count reduction (2,944 → 120 lines, 95.9%)
    - Document: Test results (0 failures, 7 MP4s, <5% overhead)
    - Document: Lessons learned, challenges, future work
    - Reference: quickstart.md, research.md, data-model.md
  - **Expected**: Complete summary of Phase 3.10 implementation
  - **Rollback**: `git reset --hard HEAD~1`
  - **Commit**: `docs: add Phase 3.10 implementation summary`

---

## Dependencies

**Sequential Dependencies**:
- T001-T002 (Setup) → T003 (TDD Foundation) → T004-T006 (Context)
- T004 (VideoRenderingContext) → T005-T015 (all rendering functions depend on context)
- T005 (_prepare_all_context) → T006-T014 (other functions need context preparation)
- T006-T014 (all sub-functions) → T015 (render_video orchestration)
- T015 (render_video) → T016-T017 (wrappers need new API)
- T016-T017 (wrappers) → T018-T019 (cleanup)
- T018-T019 (cleanup) → T020-T022 (validation)
- T020-T022 (validation) → T023-T025 (documentation)

**Parallel Opportunities**:
- T007-T011 [P]: 5 layer functions (different responsibilities, no shared code)
- T023-T025 [P]: 3 documentation updates (different files)
- Within TDD cycles: Test writing can happen in parallel (same test file, different functions)

**Critical Path**:
```
T001 → T002 → T003 → T004 → T005 → [T006-T014] → T015 → [T016-T017] → [T018-T019] → [T020-T022] → [T023-T025]
                                      ↑ Can parallelize 9 extraction tasks ↑
```

---

## Parallel Execution Examples

**Example 1: Layer Functions (T007-T011)**
```powershell
# Can work on these simultaneously (different responsibilities):
# Terminal 1: T007 (Letters layer)
# Terminal 2: T008 (Chinese/Zhuyin layer)
# Terminal 3: T009 (Timer layer)
# Terminal 4: T010 (Reveal layer)
# Terminal 5: T011 (Progress bar layer)

# Each follows TDD: test → fail → extract → pass → commit
```

**Example 2: Documentation (T023-T025)**
```powershell
# Can update these files in parallel (no conflicts):
# Terminal 1: T023 (AGENTS.md)
# Terminal 2: T024 (ARCHITECTURE.md)
# Terminal 3: T025 (IMPLEMENTATION_SUMMARY.md)
```

---

## Task Validation Checklist

**Pre-Implementation** (before starting tasks):
- [x] All contracts have corresponding tests → 24 contract tests in test_phase310_rendering_protocol.py ✅
- [x] All 11 sub-functions have contract definitions → rendering_protocol.py ✅
- [x] VideoRenderingContext entity defined → data-model.md ✅
- [x] TDD workflow documented → quickstart.md ✅
- [x] Agent context updated → copilot-instructions.md ✅

**During Implementation** (per task):
- [ ] Test written before implementation (RED state) ✅
- [ ] Implementation makes test pass (GREEN state) ✅
- [ ] No new test failures introduced ✅
- [ ] Commit after each TDD cycle ✅
- [ ] Rollback strategy documented ✅

**Post-Implementation** (after all tasks):
- [ ] 0 test failures (T020) ✅
- [ ] 7 MP4 files generated (T021) ✅
- [ ] <5% performance overhead (T022) ✅
- [ ] utils.py at ~120 lines (T019) ✅
- [ ] Documentation updated (T023-T025) ✅

---

## Notes

**TDD Discipline**:
- **MANDATORY**: Write test → verify FAIL → implement → verify PASS → commit
- **NO SHORTCUTS**: Do not implement without failing test first
- **RED-GREEN-REFACTOR**: Follow cycle strictly (see quickstart.md)

**Rollback Strategy**:
- Each task pair (test + impl) = 2 commits
- Rollback: `git reset --hard HEAD~2` removes both commits
- Safe checkpoints: After each TDD cycle

**Performance Monitoring**:
- Measure after each extraction (T006-T014)
- If >5% overhead: Profile with cProfile, optimize
- Acceptable: <5% overhead vs baseline (T002)

**Line Count Tracking**:
- Baseline: 2,944 lines (utils.py before Phase 3.10)
- Target: ~120 lines (95.9% reduction)
- Minimum: <200 lines (93.2% reduction)
- Track after T018, T019

**Success Criteria** (from spec.md):
- ✅ utils.py reduced to ~120 lines
- ✅ 11 functions extracted (single responsibility)
- ✅ 0 test failures (>30 files)
- ✅ 7 MP4 files from render_example.ps1
- ✅ <5% performance overhead
- ✅ Deprecated wrappers with DeprecationWarning
- ✅ TDD followed throughout

---

**Based on**:
- spec.md (13 functional requirements)
- plan.md (Phase 0-1 complete)
- research.md (8 design decisions)
- data-model.md (5 entities)
- contracts/rendering_protocol.py (11 function signatures)
- quickstart.md (TDD workflow)

---

*Generated by .specify workflow - Ready for TDD execution*
