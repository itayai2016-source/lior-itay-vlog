import sys, os, math, random
import real
from real import *

real.FACE = None          # drawn Itay, no photo
real.OUT = "ep2"

def cam_focus(img, t, seed, fx, fy, zoom, amp=1.0):
    sx = (math.sin(t*1.3+seed)*6 + math.sin(t*3.1+seed*2)*3)*amp
    sy = (math.sin(t*1.7+seed*3)*4 + math.sin(t*2.9+seed)*2)*amp
    cw, ch = W*S/zoom, H*S/zoom
    x0 = min(max(fx*S - cw/2 + sx*S, 0), W*S - cw)
    y0 = min(max(fy*S - ch/2 + sy*S, 0), H*S - ch)
    return img.transform(img.size, Image.AFFINE, (cw/(W*S), 0, x0, 0, ch/(H*S), y0), resample=Image.BILINEAR)

def lerp(a, b, k): return a + (b-a)*k

def arc(p0, p1, u, peak):
    """point on a throw arc from p0 to p1, u in 0..1, peak = extra height in px"""
    x = lerp(p0[0], p1[0], u); y = lerp(p0[1], p1[1], u) - peak*4*u*(1-u)
    return x, y

_spr = {}
def bottle():
    if "b" not in _spr:
        sp = Image.new("RGBA", (40*S, 100*S), (0,0,0,0))
        m, md = newmask(sp.size)
        md.rounded_rectangle([6*S, 22*S, 34*S, 98*S], radius=10*S, fill=255)
        md.polygon([(10*S, 26*S), (30*S, 26*S), (24*S, 10*S), (16*S, 10*S)], fill=255)
        paint(sp, m, (190,225,245), soft=4, light=(1.25, 0.8), rim=0.4)
        w, wd = newmask(sp.size)
        wd.rounded_rectangle([8*S, 66*S, 32*S, 96*S], radius=8*S, fill=255)
        paint(sp, w, (70,150,230), soft=4)
        d = ImageDraw.Draw(sp, "RGBA")
        d.rectangle([14*S, 2*S, 26*S, 11*S], fill=(30,80,200))
        d.rectangle([7*S, 44*S, 33*S, 58*S], fill=(240,60,60,230))
        d.line([(12*S, 30*S), (12*S, 90*S)], fill=(255,255,255,150), width=2*S)
        _spr["b"] = sp
    return _spr["b"]

def draw_bottle(img, x, y, rot):
    sp = bottle().rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(sp, (int(x*S - sp.width/2), int(y*S - sp.height/2)))

def paper_ball(img, x, y, r=13, rot=0):
    m, md = newmask(img.size)
    md.ellipse([(x-r)*S, (y-r)*S, (x+r)*S, (y+r)*S], fill=255)
    paint(img, m, (245,245,240), soft=3, rim=0.5)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(3):
        a = math.radians(rot + k*120)
        d.line([((x+math.cos(a)*r*0.7)*S, (y+math.sin(a)*r*0.7)*S), ((x-math.cos(a+1)*r*0.3)*S, (y-math.sin(a+1)*r*0.3)*S)], fill=(150,150,150), width=S)

CAN_X, CAN_TOP = 640, GY - 105
def trash_can(img, front=True):
    if front:
        m, md = newmask(img.size)
        md.polygon([((CAN_X-52)*S, CAN_TOP*S), ((CAN_X+52)*S, CAN_TOP*S), ((CAN_X+42)*S, GY*S), ((CAN_X-42)*S, GY*S)], fill=255)
        paint(img, m, (150,155,165), soft=10, light=(1.3, 0.7), rim=0.35)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(-3, 4):
            d.line([((CAN_X+k*13)*S, (CAN_TOP+10)*S), ((CAN_X+k*10.5)*S, (GY-6)*S)], fill=(0,0,0,40), width=2*S)
        d.ellipse([(CAN_X-54)*S, (CAN_TOP-10)*S, (CAN_X+54)*S, (CAN_TOP+10)*S], outline=(110,115,125), width=4*S)
    else:
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([(CAN_X-52)*S, (CAN_TOP-9)*S, (CAN_X+52)*S, (CAN_TOP+9)*S], fill=(40,40,45))

def tongue(layer, wiggle=0):
    d = ImageDraw.Draw(layer, "RGBA")
    x, y = 150 + wiggle, 72 + 33
    d.ellipse([(x-8)*S, (y-3)*S, (x+8)*S, (y+16)*S], fill=(235,95,120), outline=(170,50,70), width=S)
    d.line([(x*S, (y+1)*S), (x*S, (y+10)*S)], fill=(190,60,85), width=S)
    return layer

def stars(img, cx, cy, u, n=4, r=40):
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(n):
        a = u*5 + k*2*math.pi/n
        x, y = cx + r*math.cos(a), cy + 12*math.sin(a)
        pts = []
        for i in range(10):
            aa = math.radians(u*200 + i*36 - 90); rr = 13 if i % 2 == 0 else 5
            pts.append(((x+rr*math.cos(aa))*S, (y+rr*math.sin(aa))*S))
        d.polygon(pts, fill=(255,225,60))

LX, IX = 380, 900

# ---------------- scenes ----------------
def sc_intro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    kL = ease_out_back((t-0.5)/0.6); kI = ease_out_back((t-0.8)/0.6)
    hopL = abs(math.sin(t*5))*16 if t > 1.6 else 0
    # Lior: fists up (revenge mode); Itay: relaxed wave
    al = 120 + 15*math.sin(t*12) if t > 1.6 else 15
    place(img, character("L", "grin" if t < 2.2 else "sour", arm_l=al, arm_r=al, legs=t*2 if t < 1.2 else 0), -200 + kL*560, GY - hopL, ground_y=GY)
    place(img, character("I", "smile" if t < 2.6 else "shock", arm_l=15, arm_r=150 + 25*math.sin(t*9) if 1.6 < t < 2.6 else 15, legs=t*2 if t < 1.4 else 0), W+200 - kI*560, GY, ground_y=GY)
    img = grade(camera(img, t, 0, zoom=1.04 + 0.03*ease(t/5)))
    rec_badge(img, t)
    k = ease_out_back((t-0.1)/0.5)
    text(img, "הוולוג של", W/2, 130, 46*k, sw=5)
    text(img, "ליאור ואיתי", W/2, 205, 96*k, fill=(255,225,70), sw=8)
    k2 = ease_out_back((t-1.3)/0.5)
    if k2 > 0.02:
        d = ImageDraw.Draw(img, "RGBA"); bw = 230*k2
        d.rounded_rectangle([(W/2-bw)*S, 262*S, (W/2+bw)*S, 312*S], radius=25*S, fill=(230,40,70))
        text(img, "פרק 2: הנקמה!", W/2, 287, 38*k2, sw=0)
    if 2.2 < t < 3.8: caption(img, "ליאור: \"הפעם אני מנצח!\"", color=(255,190,120))
    elif t >= 3.8: caption(img, "איתי: \"נראה אותך...\"", color=(150,200,255))
    flash(img, f)
    return img

def sc_bottle(f):
    t = f/FPS
    img = bgc("lr", living_room)
    # Itay throw 2.2 -> fail; Lior throw 4.8 -> success
    ui = (t-2.2)/0.8; ul = (t-4.8)/0.8
    im = "smile"
    if t > 3.0: im = "sad"
    if t > 5.6: im = "shock"
    lm = "smile" if t < 5.6 else "grin"
    ai = 150 if 2.0 < t < 2.4 else (60 if t < 2.0 else 15)
    al = 150 if 4.6 < t < 5.0 else (60 if 3.4 < t < 4.6 else (165 if t > 5.8 else 15))
    hopL = abs(math.sin(t*8))*22 if t > 5.8 else 0
    place(img, character("L", lm, arm_l=al if t > 5.8 else 15, arm_r=al), LX, GY - hopL, ground_y=GY)
    place(img, character("I", im, arm_l=ai, arm_r=15), IX, GY)
    # Itay bottle
    if t < 2.2:
        if t > 1.0: draw_bottle(img, IX-60, GY-250, 0)
    elif ui < 1:
        x, y = arc((IX-60, GY-250), (IX-150, GY-20), ui, 160); draw_bottle(img, x, y, ui*470)
    else:
        roll = min((t-3.0)*40, 25)
        draw_bottle(img, IX-150-roll, GY-18, 470 + roll*3)
    # Lior bottle
    if 3.4 < t < 4.8:
        draw_bottle(img, LX+60, GY-250, 0)
    elif 0 <= ul < 1:
        x, y = arc((LX+60, GY-250), (LX+150, GY-50), ul, 170); draw_bottle(img, x, y, -360*ease(ul))
    elif ul >= 1:
        sq = max(0, 1 - (t-5.6)/0.25)
        draw_bottle(img, LX+150, GY-50, math.sin((t-5.6)*40)*8*sq)
    focus = (W/2, H/2); zoom = 1.05
    if 5.5 < t < 6.4:
        k = ease((t-5.5)/0.3) if t < 6.1 else 1 - ease((t-6.1)/0.3)
        focus = (lerp(W/2, LX+150, k), lerp(H/2, GY-80, k)); zoom = 1.05 + 0.6*k
    img = grade(cam_focus(img, t, 1, focus[0], focus[1], zoom))
    rec_badge(img, t)
    if 1.8 < t < 3.4: caption(img, "איתי מנסה ראשון..." if t < 3.0 else "נפל על הצד. אאוץ'")
    elif 3.4 <= t < 5.6: caption(img, "תור של ליאור")
    if t > 6.0:
        k = ease_out_back((t-6.0)/0.4)
        text(img, "נחת עומד!", W/2, 270, 60*k, fill=(255,225,70), sw=6)
        text(img, "+1 לליאור", W/2, 350, 56*k, fill=(90,230,130), sw=6)
        caption(img, "ליאור על הלוח!")
    scoreboard(img, 1 if t > 6.0 else 0, 0, pop_l=clamp(1-(t-6.0)/0.3) if t > 6.0 else 0)
    title_card(img, f, "אתגר #1", "בקבוק פליפ", color=(120,210,255))
    flash(img, f)
    return img

def sc_basket(f):
    t = f/FPS
    img = bgc("lr", living_room)
    ui = (t-2.2)/0.8; ul = (t-4.6)/0.8
    trash_can(img, front=False)
    # throwers
    ai = 160 if 2.0 < t < 2.4 else 15
    al = 160 if 4.4 < t < 4.8 else 15
    im = "grin" if 3.0 < t < 4.2 else ("laugh" if t > 5.6 else "smile")
    lm = "smile" if t < 5.4 else "sad"
    place(img, character("L", lm, arm_l=15, arm_r=al), LX-40, GY, ground_y=GY)
    place(img, character("I", im, arm_l=ai if t < 3.0 else (165 if t < 4.2 else 15), arm_r=15 if t < 3.0 else (165 if t < 4.2 else 15)), IX+40, GY - (abs(math.sin(t*8))*18 if 3.0 < t < 4.2 else 0), ground_y=GY)
    trash_can(img, front=True)
    if 0 <= ui < 1:
        x, y = arc((IX-10, GY-330), (CAN_X, CAN_TOP-5), ui, 220)
        if ui < 0.97: paper_ball(img, x, y, rot=ui*900)
    if 0 <= ul < 1:
        x, y = arc((LX+10, GY-330), (CAN_X-48, CAN_TOP-8), ul, 200); paper_ball(img, x, y, rot=ul*900)
    elif ul >= 1:
        v = t - 5.4
        if v < 0.7:
            x = CAN_X-48 - v*220; y = CAN_TOP-8 - (300*v - 0.5*1400*v*v)
            paper_ball(img, x, min(y, GY-13), rot=v*900)
        else:
            paper_ball(img, CAN_X-48-0.7*220 - min((v-0.7)*60, 30), GY-13, rot=600)
    img = grade(camera(img, t, 2, zoom=1.05 + (0.1*ease((t-2.6)/0.4) - 0.1*ease((t-3.2)/0.4))))
    rec_badge(img, t)
    if 1.8 < t < 3.0: caption(img, "כדור נייר לפח. איתי זורק...")
    if 3.0 <= t < 4.4:
        k = ease_out_back((t-3.0)/0.4)
        text(img, "סוויש!", W/2, 250, 64*k, fill=(255,225,70), sw=6)
        text(img, "+1 לאיתי", W/2, 330, 54*k, fill=(90,230,130), sw=6)
        caption(img, "בלי לגעת בשפה")
    if 4.4 <= t < 5.4: caption(img, "ליאור חייב לקלוע...")
    if t > 5.5:
        k = ease_out_back((t-5.5)/0.4)
        text(img, "בום! בשפה", W/2, 250, 56*k, fill=(255,90,90), sw=6)
        caption(img, "1:1. הכול פתוח!")
    scoreboard(img, 1, 1 if t > 3.0 else 0, pop_i=clamp(1-(t-3.0)/0.3) if t > 3.0 else 0)
    title_card(img, f, "אתגר #2", "קליעה לפח", color=(255,170,90))
    flash(img, f)
    return img

def sc_stare(f):
    t = f/FPS
    img = bgc("kit", kitchen)
    cd = t - 1.8; go = cd > 3.0; after = cd - 3.0
    funny = go and after > 1.2
    laugh = go and after > 2.0
    # Lior
    if funny and not laugh:
        L = character("L", "shock", arm_l=150 + 20*math.sin(t*25), arm_r=150 - 20*math.sin(t*25), look=1)
        L = tongue(L, wiggle=math.sin(t*30)*3)
    elif laugh:
        L = character("L", "grin", arm_l=160, arm_r=160)
    else:
        L = character("L", "smile", arm_l=15, arm_r=15, look=1, blink=False)
    place(img, L, 470, GY - (abs(math.sin(t*8))*18 if after > 2.6 else 0), ground_y=GY, rot=(math.sin(t*20)*4 if funny and not laugh else 0))
    # Itay
    if laugh:
        I = character("I", "laugh", arm_l=40 + 15*math.sin(t*20), arm_r=40 - 15*math.sin(t*20))
        rotI = math.sin(t*14)*5
    else:
        I = character("I", "smile", arm_l=15, arm_r=15, look=-1, blink=go and after > 1.6 and f % 6 < 2)
        rotI = 0
    place(img, I, 810, GY, ground_y=GY, rot=rotI)
    # camera: wide -> Lior close -> Itay close -> wide
    head_y = GY - 0.84*(500-72)
    fx, fy, z = W/2, H/2, 1.05
    if go:
        if 1.1 < after < 2.0:
            k = ease((after-1.1)/0.25); fx, fy, z = lerp(W/2, 470, k), lerp(H/2, head_y+20, k), 1.05 + 1.3*k
        elif 2.0 <= after < 2.9:
            k = ease((after-2.0)/0.2); fx, fy, z = lerp(470, 810, k), head_y+20, 2.35
        elif after >= 2.9:
            k = ease((after-2.9)/0.3); fx, fy, z = lerp(810, W/2, k), lerp(head_y+20, H/2, k), lerp(2.35, 1.05, k)
    img = grade(cam_focus(img, t, 3, fx, fy, z, amp=0.5 if z > 1.5 else 1.0))
    rec_badge(img, t)
    if 0 <= cd < 3.0:
        n = 3 - int(cd); k = ease_out_back((cd % 1)/0.35)
        text(img, str(n), W/2, 230, 150*k, fill=(255,90,90), sw=9, rtl=False)
        caption(img, "מי צוחק ראשון מפסיד")
    elif go and after < 1.1:
        text(img, "מתחילים!", W/2, 230, 90*ease_out_back(after/0.3), fill=(255,90,90), sw=8)
        caption(img, "...שקט מוחלט...")
    elif funny and not laugh:
        caption(img, "ליאור שולף את הפרצוף הסודי", y=640)
    elif laugh and after < 2.9:
        caption(img, "!איתי נשבר", y=640)
    if after > 3.2:
        k = ease_out_back((after-3.2)/0.4)
        text(img, "+1 לליאור", W/2, 175, 64*k, fill=(90,230,130), sw=6)
        caption(img, "ליאור מוביל 2:1!")
    scoreboard(img, 2 if after > 3.2 else 1, 1, pop_l=clamp(1-(after-3.2)/0.3) if after > 3.2 else 0)
    title_card(img, f, "אתגר #3", "אסור לצחוק", color=(255,240,110))
    flash(img, f)
    return img

def sc_blooper(f):
    t = f/FPS
    img = bgc("lr", living_room)
    bonk = 2.8
    hx, hy = 420, GY - 0.84*(500-72)
    # Lior victory dance until bonk
    if t < bonk:
        beat = t*4
        a = 100 + 60*math.sin(beat*math.pi)
        place(img, character("L", "grin", arm_l=a, arm_r=200-a, legs=beat/2), hx, GY - abs(math.sin(beat*math.pi/2))*22, ground_y=GY)
    else:
        u = t - bonk
        place(img, character("L", "shock" if u < 0.8 else "sad", arm_l=15, arm_r=15), hx, GY, rot=math.sin(u*18)*6*max(0, 1-u), ground_y=GY)
        stars(img, hx, hy-40, u)
    # Itay sneaky throw
    throw = 2.0
    ai = 160 if 1.8 < t < 2.2 else 15
    place(img, character("I", "laugh" if t > bonk+0.3 else "grin", arm_l=ai, arm_r=15 if t < bonk+0.3 else 50 + 20*math.sin(t*20), look=-1), 1050, GY, ground_y=GY)
    ub = (t - throw)/(bonk - throw)
    if 0 <= ub < 1:
        x, y = arc((1000, GY-330), (hx+20, hy-10), ub, 120); paper_ball(img, x, y, rot=ub*900)
    elif t >= bonk:
        v = t - bonk
        if v < 0.8:
            x = hx+20 + v*120; y = hy - 10 - (250*v - 0.5*1300*v*v)
            paper_ball(img, x, min(y, GY-13), rot=v*900)
        else: paper_ball(img, hx+116, GY-13, rot=700)
    shake = 3.0 if bonk < t < bonk+0.3 else 1.4
    img = grade(camera(img, t, 4, zoom=1.04, amp=shake))
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    arr = (arr*0.9 + np.array([12, 6, -4])).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 4): d.line([(0, y*S), (W*S, y*S)], fill=(0,0,0,22), width=S)
    rec_badge(img, t)
    text(img, "מאחורי הקלעים", W/2, 60, 42, fill=(255,225,70), sw=5)
    if t > bonk:
        text(img, "בוינג!", hx, hy-130, 70*ease_out_back((t-bonk)/0.3), fill=(255,90,90), sw=7)
        caption(img, "איתי: \"זה היה בטעות!\"", y=125)
    else: caption(img, "ריקוד הניצחון של ליאור", y=125)
    return img

def sc_outro(f):
    t = f/FPS
    img = bgc("lr", living_room)
    wv = 150 + 25*math.sin(t*9)
    place(img, character("L", "grin", arm_l=wv, arm_r=wv), 220, GY - abs(math.sin(t*6))*20, ground_y=GY)
    place(img, character("I", "sad" if t < 2.4 else "grin", arm_l=15 if t < 2.4 else wv, arm_r=15 if t < 2.4 else wv), 1060, GY - (abs(math.sin(t*6+1))*16 if t > 2.4 else 0), ground_y=GY)
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
    text(img, "ליאור  2", W/2, 180, 60*k, fill=(255,170,90), sw=0)
    text(img, "איתי  1", W/2, 255, 60*k, fill=(120,190,255), sw=0)
    if 0.9 < t < 2.4: caption(img, "הנקמה הושלמה!", y=360, color=(255,225,70))
    elif t >= 2.4: caption(img, "פרק 3: איתי רוצה נקמה...", y=360, color=(150,200,255))
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

SCENES = [("intro", sc_intro, 5.0), ("bottle", sc_bottle, 8.5), ("basket", sc_basket, 8.5),
          ("stare", sc_stare, 8.5), ("blooper", sc_blooper, 6.5), ("outro", sc_outro, 5.5)]

if __name__ == "__main__":
    os.makedirs("ep2", exist_ok=True)
    if len(sys.argv) < 2 or sys.argv[1] not in ("preview", "render"):
        sys.exit(f"usage: python3 {sys.argv[0]} preview|render [scene ...]")
    if sys.argv[1] == "preview":
        pts = {"intro": [3.0], "bottle": [2.7, 6.3, 7.5], "basket": [2.6, 3.6, 6.2], "stare": [4.0, 6.6, 7.3, 8.3],
               "blooper": [2.4, 3.3], "outro": [4.0]}
        for name, fn, dur in SCENES:
            for tt in pts[name]:
                render_frame(fn, int(tt*FPS)).save(f"ep2/prev_{name}_{tt:.1f}.png")
    else:
        from multiprocessing import Pool
        with Pool(2) as pool:
            pool.starmap(render_scene, SCENES)
