from pydantic import BaseModel,Field



class QueryRequest(BaseModel):
       query:str
       session_id:int | None =Field(default=None,gt=0)


class QueryResponse(BaseModel):
       response:str

class UploadResponse(BaseModel):
       message:str
       filename:str