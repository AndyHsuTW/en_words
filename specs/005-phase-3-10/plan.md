
# Implementation Plan: Phase 3.10 - Core Rendering Refactor

**Branch**: `005-phase-3-10` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-phase-3-10/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: 拆分 `render_video_moviepy` (~1,630 lines) 為 10-15 個職責單一的子函數,遷移至三層架構,並將 utils.py 從 2,944 lines 縮減至 120 lines (96.77% total reduction)。

**Technical Approach**: 
1. **TDD First**: 為每個子函數撰寫測試,確保測試失敗後再實作
2. **Incremental Migration**: 每次遷移一個函數並 commit,失敗可回退
3. **Protocol-Based Design**: 使用 Protocol 定義清晰的層次邊界和可測試介面
4. **Backward Compatibility**: 保留輕量級 wrapper 在 utils.py,觸發 DeprecationWarning

**Context from Phase 3.1-3.8**: 44/64 functions 已遷移 (68.9%),剩餘核心渲染函數需要重新設計而非直接遷移。

## Technical Context

**Language/Version**: Python 3.11.9  
**Primary Dependencies**: MoviePy (video composition), Pillow (text rendering), numpy (array operations), pydub (audio), jsonschema (validation)  
**Storage**: File-based (MP4 video output, JSON config input, PNG/MP3 assets)  
**Testing**: pytest + pytest-cov (unit tests), opencv-python (visual validation), pydub (audio validation)  
**Target Platform**: Windows (PowerShell scripts), headless CI/CD compatible  
**Project Type**: Single project (CLI tool for video generation)  
**Performance Goals**: 
- Render time per video: <30 seconds for 10-second output
- Test suite execution: <5 minutes (with pytest-xdist)
- No performance regression: <5% overhead vs Phase 3.1-3.8 baseline
**Constraints**: 
- Must not break >30 existing tests (0 failures required)
- Must maintain backward compatibility during transition
- TDD mandatory: tests before implementation
- Headless rendering support (no GUI dependencies)
**Scale/Scope**: 
- Code reduction: 2,944 → 120 lines in utils.py (95.9% this phase)
- Function split: 2 giant functions → 10-15 small functions
- Test impact: >30 test files require validation
- Integration: 7 MP4 example videos must render identically

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development ✅
- [x] TDD mandatory: Tests written → User approved → Tests fail → Then implement
- [x] Red-Green-Refactor cycle for each sub-function
- [x] Unit tests for 10-15 new functions in application/video_service.py
- [x] Contract tests for Protocol interfaces
- [x] Integration tests for complete render pipeline
- [x] Target: >80% coverage maintained (currently >95%)
- [x] Tests independent, deterministic, headless-compatible

**Status**: COMPLIANT - TDD approach explicitly required in spec (FR-006)

### II. Code Quality & Style Consistency ✅
- [x] PEP 8 with 4-space indentation and snake_case
- [x] Type hints for all public functions (Protocol definitions)
- [x] Docstrings for public APIs
- [x] Internal helpers with underscore prefix
- [x] Maintain compatibility with existing architecture (3-layer)

**Status**: COMPLIANT - Follows established patterns from Phase 3.1-3.8

### III. Backward Compatibility ✅
- [x] utils.py wrappers maintain function signatures
- [x] DeprecationWarning for deprecated APIs
- [x] CLI interface unchanged
- [x] Asset path resolution unchanged
- [x] FFmpeg integration unchanged
- [x] All >30 existing tests must pass

**Status**: COMPLIANT - Explicit requirement (FR-004)

### IV. Security & Input Validation ✅
- [x] JSON schema validation (existing SCHEMA maintained)
- [x] File path normalization (existing check_assets)
- [x] No new security surface (internal refactoring only)

**Status**: COMPLIANT - No changes to external inputs

### V. Asset & Environment Management ✅
- [x] Virtual environment isolation (.venv)
- [x] FFmpeg detection unchanged
- [x] Asset validation via check_assets()
- [x] Headless rendering support maintained
- [x] Proper context managers for resources

**Status**: COMPLIANT - Infrastructure layer unchanged

### Testing Strategy Requirements ✅
- [x] Pytest framework with pytest-cov
- [x] Visual validation (opencv-python for boundaries)
- [x] Audio validation (pydub for waveforms)
- [x] Integration tests (complete pipeline)
- [x] Contract tests (Protocol signatures)
- [x] Test assets in tests/assets/

**Status**: COMPLIANT - All testing requirements met

### Development Workflow Standards ✅
- [x] Feature Branch: 005-phase-3-10
- [x] Conventional Commits format
- [x] PowerShell script compatibility
- [x] Documentation updates (AGENTS.md, ARCHITECTURE.md)
- [x] Agent context updated via update-agent-context.sh

**Status**: COMPLIANT - Standard workflow followed

### Initial Constitution Check Result: ✅ PASS
No violations. All constitutional principles satisfied by design.

## Project Structure

### Documentation (this feature)
```
specs/005-phase-3-10/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (refactoring patterns, Protocol design)
├── data-model.md        # Phase 1 output (Context, Pipeline, Layer models)
├── quickstart.md        # Phase 1 output (TDD workflow example)
├── contracts/           # Phase 1 output (Protocol definitions)
│   ├── rendering_protocol.py      # IVideoComposer, Layer protocols
│   ├── context_protocol.py        # VideoRenderingContext structure
│   └── pipeline_protocol.py       # RenderingPipeline interface
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
spellvid/
├── shared/                      # Unchanged
│   ├── types.py                 # VideoConfig, etc.
│   ├── constants.py             # CANVAS_WIDTH, PROGRESS_BAR_*, etc.
│   └── validation.py            # SCHEMA
│
├── domain/                      # Unchanged (Phase 3.1-3.8)
│   ├── layout.py                # compute_layout_bboxes, etc.
│   ├── timing.py                # calculate_timeline, etc.
│   ├── effects.py               # Fade effects, etc.
│   └── typography.py            # Zhuyin rendering, etc.
│
├── infrastructure/              # Unchanged (Phase 3.1-3.8)
│   ├── rendering/
│   │   ├── pillow_adapter.py   # _make_text_imageclip
│   │   └── image_loader.py     # Letter image specs
│   ├── video/
│   │   ├── interface.py        # IVideoComposer Protocol
│   │   ├── moviepy_adapter.py  # MoviePy integration
│   │   └── effects.py          # Fade/transition effects
│   ├── media/
│   │   ├── ffmpeg_wrapper.py   # FFmpeg detection
│   │   └── audio.py            # Audio mixing
│   └── ui/
│       └── progress_bar.py     # Progress bar rendering
│
├── application/                 # ⭐ THIS PHASE - Major changes
│   ├── video_service.py         # 🎯 TARGET FILE (will expand significantly)
│   │                            # New functions (10-15):
│   │                            #   - _prepare_all_context()
│   │                            #   - _create_background_clip()
│   │                            #   - _render_letters_layer()
│   │                            #   - _render_chinese_zhuyin_layer()
│   │                            #   - _render_timer_layer()
│   │                            #   - _render_reveal_layer()
│   │                            #   - _render_progress_bar_layer()
│   │                            #   - _process_audio_tracks()
│   │                            #   - _load_entry_ending_clips()
│   │                            #   - _compose_and_export()
│   │                            #   - render_video() (orchestration)
│   ├── context_builder.py       # Unchanged (Phase 3.1-3.8)
│   ├── batch_service.py         # Unchanged
│   └── resource_checker.py      # Unchanged
│
├── cli/                         # Unchanged
│   ├── parser.py
│   └── commands.py
│
└── utils.py                     # ⭐ THIS PHASE - Major reduction
                                 # Before: 2,944 lines
                                 # After: ~120 lines
                                 # Content: 
                                 #   - Deprecated wrappers (~30 functions)
                                 #   - Essential constants re-exports
                                 #   - DeprecationWarning triggers

tests/
├── contract/                    # ⭐ New contract tests
│   ├── test_rendering_protocol.py      # Protocol compliance
│   ├── test_context_protocol.py        # Context structure
│   └── test_pipeline_protocol.py       # Pipeline interface
│
├── unit/                        # ⭐ New unit tests
│   └── application/
│       └── test_video_service.py       # 10-15 new test functions
│           # test_prepare_all_context()
│           # test_create_background_clip()
│           # test_render_letters_layer()
│           # ... (one per sub-function)
│
├── integration/                 # Existing tests (must pass)
│   └── test_end_to_end_migration.py
│
└── [30+ existing test files]    # Must all pass (0 failures)
    test_video_mode.py
    test_layout.py
    test_reveal_stable_positions.py
    test_countdown.py
    ... (all existing tests)
```

**Structure Decision**: Single project structure with established 3-layer architecture (shared → domain → infrastructure → application). This phase focuses on:
1. **application/video_service.py**: Expanding from ~212 lines to ~1,400-1,600 lines (10-15 new functions)
2. **utils.py**: Reducing from 2,944 lines to ~120 lines (removing core rendering, keeping wrappers)
3. **tests/**: Adding contract and unit tests for new functions

**No new layers or modules required** - working within established architecture from Phase 3.1-3.8.

## Phase 0: Outline & Research ✅ COMPLETE

**Research Areas Completed**:
1. ✅ Refactoring patterns for large functions → Extract Method + Protocol
2. ✅ Protocol-based design for testability → typing.Protocol with IVideoComposer
3. ✅ Context preparation pattern → VideoRenderingContext
4. ✅ Backward compatibility strategy → Deprecated wrappers with warnings
5. ✅ TDD workflow for refactoring → Test-first per function
6. ✅ Function boundaries analysis → 11 functions (~80-200 lines each)
7. ✅ Git strategy for incremental migration → Commit per function
8. ✅ Performance validation strategy → Baseline + continuous monitoring

**Key Decisions Documented**:
- 11 sub-functions with clear responsibilities (see research.md section 6)
- Protocol interfaces for testability
- Single VideoRenderingContext for all rendering inputs
- TDD mandatory: test → fail → implement → pass → commit

**Output**: ✅ research.md (8 research areas, all unknowns resolved)

## Phase 1: Design & Contracts ✅ COMPLETE

**Entities Extracted**:
1. ✅ VideoRenderingContext (dataclass) - Single source of truth for rendering inputs
2. ✅ Layer (Protocol) - Interface for renderable layers
3. ✅ IVideoComposer (existing Protocol) - Video composition engine
4. ✅ RenderingPipeline (conceptual model) - Orchestration pattern
5. ✅ DeprecatedWrapper - Backward compatibility pattern

**Contracts Generated**:
- ✅ `contracts/rendering_protocol.py` - Protocol definitions for all 11 sub-functions
  - VideoRenderingContext structure
  - Layer protocol (render, get_bbox, get_duration)
  - IVideoComposer protocol
  - Function signatures for 11 sub-functions
  - Validation functions

**Contract Tests Generated** (Must FAIL initially):
- ✅ `tests/contract/test_phase310_rendering_protocol.py` - 24 tests
  - VideoRenderingContext structure tests
  - Layer protocol compliance tests
  - Sub-function existence tests
  - Deprecated wrapper tests
  - Integration contract test
  - **Status**: All tests expected to FAIL (functions not yet implemented) ✅

**Test Scenarios**:
- ✅ `quickstart.md` - Complete TDD workflow example
  - Step-by-step guide for extracting _prepare_all_context()
  - RED-GREEN-REFACTOR cycle demonstration
  - Rollback strategy, performance monitoring
  - Success criteria checklist

**Agent Context Updated**:
- ✅ `.github/copilot-instructions.md` - Updated with Phase 3.10 context
  - Python 3.11.9, MoviePy, Pillow dependencies
  - File-based storage (MP4, JSON, PNG/MP3)
  - Single project structure

**Output**: ✅ All Phase 1 artifacts created and validated

## Phase 2: Task Planning Approach 📋 READY
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data-model.md, quickstart.md)
- **11 sub-functions** → 11 implementation task pairs (test + extract)
- **VideoRenderingContext** → 1 dataclass creation task
- **Layer implementations** → 5 layer class tasks (optional, can be inline)
- **Deprecated wrappers** → 2 tasks (render_video_stub + render_video_moviepy)
- **Test migration** → 3 tasks (contract tests + unit tests + update existing)
- **Documentation** → 3 tasks (AGENTS.md + ARCHITECTURE.md + IMPLEMENTATION_SUMMARY.md)
- **Validation** → 3 tasks (test suite + integration + performance)

**Ordering Strategy**:
1. **Phase 0 (Setup)**: Environment validation, branch verification
2. **Phase 1 (TDD Foundation)**: Run contract tests (expect failures)
3. **Phase 2 (Context & Background)**: 
   - T001: VideoRenderingContext dataclass [P]
   - T002-T003: _prepare_all_context() + _create_background_clip()
4. **Phase 3 (Rendering Layers)**: [P] = can parallelize
   - T004-T008: Letters, Chinese/Zhuyin, Timer, Reveal, ProgressBar
5. **Phase 4 (Media & Composition)**:
   - T009-T011: Audio, Entry/Ending, Compose/Export
6. **Phase 5 (Orchestration)**:
   - T012: render_video() refactor
7. **Phase 6 (Backward Compatibility)**:
   - T013-T014: Deprecated wrappers in utils.py
8. **Phase 7 (Cleanup)**:
   - T015: Remove old render_video_moviepy code
   - T016: utils.py reduction to 120 lines
9. **Phase 8 (Validation)**:
   - T017-T019: Test suite + integration + performance
10. **Phase 9 (Documentation)**:
    - T020-T022: Update AGENTS.md + ARCHITECTURE.md + summary

**Estimated Output**: ~22-25 numbered, ordered tasks in tasks.md

**Key Dependencies**:
- VideoRenderingContext must exist before any rendering function
- _prepare_all_context() must work before other functions
- All sub-functions must work before render_video() orchestration
- render_video() must work before deprecated wrappers
- All implementation must complete before utils.py cleanup

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Progress Tracking

**Phase 0: Outline & Research**: ✅ COMPLETE (2025-10-22)
- ✅ research.md created (8 research areas)
- ✅ All NEEDS CLARIFICATION resolved
- ✅ Key decisions documented

**Phase 1: Design & Contracts**: ✅ COMPLETE (2025-10-22)
- ✅ data-model.md created (5 entities)
- ✅ contracts/rendering_protocol.py created (11 function signatures + 3 protocols)
- ✅ tests/contract/test_phase310_rendering_protocol.py created (24 tests, expected to FAIL)
- ✅ quickstart.md created (TDD workflow guide)
- ✅ .github/copilot-instructions.md updated

**Phase 2: Task Planning**: 📋 READY FOR /tasks COMMAND
- Approach documented in plan.md
- Estimated 22-25 tasks
- Dependencies mapped

**Phase 3+: Implementation**: ⏳ PENDING (awaits /tasks command)

---

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

✅ **No Violations**: All constitutional principles satisfied by design.

No complexity tracking required for this phase.


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
