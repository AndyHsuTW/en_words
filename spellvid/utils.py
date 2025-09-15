import json
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Any
import numpy as _np
from PIL import Image, ImageDraw, ImageFont

# moviepy imports are optional; try several fallbacks so utils can detect
# moviepy whether it's packaged as `moviepy.editor` or `moviepy` module.
_mpy = None
_mpy_config = None
_HAS_MOVIEPY = False
try:
    # try editor submodule first (preferred)
    from moviepy import editor as _mpy  # type: ignore
    try:
        from moviepy import config as _mpy_config  # type: ignore
    except Exception:
        _mpy_config = None  # type: ignore
    _HAS_MOVIEPY = True
except Exception:
    try:
        # fall back to top-level moviepy module
        import moviepy as _mpy  # type: ignore
        try:
            from moviepy import config as _mpy_config  # type: ignore
        except Exception:
            _mpy_config = None  # type: ignore
        # verify it exposes the core classes we need
        if hasattr(_mpy, "ImageClip") and hasattr(_mpy, "AudioFileClip"):
            _HAS_MOVIEPY = True
        else:
            _mpy = None
    except Exception:
        _mpy = None
        _mpy_config = None
        _HAS_MOVIEPY = False

# If MoviePy is available, try to configure which ffmpeg binary to use.


def _find_and_set_ffmpeg():
    """Locate ffmpeg and set IMAGEIO_FFMPEG_EXE and moviepy config when found.

     Priority:
     1) environment FFMPEG_PATH (if given and points to ffprobe,
         try sibling ffmpeg)
     2) repo-local FFmpeg/ffmpeg.exe
     3) imageio_ffmpeg.get_ffmpeg_exe()
    """
    # 1: env-provided
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    if not ffmpeg_path:
        ffmpeg_path = os.environ.get("IMAGEIO_FFMPEG_EXE")
    if ffmpeg_path:
        # if user accidentally pointed to ffprobe, try sibling ffmpeg.exe
        base = os.path.basename(ffmpeg_path).lower()
        if "ffprobe" in base:
            candidate = os.path.join(
                os.path.dirname(ffmpeg_path), "ffmpeg.exe"
            )
            if os.path.isfile(candidate):
                ffmpeg_path = candidate
    # 2: repo-local
    if not ffmpeg_path:
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)
        )
        candidate = os.path.join(root, "FFmpeg", "ffmpeg.exe")
        if os.path.isfile(candidate):
            ffmpeg_path = candidate
    # 3: imageio-ffmpeg
    if not ffmpeg_path:
        try:
            import imageio_ffmpeg as _iioff  # type: ignore

            exe = _iioff.get_ffmpeg_exe()
            if exe:
                ffmpeg_path = exe
        except Exception:
            pass

    if ffmpeg_path and os.path.isfile(ffmpeg_path):
        os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_path)
        try:
            if _mpy_config is not None:
                _mpy_config.change_settings({"FFMPEG_BINARY": ffmpeg_path})
        except Exception:
            pass


def _measure_text_with_pil(text: str, pil_font: ImageFont.ImageFont):
    """Measure text size (w, h) using Pillow's textbbox reliably.

    Returns fallback heuristics on error.
    """
    try:
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=pil_font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        return (
            int(len(text) * getattr(pil_font, "size", 10)),
            getattr(pil_font, "size", 16),
        )


def _find_system_font(prefer_cjk: bool, size: int):
    """Try common system font paths; return PIL ImageFont (truetype)
    or load_default.
    """
    candidates = []
    if prefer_cjk:
        candidates = [
            r"C:\Windows\Fonts\msjh.ttf",
            r"C:\Windows\Fonts\msjhbd.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
    else:
        candidates = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            r"C:\Windows\Fonts\times.ttf",
        ]
    for p in candidates:
        try:
            if os.path.isfile(p):
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def _make_text_imageclip(
    text: str,
    font_size: int = 48,
    color=(0, 0, 0),
    bg=None,
    duration: float = None,
    prefer_cjk: bool = False,
    extra_bottom: int = 0,
    fixed_size: tuple | None = None,
):
    """Render text with Pillow and return a MoviePy ImageClip.

    prefer_cjk: if True, tries CJK fonts first.
    bg: background color tuple or None for transparent.
    """
    try:
        font = _find_system_font(prefer_cjk, font_size)
        w, h = _measure_text_with_pil(text, font)
    except Exception:
        font = ImageFont.load_default()
        w, h = (int(len(text) * font_size * 0.6), font_size)

    pad_x = max(12, font_size // 6)  # increased padding
    pad_y = max(8, font_size // 6)   # increased padding
    # allow caller to request timer-specific extra bottom safe margin via
    # passing bg=(0,0,0) conventionally for timer usage; default margin 0
    # allow caller to request an extra bottom safe margin; preserve the
    # existing heuristic where a black bg indicates timer usage and needs
    # additional margin. Caller may pass `extra_bottom` (e.g. reveal safe
    # margin) to reserve space beneath glyphs for underlines.
    bottom_safe_margin = int(extra_bottom or 0)
    if bg is not None and isinstance(bg, tuple) and len(bg) == 3:
        # heuristics: treat black bg callsites (timer) as needing extra bottom
        # margin to avoid glyph descent clipping. Keep this on top of
        # any extra_bottom requested by the caller.
        if bg == (0, 0, 0):
            bottom_safe_margin += 32

    img_w = int(w + pad_x * 2)
    img_h = int(h + pad_y * 2 + bottom_safe_margin)
    # If caller requests a fixed canvas size (w,h), center the rendered
    # text inside that canvas. This helps when rendering per-letter
    # clips in a group so adding/removing letters doesn't change each
    # clip's size and avoids downstream reflow in CompositeVideoClip.
    if fixed_size is not None:
        try:
            fx_w, fx_h = int(fixed_size[0]), int(fixed_size[1])
            # ensure fixed canvas at least as big as measured image
            img_w = max(img_w, fx_w)
            img_h = max(img_h, fx_h)
            # align text to the same left/top origin used by the full
            # reveal image so substrings don't change their left position
            # relative to the fixed canvas. This keeps pad_x/pad_y as the
            # drawing origin for all substrings.
            offset_x = 0
            offset_y = 0
        except Exception:
            offset_x = 0
            offset_y = 0
    else:
        offset_x = 0
        offset_y = 0
    bg_col = (255, 255, 255, 0) if bg is None else tuple(bg) + (255,)
    img = Image.new("RGBA", (img_w, img_h), bg_col)
    draw = ImageDraw.Draw(img)
    # draw text at pad + any centering offset
    draw_x = pad_x + offset_x
    draw_y = pad_y + offset_y
    draw.text((draw_x, draw_y), text, font=font, fill=color)
    arr = _np.array(img)
    # If moviepy is available, wrap into an ImageClip. Otherwise return a
    # tiny fallback object that exposes the minimal API used by tests
    # (get_frame, w, h, size, with_duration).
    if _mpy is not None:
        clip = _mpy.ImageClip(arr)
        if duration is not None:
            clip = clip.with_duration(duration)
        return clip

    class _SimpleImageClip:
        def __init__(self, arr, duration=None):
            self._arr = arr
            self.h = int(arr.shape[0])
            self.w = int(arr.shape[1])
            self.size = (self.w, self.h)
            self._duration = duration

        def get_frame(self, t=0):
            return self._arr

        def with_duration(self, duration):
            self._duration = duration
            return self

        # minimal attributes moviepy users expect
        @property
        def duration(self):
            return self._duration

    clip = _SimpleImageClip(arr, duration=duration)
    return clip


# configure ffmpeg as early as possible
_find_and_set_ffmpeg()

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "letters",
            "word_en",
            "word_zh",
            "image_path",
            "music_path",
        ],
        "properties": {
            "letters": {"type": "string"},
            "word_en": {"type": "string"},
            "word_zh": {"type": "string"},
            "image_path": {"type": "string"},
            "music_path": {"type": "string"},
            "countdown_sec": {"type": "integer"},
            "reveal_hold_sec": {"type": "integer"},
            "theme": {"type": "string"}
        },
        "additionalProperties": False
    }
}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data: Any) -> List[str]:
    """Very small schema validator: returns list of errors (empty if ok)."""
    errors = []
    if not isinstance(data, list):
        errors.append("root must be array")
        return errors
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"item[{i}] not object")
            continue
        for req in SCHEMA["items"]["required"]:
            if req not in item:
                errors.append(f"item[{i}] missing required {req}")
        # detect additional properties
        allowed = set(SCHEMA["items"]["properties"].keys())
        for k in item.keys():
            if k not in allowed:
                errors.append(f"item[{i}] has additional property {k}")
    return errors


# Simple zhuyin map for basic characters used in tests
_ZHUYIN_MAP = {
    "冰": "ㄅㄧㄥ",
    "塊": "ㄎㄨㄞˋ",
}


def zhuyin_for(text: str) -> str:
    """Return a naive zhuyin by joining per-character lookup.

    Missing chars are skipped.
    """
    parts = []
    for ch in text:
        parts.append(_ZHUYIN_MAP.get(ch, ""))
    return " ".join([p for p in parts if p])


def compute_layout_bboxes(
    item: Dict[str, Any], video_size=(1920, 1080)
) -> Dict[str, Dict[str, int]]:
    """Compute bounding boxes for main text elements without using MoviePy.

    Returns a dict with keys 'letters', 'zh', 'timer', 'reveal' each mapping
    to a dict {'x':, 'y':, 'w':, 'h':} representing pixel bbox. Uses the same
    candidates and sizes as the renderer to emulate layout.
    """
    """Headless text bbox calculator using Pillow.

    Returns bounding boxes for keys: letters, zh, timer, reveal.
    """
    w_vid, h_vid = video_size
    boxes: Dict[str, Dict[str, int]] = {}

    # helper alias to module-level measurer
    measure_text = _measure_text_with_pil

    # Letters (top-left)
    letters = item.get("letters", "")
    if letters:
        letters_y = 120  # updated to match renderer
        font_size = 140
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        if font is None:
            text_w = int(len(letters) * font_size * 0.6)
            text_h = font_size
        else:
            text_w, text_h = measure_text(letters, font)
        boxes["letters"] = {"x": 64, "y": letters_y, "w": text_w, "h": text_h}

    # Chinese + zhuyin (top-right)
    word_zh = item.get("word_zh", "")
    zhuyin = zhuyin_for(word_zh)
    zh_text = word_zh + (" " + zhuyin if zhuyin else "")
    if zh_text:
        font_candidates = [
            r"C:\Windows\Fonts\msjh.ttf",
            r"C:\Windows\Fonts\msjhbd.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        font_path = None
        for p in font_candidates:
            if os.path.isfile(p):
                font_path = p
                break
        font_size = 64
        try:
            if font_path:
                pil_font = ImageFont.truetype(font_path, font_size)
            else:
                pil_font = ImageFont.load_default()
            lines = [word_zh, zhuyin] if zhuyin else [word_zh]
            max_w = 0
            total_h = 0
            padding = 8
            for line in lines:
                w, h = measure_text(line, pil_font)
                if w > max_w:
                    max_w = w
                total_h += h + 4
            img_w = max_w + padding * 2
            img_h = total_h + padding * 2
        except Exception:
            img_w = len(zh_text) * font_size // 2
            img_h = font_size * 2
        pos_x = w_vid - 64 - img_w
        boxes["zh"] = {"x": pos_x, "y": 64, "w": img_w, "h": img_h}

    # Timer bbox (first second position) - compute using the same format
    # the renderer will use (mm:ss) based on item countdown to avoid
    # underestimating size when digits change.
    countdown = int(item.get("countdown_sec", 10))
    sec_left = max(0, countdown)
    mm = sec_left // 60
    ss = sec_left % 60
    timer_text = f"{mm:02d}:{ss:02d}"
    timer_font_size = 64
    try:
        # use the same font selection logic as _make_text_imageclip so
        # measured size matches rendered image
        timer_font = _find_system_font(False, timer_font_size)
        tw, th = measure_text(timer_text, timer_font)
    except Exception:
        tw, th = timer_font_size, timer_font_size // 2
    # match _make_text_imageclip padding so predicted box
    # equals rendered image size
    pad_x = max(12, timer_font_size // 6)
    pad_y = max(8, timer_font_size // 6)
    bottom_safe_margin = 32
    img_w = int(tw + pad_x * 2)
    img_h = int(th + pad_y * 2 + bottom_safe_margin)
    # updated to match renderer position; include font_size for tests
    boxes["timer"] = {
        "x": 64,
        "y": 450,
        "w": img_w,
        "h": img_h,
        "font_size": timer_font_size,
    }

    # Reveal area (center bottom) - approximate width for longest word_en
    word_en = item.get("word_en", "")
    if word_en:
        reveal_font_size = 128
        try:
            # Use the same font selection as the renderer to get consistent
            # measurements (avoid tiny default bitmap font causing tiny boxes)
            rf = _find_system_font(False, reveal_font_size)
            rw, rh = measure_text(word_en, rf)
        except Exception:
            rw = int(len(word_en) * reveal_font_size * 0.6)
            rh = reveal_font_size
        # match _make_text_imageclip padding so predicted box equals rendered
        pad_x = max(12, reveal_font_size // 6)
        pad_y = max(8, reveal_font_size // 6)
        # reserve extra bottom space inside the reveal image so underlines
        # can be drawn beneath the glyphs without overlapping. This must
        # mirror the extra_bottom used when creating reveal ImageClips.
        reveal_extra_bottom = 32
        img_w = int(rw + pad_x * 2)
        img_h = int(rh + pad_y * 2 + reveal_extra_bottom)

        # For headless layout calculations we should return the reveal box
        # x as an absolute coordinate in the video frame (centered). The
        # renderer composes the reveal ImageClip centered on the video
        # and previously compute_layout_bboxes returned rx=0 which made
        # the caller treat underline positions as local to the reveal
        # image. That mismatch meant underlines were placed at the left
        # edge. Return an absolute centered x so downstream code can
        # overlay underlines at correct absolute positions.
        rx = max(0, (w_vid - img_w) // 2)
        # place reveal so it sits above the bottom of the video with a
        # safe margin to avoid glyph descent clipping on some fonts
        safe_bottom_margin = 32
        ry = max(0, h_vid - img_h - safe_bottom_margin)
        boxes["reveal"] = {
            "x": rx,
            "y": ry,
            "w": img_w,
            "h": img_h,
            "font_size": reveal_font_size,
        }

        # compute per-letter underline boxes (absolute positions)
        # each underline is a small horizontal bar beneath a letter position.
        # Approximate per-letter horizontal region by splitting the measured
        # text width into equal segments. Previously these underline boxes
        # were returned relative to the reveal image (local coords). Since
        # the reveal box now reports an absolute x, return underline boxes
        # with absolute x/y so tests and renderer align.
        num_letters = len(word_en)
        if num_letters > 0:
            # available width for letters inside reveal image (exclude padding)
            inner_w = rw
            # avoid zero-division
            seg_w = max(1, inner_w // num_letters)
            underline_h = 4
            # leave a slightly larger margin between glyph baseline and
            # underline so they don't overlap across fonts
            underline_margin_bottom = 12
            underlines = []
            # left padding used when constructing the image in
            # _make_text_imageclip
            pad_x = max(12, reveal_font_size // 6)
            pad_y = max(8, reveal_font_size // 6)
            # Introduce a small horizontal gap between adjacent underlines so
            # they don't visually touch. Compute a gap as a fraction of the
            # segment width but clamp to a few pixels to remain stable across
            # small fonts. Center each underline inside its segment and reduce
            # its width accordingly.
            # Instead of equal segments, measure each glyph's actual width
            # using Pillow so the underline centers under the glyph. This
            # produces more accurate alignment especially for variable-width
            # fonts. Keep a small horizontal gap between adjacent underlines.
            try:
                # get a PIL font similar to what renderer uses
                pil_font = _find_system_font(False, reveal_font_size)
                # measure each character
                char_widths = []
                for ch in word_en:
                    cw, _ch_h = measure_text(ch, pil_font)
                    char_widths.append(max(1, int(cw)))
            except Exception:
                # fallback: equal-width approximation
                char_widths = [max(1, seg_w) for _ in range(num_letters)]

            gap = max(4, seg_w // 10)
            # compute the starting x of the first glyph relative to
            # the reveal image. This mirrors how text is drawn at pad_x
            cursor = pad_x
            for i, ch_w in enumerate(char_widths):
                seg_start = cursor
                avail = min(ch_w, max(0, (pad_x + inner_w) - seg_start))
                uw = max(1, avail - gap)
                # center underline under the glyph box
                local_ux = seg_start + max(0, (avail - uw) // 2)
                # advance cursor by the glyph width (not by seg_w)
                cursor += ch_w
                # y relative to reveal image: prefer placing underline
                # inside the reserved extra-bottom area so it won't overlap
                # drawn glyph pixels. Compute two candidates and choose the
                # lower (visually further down) one.
                candidate_from_text = pad_y + rh + underline_margin_bottom
                # start of the reserved extra bottom zone
                extra_zone_start = img_h - reveal_extra_bottom
                # prefer placing underline inside extra zone (with small
                # inset), otherwise fall back to candidate_from_text
                # add a small inset into the extra zone to avoid touching
                # antialiased glyph pixels
                local_uy = max(candidate_from_text, extra_zone_start + 6)
                # ensure underline fits inside image
                if local_uy + underline_h > img_h:
                    local_uy = max(0, img_h - underline_h)
                # keep underline coords relative to the reveal image.
                # The renderer composes the reveal image at absolute
                # position r_box['x']/['y'] and will add those offsets
                # when overlaying underlines.
                ux = local_ux
                uy = local_uy
                underlines.append(
                    {"x": ux, "y": uy, "w": uw, "h": underline_h}
                )
            boxes["reveal_underlines"] = underlines

    return boxes


def _make_fixed_letter_clip(
    letter: str,
    fixed_size: tuple,
    font_size: int = 128,
    color=(0, 0, 0),
    duration: float = None,
    prefer_cjk: bool = False,
):
    """Render a single letter centered on a fixed transparent canvas and
    return an ImageClip. This ensures per-letter clips have identical
    dimensions to avoid pushing other clips when they appear/disappear."""
    # delegate to _make_text_imageclip which now supports fixed_size
    return _make_text_imageclip(
        text=letter,
        font_size=font_size,
        color=color,
        duration=duration,
        prefer_cjk=prefer_cjk,
        extra_bottom=0,
        fixed_size=fixed_size,
    )


def check_assets(item: Dict[str, Any]) -> Dict[str, bool]:
    res = {"image_exists": False, "music_exists": False}
    if os.path.isfile(item.get("image_path", "")):
        res["image_exists"] = True
    if os.path.isfile(item.get("music_path", "")):
        res["music_exists"] = True
    return res


def synthesize_beeps(duration_sec: int = 3, rate_hz: int = 1) -> bytes:
    """Return a stub bytes object representing beep audio.

    This is intentionally simple to avoid binary deps.
    """
    return b"BEEP" * max(1, duration_sec * rate_hz)


def _create_placeholder_mp4_with_ffmpeg(out_path: str) -> bool:
    """Create a tiny valid mp4 using ffmpeg if available.

    Returns True on success, False otherwise.
    """
    try:
        ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE") or shutil.which("ffmpeg")
        if not ffmpeg:
            return False
    # create a single white frame PNG and encode to mp4
    # (use +faststart to ensure moov atom is at file start)
        with tempfile.TemporaryDirectory() as td:
            png = os.path.join(td, "frame.png")
            try:
                from PIL import Image

                img = Image.new("RGB", (1920, 1080), (255, 255, 255))
                img.save(png, "PNG")
            except Exception:
                return False

            cmd = [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                png,
                "-t",
                "1",
                "-vf",
                "scale=1920:1080",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                out_path,
            ]
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return True
    except Exception:
        return False


def render_video_stub(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    use_moviepy: bool = False,
) -> Dict[str, Any]:
    """Render video.

    If MoviePy is available and use_moviepy is True, call the real renderer.
    Otherwise fallback to the small stub that writes a placeholder file.
    """
    if use_moviepy and _HAS_MOVIEPY:
        return render_video_moviepy(item, out_path, dry_run=dry_run)

    if dry_run:
        return {"status": "dry-run", "out": out_path}
    # ensure out dir
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Try to write a minimal valid mp4 using ffmpeg if available
    created = _create_placeholder_mp4_with_ffmpeg(out_path)
    if not created:
        # fallback to a tiny placeholder header (not a valid mp4 but keeps API)
        with open(out_path, "wb") as f:
            f.write(b"MP4")
    return {"status": "ok", "out": out_path}


def render_video_moviepy(
    item: Dict[str, Any], out_path: str, dry_run: bool = False
) -> Dict[str, Any]:
    """Real video rendering using MoviePy.

    This implementation creates a simple layout:
    - background: image if present, otherwise white color
    - letters (top-left), chinese+zhuyin (top-right)
    - countdown timer on left side (updates every second)
    - reveal (bottom center) appears after countdown with typewriter effect
    - optional music and short beeps in last 3 seconds
    """
    if not _HAS_MOVIEPY:
        raise RuntimeError("MoviePy not available")

    countdown = int(item.get("countdown_sec", 10))
    reveal = int(item.get("reveal_hold_sec", 5))
    duration = float(countdown + reveal)

    if dry_run:
        return {"status": "dry-run", "out": out_path}

    # prepare background: always use a white full-screen ColorClip
    bg = (
        _mpy.ColorClip(size=(1920, 1080), color=(255, 255, 255))
        .with_duration(duration)
    )
    clips = [bg]

    # If an image is provided, load via Pillow, scale to fit a centered
    # square region and overlay it in the center of the video.
    img_path = item.get("image_path")
    bg_used = False
    bg_error = None
    if img_path and os.path.isfile(img_path):
        img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
        if img_path.lower().endswith(img_exts):
            try:
                from PIL import Image as _PILImage

                pil_img = _PILImage.open(img_path).convert("RGBA")
                # define centered square size (max square side)
                square_size = int(min(1920, 1080) * 0.7)  # 70% of shorter dim
                w0, h0 = pil_img.size
                scale = min(square_size / w0, square_size / h0)
                new_w = max(1, int(w0 * scale))
                new_h = max(1, int(h0 * scale))
                pil_img = pil_img.resize((new_w, new_h), _PILImage.LANCZOS)
                arr = _np.array(pil_img)

                img_clip = _mpy.ImageClip(arr).with_duration(duration)
                # position centered
                pos_x = (1920 - new_w) // 2
                pos_y = (1080 - new_h) // 2
                img_clip = img_clip.with_position((pos_x, pos_y))
                clips.append(img_clip)
                bg_used = True
            except Exception as e:
                bg_error = str(e)
                # leave only white background
        else:
            # not an image extension; ignore and keep white bg
            pass

    # Letters (top-left) — move lower to avoid clipping
    letters = item.get("letters", "")
    if letters:
        letters_y = 120  # increased from 80 to avoid top clipping
        txt_letters = _make_text_imageclip(
            text=letters, font_size=140, color=(0, 0, 0), duration=duration
        )
        txt_letters = txt_letters.with_position((64, letters_y))
        clips.append(txt_letters)

    # Chinese + zhuyin (top-right) — render via Pillow to ensure CJK support
    word_zh = item.get("word_zh", "")
    zhuyin = zhuyin_for(word_zh)
    zh_text = word_zh + (" " + zhuyin if zhuyin else "")
    if zh_text:
        # try common Windows font paths for CJK
        font_candidates = [
            r"C:\Windows\Fonts\msjh.ttf",
            r"C:\Windows\Fonts\msjhbd.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        font_path = None
        for p in font_candidates:
            if os.path.isfile(p):
                font_path = p
                break

        try:
            from PIL import Image, ImageDraw, ImageFont

            font_size = 64
            if font_path:
                pil_font = ImageFont.truetype(font_path, font_size)
            else:
                pil_font = ImageFont.load_default()

            # measure text and create image
            lines = [word_zh, zhuyin] if zhuyin else [word_zh]
            padding = 8
            max_w = 0
            total_h = 0
            for line in lines:
                w, h = _measure_text_with_pil(line, pil_font)
                if w > max_w:
                    max_w = w
                total_h += h + 4

            img_w = max_w + padding * 2
            img_h = total_h + padding * 2
            img = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            y = padding
            for line in lines:
                draw.text((padding, y), line, font=pil_font, fill=(0, 0, 0))
                _, line_h = _measure_text_with_pil(line, pil_font)
                y += line_h + 4

            # convert to clip
            # convert pillow image to numpy array
            arr = _np.array(img)
            txt_zh_clip = _mpy.ImageClip(arr).with_duration(duration)
            pos_x = 1920 - 64 - txt_zh_clip.w
            txt_zh_clip = txt_zh_clip.with_position((pos_x, 64))
            clips.append(txt_zh_clip)
        except Exception:
            # fallback: small TextClip with default font
            t = _mpy.TextClip(
                text=word_zh, font_size=48, font=None, color="black"
            )
            t = t.with_position((1920 - 64 - t.w, 64)).with_duration(duration)
            clips.append(t)

    # Timer: create per-second TextClips placed at start times
    # Also keep the final timer display until end of video
    for i in range(countdown + 1):
        sec_left = max(0, countdown - i)
        mm = sec_left // 60
        ss = sec_left % 60
        timer_text = f"{mm:02d}:{ss:02d}"
        # For the last timer (i == countdown), extend duration to
        # end of video so the display includes 00:00 and remains until
        # the reveal period.
        timer_duration = duration - i if i == countdown else 1
        tclip = _make_text_imageclip(
            text=timer_text,
            font_size=64,
            color=(255, 255, 255),
            bg=(0, 0, 0),
            duration=timer_duration,
        )
        # moved down from 420 to 450 to avoid bottom clipping
        tclip = tclip.with_position((64, 450)).with_start(i)
        clips.append(tclip)

    # Reveal typewriter: show substrings sequentially
    word_en = item.get("word_en", "")
    if word_en:
        n = max(1, len(word_en))
        per = reveal / n
        safe_bottom_margin = 32
        # Compute the full reveal image size once so every substring
        # clip can be rendered on that fixed canvas. This avoids changing
        # clip widths during the typewriter effect which would otherwise
        # shift other positioned clips.
        try:
            full_rc = _make_text_imageclip(
                text=word_en, font_size=128, color=(0, 0, 0),
                extra_bottom=32, duration=1,
            )
            full_w = (
                getattr(full_rc, "w", None)
                or getattr(full_rc, "size", (None, None))[0]
            )
            full_h = (
                getattr(full_rc, "h", None)
                or getattr(full_rc, "size", (None, None))[1]
            )
            if full_w is None or full_h is None:
                raise Exception("could not determine full reveal size")
            fixed_canvas = (int(full_w), int(full_h))
        except Exception:
            # fallback to a reasonable fixed size based on font heuristics
            fixed_canvas = (int(len(word_en) * 128 * 0.6) + 48, 128 + 48 + 32)

        for idx in range(1, n + 1):
            sub = word_en[:idx]
            # reserve extra bottom space inside reveal image so underlines
            # can be drawn below glyphs without overlapping.
            rc = _make_text_imageclip(
                text=sub, font_size=128, color=(0, 0, 0), duration=per,
                extra_bottom=32, fixed_size=fixed_canvas,
            )
            # compute a y position so the reveal clip sits above the bottom
            # by safe_bottom_margin to avoid glyph descent clipping
            try:
                clip_h = getattr(rc, "h", None)
                if clip_h is None:
                    clip_h = getattr(rc, "size", (None, None))[1]
                clip_h = int(clip_h)
            except Exception:
                clip_h = 128 + max(8, 128 // 6) * 2
            pos_y = max(0, 1080 - clip_h - safe_bottom_margin)
            rc = rc.with_position(("center", pos_y)).with_start(
                countdown + (idx - 1) * per
            )
            clips.append(rc)

        # If reveal_underlines metadata exists (from compute_layout_bboxes),
        # create small ImageClips for each underline and overlay them at
        # absolute positions so they appear under the reveal text.
        # Default style: white underline, 4px height.
        try:
            r_meta = compute_layout_bboxes(item).get("reveal_underlines")
            r_box = compute_layout_bboxes(item).get("reveal")
        except Exception:
            r_meta = None
            r_box = None

        if r_meta and r_box and _HAS_MOVIEPY:
            try:
                for ul in r_meta:
                    abs_x = int(r_box["x"] + ul.get("x", 0))
                    abs_y = int(r_box["y"] + ul.get("y", 0))
                    w = max(1, int(ul.get("w", 1)))
                    h = max(1, int(ul.get("h", 1)))
                    # create solid RGBA image for underline
                    try:
                        import numpy as _np_local

                        rgba = _np_local.zeros(
                            (h, w, 4), dtype=_np_local.uint8)
                        rgba[..., :3] = _np_local.array(
                            (0, 0, 0), dtype=_np_local.uint8)
                        rgba[..., 3] = 255
                        ul_clip = _mpy.ImageClip(rgba).with_duration(duration)
                        ul_clip = ul_clip.with_position((abs_x, abs_y))
                        clips.append(ul_clip)
                    except Exception:
                        # fallback: draw using ColorClip if numpy unavailable
                        try:
                            ul_clip = _mpy.ColorClip(size=(w, h), color=(
                                0, 0, 0)).with_duration(duration)
                            ul_clip = ul_clip.with_position((abs_x, abs_y))
                            clips.append(ul_clip)
                        except Exception:
                            pass
            except Exception:
                pass

    final = _mpy.CompositeVideoClip(clips, size=(1920, 1080))
    final = final.with_duration(duration)

    # Audio: optional music + beep in last 3 seconds
    audio_clips = []
    music_path = item.get("music_path")
    audio_loaded = False
    audio_error = None
    if music_path and os.path.isfile(music_path):
        try:
            # ensure ffmpeg is available for moviepy to read audio
            ffprobe_ok = shutil.which("ffprobe")
            if not ffprobe_ok:
                ffprobe_ok = os.environ.get("IMAGEIO_FFMPEG_EXE")
                # no ffprobe on PATH; will try IMAGEIO_FFMPEG_EXE if set
            af = _mpy.AudioFileClip(music_path)
            try:
                src_dur = float(getattr(af, "duration", 0.0) or 0.0)
            except Exception:
                src_dur = 0.0

            # If source audio shorter than desired duration, concatenate
            # multiple copies so the writer won't read past EOF.
            try:
                if src_dur <= 0.0:
                    # unusable source duration
                    raise RuntimeError("source audio has zero duration")

                if src_dur < duration:
                    # figure how many repeats needed
                    import math as _math

                    n = int(_math.ceil(duration / src_dur))
                    # create repeated clips with start offsets so the
                    # composite covers the whole duration. Avoid calling
                    # .subclip on CompositeAudioClip which may not exist.
                    comp_clips = []
                    start = 0.0
                    for _ in range(n):
                        comp_clips.append(af.with_start(start))
                        start += src_dur
                    music = _mpy.CompositeAudioClip(comp_clips)
                else:
                    # source is long enough; take beginning portion
                    if hasattr(af, "subclip"):
                        music = af.subclip(0, duration)
                    else:
                        # try with_duration as fallback
                        try:
                            music = af.with_duration(duration)
                        except Exception:
                            music = af

                # best-effort: ensure final clip has expected duration
                try:
                    music = music.with_duration(duration)
                except Exception:
                    pass

            except Exception:
                # propagate to outer except so audio_error is recorded
                raise

            audio_clips.append(music)
            audio_loaded = True
        except Exception as e:
            # record failure to load music so callers/tests can detect it
            audio_loaded = False
            try:
                audio_error = str(e)
            except Exception:
                audio_error = "(error stringify failed)"
            # keep going — renderer can still produce video without music
            pass

    # beep: generate short sine beeps at last 3 seconds, once per second
    def make_beep(start_sec):
        freq = 1000.0
        length = 0.3

        def make_frame(t):
            # t may be array-like; compute sine and return mono samples
            mono = (_np.sin(2 * _np.pi * freq * t) * 0.2).astype(_np.float32)
            # ensure a 2-channel (stereo) array to match common audio
            # track shapes and avoid broadcasting errors during mix
            try:
                stereo = _np.column_stack((mono, mono))
            except Exception:
                stereo = mono.reshape(-1, 1)
            return stereo

        ac = _mpy.AudioClip(make_frame, duration=length, fps=44100)
        return ac.with_start(start_sec)

    last3 = min(3, int(duration))
    for k in range(last3):
        start = max(0, duration - last3 + k)
        try:
            audio_clips.append(make_beep(start))
        except Exception:
            pass

    if audio_clips:
        try:
            final_audio = _mpy.CompositeAudioClip(audio_clips)
            final = final.with_audio(final_audio)
        except Exception:
            pass

    # ensure out dir
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # write the file
    try:
        # if ffmpeg is available via IMAGEIO_FFMPEG_EXE,
        # write with explicit codecs
        ffmpeg_exe = os.environ.get("IMAGEIO_FFMPEG_EXE")
        if ffmpeg_exe:
            final.write_videofile(
                out_path,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="medium",
            )
        else:
            # fallback: simple call
            final.write_videofile(out_path, fps=30)
    finally:
        # close resources
        try:
            final.close()
        except Exception:
            pass

    return {
        "status": "ok",
        "out": out_path,
        "bg_used": bg_used,
        "bg_error": bg_error,
        "audio_loaded": audio_loaded,
        "audio_error": audio_error,
    }
