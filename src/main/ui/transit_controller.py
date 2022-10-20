from fastapi_injector import Injected

from dto.address_dto import AddressDTO
from dto.transit_dto import TransitDTO
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from service.transit_service import TransitService

transit_router = InferringRouter(tags=["TransitController"])

@cbv(transit_router)
class TransitController:
    transit_service: TransitService = Injected(TransitService)

    @transit_router.get("/transits/{transits_id}")
    def get_transit(self, transits_id: int) -> TransitDTO:
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/")
    def create_transit(self, transit_dto: TransitDTO) -> TransitDTO:
        transit = self.transit_service.create_transit(transit_dto)
        return self.transit_service.load_transit(transit.id)

    @transit_router.post("/transits/{transits_id}/changeAddressTo")
    def change_address_to(self, transits_id: int, address_dto: AddressDTO) -> TransitDTO:
        self.transit_service.change_transit_address_to(transits_id, address_dto)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/changeAddressFrom")
    def change_address_from(self, transits_id: int, address_dto: AddressDTO) -> TransitDTO:
        self.transit_service.change_transit_address_from(transits_id, address_dto)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/cancel")
    def cancel(self, transits_id: int) -> TransitDTO:
        self.transit_service.cancel_transit(transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/publish")
    def publish_transit(self, transits_id: int) -> TransitDTO:
        self.transit_service.publish_transit(transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/findDrivers")
    def find_drivers_for_transit(self, transits_id: int) -> TransitDTO:
        self.transit_service.find_drivers_for_transit(transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/accept/{driver_id}")
    def accept_transit(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.accept_transit(driver_id, transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/start/{driver_id}")
    def start(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.start_transit(driver_id, transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/reject/{driver_id}")
    def reject(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.reject_transit(driver_id, transits_id)
        return self.transit_service.load_transit(transits_id)

    @transit_router.post("/transits/{transits_id}/complete/{driver_id}")
    def complete(self, transits_id: int, driver_id: int, destination: AddressDTO) -> TransitDTO:
        self.transit_service.complete_transit(driver_id, transits_id, destination)
        return self.transit_service.load_transit(transits_id)
