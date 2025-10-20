"""圖像載入器模組

此模組負責從檔案系統載入字母圖片並獲取其尺寸資訊。
屬於基礎設施層,處理與 PIL 和檔案系統的交互。

職責:
- 檢查字母素材檔案是否存在
- 讀取圖片尺寸資訊
- 處理檔案不存在或無法讀取的情況
- 返回圖片規格列表與缺失項目清單

使用:
    from infrastructure.rendering.image_loader import load_letter_image_specs
    from domain.layout import _normalize_letters_sequence, _letter_asset_filename
    
    specs, missing = load_letter_image_specs("Ice", "assets/letters")
    for spec in specs:
        print(f"{spec['char']}: {spec['width']}x{spec['height']}")
"""

import os
from typing import Any, Dict, List, Tuple

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    Image = None
    _HAS_PIL = False


def _load_letter_image_specs(
    letters: str,
    asset_dir: str,
    *,
    normalize_fn=None,
    filename_fn=None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """載入字母圖片規格資訊

    此函數檢查指定字母的素材檔案,讀取每個存在且可讀取的圖片尺寸,
    並記錄所有缺失或無法讀取的項目。

    Args:
        letters: 字母字串 (例如: "Ice")
        asset_dir: 素材目錄路徑
        normalize_fn: 正規化函數 (預設從 domain.layout 導入)
        filename_fn: 檔名生成函數 (預設從 domain.layout 導入)

    Returns:
        (specs, missing) 元組:
        - specs: 成功載入的圖片規格列表,每個元素包含:
          - char: 字元
          - filename: 檔名
          - path: 完整路徑
          - width: 圖片寬度(像素)
          - height: 圖片高度(像素)
        - missing: 缺失或無法載入的項目列表,每個元素包含:
          - char: 字元
          - filename: 檔名 (若為 None 表示不支援的字元)
          - path: 完整路徑 (若存在)
          - reason: 原因 ("unsupported", "missing", "unreadable")
          - error: 錯誤訊息 (若 reason="unreadable")

    Raises:
        ImportError: 若 PIL 未安裝

    Examples:
        >>> # 成功載入
        >>> specs, missing = _load_letter_image_specs("Ii", "assets/letters")
        >>> len(specs)
        2
        >>> specs[0]["char"]
        'I'
        >>> specs[0]["width"]
        800

        >>> # 缺失檔案
        >>> specs, missing = _load_letter_image_specs("XYZ", "assets/letters")
        >>> len(missing)
        3
        >>> missing[0]["reason"]
        'missing'

    Note:
        - 需要 PIL (Pillow) 才能讀取圖片尺寸
        - 若 normalize_fn/filename_fn 為 None,將從 domain.layout 導入
        - 此函數不進行任何佈局計算,僅負責載入資訊
    """
    if not _HAS_PIL:
        raise ImportError(
            "PIL (Pillow) is required to load letter images. "
            "Install with: pip install Pillow"
        )

    # 延遲導入 domain 函數 (避免循環依賴)
    if normalize_fn is None:
        from spellvid.domain.layout import _normalize_letters_sequence
        normalize_fn = _normalize_letters_sequence

    if filename_fn is None:
        from spellvid.domain.layout import _letter_asset_filename
        filename_fn = _letter_asset_filename

    # 正規化字母序列
    seq = normalize_fn(letters)

    missing: List[Dict[str, Any]] = []
    specs: List[Dict[str, Any]] = []

    for ch in seq:
        # 生成檔名
        fname = filename_fn(ch)

        # 檢查是否為支援的字元
        if not fname:
            missing.append({
                "char": ch,
                "filename": None,
                "path": None,
                "reason": "unsupported",
            })
            continue

        # 構建完整路徑
        path_str = os.path.join(asset_dir, fname)

        # 檢查檔案是否存在
        if not os.path.isfile(path_str):
            missing.append({
                "char": ch,
                "filename": fname,
                "path": path_str,
                "reason": "missing",
            })
            continue

        # 嘗試讀取圖片尺寸
        try:
            with Image.open(path_str) as img:
                orig_w, orig_h = img.size
        except Exception as exc:
            missing.append({
                "char": ch,
                "filename": fname,
                "path": path_str,
                "reason": "unreadable",
                "error": str(exc),
            })
            continue

        # 成功載入,添加到規格列表
        specs.append({
            "char": ch,
            "filename": fname,
            "path": path_str,
            "width": int(orig_w),
            "height": int(orig_h),
        })

    return specs, missing
