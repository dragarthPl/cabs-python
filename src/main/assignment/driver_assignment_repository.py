from typing import Optional
from uuid import UUID

from injector import inject
from sqlmodel import Session

from assignment.assignment_status import AssignmentStatus
from assignment.driver_assignment import DriverAssignment


class DriverAssignmentRepository:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_request_uuid(self, request_uuid: UUID) -> DriverAssignment:
        return self.session.query(DriverAssignment).where(DriverAssignment.request_uuid == request_uuid).first()

    def find_by_request_uuid_and_status(self, request_uuid: UUID, status: AssignmentStatus) -> DriverAssignment:
        return self.session.query(DriverAssignment).where(
            DriverAssignment.request_uuid == request_uuid
        ).where(
            DriverAssignment.status == status
        ).first()

    def save(self, driver_assignment: DriverAssignment) -> Optional[DriverAssignment]:
        self.session.add(driver_assignment)
        self.session.commit()
        self.session.refresh(driver_assignment)
        return driver_assignment
