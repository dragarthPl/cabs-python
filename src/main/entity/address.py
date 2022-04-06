from sqlmodel import Field

from sqlalchemy import Column, String

from src.main.common.base_entity import BaseEntity


class Address(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}
    country: str
    district: str
    city: str
    street: str
    building_number: int
    additional_number: int
    postal_code: str
    name: str
    #@Column(unique=true)
    hash: int = Field(sa_column=Column("email", String, unique=True))

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

    #TODO hash