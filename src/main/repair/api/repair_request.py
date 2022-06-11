from typing import Set

from party.api.party_id import PartyId
from repair.legacy.parts.parts import Parts


class RepairRequest:
    vehicle: PartyId
    parts_to_repair: Set[Parts]

    def __init__(self, vehicle: PartyId, parts: Set[Parts]):
        self.vehicle = vehicle
        self.parts_to_repair = parts
