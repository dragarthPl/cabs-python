from datetime import datetime

from fastapi import Depends
from freezegun import freeze_time

from entity import Client, Driver, Address, Transit, CarType
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.driver_session_service import DriverSessionService
from service.transit_service import TransitService
from tests.common.car_type_fixture import CarTypeFixture
from tests.common.driver_fixture import DriverFixture
from tests.common.stubbed_transit_price import StubbedTransitPrice


class RideFixture:
    transit_service: TransitService
    transit_repository: TransitRepositoryImp
    address_repository: AddressRepositoryImp

    driver_fixture: DriverFixture
    car_type_fixture: CarTypeFixture
    stubbed_price: StubbedTransitPrice
    driver_session_service: DriverSessionService

    def __init__(
            self,
            transit_service: TransitService = Depends(TransitService),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp),
            driver_fixture: DriverFixture = Depends(DriverFixture),
            car_type_fixture: CarTypeFixture = Depends(CarTypeFixture),
            stubbed_price: StubbedTransitPrice = Depends(StubbedTransitPrice),
            driver_session_service: DriverSessionService = Depends(DriverSessionService),
    ):
        self.transit_service = transit_service
        self.transit_repository = transit_repository
        self.address_repository = address_repository
        self.driver_fixture = driver_fixture
        self.car_type_fixture = car_type_fixture
        self.stubbed_price = stubbed_price
        self.driver_session_service = driver_session_service

    def a_ride(
        self,
        price: int,
        client: Client,
        driver: Driver,
        address_from: Address,
        destination: Address
    ) -> Transit:
        address_from = self.address_repository.save(address_from)
        destination = self.address_repository.save(destination)
        self.car_type_fixture.an_active_car_category(CarType.CarClass.VAN)
        transit: Transit = self.transit_service.create_transit_transaction(
            client.id, address_from, destination, CarType.CarClass.VAN)
        self.transit_service.publish_transit(transit.id)
        self.transit_service.find_drivers_for_transit(transit.id)
        self.transit_service.accept_transit(driver.id, transit.id)
        self.transit_service.start_transit(driver.id, transit.id)
        self.transit_service._complete_transit(driver.id, transit.id, destination)
        self.stubbed_price.stub(transit.id, Money(price))
        return self.transit_repository.get_one(transit.id)

    def a_ride_with_fixed_clock(
            self,
            price: int,
            published_at: datetime,
            completed_at: datetime,
            client: Client,
            driver: Driver,
            address_from: Address,
            destination: Address,
    ) -> Transit:
        address_from = self.address_repository.save(address_from)
        destination = self.address_repository.save(destination)
        with freeze_time(published_at):
            self.car_type_fixture.an_active_car_category(CarType.CarClass.VAN)
            transit: Transit = self.transit_service.create_transit_transaction(
                client.id, address_from, destination, CarType.CarClass.VAN)
            self.transit_service.publish_transit(transit.id)
            self.transit_service.find_drivers_for_transit(transit.id)
            self.transit_service.accept_transit(driver.id, transit.id)
            self.transit_service.start_transit(driver.id, transit.id)
        with freeze_time(completed_at):
            self.transit_service._complete_transit(
                driver.id, transit.id, destination)
            self.stubbed_price.stub(transit.id, Money(price))
            return self.transit_repository.get_one(transit.id)
