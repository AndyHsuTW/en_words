# Repository Guidelines

 **所有代理回覆必須使用繁體中文**  
(Please ensure all responses are in Traditional Chinese)

---

## Project Structure & Module Organization
- `spellvid/` holds the production code: `cli.py` exposes the CLI entry point while `utils.py` manages rendering, media loading, and ffmpeg integration.
- `tests/` contains pytest suites, with reusable fixtures under `tests/assets/`. Store any new golden media there, not under `assets/`.
- `assets/` keeps shared input media used by examples; `out/` is ignored and safe for local renders.
- `scripts/` provides diagnostic helpers (`run_tests.ps1`, `render_example.ps1`, `analyze_video_bounds.py`) and should remain lightweight. Long-form notes live in `doc/`; `.github/` stores workflow guidance.

## Build, Test, and Development Commands
- `python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r requirements-dev.txt` prepares the environment.
- `.\\scripts\\run_tests.ps1` executes the full pytest suite inside the venv; use this before pushing.
- `pytest tests\\test_video_mode.py` (or any path) focuses on a specific area; add `--cov=spellvid --cov-report=term-missing` when validating coverage.
- `python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh ㄧˋ` renders a word video; add `--dry-run` to validate assets without producing output.

## Coding Style & Naming Conventions

## 使用 Pylance MCP (重要)

- 在本工作區執行 Python 程式、片段或測試時，請透過 Pylance 的 MCP（mcp_pylance）機制執行或先呼叫 `configure_python_environment`，以確保編輯器分析、工具呼叫（例如 `mcp_pylance_mcp_s_pylanceRunCodeSnippet` / `mcp_pylance_mcp_s_pylanceRunCodeSnippet` 等）和實際執行使用相同的 Python 環境。這能避免環境不同步造成的導入或解析錯誤，並提升 Pylance 對型別與語法分析的正確性。

-- 小貼士：若使用 VS Code，確認 Pylance 已啟用並且 MCP runner 指向專案 venv（例如透過呼叫 `configure_python_environment` 或在 Pylance 的設定中選擇對應的 Python 可執行檔）。

- Follow PEP 8 with 4-space indentation and `snake_case` for functions, variables, and module names; reserve CamelCase for classes.
- Keep business logic in `spellvid.utils` and expose narrow orchestration in `spellvid.cli`.
- Use type hints and explicit helper functions (see `spellvid/utils.py`) to keep rendering steps testable. Prefix internal helpers with `_` when scope is private.

## Testing Guidelines
- The project relies on pytest + pytest-cov; every feature change should include or update a `test_*.py` file alongside relevant fixtures.
- Name tests after the scenario under validation (e.g., `test_video_overlap_handles_z_order`). Visual comparisons belong in helpers such as `scripts/_check_snapshot_pixels.py`.
- Store new media fixtures in `tests/assets/` and document why they are needed within the test module. Avoid committing artifacts generated in `out/`.

## Commit & Pull Request Guidelines
- Recent history favors short Traditional Chinese summaries with follow-up bullet fragments separated by ` - ` (e.g., `優化倒數動畫 - 調整觸發時機 - 更新測試`). Mirror that tone and reference issue IDs when applicable.
- Squash related changes before raising a PR. Provide a concise summary, test evidence (`scripts/run_tests.ps1` output or coverage flags), and attach a sample render path when behavior changes can be seen visually.
- Highlight media or configuration updates explicitly, including any expectations about `FFmpeg/ffmpeg.exe` usage or new assets.
