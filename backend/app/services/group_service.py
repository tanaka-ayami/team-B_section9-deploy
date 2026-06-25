from sqlalchemy.orm import Session

from app.models.user import GroupMember


def get_group_member_user_ids(db: Session, group_id) -> list:
    """
    指定したグループに所属する、全メンバーのユーザーIDを取得する。
    """
    members = (
        db.query(GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return [m.user_id for m in members]