import math

import pytest

from spellvid import utils


PROG_COLORS = utils.PROGRESS_BAR_COLORS
PROG_WIDTH = utils.PROGRESS_BAR_WIDTH
PROG_RATIOS = utils.PROGRESS_BAR_RATIOS
CORNER_RADIUS = utils.PROGRESS_BAR_CORNER_RADIUS


def _segment_at(segments, t):
    for seg in segments:
        if seg["start"] <= t < seg["end"]:
            return seg
    if segments:
        last = segments[-1]
        if math.isclose(t, last["end"], rel_tol=1e-6, abs_tol=1e-6):
            return last
    raise AssertionError(f"no segment covering time {t}")


def _color_width(seg, color):
    for span in seg.get("color_spans", []):
        if tuple(span["color"]) == color:
            return span["end"] - span["start"]
    return 0


def _color_visibility_duration(segments, color):
    total = 0.0
    for seg in segments:
        dt = seg["end"] - seg["start"]
        if dt <= 0:
            continue
        for span in seg.get("color_spans", []):
            if tuple(span["color"]) == color and span["end"] > span["start"]:
                total += dt
                break
    return total


def _last_visible_time(segments, color):
    last = 0.0
    for seg in segments:
        for span in seg.get("color_spans", []):
            if tuple(span["color"]) == color and span["end"] > span["start"]:
                last = max(last, seg["end"])
                break
    return last


def _span_widths(seg):
    return {
        tuple(span["color"]): span["end"] - span["start"]
        for span in seg.get("color_spans", [])
    }


def test_progress_bar_segments_default_countdown():
    segments = utils._build_progress_bar_segments(
        countdown=10,
        total_duration=16,
    )
    active = [s for s in segments if s["width"] > 0]
    assert active, "expected active segments"

    assert active[0]["width"] == PROG_WIDTH
    widths = [s["width"] for s in active]
    for earlier, later in zip(widths, widths[1:]):
        assert later <= earlier

    x_starts = [s["x_start"] for s in active]
    for earlier, later in zip(x_starts, x_starts[1:]):
        assert later >= earlier
    for seg in active:
        assert seg["x_start"] + seg["width"] == PROG_WIDTH

    seg_start = _segment_at(segments, 0.05)
    start_widths = _span_widths(seg_start)
    expected_green = int(round(PROG_WIDTH * PROG_RATIOS["safe"]))
    expected_yellow = int(round(PROG_WIDTH * PROG_RATIOS["warn"]))
    expected_red = PROG_WIDTH - expected_green - expected_yellow
    assert start_widths[PROG_COLORS["safe"]] == pytest.approx(expected_green, abs=2)
    assert start_widths[PROG_COLORS["warn"]] == pytest.approx(expected_yellow, abs=2)
    assert start_widths[PROG_COLORS["danger"]] == pytest.approx(expected_red, abs=2)

    seg_mid = _segment_at(segments, 5.05)
    assert _color_width(seg_mid, PROG_COLORS["safe"]) <= 2
    assert _color_width(seg_mid, PROG_COLORS["warn"]) > 0

    seg_late = _segment_at(segments, 7.05)
    assert _color_width(seg_late, PROG_COLORS["warn"]) <= 2
    assert _color_width(seg_late, PROG_COLORS["danger"]) > 0

    assert segments[-1]["start"] == pytest.approx(10.0, abs=1e-2)
    assert segments[-1]["width"] == 0


def test_progress_bar_segment_disappearance_order_and_radius():
    segments = utils._build_progress_bar_segments(
        countdown=10,
        total_duration=14,
    )
    active = [s for s in segments if s["width"] > 0]
    assert active, "expected active segments"

    max_slice = max((s["end"] - s["start"]) for s in active)
    assert max_slice <= 0.12

    for seg in segments:
        assert seg["corner_radius"] == CORNER_RADIUS

    safe_duration = _color_visibility_duration(segments, PROG_COLORS["safe"])
    warn_duration = _color_visibility_duration(segments, PROG_COLORS["warn"])
    danger_duration = _color_visibility_duration(segments, PROG_COLORS["danger"])

    countdown = 10
    assert safe_duration == pytest.approx(countdown * PROG_RATIOS["safe"], rel=0.1)
    assert warn_duration == pytest.approx(countdown * (PROG_RATIOS["safe"] + PROG_RATIOS["warn"]), rel=0.1)
    assert danger_duration == pytest.approx(countdown, rel=0.05)
    assert warn_duration - safe_duration == pytest.approx(countdown * PROG_RATIOS["warn"], rel=0.1)
    assert danger_duration - warn_duration == pytest.approx(countdown * PROG_RATIOS["danger"], rel=0.1)

    safe_last = _last_visible_time(segments, PROG_COLORS["safe"])
    warn_last = _last_visible_time(segments, PROG_COLORS["warn"])
    danger_last = _last_visible_time(segments, PROG_COLORS["danger"])

    assert safe_last <= warn_last <= danger_last
    assert safe_last == pytest.approx(5.0, rel=0.1)
    assert warn_last == pytest.approx(7.0, rel=0.1)
    assert danger_last == pytest.approx(10.0, rel=0.1)


def test_progress_bar_proportional_segments(monkeypatch, tmp_path):
    if not utils._HAS_MOVIEPY:
        pytest.skip("MoviePy not available; skipping progress bar integration test")

    monkeypatch.setenv("SPELLVID_DEBUG_SKIP_WRITE", "1")

    item = {
        "letters": "P p",
        "word_en": "Progress",
        "word_zh": "進度",
        "image_path": "",
        "music_path": "",
        "countdown_sec": 8,
        "reveal_hold_sec": 2,
    }

    out = tmp_path / "progress.mp4"
    res = utils.render_video_moviepy(item, str(out), dry_run=False)
    segments = res.get("progress_bar_segments")
    assert segments, "expected progress bar metadata"

    def duration_for(color_key):
        target = PROG_COLORS[color_key]
        return _color_visibility_duration(segments, target)

    countdown = item["countdown_sec"]
    assert duration_for("safe") == pytest.approx(countdown * PROG_RATIOS["safe"], rel=0.1)
    assert duration_for("warn") == pytest.approx(countdown * (PROG_RATIOS["safe"] + PROG_RATIOS["warn"]), rel=0.1)
    assert duration_for("danger") == pytest.approx(countdown, rel=0.05)
    assert duration_for("warn") - duration_for("safe") == pytest.approx(countdown * PROG_RATIOS["warn"], rel=0.1)
    assert duration_for("danger") - duration_for("warn") == pytest.approx(countdown * PROG_RATIOS["danger"], rel=0.1)

    seg_start = _segment_at(segments, 1.0)
    assert _color_width(seg_start, PROG_COLORS["safe"]) > _color_width(seg_start, PROG_COLORS["warn"]) > 0

    seg_warn = _segment_at(segments, 4.5)
    assert _color_width(seg_warn, PROG_COLORS["safe"]) <= 2
    assert _color_width(seg_warn, PROG_COLORS["warn"]) > 0

    seg_danger = _segment_at(segments, 6.5)
    assert _color_width(seg_danger, PROG_COLORS["warn"]) <= 2
    assert _color_width(seg_danger, PROG_COLORS["danger"]) > 0

    for seg in segments:
        assert seg["corner_radius"] == CORNER_RADIUS

    monkeypatch.delenv("SPELLVID_DEBUG_SKIP_WRITE", raising=False)
    assert not out.exists()
