from datetime import datetime
from typing import List

from injector import inject
from sqlalchemy.dialects.postgresql import UUID

from assignment.assignment_status import AssignmentStatus
from assignment.involved_drivers_summary import InvolvedDriversSummary
from driverfleet.driver import Driver
from tracking.driver_position_dtov_2 import DriverPositionDTOV2
from assignment.driver_assignment import DriverAssignment
from geolocation.address.address_dto import AddressDTO
from geolocation.distance import Distance
from assignment.driver_assignment_repository import DriverAssignmentRepository
from carfleet.car_class import CarClass
from carfleet.car_type_service import CarTypeService
from crm.notification.driver_notification_service import DriverNotificationService
from tracking.driver_tracking_service import DriverTrackingService


class DriverAssignmentFacade:
    driver_assignment_repository: DriverAssignmentRepository
    car_type_service: CarTypeService
    driver_tracking_service: DriverTrackingService
    driver_notification_service: DriverNotificationService

    @inject
    def __init__(
        self,
        driver_assignment_repository: DriverAssignmentRepository,
        car_type_service: CarTypeService,
        driver_tracking_service: DriverTrackingService,
        driver_notification_service: DriverNotificationService,
    ):
        self.driver_assignment_repository = driver_assignment_repository
        self.car_type_service = car_type_service
        self.driver_tracking_service = driver_tracking_service
        self.driver_notification_service = driver_notification_service

    def start_assigning_drivers(
        self,
        transit_request_uuid: UUID,
        address_from: AddressDTO,
        car_class: CarClass,
        when: datetime
    ):
        self.driver_assignment_repository.save(DriverAssignment(transit_request_uuid, when))
        return self.search_for_possible_drivers(transit_request_uuid, address_from, car_class)

    def search_for_possible_drivers(
        self,
        transit_request_uuid: UUID,
        address_from: AddressDTO,
        car_class: CarClass,
    ):
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        if driver_assignment:
            distance_to_check: int = 0

            # Tested on production, works as expected.
            # If you change this code and the system will collapse AGAIN, I'll find you...
            while True:
                if driver_assignment.awaiting_drivers_responses > 4:
                    return InvolvedDriversSummary.none_found()
                distance_to_check += 1

                # FIXME: to refactor when the final business logic will be determined
                if (
                        driver_assignment.should_not_wait_for_driver_any_more(datetime.now())
                        or distance_to_check >= 20
                ):
                    driver_assignment.fail_driver_assignment()
                    self.driver_assignment_repository.save(driver_assignment)
                    return InvolvedDriversSummary.none_found()

                car_classes: List[CarClass] = self.choose_possible_car_classes(car_class)
                if not car_classes:
                    return InvolvedDriversSummary.none_found()

                drivers_avg_positions: List[DriverPositionDTOV2] = \
                    self.driver_tracking_service.find_active_drivers_nearby_by_address(
                        address_from,
                        Distance.of_km(distance_to_check), car_classes
                    )

                if not drivers_avg_positions:
                    # next iteration
                    continue

                for driver_avg_position in drivers_avg_positions:
                    if driver_assignment.can_propose_to(driver_avg_position.driver_id):
                        driver_assignment.propose_to(driver_avg_position.driver_id)
                        self.driver_notification_service.notify_about_possible_transit(
                            driver_avg_position.driver_id,
                            transit_request_uuid
                        )

                self.driver_assignment_repository.save(driver_assignment)
                return self.load_involved_drivers(driver_assignment)
        else:
            raise AttributeError(f"Transit does not exist, id = {transit_request_uuid}")

    def choose_possible_car_classes(self, car_class: CarClass):
        car_classes: List[CarClass] = []
        active_car_classes: List[CarClass] = self.car_type_service.find_active_car_classes()
        if car_class is not None:
            if car_class in active_car_classes:
                car_classes.append(car_class)
        else:
            car_classes.extend(active_car_classes)
        return car_classes

    def accept_transit(self, transit_request_uuid: UUID, driver_id: int) -> InvolvedDriversSummary:
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        driver_assignment.accept_by(driver_id)
        return self.load_involved_drivers(driver_assignment)

    def reject_transit(self, transit_request_uuid: UUID, driver_id: int) -> InvolvedDriversSummary:
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        if not driver_assignment:
            raise AttributeError(f"Assignment does not exist, id = {transit_request_uuid}")
        driver_assignment.reject_by(driver_id)
        return self.load_involved_drivers(driver_assignment)

    def is_driver_assigned(self, transit_request_uuid: UUID) -> bool:
        return self.driver_assignment_repository.find_by_request_uuid_and_status(
            transit_request_uuid,
            AssignmentStatus.ON_THE_WAY
        ) is not None

    def load_involved_drivers(self, driver_assignment: DriverAssignment) -> InvolvedDriversSummary:
        return InvolvedDriversSummary(
            driver_assignment.get_proposed_drivers(),
            driver_assignment.get_driver_rejections(),
            driver_assignment.assigned_driver,
            driver_assignment.status
        )

    def load_involved_drivers_uuid(self, transit_request_uuid: UUID) -> InvolvedDriversSummary:
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        if not driver_assignment:
            return InvolvedDriversSummary.none_found()
        return self.load_involved_drivers(driver_assignment)

    def cancel(self, transit_request_uuid):
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        if not driver_assignment:
            return InvolvedDriversSummary.none_found()
        return self.load_involved_drivers(driver_assignment)

    def find(self, transit_request_uuid: UUID) -> DriverAssignment:
        return self.driver_assignment_repository.find_by_request_uuid(transit_request_uuid)

    def notify_assigned_driver_about_changed_destination(self, transit_request_uuid: UUID):
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        if driver_assignment and driver_assignment.get_assigned_driver():
            assigned_driver: int = self.driver_assignment.get_assigned_driver()
            self.driver_notification_service.notify_about_changed_transit_address(
                assigned_driver,
                transit_request_uuid
            )
            for driver in driver_assignment.get_proposed_drivers():
                self.driver_notification_service.notify_about_changed_transit_address(driver, transit_request_uuid)

    def notify_proposed_drivers_about_changed_destination(self, transit_request_uuid: UUID):
        driver_assignment: DriverAssignment = self.find(transit_request_uuid)
        for driver in driver_assignment.get_proposed_drivers():
            self.driver_notification_service.notify_about_changed_transit_address(driver, transit_request_uuid)

    def notify_about_cancelled_destination(self, driver_assignment: DriverAssignment, transit_request_uuid: UUID):
        assigned_driver: int = driver_assignment.assigned_driver
        if assigned_driver:
            self.driver_notification_service.notify_about_cancelled_transit(assigned_driver, transit_request_uuid)
