"""Mix licensed recordings beneath existing narration; remux pictures unchanged."""
import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d


def ffmpeg(*args):
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-y", *map(str, args)],
        capture_output=True, check=True,
    )


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ]))


def stats(log):
    return json.loads(re.search(rb"\{[\s\S]*?\}", log).group())


def master_audio(root):
    root = Path(root)
    work = root / "work"
    music = json.loads((root / "music.json").read_text())
    source = work / "music-source.mp3"
    if not source.exists():
        request = urllib.request.Request(music["download_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=90) as response:
            source.write_bytes(response.read())
    assert sha256(source) == music["source_sha256"], "Music download differs from the credited recording"

    # Reuse the original speech samples and pauses, never invoke the synthesizer.
    published = music.get("narration_source") == "published_soundtrack"
    voice_source = work / ("before-online-music.mp4" if published else "narration-raw.wav")
    voice_hash = sha256(voice_source)
    rate = 48000
    if published:
        source_duration = float(next(s for s in probe(voice_source)["streams"] if s["codec_type"] == "video")["duration"])
        speech = np.frombuffer(ffmpeg(
            "-i", voice_source, "-map", "0:a:0", "-ar", rate, "-ac", "2", "-f", "f32le", "-",
        ).stdout, dtype="<f4").reshape(-1, 2).astype(np.float64)[:round(source_duration * rate)]
        voice = speech.mean(axis=1)
    else:
        voice = np.frombuffer(ffmpeg(
            "-i", voice_source, "-ar", rate, "-ac", "1", "-f", "f32le", "-",
        ).stdout, dtype="<f4").astype(np.float64)
        voice *= .095 / max(.001, np.sqrt(np.mean(voice ** 2)))
        speech = voice[:, None]
    duration = len(voice) / rate

    recording = ffmpeg(
        "-ss", music["source_start_seconds"], "-i", source, "-t", duration,
        "-af", f"loudnorm=I={music['music_lufs']}:TP=-8:LRA=11",
        "-ar", rate, "-ac", "2", "-f", "f32le", "-",
    )
    bed = np.frombuffer(recording.stdout, dtype="<f4").reshape(-1, 2).astype(np.float64)
    if len(bed) < len(voice):
        bed = np.pad(bed, ((0, len(voice) - len(bed)), (0, 0)))
    bed = bed[:len(voice)]
    time = np.arange(len(voice)) / rate
    activity = np.sqrt(np.maximum(0, uniform_filter1d(voice ** 2, size=round(rate * .18))))
    duck = 1 - .5 * np.clip(uniform_filter1d(activity, size=round(rate * .4)) / .045, 0, 1)
    edge = np.minimum(1, time / music["fade_in_seconds"])
    edge *= np.minimum(1, (duration - time) / music["fade_out_seconds"])
    bed *= (duck * edge)[:, None]
    bed *= 10 ** (music.get("music_gain_db", 0) / 20)
    mix = speech + bed
    assert np.isfinite(mix).all()
    # Float intermediates preserve headroom before true-peak mastering.
    wavfile.write(work / "music-bed.wav", rate, bed.astype(np.float32))
    wavfile.write(work / "mix-premaster.wav", rate, mix.astype(np.float32))

    chain = "highpass=f=65,loudnorm=I=-16:TP=-1.5:LRA=7"
    first = stats(ffmpeg(
        "-i", work / "mix-premaster.wav", "-af", chain + ":print_format=json", "-f", "null", "-",
    ).stderr)
    measured = (
        f":measured_I={first['input_i']}:measured_LRA={first['input_lra']}"
        f":measured_TP={first['input_tp']}:measured_thresh={first['input_thresh']}"
        f":offset={first['target_offset']}:linear=true:print_format=json"
    )
    second = stats(ffmpeg(
        "-i", work / "mix-premaster.wav", "-af", chain + measured,
        "-ar", rate, "-c:a", "pcm_s24le", work / "audio-master.wav",
    ).stderr)
    assert sha256(voice_source) == voice_hash
    report = {
        "first_pass": first, "second_pass": second,
        "voice": ("Existing published stereo soundtrack retained as the base; local narration WAV belongs to a different edit."
                  if published else "Existing narration recording and timing; no speech regenerated or time-stretched."),
        "narration_source_file": voice_source.name,
        "narration_sha256": voice_hash, "duration_seconds": duration,
        "music": music, "ducking_reduction_max_db": 6.02,
        "music_rms_dbfs_before_master": float(20 * np.log10(np.sqrt(np.mean(bed ** 2)))),
    }
    (root / "audio-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(root.name, music["title"], json.dumps(second), flush=True)


def stream_hash(path, selector):
    return subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", selector,
        "-c", "copy", "-f", "hash", "-hash", "sha256", "-",
    ], text=True).strip()


def export_audio_only(root):
    root = Path(root)
    work = root / "work"
    music = json.loads((root / "music.json").read_text())
    web = root.parent.parent / "previews" / music["video_file"]
    baseline = work / "before-online-music.mp4"
    if not baseline.exists():
        shutil.copy2(web, baseline)
    before = probe(baseline)
    original_video = next(s for s in before["streams"] if s["codec_type"] == "video")
    duration = float(original_video["duration"])
    report = json.loads((root / "audio-report.json").read_text())
    assert abs(report["duration_seconds"] - duration) < .05
    assert sha256(work / report["narration_source_file"]) == report["narration_sha256"]
    temporary = work / "online-music-export.mp4"
    ffmpeg(
        "-i", baseline, "-i", work / "audio-master.wav",
        "-map", "0:v:0", "-map", "1:a:0", "-map", "0:s?", "-map_metadata", "0",
        "-c:v", "copy", "-c:s", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", duration, "-metadata", "comment=" + music["attribution"],
        "-metadata", "copyright=Music: Kevin MacLeod, CC BY 4.0; see comment for full credit.",
        "-movflags", "+faststart", temporary,
    )
    after = probe(temporary)
    video = next(s for s in after["streams"] if s["codec_type"] == "video")
    assert video["nb_frames"] == original_video["nb_frames"]
    assert video["r_frame_rate"] == original_video["r_frame_rate"]
    assert abs(float(video["duration"]) - duration) < .001
    original_hash = stream_hash(baseline, "0:v:0")
    assert stream_hash(temporary, "0:v:0") == original_hash, "Picture stream changed"
    subtitles = any(s["codec_type"] == "subtitle" for s in before["streams"])
    if subtitles:
        assert stream_hash(temporary, "0:s:0") == stream_hash(baseline, "0:s:0")
    verification = {
        "picture_stream_identical": True, "picture_stream_sha256": original_hash,
        "narration_sha256": report["narration_sha256"], "duration_seconds": duration,
        "frame_rate": video["r_frame_rate"], "frames": int(video["nb_frames"]),
        "embedded_subtitles_preserved": subtitles, "music_title": music["title"],
    }
    shutil.copy2(temporary, web)
    masters = {"tagtune": "TagTune-demo-1080p.mp4", "efp": "EFP-presentation-1080p.mp4",
               "relivetv": "reLiveTV-demo-1080p.mp4"}
    shutil.copy2(temporary, root / masters[root.name])
    (work / "music-verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(root.name, "audio updated; video stream identical:", original_hash, flush=True)
