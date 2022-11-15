from uuid import UUID

from ride import transit


class DriverNotificationService:
    def notify_about_possible_transit(self, driver_id: int, transit_id) -> None:
        # ...
        pass

    def notify_about_changed_transit_address(self, driver_id: int, transit_id) -> None:
        # ...
        pass

    def notify_about_cancelled_transit(self, driver_id: int, transit_id) -> None:
        # ...
        pass

    def notify_about_possible_transit(self, driver_id: int, request_id: UUID) -> None:
        # find transit and delegate to notify_about_possible_transit(int, int)
        pass

    def notify_about_changed_transit_address(self, driver_id: int, request_id: UUID) -> None:
        # find transit and delegate to notify_about_changed_transit_address(int, int)
        pass

    def notify_about_cancelled_transit(self, driver_id: int, request_id: UUID) -> None:
        # find transit and delegate to notify_about_cancelled_transit(int, int)
        pass

    def ask_driver_for_details_about_claim(self, claim_no: str, transit_id) -> None:
        # ...
        pass
