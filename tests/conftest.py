import sys
import os
import string
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

# 確保測試執行時能找到專案根目錄，讓 tests 可以 import 本地套件
# 對應需求: 可在本地環境執行單元測試並引用專案程式碼
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _create_letter_image(path: Path, char: str, size: int) -> None:
    base = ord(char.upper()) if char else 65
    color = (
        50 + (base * 3) % 180,
        80 + (base * 5) % 160,
        120 + (base * 7) % 140,
        255,
    )
    img = Image.new("RGBA", (size, size), color)
    draw = ImageDraw.Draw(img)
    inset = max(2, size // 6)
    draw.rectangle(
        (inset, inset, size - inset, size - inset),
        fill=(255, 255, 255, 220),
    )
    img.save(path, "PNG")


@pytest.fixture(scope="session")
def letter_assets_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("letters_assets")
    for ch in string.ascii_uppercase:
        upper_path = base / f"{ch}.png"
        lower_path = base / f"{ch.lower()}_small.png"
        _create_letter_image(upper_path, ch, 256)
        _create_letter_image(lower_path, ch.lower(), 192)
    return base


@pytest.fixture(autouse=True)
def _use_letter_assets_env(monkeypatch: pytest.MonkeyPatch, letter_assets_dir: Path) -> None:
    monkeypatch.setenv("SPELLVID_LETTER_ASSET_DIR", str(letter_assets_dir))


# === 新增: 架構重構專用 Fixtures ===

@pytest.fixture
def sample_video_config_dict():
    """提供範例 VideoConfig 字典資料"""
    return {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "image_path": "assets/ice.png",
        "music_path": "assets/ice.mp3",
        "countdown_sec": 3.0,
        "reveal_hold_sec": 2.0,
        "timer_visible": True,
        "progress_bar": True,
    }


@pytest.fixture
def minimal_video_config_dict():
    """提供最小必填欄位的 VideoConfig 字典"""
    return {
        "letters": "A a",
        "word_en": "Apple",
        "word_zh": "蘋果",
    }


@pytest.fixture
def temp_media_files(tmp_path):
    """建立臨時媒體檔案用於測試"""
    # 建立假的圖片檔案
    img_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)

    # 建立假的音訊檔案(空檔案足夠測試路徑檢查)
    audio_path = tmp_path / "test_audio.mp3"
    audio_path.write_bytes(b"fake audio data")

    return {
        "image": str(img_path),
        "audio": str(audio_path),
        "dir": tmp_path,
    }
