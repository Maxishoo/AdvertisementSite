from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List, Optional
from app.db.session import db
from app.schemas.message import MessageCreate, MessageOut
from uuid import UUID
import re

router = APIRouter(prefix="/messages", tags=["Сообщения"])


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(message: MessageCreate, sender_id: UUID):
    """Создание нового сообщения"""

    sender_exists = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(sender_id)
    )
    if not sender_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отправитель не найден"
        )

    recipient_exists = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(message.recipient_id)
    )
    if not recipient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Получатель не найден"
        )

    if str(sender_id) == str(message.recipient_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отправить сообщение самому себе"
        )

    ad_exists = await db.fetchrow(
        "SELECT id, is_active FROM ads WHERE id = $1",
        str(message.ad_id)
    )
    if not ad_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено"
        )

    if not ad_exists["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отправить сообщение к неактивному объявлению"
        )

    query = """
    INSERT INTO messages (sender_id, recipient_id, ad_id, text, sent_at, is_read)
    VALUES ($1, $2, $3, $4, NOW(), false)
    RETURNING id, sender_id, recipient_id, ad_id, text, sent_at, is_read
    """

    try:
        new_message = await db.fetchrow(
            query,
            str(sender_id),
            str(message.recipient_id),
            str(message.ad_id),
            message.text
        )
        return dict(new_message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании сообщения"
        )


@router.get("/{message_id}", response_model=MessageOut)
async def get_message(message_id: UUID = Path(..., description="Идентификатор сообщения")):
    """Получение сообщения по ID"""

    query = """
    SELECT id, sender_id, recipient_id, ad_id, text, sent_at, is_read
    FROM messages
    WHERE id = $1
    """

    message = await db.fetchrow(query, str(message_id))
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено"
        )

    return dict(message)


@router.get("/user/{user_id}", response_model=List[MessageOut])
async def get_user_messages(
    user_id: UUID = Path(..., description="ID пользователя"),
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(50, ge=1, le=100, description="Лимит записей"),
    is_read: Optional[bool] = Query(None, description="Фильтр по прочтению"),
    direction: str = Query("all", regex="^(sent|received|all)$",
                           description="Направление сообщений"),
    ad_id: Optional[UUID] = Query(
        None, description="Фильтр по идентификатор объявления"),
    search: Optional[str] = Query(
        None, min_length=1, description="Поиск по тексту"),
):
    """Получение сообщений с поиском по тексту и username"""

    base_query = """
    SELECT
        m.id, m.sender_id, m.recipient_id, m.ad_id, m.text, m.sent_at, m.is_read,
        s.username as sender_username, r.username as recipient_username,
        a.title as ad_title
    FROM messages m
    JOIN users s ON s.id = m.sender_id
    JOIN users r ON r.id = m.recipient_id
    JOIN ads a ON a.id = m.ad_id
    """

    where_clauses = []
    params = []
    param_index = 1

    if direction == "sent":
        where_clauses.append(f"m.sender_id = ${param_index}")
        params.append(str(user_id))
        param_index += 1
    elif direction == "received":
        where_clauses.append(f"m.recipient_id = ${param_index}")
        params.append(str(user_id))
        param_index += 1
    else:
        where_clauses.append(
            f"(m.sender_id = ${param_index} OR m.recipient_id = ${param_index})")
        params.append(str(user_id))
        param_index += 1

    if ad_id is not None:
        where_clauses.append(f"m.ad_id = ${param_index}")
        params.append(str(ad_id))
        param_index += 1

    if is_read is not None:
        where_clauses.append(f"m.is_read = ${param_index}")
        params.append(is_read)
        param_index += 1

    if search is not None:
        clean_search = search.strip()
        if not re.match(r'^[а-яА-Яa-zA-Z0-9\s\-_]+$', clean_search):
            clean_search = re.sub(r'[^а-яА-Яa-zA-Z0-9\s\-_]', ' ', clean_search).strip()

        if len(clean_search) >= 1:
            where_clauses.append(
                f"(LOWER(m.text) % ${param_index}"
            )
            params.append(clean_search.lower())
            param_index += 1

    query_parts = [base_query]
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))
    query_parts.append("ORDER BY m.sent_at DESC")
    query_parts.append(f"LIMIT ${param_index} OFFSET ${param_index + 1}")
    params.extend([limit, skip])
    query = " ".join(query_parts)

    try:
        messages = await db.fetch(query, *params)
        return [
            {
                "id": msg["id"],
                "sender_id": msg["sender_id"],
                "recipient_id": msg["recipient_id"],
                "ad_id": msg["ad_id"],
                "text": msg["text"],
                "sent_at": msg["sent_at"],
                "is_read": msg["is_read"],
                "sender": {"username": msg["sender_username"]},
                "recipient": {"username": msg["recipient_username"]},
                "ad": {"title": msg["ad_title"]}
            }
            for msg in messages
        ]
    except Exception as e:
        import logging
        logging.error(f"Ошибка при поиске сообщений: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при поиске сообщений"
        )


@router.put("/{message_id}/read", status_code=status.HTTP_200_OK)
async def mark_message_as_read(
    message_id: UUID = Path(..., description="Идентификатор сообщения"),
    user_id: UUID = Query(..., description="Идентификатор пользователя"),
):
    """Отметить сообщение как прочитанное"""

    message = await db.fetchrow(
        """
        SELECT id, recipient_id, is_read
        FROM messages
        WHERE id = $1 AND recipient_id = $2
        """,
        str(message_id), str(user_id)
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено или вы не являетесь получателем"
        )

    if message["is_read"]:
        return {"message": "Сообщение уже прочитано"}

    query = """
    UPDATE messages
    SET is_read = true
    WHERE id = $1
    RETURNING id, is_read
    """

    try:
        updated_message = await db.fetchrow(query, str(message_id))
        return {"message": "Сообщение отмечено как прочитанное", "data": dict(updated_message)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении статуса сообщения"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID = Path(..., description="Идентификатор сообщения"),
    user_id: UUID = Query(..., description="Идентификатор пользователя")
):
    """Удаление сообщения"""

    message = await db.fetchrow(
        """
        SELECT id, sender_id, recipient_id
        FROM messages
        WHERE id = $1 AND (sender_id = $2 OR recipient_id = $2)
        """,
        str(message_id), str(user_id)
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено или у вас нет прав на удаление"
        )

    query = "DELETE FROM messages WHERE id = $1"

    try:
        await db.execute(query, str(message_id))
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении сообщения"
        )
