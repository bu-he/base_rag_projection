from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from utils.filepath import get_file_base
BASE_DIR=get_file_base()


class Settings(BaseSettings):
    """
    配置类
    """
 

    # model_name
    
    embedding_model_name:str="qwen3.7-text-embedding-flash"
    
    
    #语言模型配置 默认配置
    llm_provider:str="dashscope"  # dashscope or deepseek
    max_tokens:int=4096
    temperature:float=0.5
    
    # dashscope
    dashscope_model_name:str="qwen3.7-flash-2026-07-15"
    dashscope_api_key:str
    dashscope_base_url:str="https://dashscope.aliyuncs.com/compatible-mode/v1"

    # deepseek
    deepseek_model_name:str="deepseek-v4.1-flash"
    deepseek_api_key:str
    deepseek_base_url:str="https://api.deepseek.com"

    # 嵌入模型
    check_embedding_ctx_length:bool=False
    embedding_batch_size:int=100
    
    # 重排api模型配置
    rerank_model_name:str="qwen3.7-text-rerank"
    reranker_type:str="api"
    
    # rag
    chunk_size:int=200
    chunk_overlap:int=30

    # 分隔符
    separators:list=["\n\n","\n","?","。",""]
    # 数据目录
    data_dir:Path=BASE_DIR/"data"
  
    # vectorstore
    persist_directory:Path=BASE_DIR/"chroma"/"chroma_db"
    collection_name:str="rag_collection"
    # 检索
        # 用于向量j检索的k值
    vector_k:int=6
    # bm25检索的k值
    bm25_k:int=6
    # 重排top_n（实验记录：top_n=5 时 Hit@5=Hit@3=90%，第4-5位无增益，维持 3）
    reranker_top_n:int=3
    # 混合检索权重
    weights:list=[0.6,0.4]
    # cross_encoder模型
    cross_encoder_model_name:str="BAAI/bge-reranker-v2-m3"
   
    # 认证密钥
    secret_key:str
    ALGORITHM:str="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 60 * 24   

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
if __name__=="__main__":
     print("BASE_DIR:",BASE_DIR)
    


