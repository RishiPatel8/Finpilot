import asyncio
import logging
import signal
from typing import Optional
from app.core.config import settings
from app.db.session import SessionLocal
from app.telegram.client import telegram_client, TelegramClient
from app.telegram.handler import telegram_handler, TelegramUpdateHandler

logger = logging.getLogger("finpilot.telegram.polling")


class TelegramPoller:
    """
    Long-polling worker for local development and non-webhook environments.
    Guarantees no simultaneous webhook conflict by clearing webhooks first.
    """

    def __init__(self, client: Optional[TelegramClient] = None, handler: Optional[TelegramUpdateHandler] = None):
        self.client = client or telegram_client
        self.handler = handler or telegram_handler
        self._running = False

    async def start(self):
        if not self.client.is_configured:
            logger.warning("TELEGRAM_BOT_TOKEN is not configured. Poller exiting.")
            return

        logger.info("Starting Telegram Bot long-polling worker...")

        # Ensure no active webhook conflicts with getUpdates
        try:
            webhook_info = await self.client.get_webhook_info()
            if webhook_info.get("result", {}).get("url"):
                logger.info("Active webhook detected (%s). Removing webhook for polling...", webhook_info["result"]["url"])
                await self.client.delete_webhook()
        except Exception as e:
            logger.warning("Error checking/clearing webhook: %s", e)

        self._running = True
        offset: Optional[int] = None

        while self._running:
            try:
                updates_res = await self.client.get_updates(offset=offset, timeout=20)
                if not updates_res.get("ok"):
                    await asyncio.sleep(3)
                    continue

                updates = updates_res.get("result", [])
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        offset = update_id + 1

                    # Process update with dedicated database session
                    db = SessionLocal()
                    try:
                        await self.handler.handle_update(update, db)
                    except Exception as err:
                        logger.error("Error processing update %s: %s", update_id, err, exc_info=True)
                    finally:
                        db.close()

            except asyncio.CancelledError:
                logger.info("Polling loop received cancellation signal.")
                break
            except Exception as e:
                logger.error("Error in Telegram polling loop: %s", e)
                await asyncio.sleep(5)

        logger.info("Telegram long-polling worker stopped.")

    def stop(self):
        self._running = False


async def run_poller():
    poller = TelegramPoller()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, poller.stop)
        except NotImplementedError:
            # Signal handlers not implemented on Windows event loop for add_signal_handler
            pass

    await poller.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_poller())
