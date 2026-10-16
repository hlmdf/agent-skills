# 手动安装 / 更新（CLI 跑不通时的回退）

`npx skills add` 是本机首选，但它在 node 无法 spawn 子进程的环境里必然失败；
步骤 1 起是完全等价的替代做法，产出与 CLI 安装一致（已用 v3.26.0 的
`skillFolderHash` 逐位验证过）。

前置：请求 `~/.agents` 的写权限；准备一个可写的工作目录（下称 `$base`）。

## 1. 只把技能目录 checkout 出来

```powershell
$repo = 'mvanhorn/last30days-skill'   # owner/repo
$ref  = 'v3.28.0'                     # tag、分支或 commit
$path = 'skills/last30days'           # 技能目录在仓库里的路径
$src  = "$base\src"

git -c http.sslBackend=openssl clone --depth 1 --branch $ref --filter=blob:none --sparse `
    "https://github.com/$repo.git" $src
git -C $src config http.sslBackend openssl      # 关键：见下
git -C $src sparse-checkout set $path
"$src\$path"                                    # 技能内容在这里
git -C $src rev-parse "${ref}:${path}"          # 记下这行 tree hash，第 3 步要用
```

`git -C $src config http.sslBackend openssl` 不能省：稀疏检出会为缺失的 blob
另起一个 git 进程去按需抓取，那次调用看不到 `-c` 参数，会退回到失败的 schannel。

仓库没有 `skills/` 布局（散装技能文本）时，跳过 sparse-checkout，直接把需要的
文件按 `SKILL.md` + `references/` 的布局在 `$base` 里造好。

## 2. 整目录拷贝到落点

目标 `~/.agents/skills/<name>`。已有的同名技能要更新时，按新树为准同步：复制新增和
变更的文件，删掉只存在于旧版本的文件，然后清掉空目录。不要先删整个目录再拷贝，
否则中途失败会留下半成品。

装完清掉运行产物（例如运行过技能脚本产生的 `__pycache__`），让内容与上游树一致。

## 3. 只有 CLI 管理的技能才更新 lockfile

`~/.agents/.skill-lock.json` 里 `skills.<name>.skillFolderHash` 就是第 1 步 `rev-parse`
输出的 tree hash，`updatedAt` 用当前 UTC 时间（形如 `2026-10-16T07:49:11.746Z`）。

判断某个技能是否归 CLI 管：它的名字在不在这份 JSON 里。散装文本安装或自写的技能
不登记，别伪造条目 —— 那会让 `npx skills update` 之后把它当成 GitHub 来源去覆盖。

## 4. 校验（别跳过）

逐文件比对安装结果与 checkout 目录的内容，比对比"目录存在"有意义得多：

```python
import hashlib, pathlib
snap = lambda r: {p.relative_to(r).as_posix(): hashlib.sha1(p.read_bytes()).hexdigest()
                  for p in pathlib.Path(r).rglob("*") if p.is_file()}
src = pathlib.Path(r"<工作目录>\src\skills\<name>")
dst = pathlib.Path.home() / ".agents" / "skills" / "<name>"
a, b = snap(src), snap(dst)
assert a == b, sorted(set(a) ^ set(b)) or [k for k in a if a[k] != b[k]]
print("byte-identical:", len(b), "files")
```

再跑一次 `npx skills list -g` 确认它仍在清单里、`Source:` 字段没变。

## 5. 更新时多做一步

更新既有技能前，记下旧版本号；更新后在
`~/.agents/user-installed-skills.md` 里把"版本/时间"那一格改成新旧对照，
方便回退时知道该装哪个 tag。
