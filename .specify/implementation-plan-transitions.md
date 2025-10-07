# 影片轉場效果 - 實作計畫

**計畫編號**：IMPL-TRANSITION-001  
**建立日期**：2025-01-08  
**負責人**：開發團隊  
**預估時程**：6-8 工作天  
**相關規格**：SPEC-TRANSITION-001  
**決策文件**：video-transition-effects-decisions.md

---

## 📋 執行摘要 (Executive Summary)

### 目標
為 SpellVid 實作完整的影片轉場效果功能，包含淡出/淡入效果、音訊同步處理和 CLI 參數自訂。

### 範圍
- ✅ Phase 1: 核心淡出/淡入功能（2-3 天）
- ✅ Phase 2: 批次整合與測試（2 天）
- ✅ Phase 3: 音訊淡入與自訂參數（2-3 天）

### 關鍵決策
根據 Andy Hsu 的決策（詳見決策文件）：
- D1: 所有影片統一 3 秒淡出（單一與批次模式）
- D2: 批次模式第一個影片不淡入，後續影片淡入
- D4: Phase 3 實作音訊淡入（必要功能）
- D9: 完整實作 Phase 1+2+3

---

## 🎯 Phase 1: 核心功能實作（2-3 工作天）

### 1.1 任務清單

#### Task 1.1: 新增淡出/淡入常數定義
**檔案**：`spellvid/utils.py`  
**位置**：常數定義區（約第 40-80 行附近）  
**預估時間**：0.5 小時

**實作內容**：
```python
# 影片轉場效果常數
FADE_OUT_DURATION = 3.0  # 秒
FADE_IN_DURATION = 1.0   # 秒
```

**驗收標準**：
- [ ] 常數已定義且值正確
- [ ] 位置適當（與其他常數一起）

---

#### Task 1.2: 實作淡出效果輔助函式
**檔案**：`spellvid/utils.py`  
**位置**：新增函式於 `render_video_moviepy` 之前  
**預估時間**：1-2 小時

**實作內容**：
```python
def _apply_fadeout(clip, duration: float = FADE_OUT_DURATION):
    """為影片片段應用淡出效果（畫面與音訊）。
    
    Args:
        clip: MoviePy VideoClip 物件
        duration: 淡出持續時間（秒），預設 3.0
    
    Returns:
        應用淡出後的 VideoClip 物件
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip
    
    # 檢查影片長度是否足夠
    if clip.duration < duration:
        # 影片過短，不應用淡出
        return clip
    
    # 應用畫面淡出
    clip_with_fadeout = clip.fadeout(duration=duration)
    
    # 應用音訊淡出（如果存在）
    if clip_with_fadeout.audio is not None:
        clip_with_fadeout = clip_with_fadeout.audio_fadeout(duration=duration)
    
    return clip_with_fadeout
```

**測試案例**：
- [ ] 測試 10 秒影片應用 3 秒淡出
- [ ] 測試 2 秒短影片不應用淡出
- [ ] 測試有音訊的影片同步淡出
- [ ] 測試無音訊的影片僅畫面淡出

**驗收標準**：
- [ ] 函式實作正確
- [ ] 邊界情況處理完善
- [ ] 單元測試通過

---

#### Task 1.3: 實作淡入效果輔助函式
**檔案**：`spellvid/utils.py`  
**位置**：緊接 `_apply_fadeout` 之後  
**預估時間**：1 小時

**實作內容**：
```python
def _apply_fadein(clip, duration: float = FADE_IN_DURATION, apply_audio: bool = False):
    """為影片片段應用淡入效果。
    
    Args:
        clip: MoviePy VideoClip 物件
        duration: 淡入持續時間（秒），預設 1.0
        apply_audio: 是否也對音訊應用淡入（Phase 3 功能）
    
    Returns:
        應用淡入後的 VideoClip 物件
    """
    if not _HAS_MOVIEPY or clip is None:
        return clip
    
    # 檢查影片長度是否足夠
    if clip.duration < duration:
        return clip
    
    # 應用畫面淡入
    clip_with_fadein = clip.fadein(duration=duration)
    
    # Phase 3: 音訊淡入（可選）
    if apply_audio and clip_with_fadein.audio is not None:
        clip_with_fadein = clip_with_fadein.audio_fadein(duration=duration)
    
    return clip_with_fadein
```

**測試案例**：
- [ ] 測試 10 秒影片應用 1 秒淡入
- [ ] 測試 0.5 秒短影片不應用淡入
- [ ] 測試 apply_audio=True 時音訊同步淡入（Phase 3）

**驗收標準**：
- [ ] 函式實作正確
- [ ] apply_audio 參數預留擴充性
- [ ] 單元測試通過

---

#### Task 1.4: 修改 `render_video_moviepy` 應用淡出
**檔案**：`spellvid/utils.py`  
**位置**：`render_video_moviepy` 函式（約第 1684 行）  
**預估時間**：2-3 小時

**實作內容**：
在最終影片合成完成、輸出前應用淡出效果。

**修改位置**：
找到最終 `final_clip` 建立後、`final_clip.write_videofile()` 之前：

```python
# 在此處（約第 3150-3160 行）
# 原本：final_clip = _mpy.concatenate_videoclips(...)

# 新增：應用淡出效果（所有影片統一淡出，D1 決策）
final_clip = _apply_fadeout(final_clip, duration=FADE_OUT_DURATION)

# 然後：final_clip.write_videofile(...)
```

**注意事項**：
- 確保在 entry.mp4 和 ending.mp4 連接後應用淡出
- 結尾影片 (ending.mp4) 不額外淡出（D8 決策）
- 需要重新檢視程式碼結構，找到正確的應用點

**測試案例**：
- [ ] 單一影片模式輸出有 3 秒淡出
- [ ] 批次模式每個單字影片有 3 秒淡出
- [ ] 淡出不影響 ending.mp4

**驗收標準**：
- [ ] 所有影片統一應用淡出
- [ ] 不影響其他功能
- [ ] 整合測試通過

---

#### Task 1.5: 建立單元測試檔案
**檔案**：`tests/test_transition_fadeout.py`（新建）  
**預估時間**：2-3 小時

**實作內容**：
```python
"""影片淡出效果測試。

測試 _apply_fadeout 函式的正確性，包含：
- 正常影片的淡出效果
- 短影片的邊界處理
- 音訊同步淡出
"""

import pytest
from spellvid.utils import _apply_fadeout, _HAS_MOVIEPY, _mpy

pytestmark = pytest.mark.skipif(not _HAS_MOVIEPY, reason="MoviePy not available")


def test_fadeout_normal_video():
    """測試 10 秒影片應用 3 秒淡出。"""
    # 建立 10 秒純色影片
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # 應用淡出
    result = _apply_fadeout(clip, duration=3.0)
    
    # 驗證
    assert result is not None
    assert result.duration == 10  # 時長不變
    
    # 驗證關鍵幀亮度（淡出效果）
    # 7.0s 處：正常亮度（淡出開始前）
    frame_before = result.get_frame(7.0)
    # 9.9s 處：接近黑色（淡出結束）
    frame_end = result.get_frame(9.9)
    
    # 簡單驗證：結束幀應該比開始幀暗
    assert frame_end.mean() < frame_before.mean()


def test_fadeout_short_video():
    """測試短影片（< 3 秒）不應用淡出。"""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=2.0)
    
    result = _apply_fadeout(clip, duration=3.0)
    
    # 短影片應原封不動返回
    assert result is not None
    assert result.duration == 2.0


def test_fadeout_with_audio():
    """測試有音訊的影片同步淡出。"""
    # 建立帶音訊的影片
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    # 生成簡單音訊（440Hz 正弦波）
    import numpy as np
    sample_rate = 44100
    duration = 10
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t)
    
    from moviepy.audio.AudioClip import AudioClip
    audio_clip = AudioClip(lambda t: audio_array[int(t * sample_rate)], duration=duration, fps=sample_rate)
    clip = clip.set_audio(audio_clip)
    
    # 應用淡出
    result = _apply_fadeout(clip, duration=3.0)
    
    # 驗證音訊存在
    assert result.audio is not None
    assert result.audio.duration == 10


def test_fadeout_no_audio():
    """測試無音訊的影片不報錯。"""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    clip = clip.without_audio()  # 確保無音訊
    
    result = _apply_fadeout(clip, duration=3.0)
    
    assert result is not None
    assert result.audio is None  # 仍然無音訊
```

**驗收標準**：
- [ ] 所有測試通過
- [ ] 測試覆蓋主要情境
- [ ] 可在 CI 環境中執行

---

### 1.6 Phase 1 檢查清單

**開發完成標準**：
- [ ] Task 1.1: 常數定義完成
- [ ] Task 1.2: `_apply_fadeout` 實作完成
- [ ] Task 1.3: `_apply_fadein` 實作完成
- [ ] Task 1.4: `render_video_moviepy` 整合完成
- [ ] Task 1.5: 單元測試通過

**手動測試**：
```powershell
# 測試單一影片模式淡出
python -m spellvid.cli make --letters "A" --word-en Apple --word-zh 蘋果 \
  --image assets/apple.png --music assets/apple.mp3 --out out/test_fadeout.mp4

# 檢查輸出影片最後 3 秒是否淡出
ffplay out/test_fadeout.mp4
```

**預期結果**：
- 影片最後 3 秒畫面逐漸變黑
- 音訊最後 3 秒逐漸變小

---

## 🔗 Phase 2: 批次模式整合（2 工作天）

### 2.1 任務清單

#### Task 2.1: 分析批次模式現有架構
**預估時間**：1-2 小時

**目標**：
了解 `cli.batch()` 如何處理多個影片，是否已有連接邏輯。

**檢查項目**：
- [ ] 批次模式是否已支援 `--out-file` 合併輸出？
- [ ] 如何處理多個 `render_video_stub()` 的結果？
- [ ] 是否需要新增批次連接邏輯？

**行動**：
```bash
# 檢查批次模式相關程式碼
grep -n "out-file\|concatenate" spellvid/cli.py
grep -A 20 "def batch" spellvid/cli.py
```

---

#### Task 2.2: 實作批次影片連接與淡入邏輯
**檔案**：`spellvid/utils.py` 或新增 `spellvid/batch_processor.py`  
**預估時間**：3-4 小時

**實作內容**：
```python
def concatenate_videos_with_transitions(
    video_paths: List[str],
    output_path: str,
    fade_in_duration: float = FADE_IN_DURATION,
    apply_audio_fadein: bool = False,  # Phase 3 參數
) -> Dict[str, Any]:
    """連接多個影片並應用轉場效果。
    
    Args:
        video_paths: 影片檔案路徑列表
        output_path: 輸出檔案路徑
        fade_in_duration: 淡入持續時間
        apply_audio_fadein: 是否對音訊應用淡入（Phase 3）
    
    Returns:
        包含狀態與資訊的字典
    """
    if not _HAS_MOVIEPY:
        return {"status": "error", "message": "MoviePy not available"}
    
    clips = []
    
    for idx, path in enumerate(video_paths):
        try:
            clip = _mpy.VideoFileClip(path)
            
            # 第一個影片不淡入（D2 決策）
            if idx == 0:
                # 第一個影片保持原樣（已在 render 時應用淡出）
                clips.append(clip)
            else:
                # 第二個及後續影片應用淡入
                clip_with_fadein = _apply_fadein(
                    clip,
                    duration=fade_in_duration,
                    apply_audio=apply_audio_fadein
                )
                clips.append(clip_with_fadein)
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to load {path}: {str(e)}"
            }
    
    # 連接所有片段
    try:
        final_clip = _mpy.concatenate_videoclips(clips, method='compose')
        
        # 輸出
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
        )
        
        # 清理
        for clip in clips:
            clip.close()
        final_clip.close()
        
        return {
            "status": "ok",
            "output": output_path,
            "clips_count": len(clips)
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**驗收標準**：
- [ ] 函式實作正確
- [ ] 第一個影片不淡入，後續影片淡入
- [ ] 影片連接平滑無跳幀

---

#### Task 2.3: 更新 CLI 批次模式
**檔案**：`spellvid/cli.py`  
**預估時間**：2-3 小時

**實作內容**：
1. 增加 `--out-file` 參數（如果尚未存在）
2. 修改 `batch()` 函式邏輯：
   - 如果指定 `--out-file`，收集所有輸出檔案路徑
   - 呼叫 `concatenate_videos_with_transitions()`
   - 刪除臨時單個影片檔案（可選）

**範例修改**：
```python
def batch(args: argparse.Namespace) -> int:
    data = utils.load_json(args.json)
    # ... 驗證邏輯 ...
    
    output_paths = []  # 收集輸出路徑
    
    for item in data:
        # ... 現有渲染邏輯 ...
        out_path = os.path.join(args.outdir, f"{item['word_en']}.mp4")
        
        res = utils.render_video_stub(item, out_path, ...)
        
        if res.get("status") == "ok":
            output_paths.append(out_path)
    
    # 如果指定 --out-file，進行合併
    if hasattr(args, 'out_file') and args.out_file and output_paths:
        print(f"Concatenating {len(output_paths)} videos...")
        result = utils.concatenate_videos_with_transitions(
            output_paths,
            args.out_file,
            fade_in_duration=getattr(args, 'fade_in_duration', 1.0),
            apply_audio_fadein=False,  # Phase 1-2: 固定為 False
        )
        print(f"Merged output: {result}")
    
    return 0
```

**CLI 參數定義**：
```python
p_batch.add_argument(
    "--out-file",
    dest="out_file",
    help="合併所有影片至單一輸出檔案"
)
```

**驗收標準**：
- [ ] CLI 參數正確解析
- [ ] 批次合併邏輯正確
- [ ] 錯誤處理完善

---

#### Task 2.4: 整合測試
**檔案**：`tests/test_transition_integration.py`（新建）  
**預估時間**：3-4 小時

**實作內容**：
```python
"""影片轉場整合測試。

測試批次模式影片連接與轉場效果。
"""

import os
import pytest
import subprocess
from pathlib import Path

from spellvid.utils import concatenate_videos_with_transitions, _HAS_MOVIEPY

pytestmark = pytest.mark.skipif(not _HAS_MOVIEPY, reason="MoviePy not available")


def test_concatenate_two_videos_with_transitions(tmp_path):
    """測試連接兩個影片並應用轉場效果。"""
    # 建立兩個測試影片（使用 MoviePy）
    from spellvid.utils import _mpy
    
    # 影片 A: 5 秒紅色
    clip_a = _mpy.ColorClip(size=(1920, 1080), color=(255, 0, 0), duration=5)
    path_a = tmp_path / "video_a.mp4"
    clip_a.write_videofile(str(path_a), fps=30, codec='libx264', audio=False)
    clip_a.close()
    
    # 影片 B: 5 秒綠色
    clip_b = _mpy.ColorClip(size=(1920, 1080), color=(0, 255, 0), duration=5)
    path_b = tmp_path / "video_b.mp4"
    clip_b.write_videofile(str(path_b), fps=30, codec='libx264', audio=False)
    clip_b.close()
    
    # 連接影片
    output_path = tmp_path / "merged.mp4"
    result = concatenate_videos_with_transitions(
        [str(path_a), str(path_b)],
        str(output_path),
        fade_in_duration=1.0
    )
    
    # 驗證
    assert result["status"] == "ok"
    assert output_path.exists()
    
    # 驗證輸出影片時長約為 10 秒
    duration = _get_video_duration(str(output_path))
    assert 9.5 <= duration <= 10.5


def test_first_video_no_fadein(tmp_path):
    """測試第一個影片不淡入。"""
    # 實作：建立影片並驗證第一幀不是黑色
    # ...（類似上述測試）
    pass


def _get_video_duration(path: str) -> float:
    """使用 ffprobe 獲取影片時長。"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    result = subprocess.check_output(cmd)
    return float(result.strip())
```

**驗收標準**：
- [ ] 整合測試通過
- [ ] 驗證轉場效果正確
- [ ] 可在 CI 環境執行

---

### 2.5 Phase 2 檢查清單

**開發完成標準**：
- [ ] Task 2.1: 架構分析完成
- [ ] Task 2.2: 連接邏輯實作完成
- [ ] Task 2.3: CLI 更新完成
- [ ] Task 2.4: 整合測試通過

**手動測試**：
```powershell
# 建立測試 JSON（兩個單字）
$json = @"
[
  {
    "letters": "A",
    "word_en": "Apple",
    "word_zh": "蘋果",
    "image_path": "assets/apple.png",
    "music_path": "assets/apple.mp3",
    "countdown_sec": 5,
    "reveal_hold_sec": 2
  },
  {
    "letters": "B",
    "word_en": "Ball",
    "word_zh": "球",
    "image_path": "assets/ball.png",
    "music_path": "assets/ball.mp3",
    "countdown_sec": 5,
    "reveal_hold_sec": 2
  }
]
"@
$json | Out-File test_batch.json -Encoding UTF8

# 執行批次合併
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged.mp4

# 檢查合併影片
ffplay out/merged.mp4
```

**預期結果**：
- 兩個單字影片成功合併
- 第一個單字影片直接開始（無淡入）
- 第二個單字影片從黑色淡入 1 秒
- 兩個單字影片結尾都有 3 秒淡出

---

## 🎵 Phase 3: 音訊淡入與自訂參數（2-3 工作天）

### 3.1 任務清單

#### Task 3.1: 實作音訊淡入功能
**檔案**：`spellvid/utils.py`  
**預估時間**：2-3 小時

**實作內容**：
修改 `_apply_fadein` 函式，將 `apply_audio` 參數設為實際生效。

**已在 Phase 1 預留接口**：
```python
def _apply_fadein(clip, duration: float = FADE_IN_DURATION, apply_audio: bool = False):
    # ... 已實作的畫面淡入 ...
    
    # Phase 3: 啟用音訊淡入
    if apply_audio and clip_with_fadein.audio is not None:
        clip_with_fadein = clip_with_fadein.audio_fadein(duration=duration)
    
    return clip_with_fadein
```

**測試案例**：
- [ ] 測試音訊與畫面同步淡入
- [ ] 測試淡入時音量變化正確
- [ ] 測試無音訊時不報錯

**驗收標準**：
- [ ] 音訊淡入功能正常
- [ ] 與畫面淡入同步
- [ ] 單元測試通過

---

#### Task 3.2: 增加 CLI 自訂時長參數
**檔案**：`spellvid/cli.py`  
**預估時間**：1-2 小時

**實作內容**：
```python
# 在 build_parser() 的 p_batch 部分新增

p_batch.add_argument(
    "--fade-out-duration",
    type=float,
    default=3.0,
    dest="fade_out_duration",
    help="影片結尾淡出持續時間（秒），預設 3.0"
)

p_batch.add_argument(
    "--fade-in-duration",
    type=float,
    default=1.0,
    dest="fade_in_duration",
    help="下一影片淡入持續時間（秒），預設 1.0"
)

p_batch.add_argument(
    "--no-audio-fadein",
    action="store_true",
    dest="no_audio_fadein",
    help="停用音訊淡入（預設啟用）"
)
```

**修改 `batch()` 函式**：
```python
def batch(args: argparse.Namespace) -> int:
    # ... 現有邏輯 ...
    
    # 讀取自訂參數
    fade_out = getattr(args, 'fade_out_duration', 3.0)
    fade_in = getattr(args, 'fade_in_duration', 1.0)
    audio_fadein = not getattr(args, 'no_audio_fadein', False)
    
    # 傳遞給連接函式
    if args.out_file and output_paths:
        result = utils.concatenate_videos_with_transitions(
            output_paths,
            args.out_file,
            fade_in_duration=fade_in,
            apply_audio_fadein=audio_fadein,
        )
```

**同時修改 `render_video_moviepy`**：
需要支援自訂淡出時長，可能需要：
1. 增加 `fade_out_duration` 參數到 `render_video_stub()` 和 `render_video_moviepy()`
2. 從 CLI 傳遞該參數

**驗收標準**：
- [ ] CLI 參數正確解析
- [ ] 自訂時長生效
- [ ] --help 文件清晰

---

#### Task 3.3: 更新常數為可配置
**檔案**：`spellvid/utils.py`  
**預估時間**：1 小時

**實作內容**：
修改相關函式簽名以支援自訂時長：

```python
def _apply_fadeout(clip, duration: float = None):
    """為影片片段應用淡出效果。
    
    Args:
        clip: MoviePy VideoClip 物件
        duration: 淡出持續時間（秒），None 則使用預設值 FADE_OUT_DURATION
    """
    if duration is None:
        duration = FADE_OUT_DURATION
    
    # ... 其餘邏輯不變 ...
```

類似修改應用於所有相關函式。

**驗收標準**：
- [ ] 參數傳遞正確
- [ ] 向後相容（未指定時使用預設值）

---

#### Task 3.4: Phase 3 測試
**檔案**：`tests/test_transition_audio_fadein.py`（新建）  
**預估時間**：2-3 小時

**實作內容**：
```python
"""音訊淡入功能測試。"""

import pytest
import numpy as np
from spellvid.utils import _apply_fadein, _HAS_MOVIEPY, _mpy

pytestmark = pytest.mark.skipif(not _HAS_MOVIEPY, reason="MoviePy not available")


def test_audio_fadein_enabled():
    """測試啟用音訊淡入時，音訊與畫面同步淡入。"""
    # 建立帶音訊的影片
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # 生成簡單音訊
    from moviepy.audio.AudioClip import AudioClip
    sample_rate = 44100
    duration = 10
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t)
    audio_clip = AudioClip(
        lambda t: audio_array[int(t * sample_rate)],
        duration=duration,
        fps=sample_rate
    )
    clip = clip.set_audio(audio_clip)
    
    # 應用淡入（啟用音訊）
    result = _apply_fadein(clip, duration=1.0, apply_audio=True)
    
    # 驗證音訊存在
    assert result.audio is not None
    
    # 驗證音訊開始時音量接近 0
    # （實際驗證需要取樣音訊並檢查振幅）
    # 簡化驗證：確保函式不報錯
    assert result.duration == 10


def test_audio_fadein_disabled():
    """測試停用音訊淡入時，音訊直接恢復。"""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    from moviepy.audio.AudioClip import AudioClip
    sample_rate = 44100
    duration = 10
    audio_clip = AudioClip(lambda t: np.sin(2 * np.pi * 440 * t), duration=duration, fps=sample_rate)
    clip = clip.set_audio(audio_clip)
    
    # 應用淡入（停用音訊）
    result = _apply_fadein(clip, duration=1.0, apply_audio=False)
    
    # 驗證音訊未被修改（直接恢復）
    assert result.audio is not None
    # 音訊應該與原始相同（無淡入效果）


def test_custom_fade_durations():
    """測試自訂淡出/淡入時長。"""
    clip = _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=10)
    
    # 自訂 2.5 秒淡入
    result = _apply_fadein(clip, duration=2.5, apply_audio=False)
    
    assert result.duration == 10
    # 驗證淡入持續時間正確（需要幀取樣驗證）
```

**驗收標準**：
- [ ] 音訊淡入測試通過
- [ ] 自訂時長測試通過
- [ ] 覆蓋所有 Phase 3 功能

---

### 3.5 Phase 3 檢查清單

**開發完成標準**：
- [ ] Task 3.1: 音訊淡入實作完成
- [ ] Task 3.2: CLI 參數新增完成
- [ ] Task 3.3: 可配置化改造完成
- [ ] Task 3.4: Phase 3 測試通過

**手動測試**：
```powershell
# 測試音訊淡入與自訂時長
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged_audio_fadein.mp4 --fade-out-duration 2.0 --fade-in-duration 1.5

# 測試停用音訊淡入
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged_no_audio_fadein.mp4 --no-audio-fadein
```

**預期結果**：
- 自訂時長生效
- 音訊與畫面同步淡入（預設）
- --no-audio-fadein 時音訊直接恢復

---

## 📚 文件更新任務

### Task D1: 更新 README.md
**預估時間**：1 小時

**新增內容**：
- 轉場效果功能說明
- CLI 參數使用範例
- 批次合併範例

### Task D2: 更新 TDD.md
**預估時間**：2 小時

**新增內容**：
- TCS-TRANSITION-001 ~ 006 測試案例
- 測試驗證標準
- 測試資料說明

### Task D3: 建立 CHANGELOG.md
**預估時間**：0.5 小時

**內容**：
```markdown
## [Unreleased]

### Added
- 影片轉場效果功能（3 秒淡出 + 1 秒淡入）
- 音訊同步淡出/淡入
- 批次模式影片合併 (`--out-file`)
- CLI 自訂淡出/淡入時長參數
- `--no-audio-fadein` 旗標

### Changed
- FR-EXPORT-3: 所有影片統一 3 秒淡出（原規格未實作，非 Breaking Change）
```

---

## 🧪 測試策略總覽

### 測試層級

#### 單元測試（Unit Tests）
**目標**：測試個別函式

**檔案**：
- `tests/test_transition_fadeout.py`
- `tests/test_transition_fadein.py`（可選，與 fadeout 合併）
- `tests/test_transition_audio_fadein.py`

**覆蓋率目標**：> 80%

#### 整合測試（Integration Tests）
**目標**：測試多個元件協作

**檔案**：
- `tests/test_transition_integration.py`

**測試案例**：
- 批次模式影片連接
- 轉場效果正確性
- 音訊與畫面同步

#### 端對端測試（E2E Tests）
**目標**：測試完整 CLI 流程

**方式**：手動測試或腳本自動化

**測試案例**：
- 單一影片輸出
- 批次合併輸出
- 自訂參數測試

---

## 📊 進度追蹤

### 每日檢查點

**Day 1**（Phase 1 開始）:
- [ ] Task 1.1-1.3 完成（輔助函式）
- [ ] 單元測試框架建立

**Day 2-3**（Phase 1 完成）:
- [ ] Task 1.4 完成（整合淡出）
- [ ] Task 1.5 完成（單元測試）
- [ ] Phase 1 手動測試通過

**Day 4-5**（Phase 2 完成）:
- [ ] Task 2.1-2.3 完成（批次整合）
- [ ] Task 2.4 完成（整合測試）
- [ ] Phase 2 手動測試通過

**Day 6-8**（Phase 3 完成）:
- [ ] Task 3.1-3.3 完成（音訊淡入與參數）
- [ ] Task 3.4 完成（Phase 3 測試）
- [ ] 文件更新完成
- [ ] 所有測試通過

---

## 🚀 交付標準

### 程式碼品質
- [ ] 所有函式有 docstring
- [ ] 型別註解完整
- [ ] 符合專案風格指南（PEP 8）
- [ ] 無明顯程式碼異味

### 測試品質
- [ ] 單元測試覆蓋率 > 80%
- [ ] 整合測試通過
- [ ] E2E 手動測試通過
- [ ] CI 環境測試通過

### 文件品質
- [ ] README.md 更新
- [ ] TDD.md 更新
- [ ] CHANGELOG.md 建立
- [ ] 程式碼註解清晰

### 功能驗收
- [ ] 所有影片統一 3 秒淡出
- [ ] 批次模式第一個影片不淡入
- [ ] 批次模式後續影片 1 秒淡入
- [ ] 音訊與畫面同步處理
- [ ] CLI 參數正常運作
- [ ] 無明顯 bug

---

## ⚠️ 風險與緩解

### 風險 1：MoviePy 版本相容性
**影響**：fade 函式行為可能因版本而異

**緩解措施**：
- 鎖定 MoviePy 版本於 `requirements-dev.txt`
- 測試多個版本確保相容
- 文件記錄已測試版本

### 風險 2：效能問題
**影響**：淡出/淡入處理可能增加渲染時間

**緩解措施**：
- 監測渲染時間變化
- 優化 MoviePy 參數（preset, threads）
- 必要時提供 `--disable-transitions` 旗標

### 風險 3：音訊同步問題
**影響**：複雜場景下音訊與畫面可能不同步

**緩解措施**：
- 詳細測試音訊同步
- 使用 MoviePy 內建同步機制
- 記錄已知限制於文件

### 風險 4：測試環境限制
**影響**：CI 環境可能缺少 FFmpeg 或 MoviePy

**緩解措施**：
- 使用 `pytest.skip` 條件跳過
- 提供本地測試腳本
- 文件說明測試環境需求

---

## 📞 團隊溝通

### 開發階段同步
- **頻率**：每日或每兩日
- **內容**：進度更新、阻塞問題、技術討論

### 程式碼審查
- **時機**：每個 Phase 完成後
- **檢查點**：功能正確性、測試覆蓋率、程式碼品質

### 最終驗收
- **時機**：Phase 3 完成後
- **參與者**：產品負責人、技術負責人、QA
- **標準**：參照「交付標準」章節

---

## 📝 附錄

### A. 相關檔案清單

**核心程式碼**：
- `spellvid/utils.py` - 主要邏輯修改
- `spellvid/cli.py` - CLI 參數與批次邏輯

**測試檔案**：
- `tests/test_transition_fadeout.py`
- `tests/test_transition_integration.py`
- `tests/test_transition_audio_fadein.py`

**文件檔案**：
- `README.md`
- `doc/TDD.md`
- `CHANGELOG.md`

### B. 參考資源

- [MoviePy Documentation](http://zulko.github.io/moviepy/)
- [MoviePy fadeout/fadein API](http://zulko.github.io/moviepy/ref/VideoClip/VideoClip.html)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- 專案規格文件：`.specify/video-transition-effects.md`
- 決策文件：`.specify/video-transition-effects-decisions.md`

### C. 常見問題

**Q: 為什麼單一影片也要淡出？**  
A: 根據 D1 決策，選擇一致性優先，所有影片統一淡出簡化實作。

**Q: 為什麼第一個影片不淡入？**  
A: 根據 D2 決策，開頭影片很短，直接開始避免額外延遲。

**Q: Phase 3 音訊淡入是否必要？**  
A: 根據 D4 決策，音訊淡入是必要功能，避免音訊突兀恢復。

---

**計畫版本歷史**

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-01-08 | 初版建立 | GitHub Copilot |

---

**計畫結束**

請依序執行 Phase 1 → Phase 2 → Phase 3，每個階段完成後進行檢查點驗收再繼續下一階段。祝開發順利！🚀
