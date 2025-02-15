from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import exposure
from sklearn.cluster import KMeans
from collections import Counter

class StixisColorProcessor:
    def __init__(self, num_colors=5, grid_size=None, smoothing=False, 
                 smoothing_sigma=1.0, darkness_threshold=0.1,
                 enhance_contrast=False, contrast_percentile=(2, 98),
                 color_palette_size=8, invert=False):
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
        
    def _extract_color_palette(self, image):
        """Extract dominant colors from the image."""
        # Convert image to RGB array
        img_array = np.array(image.convert('RGB'))
        
        # Reshape for KMeans
        pixels = img_array.reshape(-1, 3)
        
        # Use KMeans to find dominant colors
        kmeans = KMeans(n_clusters=self.color_palette_size, n_init=10)
        kmeans.fit(pixels)
        
        # Get the colors and their frequencies
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        color_counts = Counter(labels)
        
        # Sort colors by frequency
        sorted_colors = [colors[i] for i, _ in color_counts.most_common()]
        return sorted_colors
    
    def _find_nearest_color(self, pixel_color, palette):
        """Find the nearest color in the palette."""
        pixel_color = np.array(pixel_color)
        distances = np.sqrt(np.sum((palette - pixel_color) ** 2, axis=1))
        return tuple(palette[np.argmin(distances)])
    
    def process(self, image):
        """Process the image and create colored circle pattern effect."""
        self.width, self.height = image.size
        
        # Handle transparency
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (0, 0, 0))
            image = Image.alpha_composite(background.convert('RGBA'), image)
        
        # Extract color palette
        color_palette = self._extract_color_palette(image)
        
        # Convert to RGB for color processing
        rgb_image = image.convert('RGB')
        rgb_array = np.array(rgb_image)
        
        # Convert to grayscale for brightness
        gray_array = np.array(image.convert('L'))
        
        # Create output image with black background
        output = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(output)
        
        # Calculate grid size based on divisions
        if self.grid_size is None:
            self.grid_size = min(self.width, self.height) // self.num_colors
        else:
            self.grid_size = min(self.width, self.height) // self.grid_size
        
        # Process each grid cell
        for y in range(0, self.height, self.grid_size):
            for x in range(0, self.width, self.grid_size):
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
                            draw.ellipse([
                                center_x - circle_size//2, 
                                center_y - circle_size//2,
                                center_x + circle_size//2, 
                                center_y + circle_size//2
                            ], fill=circle_color)
        
        # Invert the final image if requested
        if self.invert:
            output = ImageOps.invert(output)
        
        return output 