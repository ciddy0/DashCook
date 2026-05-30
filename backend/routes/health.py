from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def home():
    return "hai!"


@router.get("/ping")
def ping():
    return "pong"
