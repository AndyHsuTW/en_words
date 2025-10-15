# Data Model: 專案架構重構 - 實體與介面定義

**Feature**: 002-refactor-architecture  
**Date**: 2025-10-14  
**Purpose**: 定義重構後架構中的核心實體、值物件與介面契約

---

## 概覽

本文檔定義重構後 SpellVid 專案的資料模型,包括:
- **領域實體** (Domain Entities): 業務邏輯核心物件
- **值物件** (Value Objects): 不可變的資料載體
- **介面契約** (Interface Protocols): 基礎設施抽象層

所有定義遵循 Python 3.11+ 型別提示規範,使用 `@dataclass` 與 `typing.Protocol`。

---

## 1. 領域實體 (Domain Entities)

### 1.1 VideoConfig

**職責**: 封裝單支視頻的所有配置資訊

**位置**: `spellvid/shared/types.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class VideoConfig:
    """單支教學視頻的配置資料
    
    此類別取代原本的 Dict[str, Any],提供型別安全與 IDE 自動完成。
    所有欄位對應 JSON schema 中的項目。
    """
    # 必填欄位
    letters: str  # 英文字母(大小寫,空格分隔)
    word_en: str  # 英文單字
    word_zh: str  # 中文釋義(含注音)
    
    # 可選資源路徑
    image_path: Optional[str] = None  # 中央圖片/視頻路徑
    music_path: Optional[str] = None  # 背景音樂路徑
    video_path: Optional[str] = None  # 背景視頻路徑(與 image_path 互斥)
    
    # 時間控制
    countdown_sec: float = 3.0  # 倒數計時秒數
    reveal_hold_sec: float = 2.0  # 中文顯示停留秒數
    entry_hold_sec: float = 0.0  # 片頭停留秒數
    
    # 視覺選項
    timer_visible: bool = True  # 是否顯示倒數計時器
    progress_bar: bool = True  # 是否顯示進度條
    letters_as_image: bool = True  # 字母使用圖片或文字
    
    # 視頻模式 (當 video_path 存在時)
    video_mode: str = "cover"  # "cover" 或 "fit"
    
    # 輸出路徑 (batch 模式時設定)
    output_path: Optional[str] = None
    
    def __post_init__(self):
        """驗證配置一致性"""
        if self.image_path and self.video_path:
            raise ValueError("image_path 與 video_path 不可同時設定")
        
        if self.countdown_sec < 0:
            raise ValueError("countdown_sec 必須 >= 0")
        
        if self.video_mode not in ("cover", "fit"):
            raise ValueError("video_mode 必須是 'cover' 或 'fit'")
    
    @classmethod
    def from_dict(cls, data: dict) -> "VideoConfig":
        """從 JSON 字典建立 VideoConfig
        
        Args:
            data: 從 config.json 載入的單項資料
            
        Returns:
            VideoConfig 實例
        """
        # 過濾未定義的欄位
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)
    
    def to_dict(self) -> dict:
        """轉換為字典格式(向後相容)
        
        Returns:
            包含所有欄位的字典
        """
        from dataclasses import asdict
        return asdict(self)
```

---

### 1.2 LayoutBox

**職責**: 表示螢幕上的矩形區域

**位置**: `spellvid/shared/types.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LayoutBox:
    """不可變的矩形邊界框
    
    用於描述視覺元素在 1920x1080 畫布上的位置與尺寸。
    frozen=True 確保值物件不可變性。
    """
    x: int  # 左上角 X 座標
    y: int  # 左上角 Y 座標
    width: int  # 寬度(像素)
    height: int  # 高度(像素)
    
    def __post_init__(self):
        """驗證邊界框有效性"""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width 與 height 必須 > 0")
        
        if self.x < 0 or self.y < 0:
            raise ValueError("x 與 y 必須 >= 0")
    
    @property
    def right(self) -> int:
        """右邊界 X 座標"""
        return self.x + self.width
    
    @property
    def bottom(self) -> int:
        """下邊界 Y 座標"""
        return self.y + self.height
    
    @property
    def center_x(self) -> int:
        """中心點 X 座標"""
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        """中心點 Y 座標"""
        return self.y + self.height // 2
    
    def overlaps(self, other: "LayoutBox") -> bool:
        """檢查是否與另一邊界框重疊
        
        Args:
            other: 另一個 LayoutBox
            
        Returns:
            True 若兩者有重疊區域
        """
        return not (
            self.right <= other.x or
            self.x >= other.right or
            self.bottom <= other.y or
            self.y >= other.bottom
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "LayoutBox":
        """從字典建立 LayoutBox
        
        Args:
            data: 包含 x, y, width, height 的字典
            
        Returns:
            LayoutBox 實例
        """
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"]
        )
    
    def to_dict(self) -> dict:
        """轉換為字典格式
        
        Returns:
            包含 x, y, width, height 的字典
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
```

---

### 1.3 LayoutResult

**職責**: 封裝佈局計算的完整結果

**位置**: `spellvid/domain/layout.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from spellvid.shared.types import LayoutBox

@dataclass
class ZhuyinColumn:
    """單個中文字元的注音排版資訊"""
    char: str  # 中文字元
    main_symbols: List[str]  # 主要注音符號
    tone_symbol: Optional[str]  # 聲調符號
    bbox: LayoutBox  # 整體邊界框
    main_bbox: LayoutBox  # 主要注音區域
    tone_bbox: Optional[LayoutBox]  # 聲調區域(若有)

@dataclass
class LayoutResult:
    """完整的佈局計算結果
    
    包含所有視覺元素的位置資訊,供渲染層使用。
    """
    # 主要元素邊界框
    letters: LayoutBox  # 左側字母區域
    word_zh: LayoutBox  # 右側中文區域
    reveal: LayoutBox  # 中文顯示區域
    timer: Optional[LayoutBox] = None  # 倒數計時器(可選)
    image: Optional[LayoutBox] = None  # 中央圖片區域(可選)
    
    # 注音細節
    zhuyin_columns: List[ZhuyinColumn] = field(default_factory=list)
    
    # 下劃線位置(用於 reveal 動畫)
    reveal_underlines: List[Tuple[int, int, int, int]] = field(default_factory=list)
    # 每個 tuple: (x, y, width, height)
    
    # 進度條資訊
    progress_bar_y: Optional[int] = None  # 進度條 Y 座標
    
    def to_dict(self) -> Dict[str, any]:
        """轉換為舊版 Dict 格式(向後相容)
        
        Returns:
            與 compute_layout_bboxes 原本回傳格式相同的字典
        """
        result = {
            "letters": self.letters.to_dict(),
            "word_zh": self.word_zh.to_dict(),
            "reveal": self.reveal.to_dict(),
        }
        
        if self.timer:
            result["timer"] = self.timer.to_dict()
        
        if self.image:
            result["image"] = self.image.to_dict()
        
        if self.reveal_underlines:
            result["reveal_underlines"] = self.reveal_underlines
        
        if self.progress_bar_y is not None:
            result["progress_bar_y"] = self.progress_bar_y
        
        # 注音細節轉換
        if self.zhuyin_columns:
            result["zhuyin_details"] = [
                {
                    "char": col.char,
                    "main": col.main_symbols,
                    "tone": col.tone_symbol,
                    "bbox": col.bbox.to_dict(),
                    "main_bbox": col.main_bbox.to_dict(),
                    "tone_bbox": col.tone_bbox.to_dict() if col.tone_bbox else None
                }
                for col in self.zhuyin_columns
            ]
        
        return result
```

---

## 2. 應用層物件 (Application Layer Objects)

### 2.1 RenderContext

**職責**: 封裝視頻渲染所需的所有上下文資訊

**位置**: `spellvid/application/video_service.py`

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from spellvid.shared.types import VideoConfig
from spellvid.domain.layout import LayoutResult

@dataclass
class RenderContext:
    """視頻渲染上下文
    
    聚合配置、佈局、資源等渲染所需的所有資訊,
    避免在函數間傳遞過多參數。
    """
    # 核心配置
    config: VideoConfig
    
    # 佈局計算結果
    layout: LayoutResult
    
    # 載入的資源
    assets: Dict[str, Any]  # key: "image", "music", "letters", etc.
    
    # 時間軸資訊
    duration: float  # 總時長(秒)
    countdown_start: float  # 倒數開始時間
    reveal_start: float  # 中文顯示時間
    
    # 輸出設定
    output_path: str
    dry_run: bool = False
    skip_ending: bool = False
    
    # 可選的除錯資訊
    debug_overlay: bool = False
```

---

## 3. 基礎設施介面 (Infrastructure Interfaces)

### 3.1 IVideoComposer

**職責**: 定義與視頻合成框架(MoviePy)無關的抽象層

**位置**: `spellvid/infrastructure/video/interface.py`

```python
from typing import Protocol, Any, List, Tuple, runtime_checkable
import numpy as np

@runtime_checkable
class IVideoComposer(Protocol):
    """視頻合成引擎介面
    
    抽象化 MoviePy 的 Clip 概念,提供高階的場景渲染 API。
    實作者: MoviePyAdapter (當前), 未來可替換為其他引擎。
    """
    
    def create_color_clip(
        self, 
        size: Tuple[int, int], 
        color: Tuple[int, int, int],
        duration: float
    ) -> Any:
        """建立純色背景 Clip
        
        Args:
            size: (width, height) 尺寸
            color: (R, G, B) 顏色值 (0-255)
            duration: 持續時間(秒)
            
        Returns:
            框架特定的 Clip 物件
        """
        ...
    
    def create_image_clip(
        self,
        image_array: np.ndarray,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立圖片 Clip
        
        Args:
            image_array: NumPy 陣列 (H, W, C)
            duration: 持續時間(秒)
            position: (x, y) 位置
            
        Returns:
            框架特定的 Clip 物件
        """
        ...
    
    def create_video_clip(
        self,
        video_path: str,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立視頻 Clip
        
        Args:
            video_path: 視頻檔案路徑
            duration: 目標持續時間(秒)
            position: (x, y) 位置
            
        Returns:
            框架特定的 Clip 物件
        """
        ...
    
    def compose_clips(
        self,
        clips: List[Any],
        size: Tuple[int, int] = (1920, 1080)
    ) -> Any:
        """組合多個 Clips 為單一合成 Clip
        
        Args:
            clips: Clip 物件列表(由內而外,底層在前)
            size: 畫布尺寸
            
        Returns:
            合成後的 Clip 物件
        """
        ...
    
    def apply_fadeout(
        self,
        clip: Any,
        duration: float
    ) -> Any:
        """對 Clip 套用淡出效果
        
        Args:
            clip: 要處理的 Clip
            duration: 淡出持續時間(秒)
            
        Returns:
            套用淡出後的 Clip
        """
        ...
    
    def render_to_file(
        self,
        clip: Any,
        output_path: str,
        fps: int = 30,
        codec: str = "libx264"
    ) -> None:
        """將 Clip 渲染為視頻檔案
        
        Args:
            clip: 要渲染的 Clip
            output_path: 輸出檔案路徑
            fps: 影格率
            codec: 視頻編碼器
        """
        ...
    
    def concatenate_clips(
        self,
        clips: List[Any],
        method: str = "compose"
    ) -> Any:
        """串接多個 Clips
        
        Args:
            clips: 要串接的 Clip 列表
            method: 串接方法 ("compose" 或 "chain")
            
        Returns:
            串接後的 Clip
        """
        ...
```

---

### 3.2 ITextRenderer

**職責**: 定義與圖片處理庫(Pillow)無關的文字渲染抽象

**位置**: `spellvid/infrastructure/rendering/interface.py`

```python
from typing import Protocol, Tuple, Optional, runtime_checkable
from PIL import Image

@runtime_checkable
class ITextRenderer(Protocol):
    """文字渲染引擎介面
    
    抽象化 Pillow 的文字繪製功能。
    實作者: PillowAdapter (當前)
    """
    
    def render_text_image(
        self,
        text: str,
        font_path: str,
        font_size: int,
        color: Tuple[int, int, int] = (0, 0, 0),
        bg_color: Optional[Tuple[int, int, int]] = None,
        padding: int = 0,
        fixed_size: Optional[Tuple[int, int]] = None
    ) -> Image.Image:
        """渲染文字為 PIL Image
        
        Args:
            text: 要渲染的文字
            font_path: 字型檔案路徑
            font_size: 字型大小
            color: 文字顏色 (R, G, B)
            bg_color: 背景顏色,None 表示透明
            padding: 內距(像素)
            fixed_size: 固定尺寸 (width, height),None 表示自動
            
        Returns:
            PIL.Image.Image 物件
        """
        ...
    
    def measure_text_size(
        self,
        text: str,
        font_path: str,
        font_size: int
    ) -> Tuple[int, int]:
        """測量文字渲染後的尺寸
        
        Args:
            text: 要測量的文字
            font_path: 字型檔案路徑
            font_size: 字型大小
            
        Returns:
            (width, height) 尺寸
        """
        ...
    
    def find_system_font(
        self,
        prefer_cjk: bool = False
    ) -> str:
        """尋找系統可用的字型
        
        Args:
            prefer_cjk: 是否優先尋找 CJK 字型
            
        Returns:
            字型檔案絕對路徑
            
        Raises:
            FileNotFoundError: 找不到可用字型
        """
        ...
```

---

### 3.3 IMediaProcessor

**職責**: 定義與媒體處理工具(FFmpeg)無關的抽象

**位置**: `spellvid/infrastructure/media/interface.py`

```python
from typing import Protocol, Optional, Tuple, runtime_checkable

@runtime_checkable
class IMediaProcessor(Protocol):
    """媒體處理工具介面
    
    抽象化 FFmpeg 功能。
    實作者: FFmpegWrapper (當前)
    """
    
    def probe_duration(
        self,
        media_path: str
    ) -> float:
        """查詢媒體檔案時長
        
        Args:
            media_path: 媒體檔案路徑
            
        Returns:
            時長(秒)
            
        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析時長
        """
        ...
    
    def probe_dimensions(
        self,
        video_path: str
    ) -> Tuple[int, int]:
        """查詢視頻尺寸
        
        Args:
            video_path: 視頻檔案路徑
            
        Returns:
            (width, height) 尺寸
            
        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析尺寸
        """
        ...
    
    def create_placeholder_video(
        self,
        output_path: str,
        duration: float = 1.0,
        size: Tuple[int, int] = (1920, 1080),
        color: Tuple[int, int, int] = (255, 255, 255)
    ) -> bool:
        """建立佔位視頻檔案
        
        Args:
            output_path: 輸出路徑
            duration: 時長(秒)
            size: (width, height) 尺寸
            color: (R, G, B) 顏色
            
        Returns:
            True 若成功, False 若失敗
        """
        ...
    
    def extract_audio(
        self,
        video_path: str,
        output_path: str
    ) -> bool:
        """從視頻提取音訊
        
        Args:
            video_path: 視頻檔案路徑
            output_path: 音訊輸出路徑
            
        Returns:
            True 若成功, False 若失敗
        """
        ...
```

---

## 4. 常數定義 (Constants)

**位置**: `spellvid/shared/constants.py`

```python
"""全域常數定義

集中管理所有 magic numbers 與預設值,避免散落在各模組中。
"""

# ===== 畫布尺寸 =====
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# ===== 佈局常數 =====
LETTER_SAFE_X = 64
LETTER_SAFE_Y = 48
LETTER_AVAILABLE_WIDTH = 750
LETTER_AVAILABLE_HEIGHT = 984

MAIN_SAFE_X = 1084
MAIN_SAFE_Y = 48
MAIN_AVAILABLE_WIDTH = 772
MAIN_AVAILABLE_HEIGHT = 984

# ===== 進度條常數 =====
PROGRESS_BAR_SAFE_X = 64
PROGRESS_BAR_MAX_X = 1856
PROGRESS_BAR_WIDTH = PROGRESS_BAR_MAX_X - PROGRESS_BAR_SAFE_X
PROGRESS_BAR_HEIGHT = 32
PROGRESS_BAR_CORNER_RADIUS = 16

PROGRESS_BAR_COLORS = {
    "safe": (164, 223, 195),
    "warn": (247, 228, 133),
    "danger": (248, 187, 166),
}

PROGRESS_BAR_RATIOS = {
    "safe": 0.5,
    "warn": 0.2,
    "danger": 0.3,
}

# ===== 渲染常數 =====
MAIN_BG_COLOR = (255, 255, 255)
FADE_OUT_DURATION = 0.5

# ===== 預設路徑 =====
DEFAULT_LETTER_ASSET_DIR = "assets/AZ"
DEFAULT_ENTRY_VIDEO_PATH = "assets/entry.mp4"
DEFAULT_ENDING_VIDEO_PATH = "assets/ending.mp4"

# ===== 字型常數 =====
DEFAULT_FONT_SIZE_EN = 180
DEFAULT_FONT_SIZE_ZH = 144
DEFAULT_FONT_SIZE_TIMER = 128

# ===== MoviePy 可用性 =====
HAS_MOVIEPY = False  # 由 __init__.py 初始化時設定
```

---

## 5. 型別別名 (Type Aliases)

**位置**: `spellvid/shared/types.py`

```python
"""型別別名與工具型別"""

from typing import Dict, Any, List, Tuple
from PIL import Image
import numpy as np

# ===== 舊版相容型別 =====
ConfigDict = Dict[str, Any]  # 舊版配置字典
LayoutDict = Dict[str, Dict[str, int]]  # 舊版佈局字典

# ===== 媒體型別 =====
ImageArray = np.ndarray  # NumPy 陣列 (H, W, C)
PILImage = Image.Image  # Pillow Image

# ===== 座標型別 =====
Position = Tuple[int, int]  # (x, y)
Size = Tuple[int, int]  # (width, height)
Color = Tuple[int, int, int]  # (R, G, B)
BBox = Tuple[int, int, int, int]  # (x, y, width, height)

# ===== Clip 型別提示 =====
# 注意：實際 Clip 型別由框架決定,這裡用 Any 表示
ClipLike = Any  # MoviePy Clip 或相容物件
```

---

## 6. 資料流總覽

```
JSON 輸入
  ↓ from_dict()
VideoConfig (shared/types.py)
  ↓ 傳遞給
compute_layout_bboxes() (domain/layout.py)
  ↓ 回傳
LayoutResult (domain/layout.py)
  ↓ 聚合為
RenderContext (application/video_service.py)
  ↓ 傳遞給
IVideoComposer (infrastructure/video/interface.py)
  ↓ 實作
MoviePyAdapter (infrastructure/video/moviepy_adapter.py)
  ↓ 輸出
MP4 檔案
```

---

## 7. 向後相容策略

### 7.1 保留舊版 API

`spellvid/utils.py` 保留以下函數:

```python
from spellvid.shared.types import VideoConfig
from spellvid.domain.layout import compute_layout_bboxes as _new_compute_layout_bboxes
import warnings

def compute_layout_bboxes(item: Dict[str, Any], ...) -> Dict[str, Dict[str, int]]:
    """向後相容的佈局計算函數
    
    ⚠️ DEPRECATED: 請改用 spellvid.domain.layout.compute_layout_bboxes
    """
    warnings.warn(
        "utils.compute_layout_bboxes is deprecated. "
        "Use domain.layout.compute_layout_bboxes instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    config = VideoConfig.from_dict(item)
    result = _new_compute_layout_bboxes(config, ...)
    return result.to_dict()
```

### 7.2 測試匯入相容性

測試可繼續使用:
```python
from spellvid.utils import _make_text_imageclip, _HAS_MOVIEPY
```

這些會 re-export 自新位置,但附帶 DeprecationWarning。

---

## 8. 驗收標準

- [x] 所有 dataclass 定義完整,具有型別提示
- [x] 所有 Protocol 定義完整,標記 `@runtime_checkable`
- [x] VideoConfig.from_dict() 與 to_dict() 實作
- [x] LayoutResult.to_dict() 實作向後相容
- [x] 所有介面方法具有完整 docstring
- [x] 常數集中定義於 shared/constants.py

---

**狀態**: ✅ 資料模型定義完成  
**下一步**: 生成 contracts/function-contracts.md
