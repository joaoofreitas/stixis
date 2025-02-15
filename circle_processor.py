from PIL import Image, ImageDraw
import numpy as np
import os
from scipy.ndimage import gaussian_filter
from skimage import exposure  # This is the correct import after installing scikit-image

class StixisProcessor:
    def __init__(self, num_colors, image_path, grid_size=None, output_path=None, output_dir=None, 
                 smoothing=False, smoothing_sigma=1.0, darkness_threshold=0.1,
                 enhance_contrast=False, contrast_percentile=(2, 98)):
        """
        Initialize the Stixis processor with the given parameters.
        
        Args:
            num_colors (int): Number of colors for the grayscale filter (2-10)
            image_path (str): Path to the input image file (jpg/jpeg/png)
            grid_size (int, optional): Number of divisions for the grid. If None, calculated from num_colors
            output_path (str, optional): Path where the processed image will be saved. If None, auto-generated
            output_dir (str, optional): Directory to save the output file
            smoothing (bool): Whether to apply smoothing to reduce noise
            smoothing_sigma (float): Gaussian smoothing sigma parameter
            darkness_threshold (float): Threshold for considering a region as dark (0-1)
            enhance_contrast (bool): Whether to apply contrast enhancement
            contrast_percentile (tuple): Percentiles for contrast stretching (low, high)
        """
        self.num_colors = num_colors
        self.image_path = image_path
        self.img = None
        self.width = None
        self.height = None
        self.grid_size = grid_size
        self.actual_divisions = grid_size if grid_size else num_colors
        self.smoothing = smoothing
        self.smoothing_sigma = smoothing_sigma
        self.darkness_threshold = darkness_threshold
        self.enhance_contrast = enhance_contrast
        self.contrast_percentile = contrast_percentile
        
        # Generate output path if not provided
        if output_path is None:
            original_name = os.path.splitext(os.path.basename(image_path))[0]
            smooth_suffix = "_smooth" if smoothing else ""
            contrast_suffix = "_contrast" if enhance_contrast else ""
            filename = f"{original_name}_GS{num_colors}_DIV{self.actual_divisions}{smooth_suffix}{contrast_suffix}.jpg"
            self.output_path = os.path.join(output_dir, filename) if output_dir else filename
        else:
            self.output_path = output_path
            
    def load_image(self):
        """Load and convert image to grayscale."""
        self.img = Image.open(self.image_path)
        self.img = self.img.convert('L')
        self.width, self.height = self.img.size
        
        if self.grid_size is None:
            self.grid_size = min(self.width, self.height) // self.num_colors
        else:
            # Calculate actual grid cell size based on the number of divisions
            self.grid_size = min(self.width, self.height) // self.grid_size
        
    def preprocess_image(self, pixels):
        """Apply preprocessing steps to the image."""
        if self.smoothing:
            # Apply stronger smoothing with multiple passes
            pixels = gaussian_filter(pixels, sigma=self.smoothing_sigma)
            # Second pass with smaller sigma for edge preservation
            pixels = gaussian_filter(pixels, sigma=self.smoothing_sigma * 0.5)

        if self.enhance_contrast:
            # Convert to float for contrast enhancement
            pixels_float = pixels.astype(float) / 255.0
            
            # Apply contrast stretching
            p_low, p_high = self.contrast_percentile
            pixels_float = exposure.rescale_intensity(
                pixels_float, 
                in_range=tuple(np.percentile(pixels_float, (p_low, p_high)))
            )
            
            # Convert back to original range
            pixels = (pixels_float * 255).astype(np.uint8)

        return pixels

    def should_draw_circle(self, cell, neighborhood):
        """
        Determine if a circle should be drawn based on cell brightness and neighborhood.
        More aggressive smoothing and contrast-aware version.
        """
        avg_brightness = np.mean(cell) / 255.0
        
        if not self.smoothing:
            return avg_brightness > self.darkness_threshold, avg_brightness
        
        # Calculate neighborhood statistics
        neighborhood_brightness = np.mean(neighborhood) / 255.0
        neighborhood_std = np.std(neighborhood) / 255.0
        
        # More aggressive brightness adjustment
        effective_brightness = avg_brightness
        
        # If the cell is dark and neighborhood is also dark, suppress more aggressively
        if avg_brightness < self.darkness_threshold * 1.2:  # Increased threshold
            if neighborhood_brightness < self.darkness_threshold * 1.5:  # More aggressive
                return False, 0
        
        # Enhanced contrast-aware adjustment
        if neighborhood_std > 0.15:  # Lower threshold for more aggressive smoothing
            # Weight more towards neighborhood in high contrast areas
            effective_brightness = (avg_brightness * 0.3 + neighborhood_brightness * 0.7)
        
        # Additional smoothing for mid-range brightness
        if 0.2 < effective_brightness < 0.8:
            effective_brightness = (effective_brightness + neighborhood_brightness) / 2
        
        return effective_brightness > self.darkness_threshold, effective_brightness

    def get_neighborhood(self, pixels, y, x):
        """Get the surrounding cells for neighborhood analysis."""
        y_start = max(0, y - self.grid_size)
        y_end = min(self.height, y + 2 * self.grid_size)
        x_start = max(0, x - self.grid_size)
        x_end = min(self.width, x + 2 * self.grid_size)
        
        return pixels[y_start:y_end, x_start:x_end]

    def process_image(self):
        """Process the image and create circle filter effect."""
        pixels = np.array(self.img)
        
        # Apply preprocessing
        pixels = self.preprocess_image(pixels)
        
        output = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(output)
        
        for y in range(0, self.height, self.grid_size):
            for x in range(0, self.width, self.grid_size):
                # Get grid cell region
                cell = pixels[y:min(y+self.grid_size, self.height), 
                            x:min(x+self.grid_size, self.width)]
                
                if cell.size > 0:
                    neighborhood = self.get_neighborhood(pixels, y, x)
                    should_draw, effective_brightness = self.should_draw_circle(cell, neighborhood)
                    
                    if should_draw:
                        # Calculate circle size based on effective brightness
                        circle_size = int(effective_brightness * self.grid_size * 0.8)
                        
                        if circle_size > 0:
                            # Calculate center of the grid cell
                            center_x = x + self.grid_size//2
                            center_y = y + self.grid_size//2
                            
                            # Draw white circle
                            draw.ellipse([
                                center_x - circle_size//2, 
                                center_y - circle_size//2,
                                center_x + circle_size//2, 
                                center_y + circle_size//2
                            ], fill=255)
        
        return output
    
    def save_image(self, output_image):
        """Save the processed image."""
        output_image.save(self.output_path)
        
    def run(self):
        """Execute the complete image processing pipeline."""
        self.load_image()
        output_image = self.process_image()
        self.save_image(output_image)
        print(f"Processed image saved as {self.output_path}")
