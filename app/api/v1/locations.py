from fastapi import APIRouter, HTTPException, status, Query, Path, Body
from typing import List, Optional
from app.db.session import db
from app.schemas.location import LocationCreate, LocationUpdate, LocationOut
import re

router = APIRouter(prefix="/locations", tags=["Локации"])


@router.post("/", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate):
    """Создание новой локации"""

    existing_location = await db.fetchrow(
        """
        SELECT id FROM locations
        WHERE city = $1 AND district = $2 AND street = $3 AND building = $4
        """,
        location.city, location.district or None, location.street or None, location.building or None
    )
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Локация с такими параметрами уже существует"
        )

    query = """
    INSERT INTO locations (city, district, street, building, latitude, longitude, postal_code)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING id, city, district, street, building, latitude, longitude, postal_code
    """

    try:
        new_location = await db.fetchrow(
            query,
            location.city,
            location.district,
            location.street,
            location.building,
            location.latitude,
            location.longitude,
            location.postal_code
        )
        return dict(new_location)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании локации: {str(e)}"
        )


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: int = Path(..., description="ID локации")):
    """Получение локации по ID"""

    query = """
    SELECT id, city, district, street, building, latitude, longitude, postal_code 
    FROM locations
    WHERE id = $1
    """

    location = await db.fetchrow(query, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )

    return dict(location)


@router.get("/", response_model=List[LocationOut])
async def get_locations(
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=100, description="Лимит записей"),
    city: Optional[str] = Query(
        None, min_length=3, description="Фильтр по городу"),
    district: Optional[str] = Query(
        None, min_length=3, description="Фильтр по району"),
):
    """Получение списка локаций с подстроковым поиском по городу и району"""

    base_query = """
    SELECT id, city, district, street, building, latitude, longitude, postal_code 
    FROM locations
    """
    where_clauses = []
    params = []
    param_index = 1

    if city is not None:
        clean_city = city.strip()
        if not re.match(r'^[а-яА-Яa-zA-Z0-9\s\-_]+$', clean_city):
            clean_city = re.sub(r'[^а-яА-Яa-zA-Z0-9\s\-_]',
                                ' ', clean_city).strip()
        if len(clean_city) >= 3:
            pattern = f"%{clean_city}%"
            where_clauses.append(f"city ILIKE ${param_index}")
            params.append(pattern)
            param_index += 1

    if district is not None:
        clean_district = district.strip()
        if not re.match(r'^[а-яА-Яa-zA-Z0-9\s\-_]+$', clean_district):
            clean_district = re.sub(
                r'[^а-яА-Яa-zA-Z0-9\s\-_]', ' ', clean_district).strip()
        if len(clean_district) >= 3:
            pattern = f"%{clean_district}%"
            where_clauses.append(f"district ILIKE ${param_index}")
            params.append(pattern)
            param_index += 1

    query_parts = [base_query]
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    query_parts.append("ORDER BY city, district, street")
    query_parts.append(f"LIMIT ${param_index} OFFSET ${param_index + 1}")
    params.extend([limit, skip])

    query = " ".join(query_parts)

    try:
        locations = await db.fetch(query, *params)
        return [dict(location) for location in locations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при получении локаций: {str(e)}"
        )


@router.put("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: int = Path(..., description="ID локации"),
    location: LocationUpdate = Body(..., description="Изменяемые данные")
):
    """Обновление локации"""

    existing_location = await db.fetchrow(
        "SELECT id FROM locations WHERE id = $1",
        location_id
    )
    if not existing_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )

    update_clauses = []
    params = []
    param_index = 1

    if location.city is not None:
        update_clauses.append("city = $" + str(param_index))
        params.append(location.city)
        param_index += 1

    if location.district is not None:
        update_clauses.append("district = $" + str(param_index))
        params.append(location.district)
        param_index += 1

    if location.street is not None:
        update_clauses.append("street = $" + str(param_index))
        params.append(location.street)
        param_index += 1

    if location.building is not None:
        update_clauses.append("building = $" + str(param_index))
        params.append(location.building)
        param_index += 1

    if location.latitude is not None:
        if not (-90 <= location.latitude <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Широта должна быть в диапазоне от -90 до 90"
            )
        update_clauses.append("latitude = $" + str(param_index))
        params.append(location.latitude)
        param_index += 1

    if location.longitude is not None:
        if not (-180 <= location.longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Долгота должна быть в диапазоне от -180 до 180"
            )
        update_clauses.append("longitude = $" + str(param_index))
        params.append(location.longitude)
        param_index += 1

    if location.postal_code is not None:
        update_clauses.append("postal_code = $" + str(param_index))
        params.append(location.postal_code)
        param_index += 1

    if not update_clauses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет полей для обновления"
        )

    set_clause = ", ".join(update_clauses)
    params.append(location_id)

    query = f"""
    UPDATE locations
    SET {set_clause}
    WHERE id = ${param_index}
    RETURNING id, city, district, street, building, latitude, longitude, postal_code
    """

    try:
        updated_location = await db.fetchrow(query, *params)
        if not updated_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Локация не найдена"
            )
        return dict(updated_location)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении локации: {str(e)}"
        )


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int = Path(..., description="Идентификатор локации")):
    """Удаление локации"""
    existing_location = await db.fetchrow(
        "SELECT id FROM locations WHERE id = $1",
        location_id
    )
    if not existing_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )

    query = "DELETE FROM locations WHERE id = $1"

    try:
        await db.execute(query, location_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении локации: {str(e)}"
        )
