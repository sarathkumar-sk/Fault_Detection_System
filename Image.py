from PIL import Image
import os
import shutil

# Function to convert .bmp to .jpg and store in a separate folder
def convert_bmp_to_jpg(folder_path):
    # Create a new folder with the same name as the initial folder
    folder_name = os.path.basename(folder_path)
    new_folder_path = os.path.join(os.path.dirname(folder_path), f"{folder_name}_converted")
    
    # If the new folder does not exist, create it
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    # Loop through all files in the original folder
    for filename in os.listdir(folder_path):
        # Check if the file is a .bmp file
        if filename.lower().endswith('.bmp'):
            # Open the .bmp image
            bmp_path = os.path.join(folder_path, filename)
            with Image.open(bmp_path) as img:
                # Define the new filename with .jpg extension
                jpg_filename = filename[:-4] + '.jpg'
                jpg_path = os.path.join(new_folder_path, jpg_filename)
                
                # Convert the image to RGB (needed for .jpg format)
                img = img.convert('RGB')
                
                # Save the image as .jpg in the new folder
                img.save(jpg_path, 'JPEG')
                print(f'Converted {filename} to {jpg_filename} and saved to {new_folder_path}')


folder_path = 'D:/BIMETAL/SCORE MARK'

# Call the function to convert images
convert_bmp_to_jpg(folder_path)
