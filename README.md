# Game packer

Package a Windows game as an AppImage using Proton.

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
