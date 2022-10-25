from datetime import datetime

from freezegun import freeze_time
from injector import inject

from carfleet.car_class import CarClass
from driverfleet.driver import Driver
from entity import Client, Address, Transit
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.driver_session_service import DriverSessionService
from service.transit_service import TransitService
from tests.common.car_type_fixture import CarTypeFixture
from tests.common.driver_fixture import DriverFixture
from tests.common.stubbed_transit_price import StubbedTransitPrice
from transitdetails.transit_details_facade import TransitDetailsFacade


class RideFixture:
    transit_service: TransitService
    transit_details_facade: TransitDetailsFacade
    transit_repository: TransitRepositoryImp
    address_repository: AddressRepositoryImp

    driver_fixture: DriverFixture
    car_type_fixture: CarTypeFixture
    stubbed_price: StubbedTransitPrice
    driver_session_service: DriverSessionService

    @inject
    def __init__(
            self,
            transit_service: TransitService,
            transit_details_facade: TransitDetailsFacade,
            transit_repository: TransitRepositoryImp,
            address_repository: AddressRepositoryImp,
            driver_fixture: DriverFixture,
            car_type_fixture: CarTypeFixture,
            stubbed_price: StubbedTransitPrice,
            driver_session_service: DriverSessionService,
    ):
        self.transit_service = transit_service
        self.transit_details_facade = transit_details_facade
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
        self.car_type_fixture.an_active_car_category(CarClass.VAN)
        transit: Transit = self.transit_service.create_transit_transaction(
            client.id, address_from, destination, CarClass.VAN)
        self.transit_service.publish_transit(transit.id)
        self.transit_service.find_drivers_for_transit(transit.id)
        self.transit_service.accept_transit(driver.id, transit.id)
        self.transit_service.start_transit(driver.id, transit.id)
        self.transit_service._complete_transit(driver.id, transit.id, destination)
        self.__stub_price(price, transit)
        return self.transit_repository.get_one(transit.id)

    def __stub_price(self, price: int, transit: Transit):
        fake_price: Money = Money(price)
        self.stubbed_price.stub(transit.id, fake_price)
        self.transit_details_facade.transit_completed(transit.id, datetime.now(), fake_price, fake_price)

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
            self.car_type_fixture.an_active_car_category(CarClass.VAN)
            transit: Transit = self.transit_service.create_transit_transaction(
                client.id, address_from, destination, CarClass.VAN)
            self.transit_service.publish_transit(transit.id)
            self.transit_service.find_drivers_for_transit(transit.id)
            self.transit_service.accept_transit(driver.id, transit.id)
            self.transit_service.start_transit(driver.id, transit.id)
        with freeze_time(completed_at):
            self.transit_service._complete_transit(
                driver.id, transit.id, destination)
            self.stubbed_price.stub(transit.id, Money(price))
            return self.transit_repository.get_one(transit.id)
