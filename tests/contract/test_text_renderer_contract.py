"""契約測試: ITextRenderer Protocol

此測試驗證文字渲染引擎適配器是否正確實作 ITextRenderer Protocol。

測試策略:
1. 驗證適配器實作 Protocol
2. 驗證所有方法存在且可呼叫
3. 驗證方法回傳值符合契約要求
"""

import pytest


class TestTextRendererContract:
    """ITextRenderer Protocol 契約測試套件

    驗證 PillowAdapter 是否符合 ITextRenderer 介面定義。
    """

    def test_pillow_adapter_implements_interface(self):
        """TC-CONTRACT-010: 驗證 PillowAdapter 實作 ITextRenderer

        測試案例: Protocol 符合性檢查
        前置條件: ITextRenderer 已定義為 @runtime_checkable Protocol
        預期結果: isinstance(adapter, ITextRenderer) 回傳 True
        """
        from spellvid.infrastructure.rendering.interface import (
            ITextRenderer,
        )
        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()

        assert isinstance(adapter, ITextRenderer), \
            "PillowAdapter 必須實作 ITextRenderer Protocol"

    def test_adapter_has_required_methods(self):
        """TC-CONTRACT-011: 驗證 PillowAdapter 實作所有必要方法

        測試案例: 方法完整性
        前置條件: PillowAdapter 已實作
        預期結果: adapter 具有 3 個方法
        """
        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()

        required_methods = [
            'render_text_image',
            'measure_text_size',
            'find_system_font'
        ]

        for method_name in required_methods:
            assert hasattr(adapter, method_name), \
                f"PillowAdapter 缺少 {method_name} 方法"
            assert callable(getattr(adapter, method_name)), \
                f"PillowAdapter.{method_name} 必須可呼叫"

    def test_render_text_image_returns_pil_image(self):
        """TC-CONTRACT-012: 驗證 render_text_image 回傳 PIL Image

        測試案例: 回傳值型別檢查
        前置條件: PillowAdapter.render_text_image 已實作
        預期結果: 回傳 PIL.Image.Image 物件
        """
        from PIL import Image

        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()

        # 使用系統字型渲染文字
        font_path = adapter.find_system_font()
        img = adapter.render_text_image(
            text="Test",
            font_path=font_path,
            font_size=48,
            color=(0, 0, 0)
        )

        assert isinstance(img, Image.Image), \
            "render_text_image 必須回傳 PIL.Image.Image"
        assert img.width > 0, "渲染的圖片寬度必須 > 0"
        assert img.height > 0, "渲染的圖片高度必須 > 0"

    def test_measure_text_size_returns_tuple(self):
        """TC-CONTRACT-013: 驗證 measure_text_size 回傳尺寸 tuple

        測試案例: 回傳值型別檢查
        前置條件: PillowAdapter.measure_text_size 已實作
        預期結果: 回傳 (width, height) tuple
        """
        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()

        font_path = adapter.find_system_font()
        size = adapter.measure_text_size(
            text="Test",
            font_path=font_path,
            font_size=48
        )

        assert isinstance(size, tuple), "measure_text_size 必須回傳 tuple"
        assert len(size) == 2, \
            "回傳的 tuple 必須有 2 個元素 (width, height)"
        assert size[0] > 0, "文字寬度必須 > 0"
        assert size[1] > 0, "文字高度必須 > 0"

    def test_find_system_font_returns_valid_path(self):
        """TC-CONTRACT-014: 驗證 find_system_font 回傳有效路徑

        測試案例: 回傳值有效性檢查
        前置條件: PillowAdapter.find_system_font 已實作
        預期結果: 回傳存在的字型檔案路徑
        """
        from pathlib import Path

        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()

        # 尋找一般字型
        font_path = adapter.find_system_font(prefer_cjk=False)
        assert isinstance(font_path, str), "find_system_font 必須回傳字串"
        assert Path(font_path).exists(), "回傳的字型檔案必須存在"

        # 尋找 CJK 字型
        cjk_font_path = adapter.find_system_font(prefer_cjk=True)
        assert Path(cjk_font_path).exists(), "CJK 字型檔案必須存在"

    def test_render_with_different_parameters(self):
        """TC-CONTRACT-015: 驗證 render_text_image 接受各種參數組合

        測試案例: 參數彈性檢查
        前置條件: PillowAdapter.render_text_image 已實作
        預期結果: 支援可選參數(bg_color, padding, fixed_size)
        """
        from PIL import Image

        from spellvid.infrastructure.rendering.pillow_adapter import (
            PillowAdapter,
        )

        adapter = PillowAdapter()
        font_path = adapter.find_system_font()

        # 測試不同參數組合
        img1 = adapter.render_text_image("Test", font_path, 48)
        assert isinstance(img1, Image.Image)

        img2 = adapter.render_text_image(
            "Test", font_path, 48,
            bg_color=(255, 255, 255),
            padding=10
        )
        assert isinstance(img2, Image.Image)

        img3 = adapter.render_text_image(
            "Test", font_path, 48,
            fixed_size=(200, 100)
        )
        assert isinstance(img3, Image.Image)
        assert img3.size == (200, 100), "fixed_size 應該設定圖片尺寸"


# 標記此測試模組為契約測試
pytestmark = pytest.mark.contract
