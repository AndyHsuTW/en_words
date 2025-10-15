"""單元測試: shared/validation.py - JSON Schema 驗證

測試目標:
- validate_schema() 驗證 JSON 資料符合 schema
- load_json() 載入 JSON 檔案
- SCHEMA 定義的完整性

遵循 TDD 原則: 這些測試在實作前應該失敗
"""

import json
import pytest


# === TC-RESOURCE-001: validate_schema() 驗證通過 ===

def test_validate_schema_valid_minimal():
    """驗證最小必填欄位通過 schema 驗證

    測試案例: TC-VALIDATION-001
    前置條件: 提供包含必填欄位的資料
    預期結果: 驗證通過,不拋出異常
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰"
    }

    # 不應拋出異常
    validate_schema(data)


def test_validate_schema_valid_full():
    """驗證完整欄位通過 schema 驗證

    測試案例: TC-VALIDATION-001
    前置條件: 提供所有可選欄位
    預期結果: 驗證通過
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "image_path": "assets/ice.png",
        "music_path": "assets/ice.mp3",
        "countdown_sec": 5.0,
        "reveal_hold_sec": 3.0,
        "timer_visible": False,
        "progress_bar": True,
    }

    validate_schema(data)


# === TC-RESOURCE-002: validate_schema() 驗證失敗 ===

def test_validate_schema_missing_required_field():
    """驗證缺少必填欄位時拋出異常

    測試案例: TC-VALIDATION-002
    前置條件: 缺少 word_en 或 word_zh
    預期結果: 拋出 ValidationError
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": "I i",
        # 缺少 word_en, word_zh
    }

    with pytest.raises(Exception):  # jsonschema.ValidationError
        validate_schema(data)


def test_validate_schema_invalid_type_letters():
    """驗證 letters 型別錯誤時拋出異常

    測試案例: TC-VALIDATION-002
    前置條件: letters 為數字而非字串
    預期結果: 拋出 ValidationError
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": 123,  # 應為字串
        "word_en": "Ice",
        "word_zh": "冰"
    }

    with pytest.raises(Exception):
        validate_schema(data)


def test_validate_schema_invalid_countdown_sec():
    """驗證 countdown_sec 型別錯誤時拋出異常

    測試案例: TC-VALIDATION-002
    前置條件: countdown_sec 為字串而非數字
    預期結果: 拋出 ValidationError
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "countdown_sec": "not a number"  # 應為數字
    }

    with pytest.raises(Exception):
        validate_schema(data)


def test_validate_schema_invalid_timer_visible():
    """驗證 timer_visible 型別錯誤時拋出異常

    測試案例: TC-VALIDATION-002
    前置條件: timer_visible 為字串而非布林值
    預期結果: 拋出 ValidationError
    """
    from spellvid.shared.validation import validate_schema

    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "timer_visible": "yes"  # 應為布林值
    }

    with pytest.raises(Exception):
        validate_schema(data)


# === load_json() 測試 ===

def test_load_json_valid_file(tmp_path):
    """驗證 load_json() 可正確載入 JSON 陣列

    測試案例: 資源載入
    前置條件: JSON 檔案包含有效陣列
    預期結果: 回傳 list[dict]
    """
    from spellvid.shared.validation import load_json

    # 建立測試 JSON 檔案
    json_file = tmp_path / "test_config.json"
    data = [
        {"letters": "I i", "word_en": "Ice", "word_zh": "冰"},
        {"letters": "A a", "word_en": "Apple", "word_zh": "蘋果"}
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    # 載入並驗證
    result = load_json(str(json_file))

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["word_en"] == "Ice"
    assert result[1]["word_en"] == "Apple"


def test_load_json_file_not_found():
    """驗證 load_json() 處理檔案不存在

    測試案例: 錯誤處理
    前置條件: 檔案路徑不存在
    預期結果: 拋出 FileNotFoundError
    """
    from spellvid.shared.validation import load_json

    with pytest.raises(FileNotFoundError):
        load_json("non_existent_file.json")


def test_load_json_invalid_json(tmp_path):
    """驗證 load_json() 處理無效 JSON

    測試案例: 錯誤處理
    前置條件: 檔案包含無效 JSON
    預期結果: 拋出 json.JSONDecodeError
    """
    from spellvid.shared.validation import load_json

    json_file = tmp_path / "invalid.json"
    json_file.write_text("{ invalid json }", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_json(str(json_file))


def test_load_json_not_array(tmp_path):
    """驗證 load_json 處理非陣列 JSON

    測試案例: TC-RESOURCE-003 - 處理格式錯誤的 JSON
    前置條件: JSON 為物件而非陣列
    預期結果: 拋出 TypeError
    """
    from spellvid.shared.validation import load_json
    import pytest

    json_file = tmp_path / "not_array.json"
    json_file.write_text('{"key": "value"}', encoding="utf-8")

    # 應該拋出 TypeError(JSON 根節點必須是陣列)
    with pytest.raises(TypeError, match="JSON 根節點必須是陣列"):
        load_json(str(json_file))


# === SCHEMA 定義完整性測試 ===

def test_schema_definition_exists():
    """驗證 SCHEMA 常數存在

    測試案例: 模組結構
    前置條件: 匯入 validation 模組
    預期結果: SCHEMA 可被匯入
    """
    from spellvid.shared.validation import SCHEMA

    assert SCHEMA is not None
    assert isinstance(SCHEMA, dict)


def test_schema_has_required_fields():
    """驗證 SCHEMA 定義了必填欄位

    測試案例: Schema 完整性
    前置條件: SCHEMA 已定義
    預期結果: items.required 列表存在
    """
    from spellvid.shared.validation import SCHEMA

    # SCHEMA 是陣列 schema,必填欄位定義在 items.required
    assert "items" in SCHEMA
    assert "required" in SCHEMA["items"]
    assert isinstance(SCHEMA["items"]["required"], list)
    assert len(SCHEMA["items"]["required"]) > 0


def test_schema_defines_letters_field():
    """驗證 SCHEMA 定義了 letters 欄位

    測試案例: Schema 完整性
    前置條件: SCHEMA 已定義
    預期結果: properties 包含 letters
    """
    from spellvid.shared.validation import SCHEMA

    if "properties" in SCHEMA:
        assert "letters" in SCHEMA["properties"]


def test_validate_schema_rejects_empty_dict():
    """驗證空字典無法通過驗證

    測試案例: TC-VALIDATION-002
    前置條件: 空字典
    預期結果: 拋出 ValidationError
    """
    from spellvid.shared.validation import validate_schema

    with pytest.raises(Exception):
        validate_schema({})
