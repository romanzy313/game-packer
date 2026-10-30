# Game packer

Package a Windows game as an AppImage using Proton. Images are written to `./out/`.

Download the
[SuperTuxKart Windows ZIP](https://github.com/supertuxkart/stk-code/releases/download/1.5/SuperTuxKart-1.5-win.zip)
and extract it to `game-data/SuperTuxKart`, then build:

```sh
python3 build.py game-data/SuperTuxKart \
  stk-code/build-x86_64/bin/supertuxkart.exe \
  --output SuperTuxKart.AppImage
```

```sh
python3 build.py game-data/cs16 cs.exe --output cs16.AppImage
```

Game changes, saves, and settings are kept in `/tmp/<AppImage filename>` by
default. To keep them in another directory across launches:

```sh
GAME_PACKER_DATA_DIR="$HOME/.local/share/game-packer/cs16" ./out/cs16.AppImage
```

Remove that directory to reset the game. Files in `/tmp` may be removed by the
system; caches and temporary files are discarded after each session. The target
requires FUSE and `fusermount3` for the writable overlay.

For concise error output:

```sh
WINEDEBUG=-all,err+all ./out/cs16.AppImage
```
