from spellvid import utils
import os
import pytest
from PIL import ImageFont


FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msjh.ttf",
    r"C:\Windows\Fonts\msjhbd.ttf",
    r"C:\Windows\Fonts\mingliu.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]



def _resolve_font_path() -> str:
    for candidate in FONT_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    pytest.skip("系統缺少支援 zhuyin 的字型，跳過字體大小測試")



def _compute_zh_font_metrics(ch: str, zh_text: str) -> tuple[int, int]:
    font_path = _resolve_font_path()
    base_font = ImageFont.truetype(font_path, 96)
    _, ch_h = utils._measure_text_with_pil(ch, base_font)
    tone_marks = {"ˊ", "ˇ", "ˋ", "˙"}
    lines = list(zh_text)
    main_syms = [s for s in lines if s not in tone_marks]
    target_base = max(
        utils.ZHUYIN_MIN_FONT_SIZE,
        int(ch_h * utils.ZHUYIN_BASE_HEIGHT_RATIO),
    )
    zh_font_size = min(target_base, int(ch_h))
    while True:
        zh_font = ImageFont.truetype(font_path, zh_font_size)
        total_main_h = 0
        for sym in main_syms if main_syms else lines:
            _, sh = utils._measure_text_with_pil(sym, zh_font)
            total_main_h += sh + 2
        if total_main_h <= ch_h or zh_font_size <= utils.ZHUYIN_MIN_FONT_SIZE:
            break
        zh_font_size -= 1
    return ch_h, zh_font_size


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



def test_zhuyin_animal_map():
    """確認內建注音對照涵蓋常用動物詞彙"""
    res = utils.zhuyin_for("動物")
    assert "ㄉㄨㄥˋ" in res
    assert "ㄨˋ" in res



def test_single_symbol_zhuyin_font_is_capped():
    """單一注音符號時字級應維持與其他字相近"""
    ch_h, zh_size = _compute_zh_font_metrics("物", "ㄨˋ")
    assert zh_size < ch_h
    assert zh_size <= int(ch_h * utils.ZHUYIN_BASE_HEIGHT_RATIO)
    assert zh_size >= utils.ZHUYIN_MIN_FONT_SIZE


def test_zhuyin_neutral_tone_offsets():
    """確認輕聲點會被排在主符號上方並對齊中央。"""
    cursor_y = 10
    col_h = 200
    total_main_h = 120
    tone_syms = ["˙"]
    tone_sizes = [(18, 18)]
    layout = utils._layout_zhuyin_column(
        cursor_y=cursor_y,
        col_h=col_h,
        total_main_h=total_main_h,
        tone_syms=tone_syms,
        tone_sizes=tone_sizes,
    )
    assert layout["tone_alignment"] == "center"
    assert layout["tone_start_y"] is not None
    assert layout["tone_box_height"] == tone_sizes[0][1]
    # tone_start_y + tone_height + 預設間距 (2px) 應該等於 main_start_y
    expected_gap = tone_sizes[0][1] + 2
    assert layout["main_start_y"] == layout["tone_start_y"] + expected_gap
    assert layout["main_start_y"] > layout["tone_start_y"]




def test_zhuyin_main_symbols_align_with_character_top():
    """確認注音主體與中文字頂端對齊。"""
    cursor_y = 12
    col_h = 140
    total_main_h = 100
    layout = utils._layout_zhuyin_column(
        cursor_y=cursor_y,
        col_h=col_h,
        total_main_h=total_main_h,
        tone_syms=[],
        tone_sizes=[],
    )
    assert layout["main_start_y"] == cursor_y
    assert layout["main_start_y"] + total_main_h <= cursor_y + col_h

def test_zhuyin_non_neutral_tone_remains_side_aligned():
    """確認遇到一般聲調時，注音主符仍貼著中文字右側排列，聲調從主符中段向外延伸。"""
    cursor_y = 8
    col_h = 180
    total_main_h = 100
    tone_syms = ["ˊ"]
    tone_sizes = [(16, 20)]
    layout = utils._layout_zhuyin_column(
        cursor_y=cursor_y,
        col_h=col_h,
        total_main_h=total_main_h,
        tone_syms=tone_syms,
        tone_sizes=tone_sizes,
    )
    assert layout["tone_alignment"] == "right"
    assert layout["main_start_y"] == cursor_y
    assert layout["main_start_y"] + total_main_h <= cursor_y + col_h
    assert layout["tone_start_y"] == cursor_y + total_main_h // 2
    assert layout["tone_box_height"] == tone_sizes[0][1]
