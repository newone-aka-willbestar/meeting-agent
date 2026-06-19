"""Skill 加载器：读取 skills/ 下的 SKILL.md，解析成 (name, description, body)。

Skill = 一个 markdown 文件 = YAML 头（元信息）+ 正文（给 agent 的指令）。
抽取 agent 按会议类型 load 对应 skill，把正文拼进给 LLM 的 prompt。

frontmatter 这里手写极简解析（key: value），不引入 pyyaml 依赖。"""

from dataclasses import dataclass
from pathlib import Path

# 仓库根下的 skills/ 目录（loader.py 在 backend/app/skills/ 下，往上四层到仓库根）
SKILLS_DIR = Path(__file__).resolve().parents[3] / "skills"


@dataclass
class Skill:
    name: str
    description: str   # 决定"何时加载"的触发器
    body: str          # 拼进 prompt 的抽取规则
    meeting_type: str = ""


def _parse(text: str, fallback_name: str) -> Skill:
    lines = text.splitlines()
    front: dict[str, str] = {}
    body = text.strip()

    # 识别开头的 --- frontmatter --- 块
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            for line in lines[1:end]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    front[key.strip()] = value.strip()
            body = "\n".join(lines[end + 1:]).strip()

    return Skill(
        name=front.get("name", fallback_name),
        description=front.get("description", ""),
        body=body,
        meeting_type=front.get("meeting_type", ""),
    )


def load_skill(name: str, skills_dir: Path = SKILLS_DIR) -> Skill:
    """按名字加载一个 skill（name 对应 skills/<name>.md）。"""
    path = skills_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"skill 不存在: {path}")
    return _parse(path.read_text(encoding="utf-8"), fallback_name=name)


def list_skills(skills_dir: Path = SKILLS_DIR) -> list[Skill]:
    """列出所有可用 skill（agent 据 description 判断该用哪个）。"""
    if not skills_dir.exists():
        return []
    return [
        _parse(p.read_text(encoding="utf-8"), fallback_name=p.stem)
        for p in sorted(skills_dir.glob("*.md"))
    ]


def build_extraction_prompt(skill: Skill, transcript: str) -> str:
    """演示：把 skill 正文拼进抽取 prompt。Phase 2 的抽取 agent 会用类似逻辑。"""
    return (
        "你是会议纪要抽取助手。请从转写中抽取 决策/待办/风险/待议。\n"
        f"本场会议类型：{skill.meeting_type or skill.name}。遵循以下专项规则：\n"
        "----- 规则开始 -----\n"
        f"{skill.body}\n"
        "----- 规则结束 -----\n\n"
        f"会议转写：\n{transcript}\n"
    )
