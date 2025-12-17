from fastapi import APIRouter, HTTPException, status, Query, Path, Body
from typing import List, Optional
from app.db.session import db
from app.schemas.tag import TagCreate, TagUpdate, TagOut
import re

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(tag: TagCreate):
    """Создание нового тега"""
    existing_name = await db.fetchrow(
        "SELECT id FROM tags WHERE name = $1",
        tag.name
    )
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тег с таким названием уже существует"
        )

    existing_slug = await db.fetchrow(
        "SELECT id FROM tags WHERE slug = $1",
        tag.slug
    )
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тег с таким slug уже существует"
        )

    query = """
    INSERT INTO tags (name, slug)
    VALUES ($1, $2)
    RETURNING id, name, slug
    """

    try:
        new_tag = await db.fetchrow(query, tag.name, tag.slug)
        return dict(new_tag)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании тега: {str(e)}"
        )


@router.get("/{tag_id}", response_model=TagOut)
async def get_tag(tag_id: int):
    """Получение тега по ID"""
    query = """
    SELECT id, name, slug
    FROM tags
    WHERE id = $1
    """

    tag = await db.fetchrow(query, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )

    return dict(tag)


@router.get("/", response_model=List[TagOut])
async def get_tags(
    skip: int = Query(
        0, ge=0, description="Количество тегов, которые нужно пропустить"),
    limit: int = Query(
        100, ge=1, le=100, description="Максимальное количество возвращаемых тегов"),
    search: Optional[str] = Query(
        None, min_length=3, description="Подстрока для фильтрации тегов по названию и slug"),
):
    """Получение списка тегов с подстроковым поиском по name и slug"""
    base_query = """
    SELECT id, name, slug
    FROM tags
    """
    where_clauses = []
    params = []
    param_index = 1

    if search is not None:
        clean_search = search.strip()
        if not re.match(r'^[а-яА-Яa-zA-Z0-9\s\-_]+$', clean_search):
            clean_search = re.sub(
                r'[^а-яА-Яa-zA-Z0-9\s\-_]', ' ', clean_search).strip()

        if len(clean_search) >= 3:
            pattern = f"%{clean_search}%"
            where_clauses.append(
                f"(name ILIKE ${param_index} OR slug ILIKE ${param_index})"
            )
            params.append(pattern)
            param_index += 1

    query_parts = [base_query]
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    query_parts.append("ORDER BY name ASC")
    query_parts.append(f"LIMIT ${param_index} OFFSET ${param_index + 1}")
    params.extend([limit, skip])

    query = " ".join(query_parts)

    try:
        tags = await db.fetch(query, *params)
        return [dict(tag) for tag in tags]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении тегов: {str(e)}"
        )


@router.put("/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: int = Path(..., description="ID тега"),
    tag: TagUpdate = Body(..., description="Данные для обновления")
):
    """Обновление тега"""
    existing_tag = await db.fetchrow(
        "SELECT id FROM tags WHERE id = $1",
        tag_id
    )
    if not existing_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )

    update_clauses = []
    params = []
    param_index = 1

    if tag.name is not None:
        existing_name = await db.fetchrow(
            "SELECT id FROM tags WHERE name = $1 AND id != $2",
            tag.name, tag_id
        )
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Тег с таким названием уже существует"
            )
        update_clauses.append("name = $" + str(param_index))
        params.append(tag.name)
        param_index += 1

    if tag.slug is not None:
        existing_slug = await db.fetchrow(
            "SELECT id FROM tags WHERE slug = $1 AND id != $2",
            tag.slug, tag_id
        )
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Тег с таким slug уже существует"
            )
        update_clauses.append("slug = $" + str(param_index))
        params.append(tag.slug)
        param_index += 1

    if not update_clauses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    set_clause = ", ".join(update_clauses)
    params.append(tag_id)

    query = f"""
    UPDATE tags
    SET {set_clause}
    WHERE id = ${param_index}
    RETURNING id, name, slug
    """

    try:
        updated_tag = await db.fetchrow(query, *params)
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тег не найден"
            )
        return dict(updated_tag)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении тега: {str(e)}"
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int = Path(..., description="Идентификатор тега")):
    """Удаление тега"""
    existing_tag = await db.fetchrow(
        "SELECT id FROM tags WHERE id = $1",
        tag_id
    )
    if not existing_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )

    query = "DELETE FROM tags WHERE id = $1"

    try:
        await db.execute(query, tag_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении тега: {str(e)}"
        )
