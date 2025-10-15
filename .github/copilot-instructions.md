<!-- .github/copilot-instructions.md -->
# Copilot instructions for SpellVid (en_words)

Purpose: Give an AI coding agent the exact, discoverable knowledge needed to contribute code, tests, and fixes in this repository quickly.

- Short repo summary
  - CLI tool that composes short 1080p teaching videos (left letters, right Chinese+zhuyin, left timer, center image, bottom reveal).
  - Implemented in Python using MoviePy for composition and FFmpeg for encoding. Key code lives in `spellvid/`.

- Important files to read first (order matters)
  1. `spellvid/utils.py` — core helpers: layout math (`compute_layout_bboxes`), Pillow text renderer (`_make_text_imageclip`), ffmpeg detection (`_find_and_set_ffmpeg`), schema (`SCHEMA`), asset checks and small audio stubs. Many tests import internal helpers from here.
  2. `spellvid/cli.py` — CLI entrypoints (`make`, `batch`) and argument semantics. Use this to understand expected CLI flags (e.g. `--dry-run`, `--use-moviepy`).
  3. `config.json` — example single-item data used by examples; shows field names and paths.
  4. `requirements-dev.txt` — canonical dependencies for development & CI (moviepy, numpy, pydub, jsonschema, opencv-python, pytest).
  5. `tests/` — pytest suite demonstrates project patterns (headless layout checks, integration expectations). `tests/test_layout.py` shows how tests rely on internal helpers like `_make_text_imageclip` and `_mpy` being present.
  6. `doc/` — `requirement.md` and `TDD.md` contain project intent, CLI examples, testing strategy and acceptance criteria. Good to cite for behavior expectations.

- Big-picture architecture (short)
  - **NEW (重構中)**: 專案正在進行架構重構(branch: `002-refactor-architecture`),將單體 `utils.py` 拆分為分層模組:
    - `spellvid/shared/` — 共用型別、常數、驗證邏輯
    - `spellvid/domain/` — 領域邏輯(佈局、注音、效果、計時)
    - `spellvid/application/` — 應用服務(視頻生成、批次處理、資源檢查)
    - `spellvid/infrastructure/` — 基礎設施適配器(MoviePy、Pillow、FFmpeg)
    - `spellvid/cli/` — CLI 命令入口
  - Input: JSON array (schema in `spellvid/shared/validation.py` as `SCHEMA`).
  - Pipeline: parse JSON → validate schema → per-item layout computation (`domain.layout.compute_layout_bboxes`) → render text/image clips using Pillow + MoviePy (`infrastructure.rendering` / `infrastructure.video`) → optional audio/beep mixing → export via MoviePy which uses ffmpeg (configured by `infrastructure.media.ffmpeg_wrapper`).
  - Output: MP4 per item, default path `out/{word_en}.mp4` (see `cli.batch` behavior).
  - **向後相容**: `spellvid/utils.py` 保留但標記為 deprecated,re-export 新模組函數以維持測試通過。

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
