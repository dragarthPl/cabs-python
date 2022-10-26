from injector import inject

from entity import Address
from geolocation.address.address_repository import AddressRepositoryImp

class AddressFixture:

    address_repository: AddressRepositoryImp

    @inject
    def __init__(
        self,
        address_repository: AddressRepositoryImp,
    ):
        self.address_repository = address_repository

    def an_address(self) -> Address:
        return self.address_repository.save(
            Address(country="Polska", city="Warszawa", street="Młynarska", building_number=20))
