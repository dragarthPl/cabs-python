from datetime import datetime

from entity import Miles


class TwoStepExpiringMiles(Miles):
    amount: int = 0
    when_first_half_expires: datetime
    when_expires: datetime

    def __init__(self, amount: int, when_first_half_expires: datetime, when_expires: datetime):
        self.amount = amount
        self.when_first_half_expires = when_first_half_expires
        self.when_expires = when_expires

    def get_amount_for(self, moment: datetime) -> int:
        if self.when_first_half_expires >= moment:
            return self.amount
        if self.when_expires >= moment:
            return self.amount - self.half_of(self.amount)
        return 0

    def half_of(self, amount: int) -> int:
        return self.amount // 2

    def subtract(self, amount: int, moment: datetime) -> 'TwoStepExpiringMiles':
        current_amount = self.get_amount_for(moment)
        if current_amount < amount:
            raise AttributeError('Insufficient amount of miles')
        return TwoStepExpiringMiles(current_amount - amount, self.when_first_half_expires, self.when_expires)

    def expires_at(self) -> datetime:
        return self.when_expires

    def __eq__(self, other):
        if not isinstance(other, TwoStepExpiringMiles):
            return False
        return (
            self.amount == other.amount
            and self.when_expires == other.when_expires
            and self.when_first_half_expires == other.when_first_half_expires
        )

    def __str__(self):
        return (
            f"TwoStepExpiringMiles{{" 
            f"amount={self.amount}"
            f", whenFirstHalfExpires={self.when_first_half_expires}" 
            f", whenExpires={self.when_expires}" 
            f"}}"
        )
