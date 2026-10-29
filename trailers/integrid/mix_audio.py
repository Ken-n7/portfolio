"""Mix the app's authored music and original sample-bank cues to the edit timeline."""
from pathlib import Path
from scipy.io import wavfile
from scipy.signal import resample_poly
import ast,json,subprocess,numpy as np
ROOT=Path(__file__).resolve().parent;W=ROOT/'work';G=W/'game';R=W/'render';RATE=48000
module=ast.parse((ROOT/'render.py').read_text());scenes=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCENES' for t in n.targets)));at=0
for i,s in enumerate(scenes):s['offset']=at;at+=s['duration']-(.2 if i<len(scenes)-1 else 0)
total=round(at,5);count=round(total*RATE);manifest=json.loads((W/'capture-manifest.json').read_text());shots={s['name']:s for s in manifest['shots']};gen=json.loads((G/'public/sounds/generation.json').read_text());audit=[]
def decode(p):
 data=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-i',str(p),'-f','f32le','-ac','2','-ar',str(RATE),'pipe:1']);return np.frombuffer(data,dtype='<f4').reshape(-1,2).copy()
music=decode(G/'public/music/puzzle-game-3.mp3')[:count];music*=.72
fadein=np.minimum(1,np.arange(count)/(RATE*.5));fadeout=np.minimum(1,(count-1-np.arange(count))/(RATE*1.05));envelope=(fadein*fadeout).astype(np.float32)
rate,bank=wavfile.read(G/'public/sounds/puzzle-kit.wav');bank=bank.astype(np.float32)/32768
if bank.ndim==1:bank=np.repeat(bank[:,None],2,axis=1)
if rate!=RATE:bank=resample_poly(bank,RATE,rate).astype(np.float32)
win=decode(G/'public/sounds/level-win.wav');mix=np.zeros((count,2),np.float32)
def sound(name,t,gain):
 if t<0 or t>=total:return
 if name=='win':data=win;source='public/sounds/level-win.wav'
 elif name=='lose':data=decode(G/'public/sounds/game-over.wav');source='public/sounds/game-over.wav'
 elif name in gen['cues']:
  cue=gen['cues'][name];a=round(cue['offset']*RATE);b=round((cue['offset']+cue['duration'])*RATE);data=bank[a:b];source='public/sounds/puzzle-kit.wav#'+name
 else:return
 start=round(t*RATE);end=min(count,start+len(data));mix[start:end]+=data[:end-start]*gain;audit.append({'name':name,'time':round(t,4),'gain':gain,'source':source})
 if name=='win':
  a=max(0,start-round(.08*RATE));b=min(count,end+round(.35*RATE));duck=np.ones(b-a,np.float32)*.5;fade=min(round(.15*RATE),len(duck)//2);duck[:fade]=np.linspace(1,.5,fade);duck[-fade:]=np.linspace(.5,1,fade);envelope[a:b]*=duck
for scene in scenes:
 for e in shots[scene['shot']].get('audio',[]):
  t=e['time']-scene['trim']
  if 0<=t<min(scene['duration'],shots[scene['shot']]['duration']-scene['trim']-.75):
   name=e['name'];gain={'select':.65,'right':.78,'clue':.72,'hint':.72,'tap':.48,'win':1.0}.get(name,.6);sound(name,scene['offset']+t,gain)
 if scene['id']==4:
  for e in shots['battle-2'].get('audio',[]):
   t=e['time']-scene['trim']
   if 0<=t<min(scene['duration'],shots['battle-2']['duration']-scene['trim']-.75):sound(e['name'],scene['offset']+t,.35)
sound('start',.22,.55);sound('start',scenes[4]['offset']+.22,.42)
mix+=music*envelope[:,None]
raw=R/'mix-raw.wav';wavfile.write(raw,RATE,mix)
probe=subprocess.run(['ffmpeg','-hide_banner','-i',str(raw),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);measured=json.loads(probe.stderr[probe.stderr.rfind('{'):probe.stderr.rfind('}')+1]);f=f"loudnorm=I=-16:TP=-2:LRA=9:measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-af',f,'-ar',str(RATE),'-c:a','pcm_s24le',str(R/'mix-final.wav')],check=True)
(R/'audio-audit.json').write_text(json.dumps({'music':{'title':'Puzzle Game 3 (Looping)','artist':'Eric Matyas','source':'https://soundimage.org/puzzle-music/','license':'https://soundimage.org/sample-page/','attribution':'Music by Eric Matyas / www.soundimage.org','edits':'Excerpted, faded, and briefly ducked for the native level-completion sound.'},'target':{'lufs':-16,'true_peak':-2},'duration':total,'events':audit,'pre_normalization':measured},indent=2));print('Audio mixed:',round(total,2),'seconds;',len(audit),'native game cues. Raw peak',round(20*np.log10(np.max(np.abs(mix))),2),'dBFS')
