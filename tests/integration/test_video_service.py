"""整合測試: VideoService - 視頻生成服務

此測試驗證 video_service.render_video() 是否正確協調 domain 與 infrastructure 層。

測試策略:
1. 使用 mock 基礎設施適配器
2. 驗證 service 正確呼叫 domain 計算
3. 驗證 service 正確組裝視頻組件
4. 驗證 dry-run 與實際渲染行為差異
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, MagicMock
from pathlib import Path


class TestVideoServiceIntegration:
    """VideoService 整合測試套件

    驗證 render_video() 是否正確協調各層邏輯。
    """

    def test_render_video_dry_run_returns_metadata(self):
        """TC-APP-001: 驗證 dry-run 模式回傳 metadata 不產生檔案

        測試案例: Dry-run 行為
        前置條件: VideoService 已實作
        預期結果: 回傳 metadata 字典,不呼叫 composer.render_to_file
        """
        from spellvid.application.video_service import render_video
        from spellvid.shared.types import VideoConfig

        config = VideoConfig(
            letters="I i",
            word_en="Ice",
            word_zh="bing ice",
        )

        # Mock composer
        mock_composer = Mock()

        result = render_video(
            config=config,
            output_path="out/test.mp4",
            dry_run=True,
            composer=mock_composer
        )

        assert result["success"] is True, "Dry-run 應該成功"
        assert "metadata" in result, "應該包含 metadata"
        assert "duration" in result, "應該包含 duration"
        assert mock_composer.render_to_file.call_count == 0, \
            "Dry-run 不應該呼叫 render_to_file"

    def test_render_video_calls_domain_layout(self):
        """TC-APP-002: 驗證 render_video 呼叫 domain 佈局計算

        測試案例: Domain 層協調
        前置條件: VideoService 與 domain.layout 已實作
        預期結果: 呼叫 compute_layout_bboxes() 並使用結果
        """
        from spellvid.application.video_service import render_video
        from spellvid.shared.types import VideoConfig
        from unittest.mock import patch

        config = VideoConfig(
            letters="A a",
            word_en="Apple",
            word_zh="apple fruit"
        )

        with patch("spellvid.application.video_service.compute_layout_bboxes") as mock_layout:
            mock_layout.return_value = MagicMock()
            mock_composer = Mock()

            render_video(config, "out/test.mp4",
                         dry_run=True, composer=mock_composer)

            assert mock_layout.called, "應該呼叫 compute_layout_bboxes"
            assert mock_layout.call_args[0][0] == config, \
                "應該傳入 VideoConfig"

    def test_render_video_composes_clips_in_order(self):
        """TC-APP-003: 驗證 render_video 按順序組裝 clips

        測試案例: Clip 組裝順序
        前置條件: VideoService 已實作
        預期結果: 背景 → 圖片 → 文字 → 計時器 → 進度條
        """
        pytest.skip("尚未實作 VideoService")

        # from spellvid.application.video_service import render_video
        # from spellvid.shared.types import VideoConfig
        #
        # config = VideoConfig(
        #     letters="B b",
        #     word_en="Ball",
        #     word_zh="球",
        #     image_path="assets/ball.png"
        # )
        #
        # mock_composer = Mock()
        # mock_composer.create_color_clip.return_value = Mock()
        # mock_composer.create_image_clip.return_value = Mock()
        # mock_composer.compose_clips.return_value = Mock()
        #
        # render_video(config, "out/test.mp4", dry_run=True, composer=mock_composer)
        #
        # # 驗證呼叫順序
        # assert mock_composer.create_color_clip.called, "應該建立背景"
        # assert mock_composer.create_image_clip.called, "應該建立圖片 clip"
        # assert mock_composer.compose_clips.called, "應該組合所有 clips"

    def test_render_video_applies_fadeout_when_requested(self):
        """TC-APP-004: 驗證 render_video 套用淡出效果

        測試案例: 效果應用
        前置條件: VideoService 與 domain.effects 已實作
        預期結果: 呼叫 apply_fadeout() 並套用到 final clip
        """
        pytest.skip("尚未實作 VideoService")

        # from spellvid.application.video_service import render_video
        # from spellvid.shared.types import VideoConfig
        #
        # config = VideoConfig(
        #     letters="C c",
        #     word_en="Cat",
        #     word_zh="貓",
        #     fadeout_sec=1.0
        # )
        #
        # mock_composer = Mock()
        # mock_composer.apply_fadeout.return_value = Mock()
        #
        # render_video(config, "out/test.mp4", dry_run=True, composer=mock_composer)
        #
        # assert mock_composer.apply_fadeout.called, \
        #     "fadeout_sec > 0 時應該呼叫 apply_fadeout"

    def test_render_video_actual_render_creates_file(self):
        """TC-APP-005: 驗證實際渲染產生檔案

        測試案例: 實際渲染行為
        前置條件: VideoService 已實作
        預期結果: dry_run=False 時呼叫 composer.render_to_file()
        """
        pytest.skip("尚未實作 VideoService")

        # from spellvid.application.video_service import render_video
        # from spellvid.shared.types import VideoConfig
        #
        # config = VideoConfig(
        #     letters="D d",
        #     word_en="Dog",
        #     word_zh="狗"
        # )
        #
        # mock_composer = Mock()
        # mock_final_clip = Mock()
        # mock_composer.compose_clips.return_value = mock_final_clip
        #
        # result = render_video(
        #     config,
        #     "out/test.mp4",
        #     dry_run=False,
        #     composer=mock_composer
        # )
        #
        # assert mock_composer.render_to_file.called, \
        #     "dry_run=False 時應該呼叫 render_to_file"
        # assert mock_composer.render_to_file.call_args[0][0] == mock_final_clip, \
        #     "應該渲染 final clip"
        # assert result["output_path"] == "out/test.mp4", \
        #     "應該回傳輸出路徑"

    def test_render_video_skip_ending_omits_ending_clip(self):
        """TC-APP-006: 驗證 skip_ending 參數控制片尾

        測試案例: 片尾跳過邏輯
        前置條件: VideoService 已實作
        預期結果: skip_ending=True 時不組裝片尾 clip
        """
        pytest.skip("尚未實作 VideoService")

        # from spellvid.application.video_service import render_video
        # from spellvid.shared.types import VideoConfig
        #
        # config = VideoConfig(
        #     letters="E e",
        #     word_en="End",
        #     word_zh="結尾"
        # )
        #
        # mock_composer = Mock()
        # clips_composed = []
        #
        # def capture_compose(clips, size):
        #     clips_composed.extend(clips)
        #     return Mock()
        #
        # mock_composer.compose_clips.side_effect = capture_compose
        #
        # # 測試 skip_ending=True
        # render_video(config, "out/test.mp4", dry_run=True,
        #              skip_ending=True, composer=mock_composer)
        #
        # # 驗證 clips 中沒有 ending (需要根據實際實作調整判斷邏輯)
        # # assert all("ending" not in str(clip) for clip in clips_composed)

    def test_render_video_handles_missing_resources(self):
        """TC-APP-007: 驗證缺少資源時拋出異常

        測試案例: 錯誤處理
        前置條件: VideoService 已實作
        預期結果: 資源檔案不存在時拋出 FileNotFoundError
        """
        from spellvid.application.video_service import render_video
        from spellvid.shared.types import VideoConfig

        config = VideoConfig(
            letters="F f",
            word_en="Fail",
            word_zh="fail error",
            image_path="/nonexistent/image.png"
        )

        with pytest.raises(FileNotFoundError):
            render_video(config, "out/test.mp4", dry_run=False)

    def test_render_video_performance_dry_run(self):
        """TC-APP-008: 驗證 dry-run 效能 < 100ms

        測試案例: 效能基準
        前置條件: VideoService 已實作
        預期結果: dry-run 執行時間 < 100ms
        """
        pytest.skip("尚未實作 VideoService")

        # import time
        # from spellvid.application.video_service import render_video
        # from spellvid.shared.types import VideoConfig
        #
        # config = VideoConfig(
        #     letters="G g",
        #     word_en="Go",
        #     word_zh="走"
        # )
        #
        # mock_composer = Mock()
        # mock_composer.create_color_clip.return_value = Mock()
        # mock_composer.create_image_clip.return_value = Mock()
        # mock_composer.compose_clips.return_value = Mock()
        #
        # start = time.time()
        # render_video(config, "out/test.mp4", dry_run=True, composer=mock_composer)
        # elapsed = time.time() - start
        #
        # assert elapsed < 0.1, \
        #     f"Dry-run 應該 < 100ms,實際 {elapsed*1000:.1f}ms"


# 標記此測試模組為整合測試
pytestmark = pytest.mark.integration
