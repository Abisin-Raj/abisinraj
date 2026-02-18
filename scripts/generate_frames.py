from PIL import Image, ImageDraw
import os

def create_frame(season):
    # Base 32x32 frame
    img = Image.new("RGBA", (32, 32), (16, 16, 16, 255)) # 101010 background
    draw = ImageDraw.Draw(img)
    
    # Character base (body/head) - Simple stick-ish figure
    # We'll adjust attire based on season
    
    if season == "spring":
        # Sakura pink blossoms in background
        for x, y in [(5, 5), (10, 8), (20, 4), (25, 12)]:
            draw.point((x, y), fill=(255, 183, 197, 255))
        # Character in light green gear
        draw.rectangle([14, 15, 17, 25], fill=(144, 238, 144, 255)) # Body
        draw.rectangle([14, 11, 17, 14], fill=(233, 196, 106, 255)) # Head
        
    elif season == "summer":
        # Yellow sun
        draw.ellipse([2, 2, 8, 8], fill=(255, 255, 0, 255))
        # Character in yellow t-shirt
        draw.rectangle([14, 15, 17, 25], fill=(255, 204, 0, 255)) # Body
        draw.rectangle([14, 11, 17, 14], fill=(233, 196, 106, 255)) # Head

    elif season == "autumn":
        # Orange/Red leaves
        for x, y in [(2, 28), (8, 25), (28, 20), (22, 27)]:
            draw.point((x, y), fill=(210, 105, 30, 255))
        # Rain streaks (slanted)
        for i in range(5):
            x = (i * 7) % 32
            draw.line([x, 0, x+2, 4], fill=(100, 149, 237, 150))
        # Character in brown raincoat
        draw.rectangle([14, 15, 17, 25], fill=(139, 69, 19, 255)) # Body
        draw.rectangle([14, 11, 17, 14], fill=(233, 196, 106, 255)) # Head

    elif season == "winter":
        # Snowflakes
        for i in range(10):
            draw.point(((i*7)%32, (i*11)%32), fill=(255, 255, 255, 200))
        # Character in blue coat & red hat
        draw.rectangle([14, 15, 17, 25], fill=(0, 0, 139, 255)) # Body
        draw.rectangle([14, 11, 17, 14], fill=(233, 196, 106, 255)) # Head
        draw.rectangle([14, 10, 17, 11], fill=(255, 0, 0, 255)) # Hat
    
    return img

if __name__ == "__main__":
    base_dir = "/home/abisin/.gemini/antigravity/brain/d18f038d-1088-4e59-b7ad-76281150e007"
    seasons = ["winter", "spring", "summer", "autumn"]
    
    for season in seasons:
        img = create_frame(season)
        # Upscale to 128x128 for visibility while maintaining pixelated look
        img = img.resize((128, 128), Image.NEAREST)
        img.save(os.path.join(base_dir, f"{season}_pixel_art.png"))
        print(f"Generated {season}_pixel_art.png")
