"""媒體處理介面與實作

- interface.py: IMediaProcessor Protocol 定義
- ffmpeg_wrapper.py: FFmpeg 命令列包裝器(待實作)
"""

from .interface import IMediaProcessor

__all__ = ["IMediaProcessor"]
