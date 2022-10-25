from datetime import datetime

from loyalty.miles import Miles


class ConstantUntil(Miles):
    amount: int
    when_expires: datetime

    @staticmethod
    def constant_until_forever(amount: int) -> 'ConstantUntil':
        return ConstantUntil(amount, datetime.max)

    @staticmethod
    def constant_until(amount: int, when_expires: datetime) -> 'ConstantUntil':
        return ConstantUntil(amount, when_expires)

    def __init__(self, amount: int, when_expires: datetime):
        self.amount = amount
        self.when_expires = when_expires

    def get_amount_for(self, moment: datetime) -> int:
        return self.amount if self.when_expires.utctimetuple() >= moment.utctimetuple() else 0

    def subtract(self, amount: int, moment: datetime) -> Miles:
        if self.get_amount_for(moment) < amount:
            raise AttributeError("Insufficient amount of miles")
        return ConstantUntil(self.amount - amount, self.when_expires)

    def expires_at(self) -> datetime:
        return self.when_expires

    def __eq__(self, other):
        if not isinstance(other, ConstantUntil):
            return False
        return self.amount == other.amount and self.when_expires == other.when_expires
