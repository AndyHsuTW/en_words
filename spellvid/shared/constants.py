"""共用常數定義

此模組定義專案中跨層使用的常數:
- 畫布尺寸
- 進度條配置
- 安全邊距
- 顏色定義
- 預設路徑

這些常數從 utils.py 遷移而來,確保佈局計算的一致性。
"""

import os

# ========== 畫布尺寸 ==========
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# ========== 進度條配置 ==========
PROGRESS_BAR_SAFE_X = 64
PROGRESS_BAR_MAX_X = 1856
PROGRESS_BAR_WIDTH = PROGRESS_BAR_MAX_X - PROGRESS_BAR_SAFE_X  # 1792
PROGRESS_BAR_HEIGHT = 32
PROGRESS_BAR_CORNER_RADIUS = 16

# 進度條顏色(RGB tuples)
PROGRESS_BAR_COLORS = {
    "safe": (164, 223, 195),    # 綠色區段
    "warn": (247, 228, 133),    # 黃色警告區
    "danger": (248, 187, 166),  # 紅色危險區
}

# 進度條區段比例(總和應為 1.0)
PROGRESS_BAR_RATIOS = {
    "safe": 0.5,    # 50% 綠色
    "warn": 0.2,    # 20% 黃色
    "danger": 0.3,  # 30% 紅色
}

# ========== 字母區域配置 ==========
LETTER_SAFE_X = 64
LETTER_SAFE_Y = 48
LETTER_AVAILABLE_WIDTH = CANVAS_WIDTH - (LETTER_SAFE_X * 2)  # 1792
LETTER_TARGET_HEIGHT = 220
LETTER_BASE_GAP = -40  # 字母間距(負值表示重疊)
LETTER_EXTRA_SCALE = 1.5

# ========== 顏色常數 ==========
MAIN_BG_COLOR = (255, 250, 233)  # 米黃色
COLOR_WHITE = (255, 255, 255)    # 白色
COLOR_BLACK = (0, 0, 0)          # 黑色

# ========== 視頻轉場效果常數 ==========
FADE_OUT_DURATION = 3.0  # 秒 - 片尾淡出黑屏時長
FADE_IN_DURATION = 1.0   # 秒 - 片頭淡入時長

# ========== 預設資源路徑 ==========
# 注意: 這些路徑相對於 spellvid/shared/ 解析到專案根目錄的 assets/
_MODULE_DIR = os.path.dirname(__file__)  # spellvid/shared/
_PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, "..", ".."))  # 專案根目錄

DEFAULT_LETTER_ASSET_DIR = os.path.join(_PROJECT_ROOT, "assets", "AZ")
DEFAULT_ENTRY_VIDEO_PATH = os.path.join(_PROJECT_ROOT, "assets", "entry.mp4")
DEFAULT_ENDING_VIDEO_PATH = os.path.join(_PROJECT_ROOT, "assets", "ending.mp4")

# ========== 簡化注音對應表(測試用) ==========
# 注意: 完整的注音邏輯應在 domain.zhuyin 模組中
ZHUYIN_MAP_SIMPLE = {
    "冰": "ㄅㄧㄥ",
    "塊": "ㄎㄨㄞˋ",
    "動": "ㄉㄨㄥˋ",
    "物": "ㄨˋ",
}
