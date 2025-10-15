"""文字渲染引擎介面定義

此模組定義 ITextRenderer Protocol,抽象化圖片處理庫(如 Pillow)的文字渲染功能。

設計原則:
- Protocol 定義純粹的文字渲染行為
- 回傳 PIL.Image.Image 作為標準格式
- 支援字型查找、尺寸測量等輔助功能
"""

from typing import Protocol, Tuple, Optional, runtime_checkable
from PIL import Image


@runtime_checkable
class ITextRenderer(Protocol):
    """文字渲染引擎介面

    此 Protocol 定義文字轉圖片的功能,隱藏底層圖片處理庫的細節。

    實作者:
        - PillowAdapter: 當前使用的 Pillow 適配器

    座標系統:
        所有尺寸和位置使用像素為單位,左上角為 (0, 0)
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

        將文字繪製到 PIL Image 物件,可設定字型、顏色、背景等。

        Args:
            text: 要渲染的文字內容
            font_path: 字型檔案絕對路徑(.ttf 或 .otf)
            font_size: 字型大小,單位像素
            color: 文字顏色 (R, G, B),範圍 0-255,預設黑色
            bg_color: 背景顏色 (R, G, B),None 表示透明背景
            padding: 內距,單位像素,四周均勻留白
            fixed_size: 固定圖片尺寸 (width, height),None 表示自動適應文字

        Returns:
            PIL.Image.Image 物件,模式為 RGB 或 RGBA

        Raises:
            FileNotFoundError: 字型檔案不存在
            ValueError: font_size <= 0

        Example:
            >>> img = renderer.render_text_image(
            ...     "Hello", "/path/to/font.ttf", 48,
            ...     color=(0, 0, 0),
            ...     bg_color=(255, 255, 255),
            ...     padding=10
            ... )
            >>> img.size
            (120, 68)  # 視文字內容而定
        """
        ...

    def measure_text_size(
        self,
        text: str,
        font_path: str,
        font_size: int
    ) -> Tuple[int, int]:
        """測量文字渲染後的尺寸

        在不實際繪製的情況下計算文字佔據的像素尺寸。
        用於佈局計算階段,預估元素大小。

        Args:
            text: 要測量的文字
            font_path: 字型檔案絕對路徑
            font_size: 字型大小,單位像素

        Returns:
            (width, height) 像素尺寸 tuple

        Raises:
            FileNotFoundError: 字型檔案不存在

        Example:
            >>> w, h = renderer.measure_text_size("Test", "/path/font.ttf", 48)
            >>> print(f"文字將佔據 {w}x{h} 像素")
        """
        ...

    def find_system_font(
        self,
        prefer_cjk: bool = False
    ) -> str:
        """尋找系統可用的字型

        自動偵測作業系統並回傳可用的字型檔案路徑。
        用於沒有指定字型時的 fallback 機制。

        Args:
            prefer_cjk: 是否優先尋找中日韓(CJK)字型,預設 False

        Returns:
            字型檔案絕對路徑

        Raises:
            FileNotFoundError: 找不到任何可用字型

        Example:
            >>> # Windows 環境
            >>> font_path = renderer.find_system_font(prefer_cjk=True)
            >>> font_path
            'C:\\Windows\\Fonts\\msjh.ttc'  # Microsoft JhengHei

            >>> # 一般拉丁字型
            >>> font_path = renderer.find_system_font(prefer_cjk=False)
            >>> font_path
            'C:\\Windows\\Fonts\\arial.ttf'

        Note:
            實作應該處理多種作業系統(Windows, macOS, Linux)
            的字型路徑差異。
        """
        ...
