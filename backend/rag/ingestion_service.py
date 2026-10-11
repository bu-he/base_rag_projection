from rag.document_loader import DocumentService
from rag.vectorstore import VectorStore
from config.logger import logger
from config.rag import Settings
from pathlib import Path
from rag.retriever import get_retriever_service

setting=Settings()



class IngestionService:
     def __init__(self):
          self.document_loader=DocumentService()
          self.vectorstore=VectorStore()
  
     def check_is_need_update(self,current_md5:str,stored_md5:str,file_path:Path):
        """
        检查文件是否需要更新
        """
       
       
        if current_md5==stored_md5:
             logger.info(f"文件{file_path}的元数据MD5未变动,不需要更新")
             return False  # 文件未变动,不需要更新
        else:
             logger.info(f"文件{file_path}的元数据MD5变动,需要重新更新")
             return True  # 文件变动,需要重新更新
        
     def clear_deleted_file(self):
           all_stored_file_path=self.vectorstore.get_all_stored_file_path()
           if not  all_stored_file_path:
               logger.info("向量数据库中没有文件记录,无需删除")
               return False
           all_data_file_path={str(file) for file in self.document_loader.scan_dir(setting.data_dir)}
           deleted_file=all_stored_file_path-all_data_file_path
           if not deleted_file:
               logger.info("向量数据库中没有删除的文件记录,无需删除")
               return False
           for path in deleted_file:
               logger.info(f"发现删除的文件记录{path},开始删除向量数据库记录")
               ids=self.vectorstore.get_ids_by_file_path(path)
               if ids:
                    self.vectorstore.to_ids_delete(ids=ids)
                    logger.info(f"删除文件{path}的 {len(ids)} 条记录")
           return True  # 为bm25的重建做判断
                    
              
              

           
           
     def ingest(self, dir_path: Path = setting.data_dir):

          file_list = self.document_loader.scan_dir(dir_path)
          changed=False
          for file_path in file_list:
              result=self.ingest_file(file_path)
              changed=result in ["added","updated"] or changed
              
          changed=self.clear_deleted_file() or changed
          if changed:
                get_retriever_service().rebuild_bm25()
                logger.info("文件变动,bm25模型已重建")

         

           
               
          
     def ingest_file(self,file_path:Path):
            
            if not file_path.exists():
               logger.error(f"文件{file_path}不存在")
               return "failed"
            chunk,current_md5=self.document_loader.process_document(file_path)
            if chunk is None:
                     logger.error(f"文件{file_path}处理失败，跳过")
                     return "failed"
            try:   
                 stored_md5=self.vectorstore.get_metadata_md5(file_path)
                 
               #  说明是传入的新文件，重新切分向量化存入
                 if stored_md5 is  None:
                         
                             self.vectorstore.add_documents(chunk)
                             logger.info(f"用户传入了新文件{file_path}的文档已添加到向量数据库")
                             return "added"  # 为bm25的重建做判断
                          
            
                         
                 elif  self.check_is_need_update(current_md5,stored_md5,file_path): 
                             
                        self.vectorstore.update_chroma_record(file_path,chunk)
                        return "updated" # 为重建bm25做判断
                        
                 else: 
                        logger.info(f"文件{file_path}的元数据MD5未变动,跳过")
                        return "skipped"

                      
                 
                    
            except Exception as e:
                         logger.exception(f"处理文件{file_path}失败：{e}")
                         return "failed"
            
            
               
          
if __name__ == "__main__":
     #   setting=Settings()
       ingestion=IngestionService()
       ingestion.ingest()

     #   ingestion.vectorstore.add_metadata()

     #   service=IngestionService()
     #   service.ingest(get_file_path("data/故障排除.txt"))
     #   service.vectorstore.delete_chroma_record(get_file_path("data/故障排除.txt"))
     #   service.ingest(get_file_path("data/故障排除.txt"))
   
