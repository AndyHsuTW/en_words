<!-- .github/copilot-instructions.md -->
# Copilot instructions for SpellVid (en_words)

Purpose: Give an AI coding agent the exact, discoverable knowledge needed to contribute code, tests, and fixes in this repository quickly.

- Short repo summary
  - CLI tool that composes short 1080p teaching videos (left letters, right Chinese+zhuyin, left timer, center image, bottom reveal).
  - Implemented in Python using MoviePy for composition and FFmpeg for encoding. Key code lives in `spellvid/`.

- Important files to read first (order matters)
  1. **NEW (架構重構)**: `spellvid/domain/layout.py` — 核心佈局計算邏輯 (`compute_layout_bboxes`)
  2. **NEW**: `spellvid/application/video_service.py` — 主要視頻渲染服務 (`render_video`)
  3. **DEPRECATED**: `spellvid/utils.py` — 向後相容層,re-export 新模組函數,將在 v2.0 移除
  4. `spellvid/cli.py` — CLI entrypoints (`make`, `batch`) 和參數語義
  5. `config.json` — 範例配置數據,顯示欄位名稱和路徑
  6. `requirements-dev.txt` — 開發與 CI 的規範依賴 (moviepy, numpy, pydub, jsonschema, opencv-python, pytest)
  7. `tests/` — pytest 套件展示專案模式 (headless 佈局檢查、整合預期)
  8. `doc/ARCHITECTURE.md` — 新模組化架構的完整說明與遷移指南
  9. `doc/requirement.md` 與 `doc/TDD.md` — 專案意圖、CLI 範例、測試策略與驗收標準

- Big-picture architecture (short)
  - **架構重構完成** (2025-10-18): 單體 `utils.py` 已拆分為分層模組:
    - `spellvid/shared/` — 共用型別 (`types.py`)、常數 (`constants.py`)、驗證邏輯 (`validation.py`)
    - `spellvid/domain/` — 領域邏輯: `layout.py` (佈局計算)、`typography.py` (注音渲染)、`effects.py` (視覺效果)、`timing.py` (時間軸)
    - `spellvid/application/` — 應用服務: `video_service.py` (視頻生成)、`batch_service.py` (批次處理)、`resource_checker.py` (資源檢查)
    - `spellvid/infrastructure/` — 基礎設施適配器: `rendering/` (Pillow 文字渲染)、`video/` (MoviePy 整合)、`media/` (FFmpeg/音訊)
    - `spellvid/cli/` — CLI 命令入口與參數解析
  - Input: JSON array (schema in `spellvid/shared/validation.py` as `SCHEMA`)
  - Pipeline: parse JSON → validate schema → per-item layout computation (`domain.layout.compute_layout_bboxes`) → render text/image clips using Pillow + MoviePy (`infrastructure.rendering` / `infrastructure.video`) → optional audio/beep mixing → export via MoviePy which uses ffmpeg (configured by `infrastructure.media.ffmpeg_wrapper`)
  - Output: MP4 per item, default path `out/{word_en}.mp4` (see `application.batch_service` behavior)
  - **向後相容**: `spellvid/utils.py` 保留為輕量 re-export 層,供舊測試與腳本使用,標記為 deprecated 並將在 v2.0 移除

- Project-specific conventions & patterns
  - Tests may import and use internal (underscored) helpers from `spellvid.utils` (e.g. `_make_text_imageclip`) — don't rename or hide these without updating tests.
  - FFmpeg detection: `spellvid.utils._find_and_set_ffmpeg()` will prefer env vars `FFMPEG_PATH` / `IMAGEIO_FFMPEG_EXE`, then repo-local `FFmpeg/ffmpeg.exe`, then imageio-ffmpeg. When making changes affecting ffmpeg, keep this resolution order.
  - Fonts: code prefers system fonts on Windows (`C:\Windows\Fonts\...`). Layout math and headless tests rely on these heuristics. Avoid changing default font paths unless you update `compute_layout_bboxes` and tests.
  - Headless layout determinism: `compute_layout_bboxes` tries to emulate renderer padding and sizes. Any change to `_make_text_imageclip` padding/margins must be mirrored in `compute_layout_bboxes` and tests under `tests/`.
  - Minimal audio: `synthesize_beeps` returns a bytes stub used in tests; real beep behavior is modeled but simple. Tests assert presence/placement rather than full audio fidelity.

- Developer workflows & commands (Windows PowerShell)
  - Create a venv and install dev deps:

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements-dev.txt
    ```

  - Run tests (quick) — use the project helper to ensure the venv is active:

    ```powershell
    .\scripts\run_tests.ps1
    ```

  - Run the CLI locally (single item):

    ```powershell
    python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 --dry-run
    ```

  - Batch mode (dry-run checks assets only):

    ```powershell
    python -m spellvid.cli batch --json config.json --outdir out --dry-run
    ```

    - IMPORTANT: Always activate the project's virtual environment before running any Python commands or tests.
      The test suite and several helpers expect dependencies installed into the repo venv. Examples (PowerShell):

      ```powershell
      # create venv (only if venv not yet created)
      python -m venv .venv
      # activate venv in PowerShell
      .\.venv\Scripts\Activate.ps1
      # install dev deps
      pip install -r requirements-dev.txt

      # run CLI or python script while venv is active
      python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --image assets/ice.png --music assets/ice.mp3 --dry-run

      # run tests while venv is active
      pytest -q
      ```

- Integration points & external dependencies
  - MoviePy: optional at runtime for some tests; `spellvid/utils.py` supports running without moviepy for some operations but many features (ImageClip creation) require it. See `requirements-dev.txt`.
  - FFmpeg: required for final encoding. `_find_and_set_ffmpeg` uses repo-local `FFmpeg/ffmpeg.exe` first if present. CI must ensure ffmpeg is available or set `IMAGEIO_FFMPEG_EXE`.
  - imageio-ffmpeg may be used to locate ffmpeg; code will try to import it as a fallback.

- Tests & CI notes (what tests expect)
  - `tests/test_layout.py` uses `_make_text_imageclip` and `_mpy` if available. Tests will skip if MoviePy isn't importable or if ImageClip frame extraction fails. When adding features that affect text rendering, update tests that assert pixel bbox sizes and padding.
  - Keep `compute_layout_bboxes` and `_make_text_imageclip` in sync: tests compare computed boxes to actual rendered pixel bboxes.

- Small examples to reference in edits
  - Changing timer font/padding: update both `_make_text_imageclip` (pad/bottom_safe_margin) and `compute_layout_bboxes` (pad_x/pad_y/bottom_safe_margin) so tests in `tests/test_layout.py` remain valid.
  - Changing ffmpeg resolution order: update `_find_and_set_ffmpeg` and mention in README/docs + CI setup.

- Where to add changes / tests
  - **NEW (重構後)**: 根據職責選擇模組:
    - 純邏輯計算 → `spellvid/domain/` (佈局、注音、效果)
    - 業務流程編排 → `spellvid/application/` (視頻服務、批次處理)
    - 框架整合 → `spellvid/infrastructure/` (MoviePy/Pillow/FFmpeg 適配器)
    - 型別與常數 → `spellvid/shared/`
    - CLI 參數處理 → `spellvid/cli/`
  - **舊模組**: `spellvid/utils.py` (已 deprecated,避免新增功能,僅保留向後相容)
  - Tests: 
    - 單元測試 → `tests/unit/{layer}/` (測試單一模組,不依賴外部資源)
    - 契約測試 → `tests/contract/` (驗證介面實作符合 Protocol)
    - 整合測試 → `tests/integration/` (測試多模組協作)
    - 現有測試 → `tests/test_*.py` (保持通過,逐步遷移)

If any section is unclear or you want more examples (e.g. CI job steps, ffprobe commands used in tests, or a sample failing test case), tell me which area to expand and I'll iterate.
