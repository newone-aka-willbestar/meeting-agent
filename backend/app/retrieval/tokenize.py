"""中文分词：BM25 和 mock embedding 共用。

英文按空格就能分词，中文不行（字之间没空格），所以要"分词"。
用 jieba（纯 Python，无重型依赖）。这是中文 NLP 的基本功，面试可讲。"""

import jieba


def tokenize(text: str) -> list[str]:
    """把一段文本切成词列表，去掉空白 token。"""
    return [t for t in jieba.lcut(text) if t.strip()]
