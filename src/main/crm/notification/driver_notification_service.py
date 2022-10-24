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

    def ask_driver_for_details_about_claim(self, claim_no: str, transit_id) -> None:
        # ...
        pass
