r"""
remove_watermark.py

移除影片浮水印/商標的工具，提供多種策略：
  - delogo : 使用 ffmpeg 的 delogo filter（快速且簡單）
  - fill   : 取樣背景色並疊上實心矩形（快速）
  - inpaint: 使用 OpenCV 對每一幀做 inpaint（品質較好但較慢）

使用範例（PowerShell）：
  # 使用 delogo 並指定區域（可把參數拆行以利閱讀）
  python .\scripts\remove_watermark.py --mode delogo \
      --input .\assets\entry.mp4 --output .\out\entry_delogo_script.mp4 \
      --box 1368,995,249,75

  # 使用取樣背景色再覆蓋（box 格式相同）
  python .\scripts\remove_watermark.py --mode fill \
      --input .\assets\entry.mp4 --output .\out\entry_filled.mp4 \
      --box 1368,995,250,75

  # 使用 inpaint（較慢）：會先產生暫存影片，然後把音訊合回去
  python .\scripts\remove_watermark.py --mode inpaint \
      --input .\assets\entry.mp4 --output .\out\entry_inpaint.mp4 \
      --box 1368,995,250,75

說明：
  - box 格式為 x,y,w,h（像素）。若 box 接觸到畫面邊界，腳本會自動縮小 1px 以避免 ffmpeg delogo 發生錯誤。
    - 預設會使用專案內的 FFmpeg 路徑：.\FFmpeg\ffmpeg.exe；如需使用其他 ffmpeg，可用 --ffmpeg 指定。
"""

import argparse
import subprocess
from pathlib import Path


def parse_box(s):
    parts = [int(p) for p in s.split(',')]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError('box must be x,y,w,h')
    return tuple(parts)


def ensure_out_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def run_ffmpeg_cmd(cmd):
    print('Running:', ' '.join(cmd))
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise SystemExit(f'ffmpeg failed (rc={proc.returncode})')


def adjust_box_to_frame(box, W, H):
    x, y, w, h = box
    # 確保在畫面範圍內
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x + w > W:
        w = max(1, W - x - 1)
    if y + h > H:
        h = max(1, H - y - 1)
    return (x, y, w, h)


def mode_delogo(ffmpeg, infile, outfile, box):
    # 對整支影片使用 ffmpeg delogo 過濾器
    # 若 box 接觸邊界會自動縮小 1px
    # 先使用 ffprobe 探測影片尺寸
    import json
    probe = subprocess.run([
        ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe'),
        '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json', infile
    ], capture_output=True, text=True)
    try:
        j = json.loads(probe.stdout)
        W = int(j['streams'][0]['width'])
        H = int(j['streams'][0]['height'])
    except Exception:
        W = None
        H = None

    if W and H:
        box = adjust_box_to_frame(box, W, H)

    x, y, w, h = box
    # 最後保險：若 x+w 等於寬度則把 w 減 1
    if W and x + w >= W:
        w = max(1, W - x - 1)

    cmd = [ffmpeg, '-y', '-i', infile, '-vf',
           f"delogo=x={x}:y={y}:w={w}:h={h}:show=0", '-c:a', 'copy', outfile]
    run_ffmpeg_cmd(cmd)


def sample_ground_color(infile):
    # 讀取一幀（1s 位置），從底部區域取樣以找出背景色中值
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(infile)
    if not cap.isOpened():
        raise SystemExit('failed to open video for sampling')
    # seek to 1s
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise SystemExit('failed to read frame for sampling')
    H, W = frame.shape[:2]
    y_start = int(H * 0.7)
    roi = frame[y_start:H, 0:W]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_green = np.array([30, 40, 30])
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    if cv2.countNonZero(mask) > 50:
        vals = roi[mask > 0]
        med_bgr = np.median(vals, axis=0).astype(int)
    else:
        med_bgr = np.median(roi.reshape(-1, 3), axis=0).astype(int)
    # 回傳 RGB 三元組
    return (int(med_bgr[2]), int(med_bgr[1]), int(med_bgr[0]))


def mode_fill(ffmpeg, infile, outfile, box):
    # 取樣背景色，建立實心 PNG，再用 ffmpeg 疊上去
    from PIL import Image
    x, y, w, h = box
    rgb = sample_ground_color(infile)
    tmp_dir = Path('.').resolve() / 'out'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    color_png = str(tmp_dir / 'wm_fill.png')
    Image.new('RGB', (w, h), rgb).save(color_png)
    # overlay color image at box position
    cmd = [
        ffmpeg, '-y', '-i', infile, '-i', color_png,
        '-filter_complex', f"[0:v][1:v] overlay={x}:{y}",
        '-c:a', 'copy', outfile
    ]
    run_ffmpeg_cmd(cmd)


def mode_inpaint(ffmpeg, infile, outfile, box):
    # 使用 OpenCV 對每一幀做 inpaint（Telea 演算法）。會先寫出沒有音訊的暫存影片，
    # 完成後再用 ffmpeg 把原始音訊合回輸出檔
    import cv2
    import numpy as np
    tmp_vid = str(Path('.').resolve() / 'out' / 'tmp_inpaint_noaudio.mp4')
    ensure_out_dir(Path(tmp_vid))
    cap = cv2.VideoCapture(infile)
    if not cap.isOpened():
        raise SystemExit('failed to open video')
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(tmp_vid, fourcc, fps, (W, H))
    x, y, w, h = adjust_box_to_frame(box, W, H)
    mask = np.zeros((H, W), dtype='uint8')
    mask[y:y+h, x:x+w] = 255
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # inpaint requires 8-bit 1-channel mask
        try:
            out = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        except Exception:
            out = frame
        writer.write(out)
        frame_idx += 1
    cap.release()
    writer.release()
    # copy audio from infile to outfile using ffmpeg
    cmd = [ffmpeg, '-y', '-i', tmp_vid, '-i', infile, '-c:v',
           'copy', '-map', '0:v:0', '-map', '1:a:0?', outfile]
    run_ffmpeg_cmd(cmd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        '--mode', choices=['delogo', 'fill', 'inpaint'], default='delogo')
    p.add_argument(
        '--input', '-i',
        default=str(Path('.').resolve() / 'assets' / 'entry.mp4')
    )
    p.add_argument(
        '--output', '-o',
        default=str(Path('.').resolve() / 'out' / 'entry_removed.mp4')
    )
    p.add_argument('--box', type=parse_box, required=True, help='x,y,w,h')
    p.add_argument('--ffmpeg', default=str(Path('.').resolve() /
                   'FFmpeg' / 'ffmpeg.exe'), help='path to ffmpeg executable')
    args = p.parse_args()

    infile = args.input
    outfile = args.output
    box = args.box
    ffmpeg = args.ffmpeg

    ensure_out_dir(Path(outfile))

    if args.mode == 'delogo':
        mode_delogo(ffmpeg, infile, outfile, box)
    elif args.mode == 'fill':
        mode_fill(ffmpeg, infile, outfile, box)
    elif args.mode == 'inpaint':
        mode_inpaint(ffmpeg, infile, outfile, box)


if __name__ == '__main__':
    main()
