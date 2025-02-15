import os
from PIL import Image
import itertools
from stixis_processor import StixisProcessor
import argparse
from pathlib import Path
import sys

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
    
    color_range = range(2, 11, 2)  # [2, 4, 6, 8, 10]
    division_range = [4, 8, 16, 32, min(max_divisions, 50)]
    
    return color_range, division_range

def run_grid_search(image_path, output_dir=None):
    """Run grid search with different combinations of parameters."""
    output_dir = output_dir or create_output_directory(image_path)
    color_range, division_range = get_grid_search_parameters(image_path)
    
    # Grid search parameters
    smoothing_options = [False, True]
    contrast_options = [False, True]
    smoothing_sigmas = [1.5]
    
    print(f"\nStarting Grid Search...")
    print(f"Output directory: {output_dir}")
    print(f"Testing colors: {list(color_range)}")
    print(f"Testing divisions: {division_range}")
    print(f"Testing smoothing: {smoothing_options}")
    print(f"Testing contrast: {contrast_options}")
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
        
        try:
            processor = StixisProcessor(
                num_colors=num_colors,
                grid_size=divisions,
                smoothing=smoothing,
                smoothing_sigma=smoothing_sigmas[0] if smoothing else 0.0,
                enhance_contrast=enhance_contrast
            )
            
            input_image = Image.open(image_path)
            output_image = processor.process(input_image)
            
            # Generate output filename
            filename = f"GS{num_colors}_DIV{divisions}"
            if smoothing:
                filename += "_smooth"
            if enhance_contrast:
                filename += "_contrast"
            filename += ".jpg"
            
            output_path = Path(output_dir) / filename
            output_image.save(output_path)
            
        except Exception as e:
            print(f"Error processing combination: {str(e)}")

def prompt_for_parameters(image_path=None):
    """Interactive prompt for processing parameters."""
    if image_path is None:
        image_path = input("Enter path to image file (jpg/jpeg/png): ")
    
    print("\nChoose processing mode:")
    print("1. Single image process")
    print("2. Grid search (test multiple parameter combinations)")
    mode = input("Enter mode (1/2): ").strip()
    
    if mode == "2":
        output_dir = input("\nEnter output directory (optional, press Enter for default): ").strip()
        output_dir = output_dir if output_dir else None
        return {"mode": "grid_search", "image_path": image_path, "output_dir": output_dir}
    
    # Single process mode
    try:
        num_colors = int(input("\nEnter number of colors (2-10): "))
        validate_input(num_colors)
        
        use_custom_grid = input("Use custom grid? (y/n): ").lower() == 'y'
        grid_size = None
        if use_custom_grid:
            grid_size = int(input("Enter grid divisions (minimum 4): "))
            validate_grid_size(grid_size, image_path)
        
        use_smoothing = input("Apply smoothing? (y/n): ").lower() == 'y'
        smoothing_sigma = 1.5
        if use_smoothing:
            smoothing_sigma = float(input("Enter smoothing strength (0.5-3.0, default 1.5): ") or "1.5")
        
        enhance_contrast = input("Enhance contrast? (y/n): ").lower() == 'y'
        
        output_dir = input("Enter output directory (optional, press Enter for default): ").strip()
        
        return {
            "mode": "single",
            "image_path": image_path,
            "params": {
                "num_colors": num_colors,
                "grid_size": grid_size,
                "smoothing": use_smoothing,
                "smoothing_sigma": smoothing_sigma,
                "enhance_contrast": enhance_contrast
            },
            "output_dir": output_dir if output_dir else None
        }
        
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Stixis - Circle-based image processor')
    parser.add_argument('image_path', type=str, nargs='?', help='Path to input image')
    parser.add_argument('--colors', type=int, default=5, help='Number of grayscale colors (2-10)')
    parser.add_argument('--grid-size', type=int, help='Number of grid divisions (4+)')
    parser.add_argument('--output-dir', type=str, help='Output directory')
    parser.add_argument('--smooth', action='store_true', help='Apply smoothing')
    parser.add_argument('--contrast', action='store_true', help='Enhance contrast')
    parser.add_argument('--grid-search', action='store_true', help='Run grid search mode')
    
    args = parser.parse_args()
    
    # If no arguments provided, return None to trigger interactive mode
    if not args.image_path and len(sys.argv) == 1:
        return None
    
    # Validate arguments if provided
    if args.image_path and not Path(args.image_path).exists():
        raise ValueError(f"Image path does not exist: {args.image_path}")
    if args.colors and not (2 <= args.colors <= 10):
        raise ValueError("Colors must be between 2 and 10")
    
    return args 