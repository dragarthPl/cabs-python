from typing import List, Optional

from injector import inject
from sqlalchemy import text

from carfleet.car_class import CarClass
from entity import CarTypeActiveCounter
from carfleet.car_type import CarType
from sqlmodel import Session

class CarTypeActiveCounterRepositoryImp:

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_car_class(self, car_class: CarClass) -> Optional[CarTypeActiveCounter]:
        return self.session.query(CarTypeActiveCounter).filter(CarTypeActiveCounter.car_class == car_class).first()

    def increment_counter(self, car_class: CarClass) -> None:
        stmt = text(
            "UPDATE cartypeactivecounter AS counter "
            "SET active_cars_counter = active_cars_counter + 1 where counter.car_class = :car_class"
        )
        stmt = stmt.bindparams(car_class=car_class)
        self.session.execute(stmt)

    def decrement_counter(self, car_class: CarClass) -> None:
        stmt = text(
            "UPDATE cartypeactivecounter AS counter "
            "SET active_cars_counter = active_cars_counter - 1 where counter.car_class = :car_class"
        )
        stmt = stmt.bindparams(car_class=car_class)
        self.session.execute(stmt)

    def save(self, car_type_active_counter: CarTypeActiveCounter) -> Optional[CarTypeActiveCounter]:
        self.session.add(car_type_active_counter)
        self.session.commit()
        self.session.refresh(car_type_active_counter)
        return car_type_active_counter


class CarTypeRepositoryImp:
    session: Session
    car_type_active_counter_repository: CarTypeActiveCounterRepositoryImp

    @inject
    def __init__(
            self,
            session: Session,
            car_type_active_counter_repository: CarTypeActiveCounterRepositoryImp
    ) -> None:
        self.session = session
        self.car_type_active_counter_repository = car_type_active_counter_repository

    def save(self, car_type: CarType) -> Optional[CarType]:
        self.car_type_active_counter_repository.save(CarTypeActiveCounter(car_class=car_type.car_class))
        self.session.add(car_type)
        self.session.commit()
        self.session.refresh(car_type)
        return car_type

    def find_by_car_class(self, car_class: CarClass) -> Optional[CarType]:
        statement = self.session.query(CarType).where(CarType.car_class == car_class)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()

    def find_active_counter(self, car_class: CarClass) -> CarTypeActiveCounter:
        return self.car_type_active_counter_repository.find_by_car_class(car_class)

    def increment_counter(self, car_class: CarClass) -> None:
        self.car_type_active_counter_repository.increment_counter(car_class)

    def decrement_counter(self, car_class: CarClass) -> None:
        self.car_type_active_counter_repository.decrement_counter(car_class)

    def get_one(self, car_type_id: int) -> Optional[CarType]:
        statement = self.session.query(CarType).where(CarType.id == car_type_id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()

    def delete(self, car_type) -> None:
        self.session.delete(car_type)
        self.session.commit()

    def find_by_status(self, status: CarType.Status) -> List[CarType]:
        return self.session.query(CarType).where(CarType.status == status).all()




