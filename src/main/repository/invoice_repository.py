from typing import Optional

from core.database import get_session
from entity.invoice import Invoice
from fastapi import Depends
from sqlmodel import Session


class InvoiceRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, invoice: Invoice) -> Optional[Invoice]:
        self.session.add(invoice)
        self.session.commit()
        self.session.refresh(invoice)
        return invoice
