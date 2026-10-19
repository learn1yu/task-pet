#!/usr/bin/env python3
"""Local task storage. No network, telemetry, or automatic task capture."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime
import json
import os
from pathlib import Path
import tempfile
import uuid

STATUSES = ('todo', 'doing', 'done', 'cancelled')
PRIORITIES = ('P0', 'P1', 'P2', 'P3')

def data_path():
    path = Path(os.environ.get('TASK_PET_DATA', '~/.local/share/task-pet/tasks.json')).expanduser()
    if not path.is_absolute():
        raise ValueError('TASK_PET_DATA must be an absolute path')
    return path

def load(path=None):
    path = path or data_path()
    if not path.exists():
        return {'version': 1, 'tasks': []}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('tasks'), list):
        raise ValueError('Invalid task database; original file preserved')
    ids = set()
    for t in data['tasks']:
        if not isinstance(t, dict) or not all(k in t for k in ('id', 'title', 'category', 'priority', 'status', 'due', 'created_at', 'updated_at')):
            raise ValueError('Invalid task record')
        t.setdefault('notes', '')  # Legacy tasks load without rewriting the file.
        if not all(isinstance(t[k], str) for k in t) or not t['title'].strip() or t['status'] not in STATUSES or t['priority'] not in PRIORITIES or t['id'] in ids:
            raise ValueError('Invalid task fields')
        if t['due']:
            date.fromisoformat(t['due'])
        ids.add(t['id'])
    return data

@contextmanager
def locked(path):
    # OS releases advisory lock on crash; no stale-lock cleanup needed.
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.lock', 'a', encoding='utf-8') as handle:
        os.chmod(handle.name, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

def save(data, path):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.tasks-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError('Must not be empty')
    return value.strip()

def due(value):
    if value:
        try:
            date.fromisoformat(value)
        except ValueError:
            raise argparse.ArgumentTypeError('Use YYYY-MM-DD')
    return value

def summary(data):
    tasks = data['tasks']
    pending = [t for t in tasks if t['status'] in ('todo', 'doing')]
    return {'pending': len(pending), 'by_category': dict(Counter(t['category'] for t in pending)),
            'by_status': dict(Counter(t['status'] for t in tasks)),
            'overdue': [t for t in pending if t['due'] and t['due'] < date.today().isoformat()],
            'doing': [t for t in pending if t['status'] == 'doing']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add')
    add.add_argument('title', type=nonempty)
    update = commands.add_parser('update')
    update.add_argument('id')
    update.add_argument('--title', type=nonempty)
    update.add_argument('--status', choices=STATUSES)
    for p in (add, update):
        p.add_argument('--category', type=nonempty, default='收件箱' if p is add else None)
        p.add_argument('--priority', choices=PRIORITIES, default='P2' if p is add else None)
        p.add_argument('--due', type=due, default='' if p is add else None)
        p.add_argument('--notes', default='' if p is add else None, help='Situation, progress or blockers (multiline allowed)')
    listing = commands.add_parser('list')
    listing.add_argument('--status', choices=STATUSES)
    listing.add_argument('--category')
    commands.add_parser('summary')
    args = parser.parse_args()
    try:
        path = data_path()
        if args.command in ('add', 'update'):
            with locked(path):
                data = load(path)
                now = datetime.now().astimezone().isoformat(timespec='seconds')
                if args.command == 'add':
                    result = dict(id=uuid.uuid4().hex, title=args.title, category=args.category,
                                  priority=args.priority, due=args.due, notes=args.notes, status='todo', created_at=now, updated_at=now)
                    data['tasks'].append(result)
                else:
                    result = next((t for t in data['tasks'] if t['id'] == args.id), None)
                    if result is None:
                        raise ValueError('Unknown task ID')
                    for key in ('title', 'category', 'priority', 'due', 'status', 'notes'):
                        value = getattr(args, key)
                        if value is not None:
                            result[key] = value
                    result['updated_at'] = now
                save(data, path)
        else:
            data = load(path)
            result = summary(data) if args.command == 'summary' else [t for t in data['tasks'] if (not args.status or t['status'] == args.status) and (not args.category or t['category'] == args.category)]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')

if __name__ == '__main__':
    main()
