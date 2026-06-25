import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    group_id: uuid.UUID
    name: str = Field(max_length=50)
    color_code: str | None = Field(default=None, max_length=7)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    color_code: str | None = Field(default=None, max_length=7)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID | None
    name: str
    color_code: str | None