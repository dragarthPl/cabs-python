import json
from datetime import datetime

from loyalty.constant_until import ConstantUntil
from loyalty.miles import Miles


class MilesJsonEncoder(json.JSONEncoder):
    def default(self, miles: ConstantUntil) -> dict:
        if isinstance(miles, Miles):
            return {
                "amount": miles.amount,
                "when_expires": miles.when_expires.isoformat(),
                "__class__": "Miles"
            }
        else:
            return super().default(miles)


def decode_json_miles(json_obj):
    if "__class__" in json_obj and json_obj["__class__"] == "Miles":
        return ConstantUntil(
            amount=json_obj["amount"],
            when_expires=datetime.fromisoformat(json_obj["when_expires"])
        )
    return json_obj


class MilesJsonMapper:
    @staticmethod
    def serialize(miles: Miles) -> str:
        return json.dumps(miles, cls=MilesJsonEncoder)

    @staticmethod
    def deserialize(json_string: str) -> Miles:
        return json.loads(json_string, object_hook=decode_json_miles)
