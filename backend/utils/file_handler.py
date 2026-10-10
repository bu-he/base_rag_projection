from langchain_community.document_loaders import PyMuPDFLoader,TextLoader
from pathlib import Path
from config.logger import logger
import hashlib

from utils.filepath import get_file_path


def get_file_md5_value(file_path):
        
        p=Path(file_path)
        if not  p.is_file():
                logger.error(f"文件不存在：{file_path}")
                return None
        chunk_size=4024
        md5=hashlib.md5()
        with open(file_path,"rb") as f :
                chunk=f.read(chunk_size)
                while chunk:
                        md5.update(chunk)
                        chunk=f.read(chunk_size)
                md5_result=md5.hexdigest()
                return md5_result

                
# def check_md5_hex(md5_for_check:str):
#         md5_path=get_file_path("md5.txt")
#         if not Path(md5_path).exists():
#             open(md5_path,"w",encoding="utf-8").close()
#             logger.info("md5.txt文件不存在,自动创建md5.txt文件")
#             return False

#         with open(md5_path,"r",encoding="utf-8") as f :
#                lines=f.readlines()
#                for line  in lines:
#                       if line.strip()==md5_for_check:
#                              return True
#                return False     
                             
# def save_md5_hex(md5_for_check:str):    
#        with open(get_file_path("md5.txt"),"a",encoding="utf-8") as  f :
#               f.write(md5_for_check+"\n")
#               logger.info(f"已存入md5值:{md5_for_check}到md5.txt文件")   
                        





def pdf_loader(file_path):
          return PyMuPDFLoader(file_path).load()

def text_loader(file_path):
        return TextLoader(file_path,encoding="utf-8").load()





if __name__ == "__main__":
     
#      md5=get_file_md5_value("data/维护保养.txt")
#      print(md5)
#      bool=check_md5_hex(md5)
#      if not bool:
#             save_md5_hex(md5)

     text=text_loader("data/维护保养.txt")
     print(text)
     text[0].metadata["file_name"]="维护保养.txt"
     text[0].metadata["file_path"]=get_file_path("data/维护保养.txt")
     print(text[0].metadata)













