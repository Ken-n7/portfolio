"""Synthesize each scene's narration as one paragraph (natural prosody, never time-stretched).

Reuses the Kokoro model, voices and venv already downloaded for the EFP presentation:
    ../efp/work/venv/bin/python narrate.py
Writes voice-and-script-keyed WAV caches, work/narration-raw.wav and timeline.json.
"""
import json
import hashlib
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
MODEL = ROOT.parent / "efp" / "work"
FPS = 30
VOICE, SPEED = os.environ.get("VOICE", "bm_fable"), 0.97
LANG = "en-gb" if VOICE[0] == "b" else "en-us"

options = ort.SessionOptions()
options.intra_op_num_threads = 4
session = ort.InferenceSession(str(MODEL / "kokoro-v1.0.onnx"), sess_options=options,
                               providers=["CPUExecutionProvider"])
kokoro = Kokoro.from_session(session, str(MODEL / "voices-v1.0.bin"))
scenes = json.loads((ROOT / "scenes.json").read_text())
rate = 24000
pieces, offset = [], 0.0
for scene in scenes:
    # A script or voice change must never reuse narration from an earlier edit.
    key = hashlib.sha256(f"{VOICE}:{SPEED}:{scene.get('say', scene['narration'])}".encode()).hexdigest()[:12]
    dest = WORK / f"{scene['id']}-{VOICE}-{key}-voice.wav"
    if dest.exists():
        samples, sr = sf.read(dest)
    else:
        samples, sr = kokoro.create(scene.get("say", scene["narration"]), voice=VOICE, speed=SPEED, lang=LANG)
        # trim only the model's padding; breaths and inner pauses stay
        active = np.where(np.abs(samples) > 0.0015)[0]
        samples = samples[max(0, active[0] - int(.09 * sr)):min(len(samples), active[-1] + int(.18 * sr))]
        n = int(.008 * sr)
        samples[:n] *= np.linspace(0, 1, n)
        samples[-n:] *= np.linspace(1, 0, n)
        sf.write(dest, samples, sr, subtype="PCM_24")
    assert sr == rate
    lead, tail = {"intro": (1.1, .6), "outro": (.5, 1.6), "disclaimer": (.6, .9)}.get(scene["id"], (.25, .45))
    lead, tail = scene.get("lead", lead), scene.get("tail", tail)
    speech = len(samples) / sr
    length = np.ceil((lead + speech + tail) * FPS) / FPS
    footage = sum(b - a for a, b in scene.get("cuts", []))
    length = max(length, np.ceil(footage * FPS) / FPS)  # never cut the footage short
    clip = np.zeros(round(length * sr), dtype=np.float32)
    start = round(lead * sr)
    clip[start:start + len(samples)] = samples
    pieces.append(clip)
    scene.update(start=round(offset, 4), duration=round(float(length), 4), voice_start=lead,
                 voice_duration=round(speech, 3), voice=VOICE)
    offset += length
    print(f"{scene['id']:8} {speech:5.2f}s speech  {length:5.2f}s scene", flush=True)
sf.write(WORK / "narration-raw.wav", np.concatenate(pieces), rate, subtype="PCM_24")
(ROOT / "timeline.json").write_text(json.dumps(scenes, indent=2, ensure_ascii=False) + "\n")
print(f"total {offset:.2f}s", flush=True)
