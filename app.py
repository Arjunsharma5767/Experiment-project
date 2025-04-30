import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

# ========== Memory-Optimized Processing ==========
def resize_image(img):
    max_dim = 1200  # Reduced max dimension
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        return cv2.resize(img, (int(w*scale), int(h*scale)))
    return img

def denoise_image(image):
    # Lighter denoising parameters
    return cv2.fastNlMeansDenoisingColored(image, None, h=3, 
                                        templateWindowSize=3, 
                                        searchWindowSize=7)

def enhance_contrast(image):
    # Simplified contrast enhancement
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
    return cv2.cvtColor(cv2.merge((clahe.apply(l), a, b)), cv2.COLOR_LAB2BGR)

def process_image(input_path, output_path):
    # Read image in low-memory mode
    original = cv2.imread(input_path, cv2.IMREAD_REDUCED_COLOR_2)
    
    # Resize if larger than 1024px
    h, w = original.shape[:2]
    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        original = cv2.resize(original, (int(w*scale), int(h*scale)))
    
    # Sequential processing with cleanup
    denoised = denoise_image(original)
    del original
    
    enhanced = enhance_contrast(denoised)
    del denoised
    
    cv2.imwrite(output_path, enhanced)
    return enhanced

def stitch_images(images):
    # Limited stitching capability
    if len(images) > 5:
        return None  # Don't process too many images
    
    stitcher = cv2.Stitcher_create()
    status, stitched = stitcher.stitch(images)
    return stitched if status == cv2.Stitcher_OK else None

# ========== Web Routes ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML.replace("{{ CSS }}", CSS))

@app.route('/process', methods=['POST'])
def process_images():
    try:
        files = request.files.getlist('files')
        if len(files) > 5:
            return "Maximum 5 images allowed on free tier", 400

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_folder = os.path.join(app.config['PROCESSED_FOLDER'], timestamp)
        os.makedirs(session_folder, exist_ok=True)

        processed = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(input_path)
                
                output_path = os.path.join(session_folder, f"proc_{filename}")
                process_image(input_path, output_path)
                os.remove(input_path)  # Immediate cleanup
                processed.append(output_path)

        # Limited stitching for 2-5 images
        stitched = None
        if 2 <= len(processed) <= 5:
            images = [cv2.imread(p) for p in processed]
            stitched = stitch_images(images)
            if stitched is not None:
                cv2.imwrite(os.path.join(session_folder, 'panorama.jpg'), stitched)

        return render_template_string(
            RESULTS_HTML.replace("{{ CSS }}", CSS),
            timestamp=timestamp,
            count=len(processed),
            stitched=stitched is not None
        )

    except MemoryError:
        return "Memory limit exceeded - try smaller images", 413
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/processed/<timestamp>/<filename>')
def serve_processed(timestamp, filename):
    path = os.path.join(app.config['PROCESSED_FOLDER'], timestamp)
    return send_from_directory(path, filename)

# ========== Templates & CSS ==========
CSS = """/* same styles as before */"""

INDEX_HTML = """<!-- simplified upload form -->"""

RESULTS_HTML = """<!-- simplified results display -->"""

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
