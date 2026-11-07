"""Use TagTune's existing stock narrator; no cloned voice or visual generation."""
import hashlib
import json
from pathlib import Path
import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
MODEL = ROOT.parent / "efp" / "work"
VOICE, SPEED, FPS = "af_heart", .97, 30
options = ort.SessionOptions()
options.intra_op_num_threads = 3
session = ort.InferenceSession(str(MODEL / "kokoro-v1.0.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
engine = Kokoro.from_session(session, str(MODEL / "voices-v1.0.bin"))
scenes = json.loads((ROOT / "scenes.json").read_text())
pieces, offset = [], 0.
for scene in scenes:
    key = hashlib.sha256((VOICE + str(SPEED) + scene["narration"]).encode()).hexdigest()[:12]
    path = WORK / (scene["id"] + "-" + key + "-voice.wav")
    if path.exists():
        samples, sr = sf.read(path)
    else:
        samples, sr = engine.create(scene["narration"], voice=VOICE, speed=SPEED, lang="en-us")
        active = np.flatnonzero(np.abs(samples) > .0015)
        samples = samples[max(0, active[0] - int(.09 * sr)):min(len(samples), active[-1] + int(.18 * sr))]
        edge = int(.008 * sr)
        samples[:edge] *= np.linspace(0, 1, edge)
        samples[-edge:] *= np.linspace(1, 0, edge)
        sf.write(path, samples, sr, subtype="PCM_24")
    assert sr == 24000
    lead, tail = {"intro": (1., 1.), "outro": (.6, 2.)}.get(scene["id"], (.5, .85))
    duration = np.ceil(max(scene["min_duration"], lead + len(samples) / sr + tail) * FPS) / FPS
    clip = np.zeros(round(duration * sr), dtype=np.float32)
    begin = round(lead * sr)
    clip[begin:begin + len(samples)] = samples
    pieces.append(clip)
    scene.update(start=round(offset, 4), duration=float(duration), voice_start=lead, voice_duration=round(len(samples) / sr, 4), voice=VOICE)
    offset += duration
    print(scene["id"], round(len(samples)/sr,2), "speech;",duration,"scene",flush=True)
sf.write(WORK / "narration-raw.wav", np.concatenate(pieces), 24000, subtype="PCM_24")
(ROOT / "timeline.json").write_text(json.dumps(scenes, indent=2) + "\n")
print("Duration:",round(offset,2),flush=True)
