"""單元測試: shared/types.py - VideoConfig 與 LayoutBox

測試目標:
- VideoConfig 資料類別的建立、驗證與轉換
- LayoutBox 值物件的不可變性與邊界檢測

遵循 TDD 原則: 這些測試在實作前應該失敗
"""

import pytest


# === TC-SHARED-001: VideoConfig.from_dict() 正常轉換 ===

def test_videoconfig_from_dict_valid():
    """驗證從字典正確建立 VideoConfig

    測試案例: TC-SHARED-001
    前置條件: 提供包含必填欄位的字典
    預期結果: 正確建立 VideoConfig 實例,可選欄位填入預設值
    """
    from spellvid.shared.types import VideoConfig

    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "countdown_sec": 5.0
    }
    config = VideoConfig.from_dict(data)

    assert config.letters == "I i"
    assert config.word_en == "Ice"
    assert config.word_zh == "冰"
    assert config.countdown_sec == 5.0
    assert config.timer_visible is True  # 預設值
    assert config.progress_bar is True  # 預設值


def test_videoconfig_from_dict_minimal():
    """驗證僅必填欄位也能正確建立 VideoConfig

    測試案例: TC-SHARED-001 變體
    前置條件: 僅提供必填欄位 (letters, word_en, word_zh)
    預期結果: 其他欄位使用預設值
    """
    from spellvid.shared.types import VideoConfig

    data = {
        "letters": "A a",
        "word_en": "Apple",
        "word_zh": "蘋果"
    }
    config = VideoConfig.from_dict(data)

    assert config.letters == "A a"
    assert config.word_en == "Apple"
    assert config.word_zh == "蘋果"
    assert config.countdown_sec == 3.0  # 預設值
    assert config.reveal_hold_sec == 2.0  # 預設值
    assert config.timer_visible is True


# === TC-SHARED-002: VideoConfig.from_dict() 缺少必填欄位 ===

def test_videoconfig_from_dict_missing_required():
    """驗證缺少必填欄位時拋出異常

    測試案例: TC-SHARED-002
    前置條件: 字典缺少必填欄位
    預期結果: 拋出 TypeError (dataclass 缺少參數)
    """
    from spellvid.shared.types import VideoConfig

    data = {"letters": "A a"}  # 缺少 word_en, word_zh

    with pytest.raises(TypeError):
        VideoConfig.from_dict(data)


def test_videoconfig_from_dict_missing_letters():
    """驗證缺少 letters 欄位時拋出異常"""
    from spellvid.shared.types import VideoConfig

    data = {"word_en": "Apple", "word_zh": "蘋果"}  # 缺少 letters

    with pytest.raises(TypeError):
        VideoConfig.from_dict(data)


# === TC-SHARED-003: VideoConfig 驗證規則 ===

def test_videoconfig_validation_negative_countdown():
    """驗證 countdown_sec 不可為負數

    測試案例: TC-SHARED-003
    前置條件: countdown_sec < 0
    預期結果: 拋出 ValueError
    """
    from spellvid.shared.types import VideoConfig

    with pytest.raises(ValueError, match="countdown_sec"):
        VideoConfig(
            letters="A",
            word_en="A",
            word_zh="A",
            countdown_sec=-1  # 無效
        )


def test_videoconfig_validation_invalid_video_mode():
    """驗證 video_mode 必須是 'cover' 或 'fit'

    測試案例: TC-SHARED-003
    前置條件: video_mode 不是有效值
    預期結果: 拋出 ValueError
    """
    from spellvid.shared.types import VideoConfig

    with pytest.raises(ValueError, match="video_mode"):
        VideoConfig(
            letters="A",
            word_en="A",
            word_zh="A",
            video_mode="invalid"  # 無效
        )


def test_videoconfig_validation_both_image_and_video():
    """驗證 image_path 與 video_path 不可同時設定

    測試案例: TC-SHARED-003
    前置條件: 同時提供 image_path 和 video_path
    預期結果: 拋出 ValueError
    """
    from spellvid.shared.types import VideoConfig

    with pytest.raises(ValueError, match="image_path.*video_path"):
        VideoConfig(
            letters="A",
            word_en="A",
            word_zh="A",
            image_path="a.png",
            video_path="b.mp4"  # 不可同時存在
        )


def test_videoconfig_to_dict_roundtrip():
    """驗證 to_dict() 可進行往返轉換

    測試案例: TC-SHARED-001 延伸
    前置條件: 建立 VideoConfig 實例
    預期結果: to_dict() → from_dict() 可還原
    """
    from spellvid.shared.types import VideoConfig

    original = VideoConfig(
        letters="I i",
        word_en="Ice",
        word_zh="冰",
        countdown_sec=5.0,
        timer_visible=False
    )

    data = original.to_dict()
    restored = VideoConfig.from_dict(data)

    assert restored.letters == original.letters
    assert restored.word_en == original.word_en
    assert restored.word_zh == original.word_zh
    assert restored.countdown_sec == original.countdown_sec
    assert restored.timer_visible == original.timer_visible


# === TC-SHARED-004: LayoutBox 不可變性 ===

def test_layoutbox_immutable():
    """驗證 LayoutBox 為不可變值物件

    測試案例: TC-SHARED-004
    前置條件: 建立 LayoutBox 實例
    預期結果: 無法修改屬性 (frozen=True)
    """
    from spellvid.shared.types import LayoutBox

    box = LayoutBox(x=10, y=20, width=100, height=50)

    with pytest.raises(AttributeError):
        box.x = 99  # frozen=True 禁止修改


def test_layoutbox_properties():
    """驗證 LayoutBox 的計算屬性

    測試案例: TC-SHARED-004 延伸
    前置條件: 建立 LayoutBox 實例
    預期結果: right, bottom, center_x, center_y 計算正確
    """
    from spellvid.shared.types import LayoutBox

    box = LayoutBox(x=10, y=20, width=100, height=50)

    assert box.right == 110  # x + width
    assert box.bottom == 70  # y + height
    assert box.center_x == 60  # x + width // 2
    assert box.center_y == 45  # y + height // 2


def test_layoutbox_validation_positive_dimensions():
    """驗證 LayoutBox 尺寸必須為正數

    測試案例: TC-SHARED-004
    前置條件: width 或 height <= 0
    預期結果: 拋出 ValueError
    """
    from spellvid.shared.types import LayoutBox

    with pytest.raises(ValueError, match="width.*height"):
        LayoutBox(x=0, y=0, width=0, height=100)

    with pytest.raises(ValueError, match="width.*height"):
        LayoutBox(x=0, y=0, width=100, height=-10)


def test_layoutbox_validation_non_negative_position():
    """驗證 LayoutBox 位置不可為負數

    測試案例: TC-SHARED-004
    前置條件: x 或 y < 0
    預期結果: 拋出 ValueError
    """
    from spellvid.shared.types import LayoutBox

    with pytest.raises(ValueError, match="x.*y"):
        LayoutBox(x=-10, y=0, width=100, height=100)

    with pytest.raises(ValueError, match="x.*y"):
        LayoutBox(x=0, y=-10, width=100, height=100)


# === TC-SHARED-005: LayoutBox.overlaps() 正確檢測 ===

def test_layoutbox_overlaps_true():
    """驗證邊界框重疊檢測 - 重疊情況

    測試案例: TC-SHARED-005
    前置條件: 兩個邊界框部分重疊
    預期結果: overlaps() 回傳 True
    """
    from spellvid.shared.types import LayoutBox

    box1 = LayoutBox(x=0, y=0, width=100, height=100)
    box2 = LayoutBox(x=50, y=50, width=100, height=100)

    assert box1.overlaps(box2) is True
    assert box2.overlaps(box1) is True  # 對稱性


def test_layoutbox_overlaps_false():
    """驗證邊界框重疊檢測 - 不重疊情況

    測試案例: TC-SHARED-005
    前置條件: 兩個邊界框完全分離
    預期結果: overlaps() 回傳 False
    """
    from spellvid.shared.types import LayoutBox

    box1 = LayoutBox(x=0, y=0, width=100, height=100)
    box3 = LayoutBox(x=200, y=200, width=100, height=100)

    assert box1.overlaps(box3) is False
    assert box3.overlaps(box1) is False


def test_layoutbox_overlaps_edge_touching():
    """驗證邊界框邊緣相接不算重疊

    測試案例: TC-SHARED-005
    前置條件: 兩個邊界框邊緣相接但不重疊
    預期結果: overlaps() 回傳 False
    """
    from spellvid.shared.types import LayoutBox

    box1 = LayoutBox(x=0, y=0, width=100, height=100)
    box2 = LayoutBox(x=100, y=0, width=100, height=100)  # 右邊緊鄰

    assert box1.overlaps(box2) is False


def test_layoutbox_overlaps_fully_contained():
    """驗證完全包含的邊界框算重疊

    測試案例: TC-SHARED-005
    前置條件: 一個邊界框完全包含另一個
    預期結果: overlaps() 回傳 True
    """
    from spellvid.shared.types import LayoutBox

    box1 = LayoutBox(x=0, y=0, width=200, height=200)
    box2 = LayoutBox(x=50, y=50, width=50, height=50)  # 完全在 box1 內

    assert box1.overlaps(box2) is True
    assert box2.overlaps(box1) is True
