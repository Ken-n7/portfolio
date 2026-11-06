"""Mix the licensed recording in music.json beneath the existing narration."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from music_audio import master_audio

if __name__ == "__main__":
    master_audio(ROOT)
