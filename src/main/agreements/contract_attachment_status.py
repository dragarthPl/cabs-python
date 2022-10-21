import enum


class ContractAttachmentStatus(enum.Enum):
    PROPOSED = 1
    ACCEPTED_BY_ONE_SIDE = 2
    ACCEPTED_BY_BOTH_SIDES = 3
    REJECTED = 4
