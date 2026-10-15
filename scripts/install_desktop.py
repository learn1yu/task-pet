#!/usr/bin/env python3
"""Create a macOS desktop launcher pointing to this installed skill."""
import argparse
from pathlib import Path
import plistlib
import shlex
import sys

BUNDLE_ID = 'io.github.learn1yu.task-pet.launcher'


def install(skill, destination):
    skill = Path(skill).resolve()
    launcher = skill / 'Start Task Pet.command'
    if not launcher.is_file():
        raise ValueError('Start Task Pet.command is missing; keep the whole skill folder together.')
    app = Path(destination).expanduser().resolve() / 'Task Pet.app'
    contents = app / 'Contents'
    if app.exists():
        info = contents / 'Info.plist'
        try:
            existing = plistlib.loads(info.read_bytes())
        except (OSError, ValueError, plistlib.InvalidFileException):
            raise ValueError('Destination already exists and is not a Task Pet launcher.')
        if existing.get('CFBundleIdentifier') != BUNDLE_ID:
            raise ValueError('Refusing to replace an unrelated desktop app.')
    executable = contents / 'MacOS' / 'TaskPet'
    executable.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(CFBundleName='Task Pet', CFBundleDisplayName='Task Pet',
                    CFBundleIdentifier=BUNDLE_ID, CFBundleVersion='2',
                    CFBundleShortVersionString='1.1', CFBundlePackageType='APPL',
                    CFBundleExecutable='TaskPet', LSUIElement=True)
    (contents / 'Info.plist').write_bytes(plistlib.dumps(metadata))
    executable.write_text('#!/bin/sh\nexec /bin/sh ' + shlex.quote(str(launcher)) +
                          ' >> "${TMPDIR:-/tmp/}task-pet-launcher.log" 2>&1\n', encoding='utf-8')
    executable.chmod(0o755)
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path.home() / 'Desktop')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.exit(1, 'This desktop launcher is for macOS. Use scripts/pet.py on Linux.\n')
    try:
        print(install(Path(__file__).resolve().parents[1], args.destination))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
