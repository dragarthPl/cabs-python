import uvicorn
from core.database import create_db_and_tables
from fastapi import FastAPI
from ui.awards_account_controller import awards_account_router
from ui.car_type_controller import car_type_router
from ui.claim_controller import claim_router
from ui.client_controller import client_router
from ui.contract_controller import contract_router
from ui.driver_controller import driver_router
from driverreport.driver_report_controller import driver_report_router
from ui.driver_session_controller import driver_session_router
from ui.driver_tracking_controller import driver_tracking_router
from ui.transit_analyzer_controller import transit_analyzer_router
from ui.transit_controller import transit_router


class CabsApplication:
    app: FastAPI

    def __init__(self):
        self.app = FastAPI()
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

        @self.app.on_event("startup")
        def on_startup():
            create_db_and_tables()

    @classmethod
    def create_app(cls) -> FastAPI:
        return cls().app


if __name__ == '__main__':
    uvicorn.run("cabs_application:CabsApplication.create_app", host="127.0.0.1", port=5000, log_level="trace", reload=True)
