#!/bin/sh
# Double-click in Finder, or run from a terminal.
TASK_PET_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for TASK_PET_PYTHON in /opt/homebrew/bin/python3.13 /usr/local/bin/python3.13 python3; do
    if "$TASK_PET_PYTHON" -c 'import tkinter; assert tkinter.TkVersion >= 8.6' >/dev/null 2>&1; then
        exec "$TASK_PET_PYTHON" "$TASK_PET_DIR/scripts/pet.py" "$@"
    fi
done
printf '%s\n' 'Task Pet needs Python with Tk 8.6 or newer.' 'On macOS with Homebrew: brew install python-tk@3.13'
read -r TASK_PET_DISMISS
exit 1
