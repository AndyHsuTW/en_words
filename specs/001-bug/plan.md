
# Implementation Plan: 修正片尾影片重複播放問題

**Branch**: `001-bug` | **Date**: 2025-10-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bug/spec.md`

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
修正 `render_example.ps1` 腳本中的片尾影片重複播放問題。目前在處理多個單字時，每個單字影片結束都會添加片尾影片，導致最終串接的影片包含多個重複的片尾。技術修正方法：調整影片渲染和串接邏輯，確保片尾影片只在整個批次的最後添加一次。

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: MoviePy, FFmpeg, Pillow, pytest  
**Storage**: 本地檔案系統 (MP4 影片檔案)  
**Testing**: pytest  
**Target Platform**: Windows (PowerShell 腳本)  
**Project Type**: single - Python CLI 工具  
**Performance Goals**: 能夠處理多個影片串接而不影響現有渲染效能  
**Constraints**: 必須維持與現有單一影片處理模式的兼容性  
**Scale/Scope**: 處理 1-10 個單字的批次影片生成

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Test-First Development**: ✅ PASS - 將為修正建立測試，確保片尾影片邏輯正確  
**II. Code Quality & Style Consistency**: ✅ PASS - 遵循現有程式碼風格和架構模式  
**III. Backward Compatibility**: ✅ PASS - 修正不會影響現有單一影片處理功能  
**IV. Security & Input Validation**: ✅ PASS - 使用現有的 JSON schema 驗證和檔案路徑檢查  
**V. Asset & Environment Management**: ✅ PASS - 使用現有的虛擬環境和 FFmpeg 檢測機制

**Post-Design Re-evaluation**: ✅ PASS - 設計階段後重新檢查，所有原則仍然符合

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
spellvid/
├── cli.py               # CLI 進入點 - 可能需要修正批次處理邏輯
├── utils.py             # 核心渲染功能 - 主要修正目標
└── __init__.py

scripts/
├── render_example.py    # 實際處理多影片串接的腳本
└── render_example.ps1   # PowerShell 包裝器

tests/
├── test_batch_concatenation.py  # 測試批次串接功能
├── test_ending_video.py         # 測試片尾影片邏輯  
└── test_integration.py          # 整合測試

assets/
└── ending.mp4           # 片尾影片檔案
```

**Structure Decision**: 單一 Python 專案結構，主要修正集中在 `spellvid/utils.py` 和 `scripts/render_example.py` 中的影片處理邏輯。

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- 基於 Phase 1 設計文件（contracts, data model, quickstart）生成任務
- 遵循 TDD 原則：測試任務優先於實作任務
- 每個合約 → 一個合約測試任務 [P]
- 每個功能修正 → 一個實作任務
- 每個驗證場景 → 一個整合測試任務

**Ordering Strategy**:
- TDD 順序：測試先於實作
- 依賴順序：核心功能修正 → 腳本修正 → 整合測試
- 標記 [P] 表示可平行執行（獨立檔案）

**Estimated Output**: 8-12 個編號任務，包括：
1. 合約測試任務 (3-4 個) [P]
2. 核心功能修正任務 (2-3 個)
3. 腳本邏輯修正任務 (1-2 個)  
4. 整合驗證任務 (2-3 個)

**Task Categories**:
- **BUG-001 到 BUG-004**: 測試建立任務
- **BUG-005 到 BUG-007**: 核心修正實作
- **BUG-008 到 BUG-010**: 腳本和整合修正  
- **BUG-011 到 BUG-012**: 驗證和文件更新

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (無偏差)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
