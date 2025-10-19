from PIL import Image, ImageDraw
import os

in_path = os.path.abspath(r"C:\Projects\en_words\assets\entry_frame.png")
out_path = os.path.abspath(
    r"C:\Projects\en_words\assets\entry_frame_logo_adjusted.png")

# box provided by user (updated y -> 900)
box = (1368, 995, 250, 75)  # x, y, w, h


def main():
    if not os.path.exists(in_path):
        raise SystemExit(f"input not found: {in_path}")
    # load with OpenCV for color operations
    import cv2
    import numpy as np

    img_bgr = cv2.imread(in_path)
    if img_bgr is None:
        raise SystemExit(f"failed to read with OpenCV: {in_path}")

    H, W = img_bgr.shape[:2]

    # sample area: bottom quarter of the image to find the ground green
    y_start = int(H * 0.7)
    roi = img_bgr[y_start:H, 0:W]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # green-ish range (tunable)
    lower_green = np.array([30, 40, 30])
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # if mask has enough pixels, compute median on masked area, else fallback to median of roi
    if cv2.countNonZero(mask) > 50:
        # get BGR pixels where mask is true
        vals = roi[mask > 0]
        med_bgr = np.median(vals, axis=0).astype(int)
    else:
        med_bgr = np.median(roi.reshape(-1, 3), axis=0).astype(int)

    fill_color = tuple(int(c) for c in med_bgr.tolist())  # B, G, R
    # convert to RGB for PIL
    fill_rgb = (fill_color[2], fill_color[1], fill_color[0])

    # draw filled rectangle on PIL image
    pil = Image.open(in_path).convert("RGBA")
    draw = ImageDraw.Draw(pil)
    x, y, w, h = box
    draw.rectangle([x, y, x + w, y + h], fill=fill_rgb + (255,))
    pil.save(out_path)
    print('wrote', out_path)
    print('used fill RGB:', fill_rgb)


if __name__ == '__main__':
    main()
