import os
from PIL import Image

def create_seasons_gif(frame_paths, output_path, duration=500):
    """
    Creates an animated GIF from a list of image paths.
    """
    frames = []
    for path in frame_paths:
        if os.path.exists(path):
            img = Image.open(path)
            # Ensure all images are the same size and converted to RGBA
            img = img.convert("RGBA")
            frames.append(img)
        else:
            print(f"Warning: Frame not found at {path}")

    if not frames:
        print("Error: No frames found to create GIF.")
        return

    # Save as GIF
    # duration is in milliseconds between frames
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=duration,
        loop=0
    )
    print(f"Successfully created GIF at {output_path}")

if __name__ == "__main__":
    # Define asset paths
    # Assuming the artifacts are saved in the specific locations
    base_dir = "/home/abisin/.gemini/antigravity/brain/d18f038d-1088-4e59-b7ad-76281150e007"
    frame_files = [
        "winter_snow_pixel_art.png",
        "spring_sakura_pixel_art.png",
        "summer_sunny_pixel_art.png",
        "autumn_rain_pixel_art.png"
    ]
    frame_paths = [os.path.join(base_dir, f) for f in frame_files]
    
    # Target GIF path in the workspace assets
    workspace_assets = "/home/abisin/Desktop/abisinraj/assets"
    os.makedirs(workspace_assets, exist_ok=True)
    output_gif = os.path.join(workspace_assets, "seasons_walking.gif")
    
    create_seasons_gif(frame_paths, output_gif)
