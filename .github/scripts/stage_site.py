"""Stage only tracked public assets for the portfolio's S3 deployment."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_FILES = ("index.html", "styles.css", "script.js", "robots.txt", "sitemap.xml")
PUBLIC_DIRS = ("brand", "fonts", "previews")


def stage(destination):
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("The staging directory must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", *PUBLIC_FILES, *PUBLIC_DIRS], cwd=ROOT,
    ).decode().split("\0")
    paths = [path for path in tracked if path]
    missing = set(PUBLIC_FILES) - set(paths)
    if missing:
        raise ValueError(f"Required public files are not tracked: {sorted(missing)}")
    size = 0
    for path in paths:
        source = ROOT / path
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Public assets must be regular files: {path}")
        output = destination / path
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        size += source.stat().st_size
    print(f"Staged {len(paths)} public files ({size / 2**20:.1f} MiB) in {destination}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 .github/scripts/stage_site.py EMPTY_DIRECTORY")
    stage(sys.argv[1])
