# stixis

A versatile image processing tool that transforms photographs into stunning circular pattern artworks. Stixis offers multiple interfaces including web, command-line, and API access for seamless integration into your workflow.

## Purpose

Stixis transforms regular images into artistic representations using circles of varying sizes based on the image's grayscale values. It divides the image into a grid and replaces each cell with appropriately sized circles, creating an interesting visual effect that maintains the essence of the original image while presenting it in a unique artistic style.

Key features:
- Customizable number of grayscale colors (2-10)
- Adjustable grid divisions
- Optional image smoothing
- Contrast enhancement capabilities
- Multiple interface options for different use cases

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stixis
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage Options

### 1. Command Line Interface (CLI)

Run the processor from command line:
```bash
python main.py
```

You'll be prompted to choose between:
1. TestGrid mode - tests multiple parameter combinations
2. Single process mode - process one image with specific parameters

#### Single Process Mode Options:
- Number of colors (2-10)
- Custom grid divisions (optional)
- Smoothing options (with adjustable strength)
- Contrast enhancement

#### TestGrid Mode:
Automatically tests combinations of:
- Colors: [2, 4, 6, 8, 10]
- Divisions: [4, 8, 16, 32, 50]
- Smoothing: On/Off
- Contrast: On/Off

Results are saved in a directory named after your image (e.g., `myimage_stixis_patterns/`).

### 2. Web Interface

1. Start the Flask server:
```bash
python app.py
```

2. Access the interface at: `http://localhost:5000`

Features:
- Interactive form for parameter selection
- Real-time image preview
- Automatic curl command generation
- Direct file download

### 3. API (curl)

Process images programmatically using curl:

```bash
curl -X POST http://localhost:5000/process \
  -F "file=@/path/to/your/image.jpg" \
  -F "num_colors=5" \
  -F "use_custom_grid=true" \
  -F "grid_size=8" \
  -F "use_smoothing=true" \
  -F "smoothing_sigma=1.5" \
  -F "enhance_contrast=true" \
  -H "Accept: application/json"
```

#### API Parameters

| Parameter | Type | Description | Range |
|-----------|------|-------------|--------|
| file | File | Image to process | jpg, jpeg, png |
| num_colors | int | Number of grayscale colors | 2-10 |
| use_custom_grid | bool | Enable custom grid | true/false |
| grid_size | int | Number of divisions | 4+ |
| use_smoothing | bool | Enable smoothing | true/false |
| smoothing_sigma | float | Smoothing strength | 0.5-3.0 |
| enhance_contrast | bool | Enable contrast | true/false |

## Output Files

Processed images are saved with descriptive filenames:
```
originalname_GS<colors>_DIV<divisions>_smooth_contrast.jpg
```

Components:
- `GS<colors>`: Number of grayscale colors used
- `DIV<divisions>`: Number of grid divisions
- `_smooth`: Added if smoothing was applied
- `_contrast`: Added if contrast enhancement was used

## Example Usage

### CLI Examples

1. Single Process:
```bash
python main.py
> Enter path to image file: photo.jpg
> Enter number of colors (2-10): 5
> Use custom grid? (y/n): y
> Enter grid divisions: 16
> Apply smoothing? (y/n): y
> Smoothing strength: 1.5
> Enhance contrast? (y/n): y
```

2. TestGrid Mode:
```bash
python main.py
> Run TestGrid mode? (y/n): y
> Enter path to image file: photo.jpg
# Will process all combinations automatically
```

### API Examples

1. Basic Usage:
```bash
curl -X POST http://localhost:5000/process \
  -F "file=@photo.jpg" \
  -F "num_colors=5"
```

2. Advanced Usage:
```bash
curl -X POST http://localhost:5000/process \
  -F "file=@photo.jpg" \
  -F "num_colors=8" \
  -F "use_custom_grid=true" \
  -F "grid_size=32" \
  -F "use_smoothing=true" \
  -F "smoothing_sigma=2.0" \
  -F "enhance_contrast=true" \
  -H "Accept: application/json"
```

## Project Structure

```
stixis/
├── main.py           # CLI interface
├── app.py           # Flask web server
├── stixis_processor.py  # Core processing class
├── utils.py         # Utility functions
├── requirements.txt # Dependencies
├── templates/       # Web templates
└── uploads/        # Processed images
```

## Requirements

- Python 3.6+
- Dependencies (installed via requirements.txt):
    imageio==2.37.0
    lazy_loader==0.4
    networkx==3.4.2
    numpy==2.2.3
    packaging==24.2
    pillow==11.1.0
    scikit-image==0.25.1
    scipy==1.15.1
    tifffile==2025.1.10
    flask==2.0.1
    werkzeug==2.0.1
