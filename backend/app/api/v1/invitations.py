"""
招待API（issue #16 MVP外）
- GET  /v1/invitations/{token}          認証不要・招待ページ表示用
- POST /v1/invitations/{token}/accept
- POST /v1/invitations/{token}/reject
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.errors import APIError
from app.db.base import get_db
from app.models.invitation import Invitation
from app.models.user import Group, GroupMember, User
from app.schemas.invitation import InvitationPublicRead

router = APIRouter(prefix="/invitations", tags=["invitations"])


def _get_invitation_or_404(db: Session, token: str) -> Invitation:
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if invitation is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "招待が見つかりません")
    return invitation


def _ensure_not_expired(invitation: Invitation) -> None:
    if invitation.expires_at < datetime.utcnow():
        raise APIError(410, "INVITATION_EXPIRED", "招待の有効期限が切れています")


@router.get("/{token}", response_model=InvitationPublicRead)
def get_invitation(token: str, db: Session = Depends(get_db)):
    invitation = _get_invitation_or_404(db, token)
    group = db.query(Group).filter(Group.id == invitation.group_id).first()
    inviter = db.query(User).filter(User.id == invitation.invited_by).first()

    return InvitationPublicRead(
        group_name=group.name if group else "(不明なグループ)",
        invited_by_email=inviter.email if inviter else "(不明なユーザー)",
        status=invitation.status,
        expires_at=invitation.expires_at,
    )


@router.post("/{token}/accept")
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invitation = _get_invitation_or_404(db, token)
    _ensure_not_expired(invitation)

    if invitation.status != "pending":
        raise APIError(409, "INVITATION_ALREADY_HANDLED", "この招待は既に処理済みです")

    already_member = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == invitation.group_id,
            GroupMember.user_id == current_user.id,
        )
        .first()
    )
    if already_member is None:
        db.add(GroupMember(group_id=invitation.group_id, user_id=current_user.id))

    invitation.status = "accepted"
    db.commit()

    return {"group_id": invitation.group_id, "status": "accepted", "message": "グループに参加しました。"}


@router.post("/{token}/reject")
def reject_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invitation = _get_invitation_or_404(db, token)
    _ensure_not_expired(invitation)

    if invitation.status != "pending":
        raise APIError(409, "INVITATION_ALREADY_HANDLED", "この招待は既に処理済みです")

    invitation.status = "rejected"
    db.commit()

    return {"status": "rejected"}