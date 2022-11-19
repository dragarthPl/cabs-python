import json
from datetime import datetime
from typing import Any, Optional, Set
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy import Enum, Column
from sqlmodel import Field

from assignment.assignment_status import AssignmentStatus
from common.base_entity import BaseEntity


class DriverAssignment(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    request_uuid: Optional[UUID]
    published_at: Optional[datetime]
    status: Optional[AssignmentStatus] = Field(
        default=AssignmentStatus.WAITING_FOR_DRIVER_ASSIGNMENT,
        sa_column=Column(Enum(AssignmentStatus))
    )
    assigned_driver: Optional[int]
    drivers_rejections: Optional[str]
    proposed_drivers: Optional[str]
    awaiting_drivers_responses: int = 0

    def __init__(self, request_uuid: Optional[UUID] = None, published_at: Optional[datetime] = None, **data: Any):
        super().__init__(**data)
        self.request_uuid = request_uuid
        self.published_at = published_at

    def cancel(self) -> None:
        if self.status not in (AssignmentStatus.WAITING_FOR_DRIVER_ASSIGNMENT, AssignmentStatus.ON_THE_WAY):
            raise AttributeError(f"Transit cannot be cancelled, id = {self.id}")
        self.status = AssignmentStatus.CANCELLED
        self.assigned_driver = None
        self.awaiting_drivers_responses = 0

    def can_propose_to(self, driver_id: int) -> bool:
        return driver_id not in self.get_driver_rejections()

    def propose_to(self, driver_id: int) -> None:
        if self.can_propose_to(driver_id):
            self.__add_driver_to_proposed(driver_id)
            self.awaiting_drivers_responses += 1

    def __add_driver_to_proposed(self, driver_id: int) -> None:
        proposed_drivers_set: Set[int] = self.get_proposed_drivers()
        proposed_drivers_set.add(driver_id)
        self.proposed_drivers = json.dumps(list(proposed_drivers_set))

    def fail_driver_assignment(self) -> None:
        self.status = AssignmentStatus.DRIVER_ASSIGNMENT_FAILED
        self.assigned_driver = None
        self.awaiting_drivers_responses = 0

    def should_not_wait_for_driver_any_more(self, date: datetime) -> bool:
        return self.status == AssignmentStatus.CANCELLED or (self.published_at + relativedelta(seconds=300) < date)

    def accept_by(self, driver_id: int):
        if self.assigned_driver:
            raise AttributeError(f"Transit already accepted, id = {self.id}")
        else:
            if driver_id not in self.get_proposed_drivers():
                raise AttributeError(f"Driver out of possible drivers, id = {self.id}")
            else:
                if driver_id in self.get_driver_rejections():
                    raise AttributeError(f"Driver out of possible drivers, id = {self.id}")
        self.assigned_driver = driver_id
        self.awaiting_drivers_responses = 0
        self.status = AssignmentStatus.ON_THE_WAY

    def reject_by(self, driver_id: int):
        self.__add_to_driver_rejections(driver_id)
        self.awaiting_drivers_responses -= 1

    def __add_to_driver_rejections(self, driver_id: int) -> None:
        driver_rejection_set: Set[int] = self.get_driver_rejections()
        driver_rejection_set.add(driver_id)
        self.drivers_rejections = json.dumps(list(driver_rejection_set))

    def get_driver_rejections(self) -> Set[int]:
        return set(json.loads(self.drivers_rejections)) if self.drivers_rejections else set()

    def get_proposed_drivers(self) -> Set[int]:
        return set(json.loads(self.proposed_drivers)) if self.proposed_drivers else set()
