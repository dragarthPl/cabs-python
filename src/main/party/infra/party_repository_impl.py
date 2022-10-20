import uuid as uuid_pkg

from injector import inject
from sqlmodel import Session

from core.database import get_session
from party.model.party.party import Party
from party.model.party.party_repository import PartyRepository


class PartyRepositoryImpl(PartyRepository):

    @inject
    def __init__(self, session: Session):
        self.session = session

    def put(self, party_id: uuid_pkg.UUID) -> Party:
        party: Party = self.session.query(Party).where(Party.id == party_id).one_or_none()
        if not party:
            party = Party()
            party.id = party_id
            self.session.add(party)
            self.session.commit()
            self.session.refresh(party)

        return party
