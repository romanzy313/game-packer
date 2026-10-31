#!/bin/sh
set -eu

cd -- "$(dirname -- "$0")"
exec python3 build.py game-data/icytower1.3 icytower13.exe --output icytower.AppImage
