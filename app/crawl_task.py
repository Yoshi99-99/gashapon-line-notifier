import logging
import asyncio
from sqlalchemy.orm import Session
from linebot import LineBotApi
from linebot.models import TextSendMessage
from . import crud, scraper, models
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None

async def run_crawl_task(db: Session):
    logger.info("Starting crawl task")
    watches = crud.get_all_watches(db)
    
    if not watches:
        logger.info("No watches found.")
        return

    for watch in watches:
        try:
            logger.info(f"Checking watch {watch.id}: {watch.prefecture} - {watch.product_code}")
            shops = await scraper.fetch_shops(watch.product_code, watch.prefecture)
            
            if shops:
                # Send notification
                user = db.query(models.User).filter(models.User.id == watch.user_id).first()
                if user and user.line_user_id:
                    await send_notification(user.line_user_id, watch, shops, db)
            else:
                logger.info(f"No shops found for watch {watch.id}")
                
        except Exception as e:
            logger.error(f"Error processing watch {watch.id}: {e}")

    logger.info("Crawl task completed")

async def send_notification(line_user_id: str, watch: models.Watch, shops: list, db: Session):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"[{now_str} 時点]\n{watch.prefecture}で在庫ありの店舗一覧"
    
    # Limit number of shops to avoid hitting message size limits
    display_shops = shops[:10]
    
    shop_lines = []
    for shop in display_shops:
        shop_lines.append(f"・{shop['name']}\n  {shop['address']}")
    
    if len(shops) > 10:
        shop_lines.append(f"\n他 {len(shops) - 10} 件...")

    message_text = f"{title}\n\n" + "\n".join(shop_lines)
    message_text += f"\n\n検索結果: {watch.product_url}"

    try:
        if line_bot_api:
            line_bot_api.push_message(line_user_id, TextSendMessage(text=message_text))
            
            # Log notification
            payload = json.dumps({"shops": shops}, ensure_ascii=False)
            crud.create_notification(db, watch.id, payload)
            logger.info(f"Notification sent to {line_user_id}")
        else:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN not set, skipping push message")
            
    except Exception as e:
        logger.error(f"Failed to send push message to {line_user_id}: {e}")
