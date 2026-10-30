#!/bin/sh
set -eu

cd -- "$(dirname -- "$0")"
exec python3 build.py game-data/cs16 cs.exe --pre-launch configs/cs16.py --output cs16.AppImage
