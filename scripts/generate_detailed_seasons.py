from PIL import Image, ImageDraw
import random
import math

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ─── BANNER: 1200 × 256 ───────────────────────────────────────────────────────
def draw_scene(season, frame, W=1200, H=256):
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
    }
    c = {k: hex_to_rgb(v) for k, v in P[season].items()}

    # ── Layout ────────────────────────────────────────────────────────────────
    SKY_H   = int(H * 0.30)   # 0–38
    ROAD_T  = SKY_H            # 38
    ROAD_B  = int(H * 0.50)   # 64
    SLOPE_B = int(H * 0.75)   # 96

    spd = 6
    if season == "spring":
        spd = 3  # Serene pace for sakura
    shift = frame * spd

    # ── 1. Sky ────────────────────────────────────────────────────────────────
    d.rectangle([0, 0, W, SKY_H], fill=c["sky"] + (255,))

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
        ph = 28 + random.randint(-6, 6)
        bw = 65 + random.randint(0, 25)
        d.polygon([(mx, SKY_H), (mx + bw//2, SKY_H - ph), (mx + bw, SKY_H)],
                  fill=c["mtn"] + (255,))
        mx += int(bw * 0.65)

    # ── 3. Trees (parallax ×0.5) ──────────────────────────────────────────────
    t_scroll = frame * (spd // 2 if season == "spring" else 4)
    random.seed(99)
    n_trees = W // 10
    if season == "spring":
        n_trees = W // 25  # Fewer trees for a more open, serene sakura park feel
    for _ in range(n_trees):
        ox = random.randint(-60, W + 350)
        tx = ox - t_scroll
        if not (-25 < tx < W + 25):
            continue
        ty = ROAD_T + random.randint(-6, 8)
        tw, th = 13, 36

        d.rectangle([tx, ty - th, tx + tw, ty], fill=c["trunk"] + (255,))
        lc = c["leaf"] + (255,)
        d.ellipse([tx-9, ty-th-16, tx+tw//2+1, ty-th+1], fill=lc)
        d.ellipse([tx+tw//2-6, ty-th-16, tx+tw+9, ty-th+1], fill=lc)
        d.ellipse([tx-3, ty-th-27, tx+tw+3, ty-th-4], fill=lc)

        # Spring: falling petals (local to tree)
        if season == "spring":
            # Use a stable seed for positions but add a slow falling offset
            random.seed(abs(int(ox)) * 7) # Fixed seed based on tree's original position
            for _ in range(4):
                # Petals fall slowly: (frame * 2) pixels down
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

    # ── 5. Road ───────────────────────────────────────────────────────────────
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

    if season != "winter":
        random.seed(42)
        for _ in range(W // 4):
            ox = random.randint(0, W)
            fy = random.randint(ROAD_B + 2, SLOPE_B - 2)
            fx = (ox - shift) % W
            d.rectangle([fx, fy, fx+2, fy+2], fill=c["flower"] + (255,))
            d.line([fx+5, fy, fx+5, fy-4], fill=c["shade"] + (255,), width=1)
    else:
        # Snow on slope
        random.seed(77)
        for _ in range(W // 6):
            ox = random.randint(0, W)
            fy = random.randint(ROAD_B + 1, SLOPE_B - 1)
            fx = (ox - shift) % W
            d.point((fx, fy), fill=(255, 255, 255, 200))

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

    # Musical Notes (floating near head)
    random.seed(frame + 100)
    for i in range(2):
        nx_off = 15 + i * 12
        ny_off = -10 - (frame % 4) * 2 - i * 5
        nx, ny = cx + nx_off, hy2 + ny_off
        # Draw a simple note (dot + stem)
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
    for season in ["spring", "summer", "autumn", "winter"]:
        for i in range(8):
            frames.append(draw_scene(season, i))

    out = "/home/abisin/Desktop/abisinraj/assets/seasons_walking.gif"
    frames[0].save(
        out, save_all=True, append_images=frames[1:],
        optimize=False, duration=150, loop=0
    )
    print(f"Banner GIF saved → {out}")
