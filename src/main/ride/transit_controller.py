from uuid import UUID

from fastapi_injector import Injected

from geolocation.address.address_dto import AddressDTO
from ride.transit_dto import TransitDTO
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from ride.transit_service import TransitService

transit_router = InferringRouter(tags=["TransitController"])

@cbv(transit_router)
class TransitController:
    transit_service: TransitService = Injected(TransitService)

    @transit_router.get("/transits/{request_uuid}")
    def get_transit(self, request_uuid: UUID) -> TransitDTO:
        return self.transit_service.load_transit_by_uuid(request_uuid)

    @transit_router.post("/transits/")
    def create_transit(self, transit_dto: TransitDTO) -> TransitDTO:
        return self.transit_service.create_transit(transit_dto)

    @transit_router.post("/transits/{transits_id}/changeAddressTo")
    def change_address_to(self, transits_id: int, address_dto: AddressDTO) -> TransitDTO:
        self.transit_service.change_transit_address_to(
            self.transit_service.get_request_uuid(transits_id),
            address_dto
        )
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/changeAddressFrom")
    def change_address_from(self, transits_id: int, address_dto: AddressDTO) -> TransitDTO:
        self.transit_service.change_transit_address_from(
            self.transit_service.get_request_uuid(transits_id),
            address_dto
        )
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/cancel")
    def cancel(self, transits_id: int) -> TransitDTO:
        self.transit_service.cancel_transit(self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/publish")
    def publish_transit(self, transits_id: int) -> TransitDTO:
        self.transit_service.publish_transit(self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/findDrivers")
    def find_drivers_for_transit(self, transits_id: int) -> TransitDTO:
        self.transit_service.find_drivers_for_transit(self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/accept/{driver_id}")
    def accept_transit(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.accept_transit(driver_id, self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/start/{driver_id}")
    def start(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.start_transit(driver_id, self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/reject/{driver_id}")
    def reject(self, transits_id: int, driver_id: int) -> TransitDTO:
        self.transit_service.reject_transit(driver_id, self.transit_service.get_request_uuid(transits_id))
        return self.transit_service.load_transit_by_id(transits_id)

    @transit_router.post("/transits/{transits_id}/complete/{driver_id}")
    def complete(self, transits_id: int, driver_id: int, destination: AddressDTO) -> TransitDTO:
        self.transit_service.complete_transit(
            driver_id,
            self.transit_service.get_request_uuid(transits_id),
            destination
        )
        return self.transit_service.load_transit_by_id(transits_id)
