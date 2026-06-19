"""测试 skill 加载器：能解析 frontmatter 和正文、能列出、能拼 prompt。"""

import pytest

from app.skills.loader import build_extraction_prompt, list_skills, load_skill


def test_load_standup_skill():
    skill = load_skill("standup")
    assert skill.name == "standup"
    assert "站会" in skill.description       # description 是触发器
    assert "阻塞" in skill.body              # 正文是抽取规则
    assert skill.meeting_type == "站会"


def test_list_skills_includes_standup():
    names = [s.name for s in list_skills()]
    assert "standup" in names


def test_load_missing_skill_raises():
    with pytest.raises(FileNotFoundError):
        load_skill("不存在的会议类型")


def test_build_prompt_injects_skill_body():
    skill = load_skill("standup")
    prompt = build_extraction_prompt(skill, "张伟今天联调支付模块。")
    assert "站会" in prompt
    assert "宁可漏抽不可错抽" in prompt       # skill 规则被拼进去了
    assert "张伟今天联调支付模块。" in prompt   # 转写也在
