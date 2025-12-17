from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal


class LocationBase(BaseModel):
    city: str
    district: Optional[str] = None
    street: str
    building: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    postal_code: Optional[str] = None

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Широта должна быть в диапазоне от -90 до 90')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180')
        return v


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    postal_code: Optional[str] = None


class LocationOut(LocationBase):
    id: int

    class Config:
        from_attributes = True
