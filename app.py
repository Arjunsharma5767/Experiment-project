import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Utility
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Image Processing Functions
def denoise_image(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

def enhance_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_eq = cv2.equalizeHist(l)
    lab_eq = cv2.merge((l_eq, a, b))
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)

def ohrc(image):
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)

def process_image(input_path, output_path):
    original = cv2.imread(input_path)
    denoised = denoise_image(original)
    enhanced = enhance_contrast(denoised)
    final = ohrc(enhanced)
    cv2.imwrite(output_path, final)
    return original, denoised, enhanced, final

def stitch_images(images):
    stitcher = cv2.Stitcher_create() if hasattr(cv2, 'Stitcher_create') else cv2.createStitcher()
    status, stitched = stitcher.stitch(images)
    return stitched if status == cv2.Stitcher_OK else None

# HTML Templates
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>ISRO Image Processor</title>
    <style>{{ style }}</style>
</head>
<body>
    <div class="container">
        <h1>ISRO Satellite Image Processor</h1>
        <form action="/process" method="post" enctype="multipart/form-data">
            <div class="upload-box">
                <input type="file" name="files" id="file-input" multiple>
                <label for="file-input">Choose Satellite Images</label>
                <span id="file-count">0 files selected</span>
            </div>
            <button type="submit">Process Images</button>
        </form>
    </div>
    <script>
        const fileInput = document.getElementById('file-input');
        const fileCount = document.getElementById('file-count');
        fileInput.addEventListener('change', () => {
            fileCount.textContent = `${fileInput.files.length} files selected`;
        });
    </script>
</body>
</html>
"""

results_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Processing Results</title>
    <style>{{ style }}</style>
</head>
<body>
    <div class="container">
        <h1>Processing Results</h1>

        <div class="results-section">
            <h2>Statistics</h2>
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Original Mean</th>
                    <th>Denoised Mean</th>
                    <th>Enhanced Mean</th>
                    <th>OHRC Mean</th>
                </tr>
                {% for stat in stats %}
                <tr>
                    <td>{{ stat.filename }}</td>
                    <td>{{ "%.2f"|format(stat.original_mean) }}</td>
                    <td>{{ "%.2f"|format(stat.denoised_mean) }}</td>
                    <td>{{ "%.2f"|format(stat.enhanced_mean) }}</td>
                    <td>{{ "%.2f"|format(stat.ohrc_mean) }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        {% if stitched %}
        <div class="results-section">
            <h2>Stitched Panorama</h2>
            <img src="{{ url_for('serve_processed', timestamp=timestamp, filename='panorama.jpg') }}" 
                 alt="Stitched Image" class="result-image">
        </div>
        {% endif %}

        <div class="results-section">
            <h2>Processed Images</h2>
            <div class="image-grid">
                {% for stat in stats %}
                <div class="image-card">
                    <img src="{{ url_for('serve_processed', timestamp=timestamp, filename='processed_' + stat.filename) }}" 
                         alt="Processed {{ stat.filename }}">
                    <div class="image-info">{{ stat.filename }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""

style_css = """
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f0f2f5;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
h1 {
    color: #1a237e;
    text-align: center;
    margin-bottom: 30px;
}
.upload-box {
    border: 2px dashed #3f51b5;
    padding: 40px;
    text-align: center;
    margin: 20px 0;
    border-radius: 8px;
}
button {
    background: #3f51b5;
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    width: 100%;
    transition: background 0.3s;
}
button:hover {
    background: #303f9f;
}
.results-section {
    margin: 30px 0;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
}
.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}
.image-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.image-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}
.image-info {
    padding: 10px;
    text-align: center;
    background: #f8f9fa;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}
th {
    background-color: #3f51b5;
    color: white;
}
.result-image {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin-top: 15px;
}
"""

# Routes
@app.route('/')
def index():
    return render_template_string(index_html, style=style_css)

@app.route('/process', methods=['POST'])
def process_images():
    if 'files' not in request.files:
        return "No files uploaded", 400
    
    files = request.files.getlist('files')
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    session_folder = os.path.join(app.config['PROCESSED_FOLDER'], timestamp)
    os.makedirs(session_folder, exist_ok=True)

    processed_images = []
    stats = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)
            
            output_path = os.path.join(session_folder, f"processed_{filename}")
            original, denoised, enhanced, ohrc_img = process_image(input_path, output_path)

            stats.append({
                'filename': filename,
                'original_mean': np.mean(original),
                'denoised_mean': np.mean(denoised),
                'enhanced_mean': np.mean(enhanced),
                'ohrc_mean': np.mean(ohrc_img)
            })
            processed_images.append(output_path)

    stitched_image = None
    if len(processed_images) > 1:
        images = [cv2.imread(img) for img in processed_images]
        stitched_image = stitch_images(images)
        if stitched_image is not None:
            cv2.imwrite(os.path.join(session_folder, 'panorama.jpg'), stitched_image)

    return render_template_string(results_html,
                                  style=style_css,
                                  timestamp=timestamp,
                                  stats=stats,
                                  stitched=stitched_image is not None)

@app.route('/processed/<timestamp>/<filename>')
def serve_processed(timestamp, filename):
    return send_from_directory(os.path.join(app.config['PROCESSED_FOLDER'], timestamp), filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
