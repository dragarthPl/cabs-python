import enum


class AssignmentStatus(enum.Enum):
    CANCELLED = 1
    WAITING_FOR_DRIVER_ASSIGNMENT = 2
    DRIVER_ASSIGNMENT_FAILED = 3
    ON_THE_WAY = 4

