from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import exposure

class StixisProcessor:
    def __init__(self, num_colors, grid_size=None, smoothing=False, 
                 smoothing_sigma=1.0, darkness_threshold=0.1,
                 enhance_contrast=False, contrast_percentile=(2, 98), invert=False):
        """Initialize the Stixis processor with the given parameters."""
        print(f"StixisProcessor.__init__ called with invert={invert}")  # Debug log
        self.num_colors = num_colors
        self.grid_size = grid_size
        self.actual_divisions = grid_size if grid_size else num_colors
        self.smoothing = smoothing
        self.smoothing_sigma = smoothing_sigma
        self.darkness_threshold = darkness_threshold
        self.enhance_contrast = enhance_contrast
        self.contrast_percentile = contrast_percentile
        self.output_path = None
        self.invert = invert
        print(f"StixisProcessor initialized with self.invert={self.invert}")  # Debug log

    def process(self, image):
        """Process the image and create circle filter effect."""
        self.width, self.height = image.size
        
        # Handle transparency by converting transparent pixels to black
        if image.mode == 'RGBA':
            # Create a black background
            background = Image.new('RGB', image.size, (0, 0, 0))
            # Alpha composite the image over the black background
            image = Image.alpha_composite(background.convert('RGBA'), image)
        
        # Convert to grayscale
        pixels = np.array(image.convert('L'))
        
        # Apply preprocessing
        pixels = self._preprocess_image(pixels)
        
        # Create output image
        output = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(output)
        
        # Calculate grid size based on divisions
        if self.grid_size is None:
            # Default behavior based on num_colors
            self.grid_size = min(self.width, self.height) // self.num_colors
        else:
            # When custom grid divisions are specified
            # Higher number = more divisions = smaller grid size
            self.grid_size = min(self.width, self.height) // self.grid_size
        
        print(f"Image dimensions: {self.width}x{self.height}")  # Debug
        print(f"Grid size: {self.grid_size}")  # Debug
        print(f"Number of divisions: {min(self.width, self.height) // self.grid_size}")  # Debug
        
        # Process each grid cell
        for y in range(0, self.height, self.grid_size):
            for x in range(0, self.width, self.grid_size):
                cell = pixels[y:min(y+self.grid_size, self.height), 
                            x:min(x+self.grid_size, self.width)]
                
                if cell.size > 0:
                    neighborhood = self._get_neighborhood(pixels, y, x)
                    should_draw, effective_brightness = self._should_draw_circle(cell, neighborhood)
                    
                    if should_draw:
                        circle_size = int(effective_brightness * self.grid_size * 0.8)
                        if circle_size > 0:
                            center_x = x + self.grid_size//2
                            center_y = y + self.grid_size//2
                            draw.ellipse([
                                center_x - circle_size//2, 
                                center_y - circle_size//2,
                                center_x + circle_size//2, 
                                center_y + circle_size//2
                            ], fill=255)
        
        # Invert the final image if requested
        if self.invert:
            print("Inverting final image")  # Debug log
            output = ImageOps.invert(output)
        
        return output

    def _preprocess_image(self, pixels):
        """Apply preprocessing steps to the image."""
        if self.smoothing:
            pixels = gaussian_filter(pixels, sigma=self.smoothing_sigma)
            pixels = gaussian_filter(pixels, sigma=self.smoothing_sigma * 0.5)

        if self.enhance_contrast:
            pixels_float = pixels.astype(float) / 255.0
            p_low, p_high = self.contrast_percentile
            pixels_float = exposure.rescale_intensity(
                pixels_float, 
                in_range=tuple(np.percentile(pixels_float, (p_low, p_high)))
            )
            pixels = (pixels_float * 255).astype(np.uint8)

        return pixels

    def _get_neighborhood(self, pixels, y, x):
        """Get the surrounding cells for neighborhood analysis."""
        y_start = max(0, y - self.grid_size)
        y_end = min(self.height, y + 2 * self.grid_size)
        x_start = max(0, x - self.grid_size)
        x_end = min(self.width, x + 2 * self.grid_size)
        return pixels[y_start:y_end, x_start:x_end]

    def _should_draw_circle(self, cell, neighborhood):
        """Determine if a circle should be drawn based on cell brightness and neighborhood."""
        avg_brightness = np.mean(cell) / 255.0
        
        if not self.smoothing:
            return avg_brightness > self.darkness_threshold, avg_brightness
        
        neighborhood_brightness = np.mean(neighborhood) / 255.0
        neighborhood_std = np.std(neighborhood) / 255.0
        
        effective_brightness = avg_brightness
        
        if avg_brightness < self.darkness_threshold * 1.2:
            if neighborhood_brightness < self.darkness_threshold * 1.5:
                return False, 0
        
        if neighborhood_std > 0.15:
            effective_brightness = (avg_brightness * 0.3 + neighborhood_brightness * 0.7)
        
        if 0.2 < effective_brightness < 0.8:
            effective_brightness = (effective_brightness + neighborhood_brightness) / 2
        
        return effective_brightness > self.darkness_threshold, effective_brightness

    # ... rest of the processing methods remain the same, 
    # but remove save_image and load_image methods ... 