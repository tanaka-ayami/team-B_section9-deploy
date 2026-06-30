"""
グループAPI（issue #16）
- POST   /v1/groups
- GET    /v1/groups
- DELETE /v1/groups/{group_id}
- GET    /v1/groups/{group_id}/members
- POST   /v1/groups/{group_id}/invite   ※MVP外（issueの /groups/{group_id}/invitations から
  API設計書のパスに統一）
"""
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.deps_db import get_current_user
from app.core.errors import APIError
from app.db.base import get_db
from app.models.invitation import Invitation
from app.models.user import Group, GroupMember, User
from app.schemas.group import GroupCreate, GroupMemberRead, GroupRead
from app.schemas.invitation import InvitationCreate, InvitationRead
from app.services.sendgrid_service import send_invitation_email

router = APIRouter(prefix="/groups", tags=["groups"])

INVITATION_EXPIRES_DAYS = 7


def _get_group_or_404(db: Session, group_id: uuid.UUID) -> Group:
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "グループが見つかりません")
    return group


def _require_member(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    is_member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if is_member is None:
        raise APIError(403, "FORBIDDEN_GROUP_ACTION", "このグループのメンバーではありません")


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    body: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = Group(name=body.name, created_by=current_user.id)
    db.add(group)
    db.flush()  # group.id を確定させてから group_members に登録する

    db.add(GroupMember(group_id=group.id, user_id=current_user.id))
    db.commit()
    db.refresh(group)
    return group


@router.get("", response_model=list[GroupRead])
def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    if group.created_by != current_user.id:
        raise APIError(403, "FORBIDDEN_GROUP_ACTION", "グループ作成者のみ削除できます")

    db.delete(group)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # documents/categoriesがgroup_idを参照したままだと外部キー制約で削除できない
        raise APIError(
            409,
            "GROUP_DELETE_CONFLICT",
            "このグループに紐づく書類またはカテゴリが存在するため削除できません",
        )


@router.get("/{group_id}/members", response_model=list[GroupMemberRead])
def list_group_members(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_or_404(db, group_id)
    _require_member(db, group_id, current_user.id)

    rows = (
        db.query(GroupMember, User.email)
        .join(User, User.id == GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return [
        GroupMemberRead(
            id=member.id,
            group_id=member.group_id,
            user_id=member.user_id,
            email=email,
            joined_at=member.joined_at,
        )
        for member, email in rows
    ]


@router.post(
    "/{group_id}/invite",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_to_group(
    group_id: uuid.UUID,
    body: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    _require_member(db, group_id, current_user.id)

    invitation = Invitation(
        group_id=group_id,
        invited_by=current_user.id,
        invitee_email=body.invitee_email,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=INVITATION_EXPIRES_DAYS),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    send_invitation_email(
        to_email=invitation.invitee_email,
        group_name=group.name,
        token=invitation.token,
    )

    return invitation