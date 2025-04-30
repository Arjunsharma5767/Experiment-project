from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import os
from io import BytesIO
from PIL import Image

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image Pencil Sketch</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 2rem;
            background-color: #f0f2f5;
        }
        .container {
            max-width: 600px;
        }
        img {
            max-width: 100%;
            margin-top: 1rem;
            border: 1px solid #ccc;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container text-center">
        <h1 class="mb-4">🖼️ Image to Pencil Sketch</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="image" class="form-control mb-3" required>
            <button type="submit" class="btn btn-primary">Convert to Sketch</button>
        </form>
        {% if sketch_url %}
            <h3 class="mt-4">Sketch Result</h3>
            <img src="{{ sketch_url }}" alt="Sketch">
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    sketch_url = None
    if request.method == "POST":
        file = request.files["image"]
        if file:
            # Read image as OpenCV format
            in_memory_file = BytesIO()
            file.save(in_memory_file)
            in_memory_file.seek(0)
            file_bytes = np.frombuffer(in_memory_file.read(), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # Convert to sketch
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            inv = 255 - gray
            blur = cv2.GaussianBlur(inv, (21, 21), 0)
            sketch = cv2.divide(gray, 255 - blur, scale=256.0)

            # Encode to PNG
            _, buffer = cv2.imencode('.png', sketch)
            img_bytes = BytesIO(buffer.tobytes())
            img_bytes.seek(0)

            return send_file(img_bytes, mimetype='image/png')

    return render_template_string(HTML_TEMPLATE, sketch_url=sketch_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
