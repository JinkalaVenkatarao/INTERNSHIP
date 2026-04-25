"""
Object Detector using OpenCV Haar Cascades.
No downloads needed — cascade files are built into OpenCV.
Detects: faces, eyes, full body, upper body, cars, smiles.
"""

import cv2
import numpy as np
import base64
import time
from io import BytesIO
from PIL import Image


# ── Colors for each detector type ────────────────────────────────────────────
COLORS = {
    "Face":       (255, 99,  71),
    "Eyes":       (30,  144, 255),
    "Full Body":  (50,  205, 50),
    "Upper Body": (255, 165, 0),
    "Smile":      (238, 130, 238),
    "Car":        (0,   206, 209),
}

# ── Load built-in OpenCV cascade classifiers ─────────────────────────────────
def load_cascades():
    cascades = {}
    cascade_files = {
        "Face":       "haarcascade_frontalface_default.xml",
        "Eyes":       "haarcascade_eye.xml",
        "Full Body":  "haarcascade_fullbody.xml",
        "Upper Body": "haarcascade_upperbody.xml",
        "Smile":      "haarcascade_smile.xml",
        "Car":        "haarcascade_car.xml",
    }
    base_path = cv2.data.haarcascades
    for name, filename in cascade_files.items():
        path = base_path + filename
        cascade = cv2.CascadeClassifier(path)
        if not cascade.empty():
            cascades[name] = cascade
    return cascades


# Load once at module level
CASCADES = load_cascades()


def detect_objects(image_bytes: bytes, selected: list = None) -> dict:
    """
    Run detection on uploaded image bytes.

    Args:
        image_bytes: Raw image file bytes
        selected: List of detector names to run. None = run all.

    Returns:
        dict with detections, annotated image (base64), stats
    """
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Cannot read image. Please upload JPG or PNG.")

    # Resize if too large (keeps it fast)
    h, w = img.shape[:2]
    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)  # Improve contrast for better detection

    if selected is None:
        selected = list(CASCADES.keys())

    start = time.perf_counter()
    all_detections = []
    output_img = img.copy()

    for name in selected:
        if name not in CASCADES:
            continue

        cascade = CASCADES[name]
        color = COLORS.get(name, (255, 255, 0))

        # Tune parameters per detector type
        if name == "Face":
            objects = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        elif name == "Eyes":
            objects = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(20, 20))
        elif name == "Smile":
            objects = cascade.detectMultiScale(gray, scaleFactor=1.7, minNeighbors=22, minSize=(25, 25))
        elif name == "Car":
            objects = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(60, 60))
        else:
            objects = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(50, 50))

        if len(objects) == 0:
            continue

        for (x, y, bw, bh) in objects:
            # Draw filled semi-transparent rectangle
            overlay = output_img.copy()
            cv2.rectangle(overlay, (x, y), (x + bw, y + bh), color, -1)
            cv2.addWeighted(overlay, 0.15, output_img, 0.85, 0, output_img)

            # Draw border
            cv2.rectangle(output_img, (x, y), (x + bw, y + bh), color, 2)

            # Draw label background
            label = name
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
            label_y = max(y - 5, th + 5)
            cv2.rectangle(output_img, (x, label_y - th - 6), (x + tw + 8, label_y + 2), color, -1)
            cv2.putText(output_img, label, (x + 4, label_y - 2), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

            all_detections.append({
                "label": name,
                "bbox": {"x": int(x), "y": int(y), "w": int(bw), "h": int(bh)},
            })

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    # Count per class
    summary = {}
    for det in all_detections:
        summary[det["label"]] = summary.get(det["label"], 0) + 1

    # Encode annotated image to base64
    output_rgb = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
    pil_out = Image.fromarray(output_rgb)
    buf = BytesIO()
    pil_out.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "success": True,
        "count": len(all_detections),
        "detections": all_detections,
        "summary": summary,
        "inference_ms": elapsed_ms,
        "image_size": {"width": w, "height": h},
        "annotated_image": f"data:image/jpeg;base64,{b64}",
    }


def get_available_detectors() -> list:
    """Return names of loaded cascade classifiers."""
    return list(CASCADES.keys())
