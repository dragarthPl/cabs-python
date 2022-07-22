from typing import Optional

from entity import Address
from pydantic import BaseModel


class AddressDTO(BaseModel):
    country: Optional[str]
    district: Optional[str]
    city: Optional[str]
    street: Optional[str]
    building_number: Optional[int]
    additional_number: Optional[int]
    postal_code: Optional[str]
    name: Optional[str]
    hash: Optional[int]

    def to_address_entity(self) -> Address:
        address = Address()
        address.additional_number = self.additional_number
        address.building_number = self.building_number
        address.city = self.city
        address.name = self.name
        address.street = self.street
        address.country = self.country
        address.postal_code = self.postal_code
        address.district = self.district
        return address
