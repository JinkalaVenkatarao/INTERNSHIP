"""
VisionAI Flask App — Lightweight Object Detection Server
Runs with just Flask + OpenCV. No heavy ML frameworks needed.
"""

import os
import json
import time
from flask import Flask, render_template, request, jsonify
from src.detector import detect_objects, get_available_detectors

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max upload

# ── Simple in-memory stats ────────────────────────────────────────────────────
stats = {
    "total_requests": 0,
    "total_detections": 0,
    "total_errors": 0,
    "start_time": time.time(),
    "recent": [],          # last 20 requests
    "class_counts": {},
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main dashboard."""
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    """Main detection endpoint — accepts image upload."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": f"Unsupported file type. Use: JPG, PNG, BMP, WebP"}), 400

    # Get selected detectors from form
    selected_raw = request.form.get("detectors", "")
    selected = [d.strip() for d in selected_raw.split(",") if d.strip()] or None

    try:
        image_bytes = file.read()
        result = detect_objects(image_bytes, selected=selected)

        # Update stats
        stats["total_requests"] += 1
        stats["total_detections"] += result["count"]
        for cls, cnt in result["summary"].items():
            stats["class_counts"][cls] = stats["class_counts"].get(cls, 0) + cnt

        stats["recent"].append({
            "file": file.filename,
            "count": result["count"],
            "ms": result["inference_ms"],
            "time": time.strftime("%H:%M:%S"),
        })
        stats["recent"] = stats["recent"][-20:]  # keep last 20

        return jsonify(result)

    except Exception as e:
        stats["total_errors"] += 1
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    uptime = int(time.time() - stats["start_time"])
    h = uptime // 3600
    m = (uptime % 3600) // 60
    s = uptime % 60
    return jsonify({
        "status": "running",
        "uptime": f"{h}h {m}m {s}s",
        "detectors": get_available_detectors(),
    })


@app.route("/stats")
def get_stats():
    """Return monitoring stats for the dashboard."""
    uptime = int(time.time() - stats["start_time"])
    top_classes = sorted(stats["class_counts"].items(), key=lambda x: x[1], reverse=True)[:8]
    return jsonify({
        "total_requests": stats["total_requests"],
        "total_detections": stats["total_detections"],
        "total_errors": stats["total_errors"],
        "uptime_seconds": uptime,
        "uptime_human": f"{uptime//3600}h {(uptime%3600)//60}m {uptime%60}s",
        "top_classes": [{"name": k, "count": v} for k, v in top_classes],
        "recent": list(reversed(stats["recent"])),
    })


@app.route("/detectors")
def list_detectors():
    """List available detection types."""
    return jsonify({"detectors": get_available_detectors()})


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  VisionAI Object Detection Server")
    print("  Open browser: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

# cd vision-project
# venv\Scripts\activate
# python app.py
# http://localhost:5000