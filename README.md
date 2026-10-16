# agent-skills

我自己的 Codex 技能与安装约定。

## 里面有什么

### `skills/install-skill`

把 Agent Skill 装到本机 Codex 用户级目录（`~/.agents/skills`）的完整流程，包括：

- **来源判断**：GitHub / GitLab / Gitee / 压缩包 / 网页 / 本地目录 / 只有一个技能名 / 只描述了想要的能力，各自的取内容路径。
- **首选官方 CLI，失败走回退**：`npx skills@latest add <owner>/<repo> -g`；跑不通时自己 clone（稀疏检出技能目录）、整目录拷贝、给 `.skill-lock.json` 写 tree hash 书签、逐文件哈希校验。
- **本机标记约定**：只有用户明确指定安装的技能才在描述前缀和 UI 显示名上加 `#自装 `；依赖技能要不要打标由用户逐个决定；不在名单上的残留标记会被自动清掉。
- **环境约束清单**（Windows + Codex 沙箱实测）：node 无法创建子进程导致 CLI 必然失败、git 需要 `http.sslBackend=openssl`、`apply_patch` 写不了工作区外路径、`~/.agents` 需要单独授权且授权会过期、npm 需要重定向 cache、Python 默认按本地编码处理文本。

## 安装

```bash
npx skills@latest add hlmdf/agent-skills --skill=install-skill -g -a codex
```

安装后，技能落在 `~/.agents/skills/install-skill`（Codex 的用户级技能目录）。

## 结构

```text
skills/
└── install-skill/
    ├── SKILL.md                     流程本身
    ├── agents/openai.yaml           桌面端 UI 显示名
    ├── references/manual-install.md 回退安装的逐步命令与 lockfile 取法
    └── scripts/mark-user-skills.py  标记脚本（幂等，双向强制）
```

## 说明

`scripts/mark-user-skills.py` 顶部的 `TARGETS` 是「用户指定安装的技能」名单，里面是我本机的实际列表，换机器时按需改。脚本会跳过不存在的技能，所以直接跑不会出错。

标记（`#自装 `）是本机约定，用来把自己的技能和宿主自带的区分开；仓库里保存的是未打标版本，本机由脚本自动打上。
