from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TelegramLinkCodeResponse(BaseModel):
    code: str
    expires_at: datetime
    valid_for_seconds: int = 900
    bot_username: Optional[str] = None
    deep_link_url: Optional[str] = None


class TelegramStatusResponse(BaseModel):
    is_linked: bool
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    linked_at: Optional[datetime] = None
    notifications_enabled: bool = True
    notify_bills: bool = True
    notify_budget: bool = True
    notify_goals: bool = True
    notify_summary: bool = False
    bot_username: Optional[str] = None


class TelegramNotificationPrefsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    notify_bills: Optional[bool] = None
    notify_budget: Optional[bool] = None
    notify_goals: Optional[bool] = None
    notify_summary: Optional[bool] = None


class TelegramUnlinkResponse(BaseModel):
    success: bool
    message: str


class TelegramUser(BaseModel):
    id: int
    is_bot: Optional[bool] = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str  # "private", "group", "supergroup", "channel"
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None


class TelegramCallbackQuery(BaseModel):
    id: str
    from_user: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None
