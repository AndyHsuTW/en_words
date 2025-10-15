# Function Contracts: 專案架構重構 - 公開 API 規範

**Feature**: 002-refactor-architecture  
**Date**: 2025-10-14  
**Purpose**: 定義重構後各模組的公開函數簽名、輸入輸出規範與錯誤處理策略

---

## 契約說明

本文檔定義所有模組的**公開 API 契約**,包括:
- 函數簽名(參數與回傳值型別)
- 前置條件(preconditions)
- 後置條件(postconditions)
- 異常處理規範
- 效能預期(performance expectations)

所有契約遵循 **Design by Contract** 原則,並支援靜態型別檢查(Pylance/mypy)。

---

## 1. 共用層 (shared/)

### 1.1 shared/types.py

#### VideoConfig.from_dict()

```python
@classmethod
def from_dict(cls, data: dict) -> "VideoConfig"
```

**前置條件**:
- `data` 必須包含必填欄位: `letters`, `word_en`, `word_zh`
- 欄位型別必須符合 schema 定義

**後置條件**:
- 回傳有效的 `VideoConfig` 實例
- 所有可選欄位填入預設值

**異常**:
- `KeyError`: 缺少必填欄位
- `ValueError`: 欄位值無效(如 countdown_sec < 0)
- `TypeError`: 欄位型別錯誤

**範例**:
```python
data = {
    "letters": "I i",
    "word_en": "Ice",
    "word_zh": "ㄅㄧㄥ 冰"
}
config = VideoConfig.from_dict(data)
assert config.countdown_sec == 3.0  # 預設值
```

---

#### VideoConfig.to_dict()

```python
def to_dict(self) -> dict
```

**前置條件**: 無

**後置條件**:
- 回傳包含所有欄位的字典
- 可被 JSON 序列化
- 可用於 `from_dict()` 往返轉換

**異常**: 無

**範例**:
```python
config = VideoConfig(letters="A a", word_en="Apple", word_zh="蘋果")
data = config.to_dict()
assert data["letters"] == "A a"
```

---

### 1.2 shared/validation.py

#### validate_schema()

```python
def validate_schema(data: dict) -> None
```

**前置條件**:
- `data` 為字典

**後置條件**:
- 若驗證通過,無回傳值
- 若驗證失敗,拋出異常

**異常**:
- `jsonschema.ValidationError`: Schema 驗證失敗,錯誤訊息包含失敗欄位

**範例**:
```python
validate_schema({"letters": "A", "word_en": "Apple", "word_zh": "蘋果"})
# 通過,無異常

validate_schema({"letters": 123})  # ❌ letters 應為字串
# 拋出 ValidationError
```

---

#### load_json()

```python
def load_json(file_path: str) -> List[dict]
```

**前置條件**:
- `file_path` 指向存在的 JSON 檔案
- JSON 內容為陣列

**後置條件**:
- 回傳 JSON 陣列內容
- 每個項目為字典

**異常**:
- `FileNotFoundError`: 檔案不存在
- `json.JSONDecodeError`: JSON 格式錯誤
- `TypeError`: JSON 內容不是陣列

**範例**:
```python
items = load_json("config.json")
assert isinstance(items, list)
assert all(isinstance(item, dict) for item in items)
```

---

## 2. 領域層 (domain/)

### 2.1 domain/layout.py

#### compute_layout_bboxes()

```python
def compute_layout_bboxes(
    config: VideoConfig,
    timer_visible: bool = True,
    progress_bar: bool = True
) -> LayoutResult
```

**前置條件**:
- `config` 為有效的 `VideoConfig` 實例
- `config.word_zh` 包含中文字元

**後置條件**:
- 回傳 `LayoutResult`,包含所有必要邊界框
- 所有邊界框不超出 1920x1080 畫布
- 中文與字母區域不重疊(除非設計允許)
- 注音排版正確(垂直排列,符號間距合理)

**異常**:
- `ValueError`: 配置無效(如字串過長無法排版)

**效能預期**:
- 執行時間 < 50ms (單次呼叫)

**範例**:
```python
config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
result = compute_layout_bboxes(config)
assert result.letters.x < result.word_zh.x  # 字母在左,中文在右
assert result.reveal.width > 0
```

---

#### extract_chinese_chars()

```python
def extract_chinese_chars(text: str) -> List[str]
```

**前置條件**:
- `text` 為字串

**後置條件**:
- 回傳字串中的所有中文字元列表
- 過濾注音符號、空格、標點

**異常**: 無

**範例**:
```python
assert extract_chinese_chars("ㄅㄧㄥ 冰") == ["冰"]
assert extract_chinese_chars("ㄒㄩㄝˊ 雪") == ["雪"]
```

---

### 2.2 domain/typography.py

#### zhuyin_for()

```python
def zhuyin_for(chinese_char: str) -> Optional[str]
```

**前置條件**:
- `chinese_char` 為單一中文字元

**後置條件**:
- 回傳對應的注音符號字串(如 "ㄅㄧㄥ")
- 若查無對應,回傳 None

**異常**: 無

**效能預期**:
- 查詢時間 < 1ms (字典查詢)

**範例**:
```python
assert zhuyin_for("冰") == "ㄅㄧㄥ"
assert zhuyin_for("雪") == "ㄒㄩㄝˊ"
assert zhuyin_for("你好") is None  # 非單一字元
```

---

#### split_zhuyin_symbols()

```python
def split_zhuyin_symbols(zhuyin: str) -> Tuple[List[str], Optional[str]]
```

**前置條件**:
- `zhuyin` 為有效的注音字串

**後置條件**:
- 回傳 (主要符號列表, 聲調符號)
- 聲調符號為 "ˊ", "ˇ", "ˋ", "˙" 之一,或 None

**異常**: 無

**範例**:
```python
main, tone = split_zhuyin_symbols("ㄅㄧㄥ")
assert main == ["ㄅ", "ㄧ", "ㄥ"]
assert tone is None

main, tone = split_zhuyin_symbols("ㄒㄩㄝˊ")
assert main == ["ㄒ", "ㄩ", "ㄝ"]
assert tone == "ˊ"
```

---

### 2.3 domain/effects.py

#### apply_fadeout()

```python
def apply_fadeout(clip: ClipLike, duration: float) -> ClipLike
```

**前置條件**:
- `clip` 為有效的 Clip 物件
- `duration` > 0

**後置條件**:
- 回傳套用淡出效果的 Clip
- 原始 Clip 不變(immutable)

**異常**:
- `ValueError`: duration 無效

**範例**:
```python
faded = apply_fadeout(clip, 0.5)
assert faded.duration == clip.duration  # 時長不變
```

---

#### concatenate_videos_with_transitions()

```python
def concatenate_videos_with_transitions(
    clips: List[ClipLike],
    transition_duration: float = 0.5
) -> ClipLike
```

**前置條件**:
- `clips` 至少包含 2 個 Clip
- `transition_duration` >= 0

**後置條件**:
- 回傳串接後的 Clip
- 轉場淡入淡出效果正確

**異常**:
- `ValueError`: clips 數量 < 2

**效能預期**:
- 執行時間與 clips 數量成正比,不涉及實際渲染

**範例**:
```python
result = concatenate_videos_with_transitions([clip1, clip2, clip3])
assert result.duration == sum(c.duration for c in [clip1, clip2, clip3])
```

---

### 2.4 domain/timing.py

#### calculate_timeline()

```python
def calculate_timeline(
    config: VideoConfig
) -> Dict[str, float]
```

**前置條件**:
- `config` 為有效的 `VideoConfig`

**後置條件**:
- 回傳時間軸字典,包含關鍵時間點:
  - `"countdown_start"`: 倒數開始時間
  - `"reveal_start"`: 中文顯示時間
  - `"total_duration"`: 總時長

**異常**: 無

**範例**:
```python
timeline = calculate_timeline(config)
assert timeline["countdown_start"] == 0.0
assert timeline["reveal_start"] == config.countdown_sec
assert timeline["total_duration"] == config.countdown_sec + config.reveal_hold_sec
```

---

## 3. 應用層 (application/)

### 3.1 application/video_service.py

#### render_video()

```python
def render_video(
    config: VideoConfig,
    output_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
    composer: Optional[IVideoComposer] = None
) -> Dict[str, Any]
```

**前置條件**:
- `config` 為有效的 `VideoConfig`
- `output_path` 為可寫入的路徑
- 若 `dry_run=False`,資源檔案必須存在

**後置條件**:
- 若 `dry_run=True`,僅回傳 metadata,不產生檔案
- 若 `dry_run=False`,產生 MP4 檔案於 `output_path`
- 回傳字典包含:
  - `"success"`: bool
  - `"duration"`: float
  - `"output_path"`: str
  - `"metadata"`: dict (佈局、資源資訊)

**異常**:
- `FileNotFoundError`: 資源檔案不存在
- `RuntimeError`: 渲染失敗

**效能預期**:
- Dry-run: < 100ms
- 實際渲染: 取決於視頻時長,約 1-5x real-time

**範例**:
```python
result = render_video(config, "out/test.mp4", dry_run=True)
assert result["success"] is True
assert "metadata" in result

result = render_video(config, "out/test.mp4", dry_run=False)
assert os.path.exists("out/test.mp4")
```

---

### 3.2 application/batch_service.py

#### render_batch()

```python
def render_batch(
    configs: List[VideoConfig],
    output_dir: str,
    dry_run: bool = False,
    entry_hold: float = 0.0,
    skip_ending_per_video: bool = True
) -> Dict[str, Any]
```

**前置條件**:
- `configs` 至少包含 1 個 VideoConfig
- `output_dir` 為有效目錄路徑

**後置條件**:
- 產生多支視頻於 `output_dir`
- 回傳批次結果摘要:
  - `"total"`: int (總數)
  - `"success"`: int (成功數)
  - `"failed"`: int (失敗數)
  - `"results"`: List[dict] (每支視頻結果)

**異常**:
- `FileNotFoundError`: 輸出目錄不存在
- 單支視頻失敗不中斷批次處理

**效能預期**:
- 批次處理 100 支視頻 ≤ 110% 單獨處理時間總和

**範例**:
```python
result = render_batch(configs, "out/", dry_run=True)
assert result["total"] == len(configs)
assert result["success"] + result["failed"] == result["total"]
```

---

### 3.3 application/resource_checker.py

#### check_assets()

```python
def check_assets(config: VideoConfig) -> Dict[str, Any]
```

**前置條件**:
- `config` 為有效的 `VideoConfig`

**後置條件**:
- 回傳資源檢查結果:
  - `"image"`: {"exists": bool, "path": str}
  - `"music"`: {"exists": bool, "path": str}
  - `"letters"`: {"exists": bool, "paths": List[str]}
  - `"all_present"`: bool

**異常**: 無(檢查失敗回傳 exists=False)

**範例**:
```python
result = check_assets(config)
assert "all_present" in result
if result["all_present"]:
    # 所有資源存在
    pass
```

---

#### prepare_entry_context()

```python
def prepare_entry_context() -> Dict[str, Any]
```

**前置條件**: 無

**後置條件**:
- 回傳片頭資源資訊:
  - `"video_path"`: str (若存在)
  - `"duration"`: float (若可查詢)
  - `"exists"`: bool

**異常**: 無

**範例**:
```python
entry = prepare_entry_context()
if entry["exists"]:
    print(f"片頭時長: {entry['duration']}秒")
```

---

## 4. 基礎設施層 (infrastructure/)

### 4.1 infrastructure/video/moviepy_adapter.py

#### MoviePyAdapter.create_color_clip()

```python
def create_color_clip(
    self,
    size: Tuple[int, int],
    color: Tuple[int, int, int],
    duration: float
) -> Any
```

**前置條件**:
- MoviePy 已安裝且可用
- `size` 為正整數 tuple
- `color` 值在 0-255 範圍
- `duration` > 0

**後置條件**:
- 回傳 `moviepy.ColorClip` 實例

**異常**:
- `ImportError`: MoviePy 不可用
- `ValueError`: 參數無效

**範例**:
```python
adapter = MoviePyAdapter()
clip = adapter.create_color_clip((1920, 1080), (255, 255, 255), 5.0)
assert clip.size == (1920, 1080)
assert clip.duration == 5.0
```

---

#### MoviePyAdapter.render_to_file()

```python
def render_to_file(
    self,
    clip: Any,
    output_path: str,
    fps: int = 30,
    codec: str = "libx264"
) -> None
```

**前置條件**:
- `clip` 為有效的 MoviePy Clip
- `output_path` 父目錄存在
- FFmpeg 可用

**後置條件**:
- 產生視頻檔案於 `output_path`
- 檔案可用常見播放器播放

**異常**:
- `RuntimeError`: FFmpeg 失敗
- `IOError`: 無法寫入檔案

**效能預期**:
- 渲染速度約 1-5x real-time (取決於硬體)

**範例**:
```python
adapter.render_to_file(clip, "out/test.mp4", fps=30)
assert os.path.exists("out/test.mp4")
```

---

### 4.2 infrastructure/rendering/pillow_adapter.py

#### PillowAdapter.render_text_image()

```python
def render_text_image(
    self,
    text: str,
    font_path: str,
    font_size: int,
    color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: Optional[Tuple[int, int, int]] = None,
    padding: int = 0,
    fixed_size: Optional[Tuple[int, int]] = None
) -> Image.Image
```

**前置條件**:
- `font_path` 指向存在的字型檔案
- `font_size` > 0
- 顏色值在 0-255 範圍

**後置條件**:
- 回傳 PIL Image
- 若 `bg_color=None`,背景透明(RGBA mode)
- 若 `fixed_size` 指定,圖片尺寸符合

**異常**:
- `FileNotFoundError`: 字型檔案不存在
- `ValueError`: 參數無效

**效能預期**:
- 渲染時間 < 50ms (單次呼叫)

**範例**:
```python
adapter = PillowAdapter()
img = adapter.render_text_image(
    "Hello",
    "C:/Windows/Fonts/arial.ttf",
    48,
    color=(0, 0, 0)
)
assert isinstance(img, Image.Image)
```

---

#### PillowAdapter.measure_text_size()

```python
def measure_text_size(
    self,
    text: str,
    font_path: str,
    font_size: int
) -> Tuple[int, int]
```

**前置條件**:
- `font_path` 指向存在的字型檔案
- `font_size` > 0

**後置條件**:
- 回傳 (width, height) 精確尺寸

**異常**:
- `FileNotFoundError`: 字型檔案不存在

**效能預期**:
- 測量時間 < 10ms

**範例**:
```python
w, h = adapter.measure_text_size("Test", font_path, 48)
assert w > 0 and h > 0
```

---

### 4.3 infrastructure/media/ffmpeg_wrapper.py

#### FFmpegWrapper.probe_duration()

```python
def probe_duration(self, media_path: str) -> float
```

**前置條件**:
- `media_path` 指向存在的媒體檔案
- FFmpeg 或 ffprobe 可用

**後置條件**:
- 回傳媒體時長(秒)

**異常**:
- `FileNotFoundError`: 檔案不存在
- `RuntimeError`: 無法解析時長

**效能預期**:
- 查詢時間 < 500ms

**範例**:
```python
wrapper = FFmpegWrapper()
duration = wrapper.probe_duration("assets/music.mp3")
assert duration > 0
```

---

## 5. CLI 層 (cli/)

### 5.1 cli/commands.py

#### make_command()

```python
def make_command(args: argparse.Namespace) -> int
```

**前置條件**:
- `args` 包含所有必要參數(letters, word_en, word_zh)

**後置條件**:
- 執行單支視頻生成
- 回傳 exit code: 0 成功, 非 0 失敗

**異常**:
- 錯誤訊息輸出到 stderr
- 不拋出未捕獲異常

**範例**:
```bash
python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 --out out/Ice.mp4
# Exit code: 0
```

---

#### batch_command()

```python
def batch_command(args: argparse.Namespace) -> int
```

**前置條件**:
- `args.json` 指向有效的 JSON 配置檔
- `args.outdir` 為有效目錄

**後置條件**:
- 執行批次生成
- 回傳 exit code: 0 全部成功, 非 0 部分/全部失敗

**異常**:
- 錯誤訊息輸出到 stderr

**範例**:
```bash
python -m spellvid.cli batch --json config.json --outdir out/
# Exit code: 0
```

---

## 6. 錯誤處理策略

### 6.1 異常層次

```
Exception
├── SpellVidError (基礎異常類別)
│   ├── ValidationError (驗證失敗)
│   ├── ResourceError (資源問題)
│   │   ├── AssetNotFoundError
│   │   └── FFmpegNotFoundError
│   ├── RenderError (渲染失敗)
│   │   ├── MoviePyError
│   │   └── CodecError
│   └── LayoutError (佈局計算失敗)
```

### 6.2 錯誤處理原則

1. **領域層**: 拋出具體的領域異常(如 `LayoutError`)
2. **應用層**: 捕獲領域異常,轉換為使用者友善訊息
3. **基礎設施層**: 拋出基礎設施異常(如 `FFmpegNotFoundError`)
4. **CLI 層**: 捕獲所有異常,輸出錯誤訊息,回傳 exit code

---

## 7. 效能契約

| 操作 | 預期時間 | 測量方法 |
|------|---------|---------|
| compute_layout_bboxes() | < 50ms | pytest-benchmark |
| zhuyin_for() | < 1ms | 字典查詢 |
| check_assets() | < 100ms | 檔案系統檢查 |
| render_video (dry-run) | < 100ms | 不含實際渲染 |
| render_video (實際) | 1-5x real-time | 取決於硬體 |
| batch 100 videos | ≤ 110% 單獨總和 | CI 效能測試 |

---

## 8. 驗收標準

- [x] 所有公開函數具有完整簽名與 docstring
- [x] 前置條件與後置條件明確定義
- [x] 異常型別與觸發條件文檔化
- [x] 效能預期量化(含測量方法)
- [x] 範例代碼可執行

---

**狀態**: ✅ 功能契約定義完成  
**下一步**: 生成 contracts/test-contracts.md
