import argparse
import requests
import sys
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, TypedDict, Optional, Any



def get_github_contributions(username: str, year: int) -> List[Tuple[str, int]]:
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
            x0, y0 = week * cell_size + 40 + 4, day * cell_size + 20 + 4
            x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8 # Center gap (4px + 12px + 4px = 20px)
            # Block
            draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=color, outline=(255, 255, 255, 20))

def draw_legend(draw: ImageDraw.Draw, cell_size: int, image_width: int, image_height: int, username: str, year: str, theme_colors: Dict[str, Any], contributions: List[Tuple[Optional[str], int]]):
    # Draw day names (Only show Mon, Wed, Fri)
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        if day in ["Mon", "Wed", "Fri"]:
            y = i * cell_size + 20
            draw.text((5, y), day, fill=theme_colors['text'])

    # Draw month names dynamically based on data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    for i, (date_str, count) in enumerate(contributions):
        if not date_str or i % 7 != 0: continue
        
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        if dt.month != last_month:
            week = i // 7
            x = week * cell_size + 40
            draw.text((x, 5), months[dt.month - 1], fill=theme_colors['text'])
            last_month = dt.month

    # Removed year text as requested to prevent overlap



def create_tetris_gif(username: str, year: int, contributions: List[Tuple[Optional[str], int]], output_path: str, theme: str, year_range: str):
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

    frames: List[Image.Image] = []
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

        # If it's a padding element (no date), just skip animation and fill grid
        if not date:
            grid[week][day] = value
            continue

        for step in range(day + 1):
            if step % 2 == 0:  # Add frames for every second step only
                img = Image.new('RGB', (image_width, image_height), background_color)
                draw = ImageDraw.Draw(img)
                draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, contributions)
                draw_grid(draw, grid, cell_size, colors)

                # Draw moving block
                x0, y0 = week * cell_size + legend_width + 4, step * cell_size + 20 + 4
                x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8
                draw.rounded_rectangle(
                    [x0, y0, x1, y1],
                    radius=6,
                    fill=colors[value],
                    outline=(255, 255, 255, 50)
                )

                frames.append(img)

        grid[week][day] = value

        # Fade effect for the block when it stops
        for alpha in range(0, 256, 50):  # Larger steps to make the fade faster
            img = Image.new('RGB', (image_width, image_height), background_color)
            draw = ImageDraw.Draw(img)
            draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, contributions)
            draw_grid(draw, grid, cell_size, colors)

            x0, y0 = week * cell_size + legend_width + 4, day * cell_size + 20 + 4
            x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=6,
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
        contributions_current: List[Tuple[str, int]] = get_github_contributions(args.username, current_year)
        contributions_prev: List[Tuple[str, int]] = get_github_contributions(args.username, current_year - 1)
        
        # Combine and sort by date just in case
        all_contributions: List[Tuple[str, int]] = sorted(contributions_current + contributions_prev, key=lambda x: x[0])
        
        # Keep only the last 371 days (53 weeks * 7 days)
        # This gives us the rolling year window
        rolling_contributions: List[Tuple[str, int]] = all_contributions[-371:]
        
        # Shift to align with Sunday
        # Python weekday: Mon=0, ..., Sat=5, Sun=6
        # GitHub/Grid: Sun=0, Mon=1, ..., Sat=6
        if rolling_contributions:
            first_date = datetime.strptime(rolling_contributions[0][0], '%Y-%m-%d')
            # How many days from Sunday is the first date?
            # If Sun (6), shift is 0. If Mon (0), shift is 1.
            shift = (first_date.weekday() + 1) % 7
            if shift > 0:
                padding: List[Tuple[str, int]] = [(None, 0)] * shift
                rolling_contributions = padding + rolling_contributions
        
        year_range = f"{current_year - 1} - {current_year}"
        
        # Ensure output directory matches where we run it from or absolute path
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
