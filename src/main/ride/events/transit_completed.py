from datetime import datetime
from common.event import Event


class TransitCompleted(Event):
    client_id: int
    transitId: int
    address_from_hash: int
    address_to_hash: int
    started: datetime
    complete_at: datetime
    event_timestamp: datetime

    def __init__(
        self,
        client_id: int,
        transit_id: int,
        address_from_hash: int,
        address_to_hash: int,
        started: datetime,
        complete_at: datetime,
        event_timestamp: datetime
    ):
        self.client_id = client_id
        self.transit_id = transit_id
        self.address_from_hash = address_from_hash
        self.address_to_hash = address_to_hash
        self.started = started
        self.complete_at = complete_at
        self.event_timestamp = event_timestamp
