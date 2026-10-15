#!/usr/bin/env python3
"""Floating desktop pet. Click to edit local tasks; drag to move."""
import json
from pathlib import Path
import subprocess
import sys
from tasks import load, summary

SCRIPT = Path(__file__).with_name('tasks.py')


def mutate(*args):
    """Reuse the CLI's validation, file lock and atomic storage."""
    result = subprocess.run([sys.executable, str(SCRIPT), *args], text=True,
                            capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Could not save task')
    return json.loads(result.stdout)


def main():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        if tk.TkVersion < 8.6:
            raise RuntimeError('Tk 8.6+ required. On macOS: brew install python-tk@3.13; use Start Task Pet.command')
        root = tk.Tk()
    except Exception as exc:
        sys.exit(f'无法启动桌面宠物：需要图形桌面和支持 Tk 的 Python。{exc}')
    root.title('Task Pet')
    root.geometry('200x210+80+100')
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    background = '#fff5df'
    root.configure(bg=background)
    if sys.platform == 'darwin':
        try:
            root.configure(bg='systemTransparent')
            root.attributes('-transparent', True)
            background = 'systemTransparent'
        except tk.TclError:
            pass
    canvas = tk.Canvas(root, width=200, height=210, bg=background,
                       highlightthickness=0, cursor='hand2')
    canvas.pack()
    # Vector cat, no external image files or downloads.
    canvas.create_oval(35, 166, 166, 179, fill='#e5d4bb', outline='')
    canvas.create_line(148, 145, 176, 128, 174, 105, fill='#d89b63', width=13,
                       smooth=True, tags='cat')
    canvas.create_oval(53, 99, 150, 174, fill='#eab47c', outline='#805f47', width=2, tags='cat')
    canvas.create_polygon(44, 85, 43, 34, 80, 56, fill='#eab47c', outline='#805f47', width=2, tags='cat')
    canvas.create_polygon(119, 54, 154, 34, 153, 91, fill='#eab47c', outline='#805f47', width=2, tags='cat')
    canvas.create_polygon(49, 44, 50, 68, 68, 57, fill='#f3b7ad', outline='', tags='cat')
    canvas.create_polygon(147, 44, 128, 57, 147, 70, fill='#f3b7ad', outline='', tags='cat')
    canvas.create_oval(37, 51, 161, 135, fill='#f5c993', outline='#805f47', width=2, tags='cat')
    eyes = [canvas.create_oval(x, 83, x+9, 96, fill='#493c35', outline='', tags='cat') for x in (68, 122)]
    canvas.create_polygon(94, 101, 106, 101, 100, 107, fill='#c27676', outline='', tags='cat')
    canvas.create_line(89, 111, 95, 115, 100, 110, 105, 115, 111, 111,
                       fill='#805f47', smooth=True, width=2, tags='cat')
    for x, end in ((52, 24), (146, 174)):
        for y in (101, 111):
            canvas.create_line(x, y, end, y-4, fill='#805f47', tags='cat')
    badge = canvas.create_text(100, 16, text='Task Pet', fill='#624834', font=('', 12, 'bold'))
    canvas.create_text(100, 195, text='Click: tasks · Drag: move', fill='#624834', font=('', 10))
    state = {'editor': None, 'tree': None, 'data': [], 'message': None, 'tick': 0}
    anchor = {'x': 0, 'y': 0, 'moved': False}

    def press(event):
        anchor.update(x=event.x_root, y=event.y_root, moved=False)

    def drag(event):
        dx, dy = event.x_root-anchor['x'], event.y_root-anchor['y']
        if abs(dx)+abs(dy) > 4 or anchor['moved']:
            anchor['moved'] = True
            x = max(0, min(root.winfo_screenwidth()-200, root.winfo_x()+dx))
            y = max(0, min(root.winfo_screenheight()-210, root.winfo_y()+dy))
            root.geometry(f'+{x}+{y}')
            anchor.update(x=event.x_root, y=event.y_root)

    def refresh():
        try:
            data = load()
            state['data'] = data['tasks']
            counts = summary(data)
            canvas.itemconfigure(badge, text=f"{counts['pending']} pending · {len(counts['overdue'])} overdue")
            tree = state['tree']
            if tree is not None and tree.winfo_exists():
                selected = tree.selection()
                scroll = tree.yview()
                tree.delete(*tree.get_children())
                show_all = state['show_all'].get()
                for task in sorted(state['data'], key=lambda t: (t['priority'], t['due'] or '9999', t['created_at'])):
                    if show_all or task['status'] in ('todo', 'doing'):
                        tree.insert('', 'end', iid=task['id'], values=tuple(task[k] for k in ('title', 'category', 'priority', 'due', 'status')))
                for item in selected:
                    if tree.exists(item):
                        tree.selection_set(item)
                if scroll:
                    tree.yview_moveto(scroll[0])
                state['message'].set(f"{counts['pending']} pending · {counts['by_status'].get('done', 0)} completed · {len(counts['overdue'])} overdue")
        except (ValueError, OSError) as exc:
            canvas.itemconfigure(badge, text='Data error · click to inspect')
            if state['message'] is not None:
                state['message'].set(f'Read failed: {exc}')

    def commit(args, parent):
        try:
            mutate(*args)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror('Task not saved', str(exc), parent=parent)
            return False
        refresh()
        return True

    def form(task=None):
        parent = state['editor']
        dialog = tk.Toplevel(parent)
        dialog.title('Edit task' if task else 'Add task')
        dialog.attributes('-topmost', True)
        dialog.transient(parent)
        dialog.resizable(False, False)
        fields = {}
        options = {'priority': ('P1', 'P2', 'P3'), 'status': ('todo', 'doing', 'done', 'cancelled')}
        defaults = dict(title='', category='收件箱', priority='P2', due='', status='todo')
        labels = dict(title='Task / 任务', category='Category / 分类', priority='Priority / 优先级', due='Due / 截止日期 YYYY-MM-DD', status='Status / 状态')
        for row, key in enumerate(defaults):
            ttk.Label(dialog, text=labels[key]).grid(row=row, column=0, sticky='w', padx=12, pady=8)
            value = tk.StringVar(value=task[key] if task else defaults[key])
            fields[key] = value
            if key in options:
                widget = ttk.Combobox(dialog, textvariable=value, values=options[key], state='readonly', width=30)
            else:
                widget = ttk.Entry(dialog, textvariable=value, width=33)
            widget.grid(row=row, column=1, padx=12, pady=8)
            if key == 'title':
                widget.focus_set()
        def save_form():
            args = ['update', task['id']] if task else ['add', fields['title'].get()]
            for key, value in fields.items():
                if not task and key in ('title', 'status'):
                    continue
                args.extend(['--'+key, value.get()])
            if not task and fields['status'].get() != 'todo':
                messagebox.showinfo('New task', 'New tasks start as todo. You can change the status after saving.', parent=dialog)
                return
            if commit(args, dialog):
                dialog.destroy()
        ttk.Button(dialog, text='Save / 保存', command=save_form).grid(row=5, column=1, sticky='e', padx=12, pady=12)
        ttk.Button(dialog, text='Cancel', command=dialog.destroy).grid(row=5, column=0, padx=12, pady=12)
        dialog.bind('<Return>', lambda _: save_form())
        dialog.bind('<Escape>', lambda _: dialog.destroy())
        dialog.grab_set()

    def selected():
        selection = state['tree'].selection()
        if not selection:
            messagebox.showinfo('Choose a task', 'Select a task first.', parent=state['editor'])
            return None
        return next((t for t in state['data'] if t['id'] == selection[0]), None)

    def edit():
        task = selected()
        if task:
            form(task)

    def complete():
        task = selected()
        if task:
            commit(['update', task['id'], '--status', 'done'], state['editor'])

    def open_editor():
        existing = state['editor']
        if existing is not None and existing.winfo_exists():
            existing.deiconify()
            existing.lift()
            return
        window = tk.Toplevel(root)
        state['editor'] = window
        window.title('Task Pet · 我的任务')
        window.geometry('780x440')
        window.minsize(600, 300)
        window.attributes('-topmost', True)
        toolbar = ttk.Frame(window, padding=10)
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text='+ Add / 新增', command=form).pack(side='left')
        ttk.Button(toolbar, text='Edit / 编辑', command=edit).pack(side='left', padx=6)
        ttk.Button(toolbar, text='✓ Complete / 完成', command=complete).pack(side='left')
        state['show_all'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text='Show history / 历史', variable=state['show_all'], command=refresh).pack(side='right')
        table = ttk.Frame(window)
        table.pack(fill='both', expand=True, padx=10)
        columns = ('title', 'category', 'priority', 'due', 'status')
        tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse')
        state['tree'] = tree
        for key, title, width in zip(columns, ('Task / 任务', 'Category', 'Priority', 'Due', 'Status'), (300, 110, 65, 100, 90)):
            tree.heading(key, text=title)
            tree.column(key, width=width, minwidth=50)
        scrollbar = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        tree.bind('<Double-1>', lambda _: edit())
        tree.bind('<Return>', lambda _: edit())
        state['message'] = tk.StringVar()
        ttk.Label(window, textvariable=state['message'], padding=10).pack(anchor='w')
        ttk.Label(window, text='Saved locally only when you click Save or Complete. Closing this window keeps the pet running.', padding=(10, 0, 10, 10)).pack(anchor='w')
        def close_editor():
            state.update(editor=None, tree=None, message=None)
            window.destroy()
        window.protocol('WM_DELETE_WINDOW', close_editor)
        refresh()

    canvas.bind('<ButtonPress-1>', press)
    canvas.bind('<B1-Motion>', drag)
    canvas.bind('<ButtonRelease-1>', lambda _: None if anchor['moved'] else open_editor())
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label='Open tasks / 编辑任务', command=open_editor)
    menu.add_command(label='Quit pet / 退出', command=root.destroy)
    canvas.bind('<Button-3>', lambda event: menu.tk_popup(event.x_root, event.y_root))
    canvas.bind('<Control-Button-1>', lambda event: menu.tk_popup(event.x_root, event.y_root))
    root.bind('<Escape>', lambda _: root.destroy())
    root.bind('<Return>', lambda _: open_editor())
    if '--edit' in sys.argv:
        root.after(100, open_editor)
    def poll():
        refresh()
        root.after(3000, poll)
    def animate():
        state['tick'] += 1
        blink = state['tick'] % 20 == 0
        for item, x in zip(eyes, (68, 122)):
            canvas.coords(item, x, 88 if blink else 83, x+9, 91 if blink else 96)
        root.after(180, animate)
    poll()
    animate()
    root.mainloop()


if __name__ == '__main__':
    main()
