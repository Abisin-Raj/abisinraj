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
    for week in range(len(grid)):
        for day in range(len(grid[0])):
            color = colors[grid[week][day]]
            x0, y0 = week * cell_size + 80 + 2, day * cell_size + 40 + 2
            x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=color)

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
    image_height = height * cell_size + 60  # Extra bottom padding so Saturday row isn't clipped

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
    LABEL_WIDTH = 30  # approx pixel width of a 3-char label at font size 16
    for i, (date_str, count) in enumerate(contributions):
        if not date_str: continue
        m = datetime.strptime(date_str, '%Y-%m-%d').month
        if m != last_m:
            x = (i // 7) * cell_size + 80
            # If too close to previous label, nudge right just enough to clear it
            if x < last_x + LABEL_WIDTH + 4:
                x = last_x + LABEL_WIDTH + 4
            month_labels.append((x, month_names[m-1]))
            last_x = x
            last_m = m

    # ... in loops replace draw_legend calls:
    # draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
    
    # Animate each level batch
    print(f"Generating GIF for {username} - Theme: {theme}")

    # Animate each group of cells falling like actual pieces
    print(f"Generating GIF for {username} - Theme: {theme}")

    shapes = [
        [(0,0), (1,0), (2,0), (3,0)], [(0,0), (0,1), (0,2), (0,3)], [(0,0), (1,0), (0,1), (1,1)],
        [(0,0), (0,1), (0,2), (1,2)], [(0,0), (1,0), (2,0), (0,1)], [(0,0), (1,0), (1,1), (1,2)], [(2,0), (0,1), (1,1), (2,1)],
        [(1,0), (1,1), (1,2), (0,2)], [(0,0), (0,1), (1,1), (2,1)], [(0,0), (1,0), (0,1), (0,2)], [(0,0), (1,0), (2,0), (2,1)],
        [(0,0), (1,0), (2,0), (1,1)], [(1,0), (0,1), (1,1), (1,2)], [(1,0), (0,1), (1,1), (2,1)], [(0,0), (0,1), (0,2), (1,1)],
        [(1,0), (2,0), (0,1), (1,1)], [(0,0), (0,1), (1,1), (1,2)], [(0,0), (1,0), (1,1), (2,1)], [(1,0), (1,1), (0,1), (0,2)]
    ]
    normalized_shapes = []
    for s in shapes:
        ax = min(p[0] for p in s)
        ay = max(p[1] for p in s if p[0] == ax)
        normalized_shapes.append([(p[0]-ax, p[1]-ay) for p in s])
    normalized_shapes.extend([
        [(0,0), (1,0), (2,0)], [(0,0), (0,-1), (0,-2)], [(0,0), (1,0), (0,-1)], [(0,0), (1,0), (1,-1)], [(0,0), (0,-1), (1,-1)], [(0,0), (0,-1), (-1,-1)],
        [(0,0), (1,0)], [(0,0), (0,-1)], [(0,0)]
    ])
    fixed_shapes = []
    for norm in normalized_shapes:
        ax = min(p[0] for p in norm)
        ay = max(p[1] for p in norm if p[0] == ax)
        fixed = tuple(sorted([(p[0]-ax, p[1]-ay) for p in norm]))
        if fixed not in fixed_shapes:
            fixed_shapes.append(fixed)

    # Place level-0 directly to avoid animating empty squares (save time)
    for bx, by, v in batches[0]:
        grid[bx][by] = v

    assigned = [[False]*height for _ in range(width)]
    for bx, by, _ in batches[0]:
        assigned[bx][by] = True # Don't form pieces from background zeros

    final_pieces = []
    for x in range(width):
        for y in range(height-1, -1, -1):
            if assigned[x][y]: continue
            placed = False
            for shape in fixed_shapes:
                valid = True
                for dx, dy in shape:
                    nx, ny = x+dx, y+dy
                    if nx < 0 or nx >= width or ny < 0 or ny >= height or assigned[nx][ny]:
                        valid = False
                        break
                if valid:
                    shape_cells = []
                    for dx, dy in shape:
                        assigned[x+dx][y+dy] = True
                        # Find the color value for this cell
                        cell_val = 1
                        for l in range(1, 5):
                            for cx, cy, cv in batches[l]:
                                if cx == x+dx and cy == y+dy: cell_val = cv
                        shape_cells.append((x+dx, y+dy, cell_val))
                    final_pieces.append({
                        "cells": shape_cells,
                        "min_y": min(c[1] for c in shape_cells),
                        "max_y": max(c[1] for c in shape_cells),
                        "min_x": min(c[0] for c in shape_cells),
                        "start_frame": x * 2  # Cascade from left to right!
                    })
                    break

    max_frames = width * 2 + height + 10
    
    # Store current falling y offsets
    for p in final_pieces:
        p["curr_y_offset"] = -(p["max_y"] + 1) # Start completely above the board

    print(f"  Animating {len(final_pieces)} group pieces...")
    for frame in range(max_frames):
        moved_any = False
        img = Image.new('RGB', (image_width, image_height), background_color)
        draw = ImageDraw.Draw(img)
        draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
        draw_grid(draw, grid, cell_size, colors, theme_colors)
        
        for p in final_pieces:
            if frame >= p["start_frame"]:
                if p["curr_y_offset"] < 0:
                    p["curr_y_offset"] += 1
                    moved_any = True
                elif p["curr_y_offset"] == 0 and not p.get("landed"):
                    # Just landed, add to background grid
                    for cx, cy, cv in p["cells"]:
                        grid[cx][cy] = cv
                    p["landed"] = True
                    moved_any = True
        
        # Draw falling pieces
        for p in final_pieces:
            if frame >= p["start_frame"] and p["curr_y_offset"] < 0:
                for cx, cy, cv in p["cells"]:
                    x0 = cx * cell_size + legend_width + 2
                    y0 = (cy + p["curr_y_offset"]) * cell_size + 40 + 2
                    if y0 >= 40: # Only draw if it's on the board
                        x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
                        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=colors[cv], outline=(255, 255, 255, 50))
                        
        if moved_any:
            frames.append(img)
        # End early if all pieces have landed
        if all(p.get("landed") for p in final_pieces):
            break


    # Save as animated GIF
    if len(frames) == 0:
        raise Exception("No frames generated. Check contribution data.")
    frames[0].save(output_path, save_all=True, append_images=frames[1:], optimize=False, duration=50, loop=0)

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
        
        # Combine, deduplicate by date, and sort
        all_map: Dict[str, int] = {}
        for d, c in contributions_prev + contributions_current:
            if d:
                all_map[d] = c  # later entries (current year) overwrite dupes
        
        # Build a day-by-day list from exactly 1 year ago to today
        today = datetime.now()
        # GitHub graph ends on the current Saturday (or today if Saturday)
        # and starts 52 weeks before the prior Sunday
        # Find the Saturday >= today
        days_to_sat = (5 - today.weekday()) % 7
        end_date = today + timedelta(days=days_to_sat)
        # Start from 52 weeks before the Sunday before end_date
        start_date = end_date - timedelta(days=52 * 7 + 6)  # 53 weeks = 371 days
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        rolling_contributions: List[Tuple[Optional[str], int]] = []
        d = start_date
        while d <= end_date:
            ds = d.strftime('%Y-%m-%d')
            count = all_map.get(ds, 0)
            if d <= today:
                rolling_contributions.append((ds, count))
            else:
                rolling_contributions.append((None, 0))  # future padding
            d += timedelta(days=1)
        
        print(f"Total days in window: {len(rolling_contributions)}")
        if rolling_contributions and rolling_contributions[0][0]:
            print(f"First date: {rolling_contributions[0][0]}")
        if rolling_contributions and rolling_contributions[-1][0]:
            print(f"Last date: {rolling_contributions[-1][0]}")
        
        year_range = f"{current_year - 1} - {current_year}"
        
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
