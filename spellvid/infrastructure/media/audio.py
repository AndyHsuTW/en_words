"""音訊處理工具模組

此模組提供音訊生成和處理功能,主要用於視頻渲染中的音效處理。

主要功能:
- 合成嗶聲音效
- 生成 MoviePy AudioClip
"""

from typing import Any

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False
    np = None  # type: ignore


def synthesize_beeps(duration_sec: int = 3, rate_hz: int = 1) -> bytes:
    """合成嗶聲音訊的佔位資料.

    這是一個簡單的實作,返回代表嗶聲的位元組串,避免引入二進位依賴。
    主要用於測試和佔位用途,不產生實際音訊信號。

    Args:
        duration_sec: 總時長(秒),默認 3 秒
        rate_hz: 每秒嗶聲次數,默認 1 Hz

    Returns:
        表示嗶聲的位元組串 (b"BEEP" 的重複)

    Example:
        >>> beeps = synthesize_beeps(duration_sec=3, rate_hz=2)
        >>> len(beeps)  # 3 秒 × 2 Hz = 6 個 "BEEP"
        24
        >>> beeps
        b'BEEPBEEPBEEPBEEPBEEPBEEP'

    Notes:
        這不是真正的音訊生成,只是簡單的佔位符。
        真正的音訊生成應使用 make_beep() 配合 MoviePy。
    """
    return b"BEEP" * max(1, duration_sec * rate_hz)


def make_beep(
    start_sec: float,
    freq: float = 1000.0,
    length: float = 0.3
) -> Any:
    """生成短促的正弦波嗶聲 AudioClip.

    創建一個指定頻率和時長的嗶聲音訊片段,用於倒數計時或提示音效。
    返回的 AudioClip 已設定起始時間,可直接加入視頻的音訊軌道。

    Args:
        start_sec: 嗶聲在視頻中的起始時間(秒)
        freq: 正弦波頻率(Hz),默認 1000 Hz
        length: 嗶聲持續時長(秒),默認 0.3 秒

    Returns:
        MoviePy AudioClip 物件,已設定 start time

    Raises:
        RuntimeError: 如果 MoviePy 或 numpy 未安裝

    Example:
        >>> beep_clip = make_beep(start_sec=2.5)  # 2.5秒時播放嗶聲
        >>> beep_clip.duration
        0.3
        >>> beep_clip.start
        2.5

    Technical Details:
        - 採樣率: 44100 Hz (CD 音質)
        - 音量: 0.2 (20% 防止削波)
        - 聲道: 立體聲 (左右聲道相同)
        - 波形: 正弦波 sin(2πft)

    Implementation Notes:
        使用 numpy 生成正弦波樣本,然後包裝為 MoviePy AudioClip。
        時間參數 t 可能是陣列(向量化),因此使用 numpy 操作確保效能。
    """
    if not _HAS_NUMPY:
        raise RuntimeError("numpy is required for audio generation")

    try:
        import moviepy as mpy  # type: ignore
    except ImportError:
        raise RuntimeError("MoviePy is required for audio generation")

    def make_frame(t):
        """生成音訊幀的回調函數.

        Args:
            t: 時間(秒),可能是單一浮點數或 numpy 陣列

        Returns:
            立體聲音訊樣本陣列,形狀為 (n_samples, 2)
        """
        # 生成正弦波: A * sin(2πft)
        # 振幅 0.2 避免削波,頻率由 freq 決定
        mono = (np.sin(2 * np.pi * freq * t) * 0.2).astype(np.float32)

        # 轉換為立體聲(兩個聲道相同)
        # 確保形狀為 (n_samples, 2) 以匹配 MoviePy 期望
        try:
            stereo = np.column_stack((mono, mono))
        except Exception:
            # 如果 column_stack 失敗,嘗試 reshape
            stereo = mono.reshape(-1, 1)

        return stereo

    # 創建 AudioClip: 44100 Hz 採樣率,指定時長
    ac = mpy.AudioClip(make_frame, duration=length, fps=44100)

    # 設定在視頻中的起始時間
    return ac.with_start(start_sec)
