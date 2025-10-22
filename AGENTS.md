# Repository Guidelines

 **所有代理回覆必須使用繁體中文**  
(Please ensure all responses are in Traditional Chinese)

---

## Project Structure & Module Organization

### Production Code (`spellvid/`)

**Modular Architecture** (see `.github/copilot-instructions.md` for details):

- **`shared/`** — 共用型別、常數、驗證邏輯
  - `types.py` - 型別定義與 TypedDict
  - `constants.py` - 全域常數
  - `validation.py` - JSON schema 驗證

- **`domain/`** — 領域邏輯 (純邏輯,無外部依賴)
  - `layout.py` - 佈局計算 (含字母工具: `_normalize_letters_sequence`, `_letter_asset_filename`, `_letters_missing_names`)
  - `timing.py` - 時間軸計算
  - `effects.py` - 視覺效果定義
  - `typography.py` - 注音排版邏輯

- **`application/`** — 應用服務 (業務邏輯編排)
  - `video_service.py` - 視頻渲染服務 (**Phase 3.10 重構完成**)
    - `render_video()` - 80-line orchestrator (協調 11 個子函數)
    - 11 sub-functions: 2 完整實作 + 9 存根 (Phase 3.11 將完整實作)
    - VideoRenderingContext - 渲染上下文資料類別
  - `batch_service.py` - 批次處理
  - `context_builder.py` - 上下文準備
  - `resource_checker.py` - 資源驗證

- **`infrastructure/`** — 基礎設施適配器 (外部框架整合)
  - `rendering/` - Pillow 文字渲染
  - `video/` - MoviePy 整合與效果
  - `media/` - FFmpeg 包裝器與音訊處理
  - `ui/` - 進度條 UI

- **`cli/`** — CLI 命令入口
  - `parser.py` - 參數解析
  - `commands.py` - 命令實作

- ⚠️ **DEPRECATED**: **`utils.py`** 保留為向後相容層
  - **當前狀態**: 1,402 lines (原始 3,714 lines, 已減少 62.3%)
  - **內容**: ~30 個 deprecated wrappers + 2 個核心渲染函數
  - **核心函數**: 
    - `render_video_stub` (~283 lines, 功能完整 + DeprecationWarning)
    - `render_video_moviepy` (~45 lines, lightweight wrapper → application.video_service)
  - **保留原因**: 被 >30 測試覆蓋,確保向後相容,平滑過渡
  - **未來計劃**: Phase 3.11 將縮減至 120 lines (96.77% total reduction)
  - **遷移進度**: 55/64 函數已遷移 (85.9%)

### Test Suite (`tests/`)

- **`contract/`** — 契約測試 (驗證遷移契約)
  - `test_usage_analysis_contract.py` - 函數分析契約
  - `test_migration_mapping_contract.py` - 遷移對應契約
  - `test_reexport_layer_contract.py` - Re-export 層契約

- **`integration/`** — 整合測試 (端到端流程驗證)
  - `test_end_to_end_migration.py` - 完整遷移流程
  
- **`unit/`** — 單元測試 (分層模組測試)

- **Root test files** (`test_*.py`) — 功能測試 (向後相容性驗證)
  - 持續使用 `utils.py` deprecated wrappers,確保平滑過渡

- **`assets/`** — 測試用媒體資源 (不要 commit 到 `assets/`)

### Assets & Scripts

- **`assets/`** — 共享輸入媒體 (範例用)
- **`out/`** — 輸出目錄 (git ignored)
- **`scripts/`** — 診斷與分析工具
  - `run_tests.ps1` - 測試執行器
  - `render_example.ps1` / `render_example.py` - 範例渲染
  - `analyze_function_usage.py` - 函數使用分析工具 (311 lines)
  
### Documentation

- **`doc/`** — 技術文檔
  - `ARCHITECTURE.md` - 架構說明
  - `requirement.md` - 需求文檔
  - `TDD.md` - 測試策略

- **`.github/`** — Workflow 指引
  - `copilot-instructions.md` - AI 代理指示

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
- Keep business logic in appropriate layer: `domain/` for pure logic, `application/` for orchestration, `infrastructure/` for framework integration. **Avoid adding new code to `utils.py`** (deprecated).
- Use type hints and explicit helper functions to keep logic testable. Prefix internal helpers with `_` when scope is private.
- For architecture details and file reading order, see `.github/copilot-instructions.md`.

## Testing Guidelines
- The project relies on pytest + pytest-cov; every feature change should include or update a `test_*.py` file alongside relevant fixtures.
- Name tests after the scenario under validation (e.g., `test_video_overlap_handles_z_order`). Visual comparisons belong in helpers such as `scripts/_check_snapshot_pixels.py`.
- Store new media fixtures in `tests/assets/` and document why they are needed within the test module. Avoid committing artifacts generated in `out/`.

## Commit & Pull Request Guidelines
- Recent history favors short Traditional Chinese summaries with follow-up bullet fragments separated by ` - ` (e.g., `優化倒數動畫 - 調整觸發時機 - 更新測試`). Mirror that tone and reference issue IDs when applicable.
- Squash related changes before raising a PR. Provide a concise summary, test evidence (`scripts/run_tests.ps1` output or coverage flags), and attach a sample render path when behavior changes can be seen visually.
- Highlight media or configuration updates explicitly, including any expectations about `FFmpeg/ffmpeg.exe` usage or new assets.

---

## Migration Status

### Phase 3.10 Complete (2025-01-18)

**核心渲染重構完成** - render_video_moviepy 已成功遷移至 orchestration 架構

**已遷移模組** (55/64 functions = 85.9% 完成):
- ✅ Domain Layer: 9 functions (佈局計算、時間軸、效果)
- ✅ Infrastructure Layer: 22 functions (Pillow、MoviePy、FFmpeg、音訊、UI)
- ✅ Application Layer: 24 functions (上下文建構、資源檢查、批次處理、**視頻渲染服務**)
  - **NEW**: 11 video rendering sub-functions (orchestration pattern)
  - **NEW**: VideoRenderingContext dataclass
  - **NEW**: Protocol-based design (IVideoComposer)

**utils.py 狀態** (Phase 3.10):
- **原始**: 3,714 lines
- **當前**: 1,402 lines (52.4% reduction)
- **已移除**: render_video_moviepy 實作 (~1,631 lines → 45-line wrapper)
- **目標**: 120 lines (Phase 3.11) - 96.77% 縮減

**向後相容策略**:
- ✅ render_video_moviepy → 45-line deprecated wrapper (觸發 DeprecationWarning)
- ✅ render_video_stub → 保留完整功能 + DeprecationWarning (~283 lines)
- ✅ ~30 個 Phase 3.1-3.8 deprecated wrappers 持續運作
- ✅ 所有舊 API 保持可用,無 breaking changes

**Phase 3.10 成就** (詳見 `specs/005-phase-3-10/IMPLEMENTATION_SUMMARY.md`):
- ✅ **95.1% code reduction**: render_video_moviepy (1,630 → 80 lines orchestrator)
- ✅ **11 composable sub-functions**: 清晰職責分離,可測試設計
- ✅ **Contract tests**: 18/23 PASSING (78.3%)
- ✅ **Integration tests**: Batch service PASSING
- ✅ **Main test suite**: 146/211 PASSING (69.2%)

**Phase 3.11 計劃** (15-20 hours):
- 🔄 完整實作 9 個 stub rendering functions (~10-12 hours)
- 🔄 修復 38 個測試失敗 (~3-4 hours)
- 🔄 utils.py 最終清理至 120 lines (~2-3 hours)
- 🎯 達成 100% contract tests passing
- 🎯 效能驗證 (<5% overhead)

### 遷移指引

**新功能開發**:
- ✅ **Domain Logic** → `spellvid/domain/` (純邏輯,無依賴)
- ✅ **Framework Integration** → `spellvid/infrastructure/` (Pillow/MoviePy/FFmpeg)
- ✅ **Business Orchestration** → `spellvid/application/` (服務編排)
- ❌ **DO NOT** 添加新功能到 `utils.py` (deprecated)

**導入路徑**:
```python
# ✅ 推薦: 使用新模組
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.application.batch_service import batch_process

# ⚠️ 向後相容: 舊測試可繼續使用
from spellvid.utils import compute_layout_bboxes  # Deprecated wrapper
```

**測試策略**:
- 新測試應 import 新模組
- 現有測試保持不變 (向後相容)
- 契約測試確保遷移正確性
