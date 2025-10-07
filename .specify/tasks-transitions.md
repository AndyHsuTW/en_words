# 影片轉場效果 - 開發任務清單

**任務清單版本**：v1.0  
**建立日期**：2025-01-08  
**預估時程**：6-8 工作天  
**完整計畫**：`implementation-plan-transitions.md`

---

## 任務統計

- **總任務數**：17 個
  - 開發任務：14 個
  - 文件任務：3 個
- **測試檔案**：3 個新建
- **預估時程**：6-8 工作天

---

## Phase 1: 核心功能實作（2-3 工作天）

### Task 1.1 - 新增淡出/淡入常數

**預估時間**：0.5 小時  
**檔案**：`spellvid/utils.py`  
**位置**：約第 40-80 行附近（常數定義區）

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

### Task 1.2 - 實作淡出效果函式

**預估時間**：1-2 小時  
**檔案**：`spellvid/utils.py`  
**位置**：新增於 `render_video_moviepy` 之前

**函式簽名**：
```python
def _apply_fadeout(clip, duration: float = FADE_OUT_DURATION):
    """為影片片段應用淡出效果（畫面與音訊）。"""
```

**功能需求**：
- [ ] 應用畫面淡出（`fadeout()`）
- [ ] 應用音訊淡出（`audio_fadeout()`）
- [ ] 處理短影片（< 3 秒）不淡出
- [ ] 處理無音訊情況不報錯

**測試需求**：
- [ ] 10 秒影片應用 3 秒淡出
- [ ] 2 秒短影片不淡出
- [ ] 有音訊同步淡出
- [ ] 無音訊不報錯

**驗收標準**：
- [ ] 函式實作正確
- [ ] 邊界情況處理完善
- [ ] 單元測試通過

---

### Task 1.3 - 實作淡入效果函式

**預估時間**：1 小時  
**檔案**：`spellvid/utils.py`  
**位置**：緊接 `_apply_fadeout` 之後

**函式簽名**：
```python
def _apply_fadein(clip, duration: float = FADE_IN_DURATION, apply_audio: bool = False):
    """為影片片段應用淡入效果。"""
```

**功能需求**：
- [ ] 應用畫面淡入（`fadein()`）
- [ ] 預留音訊淡入接口（`apply_audio` 參數，Phase 3 啟用）
- [ ] 處理短影片（< 1 秒）不淡入

**測試需求**：
- [ ] 10 秒影片應用 1 秒淡入
- [ ] 0.5 秒短影片不淡入
- [ ] `apply_audio=True` 時音訊淡入（Phase 3 測試）

**驗收標準**：
- [ ] 函式實作正確
- [ ] `apply_audio` 參數預留擴充性
- [ ] 單元測試通過

---

### Task 1.4 - 整合淡出至 render_video_moviepy

**預估時間**：2-3 小時  
**檔案**：`spellvid/utils.py`  
**位置**：`render_video_moviepy` 函式（約第 1684 行）

**修改位置**：
找到最終 `final_clip` 建立後、`final_clip.write_videofile()` 之前

**修改內容**：
```python
# 在此處（約第 3150-3160 行）
# 原本：final_clip = _mpy.concatenate_videoclips(...)

# 新增：應用淡出效果（所有影片統一淡出，D1 決策）
final_clip = _apply_fadeout(final_clip, duration=FADE_OUT_DURATION)

# 然後：final_clip.write_videofile(...)
```

**注意事項**：
- [ ] 確保在 entry.mp4 和 ending.mp4 連接後應用
- [ ] 結尾影片 (ending.mp4) 不額外淡出（D8 決策）
- [ ] 需要重新檢視程式碼結構，找到正確的應用點

**測試需求**：
- [ ] 單一影片模式輸出有 3 秒淡出
- [ ] 批次模式每個單字影片有 3 秒淡出
- [ ] 淡出不影響 ending.mp4

**驗收標準**：
- [ ] 所有影片統一應用淡出
- [ ] 不影響其他功能
- [ ] 整合測試通過

---

### Task 1.5 - 建立單元測試

**預估時間**：2-3 小時  
**檔案**：`tests/test_transition_fadeout.py`（新建）

**測試案例**：
- [ ] `test_fadeout_normal_video()` - 正常影片淡出
- [ ] `test_fadeout_short_video()` - 短影片處理
- [ ] `test_fadeout_with_audio()` - 音訊同步淡出
- [ ] `test_fadeout_no_audio()` - 無音訊處理
- [ ] `test_fadein_normal_video()` - 正常影片淡入
- [ ] `test_fadein_short_video()` - 短影片淡入

**驗證方式**：
- [ ] 使用 MoviePy 建立測試影片
- [ ] 檢查關鍵幀亮度變化
- [ ] 驗證時長不變

**驗收標準**：
- [ ] 所有測試通過
- [ ] 測試覆蓋主要情境
- [ ] 可在 CI 環境執行（或條件跳過）

---

### Phase 1 手動驗證

**測試指令**：
```powershell
# 啟動 venv
.\.venv\Scripts\Activate.ps1

# 測試單一影片模式淡出
python -m spellvid.cli make --letters "A" --word-en Apple --word-zh 蘋果 \
  --image assets/apple.png --music assets/apple.mp3 --out out/test_fadeout.mp4

# 檢查輸出影片
ffplay out/test_fadeout.mp4
```

**預期結果**：
- [ ] 影片最後 3 秒畫面逐漸變黑
- [ ] 音訊最後 3 秒逐漸變小
- [ ] 無明顯異常或錯誤

---

## Phase 2: 批次模式整合（2 工作天）

### Task 2.1 - 分析批次模式架構

**預估時間**：1-2 小時

**目標**：
- [ ] 了解 `cli.batch()` 如何處理多個影片
- [ ] 檢查是否已有 `--out-file` 合併參數
- [ ] 確認影片連接邏輯位置

**行動**：
```bash
# 檢查批次模式相關程式碼
grep -n "out-file\|concatenate" spellvid/cli.py
grep -A 20 "def batch" spellvid/cli.py

# 檢查 utils.py 中的連接邏輯
grep -n "concatenate_videoclips" spellvid/utils.py
```

**輸出**：
- [ ] 文件筆記記錄現有架構
- [ ] 確定修改點

---

### Task 2.2 - 實作批次影片連接函式

**預估時間**：3-4 小時  
**檔案**：`spellvid/utils.py`  
**位置**：新增函式

**函式簽名**：
```python
def concatenate_videos_with_transitions(
    video_paths: List[str],
    output_path: str,
    fade_in_duration: float = FADE_IN_DURATION,
    apply_audio_fadein: bool = False,  # Phase 3 參數
) -> Dict[str, Any]:
    """連接多個影片並應用轉場效果。"""
```

**功能需求**：
- [ ] 載入多個影片片段
- [ ] 第一個影片不淡入（D2 決策）
- [ ] 第二個及後續影片應用 1 秒淡入
- [ ] 使用 `concatenate_videoclips` 連接
- [ ] 輸出最終合併影片
- [ ] 返回狀態與資訊

**實作邏輯**：
```python
clips = []
for idx, path in enumerate(video_paths):
    clip = _mpy.VideoFileClip(path)
    
    # 第一個影片不淡入（D2 決策）
    if idx == 0:
        clips.append(clip)
    else:
        # 後續影片淡入
        clip_with_fadein = _apply_fadein(
            clip, 
            duration=fade_in_duration,
            apply_audio=apply_audio_fadein
        )
        clips.append(clip_with_fadein)

# 連接
final_clip = _mpy.concatenate_videoclips(clips, method='compose')
final_clip.write_videofile(output_path, ...)
```

**驗收標準**：
- [ ] 函式實作正確
- [ ] 第一個影片不淡入，後續影片淡入
- [ ] 影片連接平滑無跳幀
- [ ] 錯誤處理完善

---

### Task 2.3 - 更新 CLI 批次模式

**預估時間**：2-3 小時  
**檔案**：`spellvid/cli.py`

**新增 CLI 參數**：
```python
p_batch.add_argument(
    "--out-file",
    dest="out_file",
    help="合併所有影片至單一輸出檔案"
)
```

**修改 `batch()` 函式**：
```python
def batch(args: argparse.Namespace) -> int:
    # ... 現有邏輯 ...
    
    output_paths = []  # 收集輸出路徑
    
    for item in data:
        # ... 渲染邏輯 ...
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
            fade_in_duration=1.0,
            apply_audio_fadein=False,  # Phase 1-2: 固定為 False
        )
        print(f"Merged output: {result}")
    
    return 0
```

**驗收標準**：
- [ ] CLI 參數正確解析
- [ ] `--help` 顯示正確
- [ ] 批次合併邏輯正確
- [ ] 錯誤處理完善

---

### Task 2.4 - 建立整合測試

**預估時間**：3-4 小時  
**檔案**：`tests/test_transition_integration.py`（新建）

**測試案例**：
- [ ] `test_concatenate_two_videos_with_transitions()`
  - 建立 2 個測試影片（紅色、綠色）
  - 連接並驗證轉場效果
  - 驗證總時長正確
  
- [ ] `test_first_video_no_fadein()`
  - 驗證第一個影片第一幀不是黑色
  
- [ ] `test_second_video_has_fadein()`
  - 驗證第二個影片前 1 秒從黑色淡入

**輔助函式**：
```python
def _get_video_duration(path: str) -> float:
    """使用 ffprobe 獲取影片時長。"""
    cmd = [
        "ffprobe", "-v", "error",
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

### Phase 2 手動驗證

**建立測試 JSON**：
```json
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
```

**測試指令**：
```powershell
# 執行批次合併
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged.mp4

# 檢查合併影片
ffplay out/merged.mp4
```

**預期結果**：
- [ ] 兩個單字影片成功合併
- [ ] 第一個單字影片直接開始（無淡入）
- [ ] 第二個單字影片從黑色淡入 1 秒
- [ ] 兩個單字影片結尾都有 3 秒淡出

---

## Phase 3: 音訊淡入與自訂參數（2-3 工作天）

### Task 3.1 - 實作音訊淡入功能

**預估時間**：2-3 小時  
**檔案**：`spellvid/utils.py`  
**修改**：`_apply_fadein()` 函式

**實作內容**：
啟用 `apply_audio` 參數實際效果

```python
def _apply_fadein(clip, duration: float = FADE_IN_DURATION, apply_audio: bool = False):
    # ... 畫面淡入 ...
    
    # Phase 3: 啟用音訊淡入
    if apply_audio and clip_with_fadein.audio is not None:
        clip_with_fadein = clip_with_fadein.audio_fadein(duration=duration)
    
    return clip_with_fadein
```

**測試需求**：
- [ ] 音訊與畫面同步淡入
- [ ] 驗證音量變化正確
- [ ] 無音訊時不報錯

**驗收標準**：
- [ ] 音訊淡入功能正常
- [ ] 與畫面淡入同步
- [ ] 單元測試通過

---

### Task 3.2 - 新增 CLI 自訂參數

**預估時間**：1-2 小時  
**檔案**：`spellvid/cli.py`

**新增參數**：
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

**驗收標準**：
- [ ] CLI 參數正確解析
- [ ] 自訂時長生效
- [ ] `--help` 文件清晰

---

### Task 3.3 - 更新函式支援自訂時長

**預估時間**：1 小時  
**檔案**：`spellvid/utils.py`

**修改函式簽名**：
```python
def _apply_fadeout(clip, duration: float = None):
    """為影片片段應用淡出效果。
    
    Args:
        duration: 淡出持續時間（秒），None 則使用預設值 FADE_OUT_DURATION
    """
    if duration is None:
        duration = FADE_OUT_DURATION
    # ... 其餘邏輯不變 ...

def _apply_fadein(clip, duration: float = None, apply_audio: bool = False):
    """為影片片段應用淡入效果。
    
    Args:
        duration: 淡入持續時間（秒），None 則使用預設值 FADE_IN_DURATION
    """
    if duration is None:
        duration = FADE_IN_DURATION
    # ... 其餘邏輯不變 ...
```

**修改影響**：
- [ ] `render_video_moviepy()` 增加 `fade_out_duration` 參數
- [ ] `concatenate_videos_with_transitions()` 已支援自訂參數
- [ ] 確保向後相容（未指定時使用預設值）

**驗收標準**：
- [ ] 參數傳遞正確
- [ ] 向後相容

---

### Task 3.4 - 建立 Phase 3 測試

**預估時間**：2-3 小時  
**檔案**：`tests/test_transition_audio_fadein.py`（新建）

**測試案例**：
- [ ] `test_audio_fadein_enabled()`
  - 驗證音訊與畫面同步淡入
  
- [ ] `test_audio_fadein_disabled()`
  - 驗證音訊直接恢復（無淡入）
  
- [ ] `test_custom_fade_durations()`
  - 驗證自訂時長生效

**測試技巧**：
```python
# 使用 numpy 生成測試音訊
import numpy as np
sample_rate = 44100
duration = 10
t = np.linspace(0, duration, int(sample_rate * duration))
audio_array = np.sin(2 * np.pi * 440 * t)

from moviepy.audio.AudioClip import AudioClip
audio_clip = AudioClip(
    lambda t: audio_array[int(t * sample_rate)],
    duration=duration,
    fps=sample_rate
)
```

**驗收標準**：
- [ ] 音訊淡入測試通過
- [ ] 自訂時長測試通過
- [ ] 覆蓋所有 Phase 3 功能

---

### Phase 3 手動驗證

**測試音訊淡入**：
```powershell
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged_audio.mp4
```

**測試自訂時長**：
```powershell
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged_custom.mp4 \
  --fade-out-duration 2.0 --fade-in-duration 1.5
```

**測試停用音訊淡入**：
```powershell
python -m spellvid.cli batch --json test_batch.json --outdir out --out-file out/merged_no_audio.mp4 \
  --no-audio-fadein
```

**預期結果**：
- [ ] 音訊與畫面同步淡入（預設）
- [ ] 自訂時長參數生效
- [ ] `--no-audio-fadein` 時音訊直接恢復

---

## 文件更新任務

### Task D1 - 更新 README.md

**預估時間**：1 小時  
**檔案**：`README.md`

**新增章節**：
```markdown
## 影片轉場效果

SpellVid 支援專業的影片轉場效果：

### 功能特點
- **統一淡出**：所有影片末端自動加入 3 秒淡出（畫面與音訊）
- **批次淡入**：批次模式中，後續影片從黑色淡入 1 秒
- **音訊同步**：音訊與畫面同步淡出/淡入處理
- **可自訂參數**：支援自訂淡出/淡入時長

### 使用範例

#### 單一影片（自動淡出）
```powershell
python -m spellvid.cli make --letters "A" --word-en Apple --word-zh 蘋果 \
  --image assets/apple.png --music assets/apple.mp3 --out out/Apple.mp4
```

#### 批次合併（含轉場效果）
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file out/merged.mp4
```

#### 自訂轉場時長
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file out/merged.mp4 \
  --fade-out-duration 2.0 --fade-in-duration 1.5
```

#### 停用音訊淡入
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file out/merged.mp4 \
  --no-audio-fadein
```
```

**驗收標準**：
- [ ] 文件清晰易懂
- [ ] 範例可執行
- [ ] 格式正確

---

### Task D2 - 更新 doc/TDD.md

**預估時間**：2 小時  
**檔案**：`doc/TDD.md`

**新增測試案例**：

#### TCS-TRANSITION-001: 淡出效果測試
- **測試檔案**：`tests/test_transition_fadeout.py`
- **測試目標**：驗證影片淡出效果正確性
- **測試案例**：
  - 正常影片淡出（10 秒影片 3 秒淡出）
  - 短影片處理（< 3 秒不淡出）
  - 音訊同步淡出
  - 無音訊處理

#### TCS-TRANSITION-002: 淡入效果測試
- **測試檔案**：`tests/test_transition_fadeout.py`
- **測試目標**：驗證影片淡入效果正確性
- **測試案例**：
  - 正常影片淡入（10 秒影片 1 秒淡入）
  - 短影片處理（< 1 秒不淡入）

#### TCS-TRANSITION-003: 音訊同步測試
- **測試檔案**：`tests/test_transition_audio_fadein.py`
- **測試目標**：驗證音訊與畫面同步淡入
- **測試案例**：
  - 音訊淡入啟用
  - 音訊淡入停用

#### TCS-TRANSITION-004: 批次轉場整合測試
- **測試檔案**：`tests/test_transition_integration.py`
- **測試目標**：驗證批次模式轉場效果
- **測試案例**：
  - 連接兩個影片
  - 第一個影片不淡入
  - 第二個影片淡入

#### TCS-TRANSITION-005: 邊界情況測試
- **測試目標**：驗證邊界情況處理
- **測試案例**：
  - 超短影片（< 1 秒）
  - 無音訊影片
  - 單一影片批次

#### TCS-TRANSITION-006: CLI 參數測試
- **測試目標**：驗證 CLI 參數正確解析
- **測試案例**：
  - 自訂淡出時長
  - 自訂淡入時長
  - --no-audio-fadein 旗標

**驗收標準**：
- [ ] 測試案例完整
- [ ] 格式符合現有 TDD.md 風格
- [ ] 驗證標準明確

---

### Task D3 - 建立 CHANGELOG.md

**預估時間**：0.5 小時  
**檔案**：`CHANGELOG.md`（新建）

**內容**：
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- 影片轉場效果功能（3 秒淡出 + 1 秒淡入）
  - 所有影片統一應用 3 秒淡出（畫面與音訊）
  - 批次模式影片間 1 秒淡入（僅畫面）
  - Phase 3: 音訊同步淡入功能
- 批次模式影片合併功能 (`--out-file`)
  - 第一個影片不淡入，後續影片淡入
- CLI 自訂轉場時長參數
  - `--fade-out-duration` 自訂淡出時長（預設 3.0 秒）
  - `--fade-in-duration` 自訂淡入時長（預設 1.0 秒）
  - `--no-audio-fadein` 停用音訊淡入旗標
- 完整的單元測試與整合測試
  - `tests/test_transition_fadeout.py`
  - `tests/test_transition_integration.py`
  - `tests/test_transition_audio_fadein.py`

### Changed
- FR-EXPORT-3: 影片淡出時長從 1 秒延長至 3 秒
  - 注意：原 1 秒淡出從未實作，此為首次實作，非破壞性變更
- FR-EXPORT-6: 新增批次模式轉場效果需求（優先度 Should）

### Technical Details
- 新增函式：`_apply_fadeout()`, `_apply_fadein()`, `concatenate_videos_with_transitions()`
- 修改函式：`render_video_moviepy()`, `batch()`
- 使用 MoviePy 內建 `fadeout()` / `fadein()` API
- 線性淡出/淡入曲線
```

**驗收標準**：
- [ ] 格式符合 Keep a Changelog 標準
- [ ] 內容完整準確
- [ ] 分類清晰（Added, Changed, Technical Details）

---

## 最終驗收檢查清單

### 功能驗收

- [ ] **淡出效果**：所有影片統一 3 秒淡出
- [ ] **淡入效果**：批次模式第一個影片不淡入
- [ ] **淡入效果**：批次模式後續影片 1 秒淡入
- [ ] **音訊同步**：音訊與畫面同步淡出/淡入
- [ ] **CLI 參數**：`--fade-out-duration` 正常運作
- [ ] **CLI 參數**：`--fade-in-duration` 正常運作
- [ ] **CLI 參數**：`--no-audio-fadein` 正常運作
- [ ] **批次合併**：`--out-file` 正常運作
- [ ] **結尾影片**：ending.mp4 不額外淡出

### 測試驗收

- [ ] **單元測試**：覆蓋率 > 80%
- [ ] **單元測試**：所有測試通過
- [ ] **整合測試**：批次轉場測試通過
- [ ] **E2E 測試**：手動測試通過
- [ ] **CI 環境**：測試可執行（或條件跳過）

### 文件驗收

- [ ] **README.md**：功能說明已新增
- [ ] **README.md**：使用範例已新增
- [ ] **doc/TDD.md**：測試案例已新增
- [ ] **CHANGELOG.md**：變更記錄已建立
- [ ] **程式碼註解**：所有函式有 docstring
- [ ] **型別註解**：函式參數與返回值完整

### 程式碼品質

- [ ] **風格**：符合 PEP 8
- [ ] **命名**：變數與函式命名清晰
- [ ] **複雜度**：無過度複雜的函式
- [ ] **重複**：無明顯重複程式碼
- [ ] **錯誤處理**：邊界情況處理完善
- [ ] **審查**：程式碼審查通過

---

## 時程追蹤

**Phase 1: 核心功能**
- 開始日期：_______________
- 完成日期：_______________
- 實際耗時：_____ 天

**Phase 2: 批次整合**
- 開始日期：_______________
- 完成日期：_______________
- 實際耗時：_____ 天

**Phase 3: 音訊與參數**
- 開始日期：_______________
- 完成日期：_______________
- 實際耗時：_____ 天

**文件更新**
- 完成日期：_______________
- 實際耗時：_____ 天

**總計耗時**：_____ 工作天（預估 6-8 天）

---

## 阻塞問題記錄

| 日期 | 問題描述 | 影響任務 | 負責人 | 狀態 | 解決方案 |
|------|---------|---------|--------|------|---------|
|      |         |         |        |      |         |

---

## 參考文件

- **完整計畫**：`.specify/implementation-plan-transitions.md`
- **決策文件**：`.specify/video-transition-effects-decisions.md`
- **規格文件**：`.specify/video-transition-effects.md`
- **檢查清單**：`.specify/task-checklist-transitions.md`

---

**最後更新**：2025-01-08  
**版本**：v1.0  
**狀態**：待開始

🚀 **準備開始開發！從 Phase 1 Task 1.1 開始！**
