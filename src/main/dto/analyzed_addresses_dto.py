from typing import List

from dto.address_dto import AddressDTO
from pydantic import BaseModel


class AnalyzedAddressesDTO(BaseModel):
    addresses: List[AddressDTO]
