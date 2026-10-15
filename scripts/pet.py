#!/usr/bin/env python3
"""Read-only draggable desktop task companion (Python + Tk)."""
import sys
from tasks import load

def main():
    try:
        import tkinter as tk
        root = tk.Tk()
    except Exception as exc:
        sys.exit(f'无法启动桌面宠物：需要图形桌面和支持 Tk 的 Python。{exc}')
    root.title('任务宠物')
    root.geometry('340x390+80+100')
    root.attributes('-topmost', True)
    root.configure(bg='#fff5df')
    root.minsize(280, 260)
    face = tk.Label(root, text=' /\_/\\\n( o.o )\n > ^ <', font=('Courier', 24), bg='#fff5df', fg='#72543c', cursor='fleur')
    face.pack(pady=8)
    anchor = [0, 0]
    def start(event):
        anchor[:] = [event.x_root - root.winfo_x(), event.y_root - root.winfo_y()]
    def drag(event):
        root.geometry(f'+{event.x_root-anchor[0]}+{event.y_root-anchor[1]}')
    face.bind('<Button-1>', start)
    face.bind('<B1-Motion>', drag)
    info = tk.Label(root, bg='#fff5df', font=('', 12))
    info.pack()
    body = tk.Text(root, wrap='word', bg='#fffaf0', relief='flat', font=('', 13), padx=12, pady=8)
    body.pack(fill='both', expand=True, padx=10, pady=8)
    tk.Button(root, text='关闭宠物', command=root.destroy).pack(pady=(0, 8))
    def refresh():
        try:
            tasks = [t for t in load()['tasks'] if t['status'] in ('todo', 'doing')]
            tasks.sort(key=lambda t: (t['priority'], t['due'] or '9999', t['created_at']))
            info.configure(text=f'还有 {len(tasks)} 项待办 · 拖动猫咪移动')
            text = '\n\n'.join(f"{'▶' if t['status']=='doing' else '○'} [{t['priority']}] {t['title']}\n   {t['category']}" + (f" · {t['due']}" if t['due'] else '') for t in tasks) or '清单为空，休息一下吧。'
        except (ValueError, OSError) as exc:
            info.configure(text='读取失败，数据未修改')
            text = str(exc)
        body.configure(state='normal')
        body.delete('1.0', 'end')
        body.insert('1.0', text)
        body.configure(state='disabled')
        root.after(3000, refresh)
    refresh()
    root.mainloop()

if __name__ == '__main__':
    main()
