from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# === ROUTER ===
router = APIRouter(prefix="/api", tags=["Bot Management"])

# === MODELS ===
class BotStatus(BaseModel):
    is_running: bool
    users_count: int
    last_update: str

class UserInfo(BaseModel):
    user_id: int
    username: str
    first_name: str
    is_active: bool

# === ENDPOINTS ===

@router.get("/status", response_model=BotStatus)
async def get_bot_status():
    """Получить статус бота"""
    return {
        "is_running": True,
        "users_count": 42,
        "last_update": "2025-11-04T20:38:00"
    }

@router.get("/users", response_model=List[UserInfo])
async def get_users():
    """Получить список пользователей"""
    return [
        {"user_id": 123, "username": "john_doe", "first_name": "John", "is_active": True},
        {"user_id": 456, "username": "jane_smith", "first_name": "Jane", "is_active": True},
    ]

@router.post("/restart")
async def restart_bot():
    """Перезагрузить бота"""
    return {"message": "Bot restart initiated", "status": "success"}

@router.get("/stats")
async def get_stats():
    """Получить статистику"""
    return {
        "total_users": 42,
        "active_today": 15,
        "messages_sent": 523,
        "errors": 2
    }
