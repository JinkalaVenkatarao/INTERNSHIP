# VisionAI — Lightweight Object Detection

A simple, fast object detection web app using **OpenCV** and **Flask**.
No PyTorch. No heavy downloads. Works on any laptop.

---

## What It Detects
- Faces (frontal)
- Eyes
- Full Body
- Upper Body
- Smiles
- Cars

---

## Setup (One Time Only)

```
1. Open Command Prompt in this folder
2. python -m venv venv
3. venv\Scripts\activate
4. pip install -r requirements.txt
5. python app.py
6. Open browser → http://localhost:5000
```

---

## Start Every Time

```
venv\Scripts\activate
python app.py
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | /detect | Upload image, get detections |
| GET | /health | Server status |
| GET | /stats | Usage metrics |
| GET | /detectors | Available detectors |
