import uuid
from datetime import datetime

import pytz
from injector import inject

from carfleet.car_class import CarClass
from common.base_entity import new_uuid
from geolocation.address.address import Address
from geolocation.distance import Distance
from driverfleet.driver import Driver
from geolocation.address.address_dto import AddressDTO
from crm.client_dto import ClientDTO
from ride.transit_dto import TransitDTO
from crm.client import Client
from money import Money
from pricing.tariff import Tariff
from ride.transit import Transit
from ride.transit_repository import TransitRepositoryImp
from ride.ride_service import RideService
from tests.common.stubbed_transit_price import StubbedTransitPrice
from ride.details.transit_details_facade import TransitDetailsFacade


class TransitFixture:
    ride_service: RideService
    transit_repository: TransitRepositoryImp
    transit_details_facade: TransitDetailsFacade
    stubbed_transit_price: StubbedTransitPrice

    @inject
    def __init__(
        self,
        ride_service: RideService,
        transit_repository: TransitRepositoryImp,
        transit_details_facade: TransitDetailsFacade,
        stubbed_transit_price: StubbedTransitPrice,
    ):
        self.ride_service = ride_service
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
        transit: Transit = self.transit_repository.save(Transit(tariff=None, transit_request_uuid=new_uuid()))
        self.stubbed_transit_price.stub(Money(price))
        self.transit_details_facade.transit_requested(
            when.astimezone(pytz.utc),
            transit.transit_request_uuid,
            address_from,
            address_to,
            Distance.of_km(20),
            client,
            CarClass.VAN,
            Money(price),
            Tariff.of_time(when)
        )
        self.transit_details_facade.transit_accepted(
            transit.transit_request_uuid,
            driver.id,
            when.astimezone(pytz.utc),
        )
        self.transit_details_facade.transit_started(
            transit.transit_request_uuid,
            transit.id,
            when.astimezone(pytz.utc)
        )
        self.transit_details_facade.transit_completed(
            transit.transit_request_uuid,
            when.astimezone(pytz.utc),
            Money(price),
            None
        )
        return transit

    def a_transit_dto_for_client(self, client: Client, address_from: AddressDTO, address_to: AddressDTO):
        transit_dto = TransitDTO()
        transit_dto.client_dto = ClientDTO(**client.dict())
        transit_dto.address_from = address_from
        transit_dto.address_to = address_to
        return transit_dto
