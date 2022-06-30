from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from contracts.model.document_header import DocumentHeader
from core.database import get_session


class DocumentHeaderRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, document_header: DocumentHeader) -> Optional[DocumentHeader]:
        self.session.add(document_header)
        self.session.commit()
        self.session.refresh(document_header)
        return document_header

    def get_one(self, document_header_id) -> Optional[DocumentHeader]:
        statement = self.session.query(DocumentHeader).where(DocumentHeader.id == document_header_id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()
