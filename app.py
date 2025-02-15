from flask import Flask, request, render_template, send_file, jsonify, abort
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from circle_processor import StixisProcessor
import imghdr

app = Flask(__name__)

# Configure upload folder with absolute path
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure upload folder exists
UPLOAD_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format if format != 'jpeg' else '.jpg'

@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        abort(400, description="No file part")
    
    file = request.files['file']
    if file.filename == '':
        abort(400, description="No selected file")

    if not file or not allowed_file(file.filename):
        abort(400, description="Invalid file type")

    filename = secure_filename(file.filename)
    
    # Validate file is actually an image
    file_ext = validate_image(file.stream)
    if not file_ext:
        abort(400, description="Invalid image file")

    # Create safe path for saving
    save_path = UPLOAD_FOLDER / filename
    
    try:
        file.save(save_path)

        # Get parameters from form/request
        num_colors = int(request.form.get('num_colors', 5))
        use_custom_grid = request.form.get('use_custom_grid') == 'true'
        grid_size = int(request.form.get('grid_size', 0)) if use_custom_grid else None
        use_smoothing = request.form.get('use_smoothing') == 'true'
        smoothing_sigma = float(request.form.get('smoothing_sigma', 1.5))
        enhance_contrast = request.form.get('enhance_contrast') == 'true'

        # Process image
        processor = StixisProcessor(
            num_colors=num_colors,
            image_path=save_path,
            grid_size=grid_size,
            smoothing=use_smoothing,
            smoothing_sigma=smoothing_sigma,
            enhance_contrast=enhance_contrast,
            output_dir=UPLOAD_FOLDER
        )
        
        processor.run()
        
        # Return processed image
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'message': 'Image processed successfully',
                'output_path': processor.output_path
            })
        
        return send_file(processor.output_path, mimetype='image/jpeg')

    except Exception as e:
        # Log the error properly in production
        abort(500, description="Error processing image")
    finally:
        # Clean up uploaded file
        if save_path.exists():
            save_path.unlink()

# Secure file download
@app.route('/download/<filename>')
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    try:
        return send_file(
            UPLOAD_FOLDER / secure_filename(filename),
            as_attachment=True
        )
    except Exception:
        abort(404)

if __name__ == '__main__':
    # In production, use proper WSGI server and don't run in debug mode
    app.run(debug=False) 