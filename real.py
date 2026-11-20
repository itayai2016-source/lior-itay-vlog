import math, os, subprocess, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS, S = 1280, 720, 30, 2
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def font(sz):
    sz = int(sz * S)
    if sz not in _fc: _fc[sz] = ImageFont.truetype(FONT, sz)
    return _fc[sz]
def clamp(t): return max(0.0, min(1.0, t))
def ease(t): t = clamp(t); return t*t*(3-2*t)
def ease_out_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1+1
    return 1 + c3*(t-1)**3 + c1*(t-1)**2

def text(img, s, cx, cy, size, fill=(255,255,255), stroke=(0,0,0), sw=5, rtl=True):
    if size < 2: return
    d = ImageDraw.Draw(img)
    kw = dict(direction="rtl") if rtl else {}
    d.text((cx*S, cy*S), s, font=font(size), fill=fill, anchor="mm", stroke_width=int(sw*S), stroke_fill=stroke, **kw)

# ---------- shading ----------
def paint(dst, mask, color, soft=5, light=(1.12, 0.80), rim=0.38):
    """composite a shaded solid shape. dst RGBA, mask L same size"""
    bb = mask.getbbox()
    if not bb: return
    pad = soft*S*2
    x0, y0 = max(0, bb[0]-pad), max(0, bb[1]-pad)
    x1, y1 = min(mask.width, bb[2]+pad), min(mask.height, bb[3]+pad)
    m = mask.crop((x0, y0, x1, y1))
    bl = np.asarray(m.filter(ImageFilter.GaussianBlur(soft*S)), dtype=np.float32)/255
    h, w = bl.shape
    gx = np.linspace(light[0], light[1], w)[None, :]
    gy = np.linspace(1.05, 0.9, h)[:, None]
    shade = gx*gy*((1-rim) + rim*bl)
    rgb = np.clip(np.array(color, np.float32)[None, None, :]*shade[..., None], 0, 255).astype(np.uint8)
    tile = Image.fromarray(rgb, "RGB").convert("RGBA")
    tile.putalpha(m)
    dst.alpha_composite(tile, (x0, y0))

def newmask(size):
    m = Image.new("L", size, 0); return m, ImageDraw.Draw(m)

# ---------- character ----------
LW, LH = 300, 520          # layer size (1x)
FEET = (150, 500); CENTER_Y = 280
PROFILE = {
    "L": dict(skin=(232,186,150), shirt=(235,120,45), pants=(55,70,105), shoes=(240,240,240), hair=(55,32,18), iris=(90,55,25)),
    "I": dict(skin=(226,178,145), shirt=(40,110,200), pants=(40,40,48), shoes=(30,30,30), hair=(30,22,18), iris=(70,50,30)),
}
def character(who, mood="smile", arm_l=12, arm_r=12, legs=0.0, spoon=False, lemon=None, mouth_open=0.0, blink=False, look=0):
    pr = PROFILE[who]
    im = Image.new("RGBA", (LW*S, LH*S), (0,0,0,0))
    size = im.size
    def P(x, y): return (x*S, y*S)
    def cap_line(d, a, b, w):
        d.line([P(*a), P(*b)], fill=255, width=int(w*S))
        for (x, y) in (a, b): d.ellipse([P(x-w/2, y-w/2), P(x+w/2, y+w/2)], fill=255)
    cx = 150
    # ---- legs + shoes
    pm, pd = newmask(size); sm, sd = newmask(size)
    for side in (-1, 1):
        sw = 16*math.sin(legs*2*math.pi + (0 if side < 0 else math.pi))
        hip = (cx+side*20, 300); knee = (cx+side*22+sw*0.6, 395); ankle = (cx+side*24+sw, 482)
        cap_line(pd, hip, knee, 36); cap_line(pd, knee, ankle, 30)
        sd.rounded_rectangle([P(ankle[0]-16+side*4, ankle[1]-6), P(ankle[0]+16+side*10, ankle[1]+18)], radius=9*S, fill=255)
    pd.rounded_rectangle([P(cx-44, 282), P(cx+44, 322)], radius=14*S, fill=255)
    paint(im, pm, pr["pants"], soft=6)
    paint(im, sm, pr["shoes"], soft=3)
    # ---- arms (geometry)
    hands = {}
    am, ad = newmask(size); hm, hd = newmask(size)
    for side, ang in ((-1, arm_l), (1, arm_r)):
        a = math.radians(ang)
        sh = (cx+side*44, 148)
        el = (sh[0]+side*math.sin(a)*78, sh[1]+math.cos(a)*78)
        a2 = a + math.radians(18 if ang < 90 else -25)
        wr = (el[0]+side*math.sin(a2)*72, el[1]+math.cos(a2)*72)
        cap_line(ad, sh, el, 28); cap_line(ad, el, (el[0]+(wr[0]-el[0])*0.45, el[1]+(wr[1]-el[1])*0.45), 25)
        cap_line(hd, (el[0]+(wr[0]-el[0])*0.45, el[1]+(wr[1]-el[1])*0.45), wr, 19)
        hd.ellipse([P(wr[0]-12, wr[1]-12), P(wr[0]+12, wr[1]+14)], fill=255)
        hands[side] = wr
    # ---- neck, torso
    nm, nd = newmask(size)
    nd.rounded_rectangle([P(cx-13, 100), P(cx+13, 145)], radius=6*S, fill=255)
    paint(im, nm, tuple(int(c*0.85) for c in pr["skin"]), soft=4)
    tm, td = newmask(size)
    td.rounded_rectangle([P(cx-50, 132), P(cx+50, 300)], radius=26*S, fill=255)
    td.polygon([P(cx-50, 160), P(cx-44, 300), P(cx+44, 300), P(cx+50, 160)], fill=255)
    paint(im, tm, pr["shirt"], soft=10)
    d = ImageDraw.Draw(im, "RGBA")
    # collar + shirt details
    d.arc([P(cx-16, 124), P(cx+16, 150)], 0, 180, fill=tuple(int(c*0.7) for c in pr["shirt"]), width=3*S)
    if who == "I":
        d.text(P(cx, 210), "23", font=font(34), fill=(255,255,255,220), anchor="mm")
    else:
        d.ellipse([P(cx-22, 190), P(cx+22, 234)], outline=(255,255,255,200), width=3*S)
        d.text(P(cx, 212), "L", font=font(26), fill=(255,255,255,220), anchor="mm")
    # folds
    d.line([P(cx-30, 270), P(cx-10, 262)], fill=(0,0,0,40), width=2*S)
    d.line([P(cx+28, 250), P(cx+10, 258)], fill=(0,0,0,40), width=2*S)
    paint(im, am, pr["shirt"], soft=5, rim=0.45)
    paint(im, hm, pr["skin"], soft=4)
    # ---- head
    hx, hy = cx, 72
    if who == "I" and FACE is not None:
        hm3, hd3 = newmask(size)
        hd3.ellipse([P(hx-57, hy-70), P(hx+57, hy+34)], fill=255)
        paint(im, hm3, (120,85,55), soft=6)
        fw, fh = FACE.size
        im.alpha_composite(FACE, (int(hx*S - fw/2), int((hy+4)*S - fh/2)))
        if spoon:
            sm2, sd2 = newmask(size)
            ny = hy + 4 - 73.5 + 0.55*147
            sd2.ellipse([P(hx-11, ny-12), P(hx+11, ny+14)], fill=255)
            sd2.line([P(hx, ny+10), P(hx+2, ny+70)], fill=255, width=6*S)
            paint(im, sm2, (205,210,220), soft=3, light=(1.25, 0.7), rim=0.5)
        if lemon is not None:
            side, bite = lemon
            wx, wy = hands[side]
            lm, ld = newmask(size)
            ld.ellipse([P(wx-17, wy-30), P(wx+17, wy-2)], fill=255)
            paint(im, lm, (245,210,40), soft=5, rim=0.45)
            if bite:
                d = ImageDraw.Draw(im, "RGBA")
                d.ellipse([P(wx-side*14-9, wy-28), P(wx-side*14+9, wy-12)], fill=(250,245,180), outline=(230,200,60), width=S)
        return im
    if who == "L":
        hb, hbd = newmask(size)
        hbd.ellipse([P(hx-42, hy-56), P(hx+42, hy+20)], fill=255)
        paint(im, hb, pr["hair"], soft=6)
    em, edd = newmask(size)
    for side in (-1, 1): edd.ellipse([P(hx+side*34-7, hy-6), P(hx+side*34+7, hy+14)], fill=255)
    paint(im, em, pr["skin"], soft=3)
    fm, fd = newmask(size)
    fd.ellipse([P(hx-34, hy-44), P(hx+34, hy+46)], fill=255)
    fd.chord([P(hx-30, hy-10), P(hx+30, hy+50)], 0, 180, fill=255)
    paint(im, fm, pr["skin"], soft=9, rim=0.3)
    d = ImageDraw.Draw(im, "RGBA")
    # hair front
    if who == "L":
        rr = random.Random(3)
        for i in range(26):
            a = math.radians(rr.uniform(195, 345)); r0 = rr.uniform(30, 42)
            x = hx + r0*math.cos(a); y = hy - 12 + r0*math.sin(a)*1.05
            c = tuple(int(v*rr.uniform(0.8, 1.35)) for v in pr["hair"])
            d.ellipse([P(x-9, y-9), P(x+9, y+9)], fill=c)
            d.arc([P(x-6, y-6), P(x+6, y+6)], 200, 320, fill=tuple(min(255, int(v*1.8)) for v in pr["hair"]), width=S)
    else:
        hm2, hd2 = newmask(size)
        hd2.chord([P(hx-35, hy-46), P(hx+35, hy+10)], 180, 360, fill=255)
        paint(im, hm2, pr["hair"], soft=3)
        cm, cd = newmask(size)
        cd.chord([P(hx-38, hy-62), P(hx+38, hy-6)], 180, 360, fill=255)
        cd.rectangle([P(hx-38, hy-36), P(hx+38, hy-28)], fill=255)
        paint(im, cm, (200,35,45), soft=6)
        d = ImageDraw.Draw(im, "RGBA")
        d.line([P(hx, hy-62), P(hx, hy-34)], fill=(120,15,25), width=2*S)
        d.rectangle([P(hx-14, hy-40), P(hx+14, hy-30)], fill=(30,30,30))   # snapback opening
        d.ellipse([P(hx-4, hy-66), P(hx+4, hy-58)], fill=(160,25,35))
    # brows
    bc = tuple(int(v*0.9) for v in pr["hair"])
    by = hy - 14
    for side in (-1, 1):
        ex = hx + side*14
        if mood == "sad": pts = [P(ex-side*8, by-4), P(ex+side*8, by+2)]
        elif mood in ("sour",): pts = [P(ex-side*8, by+2), P(ex+side*8, by-3)]
        elif mood == "shock": pts = [P(ex-8, by-6), P(ex+8, by-6)]
        else: pts = [P(ex-side*8, by), P(ex+side*8, by-2)]
        d.line(pts, fill=bc, width=4*S)
    # eyes
    ey = hy - 2
    closed = blink or mood in ("laugh", "sour")
    for side in (-1, 1):
        ex = hx + side*14
        if closed:
            if mood == "sour":
                d.line([P(ex-7, ey-2), P(ex+7, ey+1)], fill=(40,25,20), width=3*S)
                d.line([P(ex-6, ey+3), P(ex+6, ey+2)], fill=(40,25,20,120), width=2*S)
            else:
                d.arc([P(ex-7, ey-4), P(ex+7, ey+6)], 200, 340, fill=(40,25,20), width=3*S)
        else:
            oh = 7 if mood == "shock" else 5
            d.ellipse([P(ex-8, ey-oh), P(ex+8, ey+oh)], fill=(250,248,245), outline=(80,50,40), width=S)
            ix = ex + look*2
            d.ellipse([P(ix-4.5, ey-4.5), P(ix+4.5, ey+4.5)], fill=pr["iris"])
            d.ellipse([P(ix-2.2, ey-2.2), P(ix+2.2, ey+2.2)], fill=(10,8,8))
            d.ellipse([P(ix+0.5, ey-3), P(ix+2.3, ey-1.2)], fill=(255,255,255))
            d.arc([P(ex-8, ey-oh-1), P(ex+8, ey+oh)], 190, 350, fill=(50,30,25), width=2*S)
    # nose
    d.line([P(hx+2, hy+2), P(hx+5, hy+14)], fill=(150,95,70,140), width=2*S)
    d.arc([P(hx-7, hy+10), P(hx+7, hy+20)], 20, 160, fill=(140,85,65,170), width=2*S)
    # cheeks
    for side in (-1, 1): d.ellipse([P(hx+side*20-7, hy+10), P(hx+side*20+7, hy+20)], fill=(230,120,110,45))
    # mouth
    my = hy + 28; lip = (175,80,80)
    if mood == "laugh" or mouth_open > 0.3:
        r = 8 + 5*mouth_open
        d.chord([P(hx-13, my-r), P(hx+13, my+r)], 0, 180, fill=(90,25,30), outline=lip, width=2*S)
        d.chord([P(hx-11, my-r+1), P(hx+11, my-r+8)], 0, 180, fill=(245,245,240))
    elif mood == "grin":
        d.chord([P(hx-14, my-8), P(hx+14, my+8)], 0, 180, fill=(245,245,240), outline=lip, width=2*S)
    elif mood == "sour":
        d.line([P(hx-10, my+2), P(hx-4, my-2), P(hx+2, my+2), P(hx+8, my-2), P(hx+11, my+1)], fill=lip, width=3*S, joint="curve")
    elif mood == "sad":
        d.arc([P(hx-10, my), P(hx+10, my+10)], 200, 340, fill=lip, width=3*S)
    elif mood == "shock":
        d.ellipse([P(hx-6, my-5), P(hx+6, my+8)], fill=(90,25,30), outline=lip, width=2*S)
    else:
        d.arc([P(hx-12, my-8), P(hx+12, my+5)], 20, 160, fill=lip, width=3*S)
    if spoon:
        sm2, sd2 = newmask(size)
        sd2.ellipse([P(hx-9, hy+2), P(hx+9, hy+24)], fill=255)
        sd2.line([P(hx, hy+20), P(hx+2, hy+66)], fill=255, width=5*S)
        paint(im, sm2, (205,210,220), soft=3, light=(1.25, 0.7), rim=0.5)
    if lemon is not None:
        side, bite = lemon
        wx, wy = hands[side]
        lm, ld = newmask(size)
        ld.ellipse([P(wx-17, wy-30), P(wx+17, wy-2)], fill=255)
        paint(im, lm, (245,210,40), soft=5, rim=0.45)
        if bite:
            d = ImageDraw.Draw(im, "RGBA")
            d.ellipse([P(wx-side*14-9, wy-28), P(wx-side*14+9, wy-12)], fill=(250,245,180), outline=(230,200,60), width=S)
    return im

_shadow = None
FACE = None
if False and os.path.exists("face/itay_face.png"):
    FACE = Image.open("face/itay_face.png").convert("RGBA").resize((112*S, 147*S), Image.LANCZOS)
def shadow_sprite():
    global _shadow
    if _shadow is None:
        s = Image.new("RGBA", (220*S, 60*S), (0,0,0,0))
        ImageDraw.Draw(s).ellipse([30*S, 18*S, 190*S, 42*S], fill=(0,0,0,120))
        _shadow = s.filter(ImageFilter.GaussianBlur(7*S))
    return _shadow

def place(frame, layer, x, y, scale=0.84, rot=0.0, flip=False, shadow=True, ground_y=None):
    gy = y if ground_y is None else ground_y
    if shadow:
        sh = shadow_sprite()
        lift = max(0, gy - y) if not rot else 0
        k = max(0.4, 1 - lift/250)
        s2 = sh.resize((int(sh.width*k*scale), int(sh.height*k*scale)))
        frame.alpha_composite(s2, (int(x*S - s2.width/2), int(gy*S - s2.height/2)))
    if flip: layer = layer.transpose(Image.FLIP_LEFT_RIGHT)
    if scale != 1.0:
        layer = layer.resize((int(layer.width*scale), int(layer.height*scale)), Image.BILINEAR)
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(layer, (int(x*S - layer.width/2), int((y - (FEET[1]-CENTER_Y)*scale)*S - layer.height/2)))
    else:
        frame.alpha_composite(layer, (int(x*S - layer.width/2), int((y - FEET[1]*scale)*S)))

# ---------- environments ----------
def vgrad(w, h, c1, c2):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(c1)[None,None,:]*(1-a) + np.array(c2)[None,None,:]*a
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8), "RGB").convert("RGBA")

FLOOR_Y = 520
def wood_floor(img, base=(150,100,60)):
    d = ImageDraw.Draw(img, "RGBA")
    fl = vgrad(W*S, (H-FLOOR_Y)*S, tuple(int(c*0.75) for c in base), base)
    img.alpha_composite(fl, (0, FLOOR_Y*S))
    vx = W/2; rr = random.Random(5)
    for i in range(-14, 15):
        xb = W/2 + i*120
        d.line([(vx*S + (xb-vx)*0.35*S, FLOOR_Y*S), (xb*S, H*S)], fill=(60,35,20,90), width=2*S)
    y = FLOOR_Y; step = 18
    while y < H:
        d.line([(0, y*S), (W*S, y*S)], fill=(60,35,20,35), width=S)
        step *= 1.25; y += step
    d.rectangle([0, (FLOOR_Y-14)*S, W*S, FLOOR_Y*S], fill=(240,235,225))
    d.line([0, FLOOR_Y*S, W*S, FLOOR_Y*S], fill=(0,0,0,60), width=2*S)

def living_room(night=False):
    img = vgrad(W*S, FLOOR_Y*S, (226,214,196), (205,190,170))
    full = Image.new("RGBA", (W*S, H*S)); full.alpha_composite(img)
    img = full
    d = ImageDraw.Draw(img, "RGBA")
    # window
    wx0, wy0, wx1, wy1 = 120, 110, 420, 400
    sky = vgrad((wx1-wx0)*S, (wy1-wy0)*S, (110,170,235) if not night else (10,15,45), (200,225,245) if not night else (40,30,80))
    img.alpha_composite(sky, (wx0*S, wy0*S))
    if not night:
        for cx_, cy_, r_ in ((200, 180, 30), (235, 170, 38), (270, 185, 28)):
            d.ellipse([(cx_-r_)*S, (cy_-r_*0.6)*S, (cx_+r_)*S, (cy_+r_*0.6)*S], fill=(255,255,255,200))
        # far buildings / trees
        for i in range(6):
            bx = wx0 + 10 + i*50; bh = 60 + (i*37) % 70
            d.rectangle([bx*S, (wy1-bh)*S, (bx+40)*S, wy1*S], fill=(150,165,185))
        d.ellipse([(wx0+150)*S, (wy1-90)*S, (wx0+290)*S, (wy1+30)*S], fill=(80,130,70))
    else:
        d.ellipse([350*S, 140*S, 380*S, 170*S], fill=(240,240,210))
        rr = random.Random(2)
        for i in range(30):
            x = rr.uniform(wx0, wx1); y = rr.uniform(wy0, wy1-60)
            d.ellipse([x*S, y*S, (x+2)*S, (y+2)*S], fill=(255,255,255,200))
    for x in (wx0, (wx0+wx1)/2, wx1):
        d.rectangle([(x-6)*S, wy0*S, (x+6)*S, wy1*S], fill=(245,245,240))
    d.rectangle([(wx0-6)*S, (wy0-6)*S, (wx1+6)*S, (wy0+6)*S], fill=(245,245,240))
    d.rectangle([(wx0-14)*S, (wy1-4)*S, (wx1+14)*S, (wy1+10)*S], fill=(240,238,232))
    # curtains
    for side, x in ((-1, wx0-40), (1, wx1-10)):
        cm, cd = newmask(img.size)
        cd.rounded_rectangle([x*S, (wy0-30)*S, (x+50)*S, (FLOOR_Y-20)*S], radius=10*S, fill=255)
        paint(img, cm, (150,60,55), soft=8, light=(1.0, 0.85))
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(4):
            d.line([((x+8+k*11)*S, (wy0-25)*S), ((x+8+k*11)*S, (FLOOR_Y-25)*S)], fill=(0,0,0,35), width=2*S)
    d.rectangle([(wx0-60)*S, (wy0-36)*S, (wx1+60)*S, (wy0-30)*S], fill=(90,70,50))
    # frames on wall
    for (fx, fy, fw, fh, col) in ((640, 150, 150, 110, (70,120,150)), (820, 175, 80, 100, (190,140,80))):
        d.rectangle([(fx-6)*S, (fy-6)*S, (fx+fw+6)*S, (fy+fh+6)*S], fill=(50,40,35))
        art = vgrad(fw*S, fh*S, col, tuple(min(255, c+70) for c in col))
        img.alpha_composite(art, (fx*S, fy*S))
        d.ellipse([(fx+fw*0.3)*S, (fy+fh*0.3)*S, (fx+fw*0.6)*S, (fy+fh*0.6)*S], fill=(255,230,150,200))
    # couch
    cm, cd = newmask(img.size)
    cd.rounded_rectangle([560*S, 330*S, 1000*S, 470*S], radius=30*S, fill=255)
    paint(img, cm, (95,110,125), soft=14)
    cm, cd = newmask(img.size)
    cd.rounded_rectangle([540*S, 400*S, 1020*S, 505*S], radius=24*S, fill=255)
    paint(img, cm, (105,120,135), soft=12)
    for x in (600, 780):
        cm, cd = newmask(img.size)
        cd.rounded_rectangle([x*S, 360*S, (x+170)*S, 440*S], radius=26*S, fill=255)
        paint(img, cm, (115,130,145), soft=12)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([570*S, 505*S, 584*S, 518*S], fill=(50,35,25)); d.rectangle([976*S, 505*S, 990*S, 518*S], fill=(50,35,25))
    # pillow
    cm, cd = newmask(img.size)
    cd.rounded_rectangle([620*S, 380*S, 700*S, 440*S], radius=16*S, fill=255)
    paint(img, cm, (230,180,70), soft=8)
    # lamp
    d.rectangle([1105*S, 260*S, 1111*S, 505*S], fill=(60,55,50))
    d.ellipse([1075*S, 498*S, 1141*S, 512*S], fill=(50,45,40))
    lm, ld = newmask(img.size)
    ld.polygon([(1075*S, 260*S), (1140*S, 260*S), (1128*S, 200*S), (1088*S, 200*S)], fill=255)
    paint(img, lm, (250,235,200) if not night else (255,210,120), soft=6, light=(1.05, 0.9))
    # plant
    pm, pd = newmask(img.size)
    pd.polygon([(455*S, 450*S), (515*S, 450*S), (505*S, 512*S), (465*S, 512*S)], fill=255)
    paint(img, pm, (190,95,60), soft=5)
    d = ImageDraw.Draw(img, "RGBA")
    rr = random.Random(9)
    for i in range(14):
        a = math.radians(rr.uniform(200, 340)); L = rr.uniform(50, 110)
        x2 = 485 + L*math.cos(a); y2 = 450 + L*math.sin(a)
        d.line([(485*S, 450*S), (x2*S, y2*S)], fill=(40,90,40), width=2*S)
        d.ellipse([(x2-14)*S, (y2-7)*S, (x2+14)*S, (y2+7)*S], fill=(50+rr.randint(0,40), 120+rr.randint(0,40), 50))
    wood_floor(img)
    # rug
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([300*S, 585*S, 980*S, 690*S], fill=(170,70,60,200))
    d.ellipse([330*S, 595*S, 950*S, 680*S], outline=(240,200,140,180), width=3*S)
    # window light on floor
    if not night:
        d.polygon([(150*S, 540*S), (440*S, 540*S), (560*S, 700*S), (190*S, 700*S)], fill=(255,240,200,40))
    if night:
        dark = Image.new("RGBA", img.size, (10,5,30,175))
        img.alpha_composite(dark)
        glow = Image.new("RGBA", img.size, (0,0,0,0))
        ImageDraw.Draw(glow).ellipse([1000*S, 150*S, 1220*S, 330*S], fill=(255,190,90,90))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30*S)))
    return img

def kitchen():
    img = Image.new("RGBA", (W*S, H*S))
    img.alpha_composite(vgrad(W*S, FLOOR_Y*S, (238,238,232), (220,220,212)))
    d = ImageDraw.Draw(img, "RGBA")
    # backsplash tiles
    for y in range(250, 400, 30):
        for x in range(0, W, 60):
            off = 30 if (y//30) % 2 else 0
            d.rectangle([(x+off)*S, y*S, (x+off+58)*S, (y+28)*S], outline=(190,195,200), width=S, fill=(245,248,250))
    # upper cabinets
    for x in range(40, 1240, 200):
        cm, cd = newmask(img.size)
        cd.rounded_rectangle([x*S, 40*S, (x+190)*S, 220*S], radius=6*S, fill=255)
        paint(img, cm, (90,130,120), soft=10, rim=0.25)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([(x+90)*S, 150*S, (x+100)*S, 190*S], fill=(200,200,205))
    # counter
    cm, cd = newmask(img.size)
    cd.rectangle([0, 400*S, W*S, 512*S], fill=255)
    paint(img, cm, (90,130,120), soft=10, rim=0.2)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 392*S, W*S, 408*S], fill=(225,220,210))
    d.line([0, 408*S, W*S, 408*S], fill=(0,0,0,60), width=2*S)
    for x in range(0, W, 200): d.line([x*S, 410*S, x*S, 512*S], fill=(0,0,0,50), width=2*S)
    # fruit bowl and kettle
    d.chord([150*S, 350*S, 270*S, 410*S], 0, 180, fill=(240,240,240))
    for i, c in enumerate([(245,210,40), (240,200,30), (90,160,40), (245,215,50)]):
        x = 165 + i*25
        d.ellipse([x*S, 345*S, (x+34)*S, 375*S], fill=c, outline=(0,0,0,40))
    km, kd = newmask(img.size)
    kd.rounded_rectangle([1000*S, 320*S, 1080*S, 395*S], radius=20*S, fill=255)
    paint(img, km, (200,205,215), soft=8, light=(1.25, 0.7))
    # floor: checker in perspective
    fl = vgrad(W*S, (H-FLOOR_Y)*S, (170,165,160), (215,210,205))
    img.alpha_composite(fl, (0, FLOOR_Y*S))
    d = ImageDraw.Draw(img, "RGBA")
    ys = [FLOOR_Y]; step = 14
    while ys[-1] < H: step *= 1.3; ys.append(ys[-1]+step)
    for r in range(len(ys)-1):
        for c in range(-12, 13):
            if (r+c) % 2: continue
            def X(xx, y): return W/2 + (xx-W/2)*(0.35 + 0.65*(y-FLOOR_Y)/(H-FLOOR_Y))
            xa, xb = W/2 + c*110, W/2 + (c+1)*110
            y0, y1 = ys[r], ys[r+1]
            d.polygon([(X(xa,y0)*S, y0*S), (X(xb,y0)*S, y0*S), (X(xb,y1)*S, y1*S), (X(xa,y1)*S, y1*S)], fill=(60,60,65,110))
    d.rectangle([0, (FLOOR_Y-8)*S, W*S, FLOOR_Y*S], fill=(60,80,75))
    return img

_vig = None
def grade(img):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H*S, 0:W*S].astype(np.float32)
        r = np.sqrt(((xx/(W*S))-0.5)**2*1.0 + ((yy/(H*S))-0.5)**2*1.3)
        a = np.clip((r-0.35)/0.45, 0, 1)**1.6*150
        arr = np.zeros((H*S, W*S, 4), np.uint8); arr[..., 3] = a.astype(np.uint8)
        _vig = Image.fromarray(arr, "RGBA")
    img.alpha_composite(_vig)
    return img

def camera(img, t, seed=0, zoom=1.04, amp=1.0):
    sx = (math.sin(t*1.3+seed)*6 + math.sin(t*3.1+seed*2)*3)*amp
    sy = (math.sin(t*1.7+seed*3)*4 + math.sin(t*2.9+seed)*2)*amp
    rot = math.sin(t*0.9+seed)*0.4*amp
    cw, ch = W*S/zoom, H*S/zoom
    x0 = (W*S-cw)/2 + sx*S; y0 = (H*S-ch)/2 + sy*S
    out = img.transform(img.size, Image.AFFINE, (cw/(W*S), 0, x0, 0, ch/(H*S), y0), resample=Image.BILINEAR)
    if abs(rot) > 0.05: out = out.rotate(rot, resample=Image.BILINEAR)
    return out

_bgcache = {}
def bgc(key, fn):
    if key not in _bgcache: _bgcache[key] = fn()
    return _bgcache[key].copy()

# ---------- UI ----------
def scoreboard(img, l, i, pop_l=0, pop_i=0):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([20*S, 70*S, 300*S, 122*S], radius=12*S, fill=(0,0,0,150))
    text(img, "ליאור", 110, 96, 24, fill=(255,170,90), sw=0)
    text(img, str(l), 50, 96, 30*(1+0.5*pop_l), sw=0, rtl=False)
    text(img, "איתי", 210, 96, 24, fill=(120,190,255), sw=0)
    text(img, str(i), 270, 96, 30*(1+0.5*pop_i), sw=0, rtl=False)

def rec_badge(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    if int(t*2) % 2 == 0: d.ellipse([28*S, 28*S, 48*S, 48*S], fill=(240,40,40))
    text(img, "REC", 80, 38, 22, sw=3, rtl=False)
    secs = int(t)
    text(img, f"00:{secs:02d}", 155, 38, 20, sw=3, rtl=False)
    # corner brackets
    for (x, y, sx, sy) in ((16, 16, 1, 1), (W-16, 16, -1, 1), (16, H-16, 1, -1), (W-16, H-16, -1, -1)):
        d.line([(x*S, y*S), ((x+40*sx)*S, y*S)], fill=(255,255,255,200), width=3*S)
        d.line([(x*S, y*S), (x*S, (y+40*sy)*S)], fill=(255,255,255,200), width=3*S)

def caption(img, s, y=660, size=34, color=(255,255,255)):
    d = ImageDraw.Draw(img, "RGBA")
    f = font(size)
    bb = d.textbbox((W/2*S, y*S), s, font=f, anchor="mm", direction="rtl")
    d.rounded_rectangle([bb[0]-16*S, bb[1]-10*S, bb[2]+16*S, bb[3]+10*S], radius=10*S, fill=(0,0,0,160))
    d.text((W/2*S, y*S), s, font=f, fill=color, anchor="mm", direction="rtl")

def title_card(img, f, big, small, color=(255,220,60)):
    t = f/FPS
    if t < 1.8:
        a = clamp(1-(t-1.4)/0.4)
        img.alpha_composite(Image.new("RGBA", img.size, (0,0,0,int(140*a))))
        k = ease_out_back(t/0.5)
        text(img, big, W/2, 300, 92*k, fill=color, sw=7)
        text(img, small, W/2, 400, 52*k, sw=5)
    else:
        d = ImageDraw.Draw(img, "RGBA")
        f_ = font(30)
        bb = d.textbbox((W-40)*S if False else ((W-30)*S, 96*S), small, font=f_, anchor="rm", direction="rtl")
        d.rounded_rectangle([bb[0]-14*S, bb[1]-8*S, bb[2]+14*S, bb[3]+8*S], radius=10*S, fill=(0,0,0,150))
        d.text(((W-30)*S, 96*S), small, font=f_, fill=color, anchor="rm", direction="rtl")

def flash(img, f):
    if f < 8: img.alpha_composite(Image.new("RGBA", img.size, (255,255,255,int(255*(1-f/8)))))

GY = 662  # feet line
OUT = "out3"

# ---------- scenes ----------
def sc_intro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    kL = ease_out_back((t-0.5)/0.6); kI = ease_out_back((t-0.8)/0.6)
    wv = 150 + 25*math.sin(t*9)
    hopL = abs(math.sin(t*5))*16 if t > 1.6 else 0
    hopI = abs(math.sin(t*5+1))*16 if t > 1.6 else 0
    place(img, character("L", "grin", arm_l=wv if t > 1.6 else 15, arm_r=15, blink=(f % 70) < 3, legs=t*2 if t < 1.2 else 0), -200 + kL*560, GY - hopL, ground_y=GY)
    place(img, character("I", "grin", arm_l=15, arm_r=wv if t > 1.6 else 15, blink=(f % 83) < 3, legs=t*2 if t < 1.4 else 0), W+200 - kI*560, GY - hopI, ground_y=GY)
    img = grade(camera(img, t, 0, zoom=1.04 + 0.03*ease(t/5)))
    rec_badge(img, t)
    k = ease_out_back((t-0.1)/0.5)
    text(img, "הוולוג של", W/2, 130, 46*k, sw=5)
    text(img, "ליאור ואיתי", W/2, 205, 96*k, fill=(255,225,70), sw=8)
    k2 = ease_out_back((t-1.3)/0.5)
    if k2 > 0.02:
        d = ImageDraw.Draw(img, "RGBA"); bw = 200*k2
        d.rounded_rectangle([(W/2-bw)*S, 262*S, (W/2+bw)*S, 312*S], radius=25*S, fill=(230,40,70))
        text(img, "המגניבים!!!", W/2, 287, 38*k2, sw=0)
    if t > 2.4: caption(img, "פרק 1: אתגרים ושטויות")
    flash(img, f)
    return img

def sc_spoon(f):
    t = f/FPS
    img = bgc("lr", living_room)
    secs = max(0, t-1.8); fall = secs - 4.6
    lmood = "smile" if fall < 0 else ("shock" if fall < 0.6 else "sad")
    wob = math.sin(t*7)*(2 + secs*1.0) if fall < 0 else 0
    place(img, character("L", lmood, arm_l=35+8*math.sin(t*6), arm_r=35-8*math.sin(t*6), spoon=fall < 0, look=-1 if fall > 0.6 else 0), 380, GY, rot=wob)
    imood = "smile" if fall < 0.4 else "grin"
    place(img, character("I", imood, arm_l=25 if fall < 0.4 else 165, arm_r=25 if fall < 0.4 else 165, spoon=True), 900, GY - (abs(math.sin(t*8))*20 if fall > 0.4 else 0), rot=math.sin(t*5)*2, ground_y=GY)
    if fall >= 0:
        sy = min(560 + 0.5*1800*fall**2, GY)
        sp = Image.new("RGBA", (40*S, 90*S), (0,0,0,0))
        m, md = newmask(sp.size)
        md.ellipse([11*S, 4*S, 29*S, 28*S], fill=255); md.line([(20*S, 24*S), (21*S, 84*S)], fill=255, width=5*S)
        paint(sp, m, (205,210,220), soft=3, light=(1.25, 0.7), rim=0.5)
        sp = sp.rotate(-fall*720 if sy < GY else 90, expand=True)
        img.alpha_composite(sp, (int(392*S - sp.width/2), int(sy*S - sp.height/2)))
    img = grade(camera(img, t, 1, zoom=1.05 + (0.08*ease((fall-0.2)/0.5) if fall > 0 else 0)))
    rec_badge(img, t)
    if t > 1.8:
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([(W/2-80)*S, 150*S, (W/2+80)*S, 215*S], radius=14*S, fill=(0,0,0,170))
        shown = min(secs, 4.6)
        text(img, f"00:0{int(shown)}", W/2, 183, 42, fill=(90,255,130) if secs < 4.6 else (255,90,90), sw=0, rtl=False)
    if fall > 0.5:
        k = ease_out_back((fall-0.5)/0.4)
        text(img, "אופס!", W/2, 280, 64*k, fill=(255,90,90), sw=6)
        text(img, "+1 לאיתי", W/2, 360, 54*k, fill=(90,230,130), sw=6)
        caption(img, "הכפית של ליאור נפלה אחרי 4 שניות")
    elif 2.0 < t: caption(img, "מי מחזיק יותר זמן כפית על האף?")
    scoreboard(img, 0, 1 if fall > 0.5 else 0, pop_i=clamp(1-(fall-0.5)/0.3) if fall > 0.5 else 0)
    title_card(img, f, "אתגר #1", "כפית על האף")
    flash(img, f)
    return img

def sc_dance(f):
    t = f/FPS
    img = bgc("lrn", lambda: living_room(night=True))
    # party lights
    lights = Image.new("RGBA", img.size, (0,0,0,0)); ld = ImageDraw.Draw(lights)
    cols = [(255,40,120,90), (40,190,255,90), (255,220,40,80), (120,255,120,80)]
    for i in range(4):
        a = math.sin(t*1.5 + i*1.7)*0.5
        x0 = (180 + i*310)*S
        xm = x0 + math.sin(a)*800*S
        ld.polygon([(x0, 0), (xm - 130*S, H*S), (xm + 130*S, H*S)], fill=cols[i])
    img.alpha_composite(lights.filter(ImageFilter.GaussianBlur(12*S)))
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(30):  # disco dots
        rr = random.Random(i)
        x = (rr.uniform(0, W) + t*60*(1 if i % 2 else -1)) % W; y = rr.uniform(20, 600)
        d.ellipse([(x-4)*S, (y-4)*S, (x+4)*S, (y+4)*S], fill=(255,255,255,int(120+100*math.sin(t*6+i))))
    beat = t*4.0
    phase_i = 1.8 <= t < 4.6; phase_l = t >= 4.6
    bi = abs(math.sin(beat*math.pi/2))*24 if phase_i else 0
    ai = 100 + 60*math.sin(beat*math.pi) if phase_i else 15
    place(img, character("I", "grin" if phase_i else ("shock" if t > 6.4 else "smile"), arm_l=ai, arm_r=200-ai if phase_i else 15, legs=beat/2 if phase_i else 0), 920, GY - bi, ground_y=GY)
    spin = 6.0 < t < 6.6
    bl = abs(math.sin(beat*math.pi/2))*28 if phase_l else 0
    al = 165 if spin else (90 + 70*math.sin(beat*math.pi) if phase_l else 15)
    Ll = character("L", "grin" if phase_l else "smile", arm_l=al, arm_r=al if spin else 180-al, legs=beat/2 if phase_l else 0)
    flip = spin and int((t-6.0)*16) % 2 == 1
    if spin:
        sx = abs(math.cos((t-6.0)*math.pi*8))*0.85 + 0.15
        Ll = Ll.resize((max(2, int(Ll.width*sx)), Ll.height))
    place(img, Ll, 360, GY - bl - (90*math.sin((t-6.0)/0.6*math.pi) if spin else 0), flip=flip, ground_y=GY)
    img = grade(camera(img, t, 2, zoom=1.05, amp=1.6))
    rec_badge(img, t)
    if phase_i and t < 4.4: caption(img, "איתי פותח את הקרב")
    if phase_l and t < 6.6: caption(img, "ליאור עונה...")
    if t > 6.6:
        k = ease_out_back((t-6.6)/0.4)
        text(img, "סיבוב באוויר?!", W/2, 260, 54*k, fill=(255,225,70), sw=6)
        text(img, "+1 לליאור", W/2, 340, 56*k, fill=(90,230,130), sw=6)
        caption(img, "הקהל משתגע")
    scoreboard(img, 1 if t > 6.6 else 0, 1, pop_l=clamp(1-(t-6.6)/0.3) if t > 6.6 else 0)
    title_card(img, f, "אתגר #2", "קרב ריקודים", color=(255,110,210))
    flash(img, f)
    return img

def sc_lemon(f):
    t = f/FPS
    img = bgc("kit", kitchen)
    cd = t - 1.8; bite = cd > 3.0; after = cd - 3.0
    lm = "smile" if (not bite or after < 1.6) else "sour"
    shakeL = random.Random(f).uniform(-4, 4) if lm == "sour" else 0
    strain = 0.6 < after < 1.6
    place(img, character("L", lm, arm_l=15, arm_r=150 if not bite else 158, lemon=(1, bite), blink=strain and f % 20 < 3), 380 + shakeL, GY, rot=shakeL*0.5, ground_y=GY)
    place(img, character("I", "grin" if after > 2.2 else "smile", arm_l=150 if not bite else 158, arm_r=15, lemon=(-1, bite)), 900, GY)
    zoom = 1.05
    if bite and 1.6 < after < 2.4: zoom = 1.05 + 0.25*ease((after-1.6)/0.3)
    elif bite and after >= 2.4: zoom = 1.30 - 0.25*ease((after-2.4)/0.3)
    img = grade(camera(img, t, 3, zoom=zoom))
    rec_badge(img, t)
    if 0 <= cd < 3.0:
        n = 3 - int(cd); k = ease_out_back((cd % 1)/0.35)
        text(img, str(n), W/2, 260, 150*k, fill=(255,90,90), sw=9, rtl=False)
        caption(img, "לאכול לימון בלי לעשות פרצוף")
    elif bite and after < 1.0:
        text(img, "ביס!", W/2, 260, 120*ease_out_back(after/0.3), fill=(255,90,90), sw=9)
    if strain:
        d = ImageDraw.Draw(img, "RGBA"); sy = 210 + (after-0.6)*50
        d.ellipse([420*S, (sy+40)*S, 432*S, (sy+58)*S], fill=(140,200,255,220))
    if lm == "sour" and after < 2.4:
        caption(img, "חמוווווץ!!!", color=(220,255,90))
    if after > 2.2:
        k = ease_out_back((after-2.2)/0.4)
        text(img, "+1 לאיתי", W/2, 300, 60*k, fill=(90,230,130), sw=6)
        if after > 2.4: caption(img, "איתי בכלל לא זז. איך?!")
    scoreboard(img, 1, 2 if after > 2.2 else 1, pop_i=clamp(1-(after-2.2)/0.3) if after > 2.2 else 0)
    title_card(img, f, "אתגר #3", "לימון בלי פרצוף", color=(255,240,110))
    flash(img, f)
    return img

def sc_blooper(f):
    t = f/FPS
    img = bgc("kit", kitchen)
    d = ImageDraw.Draw(img, "RGBA")
    bx = 620
    if t < 2.15:
        pm, pd = newmask(img.size)
        pd.ellipse([(bx-34)*S, (GY-14)*S, (bx+34)*S, (GY+4)*S], fill=255)
        for s in (-1, 1): pd.polygon([(bx*S, (GY-6)*S), ((bx+s*52)*S, (GY-18)*S), ((bx+s*30)*S, GY*S)], fill=255)
        paint(img, pm, (245,205,50), soft=4)
    if t < 2.1:
        x = -150 + (t/2.1)*(bx+150)
        place(img, character("I", "smile", arm_l=15+15*math.sin(t*10), arm_r=15-15*math.sin(t*10), legs=t*1.8, look=1), x, GY - abs(math.sin(t*11))*4, ground_y=GY)
    else:
        u = t - 2.1
        if u < 0.9:
            x = bx + u*160
            y = GY - (440*u - 0.5*1000*u*u*0.95)
            place(img, character("I", "shock", arm_l=170, arm_r=170, legs=u*4), x, min(y, GY), rot=-u*520, ground_y=GY)
        else:
            place(img, character("I", "sad" if u < 2.4 else "laugh", arm_l=70, arm_r=70), bx, GY - 70 + (FEET[1]-CENTER_Y)*0.84, rot=90, shadow=False)
            d = ImageDraw.Draw(img, "RGBA")
            hxp = bx - (CENTER_Y - 72)*0.84
            for k in range(4):
                a = u*5 + k*math.pi/2
                x, y = hxp + 40*math.cos(a), GY - 132 + 12*math.sin(a)
                pts = []
                for i in range(10):
                    aa = math.radians(u*200 + i*36 - 90); rr = 14 if i % 2 == 0 else 6
                    pts.append(((x+rr*math.cos(aa))*S, (y+rr*math.sin(aa))*S))
                d.polygon(pts, fill=(255,225,60))
    lx = 1110; laugh = t > 2.6
    place(img, character("L", "laugh" if laugh else "smile", arm_l=30 if not laugh else 50+20*math.sin(t*20), arm_r=30 if not laugh else 50-20*math.sin(t*20), look=-1), lx, GY - (abs(math.sin(t*14))*8 if laugh else 0), ground_y=GY)
    shake = 3.0 if 2.95 < t < 3.3 else 1.4
    img = grade(camera(img, t, 4, zoom=1.04, amp=shake))
    # vhs look
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    arr = (arr*0.9 + np.array([12, 6, -4])).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 4): d.line([(0, y*S), (W*S, y*S)], fill=(0,0,0,22), width=S)
    rec_badge(img, t)
    text(img, "מאחורי הקלעים", W/2, 60, 42, fill=(255,225,70), sw=5)
    if t > 3.0:
        kk = ease_out_back((t-3.0)/0.3)
        text(img, "בום!", bx, 330, 84*kk, fill=(255,90,90), sw=7)
    if laugh: caption(img, "ליאור לא יכול להפסיק לצחוק", y=125)
    else: caption(img, "איתי בדרך למקרר...", y=125)
    return img

def sc_outro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    wv = 150 + 25*math.sin(t*9)
    place(img, character("L", "grin", arm_l=wv, arm_r=wv, blink=f % 60 < 3), 220, GY - abs(math.sin(t*6))*16, ground_y=GY)
    place(img, character("I", "grin", arm_l=wv, arm_r=wv, blink=f % 77 < 3), 1060, GY - abs(math.sin(t*6+1))*16, ground_y=GY)
    img = grade(camera(img, t, 5, zoom=1.04))
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(7)
    for i in range(70):
        x = (rnd.uniform(0, W) + math.sin(t*2+i)*30) % W
        y = (rnd.uniform(-H, 0) + t*rnd.uniform(120, 260)) % (H+40) - 20
        c = rnd.choice([(255,225,60), (60,210,255), (255,255,255), (120,255,120), (255,90,140)])
        a = math.radians(t*200 + i*30)
        pts = [((x + w*math.cos(a) - h*math.sin(a))*S, (y + w*math.sin(a) + h*math.cos(a))*S) for w, h in [(8,4),(-8,4),(-8,-4),(8,-4)]]
        d.polygon(pts, fill=c)
    rec_badge(img, t)
    k = ease_out_back(t/0.5)
    d.rounded_rectangle([(W/2-230*k)*S, 70*S, (W/2+230*k)*S, 300*S], radius=20*S, fill=(0,0,0,150))
    text(img, "תוצאה סופית", W/2, 110, 40*k, sw=0)
    text(img, "איתי  2", W/2, 180, 60*k, fill=(120,190,255), sw=0)
    text(img, "ליאור  1", W/2, 255, 60*k, fill=(255,170,90), sw=0)
    if t > 0.9: caption(img, "ליאור דורש נקמה בפרק הבא!", y=360, color=(255,225,70))
    k3 = ease_out_back((t-1.6)/0.5)
    if k3 > 0.02:
        pulse = 1 + 0.05*math.sin(t*8)
        bw, bh = 220*k3*pulse, 42*k3*pulse
        d.rounded_rectangle([(W/2-bw)*S, (480-bh)*S, (W/2+bw)*S, (480+bh)*S], radius=int(20*S*k3), fill=(225,30,40))
        text(img, "לייק והרשמה!", W/2, 480, 44*k3*pulse, sw=0)
        if t > 2.6:
            u = t - 2.6
            cx = W/2 + 300 - min(u, 0.6)/0.6*160; cy = 570 - min(u, 0.6)/0.6*70
            d.polygon([(cx*S, cy*S), (cx*S, (cy+44)*S), ((cx+12)*S, (cy+34)*S), ((cx+24)*S, (cy+52)*S), ((cx+32)*S, (cy+48)*S), ((cx+20)*S, (cy+30)*S), ((cx+36)*S, (cy+30)*S)], fill=(255,255,255), outline=(0,0,0))
            if u > 0.6:
                r = (u-0.6)*200
                if r < 80: d.ellipse([(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], outline=(255,255,255,int(255*(1-r/80))), width=4*S)
    flash(img, f)
    return img

SCENES = [("intro", sc_intro, 5.0), ("spoon", sc_spoon, 8.5), ("dance", sc_dance, 8.5),
          ("lemon", sc_lemon, 8.5), ("blooper", sc_blooper, 6.5), ("outro", sc_outro, 5.5)]

def render_frame(fn, f): return fn(f).convert("RGB").reduce(S)

def render_scene(name, fn, dur):
    n = int(round(dur*FPS)); tmp = f"{OUT}/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
                          "-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(n): p.stdin.write(render_frame(fn, f).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, f"{OUT}/{name}.mp4")
    else: sys.exit("ffmpeg failed " + name)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for name, fn, dur in SCENES:
            if len(sys.argv) > 2 and name not in sys.argv[2:]: continue
            for tt in (1.0, dur*0.5, dur*0.85):
                render_frame(fn, int(tt*FPS)).save(f"{OUT}/prev_{name}_{tt:.1f}.png")
    else:
        from multiprocessing import Pool
        names = sys.argv[2:] or [s[0] for s in SCENES]
        jobs = [s for s in SCENES if s[0] in names]
        with Pool(min(len(jobs), os.cpu_count() or 2)) as pool:
            pool.starmap(render_scene, jobs)
