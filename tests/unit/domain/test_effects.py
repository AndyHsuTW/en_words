"""單元測試: 視頻效果邏輯

此測試驗證 domain/effects.py 中的視頻效果應用邏輯,包括:
- Fadeout 淡出效果參數計算
- Fadein 淡入效果參數計算
- 過渡效果的時間軸規劃

測試策略:
1. 純邏輯測試,不依賴 MoviePy
2. 驗證效果參數的正確性(持續時間、觸發時機)
3. 邊界情況處理
"""

import pytest


class TestFadeoutEffect:
    """淡出效果測試"""

    def test_apply_fadeout_basic(self):
        """TC-EFFECT-001: 驗證基本淡出參數計算

        測試案例: 標準淡出設定
        前置條件: 視頻長度 5 秒,淡出持續 1 秒
        預期結果: 淡出從第 4 秒開始,持續 1 秒
        """
        from spellvid.domain.effects import apply_fadeout

        # 模擬 5 秒視頻,最後 1 秒淡出
        result = apply_fadeout(
            clip_duration=5.0,
            fadeout_duration=1.0
        )

        assert result["start_time"] == 4.0, "淡出應該從第 4 秒開始"
        assert result["duration"] == 1.0, "淡出持續 1 秒"
        assert result["clip_duration"] == 5.0, "視頻總長度 5 秒"

    def test_apply_fadeout_zero_duration(self):
        """TC-EFFECT-002: 驗證零淡出持續時間

        測試案例: 不應用淡出效果
        前置條件: fadeout_duration 為 0
        預期結果: 回傳 None 或指示不應用效果
        """
        from spellvid.domain.effects import apply_fadeout

        result = apply_fadeout(
            clip_duration=5.0,
            fadeout_duration=0.0
        )

        assert result is None or result["duration"] == 0.0

    def test_apply_fadeout_exceeds_duration(self):
        """TC-EFFECT-003: 驗證淡出時間過長的處理

        測試案例: 淡出時間 >= 視頻長度
        前置條件: fadeout_duration >= clip_duration
        預期結果: 拋出 ValueError 或限制為最大可用時長
        """
        from spellvid.domain.effects import apply_fadeout

        # 淡出時間 > 視頻長度
        with pytest.raises(ValueError, match="持續時間.*超過.*最大值"):
            apply_fadeout(clip_duration=3.0, fadeout_duration=5.0)

        # 淡出時間 = 視頻長度(邊界)
        with pytest.raises(ValueError):
            apply_fadeout(clip_duration=3.0, fadeout_duration=3.0)

    def test_apply_fadeout_short_clip(self):
        """TC-EFFECT-004: 驗證短視頻的淡出

        測試案例: 視頻長度 < 2 秒
        前置條件: 視頻長度 1.5 秒,淡出 0.5 秒
        預期結果: 正確計算淡出起始時間
        """
        from spellvid.domain.effects import apply_fadeout

        result = apply_fadeout(
            clip_duration=1.5,
            fadeout_duration=0.5
        )

        assert result["start_time"] == 1.0
        assert result["duration"] == 0.5


class TestFadeinEffect:
    """淡入效果測試"""

    def test_apply_fadein_basic(self):
        """TC-EFFECT-005: 驗證基本淡入參數計算

        測試案例: 標準淡入設定
        前置條件: 淡入持續 0.5 秒
        預期結果: 淡入從第 0 秒開始,持續 0.5 秒
        """
        from spellvid.domain.effects import apply_fadein

        result = apply_fadein(fadein_duration=0.5)

        assert result["start_time"] == 0.0, "淡入從視頻開始"
        assert result["duration"] == 0.5, "淡入持續 0.5 秒"

    def test_apply_fadein_zero_duration(self):
        """TC-EFFECT-006: 驗證零淡入持續時間

        測試案例: 不應用淡入效果
        預期結果: 回傳 None
        """
        from spellvid.domain.effects import apply_fadein

        result = apply_fadein(fadein_duration=0.0)

        assert result is None or result["duration"] == 0.0


class TestTransitionPlanning:
    """過渡效果規劃測試"""

    def test_plan_transition_basic(self):
        """TC-EFFECT-007: 驗證基本過渡規劃

        測試案例: 兩個 clip 之間的交叉淡化
        前置條件: clip1 長度 5 秒,clip2 長度 3 秒,過渡 0.5 秒
        預期結果: 計算出正確的重疊時間
        """
        from spellvid.domain.effects import plan_transition

        result = plan_transition(
            clip1_duration=5.0,
            clip2_duration=3.0,
            transition_duration=0.5
        )

        # clip1 應該在 4.5 秒開始淡出
        assert result["clip1_fadeout_start"] == 4.5
        # clip2 應該在 4.5 秒開始(重疊開始點)
        assert result["clip2_start_time"] == 4.5
        # 總長度 = clip1_duration + clip2_duration - transition_duration
        assert result["total_duration"] == 7.5

    def test_plan_transition_no_overlap(self):
        """TC-EFFECT-008: 驗證無過渡的情況

        測試案例: transition_duration 為 0
        預期結果: clip 依序播放,無重疊
        """
        from spellvid.domain.effects import plan_transition

        result = plan_transition(
            clip1_duration=5.0,
            clip2_duration=3.0,
            transition_duration=0.0
        )

        assert result["clip2_start_time"] == 5.0, "clip2 在 clip1 結束後開始"
        assert result["total_duration"] == 8.0


class TestEffectValidation:
    """效果參數驗證測試"""

    def test_validate_effect_duration_negative(self):
        """TC-EFFECT-009: 驗證負數持續時間拒絕

        測試案例: 負數效果持續時間
        預期結果: 拋出 ValueError
        """
        from spellvid.domain.effects import validate_effect_duration

        with pytest.raises(ValueError, match="持續時間.*不能為負數"):
            validate_effect_duration(-1.0)

    def test_validate_effect_duration_too_large(self):
        """TC-EFFECT-010: 驗證過大持續時間拒絕

        測試案例: 效果持續時間 > 視頻長度
        預期結果: 拋出 ValueError
        """
        from spellvid.domain.effects import validate_effect_duration

        with pytest.raises(ValueError, match="持續時間.*超過.*最大值"):
            validate_effect_duration(
                duration=10.0,
                clip_duration=5.0
            )


# 標記此測試模組為單元測試
pytestmark = pytest.mark.unit
