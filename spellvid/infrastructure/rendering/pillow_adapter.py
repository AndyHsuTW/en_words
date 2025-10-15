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
