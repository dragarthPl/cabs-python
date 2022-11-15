import enum


class DocumentStatus(enum.Enum):
    DRAFT = 1
    VERIFIED = 2
    PUBLISHED = 3
    ARCHIVED = 4
