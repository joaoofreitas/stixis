import argparse
from pathlib import Path
from stixis_processor import StixisProcessor
from stixis_color_processor import StixisColorProcessor
from PIL import Image

def main():
    parser = argparse.ArgumentParser(description='Stixis - Circle Pattern Generator')
    parser.add_argument('--input', type=str, help='Input image path')
    parser.add_argument('--output', type=str, help='Output image path')
    parser.add_argument('--colors', type=int, default=5, help='Number of circle sizes (2-10)')
    parser.add_argument('--grid-size', type=int, help='Number of grid divisions (4+)')
    parser.add_argument('--smooth', action='store_true', help='Apply smoothing')
    parser.add_argument('--sigma', type=float, default=1.5, help='Smoothing sigma value')
    parser.add_argument('--contrast', action='store_true', help='Enhance contrast')
    parser.add_argument('--invert', action='store_true', help='Invert colors')
    parser.add_argument('--mode', choices=['grayscale', 'color'], default='grayscale',
                      help='Processing mode (grayscale/color)')
    parser.add_argument('--palette-size', type=int, default=8,
                      help='Number of colors in palette (color mode only)')
    parser.add_argument('--mapping', choices=['linear', 'logarithmic', 'exponential', 
                                            'sigmoid', 'power', 'adaptive'],
                      default='linear', help='Brightness mapping mode')
    parser.add_argument('--gamma', type=float, default=2.2,
                      help='Gamma value for power mapping')
    parser.add_argument('--upscale', type=int, choices=[1, 2, 4, 8], default=1,
                       help='Upscale factor for better quality (1x, 2x, 4x, 8x)')

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        return

    # Validate input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' does not exist")
        return

    # Set default output path if not provided
    if not args.output:
        output_path = input_path.with_stem(input_path.stem + "_stixis")
    else:
        output_path = Path(args.output)

    # Load input image
    try:
        input_image = Image.open(input_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    # Create appropriate processor
    if args.mode == 'color':
        processor = StixisColorProcessor(
            num_colors=args.colors,
            grid_size=args.grid_size,
            smoothing=args.smooth,
            smoothing_sigma=args.sigma,
            enhance_contrast=args.contrast,
            color_palette_size=args.palette_size,
            invert=args.invert
        )
    else:
        processor = StixisProcessor(
            num_colors=args.colors,
            grid_size=args.grid_size,
            smoothing=args.smooth,
            smoothing_sigma=args.sigma,
            enhance_contrast=args.contrast,
            invert=args.invert,
            brightness_mapping=args.mapping,
            gamma=args.gamma
        )

    # Process image
    try:
        output_image = processor.process(input_image)
        output_image.save(output_path)
        print(f"Processed image saved to: {output_path}")
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    main()
