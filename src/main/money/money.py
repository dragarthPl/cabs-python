import hashlib


class Money:
    value: int

    @classmethod
    @property
    def ZERO(cls):
        return cls(0)

    def __init__(self, value: int):
        self.value = value

    def add(self, other: 'Money') -> 'Money':
        return Money(self.value + other.value)

    def subtract(self, other: 'Money') -> 'Money':
        return Money(self.value - other.value)

    def percentage(self, percentage: int) -> 'Money':
        return Money(round(percentage * self.value/100.0))

    def to_int(self) -> int:
        return self.value

    def __eq__(self, other):
        if not isinstance(other, Money):
            return False
        return self.value == other.value

    def __hash__(self):
        m = hashlib.md5()
        m.update(str(self.value).encode('utf-8'))

        return int(m.hexdigest(), 16)

    def to_string(self):
        value: float = self.value / 100.0
        return f'{value:.2f}'
