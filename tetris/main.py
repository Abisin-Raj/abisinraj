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

_FONT_CACHE = {}

def get_font(size):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    # Try more paths for fonts on different Linux distros
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, size)
            _FONT_CACHE[size] = font
            return font
        except Exception:
            continue
    _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]

def draw_grid(draw, grid, cell_size, colors, theme_colors):
    # Neutral grey border — very subtle on both light and dark themes
    border_color = (150, 150, 150, 25)
    for week in range(len(grid)):
        for day in range(len(grid[0])):
            color = colors[grid[week][day]]
            # 2px padding for tighter GitHub-like appearance at 40px resolution
            x0, y0 = week * cell_size + 80 + 2, day * cell_size + 40 + 2
            x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
            # Rounder corners (radius=8) with grey border
            draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=color, outline=border_color, width=1)

def draw_legend(draw: ImageDraw.Draw, cell_size: int, image_width: int, image_height: int, username: str, year: str, theme_colors: Dict[str, Any], month_labels: List[Tuple[int, str]]):
    # Draw day names (Only show Mon, Wed, Fri)
    font = get_font(16)
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        if day in ["Mon", "Wed", "Fri"]:
            y = i * cell_size + 40
            draw.text((10, y + 10), day, font=font, fill=theme_colors['text'])

    # Use pre-calculated month labels
    for x, month_name in month_labels:
        draw.text((x, 10), month_name, font=font, fill=theme_colors['text'])

    # Removed year text as requested to prevent overlap



def create_tetris_gif(username: str, year: int, contributions: List[Tuple[Optional[str], int]], output_path: str, theme: str, year_range: str):
    total_weeks = 53       # full year of data
    visible_weeks = 26     # how many weeks visible at once (sliding window)
    height = 7             # days per week
    cell_size = 40
    legend_width = 80
    image_width = visible_weeks * cell_size + legend_width
    image_height = height * cell_size + 40

    THEMES = {
        'light': {
            'background': '#ffffff',
            'text': (36, 41, 47),
            'colors': ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
        },
        'dark': {
            'background': '#0d1117',
            'text': (201, 209, 217),
            'colors': ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
        }
    }

    theme_colors = THEMES.get(theme, THEMES['light'])
    colors = theme_colors['colors']
    background_color = theme_colors['background']
    border_color = (150, 150, 150, 25)

    # Build full grid: total_weeks x height
    full_grid: List[List[int]] = [[0] * height for _ in range(total_weeks)]
    for i, (date, count) in enumerate(contributions):
        week = i // 7
        day = i % 7
        if week >= total_weeks: break
        if count == 0: val = 0
        elif count <= 3: val = 1
        elif count <= 6: val = 2
        elif count <= 9: val = 3
        else: val = 4
        full_grid[week][day] = val

    # Build month labels for each week index (relative to full_grid)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # week_month[w] = month name if a new month starts at week w, else None
    week_month: List[Optional[str]] = [None for _ in range(total_weeks)]
    last_m = -1
    for i, (date_str, count) in enumerate(contributions):
        if not date_str: continue
        w = i // 7
        if w >= total_weeks: break
        m = datetime.strptime(date_str, '%Y-%m-%d').month
        if m != last_m:
            week_month[w] = month_names[m - 1]
            last_m = m

    def draw_frame(start_week: int) -> Image.Image:
        img = Image.new('RGB', (image_width, image_height), background_color)
        draw = ImageDraw.Draw(img)
        font = get_font(16)

        # Draw day labels
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            if day in ["Mon", "Wed", "Fri"]:
                y = i * cell_size + 40
                draw.text((10, y + 10), day, font=font, fill=theme_colors['text'])

        # Draw month labels for visible weeks, with overlap prevention
        last_label_x = -999
        LABEL_WIDTH = 30
        for col, w in enumerate(range(start_week, start_week + visible_weeks)):
            if w < total_weeks and week_month[w]:
                x = col * cell_size + legend_width
                if x >= last_label_x + LABEL_WIDTH + 4:
                    draw.text((x, 10), week_month[w], font=font, fill=theme_colors['text'])
                    last_label_x = x

        # Draw cells for visible window
        for col, w in enumerate(range(start_week, start_week + visible_weeks)):
            for day in range(height):
                val = full_grid[w][day] if w < total_weeks else 0
                color = colors[val]
                x0 = col * cell_size + legend_width + 2
                y0 = day * cell_size + 40 + 2
                x1 = x0 + cell_size - 4
                y1 = y0 + cell_size - 4
                draw.rounded_rectangle([x0, y0, x1, y1], radius=8,
                                       fill=color, outline=border_color, width=1)
        return img

    frames: List[Image.Image] = []
    print(f"Generating scrolling GIF for {username} - Theme: {theme}")

    # Scroll from week 0 to the last possible start position
    # so the final frame shows the most recent visible_weeks
    max_start = total_weeks - visible_weeks
    for start in range(max_start + 1):
        frames.append(draw_frame(start))

    if len(frames) == 0:
        raise Exception("No frames generated. Check contribution data.")

    # duration per frame in ms — slower = easier to read
    frames[0].save(output_path, save_all=True, append_images=frames[1:],
                   optimize=False, duration=120, loop=0)


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

        # Get the latest possible date provided by the API
        if rolling_contributions and rolling_contributions[-1][0]:
            last_date = datetime.strptime(rolling_contributions[-1][0], '%Y-%m-%d')
            # Pad at the END to reach the end of the current week (Saturday)
            # Python weekday: Mon=0, ..., Sat=5, Sun=6. Saturday is target.
            # If Mon (0), we need 5 days (Sat-Mon). If Sat (5), we need 0. If Sun (6), we need 6.
            days_to_saturday = (5 - last_date.weekday()) % 7
            if days_to_saturday > 0:
                end_padding: List[Tuple[Optional[str], int]] = [(None, 0)] * days_to_saturday
                rolling_contributions = rolling_contributions + end_padding

        # Shift to align with Sunday at the START
        if rolling_contributions and rolling_contributions[0][0]:
            first_date = datetime.strptime(rolling_contributions[0][0], '%Y-%m-%d')
            shift = (first_date.weekday() + 1) % 7
            if shift > 0:
                start_padding: List[Tuple[Optional[str], int]] = [(None, 0)] * shift
                rolling_contributions = start_padding + rolling_contributions
        elif not rolling_contributions:
            raise Exception(f"No contribution data available for user {args.username}")

        # Now take the LAST 371 days (53 weeks) from this padded list
        # This ensures we have today (and its week) at the very end.
        rolling_contributions = rolling_contributions[-371:]
        
        # Guard: if it's still shorter than 371, pad the start (shouldn't happen with API data)
        while len(rolling_contributions) < 371:
            rolling_contributions = [(None, 0)] + rolling_contributions
        
        year_range = f"{current_year - 1} - {current_year}"
        
        # Ensure output directory matches where we run it from or absolute path
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
