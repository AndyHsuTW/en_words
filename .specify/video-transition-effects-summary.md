# 影片轉場效果規格 - 快速摘要

**規格編號**：SPEC-TRANSITION-001  
**建立日期**：2025-01-08  
**詳細規格**：見 `video-transition-effects.md`

---

## 📋 核心需求一覽

### 影片結尾轉場（每個單字影片）
- ✅ **淡出時機**：結束前 **3 秒** 開始
- ✅ **畫面淡出**：線性淡至黑色 (RGB 0,0,0)
- ✅ **音訊淡出**：線性淡至靜音（同步 3 秒）

### 下一影片開場轉場
- ✅ **淡入時機**：影片開始後 **1 秒** 內
- ✅ **畫面淡入**：從黑色線性淡入
- ✅ **音訊行為**：**立即恢復原始音量**（無淡入）

---

## 🎯 快速理解圖示

```
影片 A (15秒)                      影片 B (15秒)
├─────────────┤                   ├─────────────┤
│  正常播放   │ 淡出3s │           │淡入1s│  正常播放   │
│             │█████░░│ → 黑色 → │░░░███│             │
0s          12s    15s           15s 16s  17s       30s
              ↓                         ↓
         畫面+音訊淡出              畫面淡入，音訊直接恢復
```

---

## 🛠️ 實作要點

### MoviePy 核心程式碼
```python
# 淡出效果（每個影片片段）
if clip.duration >= 3.0:
    clip = clip.fadeout(duration=3.0)  # 畫面淡出
    if clip.audio:
        clip = clip.audio_fadeout(duration=3.0)  # 音訊淡出

# 淡入效果（第二個及後續影片）
if idx > 0 and clip.duration >= 1.0:
    clip = clip.fadein(duration=1.0)  # 僅畫面淡入
```

### CLI 使用範例
```powershell
# 預設轉場（淡出3s + 淡入1s）
python -m spellvid.cli batch --json config.json --outdir out --out-file merged.mp4

# 自訂轉場時長（未來擴充）
python -m spellvid.cli batch --json config.json --out-file merged.mp4 \
  --fade-out-duration 2.0 --fade-in-duration 0.5

# 停用轉場（硬切模式）
python -m spellvid.cli batch --json config.json --out-file merged.mp4 \
  --disable-transitions
```

---

## ✅ 驗收檢查清單

### 功能驗收
- [ ] 影片結尾前 3 秒進行畫面淡出（線性到黑色）
- [ ] 影片結尾前 3 秒進行音訊淡出（線性到靜音）
- [ ] 下一影片開始 1 秒進行畫面淡入（從黑色）
- [ ] 下一影片音訊立即恢復（無淡入）
- [ ] 批次模式正確連接多個影片

### 技術驗收
- [ ] 淡出/淡入時間軸對齊正確
- [ ] 無閃爍、跳幀或音訊斷層
- [ ] 渲染時間增加 < 5%
- [ ] 輸出格式 H.264 + AAC 正常

### 測試驗收
- [ ] 單元測試：淡出效果（TCS-TRANSITION-001）
- [ ] 單元測試：淡入效果（TCS-TRANSITION-002）
- [ ] 單元測試：音訊淡出（TCS-TRANSITION-003）
- [ ] 整合測試：批次轉場（TCS-TRANSITION-004）
- [ ] 邊界測試：短影片、無音訊（TCS-TRANSITION-005）
- [ ] E2E 測試：完整 CLI 流程（TCS-TRANSITION-006）

---

## 📝 需更新的文件

1. **doc/requirement.md**
   - 更新 FR-EXPORT-3：淡出時長從 1 秒改為 3 秒
   - 新增 FR-EXPORT-6：批次轉場效果規格

2. **doc/TDD.md**
   - 新增 TCS-TRANSITION-001 ~ 006 測試案例

3. **README.md**（可選）
   - 增加批次轉場使用範例

---

## ⚠️ 注意事項

### 邊界情況
1. **短影片（< 3 秒）**：不應用淡出
2. **無音訊**：淡出不應報錯
3. **單一影片模式**：建議不應用轉場（或提供旗標）
4. **第一個影片**：建議應用淡入（提供開場效果）

### 向後相容
- 修改 FR-EXPORT-3 淡出時長（1s → 3s）會改變現有行為
- 建議提供 CLI 參數讓使用者自訂

---

## 🚀 實作階段

### Phase 1：核心功能（2-3 天）
- 實作淡出效果（畫面 + 音訊）
- 實作淡入效果（僅畫面）
- 基本單元測試

### Phase 2：整合與測試（2 天）
- 整合至 batch 流程
- 整合測試與 E2E 測試
- 更新文件

### Phase 3：進階功能（1-2 天，可選）
- CLI 自訂參數
- JSON 層級設定
- 音訊淡入（可選）

---

## 📚 相關文件

- **詳細規格**：`.specify/video-transition-effects.md`
- **需求文件**：`doc/requirement.md`
- **測試計畫**：`doc/TDD.md`
- **專案憲法**：`CONSTITUTION.md`

---

**問題或建議？**  
請參考詳細規格文件或聯繫專案維護者。
