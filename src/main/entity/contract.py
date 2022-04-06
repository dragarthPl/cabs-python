from datetime import datetime
from enum import Enum
from typing import Set

from src.main.common.base_entity import BaseEntity


class Contract(BaseEntity, table=True):
    class Status(Enum):
        NEGOTIATIONS_IN_PROGRESS= 1
        REJECTED = 2
        ACCEPTED = 3

    attachments: Set[ContractAttachment]
    partner_name: str
    subject: str
    creation_date: datetime
    accepted_at: datetime
    rejected_at: datetime
    change_date: datetime
    status: Status = Status.NEGOTIATIONS_IN_PROGRESS
    contract_no: str
