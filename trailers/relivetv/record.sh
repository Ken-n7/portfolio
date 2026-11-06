#!/bin/sh
# Records the demo: the real app in an isolated HOME (empty My List, a copy of the channel cache so the
# catalog loads instantly), as an X11 window so ffmpeg can grab it. Needs a venv with python-xlib.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
APP=${APP:-$HOME/Workspace/tv-channels}
XPY=${XPY:-/tmp/claude-1000/-home-ken-Workspace-portfolio/c18c8276-979b-4704-9eb8-30e26a7c408d/scratchpad/xvenv/bin/python}
# fresh settings each take, with My List seeded: the saved-channel cards shown on Home
rm -rf "$HERE/work/home/.local"
mkdir -p "$HERE/work/home/.local/share/com.ken.tv_channels"
cp "$HERE/my-list.json" "$HERE/work/home/.local/share/com.ken.tv_channels/shared_preferences.json"
cd "$APP"
PUB_CACHE=$HOME/.pub-cache HOME=$HERE/work/home GDK_BACKEND=x11 \
  flutter test integration_test/demo_trailer_test.dart -d linux \
  --dart-define=DEMO_DIR=$HERE/work --dart-define="RESIZER=$XPY $HERE/xresize.py"
