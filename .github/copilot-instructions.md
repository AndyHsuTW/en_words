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
  - Input: JSON array (schema in `spellvid/utils.py` as `SCHEMA`).
  - Pipeline: parse JSON → validate schema → per-item layout computation (`compute_layout_bboxes`) → render text/image clips using Pillow + MoviePy (`_make_text_imageclip` / ImageClip) → optional audio/beep mixing → export via MoviePy which uses ffmpeg (configured by `_find_and_set_ffmpeg`).
  - Output: MP4 per item, default path `out/{word_en}.mp4` (see `cli.batch` behavior).

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
  - Code changes: `spellvid/utils.py` (core), `spellvid/cli.py` (flags/behavior), `scripts/` for auxiliary helpers.
  - Tests: `tests/` — follow existing style (pytest, skip when MoviePy missing). Add a unit test for any public helper you change and update layout pixel tests when behavior alters rendering.

If any section is unclear or you want more examples (e.g. CI job steps, ffprobe commands used in tests, or a sample failing test case), tell me which area to expand and I'll iterate.
