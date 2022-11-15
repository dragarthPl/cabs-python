from typing import Set, Optional

from assignment.assignment_status import AssignmentStatus


class InvolvedDriversSummary:
    proposed_drivers: Set[int] = set()
    driver_rejections: Set[int] = set()
    assigned_driver: int = 0
    status: AssignmentStatus

    def __init__(
        self,
        proposed_drivers: Set[int],
        driver_rejections: Set[int],
        assigned_driver_id: Optional[int],
        status: AssignmentStatus,
    ):
        self.proposed_drivers = proposed_drivers
        self.driver_rejections = driver_rejections
        self.status = status

    @classmethod
    def none_found(cls) -> 'InvolvedDriversSummary':
        return cls(set(), set(), None, AssignmentStatus.DRIVER_ASSIGNMENT_FAILED)
