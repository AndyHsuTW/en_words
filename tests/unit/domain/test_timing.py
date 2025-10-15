"""單元測試: 時間軸與計時器邏輯

此測試驗證 domain/timing.py 中的時間軸計算與計時器格式化功能,包括:
- 倒數計時器文字格式化
- 視頻時間軸計算
- 事件觸發時機規劃

測試策略:
1. 純邏輯測試,不依賴外部資源
2. 驗證時間格式化的正確性
3. 邊界情況處理(0 秒、負數等)
"""

import pytest


class TestCountdownFormatting:
    """倒數計時器格式化測試"""

    def test_format_countdown_seconds_only(self):
        """TC-TIMING-001: 驗證秒數格式化

        測試案例: 小於 60 秒的倒數
        前置條件: 輸入秒數 < 60
        預期結果: 格式化為 "SS" 或 "S"
        """
        from spellvid.domain.timing import format_countdown_text

        # 個位數秒
        assert format_countdown_text(5.0) == "5"
        assert format_countdown_text(9.0) == "9"

        # 十位數秒
        assert format_countdown_text(45.0) == "45"
        assert format_countdown_text(59.0) == "59"

    def test_format_countdown_minutes_seconds(self):
        """TC-TIMING-002: 驗證分:秒格式化

        測試案例: >= 60 秒的倒數
        前置條件: 輸入秒數 >= 60
        預期結果: 格式化為 "M:SS"
        """
        from spellvid.domain.timing import format_countdown_text

        # 整分鐘
        assert format_countdown_text(60.0) == "1:00"
        assert format_countdown_text(120.0) == "2:00"

        # 分+秒
        assert format_countdown_text(65.0) == "1:05"
        assert format_countdown_text(90.0) == "1:30"
        assert format_countdown_text(125.0) == "2:05"

    def test_format_countdown_zero(self):
        """TC-TIMING-003: 驗證零秒的格式化

        測試案例: 倒數到 0
        預期結果: "0"
        """
        from spellvid.domain.timing import format_countdown_text

        assert format_countdown_text(0.0) == "0"

    def test_format_countdown_fractional(self):
        """TC-TIMING-004: 驗證小數秒的處理

        測試案例: 非整數秒數
        前置條件: 輸入 float 秒數
        預期結果: 取整或四捨五入
        """
        from spellvid.domain.timing import format_countdown_text

        # 應該向下取整(floor)
        assert format_countdown_text(5.9) == "5"
        assert format_countdown_text(59.1) == "59"

        # 分秒格式
        assert format_countdown_text(65.8) == "1:05"

    def test_format_countdown_negative(self):
        """TC-TIMING-005: 驗證負數的處理

        測試案例: 負數倒數時間
        預期結果: 回傳 "0"
        """
        from spellvid.domain.timing import format_countdown_text

        # 選項 2: 回傳 "0"
        assert format_countdown_text(-5.0) == "0"


class TestTimelineCalculation:
    """時間軸計算測試"""

    def test_calculate_timeline_basic(self):
        """TC-TIMING-006: 驗證基本時間軸計算

        測試案例: 單一視頻的時間軸
        前置條件: 視頻長度 10 秒,無淡入淡出
        預期結果: 時間軸事件列表正確
        """
        from spellvid.domain.timing import calculate_timeline

        timeline = calculate_timeline(
            video_duration=10.0,
            fadeout_duration=0.0
        )

        assert timeline["total_duration"] == 10.0
        assert timeline["video_start"] == 0.0
        assert timeline["video_end"] == 10.0
        assert len(timeline["events"]) >= 1

    def test_calculate_timeline_with_fadeout(self):
        """TC-TIMING-007: 驗證含淡出的時間軸

        測試案例: 視頻長度 10 秒,最後 2 秒淡出
        預期結果: 淡出事件在第 8 秒觸發
        """
        from spellvid.domain.timing import calculate_timeline

        timeline = calculate_timeline(
            video_duration=10.0,
            fadeout_duration=2.0
        )

        # 尋找淡出事件
        fadeout_event = next(
            e for e in timeline["events"]
            if e["type"] == "fadeout"
        )

        assert fadeout_event["time"] == 8.0
        assert fadeout_event["duration"] == 2.0

    def test_calculate_timeline_reveal_event(self):
        """TC-TIMING-008: 驗證揭示事件的計算

        測試案例: 字母揭示時間點
        前置條件: 揭示在第 3 秒
        預期結果: 時間軸包含揭示事件
        """
        from spellvid.domain.timing import calculate_timeline

        timeline = calculate_timeline(
            video_duration=10.0,
            reveal_time=3.0
        )

        reveal_event = next(
            e for e in timeline["events"]
            if e["type"] == "reveal"
        )

        assert reveal_event["time"] == 3.0

    def test_calculate_timeline_multiple_events(self):
        """TC-TIMING-009: 驗證多事件時間軸

        測試案例: 包含揭示、淡出、計時器更新等多個事件
        預期結果: 事件依時間排序,無重疊衝突
        """
        from spellvid.domain.timing import calculate_timeline

        timeline = calculate_timeline(
            video_duration=10.0,
            reveal_time=3.0,
            fadeout_duration=2.0,
            timer_update_interval=1.0
        )

        events = timeline["events"]

        # 事件應該按時間排序
        assert all(
            events[i]["time"] <= events[i+1]["time"]
            for i in range(len(events) - 1)
        )

        # 至少有揭示和淡出兩個事件
        event_types = {e["type"] for e in events}
        assert "reveal" in event_types
        assert "fadeout" in event_types


class TestTimerUpdateLogic:
    """計時器更新邏輯測試"""

    def test_calculate_timer_updates(self):
        """TC-TIMING-010: 驗證計時器更新點計算

        測試案例: 10 秒視頻,每秒更新一次
        預期結果: 生成 10 個更新時間點
        """
        from spellvid.domain.timing import calculate_timer_updates

        updates = calculate_timer_updates(
            video_duration=10.0,
            update_interval=1.0
        )

        assert len(updates) == 10
        assert updates[0] == 0.0
        assert updates[-1] == 9.0

    def test_calculate_timer_updates_non_integer(self):
        """TC-TIMING-011: 驗證非整數間隔的處理

        測試案例: 更新間隔 0.5 秒
        預期結果: 正確處理小數間隔
        """
        from spellvid.domain.timing import calculate_timer_updates

        updates = calculate_timer_updates(
            video_duration=5.0,
            update_interval=0.5
        )

        assert len(updates) == 10
        assert updates[0] == 0.0
        assert updates[1] == 0.5
        assert updates[-1] == 4.5


class TestEdgeCases:
    """邊界情況測試"""

    def test_format_countdown_very_long(self):
        """TC-TIMING-012: 驗證長時間格式化

        測試案例: 超過 1 小時的倒數
        預期結果: 正確格式化
        """
        from spellvid.domain.timing import format_countdown_text

        # 1 小時 (60 分鐘)
        assert format_countdown_text(3600.0) == "60:00"

    def test_calculate_timeline_zero_duration(self):
        """TC-TIMING-013: 驗證零長度視頻

        測試案例: 視頻長度為 0
        預期結果: 拋出 ValueError
        """
        from spellvid.domain.timing import calculate_timeline

        with pytest.raises(ValueError, match="視頻長度.*必須大於零"):
            calculate_timeline(video_duration=0.0)

    def test_calculate_timeline_reveal_after_end(self):
        """TC-TIMING-014: 驗證揭示時間超出範圍

        測試案例: 揭示時間 > 視頻長度
        預期結果: 拋出 ValueError
        """
        from spellvid.domain.timing import calculate_timeline

        with pytest.raises(ValueError, match="揭示時間.*超出視頻長度"):
            calculate_timeline(
                video_duration=10.0,
                reveal_time=15.0
            )


# 標記此測試模組為單元測試
pytestmark = pytest.mark.unit
