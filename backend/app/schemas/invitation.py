import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InvitationCreate(BaseModel):
    invitee_email: str  # EmailStrから変更（email-validator未導入のため）


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    invitee_email: str
    status: str
    expires_at: datetime
    created_at: datetime


class InvitationPublicRead(BaseModel):
    """GET /invitations/{token}：認証不要の招待ページ表示用"""
    group_name: str
    invited_by_email: str
    status: str
    expires_at: datetime