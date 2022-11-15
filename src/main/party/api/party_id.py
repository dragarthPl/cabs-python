from uuid import UUID

from common.base_entity import new_uuid


class PartyId:
    id: UUID

    def __init__(self, uuid: UUID = None):
        if uuid:
            self.id = uuid
        else:
            self.id = new_uuid()

    def to_uuid(self):
        return self.id
