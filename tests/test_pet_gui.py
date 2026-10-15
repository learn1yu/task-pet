"""Opt-in actual Tk form tests: TASK_PET_GUI_TEST=1 python3 -m unittest discover -s tests."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

@unittest.skipUnless(os.environ.get('TASK_PET_GUI_TEST') == '1', 'Requires Tk graphical desktop')
class PetEditorTest(unittest.TestCase):
    def test_editor_persists_only_explicit_actions(self):
        import tkinter as tk
        from tkinter import ttk
        import pet
        from tasks import load

        def children(widget):
            return [child for w in widget.winfo_children() for child in [w, *children(w)]]

        def button(window, text):
            return next(w for w in children(window) if isinstance(w, ttk.Button) and w.cget('text') == text)

        def editor_dialog(window):
            return next(w for w in window.winfo_children() if isinstance(w, tk.Toplevel))

        def replace_title(dialog, title):
            entry = next(w for w in children(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox))
            entry.delete(0, 'end')
            entry.insert(0, title)

        original_mainloop = tk.Misc.mainloop
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, TASK_PET_DATA=str(Path(tmp)/'tasks.json')):
            def exercise(root, *args):
                try:
                    root.after(150, root.quit)
                    original_mainloop(root)
                    root.update()
                    window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                    self.assertEqual(load()['tasks'], [])
                    self.assertFalse((Path(tmp)/'tasks.json').exists())
                    button(window, '+ Add / 新增').invoke()
                    dialog = editor_dialog(window)
                    replace_title(dialog, '桌面测试')
                    self.assertEqual(load()['tasks'], [])
                    button(dialog, 'Save / 保存').invoke()
                    task = load()['tasks'][0]
                    self.assertEqual(task['title'], '桌面测试')
                    tree = next(w for w in children(window) if isinstance(w, ttk.Treeview))
                    tree.selection_set(task['id'])
                    button(window, 'Edit / 编辑').invoke()
                    dialog = editor_dialog(window)
                    replace_title(dialog, '修改后任务')
                    button(dialog, 'Cancel').invoke()
                    self.assertEqual(load()['tasks'][0]['title'], '桌面测试')
                    button(window, 'Edit / 编辑').invoke()
                    dialog = editor_dialog(window)
                    replace_title(dialog, '修改后任务')
                    button(dialog, 'Save / 保存').invoke()
                    self.assertEqual(load()['tasks'][0]['title'], '修改后任务')
                    tree.selection_set(task['id'])
                    button(window, '✓ Complete / 完成').invoke()
                    self.assertEqual(load()['tasks'][0]['status'], 'done')
                    self.assertEqual(tree.get_children(), ())
                    checkbox = next(w for w in children(window) if isinstance(w, ttk.Checkbutton))
                    checkbox.invoke()
                    self.assertTrue(tree.exists(task['id']))
                finally:
                    root.destroy()
            with patch.object(tk.Misc, 'mainloop', exercise), patch.object(sys, 'argv', ['pet.py', '--edit']):
                pet.main()

if __name__ == '__main__':
    unittest.main()
