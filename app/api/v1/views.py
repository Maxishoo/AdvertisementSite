from fastapi import APIRouter, HTTPException, status, Query, Path
from uuid import UUID
from typing import Optional
from app.db.session import db


router = APIRouter(prefix="/views", tags=["Просмотры"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def record_view(
    ad_id: UUID = Query(..., description="Уникальный идентификатор объявления"),
    user_id: Optional[UUID] = Query(None, description="Уникальный идентификатор пользователя"),
    device: str = Query("MOBILE", description="Тип устройства, с которого выполнен просмотр: MOBILE or PC"),
):
    """Запись просмотра объявления"""

    ad_exists = await db.fetchrow(
        "SELECT id FROM ads WHERE id = $1 AND is_active = true",
        str(ad_id)
    )
    if not ad_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено или неактивно"
        )

    if user_id:
        user_exists = await db.fetchrow(
            "SELECT id FROM users WHERE id = $1",
            str(user_id)
        )
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

    query = """
    INSERT INTO views (ad_id, user_id, viewed_at, device)
    VALUES ($1, $2, NOW(), $3)
    """

    try:
        await db.execute(query, str(ad_id), str(user_id) if user_id else None, device)
        return {"message": "Просмотр записан"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при записи просмотра: {str(e)}"
        )


@router.get("/stats/{ad_id}")
async def get_ad_views_stats(ad_id: UUID = Path(..., description="Уникальный идентификатор объявления")):
    """Получение статистики просмотров для объявления"""
    ad_exists = await db.fetchrow(
        "SELECT id, views_count FROM ads WHERE id = $1",
        str(ad_id)
    )
    if not ad_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )

    total_views_query = """
    SELECT
        COUNT(*) as total_views,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) FILTER (WHERE device = 'MOBILE') as mobile_views,
        COUNT(*) FILTER (WHERE device = 'PC') as pc_views
    FROM views
    WHERE ad_id = $1
    """

    daily_stats_query = """
    SELECT
        DATE(viewed_at) as date,
        COUNT(*) as views_count,
        COUNT(DISTINCT user_id) as unique_users
    FROM views
    WHERE ad_id = $1 AND viewed_at >= NOW() - INTERVAL '7 days'
    GROUP BY DATE(viewed_at)
    ORDER BY date DESC
    """

    try:
        total_stats = await db.fetchrow(total_views_query, str(ad_id))
        daily_stats = await db.fetch(daily_stats_query, str(ad_id))

        return {
            "ad_id": str(ad_id),
            "current_views_count": ad_exists["views_count"],
            "total_views_recorded": total_stats["total_views"],
            "unique_users": total_stats["unique_users"],
            "device_breakdown": {
                "mobile": total_stats["mobile_views"],
                "pc": total_stats["pc_views"]
            },
            "daily_stats": [
                {
                    "date": stat["date"].isoformat(),
                    "views_count": stat["views_count"],
                    "unique_users": stat["unique_users"]
                }
                for stat in daily_stats
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )
