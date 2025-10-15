# Feature Specification: 專案架構重構 - 職責分離與降低耦合度

**Feature Branch**: `002-refactor-architecture`  
**Created**: 2025-10-14  
**Status**: Draft  
**Input**: User description: "重構專案架構 - 實現職責分離和降低耦合度"

## Execution Flow (main)
```
1. Parse user description from Input
   ✓ Description: 重構現有 SpellVid 專案架構,實現職責分離,降低模組間耦合度
2. Extract key concepts from description
   ✓ Identified: 架構層次劃分、職責邊界定義、依賴方向管理、可測試性提升
3. For each unclear aspect:
   - 重構範圍: 僅針對 spellvid/ 目錄下的生產代碼
   - 向後相容性: 保持 CLI 介面和現有測試不受影響
4. Fill User Scenarios & Testing section
   ✓ Completed - 包含開發者體驗改善場景
5. Generate Functional Requirements
   ✓ All requirements are testable and measurable
6. Identify Key Entities (if data involved)
   ✓ Identified architectural layers and module boundaries
7. Run Review Checklist
   ✓ No implementation details leaked
   ✓ Focus on WHAT and WHY, not HOW
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ 聚焦於「開發者如何更容易理解與修改系統」
- ✅ 確保架構決策可被驗證（透過測試和靜態分析）
- ❌ 不指定具體的框架或設計模式實作細節
- 👥 目標讀者：專案維護者、新進貢獻者、架構審查者

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
**作為專案維護者**，我希望專案代碼具有清晰的職責邊界和明確的依賴方向，這樣當我需要：
- 添加新的視頻效果時，不需要修改 CLI 或資源檢查邏輯
- 更換底層的視頻合成引擎（MoviePy → 其他）時，不影響業務邏輯
- 理解某個功能的實作時，能快速定位到對應的單一模組
- 為某個模組撰寫單元測試時，不需要啟動整個系統

### Acceptance Scenarios

#### 場景 1: 新增視頻效果功能
**Given** 系統已完成架構重構  
**When** 開發者需要新增一個「片尾字幕動畫」功能  
**Then** 
- 該功能的實作應侷限於單一「視頻效果」模組內
- 不需要修改 CLI 參數解析邏輯
- 不需要修改資料驗證或資源檢查模組
- 可以為該功能撰寫獨立的單元測試

#### 場景 2: 替換視頻合成引擎
**Given** 系統已完成架構重構  
**When** 專案決定從 MoviePy 遷移到其他視頻處理庫  
**Then**
- 所有業務邏輯（佈局計算、資料驗證、資源管理）不需要改動
- 僅需要實作新的「視頻合成適配器」
- 所有現有的單元測試（非整合測試）應保持通過
- CLI 介面和使用方式維持不變

#### 場景 3: 理解與維護現有功能
**Given** 新進貢獻者閱讀重構後的代碼  
**When** 需要理解「進度條渲染」的實作方式  
**Then**
- 能從模組命名和目錄結構直觀找到相關代碼
- 該模組的依賴關係清晰可見（不依賴 CLI 或 FFmpeg 細節）
- 模組內的函數職責單一，命名能反映其用途
- 存在清晰的模組文檔或型別提示，說明輸入/輸出

#### 場景 4: 撰寫單元測試
**Given** 開發者需要為「字母圖片載入」功能撰寫測試  
**When** 撰寫測試代碼時  
**Then**
- 不需要模擬 MoviePy 物件
- 不需要準備完整的 JSON 輸入資料
- 可以直接呼叫該功能的公開介面，傳入最小化的測試資料
- 測試執行速度快（無需實際視頻渲染）

### Edge Cases
- 當某個模組的依賴項不可用時（例如 MoviePy 未安裝），系統應能明確報告缺失的層次（而非模糊的匯入錯誤）
- 當配置資料格式不符時，驗證邏輯應在「輸入層」就攔截，不應傳遞到「業務邏輯層」
- 當測試需要模擬某個依賴時，應能透過介面替換，而非 monkey-patching 私有函數

---

## Requirements *(mandatory)*

### Functional Requirements

#### FR-001: 分層架構清晰可辨識
系統 MUST 將代碼組織為可識別的架構層次，每層具有明確的職責邊界：
- **輸入層**：處理 CLI 參數解析、JSON 載入、資料驗證
- **業務邏輯層**：佈局計算、資源檢查、效果組合邏輯
- **基礎設施層**：視頻合成引擎介面、檔案 I/O、FFmpeg 呼叫

#### FR-002: 依賴方向單向流動
系統 MUST 確保依賴關係由外向內流動：
- CLI 層可依賴業務邏輯層
- 業務邏輯層可依賴基礎設施層介面（不依賴具體實作）
- 基礎設施層不依賴業務邏輯層
- 任何循環依賴 MUST 被消除

#### FR-003: 業務邏輯與框架解耦
系統 MUST 確保核心業務邏輯不直接依賴特定框架：
- 佈局計算邏輯不應依賴 MoviePy 資料結構
- 進度條生成邏輯不應依賴 PIL/Pillow 物件
- 資料驗證邏輯不應依賴 argparse.Namespace

#### FR-004: 介面與實作分離
系統 MUST 為關鍵基礎設施提供明確介面：
- 視頻合成引擎應透過抽象介面定義（例如：渲染一組 Clip 為視頻檔）
- FFmpeg 呼叫應透過統一的媒體處理介面
- 字型載入、文字渲染應透過可替換的適配器

#### FR-005: 模組職責單一化
系統 MUST 確保每個模組具有單一、明確的職責：
- 不應存在「同時處理 CLI 解析 + 視頻渲染」的模組
- 不應存在「同時驗證資料 + 執行 FFmpeg」的函數
- 每個公開函數應能用一句話描述其職責

#### FR-006: 可測試性設計
系統 MUST 支援不同層級的測試策略：
- 業務邏輯層的函數應可在不啟動 MoviePy 的情況下測試
- 資料驗證邏輯應可獨立於 CLI 進行測試
- 佈局計算應可透過純函數方式驗證（給定輸入 → 固定輸出）

#### FR-007: 向後相容性保證
重構 MUST 保持以下不變：
- CLI 的 `make` 和 `batch` 命令介面
- 現有的 JSON 輸入格式
- 所有現有的整合測試應保持通過（允許調整內部實作測試）

#### FR-008: 明確的錯誤邊界
系統 MUST 在每個架構層次明確定義錯誤處理策略：
- 輸入層錯誤：資料驗證失敗應回報明確的欄位錯誤訊息
- 業務邏輯層錯誤：資源缺失應回報具體的檔案路徑
- 基礎設施層錯誤：FFmpeg 失敗應保留原始錯誤訊息並標註來源

#### FR-009: 文檔與型別完整性
重構後的代碼 MUST 提供：
- 所有公開函數具有型別提示（Type Hints）
- 模組級別的文檔字串，說明該模組的職責範圍
- 複雜的業務邏輯具有內聯註解，解釋「為何」而非「如何」

#### FR-010: 程式碼組織的可發現性
系統的目錄結構與模組命名 MUST 反映架構設計：
- 從目錄名稱應能直觀理解該模組屬於哪個架構層次
- 從檔案名稱應能理解該模組的核心職責
- 不應存在「utils」、「helpers」等模糊命名（除非僅為工具函數集）

### Key Entities *(architectural components)*

#### 架構層次定義

1. **輸入適配層 (Input Adapters)**
   - CLI 參數解析與驗證
   - JSON 配置載入與 Schema 驗證
   - 外部資料來源適配（如果未來需要）
   - 職責：將外部輸入轉換為領域物件

2. **應用服務層 (Application Services)**
   - 視頻生成流程編排（單支視頻、批次處理）
   - 資源完整性檢查
   - 輸出路徑管理與檔案命名
   - 職責：協調業務邏輯，實作使用案例

3. **領域邏輯層 (Domain Logic)**
   - 佈局計算（字母、文字、圖片位置）
   - 進度條生成邏輯
   - 注音轉換與排版
   - 倒數計時器邏輯
   - 效果組合規則（淡入、淡出、轉場）
   - 職責：封裝核心業務規則，不依賴外部框架

4. **基礎設施介面層 (Infrastructure Interfaces)**
   - 視頻合成引擎介面（IVideoComposer）
   - 媒體處理介面（IMediaProcessor - FFmpeg wrapper）
   - 文字渲染介面（ITextRenderer）
   - 字型載入介面（IFontLoader）
   - 職責：定義對外部依賴的抽象契約

5. **基礎設施實作層 (Infrastructure Implementations)**
   - MoviePy 視頻合成適配器
   - FFmpeg 命令列包裝器
   - Pillow 文字渲染適配器
   - 系統字型載入器
   - 職責：實作基礎設施介面，處理技術細節

#### 模組邊界範例

**Before（現況 - 高耦合）**:
```
spellvid/
  cli.py          # 混合 CLI 解析 + 業務邏輯呼叫
  utils.py        # 3600+ 行，包含所有功能
```

**After（重構目標 - 職責分離）**:
```
spellvid/
  cli/
    parser.py       # 僅負責 CLI 參數解析
    commands.py     # 實作 make/batch 命令邏輯
  application/
    video_service.py      # 視頻生成服務
    batch_service.py      # 批次處理服務
    resource_checker.py   # 資源檢查服務
  domain/
    layout.py             # 佈局計算純邏輯
    effects.py            # 效果組合規則
    typography.py         # 文字與注音處理
    timing.py             # 時間軸與計時器
  infrastructure/
    video/
      interface.py        # IVideoComposer 介面定義
      moviepy_adapter.py  # MoviePy 實作
    media/
      interface.py        # IMediaProcessor 介面
      ffmpeg_wrapper.py   # FFmpeg 實作
    rendering/
      interface.py        # ITextRenderer 介面
      pillow_adapter.py   # Pillow 實作
  shared/
    types.py              # 共用型別定義
    constants.py          # 常數定義（顏色、尺寸等）
    validation.py         # Schema 驗證邏輯
```

#### 依賴流動規則

```
CLI Layer
  ↓ (depends on)
Application Layer
  ↓ (depends on)
Domain Layer
  ↓ (depends on)
Infrastructure Interfaces
  ↑ (implemented by)
Infrastructure Implementations
```

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)  
  → 僅定義架構層次和職責，未指定具體設計模式或框架版本
- [x] Focused on user value and business needs  
  → 重構目標是改善開發者體驗、提升可維護性
- [x] Written for non-technical stakeholders  
  → 場景描述以「開發者工作流程」為中心，可被專案經理理解
- [x] All mandatory sections completed  
  → 所有必要章節已填寫

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain  
  → 所有需求明確，範疇限定在 spellvid/ 目錄
- [x] Requirements are testable and unambiguous  
  → 每項 FR 都可透過程式碼檢查、測試或靜態分析驗證
- [x] Success criteria are measurable  
  → 透過「能否獨立測試某模組」、「能否替換某基礎設施」等標準衡量
- [x] Scope is clearly bounded  
  → 明確排除 CLI 介面改動、JSON 格式變更
- [x] Dependencies and assumptions identified  
  → 假設現有測試涵蓋足夠，依賴項為 MoviePy/FFmpeg/Pillow

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none remaining)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified (architectural layers)
- [x] Review checklist passed

---

## Additional Context

### Rationale for Architectural Patterns

本規格建議採用 **分層架構 (Layered Architecture)** 搭配 **六邊形架構 (Ports & Adapters / Hexagonal Architecture)** 的理念：

1. **分層架構**：確保依賴方向單向、職責清晰
2. **介面與實作分離**：允許未來替換 MoviePy、FFmpeg 等基礎設施
3. **領域邏輯獨立**：佈局計算、效果組合等核心邏輯不依賴框架

### Benefits to Stakeholders

- **專案維護者**：降低修改某功能的連鎖影響範圍
- **新進貢獻者**：透過清晰的模組邊界快速理解系統
- **QA/測試人員**：可針對不同層次撰寫測試，提升測試覆蓋率
- **架構審查者**：可透過靜態分析工具驗證依賴方向是否符合設計

### Non-Goals (明確排除)

- ❌ 不改變 CLI 的 `--letters`, `--word-en` 等參數名稱
- ❌ 不改變 JSON 輸入格式的 Schema
- ❌ 不在此階段引入 Dependency Injection 容器或框架
- ❌ 不在此階段實作「插件系統」或「擴展機制」

### Future Considerations

重構完成後，未來可考慮的演進方向（不在此規格範圍）：
- 引入 DI 容器管理基礎設施實作的生命週期
- 將領域邏輯層封裝為獨立的 Python 套件
- 提供 REST API 或 gRPC 介面（目前僅 CLI）
- 支援更多視頻合成後端（OpenCV、GStreamer）

---

**Spec Completed**: 2025-10-14  
**Ready for Planning Phase**: ✓
