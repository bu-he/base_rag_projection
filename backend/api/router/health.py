from fastapi import APIRouter
from fastapi.responses import JSONResponse


router=APIRouter(tags=["health"])


from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}



@router.get("/ready")
def ready():
    from rag.retriever import is_ready
   
    if not is_ready():
        return JSONResponse(
            status_code=503,
            content={"status": "loading"}
        )
    return {
        "status": "ok"
    }