# Feature Specification: 修正片尾影片重複播放問題

**Feature Branch**: `001-bug`  
**Created**: 2025-10-07  
**Status**: Draft  
**Input**: User description: "bug 不應該在每個單字影片結束都加上片尾影片, 整部影片只應該出現一次片尾."

## 問題描述

在使用 `.\scripts\render_example.ps1` 腳本處理多個單字影片時，系統目前會在每個單字影片結束後都添加片尾影片 (`ending.mp4`)。當腳本將這些影片串接成最終輸出檔案時，用戶在觀看完整的單字學習影片時會看到重複的片尾內容，影響觀看體驗。

正確的行為應該是：腳本生成的最終串接影片只在最後添加一次片尾影片，而不是每個單字影片都加上片尾。

---

## ⚡ 修正要點
- ✅ 修正 `render_example.ps1` 腳本中片尾影片的串接邏輯
- ✅ 確保片尾影片只在最終串接影片的最後出現一次
- ❌ 避免在每個單字影片結束後都添加片尾

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
用戶使用 `.\scripts\render_example.ps1` 腳本處理多個單字 (例如：Cat, Dog, Ball) 時，希望生成一個完整的學習影片，在影片最後僅播放一次片尾內容，而不是每個單字結束後都看到重複的片尾。腳本會將所有單字影片串接成一個最終輸出檔案。

### Acceptance Scenarios
1. **Given** 有一個包含 3 個單字的 JSON 配置檔案，**When** 執行 `.\scripts\render_example.ps1 -OutFile batch_result.mp4`，**Then** 輸出的影片應該是：單字1 → 單字2 → 單字3 → 片尾影片 (只有一次)

2. **Given** 使用者觀看透過 `render_example.ps1` 生成的批次影片，**When** 影片播放到各個單字之間的轉換，**Then** 不應該看到片尾影片內容

3. **Given** 批次包含 5 個單字，**When** 使用 `render_example.ps1` 生成完整影片並播放完畢，**Then** 片尾影片應該只在最後出現一次

### Edge Cases
- 如果批次只包含 1 個單字，片尾影片仍應該只出現一次 (在該單字結束後)
- 如果配置中沒有指定片尾影片路徑，系統應該正常運作而不加入任何片尾內容

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: 使用 `render_example.ps1` 腳本處理多個單字時，系統必須僅在最終串接影片的最後添加一次片尾影片
- **FR-002**: 系統必須確保單字與單字之間的轉換不包含片尾影片內容
- **FR-003**: 即使 JSON 配置只包含一個單字，片尾影片也只能出現一次 (在該單字結束後)
- **FR-004**: 如果配置中未指定片尾影片，腳本必須正常處理串接而不添加任何片尾內容
- **FR-005**: 修正後的行為必須保持與現有單一單字處理模式的兼容性

### Bug Fix Requirements
- **BF-001**: 識別並修正導致每個單字都添加片尾影片的程式邏輯錯誤
- **BF-002**: 確保片尾影片的添加邏輯只在 `render_example.ps1` 最終串接階段執行
- **BF-003**: 驗證修正不會影響其他現有功能 (如音樂、圖片、文字渲染等)

---

## Review & Acceptance Checklist
*GATE: 修正驗證檢查項目*

### 內容品質
- [x] 未包含實現細節 (程式語言、框架、API)
- [x] 專注於用戶價值和業務需求
- [x] 適合非技術利害關係人閱讀
- [x] 所有必要章節已完成

### 需求完整性
- [x] 無 [NEEDS CLARIFICATION] 標記
- [x] 需求可測試且明確
- [x] 成功標準可衡量
- [x] 範圍邊界清楚
- [x] 依賴性和假設已識別

---

## Execution Status
*Bug 修正處理狀態*

- [x] 用戶描述已解析
- [x] 關鍵概念已提取 (render_example.ps1 腳本、片尾影片重複、串接邏輯)
- [x] 模糊點已標記 (無模糊點)
- [x] 用戶場景已定義
- [x] 需求已生成
- [x] 實體已識別 (N/A - 此為 bug 修正)
- [x] 檢查清單已通過

---
