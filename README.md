# Task Pet · 任务宠物

仅在你主动调用时记录、分类和总结待办，附带可拖动、置顶的浮动猫咪，点击即可直接编辑任务。

## 安装与使用

把本目录放进支持 Agent Skills 的客户端技能目录，例如 `~/.codex/skills/task-pet/`，重新载入技能。

- `$task-pet 记录：周五之前完成论文初稿，分类科研，P1`
- `$task-pet 查看我的科研任务`
- `$task-pet 把 <任务ID> 标记为完成`
- `$task-pet 总结当前待办`
- `$task-pet 启动桌面宠物`

Codex 的显式调用策略位于 `agents/openai.yaml`；其他客户端仍须遵循 SKILL.md 的调用边界。普通聊天不会自动转成待办；模型建议的新任务必须由你接受后才能记录。

## 桌面直接编辑

macOS 可双击 `Start Task Pet.command`（或终端运行 `sh "Start Task Pet.command"`）。启动后：

- 点击猫咪：打开任务清单；拖动猫咪：移动位置。
- 点击「新增」填写标题、分类、优先级、截止日期，再点击「保存」。
- 选中任务点击「编辑」，或双击任务；点击「完成」更新状态。
- 勾选「历史」查看已完成或已取消任务，编辑状态可恢复。
- 关闭清单只收起编辑器；右键猫咪选择「退出」结束程序（也可 Ctrl+单击）。

桌面点击保存/完成是显式操作，不需要经过聊天。未保存的输入不会落盘。macOS 使用透明背景；其他平台使用小型无标题栏背景窗口。

也可从内置宠物的聊天输入框调用 `$task-pet` 管理任务；独立编辑器不修改内置宠物界面。

## 本地运行

需要 Python 3.9+；任务存储脚本仅使用标准库，支持 macOS/Linux。桌面窗口还需要 Tk 和图形桌面。

```sh
python3 scripts/tasks.py list
python3 scripts/tasks.py add '我的任务' --category 学习 --priority P2
python3 scripts/tasks.py summary
python3 scripts/pet.py
python3 -m unittest discover -s tests
```

macOS 自带的旧 Tk 8.5 可能崩溃，请先安装 `brew install python-tk@3.13`，再使用启动器。若其他 Python 缺少 tkinter，请使用带 Tk 8.6+ 的 Python 发行版；无图形环境仍可使用清单功能。宠物是独立桌面窗口，不是 ChatGPT Work Pets。窗口每三秒重读本地文件，关闭即退出；不联网、不采集聊天、不自动新增、不安装开机启动。

数据默认位于 `~/.local/share/task-pet/tasks.json`。可设置绝对路径环境变量 `TASK_PET_DATA` 自定义位置。清单只读操作不会创建文件；变更使用文件锁和原子替换。取消任务保留记录，不提供永久删除命令。

仓库只包含技能和程序，请勿提交真实待办文件。技能是给代理的指令，无法在忽略指令的客户端中强制执行授权隔离；CLI 供用户手动运行，不解析聊天授权。
