import os
from stixis_processor import StixisProcessor
from utils import run_grid_search, run_single_process

def main():
    """Main function to handle program execution flow."""
    try:
        print("Stixis - Artistic Circle Pattern Generator")
        print("----------------------------------------")
        use_grid_search = input("Do you want to run TestGrid mode? (y/n): ").lower()
        
        image_path = input("Enter path to image file (jpg/jpeg/png): ")
        if not os.path.exists(image_path):
            raise FileNotFoundError("Image file not found")
            
        if use_grid_search == 'y':
            run_grid_search(image_path)
        else:
            run_single_process()
            
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Error: Image file not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
