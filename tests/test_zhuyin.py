from spellvid import utils


def test_zhuyin_basic():
    """測試 zhuyin 轉換的基本行為。

    對應需求: 顯示注音於畫面（需要一個可用的注音轉換函式）。
    """
    res = utils.zhuyin_for("冰塊")
    assert "ㄅㄧㄥ" in res and "ㄎㄨㄞˋ" in res


def test_beep_stub():
    """synthesize_beeps 應回傳 bytes，作為 beep 音的簡易替代物。

    對應需求: 在倒數時提供簡短 beep（測試使用 stub）。
    """
    b = utils.synthesize_beeps(3, 1)
    assert isinstance(b, (bytes, bytearray)) and len(b) > 0
