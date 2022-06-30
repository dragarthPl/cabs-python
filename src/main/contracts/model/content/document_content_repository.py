from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from contracts.model.content.document_content import DocumentContent
from core.database import get_session


class DocumentContentRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, document_content: DocumentContent) -> Optional[DocumentContent]:
        self.session.add(document_content)
        self.session.commit()
        self.session.refresh(document_content)
        return document_content

    def get_one(self, document_header_id) -> Optional[DocumentContent]:
        statement = self.session.query(DocumentContent).where(DocumentContent.id == document_header_id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()
