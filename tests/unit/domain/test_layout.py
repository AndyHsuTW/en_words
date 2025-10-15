"""單元測試: 佈局計算邏輯

此測試驗證 domain/layout.py 中的佈局計算功能,包括:
- 基本邊界框計算
- 注音排版
- 計時器與進度條處理
- 效能需求 (< 50ms)
"""

import pytest
from spellvid.shared.types import VideoConfig


pytestmark = pytest.mark.unit


class TestComputeLayoutBasic:
    """基本佈局計算測試"""

    def test_compute_layout_basic(self):
        """TC-LAYOUT-001: 驗證基本佈局計算"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
        result = compute_layout_bboxes(config)

        # 驗證邊界框存在且有效
        assert result.letters.width > 0
        assert result.letters.height > 0
        assert result.word_zh.width > 0
        assert result.word_zh.height > 0
        assert result.reveal.width > 0

        # 驗證位置關係
        assert result.letters.x < result.word_zh.x, "字母應在中文左側"
        assert result.letters.right <= 1920
        assert result.word_zh.right <= 1920

    def test_compute_layout_no_overlap(self):
        """TC-LAYOUT-002: 驗證字母與中文區域不重疊"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="ABC abc", word_en="Apple", word_zh="蘋果")
        result = compute_layout_bboxes(config)

        # 使用 LayoutBox.overlaps() 檢查重疊
        assert not result.letters.overlaps(result.word_zh), \
            "字母與中文區域不應重疊"

    def test_compute_layout_within_canvas(self):
        """TC-LAYOUT-003: 驗證所有元素在畫布範圍內"""
        from spellvid.domain.layout import compute_layout_bboxes
        from spellvid.shared.constants import CANVAS_WIDTH, CANVAS_HEIGHT

        test_cases = [
            {"letters": "A a", "word_en": "A", "word_zh": "A"},
            {"letters": "ABC abc", "word_en": "Apple", "word_zh": "蘋果"},
        ]

        for data in test_cases:
            config = VideoConfig(**data)
            result = compute_layout_bboxes(config)

            # 檢查主要邊界框
            for bbox_name in ["letters", "word_zh", "reveal"]:
                bbox = getattr(result, bbox_name)
                assert bbox.x >= 0
                assert bbox.y >= 0
                assert bbox.right <= CANVAS_WIDTH
                assert bbox.bottom <= CANVAS_HEIGHT


class TestZhuyinLayout:
    """注音排版測試"""

    def test_compute_layout_zhuyin_exists(self):
        """TC-LAYOUT-004: 驗證注音符號排版存在"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
        result = compute_layout_bboxes(config)

        # 驗證注音列存在
        assert len(result.zhuyin_columns) >= 1, "應該至少有一個注音列"

    def test_compute_layout_zhuyin_horizontal_order(self):
        """TC-LAYOUT-005: 驗證注音水平排列順序"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A a", word_en="A", word_zh="冰雪")
        result = compute_layout_bboxes(config)

        # 驗證注音從左到右排列
        if len(result.zhuyin_columns) >= 2:
            for i in range(len(result.zhuyin_columns) - 1):
                assert result.zhuyin_columns[i].bbox.x < \
                    result.zhuyin_columns[i+1].bbox.x

    def test_compute_layout_zhuyin_bbox_properties(self):
        """TC-LAYOUT-006: 驗證注音邊界框屬性"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
        result = compute_layout_bboxes(config)

        for col in result.zhuyin_columns:
            assert col.bbox.width > 0
            assert col.bbox.height > 0
            assert col.main_bbox.width > 0
            assert col.main_bbox.height > 0


class TestTimerAndProgressBar:
    """計時器與進度條測試"""

    def test_compute_layout_timer_visible(self):
        """TC-LAYOUT-007: 驗證計時器可見時的佈局"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A a", word_en="A", word_zh="A")
        result = compute_layout_bboxes(config, timer_visible=True)

        assert result.timer is not None, "timer_visible=True 時應該有 timer"
        assert result.timer.width > 0
        assert result.timer.height > 0

    def test_compute_layout_timer_hidden(self):
        """TC-LAYOUT-008: 驗證計時器隱藏時的佈局"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A a", word_en="A", word_zh="A")
        result = compute_layout_bboxes(config, timer_visible=False)

        assert result.timer is None, "timer_visible=False 時不應有 timer"

    def test_compute_layout_progress_bar_y(self):
        """TC-LAYOUT-009: 驗證進度條 Y 座標"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A a", word_en="A", word_zh="A")
        result = compute_layout_bboxes(config, progress_bar=True)

        assert result.progress_bar_y is not None
        assert isinstance(result.progress_bar_y, int)
        assert 0 <= result.progress_bar_y <= 1080


class TestLayoutPerformance:
    """佈局計算效能測試"""

    def test_compute_layout_performance_simple(self):
        """TC-LAYOUT-010: 驗證簡單配置的效能 < 50ms"""
        import time
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A a", word_en="A", word_zh="A")

        start = time.perf_counter()
        result = compute_layout_bboxes(config)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50.0, f"耗時 {elapsed:.2f}ms,超過 50ms 需求"
        assert result.letters.width > 0

    def test_compute_layout_performance_complex(self):
        """TC-LAYOUT-011: 驗證複雜配置的效能 < 50ms"""
        import time
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(
            letters="ABCDEFG abcdefg",
            word_en="Example",
            word_zh="範例測試"
        )

        start = time.perf_counter()
        result = compute_layout_bboxes(config)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50.0, f"耗時 {elapsed:.2f}ms,超過 50ms 需求"
        assert result.letters.width > 0
        assert len(result.zhuyin_columns) >= 4


class TestEdgeCases:
    """邊界情況測試"""

    def test_compute_layout_single_char(self):
        """TC-LAYOUT-012: 驗證單個中文字"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(letters="A", word_en="A", word_zh="冰")
        result = compute_layout_bboxes(config)

        assert result.letters.width > 0
        assert result.word_zh.width > 0

    def test_compute_layout_long_text(self):
        """TC-LAYOUT-013: 驗證長文字"""
        from spellvid.domain.layout import compute_layout_bboxes

        config = VideoConfig(
            letters="ABCDEFGHIJ abcdefghij",
            word_en="VeryLongWord",
            word_zh="非常長的中文詞彙"
        )
        result = compute_layout_bboxes(config)

        assert result.letters.width > 0
        assert result.word_zh.width > 0


class TestExtractChineseChars:
    """extract_chinese_chars 函數測試"""

    def test_extract_mixed_text(self):
        """驗證從混合文字提取中文字"""
        from spellvid.domain.layout import extract_chinese_chars

        assert extract_chinese_chars("ㄅㄧㄥ 冰") == ["冰"]
        assert extract_chinese_chars("ㄒㄩㄝˊ 雪") == ["雪"]

    def test_extract_multiple_chars(self):
        """驗證提取多個中文字"""
        from spellvid.domain.layout import extract_chinese_chars

        assert extract_chinese_chars("冰雪") == ["冰", "雪"]
        assert extract_chinese_chars("你好世界") == ["你", "好", "世", "界"]

    def test_extract_no_chinese(self):
        """驗證無中文字時回傳空列表"""
        from spellvid.domain.layout import extract_chinese_chars

        assert extract_chinese_chars("ABC 123") == []
        assert extract_chinese_chars("") == []
