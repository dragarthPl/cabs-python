import enum


class Status(enum.Enum):
    DRAFT = 1
    NEW = 2
    IN_PROCESS = 3
    REFUNDED = 4
    ESCALATED = 5
    REJECTED = 6
