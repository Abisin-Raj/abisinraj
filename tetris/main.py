import argparse
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from typing import List, Tuple, Dict, TypedDict



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
            x0, y0 = week * cell_size + 40 + 1, day * cell_size + 20 + 1
            x1, y1 = x0 + cell_size - 2, y0 + cell_size - 2 # Center gap (1px + 18px + 1px = 20px)
            # Block
            draw.rounded_rectangle([x0, y0, x1, y1], radius=2, fill=color, outline=(255, 255, 255, 20))

def draw_legend(draw, cell_size, image_width, image_height, username, year, theme_colors):
    # Draw day names
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        y = i * cell_size + 20
        draw.text((5, y), day, fill=theme_colors['text'])

    # Draw month names
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_positions = {1: 0, 2: 4, 3: 8, 4: 12, 5: 16, 6: 20, 7: 24, 8: 28, 9: 32, 10: 36, 11: 40, 12: 44}
    for month, week in month_positions.items():
        x = week * cell_size + 40
        draw.text((x, 5), months[month - 1], fill=theme_colors['text'])

    # Removed year text as requested to prevent overlap



def create_tetris_gif(username, year, contributions, output_path, theme, year_range):
    width = 53  # 53 weeks
    height = 7  # 7 days per week
    cell_size = 20
    legend_width = 40
    image_width = width * cell_size + legend_width
    image_height = height * cell_size + 20  # Reduced height since credits are removed

    # Theme Configuration
    class Theme(TypedDict):
        background: str
        text: Tuple[int, int, int]
        colors: List[str]

    THEMES: Dict[str, Theme] = {
        'light': {
            'background': '#ffffff',
            'text': (36, 41, 47),
            'colors': ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
        },
        'dark': {
            'background': '#0d1117',
            'text': (201, 209, 217), # GitHub Dark Text
            'colors': ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
        }
    }
    
    theme_colors = THEMES.get(theme, THEMES['light'])
    colors = theme_colors['colors']
    background_color = theme_colors['background']

    frames = []
    # Initialize grid with background color index (0)
    # Initialize grid with background color index (0)
    grid: List[List[int]] = [[0] * height for _ in range(width)]

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
                draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors)
                draw_grid(draw, grid, cell_size, colors)

                # Draw moving block
                x0, y0 = week * cell_size + legend_width + 1, step * cell_size + 20 + 1
                x1, y1 = x0 + cell_size - 2, y0 + cell_size - 2
                draw.rounded_rectangle(
                    [x0, y0, x1, y1],
                    radius=2,
                    fill=colors[value],
                    outline=(255, 255, 255, 50)
                )

                frames.append(img)

        grid[week][day] = value

        # Fade effect for the block when it stops
        for alpha in range(0, 256, 50):  # Larger steps to make the fade faster
            img = Image.new('RGB', (image_width, image_height), background_color)
            draw = ImageDraw.Draw(img)
            draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors)
            draw_grid(draw, grid, cell_size, colors)

            x0, y0 = week * cell_size + legend_width + 1, day * cell_size + 20 + 1
            x1, y1 = x0 + cell_size - 2, y0 + cell_size - 2
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=2,
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
    parser.add_argument('--theme', type=str, choices=['light', 'dark'], default='light', help='Theme argument (light/dark)')
    parser.add_argument('--output', type=str, default='tetris_github.gif', help='Output file name')
    
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
        
        year_range = f"{current_year - 1} - {current_year}"
        
        # Ensure output directory matches where we run it from or absolute path
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(e)
