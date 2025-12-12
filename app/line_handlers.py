import os
import re
import logging
from fastapi import Request, HTTPException, BackgroundTasks
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sqlalchemy.orm import Session
from . import crud, models, scraper

logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if LINE_CHANNEL_ACCESS_TOKEN:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
else:
    line_bot_api = None
    logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set.")

if LINE_CHANNEL_SECRET:
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
else:
    handler = None
    logger.warning("LINE_CHANNEL_SECRET is not set.")

async def handle_webhook(request: Request, db: Session, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        # We need to pass the db session to the handler, but the standard handler doesn't support extra args.
        # So we'll handle the events manually or wrap the handler.
        # A simple way is to process events in a loop after parsing.
        
        # However, line-bot-sdk's handler.handle() calls the registered functions.
        # We can use a global variable or a context var, but that's messy.
        # Better approach: Parse the body manually using the parser provided by the SDK, 
        # then iterate over events.
        
        from linebot.models import Event
        from linebot.webhook import WebhookParser
        
        parser = WebhookParser(LINE_CHANNEL_SECRET)
        events = parser.parse(body_str, signature)

        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                await handle_message(event, db)

    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return "OK"

async def handle_message(event: MessageEvent, db: Session):
    text = event.message.text.strip()
    line_user_id = event.source.user_id
    
    # Ensure user exists
    user = crud.get_user_by_line_id(db, line_user_id)
    if not user:
        user = crud.create_user(db, line_user_id)

    if text.startswith("登録"):
        await handle_register(event, text, user, db)
    elif text == "一覧":
        await handle_list(event, user, db)
    elif text.startswith("削除"):
        await handle_delete(event, text, user, db)
    else:
        # Echo or help message
        reply_text = (
            "【使い方ガイド】\n\n"
            "🤖 監視を登録する\n"
            "「登録 {都道府県} {商品URL}」\n"
            "例：登録 東京 https://gashapon.jp/products/detail.php?jan_code=...\n\n"
            "📋 登録リストを見る\n"
            "「一覧」\n\n"
            "🗑️ 登録を削除する\n"
            "「削除 {監視ID}」\n"
            "※IDは一覧コマンドで確認できます。"
        )
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

async def handle_register(event, text, user, db):
    # Format: 登録 {Prefecture} {URL}
    parts = text.split()
    if len(parts) != 3:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="フォーマットエラー: 登録 {都道府県} {商品URL}"))
        return

    pref_input = parts[1]
    url = parts[2]
    
    # Normalize prefecture
    normalized_pref = None
    for p in scraper.PREFECTURE_MAP.keys():
        if pref_input in p: # Simple matching (e.g. "東京" in "東京都")
            normalized_pref = p
            break
    
    if not normalized_pref:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"都道府県が見つかりません: {pref_input}"))
        return

    # Extract product code
    # URL example: 
    # https://gashapon.jp/shop/gplus_list.php?product_code=XXXXXX
    # https://gashapon.jp/products/detail.php?jan_code=XXXXXX
    match = re.search(r"(?:product_code|jan_code)=([a-zA-Z0-9]+)", url)
    if not match:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="URLから商品コード(product_code または jan_code)を抽出できませんでした。"))
        return
    
    product_code = match.group(1)
    
    crud.create_watch(db, user.id, normalized_pref, url, product_code)
    
    reply_text = f"{normalized_pref} × {product_code} を監視登録しました。"
    if line_bot_api:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

async def handle_list(event, user, db):
    watches = crud.get_watches_by_user(db, user.id)
    if not watches:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="監視中の商品はありません。"))
        return
    
    lines = ["【監視リスト】"]
    for w in watches:
        lines.append(f"ID: {w.id}\n地域: {w.prefecture}\nコード: {w.product_code}\n---")
    
    if line_bot_api:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))

async def handle_delete(event, text, user, db):
    parts = text.split()
    if len(parts) != 2:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="フォーマットエラー: 削除 {監視ID}"))
        return
    
    watch_id_str = parts[1]
    try:
        watch_id = models.uuid.UUID(watch_id_str)
    except ValueError:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="無効なID形式です。"))
        return

    success = crud.delete_watch(db, watch_id, user.id)
    if success:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="削除しました。"))
    else:
        if line_bot_api:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="該当する監視設定が見つかりません。"))
