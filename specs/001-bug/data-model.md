# Data Model: 片尾影片控制

## 實體模型

### VideoConfig
影片配置實體，擴展以支援片尾控制：

**Fields**:
- `word_en`: 英文單字 (string)
- `word_zh`: 中文/注音 (string) 
- `letters`: 字母序列 (string)
- `image`: 圖片路徑 (string)
- `music`: 音樂路徑 (string, optional)
- `ending`: 片尾影片路徑 (string, optional)
- `skip_ending`: 是否跳過片尾 (boolean, 新增)

**Validation Rules**:
- `skip_ending` 默認為 `False`
- 當 `skip_ending` 為 `True` 時，忽略 `ending` 欄位
- 在批次處理中，除最後一項外，所有項目的 `skip_ending` 應為 `True`

### BatchConfig
批次處理配置：

**Fields**:
- `items`: VideoConfig 陣列
- `output_file`: 最終輸出檔案名稱 (string)
- `global_ending`: 全域片尾影片路徑 (string, optional)

**State Transitions**:
1. 載入配置 → 驗證每個項目
2. 處理批次 → 設定除最後一項外的 `skip_ending=True`
3. 渲染個別影片 → 根據 `skip_ending` 決定是否添加片尾
4. 串接影片 → 如有 `global_ending`，添加至最終影片

## 修正邏輯模型

### EndingVideoHandler
負責片尾影片邏輯的處理器：

**Methods**:
- `should_add_ending(item_index, total_items, skip_ending)`: 判斷是否添加片尾
- `prepare_batch_items(items)`: 準備批次項目，設定 `skip_ending` 標記
- `add_global_ending(video_path, ending_path)`: 添加全域片尾至最終影片

**Logic Rules**:
- 單一影片：總是添加片尾 (如有配置)
- 批次最後一項：添加片尾 (如有配置)
- 批次中間項目：跳過片尾
- 無片尾配置：正常處理，不添加任何片尾