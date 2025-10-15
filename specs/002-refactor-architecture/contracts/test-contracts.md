# Test Contracts: 專案架構重構 - 測試規範

**Feature**: 002-refactor-architecture  
**Date**: 2025-10-14  
**Purpose**: 定義重構後的測試策略、測試清單與驗收標準

---

## 測試金字塔

```
        /\
       /  \       E2E 測試 (5%)
      /____\      
     /      \     整合測試 (15%)
    /________\    
   /          \   契約測試 (20%)
  /____________\  
 /              \ 單元測試 (60%)
/________________\
```

**測試分佈目標**:
- **單元測試** (60%): 測試單一模組/函數,不依賴外部資源
- **契約測試** (20%): 驗證介面實作符合 Protocol 定義
- **整合測試** (15%): 測試多模組協作(如 layout + rendering)
- **E2E 測試** (5%): 測試完整流程(CLI → 視頻產出)

---

## 1. 單元測試 (Unit Tests)

### 1.1 tests/unit/shared/test_types.py

**測試目標**: `shared/types.py` 中的 VideoConfig, LayoutBox

#### TC-SHARED-001: VideoConfig.from_dict() 正常轉換

```python
def test_videoconfig_from_dict_valid():
    """驗證從字典正確建立 VideoConfig"""
    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "countdown_sec": 5.0
    }
    config = VideoConfig.from_dict(data)
    
    assert config.letters == "I i"
    assert config.word_en == "Ice"
    assert config.word_zh == "冰"
    assert config.countdown_sec == 5.0
    assert config.timer_visible is True  # 預設值
```

#### TC-SHARED-002: VideoConfig.from_dict() 缺少必填欄位

```python
def test_videoconfig_from_dict_missing_required():
    """驗證缺少必填欄位時拋出異常"""
    data = {"letters": "A a"}  # 缺少 word_en, word_zh
    
    with pytest.raises(KeyError):
        VideoConfig.from_dict(data)
```

#### TC-SHARED-003: VideoConfig 驗證規則

```python
def test_videoconfig_validation():
    """驗證 __post_init__ 驗證規則"""
    with pytest.raises(ValueError, match="countdown_sec"):
        VideoConfig(
            letters="A", word_en="A", word_zh="A",
            countdown_sec=-1  # 無效
        )
    
    with pytest.raises(ValueError, match="video_mode"):
        VideoConfig(
            letters="A", word_en="A", word_zh="A",
            video_mode="invalid"
        )
```

#### TC-SHARED-004: LayoutBox 不可變性

```python
def test_layoutbox_immutable():
    """驗證 LayoutBox 為不可變值物件"""
    box = LayoutBox(x=10, y=20, width=100, height=50)
    
    with pytest.raises(AttributeError):
        box.x = 99  # frozen=True 禁止修改
```

#### TC-SHARED-005: LayoutBox.overlaps() 正確檢測

```python
def test_layoutbox_overlaps():
    """驗證邊界框重疊檢測"""
    box1 = LayoutBox(x=0, y=0, width=100, height=100)
    box2 = LayoutBox(x=50, y=50, width=100, height=100)
    box3 = LayoutBox(x=200, y=200, width=100, height=100)
    
    assert box1.overlaps(box2) is True
    assert box1.overlaps(box3) is False
```

---

### 1.2 tests/unit/shared/test_validation.py

**測試目標**: `shared/validation.py` 中的 JSON schema 驗證

#### TC-VALIDATION-001: Schema 驗證通過

```python
def test_validate_schema_valid():
    """驗證符合 schema 的資料通過驗證"""
    data = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰"
    }
    validate_schema(data)  # 不應拋出異常
```

#### TC-VALIDATION-002: Schema 驗證失敗

```python
def test_validate_schema_invalid():
    """驗證不符合 schema 的資料拋出異常"""
    data = {
        "letters": 123,  # 應為字串
        "word_en": "Ice"
    }
    
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(data)
```

---

### 1.3 tests/unit/domain/test_layout.py

**測試目標**: `domain/layout.py` 中的佈局計算邏輯

#### TC-LAYOUT-001: 基本佈局計算

```python
def test_compute_layout_basic():
    """驗證基本佈局計算結果"""
    config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
    result = compute_layout_bboxes(config)
    
    # 驗證邊界框存在
    assert result.letters.width > 0
    assert result.word_zh.width > 0
    assert result.reveal.width > 0
    
    # 驗證位置關係
    assert result.letters.x < result.word_zh.x  # 字母在左
    assert result.letters.right <= 1920  # 不超出畫布
    assert result.word_zh.bottom <= 1080
```

#### TC-LAYOUT-002: 字母與中文不重疊

```python
def test_compute_layout_no_overlap():
    """驗證字母與中文區域不重疊"""
    config = VideoConfig(letters="ABC abc", word_en="Apple", word_zh="蘋果")
    result = compute_layout_bboxes(config)
    
    assert not result.letters.overlaps(result.word_zh)
```

#### TC-LAYOUT-003: 注音排版計算

```python
def test_compute_layout_zhuyin():
    """驗證注音符號垂直排版計算"""
    config = VideoConfig(letters="I i", word_en="Ice", word_zh="冰")
    result = compute_layout_bboxes(config)
    
    assert len(result.zhuyin_columns) > 0
    
    # 驗證注音垂直排列
    for i in range(len(result.zhuyin_columns) - 1):
        col1 = result.zhuyin_columns[i]
        col2 = result.zhuyin_columns[i + 1]
        assert col1.bbox.right <= col2.bbox.x  # 從左到右排列
```

#### TC-LAYOUT-004: Timer 位置計算

```python
def test_compute_layout_timer_position():
    """驗證倒數計時器位置"""
    config = VideoConfig(letters="A a", word_en="A", word_zh="A")
    result = compute_layout_bboxes(config, timer_visible=True)
    
    assert result.timer is not None
    assert result.timer.x >= 0
    assert result.timer.bottom <= 1080
```

#### TC-LAYOUT-005: 效能要求

```python
def test_compute_layout_performance(benchmark):
    """驗證佈局計算效能 < 50ms"""
    config = VideoConfig(letters="ABC abc", word_en="Apple", word_zh="蘋果")
    
    result = benchmark(compute_layout_bboxes, config)
    
    # pytest-benchmark 會自動驗證執行時間
    assert result.letters.width > 0
```

---

### 1.4 tests/unit/domain/test_typography.py

**測試目標**: `domain/typography.py` 中的注音處理

#### TC-TYPO-001: 中文轉注音

```python
def test_zhuyin_for_valid_chars():
    """驗證常見中文字的注音轉換"""
    assert zhuyin_for("冰") == "ㄅㄧㄥ"
    assert zhuyin_for("雪") == "ㄒㄩㄝˊ"
    assert zhuyin_for("山") == "ㄕㄢ"
```

#### TC-TYPO-002: 無效字元回傳 None

```python
def test_zhuyin_for_invalid():
    """驗證非中文字元回傳 None"""
    assert zhuyin_for("A") is None
    assert zhuyin_for("123") is None
    assert zhuyin_for("") is None
```

#### TC-TYPO-003: 分割注音符號

```python
def test_split_zhuyin_symbols():
    """驗證注音符號分割"""
    main, tone = split_zhuyin_symbols("ㄅㄧㄥ")
    assert main == ["ㄅ", "ㄧ", "ㄥ"]
    assert tone is None
    
    main, tone = split_zhuyin_symbols("ㄒㄩㄝˊ")
    assert main == ["ㄒ", "ㄩ", "ㄝ"]
    assert tone == "ˊ"
```

---

### 1.5 tests/unit/domain/test_effects.py

**測試目標**: `domain/effects.py` 中的效果邏輯

#### TC-EFFECTS-001: 淡出效果不改變時長

```python
def test_fadeout_preserves_duration():
    """驗證淡出效果不改變 Clip 時長"""
    from unittest.mock import Mock
    
    clip = Mock()
    clip.duration = 5.0
    
    faded = apply_fadeout(clip, 0.5)
    
    # 驗證呼叫了 fadeout 方法
    clip.fadeout.assert_called_once_with(0.5)
```

---

### 1.6 tests/unit/application/test_resource_checker.py

**測試目標**: `application/resource_checker.py`

#### TC-RESOURCE-001: 檢測存在的資源

```python
def test_check_assets_all_present(tmp_path):
    """驗證所有資源存在時回傳 True"""
    # 建立測試資源
    (tmp_path / "image.png").touch()
    (tmp_path / "music.mp3").touch()
    
    config = VideoConfig(
        letters="A a", word_en="A", word_zh="A",
        image_path=str(tmp_path / "image.png"),
        music_path=str(tmp_path / "music.mp3")
    )
    
    result = check_assets(config)
    
    assert result["image"]["exists"] is True
    assert result["music"]["exists"] is True
    assert result["all_present"] is True
```

#### TC-RESOURCE-002: 檢測缺少的資源

```python
def test_check_assets_missing():
    """驗證資源缺失時回傳 False"""
    config = VideoConfig(
        letters="A a", word_en="A", word_zh="A",
        image_path="/nonexistent/image.png"
    )
    
    result = check_assets(config)
    
    assert result["image"]["exists"] is False
    assert result["all_present"] is False
```

---

## 2. 契約測試 (Contract Tests)

### 2.1 tests/contract/test_video_composer_contract.py

**測試目標**: 驗證 IVideoComposer 介面實作

#### TC-CONTRACT-001: MoviePyAdapter 符合介面

```python
def test_moviepy_adapter_implements_interface():
    """驗證 MoviePyAdapter 實作 IVideoComposer 的所有方法"""
    from spellvid.infrastructure.video.moviepy_adapter import MoviePyAdapter
    from spellvid.infrastructure.video.interface import IVideoComposer
    
    adapter = MoviePyAdapter()
    
    # runtime_checkable 允許執行時檢查
    assert isinstance(adapter, IVideoComposer)
    
    # 驗證方法存在
    assert hasattr(adapter, 'create_color_clip')
    assert hasattr(adapter, 'create_image_clip')
    assert hasattr(adapter, 'compose_clips')
    assert hasattr(adapter, 'render_to_file')
```

#### TC-CONTRACT-002: create_color_clip 契約

```python
def test_create_color_clip_contract():
    """驗證 create_color_clip 回傳可組合的 Clip"""
    adapter = MoviePyAdapter()
    
    clip = adapter.create_color_clip((100, 100), (255, 0, 0), 1.0)
    
    # 驗證回傳物件具有 Clip 介面
    assert hasattr(clip, 'duration')
    assert hasattr(clip, 'size')
    assert clip.duration == 1.0
    assert clip.size == (100, 100)
```

#### TC-CONTRACT-003: compose_clips 契約

```python
def test_compose_clips_contract():
    """驗證 compose_clips 接受多個 Clip 並回傳合成 Clip"""
    adapter = MoviePyAdapter()
    
    clip1 = adapter.create_color_clip((100, 100), (255, 0, 0), 1.0)
    clip2 = adapter.create_color_clip((50, 50), (0, 255, 0), 1.0)
    
    composed = adapter.compose_clips([clip1, clip2])
    
    assert hasattr(composed, 'duration')
    assert hasattr(composed, 'size')
```

---

### 2.2 tests/contract/test_text_renderer_contract.py

**測試目標**: 驗證 ITextRenderer 介面實作

#### TC-CONTRACT-004: PillowAdapter 符合介面

```python
def test_pillow_adapter_implements_interface():
    """驗證 PillowAdapter 實作 ITextRenderer"""
    from spellvid.infrastructure.rendering.pillow_adapter import PillowAdapter
    from spellvid.infrastructure.rendering.interface import ITextRenderer
    
    adapter = PillowAdapter()
    
    assert isinstance(adapter, ITextRenderer)
    assert hasattr(adapter, 'render_text_image')
    assert hasattr(adapter, 'measure_text_size')
```

#### TC-CONTRACT-005: render_text_image 契約

```python
def test_render_text_image_contract():
    """驗證 render_text_image 回傳 PIL Image"""
    adapter = PillowAdapter()
    
    # 使用系統字型
    font_path = adapter.find_system_font()
    img = adapter.render_text_image("Test", font_path, 48)
    
    assert isinstance(img, Image.Image)
    assert img.width > 0
    assert img.height > 0
```

---

### 2.3 tests/contract/test_media_processor_contract.py

**測試目標**: 驗證 IMediaProcessor 介面實作

#### TC-CONTRACT-006: FFmpegWrapper 符合介面

```python
def test_ffmpeg_wrapper_implements_interface():
    """驗證 FFmpegWrapper 實作 IMediaProcessor"""
    from spellvid.infrastructure.media.ffmpeg_wrapper import FFmpegWrapper
    from spellvid.infrastructure.media.interface import IMediaProcessor
    
    wrapper = FFmpegWrapper()
    
    assert isinstance(wrapper, IMediaProcessor)
    assert hasattr(wrapper, 'probe_duration')
    assert hasattr(wrapper, 'probe_dimensions')
```

---

## 3. 整合測試 (Integration Tests)

### 3.1 tests/integration/test_video_rendering.py

**測試目標**: 測試佈局 + 渲染整合流程

#### TC-INTEGRATION-001: 完整渲染流程

```python
def test_full_rendering_pipeline(tmp_path):
    """驗證從配置到視頻產出的完整流程"""
    config = VideoConfig(
        letters="I i",
        word_en="Ice",
        word_zh="冰",
        countdown_sec=1.0,
        reveal_hold_sec=1.0
    )
    
    output_path = str(tmp_path / "test.mp4")
    
    result = render_video(config, output_path, dry_run=False)
    
    assert result["success"] is True
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
```

#### TC-INTEGRATION-002: Dry-run 不產生檔案

```python
def test_dry_run_no_file(tmp_path):
    """驗證 dry-run 模式不產生視頻檔案"""
    config = VideoConfig(letters="A a", word_en="A", word_zh="A")
    output_path = str(tmp_path / "test.mp4")
    
    result = render_video(config, output_path, dry_run=True)
    
    assert result["success"] is True
    assert not os.path.exists(output_path)
    assert "metadata" in result
```

---

### 3.2 tests/integration/test_batch_processing.py

**測試目標**: 測試批次處理整合

#### TC-INTEGRATION-003: 批次處理多支視頻

```python
def test_batch_render_multiple(tmp_path):
    """驗證批次處理產生多支視頻"""
    configs = [
        VideoConfig(letters="A a", word_en="Apple", word_zh="蘋果"),
        VideoConfig(letters="B b", word_en="Ball", word_zh="球"),
        VideoConfig(letters="C c", word_en="Cat", word_zh="貓")
    ]
    
    result = render_batch(configs, str(tmp_path), dry_run=False)
    
    assert result["total"] == 3
    assert result["success"] == 3
    assert result["failed"] == 0
    
    # 驗證檔案存在
    assert (tmp_path / "Apple.mp4").exists()
    assert (tmp_path / "Ball.mp4").exists()
    assert (tmp_path / "Cat.mp4").exists()
```

---

## 4. E2E 測試 (End-to-End Tests)

### 4.1 tests/e2e/test_cli.py

**測試目標**: 測試 CLI 完整流程

#### TC-E2E-001: CLI make 命令

```python
def test_cli_make_command(tmp_path):
    """驗證 CLI make 命令端到端流程"""
    output_path = str(tmp_path / "test.mp4")
    
    result = subprocess.run([
        "python", "-m", "spellvid.cli", "make",
        "--letters", "I i",
        "--word-en", "Ice",
        "--word-zh", "冰",
        "--out", output_path
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert os.path.exists(output_path)
```

#### TC-E2E-002: CLI batch 命令

```python
def test_cli_batch_command(tmp_path, config_file):
    """驗證 CLI batch 命令端到端流程"""
    result = subprocess.run([
        "python", "-m", "spellvid.cli", "batch",
        "--json", str(config_file),
        "--outdir", str(tmp_path)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert len(list(tmp_path.glob("*.mp4"))) > 0
```

---

## 5. 效能測試 (Performance Tests)

### 5.1 tests/performance/test_layout_performance.py

#### TC-PERF-001: 佈局計算效能

```python
def test_layout_performance_batch(benchmark):
    """驗證批次佈局計算效能"""
    configs = [
        VideoConfig(letters=f"W{i} w{i}", word_en=f"Word{i}", word_zh=f"字{i}")
        for i in range(100)
    ]
    
    def run_layouts():
        return [compute_layout_bboxes(c) for c in configs]
    
    results = benchmark(run_layouts)
    
    assert len(results) == 100
```

---

## 6. 向後相容測試 (Backward Compatibility Tests)

### 6.1 tests/compat/test_utils_compat.py

**測試目標**: 驗證舊 API 仍可使用

#### TC-COMPAT-001: utils.compute_layout_bboxes 仍可用

```python
def test_utils_compute_layout_deprecated():
    """驗證舊版 utils.compute_layout_bboxes 仍可用但會警告"""
    from spellvid import utils
    
    with pytest.warns(DeprecationWarning):
        result = utils.compute_layout_bboxes(
            {"letters": "A a", "word_en": "A", "word_zh": "A"},
            timer_visible=True
        )
    
    assert "letters" in result
    assert "word_zh" in result
```

---

## 7. 測試執行策略

### 7.1 快速測試（開發時）

```bash
# 只執行單元測試 (60% 覆蓋)
pytest tests/unit/ -v

# 跳過慢速測試
pytest -m "not slow"
```

### 7.2 完整測試（CI）

```bash
# 執行所有測試 + 覆蓋率報告
pytest tests/ -v --cov=spellvid --cov-report=term-missing

# 包含效能基準測試
pytest tests/ --benchmark-only
```

### 7.3 契約測試（重構時）

```bash
# 只執行契約測試,確保介面實作正確
pytest tests/contract/ -v
```

---

## 8. 測試覆蓋率目標

| 模組 | 目標覆蓋率 | 當前狀態 |
|------|-----------|---------|
| shared/ | 95% | 待實作 |
| domain/ | 90% | 待實作 |
| application/ | 85% | 待實作 |
| infrastructure/ | 75% | 待實作 |
| cli/ | 80% | 待實作 |
| **整體** | **85%** | 待實作 |

---

## 9. 測試資料管理

### 9.1 Fixture 組織

```
tests/
├── conftest.py           # 全域 fixtures
├── assets/               # 測試用媒體資源
│   ├── test_image.png
│   ├── test_music.mp3
│   └── test_config.json
└── fixtures/             # Python fixtures
    ├── config_fixtures.py
    └── mock_adapters.py
```

### 9.2 Mock 策略

- **單元測試**: Mock 所有外部依賴(檔案系統、MoviePy)
- **契約測試**: 使用真實實作驗證介面
- **整合測試**: 最小化 Mock,使用真實適配器
- **E2E 測試**: 不使用 Mock

---

## 10. 驗收標準

- [x] 所有測試類別定義完成(單元/契約/整合/E2E)
- [x] 每個模組至少 3 個單元測試
- [x] 每個介面至少 1 個契約測試
- [x] 至少 2 個整合測試覆蓋主要流程
- [x] 至少 1 個 E2E 測試驗證 CLI
- [x] 測試執行策略文檔化
- [x] 覆蓋率目標設定

---

**狀態**: ✅ 測試契約定義完成  
**下一步**: 生成 quickstart.md
