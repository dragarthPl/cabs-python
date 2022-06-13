from unittest import TestCase

from contracts.legacy.document import Document
from contracts.legacy.document_status import DocumentStatus
from contracts.legacy.user import User
from core.database import create_db_and_tables, drop_db_and_tables

class TestDocument(TestCase):

    ANY_NUMBER: str = "number"
    ANY_USER: User = User(id=1)
    OTHER_USER: User = User(id=2)
    TITLE: str = "title"

    def setUp(self):
        create_db_and_tables()

    def test_only_draft_can_be_verified_by_user_other_than_creator(self):
        doc: Document = Document(self.ANY_NUMBER, self.ANY_USER)

        doc.verify_by(self.OTHER_USER)

        self.assertEqual(DocumentStatus.VERIFIED, doc.status)

    def test_can_not_change_published(self):
        doc: Document = Document(self.ANY_NUMBER, self.ANY_USER)
        doc.change_title(self.TITLE)
        doc.verify_by(self.OTHER_USER)
        doc.publish()

        try:
            doc.change_title("")
        except AttributeError:
            self.assertTrue(True)
        self.assertEqual(self.TITLE, doc.title)

    def test_changing_verified_moves_to_draft(self):
        doc: Document = Document(self.ANY_NUMBER, self.ANY_USER)
        doc.change_title(self.TITLE)
        doc.verify_by(self.OTHER_USER)

        doc.change_title("")

        self.assertEqual(DocumentStatus.DRAFT, doc.status)

    def tearDown(self) -> None:
        drop_db_and_tables()
