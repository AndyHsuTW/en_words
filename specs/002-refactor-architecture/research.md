# Research: 專案架構重構 - 技術決策與實作策略

**Date**: 2025-10-14  
**Feature**: 002-refactor-architecture  
**Purpose**: 研究架構重構所需的技術選擇與實作策略，為 Phase 1 設計階段提供決策依據

---

## 研究任務概覽

本研究階段針對五個關鍵領域進行調查：

1. **現有代碼結構分析** - 識別函數職責與依賴關係
2. **測試依賴分析** - 確認哪些內部函數被測試直接使用
3. **介面定義策略** - 選擇 Python 介面實作方式
4. **漸進式重構策略** - 確保重構過程安全可控
5. **MoviePy 適配器設計** - 抽象化視頻處理框架

---

## R1: 現有代碼結構分析

### 分析方法

透過 `grep` 和語義搜尋分析 `spellvid/utils.py` (3652 行) 與 `spellvid/cli.py` (278 行)，識別函數職責歸屬。

### 函數分類結果

#### 1. 領域邏輯層 (Domain Logic)

**佈局計算** (`domain/layout.py`)
- `compute_layout_bboxes()` - 計算所有視覺元素的邊界框
- `_layout_zhuyin_column()` - 注音符號垂直排版計算
- `_measure_text_with_pil()` - 文字尺寸測量

**注音處理** (`domain/typography.py`)
- `zhuyin_for()` - 中文轉注音
- `_zhuyin_main_gap()` - 注音符號間距計算
- `_ZHUYIN_MAP` - 注音對照表

**時間軸管理** (`domain/timing.py`)
- 倒數計時邏輯（目前嵌入在 `render_video_moviepy` 中）
- 淡入淡出時機計算

**效果組合** (`domain/effects.py`)
- `_apply_fadeout()` - 淡出效果
- `_apply_fadein()` - 淡入效果
- `concatenate_videos_with_transitions()` - 視頻轉場拼接

#### 2. 應用服務層 (Application Services)

**視頻生成服務** (`application/video_service.py`)
- `render_video_stub()` - 統一渲染入口
- `render_video_moviepy()` - 核心渲染邏輯（需拆分）

**批次處理服務** (`application/batch_service.py`)
- `cli.batch()` - 批次處理邏輯（當前在 CLI 層）

**資源檢查服務** (`application/resource_checker.py`)
- `check_assets()` - 檢查圖片/音樂/字母資源
- `_prepare_entry_context()` - 準備片頭資源
- `_prepare_ending_context()` - 準備片尾資源
- `_prepare_letters_context()` - 準備字母資源

#### 3. 基礎設施層 (Infrastructure)

**視頻合成** (`infrastructure/video/`)
- `_mpy.*` - MoviePy 物件操作
- `_make_progress_bar_mask()` - 進度條遮罩生成
- `_build_progress_bar_segments()` - 進度條分段

**媒體處理** (`infrastructure/media/`)
- `_find_and_set_ffmpeg()` - FFmpeg 偵測與配置
- `_probe_media_duration()` - 媒體時長查詢
- `_create_placeholder_mp4_with_ffmpeg()` - 佔位視頻生成

**文字渲染** (`infrastructure/rendering/`)
- `_make_text_imageclip()` - Pillow 文字渲染
- `_find_system_font()` - 系統字型查找
- `_make_fixed_letter_clip()` - 字母圖片生成

#### 4. 輸入適配層 (Input Adapters)

**CLI** (`cli/`)
- `cli.make()` - 單支視頻命令
- `cli.batch()` - 批次處理命令
- `cli.build_parser()` - 參數解析

#### 5. 共用元件 (Shared)

**資料驗證** (`shared/validation.py`)
- `load_json()` - JSON 載入
- `validate_schema()` - Schema 驗證
- `SCHEMA` - JSON Schema 定義

**型別定義** (`shared/types.py`)
- 目前使用 `Dict[str, Any]`，需定義 `VideoConfig` 等型別

**常數定義** (`shared/constants.py`)
- `LETTER_SAFE_X`, `LETTER_SAFE_Y`, `LETTER_AVAILABLE_WIDTH` 等佈局常數
- `PROGRESS_BAR_*` 進度條相關常數
- `MAIN_BG_COLOR`, `FADE_OUT_DURATION` 等渲染常數
- `_DEFAULT_LETTER_ASSET_DIR`, `_DEFAULT_ENTRY_VIDEO_PATH` 等路徑常數

### 依賴關係圖（簡化）

```
cli.py (CLI 層)
  ↓ 呼叫
utils.render_video_stub() (應用層)
  ↓ 呼叫
utils.render_video_moviepy() (應用層 - 龐大，需拆分)
  ↓ 使用
  ├─ compute_layout_bboxes() (領域層)
  ├─ _make_text_imageclip() (基礎設施層)
  ├─ _find_and_set_ffmpeg() (基礎設施層)
  ├─ _apply_fadeout() (領域層/效果)
  └─ _mpy.* (基礎設施層/MoviePy)
```

### 關鍵發現

1. **`render_video_moviepy()` 過於龐大** (1000+ 行)
   - 混合了佈局計算、資源載入、Clip 生成、效果應用
   - 重構優先級：最高
   
2. **常數散布在多處**
   - 許多 magic numbers 直接寫死在函數中
   - 需集中到 `shared/constants.py`

3. **型別定義缺失**
   - 目前使用 `Dict[str, Any]` 傳遞配置
   - 缺乏型別檢查與 IDE 自動完成

---

## R2: 測試依賴分析

### 分析目標

確認哪些內部函數（`_` 前綴）被測試直接匯入，確保重構後這些函數仍可被測試訪問。

### 測試匯入內部函數清單

| 測試檔案 | 匯入的內部函數 | 用途 |
|---------|---------------|------|
| `test_layout.py` | `_make_text_imageclip` | 渲染文字以驗證像素邊界 |
| `test_layout.py` | `_mpy` (檢查是否存在) | 條件跳過測試 |
| `test_reveal_underline.py` | `_make_text_imageclip` | 檢查 underline 位置 |
| `test_reveal_stable_positions.py` | `_make_text_imageclip` | 驗證字元位置穩定性 |
| `test_ending_video.py` | `_HAS_MOVIEPY` | 條件跳過測試 |
| `test_countdown.py` | `_HAS_MOVIEPY` | 條件跳過測試 |
| `test_video_overlap.py` | `compute_layout_bboxes`, 環境變數控制 | 驗證視頻不重疊 |

### 測試策略影響

#### 保持可測試性的要求
1. `_make_text_imageclip` 必須保持可匯入
   - **決策**: 移至 `infrastructure/rendering/pillow_adapter.py`，但保留公開 API
   
2. `_HAS_MOVIEPY` 需保持可訪問
   - **決策**: 移至 `shared/constants.py` 或 `infrastructure/__init__.py`
   
3. `_mpy` 物件需條件可用
   - **決策**: 封裝在 `infrastructure/video/moviepy_adapter.py`，提供檢查函數

#### 測試重構策略

**選項 A**: 更新所有測試匯入路徑（風險高）
- 優點：強制測試使用公開 API
- 缺點：一次性變更大，容易出錯

**選項 B**: 在舊位置 re-export（推薦）
- 優點：向後相容，測試無需改動
- 缺點：增加一層間接性

**決策**: 採用 **選項 B**，在 `spellvid/utils.py` 保留 re-export，並添加 deprecation warning

```python
# spellvid/utils.py (重構後)
import warnings
from .infrastructure.rendering.pillow_adapter import make_text_imageclip as _make_text_imageclip
from .infrastructure.video.moviepy_adapter import HAS_MOVIEPY as _HAS_MOVIEPY

warnings.warn(
    "Importing internal functions from spellvid.utils is deprecated. "
    "Use public APIs from specific modules.",
    DeprecationWarning,
    stacklevel=2
)
```

---

## R3: 介面定義策略研究

### 比較三種 Python 介面實作方式

#### 選項 A: `typing.Protocol` (結構化子類型)

**範例**:
```python
from typing import Protocol, Any

class IVideoComposer(Protocol):
    def create_clip(self, clip_type: str, **kwargs) -> Any: ...
    def compose_clips(self, clips: list) -> Any: ...
    def render_to_file(self, clip: Any, output_path: str) -> None: ...
```

**優點**:
- ✅ 不需要明確繼承（Duck typing 風格）
- ✅ 支援靜態型別檢查（mypy, Pylance）
- ✅ IDE 自動完成友善
- ✅ Python 3.8+ 標準庫支援

**缺點**:
- ❌ 執行時期無法用 `isinstance()` 檢查（需 `typing.runtime_checkable`）
- ❌ 無法強制子類實作方法

#### 選項 B: `abc.ABC` (名義子類型)

**範例**:
```python
from abc import ABC, abstractmethod
from typing import Any

class IVideoComposer(ABC):
    @abstractmethod
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        pass
    
    @abstractmethod
    def compose_clips(self, clips: list) -> Any:
        pass
    
    @abstractmethod
    def render_to_file(self, clip: Any, output_path: str) -> None:
        pass
```

**優點**:
- ✅ 執行時期可用 `isinstance()` 檢查
- ✅ 強制子類實作 abstractmethod（類似 C# 的 interface/abstract class）
- ✅ Python 2/3 通用
- ✅ 編譯時期檢查：實例化未實作所有抽象方法的類別會拋出 `TypeError`

**缺點**:
- ❌ 需要明確繼承 ABC（打破 Duck Typing 哲學）
- ❌ 增加類別層次複雜度（詳見下方說明）

#### 選項 C: Duck Typing (無明確介面)

**範例**:
```python
# 無介面定義，靠文檔約定
class MoviePyAdapter:
    def create_clip(self, clip_type: str, **kwargs):
        # 實作
        pass
```

**優點**:
- ✅ 最簡單，無額外語法
- ✅ Python 傳統風格

**缺點**:
- ❌ 無靜態型別檢查
- ❌ IDE 無法提供介面契約提示
- ❌ 測試時難以驗證介面完整性

---

### 選項 B 的「類別層次複雜度」問題詳解

在 SpellVid 這個專案中，選項 B (`abc.ABC`) 的「增加類別層次複雜度」具體表現在以下幾個方面：

#### 1. **強制繼承關係污染簡單適配器**

使用 `abc.ABC` 時，所有適配器都必須明確繼承介面類別：

```python
# 使用 abc.ABC 的方式
from abc import ABC, abstractmethod

class IVideoComposer(ABC):
    @abstractmethod
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        pass

# MoviePy 適配器被迫繼承
class MoviePyAdapter(IVideoComposer):  # 明確繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        # 實作
        pass

# 未來的 FFmpeg 適配器也必須繼承
class FFmpegAdapter(IVideoComposer):  # 明確繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        # 實作
        pass
```

**問題**：
- 這些適配器本質上是**包裝器 (Wrapper)**,不應該有繼承關係
- 違反「組合優於繼承」原則
- 如果未來需要同時實作多個介面（如 `IVideoComposer` + `IMediaProcessor`），會陷入多重繼承陷阱

#### 2. **測試替身 (Test Double) 也必須繼承**

在測試中使用 Mock 或 Stub 時，選項 B 增加測試代碼複雜度：

```python
# 使用 abc.ABC 時，Mock 必須繼承
class MockVideoComposer(IVideoComposer):  # 被迫繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return "mock_clip"
    
    def compose_clips(self, clips: list) -> Any:
        return "mock_composed"
    
    def render_to_file(self, clip: Any, output_path: str) -> None:
        pass

# 使用 Protocol 時，不需要繼承（結構化子類型）
class MockVideoComposer:  # 無需繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return "mock_clip"
    
    # 只需要實作測試需要的方法，其他可以省略
```

**問題**：
- `abc.ABC` 強制實作所有抽象方法，即使測試只需要其中一兩個
- 增加測試維護成本

#### 3. **第三方類別無法符合介面**

假設未來想使用第三方視頻處理庫（如 `opencv-python`），但該庫已有自己的類別層次：

```python
# 第三方庫的類別
class ThirdPartyVideoProcessor:
    def process_video(self, input_path: str) -> str:
        # 已有的方法
        pass

# 使用 abc.ABC 時，無法直接使用（因為沒有繼承 IVideoComposer）
# 必須建立包裝類別
class ThirdPartyAdapter(IVideoComposer):  # 新增一層包裝
    def __init__(self):
        self.processor = ThirdPartyVideoProcessor()
    
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        # 轉換邏輯
        pass
```

**問題**：
- 無法讓第三方類別「事後符合」(retroactively) 介面
- 必須額外寫包裝器，增加代碼層次

#### 4. **與 MoviePy 的現有設計衝突**

SpellVid 目前的代碼中，MoviePy 物件已經有複雜的繼承樹：

```python
# MoviePy 內部的類別層次
VideoClip
  ├─ ImageClip
  ├─ TextClip
  ├─ VideoFileClip
  └─ CompositeVideoClip
```

如果使用 `abc.ABC` 定義介面，我們的適配器會形成：

```
IVideoComposer (抽象類別)
  └─ MoviePyAdapter (我們的適配器)
       └─ 內部使用 VideoClip 及其子類別

類別層次：2 層（介面 + 適配器）
實際依賴：MoviePy 已有 5+ 層繼承樹
```

**問題**：
- 適配器的職責是「轉換介面」，不是建立新的繼承體系
- 增加理解負擔：開發者需要同時理解我們的繼承 + MoviePy 的繼承

#### 5. **違反專案現有風格**

分析 `spellvid/utils.py` 現有代碼風格：

```python
# 現有代碼大量使用函數式風格，沒有繼承
def compute_layout_bboxes(item: Dict[str, Any], ...) -> Dict[str, Any]:
    # 純函數

def render_video_moviepy(item: Dict[str, Any], ...) -> Dict[str, Any]:
    # 純函數

# 唯一的類別是內部使用的 _SimpleImageClip（用於降級場景）
class _SimpleImageClip:
    def __init__(self, arr, duration=None):
        # 無繼承，純 Duck Typing
        pass
```

**問題**：
- 引入 `abc.ABC` 會與現有「函數式 + Duck Typing」風格不一致
- 增加學習曲線：新貢獻者需要理解 ABC 語法

---

### 為什麼 `typing.Protocol` 更適合 SpellVid？

相較之下，`typing.Protocol` 的優勢：

#### 1. **結構化子類型 (Structural Subtyping)**
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IVideoComposer(Protocol):
    def create_clip(self, clip_type: str, **kwargs) -> Any: ...

# 任何類別只要有這些方法，就自動符合介面（無需繼承）
class MoviePyAdapter:  # 無需繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return _mpy.ImageClip(...)

# 靜態型別檢查器會認可
def process_video(composer: IVideoComposer):
    clip = composer.create_clip("image", ...)

process_video(MoviePyAdapter())  # ✅ 型別檢查通過
```

#### 2. **測試友善**
```python
# 測試時只需要實作需要的方法
class MockComposer:
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return "mock"
    # 不需要實作其他方法

# @runtime_checkable 可選擇性啟用執行時檢查
assert isinstance(MockComposer(), IVideoComposer)  # ✅ 通過
```

#### 3. **保持函數式風格**
```python
# 介面可以定義函數簽名（不限於類別方法）
class ILayoutCalculator(Protocol):
    def __call__(self, config: VideoConfig) -> LayoutResult: ...

# 可以用函數滿足介面
def compute_layout(config: VideoConfig) -> LayoutResult:
    # 實作
    pass

# 型別檢查通過
calculator: ILayoutCalculator = compute_layout
```

#### 4. **與 Python 生態系統一致**
- Python 3.8+ 官方推薦
- Pylance、mypy、pyright 完整支援
- 不打破 Duck Typing 哲學

### 決策: 選擇 `typing.Protocol`

**理由**:
1. 符合 Python 3.8+ 的現代最佳實踐
2. 支援靜態型別檢查（Pylance, mypy）- **同時保有類似 C# interface 的編譯時檢查能力**
3. 不強制繼承，保持彈性，避免類別層次污染
4. 測試時可用 `@runtime_checkable` 裝飾器啟用執行時檢查
5. 與專案現有的函數式風格一致
6. 不增加額外的類別層次，適配器只需專注於「轉換介面」職責

**補充說明（針對 C# 強型別偏好）**:

雖然 `typing.Protocol` 不像 C# `interface` 會在**編譯時**強制要求實作（Python 沒有編譯階段），但它提供了**同等級別的安全保障**：

1. **靜態型別檢查器檢查** (等同編譯時檢查)：
   - Pylance（VS Code 預設）會在編輯時即時標記缺少的方法
   - mypy/pyright 在 CI 流程中可強制檢查
   - 效果等同 C# 編譯器檢查

2. **執行時檢查** (可選)：
   ```python
   @runtime_checkable
   class IVideoComposer(Protocol):
       def create_clip(self, ...) -> Any: ...
   
   # 執行時可檢查
   if not isinstance(adapter, IVideoComposer):
       raise TypeError("Adapter must implement IVideoComposer")
   ```

3. **測試階段強制檢查** (推薦)：
   ```python
   # 契約測試確保所有適配器實作完整
   def test_moviepy_adapter_implements_interface():
       adapter = MoviePyAdapter()
       assert hasattr(adapter, 'create_clip')
       assert hasattr(adapter, 'compose_clips')
       assert hasattr(adapter, 'render_to_file')
       # 或用 runtime_checkable + isinstance
       assert isinstance(adapter, IVideoComposer)
   ```

**總結**：`typing.Protocol` + 靜態型別檢查 + 契約測試 = C# interface 的強制力，但沒有繼承的複雜度

**實作方式**:
```python
# infrastructure/video/interface.py
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class IVideoComposer(Protocol):
    """視頻合成引擎介面
    
    定義與框架無關的視頻合成操作。實作者需提供 Clip 建立、組合與渲染功能。
    """
    
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        """建立單一 Clip 物件
        
        Args:
            clip_type: Clip 類型 ("image", "text", "color", "video")
            **kwargs: Clip 特定參數
            
        Returns:
            框架特定的 Clip 物件
        """
        ...
    
    def compose_clips(self, clips: list) -> Any:
        """組合多個 Clips 為單一合成 Clip
        
        Args:
            clips: Clip 物件列表
            
        Returns:
            合成後的 Clip 物件
        """
        ...
    
    def render_to_file(self, clip: Any, output_path: str) -> None:
        """將 Clip 渲染為視頻檔案
        
        Args:
            clip: 要渲染的 Clip 物件
            output_path: 輸出檔案路徑
        """
        ...
```

**實際使用範例對比**:

```python
# ===== 選項 A: typing.Protocol (推薦) =====
# infrastructure/video/interface.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class IVideoComposer(Protocol):
    def create_clip(self, clip_type: str, **kwargs) -> Any: ...
    def compose_clips(self, clips: list) -> Any: ...
    def render_to_file(self, clip: Any, output_path: str) -> None: ...

# infrastructure/video/moviepy_adapter.py
class MoviePyAdapter:  # 無需繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        if clip_type == "image":
            return _mpy.ImageClip(kwargs["image_array"])
        elif clip_type == "color":
            return _mpy.ColorClip(size=kwargs["size"], color=kwargs["color"])
    
    def compose_clips(self, clips: list) -> Any:
        return _mpy.CompositeVideoClip(clips)
    
    def render_to_file(self, clip: Any, output_path: str) -> None:
        clip.write_videofile(output_path, fps=30)

# application/video_service.py
def render_video(config: VideoConfig, composer: IVideoComposer) -> None:
    # Pylance 會檢查 composer 是否有需要的方法
    bg = composer.create_clip("color", size=(1920, 1080), color=(255, 255, 255))
    text = composer.create_clip("text", text=config.word_en)
    final = composer.compose_clips([bg, text])
    composer.render_to_file(final, config.output_path)
    # ✅ 如果 MoviePyAdapter 少寫了任何方法，Pylance 會標紅

# tests/contract/test_video_composer.py
def test_moviepy_adapter_satisfies_interface():
    adapter = MoviePyAdapter()
    assert isinstance(adapter, IVideoComposer)  # ✅ 通過（因為有所有方法）
    
    # 如果開發者漏寫 render_to_file 方法
    class IncompleteAdapter:
        def create_clip(self, clip_type: str, **kwargs) -> Any:
            return "clip"
        # 缺少 compose_clips 和 render_to_file
    
    incomplete = IncompleteAdapter()
    assert not isinstance(incomplete, IVideoComposer)  # ❌ 失敗（捕捉到遺漏）


# ===== 選項 B: abc.ABC (不推薦) =====
# infrastructure/video/interface.py
from abc import ABC, abstractmethod

class IVideoComposer(ABC):
    @abstractmethod
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        pass
    
    @abstractmethod
    def compose_clips(self, clips: list) -> Any:
        pass
    
    @abstractmethod
    def render_to_file(self, clip: Any, output_path: str) -> None:
        pass

# infrastructure/video/moviepy_adapter.py
class MoviePyAdapter(IVideoComposer):  # 強制繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        # 實作（同上）
        pass
    
    def compose_clips(self, clips: list) -> Any:
        # 實作（同上）
        pass
    
    def render_to_file(self, clip: Any, output_path: str) -> None:
        # 實作（同上）
        pass

# 問題 1: 測試 Mock 也必須繼承
class MockComposer(IVideoComposer):  # 被迫繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return "mock"
    
    def compose_clips(self, clips: list) -> Any:
        return "mock"
    
    def render_to_file(self, clip: Any, output_path: str) -> None:
        pass  # 即使測試不需要，也必須實作

# 問題 2: 如果開發者粗心漏寫方法
class IncompleteAdapter(IVideoComposer):  # 嘗試繼承
    def create_clip(self, clip_type: str, **kwargs) -> Any:
        return "clip"
    # 缺少 compose_clips 和 render_to_file

# 建立實例時會拋錯（這點與 C# 類似）
try:
    adapter = IncompleteAdapter()  # ❌ TypeError: Can't instantiate abstract class
except TypeError as e:
    print(f"捕捉到錯誤: {e}")

# 問題 3: 類別層次污染
# MoviePyAdapter 現在有繼承關係（雖然只是介面，但仍是一層繼承樹）
print(MoviePyAdapter.__bases__)  # (<class 'IVideoComposer'>,)
print(MoviePyAdapter.__mro__)    # (MoviePyAdapter, IVideoComposer, ABC, object)
# 增加了 2 層：IVideoComposer + ABC
```

**關鍵差異總結**:

| 面向 | `typing.Protocol` (選項 A) | `abc.ABC` (選項 B) |
|------|--------------------------|-------------------|
| **粗心遺漏檢測** | ✅ Pylance 即時標紅 + 測試時 isinstance 檢查 | ✅ 實例化時拋 TypeError |
| **類別層次** | ✅ 無繼承，適配器保持獨立 | ❌ 增加繼承樹（IVideoComposer → ABC → object） |
| **測試複雜度** | ✅ Mock 只需實作測試需要的方法 | ❌ Mock 必須實作所有抽象方法 |
| **與現有代碼風格** | ✅ 符合函數式 + Duck Typing | ❌ 引入繼承，風格不一致 |
| **IDE 支援** | ✅ Pylance/mypy 完整支援 | ✅ 同樣支援 |
| **強制力時機** | 編輯時（Pylance）+ CI（mypy）+ 測試（isinstance） | 執行時（實例化時） |

**結論**: 兩者都能達到「強制要求開發者實作所有方法」的目的，但 `typing.Protocol` 在 SpellVid 專案中更適合，因為它提供同等強制力但不增加類別層次複雜度。

---

## R4: 漸進式重構策略研究

### 三種重構模式比較

#### 模式 A: Strangler Fig Pattern (絞殺者模式)

**概念**: 新模組與舊模組並存，逐步將呼叫者轉向新模組，最後移除舊模組

**步驟**:
1. 建立新模組（如 `domain/layout.py`）
2. 複製函數到新模組並改善
3. 舊模組委派給新模組
4. 更新呼叫者使用新模組
5. 移除舊模組中的函數

**範例**:
```python
# 第1步: 新模組
# domain/layout.py
def compute_layout_bboxes(config: VideoConfig, ...) -> LayoutResult:
    # 改善後的實作
    pass

# 第2步: 舊模組委派
# spellvid/utils.py
from .domain.layout import compute_layout_bboxes as _new_compute_layout_bboxes

def compute_layout_bboxes(item: Dict[str, Any], ...) -> Dict[str, Dict[str, int]]:
    warnings.warn("Use domain.layout.compute_layout_bboxes", DeprecationWarning)
    # 轉換 Dict -> VideoConfig
    config = VideoConfig(**item)
    result = _new_compute_layout_bboxes(config, ...)
    # 轉換 LayoutResult -> Dict
    return result.to_dict()
```

**適用場景**: 函數有許多呼叫者，需要平滑遷移

#### 模式 B: Branch by Abstraction (抽象分支)

**概念**: 先建立抽象層，再遷移實作，最後切換實作

**步驟**:
1. 定義介面（如 `IVideoComposer`）
2. 舊實作包裝為適配器
3. 新實作實作介面
4. 切換使用新實作
5. 移除舊實作

**範例**:
```python
# 第1步: 定義介面
class IVideoComposer(Protocol):
    def create_clip(...): ...

# 第2步: 舊實作包裝
class LegacyMoviePyAdapter:
    def create_clip(...):
        return _mpy.ImageClip(...)  # 呼叫舊代碼

# 第3步: 新實作
class MoviePyAdapter:
    def create_clip(...):
        # 改善後的實作
        pass

# 第4步: 應用層切換
composer: IVideoComposer = MoviePyAdapter()  # 替換 LegacyMoviePyAdapter()
```

**適用場景**: 需要替換大型依賴（如 MoviePy），測試隔離需求高

#### 模式 C: Big Bang Refactoring (大爆炸重構)

**概念**: 一次性重構所有代碼

**優點**:
- ✅ 不需要維護舊新兩套代碼
- ✅ 架構一致性高

**缺點**:
- ❌ 風險極高，容易引入 bug
- ❌ code review 負擔重
- ❌ 無法漸進式驗證

**適用場景**: 小型專案或有完整測試覆蓋

### 決策: 混合使用 Strangler Fig + Branch by Abstraction

**策略**:
1. **對於領域邏輯**（layout, typography）：使用 Strangler Fig
   - 函數相對獨立，呼叫者少
   - 可快速遷移並驗證

2. **對於基礎設施**（video, rendering）：使用 Branch by Abstraction
   - 依賴 MoviePy/Pillow，需要抽象層隔離
   - 未來可能替換框架

**實作順序**（由內而外）:
```
Phase 2a: 共用層 (shared/)
  ↓ 無依賴，最安全
Phase 2b: 基礎設施介面 (infrastructure/*/interface.py)
  ↓ 定義契約
Phase 2c: 領域邏輯 (domain/)
  ↓ 純函數，易測試
Phase 2d: 基礎設施實作 (infrastructure/*/adapter.py)
  ↓ 實作介面
Phase 2e: 應用服務 (application/)
  ↓ 組合邏輯
Phase 2f: CLI 層 (cli/)
  ↓ 入口點
```

---

## R5: MoviePy 適配器設計研究

### 挑戰: MoviePy 的 Clip 概念多樣

MoviePy 提供多種 Clip 類型：
- `ImageClip` - 靜態圖片
- `TextClip` - 文字（需 ImageMagick）
- `VideoFileClip` - 視頻檔案
- `AudioFileClip` - 音訊檔案
- `ColorClip` - 純色背景
- `CompositeVideoClip` - 組合多個 Clip

### 抽象化策略

#### 選項 A: 統一 Clip 介面（深度抽象）

```python
class IClip(Protocol):
    def with_duration(self, duration: float) -> 'IClip': ...
    def with_position(self, pos: tuple) -> 'IClip': ...
    def get_frame(self, t: float) -> np.ndarray: ...

class IVideoComposer(Protocol):
    def create_image_clip(self, image: np.ndarray) -> IClip: ...
    def create_text_clip(self, text: str, ...) -> IClip: ...
    def compose(self, clips: list[IClip]) -> IClip: ...
```

**問題**: 過度抽象，與 MoviePy 耦合太深

#### 選項 B: 場景導向介面（推薦）

```python
class IVideoComposer(Protocol):
    def render_scene(
        self,
        background: ImageSource,
        overlays: List[Overlay],
        duration: float,
        output_path: str
    ) -> None:
        """渲染完整場景到檔案
        
        Args:
            background: 背景來源（顏色/圖片/視頻）
            overlays: 覆蓋元素列表（文字/圖片/進度條）
            duration: 場景時長
            output_path: 輸出路徑
        """
        ...
```

**定義輔助型別**:
```python
@dataclass
class ImageSource:
    type: Literal["color", "file", "array"]
    data: Union[Tuple[int, int, int], str, np.ndarray]

@dataclass
class Overlay:
    type: Literal["text", "image", "progress_bar"]
    position: Tuple[int, int]
    data: Any
    duration: float
    start_time: float = 0.0
```

### 決策: 採用場景導向介面

**理由**:
1. 符合 SpellVid 的使用場景（渲染教學視頻）
2. 不過度抽象 MoviePy 細節
3. 容易替換為其他渲染引擎（FFmpeg-python, OpenCV）

**MoviePy 適配器實作概要**:
```python
# infrastructure/video/moviepy_adapter.py
class MoviePyAdapter:
    def render_scene(
        self,
        background: ImageSource,
        overlays: List[Overlay],
        duration: float,
        output_path: str
    ) -> None:
        # 1. 建立背景 Clip
        if background.type == "color":
            bg_clip = _mpy.ColorClip(size=(1920, 1080), color=background.data)
        elif background.type == "file":
            bg_clip = _mpy.VideoFileClip(background.data)
        # ...
        
        # 2. 建立覆蓋層 Clips
        overlay_clips = []
        for ov in overlays:
            if ov.type == "text":
                clip = self._make_text_clip(ov.data)
            elif ov.type == "image":
                clip = _mpy.ImageClip(ov.data)
            clip = clip.with_position(ov.position).with_start(ov.start_time)
            overlay_clips.append(clip)
        
        # 3. 組合與渲染
        final_clip = _mpy.CompositeVideoClip([bg_clip] + overlay_clips, size=(1920, 1080))
        final_clip = final_clip.with_duration(duration)
        final_clip.write_videofile(output_path, fps=30)
```

---

## 研究結論與決策總表

| 研究項目 | 決策 | 理由 |
|---------|-----|------|
| **代碼結構** | 5 層架構 (CLI → App → Domain → Infra Interface → Infra Impl) | 職責清晰，依賴單向 |
| **測試相容** | Re-export 內部函數 + Deprecation Warning | 向後相容，平滑過渡 |
| **介面定義** | `typing.Protocol` + `@runtime_checkable` | 現代 Python 最佳實踐，支援靜態檢查 |
| **重構策略** | Strangler Fig (Domain) + Branch by Abstraction (Infra) | 風險可控，漸進驗證 |
| **重構順序** | 由內而外：Shared → Infra Interface → Domain → Infra Impl → App → CLI | 依賴方向，最小變更 |
| **MoviePy 抽象** | 場景導向介面 (render_scene) | 符合業務場景，不過度抽象 |

---

## 下一步驟（進入 Phase 1）

1. **定義 Data Model** (`data-model.md`)
   - `VideoConfig` dataclass
   - `LayoutBox` dataclass
   - `IVideoComposer`, `ITextRenderer` Protocol

2. **撰寫 Function Contracts** (`contracts/function-contracts.md`)
   - 各模組公開函數簽名
   - 輸入/輸出規範
   - 錯誤處理策略

3. **撰寫 Test Contracts** (`contracts/test-contracts.md`)
   - 單元測試清單
   - 契約測試清單
   - 整合測試清單

4. **生成 Quickstart** (`quickstart.md`)
   - 驗證領域邏輯獨立測試
   - 驗證介面契約
   - 驗證向後相容性
   - 端到端測試

---

**研究完成**: ✅  
**準備進入 Phase 1**: ✅
