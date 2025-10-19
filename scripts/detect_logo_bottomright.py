from PIL import Image, ImageDraw
import cv2
import numpy as np
import os

in_path = os.path.abspath(r"C:\Projects\en_words\assets\entry_frame.png")
out_annot = os.path.abspath(
    r"C:\Projects\en_words\assets\entry_frame_logo_annotated.png")


def find_logo_box(img):
    h, w = img.shape[:2]
    # search window anchored to bottom-right (tunable)
    win_w = min(500, w)
    win_h = min(300, h)
    x0 = w - win_w
    y0 = h - win_h
    roi = img[y0:h, x0:w]

    # convert to HSV to detect green-ish and bright white
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # green-ish range (tunable) and white (low saturation, high value)
    lower_green = np.array([35, 60, 40])
    upper_green = np.array([100, 255, 255])
    mask_g = cv2.inRange(hsv, lower_green, upper_green)

    # white-ish mask
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 50, 255])
    mask_w = cv2.inRange(hsv, lower_white, upper_white)

    mask = cv2.bitwise_or(mask_g, mask_w)

    # morphological ops to clean
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # choose largest contour by area
    c = max(contours, key=cv2.contourArea)
    x, y, ww, hh = cv2.boundingRect(c)
    area = ww * hh
    # heuristics: must be reasonably sized
    if area < 200:
        return None

    # expand a bit to include borders
    pad_x = int(ww * 0.08) + 4
    pad_y = int(hh * 0.2) + 4
    x_full = max(0, x0 + x - pad_x)
    y_full = max(0, y0 + y - pad_y)
    w_full = min(w - x_full, ww + pad_x * 2)
    h_full = min(h - y_full, hh + pad_y * 2)

    return (x_full, y_full, w_full, h_full)


def main():
    img = cv2.imread(in_path)
    if img is None:
        raise SystemExit(f"failed to read {in_path}")

    box = find_logo_box(img)
    pil = Image.open(in_path).convert("RGBA")
    draw = ImageDraw.Draw(pil)
    if box:
        x, y, w, h = box
        draw.rectangle([x, y, x + w, y + h], outline=(0, 0, 255, 255), width=4)
        print("found logo box:", x, y, w, h)
    else:
        print("no logo-like region found in search window")

    pil.save(out_annot)
    print("wrote", out_annot)


if __name__ == '__main__':
    main()
