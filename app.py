from flask import Flask, request, render_template, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from circle_processor import StixisProcessor

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_image():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

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
            image_path=filepath,
            grid_size=grid_size,
            smoothing=use_smoothing,
            smoothing_sigma=smoothing_sigma,
            enhance_contrast=enhance_contrast,
            output_dir=app.config['UPLOAD_FOLDER']
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 