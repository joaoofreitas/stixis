from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import exposure
from scipy.special import expit  # for sigmoid function

class StixisProcessor:
    BRIGHTNESS_MAPPINGS = {
        'linear': lambda x: x,
        'logarithmic': lambda x: np.log1p(x) / np.log1p(1),
        'exponential': lambda x: np.exp(x - 1),
        'sigmoid': lambda x: expit(6 * x - 3),  # scaled sigmoid
        'power': lambda x, gamma=2.2: x ** (1/gamma),  # gamma correction
        'adaptive': None  # will be handled separately
    }

    def __init__(self, num_colors, grid_size=None, smoothing=False, 
                 smoothing_sigma=1.0, darkness_threshold=0.1,
                 enhance_contrast=False, contrast_percentile=(2, 98), 
                 invert=False, brightness_mapping='linear', gamma=2.2,
                 upscale_factor=1):
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
        self.brightness_mapping = brightness_mapping
        self.gamma = gamma
        self.upscale_factor = upscale_factor
        self._setup_brightness_mapping()
        print(f"StixisProcessor initialized with self.invert={self.invert}")  # Debug log

    def _setup_brightness_mapping(self):
        """Precompute brightness mapping function for better performance."""
        if self.brightness_mapping == 'power':
            self._brightness_func = lambda x: self.BRIGHTNESS_MAPPINGS['power'](x, self.gamma)
        elif self.brightness_mapping == 'adaptive':
            self._brightness_func = self._adaptive_mapping
        else:
            self._brightness_func = self.BRIGHTNESS_MAPPINGS.get(
                self.brightness_mapping, 
                self.BRIGHTNESS_MAPPINGS['linear']
            )

    def process(self, image):
        """Process the image and create circle filter effect."""
        original_width, original_height = image.size
        
        # Handle transparency by converting transparent pixels to black
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (0, 0, 0))
            image = Image.alpha_composite(background.convert('RGBA'), image)
        
        # Convert to grayscale first
        pixels = np.array(image.convert('L'))
        
        # Apply preprocessing before upscaling
        pixels = self._preprocess_image(pixels)
        
        # Calculate base grid size
        if self.grid_size is None:
            base_grid_size = min(original_width, original_height) // self.num_colors
        else:
            base_grid_size = min(original_width, original_height) // self.grid_size
        
        # Apply upscaling after preprocessing if requested
        if self.upscale_factor > 1:
            # Convert preprocessed pixels back to image for high-quality upscaling
            processed_image = Image.fromarray(pixels)
            new_width = original_width * self.upscale_factor
            new_height = original_height * self.upscale_factor
            # Use LANCZOS for better quality upscaling of preprocessed image
            processed_image = processed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            pixels = np.array(processed_image)
            self.width, self.height = new_width, new_height
            self.grid_size = base_grid_size * self.upscale_factor
        else:
            self.width, self.height = original_width, original_height
            self.grid_size = base_grid_size
        
        # Create output image
        output = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(output)
        
        print(f"Image dimensions: {self.width}x{self.height}")  # Debug
        print(f"Grid size: {self.grid_size}")  # Debug
        print(f"Number of divisions: {min(self.width, self.height) // self.grid_size}")  # Debug
        
        # Create grid of cell positions
        y_coords = np.arange(0, self.height, self.grid_size)
        x_coords = np.arange(0, self.width, self.grid_size)
        
        # Process cells in vectorized manner where possible
        for y in y_coords:
            for x in x_coords:
                # Extract cell and neighborhood data
                cell_data = self._get_cell_data(pixels, y, x)
                if cell_data['valid']:
                    circle_params = self._calculate_circle_params(cell_data)
                    if circle_params['should_draw']:
                        self._draw_optimized_circle(
                            draw, 
                            x + self.grid_size//2,
                            y + self.grid_size//2,
                            circle_params['size']
                        )
        
        # Invert the final image if requested
        if self.invert:
            output = ImageOps.invert(output)
        
        return output

    def _preprocess_image(self, pixels):
        """Optimized preprocessing of image data."""
        if self.smoothing:
            # Apply single-pass smoothing with adjusted sigma
            pixels = gaussian_filter(pixels, sigma=self.smoothing_sigma * 1.2)

        if self.enhance_contrast:
            pixels_float = pixels.astype(float) / 255.0
            p_low, p_high = self.contrast_percentile
            # Use vectorized percentile calculation
            in_range = tuple(np.percentile(pixels_float, (p_low, p_high)))
            pixels_float = exposure.rescale_intensity(pixels_float, in_range=in_range)
            pixels = (pixels_float * 255).astype(np.uint8)

        return pixels

    def _get_cell_data(self, pixels, y, x):
        """Efficiently get cell and neighborhood data."""
        y_end = min(y + self.grid_size, self.height)
        x_end = min(x + self.grid_size, self.width)
        cell = pixels[y:y_end, x:x_end]
        
        if cell.size == 0:
            return {'valid': False}
            
        # Calculate neighborhood bounds
        y_start_n = max(0, y - self.grid_size)
        y_end_n = min(self.height, y + 2 * self.grid_size)
        x_start_n = max(0, x - self.grid_size)
        x_end_n = min(self.width, x + 2 * self.grid_size)
        
        neighborhood = pixels[y_start_n:y_end_n, x_start_n:x_end_n]
        
        return {
            'valid': True,
            'cell': cell,
            'neighborhood': neighborhood,
            'avg_brightness': np.mean(cell) / 255.0,
            'neighborhood_brightness': np.mean(neighborhood) / 255.0,
            'neighborhood_std': np.std(neighborhood) / 255.0
        }

    def _calculate_circle_params(self, cell_data):
        """Calculate circle parameters using vectorized operations."""
        avg_brightness = cell_data['avg_brightness']
        neighborhood_brightness = cell_data['neighborhood_brightness']
        neighborhood_std = cell_data['neighborhood_std']
        
        # Quick early exit for very dark regions
        if avg_brightness < self.darkness_threshold * 0.8:
            return {'should_draw': False, 'size': 0}
            
        # Calculate effective brightness
        if neighborhood_std > 0.15:
            effective_brightness = avg_brightness * 0.3 + neighborhood_brightness * 0.7
        else:
            effective_brightness = avg_brightness
            
        if 0.2 < effective_brightness < 0.8:
            effective_brightness = (effective_brightness + neighborhood_brightness) / 2
            
        mapped_brightness = self._brightness_func(effective_brightness)
        
        if mapped_brightness <= self.darkness_threshold:
            return {'should_draw': False, 'size': 0}
            
        circle_size = int(mapped_brightness * self.grid_size * 0.8)
        return {'should_draw': True, 'size': circle_size}

    def _draw_optimized_circle(self, draw, center_x, center_y, size):
        """Draw a circle without any artifacts."""
        if size <= 0:
            return
            
        radius = size // 2
        if radius == 0:
            draw.point((center_x, center_y), fill=255)
            return

        # Draw filled circle using optimized scanline algorithm
        for y in range(-radius, radius + 1):
            x_val = int((radius * radius - y * y) ** 0.5)
            x_start = center_x - x_val
            x_end = center_x + x_val + 1
            # Draw horizontal line
            for x in range(x_start, x_end):
                draw.point((x, center_y + y), fill=255)

    def _adaptive_mapping(self, brightness):
        """Optimized adaptive mapping."""
        if brightness < 0.2:
            return self.BRIGHTNESS_MAPPINGS['logarithmic'](brightness)
        elif brightness > 0.8:
            return self.BRIGHTNESS_MAPPINGS['sigmoid'](brightness)
        else:
            return self.BRIGHTNESS_MAPPINGS['power'](brightness, self.gamma)