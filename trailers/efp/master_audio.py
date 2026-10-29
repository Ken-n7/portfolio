"""A quiet original tonal bed, centered narration, and two-pass loudness mastering."""
from pathlib import Path
import json
import re
import subprocess
import wave
import numpy as np
from scipy.ndimage import uniform_filter1d

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'work'
def run(args):
    return subprocess.run(['ffmpeg','-hide_banner','-nostats','-y',*args],check=True,capture_output=True,text=True).stderr
run(['-i',str(WORK/'narration-raw.wav'),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(WORK/'voice-48k.wav')])
with wave.open(str(WORK/'voice-48k.wav')) as f:
    sr=f.getframerate(); voice=np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).astype(np.float64)/32768
voice *= .095/max(.001,np.sqrt(np.mean(voice**2)))
n=len(voice); t=np.arange(n)/sr
bed=np.zeros((n,2),dtype=np.float64)
chords=[[146.832,220,293.665,369.994],[123.471,185,246.942,293.665],[98,146.832,220,277.183],[110,164.814,220,293.665]]
for start in np.arange(0,len(voice)/sr,8):
    a=round(start*sr); b=min(n,a+12*sr); local=np.arange(b-a)/sr
    env=np.minimum(1,local/2.5)*np.minimum(1,(12-local)/3.5)
    for j,hz in enumerate(chords[int(start//8)%4]):
        for channel in range(2):
            phase=channel*.31+j*.7
            tone=np.sin(2*np.pi*hz*local+phase)+.12*np.sin(2*np.pi*2*hz*local+phase)
            bed[a:b,channel] += tone*env*.0012
# Duck the music in response to narration; slow fades prevent pumping.
activity=np.sqrt(np.maximum(0,uniform_filter1d(voice**2,size=int(sr*.18))))
duck=1-.65*np.clip(uniform_filter1d(activity,size=int(sr*.35))/.045,0,1)
bed *= duck[:,None]
edge=np.minimum(1,t/2)*np.minimum(1,(len(t)/sr-t)/3)
bed *= edge[:,None]
mix=voice[:,None]+bed
assert np.isfinite(mix).all(), 'Audio must contain only finite samples'
pcm=np.clip(mix,-.999,.999)
with wave.open(str(WORK/'mix-premaster.wav'),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((pcm*32767).astype(np.int16).tobytes())
chain='highpass=f=65,loudnorm=I=-16:TP=-1.5:LRA=7'
log=run(['-i',str(WORK/'mix-premaster.wav'),'-af',chain+':print_format=json','-f','null','-'])
stats=json.loads(re.search(r'\{[\s\S]*?\}',log).group(0))
params=f":measured_I={stats['input_i']}:measured_LRA={stats['input_lra']}:measured_TP={stats['input_tp']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true"
log2=run(['-i',str(WORK/'mix-premaster.wav'),'-af',chain+params+':print_format=json','-ar','48000','-c:a','pcm_s24le',str(WORK/'audio-master.wav')])
result={'first_pass':stats,'second_pass':json.loads(re.search(r'\{[\s\S]*?\}',log2).group(0)),'bed':'Original additive-synthesis chords; no third-party music or cloned voice.','voice':'Kokoro v1.0 af_heart, speed 0.97, full precision model'}
(ROOT/'audio-report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['second_pass'],indent=2))
