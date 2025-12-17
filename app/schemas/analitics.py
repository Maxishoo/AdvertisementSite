
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class TrendingAdResponse(BaseModel):
    ad_id: UUID
    title: str
    price: float
    currency: str
    city: str
    category_name: str
    views_last_period: int
    messages_last_period: int
    favorites_last_period: int
    trending_score: float
    created_at: str


class OptimalPriceResponse(BaseModel):
    ad_id: UUID
    suggested_price: float = Field(ge=0)
    message: str


class UserStatsResponse(BaseModel):
    user_id: UUID
    username: str
    role: str
    registration_date: str
    is_banned: bool
    total_ads: int
    active_ads: int
    rejected_ads: int
    total_views: int
    avg_views_per_ad: float
    total_messages_received: int
    avg_messages_per_ad: float
    total_favorites: int
    total_reports_received: int
    resolved_reports: int
    last_ad_created: Optional[str]
    ads_last_7_days: int


class CategoryMarketInsightsResponse(BaseModel):
    category_id: int
    category_name: str
    category_slug: str
    total_active_ads: int
    new_ads_last_7_days: int
    new_ads_last_24h: int
    avg_price: float
    min_price: float
    max_price: float
    total_views: int
    avg_views_per_ad: float
