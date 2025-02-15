from flask import Flask, request, render_template, send_file, jsonify, abort, url_for
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from stixis_processor import StixisProcessor
from PIL import Image  # Use PIL instead of imghdr
from image_handler import ImageHandler
import time

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
        return jsonify({'error': "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': "No selected file"}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({'error': "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    save_path = UPLOAD_FOLDER / filename
    output_path = None
    
    try:
        # Validate file is actually an image
        print(f"Validating image: {filename}")
        file_ext = validate_image(file.stream)
        if not file_ext:
            return jsonify({'error': "Invalid image file"}), 400

        print(f"Saving file to: {save_path}")
        file.save(save_path)

        # Get parameters from form
        invert = request.form.get('invert') == 'true'
        print(f"Invert parameter received: {request.form.get('invert')}")
        print(f"Invert parameter parsed: {invert}")
        
        num_colors = int(request.form.get('num_colors', 5))
        use_custom_grid = request.form.get('use_custom_grid') == 'true'
        grid_size = int(request.form.get('grid_size', 0)) if use_custom_grid else None
        use_smoothing = request.form.get('use_smoothing') == 'true'
        smoothing_sigma = float(request.form.get('smoothing_sigma', 1.5))
        enhance_contrast = request.form.get('enhance_contrast') == 'true'
        
        brightness_mapping = request.form.get('brightness_mapping', 'linear')
        gamma = float(request.form.get('gamma', 2.2))
        
        print(f"Creating processor with parameters:")
        print(f"- num_colors: {num_colors}")
        print(f"- grid_size: {grid_size}")
        print(f"- smoothing: {use_smoothing}")
        print(f"- smoothing_sigma: {smoothing_sigma}")
        print(f"- enhance_contrast: {enhance_contrast}")
        print(f"- invert: {invert}")
        print(f"- brightness_mapping: {brightness_mapping}")
        print(f"- gamma: {gamma}")
        
        # Initialize processor with parameters
        processor = StixisProcessor(
            num_colors=num_colors,
            grid_size=grid_size,
            smoothing=use_smoothing,
            smoothing_sigma=smoothing_sigma,
            enhance_contrast=enhance_contrast,
            invert=invert,
            brightness_mapping=brightness_mapping,
            gamma=gamma
        )
        
        print(f"Processor created with invert={processor.invert}")
        
        # Process image
        try:
            print("Loading and processing image")
            input_image = Image.open(save_path)
            output_image = processor.process(input_image)
            
            # Save the processed image
            output_filename = f"processed_{filename}"
            output_path = UPLOAD_FOLDER / output_filename
            output_image.save(output_path)
            
            print(f"Processing complete, output at: {output_path}")
            
            # Clean up input file early
            if save_path.exists():
                save_path.unlink()
            
            # Return response based on Accept header
            if request.headers.get('Accept') == 'application/json':
                download_url = url_for('download_file', 
                                     filename=output_filename, 
                                     _external=True)
                return jsonify({
                    'status': 'success',
                    'message': 'Image processed successfully',
                    'download_url': download_url
                }), 200
            
            # Browser request - return image directly
            return send_file(output_path, mimetype='image/jpeg')
            
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return jsonify({'error': f"Error processing image: {str(e)}"}), 500

    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': f"General error: {str(e)}"}), 500
        
    finally:
        # Only clean up input file if it still exists
        if save_path and save_path.exists():
            try:
                save_path.unlink()
            except Exception as e:
                print(f"Cleanup error: {str(e)}")

# Add cleanup schedule for processed files
def cleanup_old_files():
    """Clean up files older than 1 hour"""
    current_time = time.time()
    for file_path in UPLOAD_FOLDER.glob('processed_*'):
        if current_time - file_path.stat().st_mtime > 3600:  # 1 hour
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Cleanup error for {file_path}: {str(e)}")

@app.route('/download/<filename>')
def download_file(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': "Invalid filename"}), 404
    
    try:
        file_path = UPLOAD_FOLDER / secure_filename(filename)
        if not file_path.exists():
            return jsonify({'error': "File not found"}), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f"Error downloading file: {str(e)}"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Change port to 8000 