from fastapi import APIRouter

from app.handler import concept


api_v1_router = APIRouter()
api_v1_router.include_router(concept.router, prefix="/concept")
