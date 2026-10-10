
from config.rag import Settings
from config.logger import logger

setting=Settings()

# factory/reranker_factory.py 里新增
from langchain_core.documents import BaseDocumentCompressor, Document
from typing import Sequence, Optional
from langchain_core.callbacks import Callbacks

class DashScopeReranker(BaseDocumentCompressor):
    """DashScope 文本重排器：自己封装，替代弃用的 langchain_community 版"""
    model: str = "qwen3.7-text-rerank"
    top_n: int = 3
    api_key: str = ""

    def compress_documents(self, documents: Sequence[Document], query: str,
                           callbacks: Optional[Callbacks] = None) -> Sequence[Document]:
        from dashscope import TextReRank
        resp = TextReRank.call(
            model=self.model, query=query,
            documents=[d.page_content for d in documents],
            top_n=self.top_n, api_key=self.api_key,
        )
        if resp.status_code != 200 or not resp.output:
            raise RuntimeError(f"DashScope rerank 失败: {resp.code} {resp.message}")   # ← 错误不再被吞
        return [
            Document(
                page_content=documents[r.index].page_content,
                metadata={**documents[r.index].metadata, "relevance_score": r.relevance_score},
            )
            for r in resp.output.results   # API 已按相关性降序排好
        ]


def create_local_reranker():
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    from langchain_classic.retrievers.document_compressors import CrossEncoderReranker

    _cross_encoder=HuggingFaceCrossEncoder(model_name=setting.cross_encoder_model_name)
    logger.info(f"创建本地重排器，模型名称：{setting.cross_encoder_model_name}，top_n：{setting.reranker_top_n}")
    return CrossEncoderReranker(
                  model=_cross_encoder,
                  top_n=setting.reranker_top_n
            )

def create_api_reranker():
    return DashScopeReranker(
        model=setting.rerank_model_name,      # 加进 Settings，别硬编码
        top_n=setting.reranker_top_n,         # 用统一的 top_n，别写死 2
        api_key=setting.dashscope_api_key,
    )


def create_reranker():
    """
    根据配置创建重排器
    返回一个 LangChain 的 BaseDocumentCompressor（能用于 ContextualCompressionRetriever）
    """
    reranker_type = setting.reranker_type
    
    if reranker_type == "local":
        return create_local_reranker()
    elif reranker_type == "api":
        return create_api_reranker()
    else:
        raise ValueError(f"不支持的重排类型：{reranker_type}，可选：local / api")

