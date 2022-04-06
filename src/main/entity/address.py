import hashlib
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field

from common.base_entity import BaseEntity
import logging
logger = logging.getLogger(__name__)

class Address(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}
    country: Optional[str]
    district: Optional[str]
    city: Optional[str]
    street: Optional[str]
    building_number: Optional[int]
    additional_number: Optional[int]
    postal_code: Optional[str]
    name: Optional[str]
    #@Column(unique=true)
    hash: str = Field(sa_column=Column("hash", String, unique=True))

    def __str__(self):
        return (f"Address{{"
                f"id='{self.id}'"
                f", country='{self.country}'"
                f", district='{self.district}'"
                f", city='{self.city}'"
                f", street='{self.street}'"
                f", buildingNumber={self.building_number}"
                f", additionalNumber={self.additional_number}"
                f", postalCode='{self.postal_code}'"
                f", name='{self.name}'"
                f'}}'
                )

    def gen_hash(self) -> None:
        m = hashlib.md5()
        for s in (
            self.country,
            self.district,
            self.city,
            self.street,
            self.building_number,
            self.additional_number,
            self.postal_code,
            self.name
        ):
            m.update(str(s).encode('utf-8'))
        self.hash = str(int(m.hexdigest(), 16))

    def __eq__(self, o):
        if not isinstance(o, Address):
            return False
        return self.id is not None and self.id == o.id
