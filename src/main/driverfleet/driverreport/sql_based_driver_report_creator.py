from datetime import datetime
from typing import Optional

import pytz
from dateutil.relativedelta import relativedelta
from injector import inject

from carfleet.car_class import CarClass
from sqlmodel import Session
from sqlalchemy import text

from crm.claims.claim import Claim
from geolocation.distance import Distance
from driverfleet.driver import Driver
from driverfleet.driver_attribute_name import DriverAttributeName
from geolocation.address.address_dto import AddressDTO
from crm.claims.claim_dto import ClaimDTO
from driverfleet.driver_dto import DriverDTO
from driverfleet.driverreport.driver_report import DriverReport
from ride.details.status import Status
from tracking.driver_session_dto import DriverSessionDTO
from ride.transit_dto import TransitDTO


class SqlBasedDriverReportCreator:
    QUERY_FOR_DRIVER_WITH_ATTRS = (
        "SELECT d.id, d.first_name, d.last_name, d.driver_license, "
        "d.photo, d.status, d.type, attr.name, attr.value "
        "FROM Driver AS d "
        "LEFT JOIN DriverAttribute attr ON d.id = attr.driver_id "
        "WHERE d.id = :driver_id AND attr.name <> :filtered_attr"
    )

    QUERY_FOR_SESSIONS = (
        "SELECT ds.logged_at, ds.logged_out_at, ds.plates_number, ds.car_class, ds.car_brand, "
        "td.transit_id as TRANSIT_ID, td.request_uuid as REQUEST_ID, td.tariff_name as TARIFF_NAME, "
        "td.status as TRANSIT_STATUS, "
        "td.distance, td.tariff_km_rate, "
        "td.price, td.drivers_fee, td.estimated_price, td.tariff_base_fee, "
        "td.date_time, td.published_at, td.accepted_at, td.started, td.complete_at, td.car_type, "
        "cl.id as CLAIM_ID, cl.owner_id, cl.reason, cl.incident_description, cl.status as CLAIM_STATUS,"
        " cl.creation_date, cl.completion_date, cl.change_date, cl.completion_mode, cl.claim_no, "
        "af.country as AF_COUNTRY, af.city as AF_CITY, af.street AS AF_STREET, af.building_number AS AF_NUMBER, "
        "ato.country as ATO_COUNTRY, ato.city as ATO_CITY, ato.street AS ATO_STREET, "
        "ato.building_number AS ATO_NUMBER "
        "FROM DriverSession AS ds "
        "LEFT JOIN TransitDetails AS td ON td.driver_id = ds.driver_id "
        "LEFT JOIN Address AS af ON td.address_from_id = af.id "
        "LEFT JOIN Address AS ato ON td.address_to_id = ato.id "
        "LEFT JOIN Claim AS cl ON cl.transit_id = td.transit_id "
        "WHERE ds.driver_id = :driver_id AND td.status = :transit_status "
        "AND ds.logged_at >= :since "
        "AND td.complete_at >= ds.logged_at "
        "AND td.complete_at <= ds.logged_out_at GROUP BY ds.id, ds.logged_at"
    )

    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def create_report(self, driver_id: int, last_days: int = None) -> DriverReport:
        driver_report = DriverReport()
        stmt = text(self.QUERY_FOR_DRIVER_WITH_ATTRS)
        stmt = stmt.params(
            driver_id=driver_id,
            filtered_attr=DriverAttributeName.MEDICAL_EXAMINATION_REMARKS.name
        )
        driver_info = self.session.execute(stmt).all()

        [self.add_attr_to_report(driver_report, info) for info in driver_info]
        self.add_driver_to_report(driver_report, driver_info[0]) if driver_info[0] else None

        stmt = text(self.QUERY_FOR_SESSIONS)
        stmt = stmt.params(
            driver_id=driver_id,
            transit_status=Status.COMPLETED.name,
            since=self.calculate_starting_point(last_days)
        )
        result_stream = self.session.execute(stmt).all()

        sessions = {}
        for cells in result_stream:
            key = self.retrieve_driving_session(cells)
            value = self.retrieve_transit(cells)
            if key in sessions:
                sessions[key].append(value)
            else:
                sessions[key] = [value]

        driver_report.sessions = sessions
        return driver_report

    def retrieve_transit(self, cells) -> TransitDTO:
        row = cells._asdict()
        return TransitDTO(
            id=row.get('TRANSIT_ID'),
            factor=1,
            # TODO: LF back
            tariff=row.get('TARIFF_NAME'),
            status=Status[row.get("TRANSIT_STATUS")],
            driver=None,
            distance=Distance.of_km(row.get('km')),
            km_rate=row.get('tariff_km_rate'),
            price=row.get("price"),
            driver_fee=row.get("drivers_fee"),
            estimated_price=row.get("estimated_price"),
            base_fee=row.get("tariff_base_fee"),
            date_time=row.get("date_time"),
            published=row.get("published_at"),
            accepted_at=row.get("accepted_at"),
            started=row.get("started"),
            complete_at=row.get("complete_at"),
            claim_dto=self.retrieve_claim(cells),
            proposed_drivers=None,
            address_to=self.retrieve_to_address(cells),
            address_from=self.retrieve_from_address(cells),
            car_class=CarClass[row.get("car_class")],
            client_dto=None,
        )

    def retrieve_driving_session(self, cells) -> DriverSessionDTO:
        row = cells._asdict()
        return DriverSessionDTO(
            logged_at=row.get("logged_at"),
            logged_out_at=row.get("logged_out_at"),
            plates_number=row.get("plates_number"),
            car_class=CarClass[row.get("car_class")],
            car_brand=row.get("car_brand"),
        )

    def retrieve_to_address(self, cells) -> AddressDTO:
        row = cells._asdict()
        return AddressDTO(
            country=row.get("ATO_COUNTRY"),
            city=row.get("ATO_CITY"),
            street=row.get("ATO_STREET"),
            building_number=None if not row.get("ATO_NUMBER") else row.get("ATO_NUMBER"),
        )

    def retrieve_from_address(self, cells) -> AddressDTO:
        row = cells._asdict()
        return AddressDTO(
            country=row.get("AF_COUNTRY"),
            city=row.get("AF_CITY"),
            street=row.get("AF_STREET"),
            building_number=None if not row.get("AF_NUMBER") else row.get("AF_NUMBER"),
        )

    def retrieve_claim(self, cells) -> Optional[ClaimDTO]:
        row = cells._asdict()
        claim_id = row.get("CLAIM_ID")
        completion_mode = row.get("completion_mode")
        if not claim_id:
            return None
        return ClaimDTO(
            claim_id=claim_id,
            client_id=row.get("owner_id"),
            transit_id=row.get("transit_id"),
            reason=row.get("reason"),
            incident_description=row.get("incident_description"),
            is_draft=True,
            creation_date=row.get("creation_date"),
            completion_date=row.get("completion_date"),
            change_date=row.get("change_date"),
            completion_mode=None if not completion_mode else Claim.CompletionMode[completion_mode],
            status=row.get("claim_status"),
            claim_no=row.get("claim_no"),
        )

    def calculate_starting_point(self, last_days: int) -> datetime:
        begging_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)
        since = begging_of_today - relativedelta(days=last_days)
        return since

    def add_driver_to_report(self, driver_report: DriverReport, cells) -> None:
        row = cells._asdict()
        driver_type = row.get("type")
        driver_report.driver_dto = DriverDTO(
            id=row.get("id"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            driver_license=row.get("driver_license"),
            photo=row.get("photo"),
            status=Driver.Status[row.get("status")],
            type=None if not driver_type else Driver.Type[driver_type]
        )

    def add_attr_to_report(self, driver_report: DriverReport, cells) -> None:
        driver_report.add_attr(
            DriverAttributeName[cells._asdict().get("name")],
            cells[8]
        )
