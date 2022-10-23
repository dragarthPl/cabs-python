from typing import Optional

from injector import inject

from invocing.invoice import Invoice
from sqlmodel import Session


class InvoiceRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def save(self, invoice: Invoice) -> Optional[Invoice]:
        self.session.add(invoice)
        self.session.commit()
        self.session.refresh(invoice)
        return invoice
