from uuid import UUID, uuid4


class PartyId:
    id: UUID

    def __init__(self, uuid: UUID = None):
        if uuid:
            self.id = uuid
        else:
            self.id = uuid4()

    def to_uuid(self):
        return self.id