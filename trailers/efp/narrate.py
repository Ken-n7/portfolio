"""Synthesize complete paragraphs; keep natural prosody and never time-stretch."""
from pathlib import Path
import json
import re
import numpy as np
import soundfile as sf
import onnxruntime as ort
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'work'
options = ort.SessionOptions()
options.intra_op_num_threads = 4
session = ort.InferenceSession(str(WORK / 'kokoro-v1.0.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
kokoro = Kokoro.from_session(session, str(WORK / 'voices-v1.0.bin'))
scenes = json.loads((ROOT / 'scenes.json').read_text())
rate = 24000
timeline = []
offset = 0
pieces = []
for scene in scenes:
    dest = WORK / (scene['id'] + '-voice.wav')
    if dest.exists():
        samples, sr = sf.read(dest)
    else:
        samples, sr = kokoro.create(scene['narration'], voice='af_heart', speed=0.97, lang='en-us')
        # Trim excess model padding only, retaining breaths and all interior pauses.
        active = np.where(np.abs(samples) > 0.0015)[0]
        samples = samples[max(0, active[0] - int(.09 * sr)):min(len(samples), active[-1] + int(.18 * sr))]
        n = int(.008 * sr)
        samples[:n] *= np.linspace(0, 1, n)
        samples[-n:] *= np.linspace(1, 0, n)
        sf.write(dest, samples, sr, subtype='PCM_24')
    assert sr == rate
    # Speech starts after a comfortable visual lead; every scene ends with a pause.
    lead, tail = (1.1, .95) if scene['id'] == 'intro' else (.55, .8)
    length = int(np.ceil((lead + len(samples) / sr + tail) * 24)) / 24
    clip = np.zeros(round(length * sr), dtype=np.float32)
    start = round(lead * sr)
    clip[start:start + len(samples)] = samples
    pieces.append(clip)
    scene.update(start=offset, duration=length, voice_start=lead, voice_duration=len(samples) / sr)
    timeline.append(scene)
    offset += length
    print(scene['id'], round(len(samples) / sr, 2), 'seconds of speech', flush=True)
sf.write(WORK / 'narration-raw.wav', np.concatenate(pieces), rate, subtype='PCM_24')
(ROOT / 'timeline.json').write_text(json.dumps(timeline, indent=2, ensure_ascii=False) + '\n')
print('Total duration:', offset, flush=True)
