"""視頻效果邏輯模組

此模組負責計算視頻效果參數(淡入、淡出、過渡)與進度條佈局,為上層應用服務提供效果時間軸資料。

職責:
- 計算 fadeout 效果的起始時間與持續時間
- 計算 fadein 效果參數
- 規劃 transition 過渡效果的時間軸
- 計算進度條的顏色帶佈局與分段
- 驗證效果參數的有效性

設計原則:
- 純函數邏輯,不依賴任何基礎設施(MoviePy, Pillow 等)
- 回傳字典格式的效果參數,方便上層組裝
- 拋出 ValueError 表示無效參數

Examples:
    >>> apply_fadeout(clip_duration=5.0, fadeout_duration=1.0)
    {'start_time': 4.0, 'duration': 1.0, 'clip_duration': 5.0}

    >>> apply_fadein(fadein_duration=0.5)
    {'start_time': 0.0, 'duration': 0.5}

    >>> plan_transition(clip1_duration=5.0, clip2_duration=3.0, transition_duration=0.5)
    {'clip1_fadeout_start': 4.5, 'clip2_start_time': 4.5, 'total_duration': 7.5}
"""

import math
from typing import Any, Dict, List, Optional

from spellvid.shared.constants import (
    PROGRESS_BAR_COLORS,
    PROGRESS_BAR_CORNER_RADIUS,
    PROGRESS_BAR_RATIOS,
    PROGRESS_BAR_WIDTH,
)


# ========== 公開 API ==========


def apply_fadeout(clip_duration: float, fadeout_duration: float) -> Optional[Dict[str, Any]]:
    """計算淡出效果參數

    Args:
        clip_duration: 視頻總長度(秒)
        fadeout_duration: 淡出持續時間(秒)

    Returns:
        淡出效果參數字典,包含:
        - start_time: 淡出開始時間(秒)
        - duration: 淡出持續時間(秒)
        - clip_duration: 視頻總長度(秒)

        若 fadeout_duration 為 0,回傳 None

    Raises:
        ValueError: 當 fadeout_duration >= clip_duration 時

    Examples:
        >>> apply_fadeout(clip_duration=5.0, fadeout_duration=1.0)
        {'start_time': 4.0, 'duration': 1.0, 'clip_duration': 5.0}

        >>> apply_fadeout(clip_duration=1.5, fadeout_duration=0.5)
        {'start_time': 1.0, 'duration': 0.5, 'clip_duration': 1.5}

        >>> apply_fadeout(clip_duration=5.0, fadeout_duration=0.0)
        None
    """
    # 零持續時間 = 不應用效果
    if fadeout_duration == 0.0:
        return None

    # 驗證參數
    validate_effect_duration(fadeout_duration, clip_duration)

    # 計算淡出起始時間: 視頻結束前 fadeout_duration 秒
    start_time = clip_duration - fadeout_duration

    return {
        "start_time": start_time,
        "duration": fadeout_duration,
        "clip_duration": clip_duration,
    }


def apply_fadein(fadein_duration: float) -> Optional[Dict[str, Any]]:
    """計算淡入效果參數

    Args:
        fadein_duration: 淡入持續時間(秒)

    Returns:
        淡入效果參數字典,包含:
        - start_time: 淡入開始時間(固定為 0.0)
        - duration: 淡入持續時間(秒)

        若 fadein_duration 為 0,回傳 None

    Examples:
        >>> apply_fadein(fadein_duration=0.5)
        {'start_time': 0.0, 'duration': 0.5}

        >>> apply_fadein(fadein_duration=0.0)
        None
    """
    # 零持續時間 = 不應用效果
    if fadein_duration == 0.0:
        return None

    # 淡入總是從視頻開始
    return {
        "start_time": 0.0,
        "duration": fadein_duration,
    }


def plan_transition(
    clip1_duration: float,
    clip2_duration: float,
    transition_duration: float
) -> Dict[str, Any]:
    """規劃兩個 clip 之間的過渡效果時間軸

    Args:
        clip1_duration: 第一個 clip 的長度(秒)
        clip2_duration: 第二個 clip 的長度(秒)
        transition_duration: 過渡重疊時間(秒)

    Returns:
        過渡效果參數字典,包含:
        - clip1_fadeout_start: clip1 開始淡出的時間(秒)
        - clip2_start_time: clip2 開始播放的時間(秒)
        - total_duration: 兩個 clip 合併後的總長度(秒)

    Raises:
        ValueError: 當 transition_duration > clip1_duration 或 clip2_duration 時

    Examples:
        >>> plan_transition(clip1_duration=5.0, clip2_duration=3.0, transition_duration=0.5)
        {'clip1_fadeout_start': 4.5, 'clip2_start_time': 4.5, 'total_duration': 7.5}

        >>> plan_transition(clip1_duration=5.0, clip2_duration=3.0, transition_duration=0.0)
        {'clip1_fadeout_start': 5.0, 'clip2_start_time': 5.0, 'total_duration': 8.0}
    """
    # 驗證過渡時間不超過任一 clip 長度
    if transition_duration > clip1_duration:
        raise ValueError(
            f"過渡持續時間 {transition_duration:.2f} 秒超過第一個 clip 長度 {clip1_duration:.2f} 秒"
        )
    if transition_duration > clip2_duration:
        raise ValueError(
            f"過渡持續時間 {transition_duration:.2f} 秒超過第二個 clip 長度 {clip2_duration:.2f} 秒"
        )

    # clip1 淡出起始時間 = clip1_duration - transition_duration
    clip1_fadeout_start = clip1_duration - transition_duration

    # clip2 在 clip1 淡出開始時同時開始(重疊)
    clip2_start_time = clip1_fadeout_start

    # 總長度 = clip1 + clip2 - 重疊部分
    total_duration = clip1_duration + clip2_duration - transition_duration

    return {
        "clip1_fadeout_start": clip1_fadeout_start,
        "clip2_start_time": clip2_start_time,
        "total_duration": total_duration,
    }


def validate_effect_duration(duration: float, clip_duration: Optional[float] = None) -> None:
    """驗證效果持續時間的有效性

    Args:
        duration: 效果持續時間(秒)
        clip_duration: 視頻總長度(秒),可選

    Raises:
        ValueError: 當持續時間無效時(負數或超過視頻長度)

    Examples:
        >>> validate_effect_duration(1.0)
        # 無異常

        >>> validate_effect_duration(-1.0)
        Traceback (most recent call last):
        ValueError: 持續時間 -1.00 秒不能為負數

        >>> validate_effect_duration(10.0, clip_duration=5.0)
        Traceback (most recent call last):
        ValueError: 持續時間 10.00 秒超過最大值 5.00 秒
    """
    if duration < 0:
        raise ValueError(f"持續時間 {duration:.2f} 秒不能為負數")

    if clip_duration is not None and duration >= clip_duration:
        raise ValueError(
            f"持續時間 {duration:.2f} 秒超過最大值 {clip_duration:.2f} 秒"
        )


# ============================================================================
# 進度條佈局計算 (Progress Bar Layout)
# ============================================================================


def _progress_bar_band_layout(bar_width: int) -> List[Dict[str, Any]]:
    """計算進度條顏色帶的像素範圍佈局
    
    根據預設的顏色帶比例 (PROGRESS_BAR_RATIOS),計算每個顏色帶在進度條中的
    起始與結束像素位置。顏色帶順序為: safe (綠) → warn (黃) → danger (紅)
    
    Args:
        bar_width: 進度條總寬度(像素)
    
    Returns:
        顏色帶佈局列表,每個元素包含:
        - name: 顏色帶名稱 ("safe", "warn", "danger")
        - color: RGB 顏色元組 (from PROGRESS_BAR_COLORS)
        - start: 起始 X 座標(像素)
        - end: 結束 X 座標(像素)
    
    Examples:
        >>> layout = _progress_bar_band_layout(1792)
        >>> len(layout)
        3
        >>> layout[0]["name"]
        'safe'
        >>> layout[0]["start"]
        0
        >>> layout[-1]["name"]
        'danger'
        >>> layout[-1]["end"]
        1792
    
    Note:
        - 最後一個顏色帶的 end 總是等於 bar_width,確保覆蓋整個進度條
        - 使用四捨五入避免浮點數誤差
    """
    order = ("safe", "warn", "danger")
    layout: List[Dict[str, Any]] = []
    cursor = 0
    
    for idx, key in enumerate(order):
        if idx == len(order) - 1:
            # 最後一個顏色帶延伸到進度條末端
            end = bar_width
        else:
            # 根據比例計算寬度
            width = int(round(bar_width * PROGRESS_BAR_RATIOS[key]))
            end = min(bar_width, cursor + width)
        
        # 確保 end >= cursor
        end = max(cursor, end)
        
        layout.append(
            {
                "name": key,
                "color": PROGRESS_BAR_COLORS[key],
                "start": cursor,
                "end": end,
            }
        )
        cursor = end
    
    # 確保最後一個顏色帶延伸到進度條末端
    if layout:
        layout[-1]["end"] = bar_width
    
    return layout


def _build_progress_bar_segments(
    countdown: float,
    total_duration: float,
    *,
    fps: int = 10,
    bar_width: int = PROGRESS_BAR_WIDTH,
) -> List[Dict[str, Any]]:
    """規劃倒數計時中進度條的各個時間分段
    
    將倒數計時分割為多個時間段,計算每個時間段內進度條應顯示的寬度、位置、
    以及顏色區段。進度條從右向左縮減(倒數效果)。
    
    Args:
        countdown: 倒數時長(秒)
        total_duration: 視頻總時長(秒),應 >= countdown
        fps: 進度條更新頻率(幀/秒),預設 10fps
        bar_width: 進度條總寬度(像素),預設 PROGRESS_BAR_WIDTH
    
    Returns:
        時間分段列表,每個元素包含:
        - start: 分段起始時間(秒)
        - end: 分段結束時間(秒)
        - width: 進度條可見寬度(像素)
        - x_start: 進度條起始 X 座標(像素)
        - color_spans: 該分段內的顏色區段列表
        - corner_radius: 圓角半徑(像素)
        
        若 countdown=0,返回單一分段(寬度為 0)
        若 fps<=0 或 bar_width<=0,返回空列表
    
    Examples:
        >>> # 10 秒倒數,10fps
        >>> segments = _build_progress_bar_segments(
        ...     countdown=10.0, total_duration=15.0, fps=10
        ... )
        >>> len(segments)
        101  # 100 個倒數分段 + 1 個結束分段
        
        >>> # 第一個分段(倒數開始,進度條滿)
        >>> segments[0]["start"]
        0.0
        >>> segments[0]["width"]
        1792  # 假設 PROGRESS_BAR_WIDTH=1792
        
        >>> # 最後一個分段(倒數結束後)
        >>> segments[-1]["start"]
        10.0
        >>> segments[-1]["width"]
        0
        
        >>> # 無倒數
        >>> segments = _build_progress_bar_segments(
        ...     countdown=0.0, total_duration=5.0
        ... )
        >>> len(segments)
        1
        >>> segments[0]["width"]
        0
    
    Note:
        - 進度條從右向左縮減(x_start 增加,width 減少)
        - 每個分段的 color_spans 根據 _progress_bar_band_layout 計算
        - 最後總是追加一個倒數結束後的分段(width=0)
    """
    countdown = float(max(0.0, countdown))
    total_duration = float(max(total_duration, countdown))
    
    # 參數驗證
    if fps <= 0 or bar_width <= 0:
        return []
    
    # 無倒數情況:返回單一分段(進度條不顯示)
    if countdown == 0.0:
        return [
            {
                "start": 0.0,
                "end": round(total_duration, 6),
                "width": 0,
                "x_start": bar_width,
                "color_spans": [],
                "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
            }
        ]
    
    # 計算顏色帶佈局
    layout = _progress_bar_band_layout(bar_width)
    
    # 計算分段數量與每段時長
    step_count = max(1, int(math.ceil(countdown * float(fps))))
    step = countdown / step_count
    
    segments: List[Dict[str, Any]] = []
    prev_width = bar_width
    
    for idx in range(step_count):
        # 計算時間範圍
        start = min(countdown, idx * step)
        end = min(countdown, (idx + 1) * step)
        
        if end <= start:
            continue
        
        # 計算剩餘時間比例
        remaining = max(0.0, countdown - start)
        ratio = remaining / countdown if countdown else 0.0
        
        # 計算進度條寬度
        raw_width = int(round(bar_width * ratio))
        visible_width = min(prev_width, max(0, raw_width))
        
        # 確保進度條不會突然出現/消失
        if ratio > 0.0:
            if prev_width > 0:
                visible_width = max(1, visible_width)
            else:
                visible_width = 0
        else:
            visible_width = 0
        
        # 計算 X 起始位置(從右向左縮減)
        x_start = bar_width - visible_width if visible_width > 0 else bar_width
        
        # 計算該分段內的顏色區段
        color_spans: List[Dict[str, Any]] = []
        if visible_width > 0:
            span_start = x_start
            span_end = x_start + visible_width
            
            for band in layout:
                # 計算顏色帶與進度條的重疊區域
                overlap_start = max(span_start, band["start"])
                overlap_end = min(span_end, band["end"])
                
                if overlap_end > overlap_start:
                    color_spans.append(
                        {
                            "color": band["color"],
                            "start": int(overlap_start),
                            "end": int(overlap_end),
                        }
                    )
        
        segments.append(
            {
                "start": round(float(start), 6),
                "end": round(float(end), 6),
                "width": int(visible_width),
                "x_start": int(x_start),
                "color_spans": color_spans,
                "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
            }
        )
        prev_width = visible_width
    
    # 追加倒數結束後的分段
    segments.append(
        {
            "start": round(float(countdown), 6),
            "end": round(float(total_duration), 6),
            "width": 0,
            "x_start": bar_width,
            "color_spans": [],
            "corner_radius": PROGRESS_BAR_CORNER_RADIUS,
        }
    )
    
    return segments
