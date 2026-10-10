from config.logger import logger
from factory.model_factory import embed_model
from langchain_chroma import Chroma
from config.rag import Settings
from langchain_core.documents import Document

from pathlib import Path
setting=Settings()




class VectorStore:
    def __init__(self):
           self.embeddings=embed_model()
           
           self.vectorstore=Chroma(embedding_function=self.embeddings,
                  persist_directory=setting.persist_directory,
                  collection_name=setting.collection_name)

    # 获取元数据MD5  可以用于调试和判断

    def get_metadata_md5(self, file_path: str | Path) -> str | None:
     result = self.vectorstore.get(
        where={"file_path": str(file_path)},
        include=["metadatas"]
    )
  
#     没查到，返回 None
     if not result["ids"]:
        return None
    
    # 查到了，取第一条的 md5
     return result["metadatas"][0].get("md5")
     
    def get_all_chunks(self):
        result=self.vectorstore.get(include=["documents","metadatas"])
        ids=result.get("ids",[])
        documents=result.get("documents",[])
        metadatas=result.get("metadatas",[])
        #    return chunks
        list=[]
        for i in range(len(ids)):
           chunk=Document(
                  page_content=documents[i],
                  metadata=metadatas[i]
           )
           list.append(chunk)
        return list
          


    def add_documents(self,documents:list[Document]):
                 if not documents:
                        logger.error(f"添加的文档列表为空")
                        return
                 try:
                     logger.info(f"开始添加{len(documents)}条文档到向量数据库")
                     self.vectorstore.add_documents(documents)
                        
                     logger.info(f"已添加{len(documents)}条文档到向量数据库")
                    

                 except Exception as e:
                     logger.exception(f"添加文档到向量数据库失败：{e}")
                     raise
    def get_ids_by_file_path(self,file_path:Path | str) -> list[str]:
         result=self.vectorstore.get(where={"file_path": str(file_path)})
         if not result["ids"]:
            return []
         return result["ids"]
    
    def to_ids_delete(self,ids:list[str]):
         self.vectorstore.delete(ids=ids)
        
       
     
    def update_chroma_record(self,file_path:Path | str,documents:list[Document]):
       old = self.vectorstore.get(where={"file_path": str(file_path)})
       if old["ids"]:
            # 删除旧md5的向量数据库记录
            self.to_ids_delete(ids=old["ids"]) 
            logger.info(f"已删除文件{file_path}的 {len(old['ids'])} 条旧记录")
             
           
         
           # 添加新的md5的向量数据库记录
       self.add_documents(documents)
       logger.info(f"需要更新的文件{file_path}已重新写入到向量数据库")
      
      
    def  get_all_stored_file_path(self) -> set[str]:
         result=self.vectorstore.get(include=["metadatas"])
         metadatas=result.get("metadatas",[])
         all_stored_file_path={m["file_path"] for m in metadatas}
         return all_stored_file_path
   
            
    def get_retriever(self,k:int | None =setting.vector_k):


          return  self.vectorstore.as_retriever(k=k)

    
    

  
if __name__ == "__main__":
    
      vectorstore=VectorStore()
   
      result=vectorstore.distance_search("我现在处于什么阶段？")
      print(result)

