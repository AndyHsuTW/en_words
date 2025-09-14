import os
import wave
import math
import struct
import subprocess
import shutil
import pytest
from spellvid import utils

# Try to import VideoFileClip for audio inspection (moviepy API surface
# differs across installs)
VideoFileClip = None
try:
    from moviepy.editor import VideoFileClip
except Exception:
    try:
        from moviepy import VideoFileClip
    except Exception:
        try:
            import moviepy as _m

            VideoFileClip = getattr(_m, "VideoFileClip", None)
        except Exception:
            VideoFileClip = None


def _has_moviepy():
    return getattr(utils, "_HAS_MOVIEPY", False)


@pytest.mark.parametrize("use_moviepy", [True, False])
def test_music_included_in_render(tmp_path, use_moviepy):
    """Render a short video with a music file and assert the output
    contains audio when using the MoviePy renderer.

    The test will be skipped if MoviePy isn't available when use_moviepy=True.
    For the non-moviepy stub path, we assert that check_assets reports the
    music file presence and that render_video_stub returns ok status.
    """
    # Prefer the test-local asset `tests/assets/ball.mp3` if present.
    assets_mp3 = os.path.join(
        os.path.dirname(__file__), "assets", "ball.mp3"
    )
    assets_mp3 = os.path.normpath(assets_mp3)

    if use_moviepy and not _has_moviepy():
        pytest.skip(
            "MoviePy not available; skipping moviepy audio inclusion test"
        )

    # If using the real MoviePy renderer, generate a short sine WAV in
    # tmp_path to ensure the source audio is audible and deterministic.
    if use_moviepy:
        src_wav = tmp_path / "src_music.wav"
        sr = 44100
        duration = 1.0  # seconds
        freq = 440.0
        n_samples = int(sr * duration)
        amp = 0.6
        with wave.open(str(src_wav), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            for i in range(n_samples):
                t = i / sr
                v = int(amp * 32767.0 * math.sin(2 * math.pi * freq * t))
                wf.writeframes(struct.pack("<h", v))
        assets_mp3 = str(src_wav)

    # create a short dummy item
    item = {
        "letters": "A",
        "word_en": "Arm",
        "word_zh": "手臂",
        "image_path": "",
        "music_path": assets_mp3,
        "countdown_sec": 1,
        "reveal_hold_sec": 1,
    }

    out_mp4 = tmp_path / ("out_%s.mp4" % ("mpy" if use_moviepy else "stub"))

    if use_moviepy:
        # call real renderer
        res = utils.render_video_moviepy(item, str(out_mp4), dry_run=False)
        assert res.get("status") == "ok"
        # Ensure renderer reports having loaded the provided music file.
        # This is the most reliable indicator that the music was accepted
        # by the renderer (avoids false negatives caused by encoding
        # toolchain differences affecting exported audio streams).
        if item.get("music_path"):
            assert res.get("audio_loaded") is True, (
                "renderer reported it did not load the provided music file"
            )
        assert out_mp4.exists(), "output not created"
        assert out_mp4.stat().st_size > 1000
    # Prefer using ffprobe to detect audio streams reliably.

        def _find_ffprobe():
            # 1) IMAGEIO_FFMPEG_EXE sibling
            exe = os.environ.get("IMAGEIO_FFMPEG_EXE")
            if exe:
                candidate = os.path.join(os.path.dirname(exe), "ffprobe")
                if os.name == "nt":
                    candidate += ".exe"
                if os.path.isfile(candidate):
                    return candidate
            # 2) system ffprobe
            p = shutil.which("ffprobe")
            if p:
                return p
            # 3) repo-local
            root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), os.pardir)
            )
            repo_ff = os.path.join(root, "FFmpeg", "ffprobe.exe")
            if os.path.isfile(repo_ff):
                return repo_ff
            return None
        ffprobe = _find_ffprobe()
        expected_dur = float(item.get("countdown_sec", 0)) + float(
            item.get("reveal_hold_sec", 0)
        )
        if ffprobe:
            # query audio stream duration
            cmd = [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(out_mp4),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            out = proc.stdout.strip()
            if not out:
                raise AssertionError(
                    "ffprobe: no audio stream found in output"
                )
            # take the first audio stream duration
            try:
                audio_dur = float(out.splitlines()[0])
            except Exception:
                audio_dur = 0.0
            # audio should cover most of the video duration
            if audio_dur < expected_dur * 0.75:
                raise AssertionError(
                    f"audio duration ({audio_dur:.2f}s) "
                    f"is too short vs expected {expected_dur:.2f}s"
                )
        else:
            # fallback: use MoviePy checks (as before)
            if VideoFileClip is None:
                pytest.skip(
                    "moviepy VideoFileClip import unavailable; "
                    "skip audio inspection"
                )

            clip = VideoFileClip(str(out_mp4))
            try:
                audio = getattr(clip, "audio", None)
                assert audio is not None, "output video missing audio track"
                assert audio.duration > 0.1, "audio track too short"
            finally:
                clip.close()
    else:
        # Use stub renderer path
        res = utils.render_video_stub(
            item, str(out_mp4), dry_run=False, use_moviepy=False
        )
        assert res.get("status") == "ok"
        # check_assets should still report music exists based on path
        assets = utils.check_assets(item)
        # If the asset file does not actually exist in repo, it's okay;
        # the test asserts that check_assets matches the filesystem.
        assert assets["music_exists"] == os.path.isfile(
            item["music_path"]
        )
