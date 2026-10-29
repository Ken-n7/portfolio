"""Mux the completed picture and mastered audio into browser-compatible MP4."""
from pathlib import Path
import json
import subprocess
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from render import scenes, frame, caption_intervals
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'work'
PREVIEWS=ROOT.parent.parent/'previews'
def stamp(t,separator='.'):
    ms=round(t*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}{separator}{ms%1000:03d}'
vtt=['WEBVTT',''];srt=[];i=1
for s in scenes:
    for begin,end,text in caption_intervals(s):
        a,b=begin+s['start'],end+s['start']
        vtt.extend([f'{stamp(a)} --> {stamp(b)}',text,''])
        srt.extend([str(i),f'{stamp(a,",")} --> {stamp(b,",")}',text,'']);i+=1
(PREVIEWS/'efp-presentation.vtt').write_text('\n'.join(vtt),encoding='utf-8')
(WORK/'captions.srt').write_text('\n'.join(srt),encoding='utf-8')
dest=ROOT/'EFP-presentation-1080p.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(WORK/'picture-final.mp4'),'-i',str(WORK/'audio-master.wav'),'-i',str(WORK/'captions.srt'),'-map','0:v:0','-map','1:a:0','-map','2:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata','title=EFP Supply Chain | Consignment Ledger','-metadata','comment=Real application capture with sample data. Synthetic narration: Kokoro af_heart. Original tonal score.','-movflags','+faststart',str(dest)],check=True)
shutil.copyfile(dest,PREVIEWS/'efp-presentation.mp4')
# A designed poster with no mid-sentence subtitle.
poster=frame(scenes[0],scenes[0]['duration']-.5)
poster.save(PREVIEWS/'efp-presentation-poster.jpg',quality=93)
print('Exported:',dest)
