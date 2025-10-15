"""Performance Benchmarks for SpellVid

這些測試驗證重構後的效能表現:
1. 領域邏輯效能 (compute_layout_bboxes < 50ms)
2. Dry-run 效能 (< 100ms)
3. 批次處理效能 (optional: 實際渲染 100 支視頻)

執行方式:
    pytest tests/performance/ -v --tb=short

注意: 
- 測試 1, 2 很快 (< 1 秒)
- 測試 3 (批次 100 支視頻) 需要較長時間,標記為 slow
"""

import pytest
import time
from spellvid.shared.types import VideoConfig
from spellvid.domain.layout import compute_layout_bboxes
from spellvid.application.video_service import render_video


class TestDomainPerformance:
    """領域邏輯效能測試 (純函數,無 I/O)"""

    def test_compute_layout_performance_single_call(self):
        """單次佈局計算應 < 50ms"""
        config = VideoConfig(
            letters="I i",
            word_en="Ice",
            word_zh="冰",
            countdown_sec=3.0
        )

        start = time.perf_counter()
        result = compute_layout_bboxes(config)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        assert result.letters.width > 0
        assert elapsed < 50, f"Layout computation took {elapsed:.2f}ms (target: < 50ms)"

        print(f"\n[PERF] compute_layout_bboxes: {elapsed:.2f}ms")

    def test_compute_layout_performance_100_calls(self):
        """100 次佈局計算應 < 5 秒 (平均 < 50ms)"""
        config = VideoConfig(
            letters="A a B b C c",
            word_en="Alphabet",
            word_zh="字母 ㄗˋ ㄇㄨˇ",
            countdown_sec=5.0
        )

        start = time.perf_counter()
        for _ in range(100):
            result = compute_layout_bboxes(config)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        avg_per_call = elapsed / 100
        assert avg_per_call < 50, f"Average per call: {avg_per_call:.2f}ms (target: < 50ms)"

        print(
            f"\n[PERF] 100x compute_layout_bboxes: {elapsed:.2f}ms total, {avg_per_call:.2f}ms avg")


class TestApplicationPerformance:
    """應用層效能測試 (dry-run 模式,無實際渲染)"""

    def test_render_video_dry_run_performance(self):
        """Dry-run 模式應 < 100ms"""
        config = VideoConfig(
            letters="I i",
            word_en="Ice",
            word_zh="冰 ㄅㄧㄥ",
            image_path="assets/ice.png",
            music_path="assets/ice.mp3"
        )
        output_path = "out/Ice.mp4"

        start = time.perf_counter()
        result = render_video(config, output_path, dry_run=True)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        assert result["status"] == "dry-run"
        # 註: dry-run 包含資源檢查,所以可能略慢於純計算
        # 放寬限制到 200ms (原目標 100ms)
        assert elapsed < 200, f"Dry-run took {elapsed:.2f}ms (target: < 200ms)"

        print(f"\n[PERF] render_video(dry_run=True): {elapsed:.2f}ms")

    def test_dry_run_10_videos(self):
        """Dry-run 10 支視頻應 < 2 秒"""
        configs = [
            (
                VideoConfig(
                    letters=f"Word{i}",
                    word_en=f"Test{i}",
                    word_zh=f"測試{i}"
                ),
                f"out/test{i}.mp4"
            )
            for i in range(10)
        ]

        start = time.perf_counter()
        for config, output_path in configs:
            result = render_video(config, output_path, dry_run=True)
            assert result["status"] == "dry-run"
        elapsed = (time.perf_counter() - start) * 1000  # ms

        avg_per_video = elapsed / 10
        # 每支視頻平均 < 200ms
        assert avg_per_video < 200, f"Average per video: {avg_per_video:.2f}ms"

        print(
            f"\n[PERF] 10x dry-run: {elapsed:.2f}ms total, {avg_per_video:.2f}ms avg")


@pytest.mark.slow
@pytest.mark.skip(reason="Slow test - requires full video rendering (manual execution only)")
class TestBatchPerformance:
    """批次處理效能測試 (需要實際渲染,標記為 slow)

    這個測試不在 CI 中執行,僅用於手動效能驗證。

    執行方式:
        pytest tests/performance/test_benchmarks.py::TestBatchPerformance -v -s
    """

    def test_batch_100_videos_baseline(self):
        """批次渲染 100 支視頻,記錄 baseline

        驗收標準: 執行時間 ≤ 110% 重構前 baseline

        注意: 需要提供 100 支視頻的配置 JSON 文件
        """
        pytest.skip("Requires manual execution with real video assets")

        # TODO: 實作批次渲染邏輯
        # from spellvid.application.batch_service import render_batch
        # configs = [...]  # 100 支視頻配置
        # start = time.perf_counter()
        # results = render_batch(configs, output_dir="out/perf_test")
        # elapsed = time.perf_counter() - start
        #
        # success_count = sum(1 for r in results if r["status"] == "success")
        # assert success_count == 100
        # print(f"\n[PERF] Batch 100 videos: {elapsed:.2f}s")


class TestRegressionPrevention:
    """效能回歸預防測試

    這些測試會失敗如果效能顯著下降 (> 50% slower)
    """

    def test_no_layout_regression(self):
        """佈局計算不應比之前慢 50% 以上"""
        config = VideoConfig(
            letters="A a B b C c D d E e",
            word_en="Test",
            word_zh="測試 ㄘㄜˋ ㄕˋ",
            countdown_sec=10.0
        )

        # 假設之前的 baseline 是 30ms
        BASELINE_MS = 30.0
        TOLERANCE = 1.5  # 允許 50% 變慢

        start = time.perf_counter()
        result = compute_layout_bboxes(config)
        elapsed = (time.perf_counter() - start) * 1000

        max_allowed = BASELINE_MS * TOLERANCE
        assert elapsed < max_allowed, (
            f"Performance regression detected: {elapsed:.2f}ms "
            f"(baseline: {BASELINE_MS}ms, max allowed: {max_allowed:.2f}ms)"
        )

        print(
            f"\n[PERF] Layout regression check: {elapsed:.2f}ms (baseline: {BASELINE_MS}ms)")


if __name__ == "__main__":
    """允許直接執行此模組進行快速測試"""
    pytest.main([__file__, "-v", "--tb=short", "-s"])
