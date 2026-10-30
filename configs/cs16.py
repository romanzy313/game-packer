#!/usr/bin/env python3
"""Initialize Counter-Strike's player name once per game state."""
import os
from pathlib import Path
import pwd
import re
import sys


def main():
    game, state = map(Path, sys.argv[1:])
    marker = state / '.cs16-name-initialized'
    if marker.exists():
        return

    username = pwd.getpwuid(os.getuid()).pw_name
    if not username or any(ord(c) < 32 or ord(c) > 126 or c in '"\\;' for c in username):
        raise ValueError('Linux username cannot be safely represented in config.cfg')
    name = username.encode('ascii')
    config = game / 'cstrike' / 'config.cfg'
    data = config.read_bytes()
    pattern = re.compile(rb'(?im)^([ \t]*name[ \t]+)(?:"[^"\r\n]*"|[^\s;]+)([^\r\n]*)')
    writable = state / 'upper' / 'cstrike' / 'config.cfg'
    existing = pattern.search(data)
    if not (writable.is_file() and existing):
        if existing:
            data = pattern.sub(lambda match: match.group(1) + b'"' + name + b'"' + match.group(2), data, count=1)
        else:
            ending = b'\r\n' if b'\r\n' in data else b'\n'
            if data and not data.endswith((b'\n', b'\r')):
                data += ending
            data += b'name "' + name + b'"' + ending
        config.write_bytes(data)
    marker.touch()


if __name__ == '__main__':
    try:
        main()
    except (OSError, KeyError, ValueError) as error:
        sys.exit(f'Counter-Strike pre-launch: {error}')
