from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class MessageBase(BaseModel):
    recipient_id: UUID
    ad_id: UUID
    text: str


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    text: Optional[str] = None
    is_read: Optional[bool] = None


class MessageOut(MessageBase):
    id: UUID
    sender_id: UUID
    sent_at: datetime
    is_read: bool
    sender: Optional[dict] = None
    recipient: Optional[dict] = None
    ad: Optional[dict] = None

    class Config:
        from_attributes = True
