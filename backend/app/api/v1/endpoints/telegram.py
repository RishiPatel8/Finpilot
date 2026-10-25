import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from app.schemas.telegram import (
    TelegramLinkCodeResponse,
    TelegramStatusResponse,
    TelegramNotificationPrefsUpdate,
    TelegramUnlinkResponse,
)
from app.telegram.service import telegram_service
from app.telegram.handler import telegram_handler
from app.telegram.notifications import notification_dispatcher
from app.telegram.client import telegram_client

logger = logging.getLogger("finpilot.api.telegram")

router = APIRouter()


@router.post("/link-code", response_model=TelegramLinkCodeResponse)
def generate_telegram_link_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a cryptographically secure, single-use, 15-minute link code
    for the authenticated user.
    """
    link_code = telegram_service.generate_link_code(db, current_user.id)
    bot_user = settings.TELEGRAM_BOT_USERNAME or ""

    deep_link = None
    if bot_user:
        deep_link = f"https://t.me/{bot_user}?start={link_code.code}"

    return TelegramLinkCodeResponse(
        code=link_code.code,
        expires_at=link_code.expires_at,
        valid_for_seconds=900,
        bot_username=bot_user or None,
        deep_link_url=deep_link,
    )


@router.get("/status", response_model=TelegramStatusResponse)
def get_telegram_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if the authenticated user has linked their Telegram account and
    retrieve active notification preferences.
    """
    link = telegram_service.get_link_by_user_id(db, current_user.id)
    bot_user = settings.TELEGRAM_BOT_USERNAME or None

    if not link:
        return TelegramStatusResponse(
            is_linked=False,
            bot_username=bot_user,
        )

    return TelegramStatusResponse(
        is_linked=True,
        telegram_username=link.telegram_username,
        telegram_first_name=link.telegram_first_name,
        linked_at=link.created_at,
        notifications_enabled=link.notifications_enabled,
        notify_bills=link.notify_bills,
        notify_budget=link.notify_budget,
        notify_goals=link.notify_goals,
        notify_summary=link.notify_summary,
        bot_username=bot_user,
    )


@router.post("/unlink", response_model=TelegramUnlinkResponse)
def unlink_telegram_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect and remove the Telegram account mapping for the authenticated user.
    """
    success = telegram_service.unlink_account(db, current_user.id)
    if not success:
        return TelegramUnlinkResponse(
            success=False,
            message="No active Telegram account was linked to this profile.",
        )

    return TelegramUnlinkResponse(
        success=True,
        message="Telegram account successfully unlinked.",
    )


@router.put("/notifications", response_model=TelegramStatusResponse)
def update_notification_preferences(
    prefs: TelegramNotificationPrefsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update granular opt-in notification settings for the linked Telegram account.
    """
    link = telegram_service.update_notification_preferences(db, current_user.id, prefs)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Telegram link found. Please link your account first.",
        )

    return TelegramStatusResponse(
        is_linked=True,
        telegram_username=link.telegram_username,
        telegram_first_name=link.telegram_first_name,
        linked_at=link.created_at,
        notifications_enabled=link.notifications_enabled,
        notify_bills=link.notify_bills,
        notify_budget=link.notify_budget,
        notify_goals=link.notify_goals,
        notify_summary=link.notify_summary,
        bot_username=settings.TELEGRAM_BOT_USERNAME or None,
    )


@router.post("/test-notification")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an immediate test alert to verify the Telegram bot notification pipeline.
    """
    link = telegram_service.get_link_by_user_id(db, current_user.id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram account is not linked.",
        )

    test_message = (
        "🔔 <b>FinPilot Test Notification</b>\n\n"
        "Your Telegram bot connection is active and configured correctly!\n"
        "You will receive alerts for upcoming bills, budget limits, and financial milestones according to your preferences."
    )

    res = await telegram_client.send_message(chat_id=link.telegram_chat_id, text=test_message)
    return {"status": "sent", "telegram_result": res}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Secured webhook endpoint receiving updates from Telegram Bot API.
    Authenticates requests using the configured secret token header.
    """
    # Verify secret token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if not x_telegram_bot_api_secret_token or x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Rejected Telegram webhook update: invalid secret token header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid secret token",
            )

    try:
        body = await request.json()
    except Exception as exc:
        logger.error("Failed to parse Telegram webhook JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Process update asynchronously
    result = await telegram_handler.handle_update(body, db)
    return {"ok": True, "result": result}
