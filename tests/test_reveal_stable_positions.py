"""
此測試用於驗證在「逐字顯示（reveal / typewriter）」效果中，當新字元加入時，
先前已顯示的字元位置不會發生水平位移。

動機：渲染器會生成一序列逐步增加字符的 ImageClip（例如 'T'、'TE'、'TES' ...），
如果每個 substring 在固定畫布上對齊方式不同（例如居中），則第一個字元的
左邊界會在不同影格改變，導致視覺上的重排或推移。此測試確保在相同的固定畫布
下，第一個字元的最左側非透明像素（x 座標）在單字與多字渲染間保持不變。

驗證方法：
- 先渲染完整單字以取得固定畫布尺寸。
- 在該固定畫布上渲染第一個字，記錄最左側非透明像素的 x 座標。
- 在相同固定畫布上渲染前兩個字，記錄最左側非透明像素的 x 座標。
- 比較兩者 x 座標是否相等；若不相等則測試失敗。
"""

import numpy as np
import pytest

from spellvid import utils


def _leftmost_alpha_x(frame_arr: np.ndarray) -> int:
    """Return x coordinate of leftmost non-transparent pixel in RGBA array."""
    # Expect RGBA
    if frame_arr.ndim == 3 and frame_arr.shape[2] == 4:
        alpha = frame_arr[..., 3]
    else:
        # no alpha channel: consider any non-white pixel as content
        gray = np.mean(frame_arr, axis=2)
        alpha = (gray < 250).astype(np.uint8) * 255
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        return -1
    return int(xs.min())


@pytest.mark.skipif(
    not getattr(utils, "_mpy", None), reason="MoviePy not available"
)
def test_reveal_first_letter_position_stable():
    word = "TEST"
    # compute fixed canvas from full word (mirrors renderer behavior)
    full = utils._make_text_imageclip(
        text=word, font_size=128, extra_bottom=32, duration=1
    )
    full_w = (
        getattr(full, "w", None) or getattr(full, "size", (None, None))[0]
    )
    full_h = (
        getattr(full, "h", None) or getattr(full, "size", (None, None))[1]
    )
    assert full_w is not None and full_h is not None
    fixed = (int(full_w), int(full_h))

    # single-letter clip for first letter
    a = utils._make_text_imageclip(
        text=word[0],
        font_size=128,
        extra_bottom=32,
        duration=1,
        fixed_size=fixed,
    )
    fa = a.get_frame(0)
    left_a = _leftmost_alpha_x(fa)

    # multi-letter clip where first letter should remain at same x within
    # same fixed canvas
    b = utils._make_text_imageclip(
        text=word[:2],
        font_size=128,
        extra_bottom=32,
        duration=1,
        fixed_size=fixed,
    )
    fb = b.get_frame(0)
    left_b = _leftmost_alpha_x(fb)

    # They must be equal — if not, the first glyph has shifted horizontally
    assert left_a == left_b, f"first letter moved: {left_a} != {left_b}"
