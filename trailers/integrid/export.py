"""Export a high-quality master, web video, poster and review contact sheet."""
from pathlib import Path
import json, subprocess
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
R=ROOT/'work/render'
PREVIEWS=REPO/'previews'
PLAN=json.loads((ROOT/'work/edit-plan.json').read_text())

def ff(*args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

master=ROOT/'INTEGRID-trailer-1080p.mp4'
web=PREVIEWS/'integrid-trailer.mp4'
ff('-i',R/'picture.mp4','-i',R/'mix-final.wav','-map','0:v','-map','1:a',
   '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',PLAN['duration'],
   '-movflags','+faststart','-metadata','title=INTEGRID — In Action',master)
ff('-i',master,'-c:v','libx264','-threads','4','-preset','slow','-crf','22',
   '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',web)
ff('-ss','40.8','-i',web,'-frames:v','1','-q:v','2',PREVIEWS/'integrid-trailer-poster.jpg')

times=[2.5,8.2,15.2,20.5,29.5,40.8]
sheet=Image.new('RGB',(1440,1287),'#fff8e8')
draw=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    frame=R/f'review-{i}.jpg'
    ff('-ss',t,'-i',web,'-frames:v','1','-vf','scale=704:396','-q:v','2',frame)
    x=8+(i%2)*720;y=8+(i//2)*429
    sheet.paste(Image.open(frame),(x,y))
    draw.text((x+8,y+402),f'{t:04.1f}s',fill='#7a3b0c')
sheet.save(ROOT/'INTEGRID-trailer-preview.jpg',quality=92)

audio=json.loads((R/'audio-audit.json').read_text())
production={
    'title':'INTEGRID — In Action',
    'app':'https://integrid-phi.vercel.app/',
    'source_revision':'bfb9d2b2ffafd8d2d0c945cf65f263da217aad7e',
    'video':{'width':1920,'height':1080,'fps':30,'seconds':PLAN['duration'],'frames':PLAN['frames'],'codec':'H.264 / AAC'},
    'scenes':PLAN['scenes'],
    'capture_notes':json.loads((ROOT/'work/capture-manifest.json').read_text())['notes']+[
        'Game viewport 430×900 CSS pixels is cropped from the padded capture canvas.',
        'Original gameplay speed retained. Short tails freeze the last frame instead of showing subsequent navigation.',
        'Native sound cue timings were logged during capture, then mixed with the existing app music.',
    ],
    'tools':['Playwright / Chromium','Native app controls and puzzle engine','HTML/CSS motion plates','Nunito Variable and native game artwork','FFmpeg / ffprobe','NumPy / SciPy','Pillow review contact sheet'],
    'music':audio['music'],
    'sound_effects':[
        {'source':'public/sounds/puzzle-kit.wav','credit':'Original game feedback rendered with FluidSynth and GeneralUser GS 2.0.3 by S. Christian Collins','instrument_license':'https://www.schristiancollins.com/generaluser.php'},
        {'source':'public/sounds/level-win.wav','credit':'Level win by Tuudurt / freesound_community','url':'https://pixabay.com/sound-effects/musical-level-win-6416/','license':'https://pixabay.com/service/license-summary/'},
    ],
    'native_sound_cues':len(audio['events']),
    'audio_target':audio['target'],
    'website_asset':'previews/integrid-trailer.mp4',
    'master_bytes':master.stat().st_size,'web_bytes':web.stat().st_size,
}
(ROOT/'production.json').write_text(json.dumps(production,indent=2)+'\n')
print(f'Exported {PLAN["duration"]}s; master {master.stat().st_size/1e6:.1f} MB, web {web.stat().st_size/1e6:.1f} MB',flush=True)
