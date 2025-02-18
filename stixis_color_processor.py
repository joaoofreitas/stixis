from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import exposure
from collections import Counter

class StixisColorProcessor:
    def __init__(self, num_colors=5, grid_size=None, smoothing=False, 
                 smoothing_sigma=1.0, darkness_threshold=0.1,
                 enhance_contrast=False, contrast_percentile=(2, 98),
                 color_palette_size=8, invert=False, upscale_factor=1):
        """Initialize the Stixis color processor."""
        self.num_colors = num_colors
        self.grid_size = grid_size
        self.smoothing = smoothing
        self.smoothing_sigma = smoothing_sigma
        self.darkness_threshold = darkness_threshold
        self.enhance_contrast = enhance_contrast
        self.contrast_percentile = contrast_percentile
        self.color_palette_size = color_palette_size
        self.invert = invert
        self.upscale_factor = upscale_factor
        self.color_cache = {}
        
    def _median_cut(self, pixels, depth):
        """Implement median cut algorithm for color quantization."""
        if depth == 0 or len(pixels) == 0:
            if len(pixels) == 0:
                return np.array([0, 0, 0])
            return np.mean(pixels, axis=0).astype(int)
            
        # Find the color channel with the largest range
        ranges = np.ptp(pixels, axis=0)
        channel = np.argmax(ranges)
        
        # Sort pixels by the channel with largest range
        pixels = pixels[pixels[:, channel].argsort()]
        median = len(pixels) // 2
        
        # Recursively process both halves
        return np.vstack([
            self._median_cut(pixels[:median], depth - 1),
            self._median_cut(pixels[median:], depth - 1)
        ])
    
    def _extract_color_palette(self, image):
        """Extract dominant colors using median cut algorithm."""
        # Convert image to RGB array and reshape
        img_array = np.array(image.convert('RGB'))
        pixels = img_array.reshape(-1, 3)
        
        # Subsample pixels for faster processing
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixels = pixels[indices]
        
        # Calculate depth needed for desired palette size
        depth = int(np.log2(self.color_palette_size))
        palette = self._median_cut(pixels, depth)
        
        # Count frequency of nearest colors
        distances = np.sqrt(((pixels[:, np.newaxis] - palette) ** 2).sum(axis=2))
        labels = np.argmin(distances, axis=1)
        color_counts = Counter(labels)
        
        # Sort colors by frequency
        sorted_colors = [palette[i] for i, _ in color_counts.most_common()]
        return np.array(sorted_colors)
    
    def _find_nearest_color(self, pixel_color, palette):
        """Find the nearest color in the palette using vectorized operations."""
        cache_key = (*pixel_color, palette.tobytes())
        if cache_key in self.color_cache:
            return self.color_cache[cache_key]
            
        pixel_color = np.array(pixel_color)
        distances = np.sqrt(np.sum((palette - pixel_color) ** 2, axis=1))
        nearest_color = tuple(palette[np.argmin(distances)])
        self.color_cache[cache_key] = nearest_color
        return nearest_color
    
    def _draw_pixel_perfect_circle(self, draw, center_x, center_y, size, color):
        """Draw a perfectly crisp colored circle without any artifacts."""
        if size <= 0:
            return
            
        radius = size // 2
        if radius == 0:
            draw.point((center_x, center_y), fill=color)
            return

        # Draw filled circle using optimized scanline algorithm
        for y in range(-radius, radius + 1):
            x_val = int((radius * radius - y * y) ** 0.5)
            x_start = center_x - x_val
            x_end = center_x + x_val + 1
            # Draw horizontal line
            for x in range(x_start, x_end):
                draw.point((x, center_y + y), fill=color)

    def save_image(self, image, file_path):
        """Save the processed image as a PNG file."""
        image.save(file_path, format='PNG')

    def process(self, image):
        """Process the image and create colored circle pattern effect."""
        original_width, original_height = image.size
        
        # Extract color palette BEFORE upscaling
        color_palette = self._extract_color_palette(image)
        
        # Calculate base grid size before upscaling
        if self.grid_size is None:
            base_grid_size = min(original_width, original_height) // self.num_colors
        else:
            base_grid_size = min(original_width, original_height) // self.grid_size
        
        # Apply upscaling if requested
        if self.upscale_factor > 1:
            new_width = original_width * self.upscale_factor
            new_height = original_height * self.upscale_factor
            image = image.resize((new_width, new_height), Image.Resampling.BILINEAR)
            self.width, self.height = new_width, new_height
            self.grid_size = base_grid_size * self.upscale_factor
        else:
            self.width, self.height = original_width, original_height
            self.grid_size = base_grid_size
        
        # Handle transparency
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (0, 0, 0))
            image = Image.alpha_composite(background.convert('RGBA'), image)
        
        # Convert to arrays and process in batches
        rgb_array = np.array(image.convert('RGB'))
        gray_array = np.array(image.convert('L'))
        
        # Create output image
        output = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(output)
        
        # Calculate grid positions
        y_positions = range(0, self.height, self.grid_size)
        x_positions = range(0, self.width, self.grid_size)
        
        # Process grid cells in batches
        for y in y_positions:
            for x in x_positions:
                # Get cell data
                gray_cell = gray_array[y:min(y+self.grid_size, self.height), 
                                    x:min(x+self.grid_size, self.width)]
                rgb_cell = rgb_array[y:min(y+self.grid_size, self.height), 
                                   x:min(x+self.grid_size, self.width)]
                
                if gray_cell.size > 0:
                    # Calculate brightness and color
                    avg_brightness = np.mean(gray_cell) / 255.0
                    avg_color = tuple(np.mean(rgb_cell, axis=(0, 1)).astype(int))
                    
                    # Find nearest palette color
                    circle_color = self._find_nearest_color(avg_color, color_palette)
                    
                    # Draw circle if bright enough
                    if avg_brightness > self.darkness_threshold:
                        circle_size = int(avg_brightness * self.grid_size * 0.8)
                        if circle_size > 0:
                            center_x = x + self.grid_size//2
                            center_y = y + self.grid_size//2
                            self._draw_pixel_perfect_circle(
                                draw, 
                                center_x, 
                                center_y, 
                                circle_size, 
                                circle_color
                            )
        
        # Invert the final image if requested
        if self.invert:
            output = ImageOps.invert(output)
        
        return output 

    def process_and_save(self, image, file_path):
        """Process the image and save the result as a PNG file."""
        processed_image = self.process(image)
        self.save_image(processed_image, file_path) 