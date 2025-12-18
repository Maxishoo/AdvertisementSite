from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AdBase(BaseModel):
    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=50)
    price: float = Field(..., gt=0)
    currency: str = Field("RUB", pattern="^(RUB|USD|EUR)$")
    category_id: int
    location_id: int
    moderation_status: Optional[str] = "PENDING"
    is_active: Optional[bool] = True
    image_urls: Optional[str] = None


class AdCreate(AdBase):
    tag_ids: Optional[List[int]] = []


class AdUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=10, max_length=255)
    description: Optional[str] = Field(None, min_length=50)
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^(RUB|USD|EUR)$")
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    moderation_status: Optional[str] = None
    is_active: Optional[bool] = None
    image_urls: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class AdInDB(AdBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    views_count: int = 0

    class Config:
        from_attributes = True


class AdOut(AdBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    views_count: int
    category: Optional[dict] = None
    location: Optional[dict] = None
    tags: Optional[List[dict]] = []
    owner: Optional[dict] = None

    class Config:
        from_attributes = True


class AdStatisticsResponse(BaseModel):
    ad_id: UUID
    title: str
    price: float
    currency: str
    created_at: str
    moderation_status: str
    is_active: bool

    views_count: int
    total_views: int
    unique_viewers: int
    mobile_views: int
    pc_views: int

    total_messages: int
    unique_senders: int
    unread_messages: int

    favorites_count: int

    total_reports: int
    pending_reports: int
    resolved_reports: int
    rejected_reports: int

    category_name: str
    city: str
    owner_username: str
    owner_is_banned: bool


class AdCreate2(BaseModel):
    user_id: UUID
    category_id: int
    location_id: int
    title: str
    description: str
    price: int
    currency: str
    moderation_status: str
    is_active: bool
    image_urls: str
    tag_ids: Optional[List[int]]
