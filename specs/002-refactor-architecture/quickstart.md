# Quickstart: 專案架構重構 - 驗證指南

**Feature**: 002-refactor-architecture  
**Date**: 2025-10-14  
**Purpose**: 提供快速驗證重構成果的場景與命令,確保架構目標達成

---

## 🎯 驗證目標

本指南提供 **4 個驗證場景**,對應 spec.md 中的使用者故事:

1. **獨立測試領域邏輯** - 無需 MoviePy,純邏輯測試
2. **驗證介面契約** - 確保適配器符合 Protocol
3. **驗證向後相容性** - 現有測試持續通過
4. **端到端測試** - CLI 功能不受影響

每個場景包含:
- ✅ **成功標準**: 應該看到的結果
- ❌ **失敗訊號**: 需要修復的問題
- 🔧 **修復提示**: 常見問題的解決方案

---

## 前置準備

### 1. 安裝依賴

```bash
# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 安裝開發依賴
pip install -r requirements-dev.txt

# 確認安裝成功
python -c "import pytest; print('pytest OK')"
python -c "from spellvid.shared.types import VideoConfig; print('Types OK')"
```

### 2. 確認專案結構

```bash
# 確認新模組目錄存在
Test-Path spellvid\domain
Test-Path spellvid\application
Test-Path spellvid\infrastructure
Test-Path spellvid\shared

# 應全部回傳 True
```

---

## 場景 1: 獨立測試領域邏輯 🔬

**目標**: 驗證領域層(domain/)可獨立測試,不依賴 MoviePy 或 FFmpeg

### 執行命令

```bash
# 只執行領域層單元測試
pytest tests/unit/domain/ -v
```

### ✅ 成功標準

```
tests/unit/domain/test_layout.py::test_compute_layout_basic PASSED
tests/unit/domain/test_layout.py::test_compute_layout_no_overlap PASSED
tests/unit/domain/test_layout.py::test_compute_layout_zhuyin PASSED
tests/unit/domain/test_typography.py::test_zhuyin_for_valid_chars PASSED
tests/unit/domain/test_typography.py::test_split_zhuyin_symbols PASSED

======================== 5 passed in 0.12s ========================
```

**驗證點**:
- [x] 測試執行時間 < 1 秒(無 I/O 操作)
- [x] 不啟動 MoviePy(無 `import moviepy` 訊息)
- [x] 測試失敗時錯誤訊息清晰(指向業務邏輯問題)

### ❌ 失敗訊號

```
ImportError: cannot import name 'moviepy' from 'spellvid.domain.layout'
```

**問題**: 領域層仍依賴基礎設施層

🔧 **修復**: 檢查 `domain/layout.py`,移除 MoviePy 匯入,改用純 Python 計算

---

```
AssertionError: assert False == True  # letters.overlaps(word_zh)
```

**問題**: 佈局計算邏輯錯誤,字母與中文重疊

🔧 **修復**: 檢查 `compute_layout_bboxes` 中的座標計算,確保安全邊界

---

## 場景 2: 驗證介面契約 📜

**目標**: 驗證基礎設施適配器實作了介面 Protocol

### 執行命令

```bash
# 只執行契約測試
pytest tests/contract/ -v
```

### ✅ 成功標準

```
tests/contract/test_video_composer_contract.py::test_moviepy_adapter_implements_interface PASSED
tests/contract/test_video_composer_contract.py::test_create_color_clip_contract PASSED
tests/contract/test_text_renderer_contract.py::test_pillow_adapter_implements_interface PASSED
tests/contract/test_media_processor_contract.py::test_ffmpeg_wrapper_implements_interface PASSED

======================== 4 passed in 0.31s ========================
```

**驗證點**:
- [x] 所有 `isinstance(adapter, IProtocol)` 檢查通過
- [x] 介面方法回傳值型別正確
- [x] 無 `AttributeError: 'Adapter' object has no attribute 'method_name'`

### ❌ 失敗訊號

```
AssertionError: assert False  # isinstance(MoviePyAdapter(), IVideoComposer)
```

**問題**: MoviePyAdapter 缺少介面方法

🔧 **修復**:
1. 檢查 `IVideoComposer` 定義了哪些方法
2. 在 `MoviePyAdapter` 中實作缺少的方法
3. 確認方法簽名完全一致(參數名稱、型別提示)

**範例修復**:
```python
# infrastructure/video/moviepy_adapter.py
class MoviePyAdapter:
    def create_color_clip(self, size, color, duration):  # ❌ 缺少型別提示
        ...

# 修正為:
    def create_color_clip(
        self, 
        size: Tuple[int, int],  # ✅ 加上型別
        color: Tuple[int, int, int], 
        duration: float
    ) -> Any:
        ...
```

---

```
TypeError: create_image_clip() missing 1 required positional argument: 'position'
```

**問題**: 介面更新但實作未同步

🔧 **修復**: 檢查 `interface.py` 的最新簽名,更新 `adapter.py`

---

## 場景 3: 驗證向後相容性 🔄

**目標**: 確保現有 25 個測試持續通過,API 不破壞

### 執行命令

```bash
# 執行所有現有整合測試
pytest tests/test_integration.py tests/test_layout.py tests/test_reveal_*.py -v
```

### ✅ 成功標準

```
tests/test_integration.py::test_render_video_dry_run PASSED
tests/test_layout.py::test_layout_pixel_bounds PASSED
tests/test_reveal_underline.py::test_underline_positions PASSED
tests/test_reveal_stable_positions.py::test_positions_stable PASSED

======================== 25 passed in 4.21s ========================
```

**驗證點**:
- [x] 所有測試通過(可能有 DeprecationWarning,但不失敗)
- [x] 測試執行時間與重構前相近(±10%)
- [x] 可以看到 DeprecationWarning 訊息(表示舊 API 保留)

### ❌ 失敗訊號

```
ImportError: cannot import name '_make_text_imageclip' from 'spellvid.utils'
```

**問題**: 舊 API 未正確 re-export

🔧 **修復**: 在 `utils.py` 中加入:

```python
# spellvid/utils.py
import warnings
from .infrastructure.rendering.pillow_adapter import make_text_imageclip as _make_text_imageclip

# 使用時會顯示警告,但功能正常
warnings.warn(
    "Importing _make_text_imageclip from utils is deprecated.",
    DeprecationWarning,
    stacklevel=2
)
```

---

```
AssertionError: assert result["letters"]["x"] == 64
KeyError: 'letters'
```

**問題**: `compute_layout_bboxes` 回傳型別改變

🔧 **修復**: 在 `utils.py` 的包裝函數中加入 `to_dict()`:

```python
def compute_layout_bboxes(item: Dict[str, Any], ...) -> Dict[str, Dict[str, int]]:
    config = VideoConfig.from_dict(item)
    result = _new_compute_layout_bboxes(config, ...)
    return result.to_dict()  # ✅ 轉回舊格式
```

---

## 場景 4: 端到端測試 🚀

**目標**: 驗證 CLI 功能完全不受影響

### 4.1 測試單支視頻生成

```bash
# 使用 CLI make 命令
python -m spellvid.cli make \
  --letters "I i" \
  --word-en Ice \
  --word-zh "ㄅㄧㄥ 冰" \
  --image assets/ice.png \
  --music assets/ice.mp3 \
  --out out/Ice.mp4 \
  --dry-run
```

### ✅ 成功標準

```
✓ 配置解析成功
✓ 資源檢查完成
  - 圖片: assets/ice.png [存在]
  - 音樂: assets/ice.mp3 [存在]
  - 字母: assets/AZ/I.png, assets/AZ/i.png [存在]
✓ 佈局計算完成
  - Letters: (64, 48, 750, 984)
  - Word ZH: (1084, 48, 772, 984)
✓ Dry-run 完成 (0.08s)

Exit code: 0
```

**驗證點**:
- [x] Exit code 為 0
- [x] 輸出包含佈局資訊
- [x] 執行時間 < 200ms (dry-run)

### ❌ 失敗訊號

```
AttributeError: module 'spellvid.cli' has no attribute 'make'
```

**問題**: CLI 入口未正確設定

🔧 **修復**: 檢查 `cli/__init__.py` 是否匯出 `make`, `batch`:

```python
# spellvid/cli/__init__.py
from .commands import make_command, batch_command

__all__ = ["make_command", "batch_command"]
```

---

### 4.2 測試批次處理

```bash
# 使用 CLI batch 命令
python -m spellvid.cli batch \
  --json config.json \
  --outdir out/ \
  --dry-run
```

### ✅ 成功標準

```
✓ 載入配置: config.json (3 items)
✓ 批次處理開始
  [1/3] Ice ... OK (0.05s)
  [2/3] Snow ... OK (0.06s)
  [3/3] Mountain ... OK (0.05s)
✓ 批次完成: 3 成功, 0 失敗 (0.18s)

Exit code: 0
```

**驗證點**:
- [x] 所有項目處理成功
- [x] 平均每項處理時間 < 100ms (dry-run)

---

### 4.3 測試實際渲染

```bash
# 不加 --dry-run,實際產生視頻
python -m spellvid.cli make \
  --letters "A a" \
  --word-en Apple \
  --word-zh "蘋果" \
  --out out/Apple.mp4
```

### ✅ 成功標準

```
✓ 配置解析成功
✓ 資源檢查完成
✓ 佈局計算完成
✓ 視頻渲染中...
  [████████████████████] 100% (3.2s)
✓ 視頻產出: out/Apple.mp4
  - 檔案大小: 1.2 MB
  - 時長: 5.0 sec
  - 解析度: 1920x1080

Exit code: 0
```

**驗證點**:
- [x] out/Apple.mp4 存在
- [x] 檔案大小 > 0
- [x] 可用播放器播放
- [x] 內容正確(字母在左,中文在右,倒數計時器顯示)

### ❌ 失敗訊號

```
RuntimeError: MoviePy not available
```

**問題**: MoviePy 未正確初始化

🔧 **修復**:
1. 確認 MoviePy 已安裝: `pip show moviepy`
2. 檢查 `shared/constants.py` 中 `HAS_MOVIEPY` 設定邏輯
3. 確認 `infrastructure/video/moviepy_adapter.py` 匯入成功

---

## 場景 5: 效能驗證 ⚡ (可選)

**目標**: 確保重構未降低效能

### 執行命令

```bash
# 執行效能基準測試
pytest tests/performance/ --benchmark-only
```

### ✅ 成功標準

```
--------------------- benchmark: compute_layout_bboxes ---------------------
Name                        Min      Max      Mean    StdDev    Median
---------------------------------------------------------------------------
test_layout_performance   0.015s   0.018s   0.016s   0.001s    0.016s

============================ 1 passed in 0.12s ============================
```

**驗證點**:
- [x] `compute_layout_bboxes` 平均執行時間 < 50ms
- [x] 批次處理 100 支視頻 ≤ 110% 基準時間

---

## 完整驗證流程 (CI/CD)

```bash
# 1. 執行所有測試
pytest tests/ -v --cov=spellvid --cov-report=term-missing

# 2. 檢查測試覆蓋率
# 目標: 總覆蓋率 >= 85%

# 3. 執行靜態型別檢查
mypy spellvid/ --strict

# 4. 執行程式碼風格檢查
flake8 spellvid/ --max-line-length=100

# 5. 執行端到端測試
python -m spellvid.cli batch --json config.json --outdir out/
```

### ✅ CI 通過標準

```
✓ Pytest: 所有測試通過
✓ Coverage: 85%+ (shared: 95%, domain: 90%, app: 85%, infra: 75%)
✓ Mypy: No errors
✓ Flake8: No errors
✓ E2E: 視頻產出正確
```

---

## 故障排除指南 🛠️

### 問題 1: 測試全部跳過

**症狀**:
```
tests/test_ending_video.py::test_moviepy_appends_ending_clip SKIPPED (缺少 MoviePy)
```

**原因**: MoviePy 未安裝或 `_HAS_MOVIEPY` 未正確設定

**解決**:
```bash
pip install moviepy
python -c "from spellvid.shared.constants import HAS_MOVIEPY; print(HAS_MOVIEPY)"
# 應輸出 True
```

---

### 問題 2: 匯入錯誤

**症狀**:
```
ModuleNotFoundError: No module named 'spellvid.domain'
```

**原因**: `__init__.py` 缺失

**解決**:
```bash
# 確認所有目錄有 __init__.py
New-Item -ItemType File spellvid\domain\__init__.py
New-Item -ItemType File spellvid\application\__init__.py
New-Item -ItemType File spellvid\infrastructure\__init__.py
```

---

### 問題 3: 型別檢查失敗

**症狀**:
```
error: Argument 1 has incompatible type "dict[str, Any]"; expected "VideoConfig"
```

**原因**: 呼叫者仍使用舊版 Dict 而非 VideoConfig

**解決**:
```python
# 舊代碼
compute_layout_bboxes(item_dict)

# 改為
config = VideoConfig.from_dict(item_dict)
compute_layout_bboxes(config)
```

---

## 驗收檢查清單 ✅

在提交 PR 前,確認以下所有項目:

### 功能驗收
- [ ] 場景 1: 領域邏輯獨立測試通過
- [ ] 場景 2: 介面契約測試通過
- [ ] 場景 3: 向後相容測試通過(25/25)
- [ ] 場景 4: CLI 端到端測試通過
- [ ] 場景 5: 效能基準測試通過(可選)

### 代碼品質
- [ ] 測試覆蓋率 ≥ 85%
- [ ] Mypy 型別檢查通過
- [ ] 所有公開函數有 docstring
- [ ] 所有 DeprecationWarning 已標記

### 文檔完整性
- [ ] README.md 更新架構說明
- [ ] 新模組有模組級 docstring
- [ ] AGENTS.md 或 .github/copilot-instructions.md 已更新

---

## 下一步 🎯

完成所有驗證場景後:

1. **提交代碼**: `git add . && git commit -m "feat: 完成架構重構 - 職責分離與降低耦合度"`
2. **推送分支**: `git push origin 002-refactor-architecture`
3. **建立 PR**: 附上此 quickstart.md 的驗證結果截圖
4. **Code Review**: 等待團隊審查
5. **合併到 main**: 完成重構!

---

**狀態**: ✅ Quickstart 文檔完成  
**版本**: 1.0  
**最後更新**: 2025-10-14
