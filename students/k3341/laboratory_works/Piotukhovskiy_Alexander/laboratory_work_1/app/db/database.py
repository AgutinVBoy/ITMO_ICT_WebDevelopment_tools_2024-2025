import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from config import settings
from db import models


def get_database_url():
    if os.getenv("TESTING") == "true":
        return "sqlite:///./test.db"

    return (
        f"postgresql://{settings.db_user}:{settings.db_password}@"
        f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


def create_db_engine():
    database_url = get_database_url()

    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=True
        )
    else:
        return create_engine(database_url, echo=True)


engine = create_db_engine()


def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
