import math
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta
from dto.address_dto import AddressDTO
from dto.driver_position_dtov_2 import DriverPositionDTOV2
from dto.transit_dto import TransitDTO
from entity import Address, CarType, Driver, Transit
from fastapi import Depends

from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.driver_position_repository import DriverPositionRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.awards_service import AwardsService, AwardsServiceImpl
from service.car_type_service import CarTypeService
from service.distance_calculator import DistanceCalculator
from service.driver_fee_service import DriverFeeService
from service.driver_notification_service import DriverNotificationService
from service.geocoding_service import GeocodingService
from service.invoice_generator import InvoiceGenerator


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

    def __init__(
            self,
            driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
            invoice_generator: InvoiceGenerator = Depends(InvoiceGenerator),
            notification_service: DriverNotificationService = Depends(DriverNotificationService),
            distance_calculator: DistanceCalculator = Depends(DistanceCalculator),
            driver_position_repository: DriverPositionRepositoryImp = Depends(DriverPositionRepositoryImp),
            driver_session_repository: DriverSessionRepositoryImp = Depends(DriverSessionRepositoryImp),
            car_type_service: CarTypeService = Depends(CarTypeService),
            geocoding_service: GeocodingService = Depends(GeocodingService),
            address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp),
            driver_fee_service: DriverFeeService = Depends(DriverFeeService),
            awards_service: AwardsService = Depends(AwardsServiceImpl)
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

    def create_transit(self, transit_dto: TransitDTO) -> Transit:
        address_from = self.__address_from_dto(transit_dto.address_from)
        address_to = self.__address_from_dto(transit_dto.address_to)
        return self.create_transit_transaction(
            transit_dto.client_dto.id, address_from, address_to, transit_dto.car_class)

    def __address_from_dto(self, address_dto: AddressDTO) -> Address:
        address = address_dto.to_address_entity()
        return self.address_repository.save(address)

    def create_transit_transaction(
            self, client_id: int, address_from: Address, address_to: Address, car_class: CarType.CarClass) -> Transit:
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exist, id = " + str(client_id))

        transit = Transit()

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(address_to)

        transit.client = client
        transit.address_from = address_from
        transit.address_to = address_to
        transit.car_type = car_class
        transit.status = Transit.Status.DRAFT
        transit.date_time = datetime.now()
        transit.set_km(float(self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1])))

        return self.transit_repository.save(transit)

    def _change_transit_address_from(self, transit_id: int, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        # FIXME later: add some exceptions handling
        geo_from_new: List[float] = self.geocoding_service.geocode_address(new_address)
        geo_to_new: List[float] = self.geocoding_service.geocode_address(transit.address_from)

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

        if not (
                transit.status == Transit.Status.DRAFT or
                transit.status == Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT or
                transit.pickup_address_change_counter > 2 or
                distance_in_kmeters > 0.25
        ):
            raise AttributeError("Address 'from' cannot be changed, id = " + str(transit_id))

        transit.address_from = new_address
        transit.set_km(float(
            self.distance_calculator.calculate_by_map(geo_from_new[0], geo_from_new[1], geo_to_new[0], geo_to_new[1])))
        transit.pickup_address_change_counter = transit.pickup_address_change_counter + 1
        self.transit_repository.save(transit)

        for driver in transit.proposed_drivers:
            self.notification_service.notify_about_changed_transit_address(driver.id, transit_id)

    def change_transit_address_to(self, transit_id: int, new_address: AddressDTO) -> None:
        self._change_transit_address_to(transit_id, new_address.to_address_entity())

    def change_transit_address_from(self, transit_id: int, new_address: AddressDTO) -> None:
        self._change_transit_address_from(transit_id, new_address.to_address_entity())

    def _change_transit_address_to(self, transit_id: int, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit: Transit = self.transit_repository.get_one(transit_id)
        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        if transit.status == Transit.Status.COMPLETED:
            raise AttributeError("Address 'to' cannot be changed, id = " + str(transit_id))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(transit.address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(new_address)

        transit.address_to = new_address
        transit.set_km(float(self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1])))
        self.transit_repository.save(transit)

        if transit.driver is not None:
            self.notification_service.notify_about_changed_transit_address(transit.driver.id, transit_id)

    def cancel_transit(self, transit_id: int) -> None:
        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        if not transit.status in (
            Transit.Status.DRAFT, Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT, Transit.Status.TRANSIT_TO_PASSENGER
        ):
            raise AttributeError("Transit cannot be canceled, id = " + str(transit_id))

        if transit.driver != None:
            self.notification_service.notify_about_cancelled_transit(transit.driver.id, transit.id)

        transit.status = Transit.Status.CANCELLED
        transit.driver = None
        transit.set_km(0)
        transit.awaiting_drivers_responses = 0
        self.transit_repository.save(transit)

    def publish_transit(self, transit_id: int) -> Transit:
        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        transit.status = Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT
        transit.published = datetime.now()
        self.transit_repository.save(transit)

        return self.find_drivers_for_transit(transit_id)

    def find_drivers_for_transit(self, transit_id: int) -> Transit:
        transit = self.transit_repository.get_one(transit_id)

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
                    if (transit.published + relativedelta(seconds=300) > datetime.now() or
                            distance_to_check >= 20 or
                            transit.status == Transit.Status.CANCELLED
                    ):
                        transit.status = Transit.Status.DRIVER_ASSIGNMENT_FAILED
                        transit.driver = None; transit.set_km(0)
                        transit.awaiting_drivers_responses = 0
                        self.transit_repository.save(transit)
                        return transit
                    geocoded = [None, None]

                    try:
                        geocoded = self.geocoding_service.geocode_address(transit.address_from)
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
                    if not drivers_avg_positions:
                        comparator = lambda d1, d2: math.sqrt(
                            math.pow(latitude - d1.latitude, 2) + math.pow(longitude - d1.longitude, 2)
                        ) - math.sqrt(
                            math.pow(latitude - d2.latitude, 2) + math.pow(longitude - d2.longitude, 2)
                        )

                        drivers_avg_positions = sorted(drivers_avg_positions, key=comparator)
                        drivers_avg_positions = drivers_avg_positions[:20]
                        car_classes = []
                        active_car_classes = self.car_type_service.find_active_car_classes()
                        if not active_car_classes:
                            return transit
                        if transit.car_type != None:
                            if transit.car_type in active_car_classes:
                                car_classes.append(transit.car_type)
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

                        drivers_avg_positions = list(filter(lambda dp: dp.driver.id in active_driver_ids_in_specific_car))

                        # Iterate across average driver positions
                        for driver_avg_position in drivers_avg_positions:
                            driver = driver_avg_position.driver
                            if driver.status == Driver.Status.ACTIVE and driver.is_occupied == False:
                                if not driver in transit.drivers_rejections:
                                    transit.proposed_drivers.append(driver); transit.awaiting_drivers_responses += 1
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
                if transit.driver != None:
                    raise AttributeError("Transit already accepted, id = " + str(transits_id))
                else:
                    transit.driver = driver
                    transit.awaiting_drivers_responses = 0
                    transit.accepted_at = datetime.now()
                    transit.status = Transit.Status.TRANSIT_TO_PASSENGER
                    self.transit_repository.save(transit)
                    driver.is_occupied = True
                    self.driver_repository.save(driver)

    def start_transit(self, driver_id: int, transits_id: int):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transits_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transits_id))

        if not transit.status == Transit.Status.TRANSIT_TO_PASSENGER:
            raise AttributeError("Transit cannot be started, id = " + str(transits_id))

        transit.status = Transit.Status.IN_TRANSIT
        transit.started = datetime.now()
        self.transit_repository.save(transit)

    def reject_transit(self, driver_id: int, transits_id: int):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transits_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transits_id))

        transit.drivers_rejections.append(driver)
        transit.awaiting_drivers_responses -= 1
        self.transit_repository.save(transit)

    def complete_transit(self, driver_id: int, transits_id: int, destination: AddressDTO):
        self._complete_transit(driver_id, transits_id, destination.to_address_entity())

    def _complete_transit(self, driver_id: int, transit_id: int, destination_address: Address):
        destination_address = self.address_repository.save(destination_address)
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit = self.transit_repository.get_one(transit_id)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(transit_id))

        if transit.status == Transit.Status.IN_TRANSIT:
            # FIXME later: add some exceptions handling
            geo_from: List[float] = self.geocoding_service.geocode_address(transit.address_from)
            geo_to: List[float] = self.geocoding_service.geocode_address(transit.address_to)

            transit.address_to = destination_address
            transit.set_km(float(self.distance_calculator.calculate_by_map(
                geo_from[0], geo_from[1], geo_to[0], geo_to[1])
            ))
            transit.status = Transit.Status.COMPLETED
            transit.calculate_final_costs()
            driver.is_occupied = False
            transit.complete_at = datetime.now()
            driver_fee: Money = self.driver_fee_service.calculate_driver_fee(transit_id)
            transit.drivers_fee = driver_fee
            self.driver_repository.save(driver)
            self.awards_service.register_miles(transit.client.id, transit_id)
            self.transit_repository.save(transit)
            self.invoice_generator.generate(transit.get_price().to_int(), transit.client.name + " " + transit.client.last_name)
        else:
            raise AttributeError("Cannot complete Transit, id = " + str(transit_id))

    def load_transit(self, transit_id: int) -> TransitDTO:
        return TransitDTO(transit=self.transit_repository.get_one(transit_id))
