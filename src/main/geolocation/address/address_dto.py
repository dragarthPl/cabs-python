from typing import Optional, Any

from pydantic import BaseModel

from geolocation.address.address import Address


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

    def __init__(self, *, address: Optional[Address] = None, **data: Any):
        super().__init__(**data)
        if address:
            self.country = address.country
            self.district = address.district
            self.city = address.city
            self.street = address.street
            self.building_number = address.building_number
            self.additional_number = address.additional_number
            self.postal_code = address.postal_code
            self.name = address.name
            self.hash = address.hash

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
