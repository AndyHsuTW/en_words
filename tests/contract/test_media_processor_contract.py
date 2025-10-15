"""契約測試: IMediaProcessor Protocol

此測試驗證媒體處理工具包裝器是否正確實作 IMediaProcessor Protocol。

測試策略:
1. 驗證包裝器實作 Protocol
2. 驗證所有方法存在且可呼叫
3. 驗證方法回傳值符合契約要求
"""

import pytest


class TestMediaProcessorContract:
    """IMediaProcessor Protocol 契約測試套件

    驗證 FFmpegWrapper 是否符合 IMediaProcessor 介面定義。
    """

    def test_ffmpeg_wrapper_implements_interface(self):
        """TC-CONTRACT-016: 驗證 FFmpegWrapper 實作 IMediaProcessor

        測試案例: Protocol 符合性檢查
        前置條件: IMediaProcessor 已定義為 @runtime_checkable Protocol
        預期結果: isinstance(wrapper, IMediaProcessor) 回傳 True
        """
        from spellvid.infrastructure.media.interface import IMediaProcessor
        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        assert isinstance(wrapper, IMediaProcessor), \
            "FFmpegWrapper 必須實作 IMediaProcessor Protocol"

    def test_wrapper_has_required_methods(self):
        """TC-CONTRACT-017: 驗證 FFmpegWrapper 實作所有必要方法

        測試案例: 方法完整性
        前置條件: FFmpegWrapper 已實作
        預期結果: wrapper 具有 4 個方法
        """
        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        required_methods = [
            'probe_duration',
            'probe_dimensions',
            'extract_audio',
            'ensure_ffmpeg_available'
        ]

        for method_name in required_methods:
            assert hasattr(wrapper, method_name), \
                f"FFmpegWrapper 缺少 {method_name} 方法"
            assert callable(getattr(wrapper, method_name)), \
                f"FFmpegWrapper.{method_name} 必須可呼叫"

    def test_probe_duration_with_valid_file(self):
        """TC-CONTRACT-018: 驗證 probe_duration 回傳浮點數時長

        測試案例: 回傳值型別檢查
        前置條件: FFmpegWrapper.probe_duration 已實作
        預期結果: 回傳 float 型別的秒數
        """
        from pathlib import Path

        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        # 使用專案中的測試音訊檔案
        test_audio = (
            Path(__file__).parent.parent / "assets" / "test_audio.mp3"
        )

        if test_audio.exists():
            duration = wrapper.probe_duration(str(test_audio))

            assert isinstance(duration, float), \
                "probe_duration 必須回傳 float"
            assert duration > 0, "音訊時長必須 > 0"
        else:
            pytest.skip("找不到測試音訊檔案")

    def test_probe_duration_file_not_found(self):
        """TC-CONTRACT-019: 驗證 probe_duration 對不存在檔案拋出異常

        測試案例: 錯誤處理
        前置條件: FFmpegWrapper.probe_duration 已實作
        預期結果: 拋出 FileNotFoundError
        """
        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        with pytest.raises(FileNotFoundError):
            wrapper.probe_duration("/nonexistent/file.mp3")

    def test_probe_dimensions_with_valid_video(self):
        """TC-CONTRACT-020: 驗證 probe_dimensions 回傳尺寸 tuple

        測試案例: 回傳值型別檢查
        前置條件: FFmpegWrapper.probe_dimensions 已實作
        預期結果: 回傳 (width, height) tuple
        """
        from pathlib import Path

        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        # 使用專案中的測試視頻檔案
        test_video = (
            Path(__file__).parent.parent / "assets" / "test_video.mp4"
        )

        if test_video.exists():
            width, height = wrapper.probe_dimensions(str(test_video))

            assert isinstance(width, int), "寬度必須是整數"
            assert isinstance(height, int), "高度必須是整數"
            assert width > 0, "視頻寬度必須 > 0"
            assert height > 0, "視頻高度必須 > 0"
        else:
            pytest.skip("找不到測試視頻檔案")

    def test_extract_audio_signature(self):
        """TC-CONTRACT-021: 驗證 extract_audio 方法簽章

        測試案例: 方法簽章符合性
        前置條件: FFmpegWrapper.extract_audio 已實作
        預期結果: 接受 (video_path, output_path) 並成功提取音訊
        """
        import tempfile
        from pathlib import Path

        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        test_video = (
            Path(__file__).parent.parent / "assets" / "test_video.mp4"
        )

        if test_video.exists():
            with tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            ) as tmp:
                output_path = tmp.name

            try:
                wrapper.extract_audio(str(test_video), output_path)

                # 驗證音訊檔案已建立
                assert Path(output_path).exists(), \
                    "extract_audio 應該建立輸出檔案"
                assert Path(output_path).stat().st_size > 0, \
                    "提取的音訊檔案不應為空"
            finally:
                if Path(output_path).exists():
                    Path(output_path).unlink()
        else:
            pytest.skip("找不到測試視頻檔案")

    def test_ensure_ffmpeg_available_returns_bool(self):
        """TC-CONTRACT-022: 驗證 ensure_ffmpeg_available 回傳布林值

        測試案例: 回傳值型別檢查
        前置條件: FFmpegWrapper.ensure_ffmpeg_available 已實作
        預期結果: 回傳 True 或 False
        """
        from spellvid.infrastructure.media.ffmpeg_wrapper import (
            FFmpegWrapper,
        )

        wrapper = FFmpegWrapper()

        result = wrapper.ensure_ffmpeg_available()

        assert isinstance(result, bool), \
            "ensure_ffmpeg_available 必須回傳布林值"


# 標記此測試模組為契約測試
pytestmark = pytest.mark.contract
