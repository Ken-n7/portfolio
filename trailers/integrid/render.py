"""Compose the portrait gameplay into a 1920×1080 landscape trailer with FFmpeg."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parent;W=ROOT/'work';R=W/'render';G=W/'game';FF='ffmpeg';FPS=30
capture=json.loads((W/'capture-manifest.json').read_text());shots={s['name']:s for s in capture['shots']}
SCENES=[
 {'id':0,'shot':'relax-solve','trim':0,'duration':6.4,'x':1130,'side':1,'title':'Find the missing number'},
 {'id':1,'shot':'clue','trim':0,'duration':6.4,'x':150,'side':-1,'title':'Learn the signs. Solve the grid.'},
 {'id':2,'shot':'finish','trim':3.9,'duration':4.8,'x':1130,'side':1,'title':'Clear the grid. Celebrate the win.'},
 {'id':3,'shot':'expert','trim':0,'duration':8,'x':150,'side':-1,'title':'A bigger grid. A new challenge.'},
 {'id':4,'shot':'battle','trim':0,'duration':9.6,'x':400,'side':-1,'title':'Team up. Race the grid.'},
 {'id':5,'shot':'modes','trim':0,'duration':4.8,'x':150,'side':-1,'title':'Choose your adventure.'},
 {'id':6,'shot':'landing','trim':0,'duration':6.4,'x':1130,'side':1,'title':'INTEGRID In Action'},
]
fade=.2;at=0
for i,s in enumerate(SCENES):s['offset']=at;at+=s['duration']-(fade if i<len(SCENES)-1 else 0)
TOTAL=round(at,5);FRAMES=round(TOTAL*FPS)
def run(args,**kw):return subprocess.run([FF,'-hide_banner','-loglevel','error','-y']+list(map(str,args)),check=True,**kw)
def png(file,d):return ['-threads','1','-loop','1','-framerate',FPS,'-t',d,'-i',R/file]
def source(name,trim=0):
 # Leave a short handle before the next click: recorder startup is asynchronous.
 s=shots[name];return ['-threads','2','-ss',s['start']+trim,'-t',max(.04,s['duration']-trim-.75),'-i',s['file']]
def scene(s):
 i=s['id'];d=s['duration'];args=png(f'bg{i}.png',d)+png(f'title{i}.png',d)+png('phone.png',d)+png('mask.png',d)+source(s['shot'],s['trim']);f=[]
 f += [f'[0:v]format=rgba,scale=2000:1125,crop=1920:1080:x=40+12*sin(t*.4):y=22+8*cos(t*.4),trim=duration={d},setpts=PTS-STARTPTS[bg]']
 f += [f'[1:v]format=rgba,trim=duration={d},setpts=PTS-STARTPTS,fade=t=in:st=0.12:d=0.32:alpha=1,fade=t=out:st={d-.18}:d=0.18:alpha=1[title]']
 f += ['[2:v]format=rgba,split=2[frame1][frame2]','[3:v]format=gray,split=2[mask1][mask2]']
 def phone(v,which,scale=1):
  # Playwright records CSS pixels, padding a larger requested canvas at bottom/right.
  return [f'[{v}:v]fps={FPS},crop=430:900:0:0,setsar=1,format=rgba,tpad=stop_mode=clone:stop_duration=4,trim=duration={d},setpts=PTS-STARTPTS[screen{which}]',f'[screen{which}][mask{which}]alphamerge[cut{which}]',f'[frame{which}][cut{which}]overlay=x=85:y=80:shortest=1[rawphone{which}]',f'[rawphone{which}]scale={round(600*scale)}:{round(1080*scale)},rotate=a=0.012*sin(t*.9+{which}):ow=iw:oh=ih:c=none[phone{which}]']
 f+=phone(4,1,.70 if i==4 else 1)
 if i==4:
  args+=source('battle-2',s['trim']);f+=phone(5,2,.70)
  f += ["[bg][phone1]overlay=x='400-90*pow(max(0,1-t/.8),3)':y='310+4*sin(t*.9)'[v1]", "[v1][phone2]overlay=x='1040+90*pow(max(0,1-t/.8),3)':y='310+4*sin(t*.9+2)'[v2]"]
 else:
  f += ['[frame2]nullsink','[mask2]nullsink',f"[bg][phone1]overlay=x='{s['x']}+{s['side']*105}*pow(max(0,1-t/.9),3)':y='4*sin(t*.9)'[v2]"]
 f += ["[v2][title]overlay=x=0:y='22*pow(max(0,1-t/.65),3)':shortest=1[vtitle]"]
 if i==0:
  args+=png('answer0.png',d);f += [f'[5:v]format=rgba,trim=duration={d},fade=t=in:st=1.35:d=0.16:alpha=1,fade=t=out:st={d-.18}:d=0.18:alpha=1[answer]',"[vtitle][answer]overlay=x=0:y=0:shortest=1[vfinal]"]
 else:f+=['[vtitle]null[vfinal]']
 filt=R/f'scene-{i}.filter';filt.write_text(';\n'.join(f))
 output=R/f'scene-{i}.mp4';run(args+['-filter_complex_threads','2','-filter_complex_script',filt,'-map','[vfinal]','-an','-t',d,'-frames:v',round(d*FPS),'-progress',R/f'progress-{i}.txt','-r',FPS,'-c:v','libx264','-threads','3','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',output]);print('Rendered scene',i,s['title'],flush=True)
 return output
if '--first' in sys.argv:
 scene(SCENES[0]);run(['-ss','2.4','-i',R/'scene-0.mp4','-frames:v','1',R/'first-scene.jpg']);sys.exit(0)
with ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(scene,[s for s in SCENES if not (R/f"scene-{s['id']}.mp4").exists()]))
# A short crossfade joins each composition; portrait gameplay keeps its original speed.
args=[]
for s in SCENES:args+=['-threads','1','-i',R/f"scene-{s['id']}.mp4"]
f=[]
for i in range(len(SCENES)):f.append(f'[{i}:v]setpts=PTS-STARTPTS,fps={FPS},settb=AVTB[v{i}]')
last='v0';offset=SCENES[0]['duration']-fade
for i in range(1,len(SCENES)):
 out=f'x{i}';f.append(f'[{last}][v{i}]xfade=transition=fade:duration={fade}:offset={offset},fps={FPS},settb=AVTB[{out}]');last=out;offset+=SCENES[i]['duration']-fade
f.append(f'[{last}]fade=t=in:st=0:d=0.18,fade=t=out:st={TOTAL-.5}:d=0.5,format=yuv420p[final]')
(R/'edit.filter').write_text(';\n'.join(f));run(args+['-filter_complex_threads','2','-filter_complex_script',R/'edit.filter','-map','[final]','-an','-frames:v',FRAMES,'-c:v','libx264','-threads','4','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',R/'picture.mp4'])
plan={'fps':FPS,'frames':FRAMES,'duration':TOTAL,'transition_seconds':fade,'scenes':SCENES};(W/'edit-plan.json').write_text(json.dumps(plan,indent=2));print('Picture edit complete:',TOTAL,'seconds',flush=True)
