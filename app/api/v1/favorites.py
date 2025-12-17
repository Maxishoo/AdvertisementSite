from fastapi import (APIRouter, HTTPException, status, Query, Path)
from uuid import UUID
from typing import List
from app.db.session import db
from app.schemas.favorites import FavoriteAdOut
import json

router = APIRouter(prefix="/favorites", tags=["Избранное"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    ad_id: UUID = Query(..., description="Идентификатор объявления"),
    user_id: UUID = Query(..., description="Идентификатор пользователя"),
):
    """Добавление объявления в избранное"""

    ad_exists = await db.fetchrow(
        "SELECT id FROM ads WHERE id = $1 AND is_active = true AND moderation_status = 'APPROVED'",
        str(ad_id)
    )
    if not ad_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено, неактивно или не прошло модерацию"
        )

    user_exists = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(user_id)
    )
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    existing_favorite = await db.fetchrow(
        "SELECT 1 FROM favorites WHERE user_id = $1 AND ad_id = $2",
        str(user_id), str(ad_id)
    )
    if existing_favorite:
        return {"message": "Объявление уже в избранном", "ad_id": str(ad_id)}

    try:
        await db.execute(
            """
            INSERT INTO favorites (user_id, ad_id, added_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id, ad_id) DO NOTHING
            """,
            str(user_id), str(ad_id)
        )
        return {"message": "Объявление добавлено в избранное", "ad_id": str(ad_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении в избранное"
        )


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    ad_id: UUID = Path(..., description="Идентификатор объявления"),
    user_id: UUID = Query(..., description="Идентификатор пользователя"),
):
    """Удаление объявления из избранного"""

    try:
        existing = await db.fetchrow(
            """
            SELECT 1 FROM favorites
            WHERE user_id = $1 AND ad_id = $2
            """,
            str(user_id), str(ad_id)
        )

        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объявление не найдено в избранном"
            )

        result = await db.execute(
            """
            DELETE FROM favorites
            WHERE user_id = $1 AND ad_id = $2
            """,
            str(user_id), str(ad_id)
        )

        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объявление не найдено в избранном"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Ошибка при удалении из избранного: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении из избранного"
        )


@router.get("/", response_model=List[FavoriteAdOut])
async def get_user_favorites(
    user_id: UUID = Path(..., description="Идентификатор объявления"),
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(
        20, ge=1, le=100, description="Количество записей для возврата")
):
    """Получение списка избранных объявлений пользователя"""

    query = """
    SELECT
        a.id, a.title, a.description, a.price, a.currency, a.created_at,
        a.views_count,
        a.image_urls,
        c.name as category_name,
        l.city,
        l.district,
        u.username as owner_username,
        u.avatar_url as owner_avatar
    FROM favorites f
    JOIN ads a ON a.id = f.ad_id
    JOIN categories c ON c.id = a.category_id
    JOIN locations l ON l.id = a.location_id
    JOIN users u ON u.id = a.user_id
    WHERE f.user_id = $1
        AND a.is_active = true
        AND a.moderation_status = 'APPROVED'
    ORDER BY f.added_at DESC
    LIMIT $2 OFFSET $3
    """

    try:
        favorites = await db.fetch(query, str(user_id), limit, skip)

        result = []
        for fav in favorites:
            image_urls = []
            try:
                if fav["image_urls"]:
                    if isinstance(fav["image_urls"], str):
                        parsed = json.loads(fav["image_urls"])
                        if isinstance(parsed, list):
                            image_urls = [str(item)
                                          for item in parsed if item is not None]
                    elif isinstance(fav["image_urls"], list):
                        image_urls = [
                            str(item) for item in fav["image_urls"] if item is not None]
            except (TypeError, ValueError, json.JSONDecodeError):
                image_urls = []

            description = str(fav["description"]) if fav["description"] else ""
            if len(description) > 150:
                cut_pos = description.rfind(' ', 0, 150)
                if cut_pos == -1 or cut_pos < 100:
                    cut_pos = 150
                description = description[:cut_pos].strip() + "..."

            result.append({
                "id": fav["id"],
                "title": fav["title"],
                "description": description,
                "price": float(fav["price"]),
                "currency": fav["currency"],
                "created_at": fav["created_at"],
                "views_count": fav["views_count"],
                "image_urls": image_urls,
                "category": {
                    "name": fav["category_name"]
                },
                "location": {
                    "city": fav["city"],
                    "district": fav["district"] if fav["district"] else None
                },
                "owner": {
                    "username": fav["owner_username"],
                    "avatar_url": fav["owner_avatar"] if fav["owner_avatar"] else None
                }
            })

        return result
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении избранного: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка избранного"
        )
