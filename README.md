# Stixis - Circle Pattern Generator

Stixis is a Python-based image processing tool that transforms images into artistic circle patterns. It offers both a web interface and command-line functionality.

## Features

### Basic Controls
- Adjustable number of colors/divisions
- Custom grid size option
- Smoothing with adjustable sigma
- Contrast enhancement
- Color inversion (black/white background toggle)

### Advanced Features
- Multiple brightness mapping modes:
  - Linear (default)
  - Logarithmic (better for dark details)
  - Exponential (emphasizes bright areas)
  - Sigmoid (smooth transition)
  - Power/Gamma (traditional photo correction)
  - Adaptive (context-aware)
- Color processing mode:
  - Extracts dominant colors from the image
  - Adjustable color palette size (4-16 colors)
  - Maintains image color scheme in circle patterns

### Processing Modes
1. **Grayscale (Classic)**
   - Black and white circle patterns
   - Configurable brightness mapping
   - Traditional dot pattern style

2. **Color (Experimental)**
   - Color-aware circle patterns
   - Automatic color palette extraction
   - Preserves image color themes

## Installation

```bash
git clone https://github.com/yourusername/stixis.git
cd stixis
pip install -r requirements.txt
```

## Usage

### Web Interface
```bash
python app.py
```
Then open `http://localhost:8000` in your browser.

### Command Line
```bash
python main.py --input image.jpg --output result.jpg
```

#### Command Line Options
```
--input          Input image path
--output         Output image path
--num-colors     Number of colors/divisions (default: 5)
--grid-size      Custom grid size (optional)
--smoothing      Enable smoothing
--sigma          Smoothing sigma value (default: 1.0)
--contrast       Enable contrast enhancement
--invert         Invert colors (white background)
--mode           Processing mode (grayscale/color)
--palette-size   Number of colors in palette (color mode only)
--mapping        Brightness mapping mode
--gamma          Gamma value for power mapping
```

## API Usage

The service can be accessed via HTTP API:

```bash
curl -X POST http://localhost:8000/process \
    -F "file=@image.jpg" \
    -F "num_colors=5" \
    -F "use_custom_grid=true" \
    -F "grid_size=16" \
    -F "use_smoothing=true" \
    -F "smoothing_sigma=1.5" \
    -F "enhance_contrast=true" \
    -F "invert=false" \
    -F "processor_mode=color" \
    -F "color_palette_size=8" \
    -F "brightness_mapping=linear" \
    -H "Accept: application/json"
```

## Examples

[Include some example images showing different processing modes and settings]

