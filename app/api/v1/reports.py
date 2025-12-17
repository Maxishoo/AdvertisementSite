from fastapi import APIRouter, HTTPException, status, Query, Path
from uuid import UUID
from typing import List, Optional
from app.db.session import db

router = APIRouter(prefix="/reports", tags=["Жалобы"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    ad_id: UUID = Query(..., description="ID объявления"),
    complainant_id: UUID = Query(...,
                                 description="ID жалующегося пользователя"),
    reason: str = Query(
        "APPROVED",
        regex="^(FRAUD|INAPPROPRIATE_CONTENT|SPAM|COPYRIGHT|FAKE_PROFILE|OTHER)$",
        description="Причина жалобы"
    ),
    description: str = Query("without a description",
                             description="Описание жалобы"),
):
    """Создание новой жалобы"""
    ad_exists = await db.fetchrow(
        "SELECT id, user_id FROM ads WHERE id = $1 AND is_active = true",
        str(ad_id)
    )
    if not ad_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено или неактивно"
        )

    user_exists = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(complainant_id)
    )
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if str(complainant_id) == str(ad_exists["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя пожаловаться на собственное объявление"
        )

    valid_reasons = {'FRAUD', 'INAPPROPRIATE_CONTENT',
                     'SPAM', 'COPYRIGHT', 'FAKE_PROFILE', 'OTHER'}
    if reason not in valid_reasons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимая причина жалобы"
        )

    query = """
    INSERT INTO reports (
        ad_id, complainant_id, reason, description, status
    ) VALUES ($1, $2, $3, $4, 'PENDING')
    RETURNING id, ad_id, complainant_id, reported_user_id, reason, description, status, created_at
    """

    try:
        new_report = await db.fetchrow(
            query,
            str(ad_id),
            str(complainant_id),
            reason,
            description
        )
        return dict(new_report)
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg or "already has an active report" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У вас уже есть активная жалоба на это объявление"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании жалобы"
        )


@router.get("/user/{user_id}", response_model=List[dict])
async def get_user_reports(
    user_id: UUID = Path(..., description="идентификатор пользователя"),
    status: Optional[str] = Query(
        None, regex="^(PENDING|IN_PROGRESS|RESOLVED|REJECTED)$", description="статус жалобы")
):
    """Получение жалоб пользователя"""
    base_query = """
    SELECT
        r.id, r.ad_id, r.reason, r.description, r.status, r.created_at,
        a.title as ad_title, a.price as ad_price,
        u.username as reported_username
    FROM reports r
    JOIN ads a ON a.id = r.ad_id
    JOIN users u ON u.id = r.reported_user_id
    WHERE r.complainant_id = $1
    """

    params = [str(user_id)]
    param_index = 2

    if status:
        base_query += " AND r.status = $" + str(param_index)
        params.append(status)
        param_index += 1

    base_query += " ORDER BY r.created_at DESC"
    query = base_query

    try:
        reports = await db.fetch(query, *params)
        return [dict(report) for report in reports]
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении жалоб: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении жалоб"
        )


@router.get("/moderation", response_model=List[dict])
async def get_reports_for_moderation(
    status: str = Query(
        "PENDING",
        regex="^(PENDING|IN_PROGRESS|RESOLVED|REJECTED)$",
        description="Статус модерации"
    ),
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(20, ge=1, le=100, description="Лимит записей"),
):
    """Получение жалоб для модерации"""

    query = """
    SELECT
        r.id, r.ad_id, r.complainant_id, r.reported_user_id, r.reason,
        r.description, r.status, r.created_at,
        a.title as ad_title, a.description as ad_description, a.price as ad_price,
        c.username as complainant_username,
        u.username as reported_username
    FROM reports r
    JOIN ads a ON a.id = r.ad_id
    JOIN users c ON c.id = r.complainant_id
    JOIN users u ON u.id = r.reported_user_id
    WHERE r.status = $1
    ORDER BY r.created_at DESC
    LIMIT $2 OFFSET $3
    """

    try:
        reports = await db.fetch(query, status, limit, skip)
        return [dict(report) for report in reports]
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении жалоб для модерации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении жалоб для модерации"
        )


@router.put("/{report_id}/resolve")
async def resolve_report(
    report_id: UUID = Path(..., description="ID жалобы"),
    moderator_id: UUID = Query(..., description="ID модератора"),
    status: str = Query(
        ...,
        regex="^(RESOLVED|REJECTED|IN_PROGRESS)$",
        description="Новый статус жалобы"
    ),
    resolution_comment: Optional[str] = Query(
        None, description="Комментарий модератора"),
):
    """Разрешение жалобы (только для модераторов)"""

    report_exists = await db.fetchrow(
        "SELECT id, status FROM reports WHERE id = $1",
        str(report_id)
    )
    if not report_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жалоба не найдена"
        )

    if report_exists["status"] not in ["PENDING", "IN_PROGRESS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Жалоба уже обработана"
        )

    query = """
    UPDATE reports
    SET status = $1, resolution_comment = $2, reviewed_at = NOW(), reviewed_by = $3
    WHERE id = $4
    RETURNING id, status, resolution_comment
    """

    try:
        updated_report = await db.fetchrow(
            query,
            status,
            resolution_comment,
            str(moderator_id),
            str(report_id)
        )
        return dict(updated_report)
    except Exception as e:
        import logging
        logging.error(f"Ошибка при обновлении жалобы: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении жалобы"
        )
