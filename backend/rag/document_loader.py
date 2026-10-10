from utils.file_handler  import pdf_loader,text_loader,get_file_md5_value

from config.rag import Settings
from config.logger import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from utils.file_handler import get_file_path
from langchain_core.documents import Document



setting=Settings()

class DocumentService:
      def __init__(self):
            self.data_dir=setting.data_dir
            self.text_splitter=RecursiveCharacterTextSplitter(
                  chunk_size=setting.chunk_size,
                  chunk_overlap=setting.chunk_overlap,
                  separators=setting.separators
            )

      def scan_dir(self,dir_path):
            dir_path=Path(dir_path)
            if not dir_path.is_dir():
                  logger.error(f"文件夹不存在：{dir_path}")
                  return []
            return [file for file in dir_path.iterdir() if file.is_file()]
      
      

      # def is_file_processed(self,file_path):
      #       md5=get_file_md5_value(file_path)
      #       if md5 is None:
      #              logger.error(f"文件{file_path}不存在或处理md5失败")
      #              return None,None
      #       processed=check_md5_hex(md5)
            
      #       return processed,md5
             

      def load_file(self,file_path):
            if file_path.suffix==".pdf":
                  return pdf_loader(file_path)
            elif file_path.suffix==".txt":
                  return text_loader(file_path)
            else:
                  logger.error(f"不支持的文件类型：{file_path}")
                  return None
            

      def add_metadata(self,file_path:Path,documents:list[Document],md5:str):
           
             for index,document in enumerate(documents):
                  document.metadata["file_name"]=str(file_path.name)
                  document.metadata["file_path"]=str(get_file_path(file_path))
                  document.metadata["md5"]=md5   
                  document.metadata["chunk_id"]=str(file_path.name)+"_"+str(index)  
      
      


      def split_documents(self,documents):
            return self.text_splitter.split_documents(documents)

      def process_document(self,file_path):
       try:
            
            
            
            # is_processed,md5=self.is_file_processed(file_path)
            
            # if is_processed:
            #       logger.info(f"文件{file_path}已处理")
            #       return None,md5
                  
            md5=get_file_md5_value(file_path)
            if md5 is None:
                  logger.error(f"文件{file_path}不存在或处理md5失败")
                  return None,None
            documents=self.load_file(file_path)
            
            if not documents :
                  logger.error(f"加载文件{file_path}失败或返回空文档")
                  return None,None
            chunk=self.split_documents(documents)
            if not chunk:
                  logger.error(f"分割文件{file_path}的文档失败或返回空文档")
                  return None,None
            
            
            self.add_metadata(file_path,chunk,md5)
            logger.info(f"添加文件{file_path}的元数据完成\n\n")
            
            return chunk,md5
            

       except Exception as e:
            logger.error(f"处理文件{file_path}时出错：{e}")
            return None,None

            

if __name__ == "__main__":
      loader=DocumentService() 
      # files=loader.scan_dir(setting.data_dir)
      # for file in files:
           
      
      #       chunks,md5=loader.process_document(file)
      #       if chunks is None:
      #             continue
      #       save_md5_hex(file,md5)
      #       logger.info(f"文件{file}处理完成，md5值：{md5}")
      
