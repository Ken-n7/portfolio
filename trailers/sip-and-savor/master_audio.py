"""Mix a credited human-composed recording underneath the TagTune narrator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from music_audio import master_audio

if __name__ == "__main__":
    master_audio(ROOT)
