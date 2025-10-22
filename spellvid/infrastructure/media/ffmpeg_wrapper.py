"""FFmpeg 媒體處理包裝器

此模組實作 IMediaProcessor Protocol,使用 FFmpeg/ffprobe 進行媒體處理。

主要功能:
- 媒體元資料探測(時長、尺寸)
- 音訊提取
- FFmpeg 可用性檢查
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple


class FFmpegWrapper:
    """FFmpeg 媒體處理包裝器

    實作 IMediaProcessor Protocol,提供 FFmpeg 工具的包裝。

    使用 ffprobe 進行元資料探測,使用 ffmpeg 進行音訊提取。
    """

    def __init__(self):
        """初始化 FFmpegWrapper 並確保 FFmpeg 可用"""
        self._ffmpeg_exe: str | None = None
        self._ffprobe_exe: str | None = None
        self.ensure_ffmpeg_available()

    def probe_duration(self, media_path: str) -> float:
        """查詢媒體檔案時長

        使用 ffprobe 讀取音訊/視頻檔案的總時長。

        Args:
            media_path: 媒體檔案絕對路徑(.mp3, .mp4, .wav 等)

        Returns:
            時長,單位秒

        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析時長

        Example:
            >>> wrapper = FFmpegWrapper()
            >>> duration = wrapper.probe_duration("/path/to/music.mp3")
            >>> duration
            183.52
        """
        if not Path(media_path).exists():
            raise FileNotFoundError(f"Media file not found: {media_path}")

        ffprobe = self._get_ffprobe_exe()
        if not ffprobe:
            raise RuntimeError("ffprobe not available")

        cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            media_path,
        ]

        try:
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                text=True
            )
            duration = float(output.strip())

            if duration < 0:
                raise RuntimeError(
                    f"Invalid duration: {duration} for {media_path}"
                )

            return duration
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ffprobe failed for {media_path}: {e.output}"
            )
        except ValueError as e:
            raise RuntimeError(
                f"Cannot parse duration from {media_path}: {e}"
            )

    def probe_dimensions(self, video_path: str) -> Tuple[int, int]:
        """查詢視頻尺寸

        讀取視頻檔案的寬度與高度資訊。

        Args:
            video_path: 視頻檔案絕對路徑(.mp4, .avi, .mov 等)

        Returns:
            (width, height) 像素尺寸 tuple

        Raises:
            FileNotFoundError: 檔案不存在
            RuntimeError: 無法解析尺寸

        Example:
            >>> wrapper = FFmpegWrapper()
            >>> w, h = wrapper.probe_dimensions("/path/to/video.mp4")
            >>> print(f"視頻解析度: {w}x{h}")
            視頻解析度: 1920x1080
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        ffprobe = self._get_ffprobe_exe()
        if not ffprobe:
            raise RuntimeError("ffprobe not available")

        cmd = [
            ffprobe,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_path,
        ]

        try:
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                text=True
            )
            parts = output.strip().split("x")

            if len(parts) != 2:
                raise RuntimeError(
                    f"Cannot parse dimensions from output: {output}"
                )

            width = int(parts[0])
            height = int(parts[1])

            if width <= 0 or height <= 0:
                raise RuntimeError(
                    f"Invalid dimensions: {width}x{height}"
                )

            return (width, height)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ffprobe failed for {video_path}: {e.output}"
            )
        except ValueError as e:
            raise RuntimeError(
                f"Cannot parse dimensions from {video_path}: {e}"
            )

    def extract_audio(
        self,
        video_path: str,
        output_path: str,
        audio_codec: str = "mp3"
    ) -> None:
        """從視頻提取音訊軌

        將視頻檔案的音訊軌道提取並儲存為獨立音訊檔案。

        Args:
            video_path: 來源視頻檔案絕對路徑
            output_path: 輸出音訊檔案絕對路徑
            audio_codec: 音訊編碼器,支援 "mp3", "aac", "wav" 等

        Raises:
            FileNotFoundError: 來源視頻不存在
            RuntimeError: 轉換失敗
            IOError: 無法寫入輸出檔案

        Example:
            >>> wrapper = FFmpegWrapper()
            >>> wrapper.extract_audio(
            ...     "/path/to/video.mp4",
            ...     "/output/audio.mp3",
            ...     audio_codec="mp3"
            ... )
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        ffmpeg = self._get_ffmpeg_exe()
        if not ffmpeg:
            raise RuntimeError("ffmpeg not available")

        # 確保輸出目錄存在
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # 映射音訊編碼器
        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "wav": "pcm_s16le",
        }
        codec_arg = codec_map.get(audio_codec.lower(), audio_codec)

        cmd = [
            ffmpeg,
            "-i", video_path,
            "-vn",  # 不包含視頻
            "-acodec", codec_arg,
            "-y",  # 覆蓋輸出檔案
            output_path,
        ]

        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                text=True
            )

            if not Path(output_path).exists():
                raise IOError(f"Failed to create output file: {output_path}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ffmpeg failed to extract audio from {video_path}: "
                f"{e.output}"
            )

    def ensure_ffmpeg_available(self) -> bool:
        """確保 FFmpeg 可用

        檢查 FFmpeg 執行檔是否可被呼叫。
        嘗試多種查找策略:
        1. 環境變數 FFMPEG_PATH / IMAGEIO_FFMPEG_EXE
        2. 專案本地 FFmpeg/ 目錄
        3. 系統 PATH
        4. imageio-ffmpeg package

        Returns:
            True 若 FFmpeg 可用,False 否則

        Side Effects:
            快取 FFmpeg 和 ffprobe 路徑

        Example:
            >>> wrapper = FFmpegWrapper()
            >>> if wrapper.ensure_ffmpeg_available():
            ...     print("FFmpeg 就緒")
            FFmpeg 就緒
        """
        # 如果已經找到,直接回傳
        if self._ffmpeg_exe and self._ffprobe_exe:
            return True

        # 1. 環境變數
        ffmpeg_path = os.environ.get("FFMPEG_PATH")
        if not ffmpeg_path:
            ffmpeg_path = os.environ.get("IMAGEIO_FFMPEG_EXE")

        if ffmpeg_path and os.path.isfile(ffmpeg_path):
            self._ffmpeg_exe = ffmpeg_path
            # 嘗試找 ffprobe
            ffprobe_path = self._find_sibling_exe(ffmpeg_path, "ffprobe")
            if ffprobe_path:
                self._ffprobe_exe = ffprobe_path
                return True

        # 2. 專案本地 FFmpeg/ 目錄
        module_dir = Path(__file__).parent
        project_root = module_dir.parent.parent.parent
        ffmpeg_dir = project_root / "FFmpeg"

        if ffmpeg_dir.exists():
            ffmpeg_exe = self._find_exe_in_dir(ffmpeg_dir, "ffmpeg")
            ffprobe_exe = self._find_exe_in_dir(ffmpeg_dir, "ffprobe")

            if ffmpeg_exe and ffprobe_exe:
                self._ffmpeg_exe = str(ffmpeg_exe)
                self._ffprobe_exe = str(ffprobe_exe)
                return True

        # 3. 系統 PATH
        ffmpeg_sys = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        ffprobe_sys = shutil.which("ffprobe") or shutil.which("ffprobe.exe")

        if ffmpeg_sys and ffprobe_sys:
            self._ffmpeg_exe = ffmpeg_sys
            self._ffprobe_exe = ffprobe_sys
            return True

        # 4. imageio-ffmpeg
        try:
            import imageio_ffmpeg  # type: ignore

            ffmpeg_iio = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_iio and os.path.isfile(ffmpeg_iio):
                self._ffmpeg_exe = ffmpeg_iio
                # imageio-ffmpeg 通常只提供 ffmpeg
                # 嘗試找同目錄的 ffprobe
                ffprobe_iio = self._find_sibling_exe(ffmpeg_iio, "ffprobe")
                if ffprobe_iio:
                    self._ffprobe_exe = ffprobe_iio
                    return True
        except ImportError:
            pass

        return False

    def _get_ffmpeg_exe(self) -> str | None:
        """取得 ffmpeg 執行檔路徑"""
        return self._ffmpeg_exe

    def _get_ffprobe_exe(self) -> str | None:
        """取得 ffprobe 執行檔路徑"""
        return self._ffprobe_exe

    def _find_sibling_exe(
        self,
        exe_path: str,
        exe_name: str
    ) -> str | None:
        """在同目錄尋找另一個執行檔

        Args:
            exe_path: 已知執行檔路徑
            exe_name: 要尋找的執行檔名稱(不含副檔名)

        Returns:
            找到的執行檔路徑,或 None
        """
        exe_dir = Path(exe_path).parent

        for suffix in ["", ".exe"]:
            candidate = exe_dir / f"{exe_name}{suffix}"
            if candidate.is_file():
                return str(candidate)

        return None

    def _find_exe_in_dir(
        self,
        directory: Path,
        exe_name: str
    ) -> Path | None:
        """在目錄中尋找執行檔

        Args:
            directory: 要搜尋的目錄
            exe_name: 執行檔名稱(不含副檔名)

        Returns:
            找到的執行檔 Path,或 None
        """
        for suffix in ["", ".exe"]:
            candidate = directory / f"{exe_name}{suffix}"
            if candidate.is_file():
                return candidate

        return None


# ============================================================================
# Module-level utility functions for legacy compatibility
# ============================================================================

# Global cache for media duration probing (filepath -> (mtime, duration))
_entry_probe_cache: dict[str, tuple[float, float | None]] = {}


def _probe_media_duration(path: str) -> float | None:
    """Best-effort probe for a media file duration in seconds.

    This function attempts to retrieve the duration of a media file using:
    1. In-memory cache (based on file mtime)
    2. MoviePy VideoFileClip (if available)
    3. ffprobe subprocess fallback

    Cache Strategy:
        Results are cached based on file path + modification time.
        If file hasn't changed (same mtime), cached duration is returned.

    FFprobe Discovery:
        Searches for ffprobe in this order:
        1. System PATH (shutil.which)
        2. Repo-local FFmpeg/ffprobe[.exe]

    Args:
        path: Absolute path to media file (video or audio)

    Returns:
        Duration in seconds (float), or None if:
        - File doesn't exist
        - Duration cannot be determined
        - Duration is negative (invalid)

    Example:
        >>> duration = _probe_media_duration("assets/music.mp3")
        >>> if duration:
        ...     print(f"Duration: {duration:.2f}s")
        Duration: 183.52s
    """
    import os
    import shutil
    import subprocess

    if not path or not os.path.isfile(path):
        return None

    # Get file modification time for cache validation
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0.0

    # Check cache
    cache_key = os.path.abspath(path)
    cached = _entry_probe_cache.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]

    duration: float | None = None

    # Try MoviePy first if available
    try:
        import moviepy as mpy  # type: ignore
        _HAS_MOVIEPY = True
    except ImportError:
        _HAS_MOVIEPY = False

    if _HAS_MOVIEPY:
        try:
            clip = mpy.VideoFileClip(path)  # type: ignore
            try:
                raw = getattr(clip, "duration", None)
                if raw is not None:
                    duration = float(raw)
            finally:
                try:
                    clip.close()
                except Exception:
                    pass
        except Exception:
            duration = None

    # Fallback to ffprobe if MoviePy failed or unavailable
    if duration is None:
        candidates = [
            shutil.which("ffprobe"),
            shutil.which("ffprobe.exe"),
            None,
        ]
        # Check repo-local FFmpeg directory
        ffmpeg_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "FFmpeg"
        )
        for exe in ("ffprobe", "ffprobe.exe"):
            candidate = os.path.join(ffmpeg_dir, exe)
            if os.path.isfile(candidate):
                candidates.append(candidate)

        for cand in candidates:
            if not cand:
                continue
            cmd = [
                cand,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ]
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                text = out.decode("utf-8", errors="ignore").strip()
                if text:
                    duration = float(text)
                    break
            except Exception:
                continue

    # Validate duration (reject negative values)
    if duration is not None and duration < 0:
        duration = None

    # Update cache
    _entry_probe_cache[cache_key] = (mtime, duration)
    return duration


def _find_and_set_ffmpeg():
    """Locate ffmpeg and set IMAGEIO_FFMPEG_EXE and moviepy config when found.

    This function searches for ffmpeg executable and configures environment
    variables and MoviePy settings to use the located ffmpeg.

    Search Priority:
        1. Environment variable: FFMPEG_PATH or IMAGEIO_FFMPEG_EXE
           - If points to ffprobe, tries sibling ffmpeg.exe
        2. Repo-local: ../../../FFmpeg/ffmpeg.exe (relative to this file)
        3. imageio_ffmpeg.get_ffmpeg_exe() (if package installed)

    Side Effects:
        - Sets IMAGEIO_FFMPEG_EXE environment variable
        - Updates MoviePy config FFMPEG_BINARY (if MoviePy available)

    Usage:
        This function is typically called once at module initialization:
        >>> _find_and_set_ffmpeg()  # Auto-configure ffmpeg

    Notes:
        - Silent on failure (no exceptions raised)
        - Only sets env var if ffmpeg file actually exists
        - Handles both POSIX and Windows executables (.exe)
    """
    import os

    # 1: Check environment variables
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    if not ffmpeg_path:
        ffmpeg_path = os.environ.get("IMAGEIO_FFMPEG_EXE")

    if ffmpeg_path:
        # If user accidentally pointed to ffprobe, try sibling ffmpeg.exe
        base = os.path.basename(ffmpeg_path).lower()
        if "ffprobe" in base:
            candidate = os.path.join(
                os.path.dirname(ffmpeg_path), "ffmpeg.exe"
            )
            if os.path.isfile(candidate):
                ffmpeg_path = candidate

    # 2: Check repo-local FFmpeg directory
    if not ffmpeg_path:
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        candidate = os.path.join(root, "FFmpeg", "ffmpeg.exe")
        if os.path.isfile(candidate):
            ffmpeg_path = candidate

    # 3: Try imageio-ffmpeg package
    if not ffmpeg_path:
        try:
            import imageio_ffmpeg as _iioff  # type: ignore

            exe = _iioff.get_ffmpeg_exe()
            if exe:
                ffmpeg_path = exe
        except Exception:
            pass

    # Set environment variable and MoviePy config if found
    if ffmpeg_path and os.path.isfile(ffmpeg_path):
        os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_path)

        # Try to configure MoviePy if available
        try:
            import moviepy.config as _mpy_config  # type: ignore
            if _mpy_config is not None:
                _mpy_config.change_settings({"FFMPEG_BINARY": ffmpeg_path})
        except Exception:
            pass
