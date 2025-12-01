import os
import sys
import pytest
from typing import Generator
from sqlmodel import Session, SQLModel
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

os.environ["TESTING"] = "true"
os.environ["DB_USER"] = "test_user"
os.environ["DB_PASSWORD"] = "test_password"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "test_db"
os.environ["JWT_SECRET"] = "test_secret_key_for_integration_tests"

@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    from app.db import database
    import os as os_module

    test_db_path = "./test.db"
    if os_module.path.exists(test_db_path):
        os_module.remove(test_db_path)

    SQLModel.metadata.create_all(database.engine)

    yield database.engine

    SQLModel.metadata.drop_all(database.engine)
    database.engine.dispose()

    import time
    time.sleep(0.1)

    try:
        if os_module.path.exists(test_db_path):
            os_module.remove(test_db_path)
    except PermissionError:
        pass


@pytest.fixture(name="app", scope="session")
def app_fixture(engine):
    from fastapi import FastAPI
    from app.routes import auth_router, user_router, trip_router

    test_app = FastAPI()
    test_app.include_router(auth_router, prefix="/auth", tags=["auth"])
    test_app.include_router(user_router, prefix="/users", tags=["users"])
    test_app.include_router(trip_router, prefix="/trip", tags=["trip"])

    return test_app


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture(name="client")
def client_fixture(app, engine, session: Session) -> Generator[TestClient, None, None]:
    from app.db.database import get_session

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
