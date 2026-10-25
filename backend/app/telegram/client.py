import logging
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramClient:
    """
    Official Telegram Bot API HTTP client with resilient network calls,
    proper error isolation, and test mocking support.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"{TELEGRAM_API_BASE}{self.token}" if self.token else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.token and not self.token.startswith("mock_disabled"))

    async def _post(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured:
            logger.info("TelegramClient: Bot token not configured, skipping API call to %s", method)
            return {"ok": True, "result": {"message_id": 999999, "mock": True}}

        url = f"{self.base_url}/{method}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=data)
                resp_json = resp.json()
                if not resp_json.get("ok"):
                    logger.warning(
                        "Telegram API error on %s: %s (code %s)",
                        method,
                        resp_json.get("description"),
                        resp_json.get("error_code"),
                    )
                return resp_json
        except Exception as exc:
            logger.error("Failed to connect to Telegram Bot API %s: %s", method, exc)
            return {"ok": False, "error": str(exc)}

    async def _get(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.is_configured:
            logger.info("TelegramClient: Bot token not configured, skipping API call to %s", method)
            return {"ok": True, "result": {"mock": True}}

        url = f"{self.base_url}/{method}"
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.get(url, params=params)
                return resp.json()
        except Exception as exc:
            logger.error("Failed to get Telegram Bot API %s: %s", method, exc)
            return {"ok": False, "error": str(exc)}

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        disable_web_page_preview: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a message to a Telegram chat.
        """
        payload: Dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("sendMessage", payload)

    async def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Edit an existing message, typically used when confirming or canceling pending actions.
        """
        payload: Dict[str, Any] = {
            "chat_id": str(chat_id),
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self._post("editMessageText", payload)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> Dict[str, Any]:
        """
        Acknowledge a Telegram button callback.
        """
        payload: Dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            payload["text"] = text
        return await self._post("answerCallbackQuery", payload)

    async def set_webhook(self, url: str, secret_token: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "url": url,
            "allowed_updates": ["message", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._post("setWebhook", payload)

    async def delete_webhook(self, drop_pending_updates: bool = False) -> Dict[str, Any]:
        return await self._post("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    async def get_webhook_info(self) -> Dict[str, Any]:
        return await self._get("getWebhookInfo")

    async def get_me(self) -> Dict[str, Any]:
        return await self._get("getMe")

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if offset is not None:
            params["offset"] = offset
        return await self._get("getUpdates", params)


telegram_client = TelegramClient()
