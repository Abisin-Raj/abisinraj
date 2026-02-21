from PIL import Image, ImageDraw
import random
import math

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ─── BANNER: 1200 × 256 ───────────────────────────────────────────────────────
def draw_scene(season, frame, W=1200, H=320):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)

    # ── Palettes ──────────────────────────────────────────────────────────────
    P = {
        "spring":  dict(sky="#87CEFA", mtn="#7B68EE", road="#8B4513",
                        grass="#66CD00", shade="#458B00", trunk="#8B4513",
                        leaf="#FFB7C5", river="#1E90FF", flower="#FF69B4"),
        "summer":  dict(sky="#00BFFF", mtn="#483D8B", road="#A0522D",
                        grass="#32CD32", shade="#006400", trunk="#8B4513",
                        leaf="#228B22", river="#0000CD", flower="#FFD700"),
        "autumn":  dict(sky="#FF7F50", mtn="#8B4513", road="#696969",
                        grass="#DAA520", shade="#8B4513", trunk="#654321",
                        leaf="#FF4500", river="#4682B4", flower="#800000"),
        "winter":  dict(sky="#B0C4DE", mtn="#708090", road="#A9A9A9",
                        grass="#E8F4F8", shade="#AFEEEE", trunk="#2F4F4F",
                        leaf="#D0E8F0", river="#B0E0E6", flower="#FFFFFF"),
        "wasteland": dict(sky="#FFD39B", mtn="#A0522D", road="#D2B48C",
                          grass="#C5A059", shade="#8B4513", trunk="#8B4513",
                          leaf="#556B2F", river="#A0522D", flower="#8B4513"),
    }
    c = {k: hex_to_rgb(v) for k, v in P[season].items()}

    # ── Layout ────────────────────────────────────────────────────────────────
    SKY_H   = int(H * 0.40)   # Increased sky for flying warriors
    ROAD_T  = SKY_H            
    ROAD_B  = int(H * 0.60)   
    SLOPE_B = int(H * 0.80)   

    spd = 6
    if season == "spring":
        spd = 3  # Serene pace for sakura
    shift = frame * spd

    # ── 1. Sky ────────────────────────────────────────────────────────────────
    d.rectangle([0, 0, W, SKY_H], fill=c["sky"] + (255,))

    if season == "wasteland":
        # Arid haze
        for y in range(0, SKY_H, 4):
            alpha = int(100 * (1 - y/SKY_H))
            d.rectangle([0, y, W, y+4], fill=(255, 100, 0, alpha))
    

    # Sun / Moon
    if season == "winter":
        d.ellipse([W-55, 4, W-15, 44], fill=(220, 230, 255, 200))  # pale moon
    elif season == "autumn":
        d.ellipse([W-55, 4, W-15, 44], fill=(255, 140, 0, 200))
    else:
        d.ellipse([W-55, 4, W-15, 44], fill=(255, 255, 200, 200))

    # ── 2. Mountains ──────────────────────────────────────────────────────────
    # Mount Fuji (Spring only)
    if season == "spring":
        fuji_w = 400
        fuji_h = 70
        fuji_x = W // 2 - fuji_w // 2
        fuji_y = SKY_H
        # Main mountain body
        d.polygon([
            (fuji_x, fuji_y), 
            (fuji_x + fuji_w // 2, fuji_y - fuji_h), 
            (fuji_x + fuji_w, fuji_y)
        ], fill=(123, 104, 238, 255)) # Medium slate blue
        # Snow cap
        cap_h = fuji_h // 3
        d.polygon([
            (fuji_x + fuji_w // 2 - fuji_w // 6, fuji_y - fuji_h + cap_h),
            (fuji_x + fuji_w // 2, fuji_y - fuji_h),
            (fuji_x + fuji_w // 2 + fuji_w // 6, fuji_y - fuji_h + cap_h),
            (fuji_x + fuji_w // 2, fuji_y - fuji_h + cap_h + 5)
        ], fill=(255, 255, 255, 255))

    random.seed(11)
    mx = -60
    while mx < W + 60:
        if season == "wasteland":
            # Rock Pillars and Plateaus
            random.seed(mx + 500)
            if random.random() > 0.6: # Plateau
                pw = random.randint(150, 300)
                ph = random.randint(40, 70)
                d.rectangle([mx, SKY_H - ph, mx + pw, SKY_H], fill=c["mtn"] + (255,))
                # Jagged top
                for j in range(mx, mx + pw, 10):
                    jy = SKY_H - ph - random.randint(0, 5)
                    d.rectangle([j, jy, j+10, SKY_H - ph], fill=c["mtn"] + (255,))
                mx += pw
            else: # Pillar
                pw = random.randint(30, 60)
                ph = random.randint(80, 150)
                d.rectangle([mx, SKY_H - ph, mx + pw, SKY_H], fill=c["mtn"] + (255,))
                mx += pw + random.randint(50, 100)
        else:
            ph = 28 + random.randint(-6, 6)
            bw = 65 + random.randint(0, 25)
            d.polygon([(mx, SKY_H), (mx + bw//2, SKY_H - ph), (mx + bw, SKY_H)],
                      fill=c["mtn"] + (255,))
            mx += int(bw * 0.65)
     # ── 3. Trees/Flora (parallax ×0.5) ──────────────────────────────────────────────
    t_scroll = frame * (spd // 2 if season == "spring" else 4)
    random.seed(99)
    n_trees = W // 10
    if season == "spring":
        n_trees = W // 25
    elif season == "wasteland":
        n_trees = W // 40 # Sparse vegetation

    for _ in range(n_trees):
        ox = random.randint(-60, W + 350)
        tx = ox - t_scroll
        if not (-25 < tx < W + 25):
            continue
        ty = ROAD_T + random.randint(-6, 8)
        
        if season == "wasteland":
            # Cacti
            d.rectangle([tx, ty-20, tx+4, ty], fill=(40, 100, 40, 255))
            if random.random() > 0.5:
                # Arm
                d.rectangle([tx+4, ty-15, tx+10, ty-12], fill=(40, 100, 40, 255))
                d.rectangle([tx+8, ty-18, tx+12, ty-12], fill=(40, 100, 40, 255))
        else:
            tw, th = 13, 36
            d.rectangle([tx, ty - th, tx + tw, ty], fill=c["trunk"] + (255,))
            lc = c["leaf"] + (255,)
            d.ellipse([tx-9, ty-th-16, tx+tw//2+1, ty-th+1], fill=lc)
            d.ellipse([tx+tw//2-6, ty-th-16, tx+tw+9, ty-th+1], fill=lc)
            d.ellipse([tx-3, ty-th-27, tx+tw+3, ty-th-4], fill=lc)

            if season == "spring":
                random.seed(abs(int(ox)) * 7)
                for _ in range(4):
                    px = tx + random.randint(-40, 60) - (frame * 0.5)
                    py = ty - random.randint(-10, 40) + (frame * 1.5)
                    d.point((int(px), int(py)), fill=(255, 105, 180, 200))
     # ── 4. Season-specific atmosphere ─────────────────────────────────────────

    # SPRING – Very slow wind lines + pink petals
    if season == "spring":
        # Slow down wind lines speed further
        p_shift = frame * 3
        random.seed(333)
        for _ in range(W // 25):
            ox0 = random.randint(-120, W)
            oy  = random.randint(5, SLOPE_B - 20)
            wx  = (ox0 + p_shift * 1.5) % (W + 120) - 60
            d.line([wx, oy, wx + 40, oy], fill=(255, 255, 255, 70), width=1)
        
        # Drift even more slowly: 1 pixel per frame
        random.seed(9999)
        for _ in range(W // 8):
            ox0 = random.randint(-200, W + 200)
            oy0 = random.randint(-50, H + 50)
            # Drift very slowly: 1 pixel per frame left, 0.5 pixels down
            px = (ox0 - frame * 1) % W
            py = (oy0 + frame * 0.5 + math.sin(frame * 0.3 + ox0) * 4) % H
            # Varied pink shades
            p_col = random.choice([(255, 182, 193, 160), (255, 105, 180, 140), (255, 192, 203, 120)])
            d.rectangle([px, py, px+1, py+1], fill=p_col)

    # SUMMER – heat shimmer dots + golden pollen
    elif season == "summer":
        random.seed(frame * 5 + 2)
        for _ in range(W // 6):
            dx, dy = random.randint(0, W), random.randint(0, H)
            d.point((dx, dy), fill=(255, 255, 180, 130))
        # Subtle horizontal shimmer lines near road
        random.seed(frame + 77)
        for _ in range(8):
            sy = random.randint(ROAD_T + 2, ROAD_B - 2)
            sx = random.randint(0, W - 40)
            d.line([sx, sy, sx + random.randint(15, 40), sy],
                   fill=(255, 255, 255, 60), width=1)

    # AUTUMN – falling leaves + gentle wind
    elif season == "autumn":
        wshift = frame * 10
        random.seed(444)
        for _ in range(W // 28):
            wx0 = random.randint(-80, W)
            wy  = random.randint(5, SLOPE_B)
            wx  = (wx0 + wshift) % (W + 80) - 40
            d.line([wx, wy, wx + 20, wy + 3], fill=(255, 200, 100, 90), width=1)
        # Falling leaf dots
        random.seed(frame * 7 + 3)
        for _ in range(W // 12):
            lx = random.randint(0, W)
            ly = random.randint(0, SLOPE_B)
            leaf_col = random.choice([
                (255, 69, 0, 200), (210, 105, 30, 200), (255, 165, 0, 200)
            ])
            d.rectangle([lx, ly, lx+2, ly+2], fill=leaf_col)

    # WINTER – snowflakes
    elif season == "winter":
        # Snowflakes
        random.seed(frame * 11 + 4)
        for _ in range(W // 20):
            sx = random.randint(0, W)
            sy = (random.randint(0, H) + frame * 3) % H
            d.point((sx, sy), fill=(255, 255, 255, 220))
            
    # WASTELAND – Dust Storm
    elif season == "wasteland":
        random.seed(frame * 2)
        for _ in range(W // 10):
            dx = random.randint(0, W)
            dy = random.randint(0, H)
            size = random.randint(1, 3)
            d.rectangle([dx, dy, dx+size, dy+1], fill=(210, 180, 140, 100))
     # 5. Road ───────────────────────────────────────────────────────────────
    d.rectangle([0, ROAD_T, W, ROAD_B], fill=c["road"] + (255,))
    random.seed(123)
    for _ in range(W * 2):
        ox = random.randint(-W, W * 2)
        ry = random.randint(ROAD_T, ROAD_B)
        rx = (ox - shift) % W
        shade = random.choice([(55, 55, 55), (115, 115, 115)])
        d.point((rx, ry), fill=shade + (255,))
    d.line([0, ROAD_B, W, ROAD_B], fill=(40, 40, 40, 255), width=2)
# Removed duplicate line 177: d.line([0, ROAD_B, W, ROAD_B], fill=(40, 40, 40, 255), width=2)

    # ── 6. Slope ──────────────────────────────────────────────────────────────
    steps = 18
    sh = (SLOPE_B - ROAD_B) / steps
    for i in range(steps):
        sy = ROAD_B + i * sh
        ey = sy + sh + 1
        f  = i / steps
        r, g, b = c["grass"]
        si = 0.5 * (1 - f)
        d.rectangle([0, sy, W, ey],
                    fill=(int(r*(1-si)), int(g*(1-si)), int(b*(1-si)), 255))
    d.line([0, ROAD_B, W, ROAD_B], fill=(200, 200, 200, 90), width=1)

    if season not in ["winter", "wasteland"]:
        random.seed(42)
        for _ in range(W // 4):
            ox = random.randint(0, W)
            fy = random.randint(ROAD_B + 2, SLOPE_B - 2)
            fx = (ox - shift) % W
            d.rectangle([fx, fy, fx+2, fy+2], fill=c["flower"] + (255,))
            d.line([fx+5, fy, fx+5, fy-4], fill=c["shade"] + (255,), width=1)
    elif season == "wasteland":
        # Sand texture
        random.seed(shift)
        for _ in range(W // 2):
            fx = random.randint(0, W)
            fy = random.randint(ROAD_B, SLOPE_B)
            d.point((fx, fy), fill=(139, 69, 19, 100))
    else:
        # Snow on slope
        random.seed(77)
        for _ in range(W // 6):
            ox = random.randint(0, W)
            fy = random.randint(ROAD_B + 1, SLOPE_B - 1)
            fx = (ox - shift) % W
            d.point((fx, fy), fill=(255, 255, 255, 200))

    if season == "wasteland": # No river in wasteland
        d.rectangle([0, SLOPE_B, W, H], fill=c["road"] + (255,))
        random.seed(77)
        for _ in range(W // 2):
            fx = random.randint(0, W)
            fy = random.randint(SLOPE_B, H)
            d.point((fx, fy), fill=(139, 69, 19, 80))
            
        # ── Thor's Hammer (Mjolnir) Easter Egg ──
        hammer_ox = W // 2 + 150
        hx = (hammer_ox - shift + W * 4) % W
        hy = SLOPE_B + 20
        
        # Dirt crater/mound around the hammer
        d.ellipse([hx - 25, hy - 6, hx + 25, hy + 8], fill=(120, 60, 15, 255))
        d.ellipse([hx - 15, hy - 3, hx + 15, hy + 6], fill=(90, 40, 10, 255))
        
        # Mjolnir Head
        d.polygon([
            (hx - 10, hy - 10), (hx + 6, hy - 16), 
            (hx + 14, hy + 2), (hx - 2, hy + 8)
        ], fill=(160, 160, 160, 255))
        
        # Side bevel lighting for 3D effect
        d.polygon([
            (hx - 10, hy - 10), (hx - 2, hy + 8),
            (hx + 2, hy + 6), (hx - 6, hy - 11)
        ], fill=(120, 120, 120, 255))
        
        # Handle pointing UP and slightly RIGHT from the top-center face
        hx_center, hy_center = hx + 2, hy - 7
        hx_end, hy_end = hx + 12, hy - 32
        
        d.line([(hx_center, hy_center), (hx_end, hy_end)], fill=(90, 45, 10, 255), width=4)
        
        # Handle ridges (leather wrap)
        for i in range(1, 6):
            lx = hx_center + int((hx_end - hx_center) * (i / 6.0))
            ly = hy_center + int((hy_end - hy_center) * (i / 6.0))
            d.line([(lx-3, ly+1), (lx+3, ly-1)], fill=(50, 25, 5, 255), width=1)
            
        # Pommel at the top of the handle
        d.ellipse([hx_end - 3, hy_end - 4, hx_end + 3, hy_end + 2], fill=(180, 180, 180, 255))
        
        # Leather strap dangling downwards
        d.arc([hx_end, hy_end, hx_end + 12, hy_end + 15], start=45, end=250, fill=(100, 50, 10, 255), width=1)
            
        # ── Flying Warriors ──────────
        stage = min(4, frame // 3)
        hair_colors = [
            (255, 255, 0, 255),   # Yellow
            (255, 255, 0, 255),   # Yellow
            (255, 255, 0, 255),   # Yellow
            (255, 60, 60, 255),   # Red
            (60, 160, 255, 255),  # Blue
        ]
        
        def draw_warrior(x, y, char_stage, is_char1, f, force_dir=None):
            suit = (255, 120, 0, 255) if is_char1 else (0, 80, 200, 255)
            skin = (255, 210, 170, 255)
            h_col = hair_colors[char_stage]
            aura_rgb = h_col[:3]
            dr = force_dir if force_dir is not None else (1 if is_char1 else -1)

            # Aura removed by user request

            # --- FIGHTING STANCE (MUSCULAR, VARIED POSES) ---
            pose = (f // 3 + (1 if is_char1 else 0)) % 3

            if pose == 0:
                # Pose 0: Standard Punch
                # Front leg
                d.line([x+dr*4, y-2, x+dr*16, y+14], fill=suit, width=9)
                d.line([x+dr*16, y+14, x+dr*19, y+24], fill=suit, width=8)
                bx0, bx1 = sorted([x+dr*15, x+dr*25])
                d.rectangle([bx0, y+22, bx1, y+29], fill=(30, 30, 30, 255))
                # Back leg
                d.line([x-dr*4, y-2, x-dr*14, y+16], fill=suit, width=9)
                d.line([x-dr*14, y+16, x-dr*11, y+24], fill=suit, width=8)
                bx2, bx3 = sorted([x-dr*16, x-dr*7])
                d.rectangle([bx2, y+22, bx3, y+29], fill=(30, 30, 30, 255))
            elif pose == 1:
                # Pose 1: High Knee / Block
                # Front leg (knee up)
                d.line([x+dr*2, y-2, x+dr*15, y+5], fill=suit, width=9)
                d.line([x+dr*15, y+5, x+dr*10, y+15], fill=suit, width=8)
                bx0, bx1 = sorted([x+dr*7, x+dr*15])
                d.rectangle([bx0, y+13, bx1, y+20], fill=(30, 30, 30, 255))
                # Back leg (straight down)
                d.line([x-dr*3, y-2, x-dr*6, y+15], fill=suit, width=9)
                d.line([x-dr*6, y+15, x-dr*5, y+24], fill=suit, width=8)
                bx2, bx3 = sorted([x-dr*9, x-dr*1])
                d.rectangle([bx2, y+22, bx3, y+29], fill=(30, 30, 30, 255))
            else:
                # Pose 2: Wide Stance Upper Body Blast / Guard
                # Front leg
                d.line([x+dr*6, y-2, x+dr*20, y+12], fill=suit, width=9)
                d.line([x+dr*20, y+12, x+dr*22, y+24], fill=suit, width=8)
                bx0, bx1 = sorted([x+dr*18, x+dr*26])
                d.rectangle([bx0, y+22, bx1, y+29], fill=(30, 30, 30, 255))
                # Back leg
                d.line([x-dr*6, y-2, x-dr*20, y+12], fill=suit, width=9)
                d.line([x-dr*20, y+12, x-dr*22, y+24], fill=suit, width=8)
                bx2, bx3 = sorted([x-dr*26, x-dr*18])
                d.rectangle([bx2, y+22, bx3, y+29], fill=(30, 30, 30, 255))

            # Torso (Muscular V-shape)
            d.polygon([
                (x-14, y-16), (x+14, y-16),  # wide shoulders
                (x+8, y+4), (x-8, y+4)       # narrower waist
            ], fill=suit)

            # Shoulder pads (deltoids)
            d.ellipse([x-18, y-20, x-8, y-10], fill=suit)
            d.ellipse([x+8, y-20, x+18, y-10], fill=suit)

            # Head
            d.ellipse([x-6, y-28, x+6, y-16], fill=skin)



            if pose == 0:
                # Forward arm (punching forward — thick)
                ex1, ey1 = x + dr*28, y - 12
                d.line([x+dr*12, y-13, ex1, ey1], fill=suit, width=8)
                d.ellipse([ex1-5, ey1-5, ex1+5, ey1+5], fill=skin)
                # Guard arm (bent, guarding chest — thick)
                d.line([x-dr*12, y-13, x-dr*16, y-4], fill=suit, width=8)
                ex2, ey2 = x - dr*10, y + 2
                d.line([x-dr*16, y-4, ex2, ey2], fill=suit, width=7)
                d.ellipse([ex2-4, ey2-4, ex2+4, ey2+4], fill=skin)
            elif pose == 1:
                # Both arms defending (crossed high)
                d.line([x+dr*10, y-13, x+dr*4, y-6], fill=suit, width=8)
                ex1, ey1 = x-dr*4, y-8
                d.line([x+dr*4, y-6, ex1, ey1], fill=suit, width=7)
                d.ellipse([ex1-4, ey1-4, ex1+4, ey1+4], fill=skin)

                d.line([x-dr*10, y-13, x, y-4], fill=suit, width=8)
                ex2, ey2 = x+dr*6, y-6
                d.line([x, y-4, ex2, ey2], fill=suit, width=7)
                d.ellipse([ex2-4, ey2-4, ex2+4, ey2+4], fill=skin)
            else:
                # Double lower blast/charge
                d.line([x+dr*12, y-13, x+dr*20, y-2], fill=suit, width=8)
                ex1, ey1 = x+dr*25, y+5
                d.line([x+dr*20, y-2, ex1, ey1], fill=suit, width=7)
                d.ellipse([ex1-4, ey1-4, ex1+4, ey1+4], fill=skin)

                d.line([x-dr*12, y-13, x-dr*20, y-2], fill=suit, width=8)
                ex2, ey2 = x-dr*25, y+5
                d.line([x-dr*20, y-2, ex2, ey2], fill=suit, width=7)
                d.ellipse([ex2-4, ey2-4, ex2+4, ey2+4], fill=skin)

            # --- Spiky Hair ---
            ht = y - 28
            if char_stage == 0:
                d.polygon([
                    (x-6, ht), (x-4, ht-10), (x-1, ht-5),
                    (x, ht-16), (x+1, ht-5), (x+4, ht-10),
                    (x+6, ht)
                ], fill=h_col)
            elif char_stage == 1:
                d.polygon([
                    (x-6, ht), (x-5, ht-14), (x-2, ht-7),
                    (x, ht-26), (x+2, ht-7), (x+5, ht-14),
                    (x+6, ht)
                ], fill=h_col)
            elif char_stage == 2:
                if is_char1:
                    d.polygon([
                        (x-6, ht), (x-5, ht-20), (x-3, ht-12),
                        (x-1, ht-34), (x, ht-48),
                        (x+1, ht-34), (x+3, ht-12),
                        (x+5, ht-20), (x+6, ht)
                    ], fill=h_col)
                    for sx in range(-5, 6, 3):
                        d.line([x+sx, ht, x+sx, y+8], fill=h_col, width=2)
                else:
                    d.polygon([
                        (x-6, ht), (x-5, ht-14), (x-2, ht-7),
                        (x, ht-26), (x+2, ht-7), (x+5, ht-14),
                        (x+6, ht)
                    ], fill=h_col)
            elif char_stage >= 3:
                d.polygon([
                    (x-6, ht), (x-4, ht-10), (x-1, ht-5),
                    (x, ht-16), (x+1, ht-5), (x+4, ht-10),
                    (x+6, ht)
                ], fill=h_col)

        # --- Fast Teleporting Combat in the Sky ---
        rng_state = random.getstate()
        
        # New pose/position every 3 frames (stay static for 2 frames, invisible for 1)
        pose_seed = frame // 3
        random.seed(pose_seed + 888)
        
        # Make them invisible 1 out of every 3 frames to look incredibly fast
        is_visible = (frame % 3) != 2 
        
        if is_visible:
            # Pick a random clash point
            cx = random.randint(250, W - 250)
            cy = random.randint(60, SKY_H - 60)
            
            # Distance between them
            dist = random.randint(70, 220)
            
            # 50% chance to swap sides
            swapped = random.random() > 0.5
            dr1 = -1 if swapped else 1
            dr2 = 1 if swapped else -1
            
            # Calculate positions relative to clash point
            c1_x = cx - (dist // 2) * dr1
            c2_x = cx - (dist // 2) * dr2
            
            # Draw warriors with small vertical offsets
            draw_warrior(c1_x, cy + random.randint(-15, 15), stage, True, frame, force_dir=dr1)
            c2_stage = 1 if stage == 2 else stage
            draw_warrior(c2_x, cy + random.randint(-15, 15), c2_stage, False, frame, force_dir=dr2)
            
            # Combat effects depending on distance
            if dist <= 120 and (frame % 3) == 0:
                # Close quarters: physical impact flash (hit!)
                flash_r = random.randint(30, 60)
                # Draw starburst
                d.polygon([
                    (cx, cy - flash_r), (cx + flash_r//4, cy - flash_r//4),
                    (cx + flash_r, cy), (cx + flash_r//4, cy + flash_r//4),
                    (cx, cy + flash_r), (cx - flash_r//4, cy + flash_r//4),
                    (cx - flash_r, cy), (cx - flash_r//4, cy - flash_r//4)
                ], fill=(255, 255, 255, 200))
                # Inner blast
                d.ellipse([cx-15, cy-15, cx+15, cy+15], fill=(255, 255, 0, 255))
            elif dist > 140 and (frame % 3) == 0:
                # Long range: Ki blast!
                if random.random() > 0.5:
                    # Blast from Char 1 to Char 2
                    blast_col = hair_colors[stage]
                    d.line([c1_x + dr1*20, cy, cx + dr1*40, cy], fill=blast_col[:3] + (200,), width=12)
                    d.line([c1_x + dr1*20, cy, cx + dr1*40, cy], fill=(255,255,255,255), width=6)
                    # Blast head
                    bx = cx + dr1*40
                    d.ellipse([bx-12, cy-12, bx+12, cy+12], fill=blast_col[:3] + (255,))
                    d.ellipse([bx-6, cy-6, bx+6, cy+6], fill=(255,255,255,255))
                else:
                    # Blast from Char 2 to Char 1
                    blast_col = hair_colors[c2_stage]
                    d.line([c2_x + dr2*20, cy, cx + dr2*40, cy], fill=blast_col[:3] + (200,), width=12)
                    d.line([c2_x + dr2*20, cy, cx + dr2*40, cy], fill=(255,255,255,255), width=6)
                    # Blast head
                    bx = cx + dr2*40
                    d.ellipse([bx-12, cy-12, bx+12, cy+12], fill=blast_col[:3] + (255,))
                    d.ellipse([bx-6, cy-6, bx+6, cy+6], fill=(255,255,255,255))
        
        random.setstate(rng_state)
    
    if season != "wasteland":
        # ── 7. River ──────────────────────────────────────────────────────────────
        d.rectangle([0, SLOPE_B, W, H], fill=c["river"] + (255,))
        rflow = 0 if season == "winter" else frame * 10
        random.seed(55)
        for _ in range(W // 5):
            ox = random.randint(0, W)
            ry = random.randint(SLOPE_B + 2, H - 2)
            lw = random.randint(10, 35)
            lx = (ox - rflow) % W
            d.line([lx, ry, lx + lw, ry], fill=(255, 255, 255, 110), width=1)
        if season == "winter":
            # Ice cracks
            random.seed(88)
            for _ in range(W // 30):
                ix = random.randint(0, W)
                iy = random.randint(SLOPE_B + 2, H - 2)
                d.line([ix, iy, ix + random.randint(5, 15), iy + random.randint(-2, 2)],
                       fill=(200, 230, 255, 150), width=1)
                       
        # ── 7.5 River Activities ──────────────────────────────────────────────────
        if season in ["spring", "summer"]:
            # People fishing
            random.seed(999) 
            for _ in range(3):
                ox = random.randint(0, W * 2)
                fx = (ox - shift) % W
                fy = SLOPE_B - 20
                # Person sitting
                d.rectangle([fx, fy, fx+12, fy+20], fill=(100, 150, 200, 255)) # body
                d.ellipse([fx+2, fy-12, fx+10, fy-4], fill=(141, 85, 36, 255)) # head (skin tone)
                # Hat for summer
                if season == "summer":
                    d.ellipse([fx-5, fy-12, fx+17, fy-8], fill=(220, 200, 100, 255))
                    d.ellipse([fx+2, fy-16, fx+10, fy-10], fill=(220, 200, 100, 255))
                # Fishing Rod
                d.line([fx+10, fy+8, fx+40, fy-20], fill=(60, 40, 20, 255), width=2)
                # Line
                line_y = SLOPE_B + 20 + abs((frame % 6) - 3) # bobbing
                d.line([fx+40, fy-20, fx+40, line_y], fill=(255, 255, 255, 150), width=1)
                # Bobber
                d.ellipse([fx+38, line_y-2, fx+42, line_y+2], fill=(255, 50, 50, 255))
                
        elif season == "autumn":
            # Fish jumping
            random.seed(frame * 17)
            for _ in range(3):
                jx = random.randint(0, W)
                jy = random.randint(SLOPE_B + 20, H - 20)
                
                # Simple fish shape
                d.ellipse([jx, jy-8, jx+16, jy+2], fill=(180, 200, 200, 255)) # Body
                d.polygon([(jx, jy-3), (jx-6, jy-8), (jx-6, jy+2)], fill=(180, 200, 200, 255)) # Tail
                
                # Splashes
                d.arc([jx-10, jy-5, jx+26, jy+15], start=180, end=0, fill=(255, 255, 255, 200), width=2)
                d.point((jx+5, jy+5), fill=(255, 255, 255, 255))
                d.point((jx+12, jy+8), fill=(255, 255, 255, 255))
                d.point((jx-2, jy+6), fill=(255, 255, 255, 255))

        # ── 7.6 Couples on slope (spring, summer) ─────────────────────────────────
        def draw_pixel_heart(hx, hy, size=2, color=(255, 80, 80, 220)):
            # 7x6 pixel heart grid, each cell = size×size square
            pattern = [
                (1,0),(2,0),(4,0),(5,0),
                (0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
                (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
                (1,3),(2,3),(3,3),(4,3),(5,3),
                (2,4),(3,4),(4,4),
                (3,5),
            ]
            for px, py in pattern:
                rx = hx + (px - 3) * size
                ry = hy + (py - 3) * size
                d.rectangle([rx, ry, rx + size - 1, ry + size - 1], fill=color)

        def draw_broken_heart(hx, hy, progress, size=2):
            # Left half drifts upper-left, right half drifts upper-right
            left_half = [(0,0),(1,0),(0,1),(1,1),(2,1),(0,2),(1,2),(2,2),(1,3),(2,3),(2,4)]
            right_half = [(4,0),(5,0),(3,1),(4,1),(5,1),(6,1),(3,2),(4,2),(5,2),(6,2),(4,3),(5,3),(3,4),(4,4),(3,5)]
            drift = int(progress * 8 * size)
            rise  = int(progress * 5 * size)
            fade  = max(0, int(255 * (1 - progress)))
            col   = (255, 60, 60, fade)
            for px, py in left_half:
                rx = hx + (px - 3) * size - drift
                ry = hy + (py - 3) * size - rise
                d.rectangle([rx, ry, rx + size - 1, ry + size - 1], fill=col)
            for px, py in right_half:
                rx = hx + (px - 3) * size + drift
                ry = hy + (py - 3) * size - rise
                d.rectangle([rx, ry, rx + size - 1, ry + size - 1], fill=col)

        if season in ["spring", "summer"]:
            # Fixed couples: one crosses avatar mid-animation, other stays right of screen
            couple_origins = [W // 2 + 15 * spd, W // 2 + 15 * spd + 450]
            for ci, ox in enumerate(couple_origins):
                cpx = (ox - shift + W * 4) % W
                cpy = ROAD_B + (SLOPE_B - ROAD_B) * 2 // 3

                skin_c  = (141, 85, 36, 255)
                dress_c = (255, 160, 185, 255) if season == "spring" else (255, 215, 100, 255)
                shirt_c = (80,  110, 200, 255) if season == "spring" else (60,  180, 100, 255)

                # -- Couple figures --
                d.rectangle([cpx - 12, cpy - 16, cpx - 5,  cpy], fill=dress_c)
                d.ellipse  ([cpx - 13, cpy - 26, cpx - 4,  cpy - 16], fill=skin_c)
                d.rectangle([cpx + 5,  cpy - 16, cpx + 12, cpy], fill=shirt_c)
                d.ellipse  ([cpx + 3,  cpy - 26, cpx + 13, cpy - 16], fill=skin_c)

                # -- Umbrella dome (chord = arc + straight chord, gives flat-bottom dome) --
                umb_fill  = (255, 190, 210, 240) if season == "spring" else (255, 235, 80, 240)
                umb_edge  = (220, 100, 140, 255) if season == "spring" else (200, 170, 30, 255)
                d.chord([cpx - 26, cpy - 54, cpx + 26, cpy - 18],
                        start=180, end=360, fill=umb_fill, outline=umb_edge)
                # Scallop bumps along bottom edge of dome
                for i in range(5):
                    bx = cpx - 20 + i * 10
                    d.ellipse([bx - 4, cpy - 22, bx + 4, cpy - 14], fill=umb_fill, outline=umb_edge)
                # Handle
                d.line([cpx, cpy - 18, cpx, cpy - 2], fill=(110, 70, 40, 255), width=2)

                # -- Rising heart from couple: rises 5px per frame, fades out, resets each cycle --
                h_rise  = (frame * 4) % 50          # 0..50 over 16 frames
                h_alpha = max(20, 230 - h_rise * 5)
                h_y     = cpy - 60 - h_rise
                draw_pixel_heart(cpx, h_y, size=2, color=(255, 80, 110, h_alpha))

        # --- Captain America "On your left" in Summer ---
        if season == "summer":
            # Runs very fast across the screen (left to right)
            cap_x = -150 + frame * 105
            cap_y = ROAD_B + 10
            
            if -50 < cap_x < W + 100:
                # Legs running (fast)
                run_t = (frame % 4) / 4.0
                r_leg_x = 15 * math.sin(run_t * 2 * math.pi)
                l_leg_x = 15 * math.sin((run_t + 0.5) * 2 * math.pi)
                
                d.line([cap_x, cap_y-8, cap_x + int(r_leg_x), cap_y+12], fill=(30, 40, 160, 255), width=7)
                d.line([cap_x, cap_y-8, cap_x + int(l_leg_x), cap_y+12], fill=(30, 40, 160, 255), width=7)
                
                # Boots
                d.rectangle([cap_x + int(r_leg_x) - 4, cap_y+5, cap_x + int(r_leg_x) + 4, cap_y+12], fill=(160, 30, 30, 255))
                d.rectangle([cap_x + int(l_leg_x) - 4, cap_y+5, cap_x + int(l_leg_x) + 4, cap_y+12], fill=(160, 30, 30, 255))

                # Body (Blue uniform)
                d.rectangle([cap_x-9, cap_y-25, cap_x+7, cap_y-8], fill=(30, 40, 160, 255))
                # Star on chest
                d.point((cap_x-1, cap_y-18), fill=(255, 255, 255, 255))
                
                # Head (Blue helmet)
                d.ellipse([cap_x-6, cap_y-36, cap_x+6, cap_y-23], fill=(30, 40, 160, 255))
                d.ellipse([cap_x-4, cap_y-30, cap_x+6, cap_y-23], fill=(255, 210, 170, 255)) # Face peeking out
                
                # Shield swinging on the arm facing us
                shield_x = cap_x + int(8 * math.sin((run_t + 0.25) * 2 * math.pi))
                shield_y = cap_y - 14
                d.ellipse([shield_x-9, shield_y-9, shield_x+9, shield_y+9], fill=(200, 30, 30, 255))
                d.ellipse([shield_x-6, shield_y-6, shield_x+6, shield_y+6], fill=(240, 240, 240, 255))
                d.ellipse([shield_x-3, shield_y-3, shield_x+3, shield_y+3], fill=(30, 40, 160, 255))
                d.point((shield_x, shield_y), fill=(255, 255, 255, 255)) # tiny star center
                
                # Dialog box "On your left"
                # Showing it only when he's reasonably close to the center
                if cap_x > 100 and cap_x < W - 100:
                    bx = cap_x - 10
                    by = cap_y - 65
                    d.rectangle([bx-10, by-8, bx+75, by+10], fill=(255, 255, 255, 200), outline=(0,0,0,150))
                    # Tail of the speech bubble
                    d.polygon([(bx+15, by+10), (bx+25, by+10), (bx+10, by+18)], fill=(255, 255, 255, 200))
                    # Text!
                    d.text((bx-4, by-4), "On your left.", fill=(0, 0, 0, 255))

    # ── 8. Avatar ─────────────────────────────────────────────────────────────

    cx   = W // 2
    foot = ROAD_B - 4
    skin = hex_to_rgb("#8D5524")
    hair = hex_to_rgb("#1A0A00")
    blue_jeans = (30, 30, 140, 255)

    shirts = {
        "spring": (144, 238, 144, 255),
        "summer": (0, 191, 255, 255),
        "autumn": (139, 69, 19, 255),
        "winter": (60, 80, 200, 255),
        "wasteland": (255, 140, 0, 255),
    }
    shirt = shirts[season]

    # Walk cycle
    t = (frame % 8) / 8.0
    hip_x, hip_y = cx, foot - 22

    r_leg = 35 * math.sin(t * 2 * math.pi)
    l_leg = 35 * math.sin(t * 2 * math.pi + math.pi)

    def leg(hx, hy, angle, col):
        rad = math.radians(angle)
        kx = hx + 8 * math.sin(rad)
        ky = hy + 8 * math.cos(rad)
        d.line([hx, hy, kx, ky], fill=col, width=6)   # thigh
        bend = -12 if angle > 0 else 0
        rad2 = math.radians(angle + bend)
        fx = kx + 9 * math.sin(rad2)
        fy = ky + 9 * math.cos(rad2)
        d.line([kx, ky, fx, fy], fill=col, width=4)   # calf

    # Back leg
    leg(hip_x, hip_y, l_leg, blue_jeans)

    # Body
    d.rectangle([cx-7, hip_y-17, cx+7, hip_y], fill=shirt)

    # Front leg
    leg(hip_x, hip_y, r_leg, blue_jeans)

    # Head
    hy2 = hip_y - 28
    d.rectangle([cx-6, hy2, cx+6, hy2+11], fill=skin + (255,))
    d.rectangle([cx-7, hy2-3, cx+7, hy2+4], fill=hair + (255,))
    d.rectangle([cx-7, hy2, cx-5, hy2+9], fill=hair + (255,))

    # Arm (right, swings opposite to right leg)
    r_arm = 35 * math.sin(t * 2 * math.pi + math.pi)
    sho_y = hip_y - 13
    rad_a = math.radians(r_arm)
    ex = cx + 5 * math.sin(rad_a)
    ey = sho_y + 5 * math.cos(rad_a)
    d.line([cx, sho_y, ex, ey], fill=shirt, width=4)
    hx2 = ex + 5 * math.sin(rad_a - 0.2)
    hy3 = ey + 5 * math.cos(rad_a - 0.2)
    d.line([ex, ey, hx2, hy3], fill=skin + (255,), width=3)

    # ── Props ─────────────────────────────────────────────────────────────────
    # Walkman (small blue rectangle on hip)
    wm_x, wm_y = cx + 4, hip_y - 10
    d.rectangle([wm_x, wm_y, wm_x + 4, wm_y + 6], fill=(20, 40, 150, 255)) # Blue Walkman
    
    # Headphones (headband and ear cups)
    # Headband
    d.arc([cx-7, hy2-4, cx+7, hy2+4], start=180, end=0, fill=(40, 40, 40, 255), width=2)
    # Ear cups
    d.rectangle([cx-8, hy2+4, cx-5, hy2+9], fill=(20, 20, 20, 255))
    d.rectangle([cx+5, hy2+4, cx+8, hy2+9], fill=(20, 20, 20, 255))
    
    # Wire (from walkman to ear cup)
    d.line([wm_x + 2, wm_y, cx + 6, hy2 + 7], fill=(30, 30, 30, 180), width=1)

    # Music notes OR breaking heart depending on proximity to couple
    if season != "wasteland":
        near_couple = False
        couple_prox = 0.0
        if season in ["spring", "summer"]:
            spd_local = {"spring": 3, "summer": 6}.get(season, 6)
            couple_origins_check = [W // 2 + 15 * spd_local, W // 2 + 15 * spd_local + 450]
            shift_check = frame * spd_local
            for ox_c in couple_origins_check:
                cpx_c = (ox_c - shift_check + W * 4) % W
                d_c = abs(cpx_c - cx)
                if d_c < 90:
                    near_couple = True
                    couple_prox = (90 - d_c) / 90.0

        if near_couple:
            # Draw breaking heart above head instead of music notes
            hx = cx + 14
            hy_base = hy2 - 18 - int(couple_prox * 10)
            if couple_prox >= 0.55:
                # Break: left half drifts left+up, right half drifts right+up
                bp = min(1.0, (couple_prox - 0.55) / 0.45)
                drift = int(bp * 10)
                rise  = int(bp * 6)
                fade  = max(0, int(220 * (1 - bp)))
                col   = (255, 60, 60, fade)
                lh = [(0,0),(1,0),(0,1),(1,1),(2,1),(0,2),(1,2),(2,2),(1,3),(2,3),(2,4)]
                rh = [(4,0),(5,0),(3,1),(4,1),(5,1),(6,1),(3,2),(4,2),(5,2),(6,2),(4,3),(5,3),(3,4),(4,4),(3,5)]
                for px, py in lh:
                    rx = hx + (px - 3) * 2 - drift
                    ry = hy_base + (py - 3) * 2 - rise
                    d.rectangle([rx, ry, rx + 1, ry + 1], fill=col)
                for px, py in rh:
                    rx = hx + (px - 3) * 2 + drift
                    ry = hy_base + (py - 3) * 2 - rise
                    d.rectangle([rx, ry, rx + 1, ry + 1], fill=col)
            else:
                # Solid heart rising toward the couple
                alpha = int(220 * couple_prox)
                pattern = [(1,0),(2,0),(4,0),(5,0),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
                           (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(1,3),(2,3),(3,3),(4,3),(5,3),
                           (2,4),(3,4),(4,4),(3,5)]
                for px, py in pattern:
                    rx = hx + (px - 3) * 2
                    ry = hy_base + (py - 3) * 2
                    d.rectangle([rx, ry, rx + 1, ry + 1], fill=(255, 80, 100, alpha))
        else:
            # Normal: music notes float upward
            for i in range(2):
                nx_off = 15 + i * 12
                ny_off = -10 - (frame % 4) * 2 - i * 5
                nx, ny = cx + nx_off, hy2 + ny_off
                d.ellipse([nx, ny, nx + 4, ny + 3], fill=(255, 255, 255, 180))
                d.line([nx + 3, ny + 1, nx + 3, ny - 6], fill=(255, 255, 255, 180), width=1)
                if i % 2 == 0:
                    d.line([nx + 3, ny - 6, nx + 7, ny - 4], fill=(255, 255, 255, 180), width=1)


    if season == "autumn":
        # Bug-catching net
        l_arm = 35 * math.sin(t * 2 * math.pi)
        rad_la = math.radians(l_arm)
        lex = cx - 5 * math.sin(rad_la)
        ley = sho_y + 5 * math.cos(rad_la)
        nx_net, ny_net = int(lex) + 6, int(ley) - 4
        d.line([nx_net, ny_net, nx_net + 12, ny_net - 14], fill=(100, 60, 20, 255), width=2)
        d.ellipse([nx_net + 8, ny_net - 20, nx_net + 20, ny_net - 8],
                  outline=(180, 180, 180, 220), width=1)

    return img


if __name__ == "__main__":
    frames = []
    for season in ["spring", "summer", "autumn", "winter", "wasteland"]:
        for i in range(16):
            frames.append(draw_scene(season, i, H=320))

    out = "/home/abisin/Desktop/abisinraj/assets/seasons_walking.gif"
    frames[0].save(
        out, save_all=True, append_images=frames[1:],
        optimize=False, duration=180, loop=0
    )
    print(f"Banner GIF saved → {out}")
