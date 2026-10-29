#!/usr/bin/env python3
"""Build an AppImage from a local Windows game and cached runtime assets."""
import argparse
import io
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
DOWNLOADS = ROOT / 'downloads'
ASSETS = {
    'GE-Proton9-27.tar.gz': (
        'https://github.com/GloriousEggroll/proton-ge-custom/releases/download/'
        'GE-Proton9-27/GE-Proton9-27.tar.gz'
    ),
    'umu-launcher-1.2.5-zipapp.tar': (
        'https://github.com/Open-Wine-Components/umu-launcher/releases/download/'
        '1.2.5/umu-launcher-1.2.5-zipapp.tar'
    ),
    'SteamLinuxRuntime_sniper-3.0.20261021.266025.tar.xz': (
        'https://repo.steampowered.com/steamrt-images-sniper/snapshots/'
        '3.0.20261021.266025/SteamLinuxRuntime_sniper.tar.xz'
    ),
    'runtime-x86_64': (
        'https://github.com/AppImage/type2-runtime/releases/download/'
        'continuous/runtime-x86_64'
    ),
    'bubblewrap_0.6.1-1ubuntu0.3_amd64.deb': (
        'https://archive.ubuntu.com/ubuntu/pool/main/b/bubblewrap/'
        'bubblewrap_0.6.1-1ubuntu0.3_amd64.deb'
    ),
}


def download(item):
    name, url = item
    dest = DOWNLOADS / name
    if dest.is_file():
        print(f'Using cached {name}', flush=True)
        return
    print(f'Downloading {name}', flush=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=DOWNLOADS, prefix=f'.{name}.',
                                         suffix='.part', delete=False) as out:
            temporary = Path(out.name)
            with urllib.request.urlopen(url, timeout=120) as response:
                shutil.copyfileobj(response, out)
        temporary.replace(dest)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def extract(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as src:
        # The archives are downloaded from the upstream projects.
        src.extractall(destination, filter='data')


def extract_bwrap(deb, destination):
    # Debian packages are ar archives; the executable is in data.tar.*.
    with deb.open('rb') as src:
        if src.read(8) != b'!<arch>\n':
            raise ValueError('Invalid bubblewrap package')
        while header := src.read(60):
            if len(header) != 60 or header[58:] != b'`\n':
                raise ValueError('Invalid bubblewrap package member')
            name = header[:16].decode('ascii').strip().rstrip('/')
            size = int(header[48:58].decode('ascii').strip())
            if name.startswith('data.tar'):
                data = src.read(size)
                with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                    member = archive.getmember('./usr/bin/bwrap')
                    with archive.extractfile(member) as executable:
                        with destination.open('wb') as out:
                            shutil.copyfileobj(executable, out)
                destination.chmod(0o755)
                return
            src.seek(size + size % 2, 1)
    raise ValueError('bubblewrap executable missing from package')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_directory', type=Path, help='directory containing the game')
    parser.add_argument('game_executable', help='executable path relative to the game directory')
    parser.add_argument('-o', '--output', type=Path, default=Path('Game-x86_64.AppImage'),
                        help='output AppImage path (default: %(default)s)')
    args = parser.parse_args()
    if platform.machine() != 'x86_64':
        raise ValueError('An x86-64 build machine is required')
    game = args.game_directory.resolve(strict=True)
    executable_value = args.game_executable
    if not game.is_dir():
        raise ValueError('game_directory must be a directory')
    executable = Path(executable_value)
    if (not executable_value or executable.is_absolute() or '..' in executable.parts
            or not (game / executable).is_file()
            or not (game / executable).resolve().is_relative_to(game)):
        raise ValueError('game_executable must be a file inside game_directory')
    output = args.output.absolute()
    if not output.parent.is_dir():
        raise ValueError('The output directory does not exist')
    if output.parent.resolve().is_relative_to(game):
        raise ValueError('Output directory must be outside game_directory')
    if not shutil.which('mksquashfs'):
        raise ValueError('mksquashfs is required to build the AppImage')
    DOWNLOADS.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(download, ASSETS.items()))

    with tempfile.TemporaryDirectory(prefix='.game-packer-', dir=output.parent) as temp:
        tmp = Path(temp)
        app = tmp / 'AppDir'
        assets = app / 'assets'
        assets.mkdir(parents=True)
        print('Preparing game and runtime assets', flush=True)
        shutil.copytree(game, app / 'game', symlinks=False)
        extract(DOWNLOADS / 'GE-Proton9-27.tar.gz', assets / 'proton')
        extract(DOWNLOADS / 'umu-launcher-1.2.5-zipapp.tar', assets / 'launcher')
        extract(DOWNLOADS / 'SteamLinuxRuntime_sniper-3.0.20261021.266025.tar.xz',
                assets / 'steam')
        steam = assets / 'steam' / 'SteamLinuxRuntime_sniper'
        (steam / '_v2-entry-point').rename(steam / 'umu')
        shim = steam / 'umu-shim'
        shim.write_text('#!/bin/sh\nexec "$@"\n')
        shim.chmod(0o755)
        extract_bwrap(DOWNLOADS / 'bubblewrap_0.6.1-1ubuntu0.3_amd64.deb',
                      assets / 'bwrap')
        shutil.copy(ROOT / 'AppRun', app / 'AppRun')
        (app / 'AppRun').chmod(0o755)
        (app / 'executable').write_text(executable.as_posix())
        (app / 'game.desktop').write_text(
            '[Desktop Entry]\nType=Application\nName=Game\nExec=AppRun\n'
            'Icon=game\nCategories=Game;\n')
        (app / 'game.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
            '<rect width="64" height="64" fill="#222"/>'
            '<text x="8" y="48" font-size="45" fill="white">G</text></svg>')
        squash = tmp / 'image.squashfs'
        subprocess.run(['mksquashfs', str(app), str(squash), '-noappend',
                        '-comp', 'gzip', '-processors', '2'], check=True)
        # Place the temporary output alongside its destination for atomic rename.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.game-packer-',
                                             delete=False) as dest:
                temporary = Path(dest.name)
                with (DOWNLOADS / 'runtime-x86_64').open('rb') as runtime:
                    shutil.copyfileobj(runtime, dest)
                with squash.open('rb') as data:
                    shutil.copyfileobj(data, dest)
            temporary.chmod(0o755)
            temporary.replace(output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    print(f'Created {output}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as error:
        sys.exit(f'Game packer: {error}')
