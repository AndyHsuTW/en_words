"""JSON Schema 驗證與載入

此模組提供 config.json 的驗證與載入功能:
- SCHEMA: JSON Schema 定義(Draft-07 規範)
- validate_schema: 驗證單一資料項目
- load_json: 從檔案載入並解析 JSON

這些函數從 utils.py 遷移而來,並增強錯誤處理。
"""

import json
from typing import Any, List
from pathlib import Path

# ========== JSON Schema 定義 ==========
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "letters",
            "word_en",
            "word_zh",
        ],
        "properties": {
            # 必填欄位
            "letters": {"type": "string"},
            "word_en": {"type": "string"},
            "word_zh": {"type": "string"},

            # 資源路徑(可選)
            "image_path": {"type": "string"},
            "music_path": {"type": "string"},
            "video_path": {"type": "string"},

            # 時間控制(可選)
            "countdown_sec": {"type": "number", "minimum": 0},
            "reveal_hold_sec": {"type": "number", "minimum": 0},
            "entry_hold_sec": {"type": "number", "minimum": 0},

            # 視覺選項(可選)
            "entry_enabled": {"type": "boolean", "default": True},
            "progress_bar": {"type": "boolean", "default": True},
            "timer_visible": {"type": "boolean", "default": True},
            "letters_as_image": {"type": "boolean", "default": True},

            # 視頻模式(可選)
            "video_mode": {
                "type": "string",
                "enum": ["fit", "cover"],
                "default": "cover"
            },

            # 主題(可選,目前未使用)
            "theme": {"type": "string"},

            # 輸出路徑(batch 模式使用)
            "output_path": {"type": "string"},
        },
        "additionalProperties": False
    }
}


class ValidationError(Exception):
    """JSON Schema 驗證失敗時拋出的異常

    此異常包含所有驗證錯誤訊息的清單。

    Attributes:
        errors: 錯誤訊息清單,每項描述一個驗證失敗的欄位

    Example:
        >>> try:
        ...     validate_schema({})  # 缺少必填欄位
        ... except ValidationError as e:
        ...     print(e.errors)
        ['缺少必填欄位: letters', '缺少必填欄位: word_en', ...]
    """

    def __init__(self, errors: List[str]):
        self.errors = errors
        message = f"驗證失敗: {len(errors)} 個錯誤\n" + \
            "\n".join(f"  - {err}" for err in errors)
        super().__init__(message)


def validate_schema(data: dict) -> None:
    """驗證單一資料項目符合 SCHEMA 定義

    此函數執行簡化的 JSON Schema 驗證:
    1. 檢查必填欄位是否存在
    2. 檢查欄位型別是否正確
    3. 檢查是否有額外的未定義欄位

    Args:
        data: 待驗證的字典資料(單一視頻配置)

    Raises:
        TypeError: 當 data 不是字典時
        ValidationError: 當驗證失敗時,包含所有錯誤訊息

    Example:
        >>> validate_schema({"letters": "A", "word_en": "A", "word_zh": "A"})  # 通過
        >>> validate_schema({"letters": "A"})  # ValidationError: 缺少 word_en, word_zh
    """
    if not isinstance(data, dict):
        raise TypeError(f"data 必須是字典,收到 {type(data).__name__}")

    errors = []
    schema_item = SCHEMA["items"]

    # 檢查必填欄位
    for required_field in schema_item["required"]:
        if required_field not in data:
            errors.append(f"缺少必填欄位: {required_field}")

    # 檢查欄位型別
    properties = schema_item["properties"]
    for key, value in data.items():
        if key not in properties:
            # 額外欄位(additionalProperties=False)
            errors.append(f"未定義的欄位: {key}")
            continue

        expected_type = properties[key].get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"欄位 {key} 必須是字串,收到 {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"欄位 {key} 必須是數字,收到 {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"欄位 {key} 必須是布林值,收到 {type(value).__name__}")

        # 檢查數字範圍
        if expected_type == "number" and "minimum" in properties[key]:
            minimum = properties[key]["minimum"]
            if isinstance(value, (int, float)) and value < minimum:
                errors.append(f"欄位 {key} 必須 >= {minimum},收到 {value}")

        # 檢查枚舉值
        if "enum" in properties[key]:
            if value not in properties[key]["enum"]:
                errors.append(
                    f"欄位 {key} 必須是 {properties[key]['enum']} 之一,收到 {value}")

    if errors:
        raise ValidationError(errors)


def load_json(file_path: str) -> List[dict]:
    """從檔案載入 JSON 陣列

    此函數讀取 config.json 並解析為 Python 物件。

    Args:
        file_path: JSON 檔案路徑

    Returns:
        字典清單,每項代表一個視頻配置

    Raises:
        FileNotFoundError: 當檔案不存在時
        json.JSONDecodeError: 當 JSON 格式錯誤時
        TypeError: 當 JSON 根節點不是陣列時

    Example:
        >>> items = load_json("config.json")
        >>> len(items)
        5
        >>> items[0]["word_en"]
        'Ice'
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到檔案: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise TypeError(f"JSON 根節點必須是陣列,收到 {type(data).__name__}")

    return data
