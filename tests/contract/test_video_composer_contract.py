"""契約測試: IVideoComposer Protocol

此測試驗證視頻合成引擎適配器是否正確實作 IVideoComposer Protocol。

測試策略:
1. 驗證適配器實作 Protocol (isinstance 檢查)
2. 驗證所有方法存在且可呼叫
3. 驗證方法回傳值符合契約要求
"""

import pytest
import numpy as np


class TestVideoComposerContract:
    """IVideoComposer Protocol 契約測試套件"""

    def test_moviepy_adapter_implements_interface(self):
        """TC-CONTRACT-001: 驗證 MoviePyAdapter 實作 IVideoComposer"""
        from spellvid.infrastructure.video.interface import IVideoComposer
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()

        assert isinstance(adapter, IVideoComposer), \
            "MoviePyAdapter 必須實作 IVideoComposer Protocol"

    def test_adapter_has_all_methods(self):
        """TC-CONTRACT-002: 驗證 MoviePyAdapter 實作所有方法"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()

        required_methods = [
            'create_color_clip',
            'create_image_clip',
            'create_video_clip',
            'compose_clips',
            'apply_fadeout',
            'render_to_file',
            'concatenate_clips'
        ]

        for method_name in required_methods:
            assert hasattr(adapter, method_name), \
                f"MoviePyAdapter 缺少 {method_name} 方法"
            assert callable(getattr(adapter, method_name)), \
                f"{method_name} 必須是可呼叫的方法"

    def test_create_color_clip_returns_clip(self):
        """TC-CONTRACT-003: 驗證 create_color_clip 回傳值"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        clip = adapter.create_color_clip(
            size=(100, 100),
            color=(255, 0, 0),
            duration=1.0
        )

        assert clip is not None
        assert hasattr(clip, 'duration')
        assert clip.duration == 1.0

    def test_create_image_clip_returns_clip(self):
        """TC-CONTRACT-004: 驗證 create_image_clip 回傳值"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        img = np.zeros((50, 100, 3), dtype=np.uint8)
        clip = adapter.create_image_clip(
            image_array=img,
            duration=2.0,
            position=(10, 10)
        )

        assert clip is not None
        assert hasattr(clip, 'duration')
        assert clip.duration == 2.0

    def test_compose_clips_returns_composite(self):
        """TC-CONTRACT-005: 驗證 compose_clips 回傳值"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        clip1 = adapter.create_color_clip((100, 100), (255, 0, 0), 1.0)
        clip2 = adapter.create_color_clip((50, 50), (0, 255, 0), 1.0)

        composed = adapter.compose_clips([clip1, clip2], size=(100, 100))

        assert composed is not None
        assert hasattr(composed, 'duration')

    def test_apply_fadeout_returns_clip(self):
        """TC-CONTRACT-006: 驗證 apply_fadeout 回傳值"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        clip = adapter.create_color_clip((100, 100), (255, 0, 0), 5.0)
        faded = adapter.apply_fadeout(clip, 1.0)

        assert faded is not None
        assert hasattr(faded, 'duration')
        assert faded.duration == 5.0  # 總時長不變

    def test_concatenate_clips_chain_method(self):
        """TC-CONTRACT-007: 驗證 concatenate_clips chain 方法"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        clip1 = adapter.create_color_clip((100, 100), (255, 0, 0), 2.0)
        clip2 = adapter.create_color_clip((100, 100), (0, 255, 0), 3.0)

        combined = adapter.concatenate_clips([clip1, clip2], method="chain")

        assert combined is not None
        assert hasattr(combined, 'duration')
        # chain 方法應該串接時間
        assert combined.duration == 5.0

    def test_concatenate_clips_invalid_method_raises(self):
        """TC-CONTRACT-008: 驗證不支援的 method 拋出異常"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()
        clip1 = adapter.create_color_clip((100, 100), (255, 0, 0), 2.0)

        with pytest.raises(ValueError, match="不支援的串接方法"):
            adapter.concatenate_clips([clip1], method="invalid_method")

    def test_create_video_clip_missing_file_raises(self):
        """TC-CONTRACT-009: 驗證不存在的視頻檔案拋出異常"""
        from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter

        adapter = MoviePyAdapter()

        with pytest.raises(FileNotFoundError, match="視頻檔案不存在"):
            adapter.create_video_clip(
                "/nonexistent/path/to/video.mp4",
                duration=5.0
            )


# 標記此測試模組為契約測試
pytestmark = pytest.mark.contract
