# Feature Specification: 完成新模組實作並真正移除 utils.py 舊程式碼

**Feature Branch**: `004-complete-module-migration`  
**Created**: 2025-10-19  
**Status**: Draft  
**Previous Phase**: 003-phase2-remove-old-code (標記 Deprecation 但未移除)  
**Input**: 根據 ACTUAL_COMPLETION_ASSESSMENT.md 的誠實評估,完成原始「完全移除」需求

## Execution Flow (main)
```
1. Parse user description from Input
   ✓ Feature: 完成新模組遷移 + 真正移除 utils.py 舊程式碼
2. Extract key concepts from description
   ✓ Actors: 開發者、測試套件、CI 系統
   ✓ Actions: 遷移函數、統一簽章、更新測試、建立 re-export、刪除舊實作
   ✓ Data: utils.py (3,714 行) → 新模組 + 最小 re-export (~120 行)
   ✓ Constraints: 必須維持 100% 向後相容,所有測試通過,render_example.ps1 正常運作
3. For each unclear aspect:
   → [已釐清] 基於 Phase 2 的誠實評估,明確知道需要遷移的 ~35 個函數
4. Fill User Scenarios & Testing section
   ✓ Clear user flow identified
5. Generate Functional Requirements
   ✓ All requirements are testable
6. Identify Key Entities (if data involved)
   ✓ 明確的函數對應表 (data-model.md)
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
開發者需要完成 Phase 2 未達成的「完全移除舊程式碼」目標。根據 ACTUAL_COMPLETION_ASSESSMENT.md 的評估,當前 utils.py 保留了 3,714 行完整實作 (僅新增 DeprecationWarning),移除率為 0%。開發者需要:
1. **分析函數使用情況** — 掃描專案中每個函數的實際使用,識別冗餘/未使用函數
   - **生產代碼使用**: 函數被 `spellvid/` (非測試) 或 `scripts/` 引用
   - **測試專用函數**: 僅被 `tests/` 引用的函數視為冗餘
   - **完全未使用**: 無任何引用的函數視為冗餘
2. **移除冗餘函數** — 直接刪除未被生產代碼使用的函數,包含測試專用函數 (無需遷移)
3. **遷移有效函數** — 僅遷移被生產代碼實際使用的函數至新模組架構 (預估 ~15-25 個)
4. **建立最小 re-export 層** — 為仍被使用的函數建立 re-export (~80-120 行)
5. **刪除所有舊實作** — 刪除所有實作程式碼 (3,714 行 → 80-120 行)
6. **確保功能正常** — 所有功能與測試維持正常運作

### Acceptance Scenarios
1. **Given** Phase 2 已標記 utils.py 為 deprecated 但保留完整實作, **When** 開發者分析 utils.py 中所有函數的使用情況, **Then** 產生完整的函數使用報告,區分三類:
   - **生產使用**: 被 `spellvid/` (非測試) 或 `scripts/` 引用的函數
   - **測試專用**: 僅被 `tests/` 引用的函數
   - **完全未使用**: 無任何引用的函數
2. **Given** 函數使用報告已產生, **When** 識別出未被生產代碼使用的冗餘函數 (測試專用 + 完全未使用), **Then** 直接從 utils.py 刪除這些函數,無需遷移 (預估可直接移除 ~10-20 個函數)
3. **Given** 冗餘函數已移除, **When** 開發者遷移剩餘有效函數到新模組, **Then** 所有被生產代碼使用的函數都能在新模組中找到對應實作 (預估遷移 ~15-25 個函數)
4. **Given** 所有有效函數已遷移至新模組, **When** 開發者建立最小 re-export utils.py (~80-120 行), **Then** 所有現有 import 路徑維持有效且指向新模組
5. **Given** 最小 re-export 層已建立, **When** 執行完整測試套件 `.\scripts\run_tests.ps1`, **Then** 測試可能失敗 (因測試專用函數已刪除),需更新測試改為使用新模組
6. **Given** 測試已更新, **When** 再次執行 `.\scripts\run_tests.ps1`, **Then** 所有測試通過 (0 failures),無 import 錯誤
7. **Given** 測試全通過, **When** 執行 `.\scripts\render_example.ps1`, **Then** 成功產出 7 個有效 MP4 檔案
8. **Given** 核心功能驗證完成, **When** 開發者刪除 utils.py 中的舊實作程式碼, **Then** utils.py 從 3,714 行縮減至 ~80-120 行 (≥95% 縮減率)
9. **Given** utils.py 已最小化, **When** 檢查檔案內容, **Then** 僅包含 import/re-export/DeprecationWarning,無任何實作邏輯

### Edge Cases
- 如果某個函數僅在已被標記為 deprecated 的測試中使用,是否應移除該函數?
- 如果函數簽章在新模組中已改變 (如 Dict → VideoConfig),如何建立相容的 wrapper?
- 如果測試直接依賴 utils.py 內部實作細節 (如 `_make_text_imageclip`),但函數實際未被生產代碼使用,是否應保留?
- 如果發現某些「輔助函數」僅被其他「輔助函數」呼叫,形成未使用的函數鏈,如何識別並批量移除?
- 如果完整測試套件仍耗時 >30 分鐘,如何確保 CI 可行性?
- 如果函數使用分析發現某些函數僅在 __pycache__ 或備份檔案中被引用,如何正確過濾?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-000**: 系統 MUST 分析 utils.py 中所有函數的使用情況,產生函數引用報告 (包含引用位置、次數、呼叫者)
- **FR-001**: 系統 MUST 識別並直接刪除未被使用的冗餘函數 (預估 ~10-20 個),無需遷移
- **FR-002**: 系統 MUST 將剩餘有效函數 (預估 ~15-25 個) 遷移至對應新模組 (domain/infrastructure/application)
- **FR-003**: 系統 MUST 統一函數簽章,確保新模組函數能透過 re-export 層完全替代舊實作
- **FR-004**: 系統 MUST 更新所有測試檔案 (20+ 檔案) 的 import 路徑,從 `spellvid.utils` 改為新模組路徑
- **FR-005**: 系統 MUST 建立最小 re-export utils.py (~80-120 行),僅包含 import、alias、DeprecationWarning
- **FR-006**: 系統 MUST 刪除 utils.py 中所有實作程式碼,將檔案從 3,714 行縮減至 ~80-120 行
- **FR-007**: 系統 MUST 確保 render_example.ps1 在新架構下正常執行並產出有效 MP4
- **FR-008**: 系統 MUST 確保完整測試套件通過 (0 failures),無 import 或相容性錯誤
- **FR-009**: 系統 MUST 提供函數處理對應表,記錄每個函數的處理方式 (已移除/已遷移/已保留+原因)
- **FR-010**: 系統 SHOULD 解決完整測試套件性能問題 (>30 分鐘 → <5 分鐘)
- **FR-011**: 系統 MUST 更新文件,移除「標記 deprecated 但保留」的描述,改為「已完全遷移至新模組,冗餘函數已清理」

### Key Entities *(include if feature involves data)*

#### utils.py (當前狀態)
- **檔案大小**: 147,403 bytes (3,714 行)
- **狀態**: 完整實作保留 + DeprecationWarning + __all__ export list
- **包含函數**: ~50+ 函數
- **已遷移函數**: ~15 個核心函數 (30%)
- **未遷移函數**: ~35 個輔助函數 (70%)

#### 未遷移函數清單 (從 ACTUAL_COMPLETION_ASSESSMENT.md)
基於 data-model.md 與實際檢視,以下函數仍在 utils.py 中未遷移。

**⚠️ 重要**: 在遷移前,必須先分析每個函數的實際使用情況:
- **使用中**: 遷移至新模組
- **未使用**: 直接刪除,無需遷移
- **測試專用**: 評估是否保留 (僅測試使用 vs 生產+測試)

**進度條相關** (~10 函數):
- `_progress_bar_band_layout()` — 待分析使用情況
- `_progress_bar_base_arrays()` — 待分析使用情況
- `_make_progress_bar_mask()` — 待分析使用情況
- `_build_progress_bar_segments()` — 待分析使用情況
- 其他進度條輔助函數 — 待分析使用情況

**視頻效果** (~8 函數):
- `_apply_fadeout()` — 待分析使用情況
- `_apply_fadein()` — 待分析使用情況
- `concatenate_videos_with_transitions()` — 待分析使用情況
- `_ensure_dimensions()` — 待分析使用情況
- `_ensure_fullscreen_cover()` — 待分析使用情況
- `_auto_letterbox_crop()` — 待分析使用情況

**字母與佈局輔助** (~7 函數):
- `_normalize_letters_sequence()` — 待分析使用情況
- `_letter_asset_filename()` — 待分析使用情況
- `_plan_letter_images()` — 待分析使用情況
- `_letters_missing_names()` — 待分析使用情況
- `_prepare_letters_context()` — 待分析使用情況
- `_log_missing_letter_assets()` — 待分析使用情況

**媒體處理** (~5 函數):
- `_probe_media_duration()` — 待分析使用情況
- `_create_placeholder_mp4_with_ffmpeg()` — 待分析使用情況
- `_coerce_non_negative_float()` — 待分析使用情況
- `_coerce_bool()` — 待分析使用情況

**Entry/Ending 視頻** (~5 函數):
- `_resolve_entry_video_path()` — 待分析使用情況
- `_is_entry_enabled()` — 待分析使用情況
- `_resolve_ending_video_path()` — 待分析使用情況
- `_is_ending_enabled()` — 待分析使用情況
- `_prepare_entry_context()` — 待分析使用情況
- `_prepare_ending_context()` — 待分析使用情況

**預估結果**:
- 總計 ~35 個未遷移函數
- 預估 ~10-20 個為冗餘函數 (可直接刪除)
- 預估 ~15-25 個為有效函數 (需遷移)

#### 新模組架構 (目標)
- `spellvid/shared/` — 型別、常數、驗證邏輯
- `spellvid/domain/` — 佈局、注音、效果、時間軸 (純邏輯)
- `spellvid/infrastructure/` — MoviePy、Pillow、FFmpeg 適配器
- `spellvid/application/` — 視頻服務、批次處理、資源檢查
- `spellvid/cli/` — CLI 命令入口

#### utils.py (目標狀態)
- **檔案大小**: ~4,000-6,000 bytes (~80-120 行)
- **狀態**: 最小 re-export 層
- **內容**:
  1. DeprecationWarning (約 15 行)
  2. Import from 新模組 (約 30-50 行,取決於有效函數數量)
  3. Alias 定義 (約 15-30 行,如 `render_video_stub = render_video`)
  4. `__all__` export list (約 20-25 行)
- **縮減率**: ≥95% (3,714 → 80-120 行)
- **函數數量**: ~15-25 個 re-export (相比原始 ~50+ 函數,刪除 ~10-20 個冗餘函數)

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
- [x] Ambiguities marked (已釐清)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---

## Dependencies & Assumptions

### Dependencies
- **前置條件**: 003-phase2-remove-old-code 已完成 (utils.py 標記為 deprecated)
- **新模組架構**: domain/infrastructure/application 模組已存在
- **函數對應表**: specs/003-phase2-remove-old-code/data-model.md 提供遷移指引
- **測試套件**: 現有 pytest 測試能驗證功能正確性

### Assumptions
- 新模組架構資料夾結構已建立,但函數實作不完整
- 剩餘 ~35 個函數可透過分析 utils.py 程式碼識別
- 測試更新可透過簡單的 import 路徑替換完成
- render_example.ps1 依賴的函數都在待遷移清單中
- 函數簽章差異可透過 wrapper 或 adapter 解決

---

## Success Criteria (Measurable)

### 主要成功標準
1. ✅ **SC-1: 函數使用分析完成** - 產生完整的函數引用報告,列出每個函數的使用情況 (引用位置、次數、呼叫者)
2. ✅ **SC-2: 冗餘函數清理** - 識別並刪除未使用的冗餘函數 (預估 ~10-20 個),記錄刪除理由
3. ✅ **SC-3: 有效函數遷移完成** - 剩餘有效函數 (預估 ~15-25 個) 全部遷移至新模組,100% 遷移率
4. ✅ **SC-4: utils.py 最小化** - utils.py 從 3,714 行縮減至 ~80-120 行,縮減率 ≥ 95%
5. ✅ **SC-5: 測試全通過** - 執行 `.\scripts\run_tests.ps1` 結果為 0 failures,所有測試通過
6. ✅ **SC-6: 核心功能驗證** - `.\scripts\render_example.ps1` 成功產出 7 個有效 MP4 檔案
7. ✅ **SC-7: 無實作程式碼** - utils.py 檔案檢查,僅包含 import/re-export/warning,無任何實作邏輯 (def/class body)
8. ✅ **SC-8: 文件更新** - AGENTS.md、copilot-instructions.md 反映「已完全遷移+冗餘清理」狀態
9. 🎯 **SC-9 (可選): 測試性能改善** - 完整測試套件執行時間 < 5 分鐘 (當前 >30 分鐘)

### 驗收檢查點
- [ ] 函數使用分析報告完整 (包含所有 ~50+ 函數的引用情況)
- [ ] 冗餘函數識別清單完整 (列出每個待刪除函數及理由)
- [ ] 有效函數遷移對應表完整 (每個遷移函數都有新位置記錄)
- [ ] 所有測試檔案 import 路徑已更新 (無殘留 `from spellvid.utils import` 直接呼叫實作)
- [ ] 最小 re-export utils.py 建立並驗證 (DeprecationWarning 觸發正常)
- [ ] 舊實作程式碼完全刪除 (utils.py 不包含任何 function body)
- [ ] CI 執行成功 (契約測試、單元測試、整合測試全通過)
- [ ] 程式碼審查通過 (函數遷移位置合理,刪除決策有據)
- [ ] 函數處理記錄完整 (每個函數的處理方式: 已移除/已遷移/已保留+原因)

---

## Out of Scope (明確排除)

本次重構**不包含**以下項目:
- ❌ 改變公開 API 行為或函數簽章 (僅內部重構)
- ❌ 新增功能或改進現有邏輯
- ❌ 重寫測試 (僅更新 import 路徑)
- ❌ 修改 render_example.ps1 腳本邏輯 (僅確保其正常運作)
- ❌ 優化視頻渲染性能
- ❌ 建立新的 CI pipeline (使用現有測試框架)

---

## Risk Assessment

### High Risk
- **誤刪有效函數**: 函數使用分析可能遺漏某些動態引用或間接呼叫
  - **Mitigation**: 使用多種分析工具交叉驗證 (grep + AST 分析 + 執行時追蹤),建立「待確認」清單供人工審查
- **測試更新遺漏**: 20+ 測試檔案需更新 import,可能遺漏部分檔案
  - **Mitigation**: 使用 grep 工具掃描所有 `from spellvid.utils import`,建立完整清單,逐一驗證
- **函數簽章不相容**: 新模組函數參數型別可能與舊實作不同
  - **Mitigation**: 建立 adapter wrapper,保持 re-export 層的相容性

### Medium Risk
- **隱藏依賴**: 某些函數間可能存在未記錄的內部依賴
  - **Mitigation**: 逐步遷移並驗證,每遷移一組函數就執行測試
- **測試性能**: 完整測試套件耗時 >30 分鐘,可能影響開發迭代速度
  - **Mitigation**: 先完成功能遷移,測試性能優化作為獨立任務

### Low Risk
- **文件同步**: 需更新多個文件描述
  - **Mitigation**: 建立文件更新檢查清單

---

## Notes

### 與 Phase 2 的差異
Phase 2 (003-phase2-remove-old-code) 實際完成:
- ✅ 標記 utils.py 為 deprecated (DeprecationWarning)
- ✅ 確保 render_example.ps1 正常運作
- ❌ **未完成**: 移除舊程式碼 (0% 移除率)

Phase 4 (本階段) 目標:
- ✅ 完成 Phase 2 未達成的「完全移除」需求
- ✅ **優先清理**: 分析並刪除冗餘函數 (~10-20 個)
- ✅ **精準遷移**: 僅遷移有效函數 (~15-25 個)
- ✅ 建立最小 re-export 層 (~80-120 行)
- ✅ 刪除所有舊實作程式碼
- ✅ 達成 ≥95% 縮減率 (3,714 → 80-120 行)

### 預估工作量
根據 ACTUAL_COMPLETION_ASSESSMENT.md 與新增的函數分析策略:
- Step 0: 函數使用分析 — 3-5 小時 (掃描、分析、產生報告)
- Step 1: 冗餘函數清理 — 2-3 小時 (刪除 ~10-20 個未使用函數)
- Step 2: 完成有效函數遷移 — 15-20 小時 (遷移 ~15-25 個函數,相比原估 20-30h 減少)
- Step 3: 建立最小 re-export 層 — 2-3 小時
- Step 4: 驗證與測試 — 5-8 小時
- Step 5: 文件與部署 — 2-3 小時
- **總計**: 30-42 小時 (相比原估 30-45h 略少,因減少不必要的遷移工作)

### 成功後的狀態
- utils.py: 80-120 行 (僅 re-export)
- 新模組: ~15-25 個有效函數遷移
- 冗餘清理: ~10-20 個函數直接刪除
- 測試: 全通過
- 文件: 反映「已完全遷移+冗餘清理」
- 技術債: 消除 (不再是「標記但保留」)
- 程式碼品質: 提升 (移除死程式碼)

---

**Specification Created**: 2025-10-19  
**Based On**: ACTUAL_COMPLETION_ASSESSMENT.md 誠實評估  
**Ready for**: Planning Phase
