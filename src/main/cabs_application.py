import uvicorn
from fastapi import FastAPI

from core.database import create_db_and_tables
from ui.car_type_controller import car_type_router
from ui.claim_controller import claim_router


class CabsApplication:
    app: FastAPI

    def __init__(self):
        self.app = FastAPI()
        self.app.include_router(car_type_router)
        self.app.include_router(claim_router)

        @self.app.on_event("startup")
        def on_startup():
            create_db_and_tables()

    @classmethod
    def create_app(cls) -> FastAPI:
        return cls().app


if __name__ == '__main__':
    uvicorn.run("cabs_application:CabsApplication.create_app", host="127.0.0.1", port=5000, log_level="trace", reload=True)
