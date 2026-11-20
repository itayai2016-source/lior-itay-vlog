import sys, os, math, random
import real
from real import *
import ep2
from ep2 import cam_focus, lerp, arc, stars

real.FACE = None
real.OUT = "ep3"

def book(img, x, y, rot=0, color=(40,120,90)):
    sp = Image.new("RGBA", (90*S, 40*S), (0,0,0,0))
    m, md = newmask(sp.size)
    md.rounded_rectangle([6*S, 10*S, 84*S, 30*S], radius=3*S, fill=255)
    paint(sp, m, color, soft=3, rim=0.4)
    d = ImageDraw.Draw(sp, "RGBA")
    d.rectangle([10*S, 24*S, 80*S, 28*S], fill=(245,240,225))
    d.line([(6*S, 18*S), (84*S, 18*S)], fill=(255,220,120), width=2*S)
    sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(sp, (int(x*S - sp.width/2), int(y*S - sp.height/2)))

def plane(img, x, y, ang):
    sp = Image.new("RGBA", (90*S, 50*S), (0,0,0,0))
    d = ImageDraw.Draw(sp, "RGBA")
    d.polygon([(85*S, 25*S), (5*S, 8*S), (25*S, 26*S)], fill=(250,250,250), outline=(150,150,160))
    d.polygon([(85*S, 25*S), (25*S, 26*S), (8*S, 44*S)], fill=(220,222,230), outline=(150,150,160))
    d.line([(85*S, 25*S), (20*S, 27*S)], fill=(140,140,150), width=S)
    sp = sp.rotate(ang, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(sp, (int(x*S - sp.width/2), int(y*S - sp.height/2)))

POUF_X = 640
def pouf(img, x=POUF_X, part="all"):
    m, md = newmask(img.size)
    md.rounded_rectangle([(x-75)*S, (GY-100)*S, (x+75)*S, GY*S], radius=30*S, fill=255)
    paint(img, m, (200,60,90), soft=14, rim=0.35)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([(x-70)*S, (GY-108)*S, (x+70)*S, (GY-86)*S], fill=(225,85,115))
    for k in (-40, 0, 40):
        d.line([((x+k)*S, (GY-92)*S), ((x+k*1.1)*S, (GY-6)*S)], fill=(0,0,0,35), width=2*S)

def seated(img, who, x, mood="grin", arm_l=20, arm_r=20, pouf_x=POUF_X):
    """character sitting on pouf: torso layer cropped at hips + legs dangling in front"""
    lay = character(who, mood, arm_l=arm_l, arm_r=arm_r)
    cut = 318*S
    lay = lay.crop((0, 0, lay.width, cut))
    full = Image.new("RGBA", (LW*S, LH*S), (0,0,0,0)); full.alpha_composite(lay)
    hip_y = GY - 100
    place(img, full, x, hip_y + 0.84*(FEET[1]-308), shadow=False)
    pr = PROFILE[who]
    m, md = newmask(img.size)
    for side in (-1, 1):
        hx = x + side*16
        md.rounded_rectangle([(hx-14)*S, (hip_y-12)*S, (hx+14)*S, (GY-14)*S], radius=12*S, fill=255)
    paint(img, m, pr["pants"], soft=5)
    m, md = newmask(img.size)
    for side in (-1, 1):
        hx = x + side*18
        md.rounded_rectangle([(hx-14)*S, (GY-20)*S, (hx+16)*S, (GY-2)*S], radius=8*S, fill=255)
    paint(img, m, pr["shoes"], soft=3)

LX, IX = 380, 900

def sc_intro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    kL = ease_out_back((t-0.8)/0.6); kI = ease_out_back((t-0.5)/0.6)
    ai = 120 + 15*math.sin(t*12) if t > 1.6 else 15
    hopI = abs(math.sin(t*5))*16 if t > 1.6 else 0
    place(img, character("L", "grin" if t < 2.4 else "shock", arm_l=150 + 25*math.sin(t*9) if 1.6 < t < 2.4 else 15, arm_r=15, legs=t*2 if t < 1.4 else 0), -200 + kL*560, GY, ground_y=GY)
    place(img, character("I", "sour" if t > 1.6 else "smile", arm_l=ai, arm_r=ai, legs=t*2 if t < 1.2 else 0), W+200 - kI*560, GY - hopI, ground_y=GY)
    img = grade(camera(img, t, 0, zoom=1.04 + 0.03*ease(t/5)))
    rec_badge(img, t)
    k = ease_out_back((t-0.1)/0.5)
    text(img, "הוולוג של", W/2, 130, 46*k, sw=5)
    text(img, "ליאור ואיתי", W/2, 205, 96*k, fill=(255,225,70), sw=8)
    k2 = ease_out_back((t-1.3)/0.5)
    if k2 > 0.02:
        d = ImageDraw.Draw(img, "RGBA"); bw = 250*k2
        d.rounded_rectangle([(W/2-bw)*S, 262*S, (W/2+bw)*S, 312*S], radius=25*S, fill=(40,110,220))
        text(img, "פרק 3: איתי מחזיר!", W/2, 287, 38*k2, sw=0)
    if 2.2 < t < 3.8: caption(img, "איתי: \"עכשיו תורי לנקום!\"", color=(150,200,255))
    elif t >= 3.8: caption(img, "ליאור: \"אוי לא...\"", color=(255,190,120))
    flash(img, f)
    return img

def sc_book(f):
    t = f/FPS
    img = bgc("lr", living_room)
    d = ImageDraw.Draw(img, "RGBA")
    # finish flags
    for fx in (650, 1150):
        d.rectangle([fx*S, (GY-190)*S, (fx+5)*S, GY*S], fill=(60,60,60))
        for r in range(4):
            for c in range(5):
                if (r+c) % 2 == 0: d.rectangle([(fx+5+c*10)*S, (GY-190+r*10)*S, (fx+15+c*10)*S, (GY-180+r*10)*S], fill=(20,20,20))
                else: d.rectangle([(fx+5+c*10)*S, (GY-190+r*10)*S, (fx+15+c*10)*S, (GY-180+r*10)*S], fill=(255,255,255))
    walk = clamp((t-1.8)/4.0)
    # Lior: drops book at 4.0 and stops
    lstop = t > 4.0
    lx = 150 + (min(t, 4.0)-1.8)/4.0*480 if t > 1.8 else 150
    ix = 640 + walk*480
    wobL = math.sin(t*9)*(t-1.8)*5 if 1.8 < t < 4.0 else 0
    lm = "smile" if t < 4.0 else ("shock" if t < 4.8 else "sad")
    place(img, character("L", lm, arm_l=70 + 25*math.sin(t*9), arm_r=70 - 25*math.sin(t*9), legs=(t-1.8)*1.6 if 1.8 < t < 4.0 else 0), lx, GY - (abs(math.sin(t*6))*3 if 1.8 < t < 4.0 else 0), rot=wobL*0.3, ground_y=GY)
    im = "smile" if walk < 1 else "grin"
    place(img, character("I", im, arm_l=70 if walk < 1 else 165, arm_r=70 if walk < 1 else 165, legs=(t-1.8)*1.6 if 0 < walk < 1 else 0), ix, GY - (abs(math.sin(t*6))*3 if 0 < walk < 1 else (abs(math.sin(t*8))*18 if walk >= 1 else 0)), ground_y=GY)
    # books
    if t < 4.0:
        book(img, lx + wobL*0.6, GY - 403 + abs(math.sin(t*6))*-3, rot=wobL*1.5, color=(200,60,60))
    else:
        u = t - 4.0
        if u < 0.5:
            book(img, lx - 30 - u*120, GY - 403 + 0.5*2600*u*u, rot=60 + u*500, color=(200,60,60))
        else:
            book(img, lx - 90, GY - 10, rot=8, color=(200,60,60))
    book(img, ix, GY - 415 + (abs(math.sin(t*6))*-3 if 0 < walk < 1 else 0), rot=math.sin(t*5)*2 if walk < 1 else 0)
    img = grade(camera(img, t, 1, zoom=1.04))
    rec_badge(img, t)
    if 1.8 < t < 4.0: caption(img, "ספר על הראש, הולכים עד הדגל")
    elif 4.0 <= t < 6.2: caption(img, "הספר של ליאור נפל!")
    if t > 6.2:
        k = ease_out_back((t-6.2)/0.4)
        text(img, "+1 לאיתי", W/2, 230, 60*k, fill=(90,230,130), sw=6)
        caption(img, "איתי הגיע עד הסוף בלי ליפול")
    scoreboard(img, 0, 1 if t > 6.2 else 0, pop_i=clamp(1-(t-6.2)/0.3) if t > 6.2 else 0)
    title_card(img, f, "אתגר #1", "ספר על הראש", color=(150,220,150))
    flash(img, f)
    return img

def sc_plane(f):
    t = f/FPS
    img = bgc("lr", living_room)
    lx, ix = 230, 470
    hx, hy = lx, GY - 360
    ai = 150 if 1.8 < t < 2.2 else 15
    al = 150 if 4.0 < t < 4.4 else 15
    im = "smile" if t < 3.2 else ("grin" if t < 5.4 else "laugh")
    lm = "smile" if t < 5.4 else ("shock" if t < 6.0 else "sad")
    place(img, character("I", im, arm_l=15, arm_r=ai if t < 3.2 else (165 if t < 4.0 else (40 + 15*math.sin(t*20) if t > 5.4 else 15))), ix, GY - (abs(math.sin(t*8))*16 if 3.2 < t < 4.0 else 0), ground_y=GY)
    rL = math.sin((t-5.4)*18)*6*max(0, 1-(t-5.4)) if t > 5.4 else 0
    place(img, character("L", lm, arm_l=15, arm_r=al), lx, GY, rot=rL, ground_y=GY)
    # Itay plane: straight across with gentle wave
    u = (t-2.0)/1.4
    if 0 <= u < 1:
        x = lerp(ix+50, W+120, u); y = GY - 330 - 60*math.sin(u*math.pi) + 15*math.sin(u*12)
        plane(img, x, y, -8*math.cos(u*12))
    # Lior plane: up, loop, back into his head
    v = (t-4.2)/1.2
    if 0 <= v < 1:
        cx, cy, R = lx + 300, GY - 450, 100
        s0 = (lx + 60, GY - 330)
        if v < 0.3:
            w = v/0.3; x = lerp(s0[0], cx, w); y = lerp(s0[1], cy + R, w)
            vx, vy = cx - s0[0], cy + R - s0[1]
        elif v < 0.8:
            th = math.pi/2 - (v-0.3)/0.5*1.5*math.pi
            x, y = cx + R*math.cos(th), cy + R*math.sin(th)
            vx, vy = math.sin(th), -math.cos(th)
        else:
            w = (v-0.8)/0.2; x = lerp(cx - R, hx + 20, w); y = lerp(cy, hy - 10, w)
            vx, vy = hx + 20 - (cx - R), hy - 10 - cy
        plane(img, x, y, math.degrees(math.atan2(-vy, vx)))
    elif v >= 1:
        w = t - 5.4
        y = min(hy + w*500, GY - 10)
        plane(img, hx + 40 + w*40, y, 190 if y < GY - 10 else 175)
    if t > 5.4: stars(img, hx, hy - 40, t - 5.4)
    img = grade(camera(img, t, 2, zoom=1.04, amp=3.0 if 5.4 < t < 5.7 else 1.0))
    rec_badge(img, t)
    if 1.8 < t < 3.6: caption(img, "מטוס נייר: מי מעיף הכי רחוק?" if t < 2.6 else "המטוס של איתי יצא מהמסך!")
    elif 4.0 < t < 5.4: caption(img, "ליאור זורק...")
    elif 5.4 <= t < 6.0: caption(img, "...והמטוס חזר אליו")
    if t > 5.5:
        k = ease_out_back((t-5.5)/0.3)
        text(img, "בומרנג!", W/2+120, 220, 64*k, fill=(255,90,90), sw=6)
    if t > 6.0:
        k = ease_out_back((t-6.0)/0.4)
        text(img, "+1 לאיתי", W/2+120, 300, 56*k, fill=(90,230,130), sw=6)
        caption(img, "איתי מוביל 2:0")
    scoreboard(img, 0, 2 if t > 6.0 else 1, pop_i=clamp(1-(t-6.0)/0.3) if t > 6.0 else 0)
    title_card(img, f, "אתגר #2", "מטוס נייר", color=(200,220,255))
    flash(img, f)
    return img

def sc_pouf(f):
    t = f/FPS
    img = bgc("lr", living_room)
    stop = 4.5
    if t < stop:
        # circling around pouf
        a = (t-1.0)*2.2 if t > 1.0 else 0
        lx = POUF_X + math.cos(a)*230; ix = POUF_X + math.cos(a+math.pi)*230
        beat = t*4
        bl = abs(math.sin(beat*math.pi/2))*10
        order = [("L", lx, math.sin(a)), ("I", ix, math.sin(a+math.pi))]
        pouf_drawn = False
        for who, x, depth in sorted(order, key=lambda o: o[2]):
            if depth > 0 and not pouf_drawn: pouf(img); pouf_drawn = True
            arm = 90 + 50*math.sin(beat*math.pi + (0 if who == "L" else 1))
            place(img, character(who, "grin", arm_l=arm, arm_r=180-arm, legs=beat/2), x, GY - bl + depth*8, ground_y=GY + depth*8)
        if not pouf_drawn: pouf(img)
        if t > 3.6: pass
        lx_end, ix_end = lx, ix
    else:
        a = (stop-1.0)*2.2
        lx0 = POUF_X + math.cos(a)*230; ix0 = POUF_X + math.cos(a+math.pi)*230
        u = t - stop
        pouf(img)
        if u < 0.5:
            lx = lerp(lx0, POUF_X, ease(u/0.5))
            place(img, character("L", "shock", arm_l=60, arm_r=60, legs=u*4), lx, GY, ground_y=GY)
        else:
            seated(img, "L", POUF_X, mood="grin", arm_l=160 if u > 1.3 else 30, arm_r=160 if u > 1.3 else 30)
        ix = lerp(ix0, POUF_X + 170, ease(u/0.8))
        place(img, character("I", "smile" if u < 0.3 else ("shock" if u < 1.6 else "sad"), arm_l=60 if u < 0.8 else 15, arm_r=60 if u < 0.8 else 15, legs=u*4 if u < 0.8 else 0), ix, GY, ground_y=GY)
    img = grade(camera(img, t, 3, zoom=1.04 + (0.12*ease((t-stop)/0.3) if t > stop else 0)))
    rec_badge(img, t)
    if 1.2 < t < stop:
        caption(img, "קרב על הפוף: כשהמוזיקה נעצרת, יושבים!")
        d = ImageDraw.Draw(img, "RGBA")
        for n in range(4):
            p = (t*0.6 + n/4) % 1
            text(img, "♪" if n % 2 else "♫", 200 + n*280 + math.sin(p*8)*20, 560 - p*380, 44, fill=(255,255,255,int(255*(1-p))), sw=3, stroke=(60,40,80), rtl=False)
    elif stop <= t < 5.3:
        text(img, "המוזיקה נעצרה!", W/2, 230, 60*ease_out_back((t-stop)/0.3), fill=(255,90,90), sw=6)
    if t > 5.8:
        k = ease_out_back((t-5.8)/0.4)
        text(img, "+1 לליאור", W/2, 230, 60*k, fill=(90,230,130), sw=6)
        caption(img, "ליאור תפס את הפוף ראשון!")
    scoreboard(img, 1 if t > 5.8 else 0, 2, pop_l=clamp(1-(t-5.8)/0.3) if t > 5.8 else 0)
    title_card(img, f, "אתגר #3", "קרב על הפוף", color=(255,150,190))
    flash(img, f)
    return img

def sc_blooper(f):
    t = f/FPS
    img = bgc("lr", living_room)
    pull = 2.0; land = 2.6
    px = POUF_X if t < pull else POUF_X + min((t-pull)*700, 300)
    pouf(img, px)
    lx = POUF_X - 10
    if t < pull + 0.1:
        place(img, character("L", "grin", arm_l=150 + 20*math.sin(t*9), arm_r=150 - 20*math.sin(t*9), legs=t*1.6 if t < 1.4 else 0), lerp(300, lx, clamp(t/1.4)), GY, ground_y=GY)
    elif t < land:
        u = (t - pull - 0.1)/(land - pull - 0.1)
        place(img, character("L", "shock", arm_l=170, arm_r=170), lx - u*30, GY + u*40, rot=u*90, ground_y=GY)
    else:
        u = t - land
        place(img, character("L", "sad" if u < 2.0 else "laugh", arm_l=70, arm_r=70), lx - 30, GY - 70 + (FEET[1]-CENTER_Y)*0.84, rot=90, shadow=False)
        stars(img, lx - 30 - (CENTER_Y - 72)*0.84, GY - 150, u)
    # Itay sneaks in from right, grabs pouf
    ix = lerp(W+100, POUF_X + 150, clamp((t-0.6)/1.2)) if t < pull else POUF_X + 150 + min((t-pull)*700, 300)
    place(img, character("I", "grin" if t < land + 0.2 else "laugh", arm_l=110 if t > 1.8 else 15, arm_r=15 if t < land + 0.2 else 50 + 20*math.sin(t*20), legs=t*1.8 if t < 1.8 else 0), ix, GY, ground_y=GY)
    img = grade(camera(img, t, 4, zoom=1.04, amp=3.0 if land < t < land + 0.3 else 1.4))
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    arr = (arr*0.9 + np.array([12, 6, -4])).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 4): d.line([(0, y*S), (W*S, y*S)], fill=(0,0,0,22), width=S)
    rec_badge(img, t)
    text(img, "מאחורי הקלעים", W/2, 60, 42, fill=(255,225,70), sw=5)
    if t > land:
        text(img, "בום!", lx - 30, 330, 84*ease_out_back((t-land)/0.3), fill=(255,90,90), sw=7)
        caption(img, "איתי: \"עכשיו אנחנו תיקו בשטויות\"", y=125)
    else: caption(img, "ליאור רוצה לשבת שוב על הפוף...", y=125)
    return img

def sc_outro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    wv = 150 + 25*math.sin(t*9)
    place(img, character("L", "sad" if t < 2.4 else "grin", arm_l=15 if t < 2.4 else wv, arm_r=15 if t < 2.4 else wv), 220, GY - (abs(math.sin(t*6+1))*16 if t > 2.4 else 0), ground_y=GY)
    place(img, character("I", "grin", arm_l=wv, arm_r=wv), 1060, GY - abs(math.sin(t*6))*20, ground_y=GY)
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
    if 0.9 < t < 2.4: caption(img, "איתי החזיר!", y=360, color=(150,200,255))
    elif t >= 2.4: caption(img, "פרק 4: הגמר הגדול!", y=360, color=(255,225,70))
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

SCENES = [("intro", sc_intro, 5.0), ("book", sc_book, 8.5), ("plane", sc_plane, 8.5),
          ("pouf", sc_pouf, 8.5), ("blooper", sc_blooper, 6.5), ("outro", sc_outro, 5.5)]

if __name__ == "__main__":
    os.makedirs("ep3", exist_ok=True)
    if sys.argv[1] == "preview":
        pts = {"intro": [3.0], "book": [3.2, 4.3, 7.0], "plane": [2.6, 4.7, 5.1, 6.5], "pouf": [3.0, 4.8, 6.5],
               "blooper": [2.3, 4.0], "outro": [4.0]}
        for name, fn, dur in SCENES:
            for tt in pts[name]:
                render_frame(fn, int(tt*FPS)).save(f"ep3/prev_{name}_{tt:.1f}.png")
    else:
        from multiprocessing import Pool
        with Pool(2) as pool:
            pool.starmap(render_scene, SCENES)
