from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional
from app.db.session import db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from uuid import UUID
import re

router = APIRouter(prefix="/categories", tags=["Категории"])


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate):
    """Создание новой категории"""
    existing_name = await db.fetchrow(
        "SELECT id FROM categories WHERE name = $1",
        category.name
    )
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким названием уже существует"
        )

    existing_slug = await db.fetchrow(
        "SELECT id FROM categories WHERE slug = $1",
        category.slug
    )
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким slug уже существует"
        )

    query = """
    INSERT INTO categories (name, slug, icon_url, description)
    VALUES ($1, $2, $3, $4)
    RETURNING id, name, slug, icon_url, description
    """

    try:
        new_category = await db.fetchrow(
            query,
            category.name,
            category.slug,
            category.icon_url,
            category.description
        )
        return dict(new_category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании категории: {str(e)}"
        )


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: int = Path(..., description="ID категории")):
    """Получение категории по ID"""
    query = """
    SELECT id, name, slug, icon_url, description
    FROM categories
    WHERE id = $1
    """

    category = await db.fetchrow(query, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )

    return dict(category)


@router.get("/", response_model=List[CategoryOut])
async def get_categories(
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=100, description="Лимит записей"),
    search: Optional[str] = Query(
        None, min_length=3, description="Поиск по названию (мин. 3 символа)"),
):
    """Получение списка категорий с поиском по name и slug"""
    base_query = """
    SELECT id, name, slug, icon_url, description
    FROM categories
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
        categories = await db.fetch(query, *params)
        return [dict(category) for category in categories]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении категорий: {str(e)}"
        )


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int = Path(..., description="ID категории"),
    category: CategoryUpdate = Body(..., description="Данные для обновления"),
):
    """Обновление категории"""
    existing_category = await db.fetchrow(
        "SELECT id FROM categories WHERE id = $1",
        category_id
    )
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )

    update_clauses = []
    params = []
    param_index = 1

    if category.name is not None:
        existing_name = await db.fetchrow(
            "SELECT id FROM categories WHERE name = $1 AND id != $2",
            category.name, category_id
        )
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория с таким названием уже существует"
            )
        update_clauses.append("name = $" + str(param_index))
        params.append(category.name)
        param_index += 1

    if category.slug is not None:
        existing_slug = await db.fetchrow(
            "SELECT id FROM categories WHERE slug = $1 AND id != $2",
            category.slug, category_id
        )
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория с таким slug уже существует"
            )
        update_clauses.append("slug = $" + str(param_index))
        params.append(category.slug)
        param_index += 1

    if category.icon_url is not None:
        update_clauses.append("icon_url = $" + str(param_index))
        params.append(category.icon_url)
        param_index += 1

    if category.description is not None:
        update_clauses.append("description = $" + str(param_index))
        params.append(category.description)
        param_index += 1

    if not update_clauses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    set_clause = ", ".join(update_clauses)
    params.append(category_id)

    query = f"""
    UPDATE categories
    SET {set_clause}
    WHERE id = ${param_index}
    RETURNING id, name, slug, icon_url, description
    """

    try:
        updated_category = await db.fetchrow(query, *params)
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена"
            )
        return dict(updated_category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении категории: {str(e)}"
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int = Path(..., description="ID категории")):
    """Удаление категории"""
    existing_category = await db.fetchrow(
        "SELECT id FROM categories WHERE id = $1",
        category_id
    )
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )

    query = "DELETE FROM categories WHERE id = $1"

    try:
        await db.execute(query, category_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении категории: {str(e)}"
        )
