from typing import Optional

from core.database import get_session
from entity import Address
from fastapi import Depends
from sqlmodel import Session


class AddressRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    # FIX ME: To replace with getOrCreate method instead of that?
    # Actual workaround for address uniqueness problem: assign result from repo.save to variable for later usage
    def save(self, address: Address) -> Optional[Address]:
        address.gen_hash()

        if address.id is None:
            existing_address = self.find_by_hash(address.hash)

            if existing_address is not None:
                return existing_address

        self.session.add(address)
        self.session.commit()
        self.session.refresh(address)
        return address

    def find_by_hash(self, value: str) -> Optional[Address]:
        return self.session.query(Address).where(Address.hash == value).first()

    def find_hash_by_id(self, address_id: int) -> Optional[Address]:
        return self.session.query(Address).where(Address.id == address_id).first().hash

    def get_by_hash(self, hash: int) -> Address:
        return self.session.query(Address).where(Address.hash == hash).first()

    def get_one(self, address_id: int) -> Optional[Address]:
        return self.session.query(Address).where(Address.id == address_id).first()
