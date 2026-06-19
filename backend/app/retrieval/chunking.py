"""切块（chunking）：把整段转写切成一段段适合检索的"块"。

为什么切：① 检索要定位到"具体哪一段"，而不是整篇；
② embedding 模型对过长文本效果差、也有长度上限。
块太大→检索不精准；块太小→丢上下文。所以要折中，并让相邻块"重叠(overlap)"
一点，避免把一句关键的话从中间切断、两边都丢了语境。"""

import re

# 按中文句末标点（和换行）切句，标点保留在句尾
_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def chunk_text(text: str, max_chars: int = 200, overlap: int = 40) -> list[str]:
    """把文本切成若干块：贪心地把句子塞进当前块，超过 max_chars 就另起一块，
    新块开头带上一块末尾 overlap 个字符作为重叠上下文。"""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # 当前块非空、再加这句会超长 → 先收下当前块，开新块
        if current and len(current) + len(sentence) > max_chars:
            chunks.append(current)
            current = current[-overlap:] if overlap else ""
        current += sentence

    if current.strip():
        chunks.append(current)
    return chunks
