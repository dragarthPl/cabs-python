from typing import List

from geolocation.address.address_dto import AddressDTO
from pydantic import BaseModel


class AnalyzedAddressesDTO(BaseModel):
    addresses: List[AddressDTO]
