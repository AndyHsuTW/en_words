# Phase 3.5 遷移執行計劃

## 目標
將 37 個函數從 utils.py 遷移至新模組,實現完全移除舊程式碼

## 執行策略
分 3 批次執行,每批次後驗證測試

---

## 批次 1: Domain Layer (13 個函數) - 預估 4h

### domain/layout.py (5 個函數)
- [ ] `_normalize_letters_sequence` (4 calls, low)
- [ ] `_plan_letter_images` (5 calls, medium)
- [ ] `_letter_asset_filename` (4 calls, low)
- [ ] `_letters_missing_names` (4 calls, low)
- [ ] `_layout_zhuyin_column` (4 calls, low)

### domain/effects.py (6 個函數)
- [ ] `_progress_bar_band_layout` (6 calls, medium)
- [ ] `_progress_bar_base_arrays` (4 calls, low)
- [ ] `_make_progress_bar_mask` (4 calls, low)
- [ ] `_build_progress_bar_segments` (4 calls, low)
- [ ] `_apply_fadeout` (8 calls, medium)
- [ ] `_apply_fadein` (8 calls, medium)

### domain/timing.py (2 個函數)
- [ ] `_coerce_non_negative_float` (4 calls, low)
- [ ] `_coerce_bool` (18 calls, **high**)

**批次 1 驗證**: `pytest tests/ -x -k "not slow"`

---

## 批次 2: Infrastructure Layer (12 個函數) - 預估 5h

### infrastructure/rendering/pillow_adapter.py (3 個函數)
- [ ] `_make_text_imageclip` (複雜,含內部類別 _SimpleImageClip)
- [ ] `_measure_text_with_pil` (8 calls, medium)
- [ ] `_find_system_font` (4 calls, low)

### infrastructure/video/moviepy_adapter.py (5 個函數)
- [ ] `_make_fixed_letter_clip` (4 calls, low)
- [ ] `_ensure_dimensions` (6 calls, medium)
- [ ] `_ensure_fullscreen_cover` (4 calls, low)
- [ ] `_auto_letterbox_crop` (4 calls, low)
- [ ] `_create_placeholder_mp4_with_ffmpeg` (4 calls, low)

### infrastructure/media/ffmpeg_wrapper.py (2 個函數)
- [ ] `_probe_media_duration` (6 calls, medium)
- [ ] `_find_and_set_ffmpeg` (已存在,可能需要整合)

### infrastructure/media/audio.py (2 個函數)
- [ ] `make_beep` (4 calls, low)
- [ ] `synthesize_beeps` (4 calls, low)

**批次 2 驗證**: `pytest tests/ -x`

---

## 批次 3: Application Layer (12 個函數) - 預估 5h

### application/video_service.py (12 個函數)
- [ ] `_resolve_entry_video_path` (4 calls, low)
- [ ] `_is_entry_enabled` (4 calls, low)
- [ ] `_prepare_entry_context` (6 calls, medium)
- [ ] `_resolve_ending_video_path` (4 calls, low)
- [ ] `_is_ending_enabled` (4 calls, low)
- [ ] `_prepare_ending_context` (6 calls, medium)
- [ ] `_resolve_letter_asset_dir` (8 calls, medium)
- [ ] `_prepare_letters_context` (12 calls, **high**)
- [ ] `_log_missing_letter_assets` (6 calls, medium)
- [ ] `render_video_moviepy` (複雜,主要渲染函數)
- [ ] `render_video_stub` (4 calls, low)
- [ ] `concatenate_videos_with_transitions` (8 calls, medium)

**批次 3 驗證**: `pytest tests/ -v` + `.\scripts\run_tests.ps1`

---

## 遷移後工作

### T026: 更新 __init__.py
- [ ] 確保新模組可正常 import
- [ ] 添加必要的 __all__ export

### T027: 驗證契約測試
- [ ] `pytest tests/contract/test_migration_mapping_contract.py -v`
- [ ] 預期: 5/5 測試通過

---

## 風險控制

1. **每批次前**: 創建 git commit
2. **每批次後**: 執行測試,確認無破壞
3. **失敗時**: git reset --hard 回退
4. **依賴問題**: 函數間引用需要更新 import

---

## 預估時間軸

- 批次 1 (Domain): 4h
- 批次 2 (Infrastructure): 5h  
- 批次 3 (Application): 5h
- **總計**: ~14h

## 當前狀態

- [x] 遷移計劃制定
- [ ] 批次 1 執行
- [ ] 批次 2 執行
- [ ] 批次 3 執行
- [ ] T026-T027 驗證
