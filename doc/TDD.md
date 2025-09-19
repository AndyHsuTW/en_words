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
  - FR-TIMER：10 秒倒數、左側黑底白字、最後 3 秒嗶聲（可關閉）。
  - FR-AUDIO：單支 MP3 不循環與嗶聲混音、避免削波。
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
- 音樂：`tests/assets/ball.mp3`。
- 嗶聲：動態生成（1kHz 正弦波, 300ms, 0.2 音量, 44100Hz 採樣率, 立體聲）。

---

## 6. 測試案例矩陣（TCS）

| ID               | 類型          | 對應需求      | 前置/步驟                          | 驗證點                          |
| ---------------- | ----------- | --------- | ------------------------------ | ---------------------------- |
| TCS-SCHEMA-001   | Unit        | FR-INPUT  | JSON 含未知欄位                     | 驗證 Schema 拒絕並回報欄位名           |
| TCS-SCHEMA-002   | Unit        | FR-INPUT  | 省略 countdown/reveal            | 使用預設 10/5                    |
| TCS-ZHUYIN-001   | Unit        | FR-INPUT  | `word_zh=冰塊`                   | 產生注音（ㄅㄧㄥ ㄎㄨㄞˋ），離線運作          |
| TCS-LAYOUT-001   | Unit        | FR-LAYOUT | 計算四區域座標                        | 座標在 1920×1080 安全邊界內          |
| TCS-TIMER-001    | Unit        | FR-TIMER  | 倒數 10 秒                        | 由 00:10 至 00:00，每秒更新         |
| TCS-TYPE-001     | Unit        | FR-LAYOUT | reveal\_hold=5                 | typewriter 遍歷完整字串，持續≥5s      |
| TCS-AUDIO-001    | Unit        | FR-AUDIO  | `short.mp3`                    | 不循環；尾段靜音；峰值≤-1 dBTP          |
| TCS-BEEP-001     | Unit        | FR-TIMER  | 最後 3 秒                         | 三段嗶聲可檢出；可關閉                  |
| TCS-PIPE-001     | Integration | FR-LAYOUT | 合成一支 12s                       | 中間幀序正確；無例外                   |
| TCS-PROG-001     | Unit        | FR-UI / FR-TIMER | 進度條基礎行為（countdown_sec=10） | 在 10~5s 顯示綠色、5~3s 顯示黃、3~0s 顯示紅；進度條從滿遞減至空。 |
| TCS-PROG-002     | Unit        | FR-UI     | 進度條更新率驗證                   | 進度條以至少 10 fps 更新，顏色切換平滑無閃爍。 |
| TCS-PROG-003     | Integration | FR-UI     | 非 10s 倒數（比例分段）             | 當 `countdown_sec` 非 10，進度條按比例分段（綠 50%、黃 20%、紅 30%）且顏色切換時間點符合預期。 |
| TCS-PROG-004     | Integration | FR-TIMER / FR-AUDIO | 嗶聲同步                         | 啟用 `--beep` 時，最後 3 秒嗶聲與進度條變為紅色的時間段同步發生；使用音訊/波形檢查驗證。 |
| TCS-FALLBACK-001 | Integration | FR-INPUT  | 缺 `image_path` 或視覺資產不是存在的圖片/影片 | 以白底圖合成；畫面取樣接近 #FFFFFF        |
| TCS-EXPORT-001   | Integration | FR-EXPORT | ffprobe 檢查                     | h264 / yuv420p / 30fps / aac |
| TCS-EXPORT-002   | Integration | FR-EXPORT | word\_en=Ice                   | 檔名 `Ice.mp4` 於 `out/`        |
| TCS-EXPORT-003   | Integration | FR-EXPORT | 片尾                             | 最末 1s 亮度趨降（淡出）               |
| TCS-LOG-001      | Integration | FR-OPS    | 缺圖/缺音                          | 流程不中斷；日誌 WARNING             |
| TCS-DRYRUN-001   | E2E         | NFR       | `--dry-run`                    | 不輸出檔案；列出缺資產；exit code=0      |
| TCS-BATCH-001    | E2E         | 批次驗收      | `batch --json data/words.json` | 每筆輸出 1 檔；彙總成功/失敗             |
| TCS-BEEP-TOGGLE  | E2E         | FR-TIMER  | `--beep false`                 | 最後 3 秒無嗶聲頻段峰值                |
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
  And items with missing image or video use a white background fallback
     And the process prints a summary with counts of succeeded and skipped items

  Scenario: Dry-run 檢查資產
    When I run "spellvid batch --json data/words.json --outdir out --dry-run true"
    Then no MP4 files are created
     And a list of missing assets is printed
     And the exit code is 0
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

