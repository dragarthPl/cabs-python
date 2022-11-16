from datetime import datetime

from freezegun import freeze_time
from injector import inject
from mockito import ANY, when

from carfleet.car_class import CarClass
from driverfleet.driver import Driver
from driverfleet.driver_fee import DriverFee
from geolocation.address.address_dto import AddressDTO
from geolocation.geocoding_service import GeocodingService
from ride.transit_dto import TransitDTO
from crm.client import Client
from geolocation.address.address import Address
from money import Money
from geolocation.address.address_repository import AddressRepositoryImp
from ride.transit import Transit
from ride.transit_repository import TransitRepositoryImp
from tracking.driver_session_service import DriverSessionService
from ride.ride_service import RideService
from tests.common.car_type_fixture import CarTypeFixture
from tests.common.driver_fixture import DriverFixture
from tests.common.stubbed_transit_price import StubbedTransitPrice
from ride.details.transit_details_facade import TransitDetailsFacade


class RideFixture:
    ride_service: RideService
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
            ride_service: RideService,
            transit_details_facade: TransitDetailsFacade,
            transit_repository: TransitRepositoryImp,
            address_repository: AddressRepositoryImp,
            driver_fixture: DriverFixture,
            car_type_fixture: CarTypeFixture,
            stubbed_price: StubbedTransitPrice,
            driver_session_service: DriverSessionService,
    ):
        self.ride_service = ride_service
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
        self.__stub_price(price)
        address_from = self.address_repository.save(address_from)
        destination = self.address_repository.save(destination)
        self.car_type_fixture.an_active_car_category(CarClass.VAN)
        transit_view: TransitDTO = self.ride_service.create_transit_transaction(
            client.id,
            AddressDTO(address=address_from),
            AddressDTO(address=destination),
            CarClass.VAN
        )
        self.ride_service.publish_transit(transit_view.request_id)
        self.ride_service.find_drivers_for_transit(transit_view.request_id)
        self.ride_service.accept_transit(driver.id, transit_view.request_id)
        self.ride_service.start_transit(driver.id, transit_view.request_id)
        self.ride_service._complete_transit(driver.id, transit_view.request_id, destination)
        transit_id: int = self.transit_details_facade.find_by_uuid(transit_view.request_id).transit_id
        return self.transit_repository.get_one(transit_id)

    def __stub_price(self, price: int):
        fake_price: Money = Money(price)
        self.stubbed_price.stub(fake_price)

    def a_ride_with_fixed_clock(
            self,
            price: int,
            published_at: datetime,
            completed_at: datetime,
            client: Client,
            driver: Driver,
            address_from: Address,
            destination: Address,
    ) -> TransitDTO:
        address_from = self.address_repository.save(address_from)
        destination = self.address_repository.save(destination)
        with freeze_time(published_at):
            self.stubbed_price.stub(Money(price))

            self.car_type_fixture.an_active_car_category(CarClass.VAN)
            transit: TransitDTO = self.ride_service.create_transit_transaction(
                client.id,
                AddressDTO(address=address_from),
                AddressDTO(address=destination),
                CarClass.VAN
            )
            self.ride_service.publish_transit(transit.request_id)
            self.ride_service.find_drivers_for_transit(transit.request_id)
            self.ride_service.accept_transit(driver.id, transit.request_id)
            self.ride_service.start_transit(driver.id, transit.request_id)
        with freeze_time(completed_at):
            self.ride_service._complete_transit(
                driver.id,
                transit.request_id,
                destination
            )
            return self.ride_service.load_transit_by_uuid(transit.request_id)

    def driver_has_done_session_and_picks_someone_up_in_car(
        self,
        driver: Driver,
        client: Client,
        car_class: CarClass,
        plate_number: str,
        car_brand: str,
        since: datetime,
        geocoding_service: GeocodingService,
    ) -> TransitDTO:
        with freeze_time(since):
            address_from: Address = self.address_repository.save(Address(
                country="PL",
                district="MAZ",
                city="WAW",
                street="STREET",
                building_number=1
            ))
            address_to: Address = self.address_repository.save(Address(
                country="PL",
                district="MAZ",
                city="WAW",
                street="STREET",
                building_number=100
            ))
            when(geocoding_service).geocode_address(ANY).thenReturn([1.0, 1.0])
            self.driver_fixture.driver_logs_in(plate_number, car_class, driver, car_brand)
            self.driver_fixture.driver_is_at_geo_localization(plate_number, 1, 1, car_class, driver, since, car_brand)
            self.driver_fixture.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
            transit: TransitDTO = self.a_ride_with_fixed_clock(
                30,
                since,
                since,
                client,
                driver,
                address_from,
                address_to
            )
            self.driver_session_service.log_out_current_session(driver.id)
            return transit
