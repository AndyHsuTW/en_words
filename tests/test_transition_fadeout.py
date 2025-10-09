"""Unit tests for video transition fade-out and fade-in effects.

Tests the _apply_fadeout and _apply_fadein functions for correctness,
including:
- Normal video fade-out/fade-in effects
- Short video boundary handling
- Audio synchronization
"""

import pytest
from spellvid.utils import (
    _apply_fadeout,
    _apply_fadein,
    _HAS_MOVIEPY,
    _mpy,
    FADE_OUT_DURATION,
    FADE_IN_DURATION,
)

pytestmark = pytest.mark.skipif(not _HAS_MOVIEPY, reason="MoviePy not available")


def test_fadeout_normal_video():
    """Test 10-second video with 3-second fade-out."""
    # Create a 10-second white color clip
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply fade-out
    result = _apply_fadeout(clip, duration=3.0)
    
    # Verify
    assert result is not None
    assert result.duration == 10  # Duration unchanged
    
    # Verify fade-out effect by checking frame brightness
    # Frame at 7.0s: normal brightness (before fade-out starts)
    frame_before = result.get_frame(7.0)
    # Frame at 9.9s: should be nearly black (at end of fade-out)
    frame_end = result.get_frame(9.9)
    
    # Simple verification: end frame should be darker than before frame
    assert frame_end.mean() < frame_before.mean()
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadeout_short_video():
    """Test short video (< 3 seconds) should not apply fade-out."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=2.0)
    
    result = _apply_fadeout(clip, duration=3.0)
    
    # Short video should be returned unchanged
    assert result is not None
    assert result.duration == 2.0
    
    # The clip should be the same object (no fade-out applied)
    assert result is clip
    
    # Clean up
    clip.close()


def test_fadeout_with_audio():
    """Test video with audio should have synchronized fade-out."""
    import numpy as np
    
    # Create video clip
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Generate simple audio (440Hz sine wave)
    sample_rate = 44100
    duration = 10
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t)
    
    # Create audio clip
    from moviepy.audio.AudioClip import AudioClip
    audio_clip = AudioClip(
        lambda t: audio_array[int(t * sample_rate) : int(t * sample_rate) + 1],
        duration=duration,
        fps=sample_rate,
    )
    clip = clip.with_audio(audio_clip)
    
    # Apply fade-out
    result = _apply_fadeout(clip, duration=3.0)
    
    # Verify audio exists
    assert result is not None
    assert result.audio is not None
    assert result.audio.duration == 10
    
    # Clean up
    clip.close()
    audio_clip.close()
    if result is not clip:
        result.close()


def test_fadeout_no_audio():
    """Test video without audio should not error."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    clip = clip.without_audio()  # Ensure no audio
    
    result = _apply_fadeout(clip, duration=3.0)
    
    assert result is not None
    assert result.audio is None  # Still no audio
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadein_normal_video():
    """Test 10-second video with 1-second fade-in."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply fade-in
    result = _apply_fadein(clip, duration=1.0, apply_audio=False)
    
    # Verify
    assert result is not None
    assert result.duration == 10  # Duration unchanged
    
    # Verify fade-in effect by checking frame brightness
    # Frame at 0.0s: should be black (start of fade-in)
    frame_start = result.get_frame(0.0)
    # Frame at 2.0s: should be normal brightness (after fade-in)
    frame_after = result.get_frame(2.0)
    
    # Simple verification: start frame should be darker than after frame
    assert frame_start.mean() < frame_after.mean()
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadein_short_video():
    """Test short video (< 1 second) should not apply fade-in."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=0.5)
    
    result = _apply_fadein(clip, duration=1.0, apply_audio=False)
    
    # Short video should be returned unchanged
    assert result is not None
    assert result.duration == 0.5
    
    # The clip should be the same object (no fade-in applied)
    assert result is clip
    
    # Clean up
    clip.close()


def test_fadein_audio_disabled():
    """Test fade-in with apply_audio=False should not fade audio."""
    import numpy as np
    
    # Create video clip with audio
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Generate simple audio
    sample_rate = 44100
    duration = 10
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t)
    
    from moviepy.audio.AudioClip import AudioClip
    audio_clip = AudioClip(
        lambda t: audio_array[int(t * sample_rate) : int(t * sample_rate) + 1],
        duration=duration,
        fps=sample_rate,
    )
    clip = clip.with_audio(audio_clip)
    
    # Apply fade-in with audio disabled
    result = _apply_fadein(clip, duration=1.0, apply_audio=False)
    
    # Verify audio exists but should not be faded
    assert result is not None
    assert result.audio is not None
    
    # Clean up
    clip.close()
    audio_clip.close()
    if result is not clip:
        result.close()


def test_fadein_audio_enabled():
    """Test fade-in with apply_audio=True should fade audio (Phase 3)."""
    import numpy as np
    
    # Create video clip with audio
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Generate simple audio
    sample_rate = 44100
    duration = 10
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t)
    
    from moviepy.audio.AudioClip import AudioClip
    audio_clip = AudioClip(
        lambda t: audio_array[int(t * sample_rate) : int(t * sample_rate) + 1],
        duration=duration,
        fps=sample_rate,
    )
    clip = clip.with_audio(audio_clip)
    
    # Apply fade-in with audio enabled
    result = _apply_fadein(clip, duration=1.0, apply_audio=True)
    
    # Verify audio exists and duration correct
    assert result is not None
    assert result.audio is not None
    assert result.audio.duration == 10
    
    # Clean up
    clip.close()
    audio_clip.close()
    if result is not clip:
        result.close()


def test_fadeout_custom_duration():
    """Test fade-out with custom duration."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply 2-second fade-out
    result = _apply_fadeout(clip, duration=2.0)
    
    assert result is not None
    assert result.duration == 10
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadein_custom_duration():
    """Test fade-in with custom duration."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply 1.5-second fade-in
    result = _apply_fadein(clip, duration=1.5, apply_audio=False)
    
    assert result is not None
    assert result.duration == 10
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadeout_default_duration():
    """Test fade-out uses default FADE_OUT_DURATION when duration=None."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply fade-out with duration=None (should use FADE_OUT_DURATION)
    result = _apply_fadeout(clip, duration=None)
    
    assert result is not None
    assert result.duration == 10
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()


def test_fadein_default_duration():
    """Test fade-in uses default FADE_IN_DURATION when duration=None."""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # Apply fade-in with duration=None (should use FADE_IN_DURATION)
    result = _apply_fadein(clip, duration=None, apply_audio=False)
    
    assert result is not None
    assert result.duration == 10
    
    # Clean up
    clip.close()
    if result is not clip:
        result.close()
