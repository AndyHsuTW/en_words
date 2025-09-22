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


