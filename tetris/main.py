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

def draw_grid(draw, grid, cell_size, colors):
    for week in range(len(grid)):
        for day in range(len(grid[0])):
            color = colors[grid[week][day]]
            # 2px padding for tighter GitHub-like appearance at 40px resolution
            x0, y0 = week * cell_size + 80 + 2, day * cell_size + 40 + 2
            x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
            # Block
            draw.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=color, outline=(255, 255, 255, 20))

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

    # Prepare batches by color level
    batches: List[List[Tuple[int, int, int]]] = [[] for _ in range(5)]
    for i, (date, count) in enumerate(contributions):
        week = i // 7
        day = i % 7
        if week >= width: break
        
        # Map count to color index (0-4)
        if count == 0: val = 0
        elif count <= 3: val = 1
        elif count <= 6: val = 2
        elif count <= 9: val = 3
        else: val = 4
        
        if date:
            batches[val].append((week, day, val))
        else:
            # Padding elements just fill the grid immediately
            grid[week][day] = val

    # Pre-calculate month labels to avoid slow datetime parsing in animation loop
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels = []
    last_m = -1
    last_x = -999  # track last label x position to prevent overlap
    MIN_LABEL_GAP = cell_size * 3  # at least 3 weeks (120px) between labels
    for i, (date_str, count) in enumerate(contributions):
        if not date_str: continue
        m = datetime.strptime(date_str, '%Y-%m-%d').month
        if m != last_m:
            x = (i // 7) * cell_size + 80
            if x - last_x >= MIN_LABEL_GAP:  # only draw if enough space
                month_labels.append((x, month_names[m-1]))
                last_x = x
            last_m = m

    # ... in loops replace draw_legend calls:
    # draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
    
    # Animate each level batch
    print(f"Generating GIF for {username} - Theme: {theme}")
    for level in range(5):
        batch = batches[level]
        if not batch: continue
        print(f"  Animating Level {level} batch ({len(batch)} blocks)...")
        
        # Determine max falling height in this batch
        max_day = max(b[1] for b in batch)
        
        # Simultaneous falling animation
        for step in range(max_day + 1):
            if step % 2 != 0: continue # Adjust speed
            
            img = Image.new('RGB', (image_width, image_height), background_color)
            draw = ImageDraw.Draw(img)
            draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
            draw_grid(draw, grid, cell_size, colors)
            
            for week, day, val in batch:
                current_step = min(step, day)
                x_base = week * cell_size + legend_width
                y_base = current_step * cell_size + 40
                
                # All blocks in the batch fall together
                x0, y0 = x_base + 2, y_base + 2
                x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
                draw.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=colors[val], outline=(255, 255, 255, 50))
            
            frames.append(img)

        # Post-falling logic for the batch
        if level == 0:
            # Simultaneous shatter for ALL grey blocks in this batch
            for frame_idx in range(4):
                img = Image.new('RGB', (image_width, image_height), background_color)
                draw = ImageDraw.Draw(img)
                draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
                draw_grid(draw, grid, cell_size, colors)
                
                alpha = 255 - (frame_idx * 60)
                for week, day, val in batch:
                    x_base = week * cell_size + legend_width
                    y_base = day * cell_size + 40
                    for _ in range(5):
                        frag_x = x_base + random.randint(0, cell_size - 10)
                        frag_y = y_base + random.randint(0, cell_size - 10)
                        size = random.randint(4, 8)
                        draw.rounded_rectangle([frag_x, frag_y, frag_x + size, frag_y + size], radius=2, fill=colors[0], outline=(255, 255, 255, alpha))
                frames.append(img)
        else:
            for week, day, val in batch:
                grid[week][day] = val
                
            # Batch fade animation
            for alpha in range(0, 256, 128):
                img = Image.new('RGB', (image_width, image_height), background_color)
                draw = ImageDraw.Draw(img)
                draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
                draw_grid(draw, grid, cell_size, colors)
                
                for week, day, val in batch:
                    x0, y0 = week * cell_size + legend_width + 2, day * cell_size + 40 + 2
                    x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
                    draw.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=colors[val], outline=(255, 255, 255, alpha))
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
