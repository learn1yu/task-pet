"""Opt-in actual Tk form tests: TASK_PET_GUI_TEST=1 python3 -m unittest discover -s tests."""
import json
from datetime import date
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
                    priority = next(w for w in children(dialog) if isinstance(w, ttk.Combobox)
                                    and tuple(w.cget('values')) == ('P0', 'P1', 'P2', 'P3'))
                    self.assertEqual(priority.get(), 'P2')
                    priority.set('P0')
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
                    self.assertEqual(task['priority'], 'P0')
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
                    root.update()
                    self.assertEqual(load()['tasks'][0]['status'], 'done')
                    self.assertEqual(tree.get_children(), ())
                    notebook = next(w for w in children(window) if isinstance(w, ttk.Notebook))
                    tables = [w for w in children(notebook) if isinstance(w, ttk.Treeview)]
                    pending, completed, cancelled = tables
                    self.assertEqual(completed.get_children(), (task['id'],))
                    self.assertEqual(completed.selection(), (task['id'],))
                    self.assertEqual(notebook.select(), str(completed.master))
                    self.assertIn('(1)', notebook.tab(completed.master, 'text'))
                    self.assertEqual(cancelled.get_children(), ())

                    def change_status(status):
                        button(window, 'Edit / 编辑').invoke()
                        dialog = editor_dialog(window)
                        status_box = next(w for w in children(dialog) if isinstance(w, ttk.Combobox)
                                          and tuple(w.cget('values')) == ('todo', 'doing', 'done', 'cancelled'))
                        status_box.set(status)
                        button(dialog, 'Save / 保存').invoke()
                        root.update()

                    # Reopening a completed task operates on the active tab.
                    change_status('doing')
                    self.assertEqual(pending.get_children(), (task['id'],))
                    self.assertEqual(completed.get_children(), ())
                    self.assertEqual(notebook.select(), str(pending.master))
                    # The exact reported trigger: editing status to done + Save.
                    change_status('done')
                    self.assertEqual(pending.get_children(), ())
                    self.assertEqual(completed.get_children(), (task['id'],))
                    self.assertEqual(notebook.select(), str(completed.master))
                    self.assertEqual(load()['tasks'][0]['notes'], '已完成初稿\n等待反馈')
                    change_status('cancelled')
                    self.assertEqual(completed.get_children(), ())
                    self.assertEqual(cancelled.get_children(), (task['id'],))
                    self.assertEqual(notebook.select(), str(cancelled.master))
                    change_status('done')
                    # Passive refresh must keep the chosen tab and completed row.
                    notebook.select(pending.master)
                    root.after(3200, root.quit)
                    original_mainloop(root)
                    self.assertEqual(notebook.select(), str(pending.master))
                    self.assertEqual(completed.get_children(), (task['id'],))
                    # Closing/reopening the editor rebuilds Completed from disk.
                    root.tk.call(window.protocol('WM_DELETE_WINDOW'))
                    root.event_generate('<Return>')
                    root.update()
                    window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                    notebook = next(w for w in children(window) if isinstance(w, ttk.Notebook))
                    completed = [w for w in children(notebook) if isinstance(w, ttk.Treeview)][1]
                    self.assertEqual(completed.get_children(), (task['id'],))
                    self.assertIn('(1)', notebook.tab(completed.master, 'text'))
                finally:
                    root.destroy()
            with patch.object(tk.Misc, 'mainloop', exercise), patch.object(sys, 'argv', ['pet.py', '--edit']):
                pet.main()

    def test_pending_and_completed_sort_and_reorder(self):
        import tkinter as tk
        from tkinter import ttk
        import pet
        from tasks import load

        def children(widget):
            return [child for w in widget.winfo_children() for child in [w, *children(w)]]

        # Already in expected order; store reversed to exercise actual UI sorting.
        examples = [
            ('p0-early', 'P0', '2026-11-01', '01'),
            ('p0-late', 'P0', '2030-01-01', '01'),
            ('p0-no-date', 'P0', '', '01'),
            ('early-p3', 'P3', '20261101', '01'),
            ('same-p1-old', 'P1', '2026-12-01', '01'),
            ('same-p1-new', 'P1', '2026-12-01', '02'),
            ('same-p2', 'P2', '2026-12-01', '01'),
            ('late-p1', 'P1', '2027-01-01', '01'),
            ('no-date-p1', 'P1', '', '01'),
            ('no-date-p3', 'P3', '', '01'),
        ]
        original_mainloop = tk.Misc.mainloop
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, TASK_PET_DATA=str(Path(tmp)/'tasks.json')):
            records = []
            for status in ('todo', 'done'):
                for title, priority, due, day in reversed(examples):
                    records.append(dict(id=f'{status}-{title}', title=title, priority=priority,
                                        due=due, status='doing' if status == 'todo' and title == 'early-p3' else status,
                                        category='测试', notes='', created_at=f'2026-10-{day}T12:00:00+08:00',
                                        updated_at='2026-10-03T12:00:00+08:00'))
            path = Path(tmp)/'tasks.json'
            path.write_text(json.dumps({'version': 1, 'tasks': records}), encoding='utf-8')
            before = path.read_bytes()

            def exercise(root, *args):
                try:
                    root.after(150, root.quit)
                    original_mainloop(root)
                    root.update()
                    window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                    notebook = next(w for w in children(window) if isinstance(w, ttk.Notebook))
                    pending, completed, cancelled = [w for w in children(notebook) if isinstance(w, ttk.Treeview)]
                    expected = [example[0] for example in examples]
                    def titles(tree):
                        return [tree.item(item, 'values')[0] for item in tree.get_children()]
                    self.assertEqual(titles(pending), expected)
                    self.assertEqual(titles(completed), expected)
                    self.assertEqual(cancelled.get_children(), ())
                    self.assertEqual(path.read_bytes(), before)
                    def overdue_rows(tree):
                        return {item for item in tree.get_children() if 'overdue' in tree.item(item, 'tags')}
                    self.assertEqual(overdue_rows(pending), {'todo-p0-early', 'todo-early-p3'})
                    self.assertEqual(overdue_rows(completed), set())
                    # A new day must recolor existing rows without a file edit.
                    calendar.today.return_value = date(2026, 12, 2)
                    root.after(3200, root.quit)
                    original_mainloop(root)
                    self.assertEqual(overdue_rows(pending), {'todo-p0-early', 'todo-early-p3',
                                     'todo-same-p1-old', 'todo-same-p1-new', 'todo-same-p2'})
                    self.assertEqual(overdue_rows(completed), set())
                    self.assertEqual(path.read_bytes(), before)
                    self.assertEqual(titles(pending), expected)
                    # Editing either tab must move the existing row immediately.
                    for tree, status in ((pending, 'todo'), (completed, 'done')):
                        notebook.select(tree.master)
                        root.update()
                        task_id = f'{status}-late-p1'
                        tree.selection_set(task_id)
                        next(w for w in children(window) if isinstance(w, ttk.Button)
                             and w.cget('text') == 'Edit / 编辑').invoke()
                        dialog = next(w for w in window.winfo_children() if isinstance(w, tk.Toplevel))
                        priority = next(w for w in children(dialog) if isinstance(w, ttk.Combobox)
                                        and tuple(w.cget('values')) == ('P0', 'P1', 'P2', 'P3'))
                        priority.set('P0')
                        next(w for w in children(dialog) if isinstance(w, ttk.Button)
                             and w.cget('text') == 'Save / 保存').invoke()
                        root.update()
                        self.assertEqual(titles(tree), ['p0-early', 'late-p1'] +
                                         [title for title in expected[1:] if title != 'late-p1'])
                        self.assertEqual(tree.selection(), (task_id,))
                        self.assertEqual(next(t for t in load()['tasks'] if t['id'] == task_id)['priority'], 'P0')
                    # Changing the deadline or status must also clear red rows.
                    pet.mutate('update', 'todo-p0-early', '--due', '2027-02-01')
                    pet.mutate('update', 'todo-early-p3', '--due', '')
                    pet.mutate('update', 'todo-same-p1-old', '--status', 'done')
                    pet.mutate('update', 'todo-same-p1-new', '--status', 'cancelled')
                    root.after(3200, root.quit)
                    original_mainloop(root)
                    self.assertEqual(overdue_rows(pending), {'todo-same-p2'})
                    self.assertEqual(overdue_rows(completed), set())
                    self.assertEqual(overdue_rows(cancelled), set())
                finally:
                    root.destroy()
            with patch.object(tk.Misc, 'mainloop', exercise), patch.object(sys, 'argv', ['pet.py', '--edit']), \
                    patch('tasks.date', wraps=date) as calendar:
                calendar.today.return_value = date(2026, 12, 1)
                pet.main()

if __name__ == '__main__':
    unittest.main()
