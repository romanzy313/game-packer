# Game packer

Package a Windows game as an AppImage using Proton.

## Examples

### TuxKart

Download the
[SuperTuxKart Windows ZIP](https://github.com/supertuxkart/stk-code/releases/download/1.5/SuperTuxKart-1.5-win.zip)
and extract it to `game-data/SuperTuxKart`, then build:

```sh
python3 build.py game-data/SuperTuxKart \
  stk-code/build-x86_64/bin/supertuxkart.exe \
  --output SuperTuxKart.AppImage
```

### cs 1.6

```sh
python3 build.py game-data/cs16 cs.exe --pre-launch configs/cs16.py --output cs16.AppImage
```

Alternatively, run `./build-cs16.sh`.

## Configuring

The optional `--pre-launch` script runs with Python 3 before the game starts. It
receives the writable game directory and the persistent state directory as its
first and second arguments. A nonzero exit status stops the launch.

Game changes, saves, and settings are kept in
`~/.local/share/fun/<AppImage name>/` by default, without the `.AppImage`
suffix. To use a randomly named temporary directory:

```sh
GAME_PACKER_DATA_DIR="$(mktemp -d)" ./out/cs16.AppImage
```

For concise error output:

```sh
WINEDEBUG=-all,err+all ./out/cs16.AppImage
```
