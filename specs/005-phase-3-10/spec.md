# Feature Specification: Phase 3.10 - Core Rendering Refactor

**Feature Branch**: `005-phase-3-10`  
**Created**: 2025-10-22  
**Status**: Draft  
**Input**: "Phase 3.10: Core Rendering Refactor - 拆分 render_video_moviepy 並最大化縮減 utils.py"

## Execution Flow (main)
```
1. Parse feature description: ✅ Phase 3.10 核心渲染重構
2. Extract key concepts:
   - Actors: 開發者、測試系統、CI/CD
   - Actions: 拆分函數、遷移代碼、更新測試、驗證功能
   - Data: render_video_moviepy (~1,630 lines)、utils.py (2,944 lines)
   - Constraints: 不破壞測試、向後相容、TDD 方法
3. Unclear aspects: ✅ 無 - 延續 Phase 3.1-3.8,計劃明確
4. User scenarios: ✅ 已定義
5. Functional requirements: ✅ 已生成
6. Key entities: ✅ 已識別
7. Review checklist: ✅ 通過
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT: 將 1,630 lines 單體函數拆分為 10-15 個子函數
- ✅ Focus on WHY: 提高可測試性、可維護性、完成三層架構遷移
- ❌ Avoid HOW: 不在 spec 定義具體實作細節(留給 plan.md)
- 👥 Audience: 開發者、技術決策者

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

**身為開發者**,我需要完成 Phase 3.1-3.8 開始的模組遷移,將剩餘的核心渲染函數從 `utils.py` 拆分並遷移至三層架構,以達成以下目標:

1. **可測試性**: 將 1,630 lines 的單體函數拆分為 10-15 個小函數,每個函數職責單一
2. **可維護性**: 明確的函數邊界和職責,便於未來修改和擴展
3. **架構完整性**: 完成 utils.py → 120 lines (96.77% reduction) 的最終目標
4. **向後相容**: 保持所有現有測試通過,不破壞既有功能

### Acceptance Scenarios

#### Scenario 1: 開發者成功拆分核心渲染函數

**Given**: 
- Phase 3.1-3.8 已完成 (44/64 functions migrated)
- `render_video_stub` (~230 lines) 和 `render_video_moviepy` (~1,630 lines) 保留在 utils.py
- >30 個測試依賴這兩個函數

**When**: 
- 開發者按照 TDD 方法拆分 `render_video_moviepy` 為 10-15 個子函數
- 開發者將子函數遷移至 `application/video_service.py`
- 開發者在 utils.py 保留輕量級 wrapper 供向後相容

**Then**:
- ✅ 所有現有測試通過 (>30 tests, 0 failures)
- ✅ utils.py 從 2,944 lines 縮減至 ~120 lines (95.9% reduction)
- ✅ `render_example.ps1` 產出 7 個 MP4 檔案
- ✅ 新架構支援單元測試每個子函數

#### Scenario 2: 測試系統驗證重構正確性

**Given**: 
- 重構完成,所有子函數已遷移
- utils.py wrapper 提供向後相容

**When**: 
- CI/CD 執行完整測試套件 (`pytest tests/`)
- CI/CD 執行整合測試 (`scripts/render_example.ps1`)

**Then**:
- ✅ 單元測試通過 (>95%)
- ✅ 契約測試通過 (驗證 Protocol 介面)
- ✅ 整合測試通過 (7 MP4 檔案與預期一致)
- ✅ 性能無顯著退化 (<5% overhead)

#### Scenario 3: 開發者使用新架構編寫測試

**Given**: 
- 新架構已部署
- 子函數有明確的 Protocol 定義

**When**: 
- 開發者需要測試 "字母渲染" 功能
- 開發者從 `application.video_service` import `_render_letters_layer()`

**Then**:
- ✅ 可以獨立測試該函數(不需渲染完整視頻)
- ✅ 可以 mock 依賴的 infrastructure layer (如 MoviePy)
- ✅ 測試執行速度快 (<1 秒)

### Edge Cases

1. **What happens when 拆分後的子函數有循環依賴?**
   - **Expected**: TDD 階段就會發現,重新設計介面
   - **Mitigation**: 使用 Protocol 定義明確的依賴方向

2. **How does system handle 部分測試失敗?**
   - **Expected**: 使用 Git 分支策略,每次遷移一個子函數就 commit
   - **Rollback**: `git reset --hard HEAD~1` 回退失敗的遷移

3. **What if 性能退化超過 5%?**
   - **Expected**: 優化熱點路徑(如 progress bar 渲染)
   - **Fallback**: 保留原始函數作為 fast-path

4. **How to ensure 向後相容性?**
   - **Solution**: utils.py 保留輕量級 wrapper,觸發 DeprecationWarning
   - **Timeline**: v2.0 再完全移除 wrapper

---

## Requirements *(mandatory)*

### Functional Requirements

#### Core Refactoring (FR-001 to FR-005)

- **FR-001**: System MUST 拆分 `render_video_moviepy` (~1,630 lines) 為 10-15 個子函數
  - **Sub-functions**: 
    - Context preparation (~80-130 lines)
    - Background rendering (~100-150 lines)
    - Letters layer (~150-180 lines)
    - Chinese/Zhuyin layer (~180-200 lines)
    - Timer layer (~70-90 lines)
    - Reveal layer (~150-200 lines)
    - Progress bar layer (~80-120 lines)
    - Audio processing (~180-270 lines)
    - Entry/Ending loading (~100-150 lines)
    - Composition & export (~150-200 lines)
    - Orchestration (~50-80 lines)

- **FR-002**: System MUST 遷移子函數至 `application/video_service.py`
  - **Target**: 新架構中的應用層(業務邏輯編排)
  - **Interface**: 使用 Protocol 定義可測試介面

- **FR-003**: System MUST 縮減 utils.py 至 ~120 lines
  - **Original**: 3,714 lines
  - **After Phase 3.1-3.8**: 2,944 lines (20.73% reduction)
  - **Target**: 120 lines (96.77% total reduction)
  - **Content**: Deprecated wrappers + essential constants

- **FR-004**: System MUST 保持向後相容性
  - **Method**: utils.py 保留輕量級 wrapper 呼叫新函數
  - **Warning**: 觸發 DeprecationWarning 提醒開發者遷移
  - **Timeline**: v2.0 移除 wrapper

- **FR-005**: System MUST 通過所有現有測試
  - **Target**: >30 test files, 0 failures
  - **Coverage**: 單元測試、契約測試、整合測試
  - **Integration**: `render_example.ps1` 產出 7 MP4 檔案

#### Testing Requirements (FR-006 to FR-010)

- **FR-006**: System MUST 使用 TDD 方法
  - **Process**: 先寫測試 → 測試失敗 → 實作 → 測試通過
  - **Coverage**: 每個子函數至少 1 個單元測試

- **FR-007**: System MUST 支援子函數單元測試
  - **Isolation**: 每個子函數可獨立測試(不依賴完整渲染)
  - **Mocking**: 支援 mock infrastructure layer (MoviePy, FFmpeg)
  - **Speed**: 單元測試執行 <1 秒

- **FR-008**: System MUST 通過契約測試
  - **Protocol**: 驗證每個子函數符合 Protocol 定義
  - **Interface**: 驗證輸入輸出型別正確

- **FR-009**: System MUST 通過整合測試
  - **E2E**: 從 JSON config → MP4 輸出的完整流程
  - **Validation**: 7 個範例視頻與預期一致

- **FR-010**: System MUST 保持性能水準
  - **Baseline**: Phase 3.1-3.8 的渲染時間
  - **Threshold**: 性能退化 <5%
  - **Optimization**: 識別並優化熱點路徑

#### Documentation Requirements (FR-011 to FR-013)

- **FR-011**: System MUST 更新所有相關文檔
  - **Files**: AGENTS.md, ARCHITECTURE.md, IMPLEMENTATION_SUMMARY.md
  - **Content**: 新架構說明、遷移指引、API 文檔

- **FR-012**: System MUST 記錄遷移過程
  - **Log**: 每次遷移的 commit message
  - **Summary**: IMPLEMENTATION_SUMMARY.md 記錄決策和問題

- **FR-013**: System MUST 提供遷移指引
  - **Target**: 幫助開發者從舊 API 遷移至新 API
  - **Examples**: Code snippets showing before/after

### Key Entities *(include if feature involves data)*

#### 1. VideoRenderingContext
**Purpose**: 封裝所有渲染所需的上下文資料
**Attributes**:
- `item: Dict[str, Any]` - 視頻配置(JSON item)
- `layout: Dict[str, Any]` - 佈局計算結果
- `timeline: Dict[str, Any]` - 時間軸資訊
- `entry_ctx: Dict[str, Any]` - 片頭上下文
- `ending_ctx: Dict[str, Any]` - 片尾上下文
- `letters_ctx: Dict[str, Any]` - 字母上下文

**Relationships**: 由 `_prepare_all_context()` 建立,供所有子函數使用

#### 2. RenderingPipeline
**Purpose**: 視頻渲染管線的協調器
**Attributes**:
- `context: VideoRenderingContext` - 渲染上下文
- `layers: List[Layer]` - 渲染層列表
- `composer: IVideoComposer` - 視頻組合器(Protocol)

**Relationships**: 使用 infrastructure layer 的 IVideoComposer 介面

#### 3. Layer (Protocol)
**Purpose**: 定義可渲染層的介面
**Methods**:
- `render() -> Clip` - 渲染該層並返回 MoviePy Clip
- `get_bbox() -> Dict[str, int]` - 取得該層的邊界框

**Implementations**: LettersLayer, ChineseZhuyinLayer, TimerLayer, RevealLayer, ProgressBarLayer

#### 4. DeprecatedWrapper
**Purpose**: utils.py 中的向後相容包裝器
**Behavior**:
- 觸發 DeprecationWarning
- 呼叫新架構函數
- 保持相同的函數簽名

**Lifecycle**: v2.0 完全移除

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for technical stakeholders (開發者、架構師)
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
  - ✅ utils.py → 120 lines (96.77% reduction)
  - ✅ >30 tests passing (0 failures)
  - ✅ 7 MP4 files from render_example.ps1
  - ✅ Performance <5% overhead
- [x] Scope is clearly bounded (Phase 3.10 only, follows Phase 3.1-3.8)
- [x] Dependencies and assumptions identified
  - **Dependency**: Phase 3.1-3.8 完成 (68.9% functions migrated)
  - **Assumption**: 現有測試覆蓋率 >95%
  - **Assumption**: TDD 方法可有效發現設計問題

### Architecture Alignment
- [x] Follows established 3-layer architecture (domain → infrastructure → application)
- [x] Respects layer boundaries (no domain calling infrastructure directly)
- [x] Uses Protocol for testability
- [x] Maintains backward compatibility during transition

### Risk Management
- [x] Identified risks:
  - **Risk 1**: 拆分可能破壞 >30 個測試
    - **Mitigation**: TDD + Git 分支策略,每次遷移一個函數
  - **Risk 2**: 性能可能退化
    - **Mitigation**: 基準測試 + 性能監控
  - **Risk 3**: 循環依賴
    - **Mitigation**: Protocol 定義明確依賴方向
- [x] Rollback plan: Git reset to previous commit
- [x] Incremental approach: 10-15 small functions instead of big-bang refactor

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed: "Phase 3.10: Core Rendering Refactor"
- [x] Key concepts extracted: Refactor, split functions, migrate, test, reduce utils.py
- [x] Ambiguities marked: None - clear continuation of Phase 3.1-3.8
- [x] User scenarios defined: 3 scenarios + edge cases
- [x] Requirements generated: FR-001 to FR-013 (13 requirements)
- [x] Entities identified: 4 key entities (Context, Pipeline, Layer, Wrapper)
- [x] Review checklist passed: ✅ Ready for planning phase

---

## Context from Previous Phase (Phase 3.1-3.8)

### Completed Work
- ✅ 44/64 functions migrated (68.9%)
- ✅ Domain layer: 9 functions
- ✅ Infrastructure layer: 22 functions
- ✅ Application layer: 13 functions
- ✅ ~30 deprecated wrappers for backward compatibility
- ✅ utils.py: 3,714 → 2,944 lines (20.73% reduction)
- ✅ All tests passing (>95%)

### Remaining Work (This Phase)
- ⏳ `render_video_stub` (~230 lines) - 元數據計算
- ⏳ `render_video_moviepy` (~1,630 lines) - 核心渲染管線
- 🎯 Target: utils.py → 120 lines (96.77% total reduction)

### Lessons from Phase 3.1-3.8
1. **TDD Works**: 契約測試先行確保遷移正確性
2. **Incremental Migration**: 逐步遷移降低風險
3. **Backward Compatibility**: Deprecated wrappers 確保平滑過渡
4. **Pragmatic Planning**: 20-30 hours 工作需要獨立 spec

### Why Separate Phase?
1. **Complexity**: 1,860 lines of tightly coupled code
2. **Risk**: >30 tests depend on these functions
3. **Time**: 20-30 hours of focused work
4. **TDD**: Need comprehensive test suite before refactoring

---

## Success Criteria

### Quantitative Metrics
- ✅ utils.py: 2,944 → 120 lines (95.9% reduction this phase, 96.77% total)
- ✅ Test coverage: >95% maintained
- ✅ Test success rate: 100% (0 failures)
- ✅ Integration test: 7 MP4 files produced
- ✅ Performance: <5% overhead vs baseline

### Qualitative Metrics
- ✅ Code maintainability: 10-15 small functions vs 1 giant function
- ✅ Testability: Each function can be tested in isolation
- ✅ Architecture: Complete 3-layer separation
- ✅ Documentation: Clear migration guide for developers

### Validation Methods
- **Unit Tests**: pytest tests/unit/application/test_video_service.py
- **Contract Tests**: pytest tests/contract/test_rendering_protocol.py
- **Integration Tests**: pytest tests/integration/test_end_to_end.py
- **Manual Test**: scripts/render_example.ps1 (7 MP4 files)
- **Performance Test**: Measure-Command { pytest tests/ } <5 分鐘

---

## Next Steps (After Spec Approval)

1. **Create plan.md**: Technical approach, TDD strategy, timeline
2. **Create tasks.md**: Detailed T048-T066 breakdown
3. **Execute Migration**: Incremental refactoring with continuous validation
4. **Final Validation**: Full test suite + documentation update

---

**Document Version**: 1.0  
**Author**: GitHub Copilot  
**Status**: Ready for Review
