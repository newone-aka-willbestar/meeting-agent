"""用通义语音合成（Sambert TTS）生成一段示例会议录音，喂给 ASR 跑真实链路。

跑法（需先在 .env 填好 DASHSCOPE_API_KEY）：
    backend\\.venv\\Scripts\\python.exe scripts\\gen_sample_audio.py
产出：samples/standup_demo.wav（16k 单声道 wav）
"""

import pathlib
import sys

import dashscope
from dashscope.audio.tts import SpeechSynthesizer

# 一段真实风格的站会脚本：含 决策 / 待办(负责人+ddl) / 风险，便于演示抽取
SCRIPT = (
    "好，我们开始今天的站会。先同步几件事。"
    "第一，关于新版本的上线时间，经过讨论我们决定推迟到下周三正式发布，给测试多留两天。"
    "第二，支付模块的联调还没完成，张伟你这边负责，争取这周五之前搞定。"
    "第三，这里有个风险要提醒大家，第三方支付接口的稳定性我们还没有充分验证过，"
    "如果它出问题可能会影响整个上线节奏，需要持续关注。"
    "另外李娜跟进一下客户那边的反馈，下周一之前给个汇总。今天就先到这里。"
)


def _load_key() -> str:
    env = pathlib.Path(__file__).resolve().parents[1] / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("DASHSCOPE_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    sys.exit("❌ 请先在 .env 填 DASHSCOPE_API_KEY")


def main() -> None:
    dashscope.api_key = _load_key()
    out = pathlib.Path(__file__).resolve().parents[1] / "samples" / "standup_demo.wav"
    out.parent.mkdir(parents=True, exist_ok=True)

    result = SpeechSynthesizer.call(
        model="sambert-zhichu-v1",
        text=SCRIPT,
        sample_rate=16000,
        format="wav",
    )
    audio = result.get_audio_data()
    if audio is None:
        sys.exit(f"❌ 合成失败：{result.get_response()}")
    out.write_bytes(audio)
    print(f"✅ 已生成示例录音：{out}（{len(audio) // 1024} KB）")


if __name__ == "__main__":
    main()
