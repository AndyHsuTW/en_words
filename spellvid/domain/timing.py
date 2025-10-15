"""時間軸與計時器邏輯模組

此模組負責計算視頻時間軸、格式化倒數計時器文字,為上層應用服務提供時間相關的資料。

職責:
- 格式化倒數計時器文字(秒 → "M:SS" 或 "SS")
- 計算視頻時間軸(包含揭示、淡出等事件)
- 生成計時器更新時間點列表

設計原則:
- 純函數邏輯,不依賴任何基礎設施
- 回傳標準 Python 資料結構(str, dict, list)
- 拋出 ValueError 表示無效參數

Examples:
    >>> format_countdown_text(5.0)
    '5'

    >>> format_countdown_text(65.0)
    '1:05'

    >>> calculate_timer_updates(video_duration=10.0, update_interval=1.0)
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
"""

from typing import Dict, List, Any, Optional


# ========== 公開 API ==========


def format_countdown_text(seconds: float) -> str:
    """格式化倒數計時器文字

    Args:
        seconds: 剩餘秒數

    Returns:
        格式化的倒數文字:
        - 小於 60 秒: "5", "45"
        - 大於等於 60 秒: "1:00", "2:05"

    Examples:
        >>> format_countdown_text(5.0)
        '5'

        >>> format_countdown_text(45.0)
        '45'

        >>> format_countdown_text(60.0)
        '1:00'

        >>> format_countdown_text(65.0)
        '1:05'

        >>> format_countdown_text(5.9)
        '5'
    """
    # 負數處理:回傳 "0"
    if seconds < 0:
        return "0"

    # 向下取整
    total_seconds = int(seconds)

    # 小於 60 秒:只顯示秒
    if total_seconds < 60:
        return str(total_seconds)

    # 大於等於 60 秒:顯示 M:SS 格式
    minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def calculate_timeline(
    video_duration: float,
    fadeout_duration: float = 0.0,
    reveal_time: Optional[float] = None,
    timer_update_interval: Optional[float] = None,
) -> Dict[str, Any]:
    """計算視頻時間軸

    Args:
        video_duration: 視頻總長度(秒)
        fadeout_duration: 淡出持續時間(秒),預設 0
        reveal_time: 字母揭示時間點(秒),可選
        timer_update_interval: 計時器更新間隔(秒),可選

    Returns:
        時間軸資料字典,包含:
        - total_duration: 總長度
        - video_start: 視頻開始時間
        - video_end: 視頻結束時間
        - events: 事件列表(按時間排序)

    Raises:
        ValueError: 當參數無效時

    Examples:
        >>> timeline = calculate_timeline(video_duration=10.0)
        >>> timeline['total_duration']
        10.0

        >>> timeline = calculate_timeline(
        ...     video_duration=10.0,
        ...     fadeout_duration=2.0,
        ...     reveal_time=3.0
        ... )
        >>> len([e for e in timeline['events'] if e['type'] == 'fadeout'])
        1
    """
    # 驗證參數
    if video_duration <= 0:
        raise ValueError(f"視頻長度 {video_duration:.2f} 秒必須大於零")

    if reveal_time is not None and reveal_time > video_duration:
        raise ValueError(
            f"揭示時間 {reveal_time:.2f} 秒超出視頻長度 {video_duration:.2f} 秒"
        )

    # 建立事件列表
    events: List[Dict[str, Any]] = []

    # 視頻開始事件
    events.append({"type": "video_start", "time": 0.0})

    # 揭示事件
    if reveal_time is not None:
        events.append({"type": "reveal", "time": reveal_time})

    # 淡出事件
    if fadeout_duration > 0:
        fadeout_start = video_duration - fadeout_duration
        events.append({
            "type": "fadeout",
            "time": fadeout_start,
            "duration": fadeout_duration,
        })

    # 計時器更新事件
    if timer_update_interval is not None and timer_update_interval > 0:
        timer_updates = calculate_timer_updates(
            video_duration, timer_update_interval
        )
        for update_time in timer_updates:
            events.append({"type": "timer_update", "time": update_time})

    # 視頻結束事件
    events.append({"type": "video_end", "time": video_duration})

    # 依時間排序
    events.sort(key=lambda e: e["time"])

    return {
        "total_duration": video_duration,
        "video_start": 0.0,
        "video_end": video_duration,
        "events": events,
    }


def calculate_timer_updates(
    video_duration: float,
    update_interval: float
) -> List[float]:
    """計算計時器更新時間點列表

    Args:
        video_duration: 視頻總長度(秒)
        update_interval: 更新間隔(秒)

    Returns:
        更新時間點列表(秒)

    Examples:
        >>> calculate_timer_updates(video_duration=10.0, update_interval=1.0)
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        >>> calculate_timer_updates(video_duration=5.0, update_interval=0.5)
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    """
    updates: List[float] = []
    current_time = 0.0

    while current_time < video_duration:
        updates.append(current_time)
        current_time += update_interval

    return updates
