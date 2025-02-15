from flask import Flask, request, render_template, send_file, jsonify, abort, url_for
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from stixis_processor import StixisProcessor
from PIL import Image  # Use PIL instead of imghdr
from image_handler import ImageHandler

app = Flask(__name__)

# Configure upload folder with absolute path
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure folders exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(stream):
    """Validate image using PIL instead of imghdr"""
    try:
        image = Image.open(stream)
        image.verify()  # Verify it's actually an image
        stream.seek(0)  # Reset stream position
        return '.' + (image.format.lower() if image.format != 'JPEG' else 'jpg')
    except Exception:
        return None

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
    save_path = UPLOAD_FOLDER / filename
    
    try:
        # Validate file is actually an image
        print(f"Validating image: {filename}")  # Debug log
        file_ext = validate_image(file.stream)
        if not file_ext:
            abort(400, description="Invalid image file")

        print(f"Saving file to: {save_path}")  # Debug log
        file.save(save_path)

        # Get parameters from form/request
        try:
            print("Processing form parameters")  # Debug log
            num_colors = int(request.form.get('num_colors', 5))
            if not 2 <= num_colors <= 10:
                abort(400, description="Number of colors must be between 2 and 10")

            use_custom_grid = request.form.get('use_custom_grid') == 'true'
            grid_size = None
            if use_custom_grid:
                grid_size = int(request.form.get('grid_size', 0))
                if grid_size < 4:
                    abort(400, description="Grid size must be at least 4")

            use_smoothing = request.form.get('use_smoothing') == 'true'
            smoothing_sigma = float(request.form.get('smoothing_sigma', 1.5))
            if use_smoothing and not 0.5 <= smoothing_sigma <= 3.0:
                abort(400, description="Smoothing sigma must be between 0.5 and 3.0")

            enhance_contrast = request.form.get('enhance_contrast') == 'true'
            
            print(f"Parameters: colors={num_colors}, grid={grid_size}, "
                  f"smooth={use_smoothing}, sigma={smoothing_sigma}, "
                  f"contrast={enhance_contrast}")  # Debug log
            
        except ValueError as e:
            print(f"Parameter error: {str(e)}")  # Debug log
            abort(400, description="Invalid parameter values")

        # Process image
        try:
            print("Initializing processor")  # Debug log
            processor = StixisProcessor(
                num_colors=num_colors,
                grid_size=grid_size,
                smoothing=use_smoothing,
                smoothing_sigma=smoothing_sigma,
                enhance_contrast=enhance_contrast
            )
            
            print("Loading and processing image")  # Debug log
            input_image = Image.open(save_path)
            output_image = processor.process(input_image)
            
            # Save the processed image
            output_filename = f"processed_{filename}"
            output_path = UPLOAD_FOLDER / output_filename
            output_image.save(output_path)
            processor.output_path = output_path
            
            print(f"Processing complete, output at: {output_path}")  # Debug log
            
        except Exception as e:
            print(f"Processing error: {str(e)}")  # Debug log
            abort(500, description=f"Error processing image: {str(e)}")

        # Return processed image
        try:
            # Check if request is from API (Accept: application/json)
            if request.headers.get('Accept') == 'application/json':
                download_url = url_for('download_file', 
                                     filename=output_filename, 
                                     _external=True)
                return jsonify({
                    'message': 'Image processed successfully',
                    'download_url': download_url
                })
            
            # Browser request - return image directly
            return send_file(processor.output_path, mimetype='image/jpeg')
            
        except Exception as e:
            print(f"Response error: {str(e)}")  # Debug log
            abort(500, description=f"Error sending response: {str(e)}")

    except Exception as e:
        print(f"General error: {str(e)}")  # Debug log
        abort(500, description=f"General error: {str(e)}")
        
    finally:
        # Clean up uploaded file
        try:
            if save_path.exists():
                save_path.unlink()
        except Exception as e:
            print(f"Cleanup error: {str(e)}")  # Debug log

# Secure file download
@app.route('/download/<filename>')
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    try:
        return send_file(
            UPLOAD_FOLDER / secure_filename(filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception:
        abort(404)

if __name__ == '__main__':
    # In production, use proper WSGI server and don't run in debug mode
    app.run(debug=True) 