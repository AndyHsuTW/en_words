#!/usr/bin/env python
"""
產生字母佈局預覽圖以檢查影片字母資產對齊。

目的：
    這支腳本會使用專案中的字母影像資產（通常位於 `assets/AZ`）
    輸出字母的預覽圖（PNG）。主要用於視覺化驗證與調整字母影像資產位置或尺寸。

輸出：
    - 預設輸出資料夾：`out/letter_previews`
    - 檔名格式：`{LETTER}_preview.png`（例如 `A_preview.png`、`Z_preview.png`）

範例用法（PowerShell）：
    # 產生 A~Z 的預覽（使用預設資產資料夾），若同名檔案已存在則不覆寫
    python scripts/render_letter_previews.py

    # 指定單一字母並覆寫已存在的輸出
    python scripts/render_letter_previews.py --letters Z --overwrite

    # 指定資產資料夾與輸出資料夾
    python scripts/render_letter_previews.py --letters A,B,C --asset-dir assets/AZ --out-dir out/my_previews --overwrite

注意事項：
    - 此腳本會呼叫 `spellvid.utils._prepare_letters_context` 來取得字母佈局資訊，
        因此需要在專案的虛擬環境中安裝相依（例如 Pillow）並能匯入 `spellvid`。
    - 若要快速知道預設資產位置，腳本會以 `utils._resolve_letter_asset_dir(None)` 的回傳為預設。
    - 預覽圖會畫出一個代表計算後字母 bounding box 的藍色框（半透明）。

回傳值：
    `draw_letter_preview` 會回傳輸出檔案路徑（成功）或 `None`（跳過或錯誤）。

"""

from __future__ import annotations
from spellvid import utils

import argparse
import string
import sys
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


CANVAS_SIZE = (1920, 1080)
BACKGROUND_COLOR = (255, 255, 255, 255)
OUTLINE_COLOR = (0, 128, 255, 180)


def _resample_filter() -> int:
    """Return a high quality resampling filter available in this Pillow build."""
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    return Image.LANCZOS  # deprecated alias but keeps backward compatibility


def parse_letters(raw: str | None) -> List[str]:
    if not raw:
        return list(string.ascii_uppercase)
    result: List[str] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        result.append(token[0].upper())
    return result


def build_letters_string(letter: str) -> str:
    upper = letter.upper()
    lower = letter.lower()
    if upper == lower:
        return upper
    return f"{upper} {lower}"


def load_layout(letters: str, asset_dir: Path) -> dict:
    ctx = utils._prepare_letters_context({
        "letters": letters,
        "letters_as_image": True,
        "letters_asset_dir": str(asset_dir),
    })
    return ctx.get("layout", {})


def draw_letter_preview(letter: str, asset_dir: Path, out_dir: Path, overwrite: bool = False) -> Path | None:
    letters = build_letters_string(letter)
    layout = load_layout(letters, asset_dir)
    missing = layout.get("missing", [])
    letter_entries = layout.get("letters", [])

    if not letter_entries:
        print(f"[WARN] {letters}: 找不到可用的字母資產，略過。")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{letter.upper()}_preview.png"
    if output_path.exists() and not overwrite:
        print(f"[SKIP] {output_path.name} 已存在，使用 --overwrite 以重新產生。")
        return output_path

    canvas = Image.new("RGBA", CANVAS_SIZE, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(canvas)
    resample = _resample_filter()

    for entry in letter_entries:
        asset_path = entry.get("path")
        if not asset_path:
            continue
        path = Path(asset_path)
        if not path.is_file():
            print(f"[WARN] 缺少資產: {path}")
            continue
        try:
            with Image.open(path) as img:
                img = img.convert("RGBA")
                target_height = int(entry.get("height")) if entry.get(
                    "height") else img.height
                if target_height > 0 and img.height != target_height:
                    scale = target_height / float(img.height)
                    target_width = max(1, int(round(img.width * scale)))
                    img = img.resize((target_width, target_height), resample)
                pos_x = utils.LETTER_SAFE_X + int(entry.get("x", 0))
                pos_y = utils.LETTER_SAFE_Y
                canvas.paste(img, (pos_x, pos_y), img)
        except Exception as exc:
            print(f"[WARN] 無法載入 {path}: {exc}")

    bbox = layout.get("bbox") or {}
    bbox_width = int(bbox.get("w", 0))
    bbox_height = int(bbox.get("h", 0))
    bbox_offset = int(bbox.get("x_offset", 0))
    if bbox_width > 0 and bbox_height > 0:
        top_left = (
            utils.LETTER_SAFE_X + bbox_offset,
            utils.LETTER_SAFE_Y,
        )
        bottom_right = (
            top_left[0] + bbox_width,
            top_left[1] + bbox_height,
        )
        draw.rectangle([top_left, bottom_right],
                       outline=OUTLINE_COLOR, width=2)

    canvas.convert("RGB").save(output_path, "PNG")
    if missing:
        readable = [str(m.get("filename") or m.get("char")) for m in missing if m.get("filename") or m.get("char")]  # noqa: E501
        missing_names = ", ".join(readable) if readable else str(len(missing))
        print(f"[INFO] {letters}: 預覽完成，但缺少資產: {missing_names}")
    else:
        try:
            rel_path = output_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = output_path
        print(f"[OK] 已輸出 {rel_path}")
    return output_path


def main() -> None:
    default_asset_dir = Path(utils._resolve_letter_asset_dir(None)).resolve()
    parser = argparse.ArgumentParser(description="產生字母影像預覽，檢查字母佈局是否符合預期。")
    parser.add_argument(
        "--letters",
        type=str,
        help="以逗號分隔要產生的字母，預設為 A-Z。",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("out") / "letter_previews",
        help="輸出資料夾，預設為 out/letter_previews。",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=default_asset_dir,
        help=f"字母資產資料夾，預設為 {default_asset_dir}。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="若輸出檔案已存在則覆寫。",
    )

    args = parser.parse_args()
    asset_dir = args.asset_dir.expanduser().resolve()
    if not asset_dir.is_dir():
        parser.error(f"找不到字母資產資料夾: {asset_dir}")

    letters = parse_letters(args.letters)
    if not letters:
        parser.error("沒有可用的字母輸入。")

    for letter in letters:
        draw_letter_preview(letter, asset_dir, args.out_dir,
                            overwrite=args.overwrite)


if __name__ == "__main__":
    main()
