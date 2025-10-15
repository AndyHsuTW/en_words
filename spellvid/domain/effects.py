"""視頻效果邏輯模組

此模組負責計算視頻效果參數(淡入、淡出、過渡),為上層應用服務提供效果時間軸資料。

職責:
- 計算 fadeout 效果的起始時間與持續時間
- 計算 fadein 效果參數
- 規劃 transition 過渡效果的時間軸
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

from typing import Optional, Dict, Any


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
