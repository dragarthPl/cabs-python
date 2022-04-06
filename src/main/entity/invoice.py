from decimal import Decimal

from src.main.common.base_entity import BaseEntity


class Invoice(BaseEntity, table=True):
    amount: Decimal
    subject_name: str

    def __init__(self, amount: Decimal, subject_name: str):
        self.amount = amount
        self.subject_name = subject_name
