from datetime import datetime

from src.main.dto.client_dto import ClientDTO


class AwardsAccountDTO:
    client: ClientDTO
    date: datetime
    is_active: bool
    transactions: int
