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
            self.vector_retriever=self.vectorstore.get_retriever(self.setting.vector_k)
            self.bm25_retriever=BM25Retriever.from_documents(self.vectorstore.get_all_chunks(),k=self.setting.bm25_k,preprocess_func=self.chinese_preprocess)
            self._ensemble_retriever=EnsembleRetriever(
                  retrievers=[self.vector_retriever,self.bm25_retriever],
                  weights=self.setting.weights
            )
            self.reranker=create_reranker()
            
            # 组装完整的检索器
            self.compression_retriever=ContextualCompressionRetriever(
     base_retriever=self._ensemble_retriever,
     base_compressor=self.reranker
)
            
      @staticmethod 
      def chinese_preprocess(text: str):
           return list(jieba.cut_for_search(text)) 
      
   
         

      # 组合重检索器
      def retrieve(self,query:str):
            start_time=time.perf_counter()
            result=self.compression_retriever.invoke(query)
            logger.info(f"检索耗时: {time.perf_counter() - start_time:.2f}秒")
            content=""
            for i ,doc in enumerate(result,start=1):
                   content+=f"参考资料{i}:{doc.page_content}\n\n"
            
            logger.info(f"检索后整理资料耗时: {time.perf_counter() - start_time:.2f}秒")
            return content

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
    
if __name__ == "__main__":
      rs=RetrieverService()
      # content=retriever_service.retrieve("为什么机器人突然找不到家了？")
      # print(content)
 
      # content=retriever_service.distance_score_filter("我现在处于什么阶段？")
      # print(content)



# 测试
      # retriever_service.retrieve("我现在处于什么阶段？")


# 测试召回率
      # vector_result=rs.vector_retriever.invoke("床和沙发底下比较矮，机器人能钻进去吗")
      # print(f"矢量检索结果:{vector_result}\n\n")
      # bm25_result=rs.bm25_retriever.invoke("床和沙发底下比较矮，机器人能钻进去吗")
      # print(f"BM25检索结果:{bm25_result}\n\n")
      # ensemble_result=rs._ensemble_retriever.invoke("床和沙发底下比较矮，机器人能钻进去吗")
      # print(f"混合检索结果:{ensemble_result}\n\n")
      compression_result=rs.compression_retriever.invoke("床和沙发底下比较矮，机器人能钻进去吗")
      print(f"重排检索结果:{compression_result}\n\n")
      result=rs.retrieve("床和沙发底下比较矮，机器人能钻进去吗")
      print(result)





       
      

































