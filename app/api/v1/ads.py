from fastapi import APIRouter, HTTPException, status, Query, Path, Body
from uuid import UUID
from typing import List, Optional
from app.db.session import db
from app.schemas.ad import AdCreate, AdUpdate, AdOut, AdStatisticsResponse
from datetime import datetime
import json

router = APIRouter(prefix="/ads", tags=["Объявления"])


@router.get("/{ad_id}/statistics", response_model=AdStatisticsResponse)
async def get_ad_statistics(
    ad_id: UUID = Path(..., description="ID Объявления")
):
    """
    Получение полной статистики по объявлению
    """
    try:
        query = """
        SELECT
            ad_id, title, price, currency, created_at, moderation_status, is_active,
            views_count, total_views, unique_viewers, mobile_views, pc_views,
            total_messages, unique_senders, unread_messages,
            favorites_count,
            total_reports, pending_reports, resolved_reports, rejected_reports,
            category_name, city, owner_username, owner_is_banned
        FROM ad_full_statistics
        WHERE ad_id = $1
        """

        result = await db.fetchrow(query, str(ad_id))

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Статистика для объявления не найдена"
            )

        return AdStatisticsResponse(
            ad_id=result["ad_id"],
            title=result["title"],
            price=float(result["price"]),
            currency=result["currency"],
            created_at=str(result["created_at"]),
            moderation_status=result["moderation_status"],
            is_active=result["is_active"],
            views_count=result["views_count"],
            total_views=result["total_views"],
            unique_viewers=result["unique_viewers"],
            mobile_views=result["mobile_views"],
            pc_views=result["pc_views"],
            total_messages=result["total_messages"],
            unique_senders=result["unique_senders"],
            unread_messages=result["unread_messages"],
            favorites_count=result["favorites_count"],
            total_reports=result["total_reports"],
            pending_reports=result["pending_reports"],
            resolved_reports=result["resolved_reports"],
            rejected_reports=result["rejected_reports"],
            category_name=result["category_name"],
            city=result["city"],
            owner_username=result["owner_username"],
            owner_is_banned=result["owner_is_banned"]
        )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(
            f"Ошибка при получении статистики объявления {ad_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики объявления"
        )


@router.post("/", response_model=AdOut, status_code=status.HTTP_201_CREATED)
async def create_ad(
    ad: AdCreate = Body(..., description="Данные нового объявления"),
    user_id: UUID = Query(..., description="ID владельца объявления"),
):
    """Создание нового объявления"""

    user_exists = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(user_id)
    )
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    category_exists = await db.fetchrow(
        "SELECT id FROM categories WHERE id = $1",
        ad.category_id
    )
    if not category_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )

    location_exists = await db.fetchrow(
        "SELECT id FROM locations WHERE id = $1",
        ad.location_id
    )
    if not location_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )

    # Создание объявления
    query = """
    INSERT INTO ads (
        user_id, category_id, location_id, title, description,
        price, currency, moderation_status, is_active, image_urls
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING id, user_id, category_id, location_id, title, description,
              price, currency, created_at, moderation_status, is_active,
              views_count, image_urls
    """

    params = (
        str(user_id),
        ad.category_id,
        ad.location_id,
        ad.title,
        ad.description,
        ad.price,
        ad.currency,
        ad.moderation_status,
        ad.is_active,
        ad.image_urls
    )

    try:
        new_ad = await db.fetchrow(query, *params)

        if ad.tag_ids:
            for tag_id in ad.tag_ids:
                await db.execute(
                    "INSERT INTO ad_tags (ad_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    str(new_ad["id"]), tag_id
                )

        full_ad = await get_full_ad_info(new_ad["id"])
        return full_ad
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании объявления: {str(e)}"
        )


async def get_full_ad_info(ad_id: UUID):
    """Получение полной информации об объявлении"""

    query = """
    SELECT
        a.id, a.user_id, a.category_id, a.location_id, a.title, a.description,
        a.price, a.currency, a.created_at, a.moderation_status, a.is_active,
        a.views_count, a.image_urls,
        c.name as category_name, c.slug as category_slug,
        l.city, l.district, l.street, l.building,
        u.username as owner_username, u.avatar_url as owner_avatar,
        COALESCE(array_to_json(array_agg(DISTINCT jsonb_build_object('id', t.id, 'name', t.name, 'slug', t.slug)) 
            FILTER (WHERE t.id IS NOT NULL)), '[]'::json) as tags
    FROM ads a
    JOIN categories c ON c.id = a.category_id
    JOIN locations l ON l.id = a.location_id
    JOIN users u ON u.id = a.user_id
    LEFT JOIN ad_tags at ON at.ad_id = a.id
    LEFT JOIN tags t ON t.id = at.tag_id
    WHERE a.id = $1
    GROUP BY a.id, c.id, l.id, u.id
    """

    result = await db.fetchrow(query, str(ad_id))
    if not result:
        return None

    return await build_ad_from_row(result)


async def build_ad_from_row(row):
    """Преобразование строки из БД в формат AdOut"""
    ad_data = dict(row)

    # Категория
    ad_data["category"] = {
        "id": row["category_id"],
        "name": row["category_name"],
        "slug": row["category_slug"]
    }

    # Локация
    ad_data["location"] = {
        "id": row["location_id"],
        "city": row["city"],
        "district": row["district"],
        "street": row["street"],
        "building": row["building"]
    }

    # Владелец
    ad_data["owner"] = {
        "id": row["user_id"],
        "username": row["owner_username"],
        "avatar_url": row["owner_avatar"]
    }

    # Теги
    tags_json = row["tags"]
    try:
        ad_data["tags"] = json.loads(tags_json) if tags_json else []
    except (json.JSONDecodeError, TypeError):
        ad_data["tags"] = []

    return ad_data


@router.get("/", response_model=List[AdOut])
async def get_ads(
    skip: int = Query(0, ge=0, alias="skip",
                      description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, alias="limit",
                       description="Макс. число объявлений"),
    category_id: Optional[int] = Query(
        None, description="Фильтр по ID категории"),
    min_price: Optional[float] = Query(None, ge=0, description="Мин. цена"),
    max_price: Optional[float] = Query(None, ge=0, description="Макс. цена"),
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    tag_ids: Optional[List[int]] = Query(None, description="Список ID тегов"),
    min_views: Optional[int] = Query(
        None, ge=0, description="Мин. число просмотров"),
    created_after: Optional[datetime] = Query(
        None, description="Создано после"),
    created_before: Optional[datetime] = Query(
        None, description="Создано до"),
    has_images: Optional[bool] = Query(None, description="Только с фото"),
    owner_id: Optional[UUID] = Query(
        None, description="Фильтр по ID владельца"),
    search: Optional[str] = Query(
        None, description="Поиск по заголовку/описанию"),
    sort_by: str = Query(
        "newest",
        regex="^(price_asc|price_desc|newest|oldest|views)$",
        description="Сортировка: price_asc, price_desc, newest, oldest, views"
    ),
    moderation_status: str = Query(
        "APPROVED",
        regex="^(PENDING|APPROVED|REJECTED)$",
        description="Статус модерации"
    ),
    is_active: bool = Query(True, description="Только активные объявления"),
):
    """Получение списка объявлений с фильтрацией и поиском"""

    try:
        query = """
        SELECT
            a.id, a.user_id, a.category_id, a.location_id, a.title, a.description,
            a.price, a.currency, a.created_at, a.moderation_status, a.is_active,
            a.views_count, a.image_urls,
            c.name as category_name, c.slug as category_slug,
            l.city, l.district, l.street, l.building,
            u.username as owner_username, u.avatar_url as owner_avatar,
            COALESCE(array_to_json(array_agg(DISTINCT jsonb_build_object('id', t.id, 'name', t.name, 'slug', t.slug))
                FILTER (WHERE t.id IS NOT NULL)), '[]'::json) as tags
        FROM ads a
        JOIN categories c ON c.id = a.category_id
        JOIN locations l ON l.id = a.location_id
        JOIN users u ON u.id = a.user_id
        LEFT JOIN ad_tags at ON at.ad_id = a.id
        LEFT JOIN tags t ON t.id = at.tag_id
        """

        where_conditions = []
        params = []

        where_conditions.append("a.is_active = $1")
        params.append(is_active)

        where_conditions.append("a.moderation_status = $2")
        params.append(moderation_status)

        if search and len(search.strip()) >= 3:
            search_pattern = f"%{search.strip()}%"
            pattern_param_index = len(params) + 1
            params.append(search_pattern)

            search_condition = (
                f"(a.title % ${pattern_param_index} OR "
                f"a.description % ${pattern_param_index} OR "
                f"EXISTS ("
                f"  SELECT 1 FROM ad_tags at2 "
                f"  JOIN tags t2 ON t2.id = at2.tag_id "
                f"  WHERE at2.ad_id = a.id AND t2.name % ${pattern_param_index}"
                f"))"
            )
            where_conditions.append(search_condition)

        if category_id is not None:
            where_conditions.append(f"a.category_id = ${len(params) + 1}")
            params.append(category_id)

        if min_price is not None:
            where_conditions.append(f"a.price >= ${len(params) + 1}::numeric")
            params.append(float(min_price))

        if max_price is not None:
            where_conditions.append(f"a.price <= ${len(params) + 1}::numeric")
            params.append(float(max_price))

        if min_views is not None:
            where_conditions.append(f"a.views_count >= ${len(params) + 1}")
            params.append(min_views)

        if owner_id is not None:
            where_conditions.append(f"a.user_id = ${len(params) + 1}::uuid")
            params.append(str(owner_id))

        if created_after:
            where_conditions.append(f"a.created_at >= ${len(params) + 1}")
            params.append(created_after)

        if created_before:
            where_conditions.append(f"a.created_at <= ${len(params) + 1}")
            params.append(created_before)

        if city:
            where_conditions.append(f"LOWER(l.city) % ${len(params) + 1}")
            params.append(city.strip().lower())

        if has_images is not None:
            if has_images:
                where_conditions.append(
                    "(a.image_urls IS NOT NULL AND a.image_urls != '' AND a.image_urls != '[]')")
            else:
                where_conditions.append(
                    "(a.image_urls IS NULL OR a.image_urls = '' OR a.image_urls = '[]')")

        if tag_ids:
            where_conditions.append(
                f"a.id IN (SELECT ad_id FROM ad_tags WHERE tag_id = ANY(${len(params) + 1}) "
                f"GROUP BY ad_id HAVING COUNT(DISTINCT tag_id) = ${len(params) + 2})"
            )
            params.append(tag_ids)
            params.append(len(tag_ids))

        if where_conditions:
            query += "\nWHERE " + " AND ".join(where_conditions)

        query += "\nGROUP BY a.id, c.id, l.id, u.id"

        sort_mapping = {
            "price_asc": "ORDER BY a.price ASC",
            "price_desc": "ORDER BY a.price DESC",
            "newest": "ORDER BY a.created_at DESC",
            "oldest": "ORDER BY a.created_at ASC",
            "views": "ORDER BY a.views_count DESC"
        }
        query += "\n" + sort_mapping.get(sort_by, "ORDER BY a.created_at DESC")

        query += f"\nLIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, skip])

        ads = await db.fetch(query, *params)

        result = []
        for ad in ads:
            result.append(await build_ad_from_row(ad))

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении объявлений: {str(e)}"
        )


@router.get("/{ad_id}", response_model=AdOut)
async def get_ad(ad_id: UUID = Path(..., description="ID объявления")):
    """Получение объявления по ID"""

    try:
        query = """
        SELECT
            a.id, a.user_id, a.category_id, a.location_id, a.title, a.description,
            a.price, a.currency, a.created_at, a.moderation_status, a.is_active,
            a.views_count, a.image_urls,
            c.name as category_name, c.slug as category_slug,
            l.city, l.district, l.street, l.building,
            u.username as owner_username, u.avatar_url as owner_avatar,
            COALESCE(array_to_json(array_agg(DISTINCT jsonb_build_object('id', t.id, 'name', t.name, 'slug', t.slug))
                FILTER (WHERE t.id IS NOT NULL)), '[]'::json) as tags
        FROM ads a
        JOIN categories c ON c.id = a.category_id
        JOIN locations l ON l.id = a.location_id
        JOIN users u ON u.id = a.user_id
        LEFT JOIN ad_tags at ON at.ad_id = a.id
        LEFT JOIN tags t ON t.id = at.tag_id
        WHERE a.id = $1::uuid
        GROUP BY a.id, c.id, l.id, u.id
        """

        ad = await db.fetchrow(query, str(ad_id))

        if not ad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объявление не найдено"
            )

        # счетчик просмотров
        await db.execute(
            "INSERT INTO views (ad_id, user_id) VALUES ($1, $2)",
            str(ad_id), None
        )

        return await build_ad_from_row(ad)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении объявления: {str(e)}"
        )


@router.put("/{ad_id}", response_model=AdOut)
async def update_ad(
    ad_id: UUID = Path(..., description="ID объявления"),
    ad: AdUpdate = Body(..., description="Данные для обновления объявления"),
    user_id: UUID = Query(..., description="ID пользователя (владельца)"),
):
    """Обновление объявления"""

    existing_ad = await db.fetchrow(
        "SELECT id, user_id FROM ads WHERE id = $1",
        str(ad_id)
    )
    if not existing_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )

    update_fields = []
    params = []
    param_count = 1

    if ad.title:
        update_fields.append(f"title = ${param_count}")
        params.append(ad.title)
        param_count += 1

    if ad.description:
        update_fields.append(f"description = ${param_count}")
        params.append(ad.description)
        param_count += 1

    if ad.price:
        update_fields.append(f"price = ${param_count}")
        params.append(ad.price)
        param_count += 1

    if ad.currency:
        update_fields.append(f"currency = ${param_count}")
        params.append(ad.currency)
        param_count += 1

    if ad.category_id:
        category_exists = await db.fetchrow(
            "SELECT id FROM categories WHERE id = $1",
            ad.category_id
        )
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        update_fields.append(f"category_id = ${param_count}")
        params.append(ad.category_id)
        param_count += 1

    if ad.location_id:
        location_exists = await db.fetchrow(
            "SELECT id FROM locations WHERE id = $1",
            ad.location_id
        )
        if not location_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Локация не найдена"
            )
        update_fields.append(f"location_id = ${param_count}")
        params.append(ad.location_id)
        param_count += 1

    if ad.moderation_status:
        update_fields.append(f"moderation_status = ${param_count}")
        params.append(ad.moderation_status)
        param_count += 1

    if ad.is_active is not None:
        update_fields.append(f"is_active = ${param_count}")
        params.append(ad.is_active)
        param_count += 1

    if ad.image_urls is not None:
        update_fields.append(f"image_urls = ${param_count}")
        params.append(ad.image_urls)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    params.append(str(ad_id))
    query = f"""
    UPDATE ads
    SET {', '.join(update_fields)}
    WHERE id = ${param_count}
    RETURNING id
    """

    try:
        updated_ad = await db.fetchrow(query, *params)
        if not updated_ad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Объявление не найдено"
            )

        if ad.tag_ids is not None:
            await db.execute(
                "DELETE FROM ad_tags WHERE ad_id = $1",
                str(ad_id)
            )
            for tag_id in ad.tag_ids:
                await db.execute(
                    "INSERT INTO ad_tags (ad_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    str(ad_id), tag_id
                )

        full_ad = await get_full_ad_info(ad_id)
        return full_ad
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении объявления: {str(e)}"
        )


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: UUID = Path(..., description="ID объявления"),
    user_id: UUID = Query(..., description="ID владельца объявления"),
):
    """Удаление объявления (только для владельца или администратора)"""
    existing_ad = await db.fetchrow(
        "SELECT id, user_id FROM ads WHERE id = $1",
        str(ad_id)
    )
    if not existing_ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )

    query = "DELETE FROM ads WHERE id = $1"

    try:
        await db.execute(query, str(ad_id))
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении объявления: {str(e)}"
        )
