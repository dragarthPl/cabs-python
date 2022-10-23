from decimal import Decimal

from injector import inject

from invocing.invoice import Invoice
from invocing.invoice_repository import InvoiceRepositoryImp


class InvoiceGenerator:
    invoice_repository: InvoiceRepositoryImp

    @inject
    def __init__(self, invoice_repository: InvoiceRepositoryImp):
        self.invoice_repository = invoice_repository

    def generate(self, amount: int, subject_name: str):
        return self.invoice_repository.save(Invoice(amount=Decimal(amount), subject_name=subject_name))
