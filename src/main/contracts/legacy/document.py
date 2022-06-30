from typing import Set, Any, Optional

from sqlalchemy import Column, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlmodel import Field, SQLModel, Relationship

from contracts.legacy.base_aggregate_root import BaseAggregateRoot
from contracts.legacy.document_status import DocumentStatus
from contracts.legacy.printable import Printable
from contracts.legacy.user import User


document_user_link = Table(
    'document_user_link',
    SQLModel.metadata,
    Column('document_id', ForeignKey('document.id')),
    Column('user_id', ForeignKey('user.id'))
)


class Document(BaseAggregateRoot, Printable, table=True):
    __table_args__ = {'extend_existing': True}

    number: str
    title: str
    content: str

    # @Enumerated(EnumType.STRING)
    status: DocumentStatus = Field(default=DocumentStatus.DRAFT, sa_column=Column(Enum(DocumentStatus)))

    # @ManyToMany
    assigned_users: Set[User] = Relationship(
        sa_relationship=relationship(
            "contracts.legacy.user.User", secondary=document_user_link)
    )

    # @ManyToOne
    creator_id: Optional[int] = Field(default=None, foreign_key="user.id")
    creator: Optional[User] = Relationship(
        # sa_relationship=relationship(
        #     "contracts.legacy.user.User")
        sa_relationship_kwargs=dict(foreign_keys="[Document.creator_id]")
    )

    # @ManyToOne
    verifier_id: Optional[int] = Field(default=None, foreign_key="user.id")
    verifier: Optional[User] = Relationship(
        # sa_relationship=relationship(
        #     "contracts.legacy.user.User"),
        sa_relationship_kwargs=dict(foreign_keys="[Document.verifier_id]")
    )

    override_published: bool

    def __init__(self, number: str, creator: User, **data: Any):
        super().__init__(**data)
        self.number = number
        self.creator = creator

    def verify_by(self, verifier: User) -> None:
        if self.status != DocumentStatus.DRAFT:
            raise AttributeError(f"Can not verify in status: {self.status}")
        if self.creator == verifier:
            raise AttributeError(f"Verifier can not verify documents by himself")
        self.verifier = verifier
        self.status = DocumentStatus.VERIFIED

    def publish(self) -> None:
        if self.status != DocumentStatus.VERIFIED:
            raise AttributeError(f"Can not publish in status: {self.status}")
        self.status = DocumentStatus.PUBLISHED

    #===============================================================

    def change_title(self, title: str):
        if self.status == DocumentStatus.ARCHIVED or self.status == DocumentStatus.PUBLISHED:
            raise AttributeError(f"Can not change title in status: {self.status}")
        self.title = title
        if self.status == DocumentStatus.VERIFIED:
            self.status = DocumentStatus.DRAFT

    def change_content(self, content: str, user_status: Optional[str] = None) -> None:
        if self.override_published:
            self.content = content
            return

        if self.status == DocumentStatus.ARCHIVED or self.status == DocumentStatus.PUBLISHED:
            raise AttributeError(f"Can not change content in status: {self.status}")
        self.status = content
        if self.status == DocumentStatus.VERIFIED:
            self.status = DocumentStatus.DRAFT
