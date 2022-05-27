from datetime import datetime
from typing import Optional

from dateutil.relativedelta import relativedelta
from fastapi import Depends

from dto.claim_dto import ClaimDTO
from dto.driver_attribute_dto import DriverAttributeDTO
from dto.driver_report import DriverReport
from dto.driver_session_dto import DriverSessionDTO
from dto.transit_dto import TransitDTO
from entity import DriverAttribute, Transit
from repository.claim_repository import ClaimRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from service.driver_service import DriverService

class OldDriverReportCreator:
    driver_service: DriverService = Depends(DriverService)
    driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp)
    claim_repository: ClaimRepositoryImp = Depends(ClaimRepositoryImp)
    driver_session_repository: DriverSessionRepositoryImp = Depends(DriverSessionRepositoryImp)

    def __init__(
            self,
            driver_service: DriverService = Depends(DriverService),
            driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp),
            claim_repository: ClaimRepositoryImp = Depends(ClaimRepositoryImp),
            driver_session_repository: DriverSessionRepositoryImp = Depends(DriverSessionRepositoryImp)
    ):
        self.driver_service = driver_service
        self.driver_repository = driver_repository
        self.claim_repository = claim_repository
        self.driver_session_repository = driver_session_repository

    def create_report(self, driver_id: int, last_days: Optional[int] = 0) -> DriverReport:
        driver_report = DriverReport()
        driver_dto = self.driver_service.load_driver(driver_id)
        driver_report.driver_dto = driver_dto
        driver = self.driver_repository.get_one(driver_id)
        [driver_report.attributes.append(DriverAttributeDTO(driver_attribute=attr)) for attr in filter(
            lambda attr: not attr.name == DriverAttribute.DriverAttributeName.MEDICAL_EXAMINATION_REMARKS,
            driver.attributes
        )]
        begging_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        since = begging_of_today - relativedelta(days=last_days)
        all_by_driver_and_logged_at_after = self.driver_session_repository.find_all_by_driver_and_logged_at_after(
            driver, since)
        sessions_with_transits = { }
        for session in all_by_driver_and_logged_at_after:
            dto = DriverSessionDTO(**session.dict())
            transits_in_session = list(filter(
                lambda
                    t: t.status == Transit.Status.COMPLETED and not t.complete_at < session.logged_at and not t.complete_at > session.logged_out_at,
                driver.transits
            ))
            transits_dtos_in_session = []
            for t in transits_in_session:
                transit_dto = TransitDTO(transit=t)
                by_owner_and_transit = self.claim_repository.find_by_owner_and_transit(t.client, t)
                if by_owner_and_transit is not None:
                    claim = ClaimDTO(**by_owner_and_transit[0].dict())
                    transit_dto.claim_dto = claim
                transits_dtos_in_session.append(transit_dto)
            sessions_with_transits[dto] = transits_dtos_in_session
        driver_report.sessions = sessions_with_transits
        return driver_report
