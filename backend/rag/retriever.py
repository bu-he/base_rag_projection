from rag.vectorstore import VectorStore
from config.rag import Settings
from config.logger import logger
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from factory.reranker_factory import create_reranker
# 重排

from langchain_classic.retrievers import ContextualCompressionRetriever
import jieba
import time




class RetrieverService:
      def __init__(self):
            self.vectorstore=VectorStore()
            self.setting=Settings()
            self._ensemble_retriever=self.ensemble_retriever()
            self.reranker=create_reranker()
            
            # 组装完整的检索器
            self.compression_retriever=None if self._ensemble_retriever is None else ContextualCompressionRetriever(
     base_retriever=self._ensemble_retriever,
     base_compressor=self.reranker
)
            
      @staticmethod 
      def chinese_preprocess(text: str):  # 中文分词
                  return list(jieba.cut_for_search(text)) 
      
   
      def ensemble_retriever(self):
            chunk=self.vectorstore.get_all_chunks()
            if not chunk:
                  return None
            vector_retriever=self.vectorstore.get_retriever(self.setting.vector_k)
            bm25_retriever=BM25Retriever.from_documents(chunk,k=self.setting.bm25_k,preprocess_func=self.chinese_preprocess)
            return EnsembleRetriever(
                  retrievers=[vector_retriever,bm25_retriever],
                  weights=self.setting.weights
            )


             

      # 组合重检索器
      def retrieve(self,query:str):
            start_time=time.perf_counter()
            if self._ensemble_retriever is None or self.compression_retriever is None:
                  return "没有上传任何文件，请先上传文件"

            result=self.compression_retriever.invoke(query)
            logger.info(f"检索耗时: {time.perf_counter() - start_time:.2f}秒")
            content=""
            for i ,doc in enumerate(result,start=1):
                   content+=f"参考资料{i}:{doc.page_content}\n\n"
            
            logger.info(f"检索后整理资料耗时: {time.perf_counter() - start_time:.2f}秒")
            return content
      # 重建bm25检索器
      def rebuild_bm25(self):
           chunk=self.vectorstore.get_all_chunks()
           if not chunk:
                  logger.info("向量库为空，跳过重建bm25检索器")
                  return
           self.bm25_retriever=BM25Retriever.from_documents(chunk,k=self.setting.bm25_k,preprocess_func=self.chinese_preprocess) 
           
           if self._ensemble_retriever is not None:
                 
                self._ensemble_retriever.retrievers[1]=self.bm25_retriever
           
           else:
                
                 self._ensemble_retriever = self.ensemble_retriever()
                 self.compression_retriever = ContextualCompressionRetriever(
                    base_retriever=self._ensemble_retriever,
                    base_compressor=self.reranker,
                 )
                 self.bm25_retriever=self.bm25_retriever







import threading

_retriever_service = None
_lock = threading.Lock()

def get_retriever_service():
    global _retriever_service
    if _retriever_service is None:
        with _lock:
            if _retriever_service is None:
                _retriever_service = RetrieverService()
    return _retriever_service

def is_ready() -> bool:
    return _retriever_service is not None
    






       
      

































