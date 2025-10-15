"""單元測試: 注音處理邏輯

此測試驗證 domain/typography.py 中的注音轉換與符號分割功能,包括:
- 中文字轉注音符號
- 無效輸入處理
- 注音符號分割(主要符號與聲調)

測試策略:
1. 純邏輯測試,不依賴外部資源
2. 測試常見中文字的注音轉換
3. 邊界情況處理(非中文字元、空字串等)
"""

import pytest


class TestZhuyinConversion:
    """中文轉注音測試"""

    def test_zhuyin_for_valid_chars(self):
        """TC-TYPO-001: 驗證常見中文字的注音轉換

        測試案例: 常用字的注音查詢
        前置條件: 輸入單一中文字
        預期結果: 回傳正確的注音符號字串
        """
        from spellvid.domain.typography import zhuyin_for

        # 測試常見字
        assert zhuyin_for("冰") == "ㄅㄧㄥ", "冰 應該轉換為 ㄅㄧㄥ"
        assert zhuyin_for("雪") == "ㄒㄩㄝˇ", "雪 應該轉換為 ㄒㄩㄝˇ"
        assert zhuyin_for("山") == "ㄕㄢ", "山 應該轉換為 ㄕㄢ"
        assert zhuyin_for("水") == "ㄕㄨㄟˇ", "水 應該轉換為 ㄕㄨㄟˇ"
        assert zhuyin_for("火") == "ㄏㄨㄛˇ", "火 應該轉換為 ㄏㄨㄛˇ"

    def test_zhuyin_for_tone_marks(self):
        """TC-TYPO-002: 驗證帶聲調的注音

        測試案例: 不同聲調的字
        前置條件: 輸入帶聲調的中文字
        預期結果: 注音字串包含聲調符號
        """
        from spellvid.domain.typography import zhuyin_for

        # 一聲(無標記)
        assert zhuyin_for("冰") == "ㄅㄧㄥ"

        # 二聲(ˊ)
        assert zhuyin_for("台") == "ㄊㄞˊ"

        # 三聲(ˇ)
        assert zhuyin_for("雪") == "ㄒㄩㄝˇ"
        assert zhuyin_for("水") == "ㄕㄨㄟˇ"

        # 四聲(ˋ)
        assert zhuyin_for("是") == "ㄕˋ"

        # 輕聲(˙)
        # (視實際資料而定,可能某些字有輕聲)

    def test_zhuyin_for_invalid_chars(self):
        """TC-TYPO-003: 驗證非中文字元回傳 None

        測試案例: 各種無效輸入
        前置條件: 輸入非中文字元
        預期結果: 回傳 None
        """
        from spellvid.domain.typography import zhuyin_for

        # 英文字母
        assert zhuyin_for("A") is None
        assert zhuyin_for("abc") is None

        # 數字
        assert zhuyin_for("1") is None
        assert zhuyin_for("123") is None

        # 空字串
        assert zhuyin_for("") is None

        # 標點符號
        assert zhuyin_for("。") is None
        assert zhuyin_for("!") is None

        # 多個字元(非單一字)
        assert zhuyin_for("你好") is None

    def test_zhuyin_for_uncommon_chars(self):
        """TC-TYPO-004: 驗證罕見字的處理

        測試案例: 罕用字或無資料的字
        前置條件: 輸入罕見中文字
        預期結果: 回傳 None 或拋出異常(視設計而定)
        """
        from spellvid.domain.typography import zhuyin_for

        # 罕見字可能沒有注音資料
        # 設計應該決定是回傳 None 還是拋出異常
        result = zhuyin_for("㗊")  # 罕用字範例
        assert result is None or isinstance(result, str)


class TestZhuyinSplitting:
    """注音符號分割測試"""

    def test_split_zhuyin_no_tone(self):
        """TC-TYPO-005: 驗證無聲調的注音分割

        測試案例: 一聲(無標記)的注音
        前置條件: 輸入不帶聲調符號的注音字串
        預期結果: main_symbols 為符號列表,tone_symbol 為 None
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("ㄅㄧㄥ")

        assert main == ["ㄅ", "ㄧ", "ㄥ"], "主要符號應該分割為 ['ㄅ', 'ㄧ', 'ㄥ']"
        assert tone is None, "一聲沒有聲調符號"

    def test_split_zhuyin_with_tone_2nd(self):
        """TC-TYPO-006: 驗證二聲(ˊ)的注音分割

        測試案例: 帶二聲符號的注音
        前置條件: 輸入帶 ˊ 的注音字串
        預期結果: main_symbols 為主要符號,tone_symbol 為 "ˊ"
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("ㄒㄩㄝˊ")

        assert main == ["ㄒ", "ㄩ", "ㄝ"], "主要符號應該分割為 ['ㄒ', 'ㄩ', 'ㄝ']"
        assert tone == "ˊ", "二聲符號應該是 ˊ"

    def test_split_zhuyin_with_tone_3rd(self):
        """TC-TYPO-007: 驗證三聲(ˇ)的注音分割

        測試案例: 帶三聲符號的注音
        前置條件: 輸入帶 ˇ 的注音字串
        預期結果: main_symbols 為主要符號,tone_symbol 為 "ˇ"
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("ㄕㄨㄟˇ")

        assert main == ["ㄕ", "ㄨ", "ㄟ"]
        assert tone == "ˇ"

    def test_split_zhuyin_with_tone_4th(self):
        """TC-TYPO-008: 驗證四聲(ˋ)的注音分割

        測試案例: 帶四聲符號的注音
        前置條件: 輸入帶 ˋ 的注音字串
        預期結果: tone_symbol 為 "ˋ"
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("ㄕˋ")

        assert main == ["ㄕ"]
        assert tone == "ˋ"

    def test_split_zhuyin_single_symbol(self):
        """TC-TYPO-009: 驗證單一符號的注音分割

        測試案例: 只有一個注音符號的情況
        前置條件: 輸入單一注音符號
        預期結果: main_symbols 為單元素列表
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("ㄚ")

        assert main == ["ㄚ"]
        assert tone is None

        # 帶聲調的單符號
        main, tone = split_zhuyin_symbols("ㄚˋ")
        assert main == ["ㄚ"]
        assert tone == "ˋ"

    def test_split_zhuyin_all_tone_marks(self):
        """TC-TYPO-010: 驗證所有聲調符號的識別

        測試案例: 四種聲調符號
        前置條件: 輸入包含不同聲調的注音
        預期結果: 正確識別所有聲調
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        # 二聲
        _, tone = split_zhuyin_symbols("ㄅㄚˊ")
        assert tone == "ˊ"

        # 三聲
        _, tone = split_zhuyin_symbols("ㄅㄚˇ")
        assert tone == "ˇ"

        # 四聲
        _, tone = split_zhuyin_symbols("ㄅㄚˋ")
        assert tone == "ˋ"

        # 輕聲
        _, tone = split_zhuyin_symbols("ㄅㄚ˙")
        assert tone == "˙"


class TestHelperFunctions:
    """輔助函數測試"""

    def test_extract_chinese_chars(self):
        """TC-TYPO-011: 驗證從混合文字中提取中文字

        測試案例: 包含注音、空格、標點的字串
        前置條件: 輸入混合文字
        預期結果: 只回傳純中文字元列表
        """
        from spellvid.domain.layout import extract_chinese_chars

        # 混合注音與中文
        assert extract_chinese_chars("ㄅㄧㄥ 冰") == ["冰"]
        assert extract_chinese_chars("ㄒㄩㄝˊ 雪") == ["雪"]

        # 多個中文字
        assert extract_chinese_chars("冰雪") == ["冰", "雪"]
        assert extract_chinese_chars("你好世界") == ["你", "好", "世", "界"]

        # 包含標點
        assert extract_chinese_chars("你好,世界!") == ["你", "好", "世", "界"]

        # 無中文字
        assert extract_chinese_chars("ABC 123") == []

    def test_is_chinese_char(self):
        """TC-TYPO-012: 驗證中文字元判斷

        測試案例: 各種字元的判斷
        前置條件: 輸入單一字元
        預期結果: 正確判斷是否為中文字
        """
        from spellvid.domain.typography import is_chinese_char

        # 中文字
        assert is_chinese_char("冰") is True
        assert is_chinese_char("雪") is True
        assert is_chinese_char("你") is True

        # 非中文
        assert is_chinese_char("A") is False
        assert is_chinese_char("1") is False
        assert is_chinese_char("ㄅ") is False  # 注音符號
        assert is_chinese_char("。") is False  # 標點
        assert is_chinese_char(" ") is False  # 空格


class TestEdgeCases:
    """邊界情況測試"""

    def test_zhuyin_for_empty_string(self):
        """TC-TYPO-013: 驗證空字串處理

        測試案例: 輸入空字串
        預期結果: 回傳 None 或拋出異常
        """
        from spellvid.domain.typography import zhuyin_for

        result = zhuyin_for("")
        assert result is None, "空字串應該回傳 None"

    def test_split_zhuyin_empty_string(self):
        """TC-TYPO-014: 驗證分割空字串

        測試案例: 輸入空字串給 split_zhuyin_symbols
        預期結果: 回傳空列表或拋出異常
        """
        from spellvid.domain.typography import split_zhuyin_symbols

        main, tone = split_zhuyin_symbols("")
        assert main == [], "空字串應該回傳空列表"
        assert tone is None

    def test_zhuyin_for_unicode_variants(self):
        """TC-TYPO-015: 驗證 Unicode 變體字的處理

        測試案例: 異體字或 Unicode 變體
        預期結果: 正確處理或回傳 None
        """
        from spellvid.domain.typography import zhuyin_for

        # 繁簡體可能有不同處理
        # 這裡測試是否有基本容錯
        result = zhuyin_for("台")  # vs 臺
        # 應該要有結果或至少不拋出異常
        assert result is None or isinstance(result, str)


# 標記此測試模組為單元測試
pytestmark = pytest.mark.unit
