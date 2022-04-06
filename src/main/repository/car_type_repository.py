from abc import ABCMeta, abstractmethod
from typing import Optional, List

from fastapi import Depends

from core.database import get_session
from entity.car_type import CarType

from sqlmodel import Session, select


class CarTypeRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, car_type: CarType) -> Optional[CarType]:
        self.session.add(car_type)
        self.session.commit()
        self.session.refresh(car_type)
        return car_type

    def find_by_car_class(self, car_class: CarType.CarClass) -> Optional[CarType]:
        statement = select(CarType).where(CarType.car_class == car_class)
        results = self.session.exec(statement)
        return results.first()

    def get_one(self, car_type_id: int) -> Optional[CarType]:
        statement = select(CarType).where(CarType.id == car_type_id)
        results = self.session.exec(statement)
        return results.first()

    def delete(self, car_type) -> None:
        self.session.delete(car_type)
        self.session.commit()
