# Implementation Plan: 完成新模組實作並真正移除 utils.py 舊程式碼

**Branch**: `004-complete-module-migration` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-complete-module-migration/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   ✅ Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   ✅ Project Type: Single Python project
   ✅ Structure Decision: Modular Python package with layered architecture
3. Fill the Constitution Check section
   ✅ Constitution loaded from .specify/memory/constitution.md
4. Evaluate Constitution Check section
   ✅ No violations detected
   ✅ Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   ✅ Research completed
6. Execute Phase 1 → contracts, data-model.md, quickstart.md
   ✅ Design artifacts generated
7. Re-evaluate Constitution Check section
   ✅ No new violations
   ✅ Progress Tracking: Post-Design Constitution Check PASS
8. Plan Phase 2 → Describe task generation approach
   ✅ Task planning strategy documented
9. STOP - Ready for /tasks command
   ✅ Plan complete, awaiting /tasks
```

**IMPORTANT**: The /plan command STOPS at step 8. Phase 2 execution creates tasks.md via /tasks command.

## Summary

本特性旨在完成 Phase 2 (003-phase2-remove-old-code) 未達成的「完全移除舊程式碼」目標。根據 ACTUAL_COMPLETION_ASSESSMENT.md 的誠實評估,當前 `spellvid/utils.py` 保留了 3,714 行完整實作 (僅新增 DeprecationWarning),移除率為 0%。

**核心技術策略**:
1. **函數使用分析** — 使用多工具交叉驗證 (grep + AST 分析 + 執行時追蹤) 識別三類函數:
   - 生產使用: 被 `spellvid/` (非測試) 或 `scripts/` 引用
   - 測試專用: 僅被 `tests/` 引用 → 視為冗餘
   - 完全未使用: 無任何引用 → 視為冗餘
2. **冗餘函數清理** — 直接刪除 ~10-20 個未被生產代碼使用的函數
3. **有效函數遷移** — 遷移 ~15-25 個生產使用函數至新模組架構 (domain/infrastructure/application)
4. **最小 re-export 層** — 建立 80-120 行的向後相容層
5. **驗證與測試** — 確保所有測試通過,render_example.ps1 正常產出 7 個 MP4 檔案

**預期成果**: utils.py 從 3,714 行縮減至 80-120 行 (≥95% 縮減率),消除技術債,提升程式碼品質。

## Technical Context

**Language/Version**: Python 3.13.0  
**Primary Dependencies**: MoviePy, Pillow, pydub, opencv-python, pytest, pytest-cov  
**Storage**: 檔案系統 (JSON 配置、媒體資產、MP4 輸出)  
**Testing**: pytest (40 test files, 20+ 需更新 import 路徑)  
**Target Platform**: Windows 開發環境 (PowerShell), Linux CI 環境  
**Project Type**: Single Python project (modular architecture)  
**Performance Goals**: 完整測試套件 <5 分鐘 (當前 >30 分鐘, optional SC-9)  
**Constraints**: 
  - 必須維持 100% 向後相容 (現有 import 路徑有效)
  - 所有測試通過 (0 failures)
  - render_example.ps1 成功產出 7 個有效 MP4 檔案
  - FFmpeg 整合維持現有環境變數優先順序
**Scale/Scope**: 
  - 3,714 行 utils.py → 80-120 行 re-export
  - ~50+ 函數 → ~15-25 個有效函數遷移
  - ~10-20 個冗餘函數刪除
  - 20+ 測試檔案 import 更新

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Test-First Development (NON-NEGOTIABLE)
- **Status**: PASS
- **Rationale**: 
  - 本特性為重構任務,現有 40 測試檔案提供完整覆蓋
  - 遷移策略: 每遷移一組函數即執行測試驗證
  - Acceptance Scenario 5-6 明確定義測試失敗處理流程
  - SC-5 要求所有測試通過 (0 failures)
  - SC-6 要求 render_example.ps1 產出 7 個有效 MP4 (整合驗證)

### ✅ II. Code Quality & Style Consistency
- **Status**: PASS
- **Rationale**:
  - 遷移至新模組架構將改善程式碼組織 (分層架構: domain/infrastructure/application)
  - FR-003 要求統一函數簽章,確保相容性
  - 函數處理對應表 (FR-009) 記錄每個函數的處理方式與理由
  - Edge Case 2 明確處理簽章差異 (wrapper/adapter 策略)

### ✅ III. Backward Compatibility
- **Status**: PASS
- **Rationale**:
  - FR-005 要求建立最小 re-export 層,維持現有 import 路徑
  - FR-006 明確「僅刪除實作,保留 re-export」
  - Acceptance Scenario 4 驗證所有現有 import 路徑維持有效
  - Out of Scope 明確排除「改變公開 API 行為或函數簽章」

### ✅ IV. Security & Input Validation
- **Status**: PASS (N/A for this refactoring)
- **Rationale**:
  - 本特性為內部重構,不涉及外部輸入或安全敏感變更
  - 現有 JSON schema 驗證邏輯已在 `spellvid/shared/validation.py`
  - 無新增檔案路徑處理或 subprocess 呼叫

### ✅ V. Asset & Environment Management
- **Status**: PASS
- **Rationale**:
  - FFmpeg 偵測邏輯已在 `spellvid/infrastructure/media/ffmpeg_wrapper.py`
  - 不改變現有環境變數優先順序 (FFMPEG_PATH → repo-local → imageio-ffmpeg)
  - SC-6 驗證 render_example.ps1 正常運作 (資產驗證涵蓋)
  - 虛擬環境隔離已在開發工作流程中強制執行

### Constitution Summary
**Initial Check**: ✅ PASS (All principles satisfied)  
**Post-Design Check**: ⏳ Pending Phase 1 completion  
**Complexity Deviations**: None

## Project Structure

### Documentation (this feature)
```
specs/004-complete-module-migration/
├── spec.md              # Feature specification (完成)
├── plan.md              # This file (本檔案)
├── research.md          # Phase 0 output (函數分析工具研究)
├── data-model.md        # Phase 1 output (函數遷移對應表)
├── quickstart.md        # Phase 1 output (驗證步驟)
├── contracts/           # Phase 1 output (函數簽章契約)
│   ├── usage_analysis.md      # 函數使用分析契約
│   ├── migration_mapping.md   # 遷移對應契約
│   └── reexport_layer.md      # Re-export 層契約
└── tasks.md             # Phase 2 output (/tasks command - 尚未建立)
```

### Source Code (repository root)
```
spellvid/
├── utils.py             # 當前 3,714 行 → 目標 80-120 行 re-export
├── shared/              # 共用型別、常數、驗證
│   ├── types.py
│   ├── constants.py
│   └── validation.py
├── domain/              # 領域邏輯 (純函數)
│   ├── layout.py        # 佈局計算
│   ├── typography.py    # 注音渲染
│   ├── effects.py       # 視覺效果
│   └── timing.py        # 時間軸
├── infrastructure/      # 框架整合適配器
│   ├── rendering/       # Pillow 文字渲染
│   ├── video/           # MoviePy 整合
│   └── media/           # FFmpeg/音訊
├── application/         # 應用服務
│   ├── video_service.py # 視頻生成
│   ├── batch_service.py # 批次處理
│   └── resource_checker.py
└── cli/                 # CLI 命令入口
    ├── commands.py
    └── parser.py

tests/
├── unit/                # 單元測試 (測試單一模組)
├── contract/            # 契約測試 (驗證介面實作)
├── integration/         # 整合測試 (測試多模組協作)
└── test_*.py            # 現有測試 (20+ 檔案需更新 import)

scripts/
├── run_tests.ps1        # 測試套件執行腳本
└── render_example.ps1   # 核心功能驗證腳本 (7 MP4 產出)
```

**Structure Decision**: 採用既有的分層模組架構 (已在 Phase 2 建立)。本特性將完成函數遷移,從單體 utils.py 移至對應模組,並建立最小 re-export 層以維持向後相容。

## Phase 0: Outline & Research

### Unknowns & Research Tasks

1. **函數使用分析工具選擇**:
   - **Unknown**: 如何可靠識別生產使用 vs 測試專用 vs 完全未使用?
   - **Research Task**: 評估 Python 靜態分析工具 (grep, AST analysis, vulture, coverage.py)
   - **Goal**: 選擇多工具交叉驗證策略,降低誤刪風險

2. **函數簽章相容性處理**:
   - **Unknown**: 新模組函數簽章已改變 (如 Dict → VideoConfig),如何建立相容 wrapper?
   - **Research Task**: 研究 Python adapter pattern 最佳實踐
   - **Goal**: 定義 re-export 層的 wrapper 實作策略

3. **測試性能優化方法**:
   - **Unknown**: 完整測試套件 >30 分鐘,如何優化至 <5 分鐘? (SC-9, optional)
   - **Research Task**: 研究 pytest 並行執行、selective testing、fixture 優化
   - **Goal**: 提供測試性能改善建議 (不強制,但記錄供後續參考)

4. **函數鏈依賴識別**:
   - **Unknown**: 如何識別「僅被其他輔助函數呼叫」的未使用函數鏈? (Edge Case 4)
   - **Research Task**: 研究呼叫圖分析工具 (pyan, pycallgraph2)
   - **Goal**: 定義批量移除函數鏈的安全策略

### Research Execution

**Output**: `research.md` 包含:
- 函數使用分析工具評估結果與選擇決策
- Adapter pattern 實作指引與範例
- 測試性能優化建議清單 (optional)
- 函數鏈依賴識別策略與工具使用方法

## Phase 1: Design & Contracts

### 1. Data Model Extraction → `data-model.md`

從 spec.md 的 Key Entities 章節提取函數清單,建立函數處理對應表:

**Entities**:
- **FunctionUsageReport** — 函數使用分析報告
  - function_name: str
  - category: Enum["production", "test_only", "unused"]
  - references: List[FileReference]
  - call_count: int
  
- **FunctionMigration** — 函數遷移對應
  - old_location: str (utils.py)
  - new_location: str (domain/infrastructure/application 模組路徑)
  - migration_status: Enum["deleted", "migrated", "kept"]
  - reason: str (處理理由)
  - wrapper_needed: bool
  
- **ReexportLayer** — Re-export 層定義
  - exported_functions: List[str]
  - import_statements: List[str]
  - aliases: Dict[str, str]
  - deprecation_warnings: List[str]

**State Transitions**:
1. utils.py 函數 (3,714 行) → 使用分析 → FunctionUsageReport
2. FunctionUsageReport → 分類決策 → FunctionMigration (deleted/migrated/kept)
3. FunctionMigration → 遷移執行 → 新模組實作 + ReexportLayer
4. ReexportLayer → 驗證測試 → utils.py 最小化 (80-120 行)

**Output**: `data-model.md` 包含完整的函數對應表與狀態轉換規則

### 2. Contract Generation → `/contracts/`

**Contracts to Generate**:

1. **`usage_analysis.md`** — 函數使用分析契約
   - Input: utils.py 原始檔案
   - Output: FunctionUsageReport JSON (所有函數的使用情況)
   - Validation Rules:
     - 生產使用: 被 `spellvid/*.py` (排除 tests) 或 `scripts/*.py` 引用
     - 測試專用: 僅被 `tests/*.py` 引用
     - 完全未使用: 無任何 .py 檔案引用 (排除 __pycache__, .bak)
   - Cross-validation: grep + AST + coverage 結果必須一致

2. **`migration_mapping.md`** — 遷移對應契約
   - Input: FunctionUsageReport (category="production")
   - Output: FunctionMigration 對應表
   - Mapping Rules:
     - Progress bar 函數 → `domain/effects.py`
     - Video effects 函數 → `infrastructure/video/effects.py`
     - Letter/layout 函數 → `domain/layout.py`
     - Media 函數 → `infrastructure/media/`
     - Entry/Ending 函數 → `application/video_service.py`
   - Signature Compatibility: 需要 wrapper 的函數清單

3. **`reexport_layer.md`** — Re-export 層契約
   - Input: FunctionMigration (status="migrated")
   - Output: 新 utils.py 內容 (80-120 行)
   - Structure:
     - DeprecationWarning (15 行)
     - Import statements (30-50 行)
     - Aliases (15-30 行)
     - __all__ list (20-25 行)
   - Validation: 所有現有 `from spellvid.utils import X` 仍有效

### 3. Contract Tests Generation

**Contract Test Files** (放置於 `tests/contract/`):

1. **`test_usage_analysis_contract.py`**
   - 測試函數使用分析輸出格式正確
   - 驗證三類分類互斥且完整
   - 測試檔案路徑過濾規則 (__pycache__, .bak 被排除)

2. **`test_migration_mapping_contract.py`**
   - 測試遷移對應表完整性 (所有 production 函數都有對應)
   - 驗證新模組路徑存在且可匯入
   - 測試 wrapper 函數簽章相容性

3. **`test_reexport_layer_contract.py`**
   - 測試新 utils.py 行數在 80-120 範圍
   - 驗證所有 re-export 函數可匯入
   - 測試 DeprecationWarning 觸發正常
   - 驗證 __all__ 列表與實際 export 一致

**Initial State**: 所有契約測試應 FAIL (因尚未實作)

### 4. Integration Test Scenarios → `quickstart.md`

從 Acceptance Scenarios 提取驗證步驟:

**Quickstart Validation Steps**:
1. 執行函數使用分析,產生報告 (對應 Scenario 1)
2. 刪除冗餘函數,驗證刪除理由 (對應 Scenario 2)
3. 遷移有效函數至新模組 (對應 Scenario 3)
4. 建立最小 re-export 層 (對應 Scenario 4)
5. 執行測試套件,預期部分測試失敗 (對應 Scenario 5)
6. 更新測試 import 路徑,再次執行測試,預期全通過 (對應 Scenario 6)
7. 執行 render_example.ps1,驗證 7 個 MP4 產出 (對應 Scenario 7)
8. 檢查 utils.py 行數與內容 (對應 Scenario 8-9)

**Output**: `quickstart.md` 包含完整驗證流程與預期結果

### 5. Update Agent Context

執行憲法要求的 agent context 更新:

```bash
.specify/scripts/bash/update-agent-context.sh copilot
```

**更新內容**:
- 新增本特性的技術背景 (函數使用分析、遷移策略)
- 記錄重要檔案閱讀順序 (usage report → migration mapping → reexport layer)
- 保留手動新增內容於標記之間
- 更新最近變更 (保留最後 3 筆)
- 控制在 150 行以內

**Output**: `.github/copilot-instructions.md` 更新

### Phase 1 Outputs Summary
- ✅ `data-model.md` — 函數對應表與狀態轉換 (COMPLETED)
- ✅ `contracts/usage_analysis.md` — 使用分析契約 (COMPLETED)
- ✅ `contracts/migration_mapping.md` — 遷移對應契約 (COMPLETED)
- ✅ `contracts/reexport_layer.md` — Re-export 層契約 (COMPLETED)
- ⏳ `tests/contract/test_*_contract.py` — 3 個契約測試 (待 /tasks 命令生成)
- ✅ `quickstart.md` — 完整驗證流程 (COMPLETED)
- ⏳ `.github/copilot-instructions.md` — Agent context 更新 (待 /tasks 或實作階段)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load Templates & Inputs**:
   - Base: `.specify/templates/tasks-template.md`
   - Inputs: `data-model.md`, `contracts/`, `research.md`

2. **Generate Tasks from Design**:

   **Step 0: 函數使用分析** (3-5h):
   - T001 [P]: 建立函數使用分析腳本 (grep + AST)
   - T002 [P]: 實作呼叫圖分析 (識別函數鏈)
   - T003: 執行分析,產生 FunctionUsageReport
   - T004: 人工審查「待確認」清單,確認分類正確性
   - T005: 完成契約測試 `test_usage_analysis_contract.py`

   **Step 1: 冗餘函數清理** (2-3h):
   - T006 [P]: 刪除完全未使用函數
   - T007 [P]: 刪除測試專用函數
   - T008: 記錄刪除理由於 data-model.md
   - T009: 執行測試確認無意外破壞

   **Step 2: 有效函數遷移** (15-20h):
   - T010-T014 [P]: 遷移 Progress bar 函數至 domain/effects.py
   - T015-T020 [P]: 遷移 Video effects 至 infrastructure/video/effects.py
   - T021-T025 [P]: 遷移 Letter/layout 函數至 domain/layout.py
   - T026-T028 [P]: 遷移 Media 函數至 infrastructure/media/
   - T029-T032 [P]: 遷移 Entry/Ending 函數至 application/video_service.py
   - T033: 完成契約測試 `test_migration_mapping_contract.py`

   **Step 3: 建立最小 re-export 層** (2-3h):
   - T034: 實作 wrapper 函數 (處理簽章差異)
   - T035: 建立新 utils.py (import + alias + __all__)
   - T036: 完成契約測試 `test_reexport_layer_contract.py`
   - T037: 驗證 DeprecationWarning 觸發

   **Step 4: 驗證與測試** (5-8h):
   - T038: 更新 20+ 測試檔案 import 路徑
   - T039: 執行完整測試套件,修正失敗測試
   - T040: 執行 render_example.ps1,驗證 7 個 MP4
   - T041: 測試性能分析 (optional, SC-9)

   **Step 5: 文件與部署** (2-3h):
   - T042: 更新 AGENTS.md (移除「標記但保留」描述)
   - T043: 更新 .github/copilot-instructions.md
   - T044: 建立 IMPLEMENTATION_SUMMARY.md
   - T045: 最終驗證清單檢查

3. **Ordering Strategy**:
   - **Sequential**: Step 0 → Step 1 → Step 2 → Step 3 → Step 4 → Step 5
   - **Parallel within steps**: [P] 標記的任務可並行 (獨立檔案/模組)
   - **TDD order**: Contract tests → Implementation → Validation

4. **Estimated Output**: 
   - **Total Tasks**: 45 個編號任務 (T001-T045)
   - **Parallel Tasks**: ~20 個可並行執行
   - **Critical Path**: Step 0 → Step 1 → Step 2 核心遷移 → Step 3 → Step 4 驗證

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks T001-T045 following constitutional TDD principles)  
**Phase 5**: Validation (SC-1 to SC-9 checklist, render_example.ps1, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | No constitutional violations in this refactoring |

**Note**: 本重構特性完全符合專案憲法要求,無複雜度偏差需記錄。

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [ ] Phase 3: Tasks generated (/tasks command) ⏳
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented (N/A) ✅

**Execution Completion**:
- [x] Step 1: Feature spec loaded ✅
- [x] Step 2: Technical context filled (no NEEDS CLARIFICATION) ✅
- [x] Step 3: Constitution check completed ✅
- [x] Step 4: Initial constitution evaluation PASS ✅
- [x] Step 5: Phase 0 research completed ✅
- [x] Step 6: Phase 1 design artifacts completed ✅
- [x] Step 7: Post-design constitution check PASS ✅
- [x] Step 8: Phase 2 task planning strategy documented ✅
- [x] Step 9: Ready for /tasks command ✅

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
*Plan completed: 2025-10-19*
*Next command: `/tasks` to generate tasks.md*
