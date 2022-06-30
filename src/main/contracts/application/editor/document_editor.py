from uuid import UUID

from fastapi import Depends

from contracts.application.editor.commit_result import CommitResult
from contracts.application.editor.document_dto import DocumentDTO
from contracts.model.content.document_content import DocumentContent
from contracts.model.content.document_content_repository import DocumentContentRepository


class DocumentEditor:
    document_content_repository: DocumentContentRepository

    def __init__(
            self,
            document_content_repository: DocumentContentRepository = Depends(DocumentContentRepository)
    ):
        self.document_content_repository = document_content_repository

    def commit(self, document: DocumentDTO):

        previous_id: UUID = document.content_id

        content: DocumentContent = DocumentContent(
            previous_id,
            document.content_version,
            document.physical_content
        )
        self.document_content_repository.save(content)
        return CommitResult(content.id, CommitResult.Result.SUCCESS)
