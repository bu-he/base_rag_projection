from pydantic import BaseModel,Field



class QueryRequest(BaseModel):
    query:str
    session_id:int|None=Field(default=None,description="会话ID",gt=0)





class QueryResponse(BaseModel):
    response:str
