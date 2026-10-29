"""Render a narrated product film from real app captures using Pillow + FFmpeg."""
from pathlib import Path
import json
import subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'work'
W, H, FPS = 1920, 1080, 24
scenes = json.loads((ROOT / 'timeline.json').read_text())
BG, FG, MUTED, ACCENT = '#091e1a', '#f2f3e9', '#a6b8ac', '#c9eea0'
for weight in [400, 600, 700]:
    dest = WORK / f'commissioner-{weight}.ttf'
    if not dest.exists():
        font = TTFont(ROOT.parent.parent / 'fonts/commissioner.woff2')
        font.flavor = None
        instantiateVariableFont(font, {'wght':weight}, inplace=True).save(dest)
@lru_cache(maxsize=64)
def font(size, weight=400):
    face='LiberationSans-Bold.ttf' if weight>=600 else 'LiberationSans-Regular.ttf'
    return ImageFont.truetype('/usr/share/fonts/truetype/liberation/'+face,size)
@lru_cache(maxsize=8)
def window_font(size, weight=400):
    return ImageFont.truetype(str(WORK / f'commissioner-{weight}.ttf'), size)
def ease(t):
    t = max(0, min(1, t))
    return t*t*(3-2*t)
def wrap(draw, text, f, maxwidth):
    out, line = [], ''
    for word in text.split():
        test = f'{line} {word}'.strip()
        if draw.textlength(test, font=f) > maxwidth and line:
            out.append(line); line = word
        else: line = test
    if line: out.append(line)
    return out

# A fixed textured field keeps the film clean while the UI and focus guides move.
yy, xx = np.mgrid[:H, :W]
glow = np.exp(-(((xx-1550)/1000)**2 + ((yy-300)/850)**2))
base = np.zeros((H,W,3), dtype=np.uint8)
for c, v in enumerate([9,30,26]): base[:,:,c] = v + (glow * [5,13,7][c]).astype(np.uint8)
background = Image.fromarray(base)
d = ImageDraw.Draw(background)
for x in range(80,W,80):
    for y in range(120,H-100,80): d.ellipse((x,y,x+1,y+1),fill='#294236')
d.line((80,119,1840,119),fill='#34473b',width=1)
captures = {p.stem:Image.open(p).convert('RGB') for p in (WORK/'capture').glob('*.png')}
@lru_cache(maxsize=16)
def panel_source(name):
    src=captures[name]
    src=src.crop((354,78,src.width,src.height))
    return src.resize((1230,round(src.height*1230/src.width)),Image.Resampling.LANCZOS)
def panel(name, p):
    # Remove the repeated navigation and account header; retain real app content.
    src = panel_source(name)
    width, height = 1230, 710
    return src.crop((0,0,width,height))
def caption_intervals(s):
    weights = [len(c.split()) + 2 for c in s['captions']]
    cursor = s['voice_start']
    out=[]
    for c, weight in zip(s['captions'], weights):
        duration = s['voice_duration'] * weight/sum(weights)
        out.append((cursor,cursor+duration,c))
        cursor += duration
    return out
@lru_cache(maxsize=8)
def layout(scene_id):
    s=next(sc for sc in scenes if sc['id']==scene_id)
    t=1.;p=0.
    img=background.copy(); draw=ImageDraw.Draw(img)
    p=t/s['duration']
    draw.text((80,51),'EFP',font=font(38,700),fill=ACCENT)
    draw.text((168,62),'SUPPLY CHAIN / CONSIGNMENT LEDGER',font=font(18,600),fill=FG)
    draw.text((1600,62),f"PROJECT FILM    {scenes.index(s)+1:02d} / 08",font=font(16,600),fill=MUTED)
    slide=round(18*(1-ease(t/.7)))
    draw.text((80,182+slide),s['eyebrow'],font=font(17,600),fill=ACCENT)
    size=68
    while max(draw.textlength(line,font=font(size,600)) for line in s['title'].split('\n')) > 475: size-=1
    draw.multiline_text((76,255+slide),s['title'],font=font(size,600),fill=FG,spacing=6)
    y=530
    for line in wrap(draw,s['subtitle'],font(27),465):
        draw.text((80,y),line,font=font(27),fill=MUTED);y+=38
    if s['id']=='reconciliation':
        draw.rounded_rectangle((80,690,545,833),radius=18,fill='#18382a',outline='#456449',width=1)
        draw.text((104,705),'15 - 13 = 2',font=font(47,600),fill=ACCENT)
        draw.text((106,773),'DELIVERED    SOLD    TO RESOLVE',font=font(14,600),fill=MUTED)
    else:
        y=max(y+55,690)
        for line in wrap(draw,s['tag'],font(20),445):
            draw.text((80,y),line,font=font(20),fill=ACCENT);y+=31
    # Native page changes explain the narration: sales → reports, roles → audit.
    first = {'intro':'dashboard','outro':'dashboard','audit':'users'}.get(s['id'],s['id'])
    second = {'summary':'reports','audit':'audit','reconciliation':'resolve'}.get(s['id'])
    view=panel(first,p)
    if second:
        q=ease((p-({'audit':.31,'summary':.60,'reconciliation':.65}[s['id']]))/.065)
        if q>0: view=Image.blend(view,panel(second,p),q)
    px, py = 610, 184+round(15*(1-ease(t/.8)))
    shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow)
    sd.rounded_rectangle((px-5,py-30,px+1238,py+730),radius=18,fill=(0,0,0,110))
    shadow=shadow.filter(ImageFilter.GaussianBlur(15))
    img=Image.alpha_composite(img.convert('RGBA'),shadow).convert('RGB');draw=ImageDraw.Draw(img)
    draw.rounded_rectangle((px-1,py-37,px+1231,py+713),radius=13,fill='#dce4da',outline='#718172',width=1)
    draw.rounded_rectangle((px,py-36,px+1230,py+13),radius=12,fill='#203c32')
    for i,c in enumerate(['#8ca877','#69866c','#496950']):draw.ellipse((px+18+i*20,py-24,px+26+i*20,py-16),fill=c)
    draw.text((px+100,py-28),'EFP Supply Chain',font=window_font(16,600),fill=FG)
    draw.text((px+1055,py-27),'SAMPLE DATA',font=window_font(13,600),fill=ACCENT)
    img.paste(view,(px,py))
    draw=ImageDraw.Draw(img)
    # A small animated focus rail beneath the real interface ties each chapter together.
    draw.line((px,py+724,px+1230,py+724),fill='#3b5745',width=2)
    draw.line((px,py+724,px+round(1230*p),py+724),fill=ACCENT,width=3)
    draw.text((80,1030),'JOHN KENNETH CAÑETE',font=font(14,600),fill=MUTED)
    draw.text((1560,1030),'BUILT FOR FRESH PRODUCE',font=font(14,600),fill=MUTED)
    # Eight chapter markers remain visible throughout the film.
    for i,sc in enumerate(scenes):
        x=715+i*64
        draw.rounded_rectangle((x,1037,x+46,1040),radius=1,fill=ACCENT if i<=scenes.index(s) else '#35513e')
    return img

def frame(s,t):
    p=t/s['duration']
    img=layout(s['id']).copy()
    first = {'intro':'dashboard','outro':'dashboard','audit':'users'}.get(s['id'],s['id'])
    second = {'summary':'reports','audit':'audit','reconciliation':'resolve'}.get(s['id'])
    if second:
        q=ease((p-({'audit':.31,'summary':.60,'reconciliation':.65}[s['id']]))/.065)
        if q>0:img.paste(Image.blend(panel(first,0),panel(second,0),q),(610,184))
    draw=ImageDraw.Draw(img)
    draw.line((610,908,610+round(1230*p),908),fill=ACCENT,width=3)
    for begin,end,text in caption_intervals(s):
        if begin<=t<end:
            cf=font(27,600)
            lines=wrap(draw,text,cf,1690)
            top=943 if len(lines)==1 else 925
            draw.rounded_rectangle((64,top-12,1856,top+len(lines)*35+13),radius=12,fill='#061310')
            for j,line in enumerate(lines):draw.text(((W-draw.textlength(line,font=cf))/2,top+j*35),line,font=cf,fill=FG)
    fade=min(ease(t/.4),ease((s['duration']-t)/.35))
    if fade<1:img=Image.blend(background,img,fade)
    return img

if __name__=='__main__':
    import sys
    if '--review' in sys.argv:
        thumbs=[]
        for s in scenes:
            im=frame(s,s['duration']*.4)
            im.save(WORK/f"review-{s['id']}.jpg",quality=90)
            thumbs.append(im.resize((640,360)))
        sheet=Image.new('RGB',(1280,1440))
        for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*640,(i//2)*360))
        sheet.save(ROOT/'EFP-presentation-review.jpg',quality=92)
    else:
        dest=WORK/'picture-final.mp4'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads','4',str(dest)]
        with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
            for s in scenes:
                for i in range(round(s['duration']*FPS)):
                    proc.stdin.write(frame(s,i/FPS).tobytes())
                print('Rendered',s['id'],flush=True)
            proc.stdin.close()
            if proc.wait(): raise RuntimeError('Video encode failed')
