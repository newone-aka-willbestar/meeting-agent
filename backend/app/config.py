"""集中式配置：把 .env / 环境变量读成一个带类型校验的对象。

好处：全项目只有这一处碰环境变量，别处直接 import settings 用；
拼错变量名、类型不对会在启动时就报错，而不是运行到一半才崩。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 从项目根的 .env 读；多出来的变量忽略（前端/其他服务的也写在同一个 .env）
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---- 基础设施地址 ----
    database_url: str = "postgresql://meeting:meeting_pw@localhost:5432/meeting"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # ---- ASR（语音转写）----
    # provider 决定用哪个实现：dashscope（真·阿里云）/ mock（测试用假数据）
    asr_provider: str = "mock"
    asr_api_key: str = ""

    # ---- 检索：Embedding / Rerank ----
    embedding_provider: str = "mock"   # mock / dashscope
    rerank_provider: str = "mock"      # mock / dashscope
    # 阿里云百炼 key（embedding/rerank 用；通常和 ASR_API_KEY 是同一个）
    dashscope_api_key: str = ""

    # ---- LLM（抽取 / 纪要 / 周报）----
    llm_provider: str = "mock"         # mock / dashscope（通义 Qwen）
    llm_model: str = "qwen-plus"
    llm_api_key: str = ""              # 没填则退回 dashscope_api_key / asr_api_key

    # ---- 上传文件落盘目录 ----
    storage_dir: str = "storage"


@lru_cache
def get_settings() -> Settings:
    """缓存成单例：整个进程只读一次 .env、只建一个 Settings 对象。"""
    return Settings()
