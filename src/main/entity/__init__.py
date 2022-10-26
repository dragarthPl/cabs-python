from driverfleet.driver_license import DriverLicense
from .tariff import Tariff

from geolocation.address.address import Address
from carfleet.car_type import CarType
from .transit import Transit
from crm.client import Client


__all__ = [
    "Address",
    "CarType",
    "Transit",
    "Client",
    "DriverLicense",
    "Tariff",
]
