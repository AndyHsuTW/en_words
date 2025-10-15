SpellVid (en_words)
=====================

Small CLI to compose short 1080p teaching videos for English words.

## Architecture

SpellVid 採用 **分層架構 (Layered Architecture)** 設計,將專案分為 5 個清晰的層次:

```
CLI Layer → Application Layer → Domain Layer → Infrastructure Layer → Shared Layer
```

### 核心特性

- **職責分離**: 每層專注於自己的職責 (CLI 處理參數 → Application 協調流程 → Domain 計算邏輯 → Infrastructure 適配外部框架)
- **可測試性**: Domain 層使用純函數,可在 < 1 秒內測試完成,無需真實檔案或 MoviePy
- **可擴展性**: 透過 Protocol 介面 (IVideoComposer, ITextRenderer, IMediaProcessor),可輕鬆替換底層實作 (例如用 OpenCV 取代 MoviePy)
- **向後相容**: 舊 API (`spellvid.utils`, `spellvid.cli`) 繼續可用,同時引導遷移到新架構

**詳細架構文檔**: 請參閱 [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)

### 快速導航

| 功能 | 模組 | 說明 |
|-----|------|-----|
| 佈局計算 | `spellvid.domain.layout` | 計算字母、中文、圖片的螢幕位置 (純函數) |
| 注音轉換 | `spellvid.domain.typography` | 中文轉注音邏輯 |
| 視頻生成 | `spellvid.application.video_service` | 協調完整視頻生成流程 |
| 批次處理 | `spellvid.application.batch_service` | 處理多支視頻批次渲染 |
| CLI 命令 | `spellvid.cli.commands` | 命令列介面處理 |

**使用範例** (新 API):

```python
from spellvid.shared.types import VideoConfig
from spellvid.application.video_service import render_video

config = VideoConfig(
    letters="I i",
    word_en="Ice",
    word_zh="冰",
    image_path="assets/ice.png",
    music_path="assets/ice.mp3",
    output_path="out/Ice.mp4"
)

result = render_video(config, dry_run=True)
print(result["status"])  # "dry-run"
```

---

Quick start
-----------

1. Create and activate the project virtual environment (PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

2. Run the test suite inside the venv. Use the provided helper script to ensure
   tests run inside the project's venv:

   ```powershell
   .\scripts\run_tests.ps1
   ```

3. Render a single item (dry-run to validate assets):

   ```powershell
   python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 \
     --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 --dry-run
   ```

---

## Testing

SpellVid 採用測試金字塔策略,從快速的單元測試到完整的端到端測試:

### 快速測試 (< 1 秒)

```powershell
# 測試 Domain 純函數 (無外部依賴)
pytest tests/unit/domain/ -v
```

### 契約測試 (Infrastructure 介面驗證)

```powershell
# 驗證 MoviePy/Pillow/FFmpeg 適配器符合 Protocol
pytest tests/contract/ -v
```

### 整合測試 (Application 協調邏輯)

```powershell
# 測試 video_service 和 batch_service
pytest tests/integration/ -v
```

### 完整測試套件

```powershell
# 執行所有測試 (使用專案 venv)
.\scripts\run_tests.ps1
```

**測試覆蓋率目標**:
- Shared Layer: 95%
- Domain Layer: 90%
- Application Layer: 85%
- Infrastructure Layer: 75%

---

## Backward Compatibility (向後相容性)

舊 API 完全保留,但會顯示 DeprecationWarning:

### 舊 API (仍可使用)

```python
# ⚠️ Deprecated - 會顯示 DeprecationWarning
from spellvid.utils import compute_layout_bboxes, render_video_stub
from spellvid import cli

item = {"letters": "I i", "word_en": "Ice", "word_zh": "冰"}
layout = compute_layout_bboxes(item)  # 傳入 dict
cli.make(args)  # 舊 CLI 函數
```

### 新 API (推薦)

```python
# ✅ 新架構 - 型別安全,IDE 友善
from spellvid.shared.types import VideoConfig
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.cli.commands import make_command

config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
layout = compute_layout_bboxes(config)  # 傳入 VideoConfig
make_command(args)  # 新 CLI 函數
```

**遷移時程**:
- **v2.x** (目前): 完全向後相容,舊 API 保留
- **v3.0**: 移除 `utils.py` 實作,僅保留 re-export
- **v4.0**: 完全移除舊 API

**詳細遷移指南**: 請參閱 [doc/ARCHITECTURE.md#遷移指南](doc/ARCHITECTURE.md#遷移指南)

---

Notes
-----
- The project prefers running tests and CLI inside the repository `.venv`.
- If `ffmpeg` isn't available on your PATH, the repo contains `FFmpeg/ffmpeg.exe` which will be used by default.
- See [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) for detailed architecture documentation.

If you want CI integration or a GitHub Actions job that runs tests automatically, tell me and I can add an example workflow.
