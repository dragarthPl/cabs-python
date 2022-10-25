from unittest import TestCase

from agreements.contract_attachment import ContractAttachment
from agreements.contract_attachment_status import ContractAttachmentStatus
from agreements.contract_status import ContractStatus
from agreements.contract import Contract


class TestContractLifecycle(TestCase):

    def test_can_create_contract(self):
        # when
        contract: Contract = self.create_contract("partnerNameVeryUnique", "umowa o cenę")

        # then
        self.assertEqual("partnerNameVeryUnique", contract.partner_name)
        self.assertEqual("umowa o cenę", contract.subject)
        self.assertEqual(ContractStatus.NEGOTIATIONS_IN_PROGRESS, contract.status)
        self.assertIsNotNone(contract.creation_date)
        self.assertIsNone(contract.change_date)
        self.assertIsNone(contract.accepted_at)
        self.assertIsNone(contract.rejected_at)

    def test_can_add_attachment_to_contract(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")

        # when
        contract_attachment: ContractAttachment = contract.propose_attachment()

        # then
        self.assertEqual(1, len(contract.get_attachment_ids()))
        self.assertEqual(
            ContractAttachmentStatus.PROPOSED,
            contract.find_attachment(contract_attachment.contract_attachment_no).status
        )

    def test_can_remove_attachment_from_contract(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()

        # when
        contract.remove(attachment.contract_attachment_no)
        # then
        self.assertEqual(0, len(contract.get_attachment_ids()))

    def test_can_accept_attachment_by_one_side(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()

        # when
        contract.accept_attachment(attachment.contract_attachment_no)

        # then
        self.assertEqual(1, len(contract.get_attachment_ids()))
        self.assertEqual(
            ContractAttachmentStatus.ACCEPTED_BY_ONE_SIDE,
            contract.find_attachment(attachment.contract_attachment_no).status
        )

    def test_can_accept_attachment_by_two_sides(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()

        # when
        contract.accept_attachment(attachment.contract_attachment_no)
        contract.accept_attachment(attachment.contract_attachment_no)

        # then
        self.assertEqual(1, len(contract.get_attachment_ids()))
        self.assertEqual(
            ContractAttachmentStatus.ACCEPTED_BY_BOTH_SIDES,
            contract.find_attachment(attachment.contract_attachment_no).status
        )

    def test_can_reject_attachment(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()

        # when
        contract.reject_attachment(attachment.contract_attachment_no)

        # then
        self.assertEqual(1, len(contract.get_attachment_ids()))
        self.assertEqual(
            ContractAttachmentStatus.REJECTED,
            contract.find_attachment(attachment.contract_attachment_no).status
        )

    def test_can_accept_contract_when_all_attachments_accepted(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()
        contract.accept_attachment(attachment.contract_attachment_no)
        # and
        contract.accept_attachment(attachment.contract_attachment_no)
        contract.accept_attachment(attachment.contract_attachment_no)

        # when
        contract.accept()

        # then
        self.assertEqual(
            ContractStatus.ACCEPTED,
            contract.status
        )

    def test_can_reject_contract(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()
        contract.accept_attachment(attachment.contract_attachment_no)
        contract.accept_attachment(attachment.contract_attachment_no)

        # when
        contract.reject()

        # then
        self.assertEqual(
            ContractStatus.REJECTED,
            contract.status
        )

    def test_cannot_accept_contract_when_not_all_attachments_accepted(self):
        # given
        contract: Contract = self.create_contract("partnerName", "umowa o cenę")
        # and
        attachment: ContractAttachment = contract.propose_attachment()
        # and
        contract.accept_attachment(attachment.contract_attachment_no)

        # then
        with self.assertRaises(AttributeError):
            contract.accept()
        self.assertNotEqual(ContractStatus.ACCEPTED, contract.status)

    def create_contract(self, partner_name: str, subject: str) -> Contract:
        return Contract(partner_name=partner_name, subject=subject, contract_no="no")
