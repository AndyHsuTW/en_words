# Contract: render_example.ps1 執行契約

## Purpose
驗證 `render_example.ps1` 腳本在移除舊程式碼後仍能正常執行,產出有效的影片檔案。

## Preconditions
- 虛擬環境已啟動 (`.venv`)
- 開發依賴已安裝 (`requirements-dev.txt`)
- FFmpeg 可執行檔存在於 `FFmpeg/ffmpeg.exe`
- 輸入配置檔存在 (`config.json`)
- 輸出目錄可寫入 (`out/`)

## Input
```powershell
.\scripts\render_example.ps1
```

可選參數:
- `-OutFile <filename>`: 指定輸出檔名
- `-Json <path>`: 指定配置 JSON 檔案路徑
- `-OutDir <path>`: 指定輸出目錄
- `-DryRun`: 僅驗證資源不產出影片
- `-UseMoviepy`: 使用 MoviePy 渲染器
- `-HideTimer`: 隱藏計時器(預設 true)

## Expected Output

### 成功執行
1. **終端輸出**:
   - 無 Python ImportError 或 ModuleNotFoundError
   - 無 DeprecationWarning
   - 顯示 "Running: python scripts/render_example.py ..."
   - 顯示 ffprobe 結果

2. **檔案系統**:
   - `out/` 目錄存在
   - 至少產出一個 `.mp4` 檔案
   - 檔案大小 > 0 bytes

3. **影片品質**(透過 ffprobe 驗證):
   ```
   codec_type=video
   codec_name=h264
   codec_type=audio
   codec_name=aac
   ```

### 失敗場景
- 退出碼非 0
- 產生 Python traceback
- 無檔案產出在 `out/`
- 產生的 MP4 無法被 ffprobe 解析

## Postconditions
- `out/` 目錄包含可播放的 MP4 檔案
- 腳本退出碼為 0
- 無錯誤訊息或警告

## Test Implementation
```python
# tests/contract/test_render_example_contract.py
import subprocess
import os
from pathlib import Path

def test_render_example_script_succeeds():
    """Verify render_example.ps1 executes without errors"""
    result = subprocess.run(
        ["pwsh", "-File", "scripts/render_example.ps1", "-DryRun"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr

def test_render_example_produces_valid_mp4():
    """Verify script outputs valid MP4 file"""
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    
    result = subprocess.run(
        ["pwsh", "-File", "scripts/render_example.ps1"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0
    mp4_files = list(out_dir.glob("*.mp4"))
    assert len(mp4_files) > 0, "No MP4 files generated"
    
    # Verify with ffprobe
    for mp4 in mp4_files:
        probe_result = subprocess.run(
            ["FFmpeg/ffprobe.exe", "-v", "error", 
             "-show_entries", "stream=codec_type", 
             str(mp4)],
            capture_output=True,
            text=True
        )
        assert "codec_type=video" in probe_result.stdout
```

## Notes
- 此契約是核心工作流程的守護測試
- 應在每次 PR 前執行
- 失敗表示重構破壞了使用者工作流程
