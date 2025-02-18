from pathlib import Path
from PIL import Image

class ImageHandler:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_image(self, image_path):
        """Load image from path."""
        return Image.open(image_path)

    def save_image(self, image, original_name, num_colors, divisions, 
                  smoothing=False, enhance_contrast=False):
        """Save processed image with appropriate naming."""
        smooth_suffix = "_smooth" if smoothing else ""
        contrast_suffix = "_contrast" if enhance_contrast else ""
        filename = f"{original_name}_GS{num_colors}_DIV{divisions}{smooth_suffix}{contrast_suffix}.png"
        output_path = self.output_dir / filename
        
        # Save with maximum quality PNG settings
        image.save(output_path, format='PNG', optimize=False)
        return output_path

    @staticmethod
    def validate_image(file_path):
        """Validate if file is a valid image using PIL."""
        if not Path(file_path).exists():
            raise ValueError("File does not exist")
            
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify it's actually an image
                if img.format.lower() not in ['jpeg', 'png']:
                    raise ValueError("Invalid image format")
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}") 