import uuid
from datetime import datetime
from unittest import TestCase

from assignment.assignment_status import AssignmentStatus
from assignment.driver_assignment import DriverAssignment
from common.base_entity import new_uuid


class TestDriverAssignment(TestCase):
    DRIVER: int = 1
    SECOND_DRIVER: int = 2

    def test_can_accept_transit(self):
        # given
        assignment: DriverAssignment = self.assigment_for_transit(datetime.now())
        # and
        assignment.propose_to(self.DRIVER)

        # when
        assignment.accept_by(self.DRIVER)
        # then
        self.assertEqual(AssignmentStatus.ON_THE_WAY, assignment.status)

    def test_only_one_driver_can_accept_transit(self):
        # given
        assignment: DriverAssignment = self.assigment_for_transit(datetime.now())
        # and
        assignment.propose_to(self.DRIVER)
        # and
        assignment.accept_by(self.DRIVER)

        # expect
        with self.assertRaises(AttributeError):
            assignment.accept_by(self.SECOND_DRIVER)

    def test_transit_cannot_by_accepted_by_driver_who_already_rejected(self):
        # given
        assignment: DriverAssignment = self.assigment_for_transit(datetime.now())
        # and
        assignment.reject_by(self.DRIVER)

        # expect
        with self.assertRaises(AttributeError):
            assignment.accept_by(self.DRIVER)

    def test_transit_cannot_by_accepted_by_driver_who_has_not_seen_proposal(self):
        # given
        assignment: DriverAssignment = self.assigment_for_transit(datetime.now())

        # expect
        with self.assertRaises(AttributeError):
            assignment.accept_by(self.DRIVER)

    def test_can_reject_transit(self):
        # given
        assignment: DriverAssignment = self.assigment_for_transit(datetime.now())

        # when
        assignment.reject_by(self.DRIVER)

        # then
        self.assertEqual(AssignmentStatus.WAITING_FOR_DRIVER_ASSIGNMENT, assignment.status)

    def assigment_for_transit(self, when: datetime) -> DriverAssignment:
        return DriverAssignment(new_uuid(), when)