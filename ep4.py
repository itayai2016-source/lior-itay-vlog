import sys, os, math, random
import real
from real import *
from ep2 import cam_focus, lerp, arc, stars, draw_bottle, paper_ball, trash_can, tongue, CAN_X, CAN_TOP
from ep3 import pouf, seated, POUF_X

real.FACE = None
real.OUT = "ep4"
LX, IX = 380, 900
GOLD = (255, 200, 50)

# ---------------- special pieces ----------------
def stage_bg():
    img = Image.new("RGBA", (W*S, H*S))
    img.alpha_composite(vgrad(W*S, FLOOR_Y*S, (18,8,48), (55,18,85)))
    d = ImageDraw.Draw(img, "RGBA")
    # LED screen
    sc = vgrad(560*S, 250*S, (30,40,130), (110,25,140))
    img.alpha_composite(sc, (360*S, 70*S))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(360, 920, 20): d.line([(x*S, 70*S), (x*S, 320*S)], fill=(255,255,255,12), width=S)
    for y in range(70, 320, 20): d.line([(360*S, y*S), (920*S, y*S)], fill=(255,255,255,12), width=S)
    d.rounded_rectangle([352*S, 62*S, 928*S, 328*S], radius=10*S, outline=(200,170,60), width=6*S)
    # truss and lamps
    d.rectangle([0, 14*S, W*S, 30*S], fill=(70,70,80))
    for x in range(40, W, 60): d.line([(x*S, 14*S), ((x+30)*S, 30*S)], fill=(110,110,120), width=2*S)
    for x in range(120, W, 160):
        d.rectangle([(x-14)*S, 30*S, (x+14)*S, 52*S], fill=(30,30,35))
        d.ellipse([(x-10)*S, 44*S, (x+10)*S, 58*S], fill=(255,240,200))
    # curtains
    for x0, x1 in ((0, 190), (1090, W)):
        m, md = newmask(img.size)
        md.rectangle([x0*S, 30*S, x1*S, FLOOR_Y*S], fill=255)
        paint(img, m, (150,20,40), soft=10, light=(1.0, 0.8))
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(x0+12, x1, 22):
            d.line([(k*S, 32*S), (k*S, FLOOR_Y*S)], fill=(0,0,0,55), width=3*S)
            d.line([((k+6)*S, 32*S), ((k+6)*S, FLOOR_Y*S)], fill=(255,255,255,18), width=2*S)
        d.rectangle([x0*S, 30*S, x1*S, 52*S], fill=(200,160,50))
    # stage floor: glossy
    fl = vgrad(W*S, (H-FLOOR_Y)*S, (60,35,80), (25,15,35))
    img.alpha_composite(fl, (0, FLOOR_Y*S))
    d = ImageDraw.Draw(img, "RGBA")
    y = FLOOR_Y; step = 16
    while y < H:
        d.line([(0, y*S), (W*S, y*S)], fill=(255,255,255,14), width=S); step *= 1.3; y += step
    for x in range(0, W, 26):
        d.ellipse([(x+8)*S, (FLOOR_Y-5)*S, (x+16)*S, (FLOOR_Y+3)*S], fill=(255,210,90))
    refl = Image.new("RGBA", img.size, (0,0,0,0))
    ImageDraw.Draw(refl).rectangle([360*S, (FLOOR_Y+6)*S, 920*S, (FLOOR_Y+110)*S], fill=(120,60,200,40))
    img.alpha_composite(refl.filter(ImageFilter.GaussianBlur(14*S)))
    return img

def led_text(img, s, size=64, color=GOLD, y=195):
    text(img, s, 640, y, size, fill=color, sw=4, stroke=(40,10,60))

def spotlights(img, t, n=4, alpha=70):
    lay = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(lay)
    cols = [(255,230,150), (150,200,255), (255,150,220), (200,255,180)]
    for i in range(n):
        x0 = 120 + i*(1040/(n-1))
        a = math.sin(t*1.2 + i*1.9)*0.45
        xm = x0 + math.sin(a)*700
        c = cols[i % 4]
        d.polygon([(x0, 40), (xm-110, H), (xm+110, H)], fill=c + (alpha,))
    lay = lay.filter(ImageFilter.GaussianBlur(10)).resize((W*S, H*S), Image.BILINEAR)
    img.alpha_composite(lay)

def crowd(img, t, cheer=0.5, seed=1):
    d = ImageDraw.Draw(img, "RGBA")
    rr = random.Random(seed)
    for i in range(16):
        x = i*84 + rr.uniform(-15, 15) + 20
        ph = rr.uniform(0, 6)
        bob = abs(math.sin(t*6 + ph))*10*cheer
        y = 708 - bob + rr.uniform(-8, 8)
        c = (14, 8, 24, 255)
        if cheer > 0.3 and (i + int(t*2)) % 3 == 0:
            for s_ in (-1, 1):
                d.line([((x+s_*26)*S, (y+30)*S), ((x+s_*40)*S, (y-40 - bob)*S)], fill=c, width=12*S)
                d.ellipse([(x+s_*40-8)*S, (y-48-bob)*S, (x+s_*40+8)*S, (y-32-bob)*S], fill=c)
        if i % 5 == 2:
            px, py = x+34, y-22-bob
            d.line([((x+24)*S, (y+20)*S), (px*S, py*S)], fill=c, width=10*S)
            d.rectangle([(px-6)*S, (py-12)*S, (px+6)*S, (py+8)*S], fill=(30,30,40))
            d.rectangle([(px-4)*S, (py-10)*S, (px+4)*S, (py+6)*S], fill=(190,220,255))
        d.ellipse([(x-46)*S, (y+22)*S, (x+46)*S, (y+90)*S], fill=c)
        d.ellipse([(x-24)*S, (y-22)*S, (x+24)*S, (y+28)*S], fill=c)

def fireworks(img, t, shots):
    d = ImageDraw.Draw(img, "RGBA")
    for (t0, x, y, col) in shots:
        age = t - t0
        if age < 0: continue
        if age < 0.45:  # rising trail
            k = age/0.45
            yy = lerp(H, y, 1-(1-k)**2)
            d.ellipse([(x-3)*S, (yy-3)*S, (x+3)*S, (yy+3)*S], fill=(255,240,200))
            continue
        a = age - 0.45
        if a > 1.6: continue
        al = int(255*(1 - a/1.6))
        r = 150*(1 - math.exp(-a*3.2))
        for i in range(34):
            ang = i*2*math.pi/34
            px = x + math.cos(ang)*r; py = y + math.sin(ang)*r + 45*a*a
            px2 = x + math.cos(ang)*r*0.82; py2 = y + math.sin(ang)*r*0.82 + 45*a*a
            d.line([(px2*S, py2*S), (px*S, py*S)], fill=col + (al,), width=3*S)
            d.ellipse([(px-3)*S, (py-3)*S, (px+3)*S, (py+3)*S], fill=(255,255,255,al))

def trophy(img, x, base_y, s=1.0, sparkle_t=None):
    m, md = newmask(img.size)
    def R(a, b, c, e): return [(x+a*s)*S, (base_y+b*s)*S, (x+c*s)*S, (base_y+e*s)*S]
    md.rounded_rectangle(R(-55, -26, 55, 0), radius=int(5*s*S), fill=255)
    md.rounded_rectangle(R(-38, -44, 38, -24), radius=int(4*s*S), fill=255)
    md.polygon([((x-10*s)*S, (base_y-44*s)*S), ((x+10*s)*S, (base_y-44*s)*S), ((x+7*s)*S, (base_y-90*s)*S), ((x-7*s)*S, (base_y-90*s)*S)], fill=255)
    md.chord(R(-60, -200, 60, -80), 0, 180, fill=255)
    md.rectangle(R(-60, -150, 60, -138), fill=255)
    for side in (-1, 1):
        md.arc(R(-95 if side < 0 else 30, -175, -30 if side < 0 else 95, -105), 90 if side < 0 else 270, 270 if side < 0 else 450, fill=255, width=int(12*s*S))
    paint(img, m, (235,180,40), soft=6, light=(1.5, 0.65), rim=0.5)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle(R(-30, -20, 30, -6), fill=(60,40,10))
    text(img, "1", x, base_y - 115*s, 40*s, fill=(255,240,180), sw=0, rtl=False)
    if sparkle_t is not None:
        for k in range(5):
            p = (sparkle_t*0.8 + k/5) % 1
            sx = x + math.cos(k*2.3)*70*s; sy = base_y - 150*s + math.sin(k*1.7)*60*s
            r_ = 10*s*math.sin(p*math.pi)
            d.line([((sx-r_)*S, sy*S), ((sx+r_)*S, sy*S)], fill=(255,255,255,230), width=2*S)
            d.line([(sx*S, (sy-r_)*S), (sx*S, (sy+r_)*S)], fill=(255,255,255,230), width=2*S)

def badge(img):
    d = ImageDraw.Draw(img, "RGBA")
    s_ = "★ ספיישל: הגמר הגדול ★"
    f_ = font(22)
    bb = d.textbbox((W/2*S, 38*S), s_, font=f_, anchor="mm", direction="rtl")
    d.rounded_rectangle([bb[0]-16*S, bb[1]-8*S, bb[2]+16*S, bb[3]+8*S], radius=16*S, fill=GOLD + (235,), outline=(255,250,220), width=2*S)
    d.text((W/2*S, 38*S), s_, font=f_, fill=(60,30,0), anchor="mm", direction="rtl")

def confetti(img, t, n=70, seed=7):
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(seed)
    for i in range(n):
        x = (rnd.uniform(0, W) + math.sin(t*2+i)*30) % W
        y = (rnd.uniform(-H, 0) + t*rnd.uniform(120, 260)) % (H+40) - 20
        c = rnd.choice([(255,215,60), (60,210,255), (255,255,255), (120,255,120), (255,90,140)])
        a = math.radians(t*200 + i*30)
        pts = [((x + w*math.cos(a) - h*math.sin(a))*S, (y + w*math.sin(a) + h*math.cos(a))*S) for w, h in [(8,4),(-8,4),(-8,-4),(8,-4)]]
        d.polygon(pts, fill=c)

def vhs(img):
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    arr = (arr*0.9 + np.array([12, 6, -4])).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 4): d.line([(0, y*S), (W*S, y*S)], fill=(0,0,0,22), width=S)
    return img

def round_card(img, f, n, name, color):
    title_card(img, f, f"סיבוב {n} מתוך 6", name, color=color)

def finish(img, f, l, i, pop_l=0, pop_i=0, rec=True, t=0, score=True):
    if rec: rec_badge(img, t)
    if score: scoreboard(img, l, i, pop_l, pop_i)
    badge(img)
    flash(img, f)
    return img

def win_text(img, t, t0, who, y=240):
    if t > t0:
        k = ease_out_back((t-t0)/0.4)
        text(img, "+1 לליאור" if who == "L" else "+1 לאיתי", W/2, y, 60*k, fill=(90,230,130), sw=6)

def pop(t, t0): return clamp(1-(t-t0)/0.3) if t > t0 else 0

def head_y(y): return y - 0.84*(FEET[1]-72)

# ---------------- scenes ----------------
def s_open(f):
    t = f/FPS
    if t < 3.0:
        img = Image.new("RGBA", (W*S, H*S), (5,3,12,255))
        n = 3 - int(t); k = ease_out_back((t % 1)/0.3)
        d = ImageDraw.Draw(img, "RGBA")
        r = 160 + 20*math.sin(t*20)
        d.ellipse([(W/2-r)*S, (H/2-r)*S, (W/2+r)*S, (H/2+r)*S], outline=GOLD + (120,), width=4*S)
        text(img, str(n), W/2, H/2, 220*k, fill=GOLD, sw=8, stroke=(60,30,0), rtl=False)
        text(img, "פרק מיוחד מתחיל בעוד...", W/2, 620, 34, fill=(220,210,240), sw=0)
        return img
    u = t - 3.0
    img = bgc("stage", stage_bg)
    spotlights(img, t, alpha=int(80*clamp(u/0.8)))
    shots = [(3.0, 300, 170, (255,200,60)), (3.5, 980, 140, (90,200,255)), (4.1, 640, 110, (255,90,160)),
             (5.0, 200, 200, (140,255,140)), (5.6, 1080, 190, (255,200,60)), (9.8, 640, 140, (255,220,120)),
             (12.0, 350, 150, (255,120,200)), (12.4, 930, 150, (120,220,255))]
    fireworks(img, t, shots)
    if u > 1.0: led_text(img, "פרק 4", 50, (255,255,255), y=130)
    if u > 1.4: led_text(img, "הגמר הגדול", 72*ease_out_back((u-1.4)/0.5), GOLD, y=215)
    # trophy rises on pedestal
    if u > 6.0:
        ty = GY - 10 + 200*(1-ease((u-6.0)/1.2))
        d = ImageDraw.Draw(img, "RGBA")
        if ty - 60 < GY:
            d.rectangle([590*S, (ty-60)*S, 690*S, GY*S], fill=(40,25,60))
            d.rectangle([585*S, (ty-66)*S, 695*S, (ty-56)*S], fill=(200,160,50))
        trophy(img, 640, ty - 66, 0.9, sparkle_t=t)
    # characters run in
    kL = ease_out_back((u-3.5)/0.7); kI = ease_out_back((u-3.8)/0.7)
    if u > 3.4:
        wv = 150 + 25*math.sin(t*9)
        place(img, character("L", "grin", arm_l=wv if u > 4.3 else 40, arm_r=40 if u < 4.3 else wv, legs=t*2 if u < 4.2 else 0), -150 + kL*500, GY - (abs(math.sin(t*5))*14 if u > 4.3 else 0), ground_y=GY)
        place(img, character("I", "grin", arm_l=40 if u < 4.5 else wv, arm_r=wv if u > 4.5 else 40, legs=t*2 if u < 4.5 else 0), W+150 - kI*520, GY - (abs(math.sin(t*5+1))*14 if u > 4.5 else 0), ground_y=GY)
    crowd(img, t, cheer=0.4 + 0.6*clamp((u-0.5)/1.0))
    img = grade(camera(img, t, 0, zoom=1.25 - 0.21*ease(u/2.5)))
    k = ease_out_back((u-0.2)/0.5)
    if u < 3.2:
        text(img, "ספיישל", W/2, 400, 150*k, fill=GOLD, sw=9, stroke=(70,30,0))
    if u > 7.5: caption(img, "מי יהיה אלוף העונה?", y=470 if False else 640, color=GOLD)
    if u < 0.3: img.alpha_composite(Image.new("RGBA", img.size, (255,255,255,int(255*(1-u/0.3)))))
    badge(img) if u > 3.2 else None
    return img

def s_host(f):
    t = f/FPS
    img = bgc("stage", stage_bg)
    spotlights(img, t, alpha=55)
    led_text(img, "החוקים", 46, (255,255,255), y=120)
    led_text(img, "6 סיבובים · גביע אחד", 48, GOLD, y=200)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([590*S, (GY-70)*S, 690*S, GY*S], fill=(40,25,60))
    d.rectangle([585*S, (GY-76)*S, 695*S, (GY-66)*S], fill=(200,160,50))
    trophy(img, 640, GY-76, 0.9, sparkle_t=t)
    lm = "grin" if t < 6 else "smile"
    talkL = 4.0 < t < 7.0; talkI = 7.0 < t < 10.0
    place(img, character("L", lm, arm_l=15, arm_r=(140 + 15*math.sin(t*10)) if talkL else 15, mouth_open=0.6*abs(math.sin(t*14)) if talkL else 0), LX, GY, ground_y=GY)
    place(img, character("I", "grin" if t > 10 else "smile", arm_l=(140 + 15*math.sin(t*10)) if talkI else 15, arm_r=15, mouth_open=0.6*abs(math.sin(t*14)) if talkI else 0), IX, GY, ground_y=GY)
    crowd(img, t, cheer=0.3)
    zoom = 1.05; fx, fy = W/2, H/2
    if 4.0 < t < 7.0: k = ease((t-4.0)/0.4) if t < 6.6 else 1-ease((t-6.6)/0.4); fx, fy, zoom = lerp(W/2, LX, k), lerp(H/2, head_y(GY)+80, k), 1.05 + 0.6*k
    if 7.0 < t < 10.0: k = ease((t-7.0)/0.4) if t < 9.6 else 1-ease((t-9.6)/0.4); fx, fy, zoom = lerp(W/2, IX, k), lerp(H/2, head_y(GY)+80, k), 1.05 + 0.6*k
    img = grade(cam_focus(img, t, 1, fx, fy, zoom))
    if t < 4.0: caption(img, "מי שמנצח הכי הרבה סיבובים – לוקח את הגביע!", color=GOLD)
    elif t < 7.0: caption(img, "ליאור: \"הגביע הזה כבר שלי\"", color=(255,190,120))
    elif t < 10.0: caption(img, "איתי: \"תמשיך לחלום...\"", color=(150,200,255))
    else:
        text(img, "יאללה, מתחילים!", W/2, 330, 64*ease_out_back((t-10)/0.4), fill=(255,255,255), sw=6)
    return finish(img, f, 0, 0, t=t, score=t > 10)

def s_spoon(f):
    t = f/FPS
    img = bgc("lr", living_room)
    secs = max(0, t-4.0); fall = secs - 7.6
    wobI = math.sin(t*7)*(2 + secs*1.6) if fall < 0 else 0
    wobL = math.sin(t*5.3)*(1.5 + secs*0.6)
    place(img, character("L", "smile" if fall < 0.4 else "grin", arm_l=35 if fall < 0.4 else 165, arm_r=35 if fall < 0.4 else 165, spoon=True), LX, GY - (abs(math.sin(t*8))*20 if fall > 0.4 else 0), rot=wobL if fall < 0 else 0, ground_y=GY)
    im = "smile" if fall < 0 else ("shock" if fall < 0.7 else "sad")
    place(img, character("I", im, arm_l=35+8*math.sin(t*6), arm_r=35-8*math.sin(t*6), spoon=fall < 0), IX, GY, rot=wobI, ground_y=GY)
    if fall >= 0:
        sy = min(320 + 0.5*1800*fall**2, GY)
        sp = Image.new("RGBA", (40*S, 90*S), (0,0,0,0))
        m, md = newmask(sp.size)
        md.ellipse([11*S, 4*S, 29*S, 28*S], fill=255); md.line([(20*S, 24*S), (21*S, 84*S)], fill=255, width=5*S)
        paint(sp, m, (205,210,220), soft=3, light=(1.25, 0.7), rim=0.5)
        sp = sp.rotate(-fall*720 if sy < GY else 90, expand=True)
        img.alpha_composite(sp, (int((IX+12)*S - sp.width/2), int(sy*S - sp.height/2)))
    fx, fy, z = W/2, H/2, 1.05
    if 6.5 < secs < 7.6:
        k = ease((secs-6.5)/0.4); fx, fy, z = W/2, lerp(H/2, head_y(GY)+40, k), 1.05 + 0.25*k
    elif 7.6 <= secs and fall < 1.0:
        k = ease(fall/0.3); fx, fy, z = lerp(W/2, IX, k), head_y(GY)+40 + 60*k, 1.3 + 0.4*k
    elif fall >= 1.0:
        k = ease((fall-1.0)/0.4); fx, fy, z = lerp(IX, W/2, k), lerp(head_y(GY)+100, H/2, k), lerp(1.7, 1.05, k)
    img = grade(cam_focus(img, t, 1, fx, fy, z))
    if t > 3.6:
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([(W/2-80)*S, 150*S, (W/2+80)*S, 215*S], radius=14*S, fill=(0,0,0,170))
        shown = min(secs, 7.6)
        text(img, f"00:{int(shown):02d}", W/2, 183, 42, fill=(90,255,130) if fall < 0 else (255,200,60), sw=0, rtl=False)
    if 2.0 < t < 4.0: caption(img, "שיא קודם: 4 שניות. הפעם שניהם ביחד!")
    elif 4.0 <= t and fall < 0: caption(img, "...5... 6... 7..." if secs > 5 else "הטיימר רץ...")
    elif 0 <= fall < 1.0: caption(img, "הכפית של איתי נפלה!")
    win_text(img, t, 12.4, "L")
    if t > 12.6: caption(img, "ליאור: \"זה בשביל פרק 1!\"", color=(255,190,120))
    round_card(img, f, 1, "כפית על האף", (220,230,255))
    return finish(img, f, 1 if t > 12.4 else 0, 0, pop_l=pop(t, 12.4), t=t)

THROWS = [("I", 3.0, "in"), ("L", 6.5, "in"), ("I", 10.0, "in"), ("L", 13.5, "rim"), ("I", 17.0, "miss"), ("L", 20.5, "rim")]
def s_basket(f):
    t = f/FPS
    img = bgc("lr", living_room)
    trash_can(img, front=False)
    lxp, ixp = LX-40, IX+40
    cur = None
    for w, t0, r in THROWS:
        if t0-0.3 < t < t0+0.2: cur = w
    hits = {"L": 0, "I": 0}
    for w, t0, r in THROWS:
        if t > t0 + 0.9 and r == "in": hits[w] += 1
    lastL = [r for w, t0, r in THROWS if w == "L" and t0+0.9 < t]
    lastI = [r for w, t0, r in THROWS if w == "I" and t0+0.9 < t]
    def mood(who, last, t_last):
        if not last: return "smile"
        if t - t_last > 2.2: return "smile"
        return "grin" if last[-1] == "in" else "sad"
    tL = max([t0 for w, t0, r in THROWS if w == "L" and t0+0.9 < t], default=0) + 0.9
    tI = max([t0 for w, t0, r in THROWS if w == "I" and t0+0.9 < t], default=0) + 0.9
    endL = t > 24.5
    place(img, character("L", "sad" if endL else mood("L", lastL, tL), arm_l=15, arm_r=160 if cur == "L" else 15), lxp, GY, ground_y=GY)
    hopI = abs(math.sin(t*8))*18 if t > 24.5 else 0
    place(img, character("I", "grin" if endL else mood("I", lastI, tI), arm_l=160 if cur == "I" or endL else 15, arm_r=165 if endL else 15), ixp, GY - hopI, ground_y=GY)
    trash_can(img, front=True)
    for w, t0, r in THROWS:
        u = (t - t0)/0.8
        sx, sy = (ixp-50, GY-330) if w == "I" else (lxp+50, GY-330)
        if r == "in": tgt = (CAN_X, CAN_TOP-5)
        elif r == "rim": tgt = (CAN_X + (48 if w == "I" else -48), CAN_TOP-8)
        else: tgt = (CAN_X - 140, GY-13)
        if 0 <= u < 1:
            x, y = arc((sx, sy), tgt, u, 220 if r != "miss" else 260)
            if not (r == "in" and u > 0.96): paper_ball(img, x, y, rot=u*900)
        elif u >= 1 and r != "in":
            v = t - t0 - 0.8; dirn = 1 if w == "I" else -1
            if r == "rim" and v < 0.7:
                x = tgt[0] + dirn*v*200; y = tgt[1] - (300*v - 0.5*1400*v*v)
                paper_ball(img, x, min(y, GY-13), rot=v*900)
            else:
                rest = tgt[0] + (dirn*140 if r == "rim" else -20)
                paper_ball(img, rest, GY-13, rot=600)
    img = grade(camera(img, t, 2, zoom=1.05))
    # hit counters
    for who, x in (("L", lxp), ("I", ixp)):
        n_th = sum(1 for w, t0, r in THROWS if w == who and t > t0+0.9)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(3):
            cx = x - 40 + k*40; cy = 250
            if k < n_th:
                res = [r for w, t0, r in THROWS if w == who][k]
                col = (90,230,130) if res == "in" else (230,70,70)
                d.ellipse([(cx-13)*S, (cy-13)*S, (cx+13)*S, (cy+13)*S], fill=col, outline=(255,255,255), width=2*S)
            else:
                d.ellipse([(cx-13)*S, (cy-13)*S, (cx+13)*S, (cy+13)*S], outline=(255,255,255,200), width=3*S)
    msgs = {3.9: "סוויש!", 7.4: "גם ליאור קולע!", 10.9: "איתי 2 מ־2!", 14.3: "בשפה...", 17.9: "פספוס!", 21.3: "שוב בשפה!"}
    for tm, s_ in msgs.items():
        if tm < t < tm + 1.8: text(img, s_, W/2, 200, 54*ease_out_back((t-tm)/0.3), fill=(255,225,70), sw=6)
    if 2.0 < t < 3.0: caption(img, "3 זריקות לכל אחד. מי שקולע יותר מנצח")
    elif t > 22 and t < 24.5: caption(img, "איתי 2, ליאור 1")
    win_text(img, t, 24.5, "I", y=320)
    if t > 25: caption(img, "שוויון 1:1!")
    round_card(img, f, 2, "קליעה לפח", (255,170,90))
    return finish(img, f, 1, 1 if t > 24.5 else 0, pop_i=pop(t, 24.5), t=t)

FLIPS = [("L", 3.0, True), ("I", 6.0, True), ("L", 9.0, True), ("I", 12.0, False)]
def s_bottle(f):
    t = f/FPS
    img = bgc("kit", kitchen)
    cur = None
    for w, t0, ok in FLIPS:
        if t0-0.3 < t < t0+0.2: cur = w
    endT = 13.5
    im = "smile"
    if 12.8 < t: im = "shock" if t < 13.6 else "sad"
    place(img, character("L", "grin" if t > endT else "smile", arm_l=165 if t > endT else 15, arm_r=150 if cur == "L" else (165 if t > endT else 15)), LX, GY - (abs(math.sin(t*8))*20 if t > endT else 0), ground_y=GY)
    place(img, character("I", im, arm_l=150 if cur == "I" else 15, arm_r=15), IX, GY, ground_y=GY)
    for who in ("L", "I"):
        mine = [(t0, ok) for w, t0, ok in FLIPS if w == who]
        hx = LX+60 if who == "L" else IX-60
        land = LX+150 if who == "L" else IX-150
        dirn = 1 if who == "L" else -1
        active = None
        for idx, (t0, ok) in enumerate(mine):
            nxt = mine[idx+1][0] if idx+1 < len(mine) else 99
            if t0-1.0 < t < nxt-1.0: active = (t0, ok)
        if active is None:
            if t > 2.2: draw_bottle(img, hx, GY-250, 0)
            continue
        t0, ok = active
        u = (t-t0)/0.8
        if u < 0: draw_bottle(img, hx, GY-250, 0)
        elif u < 1:
            x, y = arc((hx, GY-250), (land, GY-50 if ok else GY-20), u, 170)
            draw_bottle(img, x, y, (-360*ease(u) if ok else 470*u)*dirn)
        else:
            if ok: draw_bottle(img, land, GY-50, 0)
            else:
                roll = min((t-t0-0.8)*40, 25)
                draw_bottle(img, land - dirn*roll, GY-18, 470*dirn + roll*3)
    focus = (W/2, H/2); z = 1.05
    for w, t0, ok in FLIPS:
        if t0+0.6 < t < t0+1.6:
            k = ease((t-t0-0.6)/0.25) if t < t0+1.35 else 1-ease((t-t0-1.35)/0.25)
            land = LX+150 if w == "L" else IX-150
            focus = (lerp(W/2, land, k), lerp(H/2, GY-80, k)); z = 1.05 + 0.6*k
    img = grade(cam_focus(img, t, 3, focus[0], focus[1], z))
    if 2.0 < t < 3.0: caption(img, "מוות פתאומי: מי שמפספס ראשון מפסיד")
    for w, t0, ok in FLIPS:
        if t0+0.9 < t < t0+2.6:
            caption(img, ("ליאור" if w == "L" else "איתי") + (": נחת!" if ok else ": נפל!"), color=(90,230,130) if ok else (255,120,120))
    win_text(img, t, endT, "L")
    if t > endT + 0.6: caption(img, "ליאור מוביל 2:1!")
    round_card(img, f, 3, "בקבוק פליפ", (120,210,255))
    return finish(img, f, 2 if t > endT else 1, 1, pop_l=pop(t, endT), t=t)

def s_dance(f):
    t = f/FPS
    img = bgc("stage", stage_bg)
    spotlights(img, t, n=5, alpha=85)
    if t < 27: led_text(img, "קרב ריקודים", 64, (255,120,220))
    beat = t*4.4
    Ion = 3.0 <= t < 12; Lon = 12 <= t < 21; both = 21 <= t < 27
    def dancer(who, on, x, ph=0):
        if on:
            b = abs(math.sin(beat*math.pi/2 + ph))*26
            a = 100 + 60*math.sin(beat*math.pi + ph)
            style = int(t/3) % 3
            if style == 1: al, ar = 165, 165 - 40*abs(math.sin(beat*math.pi))
            elif style == 2: al, ar = 60 + 100*abs(math.sin(beat*math.pi/2)), 160 - 100*abs(math.sin(beat*math.pi/2))
            else: al, ar = a, 200 - a
            xx = x + math.sin(t*1.7 + ph)*60
            place(img, character(who, "grin", arm_l=al, arm_r=ar, legs=beat/2), xx, GY - b, ground_y=GY)
        else:
            place(img, character(who, "smile" if t < 27 else ("grin" if who == "I" else "sad"), arm_l=15, arm_r=15 if who == "L" else (165 if t > 29.5 else 15)), x, GY - (abs(math.sin(t*8))*18 if who == "I" and t > 29.5 else 0), ground_y=GY)
    # Lior spin at 18-18.6
    if Lon and 18.0 < t < 18.6:
        L = character("L", "grin", arm_l=165, arm_r=165)
        sx = abs(math.cos((t-18.0)*math.pi*8))*0.85 + 0.15
        L = L.resize((max(2, int(L.width*sx)), L.height))
        place(img, L, LX, GY - 90*math.sin((t-18.0)/0.6*math.pi), flip=int((t-18.0)*16) % 2 == 1, ground_y=GY)
    else:
        dancer("L", Lon or both, LX)
    dancer("I", Ion or both, IX, ph=1.3)
    crowd(img, t, cheer=0.9 if (Ion or Lon or both) else 0.3, seed=2)
    img = grade(camera(img, t, 4, zoom=1.06, amp=1.6))
    if 2.0 < t < 3.0: caption(img, "הקהל מחליט מי ניצח!")
    elif Ion: caption(img, "איתי פותח עם מהלכים חדשים")
    elif Lon: caption(img, "ליאור עונה" if t < 18 else "סיבוב באוויר!")
    elif both: caption(img, "דאנס־אוף: שניהם ביחד!")
    if t >= 27:
        k = ease((t-27)/2.2)
        d = ImageDraw.Draw(img, "RGBA")
        for who, x, lvl, col in (("ליאור", 560, 0.78, (255,150,60)), ("איתי", 720, 0.86, (60,150,255))):
            hgt = 260*lvl*k
            d.rounded_rectangle([(x-36)*S, 210*S, (x+36)*S, 470*S], radius=10*S, fill=(0,0,0,150), outline=(255,255,255), width=2*S)
            d.rounded_rectangle([(x-30)*S, (464-hgt)*S, (x+30)*S, 464*S], radius=8*S, fill=col)
            text(img, who, x, 495, 26, sw=4)
        text(img, "מד מחיאות הכפיים", W/2, 180, 32, fill=GOLD, sw=4)
    win_text(img, t, 29.5, "I", y=560)
    if t > 30: caption(img, "בהפרש קטן. 2:2!")
    round_card(img, f, 4, "קרב ריקודים על הבמה", (255,120,220))
    return finish(img, f, 2, 2 if t > 29.5 else 1, pop_i=pop(t, 29.5), t=t)

def s_half(f):
    t = f/FPS
    img = bgc("stage", stage_bg)
    spotlights(img, t, alpha=45)
    led_text(img, "הפסקה", 44, (255,255,255), y=120)
    led_text(img, "2  :  2", 90, GOLD, y=215)
    # both drinking water, panting
    for who, x in (("L", LX), ("I", IX)):
        drink = (t % 4) < 2.0
        place(img, character(who, "smile" if drink else "grin", arm_l=15 if who == "L" else (150 if drink else 15), arm_r=(150 if drink else 15) if who == "L" else 15, blink=drink), x, GY + math.sin(t*5)*2, ground_y=GY)
        hx = x + (60 if who == "L" else -60)
        if drink: draw_bottle(img, hx, GY-330, 140 if who == "L" else -140)
    crowd(img, t, cheer=0.5, seed=3)
    img = grade(camera(img, t, 5, zoom=1.04))
    if t < 4: caption(img, "אחרי 4 סיבובים: תיקו!", color=GOLD)
    elif t < 8: caption(img, "שני סיבובים אחרונים. המתח בשיא")
    else: caption(img, "ממשיכים...")
    return finish(img, f, 2, 2, t=t)

def s_lemon(f):
    t = f/FPS
    img = bgc("kit", kitchen)
    cd = t - 3.0; bite = cd > 3.0; after = cd - 3.0
    sour = bite and after > 3.2
    sh = random.Random(f).uniform(-4, 4) if sour else 0
    strain = bite and 1.5 < after < 3.2
    place(img, character("L", "sour" if sour else "smile", arm_l=15, arm_r=150 if not bite else 158, lemon=(1, bite), blink=strain and f % 18 < 3), LX + sh, GY, rot=sh*0.5, ground_y=GY)
    place(img, character("I", "sour" if sour else "smile", arm_l=150 if not bite else 158, arm_r=15, lemon=(-1, bite), blink=strain and f % 23 < 3), IX - sh, GY, rot=-sh*0.5, ground_y=GY)
    hy = head_y(GY) + 30
    fx, fy, z = W/2, H/2, 1.05
    if bite and 0.8 < after < 2.0: k = ease((after-0.8)/0.3); fx, fy, z = lerp(W/2, LX, k), lerp(H/2, hy, k), 1.05 + 1.3*k
    elif bite and 2.0 <= after < 3.2: k = ease((after-2.0)/0.2); fx, fy, z = lerp(LX, IX, k), hy, 2.35
    elif bite and after >= 3.2: k = ease((after-3.2)/0.25); fx, fy, z = lerp(IX, W/2, k), lerp(hy, H/2, k), lerp(2.35, 1.05, k)
    img = grade(cam_focus(img, t, 6, fx, fy, z, amp=0.5 if z > 1.5 else 1.0))
    if 0 <= cd < 3.0:
        n = 3 - int(cd); k = ease_out_back((cd % 1)/0.35)
        text(img, str(n), W/2, 260, 150*k, fill=(255,90,90), sw=9, rtl=False)
        caption(img, "לימון בלי פרצוף, הפעם שניהם ביחד")
    elif bite and after < 0.8:
        text(img, "ביס!", W/2, 260, 120*ease_out_back(after/0.3), fill=(255,90,90), sw=9)
    elif bite and after < 2.0: caption(img, "ליאור מחזיק...", y=640)
    elif bite and after < 3.2: caption(img, "איתי מחזיק...", y=640)
    if sour:
        k = ease_out_back((after-3.4)/0.4)
        text(img, "חמוווווץ!", W/2, 220, 66*k, fill=(200,255,80), sw=6)
        if after > 4.4: caption(img, "שניהם נשברו באותה שנייה! אין נקודה, נשאר 2:2")
    round_card(img, f, 5, "לימון בלי פרצוף", (255,240,110))
    return finish(img, f, 2, 2, t=t)

def s_final(f):
    t = f/FPS
    stop = 13.0
    replay = 15.5 <= t < 20.5
    tt = 13.0 + (t-15.5)*0.15 if replay else t
    img = bgc("stage", stage_bg)
    spotlights(img, tt, n=4, alpha=70 if tt < stop else 35)
    led_text(img, "סיבוב מכריע", 60, GOLD)
    a0 = (stop-2.0)*1.9
    if tt < stop:
        a = (tt-2.0)*1.9 if tt > 2.0 else 0
        lx = POUF_X + math.cos(a)*240; ix = POUF_X + math.cos(a+math.pi)*240
        beat = tt*4
        order = [("L", lx, math.sin(a)), ("I", ix, math.sin(a+math.pi))]
        drawn = False
        for who, x, depth in sorted(order, key=lambda o: o[2]):
            if depth > 0 and not drawn: pouf(img); drawn = True
            arm = 90 + 50*math.sin(beat*math.pi + (0 if who == "L" else 1))
            place(img, character(who, "grin", arm_l=arm, arm_r=180-arm, legs=beat/2), x, GY - abs(math.sin(beat*math.pi/2))*10 + depth*8, ground_y=GY + depth*8)
        if not drawn: pouf(img)
    else:
        u = tt - stop
        lx0 = POUF_X + math.cos(a0)*240; ix0 = POUF_X + math.cos(a0+math.pi)*240
        pouf(img)
        if u < 0.6:
            place(img, character("L", "shock", arm_l=60, arm_r=60, legs=u*4), lerp(lx0, POUF_X-40, ease(u/0.6)), GY, ground_y=GY)
            place(img, character("I", "shock", arm_l=60, arm_r=60, legs=u*4), lerp(ix0, POUF_X+40, ease(u/0.6)), GY, ground_y=GY)
        else:
            happy = t > 22.5
            seated(img, "L", POUF_X-42, mood="grin" if happy else "shock", arm_l=160 if happy else 40, arm_r=40 if not happy else 120)
            seated(img, "I", POUF_X+42, mood="grin" if happy else "shock", arm_l=120 if happy else 40, arm_r=160 if happy else 40)
    crowd(img, tt, cheer=0.8 if tt < stop or t > 22.5 else 0.15, seed=4)
    z = 1.05 + (0.25*ease((tt-stop)/0.4) if tt > stop else 0)
    if replay: z = 1.5
    img = grade(cam_focus(img, tt, 7, POUF_X, H/2 + (60 if z > 1.2 else 0), z))
    if replay:
        arr = np.asarray(img.convert("RGB"), dtype=np.float32)
        g = arr.mean(axis=2, keepdims=True)
        arr = (arr*0.35 + g*0.65)*np.array([1.0, 0.97, 1.08])
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB").convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([(W-250)*S, 140*S, (W-30)*S, 190*S], radius=10*S, fill=(220,30,40))
        text(img, "הילוך חוזר", W-140, 165, 28, sw=0)
        if int(t*2) % 2 == 0: d.ellipse([(W-280)*S, 155*S, (W-262)*S, 173*S], fill=(255,60,60))
        caption(img, "בודקים מי ישב ראשון...")
    elif 3.0 < t < stop:
        caption(img, "כשהמוזיקה נעצרת, מי שיושב על הפוף זוכה בגביע!")
        for n in range(4):
            p = (t*0.6 + n/4) % 1
            text(img, "♪" if n % 2 else "♫", 200 + n*280 + math.sin(p*8)*20, 560 - p*380, 44, fill=(255,255,255,int(255*(1-p))), sw=3, stroke=(60,40,80), rtl=False)
    elif stop <= t < 15.5:
        text(img, "המוזיקה נעצרה!", W/2, 240, 60*ease_out_back((t-stop)/0.3), fill=(255,90,90), sw=6)
    elif 20.5 <= t < 22.5:
        text(img, "באותה שנייה בדיוק!", W/2, 240, 58*ease_out_back((t-20.5)/0.4), fill=(255,225,70), sw=6)
    if t > 22.5:
        k = ease_out_back((t-22.5)/0.4)
        text(img, "נקודה לשניהם!", W/2, 240, 60*k, fill=(90,230,130), sw=6)
        caption(img, "3:3. תיקו בגמר!", color=GOLD)
    round_card(img, f, 6, "קרב על הפוף: הסיבוב המכריע", GOLD)
    sc = 3 if t > 22.5 else 2
    return finish(img, f, sc, sc, pop_l=pop(t, 22.5), pop_i=pop(t, 22.5), t=t)

def clapper(img, lt, take):
    if lt > 0.8: return
    k = ease_out_back(lt/0.25)
    sp = Image.new("RGBA", (260*S, 200*S), (0,0,0,0)); d = ImageDraw.Draw(sp)
    d.rectangle([10*S, 60*S, 250*S, 195*S], fill=(25,25,25))
    ang = 0 if lt > 0.35 else 25*(1 - lt/0.35)
    top = Image.new("RGBA", (240*S, 40*S), (0,0,0,0)); td = ImageDraw.Draw(top)
    td.rectangle([0, 0, 240*S, 40*S], fill=(25,25,25))
    for i in range(6): td.polygon([((i*40+10)*S, 0), ((i*40+30)*S, 0), ((i*40+10)*S, 40*S), ((i*40-10)*S, 40*S)], fill=(240,240,240))
    top = top.rotate(ang, expand=True, center=(0, 40*S))
    sp.alpha_composite(top, (10*S, max(0, 20*S - (top.height-40*S))))
    d.text((130*S, 130*S), f"טייק {take}", font=font(36), fill=(255,255,255), anchor="mm", direction="rtl")
    sp = sp.resize((int(sp.width*k)+1, int(sp.height*k)+1))
    img.alpha_composite(sp, (int(W/2*S - sp.width/2), int(330*S - sp.height/2)))

def s_bloopers(f):
    t = f/FPS
    bit = min(3, int(t/7.5)); lt = t - bit*7.5
    if bit == 0:  # Itay banana
        img = bgc("kit", kitchen); bx = 620
        if lt < 2.75:
            pm, pd = newmask(img.size)
            pd.ellipse([(bx-34)*S, (GY-14)*S, (bx+34)*S, (GY+4)*S], fill=255)
            for s_ in (-1, 1): pd.polygon([(bx*S, (GY-6)*S), ((bx+s_*52)*S, (GY-18)*S), ((bx+s_*30)*S, GY*S)], fill=255)
            paint(img, pm, (245,205,50), soft=4)
        if lt < 2.7:
            x = -150 + clamp((lt-0.6)/2.1)*(bx+150)
            place(img, character("I", "smile", arm_l=15+15*math.sin(lt*10), arm_r=15-15*math.sin(lt*10), legs=lt*1.8), x, GY, ground_y=GY)
        else:
            u = lt - 2.7
            if u < 0.9:
                place(img, character("I", "shock", arm_l=170, arm_r=170), bx + u*160, min(GY - (440*u - 475*u*u), GY), rot=-u*520, ground_y=GY)
            else:
                place(img, character("I", "laugh", arm_l=70, arm_r=70), bx, GY - 70 + (FEET[1]-CENTER_Y)*0.84, rot=90, shadow=False)
                stars(img, bx - (CENTER_Y-72)*0.84, GY - 150, u)
        laugh = lt > 3.2
        place(img, character("L", "laugh" if laugh else "smile", arm_l=50 + (20*math.sin(t*20) if laugh else 0), arm_r=50 - (20*math.sin(t*20) if laugh else 0)), 1110, GY, ground_y=GY)
        cap = "איתי והבננה: חלק 2!"
    elif bit == 1:  # trophy too heavy
        img = bgc("stage", stage_bg)
        lx = 560
        if lt < 2.2:
            place(img, character("L", "grin", arm_l=40, arm_r=40), lx, GY, ground_y=GY)
            trophy(img, lx + 90, GY, 0.8)
        elif lt < 3.6:
            w = math.sin((lt-2.2)*14)*10
            place(img, character("L", "shock", arm_l=165, arm_r=165), lx, GY, rot=w, ground_y=GY)
            trophy(img, lx + w*3, head_y(GY) - 10, 0.8)
        else:
            u = lt - 3.6
            place(img, character("L", "sad" if u < 2 else "laugh", arm_l=70, arm_r=70), lx, GY - 70 + (FEET[1]-CENTER_Y)*0.84, rot=-90, shadow=False)
            trophy(img, lx - 150, GY, 0.8)
            stars(img, lx + (CENTER_Y-72)*0.84, GY - 150, u)
        place(img, character("I", "laugh" if lt > 3.8 else "smile", arm_l=50, arm_r=50), 1000, GY, ground_y=GY)
        cap = "הגביע כבד יותר ממה שחשבנו"
    elif bit == 2:  # collision
        img = bgc("lr", living_room)
        hit = 1.6
        if lt < hit:
            k = clamp((lt-0.4)/(hit-0.4))
            place(img, character("L", "grin", arm_l=40, arm_r=40, legs=lt*3), lerp(-100, W/2-60, k), GY, ground_y=GY)
            place(img, character("I", "grin", arm_l=40, arm_r=40, legs=lt*3), lerp(W+100, W/2+60, k), GY, ground_y=GY)
        else:
            u = lt - hit
            if u < 0.5:
                place(img, character("L", "shock", arm_l=160, arm_r=160), W/2-60 - u*200, GY + u*60, rot=u/0.5*90 if u > 0 else 0, ground_y=GY)
                place(img, character("I", "shock", arm_l=160, arm_r=160), W/2+60 + u*200, GY + u*60, rot=-u/0.5*90, ground_y=GY)
            else:
                yl = GY - 70 + (FEET[1]-CENTER_Y)*0.84
                place(img, character("L", "laugh" if u > 2.5 else "sad", arm_l=70, arm_r=70), W/2-200, yl, rot=90, shadow=False)
                place(img, character("I", "laugh" if u > 2.5 else "sad", arm_l=70, arm_r=70), W/2+200, yl, rot=-90, shadow=False)
                stars(img, W/2-200 - (CENTER_Y-72)*0.84, GY - 150, u)
                stars(img, W/2+200 + (CENTER_Y-72)*0.84, GY - 150, u + 1)
        cap = "שניהם רצו לאותו מקום!"
    else:  # Lior backflip
        img = bgc("lr", living_room)
        lx = 560; jump = 2.0
        if lt < jump:
            place(img, character("L", "grin", arm_l=40 if lt < 1.6 else 150, arm_r=40 if lt < 1.6 else 150), lx, GY + (8 if lt > 1.6 else 0), ground_y=GY)
        elif lt < jump + 0.8:
            u = (lt - jump)/0.8
            place(img, character("L", "shock", arm_l=170, arm_r=170), lx + u*80, GY - 260*4*u*(1-u), rot=-u*300, ground_y=GY)
        else:
            u = lt - jump - 0.8
            place(img, character("L", "sad" if u < 2.4 else "laugh", arm_l=70, arm_r=70), lx + 80, GY - 70 + (FEET[1]-CENTER_Y)*0.84, rot=-90, shadow=False)
            stars(img, lx + 80 + (CENTER_Y-72)*0.84, GY - 150, u)
        place(img, character("I", "laugh" if lt > jump + 1.0 else "smile", arm_l=50, arm_r=50, look=-1), 1000, GY, ground_y=GY)
        cap = "ליאור מנסה סלטה..."
    shake = 3.0 if (bit == 0 and 3.5 < lt < 3.8) or (bit == 2 and 1.6 < lt < 1.9) or (bit == 3 and 2.8 < lt < 3.1) else 1.3
    img = grade(camera(img, t, 8 + bit, zoom=1.04, amp=shake))
    img = vhs(img)
    rec_badge(img, t)
    text(img, "מאחורי הקלעים", W/2, 95, 40, fill=(255,225,70), sw=5)
    caption(img, cap, y=150)
    clapper(img, lt, [3, 9, 14, 27][bit])
    badge(img)
    return img

def s_ceremony(f):
    t = f/FPS
    img = bgc("stage", stage_bg)
    spotlights(img, t, n=5, alpha=60 if t < 3 else 90)
    shots = [(3.0, 300, 170, (255,200,60)), (3.3, 980, 150, (90,200,255)), (3.7, 640, 100, (255,90,160)),
             (6.0, 200, 200, (140,255,140)), (6.3, 1080, 190, (255,200,60)), (9.0, 400, 130, (255,120,200)),
             (9.4, 880, 130, (120,220,255)), (19.0, 640, 120, (255,220,120)), (19.5, 260, 160, (255,90,90)), (20.0, 1020, 160, (90,255,160))]
    fireworks(img, t, shots)
    led_text(img, "אלופי העונה", 60, GOLD)
    # podium
    d = ImageDraw.Draw(img, "RGBA")
    pm, pd = newmask(img.size)
    pd.rectangle([440*S, (GY-70)*S, 840*S, GY*S], fill=255)
    paint(img, pm, (230,180,40), soft=10, light=(1.4, 0.7))
    text(img, "1", 640, GY-35, 48, fill=(120,80,0), sw=0, rtl=False)
    lift = t > 6.0
    py = GY - 70
    lb = abs(math.sin(t*6))*14 if t > 19 else 0
    place(img, character("L", "grin", arm_l=40 if not lift else 30, arm_r=165 if lift else (150 + 20*math.sin(t*9) if t > 3 else 15)), 570, py - lb, ground_y=py)
    place(img, character("I", "grin", arm_l=165 if lift else (150 + 20*math.sin(t*9) if t > 3 else 15), arm_r=40 if not lift else 30), 710, py - lb, ground_y=py)
    if t > 3.0:
        if t < 6.0:
            ty = lerp(-60, head_y(py) - 30, ease((t-3.0)/2.5))
        else:
            ty = head_y(py) - 30 + math.sin(t*4)*6 - lb
        trophy(img, 640, ty, 0.62, sparkle_t=t)
    crowd(img, t, cheer=0.2 if t < 3 else 1.0, seed=5)
    img = grade(camera(img, t, 9, zoom=1.06 + 0.06*math.sin(t*0.4)))
    if t > 3: confetti(img, t - 3, n=90)
    if t < 3.0:
        text(img, "והאלופים של העונה הם...", W/2, 380, 52*ease_out_back(t/0.5), fill=(255,255,255), sw=6)
    elif t < 9.0:
        k = ease_out_back((t-3.0)/0.5)
        text(img, "ליאור ואיתי!", W/2, 330, 92*k, fill=GOLD, sw=8, stroke=(70,30,0))
    if 9.0 < t < 14.0: caption(img, "ליאור: \"אין עם מי לעשות את זה חוץ ממך\"", color=(255,190,120))
    elif 14.0 <= t < 19.0: caption(img, "איתי: \"גם אני... אבל בעונה הבאה אני מנצח!\"", color=(150,200,255))
    elif t >= 19.0: caption(img, "אלופי עונה 1!", color=GOLD)
    return finish(img, f, 3, 3, t=t, rec=False)

CREDITS = [("בכיכוב", "ליאור ואיתי"), ("צלם", "המצלמה הרועדת"), ("אחראי בננות", "איתי"), ("אחראי לימונים", "המקרר"),
           ("כפיות", "המגירה במטבח"), ("מטוסי נייר", "המדפסת"), ("פוף", "הפוף האדום"), ("ריקודים", "ליאור ואיתי"),
           ("קהל", "כל מי שצפה"), ("תודה מיוחדת", "לכם!")]
def s_credits(f):
    t = f/FPS
    img = Image.new("RGBA", (W*S, H*S))
    img.alpha_composite(vgrad(W*S, H*S, (10,6,30), (40,15,60)))
    d = ImageDraw.Draw(img, "RGBA")
    rr = random.Random(11)
    for i in range(80):
        x, y = rr.uniform(0, W), rr.uniform(0, H)
        a = int(120 + 120*math.sin(t*2 + i))
        d.ellipse([(x-1.5)*S, (y-1.5)*S, (x+1.5)*S, (y+1.5)*S], fill=(255,255,255,max(0, a)))
    y0 = H + 40 - t*62
    text(img, "הוולוג של ליאור ואיתי", 470, y0, 54, fill=GOLD, sw=5)
    text(img, "ספיישל הגמר הגדול", 470, y0 + 60, 34, fill=(255,255,255), sw=0)
    for i, (role, name) in enumerate(CREDITS):
        yy = y0 + 160 + i*78
        if -40 < yy < H + 40:
            text(img, role, 470, yy, 24, fill=(190,180,230), sw=0)
            text(img, name, 470, yy + 30, 34, fill=(255,255,255), sw=0)
    end_y = y0 + 160 + len(CREDITS)*78 + 80
    text(img, "נוצר עם Claude", 470, end_y, 26, fill=(190,180,230), sw=0)
    # small waving duo
    wv = 150 + 25*math.sin(t*9)
    place(img, character("L", "grin", arm_l=wv, arm_r=40), 1010, 660 - abs(math.sin(t*5))*8, scale=0.55, ground_y=660)
    place(img, character("I", "grin", arm_l=40, arm_r=wv), 1150, 660 - abs(math.sin(t*5+1))*8, scale=0.55, ground_y=660)
    if t > 18.0:
        k = ease_out_back((t-18.0)/0.5)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, W*S, H*S], fill=(0,0,0,int(150*clamp((t-18)/0.6))))
        text(img, "עונה 2 בקרוב...", W/2, 300, 76*k, fill=GOLD, sw=6, stroke=(70,30,0))
        pulse = 1 + 0.05*math.sin(t*8)
        bw, bh = 220*k*pulse, 42*k*pulse
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([(W/2-bw)*S, (430-bh)*S, (W/2+bw)*S, (430+bh)*S], radius=int(20*S*k), fill=(225,30,40))
        text(img, "לייק והרשמה!", W/2, 430, 44*k*pulse, sw=0)
    if t > 23.0: img.alpha_composite(Image.new("RGBA", img.size, (0,0,0,int(255*clamp((t-23.0)/1.0)))))
    badge(img)
    return img

SCENES = [("s01_open", s_open, 16.0), ("s03_host", s_host, 14.0), ("s04_spoon", s_spoon, 20.0),
          ("s05_basket", s_basket, 30.0), ("s06_bottle", s_bottle, 22.0), ("s07_dance", s_dance, 32.0),
          ("s08_half", s_half, 12.0), ("s09_lemon", s_lemon, 18.0), ("s10_final", s_final, 28.0),
          ("s11_bloopers", s_bloopers, 30.0), ("s12_ceremony", s_ceremony, 26.0), ("s13_credits", s_credits, 24.0)]

if __name__ == "__main__":
    os.makedirs("ep4", exist_ok=True)
    if sys.argv[1] == "preview":
        want = sys.argv[2:]
        pts = {"s01_open": [1.5, 6.0, 12.0], "s03_host": [2.0, 5.5], "s04_spoon": [1.0, 10.0, 12.0, 13.0],
               "s05_basket": [7.2, 14.6, 26.0], "s06_bottle": [3.5, 10.2, 14.5], "s07_dance": [6.0, 18.3, 24.0, 30.0],
               "s08_half": [5.0], "s09_lemon": [7.5, 9.8, 11.0], "s10_final": [8.0, 14.0, 17.0, 23.5],
               "s11_bloopers": [0.3, 5.0, 12.0, 19.0, 26.0], "s12_ceremony": [2.0, 4.5, 10.0], "s13_credits": [8.0, 20.0]}
        for name, fn, dur in SCENES:
            if want and name not in want: continue
            for tt in pts[name]:
                render_frame(fn, int(tt*FPS)).save(f"ep4/prev_{name}_{tt:04.1f}.png")
    else:
        from multiprocessing import Pool
        names = sys.argv[2:]
        jobs = [s for s in SCENES if not names or s[0] in names]
        with Pool(2) as pool:
            pool.starmap(render_scene, jobs, chunksize=1)
