# 影片轉場效果規格 (Video Transition Effects Specification)

**規格編號**：SPEC-TRANSITION-001  
**建立日期**：2025-01-08  
**決策日期**：2025-01-08  
**狀態**：✅ Approved  
**優先度**：Should  
**相關需求**：FR-EXPORT-6 (新增)  
**影響範圍**：批次模式影片合併、單一影片輸出  
**實作範圍**：完整 Phase 1 + Phase 2 + Phase 3（6-8 工作天）  
**決策文件**：video-transition-effects-decisions.md

---

## 📋 決策摘要 (Decision Summary)

**決策日期**：2025-01-08  
**決策者**：Andy Hsu

### 核心決策
- ✅ **D1**: 單一影片模式**也**應用淡出（選項 3 - 一致性優先）
- ✅ **D7**: 直接實作 3 秒淡出（原 1 秒尚未實作，無向後相容問題）
- ✅ **D9**: 完整實作 Phase 1 + 2 + 3（6-8 工作天）

### 技術決策
- ✅ **D2**: 第一個單字影片**不**淡入（開頭影片短，直接開始）
- ✅ **D3**: 使用線性淡出/淡入曲線（MoviePy 預設）
- ✅ **D8**: 結尾影片 (ending.mp4) 不額外淡出

### Phase 3 實作（必要功能）
- ✅ **D4**: 音訊淡入功能（必要，與畫面同步 1 秒淡入）
- ✅ **D5**: 自訂淡出/淡入時長參數（CLI 旗標）
- ⏸️ **D6**: JSON 層級轉場設定（暫不支援）

詳細決策記錄請參考：`.specify/video-transition-effects-decisions.md`

---

## 1. 目的與背景 (Purpose & Background)

### 1.1 目的
為 SpellVid 批次輸出模式增加專業的影片轉場效果，提升連續播放多個單字影片時的視覺流暢度與觀看體驗。

### 1.2 背景與動機
目前批次模式 (`spellvid batch`) 可合併多個單字影片為單一輸出檔案，但各單字影片之間的切換為硬切 (hard cut)，缺乏視覺與聽覺的平滑過渡。透過增加淡出/淡入效果，可以：

- 提升影片專業度與觀看舒適度
- 提供清晰的視覺分段提示
- 減少音訊突兀切換帶來的聽覺不適

### 1.3 使用情境
- **情境 1**：教師製作包含 20 個單字的連續教學影片，希望各單字間有明確的視覺分隔
- **情境 2**：內容創作者輸出長影片到 YouTube，需要專業的過場效果
- **情境 3**：學習者連續觀看多個單字，透過淡出/淡入獲得短暫的視覺休息

---

## 2. 功能需求 (Functional Requirements)

### 2.1 影片結束淡出效果 (Video Fade-Out)

**需求編號**：FR-TRANSITION-001  
**優先度**：Must

#### 行為描述
每個單字影片在結束前的最後 **3 秒**，畫面應進行淡出 (fade to black) 效果。

#### 詳細規格

##### 2.1.1 淡出時間點
- **起始時間**：單字影片結束前 3.0 秒 (T - 3s)
- **結束時間**：單字影片結束時刻 (T)
- **持續時長**：3.0 秒

**計算範例**：
- 若單字影片總長度為 15 秒，淡出應在 12.0 秒處開始，至 15.0 秒結束
- 若單字影片總長度為 10 秒，淡出應在 7.0 秒處開始，至 10.0 秒結束

##### 2.1.2 淡出曲線
- **類型**：線性淡出 (linear fade-out)
- **起始不透明度**：100% (alpha = 1.0)
- **結束不透明度**：0% (alpha = 0.0, 完全黑色)
- **變化函數**：`alpha(t) = 1.0 - (t / 3.0)` 其中 `t` 為從淡出開始經過的時間 (0 ≤ t ≤ 3.0)

**MoviePy 實作參考**：
```python
# 假設 video_clip 為單字影片片段
fade_duration = 3.0
video_with_fadeout = video_clip.fadeout(duration=fade_duration)
```

##### 2.1.3 淡出目標顏色
- **顏色**：純黑色 RGB(0, 0, 0)
- **理由**：黑色為通用的過場顏色，不會與影片內容顏色衝突

##### 2.1.4 淡出應用層級
- **全畫面淡出**：包含所有視覺元素（字母、中文、圖像、計時器、進度條、揭示文字）
- **不受影響的元素**：無（所有畫面內容一併淡出）

#### 2.1.5 特殊情況處理

**情況 A：影片長度 < 3 秒**
- **行為**：不應用淡出效果，或僅在最後 50% 時長內淡出
- **決策**：建議不應用淡出（因為影片過短，淡出會影響主要內容可見性）
- **實作檢查**：
  ```python
  if video_duration >= 3.0:
      video_clip = video_clip.fadeout(duration=3.0)
  ```

**情況 B：單一影片輸出模式 (non-batch)**
- **行為**：單一影片**也**應用淡出效果（選項 3 - 一致性優先）
- **決策理由**：保持所有輸出影片行為一致，實作簡單（詳見 D1 決策記錄）
- **實作**：所有影片統一應用淡出，無需區分批次/單一模式

**情況 C：結尾影片 (ending.mp4) 存在時**
- **行為**：淡出應在主內容結束、切換到結尾影片前發生
- **順序**：主內容 → 淡出 3 秒 → 結尾影片（結尾影片本身不額外淡出）

---

### 2.2 音訊淡出效果 (Audio Fade-Out)

**需求編號**：FR-TRANSITION-002  
**優先度**：Must

#### 行為描述
配合畫面淡出，音訊（包含背景音樂與嗶聲）應在相同時間段內淡出至靜音。

#### 詳細規格

##### 2.2.1 淡出時間點
- **起始時間**：與畫面淡出同步，影片結束前 3.0 秒
- **結束時間**：影片結束時刻
- **持續時長**：3.0 秒

##### 2.2.2 淡出曲線
- **類型**：線性淡出 (linear fade-out)
- **起始音量**：原始音量 (gain = 1.0 或 0 dB)
- **結束音量**：靜音 (gain = 0.0 或 -∞ dB)
- **變化函數**：`gain(t) = 1.0 - (t / 3.0)` 或 `gain_db(t) = 20 * log10(1.0 - t/3.0)`

**MoviePy 實作參考**：
```python
# 假設 audio_clip 為合成後的音訊片段
fade_duration = 3.0
audio_with_fadeout = audio_clip.audio_fadeout(duration=fade_duration)
```

##### 2.2.3 音訊淡出應用範圍
- **背景音樂 (music_path)**：淡出
- **嗶聲提示音 (beep sound)**：若在淡出時段內，也應淡出
- **混音處理**：先完成音訊混音（音樂 + 嗶聲），再對混音結果應用淡出

#### 2.2.4 特殊情況處理

**情況 A：音樂在淡出前已結束**
- **行為**：淡出僅影響尚存的音訊片段（如嗶聲）
- **實作**：淡出應用於最終混音結果，自然處理此情況

**情況 B：無音訊 (music_path 缺失)**
- **行為**：若無音訊，淡出無實際效果（但不應報錯）
- **實作**：安全應用淡出，即使音軌為空

---

### 2.3 下一影片淡入效果 (Video Fade-In)

**需求編號**：FR-TRANSITION-003  
**優先度**：Must

#### 行為描述
當批次模式合併多個單字影片時，下一個單字影片應在開始後的前 **1 秒**進行淡入 (fade from black) 效果。

#### 詳細規格

##### 2.3.1 淡入時間點
- **起始時間**：下一個單字影片開始時刻 (T_next)
- **結束時間**：下一個單字影片開始後 1.0 秒 (T_next + 1s)
- **持續時長**：1.0 秒

##### 2.3.2 淡入曲線
- **類型**：線性淡入 (linear fade-in)
- **起始不透明度**：0% (alpha = 0.0, 純黑色)
- **結束不透明度**：100% (alpha = 1.0)
- **變化函數**：`alpha(t) = t / 1.0` 其中 `t` 為淡入開始後經過的時間 (0 ≤ t ≤ 1.0)

**MoviePy 實作參考**：
```python
# 假設 next_video_clip 為下一個單字影片片段
fade_duration = 1.0
video_with_fadein = next_video_clip.fadein(duration=fade_duration)
```

##### 2.3.3 淡入起始顏色
- **顏色**：純黑色 RGB(0, 0, 0)
- **與淡出一致**：確保視覺連續性（淡出到黑 → 從黑淡入）

##### 2.3.4 淡入應用層級
- **全畫面淡入**：包含所有視覺元素（字母、中文、圖像等）
- **開頭影片 (entry.mp4)**：
  - **第一個單字影片**：若有 entry.mp4，entry 本身不應用淡入（直接開始），但主內容應淡入
  - **後續單字影片**：無 entry.mp4，直接從黑色淡入

#### 2.3.5 特殊情況處理

**情況 A：影片長度 < 1 秒**
- **行為**：不應用淡入效果（理論上不應出現如此短的影片）
- **實作檢查**：
  ```python
  if video_duration >= 1.0:
      video_clip = video_clip.fadein(duration=1.0)
  ```

**情況 B：第一個單字影片**
- **行為**：第一個單字影片**不**淡入（選項 A2）
- **決策理由**：
  - 開頭影片 (entry.mp4) 很短，不適合套用一致的轉場效果
  - 第一個單字影片應直接開始，避免額外的黑色延遲
- **實作**：第一個影片不應用 `fadein()`，第二個及後續影片應用 `fadein(1.0)`

---

### 2.4 下一影片音訊恢復 (Audio Resume)

**需求編號**：FR-TRANSITION-004  
**優先度**：Must

#### 行為描述
下一個單字影片的音訊應 **立即恢復至原始音量**，不進行淡入效果。

#### 詳細規格

##### 2.4.1 音訊行為
- **音量起始**：下一個單字影片開始時，音訊以原始音量播放
- **無淡入**：不對音訊應用淡入效果
- **理由**：畫面淡入已提供視覺過渡提示，音訊直接恢復有助於維持節奏與節省時間

**MoviePy 實作參考**：
```python
# 下一個影片的音訊不應用淡入
next_audio_clip = next_video_clip.audio  # 保持原始音量，無需 audio_fadein
```

##### 2.4.2 音訊同步
- **畫面與音訊時間軸對齊**：確保音訊與畫面同步啟動
- **無靜音間隔**：前一影片淡出結束到下一影片淡入開始之間，應無額外靜音段

#### 2.4.3 特殊情況處理

**情況 A：音訊淡入需求**
- **行為**：Phase 3 **實作音訊淡入功能**
- **決策結果**：音訊也應與畫面同步淡入 1 秒（詳見 D4 決策記錄）
- **理由**：音訊直接恢復可能過於突兀，尤其是有強烈鼓點的音樂
- **實作**：Phase 3 增加 `audio_fadein(1.0)`，可選提供 `--no-audio-fadein` 停用

---

## 3. 非功能性需求 (Non-Functional Requirements)

### 3.1 效能需求

#### 3.1.1 渲染時間影響
- **淡出/淡入處理**：不應顯著增加渲染時間（預期增加 < 5%）
- **MoviePy 效能**：fade 效果為 MoviePy 內建功能，效能可接受

#### 3.1.2 記憶體使用
- **限制**：處理大量影片時，應逐段處理而非一次載入所有片段至記憶體
- **實作建議**：使用 MoviePy 的串流處理機制

### 3.2 相容性需求

#### 3.2.1 現有功能相容
- **淡出與片尾淡出 (FR-EXPORT-3) 的關係**：
  - 現有規格 FR-EXPORT-3 要求「影片末端加入 1 秒淡出」
  - 新規格 FR-TRANSITION-001 要求「最後 3 秒淡出」
  - **✅ 決策結果**：新規格取代舊規格，統一為 3 秒淡出（非破壞性變更）
  - **理由**：原本的 1 秒淡出尚未實作，可以忽略
  - **影響**：無現有使用者依賴舊行為，無向後相容問題
  - **溝通**：無需 CHANGELOG Breaking Change 標註（詳見 D7 決策記錄）

#### 3.2.2 輸出格式相容
- **編碼格式**：H.264 + AAC (與現有規格一致)
- **畫質影響**：淡出/淡入不應影響影片畫質或檔案大小（在合理範圍內）

### 3.3 可測試性需求

#### 3.3.1 視覺驗證
- **測試方式**：使用 OpenCV 或 ffprobe 取樣關鍵幀，驗證亮度變化
- **關鍵檢查點**：
  - 淡出開始前：正常亮度
  - 淡出中點 (T - 1.5s)：約 50% 亮度
  - 淡出結束 (T)：接近 0 亮度 (黑色)
  - 淡入開始：接近 0 亮度 (黑色)
  - 淡入中點 (T + 0.5s)：約 50% 亮度
  - 淡入結束 (T + 1s)：正常亮度

#### 3.3.2 音訊驗證
- **測試方式**：使用 pydub 或 ffprobe 分析音訊波形
- **關鍵檢查點**：
  - 淡出開始前：正常音量
  - 淡出中點：約 -6 dB (50% 線性)
  - 淡出結束：接近 -∞ dB (靜音)
  - 下一影片開始：立即恢復原始音量

### 3.4 使用者體驗需求

#### 3.4.1 視覺流暢度
- **幀率一致**：淡出/淡入期間維持 30 fps
- **無閃爍**：過渡應平滑，無明顯跳幀或閃爍

#### 3.4.2 可配置性
- **未來考慮**：提供 CLI 參數自訂淡出/淡入時長
- **預設值**：淡出 3 秒、淡入 1 秒（當前規格）

---

## 4. 技術實作指引 (Technical Implementation Guide)

### 4.1 MoviePy 實作範例

#### 4.1.1 單一影片淡出
```python
from moviepy.editor import VideoFileClip

def apply_transition_fadeout(video_clip, fadeout_duration=3.0):
    """為影片片段應用結尾淡出效果。
    
    Args:
        video_clip: MoviePy VideoClip 物件
        fadeout_duration: 淡出持續時間（秒）
    
    Returns:
        應用淡出後的 VideoClip 物件
    """
    if video_clip.duration < fadeout_duration:
        # 影片過短，不應用淡出
        return video_clip
    
    # 對影片應用淡出
    video_with_fadeout = video_clip.fadeout(duration=fadeout_duration)
    
    # 對音訊應用淡出（如果存在）
    if video_clip.audio is not None:
        video_with_fadeout = video_with_fadeout.audio_fadeout(duration=fadeout_duration)
    
    return video_with_fadeout
```

#### 4.1.2 批次模式影片串接
```python
from moviepy.editor import concatenate_videoclips

def concatenate_with_transitions(video_clips):
    """連接多個影片片段，並應用轉場效果。
    
    Args:
        video_clips: MoviePy VideoClip 物件列表
    
    Returns:
        合併後的 VideoClip 物件
    """
    processed_clips = []
    
    for idx, clip in enumerate(video_clips):
        # 為每個片段應用淡出（最後 3 秒）
        clip_with_fadeout = apply_transition_fadeout(clip, fadeout_duration=3.0)
        
        # 為第二個及後續片段應用淡入（前 1 秒）
        if idx > 0:
            if clip_with_fadeout.duration >= 1.0:
                clip_with_fadeout = clip_with_fadeout.fadein(duration=1.0)
        
        processed_clips.append(clip_with_fadeout)
    
    # 連接所有片段
    final_clip = concatenate_videoclips(processed_clips, method='compose')
    
    return final_clip
```

### 4.2 整合至現有程式碼

#### 4.2.1 修改位置
- **檔案**：`spellvid/utils.py`
- **函式**：`render_video_stub()` 或相關的批次處理函式
- **修改點**：在最終輸出前應用淡出效果

#### 4.2.2 實作步驟
1. 在 `render_video_stub()` 中，於影片合成完成後、輸出前應用淡出
2. 在批次模式 (`cli.batch()`) 中，收集各單字影片片段時應用淡入（除第一個外）
3. 使用 `concatenate_videoclips()` 連接所有片段
4. 確保音訊與畫面淡出/淡入同步

#### 4.2.3 配置參數
建議在 JSON schema 或 CLI 參數中增加可選配置：
```python
# CLI 參數範例
p_batch.add_argument(
    "--fade-out-duration",
    type=float,
    default=3.0,
    help="單字影片結尾淡出時長（秒），預設 3.0"
)
p_batch.add_argument(
    "--fade-in-duration",
    type=float,
    default=1.0,
    help="下一影片開始淡入時長（秒），預設 1.0"
)
p_batch.add_argument(
    "--disable-transitions",
    action="store_true",
    help="停用轉場效果（硬切）"
)
```

### 4.3 邊界情況處理清單

| 情況 | 行為 | 實作檢查 |
|------|------|----------|
| 影片 < 3 秒 | 不應用淡出 | `if duration >= 3.0: ...` |
| 影片 < 1 秒 | 不應用淡入 | `if duration >= 1.0: ...` |
| 單一影片輸出 | 可選淡出（預設不淡出） | 檢查 batch mode 旗標 |
| 無音訊 | 淡出不報錯 | `if clip.audio is not None: ...` |
| 第一個影片 | 可選淡入（預設淡入） | `if idx == 0: ...` |

---

## 5. 測試計畫 (Testing Plan)

### 5.1 單元測試

#### 5.1.1 淡出效果測試
**測試 ID**：TCS-TRANSITION-001  
**測試類型**：Unit  
**測試目標**：驗證單一影片淡出效果正確應用

**測試步驟**：
1. 建立 10 秒測試影片（純白色背景）
2. 應用 3 秒淡出效果
3. 取樣關鍵幀：
   - 6.0 秒處：亮度應為 255 (100%)
   - 8.5 秒處：亮度應約為 128 (50%)
   - 9.9 秒處：亮度應接近 0 (0%)

**驗收標準**：
- 亮度值誤差 < 10%
- 無幀跳躍或閃爍

#### 5.1.2 淡入效果測試
**測試 ID**：TCS-TRANSITION-002  
**測試類型**：Unit  
**測試目標**：驗證影片淡入效果正確應用

**測試步驟**：
1. 建立 10 秒測試影片（純白色背景）
2. 應用 1 秒淡入效果
3. 取樣關鍵幀：
   - 0.0 秒處：亮度應接近 0 (0%)
   - 0.5 秒處：亮度應約為 128 (50%)
   - 1.0 秒處：亮度應為 255 (100%)

**驗收標準**：
- 亮度值誤差 < 10%
- 淡入曲線平滑

#### 5.1.3 音訊淡出測試
**測試 ID**：TCS-TRANSITION-003  
**測試類型**：Unit  
**測試目標**：驗證音訊淡出效果正確應用

**測試步驟**：
1. 建立 10 秒測試影片，包含恆定音量音訊（-10 dBFS）
2. 應用 3 秒音訊淡出
3. 取樣音訊片段：
   - 6.0 秒處：音量應為 -10 dBFS
   - 8.5 秒處：音量應約為 -16 dBFS (50% 線性)
   - 9.9 秒處：音量應接近 -∞ dBFS

**驗收標準**：
- 音量變化符合線性淡出曲線（±2 dB）
- 無爆音或削波

### 5.2 整合測試

#### 5.2.1 批次轉場測試
**測試 ID**：TCS-TRANSITION-004  
**測試類型**：Integration  
**測試目標**：驗證批次模式下多個影片的轉場效果

**測試步驟**：
1. 建立 3 個測試影片（各 10 秒）：
   - 影片 A：紅色背景
   - 影片 B：綠色背景
   - 影片 C：藍色背景
2. 使用批次模式合併，應用轉場效果
3. 驗證輸出影片：
   - 總長度約為 30 秒（3 × 10s）
   - 影片 A 結尾 3 秒淡出（7.0-10.0s）
   - 影片 B 開始 1 秒淡入（10.0-11.0s）
   - 影片 B 結尾 3 秒淡出（17.0-20.0s）
   - 影片 C 開始 1 秒淡入（20.0-21.0s）
   - 影片 C 結尾 3 秒淡出（27.0-30.0s）

**驗收標準**：
- 時間軸對齊正確
- 顏色過渡平滑（紅→黑→綠→黑→藍→黑）
- 音訊連續無斷層

#### 5.2.2 特殊情況測試
**測試 ID**：TCS-TRANSITION-005  
**測試類型**：Integration  
**測試目標**：驗證邊界情況處理

**測試案例**：
1. **短影片 (2 秒)**：應不應用淡出，正常輸出
2. **無音訊影片**：淡出不應報錯
3. **單一影片模式**：應不應用淡出（或依旗標決定）
4. **第一個影片**：應淡入（或依規格決定）

**驗收標準**：
- 無例外拋出
- 行為符合規格定義

### 5.3 端對端測試

#### 5.3.1 CLI 批次轉場測試
**測試 ID**：TCS-TRANSITION-006  
**測試類型**：E2E  
**測試目標**：驗證完整的批次流程與轉場效果

**測試步驟**：
```powershell
# 建立測試 JSON
$config = @"
[
  {
    "letters": "A",
    "word_en": "Apple",
    "word_zh": "蘋果",
    "image_path": "assets/apple.png",
    "music_path": "assets/apple.mp3",
    "countdown_sec": 10,
    "reveal_hold_sec": 3
  },
  {
    "letters": "B",
    "word_en": "Ball",
    "word_zh": "球",
    "image_path": "assets/ball.png",
    "music_path": "assets/ball.mp3",
    "countdown_sec": 10,
    "reveal_hold_sec": 3
  }
]
"@
$config | Out-File -Encoding UTF8 test_config.json

# 執行批次渲染
python -m spellvid.cli batch --json test_config.json --outdir out --out-file merged.mp4

# 驗證輸出
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 out/merged.mp4
```

**驗收標準**：
- 成功輸出合併檔案 `merged.mp4`
- 檔案可播放，轉場效果正確
- 音訊連續且淡出正確

---

## 6. CLI 參數設計 (CLI Parameters)

### 6.1 新增參數

#### 6.1.1 淡出時長
```
--fade-out-duration <seconds>
```
- **說明**：設定單字影片結尾淡出持續時間（秒）
- **預設值**：3.0
- **範圍**：0.0 - 10.0（0 表示停用淡出）
- **範例**：`--fade-out-duration 2.5`

#### 6.1.2 淡入時長
```
--fade-in-duration <seconds>
```
- **說明**：設定下一影片開始淡入持續時間（秒）
- **預設值**：1.0
- **範圍**：0.0 - 5.0（0 表示停用淡入）
- **範例**：`--fade-in-duration 1.5`

#### 6.1.3 停用轉場
```
--disable-transitions
```
- **說明**：停用所有轉場效果（硬切模式）
- **預設值**：False（啟用轉場）
- **範例**：`--disable-transitions`

#### 6.1.4 音訊淡入（未來擴充）
```
--audio-fadein
```
- **說明**：為下一影片音訊也應用淡入效果
- **預設值**：False（音訊直接恢復）
- **範例**：`--audio-fadein`

### 6.2 使用範例

#### 範例 1：使用預設轉場設定
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file merged.mp4
```
- 淡出 3 秒、淡入 1 秒、音訊直接恢復

#### 範例 2：自訂轉場時長
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file merged.mp4 --fade-out-duration 2.0 --fade-in-duration 0.5
```
- 淡出 2 秒、淡入 0.5 秒

#### 範例 3：停用轉場
```powershell
python -m spellvid.cli batch --json config.json --outdir out --out-file merged.mp4 --disable-transitions
```
- 無淡出/淡入，硬切模式

---

## 7. JSON Schema 擴充 (Optional)

### 7.1 單字項目層級設定
可考慮在 JSON 中為每個單字項目增加轉場設定（優先度較低）：

```json
{
  "letters": "A",
  "word_en": "Apple",
  "word_zh": "蘋果",
  "image_path": "assets/apple.png",
  "music_path": "assets/apple.mp3",
  "countdown_sec": 10,
  "reveal_hold_sec": 3,
  "transition": {
    "fade_out_duration": 3.0,
    "fade_in_duration": 1.0,
    "disable": false
  }
}
```

**優缺點**：
- **優點**：每個單字可自訂轉場效果
- **缺點**：增加設定複雜度，大多數情況用不到

**建議**：暫不實作，除非有明確需求

---

## 8. 相關需求更新 (Related Requirements Update)

### 8.1 需更新的現有需求

#### FR-EXPORT-3 (原規格)
- **原內容**：「本系統應於影片末端加入 **1 秒** 淡出。」
- **新內容**：「本系統應於影片末端加入 **3 秒** 淡出（配合轉場效果）。」
- **狀態**：需更新 `doc/requirement.md`

#### FR-EXPORT-6 (新增規格)
- **內容**：「本系統應於批次模式合併影片時，為各單字影片應用轉場效果：結尾 3 秒淡出（畫面與音訊）、下一影片 1 秒淡入（僅畫面）。」
- **優先度**：Should
- **狀態**：需新增至 `doc/requirement.md`

### 8.2 需新增的測試案例

需在 `doc/TDD.md` 中新增以下測試案例：

| ID | 類型 | 對應需求 | 前置/步驟 | 驗證點 |
|----|------|----------|----------|--------|
| TCS-TRANSITION-001 | Unit | FR-EXPORT-6 | 單一影片應用 3 秒淡出 | 關鍵幀亮度值符合淡出曲線 |
| TCS-TRANSITION-002 | Unit | FR-EXPORT-6 | 單一影片應用 1 秒淡入 | 關鍵幀亮度值符合淡入曲線 |
| TCS-TRANSITION-003 | Unit | FR-EXPORT-6 | 音訊 3 秒淡出 | 音量變化符合淡出曲線 |
| TCS-TRANSITION-004 | Integration | FR-EXPORT-6 | 批次模式 3 個影片轉場 | 時間軸對齊、顏色過渡平滑 |
| TCS-TRANSITION-005 | Integration | FR-EXPORT-6 | 邊界情況（短影片、無音訊） | 無例外、行為符合規格 |
| TCS-TRANSITION-006 | E2E | FR-EXPORT-6 | CLI 批次轉場完整流程 | 輸出正確、轉場效果正常 |

---

## 9. 實作優先順序與時程 (Implementation Priority)

### 9.1 Phase 1：核心功能（高優先度）
- [x] 決策：Phase 1 必須實作（D9）
- [ ] 實作單一影片與批次模式淡出效果（畫面 + 音訊，固定 3 秒）
- [ ] 實作批次模式影片淡入效果（第二個及後續影片，固定 1 秒）
- [ ] 基本單元測試

**預估時間**：2-3 工作天

### 9.2 Phase 2：整合與測試（中優先度）
- [x] 決策：Phase 2 必須實作（D9）
- [ ] 整合至現有 batch 流程
- [ ] 整合測試（多影片轉場）
- [ ] E2E 測試
- [ ] 更新文件（requirement.md, TDD.md）

**預估時間**：2 工作天

### 9.3 Phase 3：進階功能（高優先度 - 必要功能）✨
- [x] 決策：Phase 3 完整實作（D9 選項 2）
- [ ] **音訊淡入功能**（必要，D4 決策）
  - 下一影片音訊應用 `audio_fadein(1.0)` 與畫面同步
  - 可選：提供 `--no-audio-fadein` 旗標停用
- [ ] CLI 自訂淡出/淡入時長參數（D5 決策）
  - `--fade-out-duration <seconds>`
  - `--fade-in-duration <seconds>`
- [ ] JSON 單字層級轉場設定：暫不實作（D6 決策）

**預估時間**：2-3 工作天

**決策理由**（D9 - 選項 2）：
- 音訊淡入被規劃在 Phase 3，但這是必要的功能（D4）
- 自訂時長參數對使用者有實際價值（D5）
- 一次性完成所有功能，避免後續迭代

**總時程**：6-8 工作天（完整實作 Phase 1+2+3）

---

## 10. 風險與限制 (Risks & Limitations)

### 10.1 已知限制

#### 10.1.1 效能影響
- **影響**：淡出/淡入處理會增加渲染時間（預估 < 5%）
- **緩解**：MoviePy 內建函式效能可接受，影響可控

#### 10.1.2 記憶體使用
- **影響**：處理大量長影片時記憶體使用可能增加
- **緩解**：使用串流處理，逐段輸出而非全部載入記憶體

#### 10.1.3 向後相容
- **影響**：修改淡出時長從 1 秒到 3 秒會改變現有行為
- **緩解**：提供 `--fade-out-duration` 參數讓使用者自訂（未來）

### 10.2 潛在風險

#### 10.2.1 MoviePy API 變更
- **風險**：MoviePy 版本更新可能改變 fade 函式行為
- **緩解**：鎖定 MoviePy 版本於 `requirements-dev.txt`

#### 10.2.2 音訊同步問題
- **風險**：複雜場景下音訊與畫面可能不同步
- **緩解**：詳細測試音訊同步，必要時調整實作

#### 10.2.3 使用者混淆
- **風險**：使用者可能不清楚轉場效果何時應用（batch vs single）
- **緩解**：在文件與 `--help` 中清楚說明

---

## 11. 驗收標準總結 (Acceptance Criteria Summary)

### 11.1 功能驗收
- [ ] 單字影片結尾前 3 秒進行畫面淡出（線性，淡至黑色）
- [ ] 單字影片結尾前 3 秒進行音訊淡出（線性，淡至靜音）
- [ ] 下一影片開始後 1 秒進行畫面淡入（線性，從黑色淡入）
- [ ] 下一影片音訊立即恢復原始音量（無淡入）
- [ ] 淡出/淡入時間軸對齊正確
- [ ] 批次模式正確連接多個影片，轉場平滑

### 11.2 非功能驗收
- [ ] 渲染時間增加 < 5%
- [ ] 無記憶體洩漏或異常增長
- [ ] 視覺無閃爍或跳幀
- [ ] 音訊無爆音或斷層
- [ ] 輸出影片可正常播放（H.264 + AAC）

### 11.3 測試驗收
- [ ] 所有單元測試通過（TCS-TRANSITION-001 ~ 003）
- [ ] 所有整合測試通過（TCS-TRANSITION-004 ~ 005）
- [ ] E2E 測試通過（TCS-TRANSITION-006）
- [ ] 邊界情況測試通過（短影片、無音訊等）

### 11.4 文件驗收
- [ ] 更新 `doc/requirement.md`（FR-EXPORT-3, FR-EXPORT-6）
- [ ] 更新 `doc/TDD.md`（新增測試案例）
- [ ] 更新 `README.md`（使用範例，如適用）
- [ ] 更新 `CONSTITUTION.md`（若影響開發規範）

---

## 12. 參考資料 (References)

### 12.1 技術參考
- [MoviePy Documentation - Video Effects](http://zulko.github.io/moviepy/ref/videofx.html)
- [MoviePy fadein/fadeout API](http://zulko.github.io/moviepy/ref/VideoClip/VideoClip.html#moviepy.video.VideoClip.VideoClip.fadein)
- [FFmpeg fade filter](https://ffmpeg.org/ffmpeg-filters.html#fade)

### 12.2 相關規格文件
- `doc/requirement.md` - SpellVid 需求規格
- `doc/TDD.md` - 測試驅動開發計畫
- `CONSTITUTION.md` - 專案憲法

### 12.3 相關 Issue / PR
- (待建立) Issue: 增加批次模式轉場效果
- (待建立) PR: 實作影片淡出/淡入轉場

---

## 13. 變更歷史 (Change History)

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| v0.1 | 2025-01-08 | 初版草案建立 | GitHub Copilot |

---

## 14. 批准與簽核 (Approval)

| 角色 | 姓名 | 簽核日期 | 備註 |
|------|------|----------|------|
| 產品負責人 | TBD | - | 待簽核 |
| 技術負責人 | TBD | - | 待簽核 |
| QA 負責人 | TBD | - | 待簽核 |

---

**規格文件結束 (End of Specification)**

**下一步行動 (Next Actions)**：
1. 產品負責人審查並批准規格
2. 技術團隊評估實作可行性與時程
3. 建立對應的 Issue 與 PR
4. 開始 Phase 1 實作（核心功能）
