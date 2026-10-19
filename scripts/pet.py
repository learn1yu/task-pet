#!/usr/bin/env python3
"""Floating desktop pet. Click to edit local tasks; drag to move."""
import json
from datetime import date
from pathlib import Path
import subprocess
import sys
from tasks import PRIORITIES, load, summary
from appearance import photo_path, install_photo, reset_photo

SCRIPT = Path(__file__).with_name('tasks.py')
VIEWS = (
    ('pending', '未完成 / Pending', ('todo', 'doing')),
    ('done', '已完成 / Completed', ('done',)),
    ('cancelled', '已取消 / Cancelled', ('cancelled',)),
)


def task_sort_key(task):
    """P0 first; then earliest deadline, priority, and creation order."""
    due = date.fromisoformat(task['due']) if task['due'] else date.max
    return (task['priority'] != 'P0', not task['due'], due,
            task['priority'], task['created_at'])


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
        from tkinter import ttk, messagebox, filedialog
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
    state = {'editor': None, 'tree': None, 'trees': {}, 'notebook': None,
             'data': [], 'message': None, 'tick': 0, 'form': None}
    # Keep PhotoImage referenced for as long as its canvas item exists.
    state['photo'] = None
    photo_item = canvas.create_image(100, 100, anchor='center', state='hidden')
    cat_items = [item for item in canvas.find_all() if item not in (badge, photo_item)
                 and canvas.type(item) != 'text']

    def show_photo(image):
        state['photo'] = image
        canvas.itemconfigure(photo_item, image=image, state='normal')
        for item in cat_items:
            canvas.itemconfigure(item, state='hidden')

    def choose_photo():
        filename = filedialog.askopenfilename(parent=state['editor'] or root,
            title='Choose pet photo / 选择宠物照片',
            filetypes=[('Images', '*.png *.jpg *.jpeg *.webp *.gif *.bmp *.tif *.tiff *.heic'), ('All files', '*')])
        if not filename:
            return
        try:
            show_photo(install_photo(filename, root))
        except (OSError, ValueError, tk.TclError, subprocess.SubprocessError):
            messagebox.showerror('Photo not changed',
                'Could not open this image. Try PNG or JPEG on macOS, or PNG/GIF on other platforms. Your previous photo is unchanged.',
                parent=state['editor'] or root)

    def restore_cat():
        try:
            reset_photo()
        except OSError as exc:
            messagebox.showerror('Could not reset photo', str(exc), parent=state['editor'] or root)
            return
        canvas.itemconfigure(photo_item, state='hidden')
        state['photo'] = None
        for item in cat_items:
            canvas.itemconfigure(item, state='normal')

    if photo_path().exists():
        try:
            show_photo(tk.PhotoImage(master=root, file=str(photo_path())))
        except (OSError, tk.TclError):
            pass  # Fall back to the cat if a preference file is corrupt.

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
            ordered = sorted(state['data'], key=task_sort_key)
            for key, label, statuses in VIEWS:
                tree = state['trees'].get(key)
                if tree is None or not tree.winfo_exists():
                    continue
                selected = tree.selection()
                scroll = tree.yview()
                visible = [task for task in ordered if task['status'] in statuses]
                visible_ids = {task['id'] for task in visible}
                for item in tree.get_children():
                    if item not in visible_ids:
                        tree.delete(item)
                for index, task in enumerate(visible):
                    values = tuple(task[k] for k in ('title', 'category', 'priority', 'due', 'status')) + (' '.join(task['notes'].split())[:90],)
                    if tree.exists(task['id']):
                        if tuple(str(v) for v in tree.item(task['id'], 'values')) != values:
                            tree.item(task['id'], values=values)
                        tree.move(task['id'], '', index)
                    else:
                        tree.insert('', index, iid=task['id'], values=values)
                for item in selected:
                    if tree.exists(item):
                        tree.selection_set(item)
                if scroll:
                    tree.yview_moveto(scroll[0])
                state['notebook'].tab(tree.master, text=f'{label} ({len(visible)})')
            if state['message'] is not None:
                state['message'].set(f"{counts['pending']} pending · {counts['by_status'].get('done', 0)} completed · {len(counts['overdue'])} overdue")
        except (ValueError, OSError) as exc:
            canvas.itemconfigure(badge, text='Data error · click to inspect')
            if state['message'] is not None:
                state['message'].set(f'Read failed: {exc}')

    def commit(args, parent):
        try:
            task = mutate(*args)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror('Task not saved', str(exc), parent=parent)
            return False
        refresh()
        # Follow explicit changes to their destination so a completed task never
        # appears to vanish. Passive polling updates tabs without switching them.
        key = 'pending' if task['status'] in ('todo', 'doing') else task['status']
        tree = state['trees'].get(key)
        if tree is not None and tree.exists(task['id']):
            state['notebook'].select(tree.master)
            state['tree'] = tree
            tree.selection_set(task['id'])
            tree.focus(task['id'])
            tree.see(task['id'])
        return True

    def present(window, focus=None):
        # Launchpad can leave Tk windows visible without keyboard activation.
        # Focus only on a user action; polling never raises or activates a window.
        window.deiconify()
        window.lift()
        target = focus or window
        def activate():
            if target.winfo_exists():
                target.focus_force()
        window.after_idle(activate)

    def form(task=None):
        existing = state['form']
        if existing is not None and existing.winfo_exists():
            present(existing, existing.focus_lastfor())
            return
        parent = state['editor']
        dialog = tk.Toplevel(parent)
        state['form'] = dialog
        dialog.title('Edit task' if task else 'Add task')
        dialog.transient(parent)
        dialog.resizable(False, False)
        fields = {}
        dialog.task_fields = fields  # Keep field variables alive until the dialog closes.
        def close_form():
            state['form'] = None
            dialog.destroy()
        dialog.protocol('WM_DELETE_WINDOW', close_form)
        options = {'priority': PRIORITIES, 'status': ('todo', 'doing', 'done', 'cancelled')}
        defaults = dict(title='', category='收件箱', priority='P2', due='', status='todo', notes='')
        labels = dict(title='Task / 任务', category='Category / 分类', priority='Priority / 优先级', due='Due / 截止日期 YYYY-MM-DD', status='Status / 状态', notes='Situation / 情况与备注')
        for row, key in enumerate(defaults):
            ttk.Label(dialog, text=labels[key]).grid(row=row, column=0, sticky='w', padx=12, pady=8)
            value = tk.StringVar(value=task[key] if task else defaults[key])
            fields[key] = value
            if key == 'notes':
                widget = tk.Text(dialog, width=33, height=5, wrap='word', undo=True)
                widget.insert('1.0', value.get())
                notes_widget = widget
            elif key in options:
                widget = ttk.Combobox(dialog, textvariable=value, values=options[key], state='readonly', width=30)
            else:
                widget = ttk.Entry(dialog, textvariable=value, width=33)
            widget.grid(row=row, column=1, padx=12, pady=8)
            if key == 'title':
                title_widget = widget
        def save_form():
            fields['notes'].set(notes_widget.get('1.0', 'end-1c'))
            args = ['update', task['id']] if task else ['add', fields['title'].get()]
            for key, value in fields.items():
                if not task and key in ('title', 'status'):
                    continue
                args.append('--'+key+'='+value.get())
            if not task and fields['status'].get() != 'todo':
                messagebox.showinfo('New task', 'New tasks start as todo. You can change the status after saving.', parent=dialog)
                return
            if commit(args, dialog):
                close_form()
        ttk.Button(dialog, text='Save / 保存', command=save_form).grid(row=6, column=1, sticky='e', padx=12, pady=12)
        ttk.Button(dialog, text='Cancel', command=close_form).grid(row=6, column=0, padx=12, pady=12)
        dialog.bind('<Return>', lambda event: None if isinstance(event.widget, tk.Text) else save_form())
        dialog.bind('<Control-Return>', lambda _: (save_form(), 'break')[1])
        dialog.bind('<Command-Return>', lambda _: (save_form(), 'break')[1])
        dialog.bind('<Escape>', lambda _: close_form())
        # Deliberately modeless: never capture mouse/keyboard with a Tk grab.
        present(dialog, title_widget)

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
            active_form = state['form']
            if active_form is not None and active_form.winfo_exists():
                present(active_form, active_form.focus_lastfor())
            else:
                present(existing, state['tree'])
            return
        window = tk.Toplevel(root)
        state['editor'] = window
        window.title('Task Pet · 我的任务')
        window.geometry('900x440')
        window.minsize(600, 300)
        toolbar = ttk.Frame(window, padding=10)
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text='+ Add / 新增', command=form).pack(side='left')
        ttk.Button(toolbar, text='Edit / 编辑', command=edit).pack(side='left', padx=6)
        ttk.Button(toolbar, text='✓ Complete / 完成', command=complete).pack(side='left')
        ttk.Button(toolbar, text='Photo / 照片', command=choose_photo).pack(side='left', padx=6)
        notebook = ttk.Notebook(window)
        state['notebook'] = notebook
        notebook.pack(fill='both', expand=True, padx=10)
        columns = ('title', 'category', 'priority', 'due', 'status', 'notes')
        for key, label, _ in VIEWS:
            table = ttk.Frame(notebook)
            notebook.add(table, text=label)
            tree = ttk.Treeview(table, columns=columns, show='headings', selectmode='browse')
            state['trees'][key] = tree
            for column, title, width in zip(columns, ('Task / 任务', 'Category', 'Priority', 'Due', 'Status', 'Situation / 情况'), (220, 90, 60, 95, 80, 180)):
                tree.heading(column, text=title)
                tree.column(column, width=width, minwidth=50)
            scrollbar = ttk.Scrollbar(table, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side='right', fill='y')
            tree.pack(fill='both', expand=True)
            tree.bind('<Double-1>', lambda _: edit())
            tree.bind('<Return>', lambda _: edit())
        state['tree'] = state['trees']['pending']
        def tab_changed(_):
            state['tree'] = next((tree for tree in state['trees'].values()
                                  if str(tree.master) == notebook.select()), None)
        notebook.bind('<<NotebookTabChanged>>', tab_changed)
        state['message'] = tk.StringVar()
        ttk.Label(window, textvariable=state['message'], padding=10).pack(anchor='w')
        ttk.Label(window, text='Saved locally only when you click Save or Complete. Closing this window keeps the pet running.', padding=(10, 0, 10, 10)).pack(anchor='w')
        def close_editor():
            state.update(editor=None, tree=None, trees={}, notebook=None, message=None, form=None)
            window.destroy()
        window.protocol('WM_DELETE_WINDOW', close_editor)
        refresh()
        present(window, state['tree'])

    canvas.bind('<ButtonPress-1>', press)
    canvas.bind('<B1-Motion>', drag)
    canvas.bind('<ButtonRelease-1>', lambda _: None if anchor['moved'] else open_editor())
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label='Open tasks / 编辑任务', command=open_editor)
    menu.add_command(label='Choose photo… / 选择照片', command=choose_photo)
    menu.add_command(label='Restore cat / 恢复猫咪', command=restore_cat)
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
