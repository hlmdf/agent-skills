---
name: install-skill
description: 把技能（Agent Skill）装到本机 Codex 的用户级目录，并以本机约定登记、标记为自装技能。当用户要求安装、更新或卸载某个技能时使用，无论给的是 GitHub 链接、其它托管（GitLab/Gitee/压缩包/网页/本地目录）、只有一个技能名，还是只描述了想要的能力；也用于回答「我自己装的技能在哪、怎么和自带的区分」。不用于从头撰写新技能（用 $skill-creator）。
---

# 装技能

把技能装到本机（来源可能是 GitHub，也可能是别的，见下），并让它可被发现、可被区分、
可被跟踪更新。

## 落点与标记约定

- 装到 `~/.agents/skills/<技能名>`。这是官方文档定义的 USER 作用域
  （`$HOME/.agents/skills`），Codex 自动读取；自带技能属于 SYSTEM 作用域。
- 只保留这一份。`npx skills add` 会给它探测到的每个 agent 目录各放一份副本
  （Cursor 等）。装完检查 `~/.cursor/skills/` 之类目录，多余的副本按用户意愿清掉。
- 标记约定：**只有用户明确指定安装的技能**才打标记 —— `SKILL.md` 描述前缀 `[自装] `，
  `agents/openai.yaml` 的 `display_name` 也带 `[自装] `。统一用
  `scripts/mark-user-skills.py` 处理，不要手写：它按 `TARGETS` 名单打标，同时把不在名单上
  却带着标记的技能清干净（CLI 自己装回来的配套技能如 `find-skills` 就属于不打标的那类）。
  连带装进来的依赖技能既不属于这两类，**打不打标记必须逐个问用户**，见流程第 4 步。

## 先定来源，再动手

用户不一定给链接，也不一定是 GitHub。先判断内容从哪来，后面的落点、标记、登记、校验
对所有来源都一样。

| 用户给的 | 怎么拿到内容 | 之后 |
|---|---|---|
| GitHub 仓库或链接 | 本流程第 2、3 步（先试 CLI，失败走回退） | 本流程第 4、5 步 |
| GitLab、Gitee、其它 git 托管 | 回退流程，clone URL 换成对应地址（TLS 处理相同） | 同上 |
| 压缩包、zip、网页、本地目录 | 下载或直接读取到可写工作目录，再按技能布局整理 | 同上 |
| 只有一个技能名，属于 openai/skills 精选 | `$skill-installer <name>` 取内容 | 落点、标记、登记按本技能 |
| 只有技能名，来源不明 | 先 `$find-skills` 搜索 | 搜到来源后回到上表对应一行 |
| 只描述了想要的能力 | 先 `$find-skills` 搜索可用技能 | 搜不到就向用户要来源，不要硬装 |

**不要按名字猜一个同名仓库就装。** 来源错了就是往本机装来路不明的指令。找不到可靠来源时，
把候选列给用户确认，或者直接问；拿不到来源就停在这一步并说明原因。

## 流程

1. **先看仓库形态**，决定装什么：
   - 标准技能包：仓库里有 `skills/<name>/SKILL.md` → 装那个目录。
   - 散装技能文本：根目录直接是 `SKILL_*.md`、`System_Prompt.txt` 之类 → 自己包成技能：
     上游主文件存为 `SKILL.md`（放在技能根），其余文件放 `references/`；
     frontmatter 的 `name` 用上游自带的，没有才另起一个。
   - 插件仓库（`.claude-plugin/`、`.codex-plugin/`）→ 走插件路线，不套用本流程。
2. **先试一次官方 CLI**：`npx skills add <owner>/<repo> -g`（加 `-a codex` 限定宿主，
   加 `--skill <name>` 限定技能）。本机必然失败，原因见「本机环境约束」；试一次确认即可，
   不要在它上面反复试。
3. **回退流程是本机的常规路径，不是应急预案**：自己 clone、拷目录、写 lockfile 书签、
   校验，逐步命令和 lockfile 的取法见 [references/manual-install.md](references/manual-install.md)。
4. **标记并登记**（只针对用户点名要装的技能）：
   - 先确认这个技能确实是用户指定要的。不是的话（例如只是 CLI 顺带装的配套技能），让它留在
     `TARGETS` 之外，这一步整段跳过。
   - **依赖技能要单独问，不要替用户决定。** 有些技能的正文只有一句「调用另一个技能」
     （典型例子：`grill-me` 的正文就是 `Call the Skill tool with "grilling".`），装它必须连带
     装被依赖的那个。落地前问一句：**「依赖的 `<B>` 也打 `[自装]` 标记吗？」** 按回答办 ——
     依赖技能既不是用户点名的，也不是 CLI 顺带装的，只有用户能定。同一批里有多个依赖就逐个问。
     顺带告诉用户哪个才是干活的：像 `grill-me`/`grilling` 这种组合，被调用的那个才有逻辑，
     入口那个只是转发；用户若只想留一个，留被依赖的那个。
   - 确定要打标的技能，在 `scripts/mark-user-skills.py` 的 `TARGETS` 加一行
     `"技能目录名": "owner/repo"`，再跑该脚本。脚本幂等，写回前做 YAML 校验；CLI 成功装过
     也要跑一次，因为更新会覆盖掉标记。
   - 在 `~/.agents/user-installed-skills.md` 的清单里加一行：来源、版本或 commit、日期。
5. **收尾校验**：
   - 新写的技能跑 `python "<skill-creator 目录>/scripts/quick_validate.py" <技能目录>`。
   - frontmatter 能被 YAML 解析，`name` 与目录名一致。
   - `npx skills list -g` 能列出它。
   - 技能自带 `--preflight` / `--diagnose` 的话跑一次（只读，能发现缺依赖）。
   - 告诉用户下一次对话轮次生效；界面上没变化就重启 Codex。

## 卸载（被要求时）

- 删技能目录。用 Python 删并先断言绝对路径 —— PowerShell 的 `Remove-Item` 会被策略拒绝。
- CLI 管理的技能（名字在 `~/.agents/.skill-lock.json` 里）顺手删掉那个条目，
  否则 `npx skills update` 之后可能又被装回来。
- 从 `scripts/mark-user-skills.py` 的 `TARGETS`、以及 `~/.agents/user-installed-skills.md`
  的清单里删掉对应行，别留幽灵记录。
- 确认用户是否要保留 `~/.config/last30days/.env` 之类的运行时数据；那些不在技能目录里，
  删技能不会删它们。

## 本机环境约束（决定走哪条路）

这几条是实测的，会直接让"标准做法"失效：

- **node 无法创建子进程**：本会话里 node 执行 `spawn` 一律 `EPERM`，所以
  `npx skills add/update` 一定在 `git clone` 那步挂掉 —— 直接准备回退流程。
- **git 的 schannel TLS 不可用**：必须 `git -c http.sslBackend=openssl ...`，
  否则报 `SEC_E_NO_CREDENTIALS`。网络本身是通的。
- **`~/.agents` 在沙箱工作区之外**：动手前先请求写权限，别假设可写。一次授权可能只覆盖
  一批命令，之后再写又被拒时，重新请求一次即可，不是配置坏了。
- **`apply_patch` 写不了工作区外的路径**：先在可写目录造好文件再复制，或用脚本写。
- **PowerShell 递归 `Remove-Item` 被策略拒绝**：删除改用 Python，并先断言绝对路径。
- **`npx` 需要可写的 npm cache**：设 `$env:npm_config_cache=<可写目录>`，
  否则 npm 报 `EPERM`（它默认写 `%LOCALAPPDATA%\npm-cache`）。
- **本机 Python 默认按本地编码（cp936）读写文本**，而技能文件一律 UTF-8。跑自带脚本要设
  `$env:PYTHONUTF8='1'`，否则 `quick_validate.py` 读 UTF-8 文件会直接
  `UnicodeDecodeError`；自己写的脚本一律显式 `encoding="utf-8"`。
- **`init_skill.py` 因此会把 `agents/openai.yaml` 写成 GBK 字节**：非 ASCII 的
  `display_name` 会变成乱码，连 `apply_patch` 都读不了那个文件。生成后按 UTF-8 重写一遍。

## 不要做

- 不要往不存在的技能目录里塞占位文件、README、changelog。
- 不要给散装文本安装的技能伪造 lockfile 条目 —— `~/.agents/.skill-lock.json` 只登记
  CLI 管理的 GitHub 技能。
- 不要在未确认的情况下改动技能自己的运行时代码或配置，安装就是安装。
