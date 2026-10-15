# Task Pet · 任务宠物

仅在你主动调用时记录、分类和总结待办，附带一个可拖动、置顶、只读的猫咪桌面窗口。

## 安装与使用

把本目录放进支持 Agent Skills 的客户端技能目录，例如 `~/.codex/skills/task-pet/`，重新载入技能。

- `$task-pet 记录：周五之前完成论文初稿，分类科研，P1`
- `$task-pet 查看我的科研任务`
- `$task-pet 把 <任务ID> 标记为完成`
- `$task-pet 总结当前待办`
- `$task-pet 启动桌面宠物`

Codex 的显式调用策略位于 `agents/openai.yaml`；其他客户端仍须遵循 SKILL.md 的调用边界。普通聊天不会自动转成待办；模型建议的新任务必须由你接受后才能记录。

## 本地运行

需要 Python 3.9+；任务存储脚本仅使用标准库，支持 macOS/Linux。桌面窗口还需要 Tk 和图形桌面。

```sh
python3 scripts/tasks.py list
python3 scripts/tasks.py add '我的任务' --category 学习 --priority P2
python3 scripts/tasks.py summary
python3 scripts/pet.py
python3 -m unittest discover -s tests
```

如果 Python 缺少 tkinter，请使用带 Tk 的 Python 发行版；无图形环境仍可使用清单功能。宠物是独立桌面窗口，不是 ChatGPT Work Pets。窗口每三秒重读本地文件，关闭即退出；不联网、不采集聊天、不自动新增、不安装开机启动。

数据默认位于 `~/.local/share/task-pet/tasks.json`。可设置绝对路径环境变量 `TASK_PET_DATA` 自定义位置。清单只读操作不会创建文件；变更使用文件锁和原子替换。取消任务保留记录，不提供永久删除命令。

仓库只包含技能和程序，请勿提交真实待办文件。技能是给代理的指令，无法在忽略指令的客户端中强制执行授权隔离；CLI 供用户手动运行，不解析聊天授权。
