import functools
import math
from datetime import datetime
from typing import List, Dict

from dateutil.relativedelta import relativedelta
from injector import inject

from carfleet.car_class import CarClass
from driverfleet.driver_dto import DriverDTO
from driverfleet.driver_service import DriverService
from geolocation.address.address_dto import AddressDTO
from geolocation.distance import Distance
from driverfleet.driver import Driver
from driverfleet.driverreport.travelleddistance.travelled_distance_service import TravelledDistanceService
from geolocation.geocoding_service import GeocodingService
from tracking.driver_position import DriverPosition
from tracking.driver_position_dtov_2 import DriverPositionDTOV2
from tracking.driver_position_repository import DriverPositionRepositoryImp
from tracking.driver_session_service import DriverSessionService


class DriverTrackingService:
    position_repository: DriverPositionRepositoryImp
    driver_service: DriverService
    travelled_distance_service: TravelledDistanceService
    driver_session_service: DriverSessionService
    geocoding_service: GeocodingService

    @inject
    def __init__(
            self,
            position_repository: DriverPositionRepositoryImp,
            driver_service: DriverService,
            travelled_distance_service: TravelledDistanceService,
            driver_session_service: DriverSessionService,
            geocoding_service: GeocodingService,
    ):
        self.position_repository = position_repository
        self.driver_service = driver_service
        self.driver_session_service = driver_session_service
        self.travelled_distance_service = travelled_distance_service
        self.geocoding_service = geocoding_service

    def register_position(self, driver_id: int, latitude: float, longitude: float, seen_at: datetime) -> DriverPosition:
        driver: DriverDTO = self.driver_service.load_driver(driver_id)
        if driver is None:
            raise AttributeError(("Driver does not exists, id = " + str(driver_id)))
        if driver.status != Driver.Status.ACTIVE:
            raise AttributeError(("Driver is not active, cannot register position, id = " + str(driver_id)))

        position = DriverPosition()
        position.driver_id = driver_id
        position.seen_at = seen_at
        position.latitude = latitude
        position.longitude = longitude
        position = self.position_repository.save(position)
        self.travelled_distance_service.add_position(driver_id, latitude, longitude, seen_at)
        return position

    def calculate_travelled_distance(self, driver_id: int, since: datetime, to: datetime) -> Distance:
        return self.travelled_distance_service.calculate_distance(driver_id, since, to)

    def find_active_drivers_nearby_by_address(
            self,
            address: AddressDTO,
            distance: Distance,
            car_classes: List[CarClass]
    ) -> List[DriverPositionDTOV2]:
        geocoded: List[float] = []

        try:
            geocoded = self.geocoding_service.geocode_address(address.to_address_entity())
        except Exception:
            pass

        longitude: float = geocoded[1]
        latitude: float = geocoded[0]

        # https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
        # Earth’s radius, sphere
        # double R = 6378;
        R: float = 6371  # Changed to 6371 due to Copy&Paste pattern from different source

        # offsets in meters
        dn: float = distance.to_km_in_float()
        de: float = distance.to_km_in_float()

        d_lat: float = dn / R
        d_lon: float = de / (R * math.cos(math.pi * latitude / 180))

        # Offset positions, decimal degrees
        latitude_min = latitude - d_lat * 180 / math.pi
        latitude_max = latitude + d_lat * 180 / math.pi
        longitude_min = longitude - d_lon * 180 / math.pi
        longitude_max = longitude + d_lon * 180 / math.pi

        return self.find_active_drivers_nearby(
            latitude_min,
            latitude_max,
            longitude_min,
            longitude_max,
            latitude,
            longitude,
            car_classes
        )

    def find_active_drivers_nearby(
            self,
            latitude_min: float,
            latitude_max: float,
            longitude_min: float,
            longitude_max: float,
            latitude: float,
            longitude: float,
            car_classes: List[CarClass],
    ) -> List[DriverPositionDTOV2]:
        drivers_avg_positions: List[DriverPositionDTOV2] = self.position_repository.find_average_driver_position_since(
            latitude_min,
            latitude_max,
            longitude_min,
            longitude_max,
            datetime.now() - relativedelta(minutes=5)
        )

        def comparator(d1, d2):
            d1 = math.sqrt(
                math.pow(latitude - d1.latitude, 2) + math.pow(longitude - d1.longitude, 2)
            )
            d2 = math.sqrt(
                math.pow(latitude - d2.latitude, 2) + math.pow(longitude - d2.longitude, 2)
            )
            if d1 < d2:
                return -1
            if d1 > d2:
                return 1
            return 0

        drivers_avg_positions = sorted(drivers_avg_positions, key=functools.cmp_to_key(comparator))
        drivers_avg_positions = drivers_avg_positions[:20]

        drivers_ids: List[int] = list(map(
            lambda position: position.driver_id,
            drivers_avg_positions
        ))
        active_driver_ids_in_specific_car: List[int] = self.driver_session_service.find_currently_logged_driver_ids(
            drivers_ids,
            car_classes
        )

        drivers_avg_positions = list(filter(
            lambda dp: dp.driver_id in active_driver_ids_in_specific_car,
            drivers_avg_positions
        ))

        drivers: Dict[int, DriverDTO] = dict(list(map(
            lambda driver: (driver.id, driver),
            self.driver_service.load_drivers(drivers_ids)
        )))

        def position_filter(dap: DriverPositionDTOV2) -> bool:
            d: DriverDTO = drivers.get(dap.driver_id)
            return bool(d.status == Driver.Status.ACTIVE and not d.is_occupied)

        drivers_avg_positions = list(
            filter(
                lambda dap: position_filter(dap),
                drivers_avg_positions
            )
        )
        return drivers_avg_positions
