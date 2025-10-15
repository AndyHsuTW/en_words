"""共用層 - 型別定義、常數與驗證邏輯

此模組包含專案中跨層使用的共用元件:
- types.py: VideoConfig, LayoutBox 等資料類別
- constants.py: 畫布尺寸、顏色、安全邊界等常數
- validation.py: JSON schema 驗證與資料載入
"""

# 型別定義
from .types import VideoConfig, LayoutBox

# 常數定義
from .constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    PROGRESS_BAR_SAFE_X,
    PROGRESS_BAR_MAX_X,
    PROGRESS_BAR_WIDTH,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_CORNER_RADIUS,
    PROGRESS_BAR_COLORS,
    PROGRESS_BAR_RATIOS,
    LETTER_SAFE_X,
    LETTER_SAFE_Y,
    LETTER_AVAILABLE_WIDTH,
    LETTER_TARGET_HEIGHT,
    LETTER_BASE_GAP,
    LETTER_EXTRA_SCALE,
    MAIN_BG_COLOR,
    FADE_OUT_DURATION,
    FADE_IN_DURATION,
    DEFAULT_LETTER_ASSET_DIR,
    DEFAULT_ENTRY_VIDEO_PATH,
    DEFAULT_ENDING_VIDEO_PATH,
    ZHUYIN_MAP_SIMPLE,
)

# 驗證功能
from .validation import (
    SCHEMA,
    ValidationError,
    validate_schema,
    load_json,
)

__all__ = [
    # Types
    "VideoConfig",
    "LayoutBox",
    # Constants - Canvas
    "CANVAS_WIDTH",
    "CANVAS_HEIGHT",
    # Constants - Progress Bar
    "PROGRESS_BAR_SAFE_X",
    "PROGRESS_BAR_MAX_X",
    "PROGRESS_BAR_WIDTH",
    "PROGRESS_BAR_HEIGHT",
    "PROGRESS_BAR_CORNER_RADIUS",
    "PROGRESS_BAR_COLORS",
    "PROGRESS_BAR_RATIOS",
    # Constants - Letters
    "LETTER_SAFE_X",
    "LETTER_SAFE_Y",
    "LETTER_AVAILABLE_WIDTH",
    "LETTER_TARGET_HEIGHT",
    "LETTER_BASE_GAP",
    "LETTER_EXTRA_SCALE",
    # Constants - Visual
    "MAIN_BG_COLOR",
    "FADE_OUT_DURATION",
    "FADE_IN_DURATION",
    # Constants - Paths
    "DEFAULT_LETTER_ASSET_DIR",
    "DEFAULT_ENTRY_VIDEO_PATH",
    "DEFAULT_ENDING_VIDEO_PATH",
    # Constants - Zhuyin
    "ZHUYIN_MAP_SIMPLE",
    # Validation
    "SCHEMA",
    "ValidationError",
    "validate_schema",
    "load_json",
]
