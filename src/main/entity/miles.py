import abc
from datetime import datetime


class Miles(metaclass=abc.ABCMeta):
    def get_amount_for(self, moment: datetime) -> int:
        raise NotImplementedError

    def subtract(self, amount: int,  moment: datetime) -> 'Miles':
        raise NotImplementedError

    def expires_at(self) -> datetime:
        raise NotImplementedError
