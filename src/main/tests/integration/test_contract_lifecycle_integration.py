from unittest import TestCase
from fastapi.params import Depends


from core.database import create_db_and_tables, drop_db_and_tables
from dto.contract_attachment_dto import ContractAttachmentDTO
from dto.contract_dto import ContractDTO
from entity import Contract, ContractAttachment
from service.contract_service import ContractService
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestContractLifecycleIntegration(TestCase):
    contract_service: ContractService = dependency_resolver.resolve_dependency(Depends(ContractService))

    def setUp(self):
        create_db_and_tables()

    def test_can_create_contract(self):
        # given
        created: ContractDTO = self.create_contract("partnerNameVeryUnique", "umowa o cenę")

        # when
        loaded: ContractDTO = self.load_contract(created.id)

        # then
        self.assertEqual("partnerNameVeryUnique", loaded.partner_name)
        self.assertEqual("umowa o cenę", loaded.subject)
        self.assertEqual("C/1/partnerNameVeryUnique", loaded.contract_no)
        self.assertEqual(Contract.Status.NEGOTIATIONS_IN_PROGRESS, loaded.status)
        self.assertIsNotNone(loaded.id)
        self.assertIsNotNone(loaded.creation_date)
        self.assertIsNotNone(loaded.creation_date)
        self.assertIsNone(loaded.change_date)
        self.assertIsNone(loaded.accepted_at)
        self.assertIsNone(loaded.rejected_at)

    def test_second_contract_for_the_same_partner_has_correct_no(self):
        # given
        first: ContractDTO = self.create_contract("uniqueName", "umowa o cenę")

        # when
        second: ContractDTO = self.create_contract("uniqueName", "umowa o cenę")
        # then
        first_loaded = self.load_contract(first.id)
        second_loaded = self.load_contract(second.id)

        self.assertEqual("uniqueName", first_loaded.partner_name)
        self.assertEqual("uniqueName", second_loaded.partner_name)
        self.assertEqual("C/1/uniqueName", first_loaded.contract_no)
        self.assertEqual("C/2/uniqueName", second_loaded.contract_no)

    def test_can_add_attachment_to_contract(self):
        # given
        created: ContractDTO = self.create_contract("partnerName", "umowa o cenę")

        # when
        self.add_attachment_to_contract(created, b"content")

        # then
        loaded = self.load_contract(created.id)
        self.assertEqual(1, len(loaded.attachments))
        self.assertEqual(b"content", loaded.attachments[0].data)
        self.assertEqual(ContractAttachment.Status.PROPOSED, loaded.attachments[0].status)

    def test_can_remove_attachment_from_contract(self):
        # given
        created: ContractDTO = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")

        # when
        self.remove_attachment_from_contract(created, attachment)

        # then
        loaded = self.load_contract(created.id)
        self.assertEqual(0, len(loaded.attachments))

    def test_can_accept_attachment_by_one_side(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")

        # when
        self.accept_attachment(attachment)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertEqual(1, len(loaded.attachments))
        self.assertEqual(ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE, loaded.attachments[0].status)

    def test_can_accept_attachment_by_two_sides(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")

        # when
        self.accept_attachment(attachment)
        # and
        self.accept_attachment(attachment)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertEqual(1, len(loaded.attachments))
        self.assertEqual(ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES, loaded.attachments[0].status)

    def test_can_reject_attachment(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")

        # when
        self.reject_attachment(attachment)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertEqual(1, len(loaded.attachments))
        self.assertEqual(ContractAttachment.Status.REJECTED, loaded.attachments[0].status)

    def test_can_accept_contract_when_all_attachments_accepted(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")
        # and
        self.accept_attachment(attachment)
        self.accept_attachment(attachment)

        # when
        self.accept_contract(created)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertEqual(Contract.Status.ACCEPTED, loaded.status)

    def test_can_reject_contract(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")
        # and
        self.accept_attachment(attachment)
        self.accept_attachment(attachment)

        # when
        self.reject_contract(created)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertEqual(Contract.Status.REJECTED, loaded.status)

    def test_cannot_accept_contract_when_not_all_attachments_accepted(self):
        # given
        created = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachmentDTO = self.add_attachment_to_contract(created, b"content")
        # and
        self.accept_attachment(attachment)

        # when
        with self.assertRaises(AttributeError):
            self.accept_contract(created)

        # then
        loaded: ContractDTO = self.load_contract(created.id)
        self.assertNotEqual(Contract.Status.ACCEPTED, loaded.status)

    def load_contract(self, contract_id: int) -> ContractDTO:
        return self.contract_service.find_dto(contract_id)

    def create_contract(self, partner_name: str, subject: str) -> ContractDTO:
        dto = ContractDTO()
        dto.partner_name = partner_name
        dto.subject = subject
        contract: Contract = self.contract_service.create_contract(dto)
        return self.load_contract(contract.id)

    def add_attachment_to_contract(self, created: ContractDTO, content: bytes) -> ContractAttachmentDTO:
        contract_attachment_dto = ContractAttachmentDTO()
        contract_attachment_dto.data = content
        return self.contract_service.propose_attachment(created.id, contract_attachment_dto)

    def remove_attachment_from_contract(self, contract: ContractDTO, attachment: ContractAttachmentDTO) -> None:
        self.contract_service.remove_attachment(contract.id, attachment.id)

    def accept_attachment(self, attachment: ContractAttachmentDTO) -> None:
        self.contract_service.accept_attachment(attachment.id)

    def reject_attachment(self, attachment: ContractAttachmentDTO) -> None:
        self.contract_service.reject_attachment(attachment.id)

    def accept_contract(self, contract: ContractDTO) -> None:
        self.contract_service.accept_contract(contract.id)

    def reject_contract(self, contract: ContractDTO) -> None:
        self.contract_service.reject_contract(contract.id)

    def tearDown(self) -> None:
        drop_db_and_tables()