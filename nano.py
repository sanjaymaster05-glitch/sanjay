from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return send_from_directory(STATIC_FOLDER, "index.html")

def smart_detect(file_path, filename):
    """
    AI/Real detection based on filename keywords, resolution, and basic heuristics.
    Rules:
    1. AI keywords → AI
    2. Screenshot / WhatsApp / human / animal / normal places → Real
    3. PDFs / scanned documents → AI
    4. High-resolution foreign/island → AI
    5. Fallback: image size / area heuristic
    """
    filename_lower = filename.lower()
    img = Image.open(file_path)
    width, height = img.size

    ai_keywords = ["ai", "generated", "midjourney", "stable diffusion", "robot", "fake", "render", "cgi"]
    real_keywords = ["screenshot", "whatsapp", "marksheet", "id", "card", "human", "animal", "dog", "cat", "place", "beach", "mountain"]

    # 1️⃣ AI keywords in filename → AI
    if any(word in filename_lower for word in ai_keywords):
        return 100, "AI-Generated"

    # 2️⃣ Real keywords → Real
    if any(word in filename_lower for word in real_keywords):
        return 0, "Real Image"

    # 3️⃣ PDFs / scanned documents → AI
    if filename_lower.endswith(".pdf") or "scan" in filename_lower or "document" in filename_lower:
        return 100, "AI-Generated"

    # 4️⃣ High-resolution foreign/island → AI
    if width > 3500 and height > 2500:
        return 90, "AI-Generated"

    # 5️⃣ Fallback: image area & file size heuristic
    size = os.path.getsize(file_path)
    area = width * height
    score = 0
    if area > 5000000 or area < 200000:
        score += 30
    if size < 60000:
        score += 40
    if size > 5000000:
        score += 20
    if width / height > 2 or height / width > 2:
        score += 10
    score = min(100, score)

    if score < 40:
        result = "Real Image"
    elif score < 70:
        result = "Possibly AI-Generated"
    else:
        result = "AI-Generated"

    return score, result

@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    score, result = smart_detect(filepath, file.filename)

    return jsonify({"score": score, "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

