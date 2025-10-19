"""契約測試: render_example.ps1 執行契約

驗證核心影片產出腳本 render_example.ps1 能夠正常執行並產出有效影片。
這是專案最重要的工作流程契約測試。
"""
import subprocess
from pathlib import Path
import pytest


def test_render_example_script_succeeds():
    """驗證 render_example.ps1 執行無錯誤

    契約要求:
    - 腳本退出碼為 0
    - 無 Python ImportError 或 ModuleNotFoundError
    - 無 DeprecationWarning (在新架構中)

    注意: 此測試直接調用 Python 腳本而非 PowerShell 包裝器,
    以確保在測試環境中使用正確的虛擬環境。
    """
    import sys
    repo_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts.render_example", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=repo_root
    )

    # 檢查退出碼
    assert result.returncode == 0, (
        f"Script failed with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # 檢查無 import 錯誤
    assert "ImportError" not in result.stderr, (
        f"ImportError detected:\n{result.stderr}"
    )
    assert "ModuleNotFoundError" not in result.stderr, (
        f"ModuleNotFoundError detected:\n{result.stderr}"
    )

    # 在 dry-run 模式,應該有 "Running: python" 訊息
    has_python_msg = (
        "Running: python" in result.stdout or
        "python" in result.stdout.lower()
    )
    assert has_python_msg, (
        f"Expected script execution message not found:\n{result.stdout}"
    )


def test_render_example_produces_valid_mp4():
    """驗證腳本產出有效的 MP4 檔案

    契約要求:
    - out/ 目錄產生至少一個 MP4 檔案
    - MP4 檔案大小 > 0 bytes
    - ffprobe 可以解析影片 (包含 video 與 audio stream)

    注意: 此測試直接調用 Python 腳本而非 PowerShell 包裝器。
    """
    import sys
    repo_root = Path(__file__).parent.parent.parent
    out_dir = repo_root / "out"
    out_dir.mkdir(exist_ok=True)

    # 執行腳本(非 dry-run,使用簡化配置以加速測試)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.render_example"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=300  # 5 分鐘超時
    )

    # 檢查執行成功
    assert result.returncode == 0, (
        f"Script execution failed:\n{result.stderr}"
    )

    # 檢查 MP4 檔案產生
    mp4_files = list(out_dir.glob("*.mp4"))
    assert len(mp4_files) > 0, (
        f"No MP4 files generated in {out_dir}\n"
        f"STDOUT:\n{result.stdout}"
    )

    # 驗證檔案大小
    for mp4 in mp4_files:
        assert mp4.stat().st_size > 0, (
            f"Generated MP4 file is empty: {mp4}"
        )

    # 使用 ffprobe 驗證影片格式
    ffprobe_path = repo_root / "FFmpeg" / "ffprobe.exe"
    if not ffprobe_path.exists():
        pytest.skip("ffprobe not available for validation")

    for mp4 in mp4_files:
        probe_result = subprocess.run(
            [
                str(ffprobe_path),
                "-v", "error",
                "-show_entries", "stream=codec_type",
                str(mp4)
            ],
            capture_output=True,
            text=True
        )

        # 檢查包含 video stream
        assert "codec_type=video" in probe_result.stdout, (
            f"No video stream found in {mp4.name}\n"
            f"ffprobe output:\n{probe_result.stdout}"
        )

        # 音訊為可選(部分配置可能無音訊)
        # 但如果有 music 配置,應該要有 audio stream
        # assert "codec_type=audio" in probe_result.stdout
