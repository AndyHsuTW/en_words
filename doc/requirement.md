# 簡介

**專案代號**：SpellVid\
**文件版本**：v0.9（專案版草案）\
**最後更新**：2025-09-08\
**作者/維護人**：TBD

**背景**：

- SpellVid 是一款「面向開發者」的 **命令列（CLI）** 影片合成工具，用於製作英語拼字教學短片。
- 畫面構成：左上英文字母、右上中文（含自動注音）、左側倒數計時、中間主圖（單字相關圖像或影片）、倒數結束後於底部揭示英文單字。

**利害關係人（Stakeholders）**：

| 身分            | 角色/責任   | 主要關注點            |
| ------------- | ------- | ---------------- |
| 產品負責人         | 路線圖、優先度 | 上線時程、教學成效        |
| 架構師/Tech Lead | 技術決策    | 可維運性、跨機器一致性      |
| CLI/後端工程師     | 功能實作    | 參數設計、錯誤處理、輸出品質   |
| 教材製作人員        | 內容準備    | JSON 設定檔、圖片/音樂授權 |
| QA            | 測試與驗證   | 覆核需求、驗收標準、可測試性   |

---

# 目的（Purpose）

- 以可重現、可配置的方式，批量產出統一版型的英語學習短片。
- 降低手動剪輯成本，確保輸出的一致性與可驗證性。

**成功指標**：

- 內容製作者從 JSON 設定檔到完成輸出影片的「首支影片完成時間（TTFI）」≤ 15 分鐘。
- 透過 `batch` 模式可一次生成 ≥ 100 支 1080p 短片，無人工介入。
- 產出的影片均通過本文件所列 **功能/非功能** 驗收標準。

---

# 範疇（Scope）

## In-Scope

- **CLI 工具**（Windows 11）：以 **Python + MoviePy + FFmpeg** 實作。
- **輸入**：由使用人員提供之 **JSON 陣列** 設定檔，描述每支影片的內容（字母、中文、主圖、音樂等）。
- **輸出**：`1920×1080 @ 30fps`、`H.264 + AAC` MP4 影片；檔名 `{word_en}.mp4`。
- **注音**：程式自動為中文產生注音（離線）；預設顯示於中文右方。
- **音訊**：每支影片可帶入 **專屬 MP3**（不循環）；最後 3 秒提供嗶聲提示（可開關）。

## Out-of-Scope

- 不支援雲端服務整合、線上字典/圖片/音樂抓取；不提供 GUI。
- 不輸出直式或 1:1 畫面；不提供字幕檔。

## 假設與依賴（Assumptions & Dependencies）

- 已安裝 **FFmpeg** 並可由 PATH 存取。
- 中文注音採 **本地字典**（建議：`pypinyin` 的 `Style.BOPOMOFO`；必要時以 `opencc` 做繁簡轉換），**不依賴外部 API**。
- 圖片與 MP3 之授權由使用者確保；若主圖缺失則以 **白色底圖** 代替。

---

# 功能性需求（Functional Requirements）

> 採「本系統應…」句式，MoSCoW 標記優先度。

### 1. 輸入與資料模型

| ID         | 敘述                                                                                                                | 優先度  |
| ---------- | ----------------------------------------------------------------------------------------------------------------- | ---- |
| FR-INPUT-1 | 本系統應以 **JSON 陣列** 作為批次輸入，每個元素代表一支影片。                                                                 | Must |
| FR-INPUT-2 | 本系統應支援欄位：`letters, word_en, word_zh, image_path, music_path, countdown_sec, reveal_hold_sec, theme`。 | Must |
| FR-INPUT-3 | 本系統應在 `image_path` 缺檔時以 **白色底圖** 取代，並寫入日誌。                                                           | Must |
| FR-INPUT-4 | 本系統應自動為 `word_zh` 產生 **注音** 並顯示於中文右方（可關閉）。                                                           | Must |

### 2. 版面與合成

| ID          | 敘述                                                                      | 優先度    |
| ----------- | ----------------------------------------------------------------------- | ------ |
| FR-LAYOUT-1 | 本系統應以固定解析度 **1920×1080\@30fps** 合成。                        | Must   |
| FR-LAYOUT-2 | 本系統應於左上顯示 `letters`，右上顯示中文+注音，左側顯示計時器中央為主圖，底部在倒數計時後顯示英文單字。 | Must   |
| FR-LAYOUT-3 | 本系統應支援進場特效 **fade** 與 **slide**（擇一，全域預設可在 config 指定）。      | Should |
| FR-LAYOUT-4 | 本系統應於揭示答案時使用 **typewriter** 動效。                             | Should |

### 3. 計時與音訊

| ID         | 敘述                                                                | 優先度  |
| ---------- | ----------------------------------------------------------------- | ---- |
| FR-TIMER-1 | 本系統應顯示 `MM:SS` 計時器，預設 **10 秒** 倒數；位置在 **左側黑底白字** 區塊。 | Must |
| FR-TIMER-2 | 本系統應在最後 **3 秒** 播放嗶聲提示（可透過參數停用）。                     | Must |
| FR-TIMER-3 | 本系統應支援隱藏倒數計時的顯示（例如 CLI 旗標 `--hide-timer` 或 `--timer-visible false`），但提示音（嗶聲）行為不受此設定影響，仍依 `--beep` 參數控制。 | Must |
| FR-AUDIO-1 | 本系統應支援為每支影片匯入 **一段 MP3**（不循環），與嗶聲做混音，避免削波。           | Must |

### 4. 輸出與檔名

| ID          | 敘述                                                            | 優先度  |
| ----------- | ------------------------------------------------------------- | ---- |
| FR-EXPORT-1 | 本系統應以 **H.264（yuv420p, CRF 18–23）+ AAC** 匯出 MP4。 | Must |
| FR-EXPORT-2 | 本系統應以 `{word_en}.mp4` 命名並輸出至 `./out`（可變更）。       | Must |
| FR-EXPORT-3 | 本系統應於影片末端加入 **1 秒** 淡出。                          | Must |

### 5. CLI 與操作

| ID       | 敘述                                                   | 優先度  |
| -------- | ---------------------------------------------------- | ---- |
| FR-CLI-1 | 本系統應提供 `spellvid make` 以參數生成單支影片。       | Must |
| FR-CLI-2 | 本系統應提供 `spellvid batch` 以 JSON 陣列檔批次生成。 | Must |
| FR-OPS-1 | 本系統應產出結構化日誌，遇缺檔或錯誤時不中斷整批流程並記錄。          | Must |

---

# 非功能性需求（Non-Functional Requirements）

## 效能與容量

- 單支 12 秒 1080p 輸出時間 **不設硬性上限**；但需於一般 i5/i7 桌機可穩定完成批次輸出。

## 可用性與韌性

- 批次模式遇單筆失敗時 **不中斷**，最後彙總錯誤清單。

## 安全與授權

- 離線執行；不收集或傳送個資。輸入資產授權由使用者負責。

## 可維運性與觀測性

- `--verbose` 顯示詳細日誌；提供 `--dry-run` 檢查輸入檔與資產存在性。

## 相容性與擴充性

- 平台：**Windows 11 x64**。
- 字型：採用 **系統內建字型**（預設 `Segoe UI` 英文、`Microsoft JhengHei` 中文；可於 config 覆寫）。

## 易用性（DX）

- 內建範例 JSON 與資產結構；`--help` 提供參數說明與範例。

---

# 限制條件（Constraints）

| 類別  | 條目                        | 說明                                                  |
| --- | ------------------------- | --------------------------------------------------- |
| 技術棧 | Python + MoviePy + FFmpeg | 影片合成以 MoviePy，轉碼與封裝以 FFmpeg。                        |
| 依賴  | 本地注音                      | 建議 `pypinyin`（BOPOMOFO）與 `opencc`（如需繁簡轉換）；可由內建詞表回退。 |
| 平台  | Windows 11                | 僅針對 Windows 11 驗證。                                  |
| 內容  | 授權                        | 圖片/音樂的著作權與授權由使用者提供並確認。                              |

---

# 驗收標準（Acceptance Criteria）

## 功能驗收（Gherkin）


```
Scenario: 批次生成（batch）
  Given 準備 JSON 陣列檔 data/words.json（見下方 Schema 與範例）
  When 執行  spellvid batch --json data/words.json --outdir out --beep true
  Then 為 JSON 中每個物件輸出一支 MP4，檔名為 {word_en}.mp4
   And 若 image_path 缺檔則以白色底圖替代並於日誌記錄
   And 程序完成後輸出成功/失敗總結
```

## 非功能驗收

- 批次執行時即使某些項目失敗，整體流程仍完成，並於結束給出錯誤摘要。
- `--dry-run` 能檢查所有 `image_path` 與 `music_path` 是否存在並列出缺失。

---

> **填寫指南（提交簡述前可參考）**：
>
> 1. 產品型態：API / SDK / CLI / Portal（擇一或多選）。
> 2. 目標開發者與主要用例（Top 3）。
> 3. 需要整合的既有系統/第三方。
> 4. 資料模型或核心實體（可先列名詞）。
> 5. 身分/授權模式（OIDC/OAuth2/API Key/多租戶）。
> 6. 效能與可用性目標（P95/P99、SLO、RPO/RTO）。
> 7. 安全/隱私/合規要求（若涉及個資/支付）。
> 8. 平台/雲環境/地區限制。
> 9. 時程與階段（Alpha/Beta/GA）。
> 10. 已知限制與風險。



---

# ⭐ 已確認事項（根據使用者 2025-09-08 提供）

- **產品型態**：CLI（命令列工具）。
- **主要目標**：產出短片；畫面包含：
  - 左上：英文字母（例：`I i`）。
  - 右上：中文＋自動注音（例：`冰塊` + 注音）。
  - 中央：與單字語意相關之圖像。
  - 左側：倒數計時（`MM:SS`）。
  - 下方：倒數結束後顯示答案（英文單字）。
- **技術棧**：Python + MoviePy + FFmpeg。
- **部署/平台**：Windows 11。
- **整合**：無外部服務整合（離線可執行）。

# 功能性需求（增補草案｜與上方 FR 表對齊）

| ID       | 名稱    | 敘述（本系統應…）                                   | 優先度    |
| -------- | ----- | -------------------------------------------------------- | ------ |
| FR-CLI-1 | 單片生成  | 透過 `spellvid make` 以參數建立單支影片，包含左上字母、右上中文、中央圖像、倒數計時與揭示答案。 | Must   |
| FR-CLI-2 | 批次生成  | 透過 `spellvid batch` 從 CSV/JSON 讀取多筆設定批次輸出。               | Must   |
| FR-UI-1  | 計時器疊圖 | 顯示 `MM:SS` 計時器，並於到時觸發揭示動畫。                               | Must   |
| FR-UI-2  | 圖像布局  | 依佈局參數將圖像縮放至可視框內，維持長寬比並可設定邊距。                             | Must   |
| FR-UI-3  | 揭示動畫  | 倒數結束在底部顯示英文單字，支援 `fade` 或 `typewriter`。                  | Should |
| FR-AUD-1 | 音訊混音  | （若啟用）支援 BGM 與倒數結束提示音之音量混合。                               | Could  |
| FR-EXP-1 | 轉碼輸出  | 以 FFmpeg 匯出 `MP4(H.264/AAC)`、指定 fps 與解析度。                | Must   |
| FR-OPS-1 | 日誌    | 輸出執行與錯誤日誌；缺檔案時記錄並跳過。                                     | Must   |

# 非功能性需求（增補草案）

- **相容性**：Windows 11（x64）。
- **效能**：P95 單支 12s 1080p 影片輸出時間 ≤ TBD 秒（視硬體而定）。
- **重現性**：同一輸入與版本產生可重現的影像與時間軸（±1 frame）。
- **可用性（DX）**：`--help` 出現完整參數說明與範例；提供預設模板可即用。

# 限制條件（更新）

| 類別  | 條目                        | 說明                                         |
| --- | ------------------------- | ------------------------------------------ |
| 技術棧 | Python + MoviePy + FFmpeg | 需安裝與定位 FFmpeg；影片合成以 MoviePy 為主、匯出以 FFmpeg。 |
| 平台  | Windows 11                | 以 Windows 11 為支援與測試主平台。                    |
| 整合  | 無                         | 不依賴雲端或外部 API，離線可執行。                        |

---

# 📦 輸入 JSON Schema（Draft-07）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SpellVidItems",
  "type": "array",
  "items": {
    "type": "object",
    "required": [
      "letters", "word_en", "word_zh",
      "image_path", "music_path"
    ],
    "properties": {
      "letters": {"type": "string", "description": "左上顯示之字母，例：\"I i\""},
      "word_en": {"type": "string", "description": "英文單字（底部揭示，首字母大寫）"},
      "word_zh": {"type": "string", "description": "中文（右上顯示，程式自動產生注音）"},
  "image_path": {"type": "string", "description": "中央主資產檔路徑（圖片或影片），缺檔時以白色底圖取代"},
      "music_path": {"type": "string", "description": "專屬 MP3 音樂，不循環"},
      "countdown_sec": {"type": "integer", "default": 10, "minimum": 1},
      "reveal_hold_sec": {"type": "integer", "default": 5, "minimum": 1},
      "theme": {"type": "string", "enum": ["default"], "default": "default"}
    },
    "additionalProperties": false
  }
}
```

\*\*範例 \*\***`data/words.json`**

```json
[
  {
    "letters": "I i",
    "word_en": "Ice",
    "word_zh": "冰塊",
    "image_path": "assets/ice.png",
    "music_path": "assets/ice.mp3",
    "countdown_sec": 10,
    "reveal_hold_sec": 5,
    "theme": "default"
  }
]
```

# 🛠️ CLI 介面（參考）

```bash
# 單支
spellvid make \
  --letters "I i" \
  --word-en Ice \
  --word-zh 冰塊 \
  --image assets/ice.png \
  --music assets/ice.mp3 \
  --countdown 10 \
  --reveal-hold 5 \
  --size 1920x1080 \
  --fps 30 \
  --beep true \
  --out out/Ice.mp4

# 批次
spellvid batch --json data/words.json --outdir out --beep true --dry-run false
```

# 🎨 版面配置（Default Theme: 1920×1080）

- **安全邊界（Safe Area）**：上下左右各 64 px。
 - **Letters（左上）**：x=64, y=48，字級 160（`Segoe UI`）。
   - 變更：左上顯示的英文字母改為使用預先準備的圖片資產，來源為 `assets/AZ/`。每個大寫字母使用檔名 `{LETTER}.png`（例如 `A.png`），對應小寫字母使用 `{letter}_small.png`（例如 `a_small.png`）。
  - 命名規則與預設行為：若 `letters` 欄位包含多個字元（例如 `I i`），程式應按文字順序將對應的圖片水平排列，並以既有的安全邊界與間距（gap）自動縮放以符合左上區塊；若對應圖片不存在，則不顯示該字元的圖片（留白），並在日誌中記錄 WARNING；不得以文字自動替代顯示。
  - CLI 參數影響：保留旗標 `--letters-as-image/--no-letters-as-image`（預設啟用），若使用者選擇 `--no-letters-as-image` 則始終以文字渲染；但在 `--letters-as-image` 模式下若資產缺失，行為為留白（不回退文字）。
- **Timer（左側黑底白字）**：x=64, y=420，框 220×120，字級 64，格式 `MM:SS`。
- **Chinese+Zhuyin（右上）**：右上對齊（x=1920-64, y=64），中文字級 96（`Microsoft JhengHei`），注音字級 48，置於中文下方一行；多字以空格分隔。
- **Image / Video（中央）**：在 (x=320..1600, y=220..900) 的內容框內以 **contain** 等比縮放；若為影片，將影片裁切/縮放以置中並在輸出期間播放，以loop方式填滿時長。
- **Answer（底部揭示）**：x=960, y=980（置中），字級 128，**typewriter** 動效。

# 🔊 音訊策略

- **音樂**：`music_path` 單段、不循環；整段鋪滿影片（不足長度則保持靜音，不補 loop）。
- **嗶聲**：預設開啟；最後 3 秒每秒 1 次（1kHz，300ms，-12dBFS），可以參數停用。
- **混音**：正規化峰值至 -1 dBTP；避免削波，MoviePy 混音後再由 FFmpeg 封裝。
# 📊 底部彩色進度條（新增需求）

- 進度條位置：畫面底部靠近答案揭示區域，上方保留 24 px 間距；寬度覆蓋安全區內寬度（x=64..1856），高度 16 px（可依主題設定）。
- 視覺語義（更新）：進度條一開始即由左至右呈現三段固定顏色（綠 / 黃 / 紅），三段占位固定；隨著倒數進行，進度條會自左（綠段）向右逐步「消失」（透明或背景色顯示），呈現從綠→黃→紅 逐段遞減的視覺效果，而不是顏色本身變換。
- 時間行為（預設 `countdown_sec = 10`）：
  - 初始狀態：左段為綠色（覆蓋 50% 寬度）、中段為黃色（覆蓋 20% 寬度）、右段為紅色（覆蓋 30% 寬度）。
  - 倒數進行時：從 t=0 開始（倒數開始），進度條左側像素逐步隱藏；在倒數至 5s 時綠段應已部分或全部消失；在倒數至 3s 時綠段應幾乎消失並開始隱藏黃段；在倒數至 0s 時三段皆呈隱藏（整條空）。
  - 非 10s 情況：消失進度按時間線性分配至整支倒數時長（實作端以比例計算隱藏速率）。
- 可延伸說明：若 `countdown_sec` 不是 10，系統應以相同比例分段（綠佔 50% 時間、黃佔 20% 時間、紅佔 30% 時間），以維持一致的視覺與語意；具體分段由實作端依 `countdown_sec` 計算。
- 動作細節：進度條以平滑動畫更新（建議至少 10 fps 更新率）；當啟用 `--beep` 時，嗶聲與進度條進入最後 3 秒（右側紅段即將完全消失的時段）同步發生。
- 可配置項：CLI 可新增旗標 `--progress-bar/--no-progress-bar` 控制是否顯示（預設顯示）。
- 圓角樣式：進度條應採用圓角矩形樣式以提升視覺質感，建議預設圓角半徑 8 px（在 1920×1080 視窗下）；實作應啟用抗鋸齒或軟化邊緣以避免鋸齒感。若未特別指定，圓角半徑應為固定值（不影響三段寬度比例）。

# 📁 專案結構建議

```
project/
├─ spellvid/                # 程式原始碼
├─ assets/                  # 範例圖片/音樂/嗶聲
├─ data/                    # JSON 設定檔
├─ out/                     # 輸出影片
└─ README.md
```

# ✅ 測試案例（節錄）

- **TCS-IMG-404**：`image_path` 不存在 → 以白底圖替代，日誌包含 WARNING。
- **TCS-BEEP-OFF**：`--beep false` → 最後 3 秒無嗶聲。
- **TCS-AUDIO-TRIM**：`music_path` 長度 < 影片 → 音樂不循環，尾段靜音。
- **TCS-TYPEWRITER**：揭示文字逐字出現，總時長 ≥ `reveal_hold_sec`。
 - **TCS-PROG-BAR-DEFAULT**：使用預設 `countdown_sec=10` 時，畫面底部出現三段顏色的進度條；在 10~5s 段位主要為綠色，5~3s 為黃色，3~0s 為紅色；進度條從滿條遞減到空條，顏色切換時無閃爍並與嗶聲同步（若啟用）。
 - **TCS-PROG-BAR-PROPORTIONAL**：當 `countdown_sec` 不是 10 時，進度條應按比例分段（綠 50%、黃 20%、紅 30% 的倒數時間域）；檢查顏色切換的時間點與分段比例是否符合預期。

