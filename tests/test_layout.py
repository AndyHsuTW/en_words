"""像素層檢查：確認倒數計時（timer）在實際渲染影格中沒有被裁切。

說明：
- 該測試會使用庫內部的 Pillow-based 文字渲染 helper（若存在）來產生倒數文字的影像，
  並計算影像中非透明像素的 bbox，與 headless 預測的 timer bbox 比較。
- 如果實際像素高度大於預測的 timer 高度，則視為被裁切（或超出配置的文字區塊），測試失敗。

注意：此測試檔取代原有僅檢查 bbox 是否超出畫面邊界的項目，新的目標是檢測「文字內容是否被其所屬區塊裁切」。
"""

import numpy as np
import pytest

from spellvid.utils import compute_layout_bboxes


def _bbox_from_alpha(alpha):
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        return None
    top, left = int(ys.min()), int(xs.min())
    bottom, right = int(ys.max()), int(xs.max())
    return {"x": left, "y": top, "w": right - left + 1, "h": bottom - top + 1}


def test_countdown_timer_pixel_not_exceed_assigned_box():
    """檢查倒數計時的實際像素 bbox 是否超過 compute_layout_bboxes 預測的 timer bbox。

    若缺少內部渲染 helper（例如 _make_text_imageclip）則跳過測試。
    """
    item = {
        "letters": "R",
        "word_en": "Arm",
        "word_zh": "臂",
        "image_path": "",
        "music_path": "assets/Arm, arm.mp3",
        "countdown_sec": 3,
        "reveal_hold_sec": 3,
    }

    boxes = compute_layout_bboxes(item)
    timer_box = boxes.get("timer")
    assert timer_box is not None, "no timer bbox"

    # 使用內部的 Pillow 渲染 helper 來生成倒數第一個數字的影像
    utils = __import__("spellvid.utils", fromlist=["_make_text_imageclip"])
    make_clip = getattr(utils, "_make_text_imageclip", None)
    if make_clip is None:
        pytest.skip("_make_text_imageclip helper not available")
    # skip if moviepy missing (ImageClip required)
    if getattr(utils, "_mpy", None) is None:
        pytest.skip("moviepy not available; cannot create ImageClip")

    # 使用與 renderer 一致的 timer 文本格式 (mm:ss)
    countdown = int(item.get("countdown_sec", 1))
    sec_left = max(0, countdown)
    mm = sec_left // 60
    ss = sec_left % 60
    timer_text = f"{mm:02d}:{ss:02d}"

    clip = make_clip(
        text=timer_text,
        font_size=timer_box.get("font_size", 64),
        color=(255, 255, 255),
        bg=(0, 0, 0),
        duration=1,
        prefer_cjk=False,
    )

    # 擷取時間點 0 的影格
    try:
        frame = clip.get_frame(0)
    except Exception as e:
        pytest.skip(f"cannot get frame from clip: {e}")

    # 判斷非透明像素；support RGBA or RGB
    if frame.ndim == 3 and frame.shape[2] == 4:
        alpha = frame[:, :, 3]
    else:
        # RGB: consider non-black pixels as text presence
        alpha = (frame.astype(int).sum(axis=2) > 0)

    pixel_bbox = _bbox_from_alpha(alpha)
    assert pixel_bbox is not None, "no visible pixels"

    # 比較實際像素高度與預測的 timer 高度
    actual_h = pixel_bbox["h"]
    assigned_h = timer_box.get("h")
    assert assigned_h is not None, "timer bbox must include height 'h'"

    # Fail when actual pixel height exceeds assigned box height (代表被裁切或文字過大)
    assert actual_h <= assigned_h, (
        f"Timer pixel h {actual_h} > assigned {assigned_h}"
    )

    # 檢查 rendered timer image 的上下內邊距是否合理
    # 如果底部內邊距小於頂部，代表文字在方塊內偏下（可能被裁切或視覺不平衡）
    img_h = frame.shape[0]
    top_pad = pixel_bbox["y"]
    bottom_pad = img_h - (pixel_bbox["y"] + pixel_bbox["h"])
    assert bottom_pad >= top_pad, (
        "timer vertical padding asymmetric: "
        f"top={top_pad}px bottom={bottom_pad}px"
    )


def test_reveal_word_not_clipped_bottom():
    """檢查底部輸出的英文單字（reveal）是否被裁切。

    兩個失敗條件：
    - 實際渲染的字元像素超出 compute_layout_bboxes 所分配的 reveal box
    - 實際渲染的字元像素落在整體影像（1920x1080）之外

    本測試會使用內部的 `_make_text_imageclip` Pillow 渲染 helper。
    如果 helper 不存在或無法擷取影格，則跳過測試。
    """
    item = {
        "letters": "R",
        # 使用一個典型單字（也可換成較長字以測試超出邊界的情況）
        "word_en": "Supercalifragilisticexpialidocious",
        "word_zh": "臂",
        "image_path": "",
        "music_path": "assets/Arm, arm.mp3",
        "countdown_sec": 3,
        "reveal_hold_sec": 3,
    }

    boxes = compute_layout_bboxes(item)
    reveal_box = boxes.get("reveal")
    assert reveal_box is not None, "no reveal bbox"

    # 取得內部渲染 helper
    utils = __import__("spellvid.utils", fromlist=["_make_text_imageclip"])
    make_clip = getattr(utils, "_make_text_imageclip", None)
    if make_clip is None:
        pytest.skip("_make_text_imageclip helper not available")
    # skip if moviepy missing (ImageClip required)
    if getattr(utils, "_mpy", None) is None:
        pytest.skip("moviepy not available; cannot create ImageClip")

    # compute_layout_bboxes 使用 reveal_font_size = 128
    # 我們在測試中也以相同大小來渲染以便比較
    reveal_font_size = 128

    clip = make_clip(
        text=item["word_en"],
        font_size=reveal_font_size,
        color=(255, 255, 255),
        bg=None,
        duration=1,
        prefer_cjk=False,
    )

    try:
        frame = clip.get_frame(0)
    except Exception as e:
        pytest.skip(f"cannot get frame from clip: {e}")

    if frame.ndim == 3 and frame.shape[2] == 4:
        alpha = frame[:, :, 3]
    else:
        alpha = (frame.astype(int).sum(axis=2) > 0)

    pixel_bbox = _bbox_from_alpha(alpha)
    assert pixel_bbox is not None, "no visible pixels in reveal render"

    # 檢查實際像素是否超出 assigned reveal box
    actual_h = pixel_bbox["h"]
    actual_w = pixel_bbox["w"]
    assigned_h = reveal_box.get("h")
    assigned_w = reveal_box.get("w")
    assert assigned_h is not None, "reveal bbox must include height 'h'"
    assert assigned_w is not None, "reveal bbox must include width 'w'"

    assert actual_h <= assigned_h, (
        f"Reveal pixel height {actual_h} > assigned box height {assigned_h}"
    )
    assert actual_w <= assigned_w, (
        f"Reveal pixel width {actual_w} > assigned box width {assigned_w}"
    )

    # 檢查實際渲染的像素在 renderer 的動態 placement 下是否會被截斷
    # renderer 現在會根據 clip 的實際高度計算 y：
    # pos_y = max(0, 1080 - clip_h - safe_bottom_margin)
    vid_h = 1080
    safe_bottom_margin = 32
    img_h = frame.shape[0]
    # compute renderer-like placement using the rendered clip height
    reveal_y_renderer = max(0, vid_h - img_h - safe_bottom_margin)
    abs_left = reveal_box["x"] + pixel_bbox["x"]
    abs_top = reveal_y_renderer + pixel_bbox["y"]
    abs_bottom = abs_top + pixel_bbox["h"]

    # ensure anchor point is within video horizontally and vertically
    assert abs_left >= 0 and abs_top >= 0, (
        "Reveal rendered pixels start outside video "
        f"(left={abs_left}, top={abs_top})"
    )

    # Expect no clipping: bottom coordinate should be within video height
    assert abs_bottom <= vid_h, (
        "Reveal rendered pixels extend outside video bottom "
        f"(bottom={abs_bottom} > {vid_h})"
    )
