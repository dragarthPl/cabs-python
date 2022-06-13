from fastapi import Depends
from sqlmodel import Session

from core.database import get_session


class UserRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session
