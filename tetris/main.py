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
    height = 7  # 7 days per week
    width = (len(contributions) + height - 1) // height
    cell_size = 40
    legend_width = 80
    image_width = width * cell_size + legend_width + 20 # Reduced extra padding
    image_height = height * cell_size + 80 # Reduced vertical padding

    # Theme Configuration
    class Theme(TypedDict):
        background: str
        text: Tuple[int, int, int]
        colors: List[str]

    THEMES: Dict[str, Theme] = {
        'light': {
            'background': '#ffffff',
            'text': (36, 41, 47),
            'colors': ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127', '#103d19']
        },
        'dark': {
            'background': '#0d1117',
            'text': (201, 209, 217), # GitHub Dark Text
            'colors': ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353', '#72ff88']
        }
    }
    
    theme_colors = THEMES.get(theme, THEMES['light'])
    colors = theme_colors['colors']
    background_color = theme_colors['background']

    frames: List[Image.Image] = []
    # Map counts to color index (0-5)
    # 0 -> 0, 1-10 -> 1, 11-20 -> 2, 21-30 -> 3, 31-40 -> 4, 41+ -> 5
    grid: List[List[int]] = [[0] * height for _ in range(width)]
    coord_to_val = {}
    
    for i, (date, count) in enumerate(contributions):
        week = i // 7
        day = i % 7
        if week >= width: continue
        
        if count == 0: val = 0
        elif count <= 10: val = 1
        elif count <= 20: val = 2
        elif count <= 30: val = 3
        elif count <= 40: val = 4
        else: val = 5
        
        grid[week][day] = val
        if date:
            coord_to_val[(week, day)] = val

    # Debug output removed to keep logs clean

    # Pre-calculate month labels to avoid slow datetime parsing in animation loop
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels = []
    last_m = -1
    last_x = -999  # track last label x position to prevent overlap
    LABEL_WIDTH = 45
    for i, (date_str, count) in enumerate(contributions):
        if not date_str: continue
        d_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        m = d_obj.month
        if m != last_m:
            x = (i // 7) * cell_size + legend_width
            if x > last_x + LABEL_WIDTH:
                month_labels.append((x, month_names[m-1]))
                last_x = x
            last_m = m

    # Debug: verify last few days coordinates
    print("Debug - Last 21 days positioning:")
    first_week_with_data = width
    for i in range(len(contributions)):
        d, c = contributions[i]
        if c > 0:
            first_week_with_data = min(first_week_with_data, i // 7)
        if i >= len(contributions)-21:
            w, dy = i // 7, i % 7
            print(f"  {d} -> Grid[{w}][{dy}] = {grid[w][dy]}")
    
    if first_week_with_data == width: first_week_with_data = 0
    print(f"First week with data: {first_week_with_data}")

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

    # Reset grid for animation (background stays)
    # Background (val 0) is placed immediately, non-zero pieces fall
    animated_grid = [[0] * height for _ in range(width)]
    assigned = [[False]*height for _ in range(width)]
    
    # Fill level 0 in animated_grid and mark assigned
    for wx in range(width):
        for dy in range(height):
            if (wx, dy) not in coord_to_val or coord_to_val[(wx, dy)] == 0:
                animated_grid[wx][dy] = grid[wx][dy]
                assigned[wx][dy] = True

    final_pieces = []
    for x in range(width):
        # We process from bottom-up (Saturday to Sunday) to prioritize pieces at the bottom
        for y in range(height-1, -1, -1):
            if assigned[x][y]: continue
            
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
                        nx, ny = x+dx, y+dy
                        assigned[nx][ny] = True
                        cell_val = coord_to_val.get((nx, ny), 1)
                        shape_cells.append((nx, ny, cell_val))
                    
                    final_pieces.append({
                        "cells": shape_cells,
                        "min_y": min(c[1] for c in shape_cells),
                        "max_y": max(c[1] for c in shape_cells),
                        "min_x": min(c[0] for c in shape_cells),
                        "start_frame": max(0, (x - first_week_with_data)) * 4 # Optimized cascade
                    })
                    break

    max_frames = width * 10 # More than enough
    
    # Store current falling y offsets
    for p in final_pieces:
        p["curr_y_offset"] = -(p["max_y"] + 1) # Start completely above the board

    print(f"  Animating {len(final_pieces)} group pieces...")
    for frame in range(max_frames):
        # --- 1. UPDATE STATE FIRST ---
        moved_any = False
        for p in final_pieces:
            if frame >= p["start_frame"]:
                if p["curr_y_offset"] < 0:
                    p["curr_y_offset"] += 1
                    moved_any = True
                elif p["curr_y_offset"] == 0 and not p.get("landed"):
                    # Just landed, add to animated grid
                    for cx, cy, cv in p["cells"]:
                        animated_grid[cx][cy] = cv
                    p["landed"] = True
                    moved_any = True
        
        # --- 2. DRAW AFTER STATE UPDATE ---
        img = Image.new('RGB', (image_width, image_height), background_color)
        draw = ImageDraw.Draw(img)
        draw_legend(draw, cell_size, image_width, image_height, username, year_range, theme_colors, month_labels)
        draw_grid(draw, animated_grid, cell_size, colors, theme_colors)
        
        # Draw falling pieces (still in the air)
        for p in final_pieces:
            if frame >= p["start_frame"] and p["curr_y_offset"] < 0:
                for cx, cy, cv in p["cells"]:
                    x0 = cx * cell_size + legend_width + 2
                    y0 = (cy + p["curr_y_offset"]) * cell_size + 40 + 2
                    # Define clip box to only show pieces within the grid vertically
                    x1, y1 = x0 + cell_size - 4, y0 + cell_size - 4
                    if y1 > 40: # Only draw if part of the cell is below the header
                        draw.rounded_rectangle([x0, max(40, y0), x1, y1], radius=8, fill=colors[cv], outline=(255, 255, 255, 50))
                        
        # --- 3. APPEND FRAME ---
        frames.append(img)

        # End early if all pieces have landed
        if len(final_pieces) > 0 and all(p.get("landed") for p in final_pieces):
            # Add a 10-second static pause of the COMPLETE final image
            for _ in range(100):
                frames.append(img.copy())
            break


    # Save as animated GIF
    if len(frames) == 0:
        raise Exception("No frames generated. Check contribution data.")
        
    # Ensure output directory exists before saving
    import os
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    frames[0].save(output_path, save_all=True, append_images=frames[1:], optimize=True, duration=100, loop=0)

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
        # Custom window: Sunday 52 weeks ago to the coming Saturday
        days_to_sat = (5 - today.weekday()) % 7
        end_date = today + timedelta(days=days_to_sat)
        start_date = end_date - timedelta(days=52 * 7 + 6) # Sunday 53 weeks ago (total 372 days)
        # Actually let's just make it exactly 53 weeks = 371 days
        start_date = end_date - timedelta(days=370) # Sat - 370 = Sun
        
        today = datetime.now().date()
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({len(all_map)} total days in map)")
        
        rolling_contributions: List[Tuple[Optional[str], int]] = []
        d = start_date
        while d <= end_date:
            ds = d.strftime('%Y-%m-%d')
            count = all_map.get(ds, 0)
            if d.date() <= today:
                rolling_contributions.append((ds, count))
            else:
                rolling_contributions.append((None, 0))
            d += timedelta(days=1)
        
        print(f"Total days: {len(rolling_contributions)}")
        print("Last 7 days:")
        for ds, c in rolling_contributions[-7:]:
            print(f"  {ds}: {c}")
        
        year_range = f"{current_year - 1} - {current_year}"
        create_tetris_gif(args.username, current_year, rolling_contributions, args.output, args.theme, year_range)
        print("GIF created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
