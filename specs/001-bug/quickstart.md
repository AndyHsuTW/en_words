# Quickstart: 片尾影片修正驗證

## 快速驗證修正是否生效

### 前置條件
```powershell
# 確保虛擬環境已啟動
.\.venv\Scripts\Activate.ps1

# 確保測試資產存在
ls assets/ending.mp4  # 應該存在
```

### 驗證步驟

#### 1. 測試單一影片（回歸測試）
```powershell
# 建立單一影片測試配置
echo '[{"word_en":"Test","word_zh":"測試","letters":"T t","image":"assets/cat.png","ending":"assets/ending.mp4"}]' > test_single.json

# 生成單一影片
.\scripts\render_example.ps1 -Json test_single.json -OutFile test_single.mp4

# 驗證結果：應該包含片尾
ffprobe -v error -show_entries stream=duration -of csv=p=0 out/test_single.mp4
# 預期：包含片尾的完整時長
```

#### 2. 測試批次影片（主要修正）
```powershell
# 使用現有的多單字配置
.\scripts\render_example.ps1 -Json config.json -OutFile test_batch.mp4

# 檢查輸出
ls out/test_batch.mp4  # 應該存在

# 手動檢查影片內容（可選）
# 使用 ffplay 或其他播放器確認只有最後出現一次片尾
```

#### 3. 運行自動化測試
```powershell
# 運行相關測試
pytest tests/test_ending_video.py -v
pytest tests/test_batch_concatenation.py -v

# 確保所有測試通過
```

### 預期結果

#### 修正前的問題
- 批次影片會包含多個重複的片尾
- 每個單字結束都會看到片尾內容

#### 修正後的行為  
- ✅ 單一影片仍然包含片尾（兼容性）
- ✅ 批次影片只在最後包含一次片尾
- ✅ 無片尾配置的情況正常運作
- ✅ 所有現有測試仍然通過

### 故障排除

#### 如果單一影片測試失敗
```powershell
# 檢查是否意外移除了片尾功能
grep -n "skip_ending" spellvid/utils.py
# 確保默認值為 False
```

#### 如果批次測試仍有重複片尾
```powershell
# 檢查批次處理邏輯
grep -n "skip_ending" scripts/render_example.py
# 確保除最後一項外都設為 True
```

#### 測試失敗
```powershell
# 運行具體失敗的測試並查看詳細輸出
pytest tests/test_ending_video.py::test_batch_videos_single_ending -v -s
```

### 完成驗證清單
- [ ] 單一影片包含片尾（回歸測試通過）
- [ ] 批次影片只有一個片尾（主要修正驗證）
- [ ] 無片尾配置正常運作（邊界案例）
- [ ] 所有自動化測試通過
- [ ] 手動播放驗證視覺效果正確