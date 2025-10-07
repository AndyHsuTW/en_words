# SpellVid 專案憲法 (Project Constitution)

**文件版本**：v1.0  
**最後更新**：2025-01-08  
**適用範圍**：SpellVid (en_words) 專案全體貢獻者

---

## 目的 (Purpose)

本文件定義 SpellVid 專案的核心開發標準、測試策略、命名原則、版本控制規範、Pull Request 檢查與安全標準，確保程式碼品質一致性與專案可維護性。

---

## 1. 程式風格 (Coding Style)

### 1.1 Python 風格指南

SpellVid 專案遵循以下 Python 編碼標準：

- **PEP 8 基礎**：遵循 [PEP 8](https://peps.python.org/pep-0008/) 作為基礎風格指南
- **縮排**：使用 4 個空格，禁止使用 Tab
- **行長度**：最大 88 字元（與 Black formatter 一致），註解與文件字串可適度放寬至 100 字元
- **引號**：優先使用雙引號 `"` 表示字串，除非字串內包含雙引號時使用單引號
- **Import 順序**：
  1. 標準庫 (如 `os`, `json`, `subprocess`)
  2. 第三方套件 (如 `numpy`, `PIL`, `moviepy`)
  3. 本地模組 (如 `from . import utils`)
  4. 各分組之間空一行

**範例**：
```python
import json
import os
import subprocess
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import utils
```

### 1.2 命名慣例

#### 變數與函式
- **公開函式/變數**：使用 `snake_case`
  - 範例：`compute_layout_bboxes()`, `render_video_stub()`, `word_en`
- **內部函式/變數（模組私有）**：使用底線前綴 `_snake_case`
  - 範例：`_make_text_imageclip()`, `_find_and_set_ffmpeg()`, `_mpy`
  - **重要**：測試檔案可能會匯入使用內部 helper（如 `_make_text_imageclip`），更改這些函式時務必同步更新測試

#### 常數
- **全域常數**：使用 `UPPER_SNAKE_CASE`
  - 範例：`LETTER_SAFE_X`, `PROGRESS_BAR_HEIGHT`, `MAIN_BG_COLOR`

#### 類別
- **類別名稱**：使用 `PascalCase`
  - 範例：`VideoRenderer`, `ImageClip` (外部函式庫)

#### 檔案與模組
- **模組名稱**：使用 `snake_case.py`
  - 範例：`utils.py`, `cli.py`, `test_layout.py`

### 1.3 型別註解 (Type Hints)

- **函式簽名**：所有公開函式應包含參數與回傳值的型別註解
- **複雜型別**：使用 `typing` 模組提供的泛型（`Dict`, `List`, `Optional`, `Tuple`, `Any`）
- **範例**：
```python
def compute_layout_bboxes(item: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """計算版面各區域的邊界框座標。"""
    pass

def _coerce_non_negative_float(value: Any, default: float = 0.0) -> float:
    """將輸入值轉為非負浮點數。"""
    pass
```

### 1.4 註解與文件字串 (Comments & Docstrings)

- **文件字串**：所有公開函式、類別與模組應包含 docstring
  - 格式：使用簡潔的單行或多行說明，中英文皆可，但保持一致性
  - 測試模組的 docstring 應明確說明測試目的與前置條件
  
**範例**：
```python
def compute_layout_bboxes(item: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """計算 1920x1080 版面中各區域（字母、中文、計時器、圖像、揭示區）的邊界框。
    
    Args:
        item: 包含 letters, word_zh, countdown_sec 等欄位的字典
    
    Returns:
        包含 'letters', 'chinese', 'timer', 'image', 'reveal' 等鍵的字典，
        每個值為 {'x': int, 'y': int, 'w': int, 'h': int}
    """
    pass
```

- **行內註解**：僅在邏輯複雜或不明顯之處添加註解，避免冗餘說明
  - **原則**：程式碼應自我解釋，註解補充「為什麼」而非「是什麼」

**範例**：
```python
# 調整字母間距為負值以減少視覺間隙 (experimental)
LETTER_BASE_GAP = -40
```

### 1.5 錯誤處理

- **異常類型**：捕捉具體的異常類型，避免使用空的 `except:` 或 `except Exception:` 而不處理
- **錯誤傳播**：若無法在當前層級處理，應向上傳播或記錄日誌
- **資源清理**：使用 `with` 語句管理檔案、臨時目錄等資源

**範例**：
```python
try:
    fv = float(value)
except (TypeError, ValueError):
    return float(default)
```

### 1.6 程式碼組織

- **模組職責**：
  - `utils.py`：核心邏輯、版面計算、文字渲染、FFmpeg 偵測、schema 定義、資產檢查
  - `cli.py`：CLI 入口點 (`make`, `batch`)、參數解析、使用者介面
  - `tests/`：pytest 測試套件，每個功能領域對應一個 `test_*.py` 檔案

- **函式長度**：單一函式應保持精簡（建議 < 50 行），複雜邏輯應拆分為多個小函式
- **避免重複**：共用邏輯應抽取為 helper 函式

---

## 2. 測試策略 (Testing Strategy)

### 2.1 測試框架與工具

- **測試框架**：pytest
- **測試覆蓋率**：pytest-cov (目標 > 80% 覆蓋率)
- **視覺驗證**：opencv-python, numpy (像素級邊界框檢查)
- **影音檢查**：ffprobe (編碼格式、解析度、幀率驗證)
- **音訊處理**：pydub (波形與靜音檢測)

### 2.2 測試層級

#### 單元測試 (Unit Tests)
- **範圍**：測試單一函式或模組的邏輯，不依賴外部資源（如 FFmpeg、實際檔案）
- **命名**：`test_<feature>.py`，測試函式命名為 `test_<specific_behavior>()`
- **範例**：
  - `test_layout.py`：測試 `compute_layout_bboxes()` 計算是否正確
  - `test_zhuyin.py`：測試注音轉換邏輯
  - `test_countdown.py`：測試倒數計時文字不超出分配區域

#### 整合測試 (Integration Tests)
- **範圍**：測試多個模組協作、資產載入、影片合成管線
- **範例**：
  - `test_integration.py`：測試完整的渲染流程（JSON → 視訊輸出）
  - `test_image_inclusion.py`：測試圖片資產合成至影片
  - `test_music_inclusion.py`：測試音訊混音與正規化

#### 端對端測試 (E2E Tests)
- **範圍**：透過 CLI 介面測試完整工作流程
- **範例**：執行 `spellvid batch --json config.json --dry-run` 並驗證輸出

### 2.3 測試資料與資產

- **測試資產目錄**：`tests/assets/`
  - 包含測試用圖片、音訊、影片
  - 使用最小化資產（如 1x1 像素圖片、極短音訊）以減少儲存空間
- **測試設定檔**：`config.json` 作為範例資料
- **模擬資料**：當實際資產不存在時，測試應使用白底圖或合成音訊

### 2.4 測試慣例

- **Headless 支援**：所有測試應在無圖形界面環境中執行（CI/CD 相容）
- **條件跳過**：當 MoviePy 或其他可選依賴缺失時，使用 `pytest.skip()` 跳過相關測試
  ```python
  if _make_text_imageclip is None:
      pytest.skip("_make_text_imageclip helper not available")
  ```
- **像素級驗證**：版面測試應比較 `compute_layout_bboxes` 計算結果與實際渲染像素邊界
- **FFmpeg 檢查**：輸出影片應使用 `ffprobe` 驗證編碼格式 (H.264, yuv420p, AAC, 30fps)

### 2.5 測試執行

#### 開發環境
```powershell
# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 快速執行所有測試
.\scripts\run_tests.ps1

# 或直接使用 pytest
pytest -q

# 執行特定測試檔案
pytest tests/test_layout.py -v

# 查看測試覆蓋率
pytest --cov=spellvid --cov-report=html
```

#### CI/CD 環境
- 測試應在 Python 3.13+ 環境中執行
- 確保 FFmpeg 可用（透過 `FFMPEG_PATH` 或 `IMAGEIO_FFMPEG_EXE` 環境變數）
- 所有測試必須通過才能合併 PR

### 2.6 測試原則

- **獨立性**：每個測試應獨立執行，不依賴其他測試的狀態
- **確定性**：測試結果應可重現，避免隨機性或時間依賴
- **速度**：優先撰寫快速的單元測試，整合測試應使用最小資產
- **清晰性**：測試失敗訊息應清楚指出問題所在
- **邊界檢查**：測試應涵蓋正常情況、邊界情況與錯誤情況

---

## 3. 命名原則 (Naming Conventions)

### 3.1 專案層級命名

#### 分支命名
- **主分支**：`main` 或 `master`
- **功能分支**：`feature/<feature-name>`
  - 範例：`feature/progress-bar`, `feature/entry-video`
- **修復分支**：`fix/<bug-description>`
  - 範例：`fix/timer-overflow`, `fix/audio-sync`
- **實驗分支**：`experiment/<experiment-name>`
  - 範例：`experiment/gpu-acceleration`

#### Commit 訊息
遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Type 類型**：
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文件更新
- `style`: 程式碼格式調整（不影響功能）
- `refactor`: 重構（不新增功能或修復錯誤）
- `test`: 測試相關
- `chore`: 建置工具、依賴更新等

**範例**：
```
feat(layout): add progress bar with tricolor segments

Implement a horizontal progress bar in the bottom-left area with
three color zones (green/yellow/red) at 50%/20%/30% widths.

Closes #42
```

```
fix(timer): prevent timer text from exceeding assigned bbox

Adjust padding and margin calculations in compute_layout_bboxes
and _make_text_imageclip to ensure countdown text fits within
the allocated timer region.

Fixes #38
```

### 3.2 程式碼層級命名

已涵蓋於「1.2 命名慣例」，請參考該章節。

### 3.3 測試命名

- **測試檔案**：`test_<feature>.py`
  - 範例：`test_layout.py`, `test_integration.py`, `test_zhuyin.py`
- **測試函式**：`test_<specific_behavior>()`
  - 描述測試的行為或驗證點，使用動詞 + 受詞
  - 範例：`test_countdown_timer_pixel_not_exceed_assigned_box()`
  - 範例：`test_progress_bar_displays_three_segments()`

### 3.4 資產命名

- **圖片資產**：`<lowercase-word>.png`
  - 範例：`ice.png`, `ball.png`
- **音訊資產**：`<word-name>.mp3`
  - 範例：`ice.mp3`, `Arm, arm.mp3`
- **字母圖片**：`<LETTER>.png` 與 `<letter>_small.png`
  - 範例：`A.png`, `a_small.png`, `Z.png`, `z_small.png`
- **特殊影片**：`entry.mp4` (開頭影片), `ending.mp4` (結尾影片)

---

## 4. 版本控制 (Version Control)

### 4.1 Git 工作流程

SpellVid 採用 **Feature Branch Workflow** 搭配 PR 審查機制：

1. **從 `main` 分支建立功能分支**：
   ```powershell
   git checkout main
   git pull origin main
   git checkout -b feature/new-feature
   ```

2. **在功能分支上開發**：
   - 頻繁提交小的、原子性的 commit
   - 每個 commit 應專注於單一邏輯變更
   - Commit 訊息遵循 Conventional Commits

3. **推送至遠端並建立 PR**：
   ```powershell
   git push origin feature/new-feature
   ```

4. **等待 PR 審查與測試通過**

5. **合併至 `main` 並刪除分支**

### 4.2 Git 最佳實踐

- **小步提交**：每個 commit 應可獨立建置與測試
- **避免合併衝突**：
  - 定期從 `main` rebase 或 merge 到功能分支
  - 在 PR 合併前解決所有衝突
- **敏感資料**：
  - **禁止**將密鑰、密碼、API token 提交至 Git
  - 使用 `.gitignore` 排除機密檔案（如 `.env`, `*.local`）
  - 已提交的敏感資料需立即撤銷並輪換（參考「6. 安全標準」）

### 4.3 .gitignore 規範

專案 `.gitignore` 應包含：
- Python 快取：`__pycache__/`, `*.pyc`, `*.pyo`
- 虛擬環境：`.venv/`, `venv/`, `ENV/`
- 測試快取：`.pytest_cache/`, `.coverage`
- IDE 設定：`.vscode/`, `.idea/`, `*.sublime-*`
- 輸出檔案：`out/`, `*.mp4`（除非範例）
- 本地資產：`assets/`（根據專案需求調整）
- 臨時檔案：`*.tmp`, `*.log`, `tasks-done-for-commit.md`

### 4.4 分支保護規則

#### `main` 分支保護
- **禁止直接推送**：所有變更必須透過 PR
- **必須審查**：至少 1 位審查者批准
- **CI 通過**：所有測試與檢查必須通過
- **分支更新**：PR 必須基於最新的 `main` 分支

---

## 5. Pull Request 檢查 (PR Requirements)

### 5.1 PR 建立前檢查清單

在建立 PR 之前，請確認：

- [ ] 程式碼遵循專案風格指南（PEP 8, 命名慣例）
- [ ] 所有新增功能包含對應的單元測試
- [ ] 所有測試通過（`.\scripts\run_tests.ps1` 或 `pytest`）
- [ ] 更新相關文件（如 `README.md`, `doc/requirement.md`）
- [ ] Commit 訊息遵循 Conventional Commits
- [ ] 無敏感資料（密鑰、密碼）被提交
- [ ] 無不必要的除錯程式碼或註解

### 5.2 PR 內容要求

#### PR 標題
- 遵循 Conventional Commits 格式
- 範例：`feat(cli): add --entry-hold flag for entry video duration`

#### PR 描述
應包含以下章節：

```markdown
## 變更摘要 (Summary)
簡述此 PR 的目的與變更內容。

## 變更類型 (Type of Change)
- [ ] 新功能 (feat)
- [ ] 錯誤修復 (fix)
- [ ] 文件更新 (docs)
- [ ] 重構 (refactor)
- [ ] 測試 (test)
- [ ] 其他 (chore)

## 相關 Issue
Closes #<issue-number>

## 測試說明 (Testing)
描述如何測試此變更，包含執行的命令與預期結果。

## 檢查清單 (Checklist)
- [ ] 程式碼遵循專案風格
- [ ] 包含測試
- [ ] 測試通過
- [ ] 文件已更新
- [ ] 無敏感資料
```

### 5.3 PR 審查標準

審查者應檢查以下項目：

#### 功能正確性
- 變更是否實現預期功能？
- 是否處理邊界情況與錯誤情況？
- 是否與現有功能相容？

#### 程式碼品質
- 是否遵循專案風格指南？
- 變數與函式命名是否清晰？
- 是否有不必要的複雜性？
- 是否有重複程式碼？

#### 測試充分性
- 是否包含單元測試與整合測試？
- 測試覆蓋率是否足夠？
- 測試是否有意義且可維護？

#### 文件完整性
- API 變更是否更新 docstring？
- 使用者介面變更是否更新 README？
- 複雜邏輯是否有註解說明？

#### 安全性
- 是否有潛在的安全漏洞？
- 是否暴露敏感資訊？
- 輸入驗證是否充分？

### 5.4 自動化檢查 (CI/CD)

每個 PR 應自動執行以下檢查（未來可透過 GitHub Actions 實作）：

- **Linting**：`flake8` 或 `pylint` 檢查程式碼風格
- **Type Checking**：`mypy` 檢查型別註解
- **Testing**：`pytest` 執行所有測試
- **Coverage**：測試覆蓋率報告（建議 > 80%）
- **Security Scan**：`bandit` 或 `safety` 檢查已知漏洞

### 5.5 PR 合併流程

1. **建立 PR**：從功能分支向 `main` 建立 PR
2. **自動檢查**：等待 CI/CD 執行完成
3. **人工審查**：至少 1 位審查者批准
4. **解決反饋**：根據審查意見修改程式碼
5. **更新分支**：確保 PR 基於最新的 `main` 分支
6. **合併**：使用 Squash and Merge 或 Rebase and Merge
7. **清理**：刪除已合併的功能分支

---

## 6. 安全標準 (Security Standards)

### 6.1 敏感資料管理

#### 禁止事項
- **禁止**將以下內容提交至 Git：
  - API 密鑰、Access Token
  - 密碼、資料庫連線字串
  - 私鑰、證書
  - 個人識別資訊 (PII)

#### 最佳實踐
- **環境變數**：敏感設定透過環境變數傳遞
  - 範例：`FFMPEG_PATH`, `IMAGEIO_FFMPEG_EXE`
- **設定檔案**：使用 `.env` 檔案並加入 `.gitignore`
- **輪換機制**：定期更換密鑰與密碼

#### 洩漏應對
若敏感資料已被提交：
1. **立即撤銷**：輪換所有相關密鑰與密碼
2. **清理歷史**：使用 `git filter-branch` 或 BFG Repo-Cleaner 移除
3. **通知團隊**：告知所有協作者
4. **檢討流程**：分析原因並改善流程

### 6.2 依賴安全

#### 依賴管理
- **鎖定版本**：`requirements-dev.txt` 應包含精確版本號（未來考慮使用 `pip-tools`）
- **定期更新**：每季度檢查依賴更新與安全漏洞
- **漏洞掃描**：使用 `safety` 工具檢查已知漏洞
  ```powershell
  pip install safety
  safety check
  ```

#### 信任來源
- **優先使用官方套件**：從 PyPI 安裝套件
- **檢查完整性**：驗證套件的 checksum 或簽章（pip 自動處理）

### 6.3 輸入驗證

#### JSON Schema 驗證
- 所有外部輸入（如 `config.json`）應透過 `jsonschema` 驗證
- Schema 定義位於 `spellvid/utils.py` 中的 `SCHEMA`
- 範例：
  ```python
  errors = utils.validate_schema(data)
  if errors:
      for e in errors:
          print("SCHEMA-ERROR:", e)
      return 2
  ```

#### 檔案路徑驗證
- **路徑正規化**：使用 `os.path.abspath()` 與 `os.path.normpath()`
- **路徑遍歷防護**：檢查輸入路徑不包含 `..` 或絕對路徑攻擊
- **檔案存在性**：使用 `check_assets()` 驗證資產存在

#### 命令注入防護
- **參數化執行**：使用 `subprocess` 的列表形式而非字串拼接
  ```python
  # 安全
  subprocess.run(["ffmpeg", "-i", input_path, output_path])
  
  # 不安全（避免使用）
  subprocess.run(f"ffmpeg -i {input_path} {output_path}", shell=True)
  ```

### 6.4 程式碼安全

#### 避免常見漏洞
- **SQL Injection**：不適用（專案不使用資料庫）
- **XSS**：不適用（無 Web 介面）
- **Command Injection**：使用參數化 subprocess 呼叫
- **Path Traversal**：驗證與正規化所有檔案路徑

#### 錯誤處理
- **避免洩漏敏感資訊**：錯誤訊息不應包含系統路徑、版本號等細節
- **日誌記錄**：不記錄敏感資料（密碼、Token）

### 6.5 執行環境安全

#### 虛擬環境隔離
- **必須使用虛擬環境**：避免污染全域 Python 環境
- **依賴隔離**：每個專案獨立管理依賴

#### 權限最小化
- **檔案權限**：輸出檔案使用預設權限，不需要特殊提權
- **執行權限**：CLI 工具不應要求管理員權限

#### FFmpeg 安全
- **可信來源**：使用官方 FFmpeg 二進位檔案
- **路徑驗證**：`_find_and_set_ffmpeg()` 優先使用環境變數指定的路徑
- **避免 shell 注入**：所有 FFmpeg 呼叫使用參數化列表

### 6.6 安全審查流程

#### PR 安全檢查
每個 PR 應由審查者檢查：
- 是否引入新的依賴？（評估必要性與安全性）
- 是否接受外部輸入？（確保驗證充分）
- 是否執行系統命令？（確保參數化）
- 是否讀寫檔案？（確保路徑驗證）

#### 定期安全審計
- **每季度執行**：
  - 檢查依賴漏洞 (`safety check`)
  - 審查 `.gitignore` 與敏感檔案
  - 檢查存取控制與權限設定

---

## 7. 開發工作流程 (Development Workflow)

### 7.1 環境設定

#### 初次設定
```powershell
# 1. Clone 專案
git clone <repository-url>
cd en_words

# 2. 建立虛擬環境
python -m venv .venv

# 3. 啟動虛擬環境 (PowerShell)
.\.venv\Scripts\Activate.ps1

# 4. 安裝開發依賴
pip install -r requirements-dev.txt

# 5. 執行測試確認環境正常
.\scripts\run_tests.ps1
```

#### 每日開發
```powershell
# 1. 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 2. 拉取最新變更
git pull origin main

# 3. 建立功能分支
git checkout -b feature/my-feature

# 4. 開發與測試（迭代）
# - 撰寫程式碼
# - 執行測試：pytest tests/test_my_feature.py -v
# - 修正問題

# 5. 執行完整測試套件
.\scripts\run_tests.ps1

# 6. 提交變更
git add <files>
git commit -m "feat(scope): description"

# 7. 推送並建立 PR
git push origin feature/my-feature
```

### 7.2 常用命令

#### 測試
```powershell
# 執行所有測試
pytest

# 執行特定檔案
pytest tests/test_layout.py

# 顯示詳細輸出
pytest -v

# 執行特定測試
pytest tests/test_layout.py::test_countdown_timer_pixel_not_exceed_assigned_box

# 測試覆蓋率
pytest --cov=spellvid --cov-report=html
```

#### CLI 使用
```powershell
# 單一影片製作（乾跑）
python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 \
  --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 --dry-run

# 批次製作
python -m spellvid.cli batch --json config.json --outdir out --dry-run
```

#### 除錯
```powershell
# 使用 Python debugger
python -m pdb -m spellvid.cli make --letters "A" --word-en Arm ...

# 詳細日誌（未來可實作）
python -m spellvid.cli batch --json config.json --verbose
```

---

## 8. 文件管理 (Documentation)

### 8.1 文件結構

```
en_words/
├── README.md                  # 快速入門與專案概述
├── CONSTITUTION.md            # 專案憲法（本文件）
├── doc/
│   ├── requirement.md         # 需求規格
│   ├── TDD.md                 # 測試計畫
│   └── *.csv                  # 資料檔案
├── .github/
│   └── copilot-instructions.md  # AI 協作指引
└── spellvid/
    ├── utils.py               # 包含 docstring 的核心模組
    └── cli.py                 # 包含 docstring 的 CLI 模組
```

### 8.2 文件更新原則

- **同步更新**：程式碼變更時必須同步更新相關文件
- **範例優先**：文件應包含實用範例與常見用法
- **繁體中文為主**：核心文件使用繁體中文，程式碼註解與 docstring 中英文皆可
- **版本標記**：重大文件變更應更新版本號與更新日期

### 8.3 文件類型

#### README.md
- 專案簡介與目的
- 快速入門指南
- 基本使用範例
- 環境需求

#### CONSTITUTION.md (本文件)
- 程式風格指南
- 測試策略
- 命名原則
- 版本控制規範
- PR 檢查標準
- 安全標準

#### doc/requirement.md
- 功能需求 (FR)
- 非功能需求 (NFR)
- 使用情境
- 驗收標準

#### doc/TDD.md
- 測試計畫
- 測試案例矩陣
- 測試資料說明

#### .github/copilot-instructions.md
- AI 協作指引
- 專案架構說明
- 開發慣例
- 常見工作流程

---

## 9. 持續改進 (Continuous Improvement)

### 9.1 定期審查

本憲法文件應定期審查與更新：

- **季度審查**：每 3 個月檢視一次，評估是否需要調整
- **重大變更**：當專案架構或工作流程有重大變更時立即更新
- **團隊共識**：所有變更應經團隊討論與共識

### 9.2 反饋機制

- **提出建議**：透過 GitHub Issue 提出改進建議
- **討論與投票**：團隊成員討論並達成共識
- **文件更新**：由提案者或維護者更新文件

### 9.3 指標追蹤

定期追蹤以下指標以評估專案健康度：

- **測試覆蓋率**：目標 > 80%
- **CI 成功率**：目標 > 95%
- **PR 合併時間**：目標 < 48 小時
- **已知漏洞數**：目標 = 0
- **程式碼重複率**：目標 < 5%

---

## 10. 附錄 (Appendix)

### 10.1 參考資源

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

### 10.2 工具清單

#### 開發工具
- **Python**：3.13+
- **pytest**：測試框架
- **pytest-cov**：測試覆蓋率
- **flake8** (建議)：程式碼風格檢查
- **black** (建議)：自動格式化
- **mypy** (建議)：型別檢查

#### 安全工具
- **safety**：依賴漏洞掃描
- **bandit** (建議)：安全問題檢測

#### 版本控制
- **Git**：版本控制系統
- **GitHub**：程式碼託管與協作平台

### 10.3 常見問題 (FAQ)

#### Q1: 為什麼測試可以匯入內部函式（如 `_make_text_imageclip`）？
A: 專案允許測試檔案匯入內部 helper 以便進行像素級驗證。這是為了確保版面計算與實際渲染一致。變更這些函式時務必同步更新測試。

#### Q2: FFmpeg 路徑如何設定？
A: `_find_and_set_ffmpeg()` 會按以下順序尋找 FFmpeg：
1. 環境變數 `FFMPEG_PATH` 或 `IMAGEIO_FFMPEG_EXE`
2. 專案內 `FFmpeg/ffmpeg.exe`
3. imageio-ffmpeg 套件提供的 FFmpeg

#### Q3: 為什麼要使用虛擬環境？
A: 虛擬環境隔離專案依賴，避免版本衝突並確保環境一致性。測試套件與 CLI 工具都期望在專案 venv 中執行。

#### Q4: Commit 要多小？
A: 每個 commit 應專注於單一邏輯變更，能夠獨立建置與測試。避免混合多個不相關的變更。

#### Q5: PR 被拒絕怎麼辦？
A: 根據審查者的反饋修改程式碼，推送新的 commit 到同一分支即可更新 PR。解決所有反饋後，審查者會重新批准。

### 10.4 變更歷史

| 版本   | 日期       | 變更內容            | 作者   |
|------|----------|-----------------|------|
| v1.0 | 2025-01-08 | 初版建立，定義完整專案憲法 | GitHub Copilot |

---

## 11. 憲法宣言 (Declaration)

本憲法由 SpellVid 專案團隊共同制定，旨在建立清晰、一致且可維護的開發標準。所有貢獻者應遵循本憲法的規範，共同維護專案的程式碼品質與安全性。

**本憲法並非一成不變**，我們鼓勵團隊成員提出改進建議，透過討論與共識持續優化開發流程與標準。

讓我們一起打造高品質、安全且易於維護的 SpellVid 專案！

---

**文件結束 (End of Document)**
