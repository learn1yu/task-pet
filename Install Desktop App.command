#!/bin/sh
TASK_PET_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$TASK_PET_DIR/scripts/install_desktop.py"
TASK_PET_RESULT=$?
if [ "$TASK_PET_RESULT" -eq 0 ]; then
    printf '%s\n' 'Ready. Double-click Task Pet.app on your Desktop to open it.'
else
    printf '%s\n' 'Installation failed. See the message above.'
fi
printf '%s\n' 'Press Enter to close.'
read -r TASK_PET_DISMISS
exit "$TASK_PET_RESULT"
