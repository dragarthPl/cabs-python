from datetime import datetime

import pytz
from injector import inject

from carfleet.car_class import CarClass
from geolocation.distance import Distance
from driverfleet.driver import Driver
from geolocation.address.address_dto import AddressDTO
from dto.client_dto import ClientDTO
from dto.transit_dto import TransitDTO
from entity import Client, Transit, Address, Tariff
from money import Money
from repository.transit_repository import TransitRepositoryImp
from service.transit_service import TransitService
from tests.common.stubbed_transit_price import StubbedTransitPrice
from transitdetails.transit_details_facade import TransitDetailsFacade


class TransitFixture:
    transit_service: TransitService
    transit_repository: TransitRepositoryImp
    transit_details_facade: TransitDetailsFacade
    stubbed_transit_price: StubbedTransitPrice

    @inject
    def __init__(
        self,
        transit_service: TransitService,
        transit_repository: TransitRepositoryImp,
        transit_details_facade: TransitDetailsFacade,
        stubbed_transit_price: StubbedTransitPrice,
    ):
        self.transit_service = transit_service
        self.transit_repository = transit_repository
        self.transit_details_facade = transit_details_facade
        self.stubbed_transit_price = stubbed_transit_price

    def transit_details(
        self,
        driver: Driver,
        price: int,
        when: datetime,
        client: Client,
        address_from: Address,
        address_to: Address
    ) -> Transit:
        transit: Transit = self.transit_repository.save(Transit())
        self.stubbed_transit_price.stub(transit.id, Money(price))
        transit_id: int = transit.id
        self.transit_details_facade.transit_requested(
            when.astimezone(pytz.utc),
            transit_id,
            address_from,
            address_to,
            Distance.ZERO,
            client,
            CarClass.VAN,
            Money(price),
            Tariff.of_time(when)
        )
        self.transit_details_facade.transit_accepted(transit_id, when.astimezone(pytz.utc), driver.id)
        self.transit_details_facade.transit_started(transit_id, when.astimezone(pytz.utc))
        self.transit_details_facade.transit_completed(transit_id, when.astimezone(pytz.utc), Money(price), None)
        return transit

    def a_transit_dto_for_client(self, client: Client, address_from: AddressDTO, address_to: AddressDTO):
        transit_dto = TransitDTO()
        transit_dto.client_dto = ClientDTO(**client.dict())
        transit_dto.address_from = address_from
        transit_dto.address_to = address_to
        return transit_dto
