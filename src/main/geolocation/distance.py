import hashlib
import math
from typing import Any, Optional

from pydantic import BaseModel


class Distance(BaseModel):
    MILES_TO_KILOMETERS_RATIO = 1.609344
    km: float = 0

    @classmethod
    @property
    def ZERO(cls):
        return cls.of_km(0)

    def __init__(self, km: Optional[float] = 0, **data: Any):
        super().__init__(**data)
        self.km = km

    @staticmethod
    def of_km(km: float) -> 'Distance':
        return Distance(km)

    def to_km_in_float(self) -> float:
        return self.km

    def print_in(self, unit: str) -> str:
        if unit == 'km':
            if self.km == math.ceil(self.km):
                return f"{int(round(self.km))}km"
            return "{0:.3f}km".format(self.km)
        if unit == 'miles':
            km = self.km / self.MILES_TO_KILOMETERS_RATIO
            if km == math.ceil(km):
                return f"{int(round(km))}miles"
            return "{0:.3f}miles".format(km)

        if unit == 'm':
            return f"{int(round(self.km * 1000))}m"
        raise AttributeError("Invalid unit " + unit)

    def __eq__(self, o):
        if o is None or not isinstance(o, Distance):
            return False
        return self.km == o.km

    def __hash__(self):
        m = hashlib.md5()
        m.update(str(self.km).encode('utf-8'))

        return int(m.hexdigest(), 16)

    def to_string(self) -> str:
        return f"Distance{{km={self.km}}}"

    def __str__(self) -> str:
        return self.to_string()

    def add(self, travelled: 'Distance') -> 'Distance':
        return Distance.of_km(self.km + travelled.km)
