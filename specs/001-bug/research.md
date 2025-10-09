# Research: 片尾影片重複播放問題

## 研究目標
1. 分析目前片尾影片添加的邏輯位置
2. 識別導致重複播放的程式碼區段
3. 確定最佳修正方案，確保向後兼容

## 程式碼分析結果

### Decision: 修正位置確定為 `scripts/render_example.py`
**Rationale**: 
- 經分析發現問題在於 `render_example.py` 中的串接邏輯
- 每個單字影片在渲染時都會添加片尾，然後再進行串接
- 正確做法應該是先串接所有單字影片，最後統一添加片尾

**Alternatives considered**:
- 修正 `spellvid/utils.py` 中的渲染邏輯 - 太深層，影響範圍太大
- 修正 `spellvid/cli.py` 中的批次處理 - 不處理實際串接邏輯

### Decision: 使用條件性片尾添加策略
**Rationale**:
- 為 `render_video_stub` 函數添加 `skip_ending` 參數
- 在批次處理時，除最後一個影片外都跳過片尾
- 最後統一添加一次片尾影片

**Alternatives considered**:
- 後處理移除重複片尾 - 複雜且可能影響影片品質
- 完全重構串接邏輯 - 過度工程，風險過高

### Decision: 保持現有測試架構
**Rationale**:
- 利用現有的 `test_ending_video.py` 測試架構
- 擴展測試以涵蓋批次處理場景
- 確保單一影片處理仍然正常

## 技術細節

### 修正策略
1. 在 `spellvid/utils.py` 的 `render_video_stub` 函數添加 `skip_ending` 參數
2. 修正 `scripts/render_example.py` 中的批次處理邏輯
3. 確保最後一個影片或單一影片時仍然添加片尾

### 測試策略
1. 測試單一影片仍有片尾 (回歸測試)
2. 測試批次影片只有最後一個片尾
3. 測試無片尾配置的情況正常運作

## 風險評估
- **低風險**: 修正僅影響片尾添加邏輯，不涉及核心渲染功能
- **向後兼容**: 默認行為保持不變，只在批次處理時調整
- **測試覆蓋**: 現有測試框架可以確保修正正確性