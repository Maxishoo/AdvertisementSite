from fastapi import (APIRouter, HTTPException, status, Query, Path, Body)
from uuid import UUID
from typing import List, Optional
from app.db.session import db
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Создание нового пользователя"""
    existing_email = await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        user.email
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )

    existing_phone = await db.fetchrow(
        "SELECT id FROM users WHERE phone = $1",
        user.phone
    )
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Телефон уже зарегистрирован"
        )

    hashed_password = get_password_hash(user.password)

    query = """
    INSERT INTO users (
        email, phone, password_hash, username, first_name, last_name,
        role, is_verified, is_banned, avatar_url
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING id, email, username, first_name, last_name, role,
              created_at, is_verified, is_banned, avatar_url
    """

    params = (
        user.email,
        user.phone,
        hashed_password,
        user.username,
        user.first_name,
        user.last_name,
        user.role,
        user.is_verified,
        user.is_banned,
        user.avatar_url
    )

    try:
        new_user = await db.fetchrow(query, *params)
        return dict(new_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID = Path(...,
                         description="Уникальный идентификатор пользователя")
):
    """Получение информации о пользователе по ID"""
    query = """
    SELECT id, email, username, first_name, last_name, role,
           created_at, is_verified, is_banned, avatar_url
    FROM users
    WHERE id = $1
    """

    user = await db.fetchrow(query, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    return dict(user)


@router.get("/", response_model=List[UserOut])
async def get_users(
    skip: int = Query(
        0, ge=0, description="Количество пользователей, которые нужно пропустить"),
    limit: int = Query(
        100, ge=1, le=100, description="Максимальное количество возвращаемых пользователей"),
    role: Optional[str] = Query(
        None, description="Фильтр по роли пользователя (например, 'admin', 'moderator', 'user')."),
    is_banned: Optional[bool] = Query(
        None, description="Фильтр по статусу блокировки"),
    search: Optional[str] = Query(
        None, min_length=3, description="Строка для поиска"),
):
    """Получение списка пользователей"""
    query_parts = [
        "SELECT id, email, username, first_name, last_name, role, created_at, is_verified, is_banned, avatar_url FROM users WHERE 1=1"
    ]
    params = []
    param_count = 1

    if search is not None:
        query_parts.append(
            f" AND (username || ' ' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) % ${param_count}"
        )
        params.append(search)
        param_count += 1

    if role:
        query_parts.append(f" AND role = ${param_count}")
        params.append(role)
        param_count += 1

    if is_banned is not None:
        query_parts.append(f" AND is_banned = ${param_count}")
        params.append(is_banned)
        param_count += 1

    query_parts.append(
        f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
    )
    params.extend([limit, skip])

    query = " ".join(query_parts)
    users = await db.fetch(query, *params)

    return [dict(user) for user in users]


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID = Path(..., description="ID пользователя"),
    user: UserUpdate = Body(..., description="Данные для обновления"),
):
    """Обновление информации о пользователе"""
    existing_user = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(user_id)
    )
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    update_fields = []
    params = []
    param_count = 1

    if user.email:
        existing_email = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1 AND id != $2",
            user.email, str(user_id)
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже используется другим пользователем"
            )
        update_fields.append(f"email = ${param_count}")
        params.append(user.email)
        param_count += 1

    if user.phone:
        existing_phone = await db.fetchrow(
            "SELECT id FROM users WHERE phone = $1 AND id != $2",
            user.phone, str(user_id)
        )
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Телефон уже используется другим пользователем"
            )
        update_fields.append(f"phone = ${param_count}")
        params.append(user.phone)
        param_count += 1

    if user.username:
        update_fields.append(f"username = ${param_count}")
        params.append(user.username)
        param_count += 1

    if user.first_name:
        update_fields.append(f"first_name = ${param_count}")
        params.append(user.first_name)
        param_count += 1

    if user.last_name:
        update_fields.append(f"last_name = ${param_count}")
        params.append(user.last_name)
        param_count += 1

    if user.role:
        update_fields.append(f"role = ${param_count}")
        params.append(user.role)
        param_count += 1

    if user.is_verified is not None:
        update_fields.append(f"is_verified = ${param_count}")
        params.append(user.is_verified)
        param_count += 1

    if user.is_banned is not None:
        update_fields.append(f"is_banned = ${param_count}")
        params.append(user.is_banned)
        param_count += 1

    if user.avatar_url is not None:
        update_fields.append(f"avatar_url = ${param_count}")
        params.append(user.avatar_url)
        param_count += 1

    if user.password:
        hashed_password = get_password_hash(user.password)
        update_fields.append(f"password_hash = ${param_count}")
        params.append(hashed_password)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    params.append(str(user_id))
    query = f"""
    UPDATE users
    SET {', '.join(update_fields)}
    WHERE id = ${param_count}
    RETURNING id, email, username, first_name, last_name, role,
              created_at, is_verified, is_banned, avatar_url
    """

    try:
        updated_user = await db.fetchrow(query, *params)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        return dict(updated_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении пользователя: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID = Path(..., description="Идентификатор пользователя")):
    """Удаление пользователя"""

    existing_user = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1",
        str(user_id)
    )
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    query = "DELETE FROM users WHERE id = $1"

    try:
        await db.execute(query, str(user_id))
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении пользователя: {str(e)}"
        )
