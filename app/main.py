import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from . import database, models, line_handlers, crawl_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables (for simplicity in this setup, usually handled by Alembic)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.get("/health")
def health_check():
    return "ok"

@app.post("/webhook/line")
async def line_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    return await line_handlers.handle_webhook(request, db, background_tasks)

@app.post("/cron/crawl")
async def cron_crawl(background_tasks: BackgroundTasks, authorization: str = Header(None), db: Session = Depends(database.get_db)):
    cron_secret = os.getenv("CRON_SECRET")
    
    # Simple bearer token check or just matching the secret
    # Render cron jobs can send a header. 
    # If using a simple request, we can check a custom header or query param.
    # Here assuming 'Authorization: Bearer <CRON_SECRET>' or just the secret if passed differently.
    
    if not cron_secret:
        logger.warning("CRON_SECRET not set, allowing request (unsafe in production)")
    elif authorization != f"Bearer {cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    background_tasks.add_task(crawl_task.run_crawl_task, db)
    return {"status": "accepted", "message": "Crawl task started"}
