from decimal import Decimal
from typing import Optional

from common.base_entity import BaseEntity


class Invoice(BaseEntity, table=True):
    amount: Optional[Decimal]
    subject_name: Optional[str]

    def __eq__(self, o):
        if not isinstance(o, Invoice):
            return False
        return self.id is not None and self.id == o.id
