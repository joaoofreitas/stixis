from pathlib import Path
from stixis_processor import StixisProcessor
from image_handler import ImageHandler
from cli_utils import parse_args, prompt_for_parameters, run_grid_search
from PIL import Image
import argparse

def main():
    try:
        # Parse command line arguments
        args = parse_args()
        
        # If no arguments provided, use interactive mode
        if args is None:
            params = prompt_for_parameters()
            
            if params["mode"] == "grid_search":
                run_grid_search(params["image_path"], params["output_dir"])
                return 0
            
            # Use provided parameters for single process
            args = argparse.Namespace(
                image_path=params["image_path"],
                colors=params["params"]["num_colors"],
                grid_size=params["params"]["grid_size"],
                smooth=params["params"]["smoothing"],
                contrast=params["params"]["enhance_contrast"],
                output_dir=params["output_dir"],
                grid_search=False
            )
        
        # Handle grid search mode
        if args.grid_search:
            run_grid_search(args.image_path, args.output_dir)
            return 0
        
        # Single image processing
        image_handler = ImageHandler(args.output_dir)
        processor = StixisProcessor(
            num_colors=args.colors,
            grid_size=args.grid_size,
            smoothing=args.smooth,
            enhance_contrast=args.contrast
        )
        
        # Process image
        input_image = Image.open(args.image_path)
        processed_image = processor.process(input_image)
        
        # Save result
        output_path = image_handler.save_image(
            processed_image,
            Path(args.image_path).stem,
            args.colors,
            processor.actual_divisions,
            args.smooth,
            args.contrast
        )
        
        print(f"Processed image saved as {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
