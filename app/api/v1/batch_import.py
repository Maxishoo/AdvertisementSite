from typing import List
from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from app.db.session import db
import asyncpg
from app.schemas.ad import AdCreate2

router = APIRouter(prefix="/batch-import", tags=["Батчевая загрузка данных"])


@router.post("/ads", status_code=status.HTTP_201_CREATED)
async def batch_create_ads(
    ads: List[AdCreate2] = Body(...,
                                description="Список объявлений для массовой загрузки"),
):
    """
    Массовая загрузка объявлений
    """
    if not ads:
        raise HTTPException(
            status_code=400, detail="Список объявлений со всеми полями")

    user_ids = set()
    category_ids = set()
    location_ids = set()
    all_tag_ids = set()

    for ad in ads:
        user_ids.add(ad.user_id)
        category_ids.add(ad.category_id)
        location_ids.add(ad.location_id)
        if ad.tag_ids:
            all_tag_ids.update(ad.tag_ids)

    if user_ids:
        existing_users = await db.fetch(
            "SELECT id FROM users WHERE id = ANY($1)",
            list(user_ids)
        )
        existing_user_ids = {row["id"] for row in existing_users}
        missing_users = user_ids - existing_user_ids
        if missing_users:
            raise HTTPException(
                status_code=400,
                detail=f"Пользователи не найдены: {sorted(missing_users)}"
            )

    if category_ids:
        existing_categories = await db.fetch(
            "SELECT id FROM categories WHERE id = ANY($1)",
            list(category_ids)
        )
        existing_category_ids = {row["id"] for row in existing_categories}
        missing_categories = category_ids - existing_category_ids
        if missing_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Категории не найдены: {sorted(missing_categories)}"
            )

    if location_ids:
        existing_locations = await db.fetch(
            "SELECT id FROM locations WHERE id = ANY($1)",
            list(location_ids)
        )
        existing_location_ids = {row["id"] for row in existing_locations}
        missing_locations = location_ids - existing_location_ids
        if missing_locations:
            raise HTTPException(
                status_code=400,
                detail=f"Локации не найдены: {sorted(missing_locations)}"
            )

    if all_tag_ids:
        existing_tags = await db.fetch(
            "SELECT id FROM tags WHERE id = ANY($1)",
            list(all_tag_ids)
        )
        existing_tag_ids = {row["id"] for row in existing_tags}
        missing_tags = all_tag_ids - existing_tag_ids
        if missing_tags:
            raise HTTPException(
                status_code=400,
                detail=f"Теги не найдены: {sorted(missing_tags)}"
            )
    # загрузка
    try:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                ad_values = []
                ad_tag_values = []

                for ad in ads:
                    ad_values.append((
                        ad.user_id,
                        ad.category_id,
                        ad.location_id,
                        ad.title,
                        ad.description,
                        ad.price,
                        ad.currency,
                        ad.moderation_status,
                        ad.is_active,
                        ad.image_urls
                    ))

                insert_query = """
                INSERT INTO ads (
                    user_id, category_id, location_id, title, description,
                    price, currency, moderation_status, is_active, image_urls
                )
                SELECT * FROM UNNEST($1::uuid[], $2::int[], $3::int[], $4::text[], 
                                  $5::text[], $6::numeric[], $7::text[],
                                  $8::text[], $9::boolean[], $10::text[])
                RETURNING id
                """

                user_ids_arr = [ad.user_id for ad in ads]
                category_ids_arr = [ad.category_id for ad in ads]
                location_ids_arr = [ad.location_id for ad in ads]
                titles_arr = [ad.title for ad in ads]
                descriptions_arr = [ad.description for ad in ads]
                prices_arr = [ad.price for ad in ads]
                currencies_arr = [ad.currency for ad in ads]
                statuses_arr = [ad.moderation_status for ad in ads]
                actives_arr = [ad.is_active for ad in ads]
                images_arr = [ad.image_urls for ad in ads]

                ad_results = await conn.fetch(
                    insert_query,
                    user_ids_arr,
                    category_ids_arr,
                    location_ids_arr,
                    titles_arr,
                    descriptions_arr,
                    prices_arr,
                    currencies_arr,
                    statuses_arr,
                    actives_arr,
                    images_arr
                )

                for idx, ad in enumerate(ads):
                    if ad.tag_ids:
                        ad_id = ad_results[idx]["id"]
                        for tag_id in ad.tag_ids:
                            ad_tag_values.append((ad_id, tag_id))

                if ad_tag_values:
                    tag_ad_ids = [row[0] for row in ad_tag_values]
                    tag_tag_ids = [row[1] for row in ad_tag_values]

                    await conn.execute(
                        """
                        INSERT INTO ad_tags (ad_id, tag_id)
                        SELECT * FROM UNNEST($1::uuid[], $2::int[])
                        """,
                        tag_ad_ids, tag_tag_ids
                    )

                ad_ids = [row["id"] for row in ad_results]

                return {
                    "success": True,
                    "created_count": len(ad_ids),
                    "total_requested": len(ads),
                    "ad_ids": ad_ids
                }

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при массовой вставке: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )
