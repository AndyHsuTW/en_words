# Quick Start: Phase 2 重構 - 移除舊程式碼

> 快速參考指南,幫助開發者理解與執行第二階段重構任務

## 🎯 目標
移除 `spellvid/utils.py` 中的 deprecated 向後相容層,同時確保核心影片產出工作流程正常運作。

## 📋 前置條件
- 已完成 002-refactor-architecture 的模組化重構
- Python 虛擬環境已設置: `.venv`
- 開發依賴已安裝: `pip install -r requirements-dev.txt`
- FFmpeg 已配置在 `FFmpeg/ffmpeg.exe`

## 🚀 核心驗證命令

### 1. 執行範例影片產出腳本
```powershell
.\scripts\render_example.ps1
```
**預期結果**: 在 `out/` 目錄產出 MP4 檔案且無錯誤

### 2. 執行完整測試套件
```powershell
.\scripts\run_tests.ps1
```
**預期結果**: 所有測試通過 (0 failures, 0 errors)

### 3. 檢查 import 依賴
```powershell
# 搜尋專案中所有直接 import utils.py 的位置
Get-ChildItem -Recurse -Filter "*.py" | Select-String "from spellvid.utils import" | Select-Object -Unique Path
```

### 4. 執行單一測試驗證
```powershell
pytest tests/test_layout.py -v
```

## 📁 關鍵檔案位置

### 需要檢查的檔案
- `spellvid/utils.py` — 待移除/縮減的 deprecated 模組
- `scripts/render_example.py` — 影片產出腳本入口
- `scripts/render_example.ps1` — PowerShell 包裝腳本
- `tests/test_*.py` — 可能依賴 utils.py 內部函數的測試

### 新模組架構
- `spellvid/shared/` — 型別、常數、驗證
- `spellvid/domain/` — 佈局、注音、效果、計時
- `spellvid/application/` — 影片服務、批次處理
- `spellvid/infrastructure/` — MoviePy、Pillow、FFmpeg 適配器
- `spellvid/cli/` — CLI 命令

## 🔍 常見問題排查

### Q1: render_example.ps1 執行失敗
```powershell
# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 手動執行 Python 腳本以查看詳細錯誤
python scripts/render_example.py --json config.json --out-dir out --use-moviepy
```

### Q2: 測試失敗提示 ImportError
檢查測試檔案是否使用舊的 import 路徑:
```python
# 舊(需更新):
from spellvid.utils import _make_text_imageclip

# 新:
from spellvid.infrastructure.rendering import make_text_imageclip
```

### Q3: 如何確認 utils.py 可以安全移除?
```powershell
# 1. 搜尋所有 import utils 的位置
rg "from spellvid import utils" --type py
rg "from spellvid.utils import" --type py

# 2. 檢查 __pycache__ 快取
Remove-Item -Recurse -Force **/__pycache__

# 3. 重新執行測試
.\scripts\run_tests.ps1
```

## ✅ 驗收標準
- [ ] `.\scripts\render_example.ps1` 成功執行
- [ ] `.\scripts\run_tests.ps1` 全部通過
- [ ] 無 DeprecationWarning 或 ImportWarning
- [ ] `out/` 目錄產出有效的 MP4 檔案
- [ ] ffprobe 驗證影片格式正確

## 📚 相關文件
- [Spec](./spec.md) — 功能需求與驗收場景
- [Plan](./plan.md) — 實作計畫與技術脈絡
- [AGENTS.md](../../AGENTS.md) — 專案架構指引
- [copilot-instructions.md](../../.github/copilot-instructions.md) — Copilot 整合說明

## 🛠️ 開發工作流程
1. 切換到 feature 分支: `git checkout 003-phase2-remove-old-code`
2. 啟動虛擬環境: `.\.venv\Scripts\Activate.ps1`
3. 執行測試以建立基線: `.\scripts\run_tests.ps1`
4. 進行程式碼變更(移除 deprecated code)
5. 執行驗證命令(測試 + render_example.ps1)
6. 提交變更並建立 PR

---

**最後更新**: 2025-10-18  
**狀態**: Draft - 等待 research.md 與 tasks.md 完成
