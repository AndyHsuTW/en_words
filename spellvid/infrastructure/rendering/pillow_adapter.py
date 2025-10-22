"""Pillow 文字渲染適配器

此模組實作 ITextRenderer Protocol,使用 Pillow (PIL) 進行文字渲染。

主要功能:
- 文字轉圖片渲染(支援透明背景)
- 文字尺寸預測
- 跨平台字型偵測(支援 CJK 字型)
"""

import platform
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


class PillowAdapter:
    """Pillow 文字渲染適配器

    實作 ITextRenderer Protocol,提供文字渲染服務。

    使用 Pillow (PIL) 進行:
    - 文字轉圖片(支援自訂字型、顏色、背景)
    - 文字尺寸計算
    - 系統字型偵測
    """

    def render_text_image(
        self,
        text: str,
        font_path: str,
        font_size: int,
        color: Tuple[int, int, int] = (0, 0, 0),
        bg_color: Optional[Tuple[int, int, int]] = None,
        padding: int = 0,
        fixed_size: Optional[Tuple[int, int]] = None,
    ) -> Image.Image:
        """渲染文字為 PIL Image

        Args:
            text: 要渲染的文字內容
            font_path: 字型檔案的絕對路徑
            font_size: 字型大小(點)
            color: 文字顏色 RGB tuple,預設黑色 (0, 0, 0)
            bg_color: 背景顏色 RGB tuple,None 表示透明背景
            padding: 文字周圍的內邊距(像素),預設 0
            fixed_size: 固定畫布尺寸 (width, height),None 表示自動調整

        Returns:
            PIL.Image.Image: 渲染後的圖片(RGB 或 RGBA 模式)

        Raises:
            FileNotFoundError: 字型檔案不存在
            ValueError: font_size <= 0

        Examples:
            >>> adapter = PillowAdapter()
            >>> font = adapter.find_system_font()
            >>> img = adapter.render_text_image("Hello", font, 48)
            >>> img.size  # (width, height)
            (120, 60)  # 實際尺寸依字型而定
        """
        # 驗證參數
        if font_size <= 0:
            raise ValueError(f"font_size must be > 0, got {font_size}")

        if not Path(font_path).exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")

        # 載入字型
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            raise ValueError(f"Failed to load font {font_path}: {e}")

        # 計算文字尺寸(使用 getbbox 獲取準確邊界)
        # 建立臨時畫布來測量文字
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        # 計算畫布尺寸
        if fixed_size:
            canvas_width, canvas_height = fixed_size
        else:
            canvas_width = text_width + 2 * padding
            canvas_height = text_height + 2 * padding

        # 決定圖片模式(透明背景用 RGBA)
        if bg_color is None:
            mode = "RGBA"
            bg = (0, 0, 0, 0)  # 完全透明
        else:
            mode = "RGB"
            bg = bg_color

        # 建立畫布
        img = Image.new(mode, (canvas_width, canvas_height), bg)
        draw = ImageDraw.Draw(img)

        # 計算文字位置(置中)
        text_x = (canvas_width - text_width) // 2
        text_y = (canvas_height - text_height) // 2

        # 渲染文字
        draw.text((text_x, text_y), text, fill=color, font=font)

        return img

    def measure_text_size(
        self, text: str, font_path: str, font_size: int
    ) -> Tuple[int, int]:
        """預測文字渲染後的尺寸(不實際渲染)

        Args:
            text: 要測量的文字內容
            font_path: 字型檔案的絕對路徑
            font_size: 字型大小(點)

        Returns:
            Tuple[int, int]: 文字尺寸 (width, height) 像素

        Raises:
            FileNotFoundError: 字型檔案不存在
            ValueError: font_size <= 0

        Examples:
            >>> adapter = PillowAdapter()
            >>> font = adapter.find_system_font()
            >>> size = adapter.measure_text_size("Hello", font, 48)
            >>> size
            (120, 60)  # 實際尺寸依字型而定
        """
        # 驗證參數
        if font_size <= 0:
            raise ValueError(f"font_size must be > 0, got {font_size}")

        if not Path(font_path).exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")

        # 載入字型
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            raise ValueError(f"Failed to load font {font_path}: {e}")

        # 使用 getbbox 測量文字
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)

        width = int(bbox[2] - bbox[0])
        height = int(bbox[3] - bbox[1])

        return (width, height)

    def find_system_font(self, prefer_cjk: bool = False) -> str:
        """偵測系統可用字型並回傳檔案路徑

        跨平台字型偵測:
        - Windows: C:\\Windows\\Fonts\\
        - macOS: /System/Library/Fonts/, /Library/Fonts/
        - Linux: /usr/share/fonts/

        Args:
            prefer_cjk: 是否優先選擇 CJK(中日韓)字型,預設 False

        Returns:
            str: 字型檔案的絕對路徑

        Raises:
            FileNotFoundError: 找不到任何可用字型

        Examples:
            >>> adapter = PillowAdapter()
            >>> font = adapter.find_system_font()
            >>> font
            'C:\\\\Windows\\\\Fonts\\\\arial.ttf'  # Windows

            >>> cjk_font = adapter.find_system_font(prefer_cjk=True)
            >>> cjk_font
            'C:\\\\Windows\\\\Fonts\\\\msjh.ttc'  # Microsoft JhengHei
        """
        system = platform.system()

        if system == "Windows":
            return self._find_windows_font(prefer_cjk)
        elif system == "Darwin":  # macOS
            return self._find_macos_font(prefer_cjk)
        else:  # Linux and others
            return self._find_linux_font(prefer_cjk)

    def _find_windows_font(self, prefer_cjk: bool) -> str:
        """Windows 字型偵測

        Args:
            prefer_cjk: 是否優先選擇 CJK 字型

        Returns:
            str: 字型檔案路徑

        Raises:
            FileNotFoundError: 找不到任何可用字型
        """
        fonts_dir = Path("C:/Windows/Fonts")

        if prefer_cjk:
            # CJK 字型優先順序
            cjk_fonts = [
                "msjh.ttc",  # Microsoft JhengHei (繁體中文)
                "msyh.ttc",  # Microsoft YaHei (簡體中文)
                "msgothic.ttc",  # MS Gothic (日文)
                "malgun.ttf",  # Malgun Gothic (韓文)
            ]
            for font_name in cjk_fonts:
                font_path = fonts_dir / font_name
                if font_path.exists():
                    return str(font_path)

        # 一般字型(拉丁字元)
        standard_fonts = [
            "arial.ttf",
            "Arial.ttf",
            "times.ttf",
            "calibri.ttf",
        ]
        for font_name in standard_fonts:
            font_path = fonts_dir / font_name
            if font_path.exists():
                return str(font_path)

        raise FileNotFoundError("No suitable font found on Windows")

    def _find_macos_font(self, prefer_cjk: bool) -> str:
        """macOS 字型偵測

        Args:
            prefer_cjk: 是否優先選擇 CJK 字型

        Returns:
            str: 字型檔案路徑

        Raises:
            FileNotFoundError: 找不到任何可用字型
        """
        font_dirs = [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
        ]

        if prefer_cjk:
            # CJK 字型優先順序
            cjk_fonts = [
                "PingFang.ttc",  # 蘋方(繁體/簡體中文)
                "Hiragino Sans GB.ttc",  # 簡體中文
                "AppleGothic.ttf",  # 韓文
            ]
            for font_dir in font_dirs:
                for font_name in cjk_fonts:
                    font_path = font_dir / font_name
                    if font_path.exists():
                        return str(font_path)

        # 一般字型
        standard_fonts = [
            "Arial.ttf",
            "Helvetica.ttc",
            "Times.ttc",
        ]
        for font_dir in font_dirs:
            for font_name in standard_fonts:
                font_path = font_dir / font_name
                if font_path.exists():
                    return str(font_path)

        raise FileNotFoundError("No suitable font found on macOS")

    def _find_linux_font(self, prefer_cjk: bool) -> str:
        """Linux 字型偵測

        Args:
            prefer_cjk: 是否優先選擇 CJK 字型

        Returns:
            str: 字型檔案路徑

        Raises:
            FileNotFoundError: 找不到任何可用字型
        """
        font_dirs = [
            Path("/usr/share/fonts/truetype"),
            Path("/usr/share/fonts/TTF"),
            Path("/usr/local/share/fonts"),
        ]

        if prefer_cjk:
            # CJK 字型優先順序
            cjk_patterns = [
                "**/NotoSansCJK*.ttc",
                "**/DroidSansFallback.ttf",
                "**/wqy-*.ttc",
            ]
            for font_dir in font_dirs:
                if not font_dir.exists():
                    continue
                for pattern in cjk_patterns:
                    matches = list(font_dir.glob(pattern))
                    if matches:
                        return str(matches[0])

        # 一般字型
        standard_patterns = [
            "**/Arial.ttf",
            "**/DejaVuSans.ttf",
            "**/FreeSans.ttf",
        ]
        for font_dir in font_dirs:
            if not font_dir.exists():
                continue
            for pattern in standard_patterns:
                matches = list(font_dir.glob(pattern))
                if matches:
                    return str(matches[0])

        raise FileNotFoundError("No suitable font found on Linux")


# ===== Migrated utility functions from utils.py =====

def _find_system_font(prefer_cjk: bool, size: int):
    """嘗試常見系統字型路徑,返回 PIL ImageFont (truetype) 或預設字型

    此函數按優先順序搜尋系統字型:
    - Windows 字型目錄下的常見字型
    - CJK 字型 (prefer_cjk=True): 微軟正黑體、明體、黑體、宋體
    - 西文字型 (prefer_cjk=False): Arial、Segoe UI、Calibri、Times

    Args:
        prefer_cjk: 是否優先使用 CJK (中日韓) 字型
        size: 字型大小 (像素)

    Returns:
        ImageFont: PIL ImageFont 物件
            - 成功: TrueType 字型
            - 失敗: 預設字型 (load_default)

    Examples:
        >>> # 中文字型
        >>> font = _find_system_font(prefer_cjk=True, size=48)

        >>> # 英文字型
        >>> font = _find_system_font(prefer_cjk=False, size=32)

    Notes:
        - 僅支援 Windows 系統路徑
        - 跨平台支援需額外擴充
        - 字型載入失敗時靜默回退至預設字型

    遷移自: spellvid/utils.py:677
    遷移日期: 2025-01-20
    """
    import os  # Lazy import for this utility function

    candidates = []
    if prefer_cjk:
        # CJK 字型候選清單 (Windows)
        candidates = [
            r"C:\Windows\Fonts\msjh.ttf",      # Microsoft JhengHei (微軟正黑體)
            r"C:\Windows\Fonts\msjhbd.ttf",    # Microsoft JhengHei Bold
            r"C:\Windows\Fonts\mingliu.ttc",   # MingLiU (細明體)
            r"C:\Windows\Fonts\simhei.ttf",    # SimHei (黑體)
            r"C:\Windows\Fonts\simsun.ttc",    # SimSun (宋體)
        ]
    else:
        # 西文字型候選清單 (Windows)
        candidates = [
            r"C:\Windows\Fonts\arial.ttf",     # Arial
            r"C:\Windows\Fonts\segoeui.ttf",   # Segoe UI
            r"C:\Windows\Fonts\calibri.ttf",   # Calibri
            r"C:\Windows\Fonts\times.ttf",     # Times New Roman
        ]

    # 嘗試載入第一個存在的字型檔案
    for p in candidates:
        try:
            if os.path.isfile(p):
                return ImageFont.truetype(p, size)
        except Exception:
            # 字型載入失敗,嘗試下一個
            continue

    # 所有字型都失敗,使用預設字型
    try:
        return ImageFont.load_default()
    except Exception:
        # 極端情況: 預設字型也失敗
        return ImageFont.load_default()


def _measure_text_with_pil(text: str, pil_font: ImageFont.ImageFont):
    """使用 Pillow 測量文字尺寸 (寬度, 高度)

    使用 PIL 的 textbbox 方法精確測量文字渲染後的邊界框尺寸。
    在測量失敗時返回基於字型大小的啟發式估算。

    Args:
        text: 要測量的文字字串
        pil_font: PIL ImageFont 物件 (來自 ImageFont.truetype 或 load_default)

    Returns:
        Tuple[int, int]: (寬度, 高度) 以像素為單位
            - 成功: 基於實際渲染的精確測量
            - 失敗: 啟發式估算 (長度 * 字型大小, 字型大小)

    Examples:
        >>> from PIL import ImageFont
        >>> font = ImageFont.truetype("arial.ttf", 48)
        >>> w, h = _measure_text_with_pil("Hello", font)
        >>> print(f"Text size: {w}x{h}")
        Text size: 120x56

    Notes:
        - 使用 10x10 的臨時圖像進行測量 (不影響結果)
        - textbbox 返回 (left, top, right, bottom)
        - 寬度 = right - left, 高度 = bottom - top
        - 失敗時的啟發式: w = len(text) * font.size, h = font.size

    遷移自: spellvid/utils.py:660
    遷移日期: 2025-01-20
    """
    try:
        # 建立臨時圖像用於測量
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 使用 textbbox 獲取精確邊界框
        bbox = draw.textbbox((0, 0), text, font=pil_font)

        # 計算寬度與高度
        width = bbox[2] - bbox[0]   # right - left
        height = bbox[3] - bbox[1]  # bottom - top

        return width, height
    except Exception:
        # 測量失敗,使用啟發式估算
        # 假設每個字元約佔字型大小的寬度
        font_size = getattr(pil_font, "size", 10)
        estimated_width = int(len(text) * font_size)
        estimated_height = getattr(pil_font, "size", 16)

        return estimated_width, estimated_height


def _make_text_imageclip(
    text: str,
    font_size: int = 48,
    color=(0, 0, 0),
    bg=None,
    duration: float = None,
    prefer_cjk: bool = False,
    extra_bottom: int = 0,
    fixed_size: tuple | None = None,
):
    """使用 Pillow 渲染文字並返回 MoviePy ImageClip

    此函數結合 Pillow 文字渲染與 MoviePy 視頻剪輯功能,是文字轉視頻的核心橋接器。

    功能特性:
    - 自動字型選擇 (支援 CJK 優先)
    - 智能 padding 計算 (基於字型大小)
    - 黑色背景特殊處理 (為倒數計時器保留底部空間)
    - 固定畫布大小 (用於字母群組渲染)
    - MoviePy 整合 (返回 ImageClip 或簡化替代品)

    Args:
        text: 要渲染的文字內容
        font_size: 字型大小 (像素),預設 48
        color: 文字顏色 RGB tuple,預設黑色 (0, 0, 0)
        bg: 背景顏色 RGB tuple,None 表示透明背景
            - None: 透明背景 (RGBA)
            - (0,0,0): 黑色背景 (觸發倒數計時器特殊處理)
        duration: MoviePy clip 時長 (秒),None 表示靜態圖片
        prefer_cjk: 是否優先使用 CJK 字型,預設 False
        extra_bottom: 額外底部空間 (像素),用於下劃線等,預設 0
        fixed_size: 固定畫布尺寸 (width, height),None 表示自動調整
            - 用於字母群組渲染時保持一致尺寸
            - 文字會在固定畫布內靠左上對齊

    Returns:
        ImageClip or _SimpleImageClip: 
            - MoviePy 可用時返回 ImageClip
            - MoviePy 不可用時返回簡化替代品 (測試用)

    Padding 計算邏輯:
        - pad_x = max(12, font_size // 6)  # 水平內邊距
        - pad_y = max(8, font_size // 6)   # 垂直內邊距
        - bottom_safe_margin = extra_bottom + (32 if bg == (0,0,0) else 0)
        - 總尺寸: (w + 2*pad_x) x (h + 2*pad_y + bottom_safe_margin)

    黑色背景特殊處理:
        當 bg=(0,0,0) 時,自動增加 32px 底部空間,防止倒數計時器數字下沿被裁切。

    Examples:
        >>> # 基礎用法: 透明背景文字
        >>> clip = _make_text_imageclip("Hello", font_size=48)

        >>> # 倒數計時器: 黑色背景 + 自動底部空間
        >>> timer = _make_text_imageclip("3.2", font_size=128, bg=(0,0,0))

        >>> # 字母群組: 固定畫布保持對齊
        >>> letter_i = _make_text_imageclip("I", fixed_size=(100, 150))
        >>> letter_c = _make_text_imageclip("Ic", fixed_size=(100, 150))  # 左對齊一致

    Notes:
        - 測試廣泛依賴此函數 (call_count: 50)
        - padding 邏輯需與 domain.layout.compute_layout_bboxes 保持同步
        - MoviePy 不可用時使用最小化替代品 (_SimpleImageClip)
        - 固定畫布模式確保字母子串不因增刪改變位置

    遷移自: spellvid/utils.py:689
    遷移日期: 2025-01-20
    """
    import numpy as np

    # 嘗試載入字型並測量文字尺寸
    try:
        font = _find_system_font(prefer_cjk, font_size)
        w, h = _measure_text_with_pil(text, font)
    except Exception:
        # 字型載入失敗,使用預設字型和啟發式估算
        font = ImageFont.load_default()
        w, h = (int(len(text) * font_size * 0.6), font_size)

    # 計算 padding (基於字型大小,最小值保證可讀性)
    pad_x = max(12, font_size // 6)  # 水平內邊距,至少 12px
    pad_y = max(8, font_size // 6)   # 垂直內邊距,至少 8px

    # 計算底部安全空間
    # - extra_bottom: 呼叫者明確要求的額外空間 (例如 reveal 下劃線)
    # - 黑色背景啟發式: 假設是倒數計時器,需要 32px 防止下沿裁切
    bottom_safe_margin = int(extra_bottom or 0)
    if bg is not None and isinstance(bg, tuple) and len(bg) == 3:
        if bg == (0, 0, 0):  # 黑色背景 = 倒數計時器
            bottom_safe_margin += 32

    # 計算圖片尺寸
    img_w = int(w + pad_x * 2)
    img_h = int(h + pad_y * 2 + bottom_safe_margin)

    # 固定畫布模式: 確保字母子串位置一致
    if fixed_size is not None:
        try:
            fx_w, fx_h = int(fixed_size[0]), int(fixed_size[1])
            # 固定畫布至少要能容納測量的圖片尺寸
            img_w = max(img_w, fx_w)
            img_h = max(img_h, fx_h)
            # 文字靠左上對齊 (pad_x, pad_y),不居中
            # 這確保 "I", "Ic", "Ice" 的 "I" 都在相同位置
            offset_x = 0
            offset_y = 0
        except Exception:
            offset_x = 0
            offset_y = 0
    else:
        offset_x = 0
        offset_y = 0

    # 建立 PIL 圖片
    bg_col = (255, 255, 255, 0) if bg is None else tuple(
        bg) + (255,)  # 加 alpha 通道
    img = Image.new("RGBA", (img_w, img_h), bg_col)
    draw = ImageDraw.Draw(img)

    # 繪製文字 (位置 = padding + offset)
    draw_x = pad_x + offset_x
    draw_y = pad_y + offset_y
    draw.text((draw_x, draw_y), text, font=font, fill=color)

    # 轉換為 numpy array (MoviePy 格式)
    arr = np.array(img)

    # 嘗試使用 MoviePy ImageClip
    try:
        from moviepy import editor as mpy
        clip = mpy.ImageClip(arr)
        if duration is not None:
            clip = clip.with_duration(duration)
        return clip
    except (ImportError, AttributeError):
        pass

    # MoviePy 不可用,使用簡化替代品 (測試用)
    # 最小化實作,滿足測試需要的 API: get_frame, w, h, size, with_duration, duration
    class _SimpleImageClip:
        """MoviePy ImageClip 的最小化替代品 (僅用於測試)"""

        def __init__(self, arr, duration=None):
            self._arr = arr
            self.h = int(arr.shape[0])
            self.w = int(arr.shape[1])
            self.size = (self.w, self.h)
            self._duration = duration

        def get_frame(self, t=0):
            """返回指定時間的幀 (靜態圖片始終返回同一幀)"""
            return self._arr

        def with_duration(self, duration):
            """設置 clip 時長 (鏈式呼叫)"""
            self._duration = duration
            return self

        @property
        def duration(self):
            """Clip 時長 (秒)"""
            return self._duration

    clip = _SimpleImageClip(arr, duration=duration)
    return clip
