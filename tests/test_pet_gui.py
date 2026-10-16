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
                    from appearance import photo_path
                    fixture = Path(tmp)/'fixture.png'
                    image = tk.PhotoImage(master=root, width=30, height=50)
                    image.put('red', to=(0, 0, 30, 50))
                    image.write(str(fixture), format='png')
                    with patch('tkinter.filedialog.askopenfilename', return_value=str(fixture)):
                        button(window, 'Photo / 照片').invoke()
                    self.assertTrue(photo_path().exists())
                    canvas = next(w for w in root.winfo_children() if isinstance(w, tk.Canvas))
                    photo_item = next(i for i in canvas.find_all() if canvas.type(i) == 'image')
                    self.assertEqual(canvas.itemcget(photo_item, 'state'), 'normal')
                    before_photo = photo_path().read_bytes()
                    with patch('tkinter.filedialog.askopenfilename', return_value=''):
                        button(window, 'Photo / 照片').invoke()
                    self.assertEqual(photo_path().read_bytes(), before_photo)
                    self.assertFalse((Path(tmp)/'tasks.json').exists())
                    add_button = button(window, '+ Add / 新增')
                    root.update()
                    add_button.event_generate('<ButtonPress-1>', x=10, y=10)
                    add_button.event_generate('<ButtonRelease-1>', x=10, y=10)
                    root.update()
                    dialog = editor_dialog(window)
                    root.update()
                    self.assertIsInstance(root.focus_get(), ttk.Entry)
                    self.assertIsNone(root.grab_current())
                    button(window, '+ Add / 新增').invoke()
                    self.assertEqual(sum(isinstance(w, tk.Toplevel) for w in window.winfo_children()), 1)
                    replace_title(dialog, '桌面测试')
                    notes = next(w for w in children(dialog) if isinstance(w, tk.Text))
                    notes.insert('1.0', '已完成初稿\n等待反馈')
                    entries = [w for w in children(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
                    title_entry, _, due_entry = entries
                    # Switching focus to the deadline must retain the unsaved title.
                    due_entry.focus_force()
                    root.update()
                    self.assertEqual(title_entry.get(), '桌面测试')
                    due_entry.insert(0, '2026-12-31')
                    root.after(3200, root.quit)
                    original_mainloop(root)
                    self.assertEqual(title_entry.get(), '桌面测试')
                    self.assertEqual(due_entry.get(), '2026-12-31')
                    self.assertEqual(load()['tasks'], [])
                    button(dialog, 'Save / 保存').invoke()
                    task = load()['tasks'][0]
                    self.assertEqual(task['title'], '桌面测试')
                    self.assertEqual(task['due'], '2026-12-31')
                    self.assertEqual(task['notes'], '已完成初稿\n等待反馈')
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
                    self.assertEqual(load()['tasks'][0]['notes'], '已完成初稿\n等待反馈')
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
