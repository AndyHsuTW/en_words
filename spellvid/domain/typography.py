"""注音處理模組

此模組負責中文字與注音符號的轉換與處理,是純粹的領域邏輯層。

職責:
- 中文字轉注音符號查詢
- 注音字串符號分割(主要符號 vs 聲調)
- 中文字元判斷

使用:
    from spellvid.domain.typography import zhuyin_for, split_zhuyin_symbols
    
    zhuyin = zhuyin_for("冰")  # "ㄅㄧㄥ"
    main, tone = split_zhuyin_symbols(zhuyin)  # (["ㄅ", "ㄧ", "ㄥ"], None)
"""

import re
from typing import List, Optional, Tuple


# ========== 注音對應表 ==========

# 基礎注音對應表(常用字)
# 完整版本應使用 pypinyin 或更完整的資料庫
_ZHUYIN_MAP = {
    "冰": "ㄅㄧㄥ",
    "塊": "ㄎㄨㄞˋ",
    "動": "ㄉㄨㄥˋ",
    "物": "ㄨˋ",
    "雪": "ㄒㄩㄝˇ",
    "山": "ㄕㄢ",
    "水": "ㄕㄨㄟˇ",
    "火": "ㄏㄨㄛˇ",
    "是": "ㄕˋ",
    "蘋": "ㄆㄧㄥˊ",
    "果": "ㄍㄨㄛˇ",
    "範": "ㄈㄢˋ",
    "例": "ㄌㄧˋ",
    "測": "ㄘㄜˋ",
    "試": "ㄕˋ",
    "你": "ㄋㄧˇ",
    "好": "ㄏㄠˇ",
    "世": "ㄕˋ",
    "界": "ㄐㄧㄝˋ",
    "單": "ㄉㄢ",
    "詞": "ㄘˊ",
    "字": "ㄗˋ",
    "母": "ㄇㄨˇ",
    "表": "ㄅㄧㄠˇ",
    "台": "ㄊㄞˊ",
    "臺": "ㄊㄞˊ",
}

# 聲調符號集合
_TONE_MARKS = {"ˊ", "ˇ", "ˋ", "˙"}

# 注音主要符號範圍 (Unicode)
# ㄅ到ㄩ: U+3105 到 U+3129
_ZHUYIN_PATTERN = re.compile(r"[\u3105-\u3129]")


# ========== 公開 API ==========


def zhuyin_for(chinese_char: str) -> Optional[str]:
    """查詢單一中文字的注音符號

    Args:
        chinese_char: 單一中文字元

    Returns:
        對應的注音符號字串,若查無對應則回傳 None

    Performance:
        查詢時間 < 1ms (字典查詢)

    Examples:
        >>> zhuyin_for("冰")
        'ㄅㄧㄥ'
        >>> zhuyin_for("雪")
        'ㄒㄩㄝˊ'
        >>> zhuyin_for("A")
        None
    """
    # 驗證輸入
    if not chinese_char or len(chinese_char) != 1:
        return None

    if not is_chinese_char(chinese_char):
        return None

    # 優先使用 pypinyin (如果可用)
    try:
        from pypinyin import pinyin, Style

        result = pinyin(
            chinese_char,
            style=Style.BOPOMOFO,
            heteronym=False,
            errors="ignore",
        )

        if result and result[0] and result[0][0]:
            return result[0][0]
    except (ImportError, Exception):
        # pypinyin 不可用或失敗,使用內部對應表
        pass

    # 回退至內部對應表
    return _ZHUYIN_MAP.get(chinese_char)


def split_zhuyin_symbols(zhuyin: str) -> Tuple[List[str], Optional[str]]:
    """分割注音字串為主要符號與聲調

    Args:
        zhuyin: 注音字串(如 "ㄅㄧㄥ" 或 "ㄒㄩㄝˊ")

    Returns:
        (主要符號列表, 聲調符號或None)

    Examples:
        >>> split_zhuyin_symbols("ㄅㄧㄥ")
        (['ㄅ', 'ㄧ', 'ㄥ'], None)
        >>> split_zhuyin_symbols("ㄒㄩㄝˊ")
        (['ㄒ', 'ㄩ', 'ㄝ'], 'ˊ')
        >>> split_zhuyin_symbols("ㄕˋ")
        (['ㄕ'], 'ˋ')
    """
    if not zhuyin:
        return ([], None)

    # 找出所有主要注音符號
    main_symbols = _ZHUYIN_PATTERN.findall(zhuyin)

    # 找出聲調符號(應該只有一個)
    tone_symbol = None
    for char in zhuyin:
        if char in _TONE_MARKS:
            tone_symbol = char
            break  # 只取第一個聲調符號

    return (main_symbols, tone_symbol)


def is_chinese_char(char: str) -> bool:
    """判斷是否為中文字元

    Args:
        char: 單一字元

    Returns:
        True 若為中文字元,否則 False

    Examples:
        >>> is_chinese_char("冰")
        True
        >>> is_chinese_char("A")
        False
        >>> is_chinese_char("ㄅ")
        False
    """
    if not char or len(char) != 1:
        return False

    # 中文字 Unicode 範圍: U+4E00 到 U+9FFF (CJK Unified Ideographs)
    code_point = ord(char)
    return 0x4E00 <= code_point <= 0x9FFF


# ========== 內部輔助函數 ==========


def _zhuyin_main_gap(symbol_count: int) -> int:
    """計算注音符號之間的垂直間距

    當注音符號需要垂直排列時使用。

    Args:
        symbol_count: 符號數量

    Returns:
        間距像素值
    """
    if symbol_count <= 1:
        return 0
    if symbol_count == 2:
        return 12  # 兩個符號間距較大
    return 8  # 三個以上符號間距較小
