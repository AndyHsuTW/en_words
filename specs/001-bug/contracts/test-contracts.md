# Test Contracts: 片尾影片修正

## 測試場景合約

### test_single_video_with_ending
**目的**: 確保單一影片處理仍然包含片尾（回歸測試）

**Given**: 
- JSON 配置包含 1 個單字
- 配置中指定 `ending` 路徑

**When**: 執行 `render_example.ps1 -OutFile single.mp4`

**Then**:
- 輸出影片包含片尾內容
- `ending_count` 等於 1

### test_batch_videos_single_ending
**目的**: 驗證批次處理只有一個片尾

**Given**:
- JSON 配置包含 3 個單字
- 每個配置都指定相同的 `ending` 路徑

**When**: 執行 `render_example.ps1 -OutFile batch.mp4`

**Then**:
- 輸出影片只在最後包含一次片尾
- `ending_count` 等於 1
- 中間轉換沒有片尾內容

### test_batch_videos_no_ending
**目的**: 驗證無片尾配置的批次處理正常

**Given**:
- JSON 配置包含 3 個單字
- 配置中未指定 `ending` 路徑

**When**: 執行 `render_example.ps1 -OutFile no_ending.mp4`

**Then**:
- 輸出影片不包含任何片尾
- `ending_count` 等於 0
- 影片正常串接

### test_render_video_stub_skip_ending
**目的**: 測試 `skip_ending` 參數功能

**Given**: 
- 單字配置包含 `ending` 路徑
- `skip_ending=True`

**When**: 呼叫 `render_video_stub(item, output, skip_ending=True)`

**Then**:
- 輸出影片不包含片尾
- `has_ending` 回傳 `False`

### test_render_video_stub_include_ending
**目的**: 測試預設行為保持不變

**Given**:
- 單字配置包含 `ending` 路徑  
- `skip_ending=False` (默認)

**When**: 呼叫 `render_video_stub(item, output)`

**Then**:
- 輸出影片包含片尾
- `has_ending` 回傳 `True`

## 測試資料合約

### 測試配置檔案
```json
{
  "single_with_ending": [
    {
      "word_en": "Test",
      "word_zh": "測試",
      "letters": "T t",
      "image": "assets/test.png",
      "ending": "assets/ending.mp4"
    }
  ],
  "batch_with_ending": [
    {
      "word_en": "Cat", 
      "word_zh": "貓",
      "letters": "C c",
      "image": "assets/cat.png",
      "ending": "assets/ending.mp4"
    },
    {
      "word_en": "Dog",
      "word_zh": "狗", 
      "letters": "D d",
      "image": "assets/dog.png",
      "ending": "assets/ending.mp4"
    }
  ]
}
```