"""Tag self-installed skills so they stand out from the bundled ones.

Adds a `[自装] ` prefix to the SKILL.md frontmatter `description`, which is the
field hosts display in their skill lists. Idempotent: a skill already carrying
the tag is skipped. Frontmatter is re-parsed with PyYAML after each edit, and
the script refuses to write anything that would not parse.
"""

import os
import pathlib
import sys

import yaml

TAG = "[自装] "
# 用户级技能目录。默认 ~/.agents/skills，可用 USER_SKILLS_ROOT 覆盖。
SKILLS_ROOT = pathlib.Path(
    os.environ.get("USER_SKILLS_ROOT") or pathlib.Path.home() / ".agents" / "skills"
)
TARGETS = {
    "last30days": "mvanhorn/last30days-skill",
    "deeppapernote": "917Dhj/DeepPaperNote",
    "paper-reading-zh": "FeijiangHan/PaperForge",
    "install-skill": "本地自写（非 GitHub）",
    "grill-me": "mattpocock/skills",
}

# UI 显示名的唯一来源：显示名一律写成 `[自装] ` + 这里的名字。
# 名字用英文/拉丁字母，标记只用 `[自装] ` 前缀。改显示名就改这里，再重跑本脚本。
DISPLAY_NAMES = {
    "last30days": "Last 30 Days",
    "deeppapernote": "DeepPaperNote",
    "paper-reading-zh": "PaperForge",
    "install-skill": "Install Skill",
    "grill-me": "Grill Me",
}
UI_EXTRAS = {
    "paper-reading-zh": {
        "short_description": "用中文深度精读论文：重建作者思路、讲清方法、评估证据、找出脆弱假设、提出 follow-up idea。",
        "default_prompt": "用 $paper-reading-zh 深度精读这篇论文。",
    },
}


def tag_description(text: str) -> tuple[str, bool]:
    """Return (new_text, changed). Raises on unexpected frontmatter shape."""
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        raise ValueError("file does not start with YAML frontmatter")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")

    desc = next(i for i in range(1, end) if lines[i].startswith("description:"))

    if lines[desc].rstrip("\r\n").rstrip().endswith((">", "|")):
        # Folded/literal block: description text starts on the next line.
        first = desc + 1
        while not lines[first].strip():
            first += 1
        body = lines[first]
        indent = body[: len(body) - len(body.lstrip())]
        if body.lstrip().startswith(TAG):
            return text, False
        lines[first] = f"{indent}{TAG}{body.lstrip()}"
    else:
        if TAG in lines[desc]:
            return text, False
        raw = lines[desc].rstrip("\r\n")
        eol = lines[desc][len(raw) :]
        stripped = raw[len("description:") :].strip()
        quoted = len(stripped) > 1 and stripped[0] in "\"'" and stripped[-1] == stripped[0]
        if quoted and stripped[0] == '"':
            # Keep the author's double quoting; insert the tag after the opening quote.
            lines[desc] = f'description: "{TAG}{stripped[1:]}{eol}'
        else:
            # Re-emit through PyYAML: a plain scalar starting with "[" is invalid YAML.
            value = TAG + (stripped[1:-1] if quoted else stripped)
            dumped = yaml.safe_dump(
                {"description": value},
                allow_unicode=True,
                default_flow_style=False,
                width=10**9,
            )
            lines[desc] = dumped.rstrip("\n") + eol

    return "".join(lines), True


def tag_ui(path: pathlib.Path, name: str) -> str:
    """Make interface.display_name match `[自装] ` + DISPLAY_NAMES[name]."""
    desired = f"{TAG}{DISPLAY_NAMES[name]}" if name in DISPLAY_NAMES else None

    if not path.is_file():
        interface = {"display_name": desired or f"{TAG}{name}"}
        interface.update(UI_EXTRAS.get(name, {}))
        path.parent.mkdir(parents=True, exist_ok=True)
        # Match the upstream style: one double-quoted value per line, no folding.
        lines = ["interface:"]
        lines += [f'  {key}: "{value}"' for key, value in interface.items()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return "created"

    lines = path.read_text(encoding="utf-8").splitlines()
    interface_at = next((i for i, l in enumerate(lines) if l.strip() == "interface:"), None)
    display_at = next(
        (i for i, l in enumerate(lines) if l.strip().startswith("display_name:")), None
    )

    if display_at is not None:
        raw = lines[display_at]
        indent = raw[: len(raw) - len(raw.lstrip())]
        current = raw.split(":", 1)[1].strip().strip("\"'")
        if desired is not None and current != desired:
            lines[display_at] = f'{indent}display_name: "{desired}"'
            result = "renamed"
        elif desired is None and not current.startswith(TAG):
            lines[display_at] = f'{indent}display_name: "{TAG}{current}"'
            result = "tagged"
        else:
            return "already ok"
    else:
        if interface_at is None:
            lines.append("interface:")
            interface_at = len(lines) - 1
        fallback = desired or (TAG + name)
        lines.insert(interface_at + 1, f'  display_name: "{fallback}"')
        result = "tagged"

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def untag_description(text: str) -> tuple[str, bool]:
    """Strip a `[自装] ` prefix from a SKILL.md description (inverse of tagging)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text, False
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return text, False
    desc = next((i for i in range(1, end) if lines[i].startswith("description:")), None)
    if desc is None:
        return text, False

    head = lines[desc].rstrip("\r\n")
    eol = lines[desc][len(head) :]
    value = head[len("description:") :]
    if value.strip() in (">", "|", ">-", "|-", ">+", "|+"):
        body = desc + 1
        while body < end and not lines[body].strip():
            body += 1
        if body >= end or TAG not in lines[body]:
            return text, False
        lines[body] = lines[body].replace(TAG, "", 1)
        return "".join(lines), True

    if TAG not in value:
        return text, False
    lines[desc] = "description:" + value.replace(TAG, "", 1) + eol
    return "".join(lines), True


def untag_ui(path: pathlib.Path) -> str:
    """Strip the tag from interface.display_name, if it is there."""
    if not path.is_file():
        return "no yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    at = next((i for i, l in enumerate(lines) if l.strip().startswith("display_name:")), None)
    if at is None:
        return "no display_name"
    raw = lines[at]
    indent = raw[: len(raw) - len(raw.lstrip())]
    value = raw.split(":", 1)[1].strip().strip("\"'")
    if not value.startswith(TAG):
        return "clean"
    lines[at] = f'{indent}display_name: "{value[len(TAG) :]}"'
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "untagged"


def main() -> int:
    for name, source in TARGETS.items():
        skill_dir = SKILLS_ROOT / name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            print(f"SKIP  {name}: no SKILL.md at {skill_md}")
            continue

        new_text, changed = tag_description(skill_md.read_text(encoding="utf-8"))
        data = yaml.safe_load(new_text.split("---", 2)[1])
        assert isinstance(data, dict), f"{name}: frontmatter is not a mapping"
        assert data["name"] == name, f"{name}: frontmatter name is {data['name']!r}"
        description = " ".join(str(data["description"]).split())
        assert description.startswith(TAG), f"{name}: description tag missing"
        if changed:
            skill_md.write_text(new_text, encoding="utf-8")

        ui_path = skill_dir / "agents" / "openai.yaml"
        ui_result = tag_ui(ui_path, name)
        ui = yaml.safe_load(ui_path.read_text(encoding="utf-8"))
        display = ui["interface"]["display_name"]
        assert display.startswith(TAG), f"{name}: ui display_name tag missing"

        print(f"{name:18} description={'tagged' if changed else 'ok':6} ui={ui_result}")
        print(f"{'':18} display_name={display!r}  source={source}")

    # 名单之外的技能不该带标记：发现残留就清掉。
    for skill_dir in sorted(p for p in SKILLS_ROOT.iterdir() if p.is_dir()):
        if skill_dir.name in TARGETS or not (skill_dir / "SKILL.md").is_file():
            continue
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        if TAG in text:
            cleaned, changed = untag_description(text)
            if changed:
                front = yaml.safe_load(cleaned.split("---", 2)[1])
                assert TAG not in str(front["description"]), skill_dir.name
                (skill_dir / "SKILL.md").write_text(cleaned, encoding="utf-8")
                print(f"UNTAG {skill_dir.name:18} description")
        if untag_ui(skill_dir / "agents" / "openai.yaml") == "untagged":
            print(f"UNTAG {skill_dir.name:18} display_name")
    return 0


if __name__ == "__main__":
    sys.exit(main())
