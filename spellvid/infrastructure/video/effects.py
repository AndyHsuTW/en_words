"""MoviePy video effects infrastructure.

This module provides MoviePy-specific implementations for applying
video effects (fade-in, fade-out) to video clips. These are
infrastructure adapters that wrap MoviePy's FX system.

Architecture:
- Wraps MoviePy's video.fx.FadeIn and video.fx.FadeOut
- Wraps MoviePy's audio.fx.AudioFadeIn and audio.fx.AudioFadeOut
- Provides graceful fallback when effects not available
- Uses default durations from shared constants

Technical Details:
- Requires MoviePy for clip effects
- Returns original clip if MoviePy unavailable or clip too short
- Supports both video and audio fade effects
- Exception-safe (returns clip on error)
"""

from typing import Any, Optional

try:
    import moviepy.editor as mpy

    _HAS_MOVIEPY = True
except ImportError:
    _HAS_MOVIEPY = False
    mpy = None  # type: ignore

# Import default durations from shared constants
from spellvid.shared.constants import FADE_IN_DURATION, FADE_OUT_DURATION


def apply_fadeout_effect(
    clip: Any, duration: Optional[float] = None
) -> Any:
    """Apply fade-out effect to video clip (both video and audio).

    Applies MoviePy's FadeOut effect to the video track and
    AudioFadeOut to the audio track (if present).

    Args:
        clip: MoviePy VideoClip object.
        duration: Fade-out duration in seconds. If None, uses
            FADE_OUT_DURATION constant.

    Returns:
        VideoClip with fade-out effect applied, or original clip
        if conditions not met (no MoviePy, clip too short, error).

    Example:
        >>> clip = mpy.VideoFileClip("input.mp4")
        >>> faded = apply_fadeout_effect(clip, duration=2.0)
        >>> faded.duration == clip.duration
        True
        >>> # Last 2 seconds will fade to black

    Behavior:
        - Returns original clip if MoviePy not available
        - Returns original clip if clip is None
        - Returns original clip if clip.duration < duration
        - Applies video fade-out using moviepy.video.fx.FadeOut
        - Applies audio fade-out using moviepy.audio.fx.AudioFadeOut
        - Returns clip with video fade-out if audio fade fails

    Technical Notes:
        - Uses MoviePy's FX system (effect.apply(clip))
        - Graceful degradation on exceptions
        - Audio fade is optional (continues if fails)
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip

    if duration is None:
        duration = FADE_OUT_DURATION

    # Skip fade-out if video is too short
    if clip.duration < duration:
        return clip

    # Apply video fade-out using MoviePy FX
    try:
        from moviepy.video.fx.FadeOut import FadeOut

        effect = FadeOut(duration)
        clip_with_fadeout = effect.apply(clip)
    except Exception:
        # Fallback if FadeOut not available
        return clip

    # Apply audio fade-out if audio exists
    if clip_with_fadeout.audio is not None:
        try:
            from moviepy.audio.fx.AudioFadeOut import AudioFadeOut

            audio_effect = AudioFadeOut(duration)
            clip_with_fadeout = clip_with_fadeout.with_audio(
                audio_effect.apply(clip_with_fadeout.audio)
            )
        except Exception:
            # If audio fadeout fails, continue with video fadeout only
            pass

    return clip_with_fadeout


def apply_fadein_effect(
    clip: Any,
    duration: Optional[float] = None,
    apply_audio: bool = False,
) -> Any:
    """Apply fade-in effect to video clip.

    Applies MoviePy's FadeIn effect to the video track and
    optionally AudioFadeIn to the audio track.

    Args:
        clip: MoviePy VideoClip object.
        duration: Fade-in duration in seconds. If None, uses
            FADE_IN_DURATION constant.
        apply_audio: If True, also apply fade-in to audio
            (Phase 3 feature).

    Returns:
        VideoClip with fade-in effect applied, or original clip
        if conditions not met (no MoviePy, clip too short, error).

    Example:
        >>> clip = mpy.VideoFileClip("input.mp4")
        >>> faded = apply_fadein_effect(clip, duration=1.0)
        >>> faded.duration == clip.duration
        True
        >>> # First 1 second will fade from black

        >>> # With audio fade-in
        >>> faded_with_audio = apply_fadein_effect(
        ...     clip, duration=1.0, apply_audio=True
        ... )

    Behavior:
        - Returns original clip if MoviePy not available
        - Returns original clip if clip is None
        - Returns original clip if clip.duration < duration
        - Applies video fade-in using moviepy.video.fx.FadeIn
        - Optionally applies audio fade-in (if apply_audio=True)
        - Returns clip with video fade-in if audio fade fails

    Technical Notes:
        - Uses MoviePy's FX system (effect.apply(clip))
        - Graceful degradation on exceptions
        - Audio fade is optional (controlled by apply_audio flag)
        - Audio fade requires clip to have audio track
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip

    if duration is None:
        duration = FADE_IN_DURATION

    # Skip fade-in if video is too short
    if clip.duration < duration:
        return clip

    # Apply video fade-in using MoviePy FX
    try:
        from moviepy.video.fx.FadeIn import FadeIn

        effect = FadeIn(duration)
        clip_with_fadein = effect.apply(clip)
    except Exception:
        # Fallback if FadeIn not available
        return clip

    # Phase 3: Apply audio fade-in if requested
    if apply_audio and clip_with_fadein.audio is not None:
        try:
            from moviepy.audio.fx.AudioFadeIn import AudioFadeIn

            audio_effect = AudioFadeIn(duration)
            clip_with_fadein = clip_with_fadein.with_audio(
                audio_effect.apply(clip_with_fadein.audio)
            )
        except Exception:
            # If audio fadein fails, continue with video fadein only
            pass

    return clip_with_fadein
