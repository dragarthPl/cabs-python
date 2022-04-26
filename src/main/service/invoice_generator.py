from decimal import Decimal

from fastapi import Depends

from entity.invoice import Invoice
from repository.invoice_repository import InvoiceRepositoryImp


class InvoiceGenerator:
    invoice_repository: InvoiceRepositoryImp

    def __init__(self, invoice_repository: InvoiceRepositoryImp = Depends(InvoiceRepositoryImp)):
        self.invoice_repository = invoice_repository

    def generate(self, amount: int, subject_name: str):
        return self.invoice_repository.save(Invoice(amount=Decimal(amount), subject_name=subject_name))
