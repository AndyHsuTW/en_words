from PIL import Image, ImageDraw
import cv2
import numpy as np
import os


in_path = os.path.abspath(r"C:\Projects\en_words\assets\entry_frame.png")
out_annot = os.path.abspath(
    r"C:\Projects\en_words\assets\entry_frame_annotated.png")


def main():
    img = cv2.imread(in_path)
    if img is None:
        raise SystemExit(f"failed to read {in_path}")

    h, w = img.shape[:2]
    print("image size", w, h)

    # focus on bottom-right quadrant to speed and avoid false positives
    x0 = int(w * 0.5)
    y0 = int(h * 0.5)
    roi = img[y0:h, x0:w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # high-pass-ish: emphasize text/logo edges
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    lap = cv2.Laplacian(blur, cv2.CV_8U)
    _, th = cv2.threshold(lap, 20, 255, cv2.THRESH_BINARY)

    # dilate to join characters
    kernel = np.ones((5, 5), np.uint8)
    d = cv2.dilate(th, kernel, iterations=2)

    contours, _ = cv2.findContours(
        d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for c in contours:
        x, y, ww, hh = cv2.boundingRect(c)
        area = ww * hh
        if area < 100:
            # skip tiny bits
            continue
        # filter shapes that are too tall / too wide
        if ww < 20 or hh < 8:
            continue
        candidates.append((x + x0, y + y0, ww, hh, area))

    # sort by area descending
    candidates = sorted(candidates, key=lambda x: -x[4])
    print("candidates:", candidates[:5])

    # annotate on PIL image
    pil = Image.open(in_path).convert("RGBA")
    draw = ImageDraw.Draw(pil)
    for (x, y, ww, hh, area) in candidates[:5]:
        draw.rectangle([x, y, x + ww, y + hh],
                       outline=(255, 0, 0, 255), width=3)

    pil.save(out_annot)
    print("wrote", out_annot)

    # suggest a delogo box: take union of candidates or fallback to a bottom-right guess
    if candidates:
        top3 = candidates[:3]
        minx = min(x for x, _, _, _, _ in top3)
        miny = min(y for _, y, _, _, _ in top3)
        maxx = max(x + ww for x, _, ww, _, _ in top3)
        maxy = max(y + hh for _, y, _, hh, _ in top3)
        print(
            "suggested box (x,y,w,h):",
            minx,
            miny,
            maxx - minx,
            maxy - miny,
        )
    else:
        # fallback 200x80 box anchored to bottom-right with 20px margin
        bw = 200
        bh = 80
        mx = w - 20 - bw
        my = h - 20 - bh
        print(
            "fallback suggested box (x,y,w,h):",
            mx,
            my,
            bw,
            bh,
        )


if __name__ == "__main__":
    main()
