import importlib.util
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'install_desktop.py'
spec = importlib.util.spec_from_file_location('install_desktop', SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class DesktopInstallerTest(unittest.TestCase):
    def test_portable_path_and_reinstall(self):
        with tempfile.TemporaryDirectory(prefix="task pet '") as tmp:
            skill = Path(tmp) / 'skill folder'
            skill.mkdir()
            # Fake launcher verifies shell quoting without starting a GUI.
            (skill / 'Start Task Pet.command').write_text('exit 42\n')
            app = installer.install(skill, Path(tmp) / 'desktop')
            metadata = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
            self.assertEqual(metadata['CFBundleIdentifier'], installer.BUNDLE_ID)
            executable = app / 'Contents/MacOS/TaskPet'
            self.assertEqual(subprocess.run([str(executable)]).returncode, 42)
            self.assertEqual(installer.install(skill, Path(tmp) / 'desktop'), app)

    def test_refuses_unrelated_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / 'Task Pet.app'
            app.mkdir()
            with self.assertRaises(ValueError):
                installer.install(SCRIPT.parents[1], tmp)
            self.assertEqual(list(app.iterdir()), [])
