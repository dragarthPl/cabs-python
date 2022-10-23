import functools
import math
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta
from injector import inject

from carfleet.car_class import CarClass
from distance.distance import Distance
from dto.address_dto import AddressDTO
from dto.driver_position_dtov_2 import DriverPositionDTOV2
from dto.transit_dto import TransitDTO
from entity import Address, CarType, Driver, Transit
from fastapi_events.dispatcher import dispatch

from entity.events.transit_completed import TransitCompleted
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.driver_position_repository import DriverPositionRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.awards_service import AwardsService
from carfleet.car_type_service import CarTypeService
from service.distance_calculator import DistanceCalculator
from service.driver_fee_service import DriverFeeService
from service.driver_notification_service import DriverNotificationService
from service.geocoding_service import GeocodingService
from service.invoice_generator import InvoiceGenerator
from transitdetails.transit_details_dto import TransitDetailsDTO
from transitdetails.transit_details_facade import TransitDetailsFacade


class TransitService:
    driver_repository: DriverRepositoryImp
    transit_repository: TransitRepositoryImp
    client_repository: ClientRepositoryImp
    invoice_generator: InvoiceGenerator
    notification_service: DriverNotificationService
    distance_calculator: DistanceCalculator
    driver_position_repository: DriverPositionRepositoryImp
    driver_session_repository: DriverSessionRepositoryImp
    car_type_service: CarTypeService
    geocoding_service: GeocodingService
    address_repository: AddressRepositoryImp
    driver_fee_service: DriverFeeService
    awards_service: AwardsService
    transit_details_facade: TransitDetailsFacade

    @inject
    def __init__(
            self,
            driver_repository: DriverRepositoryImp,
            transit_repository: TransitRepositoryImp,
            client_repository: ClientRepositoryImp,
            invoice_generator: InvoiceGenerator,
            notification_service: DriverNotificationService,
            distance_calculator: DistanceCalculator,
            driver_position_repository: DriverPositionRepositoryImp,
            driver_session_repository: DriverSessionRepositoryImp,
            car_type_service: CarTypeService,
            geocoding_service: GeocodingService,
            address_repository: AddressRepositoryImp,
            driver_fee_service: DriverFeeService,
            awards_service: AwardsService,
            transit_details_facade: TransitDetailsFacade,
    ):
        self.driver_repository = driver_repository
        self.transit_repository = transit_repository
        self.client_repository = client_repository
        self.invoice_generator = invoice_generator
        self.notification_service = notification_service
        self.distance_calculator = distance_calculator
        self.driver_position_repository = driver_position_repository
        self.driver_session_repository = driver_session_repository
        self.car_type_service = car_type_service
        self.geocoding_service = geocoding_service
        self.address_repository = address_repository
        self.driver_fee_service = driver_fee_service
        self.awards_service = awards_service
        self.transit_details_facade = transit_details_facade

    def create_transit(self, transit_dto: TransitDTO) -> Transit:
        address_from = self.__address_from_dto(transit_dto.address_from)
        address_to = self.__address_from_dto(transit_dto.address_to)
        return self.create_transit_transaction(
            transit_dto.client_dto.id, address_from, address_to, transit_dto.car_class)

    def __address_from_dto(self, address_dto: AddressDTO) -> Address:
        address = address_dto.to_address_entity()
        return self.address_repository.save(address)

    def create_transit_transaction(
            self, client_id: int, address_from: Address, address_to: Address, car_class: CarClass) -> Transit:
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exist, id = " + str(client_id))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(address_to)
        km = Distance.of_km(float(self.distance_calculator.calculate_by_map(
            geo_from[0],
            geo_from[1],
            geo_to[0],
            geo_to[1]))
        )
        now: datetime = datetime.now()
        transit: Transit = Transit(when=now, distance=km)
        estimated_price: Money = transit.estimate_cost()
        transit = self.transit_repository.save(transit)
        self.transit_details_facade.transit_requested(
            now,
            transit.id,
            address_from,
            address_to,
            km,
            client,
            car_class,
            estimated_price,
            transit.get_tariff()
        )
        return transit

    def _change_transit_address_from(self, transit_id: int, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit = self.transit_repository.get_one(transit_id)
        transit_details: TransitDetailsDTO = self.find_transit_details(transit_id)
        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        # FIXME later: add some exceptions handling
        geo_from_new: List[float] = self.geocoding_service.geocode_address(new_address)
        geo_to_new: List[float] = self.geocoding_service.geocode_address(
            transit_details.address_from.to_address_entity()
        )

        # https://www.geeksforgeeks.org/program-distance-two-points-earth/
        # The math module contains a function
        # named toRadians which converts from
        # degrees to radians.
        lon1: float = math.radians(geo_from_new[1])
        lon2: float = math.radians(geo_to_new[1])
        lat1: float = math.radians(geo_from_new[0])
        lat2: float = math.radians(geo_to_new[0])

        # Haversine formula
        dlon: float = lon2 - lon1
        dlat: float = lat2 - lat1
        a: float = math.pow(math.sin(dlat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon / 2), 2)

        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371

        # calculate the result
        distance_in_kmeters = c * r

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(geo_from_new[0], geo_from_new[1], geo_to_new[0], geo_to_new[1])
        ))
        transit.change_pickup_to(new_address, new_distance, distance_in_kmeters)
        self.transit_repository.save(transit)
        self.transit_details_facade.pickup_changed_to(
            transit.id,
            new_address,
            new_distance
        )

        for driver in transit.proposed_drivers:
            self.notification_service.notify_about_changed_transit_address(driver.id, transit_id)

    def change_transit_address_to(self, transit_id: int, new_address: AddressDTO) -> None:
        self._change_transit_address_to(transit_id, new_address.to_address_entity())

    def change_transit_address_from(self, transit_id: int, new_address: AddressDTO) -> None:
        self._change_transit_address_from(transit_id, new_address.to_address_entity())

    def _change_transit_address_to(self, transit_id: int, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit: Transit = self.transit_repository.get_one(transit_id)
        transit_details: TransitDetailsDTO = self.find_transit_details(transit_id)
        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(transit_details.address_from.to_address_entity())
        geo_to: List[float] = self.geocoding_service.geocode_address(new_address)

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1])
        ))
        transit.change_destination_to(new_address, new_distance)
        self.transit_repository.save(transit)
        self.transit_details_facade.destination_changed(transit.id, new_address, new_distance)
        if transit.driver is not None:
            self.notification_service.notify_about_changed_transit_address(transit.driver.id, transit_id)

    def cancel_transit(self, transit_id: int) -> None:
        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        if transit.driver != None:
            self.notification_service.notify_about_cancelled_transit(transit.driver.id, transit.id)

        transit.cancel()
        self.transit_details_facade.transit_cancelled(transit_id)
        self.transit_repository.save(transit)

    def publish_transit(self, transit_id: int) -> Transit:
        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        now: datetime = datetime.now()
        transit.publish_at(now)
        self.transit_repository.save(transit)
        self.transit_details_facade.transit_published(transit_id, now)
        return self.find_drivers_for_transit(transit_id)

    def find_drivers_for_transit(self, transit_id: int) -> Transit:
        transit = self.transit_repository.get_one(transit_id)
        transit_details: TransitDetailsDTO = self.find_transit_details(transit_id)

        if transit != None:
            if transit.status == Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT:
                distance_to_check: int = 0

                # Tested on production, works as expected.
                # If you change this code and the system will collapse AGAIN, I'll find you...
                while True:
                    if transit.awaiting_drivers_responses > 4:
                        return transit
                    distance_to_check += 1

                    # FIXME: to refactor when the final business logic will be determined
                    if (transit.should_not_wait_for_driver_any_more(datetime.now()) or
                            distance_to_check >= 20
                    ):
                        transit.fail_driver_assignment()
                        self.transit_repository.save(transit)
                        return transit
                    geocoded = [None, None]

                    try:
                        geocoded = self.geocoding_service.geocode_address(self.address_repository.get_by_hash(
                            transit_details.address_from.hash
                        ))
                    except Exception as e:
                        # Geocoding failed! Ask Jessica or Bryan for some help if needed.
                        pass

                    longitude = geocoded[1]
                    latitude = geocoded[0]

                    # https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
                    # Earth’s radius, sphere
                    # R: float = 6378;
                    R = 6371 # Changed to 6371 due to Copy&Paste pattern from different source

                    # offsets in meters
                    dn = float(distance_to_check)
                    de = float(distance_to_check)

                    # Coordinate offsets in radians
                    d_lat = dn / R
                    d_lon = de / (R * math.cos(math.pi * latitude / 180))

                    # Offset positions, decimal degrees
                    latitude_min = latitude - d_lat * 180 / math.pi
                    latitude_max = latitude + d_lat * 180 / math.pi
                    longitude_min = longitude - d_lon * 180 / math.pi
                    longitude_max = longitude + d_lon * 180 / math.pi

                    drivers_avg_positions: List[DriverPositionDTOV2] = \
                        self.driver_position_repository.find_average_driver_position_since(
                            latitude_min,
                            latitude_max,
                            longitude_min,
                            longitude_max,
                            datetime.now() - relativedelta(minutes=5)
                        )
                    if drivers_avg_positions:
                        comparator = lambda d1, d2: math.sqrt(
                            math.pow(latitude - d1.latitude, 2) + math.pow(longitude - d1.longitude, 2)
                        ) - math.sqrt(
                            math.pow(latitude - d2.latitude, 2) + math.pow(longitude - d2.longitude, 2)
                        )

                        drivers_avg_positions = sorted(drivers_avg_positions, key=functools.cmp_to_key(comparator))
                        drivers_avg_positions = drivers_avg_positions[:20]
                        car_classes = []
                        active_car_classes = self.car_type_service.find_active_car_classes()
                        if not active_car_classes:
                            return transit
                        if transit_details.car_type != None:
                            if transit_details.car_type in active_car_classes:
                                car_classes.append(transit_details.car_type)
                            else:
                                return transit
                        else:
                            car_classes.extend(active_car_classes)

                        drivers: List[Driver] = list(map(lambda pos: pos.driver, drivers_avg_positions))
                        active_driver_ids_in_specific_car: List[int] = list(map(
                                lambda ds: ds.driver.id,
                                self.driver_session_repository.find_all_by_logged_out_at_null_and_driver_in_and_car_class_in(
                                    drivers,
                                    car_classes
                                )
                        ))

                        drivers_avg_positions = list(
                            filter(
                                lambda dp: dp.driver.id in active_driver_ids_in_specific_car,
                                drivers_avg_positions
                            ),
                        )

                        # Iterate across average driver positions
                        for driver_avg_position in drivers_avg_positions:
                            driver = driver_avg_position.driver
                            if driver.status == Driver.Status.ACTIVE and not driver.is_occupied:
                                if transit.can_propose_to(driver):
                                    transit.propose_to(driver)
                                    self.notification_service.notify_about_possible_transit(driver.id, transit_id)
                            else:
                                # Not implemented yet!
                                pass
                        self.transit_repository.save(transit)
                    else:
                        # Next iteration, no drivers at specified area
                        continue
            else:
                raise AttributeError("..., id = " + str(transit_id))
        else:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

    def accept_transit(self, driver_id: int, transits_id: int):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))
        else:
            transit = self.transit_repository.get_one(transits_id)

            if transit is None:
                raise AttributeError("Transit does not exist, id = " + str(transits_id))
            else:
                now = datetime.now()
                transit.accept_by(driver, now)
                self.transit_details_facade.transit_accepted(transits_id, now, driver_id)
                self.transit_repository.save(transit)
                self.driver_repository.save(driver)

    def start_transit(self, driver_id: int, transits_id: int):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transits_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transits_id))

        now = datetime.now()
        transit.start(now)
        self.transit_details_facade.transit_started(transits_id, now)
        self.transit_repository.save(transit)

    def reject_transit(self, driver_id: int, transits_id: int):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transits_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transits_id))

        transit.reject_by(driver)
        self.transit_repository.save(transit)

    def complete_transit(self, driver_id: int, transits_id: int, destination: AddressDTO):
        self._complete_transit(driver_id, transits_id, destination.to_address_entity())

    def _complete_transit(self, driver_id: int, transit_id: int, destination_address: Address):
        destination_address = self.address_repository.save(destination_address)
        driver = self.driver_repository.get_one(driver_id)
        transit_details: TransitDetailsDTO = self.find_transit_details(transit_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(
            self.address_repository.get_by_hash(transit_details.address_from.hash))
        geo_to: List[float] = self.geocoding_service.geocode_address(
            self.address_repository.get_by_hash(transit_details.address_to.hash))
        distance = Distance.of_km(
            float(self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1]))
        )
        now = datetime.now()
        transit.complete_ride_at(now, destination_address, distance)
        driver_fee: Money = self.driver_fee_service.calculate_driver_fee(transit.get_price(), driver_id)
        driver.is_occupied = False
        self.driver_repository.save(driver)
        self.awards_service.register_miles(transit_details.client.id, transit_id)
        self.transit_repository.save(transit)
        self.transit_details_facade.transit_completed(transit_id, now, Money(transit.price), driver_fee)
        self.invoice_generator.generate(
            transit.get_price().to_int(), f"{transit_details.client.name} {transit_details.client.last_name}")
        dispatch(
            "add_transit_between_addresses",
            payload=TransitCompleted(
                transit_details.client.id,
                transit_id,
                transit_details.address_from.hash,
                transit_details.address_to.hash,
                transit_details.started,
                now,
                datetime.now()
            ),
        )

    def load_transit(self, transit_id: int) -> TransitDTO:
        transit_details: TransitDetailsDTO = self.find_transit_details(transit_id)
        return TransitDTO(transit=self.transit_repository.get_one(transit_id), transit_details=transit_details)

    def find_transit_details(self, transit_id: int) -> TransitDetailsDTO:
        return self.transit_details_facade.find(transit_id)
