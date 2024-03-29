from fastapi_injector import Injected

from carfleet.car_class import CarClass
from carfleet.car_type_dto import CarTypeDTO
from carfleet.car_type import CarType
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from carfleet.car_type_service import CarTypeService

car_type_router = InferringRouter(tags=["CarTypeController"])

@cbv(car_type_router)
class CarTypeController:

    car_type_service: CarTypeService = Injected(CarTypeService)

    @car_type_router.post("/cartypes")
    def create(self, car_type_dto: CarTypeDTO) -> CarTypeDTO:
        created: CarTypeDTO = self.car_type_service.create(car_type_dto)
        return created

    @car_type_router.post("/cartypes/{car_class}/registerCar")
    def register_car(self, car_class: CarClass) -> dict:
        self.car_type_service.register_car(car_class)
        return {}

    @car_type_router.post("/cartypes/{car_class}/unregisterCar")
    def unregister_car(self, car_class: CarClass) -> dict:
        self.car_type_service.unregister_car(car_class)
        return {}

    @car_type_router.post("/cartypes/{car_type_id}/activate")
    def activate(self, car_type_id: int) -> dict:
        self.car_type_service.activate(car_type_id)
        return {}

    @car_type_router.post("/cartypes/{car_type_id}/deactivate")
    def deactivate(self, car_type_id: int) -> dict:
        self.car_type_service.deactivate(car_type_id)
        return {}

    @car_type_router.get("/cartypes/{car_type_id}")
    def find(self, car_type_id: int) -> CarTypeDTO:
        car_type = self.car_type_service.load_dto(car_type_id)
        return car_type
