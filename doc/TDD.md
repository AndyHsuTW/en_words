# SpellVid — 測試驅動開發（TDD）測試計畫

**文件版本**：v1.0\
**最後更新**：2025-09-08\
**對應需求文件**：SpellVid 需求分析（CLI 專案）

---

## 1. 目的

以 TDD 方式確保 SpellVid（Python + MoviePy + FFmpeg 的 Windows 11 CLI）在 **批次輸出英語學習短片** 的核心需求上可被自動化驗證，覆蓋 **輸入/版面/計時/音訊/輸出/CLI/營運** 等面向。

---

## 2. 測試範圍

- **功能性（FR）**：
  - FR-INPUT：JSON 陣列輸入、欄位驗證、缺圖回退（白底）。
  - FR-LAYOUT：1920×1080\@30fps 版面；左上字母、右上中文+注音、左側計時器、中央圖像、底部 typewriter 揭示。
  - FR-TIMER：10 秒倒數、左側黑底白字、最後 3 秒嗶聲（可關閉）、計時顯示可被隱藏但嗶聲仍可獨立控制。
  - FR-EXPORT：H.264(yuv420p, CRF 18–23)+AAC、檔名 `{word_en}.mp4`、片尾 1s 淡出。
  - FR-CLI/OPS：`batch` 模式、`--dry-run`、結構化日誌、失敗不中斷。
- **非功能（NFR）**：可維運性（dry-run、日誌）、相容性（Win11 x64）。

---

## 3. 測試策略與工具

- **單元測試**：純函式（JSON 驗證、注音生成、座標與時間軸計算、typewriter 分幀、嗶聲產生器、混音正規化）。
- **整合測試**：合成管線（MoviePy → FFmpeg）、資產缺失回退、輸出屬性驗證（`ffprobe`）。
- **端對端（E2E/CLI）**：以 `spellvid batch` 驗證完整流程、錯誤彙總、參數旗標。
- **工具**：pytest、ffprobe（FFmpeg）、pydub、opencv-python、numpy。

---

## 4. 測試環境

- OS：Windows 11 x64
- Python：3.13+
- 依賴：MoviePy、FFmpeg（`ffmpeg`/`ffprobe` 於 PATH）、pydub、opencv-python、jsonschema、numpy
- 硬體：一般桌機（效能無硬性門檻）

---

## 5. 測試資料

- `data/words.json`：至少 3 筆（完整 / 缺資產（image/video 缺失） / 音樂短於影片）。
- 視覺資產（圖片或影片）：`assets/ice.png`、`assets/empty.png`（全白 1920×1080）、`assets/sample.mp4`（短片範例）。
- 開頭影片（固定加入）：`assets/entry.mp4`（作為每支輸出影片的開頭片段）。
- 音樂：`tests/assets/ball.mp3`。
- 嗶聲：動態生成（1kHz 正弦波, 300ms, 0.2 音量, 44100Hz 採樣率, 立體聲）。

---

## 6. 測試案例矩陣（TCS）

| ID               | 類型          | 對應需求      | 前置/步驟                          | 驗證點                          |
| ---------------- | ----------- | --------- | ------------------------------ | ---------------------------- |
| TCS-SCHEMA-001   | Unit        | FR-INPUT  | JSON 含未知欄位                     | 驗證 Schema 拒絕並回報欄位名           |
| TCS-SCHEMA-002   | Unit        | FR-INPUT  | 省略 countdown/reveal            | 使用預設 10/5                    |
| TCS-LETTERS-001  | Unit        | FR-LAYOUT | `letters` 使用圖片資源（assets/AZ/） | 程式應能載入 `{LETTER}.png` 與 `{letter}_small.png`，多字元按序排列；若圖片缺失，畫面應保留該字元位置為空白（不以文字替代），並在日誌中記錄 WARNING。 |
| TCS-ZHUYIN-001   | Unit        | FR-INPUT  | `word_zh=冰塊`                   | 產生注音（ㄅㄧㄥ ㄎㄨㄞˋ），離線運作          |
| TCS-LAYOUT-001   | Unit        | FR-LAYOUT | 計算四區域座標                        | 座標在 1920×1080 安全邊界內          |
| TCS-TIMER-001    | Unit        | FR-TIMER  | 倒數 10 秒                        | 由 00:10 至 00:00，每秒更新         |
| TCS-TYPE-001     | Unit        | FR-LAYOUT | reveal\_hold=5                 | typewriter 遍歷完整字串，持續≥5s      |
| TCS-AUDIO-001    | Unit        | FR-AUDIO  | `short.mp3`                    | 不循環；尾段靜音；峰值≤-1 dBTP          |
| TCS-BEEP-001     | Unit        | FR-TIMER  | 最後 3 秒                         | 三段嗶聲可檢出；可關閉                  |
| TCS-TIMER-HIDE   | Unit        | FR-TIMER  | 啟用 `--hide-timer` 或相等設定           | 畫面中不應顯示計時器區塊（畫面取樣應找不到計時 timer 的像素/區塊），但音訊仍包含最後 3 秒嗶聲（若 `--beep` 開啟）。 |
| TCS-PIPE-001     | Integration | FR-LAYOUT | 合成一支 12s                       | 中間幀序正確；無例外                   |
| TCS-PROG-001     | Unit        | FR-UI / FR-TIMER | 進度條基礎行為（countdown_sec=10） | 初始狀態顯示三段固定顏色（綠/黃/紅，寬度分別 50%/20%/30%）；隨倒數進行，進度條自左向右逐步消失，最終變空。 |
| TCS-PROG-002     | Unit        | FR-UI     | 進度條更新率驗證                   | 進度條消失動畫以至少 10 fps 更新，消失過程應平滑且無像素跳動或閃爍。 |
| TCS-PROG-003     | Integration | FR-UI     | 非 10s 倒數（比例分段）             | 當 `countdown_sec` 非 10，三段顏色寬度仍為 50%/20%/30%（固定），但消失速率依倒數時長線性調整；檢查消失進度與時間吻合。 |
| TCS-PROG-004     | Integration | FR-TIMER / FR-AUDIO | 嗶聲同步                         | 啟用 `--beep` 時，最後 3 秒嗶聲的時間窗應與進度條右側紅段即將消失的時間窗重疊；以音訊波形與畫面時間點驗證同步性。 |
| TCS-PROG-005     | Integration | FR-UI     | 圓角樣式與抗鋸齒驗證                 | 進度條邊緣應為圓角（預設半徑 8 px）；在取樣邊緣時應觀察到平滑無明顯鋸齒（使用 OpenCV 邊緣檢測與中位色檢查）。 |
| TCS-FALLBACK-001 | Integration | FR-INPUT  | 缺 `image_path` 或視覺資產不是存在的圖片/影片 | 以白底圖合成；畫面取樣接近 #FFFFFF        |
| TCS-EXPORT-001   | Integration | FR-EXPORT | ffprobe 檢查                     | h264 / yuv420p / 30fps / aac |
| TCS-ENTRY-001    | Integration | FR-EXPORT | 開頭影片合成                      | 每支輸出檔案的起始段應為 `assets/entry.mp4` 的內容（可由 ffprobe/畫面取樣驗證），且檔案總長應 ≥ entry.mp4 長度。
| TCS-ENTRY-002    | Integration | FR-EXPORT | 開頭影片停留時長                    | 當 JSON 或 CLI 指定 `entry_hold_sec`（或 `--entry-hold`）時，輸出影片在開頭影片播放完畢後應保留指定秒數的停留（可檢查時間戳或持續最後一幀的重複）。
| TCS-ENTRY-003    | Integration | FR-EXPORT / FR-CLI | 多單字合併輸出（--out-file）          | 僅第一段保留開頭影片，後續段落 entry_duration_sec=0；可透過 `scripts/render_example.py --out-file ... --dry-run` 的 JSON 輸出驗證。
| TCS-CLI-ENTRY-001| Unit/Integration | FR-CLI  | CLI 旗標驗證                        | `--entry-hold` 在 `--dry-run` 模式下應被接受並列印解析後的值；在正常執行時會影響輸出行為。 |
| TCS-EXPORT-002   | Integration | FR-EXPORT | word\_en=Ice                   | 檔名 `Ice.mp4` 於 `out/`        |
| TCS-EXPORT-003   | Integration | FR-EXPORT | 片尾                             | 最末 1s 亮度趨降（淡出）               |
| TCS-ENDING-001   | Integration | FR-EXPORT | 預設 `assets\\ending.mp4` 存在                        | 影片尾段應與結尾影片內容銜接，且最終畫面須無黑邊滿版呈現；輸出 metadata 需回報 ending_offset_sec、ending_duration_sec；若檔案缺失則應標記略過。 |
| TCS-LOG-001      | Integration | FR-OPS    | 缺圖/缺音                          | 流程不中斷；日誌 WARNING             |
| TCS-DRYRUN-001   | E2E         | NFR       | `--dry-run`                    | 不輸出檔案；列出缺資產；exit code=0      |
| TCS-LETTERS-002  | Integration | FR-INPUT  | `--dry-run` 與 `letters` 圖片化       | dry-run 應驗證 `assets/AZ/` 中所需的字母圖片是否齊全；列出缺失圖片的檔名，並確認在正常執行模式下缺失字元位置會留白（非文字替代）。 |
| TCS-BATCH-001    | E2E         | 批次驗收      | `batch --json data/words.json` | 每筆輸出 1 檔；彙總成功/失敗             |
| TCS-BEEP-TOGGLE  | E2E         | FR-TIMER  | `--beep false`                 | 最後 3 秒無嗶聲頻段峰值                |
| TCS-TIMER-HIDE-E2E| E2E        | FR-TIMER  | `--hide-timer --beep true`     | 不顯示畫面計時器，但最後 3 秒嗶聲仍會出現在輸出音軌；dry-run 應可驗證參數被接受且不影響資產檢查。 |
| TCS-PRESET-001   | E2E         | FR-LAYOUT | `--effect-in=slide`            | 可成功輸出且具滑入效果                  |

---

## 7. Gherkin（批次流程驗收）

```
Feature: 批次輸出英語學習短片
  As a content maker
  I want to run a single CLI command
  So that I can batch-generate standardized 1080p videos from a JSON array

  Background:
    Given Windows 11 and FFmpeg are installed and on PATH
    And a JSON file data/words.json with 3 items exists

  Scenario: 成功批次輸出（含缺圖回退）
    When I run "spellvid batch --json data/words.json --outdir out --beep true"
    Then for each valid item an MP4 named "{word_en}.mp4" is generated under out/
  And each output MP4 must begin with the contents of `assets\\entry.mp4`
  And if `entry_hold_sec` is specified (or `--entry-hold` passed), the output should include the configured hold duration immediately after the entry video finishes
  And items with missing image or video use a white background fallback
     And the process prints a summary with counts of succeeded and skipped items

  Scenario: Dry-run 檢查資產
    When I run "spellvid batch --json data/words.json --outdir out --dry-run true"
    Then no MP4 files are created
     And a list of missing assets is printed
     And the exit code is 0

  Scenario: 多單字合併輸出只保留一次開頭影片
    Given data/words.json 含有至少兩筆有效項目
    When I run "python scripts/render_example.py --json data/words.json --out-dir out --out-file merged.mp4 --dry-run"
    Then dry-run 輸出中的第一筆結果 `entry_duration_sec` 大於 0
    And 第二筆結果 `entry_duration_sec` 等於 0
    And 日誌顯示將合併暫存檔案成單一輸出


```

---

## 8. 覆蓋率與品質門檻

- Unit/Integration 測試覆蓋率（行數）≥ 70%。
- 主要路徑（批次生成）E2E 必須綠燈。

---

## 9. pytest 設定與標記

- `pytest.ini`
  - `markers = win11: require Windows 11 environment`
  - `addopts = -q --maxfail=1`

---

## 10. 測試輔助（建議程式）

- **ffprobe wrapper**：回傳 `streams`/`format` JSON 用於 codec/fps/pix\_fmt 驗證。
- **波形檢查**（pydub）：量測嗶聲窗口 RMS 高於背景窗口。
- **畫面取樣**（OpenCV）：對選定幀取畫面區域中位色以偵測白底替代與字幕/字母區塊存在。

---

## 11. 執行方式（範例）

```powershell
# 安裝依賴（已安裝 FFmpeg 並在 PATH）
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt

# 執行所有測試
pytest -q

# 僅跑 E2E
pytest -q tests/e2e
```

---

## 12. 產出與證據

- 測試報告（pytest JUnit XML / HTML）。
- 失敗案例的截圖（從影片取幀）與 `ffprobe` 輸出保存於 `tests/artifacts/`。

