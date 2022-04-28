from decimal import Decimal
from unittest import TestCase
from unittest.mock import ANY

from fastapi.params import Depends

from core.database import create_db_and_tables, drop_db_and_tables
from dto.address_dto import AddressDTO
from entity import CarType, Transit, DriverFee
from service.driver_session_service import DriverSessionService
from service.driver_tracking_service import DriverTrackingService
from service.geocoding_service import GeocodingService
from service.transit_service import TransitService
from tests.common.fixtures import Fixtures, DependencyResolver
from mockito import when

dependency_resolver = DependencyResolver()


class TestTransitLifeCycleIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    transit_service: TransitService = dependency_resolver.resolve_dependency(Depends(TransitService))
    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(Depends(GeocodingService))
    driver_session_service: DriverSessionService = dependency_resolver.resolve_dependency(Depends(DriverSessionService))
    driver_tracking_service: DriverTrackingService = dependency_resolver.resolve_dependency(Depends(DriverTrackingService))

    def setUp(self):
        create_db_and_tables()
        self.fixtures.an_active_car_category(CarType.CarClass.VAN)
        # when(geocodingService.geocodeAddress(any(Address.class ))).thenReturn(new double[]{ 1, 1 })
        when(self.geocoding_service).geocode_address(ANY).thenReturn([1.0, 1.0])

    def test_can_create_transit(self):
        # when
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )

        # then
        loaded = self.transit_service.load_transit(transit.id)
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
        self.assertEqual(Transit.Status.DRAFT, loaded.status)
        self.assertIsNotNone(loaded.tariff)
        self.assertNotEqual(0, loaded.km_rate)
        self.assertIsNotNone(loaded.date_time)

    def test_can_change_transit_destination(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )

        # when
        self.transit_service.change_transit_address_to(
            transit.id,
            AddressDTO(country="Polska", city="Warszawa", street="Mazowiecka", building_number=30)
        )

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(30, loaded.address_to.building_number)
        self.assertEqual("Mazowiecka", loaded.address_to.street)
        self.assertIsNotNone(loaded.estimated_price)
        self.assertEqual(Decimal(0), loaded.price)

    def test_cannot_change_destination_when_transit_is_completed(self):
        # given
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            destination
        )

        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)
        # and
        self.transit_service.start_transit(driver, transit.id)
        # and
        self.transit_service.complete_transit(driver, transit.id, destination)

        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.change_transit_address_to(
                transit.id,
                AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=23)
            )

    def test_can_change_pickup_place(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )

        # when
        self.transit_service.change_transit_address_from(
            transit.id,
            AddressDTO(country="Polska", city="Warszawa", street="Puławska", building_number=28)
        )

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(28, loaded.address_from.building_number)
        self.assertEqual("Puławska", loaded.address_from.street)

    def test_cannot_change_pickup_place_after_transit_is_accepted(self):
        # given
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            destination
        )
        # and
        changed_to = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=27)
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)

        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.change_transit_address_from(
                transit.id,
                changed_to
            )

    def test_cannot_change_pickup_place_more_than_three_times(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        self.transit_service.change_transit_address_from(
            transit.id,
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=26)
        )
        # and
        self.transit_service.change_transit_address_from(
            transit.id,
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=27)
        )
        # and
        self.transit_service.change_transit_address_from(
            transit.id,
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=28)
        )

        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.change_transit_address_from(
                transit.id,
                AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=29)
            )

    def test_cannot_change_pickup_place_when_it_is_far_way_from_original(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )

        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.change_transit_address_from(
                transit.id,
                self.far_away_address(transit)
            )

    def test_can_cancel_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )

        # when
        self.transit_service.cancel_transit(transit.id)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(loaded.status, Transit.Status.CANCELLED)

    def test_cannot_cancel_transit_after_it_was_started(self):
        # given
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            destination
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)

        # and
        self.transit_service.start_transit(driver, transit.id)
        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.cancel_transit(transit.id)

        # and
        self.transit_service.complete_transit(driver, transit.id, destination)
        # expect
        with self.assertRaises(AttributeError):
            self.transit_service.cancel_transit(transit.id)

    def test_can_publish_transit(self):
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")

        # when
        self.transit_service.publish_transit(transit.id)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT, loaded.status)
        self.assertIsNotNone(loaded.published)

    def test_can_accept_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)

        # when
        self.transit_service.accept_transit(driver, transit.id)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(Transit.Status.TRANSIT_TO_PASSENGER, loaded.status)
        self.assertIsNotNone(loaded.accepted_at)

    def test_only_one_driver_can_accept_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        second_driver = self.a_nearby_driver("DW MARIO")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)

        # when
        with self.assertRaises(AttributeError):
            self.transit_service.accept_transit(second_driver, transit.id)

    def test_transit_cannot_by_accepted_by_driver_who_already_rejected(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.reject_transit(driver, transit.id)

        # when
        with self.assertRaises(AttributeError):
            self.transit_service.accept_transit(driver, transit.id)

    def test_transit_cannot_by_accepted_by_driver_who_has_not_seen_proposal(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        far_away_driver = self.a_far_away_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)

        # when
        with self.assertRaises(AttributeError):
            self.transit_service.accept_transit(far_away_driver, transit.id)

    def test_can_start_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)

        # when
        self.transit_service.start_transit(driver, transit.id)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(Transit.Status.IN_TRANSIT, loaded.status)
        self.assertIsNotNone(loaded.started)

    def test_cannot_start_not_accepted_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)

        # when
        with self.assertRaises(AttributeError):
            self.transit_service.start_transit(driver, transit.id)

    def test_can_complete_transit(self):
        # given
        destination = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            destination,
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)
        # and
        self.transit_service.start_transit(driver, transit.id)

        # when
        self.transit_service.complete_transit(driver, transit.id, destination)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(Transit.Status.COMPLETED, loaded.status)
        self.assertIsNotNone(loaded.tariff)
        self.assertIsNotNone(loaded.price)
        self.assertIsNotNone(loaded.driver_fee)
        self.assertIsNotNone(loaded.complete_at)

    def test_cannot_complete_not_started_transit(self):
        # given
        address_to = AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            address_to,
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)
        # and
        self.transit_service.accept_transit(driver, transit.id)

        # when
        with self.assertRaises(AttributeError):
            self.transit_service.complete_transit(driver, transit.id, address_to)

    def test_can_reject_transit(self):
        # given
        transit = self.request_transit_from_to(
            AddressDTO(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            AddressDTO(country="Polska", city="Warszawa", street="Żytnia", building_number=25),
        )
        # and
        driver = self.a_nearby_driver("WU1212")
        # and
        self.transit_service.publish_transit(transit.id)

        # when
        self.transit_service.reject_transit(driver, transit.id)

        # then
        loaded = self.transit_service.load_transit(transit.id)
        self.assertEqual(Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT, loaded.status)
        self.assertIsNone(loaded.accepted_at)

    def far_away_address(self, transit: Transit):
        address_dto = AddressDTO(country="Dania", city="Kopenhaga", street="Mylve", building_number=2);
        when(self.geocoding_service).geocode_address(ANY).thenReturn([1000.0, 1000.0])
        when(self.geocoding_service).geocode_address(transit.address_from).thenReturn([1.0, 1.0])
        return address_dto

    def a_nearby_driver(self, plate_number: str) -> int:
        driver = self.fixtures.a_driver()
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        self.driver_session_service.log_in(driver.id, plate_number, CarType.CarClass.VAN, "BRAND")
        self.driver_tracking_service.register_position(driver.id, 1, 1)
        return driver.id

    def request_transit_from_to(self, pickup: AddressDTO, destination: AddressDTO) -> Transit:
        return self.transit_service.create_transit(
            self.fixtures.a_transit_dto(pickup, destination)
        )

    def a_far_away_driver(self, plate_number: str) -> int:
        driver = self.fixtures.a_driver()
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        self.driver_session_service.log_in(driver.id, plate_number, CarType.CarClass.VAN, "BRAND")
        self.driver_tracking_service.register_position(driver.id, 1000, 1000)
        return driver.id

    def tearDown(self) -> None:
        drop_db_and_tables()
