from fastapi import APIRouter,HTTPException
from rag.ingestion_service import IngestionService
from typing import Annotated
from fastapi import File,UploadFile
from pathlib import Path
from config.rag import Settings
from schemas.rag import UploadResponse
from rag.vectorstore import VectorStore
from rag.retriever import get_retriever_service
from config.logger import logger



setting=Settings()

router=APIRouter(prefix="/document",tags=["document"])

@router.post("/ingest")
def ingest():
     service=IngestionService()
     service.ingest()
     return {"message":"知识库存储完成"}

@router.post("/upload",response_model=UploadResponse)
async def upload(file:Annotated[UploadFile,File()]):
     service=IngestionService()
     setting.data_dir.mkdir(parents=True,exist_ok=True)
     safe_filename=Path(file.filename).name
     file_path=setting.data_dir/safe_filename
     with open(file_path,"wb") as f:
         while chunk := await file.read(1024 * 1024):
                    f.write(chunk)
     result=service.ingest_file(file_path)

     if result=="failed":
        raise HTTPException(status_code=400,detail="文件处理失败")
     if result in ("added","updated"):
        get_retriever_service().rebuild_bm25()   # 上传路径也要同步 BM25
        logger.info(f"上传文件触发 BM25 重建（{result}）：{safe_filename}")
     if result=="skipped":
        return UploadResponse(message="文件未变动或已上传",filename=safe_filename)
     return UploadResponse(message="文件上传成功",filename=safe_filename)

@router.get("/get_file_list")
def show_all_stored_file_path():
     vectorstore=VectorStore()
     all_stored_file_path=vectorstore.get_all_stored_file_path()
     return {"all_stored_file_path":list(all_stored_file_path)}
    