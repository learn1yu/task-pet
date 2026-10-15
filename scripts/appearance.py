"""Local photo preferences; photos never enter the skill repository."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from tasks import data_path


def photo_path():
    return data_path().with_name('pet-photo.png')


def install_photo(source, master):
    """Create a bounded display copy, retaining the original file unchanged."""
    import tkinter as tk
    source = Path(source).expanduser().resolve(strict=True)
    target = photo_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(suffix='.png', dir=target.parent)
    os.close(fd)
    try:
        if sys.platform == 'darwin':
            subprocess.run(['/usr/bin/sips', '-s', 'format', 'png', '-Z', '160',
                            str(source), '--out', temporary], check=True,
                           capture_output=True, timeout=20)
        else:
            image = tk.PhotoImage(master=master, file=str(source))
            scale = max(1, (max(image.width(), image.height())+159)//160)
            image.subsample(scale, scale).write(temporary, format='png')
        # Validate decoding before replacing the previous working appearance.
        image = tk.PhotoImage(master=master, file=temporary)
        if not image.width() or not image.height():
            raise ValueError('Empty image')
        os.replace(temporary, target)
        return image
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def reset_photo():
    path = photo_path()
    if path.exists():
        # Keep a local copy; the user's original photo is never altered.
        os.replace(path, path.with_name('pet-photo.previous.png'))
