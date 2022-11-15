from typing import Optional

from mockito.matchers import Matcher

from geolocation.address.address import Address
from geolocation.address.address_dto import AddressDTO
import logging
logger = logging.getLogger(__name__)

class AddressMatcher(Matcher):
    country: str
    city: str
    street: str
    building_number: int

    def __init__(
        self,
        address: Optional[Address] = None,
        dto: Optional[AddressDTO] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        street: Optional[str] = None,
        building_number: Optional[int] = None
    ):
        if dto:
            address = dto.to_address_entity()
        if address:
            self.country = address.country
            self.city = address.city
            self.street = address.street
            self.building_number = address.building_number
        else:
            self.country = country
            self.city = city
            self.street = street
            self.building_number = building_number

    def matches(self, right: Address) -> bool:
        if not right:
            return False
        return (
            self.country == right.country
            and self.city == right.city
            and self.street == right.street
            and self.building_number == right.building_number
        )

    def __repr__(self):
        return (
            f"country: {self.country}, "
            f"city: {self.city}, "
            f"street: {self.street}, "
            f"building_number: {self.building_number}")
