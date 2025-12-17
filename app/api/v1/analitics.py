from fastapi import APIRouter, Query, HTTPException, status, Path
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.db.session import db
from app.schemas.analitics import (
    TrendingAdResponse, OptimalPriceResponse, UserStatsResponse, CategoryMarketInsightsResponse)

router = APIRouter(prefix="/analitics", tags=["Аналитика"])


@router.get("/trending", response_model=List[TrendingAdResponse])
async def get_trending_ads(
    days: int = Query(
        7, ge=1, le=30, description="Период в днях для расчёта трендов"),
    category_id: Optional[int] = Query(
        None, description="Фильтр по категории"),
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    limit: int = Query(20, ge=1, le=50, description="Количество объявлений"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации")
):
    """
    Получение трендовых объявлений за период
    """
    try:
        category_param = category_id if category_id is not None else None

        if city and city.strip():
            city_param = city.strip()
        else:
            city_param = None

        query = """
        SELECT
            ad_id,
            title,
            price,
            currency,
            city,
            category_name,
            views_last_period,
            messages_last_period,
            favorites_last_period,
            trending_score,
            created_at
        FROM get_trending_ads($1, $2, $3, $4, $5)
        """

        results = await db.fetch(
            query,
            days,
            category_param,
            city_param,
            limit,
            offset
        )

        if not results:
            return []

        return [
            TrendingAdResponse(
                ad_id=row["ad_id"],
                title=row["title"],
                price=float(row["price"]),
                currency=row["currency"],
                city=row["city"],
                category_name=row["category_name"],
                views_last_period=row["views_last_period"],
                messages_last_period=row["messages_last_period"],
                favorites_last_period=row["favorites_last_period"],
                trending_score=float(row["trending_score"]),
                created_at=row["created_at"].isoformat(
                ) if row["created_at"] else None
            )
            for row in results
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении трендовых объявлений: {str(e)}"
        )


@router.get("/ads/{ad_id}/optimal-price", response_model=OptimalPriceResponse)
async def get_optimal_price(
    ad_id: UUID = Path(..., description="ID объявления")
):
    """
    Получение рекомендуемой цены на основе средней цены в категории
    """
    try:
        result = await db.fetchrow(
            "SELECT get_optimal_price_suggestion($1) AS suggested_price",
            str(ad_id)
        )

        suggested_price = float(
            result["suggested_price"]) if result and result["suggested_price"] else 0.0

        message = "Рекомендуемая цена установлена на основе средней цены аналогичных объявлений." if suggested_price > 0 else "Недостаточно данных для расчёта рекомендуемой цены."

        return OptimalPriceResponse(
            ad_id=ad_id,
            suggested_price=suggested_price,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(
            f"Ошибка при получении оптимальной цены для объявления {ad_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при расчёте рекомендуемой цены"
        )


@router.get("/users/{user_id}", response_model=UserStatsResponse)
async def get_user_performance(
    user_id: UUID = Path(..., description="ID пользователя")
):
    """
    Получение персонального дашборда производительности пользователя.
    """
    try:
        user_data = await db.fetchrow(
            """
            SELECT id, username, role, created_at, is_banned
            FROM users
            WHERE id = $1
            """,
            str(user_id)
        )

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        result = await db.fetchrow(
            "SELECT * FROM user_performance_dashboard WHERE user_id = $1",
            str(user_id)
        )

        if not result:
            return UserStatsResponse(
                user_id=user_data["id"],
                username=user_data["username"],
                role=user_data["role"],
                registration_date=str(user_data["created_at"]),
                is_banned=user_data["is_banned"],
                total_ads=0,
                active_ads=0,
                rejected_ads=0,
                total_views=0,
                avg_views_per_ad=0.0,
                total_messages_received=0,
                avg_messages_per_ad=0.0,
                total_favorites=0,
                total_reports_received=0,
                resolved_reports=0,
                last_ad_created=None,
                ads_last_7_days=0
            )

        return UserStatsResponse(
            user_id=result["user_id"],
            username=result["username"],
            role=result["role"],
            registration_date=str(result["registration_date"]),
            is_banned=result["is_banned"],
            total_ads=result["total_ads"],
            active_ads=result["active_ads"],
            rejected_ads=result["rejected_ads"],
            total_views=result["total_views"],
            avg_views_per_ad=float(result["avg_views_per_ad"]),
            total_messages_received=result["total_messages_received"],
            avg_messages_per_ad=float(result["avg_messages_per_ad"]),
            total_favorites=result["total_favorites"],
            total_reports_received=result["total_reports_received"],
            resolved_reports=result["resolved_reports"],
            last_ad_created=str(
                result["last_ad_created"]) if result["last_ad_created"] else None,
            ads_last_7_days=result["ads_last_7_days"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении данных дашборда"
        )


@router.get("/categories/insights", response_model=List[CategoryMarketInsightsResponse])
async def get_category_insights(
    limit: int = Query(
        50, ge=1, le=100, description="Максимальное количество категорий"),
    min_ads: int = Query(
        0, ge=0, description="Минимальное количество активных объявлений в категории")
):
    """
    Получение рыночной аналитики по всем категориям.
    Доступно всем авторизованным пользователям.
    """
    try:
        query = """
        SELECT * FROM category_market_insights
        WHERE total_active_ads >= $1
        ORDER BY total_active_ads DESC
        LIMIT $2
        """

        results = await db.fetch(query, min_ads, limit)

        if not results:
            return []

        return [
            CategoryMarketInsightsResponse(
                category_id=row["category_id"],
                category_name=row["category_name"],
                category_slug=row["category_slug"],
                total_active_ads=row["total_active_ads"],
                new_ads_last_7_days=row["new_ads_last_7_days"],
                new_ads_last_24h=row["new_ads_last_24h"],
                avg_price=float(row["avg_price"]) if row["avg_price"] else 0.0,
                min_price=float(row["min_price"]) if row["min_price"] else 0.0,
                max_price=float(row["max_price"]) if row["max_price"] else 0.0,
                total_views=row["total_views"],
                avg_views_per_ad=float(
                    row["avg_views_per_ad"]) if row["avg_views_per_ad"] else 0.0
            )
            for row in results
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении аналитики"
        )
