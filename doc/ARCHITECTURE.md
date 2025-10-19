# SpellVid 架構文檔

**版本**: 2.0 (重構後)  
**最後更新**: 2025-10-15  
**維護者**: SpellVid 團隊

---

## 目錄

- [概覽](#概覽)
- [架構圖](#架構圖)
- [分層職責](#分層職責)
- [模組導航](#模組導航)
- [資料流程](#資料流程)
- [如何新增功能](#如何新增功能)
- [遷移指南](#遷移指南)
- [設計原則](#設計原則)

---

## 概覽

SpellVid 採用 **分層架構 (Layered Architecture)** 設計,將專案分為 5 個清晰的層次:

```
CLI Layer (命令列介面層)
    ↓
Application Layer (應用服務層)
    ↓
Domain Layer (領域邏輯層)
    ↓
Infrastructure Layer (基礎設施層)
    ↓
Shared Layer (共用層)
```

### 核心設計理念

1. **職責分離**: 每層只處理自己的職責,不跨層存取
2. **依賴反轉**: 高層模組不依賴低層實作細節,透過介面 (Protocol) 解耦
3. **可測試性**: 每層可以獨立測試,不需要真實的外部依賴
4. **向後相容**: 舊代碼可繼續使用,同時引導遷移到新架構

---

## 架構圖

### 層次關係圖

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Layer                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spellvid/cli/                                         │  │
│  │  - parser.py      (參數解析)                          │  │
│  │  - commands.py    (命令處理)                          │  │
│  │  - __main__.py    (程式入口)                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spellvid/application/                                 │  │
│  │  - video_service.py      (視頻生成協調)               │  │
│  │  - batch_service.py      (批次處理邏輯)               │  │
│  │  - resource_checker.py   (資源檢查服務)               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spellvid/domain/                                      │  │
│  │  - layout.py        (佈局計算 - 純函數)               │  │
│  │  - typography.py    (注音處理 - 純函數)               │  │
│  │  - effects.py       (淡入淡出邏輯)                    │  │
│  │  - timing.py        (時間軸管理)                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spellvid/infrastructure/                              │  │
│  │  video/                                               │  │
│  │   - interface.py        (IVideoComposer Protocol)     │  │
│  │   - moviepy_adapter.py  (MoviePy 適配器)              │  │
│  │  rendering/                                           │  │
│  │   - interface.py        (ITextRenderer Protocol)      │  │
│  │   - pillow_adapter.py   (Pillow 適配器)               │  │
│  │  media/                                               │  │
│  │   - interface.py        (IMediaProcessor Protocol)    │  │
│  │   - ffmpeg_wrapper.py   (FFmpeg 包裝器)               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Shared Layer                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spellvid/shared/                                      │  │
│  │  - types.py         (VideoConfig, LayoutBox 等)       │  │
│  │  - constants.py     (常數定義)                        │  │
│  │  - validation.py    (Schema 驗證)                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 依賴方向

- ✅ **允許**: 上層 → 下層 (CLI → Application → Domain → Infrastructure → Shared)
- ✅ **允許**: 任何層 → Shared Layer (共用型別和常數)
- ❌ **禁止**: 下層 → 上層 (例如 Domain 不可匯入 Application)
- ❌ **禁止**: 跨層直接存取 (例如 CLI 直接呼叫 Domain,應透過 Application)

---

## 分層職責

### 1. CLI Layer (命令列介面層)

**位置**: `spellvid/cli/`

**職責**:
- 解析命令列參數 (`parser.py`)
- 處理使用者輸入驗證
- 委派給 Application Layer 執行業務邏輯 (`commands.py`)
- 處理錯誤訊息顯示

**特點**:
- 輕量級,只處理 I/O 和參數轉換
- 不包含業務邏輯
- 可替換 (例如未來可以新增 Web API)

**範例**:
```python
# spellvid/cli/commands.py
from spellvid.application.video_service import render_video
from spellvid.shared.types import VideoConfig

def make_command(args):
    """處理 make 命令"""
    config = VideoConfig(
        letters=args.letters,
        word_en=args.word_en,
        word_zh=args.word_zh,
        image_path=args.image,
        music_path=args.music,
        # ... 其他參數
    )
    return render_video(config, dry_run=args.dry_run)
```

---

### 2. Application Layer (應用服務層)

**位置**: `spellvid/application/`

**職責**:
- 協調多個 Domain 模組和 Infrastructure 適配器
- 管理視頻生成的完整流程 (`video_service.py`)
- 批次處理邏輯 (`batch_service.py`)
- 資源檢查和驗證 (`resource_checker.py`)

**特點**:
- 編排層 (Orchestration Layer)
- 呼叫 Domain 純函數計算結果
- 使用 Infrastructure 適配器執行副作用 (檔案 I/O, 視頻編碼)

**範例**:
```python
# spellvid/application/video_service.py
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

def render_video(config: VideoConfig, dry_run: bool = False):
    """生成單支教學視頻"""
    # 1. 計算佈局 (Domain 純函數)
    layout = compute_layout_bboxes(config)
    
    # 2. 檢查資源 (Application 邏輯)
    check_assets(config)
    
    if dry_run:
        return {"status": "dry-run", "layout": layout}
    
    # 3. 渲染視頻 (Infrastructure 適配器)
    composer = MoviePyAdapter()
    video_clip = composer.create_background_clip(config, layout)
    composer.export(video_clip, config.output_path)
    
    return {"status": "success", "path": config.output_path}
```

---

### 3. Domain Layer (領域邏輯層)

**位置**: `spellvid/domain/`

**職責**:
- 核心業務邏輯 (佈局計算、注音轉換、時間軸管理)
- **純函數** - 無副作用,可預測輸出
- 獨立於外部框架 (不依賴 MoviePy, Pillow)

**特點**:
- 最穩定的層次,很少變更
- 可以在 < 1 秒內測試完成 (不需要真實檔案)
- 效能關鍵路徑 (例如 `compute_layout_bboxes` < 50ms)

**模組**:
- `layout.py`: 計算字母、中文、圖片、進度條的螢幕位置
- `typography.py`: 中文字提取、注音轉換邏輯
- `effects.py`: 淡入淡出時間規劃
- `timing.py`: 倒數計時、進度條更新計算

**範例**:
```python
# spellvid/domain/layout.py
from spellvid.shared.types import VideoConfig, LayoutBox, LayoutResult

def compute_layout_bboxes(config: VideoConfig) -> LayoutResult:
    """計算所有元素的螢幕位置
    
    純函數,不依賴外部狀態。
    效能要求: < 50ms
    """
    # 計算左側字母區域
    letters_bbox = _calculate_letters_bbox(config.letters)
    
    # 計算右側中文區域
    chinese_bbox = _calculate_chinese_bbox(config.word_zh)
    
    # 計算中央圖片區域
    image_bbox = _calculate_image_bbox()
    
    return LayoutResult(
        letters=letters_bbox,
        chinese=chinese_bbox,
        image=image_bbox,
        # ... 其他區域
    )
```

---

### 4. Infrastructure Layer (基礎設施層)

**位置**: `spellvid/infrastructure/`

**職責**:
- 適配外部框架 (MoviePy, Pillow, FFmpeg)
- 實作 Protocol 介面 (依賴反轉)
- 處理檔案 I/O、視頻編碼、圖片渲染

**特點**:
- 可替換 (例如未來可用 OpenCV 取代 Pillow)
- 通過契約測試 (Contract Tests) 驗證介面一致性
- 隔離外部依賴的變更影響

**子目錄**:
- `video/`: 視頻組合相關 (MoviePy)
- `rendering/`: 文字/圖片渲染 (Pillow)
- `media/`: 媒體處理 (FFmpeg, 音頻混合)

**範例**:
```python
# spellvid/infrastructure/video/moviepy_adapter.py
from moviepy import VideoClip, ImageClip
from spellvid.infrastructure.video.interface import IVideoComposer

class MoviePyAdapter(IVideoComposer):
    """MoviePy 框架的適配器"""
    
    def create_background_clip(self, config: VideoConfig, layout: LayoutResult) -> VideoClip:
        """創建背景視頻 Clip"""
        if config.video_path:
            return self._load_video(config.video_path)
        else:
            return ImageClip(config.image_path).set_duration(config.countdown_sec)
    
    def add_text_overlay(self, clip: VideoClip, text: str, bbox: LayoutBox) -> VideoClip:
        """添加文字覆蓋層"""
        # MoviePy 具體實作...
        pass
```

---

### 5. Shared Layer (共用層)

**位置**: `spellvid/shared/`

**職責**:
- 跨層共用的型別定義 (`types.py`)
- 專案常數 (`constants.py`)
- JSON Schema 驗證邏輯 (`validation.py`)

**特點**:
- 所有層都可以匯入 Shared Layer
- 不依賴其他任何層
- 高內聚,低耦合

**範例**:
```python
# spellvid/shared/types.py
from dataclasses import dataclass

@dataclass
class VideoConfig:
    """單支視頻配置"""
    letters: str
    word_en: str
    word_zh: str
    image_path: str | None = None
    music_path: str | None = None
    countdown_sec: float = 3.0
    # ... 20+ 欄位

@dataclass(frozen=True)
class LayoutBox:
    """螢幕區域邊界框 (不可變)"""
    x: int
    y: int
    width: int
    height: int
```

---

## 模組導航

### 如何找到特定功能?

| 功能需求 | 所在模組 | 函數名稱 |
|---------|---------|---------|
| 計算字母螢幕位置 | `spellvid.domain.layout` | `compute_layout_bboxes()` |
| 中文轉注音 | `spellvid.domain.typography` | `zhuyin_for()` |
| 檢查圖片/音樂是否存在 | `spellvid.application.resource_checker` | `check_assets()` |
| 渲染單支視頻 | `spellvid.application.video_service` | `render_video()` |
| 批次處理多支視頻 | `spellvid.application.batch_service` | `render_batch()` |
| 驗證 JSON 格式 | `spellvid.shared.validation` | `validate_schema()` |
| 創建 MoviePy Clip | `spellvid.infrastructure.video.moviepy_adapter` | `MoviePyAdapter.create_background_clip()` |
| 渲染文字圖片 | `spellvid.infrastructure.rendering.pillow_adapter` | `PillowAdapter.render_text()` |
| 混合音頻 | `spellvid.infrastructure.media.ffmpeg_wrapper` | `FFmpegWrapper.mix_audio()` |

### Import 路徑慣例

**✅ 推薦 (新代碼)**:
```python
# 使用新架構模組
from spellvid.shared.types import VideoConfig, LayoutBox
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.application.video_service import render_video
```

**⚠️ 已棄用 (舊代碼)**:
```python
# 舊 API,會顯示 DeprecationWarning
from spellvid.utils import compute_layout_bboxes
from spellvid import cli
cli.make(args)  # 使用 cli.make_command(args) 替代
```

---

## 資料流程

### 單支視頻生成流程

```
1. CLI 解析參數
   ↓ (傳遞 Namespace)
   
2. CLI commands 創建 VideoConfig
   ↓ (呼叫 application)
   
3. Application video_service 協調流程:
   a. 呼叫 domain.layout 計算佈局 (純函數)
   b. 呼叫 resource_checker 驗證檔案存在
   c. 呼叫 infrastructure 適配器:
      - moviepy_adapter 創建 Clips
      - pillow_adapter 渲染文字
      - ffmpeg_wrapper 混合音頻
   d. 匯出視頻到指定路徑
   ↓ (返回結果字典)
   
4. CLI 顯示成功/失敗訊息
```

### 批次處理流程

```
1. CLI 解析 --json 參數
   ↓
   
2. CLI commands 載入 JSON
   ↓ (呼叫 shared.validation)
   
3. Validation 驗證 Schema
   ↓ (轉換為 VideoConfig 列表)
   
4. Application batch_service 迭代處理:
   - 每項呼叫 video_service.render_video()
   - 處理錯誤但不中斷
   - 收集成功/失敗統計
   ↓
   
5. CLI 顯示批次處理報告
```

---

## 如何新增功能

### 範例: 新增「浮水印」功能

**步驟 1: 評估影響層次**

浮水印需要:
- 位置計算 → Domain Layer
- 圖片覆蓋 → Infrastructure Layer
- 配置欄位 → Shared Layer

**步驟 2: TDD - 先寫測試**

```python
# tests/unit/domain/test_layout.py
def test_compute_watermark_position():
    """測試浮水印位置計算"""
    layout = compute_layout_bboxes(sample_config)
    assert layout.watermark.x == 900
    assert layout.watermark.y == 950
```

**步驟 3: 擴展型別定義 (Shared)**

```python
# spellvid/shared/types.py
@dataclass
class VideoConfig:
    # ... 現有欄位
    watermark_path: str | None = None  # 新增

@dataclass
class LayoutResult:
    # ... 現有欄位
    watermark: LayoutBox | None = None  # 新增
```

**步驟 4: 實作純邏輯 (Domain)**

```python
# spellvid/domain/layout.py
def compute_layout_bboxes(config: VideoConfig) -> LayoutResult:
    # ... 現有邏輯
    
    watermark_bbox = None
    if config.watermark_path:
        watermark_bbox = LayoutBox(x=900, y=950, width=100, height=50)
    
    return LayoutResult(
        # ... 現有欄位
        watermark=watermark_bbox
    )
```

**步驟 5: 實作渲染邏輯 (Infrastructure)**

```python
# spellvid/infrastructure/video/moviepy_adapter.py
class MoviePyAdapter:
    def add_watermark(self, clip: VideoClip, layout: LayoutResult) -> VideoClip:
        """疊加浮水印"""
        if not layout.watermark:
            return clip
        
        watermark = ImageClip(config.watermark_path)
        watermark = watermark.set_position((layout.watermark.x, layout.watermark.y))
        return CompositeVideoClip([clip, watermark])
```

**步驟 6: 整合到流程 (Application)**

```python
# spellvid/application/video_service.py
def render_video(config: VideoConfig, dry_run: bool = False):
    layout = compute_layout_bboxes(config)
    
    # ... 現有邏輯
    
    if config.watermark_path:
        video_clip = composer.add_watermark(video_clip, layout)
    
    # ... 匯出邏輯
```

**步驟 7: 新增 CLI 參數 (CLI)**

```python
# spellvid/cli/parser.py
def build_parser():
    parser = argparse.ArgumentParser()
    # ... 現有參數
    parser.add_argument('--watermark', help='浮水印圖片路徑')
    return parser
```

---

## 遷移指南

### 從舊 API 遷移到新架構

#### 場景 1: 使用 `compute_layout_bboxes`

**舊代碼**:
```python
from spellvid.utils import compute_layout_bboxes

item = {
    "letters": "I i",
    "word_en": "Ice",
    "word_zh": "冰"
}
result = compute_layout_bboxes(item)
letters_bbox = result["letters"]
```

**新代碼**:
```python
from spellvid.shared.types import VideoConfig
from spellvid.domain.layout import compute_layout_bboxes

config = VideoConfig(
    letters="I i",
    word_en="Ice",
    word_zh="冰"
)
result = compute_layout_bboxes(config)
letters_bbox = result.letters  # 使用 dataclass 屬性
```

**優點**:
- ✅ IDE 自動完成
- ✅ 型別檢查捕捉錯誤
- ✅ 明確的欄位定義

---

#### 場景 2: 渲染視頻

**舊代碼**:
```python
from spellvid.utils import render_video_stub

item = load_json("config.json")[0]
render_video_stub(item, output_path="out/Ice.mp4")
```

**新代碼**:
```python
from spellvid.shared.types import VideoConfig
from spellvid.shared.validation import load_json
from spellvid.application.video_service import render_video

items = load_json("config.json")
config = VideoConfig.from_dict(items[0])
result = render_video(config, dry_run=False)
print(result["status"])  # "success"
```

---

#### 場景 3: CLI 使用

**舊代碼** (仍可使用,但有 DeprecationWarning):
```python
from spellvid import cli
args = cli.build_parser().parse_args()
cli.make(args)
```

**新代碼**:
```python
from spellvid.cli.commands import make_command
from spellvid.cli.parser import build_parser

args = build_parser().parse_args()
make_command(args)
```

---

### 向後相容性保證

**保留模組** (顯示 DeprecationWarning):
- `spellvid/utils.py` - 保留所有函數,但建議遷移
- `spellvid/cli.py` - 保留 `make()`, `batch()` 等函數

**移除時程**:
- **v2.x**: 完全向後相容 (目前版本)
- **v3.0**: 移除 `utils.py`,僅保留 re-export 層
- **v4.0**: 完全移除舊 API

---

## 設計原則

### 1. 單一職責原則 (SRP)

每個模組只處理一件事:
- `layout.py` 只計算位置,不渲染
- `moviepy_adapter.py` 只包裝 MoviePy,不處理業務邏輯

### 2. 開放封閉原則 (OCP)

透過 Protocol 介面擴展功能,不修改現有代碼:
```python
# 新增 OpenCV 適配器,不需修改 video_service.py
class OpenCVAdapter(IVideoComposer):
    def create_background_clip(self, config, layout):
        # OpenCV 實作
        pass
```

### 3. 依賴反轉原則 (DIP)

高層模組依賴抽象 (Protocol),不依賴具體實作:
```python
# Application 依賴 IVideoComposer,不依賴 MoviePyAdapter
def render_video(config: VideoConfig, composer: IVideoComposer):
    clip = composer.create_background_clip(config, layout)
    # ...
```

### 4. 介面隔離原則 (ISP)

Protocol 介面精簡,只包含必要方法:
```python
class ITextRenderer(Protocol):
    def render_text(self, text: str, font_size: int) -> Image: ...
    def get_text_size(self, text: str, font_size: int) -> tuple[int, int]: ...
    # 不包含無關的視頻編碼方法
```

### 5. 純函數優先 (Functional Core)

Domain Layer 使用純函數,可預測且易測試:
```python
# 純函數 - 無副作用,輸出只依賴輸入
def compute_layout_bboxes(config: VideoConfig) -> LayoutResult:
    # 不讀寫檔案,不修改全域變數
    return LayoutResult(...)
```

---

## 測試策略

### 測試金字塔

```
           ╱ ╲
          ╱ E2E╲        (少量 - CLI 整合測試)
         ╱───────╲
        ╱ Integ. ╲      (中量 - Application 協調測試)
       ╱───────────╲
      ╱  Contract   ╲   (中量 - Infrastructure Protocol 測試)
     ╱───────────────╲
    ╱   Unit Tests    ╲ (大量 - Domain 純函數測試)
   ╱───────────────────╲
```

### 測試覆蓋率目標

| 層次 | 目標覆蓋率 | 測試類型 |
|-----|----------|---------|
| Shared | 95% | Unit |
| Domain | 90% | Unit |
| Infrastructure | 75% | Contract + Unit |
| Application | 85% | Integration (mock infra) |
| CLI | 70% | E2E (dry-run) |

### 執行測試

```bash
# 快速測試 (Domain 純函數,< 1 秒)
pytest tests/unit/domain/ -v

# 契約測試 (Infrastructure 介面)
pytest tests/contract/ -v

# 整合測試 (Application 協調邏輯)
pytest tests/integration/ -v

# 完整測試套件
.\scripts\run_tests.ps1
```

---

## 效能基準

| 函數 | 基準時間 | 測試 |
|-----|---------|------|
| `compute_layout_bboxes()` | < 50ms | `test_layout.py::test_layout_performance` |
| `render_video()` dry-run | < 100ms | `test_video_service.py::test_dry_run_fast` |
| 批次 100 支視頻 | ≤ 110% baseline | `tests/performance/` (optional) |

---

## 常見問題 (FAQ)

### Q1: 為什麼要重構?

**A**: 原本的 `utils.py` 有 3600+ 行,包含所有邏輯:
- ❌ 難以測試 (需要真實檔案和 MoviePy)
- ❌ 難以擴展 (修改一處影響多處)
- ❌ 難以理解 (職責混雜)

新架構解決這些問題:
- ✅ 清晰的職責分離
- ✅ 獨立可測試的模組
- ✅ 可替換的基礎設施

### Q2: 舊代碼會停止運作嗎?

**A**: 不會。舊 API 完全保留,只會顯示 DeprecationWarning:
```
DeprecationWarning: The spellvid.utils module is deprecated. 
Please migrate to the new modular architecture. See ARCHITECTURE.md for details.
```

你有充足時間逐步遷移。

### Q3: 如何決定功能放在哪一層?

**A**: 遵循以下規則:
1. **純計算邏輯** → Domain Layer (例如位置計算)
2. **外部依賴包裝** → Infrastructure Layer (例如 MoviePy 呼叫)
3. **流程協調** → Application Layer (例如先計算,再渲染)
4. **使用者互動** → CLI Layer (例如參數解析)
5. **跨層共用型別** → Shared Layer (例如 VideoConfig)

### Q4: Protocol 和 Abstract Class 有何不同?

**A**: 
- **Protocol** (結構性子型別): 只要實作符合方法簽名即可,不需繼承
- **Abstract Class** (名義性子型別): 必須明確繼承 `ABC`

我們選擇 Protocol 是為了:
- ✅ 不侵入現有代碼 (Strangler Fig 模式)
- ✅ Duck Typing 友善
- ✅ 更靈活的實作方式

### Q5: 測試覆蓋率不到 100%,是否有問題?

**A**: 不同層次有不同的覆蓋率目標:
- Domain Layer 90% (核心邏輯必須高覆蓋)
- Infrastructure 75% (部分依賴外部環境,難以測試)
- CLI 70% (E2E 測試成本高)

我們追求**有意義的測試**,不是數字遊戲。

---

## 參考資料

- [Hexagonal Architecture (Ports & Adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Protocol (PEP 544)](https://peps.python.org/pep-0544/)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

---

**維護提示**:
- 新增功能時,請同步更新本文檔的「模組導航」章節
- 修改 Protocol 介面時,請更新「契約測試」
- 效能基準變更時,請更新「效能基準」表格

**問題回報**: 請在 GitHub Issues 中回報文檔錯誤或不清楚的說明。
