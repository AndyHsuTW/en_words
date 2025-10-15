"""媒體處理工具介面定義

此模組定義 IMediaProcessor Protocol,抽象化媒體處理工具(如 FFmpeg)的功能。

設計原則:
- Protocol 定義純粹的媒體資訊查詢與處理行為
- 不涉及複雜的編碼邏輯(由 IVideoComposer 處理)
- 專注於元資料查詢(duration, dimensions)和簡單轉換(extract_audio)
"""

from typing import Protocol, Tuple, Optional, runtime_checkable


@runtime_checkable
class IMediaProcessor(Protocol):
    """媒體處理工具介面

    此 Protocol 定義媒體檔案的資訊查詢與基本處理功能,
    隱藏底層工具(FFmpeg, ffprobe)的細節。

    實作者:
        - FFmpegWrapper: 當前使用的 FFmpeg 包裝器

    職責範圍:
        - 查詢媒體檔案元資料(時長、尺寸)
        - 提取音訊軌
        - 確保 FFmpeg 可用性
    """

    def probe_duration(
        self,
        media_path: str
    ) -> float:
        """查詢媒體檔案時長

        使用 ffprobe 或類似工具讀取音訊/視頻檔案的總時長。

        Args:
            media_path: 媒體檔案絕對路徑(.mp3, .mp4, .wav 等)

        Returns:
            時長,單位秒,精確度通常到毫秒

        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析時長(格式不支援或檔案損壞)

        Example:
            >>> duration = processor.probe_duration("/path/to/music.mp3")
            >>> duration
            183.52  # 3 分 3.52 秒
        """
        ...

    def probe_dimensions(
        self,
        video_path: str
    ) -> Tuple[int, int]:
        """查詢視頻尺寸

        讀取視頻檔案的寬度與高度資訊。

        Args:
            video_path: 視頻檔案絕對路徑(.mp4, .avi, .mov 等)

        Returns:
            (width, height) 像素尺寸 tuple

        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析尺寸(不是視頻檔案)

        Example:
            >>> w, h = processor.probe_dimensions("/path/to/video.mp4")
            >>> print(f"視頻解析度: {w}x{h}")
            視頻解析度: 1920x1080
        """
        ...

    def extract_audio(
        self,
        video_path: str,
        output_path: str,
        audio_codec: str = "mp3"
    ) -> None:
        """從視頻提取音訊軌

        將視頻檔案的音訊軌道提取並儲存為獨立音訊檔案。

        Args:
            video_path: 來源視頻檔案絕對路徑
            output_path: 輸出音訊檔案絕對路徑
            audio_codec: 音訊編碼器,支援 "mp3", "aac", "wav" 等

        Raises:
            FileNotFoundError: 來源視頻不存在
            RuntimeError: 視頻沒有音訊軌或轉換失敗
            IOError: 無法寫入輸出檔案

        Example:
            >>> processor.extract_audio(
            ...     "/path/to/video.mp4",
            ...     "/output/audio.mp3",
            ...     audio_codec="mp3"
            ... )
            # 建立 /output/audio.mp3
        """
        ...

    def ensure_ffmpeg_available(self) -> bool:
        """確保 FFmpeg 可用

        檢查 FFmpeg 執行檔是否可被呼叫。
        實作應該嘗試多種查找策略:
        1. 環境變數 FFMPEG_PATH
        2. 專案本地 FFmpeg/ 目錄
        3. 系統 PATH
        4. imageio-ffmpeg package

        Returns:
            True 若 FFmpeg 可用,False 否則

        Side Effects:
            可能會設定全域變數或快取 FFmpeg 路徑

        Example:
            >>> if processor.ensure_ffmpeg_available():
            ...     print("FFmpeg 就緒")
            ... else:
            ...     print("請安裝 FFmpeg")
            FFmpeg 就緒

        Note:
            此方法應該被 Application 層在啟動時呼叫,
            以及早偵測環境問題。
        """
        ...
