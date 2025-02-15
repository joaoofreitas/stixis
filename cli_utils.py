import os
from PIL import Image
import itertools
from stixis_processor import StixisProcessor

def create_output_directory(image_path):
    """Create output directory based on image name."""
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = f"{base_name}_stixis_patterns"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def validate_input(num_colors):
    """Validate the number of colors input."""
    if not (2 <= num_colors <= 10):
        raise ValueError("Number of colors must be between 2 and 10")

def validate_grid_size(grid_size, image_path):
    """Validate the grid size input based on image dimensions."""
    with Image.open(image_path) as img:
        min_dimension = min(img.size)
        max_grid_divisions = min_dimension // 2
        
        if not (4 <= grid_size <= max_grid_divisions):
            raise ValueError(
                f"Grid divisions must be between 4 and {max_grid_divisions} "
                f"for this image (half of minimum dimension {min_dimension})"
            )
        return max_grid_divisions

def get_grid_search_parameters(image_path):
    """Get parameter ranges for grid search."""
    with Image.open(image_path) as img:
        min_dimension = min(img.size)
        max_divisions = min(min_dimension // 2, 50)
    
    color_range = range(2, 11, 2)
    division_range = [4, 8, 16, 32, min(max_divisions, 50)]
    
    return color_range, division_range

def run_grid_search(image_path):
    """Run grid search with different combinations of parameters."""
    color_range, division_range = get_grid_search_parameters(image_path)
    output_dir = create_output_directory(image_path)
    
    # Add smoothing and contrast parameters to grid search
    smoothing_options = [False, True]
    contrast_options = [False, True]
    smoothing_sigmas = [1.5]  # Increased from 1.0 for more aggressive smoothing
    
    print(f"\nCreated output directory: {output_dir}")
    print("\nStarting Grid Search...")
    print(f"Testing colors: {list(color_range)}")
    print(f"Testing divisions: {division_range}")
    print(f"Testing smoothing: {smoothing_options}")
    print(f"Testing contrast enhancement: {contrast_options}")
    print("This may take a while depending on the image size and parameter range.\n")
    
    total_combinations = (len(color_range) * len(division_range) * 
                         len(smoothing_options) * len(contrast_options))
    current = 0
    
    for num_colors, divisions, smoothing, enhance_contrast in itertools.product(
        color_range, division_range, smoothing_options, contrast_options
    ):
        current += 1
        print(f"Processing combination {current}/{total_combinations}: "
              f"Colors={num_colors}, Divisions={divisions}, "
              f"Smoothing={smoothing}, Contrast={enhance_contrast}")
        
        processor = StixisProcessor(
            num_colors, 
            image_path, 
            divisions, 
            output_dir=output_dir,
            smoothing=smoothing,
            smoothing_sigma=smoothing_sigmas[0] if smoothing else 0.0,
            enhance_contrast=enhance_contrast,
            contrast_percentile=(2, 98)
        )
        processor.run()

def run_single_process():
    """Run the processor with user-specified parameters."""
    num_colors = int(input("Enter number of colors for the grayscale filter (2-10): "))
    validate_input(num_colors)
    
    image_path = input("Enter path to image file (jpg/jpeg/png): ")
    
    use_custom_grid = input("Do you want to specify custom grid divisions? (y/n): ").lower()
    grid_size = None
    
    if use_custom_grid == 'y':
        grid_size = int(input("Enter number of grid divisions (minimum 4): "))
        validate_grid_size(grid_size, image_path)
    
    use_smoothing = input("Do you want to apply smoothing to reduce noise? (y/n): ").lower() == 'y'
    smoothing_sigma = 1.5  # Increased default
    if use_smoothing:
        smoothing_sigma = float(input("Enter smoothing strength (0.5-3.0, default 1.5): ") or "1.5")
    
    enhance_contrast = input("Do you want to enhance contrast? (y/n): ").lower() == 'y'
    
    processor = StixisProcessor(
        num_colors, 
        image_path, 
        grid_size,
        smoothing=use_smoothing,
        smoothing_sigma=smoothing_sigma,
        enhance_contrast=enhance_contrast
    )
    processor.run() 