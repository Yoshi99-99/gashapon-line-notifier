from sqlalchemy.orm import Session
from . import models
import uuid

def get_user_by_line_id(db: Session, line_user_id: str):
    return db.query(models.User).filter(models.User.line_user_id == line_user_id).first()

def create_user(db: Session, line_user_id: str, display_name: str = None):
    db_user = models.User(line_user_id=line_user_id, display_name=display_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_watches_by_user(db: Session, user_id: uuid.UUID):
    return db.query(models.Watch).filter(models.Watch.user_id == user_id).all()

def create_watch(db: Session, user_id: uuid.UUID, prefecture: str, product_url: str, product_code: str):
    db_watch = models.Watch(
        user_id=user_id,
        prefecture=prefecture,
        product_url=product_url,
        product_code=product_code
    )
    db.add(db_watch)
    db.commit()
    db.refresh(db_watch)
    return db_watch

def delete_watch(db: Session, watch_id: uuid.UUID, user_id: uuid.UUID):
    watch = db.query(models.Watch).filter(models.Watch.id == watch_id, models.Watch.user_id == user_id).first()
    if watch:
        db.delete(watch)
        db.commit()
        return True
    return False

def get_all_watches(db: Session):
    return db.query(models.Watch).all()

def create_notification(db: Session, watch_id: uuid.UUID, payload_json: str):
    db_notification = models.Notification(watch_id=watch_id, payload_json=payload_json)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification
