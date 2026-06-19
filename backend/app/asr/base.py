"""ASR 供应商的统一接口。

设计意图：业务代码只依赖这个抽象，不关心背后是阿里云、本地模型还是假数据。
换供应商 = 加一个子类 + 改一个环境变量，业务代码一行不动。
这是「依赖倒置 / 面向接口编程」在项目里的一个具体落点。"""

from abc import ABC, abstractmethod


class ASRProvider(ABC):
    """所有 ASR 实现都要继承它，并实现 transcribe。"""

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """把一个本地音频文件转成纯文本转写。

        入参：audio_path —— 本地音频文件路径
        出参：转写后的整段文本（MVP 不做说话人分离，故只返回一段 str）
        """
        raise NotImplementedError
