# Implementation Plan: 專案架構重構 - 職責分離與降低耦合度

# Implementation Plan: [FEATURE]

**Branch**: `002-refactor-architecture` | **Date**: 2025-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-refactor-architecture/spec.md`**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)

```## Execution Flow (/plan command scope)

1. Load feature spec from Input path```

   ✓ Spec loaded successfully1. Load feature spec from Input path

2. Fill Technical Context (scan for NEEDS CLARIFICATION)   → If not found: ERROR "No feature spec at {path}"

   ✓ Project Type: Single Python CLI project2. Fill Technical Context (scan for NEEDS CLARIFICATION)

   ✓ Structure Decision: Layered architecture within spellvid/   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)

3. Fill the Constitution Check section   → Set Structure Decision based on project type

   ✓ All gates evaluated based on constitution v1.0.03. Fill the Constitution Check section based on the content of the constitution document.

4. Evaluate Constitution Check section below4. Evaluate Constitution Check section below

   ✓ No constitutional violations - refactoring aligns with code quality principles   → If violations exist: Document in Complexity Tracking

   ✓ Update Progress Tracking: Initial Constitution Check   → If no justification possible: ERROR "Simplify approach first"

5. Execute Phase 0 → research.md   → Update Progress Tracking: Initial Constitution Check

   → In progress5. Execute Phase 0 → research.md

6. Execute Phase 1 → contracts, data-model.md, quickstart.md   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"

   → Pending Phase 0 completion6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).

7. Re-evaluate Constitution Check section7. Re-evaluate Constitution Check section

   → Pending Phase 1 completion   → If new violations: Refactor design, return to Phase 1

8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)   → Update Progress Tracking: Post-Design Constitution Check

   → Completed8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)

9. STOP - Ready for /tasks command9. STOP - Ready for /tasks command

``````



**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:

- Phase 2: /tasks command creates tasks.md- Phase 2: /tasks command creates tasks.md

- Phase 3-4: Implementation execution (manual or via tools)- Phase 3-4: Implementation execution (manual or via tools)



## Summary## Summary

[Extract from feature spec: primary requirement + technical approach from research]

**Primary Requirement**: 重構 SpellVid 專案代碼，將目前的 3600+ 行 `utils.py` 單體架構拆分為分層、職責明確的模組架構，實現：

- 清晰的架構層次（輸入層 → 應用層 → 領域層 → 基礎設施層）## Technical Context

- 單向依賴流動（外層依賴內層，內層不依賴外層）**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  

- 業務邏輯與框架解耦（核心邏輯不直接依賴 MoviePy/Pillow）**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  

- 可替換的基礎設施介面（透過 Port/Adapter 模式）**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  

**Technical Approach**: 採用分層架構 (Layered Architecture) 搭配六邊形架構 (Ports & Adapters) 理念，透過以下步驟實現：**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

1. 分析現有代碼，識別功能邊界與依賴關係**Project Type**: [single/web/mobile - determines source structure]  

2. 定義各層職責與介面契約**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  

3. 漸進式重構，每次移動一組相關函數到新模組**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  

4. 確保每次移動後所有測試仍然通過（向後相容）**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

5. 為新模組補充單元測試，提升隔離測試能力

## Constitution Check

## Technical Context*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*



**Language/Version**: Python 3.11+ (專案目前使用 Python 3.x)  [Gates determined based on constitution file]

**Primary Dependencies**: MoviePy (視頻合成), Pillow (文字渲染), NumPy (陣列操作), FFmpeg (編碼), jsonschema (資料驗證), pydub (音訊處理)  

**Storage**: 檔案系統 (JSON 配置, MP4 輸出, 媒體資源)  ## Project Structure

**Testing**: pytest + pytest-cov (單元測試與覆蓋率), opencv-python (視覺驗證), pydub (音訊驗證)  

**Target Platform**: Windows 11 (主要), Linux (CI/CD)  ### Documentation (this feature)

**Project Type**: Single Python CLI project  ```

**Performance Goals**: specs/[###-feature]/

- 批次處理 100 支影片不超過原有執行時間的 110%├── plan.md              # This file (/plan command output)

- 單支影片渲染時間不受重構影響├── research.md          # Phase 0 output (/plan command)

- 測試套件執行時間不增加（目標：提升獨立測試速度）├── data-model.md        # Phase 1 output (/plan command)

├── quickstart.md        # Phase 1 output (/plan command)

**Constraints**: ├── contracts/           # Phase 1 output (/plan command)

- 向後相容性：CLI 介面不變, JSON Schema 不變└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)

- 漸進式重構：每次變更必須保持測試通過```

- 零停機：現有功能在重構期間持續可用

- 測試驅動：新模組必須先有測試，後有實作### Source Code (repository root)

<!--

**Scale/Scope**:   ACTION REQUIRED: Replace the placeholder tree below with the concrete layout

- 代碼規模：~4000 行生產代碼 (spellvid/), ~2500 行測試代碼 (tests/)  for this feature. Delete unused options and expand the chosen structure with

- 重構範圍：spellvid/ 目錄下所有模組  real paths (e.g., apps/admin, packages/something). The delivered plan must

- 測試套件：~25 個測試檔案需要確保通過  not include Option labels.

- 新增模組：預估 12-15 個新模組檔案-->

```

## Constitution Check# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*src/

├── models/

### I. Test-First Development (TDD)├── services/

- ✅ **PASS**: 重構計畫遵循 TDD 原則├── cli/

  - 每次模組移動前，確保現有測試覆蓋該功能└── lib/

  - 新模組介面需先撰寫契約測試

  - 重構過程使用 Red-Green-Refactor 循環（測試失敗 → 修復 → 重構）tests/

  - 目標：提升測試隔離性，讓每層可獨立測試├── contract/

├── integration/

### II. Code Quality & Style Consistency└── unit/

- ✅ **PASS**: 符合代碼品質要求

  - 所有新模組遵循 PEP 8 與 snake_case 命名# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)

  - 公開函數必須具有型別提示與 docstringbackend/

  - 模組級文檔說明職責範圍├── src/

  - 內部輔助函數以 `_` 前綴（允許測試匯入）│   ├── models/

│   ├── services/

### III. Backward Compatibility│   └── api/

- ✅ **PASS**: 確保向後相容└── tests/

  - CLI 介面 (`make`, `batch` 命令) 完全不變

  - JSON Schema 保持不變frontend/

  - 現有的整合測試必須持續通過├── src/

  - 資源路徑解析邏輯維持一致│   ├── components/

  - FFmpeg 偵測順序不改變│   ├── pages/

│   └── services/

### IV. Security & Input Validation└── tests/

- ✅ **PASS**: 保持安全性

  - 資料驗證邏輯獨立為 `shared/validation.py`# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)

  - 檔案路徑處理集中管理，防止路徑遍歷攻擊api/

  - subprocess 呼叫使用參數化（現有做法維持）└── [same as backend above]

  - 不引入新的敏感資料處理

ios/ or android/

### V. Asset & Environment Management└── [platform-specific structure: feature modules, UI flows, platform tests]

- ✅ **PASS**: 環境管理不變```

  - 虛擬環境隔離維持

  - FFmpeg 偵測優先順序保持（env vars → repo-local → imageio-ffmpeg）**Structure Decision**: [Document the selected structure and reference the real

  - 資源檢查透過 `check_assets()` 繼續執行directories captured above]

  - headless 渲染能力維持（CI/CD 友善）

## Phase 0: Outline & Research

### Testing Strategy Requirements1. **Extract unknowns from Technical Context** above:

- ✅ **PASS**: 測試策略強化   - For each NEEDS CLARIFICATION → research task

  - 繼續使用 pytest + pytest-cov   - For each dependency → best practices task

  - 視覺驗證與音訊驗證邏輯保留   - For each integration → patterns task

  - 整合測試不受影響

  - **增強**：新增各層的獨立單元測試（不依賴 MoviePy 啟動）2. **Generate and dispatch research agents**:

  - **增強**：引入契約測試驗證介面設計   ```

   For each unknown in Technical Context:

### Development Workflow Standards     Task: "Research {unknown} for {feature context}"

- ✅ **PASS**: 開發流程遵守   For each technology choice:

  - Feature Branch Workflow（當前已在 `002-refactor-architecture` 分支）     Task: "Find best practices for {tech} in {domain}"

  - Conventional Commits 格式   ```

  - PowerShell 腳本相容性

  - 文檔更新（新增模組文檔）3. **Consolidate findings** in `research.md` using format:

   - Decision: [what was chosen]

**Constitution Compliance**: ✅ 完全合規，無需偏離憲法原則   - Rationale: [why chosen]

   - Alternatives considered: [what else evaluated]

## Project Structure

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Documentation (this feature)

```## Phase 1: Design & Contracts

specs/002-refactor-architecture/*Prerequisites: research.md complete*

├── plan.md              # This file (/plan command output)

├── spec.md              # Feature specification (already exists)1. **Extract entities from feature spec** → `data-model.md`:

├── research.md          # Phase 0 output (/plan command) - TO BE CREATED   - Entity name, fields, relationships

├── data-model.md        # Phase 1 output (/plan command) - TO BE CREATED   - Validation rules from requirements

├── quickstart.md        # Phase 1 output (/plan command) - TO BE CREATED   - State transitions if applicable

├── contracts/           # Phase 1 output (/plan command) - TO BE CREATED

│   ├── function-contracts.md2. **Generate API contracts** from functional requirements:

│   └── test-contracts.md   - For each user action → endpoint

└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)   - Use standard REST/GraphQL patterns

```   - Output OpenAPI/GraphQL schema to `/contracts/`



### Source Code (repository root)3. **Generate contract tests** from contracts:

```   - One test file per endpoint

spellvid/   - Assert request/response schemas

├── __init__.py                    # 套件初始化（保留現有）   - Tests must fail (no implementation yet)

├── cli/                           # 【新增】輸入適配層

│   ├── __init__.py4. **Extract test scenarios** from user stories:

│   ├── parser.py                  # CLI 參數解析   - Each story → integration test scenario

│   └── commands.py                # make/batch 命令實作   - Quickstart test = story validation steps

├── application/                   # 【新增】應用服務層

│   ├── __init__.py5. **Update agent file incrementally** (O(1) operation):

│   ├── video_service.py           # 單支視頻生成服務   - Run `.specify/scripts/bash/update-agent-context.sh copilot`

│   ├── batch_service.py           # 批次處理服務     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.

│   └── resource_checker.py        # 資源完整性檢查   - If exists: Add only NEW tech from current plan

├── domain/                        # 【新增】領域邏輯層   - Preserve manual additions between markers

│   ├── __init__.py   - Update recent changes (keep last 3)

│   ├── layout.py                  # 佈局計算純邏輯   - Keep under 150 lines for token efficiency

│   ├── effects.py                 # 效果組合規則   - Output to repository root

│   ├── typography.py              # 文字與注音處理

│   └── timing.py                  # 時間軸與計時器**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

├── infrastructure/                # 【新增】基礎設施層

│   ├── __init__.py## Phase 2: Task Planning Approach

│   ├── video/*This section describes what the /tasks command will do - DO NOT execute during /plan*

│   │   ├── __init__.py

│   │   ├── interface.py           # IVideoComposer 介面**Task Generation Strategy**:

│   │   └── moviepy_adapter.py     # MoviePy 實作- Load `.specify/templates/tasks-template.md` as base

│   ├── media/- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)

│   │   ├── __init__.py- Each contract → contract test task [P]

│   │   ├── interface.py           # IMediaProcessor 介面- Each entity → model creation task [P] 

│   │   └── ffmpeg_wrapper.py      # FFmpeg 包裝器- Each user story → integration test task

│   └── rendering/- Implementation tasks to make tests pass

│       ├── __init__.py

│       ├── interface.py           # ITextRenderer 介面**Ordering Strategy**:

│       └── pillow_adapter.py      # Pillow 適配器- TDD order: Tests before implementation 

├── shared/                        # 【新增】共用元件- Dependency order: Models before services before UI

│   ├── __init__.py- Mark [P] for parallel execution (independent files)

│   ├── types.py                   # 型別定義（VideoConfig, LayoutBox, etc.）

│   ├── constants.py               # 常數（顏色、尺寸、路徑）**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

│   └── validation.py              # Schema 驗證邏輯

├── cli.py                         # 【保留】向後相容，委派給 cli/ 模組**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

└── utils.py                       # 【逐步淘汰】暫時保留，函數逐步移至新模組

## Phase 3+: Future Implementation

tests/*These phases are beyond the scope of the /plan command*

├── unit/                          # 【新增】單元測試目錄

│   ├── domain/**Phase 3**: Task execution (/tasks command creates tasks.md)  

│   ├── application/**Phase 4**: Implementation (execute tasks.md following constitutional principles)  

│   └── infrastructure/**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

├── integration/                   # 【整理】整合測試（從現有測試遷移）

│   ├── test_video_rendering.py## Complexity Tracking

│   └── test_batch_processing.py*Fill ONLY if Constitution Check has violations that must be justified*

├── contract/                      # 【新增】契約測試

│   ├── test_video_composer_contract.py| Violation | Why Needed | Simpler Alternative Rejected Because |

│   └── test_text_renderer_contract.py|-----------|------------|-------------------------------------|

└── [現有測試檔案保留]            # 確保向後相容| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |

| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

.specify/

└── memory/

    └── constitution.md            # 憲法文件（已存在）## Progress Tracking

```*This checklist is updated during execution flow*



**Structure Decision**: 選擇 Single Project 結構，因為 SpellVid 是純 CLI 應用，無 frontend/backend 分離需求。採用分層目錄組織（cli/ application/ domain/ infrastructure/ shared/），每層職責明確，依賴關係單向。**Phase Status**:

- [ ] Phase 0: Research complete (/plan command)

## Phase 0: Outline & Research- [ ] Phase 1: Design complete (/plan command)

- [ ] Phase 2: Task planning complete (/plan command - describe approach only)

### Research Tasks- [ ] Phase 3: Tasks generated (/tasks command)

- [ ] Phase 4: Implementation complete

由於架構重構主要是組織現有代碼而非引入新技術，研究重點在於：- [ ] Phase 5: Validation passed



#### 1. 現有代碼分析**Gate Status**:

**Task**: 分析 `spellvid/utils.py` 和 `spellvid/cli.py` 的函數依賴關係- [ ] Initial Constitution Check: PASS

- 目標：識別哪些函數屬於哪一層- [ ] Post-Design Constitution Check: PASS

- 工具：靜態分析（grep, AST 解析）- [ ] All NEEDS CLARIFICATION resolved

- 輸出：函數分類表（函數名 → 建議目標模組）- [ ] Complexity deviations documented



#### 2. 測試依賴分析---

**Task**: 分析現有 25 個測試檔案對內部函數的依賴*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*

- 目標：識別哪些內部函數 (`_xxx`) 被測試直接匯入
- 輸出：測試依賴清單（測試檔 → 依賴的內部函數）
- 決策依據：這些函數在重構後需保持可測試性

#### 3. 介面設計模式研究
**Task**: 研究 Python 中介面定義的最佳實踐
- 選項 A：`typing.Protocol` (結構化子類型, Python 3.8+)
- 選項 B：`abc.ABC` (名義子類型, 需明確繼承)
- 選項 C：Duck typing (無明確介面)
- 決策標準：型別檢查支援、IDE 自動完成、測試模擬難易度

#### 4. 漸進式重構策略研究
**Task**: 研究大型模組拆分的最佳實踐
- 模式 A：Strangler Fig Pattern（新模組與舊模組並存，逐步替換）
- 模式 B：Branch by Abstraction（先建立抽象層，再遷移實作）
- 模式 C：Big Bang Refactoring（一次性重構）
- 決策標準：風險管理、測試持續通過、code review 負擔

#### 5. MoviePy 適配器設計研究
**Task**: 研究如何抽象化 MoviePy 的 Clip 概念
- 挑戰：MoviePy 的 `VideoClip`, `ImageClip`, `TextClip` 如何統一
- 目標：定義與框架無關的 `Clip` 介面
- 參考：類似的視頻處理抽象層設計（如 FFmpeg-python, OpenCV）

### Research Outputs (research.md)

研究文檔將包含以下決策：

1. **介面定義方式**: 選擇 `typing.Protocol` 或 `abc.ABC`
2. **重構順序**: 決定從哪一層開始（建議：由內而外，先 domain/）
3. **測試策略**: 決定如何維護測試通過率（建議：每次移動一組函數後立即執行測試）
4. **Adapter 模式細節**: 定義 `IVideoComposer`, `ITextRenderer` 的方法簽名
5. **向後相容層**: 決定 `utils.py` 如何委派給新模組（re-export 或 deprecation warning）

**Output**: `specs/002-refactor-architecture/research.md`

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1. Data Model Design (`data-model.md`)

#### Core Entities

從規格文件提取的關鍵實體：

**VideoConfig** (領域物件)
```python
@dataclass
class VideoConfig:
    letters: str
    word_en: str
    word_zh: str
    image_path: Optional[str]
    music_path: Optional[str]
    countdown_sec: float
    reveal_hold_sec: float
    entry_hold_sec: float
    timer_visible: bool
    progress_bar: bool
    letters_as_image: bool
    # ... 其他配置欄位
```

**LayoutBox** (值物件)
```python
@dataclass
class LayoutBox:
    x: int
    y: int
    width: int
    height: int
```

**RenderContext** (應用層物件)
```python
@dataclass
class RenderContext:
    config: VideoConfig
    layout: Dict[str, LayoutBox]  # "letters", "word_zh", "timer", etc.
    assets: Dict[str, Any]  # 已載入的資源
    duration: float
```

**IVideoComposer** (基礎設施介面)
```python
class IVideoComposer(Protocol):
    def create_clip(self, type: str, **kwargs) -> Any: ...
    def compose_clips(self, clips: List[Any]) -> Any: ...
    def render_to_file(self, clip: Any, output_path: str) -> None: ...
```

**ITextRenderer** (基礎設施介面)
```python
class ITextRenderer(Protocol):
    def render_text_image(
        self, 
        text: str, 
        font: str, 
        size: int, 
        color: Tuple[int, int, int]
    ) -> Image: ...
```

### 2. API Contracts Generation (`contracts/`)

#### Function Contracts (`contracts/function-contracts.md`)

每個模組的公開函數契約：

**domain/layout.py**
```python
def compute_layout_bboxes(
    config: VideoConfig,
    video_size: Tuple[int, int] = (1920, 1080)
) -> Dict[str, LayoutBox]:
    """
    計算所有視覺元素的邊界框位置
    
    Args:
        config: 視頻配置物件
        video_size: 視頻解析度 (width, height)
    
    Returns:
        各元素名稱 -> LayoutBox 的映射
        
    Raises:
        ValueError: 當字母字串為空或配置無效時
    """
```

**application/video_service.py**
```python
def render_video(
    config: VideoConfig,
    output_path: str,
    composer: IVideoComposer,
    renderer: ITextRenderer
) -> Dict[str, Any]:
    """
    渲染單支視頻
    
    Args:
        config: 視頻配置
        output_path: 輸出檔案路徑
        composer: 視頻合成引擎
        renderer: 文字渲染引擎
    
    Returns:
        {"status": "ok", "output": output_path} 或錯誤資訊
    """
```

#### Test Contracts (`contracts/test-contracts.md`)

每個模組的測試契約：

**tests/unit/domain/test_layout.py**
```python
def test_compute_layout_returns_all_required_boxes():
    """確保 compute_layout_bboxes 回傳所有必要的邊界框"""
    
def test_compute_layout_respects_safe_margins():
    """確保計算的位置不超出安全邊界"""
    
def test_compute_layout_handles_long_letters():
    """確保長字母串能正確計算佈局"""
```

**tests/contract/test_video_composer_contract.py**
```python
def test_moviepy_adapter_satisfies_contract():
    """驗證 MoviePy 適配器實作了 IVideoComposer 的所有方法"""
    
def test_composer_create_clip_returns_valid_object():
    """確保 create_clip 回傳的物件可被 compose_clips 接受"""
```

### 3. Contract Test Implementation

為每個介面生成失敗的測試（TDD 原則）：

```python
# tests/contract/test_video_composer_contract.py
def test_moviepy_adapter_implements_interface():
    from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter
    from spellvid.infrastructure.video.interface import IVideoComposer
    
    adapter = MoviePyAdapter()
    # 這個測試會失敗，因為介面和適配器尚未實作
    assert isinstance(adapter, IVideoComposer)
```

### 4. Quickstart Extraction (`quickstart.md`)

從使用者場景提取的快速驗證步驟：

```markdown
# Quickstart: 驗證架構重構

## 場景 1: 獨立測試領域邏輯
```bash
# 無需 MoviePy，純邏輯測試
pytest tests/unit/domain/test_layout.py -v
```

## 場景 2: 測試介面契約
```bash
# 驗證適配器實作了介面
pytest tests/contract/ -v
```

## 場景 3: 驗證向後相容性
```bash
# 所有現有測試應持續通過
pytest tests/test_integration.py -v
```

## 場景 4: 端到端測試
```bash
# CLI 介面不變，應正常運作
python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 \
  --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4
```
```

### 5. Agent Context Update

執行腳本更新 `.github/copilot-instructions.md`：

```bash
.specify/scripts/bash/update-agent-context.sh copilot
```

更新內容包括：
- 新的目錄結構說明
- 各層職責描述
- 重構期間的開發注意事項
- 測試策略更新

**Output**: 
- `data-model.md`: 實體與介面定義
- `contracts/function-contracts.md`: 函數契約
- `contracts/test-contracts.md`: 測試契約
- `quickstart.md`: 驗證步驟
- `.github/copilot-instructions.md`: 更新後的代理指引

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

### Task Generation Strategy

**輸入來源**:
- Phase 1 的 `data-model.md` → 實體與介面定義任務
- `contracts/function-contracts.md` → 公開 API 實作任務
- `contracts/test-contracts.md` → 測試撰寫任務
- `quickstart.md` → 驗收驗證任務

**生成規則**:
1. **基礎設施介面定義** → 每個介面一個任務 [P]
   - 例如: Task: Define IVideoComposer interface in infrastructure/video/interface.py
   
2. **契約測試** → 每個介面一個測試任務 [P]
   - 例如: Task: Write contract test for IVideoComposer
   
3. **領域邏輯提取** → 每個邏輯模組一組任務
   - 例如: 
     - Task: Extract layout calculation to domain/layout.py
     - Task: Add unit tests for domain/layout.py
     
4. **適配器實作** → 每個適配器一個任務
   - 例如: Task: Implement MoviePyAdapter for IVideoComposer
   
5. **應用層服務** → 每個服務一組任務
   - 例如:
     - Task: Implement video_service.py using domain + infrastructure
     - Task: Add integration test for video_service.py
     
6. **CLI 層重構** → 委派任務
   - 例如: Task: Refactor cli.py to delegate to application layer

### Ordering Strategy

**依賴順序**（由內而外）:
1. **Phase 2a: 基礎建設**
   - 定義共用型別 (`shared/types.py`)
   - 定義常數 (`shared/constants.py`)
   - 定義驗證邏輯 (`shared/validation.py`)
   
2. **Phase 2b: 基礎設施介面**
   - 定義 `IVideoComposer`, `ITextRenderer`, `IMediaProcessor` 介面
   - 撰寫契約測試（測試會失敗）
   
3. **Phase 2c: 領域邏輯**
   - 提取 `layout.py`, `typography.py`, `timing.py`, `effects.py`
   - 撰寫單元測試（不依賴 MoviePy）
   
4. **Phase 2d: 基礎設施實作**
   - 實作 `moviepy_adapter.py`, `pillow_adapter.py`, `ffmpeg_wrapper.py`
   - 使契約測試通過
   
5. **Phase 2e: 應用服務**
   - 實作 `video_service.py`, `batch_service.py`, `resource_checker.py`
   - 撰寫整合測試
   
6. **Phase 2f: CLI 層**
   - 重構 `cli.py` 委派給 `cli/commands.py`
   - 確保所有現有測試通過
   
7. **Phase 2g: 清理與文檔**
   - 標記 `utils.py` 為 deprecated
   - 更新 README 與模組文檔
   - 執行 quickstart.md 驗證

**並行執行標記 [P]**:
- 同一層內的模組可並行開發
- 例如: `layout.py`, `typography.py`, `timing.py` 可同時進行
- 介面定義任務可並行

### Estimated Output

預估任務數量：
- 基礎建設: 3 任務
- 介面定義: 3 任務 [P]
- 契約測試: 3 任務 [P]
- 領域邏輯: 4 模組 × 2 (實作+測試) = 8 任務
- 適配器實作: 3 任務
- 應用服務: 3 模組 × 2 = 6 任務
- CLI 重構: 2 任務
- 清理文檔: 2 任務

**總計**: ~30 個有序任務，tasks.md 將包含完整的任務編號、依賴關係與驗收標準

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (manual or via coding agent)
- 開發者/代理逐一執行 tasks.md 中的任務
- 每個任務完成後執行 `pytest` 確保無迴歸
- Code review 確保符合 Constitution 要求

**Phase 4**: Integration validation
- 執行完整測試套件: `pytest tests/ -v --cov=spellvid`
- 執行 quickstart.md 中的所有場景
- 效能驗證: 批次渲染 100 支影片，確保執行時間 ≤ 110% baseline

**Phase 5**: Documentation & Rollout
- 更新 README.md 說明新架構
- 撰寫 MIGRATION.md 指引（如有需要）
- 合併到 main 分支
- 通知團隊新的模組組織方式

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | No constitutional violations |

**Status**: ✅ 無憲法偏離，所有原則均獲遵守

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
  - [x] 現有代碼分析完成
  - [x] 測試依賴分析完成
  - [x] 介面設計模式決策完成
  - [x] 漸進式重構策略決策完成
  - [x] MoviePy 適配器設計完成
  - [x] research.md 文檔產出
- [x] Phase 1: Design complete (/plan command)
  - [x] data-model.md 產出
  - [x] contracts/function-contracts.md 產出
  - [x] contracts/test-contracts.md 產出
  - [x] 契約測試實作（失敗狀態 - 規範已定義,實作在 Phase 3）
  - [x] quickstart.md 產出
  - [x] Agent context 更新 (.github/copilot-instructions.md)
- [x] Phase 2: Task planning complete (/tasks command)
  - [x] 任務生成策略定義
  - [x] 任務排序策略定義
  - [x] 預估任務數量 (實際: 41 個任務)
  - [x] tasks.md 產出
- [ ] Phase 3: Implementation (execute tasks.md)
  - [ ] T001-T041 任務執行
  - [ ] 每個任務完成後 commit
  - [ ] 持續驗證測試通過
- [ ] Phase 4: Validation passed
  - [ ] quickstart.md 4 個場景全部通過
  - [ ] 效能驗證 (≤110% baseline)
  - [ ] 覆蓋率目標達成 (85%)

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (Phase 1 complete, no new violations)
- [x] All NEEDS CLARIFICATION resolved (N/A - no clarifications needed)
- [x] Complexity deviations documented (N/A - no deviations)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
