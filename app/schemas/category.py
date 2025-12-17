from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    name: str
    slug: str
    icon_url: Optional[str] = None
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None


class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True
