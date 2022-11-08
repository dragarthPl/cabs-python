from random import random

from injector import inject
from mockito import arg_that, when

from entity import Address
from geolocation.address.address_dto import AddressDTO
from geolocation.address.address_repository import AddressRepositoryImp
from geolocation.geocoding_service import GeocodingService
from tests.common.address_matcher import AddressMatcher


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

    def an_address_mock(
        self,
        geocoding_service: GeocodingService,
        country: str,
        city: str,
        street: str,
        building_number: int
    ) -> AddressDTO:
        address_dto: AddressDTO = AddressDTO(country=country, city=city, street=street, building_number=building_number)

        latitude: float = random()
        longitude: float = random()

        when(geocoding_service).geocode_address(
            arg_that(AddressMatcher(dto=address_dto).matches)
        ).thenReturn([latitude, longitude])

        return address_dto
