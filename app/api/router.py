from fastapi import APIRouter

from app.api.v1.routes_chat import router as chat_router
from app.api.v1.routes_reviews import router as reviews_router

api_router = APIRouter()
api_router.include_router(reviews_router, prefix="/v1", tags=["reviews"])
api_router.include_router(chat_router, prefix="/v1", tags=["chat"])
