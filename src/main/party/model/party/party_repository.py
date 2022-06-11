import abc
import uuid as uuid_pkg

from party.model.party.party import Party


class PartyRepository(metaclass=abc.ABCMeta):
    def put(self, pary_id: uuid_pkg.UUID) -> Party:
        raise NotImplementedError
