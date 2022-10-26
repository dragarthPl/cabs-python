import uvicorn
from fastapi_injector import attach_injector
from injector import Injector
from fastapi import FastAPI

from core.database import create_db_and_tables, DatabaseModule
from party.infra.party_relationship_repository_impl import PartyRelationshipRepositoryImpl
from party.infra.party_repository_impl import PartyRepositoryImpl
from party.model.party.party_relationship_repository import PartyRelationshipRepository
from party.model.party.party_repository import PartyRepository
from loyalty.awards_service import AwardsService
from loyalty.awards_service_impl import AwardsServiceImpl
from loyalty.awards_account_controller import awards_account_router
from carfleet.car_type_controller import car_type_router
from crm.claims.claim_controller import claim_router
from crm.client_controller import client_router
from agreements.contract_controller import contract_router
from driverfleet.driver_controller import driver_router
from driverfleet.driverreport.driver_report_controller import driver_report_router
from ui.driver_session_controller import driver_session_router
from ui.driver_tracking_controller import driver_tracking_router
from crm.transitanalyzer.transit_analyzer_controller import transit_analyzer_router
from ui.transit_controller import transit_router

from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler


def configure(binder):
    binder.bind(AwardsService, to=AwardsServiceImpl)
    binder.bind(PartyRepository, to=PartyRepositoryImpl)
    binder.bind(PartyRelationshipRepository, to=PartyRelationshipRepositoryImpl)


class CabsApplication:
    app: FastAPI

    def __init__(self):
        a_injector = Injector([configure, DatabaseModule])
        self.app = FastAPI()
        self.app.add_middleware(EventHandlerASGIMiddleware, handlers=[local_handler])
        self.app.include_router(awards_account_router)
        self.app.include_router(car_type_router)
        self.app.include_router(claim_router)
        self.app.include_router(client_router)
        self.app.include_router(contract_router)
        self.app.include_router(driver_router)
        self.app.include_router(driver_report_router)
        self.app.include_router(driver_session_router)
        self.app.include_router(driver_tracking_router)
        self.app.include_router(transit_analyzer_router)
        self.app.include_router(transit_router)
        self.app.state.injector = a_injector
        attach_injector(self.app, a_injector)

        @self.app.on_event("startup")
        def on_startup():
            create_db_and_tables()

    @classmethod
    def create_app(cls) -> FastAPI:
        return cls().app


app = CabsApplication().create_app()


if __name__ == '__main__':
    uvicorn.run("cabs_application:app", host="127.0.0.1", port=5000, log_level="trace", reload=True)
