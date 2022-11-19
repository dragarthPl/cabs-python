from datetime import datetime
from decimal import Decimal
from unittest import IsolatedAsyncioTestCase
from unittest.mock import ANY

from fastapi_events import middleware_identifier
from httpx import AsyncClient

from carfleet.car_class import CarClass
from core.database import create_db_and_tables, drop_db_and_tables
from ride.details.status import Status
from ride.transit_dto import TransitDTO
from geolocation.address.address_dto import AddressDTO
from tests.common.address_matcher import AddressMatcher
from tracking.driver_session_service import DriverSessionService
from tracking.driver_tracking_service import DriverTrackingService
from geolocation.geocoding_service import GeocodingService
from ride.ride_service import RideService
from tests.common.fixtures import Fixtures, DependencyResolver
from mockito import when

from cabs_application import CabsApplication

dependency_resolver = DependencyResolver()


class TestTransitLifeCycleIntegration(IsolatedAsyncioTestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    ride_service: RideService = dependency_resolver.resolve_dependency(RideService)
    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(GeocodingService)
    driver_session_service: DriverSessionService = dependency_resolver.resolve_dependency(DriverSessionService)
    driver_tracking_service: DriverTrackingService = dependency_resolver.resolve_dependency(DriverTrackingService)

    async def asyncSetUp(self):
        create_db_and_tables()
        app = CabsApplication().create_app()
        middleware_identifier.set(app.middleware_stack.app._id)

        self.client = AsyncClient(app=app)
        self.fixtures.an_active_car_category(CarClass.VAN)
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(ANY).thenReturn([1.0, 1.0])

    async def test_can_create_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)

        # when
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertIsNone(loaded.car_class)
        self.assertIsNone(loaded.claim_dto)
        self.assertIsNotNone(loaded.estimated_price)
        self.assertEqual(Decimal(0), loaded.price)
        self.assertEqual("Polska", loaded.address_from.country)
        self.assertEqual("Warszawa", loaded.address_from.city)
        self.assertEqual("Młynarska", loaded.address_from.street)
        self.assertEqual(20, loaded.address_from.building_number)
        self.assertEqual("Polska", loaded.address_to.country)
        self.assertEqual("Warszawa", loaded.address_to.city)
        self.assertEqual("Żytnia", loaded.address_to.street)
        self.assertEqual(25, loaded.address_to.building_number)
        self.assertEqual(Status.DRAFT, loaded.status)
        self.assertIsNotNone(loaded.tariff)
        self.assertNotEqual(0, loaded.km_rate)
        self.assertIsNotNone(loaded.date_time)

    async def test_can_change_transit_destination(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # given
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # when
        new_destination: AddressDTO = self.new_address("Polska", "Warszawa", "Mazowiecka", 30)
        # and
        self.ride_service.change_transit_address_to(transit.request_id, new_destination)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(30, loaded.address_to.building_number)
        self.assertEqual("Mazowiecka", loaded.address_to.street)
        self.assertIsNotNone(loaded.estimated_price)
        self.assertEqual(Decimal(0), loaded.price)

    async def test_cannot_change_destination_when_transit_is_completed(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit: TransitDTO = self.request_transit_from_to(
            pickup,
            destination
        )
        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)
        # and
        self.ride_service.start_transit(driver, transit.request_id)
        # and
        self.ride_service.complete_transit(driver, transit.request_id, destination)

        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.change_transit_address_to(
                transit.request_id,
                self.new_address(country="Polska", city="Warszawa", street="Żytnia", building_number=23)
            )

    async def test_can_change_pickup_place(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        self.ride_service.publish_transit(transit.request_id)

        # when
        new_pickup: AddressDTO = self.new_pickup_address_with_street("Puławska", 28)
        # and
        self.ride_service.change_transit_address_from(
            transit.request_id,
            new_pickup
        )

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(28, loaded.address_from.building_number)
        self.assertEqual("Puławska", loaded.address_from.street)

    async def test_cannot_change_pickup_place_after_transit_is_accepted(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit: TransitDTO = self.request_transit_from_to(
            pickup,
            destination
        )
        # and
        changed_to = self.new_pickup_address(10)
        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)

        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.change_transit_address_from(
                transit.request_id,
                changed_to
            )

    async def test_cannot_change_pickup_place_more_than_three_times(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        self.ride_service.publish_transit(transit.request_id)

        # and
        new_pickup_1: AddressDTO = self.new_pickup_address(10)
        self.ride_service.change_transit_address_from(transit.request_id, new_pickup_1)
        # and
        new_pickup_2: AddressDTO = self.new_pickup_address(11)
        self.ride_service.change_transit_address_from(transit.request_id, new_pickup_2)
        # and
        new_pickup_3: AddressDTO = self.new_pickup_address(12)
        self.ride_service.change_transit_address_from(transit.request_id, new_pickup_3)

        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.change_transit_address_from(
                transit.request_id,
                self.new_pickup_address(13)
            )

    async def test_cannot_change_pickup_place_when_it_is_far_way_from_original(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        self.ride_service.publish_transit(transit.request_id)

        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.change_transit_address_from(
                transit.request_id,
                self.far_away_address()
            )

    async def test_can_cancel_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # when
        self.ride_service.cancel_transit(transit.request_id)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(loaded.status, Status.CANCELLED)

    async def test_cannot_cancel_transit_after_it_was_started(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination
        )
        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)

        # and
        self.ride_service.start_transit(driver, transit.request_id)
        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.cancel_transit(transit.request_id)

        # and
        self.ride_service.complete_transit(driver, transit.request_id, destination)
        # expect
        with self.assertRaises(AttributeError):
            self.ride_service.cancel_transit(transit.request_id)

    async def test_can_publish_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # when
        self.ride_service.publish_transit(transit.request_id)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(Status.WAITING_FOR_DRIVER_ASSIGNMENT, loaded.status)
        self.assertIsNotNone(loaded.published)

    async def test_can_accept_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        self.ride_service.publish_transit(transit.request_id)

        # when
        self.ride_service.accept_transit(driver, transit.request_id)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(Status.TRANSIT_TO_PASSENGER, loaded.status)
        self.assertIsNotNone(loaded.accepted_at)

    async def test_only_one_driver_can_accept_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        second_driver = self.a_nearby_driver(pickup)
        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)

        # when
        with self.assertRaises(AttributeError):
            self.ride_service.accept_transit(second_driver, transit.request_id)

    async def test_transit_cannot_by_accepted_by_driver_who_already_rejected(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.reject_transit(driver, transit.request_id)

        # when
        with self.assertRaises(AttributeError):
            self.ride_service.accept_transit(driver, transit.request_id)

    async def test_transit_cannot_by_accepted_by_driver_who_has_not_seen_proposal(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        far_away_driver = self.a_far_away_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)

        # when
        with self.assertRaises(AttributeError):
            self.ride_service.accept_transit(far_away_driver, transit.request_id)

    async def test_can_start_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver: int = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )
        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)

        # when
        self.ride_service.start_transit(driver, transit.request_id)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(Status.IN_TRANSIT, loaded.status)
        self.assertIsNotNone(loaded.started)

    async def test_cannot_start_not_accepted_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)

        # when
        with self.assertRaises(AttributeError):
            self.ride_service.start_transit(driver, transit.request_id)

    async def test_can_complete_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)
        # and
        self.ride_service.start_transit(driver, transit.request_id)

        # when
        self.ride_service.complete_transit(driver, transit.request_id, destination)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(Status.COMPLETED, loaded.status)
        self.assertIsNotNone(loaded.tariff)
        self.assertIsNotNone(loaded.price)
        self.assertIsNotNone(loaded.driver_fee)
        self.assertIsNotNone(loaded.complete_at)

    async def test_cannot_complete_not_started_transit(self):
        # given
        address_to = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        pickup: AddressDTO = AddressDTO(country=None, city=None, street=None, building_number=0)
        # and
        driver = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            address_to,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)
        # and
        self.ride_service.accept_transit(driver, transit.request_id)

        # when
        with self.assertRaises(AttributeError):
            self.ride_service.complete_transit(driver, transit.request_id, address_to)

    async def test_can_reject_transit(self):
        # given
        pickup: AddressDTO = AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        # and
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        driver = self.a_nearby_driver(pickup)
        # and
        transit = self.request_transit_from_to(
            pickup,
            destination,
        )

        # and
        self.ride_service.publish_transit(transit.request_id)

        # when
        self.ride_service.reject_transit(driver, transit.request_id)

        # then
        loaded = self.ride_service.load_transit_by_uuid(transit.request_id)
        self.assertEqual(Status.WAITING_FOR_DRIVER_ASSIGNMENT, loaded.status)
        self.assertIsNone(loaded.accepted_at)

    def new_address(self, country: str, city: str, street: str, building_number: int) -> AddressDTO:
        address_dto: AddressDTO = self.fixtures.an_address_mocked(
            geocoding_service=self.geocoding_service,
            country=country,
            city=city,
            street=street,
            building_number=building_number
        )
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(
            AddressMatcher(dto=address_dto)
        ).thenReturn([1.0, 1.0])
        return address_dto

    def far_away_address(self):
        address_dto = AddressDTO(country="Dania", city="Kopenhaga", street="Mylve", building_number=2)
        when(self.ride_service.change_pickup_service.geocoding_service).geocode_address(
            AddressMatcher(dto=address_dto)
        ).thenReturn(
            [10000.0, 21211321.0]
        )
        return address_dto

    def a_nearby_driver(self, address_from: AddressDTO) -> int:
        return self.fixtures.a_nearby_driver_default(self.geocoding_service, address_from.to_address_entity(), 1, 1).id

    def a_far_away_driver(self, address: AddressDTO) -> int:
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(
            AddressMatcher(dto=address)
        ).thenReturn(
            [20000000.0, 100000000.0]
        )
        return self.fixtures.a_nearby_driver(
            "DW MARIO", 1000000000, 1000000000, CarClass.VAN, datetime.now(), "BRAND"
        ).id

    def request_transit_from_to(self, pickup_dto: AddressDTO, destination: AddressDTO) -> TransitDTO:
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(
            AddressMatcher(dto=destination)
        ).thenReturn([1.0, 1.0])
        return self.ride_service.create_transit(
            self.fixtures.a_transit_dto(pickup_dto, destination)
        )

    def new_pickup_address(self, building_number: int) -> AddressDTO:
        new_pickup: AddressDTO = AddressDTO(
            country="Polska", city="Warszawa", street="Mazowiecka", building_number=building_number)
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(
            AddressMatcher(dto=new_pickup)
        ).thenReturn([1, 1])
        return new_pickup

    def new_pickup_address_with_street(self, street: str, building_number: int) -> AddressDTO:
        new_pickup: AddressDTO = AddressDTO(
            country="Polska", city="Warszawa", street=street, building_number=building_number)
        when(self.ride_service.complete_transit_service.geocoding_service).geocode_address(
            AddressMatcher(dto=new_pickup)
        ).thenReturn([1, 1])
        return new_pickup

    async def asyncTearDown(self) -> None:
        drop_db_and_tables()
