import argparse
import requests
import sys
import random
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

def get_font(size):
    # Try more paths for fonts on different Linux distros
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def draw_grid(draw, grid, cell_size, colors):
    for week in range(len(grid)):
        for day in range(len(grid[0])):
            color = colors[grid[week][day]]
            # Upscaled offsets: padding 4px (2 * double)
            x0, y0 = week * cell_size + 80 + 4, day * cell_size + 40 + 4
            x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8
            # Block
            draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=color, outline=(255, 255, 255, 20))

def draw_legend(draw: ImageDraw.Draw, cell_size: int, image_width: int, image_height: int, username: str, year: str, theme_colors: Dict[str, Any], contributions: List[Tuple[Optional[str], int]]):
    # Draw day names (Only show Mon, Wed, Fri)
    font = get_font(16)
    # Draw day names (Only show Mon, Wed, Fri)
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        if day in ["Mon", "Wed", "Fri"]:
            y = i * cell_size + 40
            draw.text((10, y + 10), day, font=font, fill=theme_colors['text'])

    # Draw month names dynamically based on data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    for i, (date_str, count) in enumerate(contributions):
        # Check every day for month transitions, but only draw label at the start of a week
        if not date_str: continue
        
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        if dt.month != last_month:
            week = i // 7
            x = week * cell_size + 80
            draw.text((x, 10), months[dt.month - 1], font=font, fill=theme_colors['text'])
            last_month = dt.month

    # Removed year text as requested to prevent overlap



def create_tetris_gif(username: str, year: int, contributions: List[Tuple[Optional[str], int]], output_path: str, theme: str, year_range: str):
    width = 53  # 53 weeks
    height = 7  # 7 days per week
    cell_size = 40
    legend_width = 80
    image_width = width * cell_size + legend_width
    image_height = height * cell_size + 40  # Reduced height since credits are removed

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
        
        if week >= width:
            break  # Skip extra weeks if any
        
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
                # Double offsets: +4px padding
                x0, y0 = week * cell_size + legend_width + 4, step * cell_size + 40 + 4
                x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8
                draw.rounded_rectangle(
                    [x0, y0, x1, y1],
                    radius=6,
                    fill=colors[value],
                    outline=(255, 255, 255, 50)
                )

                frames.append(img)

        if value == 0:
            # SHATTER MECHANIC: Grey blocks break and show a message
            messages = ["REST", "IDLE", "RECHARGE", "ZEN", "PAUSE", "OFF"]
            msg = random.choice(messages)
            msg_font = get_font(24)
            
            # 4-frame shatter animation
            for frame_idx in range(4):
                img = Image.new('RGB', (image_width, image_height), background_color)
                draw = ImageDraw.Draw(img)
                draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, contributions)
                draw_grid(draw, grid, cell_size, colors)
                
                # Draw "shattered" fragments
                x_base = week * cell_size + legend_width
                y_base = day * cell_size + 40
                
                # Draw the breaking message (fade out)
                alpha = 255 - (frame_idx * 60)
                draw.text((x_base + 10, y_base - 20), msg, font=msg_font, fill=(theme_colors['text'][0], theme_colors['text'][1], theme_colors['text'][2], alpha))
                
                # Scattered fragments
                for _ in range(5):
                    frag_x = x_base + random.randint(0, cell_size - 10)
                    frag_y = y_base + random.randint(0, cell_size - 10)
                    size = random.randint(4, 8)
                    draw.rounded_rectangle([frag_x, frag_y, frag_x + size, frag_y + size], radius=2, fill=colors[0], outline=(255, 255, 255, alpha))
                
                frames.append(img)
            
            # VERY IMPORTANT: Do NOT update the grid. Grey blocks "break" and are gone.
            continue
            
        grid[week][day] = value

        # Fade effect for the block when it stops (ONLY for active green blocks)
        for alpha in range(0, 256, 50):  # Larger steps to make the fade faster
            img = Image.new('RGB', (image_width, image_height), background_color)
            draw = ImageDraw.Draw(img)
            draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, contributions)
            draw_grid(draw, grid, cell_size, colors)

            # Double offsets: +4px padding
            x0, y0 = week * cell_size + legend_width + 4, day * cell_size + 40 + 4
            x1, y1 = x0 + cell_size - 8, y0 + cell_size - 8
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=6,
                fill=colors[value],
                outline=(255, 255, 255, alpha)
            )

            frames.append(img)

    # Save as animated GIF
    if len(frames) == 0:
        raise Exception("No frames generated. Check contribution data.")
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
        
        # Combine and sort by date
        all_contributions: List[Tuple[Optional[str], int]] = sorted(contributions_current + contributions_prev, key=lambda x: x[0] if x[0] else "")
        
        if len(all_contributions) == 0:
            raise Exception(f"No contributions found for user {args.username}")

        # Get today's date and find exactly 52 weeks ago
        # GitHubcontribution data is usually up to yesterday/today.
        # We want a 53-week window (52 weeks + current partial week)
        today = datetime.now()
        start_date_limit = (today - timedelta(days=370)).strftime('%Y-%m-%d')
        
        # Filter for data from roughly one year ago
        rolling_contributions = [c for c in all_contributions if c[0] and c[0] >= start_date_limit]
        
        # If we have less than 371 days after filtering, just take the last 371
        if len(rolling_contributions) < 371:
            rolling_contributions = all_contributions[-371:]

        # Shift to align with Sunday
        if rolling_contributions and rolling_contributions[0][0]:
            first_date = datetime.strptime(rolling_contributions[0][0], '%Y-%m-%d')
            # Python weekday: Mon=0, ..., Sun=6. GitHub start: Sun=0.
            # Convert Mon=0->1, ..., Sun=6->0
            shift = (first_date.weekday() + 1) % 7
            if shift > 0:
                padding: List[Tuple[Optional[str], int]] = [(None, 0)] * shift
                rolling_contributions = padding + rolling_contributions
        elif not rolling_contributions:
            raise Exception(f"No contribution data available for user {args.username}")

        # Ensure we always have exactly 371 days to fill the 53-week grid
        if len(rolling_contributions) > 371:
            rolling_contributions = rolling_contributions[:371]
        else:
            while len(rolling_contributions) < 371:
                rolling_contributions.append((None, 0))
        
        year_range = f"{current_year - 1} - {current_year}"
        
        # Ensure output directory matches where we run it from or absolute path
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
