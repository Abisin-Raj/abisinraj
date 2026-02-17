import argparse
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def textsize(text, font):
    im = Image.new(mode="P", size=(0, 0))
    draw = ImageDraw.Draw(im)
    _, _, width, height = draw.textbbox((0, 0), text=text, font=font)
    return width, height

def get_github_contributions(username, year):
    url = f'https://github-contributions-api.jogruber.de/v4/{username}?y={year}'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from GitHub: {response.status_code}")

    body = response.json()

    return [(contribution['date'], contribution['count']) for contribution in body['contributions']]

def draw_grid(draw, grid, cell_size, colors):
    for week in range(len(grid)):
        for day in range(len(grid[0])):
            color = colors[grid[week][day]]
            x0, y0 = week * cell_size + 40, day * cell_size + 20
            x1, y1 = x0 + cell_size, y0 + cell_size
            # Shadow
            draw.rectangle([x0 + 3, y0 + 3, x1 + 3, y1 + 3], fill=(0, 0, 0, 100))  # Semi-transparent gray shadow
            # Block
            draw.rectangle([x0, y0, x1, y1], fill=color, outline=(255, 255, 255, 20)) # Reduced outline opacity

def draw_legend(draw, cell_size, image_width, image_height, username, year):
    # Draw day names
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        y = i * cell_size + 20
        draw.text((5, y), day, fill=(36, 41, 47)) # GitHub Light Text Color

    # Draw month names
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_positions = {1: 0, 2: 4, 3: 8, 4: 12, 5: 16, 6: 20, 7: 24, 8: 28, 9: 32, 10: 36, 11: 40, 12: 44}
    for month, week in month_positions.items():
        x = week * cell_size + 40
        draw.text((x, 5), months[month - 1], fill=(36, 41, 47)) # GitHub Light Text Color

    # Draw GitHub username and year in top left
    text = f"{year}"
    draw.text((5, 5), text, fill=(36, 41, 47)) # GitHub Light Text Color

    # Add black bar below months with "Credits: DEBBAWEB" aligned to the right
    legend_width = 40
    bar_height = 20
    bar_y = image_height - bar_height  # Position at the bottom of the image
    
    # Background for credits bar (matches main background)
    draw.rectangle([legend_width, bar_y, image_width, image_height], fill=(255, 255, 255))

    credits_text = f"@{username} - Credits: DEBBAWEB"
    font = ImageFont.load_default()  # Load default font
    text_width, text_height = textsize(credits_text, font=font)  # Calculate text size
    text_x = image_width - text_width - 5
    text_y = bar_y + (bar_height - text_height) // 2
    draw.text((text_x, text_y), credits_text, fill=(36, 41, 47), font=font)  # Draw text with specified font

def create_tetris_gif(username, year, contributions, output_path):
    width = 53  # 53 weeks
    height = 7  # 7 days per week
    cell_size = 20
    legend_width = 40
    image_width = width * cell_size + legend_width
    image_height = height * cell_size + 40  # Increased to accommodate legend and credits bar

    # GitHub Light Mode Contributions Colors
    # 0: Background/Empty, 1: Low, 2: Med-Low, 3: Med-High, 4: High
    colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
    
    # GitHub Light Background
    background_color = '#ffffff'

    frames = []
    grid = [[0] * height for _ in range(width)]

    for i, (date, count) in enumerate(contributions):
        week = i // 7
        day = i % 7
        
        # Map count to color index (0-4)
        if count == 0:
            value = 0
        elif count <= 3:
            value = 1
        elif count <= 6:
            value = 2
        elif count <= 9:
            value = 3
        else:
            value = 4

        for step in range(day + 1):
            if step % 2 == 0:  # Add frames for every second step only
                img = Image.new('RGB', (image_width, image_height), background_color)
                draw = ImageDraw.Draw(img)
                draw_legend(draw, cell_size, image_width, image_height, username, year)
                draw_grid(draw, grid, cell_size, colors)

                # Draw moving block
                x0, y0 = week * cell_size + legend_width, step * cell_size + 20
                x1, y1 = x0 + cell_size, y0 + cell_size
                draw.rectangle(
                    [x0, y0, x1, y1],
                    fill=colors[value],
                    outline=(255, 255, 255, 50)
                )

                frames.append(img)

        grid[week][day] = value

        # Fade effect for the block when it stops
        for alpha in range(0, 256, 50):  # Larger steps to make the fade faster
            img = Image.new('RGB', (image_width, image_height), background_color)
            draw = ImageDraw.Draw(img)
            draw_legend(draw, cell_size, image_width, image_height, username, year)
            draw_grid(draw, grid, cell_size, colors)

            x0, y0 = week * cell_size + legend_width, day * cell_size + 20
            x1, y1 = x0 + cell_size, y0 + cell_size
            draw.rectangle(
                [x0, y0, x1, y1],
                fill=colors[value],
                outline=(255, 255, 255, alpha)
            )

            frames.append(img)

    # Save as animated GIF
    frames[0].save(output_path, save_all=True, append_images=frames[1:], optimize=False, duration=20, loop=0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a GitHub contributions Tetris GIF.')
    parser.add_argument('-u', '--username', type=str, required=True, help='GitHub username')
    parser.add_argument('-y', '--year', type=int, default=datetime.now().year, help='Year for contributions')
    
    args = parser.parse_args()

    try:
        current_year = datetime.now().year
        # Fetch current and previous year to get a full rolling window
        contributions_current = get_github_contributions(args.username, current_year)
        contributions_prev = get_github_contributions(args.username, current_year - 1)
        
        # Combine and sort by date just in case
        all_contributions = sorted(contributions_current + contributions_prev, key=lambda x: x[0])
        
        # Keep only the last 371 days (53 weeks * 7 days)
        # This gives us the rolling year window
        rolling_contributions = all_contributions[-371:]
        
        # Ensure output directory matches where we run it from or absolute path
        create_tetris_gif(args.username, current_year, rolling_contributions, 'tetris_github.gif')
        print("GIF created successfully!")
    except Exception as e:
        print(e)
