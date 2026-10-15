import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'tasks.py'

class TasksTest(unittest.TestCase):
    def test_lifecycle_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data' / 'tasks.json'
            env = dict(os.environ, TASK_PET_DATA=str(path))
            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, text=True, capture_output=True)
            self.assertEqual(json.loads(run('list').stdout), [])
            self.assertFalse(path.exists())
            task = json.loads(run('add', '验证任务', '--category', '科研', '--due', '2000-01-01').stdout)
            self.assertEqual(json.loads(run('summary').stdout)['overdue'][0]['id'], task['id'])
            self.assertEqual(run('update', task['id'], '--status', 'done').returncode, 0)
            self.assertEqual(json.loads(run('summary').stdout)['pending'], 0)
            before = path.read_bytes()
            self.assertNotEqual(run('update', 'missing', '--status', 'done').returncode, 0)
            self.assertNotEqual(run('add', 'bad', '--due', '2026-02-30').returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            path.write_text('{broken', encoding='utf-8')
            self.assertNotEqual(run('add', '禁止覆盖').returncode, 0)
            self.assertEqual(path.read_text(), '{broken')

    def test_notes_and_legacy_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'tasks.json'
            env = dict(os.environ, TASK_PET_DATA=str(path))
            def run(*args):
                result = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, text=True, capture_output=True, check=True)
                return json.loads(result.stdout)
            task = run('add', 'legacy task')
            data = json.loads(path.read_text())
            del data['tasks'][0]['notes']
            path.write_text(json.dumps(data))
            before = path.read_bytes()
            self.assertEqual(run('list')[0]['notes'], '')
            self.assertEqual(path.read_bytes(), before)
            note = '初稿完成\n等待导师反馈'
            self.assertEqual(run('update', task['id'], '--notes', note)['notes'], note)
            self.assertEqual(run('update', task['id'], '--priority', 'P1')['notes'], note)
            self.assertEqual(run('update', task['id'], '--notes', '')['notes'], '')

    def test_concurrent_adds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'tasks.json'
            env = dict(os.environ, TASK_PET_DATA=str(path))
            workers = [subprocess.Popen([sys.executable, str(SCRIPT), 'add', str(i)], env=env, stdout=subprocess.DEVNULL) for i in range(12)]
            self.assertTrue(all(p.wait() == 0 for p in workers))
            tasks = json.loads(path.read_text())['tasks']
            self.assertEqual(len(tasks), 12)
            self.assertEqual(len({t['id'] for t in tasks}), 12)

if __name__ == '__main__':
    unittest.main()
