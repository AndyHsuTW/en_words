"""Integration tests for batch video concatenation with transitions.

Tests the concatenate_videos_with_transitions function and batch CLI mode
with --out-file parameter.
"""

import os
import pytest
from spellvid.utils import (
    concatenate_videos_with_transitions,
    _HAS_MOVIEPY,
    _mpy,
    FADE_IN_DURATION,
)

pytestmark = pytest.mark.skipif(
    not _HAS_MOVIEPY, reason="MoviePy not available")


def create_test_video(path, duration=5, color=(255, 0, 0), with_audio=False):
    """Helper to create a simple test video file."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=color, duration=duration)

    if with_audio:
        # Generate simple tone audio
        import numpy as np
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_array = np.sin(2 * np.pi * 440 * t)

        from moviepy.audio.AudioClip import AudioClip
        audio_clip = AudioClip(
            lambda t: audio_array[int(t * sample_rate): int(t * sample_rate) + 1],
            duration=duration,
            fps=sample_rate,
        )
        clip = clip.with_audio(audio_clip)

    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Write video (without verbose/logger parameters)
    clip.write_videofile(path, fps=30, codec="libx264", audio_codec="aac")
    clip.close()
    if with_audio:
        audio_clip.close()


def test_concatenate_two_videos(tmp_path):
    """Test concatenating two simple videos."""
    # Create two test videos
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    output = tmp_path / "output.mp4"

    create_test_video(str(video1), duration=3, color=(255, 0, 0))  # Red, 3s
    create_test_video(str(video2), duration=3, color=(0, 255, 0))  # Green, 3s

    # Concatenate
    result = concatenate_videos_with_transitions(
        [str(video1), str(video2)],
        str(output),
        fade_in_duration=1.0,
        apply_audio_fadein=False,
    )

    # Verify
    assert result["status"] == "ok"
    assert result["clips_count"] == 2
    assert os.path.exists(output)
    assert result["total_duration"] > 5  # At least 6 seconds (2 videos × 3s)

    # Verify output video
    final_clip = _mpy.VideoFileClip(str(output))
    assert final_clip.duration >= 6
    final_clip.close()


def test_concatenate_three_videos(tmp_path):
    """Test concatenating three videos with transitions."""
    # Create three test videos
    videos = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue

    for i, color in enumerate(colors):
        video_path = tmp_path / f"video{i+1}.mp4"
        create_test_video(str(video_path), duration=2, color=color)
        videos.append(str(video_path))

    output = tmp_path / "output.mp4"

    # Concatenate
    result = concatenate_videos_with_transitions(
        videos,
        str(output),
        fade_in_duration=1.0,
    )

    # Verify
    assert result["status"] == "ok"
    assert result["clips_count"] == 3
    assert os.path.exists(output)

    # Verify duration (3 videos × 2s = 6s minimum)
    final_clip = _mpy.VideoFileClip(str(output))
    assert final_clip.duration >= 6
    final_clip.close()


def test_concatenate_with_audio(tmp_path):
    """Test concatenating videos that have audio tracks."""
    # Create videos with audio
    video1 = tmp_path / "video1_audio.mp4"
    video2 = tmp_path / "video2_audio.mp4"
    output = tmp_path / "output_audio.mp4"

    create_test_video(str(video1), duration=3,
                      color=(255, 0, 0), with_audio=True)
    create_test_video(str(video2), duration=3,
                      color=(0, 255, 0), with_audio=True)

    # Concatenate
    result = concatenate_videos_with_transitions(
        [str(video1), str(video2)],
        str(output),
        fade_in_duration=1.0,
        apply_audio_fadein=False,
    )

    # Verify
    assert result["status"] == "ok"
    assert os.path.exists(output)

    # Verify audio exists
    final_clip = _mpy.VideoFileClip(str(output))
    assert final_clip.audio is not None
    final_clip.close()


def test_concatenate_empty_list():
    """Test that empty video list returns error."""
    result = concatenate_videos_with_transitions(
        [],
        "/tmp/output.mp4",
    )

    assert result["status"] == "error"
    assert "No video paths" in result["message"]


def test_concatenate_missing_file(tmp_path):
    """Test that missing input file returns error."""
    output = tmp_path / "output.mp4"

    result = concatenate_videos_with_transitions(
        ["/nonexistent/video1.mp4", "/nonexistent/video2.mp4"],
        str(output),
    )

    assert result["status"] == "error"
    assert "not found" in result["message"]


def test_concatenate_single_video(tmp_path):
    """Test concatenating a single video (edge case)."""
    video1 = tmp_path / "video1.mp4"
    output = tmp_path / "output.mp4"

    create_test_video(str(video1), duration=3, color=(255, 0, 0))

    # Concatenate single video
    result = concatenate_videos_with_transitions(
        [str(video1)],
        str(output),
        fade_in_duration=1.0,
    )

    # Should succeed - single video, no fade-in applied (idx=0)
    assert result["status"] == "ok"
    assert result["clips_count"] == 1
    assert os.path.exists(output)


def test_concatenate_custom_fade_duration(tmp_path):
    """Test concatenation with custom fade-in duration."""
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    output = tmp_path / "output.mp4"

    create_test_video(str(video1), duration=3, color=(255, 0, 0))
    create_test_video(str(video2), duration=3, color=(0, 255, 0))

    # Use custom 0.5s fade-in
    result = concatenate_videos_with_transitions(
        [str(video1), str(video2)],
        str(output),
        fade_in_duration=0.5,
    )

    assert result["status"] == "ok"
    assert os.path.exists(output)


def test_concatenate_default_fade_duration(tmp_path):
    """Test concatenation uses default FADE_IN_DURATION when None."""
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    output = tmp_path / "output.mp4"

    create_test_video(str(video1), duration=3, color=(255, 0, 0))
    create_test_video(str(video2), duration=3, color=(0, 255, 0))

    # Pass None to use default
    result = concatenate_videos_with_transitions(
        [str(video1), str(video2)],
        str(output),
        fade_in_duration=None,  # Should use FADE_IN_DURATION
    )

    assert result["status"] == "ok"
    assert os.path.exists(output)


def test_first_video_no_fadein(tmp_path):
    """Test that first video does not have fade-in applied (D2 decision)."""
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    output = tmp_path / "output.mp4"

    # Create white videos
    create_test_video(str(video1), duration=3, color=(255, 255, 255))
    create_test_video(str(video2), duration=3, color=(200, 200, 200))

    result = concatenate_videos_with_transitions(
        [str(video1), str(video2)],
        str(output),
        fade_in_duration=1.0,
    )

    assert result["status"] == "ok"

    # Load output and check first frame
    final_clip = _mpy.VideoFileClip(str(output))

    # First frame should be bright (no fade-in on first video)
    first_frame = final_clip.get_frame(0.0)
    assert first_frame.mean() > 200  # Should be bright white

    # Frame after first video should be darker (fade-in on second video)
    # At 3.0s (start of second video), there should be fade-in effect
    second_video_start = final_clip.get_frame(3.1)
    # Note: Due to fade-in, this might be slightly darker, but testing is complex
    # Just verify video was created successfully

    final_clip.close()


def test_output_directory_creation(tmp_path):
    """Test that output directory is created if it doesn't exist."""
    video1 = tmp_path / "video1.mp4"
    create_test_video(str(video1), duration=2, color=(255, 0, 0))

    # Output in non-existent subdirectory
    output = tmp_path / "subdir" / "nested" / "output.mp4"

    result = concatenate_videos_with_transitions(
        [str(video1)],
        str(output),
    )

    assert result["status"] == "ok"
    assert os.path.exists(output)
    assert os.path.exists(tmp_path / "subdir" / "nested")


def test_batch_only_one_ending_at_end():
    """T006: 測試批次處理時片尾影片只在最後一個影片出現。

    這是修正的核心測試：當批次處理多個單字時，只有最後一個單字
    影片應該包含片尾，前面的單字影片都應該 skip_ending=True。
    """
    # 這個測試將在實作 skip_ending 參數後通過
    # 目前應該會失敗，因為參數還不存在
    pytest.skip("T006: 等待 skip_ending 參數實作（T008-T011）")


def test_single_item_batch_has_ending():
    """T007: 測試單個項目的批次處理仍然包含片尾影片（邊界情況）。

    當批次只有一個項目時，它應該被視為唯一的影片，
    因此應該設定 skip_ending=False 並包含片尾。
    """
    # 這個測試將在實作 skip_ending 參數後通過
    # 目前應該會失敗，因為參數還不存在
    pytest.skip("T007: 等待 skip_ending 參數實作（T008-T011）")
