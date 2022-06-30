from fastapi import Depends

from common.application_event_publisher import ApplicationEventPublisher
from contracts.model.state.dynamic.config.actions.change_verifier import ChangeVerifier
from contracts.model.state.dynamic.config.actions.publish_event import PublishEvent
from contracts.model.state.dynamic.config.events.document_published import DocumentPublished
from contracts.model.state.dynamic.config.events.document_unpublished import DocumentUnpublished
from contracts.model.state.dynamic.config.statechange.author_is_not_averifier import AuthorIsNotAVerifier
from contracts.model.state.dynamic.config.statechange.content_not_empty_verifier import ContentNotEmptyVerifier
from contracts.model.state.dynamic.state_builder import StateBuilder
from contracts.model.state.dynamic.state_config import StateConfig

class AcmeContractStateAssembler:
    VERIFIED: str = "verified"
    DRAFT: str = "draft"
    PUBLISHED: str = "published"
    ARCHIVED: str = "archived"

    PARAM_VERIFIER: str = ChangeVerifier.PARAM_VERIFIER

    __publisher: ApplicationEventPublisher

    def __init__(
            self,
            publisher: ApplicationEventPublisher = Depends(ApplicationEventPublisher),
    ):
        self.__publisher = publisher

    def assemble(self) -> StateConfig:
        builder: StateBuilder = StateBuilder()
        builder.begin_with(
            self.DRAFT
        ).check(
            ContentNotEmptyVerifier()
        ).check(
            AuthorIsNotAVerifier()
        ).to(
            self.VERIFIED
        ).action(
            ChangeVerifier()
        )
        builder.from_name(
            self.DRAFT
        ).when_content_changed().to(
            self.DRAFT
        )
        # name of the "published" state and name of the DocumentPublished event are NOT correlated.
        # These are two different domains, name similarity is just a coincidence
        builder.from_name(
            self.VERIFIED
        ).check(
            ContentNotEmptyVerifier()
        ).to(
            self.PUBLISHED
        ).action(
            PublishEvent(
                DocumentPublished,
                self.__publisher
            )
        )
        builder.from_name(self.VERIFIED).when_content_changed().to(self.DRAFT)
        builder.from_name(self.DRAFT).to(self.ARCHIVED)
        builder.from_name(self.VERIFIED).to(self.ARCHIVED)
        builder.from_name(self.PUBLISHED).to(self.ARCHIVED).action(PublishEvent(DocumentUnpublished, self.__publisher))

        return builder
