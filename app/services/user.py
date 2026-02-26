from sqlalchemy.orm import Session

from app.db.models import User


def get_or_create_user(db: Session, firebase_uid: str, email: str, name: str | None) -> User | None:
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user:
        if email:
            user.email = email
        if name is not None:
            user.name = name
        db.commit()
        db.refresh(user)
        return user
    user = User(firebase_uid=firebase_uid, email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_fcm_token(db: Session, user_id: int, fcm_token: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    user.fcm_token = fcm_token
    db.commit()
    db.refresh(user)
    return user
