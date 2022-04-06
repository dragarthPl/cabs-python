from fastapi import Depends

from config.app_properties import get_app_properties, AppProperties
from dto.car_type_dto import CarTypeDTO
from entity.car_type import CarType
from repository.car_type_repository import CarTypeRepositoryImp


class CarTypeService:
    car_type_repository: CarTypeRepositoryImp
    app_properties: AppProperties

    def __init__(
            self,
            car_type_repository: CarTypeRepositoryImp = Depends(CarTypeRepositoryImp),
            app_properties: AppProperties = Depends(get_app_properties)
     ):
        self.car_type_repository = car_type_repository
        self.app_properties = app_properties

    # @Transactional
    def load(self, _id: int) -> CarType:
        car_type = self.car_type_repository.get_one(_id)
        if car_type is None:
            raise AttributeError("Cannot find car type")
        return car_type

    # @Transactional
    def load_dto(self, _id: int) -> CarTypeDTO:
        return CarTypeDTO(**self.load(_id).dict())

    # @Transactional
    def create(self, car_type_dto: CarTypeDTO) -> CarType:
        by_car_class: CarType = self.car_type_repository.find_by_car_class(car_type_dto.car_class)
        if by_car_class is None:
            car_type: CarType = CarType(
                car_type_dto.car_class,
                car_type_dto.description,
                self.__get_min_number_of_cars(car_type_dto.car_class)
            )
            return self.car_type_repository.save(car_type)
        else:
            by_car_class.description = car_type_dto.description
            return by_car_class

    # @Transactional
    def activate(self, _id: int) -> None:
        car_type = self.load(_id)
        car_type.activate()
        self.car_type_repository.save(car_type)

    # @Transactional
    def deactivate(self, _id: int) -> None:
        car_type = self.load(_id)
        car_type.deactivate()
        self.car_type_repository.save(car_type)

    # @Transactional
    def register_car(self, car_class: CarType.CarClass) -> None:
        car_type = self.__find_by_car_class(car_class)
        car_type.register_car()
        self.car_type_repository.save(car_type)

    # @Transactional
    def unregister_car(self, car_class: CarType.CarClass) -> None:
        car_type = self.__find_by_car_class(car_class)
        car_type.unregister_car()
        self.car_type_repository.save(car_type)

    # @Transactional
    def unregister_active_car(self, car_class: CarType.CarClass) -> None:
        car_type = self.__find_by_car_class(car_class)
        car_type.unregister_active_car()
        self.car_type_repository.save(car_type)

    # @Transactional
    def register_active_car(self, car_class: CarType.CarClass) -> None:
        car_type = self.__find_by_car_class(car_class)
        car_type.register_active_car()
        self.car_type_repository.save(car_type)

    # @Transactional
    # public List<CarClass> findActiveCarClasses() {

    def __get_min_number_of_cars(self, car_class: CarType.CarClass) -> int:
        if car_class == CarType.CarClass.ECO:
            return self.app_properties.min_no_of_cars_for_eco_class
        else:
            return 10

    # @Transactional
    def remove_car_type(self, car_class: CarType.CarClass):
        car_type = self.__find_by_car_class(car_class)
        if car_type is not None:
            self.car_type_repository.delete(car_type)

    def __find_by_car_class(self, car_class: CarType.CarClass) -> CarType:
        by_car_class = self.car_type_repository.find_by_car_class(car_class)
        if by_car_class is None:
            raise AttributeError("Car class does not exist: " + car_class)
        return by_car_class


