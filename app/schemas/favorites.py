from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class CategoryInfo(BaseModel):
    name: str


class LocationInfo(BaseModel):
    city: str
    district: Optional[str] = None


class OwnerInfo(BaseModel):
    username: str
    avatar_url: Optional[str] = None


class FavoriteAdOut(BaseModel):
    id: UUID
    title: str
    description: str
    price: float
    currency: str
    created_at: datetime
    views_count: int
    image_urls: List[str] = []
    category: CategoryInfo
    location: LocationInfo
    owner: OwnerInfo
