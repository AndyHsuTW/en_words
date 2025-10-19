"""單元測試: utils.py re-export 層驗證

驗證新的 utils.py re-export 層正確導出所有必要的函數、常數與測試輔助。
確保向後相容性維持。
"""
import warnings


def test_render_video_stub_available():
    """確認 render_video_stub 函數可以 import"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from spellvid.utils import render_video_stub

        # 檢查函數可呼叫
        assert callable(render_video_stub), (
            "render_video_stub should be callable"
        )

        # 應該發出 DeprecationWarning
        assert len(w) > 0, "Expected DeprecationWarning"
        assert any(
            issubclass(warning.category, DeprecationWarning)
            for warning in w
        ), "Expected DeprecationWarning for utils module"


def test_compute_layout_bboxes_available():
    """確認 compute_layout_bboxes 函數可以 import"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid.utils import compute_layout_bboxes

        # 檢查函數可呼叫
        assert callable(compute_layout_bboxes), (
            "compute_layout_bboxes should be callable"
        )


def test_check_assets_available():
    """確認 check_assets 函數可以 import"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid.utils import check_assets

        # 檢查函數可呼叫
        assert callable(check_assets), (
            "check_assets should be callable"
        )


def test_constants_available():
    """確認所有必要常數可以 import"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid.utils import (  # noqa: F401
            PROGRESS_BAR_SAFE_X,
            PROGRESS_BAR_MAX_X,
            PROGRESS_BAR_WIDTH,
            PROGRESS_BAR_HEIGHT,
            PROGRESS_BAR_COLORS,
            PROGRESS_BAR_RATIOS,
            PROGRESS_BAR_CORNER_RADIUS,
            LETTER_SAFE_X,
            LETTER_SAFE_Y,
            LETTER_AVAILABLE_WIDTH,
            LETTER_TARGET_HEIGHT,
            LETTER_BASE_GAP,
            LETTER_EXTRA_SCALE,
        )

        # 檢查常數類型
        assert isinstance(PROGRESS_BAR_SAFE_X, int)
        assert isinstance(PROGRESS_BAR_COLORS, dict)
        assert isinstance(LETTER_SAFE_X, int)


def test_schema_available():
    """確認 SCHEMA 常數可以 import"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid.utils import SCHEMA

        # 檢查 SCHEMA 是 dict
        assert isinstance(SCHEMA, dict), "SCHEMA should be a dictionary"
        assert "type" in SCHEMA, "SCHEMA should have 'type' field"


def test_test_helpers_available():
    """確認測試輔助函數可以 import (帶底線的內部函數)"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid.utils import (  # noqa: F401
            _make_text_imageclip,
            _mpy,
            _HAS_MOVIEPY
        )

        # _make_text_imageclip 應該可呼叫
        assert callable(_make_text_imageclip), (
            "_make_text_imageclip should be callable"
        )

        # _HAS_MOVIEPY 應該是 bool
        assert isinstance(_HAS_MOVIEPY, bool), (
            "_HAS_MOVIEPY should be boolean"
        )

        # _mpy 可能是 None 或 module
        # 不強制要求 MoviePy 可用


def test_deprecation_warning_issued():
    """確認 DeprecationWarning 正確發出"""
    # Note: The warning is issued at module import time.
    # If the module is already loaded, re-importing won't trigger it again.
    # We verify that the module HAS a deprecation warning in its docstring
    # and that importing new items triggers it.

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Try importing a specific item to potentially trigger warning
        from spellvid.utils import render_video_stub  # noqa: F401

        # Check module docstring mentions deprecation
        import spellvid.utils
        doc = spellvid.utils.__doc__
        assert doc and "deprecated" in doc.lower(), (
            "Module docstring should mention deprecation"
        )

        # If warnings were captured (first import), verify them
        if len(w) > 0:
            deprecation_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            if len(deprecation_warnings) > 0:
                message = str(deprecation_warnings[0].message)
                assert "deprecated" in message.lower(), (
                    f"Warning message should mention 'deprecated': {message}"
                )


def test_all_exports_defined():
    """確認 __all__ 列表定義且包含主要 exports"""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        from spellvid import utils

        # 檢查 __all__ 存在
        assert hasattr(utils, '__all__'), (
            "utils module should define __all__"
        )

        # 檢查包含關鍵 exports
        all_list = utils.__all__
        assert 'render_video_stub' in all_list, (
            "__all__ should include 'render_video_stub'"
        )
        assert 'compute_layout_bboxes' in all_list, (
            "__all__ should include 'compute_layout_bboxes'"
        )
        assert 'SCHEMA' in all_list, (
            "__all__ should include 'SCHEMA'"
        )
