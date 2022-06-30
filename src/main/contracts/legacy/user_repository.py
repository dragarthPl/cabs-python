from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from contracts.legacy.user import User
from core.database import get_session


class UserRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, user: User) -> Optional[User]:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_one(self, user_id) -> Optional[User]:
        statement = self.session.query(User).where(User.id == user_id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()
