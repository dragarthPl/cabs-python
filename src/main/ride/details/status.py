import enum


class Status(enum.Enum):
    DRAFT = 1
    CANCELLED = 2
    WAITING_FOR_DRIVER_ASSIGNMENT = 3
    DRIVER_ASSIGNMENT_FAILED = 4
    TRANSIT_TO_PASSENGER = 5
    IN_TRANSIT = 6
    COMPLETED = 7
