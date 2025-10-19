# Feature Specification: 第二階段重構 - 移除舊程式碼並確保 render_example.ps1 正常執行

**Feature Branch**: `003-phase2-remove-old-code`  
**Created**: 2025-10-18  
**Status**: Draft  
**Input**: User description: "第二階段重構,我要讓舊程式碼被完全移除,並且確保最常被使用的產出影片腳本 render_example.ps1 可以被正常執行"

## Execution Flow (main)
```
1. Parse user description from Input
   ✓ Feature: 移除舊程式碼 (utils.py deprecated code) + 確保核心腳本功能
2. Extract key concepts from description
   ✓ Actors: 開發者、CI 系統
   ✓ Actions: 移除、驗證、執行
   ✓ Data: render_example.ps1, utils.py, 新模組化架構
   ✓ Constraints: 向後相容性可以移除,但必須維持核心功能
3. For each unclear aspect:
   → [已釐清] 腳本正常執行的定義: 能產出有效的 MP4 影片且無錯誤
4. Fill User Scenarios & Testing section
   ✓ Clear user flow identified
5. Generate Functional Requirements
   ✓ All requirements are testable
6. Identify Key Entities (if data involved)
   ✓ Files: utils.py, render_example.ps1, 新模組
7. Run Review Checklist
   → No [NEEDS CLARIFICATION] remaining
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
開發者在完成架構重構後,需要清理遺留的舊程式碼(deprecated utils.py 中的向後相容層),並確保專案最常用的影片產出工作流程(透過 render_example.ps1 腳本)能夠無縫運作。

### Acceptance Scenarios
1. **Given** 專案已完成模組化重構(002-refactor-architecture 完成), **When** 開發者移除 utils.py 中的 deprecated 標記和向後相容 re-export, **Then** render_example.ps1 仍能成功執行並產出有效影片
2. **Given** utils.py 已被清理或移除, **When** 執行 `.\scripts\render_example.ps1`, **Then** 腳本完成且在 out/ 目錄產出可播放的 MP4 檔案
3. **Given** 舊程式碼已移除, **When** 執行完整測試套件(`.\scripts\run_tests.ps1`), **Then** 所有測試通過且無 import 錯誤
4. **Given** 核心功能維持正常, **When** CI 系統執行測試與範例渲染, **Then** 所有步驟成功且無警告

### Edge Cases
- 如果 render_example.ps1 內部仍依賴舊 utils.py 的 import 路徑,該如何更新?
- 如果測試檔案中存在 `from spellvid.utils import _internal_helper` 這類直接導入,如何處理?
- 如果 utils.py 完全移除後有任何隱藏依賴(如 __pycache__ 快取),如何確保乾淨?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 系統 MUST 允許開發者安全移除 utils.py 中的 deprecated 向後相容層,而不破壞現有功能
- **FR-002**: 系統 MUST 在移除舊程式碼後,仍能透過 render_example.ps1 成功產出影片檔案
- **FR-003**: 使用者(開發者) MUST 能夠執行 `.\scripts\render_example.ps1` 並在 out/ 目錄取得有效的 MP4 輸出
- **FR-004**: 系統 MUST 確保移除舊程式碼後,所有現有測試套件(pytest)仍能通過
- **FR-005**: 系統 MUST 記錄或更新任何需要改變 import 路徑的檔案(例如 tests/ 或 scripts/)
- **FR-006**: 系統 MUST 在移除後驗證 ffmpeg 偵測、佈局計算、影片合成等核心功能不受影響
- **FR-007**: 使用者 MUST 能夠透過單一命令(`.\scripts\run_tests.ps1` 或等效)驗證所有功能正常

### Key Entities *(include if feature involves data)*
- **utils.py (deprecated)**: 重構前的單體模組,包含所有核心邏輯與向後相容 re-export,將被移除或最小化
- **新模組化架構**: 
  - `spellvid/shared/` — 型別、常數
  - `spellvid/domain/` — 純邏輯(佈局、注音、效果、計時)
  - `spellvid/application/` — 服務層(影片生成、批次處理)
  - `spellvid/infrastructure/` — 框架適配器(MoviePy、Pillow、FFmpeg)
  - `spellvid/cli/` — CLI 命令
- **render_example.ps1**: PowerShell 腳本,呼叫 Python 模組來產出範例影片,必須在重構後仍正常運作
- **render_example.py**: Python 入口腳本,由 render_example.ps1 呼叫,可能需要更新 import 路徑
- **測試套件(tests/)**: 包含單元測試、契約測試、整合測試,部分測試可能直接導入 utils.py 內部函數

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---

## Dependencies & Assumptions

### Dependencies
- 前置條件: 002-refactor-architecture 分支已完成並合併(或至少新模組架構已建立)
- render_example.py 腳本的存在與正確性
- 測試套件能夠涵蓋核心功能

### Assumptions
- utils.py 的 deprecated 標記代表該模組可安全移除或縮減
- render_example.ps1 是專案最常用的工作流程腳本,其正常運作代表核心功能完整
- 所有必要功能已遷移至新模組化架構,無遺漏

---

## Success Criteria (Measurable)
1. ✅ `.\scripts\render_example.ps1` 執行成功且在 out/ 產出有效 MP4 檔案
2. ✅ `.\scripts\run_tests.ps1` 執行結果為所有測試通過 (0 failures)
3. ✅ utils.py 被移除或縮減至最小,無 deprecated 標記殘留
4. ✅ 專案文件(AGENTS.md, copilot-instructions.md)已更新,移除對舊 utils.py 的引用
5. ✅ CI 工作流程(如果存在)能夠成功執行測試與範例渲染
