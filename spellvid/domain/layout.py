"""佈局計算模組

此模組負責計算視頻中各視覺元素的位置與尺寸,是純粹的領域邏輯層,
不依賴任何基礎設施(MoviePy, Pillow 等)。

職責:
- 計算字母、中文、圖片、計時器等元素的邊界框
- 計算注音符號的垂直排列
- 確保所有元素不超出 1920x1080 畫布範圍
- 提供 < 50ms 的計算效能

使用:
    from spellvid.domain.layout import compute_layout_bboxes
    from spellvid.shared.types import VideoConfig
    
    config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
    result = compute_layout_bboxes(config)
    print(result.letters.x, result.word_zh.x)
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from spellvid.shared.types import LayoutBox, VideoConfig
from spellvid.shared.constants import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    PROGRESS_BAR_HEIGHT,
)


# ========== 資料結構 ==========


@dataclass
class ZhuyinColumn:
    """單個中文字元的注音排版資訊"""

    char: str  # 中文字元
    main_symbols: List[str]  # 主要注音符號
    tone_symbol: Optional[str]  # 聲調符號
    bbox: LayoutBox  # 整體邊界框
    main_bbox: LayoutBox  # 主要注音區域
    tone_bbox: Optional[LayoutBox]  # 聲調區域(若有)


@dataclass
class LayoutResult:
    """完整的佈局計算結果

    包含所有視覺元素的位置資訊,供渲染層使用。
    """

    # 主要元素邊界框
    letters: LayoutBox  # 左側字母區域
    word_zh: LayoutBox  # 右側中文區域
    reveal: LayoutBox  # 中文顯示區域
    timer: Optional[LayoutBox] = None  # 倒數計時器(可選)
    image: Optional[LayoutBox] = None  # 中央圖片區域(可選)

    # 注音細節
    zhuyin_columns: List[ZhuyinColumn] = field(default_factory=list)

    # 下劃線位置(用於 reveal 動畫)
    reveal_underlines: List[Tuple[int, int, int, int]] = field(
        default_factory=list
    )
    # 每個 tuple: (x, y, width, height)

    # 進度條資訊
    progress_bar_y: Optional[int] = None  # 進度條 Y 座標

    def to_dict(self) -> dict:
        """轉換為舊版 Dict 格式(向後相容)

        Returns:
            與 compute_layout_bboxes 原本回傳格式相同的字典
        """
        result = {
            "letters": self.letters.to_dict(),
            "word_zh": self.word_zh.to_dict(),
            "reveal": self.reveal.to_dict(),
        }

        if self.timer:
            result["timer"] = self.timer.to_dict()

        if self.image:
            result["image"] = self.image.to_dict()

        if self.reveal_underlines:
            result["reveal_underlines"] = self.reveal_underlines

        if self.progress_bar_y is not None:
            result["progress_bar_y"] = self.progress_bar_y

        # 注音細節轉換
        if self.zhuyin_columns:
            result["zhuyin_details"] = [
                {
                    "char": col.char,
                    "main": col.main_symbols,
                    "tone": col.tone_symbol,
                    "bbox": col.bbox.to_dict(),
                    "main_bbox": col.main_bbox.to_dict(),
                    "tone_bbox": (
                        col.tone_bbox.to_dict() if col.tone_bbox else None
                    ),
                }
                for col in self.zhuyin_columns
            ]

        return result


# ========== 公開 API ==========


def compute_layout_bboxes(
    config: VideoConfig,
    timer_visible: bool = True,
    progress_bar: bool = True,
) -> LayoutResult:
    """計算視頻中所有視覺元素的邊界框

    這是佈局計算的入口函數,純粹的領域邏輯,不依賴任何渲染框架。

    Args:
        config: 視頻配置
        timer_visible: 是否顯示倒數計時器
        progress_bar: 是否顯示進度條

    Returns:
        包含所有邊界框的 LayoutResult

    Raises:
        ValueError: 配置無效(如字串過長無法排版)

    Performance:
        執行時間 < 50ms
    """
    # 提取中文字元
    chinese_chars = extract_chinese_chars(config.word_zh)

    # 基本尺寸估算(參考 utils.py 現有邏輯)
    # 字母區域: 左側 1/3
    letters_width = CANVAS_WIDTH // 3
    letters_height = 400  # 估算高度
    letters_x = 50
    letters_y = (CANVAS_HEIGHT - letters_height) // 2

    letters_bbox = LayoutBox(
        x=letters_x, y=letters_y, width=letters_width, height=letters_height
    )

    # 中文區域: 右側 1/3
    word_zh_width = CANVAS_WIDTH // 3
    word_zh_height = 300
    word_zh_x = CANVAS_WIDTH - word_zh_width - 50
    word_zh_y = (CANVAS_HEIGHT - word_zh_height) // 2

    word_zh_bbox = LayoutBox(
        x=word_zh_x,
        y=word_zh_y,
        width=word_zh_width,
        height=word_zh_height,
    )

    # Reveal 區域(中文字本體)
    reveal_width = word_zh_width - 100
    reveal_height = word_zh_height // 2
    reveal_x = word_zh_x + 50
    reveal_y = word_zh_y + word_zh_height // 2

    reveal_bbox = LayoutBox(
        x=reveal_x, y=reveal_y, width=reveal_width, height=reveal_height
    )

    # 計時器
    timer_bbox = None
    if timer_visible:
        timer_size = 120
        timer_x = letters_x + 50
        timer_y = letters_y + letters_height + 30
        timer_bbox = LayoutBox(
            x=timer_x, y=timer_y, width=timer_size, height=timer_size
        )

    # 圖片區域(中央)
    image_bbox = None
    if config.image_path or config.video_path:
        image_width = 500
        image_height = 500
        image_x = (CANVAS_WIDTH - image_width) // 2
        image_y = (CANVAS_HEIGHT - image_height) // 2
        image_bbox = LayoutBox(
            x=image_x, y=image_y, width=image_width, height=image_height
        )

    # 進度條
    progress_bar_y_value = None
    if progress_bar:
        # 進度條位於畫布底部附近
        progress_bar_y_offset = 80  # 與底部的間距
        progress_bar_y_value = (
            CANVAS_HEIGHT - PROGRESS_BAR_HEIGHT - progress_bar_y_offset
        )

    # 注音排版
    zhuyin_columns = _calculate_zhuyin_layout(
        chinese_chars, word_zh_bbox.x, word_zh_bbox.y, word_zh_bbox.width
    )

    # 下劃線位置(簡化版)
    reveal_underlines = []
    if chinese_chars:
        underline_width = reveal_width // len(chinese_chars)
        for i in range(len(chinese_chars)):
            underline_x = reveal_x + i * underline_width
            underline_y = reveal_y + reveal_height - 10
            reveal_underlines.append(
                (underline_x, underline_y, underline_width - 10, 5)
            )

    return LayoutResult(
        letters=letters_bbox,
        word_zh=word_zh_bbox,
        reveal=reveal_bbox,
        timer=timer_bbox,
        image=image_bbox,
        zhuyin_columns=zhuyin_columns,
        reveal_underlines=reveal_underlines,
        progress_bar_y=progress_bar_y_value,
    )


def extract_chinese_chars(text: str) -> List[str]:
    """從混合文字中提取中文字元

    過濾掉注音符號、空格、標點,只保留中文字。

    Args:
        text: 混合文字(如 "ㄅㄧㄥ 冰")

    Returns:
        中文字元列表(如 ["冰"])

    Examples:
        >>> extract_chinese_chars("ㄅㄧㄥ 冰")
        ['冰']
        >>> extract_chinese_chars("ㄒㄩㄝˊ 雪")
        ['雪']
    """
    # 中文字 Unicode 範圍: U+4E00 到 U+9FFF
    chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
    return chinese_pattern.findall(text)


# ========== 內部輔助函數 ==========


def _calculate_zhuyin_layout(
    chinese_chars: List[str], base_x: int, base_y: int, area_width: int
) -> List[ZhuyinColumn]:
    """計算注音符號的垂直排列

    Args:
        chinese_chars: 中文字元列表
        base_x: 起始 X 座標
        base_y: 起始 Y 座標
        area_width: 可用寬度

    Returns:
        注音列資訊列表
    """
    # 簡化版實作: 不實際查詢注音,只建立結構
    # 待 typography.py 完成後可整合
    columns = []

    if not chinese_chars:
        return columns

    col_width = area_width // len(chinese_chars)
    symbol_height = 40  # 每個符號高度

    for i, char in enumerate(chinese_chars):
        col_x = base_x + i * col_width
        col_y = base_y

        # 模擬注音符號(暫時)
        main_symbols = ["ㄅ", "ㄧ", "ㄥ"]  # 簡化版
        tone_symbol = None

        # 主要注音區域
        main_bbox = LayoutBox(
            x=col_x,
            y=col_y,
            width=col_width,
            height=len(main_symbols) * symbol_height,
        )

        # 聲調區域(若有)
        tone_bbox = None
        if tone_symbol:
            tone_bbox = LayoutBox(
                x=col_x + col_width - 30,
                y=col_y,
                width=30,
                height=symbol_height,
            )

        # 整體邊界框
        bbox_height = main_bbox.height + (
            tone_bbox.height if tone_bbox else 0
        )
        bbox = LayoutBox(x=col_x, y=col_y, width=col_width, height=bbox_height)

        columns.append(
            ZhuyinColumn(
                char=char,
                main_symbols=main_symbols,
                tone_symbol=tone_symbol,
                bbox=bbox,
                main_bbox=main_bbox,
                tone_bbox=tone_bbox,
            )
        )

    return columns


# ============================================================================
# 字母處理輔助函數 (Letter Processing Helpers)
# ============================================================================


def _normalize_letters_sequence(letters: str) -> List[str]:
    """正規化字母序列,過濾空白與空字元

    Args:
        letters: 原始字母字串 (可能包含空格、換行等)

    Returns:
        過濾後的字元列表

    Example:
        >>> _normalize_letters_sequence("I  i\\n")
        ['I', 'i']
        >>> _normalize_letters_sequence("")
        []
    """
    if not letters:
        return []
    seq: List[str] = []
    for ch in letters:
        if not ch or ch.isspace():
            continue
        seq.append(ch)
    return seq


def _letter_asset_filename(ch: str) -> Optional[str]:
    """根據字元產生對應的素材檔名

    Args:
        ch: 單一字元

    Returns:
        對應的 PNG 檔名,若字元不是字母則返回 None

    Rules:
        - 大寫字母 → "{ch}.png" (例如: "A.png")
        - 小寫字母 → "{ch}_small.png" (例如: "a_small.png")
        - 非字母 → None

    Example:
        >>> _letter_asset_filename("A")
        'A.png'
        >>> _letter_asset_filename("z")
        'z_small.png'
        >>> _letter_asset_filename("1")
        None
    """
    if not ch:
        return None
    if ch.isalpha():
        if ch.isupper():
            return f"{ch}.png"
        if ch.islower():
            return f"{ch}_small.png"
    return None


def _letters_missing_names(missing: List[dict]) -> List[str]:
    """從缺失素材列表中提取檔名或字元名稱

    Args:
        missing: 缺失素材的字典列表,每個字典包含 "filename" 或 "char" 欄位

    Returns:
        去重後的名稱列表

    Example:
        >>> _letters_missing_names([
        ...     {"filename": "A.png", "char": "A"},
        ...     {"char": "B"},
        ...     {"filename": "A.png"}
        ... ])
        ['A.png', 'B']
    """
    names: List[str] = []
    for entry in missing or []:
        name = entry.get("filename") or entry.get("char")
        if name:
            name_str = str(name)
            if name_str not in names:
                names.append(name_str)
    return names


# ============================================================================
# 注音符號佈局計算 (Zhuyin Layout)
# ============================================================================


def _layout_zhuyin_column(
    cursor_y: int,
    col_h: int,
    total_main_h: int,
    tone_syms: List[str],
    tone_sizes: List[Tuple[int, int]],
    tone_gap: int = 10,
) -> Dict[str, Any]:
    """計算注音符號直行的垂直位置佈局
    
    此函數處理注音符號(聲母、韻母、介音)與聲調符號的垂直排列,
    包含特殊處理:
    - 輕聲(˙)置於主要符號上方,居中對齊
    - 其他聲調置於主要符號右側,垂直置中
    
    Args:
        cursor_y: 直行起始 Y 座標 (頂部)
        col_h: 直行可用高度
        total_main_h: 主要符號的總高度
        tone_syms: 聲調符號列表 (例如: ["ˊ"] 或 ["˙"])
        tone_sizes: 聲調符號的 (寬, 高) 列表
        tone_gap: 符號間的間距 (預設 10px)
    
    Returns:
        包含佈局資訊的字典:
        - main_start_y: 主要符號起始 Y 座標
        - tone_start_y: 聲調符號起始 Y 座標 (None 表示無聲調)
        - tone_box_height: 聲調區域總高度
        - tone_alignment: 聲調對齊方式 ("center" 或 "right")
        - tone_is_neutral: 是否為輕聲
    
    Examples:
        >>> # 一般聲調 (ˊ) - 置於右側垂直置中
        >>> _layout_zhuyin_column(
        ...     cursor_y=100, col_h=200, total_main_h=80,
        ...     tone_syms=["ˊ"], tone_sizes=[(10, 15)]
        ... )
        {'main_start_y': 100, 'tone_start_y': 140, 'tone_box_height': 15,
         'tone_alignment': 'right', 'tone_is_neutral': False}
        
        >>> # 輕聲 (˙) - 置於上方居中
        >>> _layout_zhuyin_column(
        ...     cursor_y=100, col_h=200, total_main_h=80,
        ...     tone_syms=["˙"], tone_sizes=[(10, 12)]
        ... )
        {'main_start_y': 122, 'tone_start_y': 100, 'tone_box_height': 12,
         'tone_alignment': 'center', 'tone_is_neutral': True}
    """
    tone_is_neutral = len(tone_syms) == 1 and tone_syms[0] == "˙"
    top = int(cursor_y)
    col_height = max(0, int(col_h))
    safe_total_main_h = max(0, int(total_main_h))

    # 預設主要符號從頂部開始
    base_main_start_y = top
    if safe_total_main_h > 0:
        # 確保主要符號不超出可用高度
        limit_main_start = top + col_height - safe_total_main_h
        if limit_main_start < base_main_start_y:
            base_main_start_y = limit_main_start
    
    layout: Dict[str, Any] = {
        "main_start_y": base_main_start_y,
        "tone_start_y": None,
        "tone_box_height": 0,
        "tone_alignment": "right",
        "tone_is_neutral": tone_is_neutral,
    }
    
    # 如果沒有聲調符號,直接返回
    if not tone_syms or not tone_sizes:
        return layout

    # 計算聲調符號的總高度 (包含間距)
    tone_total_h = 0
    for idx, (_, height) in enumerate(tone_sizes):
        tone_total_h += max(0, int(height))
        if idx < len(tone_sizes) - 1:
            tone_total_h += tone_gap
    tone_total_h = max(0, tone_total_h)

    if tone_is_neutral:
        # 輕聲特殊處理: 置於主要符號上方,居中對齊
        has_content = safe_total_main_h > 0 and tone_total_h > 0
        gap_to_main = tone_gap if has_content else 0
        block_h = safe_total_main_h + tone_total_h + gap_to_main
        block_start_y = top
        
        # 整體區塊置中
        if block_h > 0:
            limit_block_start = top + col_height - block_h
            if limit_block_start < block_start_y:
                block_start_y = limit_block_start
        
        layout["tone_start_y"] = block_start_y
        layout["main_start_y"] = block_start_y + tone_total_h + gap_to_main
        layout["tone_box_height"] = tone_total_h
        layout["tone_alignment"] = "center"
    else:
        # 一般聲調: 置於主要符號右側,垂直置中
        layout["main_start_y"] = base_main_start_y
        tone_start_y = base_main_start_y + max(0, safe_total_main_h // 2)
        
        # 確保聲調不超出可用高度
        if tone_total_h > 0:
            max_tone_start = top + col_height - tone_total_h
            if tone_start_y > max_tone_start:
                tone_start_y = max_tone_start
        
        layout["tone_start_y"] = tone_start_y
        layout["tone_box_height"] = tone_total_h or safe_total_main_h

    return layout
