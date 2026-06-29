import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    name: str


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime


class GroupMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    display_name: str
    joined_at: datetime